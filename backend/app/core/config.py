"""Минимальная конфигурация приложения.
Файл нужен для чтения базовых настроек из окружения.
Минимальность — только то, что требуется для соединения с БД.
"""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Контейнер настроек.
    Содержит только обязательные параметры для bootstrap.
    """

    database_url: str
    environment: str


settings = Settings(
    database_url=os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/core_platform",
    ),
    environment=os.getenv("ENVIRONMENT", "local"),
)


def validate_required_envs() -> None:
    """Проверка обязательных переменных окружения.
    Нужна при старте, чтобы платформа не запускалась в некорректной конфигурации.
    Fail-fast важнее, чем скрытые runtime-ошибки внутри endpoint'ов.
    """

    # AUTH_SECRET_KEY обязателен для корректной инициализации auth и защиты токенов.
    # DATABASE_URL обязателен для подключения к базе данных на старте.
    required_vars = ("AUTH_SECRET_KEY", "DATABASE_URL")
    missing = [name for name in required_vars if not os.getenv(name)]
    if missing:
        missing_list = ", ".join(missing)
        raise RuntimeError(
            "Отсутствуют обязательные переменные окружения: "
            f"{missing_list}. Запуск backend остановлен из-за некорректной конфигурации."
        )
