"""Платформенный реестр модулей.
Создаёт таблицу platform_modules для BLOCK 13.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_platform_modules"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создаёт таблицу реестра модулей платформы."""

    op.create_table(
        "platform_modules",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    modules_table = sa.table(
        "platform_modules",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("title", sa.String),
        sa.column("path", sa.String),
        sa.column("order", sa.Integer),
        sa.column("is_primary", sa.Boolean),
    )

    op.bulk_insert(
        modules_table,
        [
            {
                "id": "help",
                "name": "help",
                "title": "Инструкция",
                "path": "help",
                "order": 0,
                "is_primary": True,
            },
            {
                "id": "admin",
                "name": "admin",
                "title": "Администрирование",
                "path": "admin",
                "order": 1,
                "is_primary": False,
            },
        ],
    )


def downgrade() -> None:
    """Откатывает таблицу реестра модулей платформы."""

    op.drop_table("platform_modules")
