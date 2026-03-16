from __future__ import annotations

from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.auth.models import RoleModule, RoleModulePermission, UserRole
from app.modules.auth.security import hash_password
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

MODULE_ID = "employees"


def require_permission(db: Session, current_user_id: int, permission: str) -> None:
    role_ids = list(db.scalars(select(UserRole.role_id).where(UserRole.user_id == current_user_id)))
    if not role_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    has_module = db.scalar(
        select(RoleModule.role_id)
        .where(RoleModule.role_id.in_(role_ids), RoleModule.module_id == MODULE_ID)
        .limit(1)
    )
    if not has_module:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    allowed = db.scalar(
        select(RoleModulePermission.role_id)
        .where(
            RoleModulePermission.role_id.in_(role_ids),
            RoleModulePermission.module_id == MODULE_ID,
            RoleModulePermission.permission == permission,
            RoleModulePermission.is_allowed.is_(True),
        )
        .limit(1)
    )
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")


def list_users(db: Session, organization_id: int | None, search: str | None, archived: bool) -> list[dict]:
    stmt = select(User)
    if not archived:
        stmt = stmt.where(User.is_archived.is_(False))
    if search:
        stmt = stmt.where(User.full_name.ilike(f"%{search}%"))
    users = list(db.scalars(stmt.order_by(User.full_name)))

    org_map: dict[int, set[int]] = defaultdict(set)
    for user_id, org_id in db.execute(select(UserOrganization.user_id, UserOrganization.organization_id)).all():
        org_map[user_id].add(org_id)

    position_rows = db.execute(
        select(UserPosition.user_id, Position.name, Position.organization_id)
        .join(Position, Position.id == UserPosition.position_id)
    ).all()
    positions_map: dict[int, list[str]] = defaultdict(list)
    for user_id, pos_name, org_id in position_rows:
        if organization_id is None or organization_id == org_id:
            positions_map[user_id].append(pos_name)

    result: list[dict] = []
    for user in users:
        if organization_id is not None and organization_id not in org_map.get(user.id, set()):
            continue
        result.append(
            {
                "id": user.id,
                "full_name": user.full_name,
                "login": user.login,
                "phone": user.phone,
                "is_active": user.is_active,
                "is_archived": user.is_archived,
                "created_at": user.created_at,
                "positions": sorted(positions_map.get(user.id, [])),
            }
        )
    return result


def create_user(db: Session, payload) -> User:
    exists = db.scalar(select(User.id).where(User.login == payload.login))
    if exists is not None:
        raise HTTPException(status_code=400, detail="login_exists")

    user = User(
        full_name=payload.full_name,
        login=payload.login,
        password_hash=hash_password(payload.password),
        phone=payload.phone,
    )
    db.add(user)
    db.flush()

    if payload.organization_ids:
        for org_id in sorted(set(payload.organization_ids)):
            db.add(UserOrganization(user_id=user.id, organization_id=org_id, is_active=True))

    if payload.position_ids:
        positions = list(db.scalars(select(Position).where(Position.id.in_(payload.position_ids))))
        org_ids = {item.organization_id for item in positions}
        if not org_ids.issubset(set(payload.organization_ids)):
            raise HTTPException(status_code=400, detail="position_org_mismatch")
        for position_id in sorted(set(payload.position_ids)):
            db.add(UserPosition(user_id=user.id, position_id=position_id))

    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, payload) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    for key in ["full_name", "phone", "is_active"]:
        value = getattr(payload, key)
        if value is not None:
            setattr(user, key, value)

    if payload.organization_ids is not None:
        db.execute(delete(UserOrganization).where(UserOrganization.user_id == user_id))
        for org_id in sorted(set(payload.organization_ids)):
            db.add(UserOrganization(user_id=user_id, organization_id=org_id, is_active=True))

    if payload.position_ids is not None:
        positions = list(db.scalars(select(Position).where(Position.id.in_(payload.position_ids))))
        org_ids = set(db.scalars(select(UserOrganization.organization_id).where(UserOrganization.user_id == user_id)))
        if any(item.organization_id not in org_ids for item in positions):
            raise HTTPException(status_code=400, detail="position_org_mismatch")
        db.execute(delete(UserPosition).where(UserPosition.user_id == user_id))
        for position_id in sorted(set(payload.position_ids)):
            db.add(UserPosition(user_id=user_id, position_id=position_id))

    db.commit()
    db.refresh(user)
    return user


def get_effective_permissions(db: Session, user_id: int, organization_id: int) -> list[str]:
    rows = db.execute(
        select(Permission.code)
        .select_from(UserPosition)
        .join(Position, Position.id == UserPosition.position_id)
        .join(PositionRole, PositionRole.position_id == Position.id)
        .join(RolePermission, RolePermission.role_id == PositionRole.role_id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(UserPosition.user_id == user_id, Position.organization_id == organization_id)
        .distinct()
    ).all()
    return sorted([code for code, in rows])


def get_user_managers(db: Session, user_id: int, organization_id: int) -> list[dict]:
    rows = db.execute(
        select(Position.id, Position.name, Position.manager_position_id, Group.head_user_id)
        .select_from(UserPosition)
        .join(Position, Position.id == UserPosition.position_id)
        .join(Group, Group.id == Position.group_id)
        .where(UserPosition.user_id == user_id, Position.organization_id == organization_id)
    ).all()
    result = []
    for position_id, position_name, manager_position_id, head_user_id in rows:
        manager_users: list[dict] = []
        if manager_position_id is not None:
            manager_users_rows = db.execute(
                select(User.id, User.full_name)
                .join(UserPosition, UserPosition.user_id == User.id)
                .where(UserPosition.position_id == manager_position_id)
            ).all()
            manager_users = [{"id": uid, "full_name": full_name} for uid, full_name in manager_users_rows]
        elif head_user_id is not None:
            head = db.get(User, head_user_id)
            if head:
                manager_users = [{"id": head.id, "full_name": head.full_name}]

        result.append({"position_id": position_id, "position_name": position_name, "managers": manager_users})
    return result


def validate_manager_cycle(db: Session, position_id: int, manager_position_id: int | None) -> None:
    if manager_position_id is None:
        return
    if manager_position_id == position_id:
        raise HTTPException(status_code=400, detail="self_manager_forbidden")

    visited: set[int] = set()
    current = manager_position_id
    while current is not None:
        if current in visited:
            raise HTTPException(status_code=400, detail="manager_cycle")
        visited.add(current)
        if current == position_id:
            raise HTTPException(status_code=400, detail="manager_cycle")
        current = db.scalar(select(Position.manager_position_id).where(Position.id == current))


def get_role_usage(db: Session, role_id: int) -> list[dict]:
    rows = db.execute(
        select(Position.id, Position.name, Organization.id, Organization.name)
        .select_from(PositionRole)
        .join(Position, Position.id == PositionRole.position_id)
        .join(Organization, Organization.id == Position.organization_id)
        .where(PositionRole.role_id == role_id)
    ).all()
    return [
        {
            "position_id": pid,
            "position_name": pname,
            "organization_id": oid,
            "organization_name": oname,
        }
        for pid, pname, oid, oname in rows
    ]
