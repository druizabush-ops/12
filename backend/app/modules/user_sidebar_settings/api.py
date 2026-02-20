from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.context import UserContext
from app.core.security import get_current_user
from app.modules.auth.service import get_db
from app.modules.user_sidebar_settings.schemas import SidebarModulesOrderUpdate, SidebarSettingsDto
from app.modules.user_sidebar_settings.service import get_sidebar_settings, upsert_modules_order

router = APIRouter(
    prefix="/user/sidebar-settings",
    tags=["user-sidebar-settings"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=SidebarSettingsDto)
def read_sidebar_settings(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SidebarSettingsDto:
    settings = get_sidebar_settings(db, current_user.id)
    if settings is None:
        return SidebarSettingsDto(modules_order=None)
    return SidebarSettingsDto(modules_order=settings.modules_order)


@router.put("/modules-order", response_model=SidebarSettingsDto)
def save_modules_order(
    payload: SidebarModulesOrderUpdate,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SidebarSettingsDto:
    if len(payload.modules_order) != len(set(payload.modules_order)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="modules_order contains duplicate ids",
        )

    settings = upsert_modules_order(db, current_user.id, payload.modules_order)
    return SidebarSettingsDto(modules_order=settings.modules_order)
