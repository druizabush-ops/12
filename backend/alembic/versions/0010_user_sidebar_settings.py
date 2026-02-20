"""Add user sidebar settings storage."""

from alembic import op
import sqlalchemy as sa


revision = "0010_user_sidebar_settings"
down_revision = "0009_tasks_multi_verifiers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_sidebar_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("modules_order", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["auth_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_user_sidebar_settings_user_id"), "user_sidebar_settings", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_sidebar_settings_user_id"), table_name="user_sidebar_settings")
    op.drop_table("user_sidebar_settings")
