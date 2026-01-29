"""Начальная схема для auth-модуля.
Создаёт таблицу пользователей, необходимую для работы регистрации и логина.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создаёт базовую таблицу пользователей."""

    op.create_table(
        "auth_users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
    )
    op.create_index(
        "ix_auth_users_username",
        "auth_users",
        ["username"],
        unique=True,
    )


def downgrade() -> None:
    """Откатывает начальную таблицу пользователей."""

    op.drop_index("ix_auth_users_username", table_name="auth_users")
    op.drop_table("auth_users")
