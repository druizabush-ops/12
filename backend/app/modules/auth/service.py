"""Сервисный слой аутентификации.
Файл нужен для работы с БД и отделения логики от API.
Минимальность: только операции регистрации, логина и чтения пользователя.
"""

from __future__ import annotations

from typing import Generator

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.db import get_engine
from app.modules.auth.models import Role, User, UserRole
from app.modules.auth.models import RoleModule, RoleModulePermission
from app.modules.module_registry.models import PlatformModule
from app.modules.auth.security import hash_password, verify_password

# Импорт Base удалён, потому что схемой управляют миграции, а лишний импорт вводит в заблуждение.
engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
DEFAULT_ROLE_NAME = "employee"
SUPER_ADMIN_ROLE_NAME = "SUPER_ADMIN"


def _ensure_system_rbac_seed(db: Session) -> None:
    """Гарантирует системный bootstrap RBAC без ручного SQL в БД."""

    super_admin_role = db.scalar(select(Role).where(Role.name == SUPER_ADMIN_ROLE_NAME))
    if super_admin_role is None:
        super_admin_role = Role(name=SUPER_ADMIN_ROLE_NAME, can_manage_access=True)
        db.add(super_admin_role)
        db.flush()

    module_ids = list(db.scalars(select(PlatformModule.id)))
    for module_id in module_ids:
        link_exists = db.scalar(
            select(RoleModule.role_id).where(
                RoleModule.role_id == super_admin_role.id,
                RoleModule.module_id == module_id,
            )
        )
        if link_exists is None:
            db.add(RoleModule(role_id=super_admin_role.id, module_id=module_id))

    module_permissions: dict[str, list[str]] = {
        "admin": ["view", "create", "edit", "delete"],
        "employees": [
            "users.view",
            "users.create",
            "users.edit",
            "users.archive",
            "users.set_password",
            "orgstructure.view",
            "orgstructure.edit",
            "roles.view",
            "roles.create",
            "roles.edit",
            "roles.archive",
            "roles.delete",
            "organizations.switch",
            "organizations.manage",
            "admin.view",
            "employees.view",
        ],
    }

    for module_id, permissions in module_permissions.items():
        for permission in permissions:
            entry_exists = db.scalar(
                select(RoleModulePermission.role_id).where(
                    RoleModulePermission.role_id == super_admin_role.id,
                    RoleModulePermission.module_id == module_id,
                    RoleModulePermission.permission == permission,
                )
            )
            if entry_exists is None:
                db.add(
                    RoleModulePermission(
                        role_id=super_admin_role.id,
                        module_id=module_id,
                        permission=permission,
                        is_allowed=True,
                    )
                )

    admin_user = db.scalar(select(User).where(User.username == "admin"))
    if admin_user is not None:
        has_super_admin = db.scalar(
            select(UserRole.user_id).where(
                UserRole.user_id == admin_user.id,
                UserRole.role_id == super_admin_role.id,
            )
        )
        if has_super_admin is None:
            db.add(UserRole(user_id=admin_user.id, role_id=super_admin_role.id))

    db.commit()


def init_auth_storage() -> None:
    """Оставлен для совместимости старта приложения.
    Схема БД теперь управляется только миграциями Alembic, поэтому здесь ничего не создаётся.
    """

    # Схема фиксируется миграциями, а runtime не должен создавать таблицы.
    # Разрешён только безопасный idempotent bootstrap данных RBAC.
    db = SessionLocal()
    try:
        _ensure_system_rbac_seed(db)
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """Возвращает сессию базы данных.
    Нужна для доступа к таблице пользователей в API.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_username(db: Session, username: str) -> User | None:
    """Ищет пользователя по логину.
    Нужен для регистрации и логина.
    """

    return db.scalar(select(User).where(User.username == username))


def create_user(db: Session, username: str, password: str) -> User:
    """Создаёт пользователя.
    Хранит только хэш пароля и логин.
    """

    user = User(username=username, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    assign_default_role(db, user.id)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Проверяет логин и пароль.
    Возвращает пользователя при успешной проверке.
    """

    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Ищет пользователя по id.
    Используется при восстановлении текущего пользователя из токена.
    """

    return db.get(User, user_id)


def assign_default_role(db: Session, user_id: int) -> None:
    """Назначает роль по умолчанию новому пользователю."""

    role_id = db.scalar(select(Role.id).where(Role.name == DEFAULT_ROLE_NAME))
    if role_id is None:
        return None
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.commit()
