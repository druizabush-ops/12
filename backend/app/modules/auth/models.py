"""Модели хранения аутентификации и ролей.
Файл описывает технические таблицы пользователей, ролей и доступа к модулям.
Минимальность: только то, что нужно для входа и RBAC уровня модулей.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
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
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_organization_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


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


class RoleModulePermission(Base):
    """Тонкие права роли внутри модуля.
    Хранит именованные permission-флаги на уровне роль+модуль.
    """

    __tablename__ = "auth_role_module_permissions"

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
    permission: Mapped[str] = mapped_column(String(64), primary_key=True)
    is_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
