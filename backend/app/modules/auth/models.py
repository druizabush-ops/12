"""Модели хранения аутентификации и ролей.
Файл описывает технические таблицы пользователей, ролей и доступа к модулям.
Минимальность: только то, что нужно для входа и RBAC уровня модулей.
"""

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """Технический пользователь для входа.
    Включает только логин и хэш пароля без профилей и бизнес-атрибутов.
    """

    __tablename__ = "auth_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))


class Role(Base):
    """Роль доступа к модулям платформы.
    Роль хранит флаг управления доступами для делегирования.
    """

    __tablename__ = "auth_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    can_manage_access: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class UserRole(Base):
    """Связь пользователей и ролей.
    Позволяет назначать несколько ролей одному пользователю.
    """

    __tablename__ = "auth_user_roles"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("auth_users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("auth_roles.id", ondelete="CASCADE"),
        primary_key=True,
    )


class RoleModule(Base):
    """Связь ролей и модулей.
    Определяет доступ к модулю по любой роли пользователя.
    """

    __tablename__ = "auth_role_modules"

    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("auth_roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    module_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("platform_modules.id", ondelete="CASCADE"),
        primary_key=True,
    )
