from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.user_sidebar_settings.models import UserSidebarSettings


def get_sidebar_settings(db: Session, user_id: int) -> UserSidebarSettings | None:
    return db.scalar(select(UserSidebarSettings).where(UserSidebarSettings.user_id == user_id))


def upsert_modules_order(db: Session, user_id: int, modules_order: list[str]) -> UserSidebarSettings:
    settings = get_sidebar_settings(db, user_id)
    if settings is None:
        settings = UserSidebarSettings(user_id=user_id, modules_order=modules_order)
        db.add(settings)
    else:
        settings.modules_order = modules_order

    db.commit()
    db.refresh(settings)
    return settings
