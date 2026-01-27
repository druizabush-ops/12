"""Модели хранения аутентификации.
Файл существует, чтобы описать единственную техническую таблицу пользователей.
Минимальность: только id, логин и хэш пароля без дополнительных сущностей.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """Технический пользователь для входа.
    Включает только логин и хэш пароля без профилей и ролей.
    """

    __tablename__ = "auth_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
