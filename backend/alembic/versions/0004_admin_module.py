"""Добавляет закрытый модуль admin.
Создаёт запись в platform_modules и выдаёт доступ только роли admin.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004_admin_module"
down_revision = "0003_module_access_control"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Добавляет admin модуль и доступ только для роли admin."""

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
                "id": "admin",
                "name": "admin",
                "title": "Администрирование",
                "path": "admin",
                "order": 1,
                "is_primary": False,
            },
        ],
    )

    role_modules_table = sa.table(
        "auth_role_modules",
        sa.column("role_id", sa.Integer),
        sa.column("module_id", sa.String),
    )

    op.bulk_insert(
        role_modules_table,
        [
            {"role_id": 1, "module_id": "admin"},
        ],
    )


def downgrade() -> None:
    """Удаляет admin модуль и доступ."""

    op.execute(sa.text("DELETE FROM auth_role_modules WHERE module_id = 'admin'"))
    op.execute(sa.text("DELETE FROM platform_modules WHERE id = 'admin'"))
