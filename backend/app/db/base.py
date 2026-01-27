"""Единый базовый класс ORM.
Файл нужен, чтобы собрать metadata моделей для миграций.
Минимальность: только общий Base без дополнительной логики.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Общий базовый класс для всех моделей.
    Он существует исключительно для общей metadata в Alembic.
    """
