"""Сервис работы с платформенным реестром модулей.
Логика вынесена сюда, чтобы API оставался тонким слоем.
Backend остаётся источником истины о состоянии модулей.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.module_registry.models import PlatformModule


def list_modules(db: Session) -> list[PlatformModule]:
    """Возвращает модули в порядке order.
    В BLOCK 13 это единственный источник истины для frontend.
    """

    return list(db.scalars(select(PlatformModule).order_by(PlatformModule.order)))


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
