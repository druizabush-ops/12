"""Минимальный модуль работы с базой данных.
Он существует для создания подключения без моделей и миграций.
Минимальность ограничена только настройкой engine.
"""

from sqlalchemy import Engine, create_engine

from app.core.config import settings


def get_engine() -> Engine:
    """Создаёт SQLAlchemy engine.
    Это базовое подключение для проверки доступности БД.
    """

    return create_engine(settings.database_url, pool_pre_ping=True)
