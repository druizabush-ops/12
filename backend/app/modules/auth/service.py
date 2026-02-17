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
from app.modules.auth.schemas import UserListItem
from app.modules.auth.security import hash_password, verify_password

# Импорт Base удалён, потому что схемой управляют миграции, а лишний импорт вводит в заблуждение.
engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
DEFAULT_ROLE_NAME = "employee"


def init_auth_storage() -> None:
    """Оставлен для совместимости старта приложения.
    Схема БД теперь управляется только миграциями Alembic, поэтому здесь ничего не создаётся.
    """

    # Схема фиксируется миграциями, а runtime не должен создавать таблицы.
    return None


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


def list_users_for_picker(db: Session) -> list[UserListItem]:
    users = list(db.scalars(select(User).order_by(User.username.asc())))
    return [UserListItem(id=user.id, full_name=user.username) for user in users]
