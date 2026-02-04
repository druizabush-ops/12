"""HTTP API платформенного реестра модулей.
BLOCK 13 вводит единый реестр, поэтому UI модулей здесь не описывается.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.context import UserContext
from app.core.security import get_current_user
from app.modules.auth.service import get_db
from app.modules.module_registry.schemas import ModuleDto, ModuleOrderUpdate, ModulePrimaryUpdate
from app.modules.module_registry.service import (
    list_modules_with_access,
    reorder_modules,
    set_primary_module,
)

router = APIRouter(
    prefix="/modules",
    tags=["modules"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[ModuleDto])
def get_modules(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ModuleDto]:
    """Возвращает модули с флагом доступа для текущего пользователя.
    Backend вычисляет доступ по ролям и остаётся источником истины.
    """

    return list_modules_with_access(db, current_user.id)


@router.patch("/primary", response_model=list[ModuleDto])
def update_primary_module(
    payload: ModulePrimaryUpdate,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ModuleDto]:
    """Назначает основной модуль или сбрасывает его.
    Только один модуль может иметь флаг is_primary.
    """

    try:
        set_primary_module(db, payload.module_id)
        return list_modules_with_access(db, current_user.id)
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
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ModuleDto]:
    """Обновляет порядок всех модулей.
    backend остаётся источником истины для списка.
    """

    try:
        reorder_modules(db, payload.ordered_ids)
        return list_modules_with_access(db, current_user.id)
    except ValueError as exc:
        if str(exc) in {"duplicate_ids", "incomplete_ids"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ordered ids must include all modules without duplicates",
            )
        raise
