"""Расширение tasks: recurring engine и task folders."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0008_tasks_engine_v71"
down_revision = "0007_tasks_module_mvp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("tasks", sa.Column("recurrence_type", sa.String(length=16), nullable=True))
    op.add_column("tasks", sa.Column("recurrence_interval", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("recurrence_days_of_week", sa.JSON(), nullable=True))
    op.add_column("tasks", sa.Column("recurrence_end_date", sa.Date(), nullable=True))
    op.add_column("tasks", sa.Column("recurrence_master_task_id", sa.String(length=36), nullable=True))
    op.add_column("tasks", sa.Column("recurrence_state", sa.String(length=16), nullable=True))
    op.add_column("tasks", sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_foreign_key(
        "fk_tasks_recurrence_master_task_id",
        "tasks",
        "tasks",
        ["recurrence_master_task_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_tasks_recurrence_master", "tasks", ["recurrence_master_task_id"])

    op.create_table(
        "task_folders",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filter_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_task_folders_created_by_user_id", "task_folders", ["created_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_task_folders_created_by_user_id", table_name="task_folders")
    op.drop_table("task_folders")

    op.drop_index("ix_tasks_recurrence_master", table_name="tasks")
    op.drop_constraint("fk_tasks_recurrence_master_task_id", "tasks", type_="foreignkey")
    op.drop_column("tasks", "is_hidden")
    op.drop_column("tasks", "recurrence_state")
    op.drop_column("tasks", "recurrence_master_task_id")
    op.drop_column("tasks", "recurrence_end_date")
    op.drop_column("tasks", "recurrence_days_of_week")
    op.drop_column("tasks", "recurrence_interval")
    op.drop_column("tasks", "recurrence_type")
    op.drop_column("tasks", "is_recurring")
