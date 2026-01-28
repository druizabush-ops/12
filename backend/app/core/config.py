"""Минимальная конфигурация приложения.
Файл нужен для чтения базовых настроек из окружения.
Минимальность — только то, что требуется для соединения с БД.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Контейнер настроек.
    Содержит только обязательные параметры для bootstrap.
    """

    database_url: str
    environment: str


settings = Settings(
    database_url=os.getenv("DATABASE_URL"),
    environment=os.getenv("ENVIRONMENT", "local"),
)


def _is_empty_env(value: str | None) -> bool:
    """Проверяет, задано ли значение env переменной.
    Пустая строка недопустима, потому что создаёт скрытые fallback'и в рантайме.
    """

    return value is None or value.strip() == ""


def validate_required_envs() -> None:
    """Проверка обязательных переменных окружения.
    Нужна при старте, чтобы платформа не запускалась в некорректной конфигурации.
    Fail-fast важнее, чем скрытые runtime-ошибки внутри endpoint'ов.
    """

    # AUTH_SECRET_KEY обязателен для корректной инициализации auth и защиты токенов.
    # DATABASE_URL обязателен для подключения к базе данных на старте.
    # Значения по умолчанию опасны: они маскируют проблему конфигурации.
    # Переменные окружения — единственный источник конфигурации для обязательных параметров.
    required_vars = ("AUTH_SECRET_KEY", "DATABASE_URL")
    missing = [
        name for name in required_vars if _is_empty_env(os.getenv(name))
    ]
    if missing:
        missing_list = ", ".join(missing)
        raise RuntimeError(
            "Отсутствуют обязательные переменные окружения: "
            f"{missing_list}. Запуск backend остановлен из-за некорректной конфигурации."
        )
