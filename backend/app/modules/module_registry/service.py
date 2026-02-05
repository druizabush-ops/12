"""Сервис работы с платформенным реестром модулей.
Логика вынесена сюда, чтобы API оставался тонким слоем.
Backend остаётся источником истины о состоянии модулей.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import RoleModule, RoleModulePermission, UserRole
from app.modules.module_registry.models import PlatformModule


def list_modules(db: Session) -> list[PlatformModule]:
    """Возвращает модули в порядке order.
    В BLOCK 13 это единственный источник истины для frontend.
    """

    return list(db.scalars(select(PlatformModule).order_by(PlatformModule.order)))


def _build_permissions_map(db: Session, role_ids: list[int]) -> dict[str, dict[str, bool]]:
    """Строит карту permissions по module_id с OR-агрегацией по ролям."""

    if not role_ids:
        return {}

    rows = db.execute(
        select(
            RoleModulePermission.module_id,
            RoleModulePermission.permission,
            RoleModulePermission.is_allowed,
        ).where(RoleModulePermission.role_id.in_(role_ids))
    ).all()

    permissions_by_module: dict[str, dict[str, bool]] = {}
    for module_id, permission, is_allowed in rows:
        module_permissions = permissions_by_module.setdefault(module_id, {})
        module_permissions[permission] = module_permissions.get(permission, False) or bool(is_allowed)

    return permissions_by_module


def list_modules_with_access(db: Session, user_id: int) -> list[dict]:
    """Возвращает модули с флагом доступа и permissions по ролям пользователя."""

    modules = list_modules(db)
    role_ids = list(db.scalars(select(UserRole.role_id).where(UserRole.user_id == user_id)))
    permissions_by_module = _build_permissions_map(db, role_ids)

    if not role_ids:
        return [
            {
                "id": module.id,
                "name": module.name,
                "title": module.title,
                "path": module.path,
                "order": module.order,
                "is_primary": module.is_primary,
                "has_access": False,
                "permissions": {},
            }
            for module in modules
        ]

    accessible_ids = set(
        db.scalars(select(RoleModule.module_id).where(RoleModule.role_id.in_(role_ids))).all()
    )

    return [
        {
            "id": module.id,
            "name": module.name,
            "title": module.title,
            "path": module.path,
            "order": module.order,
            "is_primary": module.is_primary,
            "has_access": module.id in accessible_ids,
            "permissions": permissions_by_module.get(module.id, {}),
        }
        for module in modules
    ]


def set_primary_module(db: Session, module_id: str | None) -> list[PlatformModule]:
    """Обновляет основной модуль.
    При module_id=None снимает флаг со всех модулей.
    """

    modules = list(db.scalars(select(PlatformModule)))
    if module_id is None:
        for module in modules:
            module.is_primary = False
        db.commit()
        return list_modules(db)

    target = next((module for module in modules if module.id == module_id), None)
    if not target:
        raise ValueError("module_not_found")

    for module in modules:
        module.is_primary = module.id == module_id
    db.commit()
    return list_modules(db)


def reorder_modules(db: Session, ordered_ids: list[str]) -> list[PlatformModule]:
    """Обновляет порядок всех модулей.
    ordered_ids должен содержать полный список модулей без повторов.
    """

    modules = list(db.scalars(select(PlatformModule)))
    module_ids = {module.id for module in modules}
    ordered_set = set(ordered_ids)

    if len(ordered_ids) != len(ordered_set):
        raise ValueError("duplicate_ids")

    if module_ids != ordered_set:
        raise ValueError("incomplete_ids")

    modules_by_id = {module.id: module for module in modules}
    for index, module_id in enumerate(ordered_ids):
        modules_by_id[module_id].order = index

    db.commit()
    return list_modules(db)
