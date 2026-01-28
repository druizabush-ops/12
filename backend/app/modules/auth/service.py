"""Сервисный слой аутентификации.
Файл нужен для работы с БД и отделения логики от API.
Минимальность: только операции регистрации, логина и чтения пользователя.
"""

from __future__ import annotations

from typing import Generator

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.db import get_engine
from app.modules.auth.models import User
from app.modules.auth.security import hash_password, verify_password

engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


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
