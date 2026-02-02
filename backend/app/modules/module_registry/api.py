"""HTTP API платформенного реестра модулей.
BLOCK 13 вводит единый реестр, поэтому UI модулей здесь не описывается.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.modules.auth.service import get_db
from app.modules.module_registry.schemas import ModuleDto, ModuleOrderUpdate, ModulePrimaryUpdate
from app.modules.module_registry.service import list_modules, reorder_modules, set_primary_module

router = APIRouter(
    prefix="/modules",
    tags=["modules"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[ModuleDto])
def get_modules(db: Session = Depends(get_db)) -> list[ModuleDto]:
    """Возвращает доступные модули для текущего пользователя.
    На этом этапе доступ = все модули, без RBAC и бизнес-логики.
    """

    return list_modules(db)


@router.patch("/primary", response_model=list[ModuleDto])
def update_primary_module(
    payload: ModulePrimaryUpdate,
    db: Session = Depends(get_db),
) -> list[ModuleDto]:
    """Назначает основной модуль или сбрасывает его.
    Только один модуль может иметь флаг is_primary.
    """

    try:
        return set_primary_module(db, payload.module_id)
    except ValueError as exc:
        if str(exc) == "module_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found",
            )
        raise


@router.patch("/order", response_model=list[ModuleDto])
def update_modules_order(
    payload: ModuleOrderUpdate,
    db: Session = Depends(get_db),
) -> list[ModuleDto]:
    """Обновляет порядок всех модулей.
    backend остаётся источником истины для списка.
    """

    try:
        return reorder_modules(db, payload.ordered_ids)
    except ValueError as exc:
        if str(exc) in {"duplicate_ids", "incomplete_ids"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ordered ids must include all modules without duplicates",
            )
        raise
