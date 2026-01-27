"""Начальная миграция схемы.
Файл нужен, чтобы формализовать таблицу пользователей для аутентификации.
Минимальность: создаётся только таблица auth_users без бизнес-расширений.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создаёт минимальную таблицу пользователей.
    Нужна для соответствия текущей модели авторизации.
    """

    op.create_table(
        "auth_users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.UniqueConstraint("username", name="uq_auth_users_username"),
    )
    op.create_index(
        "ix_auth_users_username",
        "auth_users",
        ["username"],
        unique=False,
    )


def downgrade() -> None:
    """Удаляет таблицу пользователей.
    Откат нужен только для ручных операций миграций.
    """

    op.drop_index("ix_auth_users_username", table_name="auth_users")
    op.drop_table("auth_users")
