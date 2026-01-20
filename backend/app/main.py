"""Минимальное приложение FastAPI.
Файл существует для запуска сервера и проверки health-check.
Минимальность сохраняет только один маршрут и подключение к БД без бизнес-логики.
"""

from fastapi import FastAPI
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.db import get_engine

app = FastAPI(title="Core Platform Bootstrap")


def _init_db() -> None:
    """Инициализация подключения без создания моделей.
    Нужна только проверка доступности базы при старте.
    Минимальна, потому что никаких таблиц здесь не создаётся.
    """

    engine = get_engine()
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


@app.on_event("startup")
def on_startup() -> None:
    """Стартовая проверка подключения.
    Нужна для демонстрации запуска, без дополнительной логики.
    """

    _init_db()


@app.get("/health")
def health() -> dict[str, str]:
    """Простой endpoint проверки состояния.
    Он существует для внешнего мониторинга и максимально прост.
    """

    return {"status": "ok", "environment": settings.environment}
