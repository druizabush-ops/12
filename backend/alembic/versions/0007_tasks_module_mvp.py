"""Добавляет модуль задач и таблицы хранения задач (MVP)."""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007_tasks_module_mvp"
down_revision = "0006_event_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("due_time", sa.Time(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("urgency", sa.String(length=32), nullable=False),
        sa.Column("requires_verification", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verifier_user_id", sa.Integer(), sa.ForeignKey("auth_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_type", sa.String(length=128), nullable=True),
        sa.Column("source_id", sa.String(length=128), nullable=True),
    )
    op.create_index("ix_tasks_due_date", "tasks", ["due_date"])
    op.create_index("ix_tasks_due_at", "tasks", ["due_at"])
    op.create_index("ix_tasks_status", "tasks", ["status"])

    op.create_table(
        "task_assignees",
        sa.Column("task_id", sa.String(length=36), sa.ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("auth_users.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_task_assignees_user_id", "task_assignees", ["user_id"])

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
                "id": "tasks",
                "name": "tasks",
                "title": "Задачи",
                "path": "tasks",
                "order": 2,
                "is_primary": False,
            }
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
            {"role_id": 1, "module_id": "tasks"},
            {"role_id": 2, "module_id": "tasks"},
        ],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM auth_role_modules WHERE module_id = 'tasks'"))
    op.execute(sa.text("DELETE FROM platform_modules WHERE id = 'tasks'"))

    op.drop_index("ix_task_assignees_user_id", table_name="task_assignees")
    op.drop_table("task_assignees")

    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_due_at", table_name="tasks")
    op.drop_index("ix_tasks_due_date", table_name="tasks")
    op.drop_table("tasks")
