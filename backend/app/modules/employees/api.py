from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.context import UserContext
from app.core.security import get_current_user
from app.modules.auth.service import get_db
from app.modules.employees.models import (
    Group,
    Organization,
    Permission,
    Position,
    PositionRole,
    Role,
    RolePermission,
    User,
    UserOrganization,
    UserPosition,
)
from app.modules.employees.schemas import (
    AssignUserPayload,
    GroupCreate,
    GroupUpdate,
    OrganizationCreate,
    OrganizationUpdate,
    PositionCreate,
    PositionUpdate,
    RoleCreate,
    RoleUpdate,
    SwitchOrganizationPayload,
    UserCreate,
    UserSetPassword,
    UserUpdate,
)
from app.modules.employees.service import (
    create_user,
    get_effective_permissions,
    get_role_usage,
    get_user_managers,
    list_users,
    require_permission,
    update_user,
    validate_manager_cycle,
)

router = APIRouter(tags=["employees"])


@router.get("/users")
def users_list(
    organization_id: int | None = None,
    search: str | None = None,
    show_archived: bool = False,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    require_permission(db, current_user.id, "users.view")
    return list_users(db, organization_id=organization_id, search=search, archived=show_archived)


@router.get("/users/{user_id}")
def users_get(user_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "users.view")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    org_ids = list(db.scalars(select(UserOrganization.organization_id).where(UserOrganization.user_id == user_id)))
    position_rows = db.execute(
        select(Position.id, Position.name, Position.organization_id)
        .join(UserPosition, UserPosition.position_id == Position.id)
        .where(UserPosition.user_id == user_id)
    ).all()
    return {
        "id": user.id,
        "full_name": user.full_name,
        "login": user.login,
        "phone": user.phone,
        "is_active": user.is_active,
        "is_archived": user.is_archived,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "organization_ids": org_ids,
        "positions": [
            {"id": pid, "name": name, "organization_id": oid} for pid, name, oid in position_rows
        ],
    }


@router.post("/users")
def users_create(payload: UserCreate, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "users.create")
    user = create_user(db, payload)
    return {"id": user.id}


@router.patch("/users/{user_id}")
def users_patch(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "users.edit")
    user = update_user(db, user_id, payload)
    return {"id": user.id}


@router.post("/users/{user_id}/archive")
def users_archive(user_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "users.archive")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    user.is_archived = True
    user.is_active = False
    db.commit()
    return {"ok": True}


@router.post("/users/{user_id}/restore")
def users_restore(user_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "users.archive")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    user.is_archived = False
    user.is_active = True
    db.commit()
    return {"ok": True}


@router.post("/users/{user_id}/set-password")
def users_set_password(user_id: int, payload: UserSetPassword, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    from app.modules.auth.security import hash_password

    require_permission(db, current_user.id, "users.set_password")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    user.password_hash = hash_password(payload.password)
    db.commit()
    return {"ok": True}


@router.get("/users/{user_id}/permissions")
def users_permissions(user_id: int, organization_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "users.view")
    return {"permissions": get_effective_permissions(db, user_id, organization_id)}


@router.get("/users/{user_id}/managers")
def users_managers(user_id: int, organization_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "users.view")
    return {"items": get_user_managers(db, user_id, organization_id)}


@router.get("/organizations/my")
def my_orgs(db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    orgs = db.execute(
        select(Organization.id, Organization.name, Organization.code)
        .join(UserOrganization, UserOrganization.organization_id == Organization.id)
        .where(UserOrganization.user_id == current_user.id, Organization.is_archived.is_(False))
    ).all()
    return [{"id": oid, "name": name, "code": code} for oid, name, code in orgs]


@router.get("/organizations")
def orgs(db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "organizations.manage")
    return list(db.execute(select(Organization.id, Organization.name, Organization.code, Organization.is_active, Organization.is_archived)).mappings())


@router.post("/organizations")
def org_create(payload: OrganizationCreate, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "organizations.manage")
    org = Organization(name=payload.name, code=payload.code)
    db.add(org)
    db.commit()
    db.refresh(org)
    return {"id": org.id}


@router.patch("/organizations/{organization_id}")
def org_patch(organization_id: int, payload: OrganizationUpdate, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "organizations.manage")
    org = db.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="organization_not_found")
    if payload.name is not None:
        org.name = payload.name
    if payload.is_active is not None:
        org.is_active = payload.is_active
    db.commit()
    return {"ok": True}


@router.post("/organizations/{organization_id}/archive")
def org_archive(organization_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "organizations.manage")
    org = db.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="organization_not_found")
    org.is_archived = True
    org.is_active = False
    db.commit()
    return {"ok": True}


@router.post("/auth/switch-organization")
def switch_org(payload: SwitchOrganizationPayload, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "organizations.switch")
    exists = db.scalar(
        select(UserOrganization.id).where(
            UserOrganization.user_id == current_user.id,
            UserOrganization.organization_id == payload.organization_id,
        )
    )
    if exists is None:
        raise HTTPException(status_code=400, detail="organization_not_allowed")
    return {"organization_id": payload.organization_id}


@router.get("/org/groups")
def groups_list(organization_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "orgstructure.view")
    rows = list(db.scalars(select(Group).where(Group.organization_id == organization_id)))
    return [
        {
            "id": item.id,
            "organization_id": item.organization_id,
            "parent_group_id": item.parent_group_id,
            "name": item.name,
            "head_user_id": item.head_user_id,
            "sort_order": item.sort_order,
            "is_active": item.is_active,
            "is_archived": item.is_archived,
        }
        for item in rows
    ]


@router.get("/org/groups/{group_id}")
def group_get(group_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "orgstructure.view")
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="group_not_found")
    return {
        "id": group.id,
        "organization_id": group.organization_id,
        "parent_group_id": group.parent_group_id,
        "name": group.name,
        "head_user_id": group.head_user_id,
        "sort_order": group.sort_order,
        "is_active": group.is_active,
        "is_archived": group.is_archived,
    }


@router.get("/org/groups/tree")
def groups_tree(organization_id: int, show_archived: bool = False, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "orgstructure.view")
    groups_stmt = select(Group).where(Group.organization_id == organization_id)
    pos_stmt = select(Position).where(Position.organization_id == organization_id)
    if not show_archived:
        groups_stmt = groups_stmt.where(Group.is_archived.is_(False))
        pos_stmt = pos_stmt.where(Position.is_archived.is_(False))
    groups = list(db.scalars(groups_stmt.order_by(Group.sort_order, Group.id)))
    positions = list(db.scalars(pos_stmt.order_by(Position.sort_order, Position.id)))
    users_rows = db.execute(
        select(UserPosition.position_id, User.id, User.full_name, User.is_archived)
        .join(User, User.id == UserPosition.user_id)
        .join(Position, Position.id == UserPosition.position_id)
        .where(Position.organization_id == organization_id)
    ).all()
    users_by_position: dict[int, list[dict]] = {}
    for position_id, uid, full_name, is_archived in users_rows:
        users_by_position.setdefault(position_id, []).append(
            {"id": uid, "full_name": full_name, "is_archived": is_archived}
        )
    return {
        "groups": [
            {
                "id": g.id,
                "parent_group_id": g.parent_group_id,
                "name": g.name,
                "head_user_id": g.head_user_id,
                "sort_order": g.sort_order,
                "is_archived": g.is_archived,
            }
            for g in groups
        ],
        "positions": [
            {
                "id": p.id,
                "group_id": p.group_id,
                "name": p.name,
                "manager_position_id": p.manager_position_id,
                "sort_order": p.sort_order,
                "is_manager": p.manager_position_id is None,
                "users": users_by_position.get(p.id, []),
                "is_archived": p.is_archived,
            }
            for p in positions
        ],
    }


@router.post("/org/groups")
def group_create(payload: GroupCreate, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "orgstructure.edit")
    if payload.head_user_id is not None:
        in_org = db.scalar(select(UserOrganization.id).where(UserOrganization.user_id == payload.head_user_id, UserOrganization.organization_id == payload.organization_id))
        if in_org is None:
            raise HTTPException(status_code=400, detail="head_outside_organization")
    group = Group(**payload.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)
    return {"id": group.id}


@router.patch("/org/groups/{group_id}")
def group_patch(group_id: int, payload: GroupUpdate, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "orgstructure.edit")
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="group_not_found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(group, key, value)
    db.commit()
    return {"ok": True}


@router.post("/org/groups/{group_id}/archive")
def group_archive(group_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "orgstructure.edit")
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="group_not_found")
    has_children = db.scalar(select(Group.id).where(Group.parent_group_id == group_id, Group.is_archived.is_(False)).limit(1))
    has_positions = db.scalar(select(Position.id).where(Position.group_id == group_id, Position.is_archived.is_(False)).limit(1))
    if has_children or has_positions:
        raise HTTPException(status_code=400, detail="group_not_empty")
    group.is_archived = True
    group.is_active = False
    db.commit()
    return {"ok": True}


@router.get("/org/positions")
def positions(organization_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "orgstructure.view")
    rows = list(db.scalars(select(Position).where(Position.organization_id == organization_id).order_by(Position.sort_order)))
    return [
        {
            "id": item.id,
            "organization_id": item.organization_id,
            "group_id": item.group_id,
            "name": item.name,
            "manager_position_id": item.manager_position_id,
            "sort_order": item.sort_order,
            "is_active": item.is_active,
            "is_archived": item.is_archived,
        }
        for item in rows
    ]


@router.get("/org/positions/{position_id}")
def position(position_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "orgstructure.view")
    item = db.get(Position, position_id)
    if not item:
        raise HTTPException(status_code=404, detail="position_not_found")
    role_ids = list(db.scalars(select(PositionRole.role_id).where(PositionRole.position_id == position_id)))
    return {
        "id": item.id,
        "organization_id": item.organization_id,
        "group_id": item.group_id,
        "name": item.name,
        "manager_position_id": item.manager_position_id,
        "sort_order": item.sort_order,
        "is_archived": item.is_archived,
        "role_ids": role_ids,
    }


@router.post("/org/positions")
def position_create(payload: PositionCreate, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "orgstructure.edit")
    group = db.get(Group, payload.group_id)
    if not group or group.organization_id != payload.organization_id:
        raise HTTPException(status_code=400, detail="group_org_mismatch")
    position = Position(
        organization_id=payload.organization_id,
        group_id=payload.group_id,
        name=payload.name,
        manager_position_id=payload.manager_position_id,
        sort_order=payload.sort_order,
    )
    db.add(position)
    db.flush()
    validate_manager_cycle(db, position.id, payload.manager_position_id)
    for role_id in sorted(set(payload.role_ids)):
        db.add(PositionRole(position_id=position.id, role_id=role_id))
    db.commit()
    return {"id": position.id}


@router.patch("/org/positions/{position_id}")
def position_patch(position_id: int, payload: PositionUpdate, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "orgstructure.edit")
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="position_not_found")
    data = payload.model_dump(exclude_unset=True)
    if "group_id" in data and data["group_id"] is not None:
        group = db.get(Group, data["group_id"])
        if not group or group.organization_id != position.organization_id:
            raise HTTPException(status_code=400, detail="group_org_mismatch")
    for key in ["group_id", "name", "sort_order", "is_active", "manager_position_id"]:
        if key in data:
            setattr(position, key, data[key])
    validate_manager_cycle(db, position.id, position.manager_position_id)
    if payload.role_ids is not None:
        db.execute(delete(PositionRole).where(PositionRole.position_id == position_id))
        for role_id in sorted(set(payload.role_ids)):
            db.add(PositionRole(position_id=position_id, role_id=role_id))
    db.commit()
    return {"ok": True}


@router.post("/org/positions/{position_id}/archive")
def position_archive(position_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "orgstructure.edit")
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="position_not_found")
    has_users = db.scalar(select(UserPosition.id).where(UserPosition.position_id == position_id).limit(1))
    if has_users:
        raise HTTPException(status_code=400, detail="position_not_empty")
    position.is_archived = True
    position.is_active = False
    db.commit()
    return {"ok": True}


@router.post("/org/positions/{position_id}/assign-user")
def assign_user(position_id: int, payload: AssignUserPayload, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "orgstructure.edit")
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="position_not_found")
    in_org = db.scalar(select(UserOrganization.id).where(UserOrganization.user_id == payload.user_id, UserOrganization.organization_id == position.organization_id))
    if in_org is None:
        raise HTTPException(status_code=400, detail="user_not_in_organization")
    link = db.scalar(select(UserPosition.id).where(UserPosition.user_id == payload.user_id, UserPosition.position_id == position_id))
    if link is None:
        db.add(UserPosition(user_id=payload.user_id, position_id=position_id))
        db.commit()
    return {"ok": True}


@router.post("/org/positions/{position_id}/unassign-user")
def unassign_user(position_id: int, payload: AssignUserPayload, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "orgstructure.edit")
    db.execute(delete(UserPosition).where(UserPosition.position_id == position_id, UserPosition.user_id == payload.user_id))
    db.commit()
    return {"ok": True}


@router.get("/org/positions/{position_id}/users")
def position_users(position_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "orgstructure.view")
    rows = db.execute(
        select(User.id, User.full_name, User.is_archived)
        .join(UserPosition, UserPosition.user_id == User.id)
        .where(UserPosition.position_id == position_id)
    ).all()
    return [{"id": uid, "full_name": full_name, "is_archived": is_archived} for uid, full_name, is_archived in rows]


@router.get("/roles")
def roles(show_archived: bool = False, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "roles.view")
    stmt = select(Role)
    if not show_archived:
        stmt = stmt.where(Role.is_archived.is_(False))
    rows = list(db.scalars(stmt.order_by(Role.name)))
    return [
        {
            "id": item.id,
            "name": item.name,
            "code": item.code,
            "description": item.description,
            "is_system": item.is_system,
            "is_active": item.is_active,
            "is_archived": item.is_archived,
        }
        for item in rows
    ]


@router.get("/roles/{role_id}")
def role(role_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "roles.view")
    item = db.get(Role, role_id)
    if not item:
        raise HTTPException(status_code=404, detail="role_not_found")
    permission_ids = list(db.scalars(select(RolePermission.permission_id).where(RolePermission.role_id == role_id)))
    return {
        "id": item.id,
        "name": item.name,
        "code": item.code,
        "description": item.description,
        "is_system": item.is_system,
        "is_active": item.is_active,
        "is_archived": item.is_archived,
        "permission_ids": permission_ids,
        "usage": get_role_usage(db, role_id),
    }


@router.post("/roles")
def role_create(payload: RoleCreate, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "roles.create")
    role = Role(name=payload.name, code=payload.code, description=payload.description)
    db.add(role)
    db.flush()
    for permission_id in sorted(set(payload.permission_ids)):
        db.add(RolePermission(role_id=role.id, permission_id=permission_id))
    db.commit()
    return {"id": role.id}


@router.patch("/roles/{role_id}")
def role_patch(role_id: int, payload: RoleUpdate, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "roles.edit")
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="role_not_found")
    data = payload.model_dump(exclude_unset=True)
    for key in ["name", "description", "is_active"]:
        if key in data:
            setattr(role, key, data[key])
    if payload.permission_ids is not None:
        db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
        for permission_id in sorted(set(payload.permission_ids)):
            db.add(RolePermission(role_id=role_id, permission_id=permission_id))
    db.commit()
    return {"ok": True}


@router.post("/roles/{role_id}/archive")
def role_archive(role_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "roles.archive")
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="role_not_found")
    role.is_archived = True
    role.is_active = False
    db.commit()
    return {"ok": True}


@router.delete("/roles/{role_id}")
def role_delete(role_id: int, db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "roles.delete")
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="role_not_found")
    if role.code == "SUPER_ADMIN":
        raise HTTPException(status_code=400, detail="role_protected")
    usage = get_role_usage(db, role_id)
    if usage:
        raise HTTPException(status_code=400, detail="role_used")
    db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
    db.delete(role)
    db.commit()
    return {"ok": True}


@router.get("/permissions")
def permissions(db: Session = Depends(get_db), current_user: UserContext = Depends(get_current_user)):
    require_permission(db, current_user.id, "roles.view")
    rows = list(db.scalars(select(Permission).order_by(Permission.module, Permission.action)))
    return [{"id": row.id, "module": row.module, "action": row.action, "code": row.code, "name": row.name} for row in rows]
