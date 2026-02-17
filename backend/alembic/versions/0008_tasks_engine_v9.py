"""Tasks engine v9 migration."""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0008_tasks_engine_v9"
down_revision = "0007_tasks_module_mvp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_tasks_due_at", table_name="tasks")
    op.drop_column("tasks", "due_at")
    op.drop_column("tasks", "urgency")
    op.drop_column("tasks", "requires_verification")

    op.add_column("tasks", sa.Column("priority", sa.String(length=32), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE tasks
            SET status = CASE
                WHEN status = 'done' THEN 'done'
                ELSE 'active'
            END
            """
        )
    )

    op.add_column("tasks", sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("tasks", sa.Column("recurrence_type", sa.String(length=32), nullable=True))
    op.add_column("tasks", sa.Column("recurrence_interval", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("recurrence_days_of_week", sa.String(length=32), nullable=True))
    op.add_column("tasks", sa.Column("recurrence_end_date", sa.Date(), nullable=True))
    op.add_column("tasks", sa.Column("recurrence_master_task_id", sa.String(length=36), nullable=True))
    op.add_column(
        "tasks",
        sa.Column("recurrence_state", sa.String(length=32), nullable=False, server_default="active"),
    )
    op.add_column("tasks", sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_foreign_key(
        "fk_tasks_recurrence_master_task_id",
        "tasks",
        "tasks",
        ["recurrence_master_task_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_tasks_recurrence_master_task_id", "tasks", ["recurrence_master_task_id"])

    op.alter_column("tasks", "is_recurring", server_default=None)
    op.alter_column("tasks", "recurrence_state", server_default=None)
    op.alter_column("tasks", "is_hidden", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_tasks_recurrence_master_task_id", table_name="tasks")
    op.drop_constraint("fk_tasks_recurrence_master_task_id", "tasks", type_="foreignkey")

    op.drop_column("tasks", "is_hidden")
    op.drop_column("tasks", "recurrence_state")
    op.drop_column("tasks", "recurrence_master_task_id")
    op.drop_column("tasks", "recurrence_end_date")
    op.drop_column("tasks", "recurrence_days_of_week")
    op.drop_column("tasks", "recurrence_interval")
    op.drop_column("tasks", "recurrence_type")
    op.drop_column("tasks", "is_recurring")

    op.execute(sa.text("UPDATE tasks SET status = 'done' WHERE status = 'done'"))
    op.execute(sa.text("UPDATE tasks SET status = 'new' WHERE status != 'done'"))

    op.drop_column("tasks", "priority")

    op.add_column("tasks", sa.Column("requires_verification", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("tasks", sa.Column("urgency", sa.String(length=32), nullable=False, server_default="normal"))
    op.add_column("tasks", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_tasks_due_at", "tasks", ["due_at"])

    op.alter_column("tasks", "requires_verification", server_default=None)
    op.alter_column("tasks", "urgency", server_default=None)
