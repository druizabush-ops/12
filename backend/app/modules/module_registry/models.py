"""Модель платформенного реестра модулей.
Файл фиксирует таблицу для хранения состояния модулей BLOCK 13.
UI модулей здесь не описывается: backend остаётся источником истины.
"""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlatformModule(Base):
    """Техническая сущность модуля платформы.
    Нужна только для хранения порядка и флага основного модуля.
    """

    __tablename__ = "platform_modules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
