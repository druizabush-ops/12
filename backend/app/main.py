"""Минимальное приложение FastAPI.
Файл существует для запуска сервера и проверки health-check.
Минимальность сохраняет только один маршрут и подключение к БД без бизнес-логики.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings, validate_required_envs
from app.core.db import get_engine
from app.modules.auth.service import init_auth_storage
from app.modules.registry import include_module_routers

app = FastAPI(title="Core Platform Bootstrap")

# CORS нужен для браузерного frontend (http://localhost:5173), чтобы preflight OPTIONS проходил корректно.
# Это инфраструктурный middleware; архитектура BLOCK 11 и маршрутизация модулей не меняются.
# ВАЖНО: middleware добавляется ДО include_module_routers(app), иначе OPTIONS может возвращать 405.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

include_module_routers(app)
logger = logging.getLogger("startup")


def _init_db() -> None:
    """Инициализация подключения без создания моделей.
    Нужна только проверка доступности базы при старте.
    Минимальна, потому что никаких таблиц здесь не создаётся.
    """

    engine = get_engine()
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    # Проверка обязательной схемы нужна для fail-fast, если миграции не применены.
    # Runtime не создаёт таблицы, потому что схема управляется только Alembic.
    inspector = inspect(engine)
    if not inspector.has_table("auth_users"):
        raise RuntimeError(
            "Таблица auth_users не найдена. "
            "Перед запуском backend необходимо выполнить alembic upgrade head."
        )
    if not inspector.has_table("platform_modules"):
        raise RuntimeError(
            "Таблица platform_modules не найдена. "
            "Перед запуском backend необходимо выполнить alembic upgrade head."
        )
    if not inspector.has_table("auth_roles"):
        raise RuntimeError(
            "Таблица auth_roles не найдена. "
            "Перед запуском backend необходимо выполнить alembic upgrade head."
        )
    if not inspector.has_table("auth_user_roles"):
        raise RuntimeError(
            "Таблица auth_user_roles не найдена. "
            "Перед запуском backend необходимо выполнить alembic upgrade head."
        )
    if not inspector.has_table("auth_role_modules"):
        raise RuntimeError(
            "Таблица auth_role_modules не найдена. "
            "Перед запуском backend необходимо выполнить alembic upgrade head."
        )
    if not inspector.has_table("auth_role_module_permissions"):
        raise RuntimeError(
            "Таблица auth_role_module_permissions не найдена. "
            "Перед запуском backend необходимо выполнить alembic upgrade head."
        )


@app.on_event("startup")
def on_startup() -> None:
    """Стартовая проверка подключения.
    Нужна для демонстрации запуска, без дополнительной логики.
    """

    # Логирование ограничено только фазой старта, чтобы не шуметь в runtime.
    # Формат сообщений един для быстрой диагностики и поиска причины остановки.
    logger.info("STARTUP | начало запуска backend")

    # Проверка конфигурации выполняется при старте, чтобы остановить запуск при отсутствии env.
    # Fail-fast предотвращает скрытые ошибки в runtime и упрощает диагностику.
    try:
        validate_required_envs()
    except Exception as exc:
        logger.error("STARTUP | проверка конфигурации не пройдена: %s", exc)
        raise
    logger.info("STARTUP | проверка конфигурации успешна")

    # Проверка БД логируется, потому что это ключевая зависимость для старта сервиса.
    try:
        _init_db()
    except Exception as exc:
        logger.error("STARTUP | проверка БД не пройдена: %s", exc)
        raise
    logger.info("STARTUP | проверка БД успешна")

    # Инициализация auth-хранилища логируется как финальный шаг старта.
    try:
        init_auth_storage()
    except Exception as exc:
        logger.error(
            "STARTUP | инициализация auth-хранилища не пройдена: %s",
            exc,
        )
        raise

    logger.info("STARTUP | запуск backend завершён успешно")


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
