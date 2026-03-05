"""Counterparties auto tasks v2 rolling horizon."""

from alembic import op
import sqlalchemy as sa


revision = "0012_counterparty_autotasks_v2"
down_revision = "0011_counterparties_v1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("counterparty_auto_task_bindings")

    op.add_column("counterparty_auto_task_rules", sa.Column("task_kind", sa.String(length=32), nullable=True))
    op.add_column("counterparty_auto_task_rules", sa.Column("title_template", sa.String(length=255), nullable=True))
    op.add_column("counterparty_auto_task_rules", sa.Column("description_template", sa.Text(), nullable=True))
    op.add_column("counterparty_auto_task_rules", sa.Column("schedule_weekday", sa.Integer(), nullable=True))
    op.add_column("counterparty_auto_task_rules", sa.Column("schedule_due_time", sa.Time(), nullable=True))
    op.add_column("counterparty_auto_task_rules", sa.Column("horizon_days", sa.Integer(), nullable=False, server_default="15"))
    op.add_column("counterparty_auto_task_rules", sa.Column("linked_task_master_id", sa.String(length=36), nullable=True))
    op.add_column("counterparty_auto_task_rules", sa.Column("state", sa.String(length=16), nullable=False, server_default="active"))
    op.create_foreign_key(None, "counterparty_auto_task_rules", "tasks", ["linked_task_master_id"], ["id"], ondelete="SET NULL")

    op.execute(sa.text("UPDATE counterparty_auto_task_rules SET task_kind='MAKE_ORDER' WHERE task_kind IS NULL"))
    op.execute(sa.text("UPDATE counterparty_auto_task_rules SET title_template=title WHERE title_template IS NULL"))
    op.execute(sa.text("UPDATE counterparty_auto_task_rules SET schedule_weekday=1 WHERE schedule_weekday IS NULL"))

    op.alter_column("counterparty_auto_task_rules", "task_kind", nullable=False)
    op.alter_column("counterparty_auto_task_rules", "title_template", nullable=False)
    op.alter_column("counterparty_auto_task_rules", "schedule_weekday", nullable=False)

    op.create_table(
        "counterparty_auto_task_rule_assignees",
        sa.Column("rule_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["rule_id"], ["counterparty_auto_task_rules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["auth_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("rule_id", "user_id"),
    )
    op.create_table(
        "counterparty_auto_task_rule_verifiers",
        sa.Column("rule_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["rule_id"], ["counterparty_auto_task_rules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["auth_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("rule_id", "user_id"),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO counterparty_auto_task_rule_assignees(rule_id, user_id)
            SELECT id, primary_assignee_user_id FROM counterparty_auto_task_rules
            WHERE primary_assignee_user_id IS NOT NULL
            """
        )
    )

    op.create_table(
        "counterparty_module_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_creator_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["task_creator_user_id"], ["auth_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.drop_column("counterparty_auto_task_rules", "title")
    op.drop_column("counterparty_auto_task_rules", "kind")
    op.drop_column("counterparty_auto_task_rules", "recurrence_type")
    op.drop_column("counterparty_auto_task_rules", "recurrence_interval")
    op.drop_column("counterparty_auto_task_rules", "recurrence_days_of_week")
    op.drop_column("counterparty_auto_task_rules", "recurrence_end_date")
    op.drop_column("counterparty_auto_task_rules", "primary_assignee_user_id")
    op.drop_column("counterparty_auto_task_rules", "primary_text")
    op.drop_column("counterparty_auto_task_rules", "primary_due_time")
    op.drop_column("counterparty_auto_task_rules", "review_enabled")
    op.drop_column("counterparty_auto_task_rules", "review_assignee_user_id")
    op.drop_column("counterparty_auto_task_rules", "review_text")
    op.drop_column("counterparty_auto_task_rules", "review_due_time")


def downgrade() -> None:
    raise NotImplementedError
