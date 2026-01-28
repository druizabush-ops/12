"""Минимальное приложение FastAPI.
Файл существует для запуска сервера и проверки health-check.
Минимальность сохраняет только один маршрут и подключение к БД без бизнес-логики.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings, validate_required_envs
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

    # Проверка конфигурации выполняется при старте, чтобы остановить запуск при отсутствии env.
    # Fail-fast предотвращает скрытые ошибки в runtime и упрощает диагностику.
    validate_required_envs()
    _init_db()
    init_auth_storage()


@app.get("/health")
def health() -> dict[str, str]:
    """Простой endpoint проверки состояния.
    Он существует для внешнего мониторинга и максимально прост.
    """

    # /health не ходит в БД, потому что это liveness-сигнал процесса, а не проверка зависимостей.
    return {"status": "ok", "environment": settings.environment}


@app.get("/ready")
def ready() -> JSONResponse:
    """Проверка готовности сервиса работать с зависимостями."""

    # /ready ходит в БД, потому что readiness должен подтверждать доступность зависимостей.
    engine = get_engine()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        # 503 выбран, потому что сервис жив, но не готов обслуживать запросы.
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": f"База данных недоступна: {exc}"},
        )

    return JSONResponse(status_code=200, content={"status": "ready"})
