"""Tasks engine production rewrite."""

from alembic import op
import sqlalchemy as sa


revision = "0008_tasks_engine_rewrite"
down_revision = "0007_tasks_module_mvp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_folders",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("show_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("show_overdue", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("show_done", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_task_folders_created_by_user_id", "task_folders", ["created_by_user_id"])

    op.add_column("tasks", sa.Column("folder_id", sa.String(length=36), nullable=True))
    op.add_column("tasks", sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("tasks", sa.Column("recurrence_type", sa.String(length=16), nullable=True))
    op.add_column("tasks", sa.Column("recurrence_interval", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("recurrence_days_of_week", sa.String(length=32), nullable=True))
    op.add_column("tasks", sa.Column("recurrence_end_date", sa.Date(), nullable=True))
    op.add_column("tasks", sa.Column("recurrence_master_task_id", sa.String(length=36), nullable=True))
    op.add_column("tasks", sa.Column("recurrence_state", sa.String(length=16), nullable=False, server_default="active"))
    op.add_column("tasks", sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_foreign_key("fk_tasks_folder_id", "tasks", "task_folders", ["folder_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key(
        "fk_tasks_recurrence_master_task_id",
        "tasks",
        "tasks",
        ["recurrence_master_task_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_tasks_folder_id", "tasks", ["folder_id"])
    op.create_index("ix_tasks_recurrence_master_task_id", "tasks", ["recurrence_master_task_id"])


def downgrade() -> None:
    op.drop_index("ix_tasks_recurrence_master_task_id", table_name="tasks")
    op.drop_index("ix_tasks_folder_id", table_name="tasks")
    op.drop_constraint("fk_tasks_recurrence_master_task_id", "tasks", type_="foreignkey")
    op.drop_constraint("fk_tasks_folder_id", "tasks", type_="foreignkey")

    op.drop_column("tasks", "is_hidden")
    op.drop_column("tasks", "recurrence_state")
    op.drop_column("tasks", "recurrence_master_task_id")
    op.drop_column("tasks", "recurrence_end_date")
    op.drop_column("tasks", "recurrence_days_of_week")
    op.drop_column("tasks", "recurrence_interval")
    op.drop_column("tasks", "recurrence_type")
    op.drop_column("tasks", "is_recurring")
    op.drop_column("tasks", "folder_id")

    op.drop_index("ix_task_folders_created_by_user_id", table_name="task_folders")
    op.drop_table("task_folders")
