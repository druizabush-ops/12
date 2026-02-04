"""RBAC для доступа к модулям.
Добавляет роли и связи пользователей с модулями (BLOCK 16).
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_module_access_control"
down_revision = "0002_platform_modules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создаёт таблицы ролей и связей доступа к модулям."""

    op.create_table(
        "auth_roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("can_manage_access", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "auth_user_roles",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("auth_users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            sa.Integer(),
            sa.ForeignKey("auth_roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "auth_role_modules",
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
    )

    roles_table = sa.table(
        "auth_roles",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("can_manage_access", sa.Boolean),
    )

    op.bulk_insert(
        roles_table,
        [
            {"id": 1, "name": "admin", "can_manage_access": True},
            {"id": 2, "name": "employee", "can_manage_access": False},
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
            {"role_id": 1, "module_id": "help"},
            {"role_id": 2, "module_id": "help"},
        ],
    )

    op.execute(
        sa.text(
            "INSERT INTO auth_user_roles (user_id, role_id) "
            "SELECT id, 2 FROM auth_users"
        )
    )


def downgrade() -> None:
    """Откатывает таблицы ролей и связей доступа к модулям."""

    op.drop_table("auth_role_modules")
    op.drop_table("auth_user_roles")
    op.drop_table("auth_roles")
