"""Tasks multi verifiers and strict state-machine."""

from alembic import op
import sqlalchemy as sa


revision = "0009_tasks_multi_verifiers"
down_revision = "0008_tasks_engine_v9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_verifiers",
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["auth_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("task_id", "user_id"),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO task_verifiers(task_id, user_id)
            SELECT id, verifier_user_id
            FROM tasks
            WHERE verifier_user_id IS NOT NULL
            """
        )
    )

    op.drop_constraint("tasks_verifier_user_id_fkey", "tasks", type_="foreignkey")
    op.drop_column("tasks", "verifier_user_id")


def downgrade() -> None:
    op.add_column("tasks", sa.Column("verifier_user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "tasks_verifier_user_id_fkey",
        "tasks",
        "auth_users",
        ["verifier_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute(
        sa.text(
            """
            UPDATE tasks t
            SET verifier_user_id = sq.user_id
            FROM (
                SELECT task_id, MIN(user_id) AS user_id
                FROM task_verifiers
                GROUP BY task_id
            ) sq
            WHERE sq.task_id = t.id
            """
        )
    )

    op.drop_table("task_verifiers")
