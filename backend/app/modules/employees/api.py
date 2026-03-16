from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.context import UserContext
from app.core.security import get_current_user
from app.modules.auth.models import User
from app.modules.auth.service import get_db
from app.modules.employees.models import (
    EmployeeRole,
    Group,
    Organization,
    Permission,
    Position,
    PositionRole,
    RolePermission,
    UserOrganization,
    UserPosition,
)
from app.modules.employees.schemas import (
    AssignUserDto,
    EmployeeRoleDto,
    EmployeeRoleUpdate,
    EmployeeRoleUpsert,
    EmployeeUserCreate,
    EmployeeUserDto,
    EmployeeUserUpdate,
    GroupDto,
    GroupUpsert,
    OrganizationCreate,
    OrganizationDto,
    OrganizationUpdate,
    PermissionDto,
    PositionDto,
    PositionUpsert,
    SetPasswordDto,
    SwitchOrganizationDto,
)
from app.modules.employees.service import (
    build_org_tree,
    calc_user_managers,
    calc_user_permissions,
    create_employee_user,
    list_permissions,
    list_users,
    set_user_password,
    update_employee_user,
)

router = APIRouter(tags=["employees"], dependencies=[Depends(get_current_user)])


@router.get("/users", response_model=list[EmployeeUserDto])
def get_users(
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    organization_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    users = list_users(db, search, include_archived, organization_id)
    return [EmployeeUserDto(id=u.id, full_name=u.full_name, login=u.username, phone=u.phone, is_active=u.is_active, is_archived=u.is_archived, created_at=u.created_at) for u in users]


@router.get("/users/{user_id}", response_model=EmployeeUserDto)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    return EmployeeUserDto(id=user.id, full_name=user.full_name, login=user.username, phone=user.phone, is_active=user.is_active, is_archived=user.is_archived, created_at=user.created_at)


@router.post("/users", response_model=EmployeeUserDto)
def create_user(payload: EmployeeUserCreate, db: Session = Depends(get_db)):
    user = create_employee_user(db, payload)
    return EmployeeUserDto(id=user.id, full_name=user.full_name, login=user.username, phone=user.phone, is_active=user.is_active, is_archived=user.is_archived, created_at=user.created_at)


@router.patch("/users/{user_id}", response_model=EmployeeUserDto)
def patch_user(user_id: int, payload: EmployeeUserUpdate, db: Session = Depends(get_db)):
    user = update_employee_user(db, user_id, payload)
    return EmployeeUserDto(id=user.id, full_name=user.full_name, login=user.username, phone=user.phone, is_active=user.is_active, is_archived=user.is_archived, created_at=user.created_at)


@router.post("/users/{user_id}/archive")
def archive_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    user.is_archived = True
    user.is_active = False
    db.commit()
    return {"status": "ok"}


@router.post("/users/{user_id}/restore")
def restore_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    user.is_archived = False
    user.is_active = True
    db.commit()
    return {"status": "ok"}


@router.post("/users/{user_id}/set-password")
def set_password(user_id: int, payload: SetPasswordDto, db: Session = Depends(get_db)):
    set_user_password(db, user_id, payload.new_password)
    return {"status": "ok"}


@router.get("/users/{user_id}/permissions")
def user_permissions(user_id: int, organization_id: int, db: Session = Depends(get_db)):
    return calc_user_permissions(db, user_id, organization_id)


@router.get("/users/{user_id}/managers")
def user_managers(user_id: int, organization_id: int, db: Session = Depends(get_db)):
    return calc_user_managers(db, user_id, organization_id)


@router.get("/organizations/my", response_model=list[OrganizationDto])
def my_orgs(current_user: UserContext = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Organization)
        .join(UserOrganization, UserOrganization.organization_id == Organization.id)
        .where(UserOrganization.user_id == current_user.id)
        .order_by(Organization.name)
    ).scalars().all()
    return rows


@router.get("/organizations", response_model=list[OrganizationDto])
def get_orgs(db: Session = Depends(get_db)):
    return list(db.scalars(select(Organization).order_by(Organization.name)))


@router.post("/organizations", response_model=OrganizationDto)
def create_org(payload: OrganizationCreate, db: Session = Depends(get_db)):
    organization = Organization(name=payload.name, code=payload.code, is_active=True, is_archived=False)
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


@router.patch("/organizations/{organization_id}", response_model=OrganizationDto)
def update_org(organization_id: int, payload: OrganizationUpdate, db: Session = Depends(get_db)):
    organization = db.get(Organization, organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="organization_not_found")
    if payload.name is not None:
        organization.name = payload.name
    if payload.code is not None:
        organization.code = payload.code
    if payload.is_active is not None:
        organization.is_active = payload.is_active
    db.commit()
    db.refresh(organization)
    return organization


@router.post("/organizations/{organization_id}/archive")
def archive_org(organization_id: int, db: Session = Depends(get_db)):
    organization = db.get(Organization, organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="organization_not_found")
    organization.is_archived = True
    organization.is_active = False
    db.commit()
    return {"status": "ok"}


@router.post("/auth/switch-organization")
def switch_org(payload: SwitchOrganizationDto, current_user: UserContext = Depends(get_current_user), db: Session = Depends(get_db)):
    member = db.scalar(select(UserOrganization.id).where(UserOrganization.user_id == current_user.id, UserOrganization.organization_id == payload.organization_id))
    if not member:
        raise HTTPException(status_code=403, detail="organization_access_denied")
    user = db.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    user.last_organization_id = payload.organization_id
    db.commit()
    return {"status": "ok", "organization_id": payload.organization_id}


@router.get("/org/groups", response_model=list[GroupDto])
def get_groups(organization_id: int, db: Session = Depends(get_db)):
    return list(db.scalars(select(Group).where(Group.organization_id == organization_id).order_by(Group.sort_order, Group.name)))


@router.get("/org/groups/{group_id}", response_model=GroupDto)
def get_group(group_id: int, db: Session = Depends(get_db)):
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="group_not_found")
    return group


@router.get("/org/groups/tree")
def get_group_tree(organization_id: int, include_archived: bool = Query(default=False), db: Session = Depends(get_db)):
    return build_org_tree(db, organization_id, include_archived)


@router.post("/org/groups", response_model=GroupDto)
def create_group(payload: GroupUpsert, db: Session = Depends(get_db)):
    group = Group(**payload.model_dump(), is_active=True, is_archived=False)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.patch("/org/groups/{group_id}", response_model=GroupDto)
def patch_group(group_id: int, payload: GroupUpsert, db: Session = Depends(get_db)):
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="group_not_found")
    data = payload.model_dump()
    for key, value in data.items():
        setattr(group, key, value)
    db.commit()
    db.refresh(group)
    return group


@router.post("/org/groups/{group_id}/archive")
def archive_group(group_id: int, db: Session = Depends(get_db)):
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="group_not_found")
    has_subgroups = db.scalar(select(Group.id).where(Group.parent_group_id == group_id, Group.is_archived == False))  # noqa: E712
    has_positions = db.scalar(select(Position.id).where(Position.group_id == group_id, Position.is_archived == False))  # noqa: E712
    has_users = db.scalar(select(UserPosition.id).join(Position, Position.id == UserPosition.position_id).where(Position.group_id == group_id))
    if has_subgroups or has_positions or has_users:
        raise HTTPException(status_code=400, detail="group_not_empty")
    group.is_archived = True
    group.is_active = False
    db.commit()
    return {"status": "ok"}


@router.get("/org/positions", response_model=list[PositionDto])
def get_positions(organization_id: int, db: Session = Depends(get_db)):
    return list(db.scalars(select(Position).where(Position.organization_id == organization_id).order_by(Position.sort_order, Position.name)))


@router.get("/org/positions/{position_id}", response_model=PositionDto)
def get_position(position_id: int, db: Session = Depends(get_db)):
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="position_not_found")
    return position


@router.post("/org/positions", response_model=PositionDto)
def create_position(payload: PositionUpsert, db: Session = Depends(get_db)):
    position = Position(
        organization_id=payload.organization_id,
        group_id=payload.group_id,
        name=payload.name,
        manager_position_id=payload.manager_position_id,
        sort_order=payload.sort_order,
        is_active=True,
        is_archived=False,
    )
    db.add(position)
    db.flush()
    for role_id in payload.role_ids:
        db.add(PositionRole(position_id=position.id, role_id=role_id))
    db.commit()
    db.refresh(position)
    return position


@router.patch("/org/positions/{position_id}", response_model=PositionDto)
def patch_position(position_id: int, payload: PositionUpsert, db: Session = Depends(get_db)):
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="position_not_found")
    position.organization_id = payload.organization_id
    position.group_id = payload.group_id
    position.name = payload.name
    position.manager_position_id = payload.manager_position_id
    position.sort_order = payload.sort_order
    db.execute(delete(PositionRole).where(PositionRole.position_id == position_id))
    for role_id in payload.role_ids:
        db.add(PositionRole(position_id=position_id, role_id=role_id))
    db.commit()
    db.refresh(position)
    return position


@router.post("/org/positions/{position_id}/archive")
def archive_position(position_id: int, db: Session = Depends(get_db)):
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="position_not_found")
    has_users = db.scalar(select(UserPosition.id).where(UserPosition.position_id == position_id))
    if has_users:
        raise HTTPException(status_code=400, detail="position_has_users")
    position.is_archived = True
    position.is_active = False
    db.commit()
    return {"status": "ok"}


@router.post("/org/positions/{position_id}/assign-user")
def assign_user(position_id: int, payload: AssignUserDto, db: Session = Depends(get_db)):
    row = db.get(Position, position_id)
    if not row:
        raise HTTPException(status_code=404, detail="position_not_found")
    exists = db.scalar(select(UserPosition.id).where(UserPosition.user_id == payload.user_id, UserPosition.position_id == position_id))
    if not exists:
        db.add(UserPosition(user_id=payload.user_id, position_id=position_id))
        db.commit()
    return {"status": "ok"}


@router.post("/org/positions/{position_id}/unassign-user")
def unassign_user(position_id: int, payload: AssignUserDto, db: Session = Depends(get_db)):
    db.execute(delete(UserPosition).where(UserPosition.position_id == position_id, UserPosition.user_id == payload.user_id))
    db.commit()
    return {"status": "ok"}


@router.get("/org/positions/{position_id}/users", response_model=list[EmployeeUserDto])
def position_users(position_id: int, db: Session = Depends(get_db)):
    rows = db.execute(select(User).join(UserPosition, UserPosition.user_id == User.id).where(UserPosition.position_id == position_id)).scalars().all()
    return [EmployeeUserDto(id=u.id, full_name=u.full_name, login=u.username, phone=u.phone, is_active=u.is_active, is_archived=u.is_archived, created_at=u.created_at) for u in rows]


@router.get("/roles", response_model=list[EmployeeRoleDto])
def get_roles(db: Session = Depends(get_db)):
    return list(db.scalars(select(EmployeeRole).order_by(EmployeeRole.name)))


@router.get("/roles/{role_id}", response_model=EmployeeRoleDto)
def get_role(role_id: int, db: Session = Depends(get_db)):
    role = db.get(EmployeeRole, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="role_not_found")
    return role


@router.post("/roles", response_model=EmployeeRoleDto)
def create_role(payload: EmployeeRoleUpsert, db: Session = Depends(get_db)):
    role = EmployeeRole(name=payload.name, code=payload.code, description=payload.description, is_system=False, is_active=True, is_archived=False)
    db.add(role)
    db.flush()
    for permission_id in payload.permission_ids:
        db.add(RolePermission(role_id=role.id, permission_id=permission_id))
    db.commit()
    db.refresh(role)
    return role


@router.patch("/roles/{role_id}", response_model=EmployeeRoleDto)
def patch_role(role_id: int, payload: EmployeeRoleUpdate, db: Session = Depends(get_db)):
    role = db.get(EmployeeRole, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="role_not_found")
    if payload.name is not None:
        role.name = payload.name
    if payload.code is not None:
        role.code = payload.code
    if payload.description is not None:
        role.description = payload.description
    if payload.is_active is not None:
        role.is_active = payload.is_active
    if payload.permission_ids is not None:
        db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
        for permission_id in payload.permission_ids:
            db.add(RolePermission(role_id=role_id, permission_id=permission_id))
    db.commit()
    db.refresh(role)
    return role


@router.post("/roles/{role_id}/archive")
def archive_role(role_id: int, db: Session = Depends(get_db)):
    role = db.get(EmployeeRole, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="role_not_found")
    if role.code == "SUPER_ADMIN":
        raise HTTPException(status_code=400, detail="cannot_archive_super_admin")
    role.is_archived = True
    role.is_active = False
    db.commit()
    return {"status": "ok"}


@router.delete("/roles/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db)):
    role = db.get(EmployeeRole, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="role_not_found")
    usage = db.scalar(select(PositionRole.id).where(PositionRole.role_id == role_id))
    if usage:
        raise HTTPException(status_code=400, detail="role_in_use")
    db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
    db.delete(role)
    db.commit()
    return Response(status_code=204)


@router.get("/permissions", response_model=list[PermissionDto])
def get_permissions(db: Session = Depends(get_db)):
    return list_permissions(db)
