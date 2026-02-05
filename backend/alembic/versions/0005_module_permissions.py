"""Добавляет тонкие права внутри модуля (BLOCK 19).
Создаёт таблицу permission-флагов на уровне роль+модуль.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0005_module_permissions"
down_revision = "0004_admin_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создаёт таблицу прав и добавляет базовые флаги для admin модуля."""

    op.create_table(
        "auth_role_module_permissions",
        sa.Column(
            "role_id",
            sa.Integer(),
            sa.ForeignKey("auth_roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "module_id",
            sa.String(length=64),
            sa.ForeignKey("platform_modules.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("permission", sa.String(length=64), primary_key=True),
        sa.Column("is_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    permissions_table = sa.table(
        "auth_role_module_permissions",
        sa.column("role_id", sa.Integer),
        sa.column("module_id", sa.String),
        sa.column("permission", sa.String),
        sa.column("is_allowed", sa.Boolean),
    )

    op.bulk_insert(
        permissions_table,
        [
            {"role_id": 1, "module_id": "admin", "permission": "view", "is_allowed": True},
            {"role_id": 1, "module_id": "admin", "permission": "create", "is_allowed": True},
            {"role_id": 1, "module_id": "admin", "permission": "edit", "is_allowed": True},
            {"role_id": 1, "module_id": "admin", "permission": "delete", "is_allowed": True},
        ],
    )


def downgrade() -> None:
    """Откатывает таблицу прав внутри модуля."""

    op.drop_table("auth_role_module_permissions")
