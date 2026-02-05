from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.auth.models import Role, RoleModule, RoleModulePermission, User, UserRole
from app.modules.admin_access.schemas import PermissionItem
from app.modules.module_registry.models import PlatformModule

DEFAULT_PERMISSIONS_BY_MODULE: dict[str, list[str]] = {
    "admin": ["view", "create", "edit", "delete"],
}


def user_can_manage_access(db: Session, user_id: int) -> bool:
    role_ids = select(UserRole.role_id).where(UserRole.user_id == user_id)
    return bool(
        db.scalar(
            select(Role.id)
            .where(Role.id.in_(role_ids))
            .where(Role.can_manage_access.is_(True))
            .limit(1)
        )
    )


def list_roles(db: Session) -> list[dict]:
    roles = list(db.scalars(select(Role).order_by(Role.name)))
    module_rows = db.execute(select(RoleModule.role_id, RoleModule.module_id)).all()

    module_ids_by_role: dict[int, list[str]] = {}
    for role_id, module_id in module_rows:
        module_ids_by_role.setdefault(role_id, []).append(module_id)

    return [
        {
            "id": role.id,
            "name": role.name,
            "can_manage_access": role.can_manage_access,
            "module_ids": sorted(module_ids_by_role.get(role.id, [])),
        }
        for role in roles
    ]


def _module_permission_catalog(db: Session, module_id: str) -> list[str]:
    known = set(DEFAULT_PERMISSIONS_BY_MODULE.get(module_id, []))
    db_known = db.scalars(
        select(RoleModulePermission.permission)
        .where(RoleModulePermission.module_id == module_id)
        .distinct()
    ).all()
    known.update(db_known)
    return sorted(known)


def create_role(db: Session, name: str) -> dict:
    role = Role(name=name.strip(), can_manage_access=False)
    db.add(role)
    db.flush()

    modules = list(db.scalars(select(PlatformModule.id)))
    for module_id in modules:
        db.add(RoleModule(role_id=role.id, module_id=module_id))
        for permission in _module_permission_catalog(db, module_id):
            db.add(
                RoleModulePermission(
                    role_id=role.id,
                    module_id=module_id,
                    permission=permission,
                    is_allowed=True,
                )
            )

    db.commit()
    db.refresh(role)
    return {
        "id": role.id,
        "name": role.name,
        "can_manage_access": role.can_manage_access,
        "module_ids": sorted(modules),
    }


def delete_role(db: Session, role_id: int) -> None:
    role = db.get(Role, role_id)
    if not role:
        raise ValueError("role_not_found")
    db.delete(role)
    db.commit()


def update_module_access(db: Session, role_id: int, module_id: str, has_access: bool) -> None:
    role = db.get(Role, role_id)
    module = db.get(PlatformModule, module_id)
    if not role or not module:
        raise ValueError("role_or_module_not_found")

    existing = db.get(RoleModule, {"role_id": role_id, "module_id": module_id})
    if has_access and not existing:
        db.add(RoleModule(role_id=role_id, module_id=module_id))
    if not has_access and existing:
        db.delete(existing)
    db.commit()


def get_role_module_permissions(db: Session, role_id: int, module_id: str) -> dict:
    role = db.get(Role, role_id)
    module = db.get(PlatformModule, module_id)
    if not role or not module:
        raise ValueError("role_or_module_not_found")

    known = _module_permission_catalog(db, module_id)
    rows = db.execute(
        select(RoleModulePermission.permission, RoleModulePermission.is_allowed).where(
            RoleModulePermission.role_id == role_id,
            RoleModulePermission.module_id == module_id,
        )
    ).all()
    state = {permission: bool(is_allowed) for permission, is_allowed in rows}

    return {
        "role_id": role_id,
        "module_id": module_id,
        "permissions": [
            {"name": permission, "is_allowed": state.get(permission, True)} for permission in known
        ],
    }


def update_role_module_permissions(
    db: Session,
    role_id: int,
    module_id: str,
    permissions: list[PermissionItem],
) -> None:
    role = db.get(Role, role_id)
    module = db.get(PlatformModule, module_id)
    if not role or not module:
        raise ValueError("role_or_module_not_found")

    db.execute(
        delete(RoleModulePermission).where(
            RoleModulePermission.role_id == role_id,
            RoleModulePermission.module_id == module_id,
        )
    )

    for item in permissions:
        db.add(
            RoleModulePermission(
                role_id=role_id,
                module_id=module_id,
                permission=item.name,
                is_allowed=item.is_allowed,
            )
        )

    db.commit()


def list_platform_modules(db: Session) -> list[dict]:
    modules = list(db.scalars(select(PlatformModule).order_by(PlatformModule.order)))
    return [{"id": item.id, "title": item.title} for item in modules]


def list_users_with_roles(db: Session) -> list[dict]:
    users = list(db.scalars(select(User).order_by(User.username)))
    rows = db.execute(select(UserRole.user_id, UserRole.role_id)).all()
    roles_by_user: dict[int, list[int]] = {}
    for user_id, role_id in rows:
        roles_by_user.setdefault(user_id, []).append(role_id)

    return [
        {"id": user.id, "username": user.username, "role_ids": sorted(roles_by_user.get(user.id, []))}
        for user in users
    ]


def update_user_roles(db: Session, user_id: int, role_ids: list[int]) -> None:
    user = db.get(User, user_id)
    if not user:
        raise ValueError("user_not_found")

    existing_role_ids = set(db.scalars(select(Role.id)).all())
    if any(role_id not in existing_role_ids for role_id in role_ids):
        raise ValueError("role_not_found")

    db.execute(delete(UserRole).where(UserRole.user_id == user_id))
    for role_id in sorted(set(role_ids)):
        db.add(UserRole(user_id=user_id, role_id=role_id))
    db.commit()


def list_affected_users(db: Session, role_ids: list[int]) -> list[dict]:
    if not role_ids:
        return []

    rows = db.execute(
        select(User.id, User.username)
        .join(UserRole, UserRole.user_id == User.id)
        .where(UserRole.role_id.in_(role_ids))
        .distinct()
        .order_by(User.username)
    ).all()

    return [{"id": user_id, "username": username} for user_id, username in rows]
