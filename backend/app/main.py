"""Минимальное приложение FastAPI.
Файл существует для запуска сервера и проверки health-check.
Минимальность сохраняет только один маршрут и подключение к БД без бизнес-логики.
"""

from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.core.db import get_engine
from app.modules.auth.service import init_auth_storage
from app.modules.registry import include_module_routers

app = FastAPI(title="Core Platform Bootstrap")
include_module_routers(app)


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
    init_auth_storage()


@app.get("/health")
def health() -> dict[str, str]:
    """Простой endpoint проверки состояния.
    Он существует для внешнего мониторинга и максимально прост.
    """

    return {"status": "ok", "environment": settings.environment}
