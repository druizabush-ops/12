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
