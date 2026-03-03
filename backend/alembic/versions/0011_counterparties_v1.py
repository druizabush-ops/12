"""Add counterparties block v1."""

from alembic import op
import sqlalchemy as sa


revision = "0011_counterparties_v1"
down_revision = "0010_user_sidebar_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("source_module", sa.String(length=64), nullable=True))
    op.add_column("tasks", sa.Column("source_counterparty_id", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("source_trigger_id", sa.Integer(), nullable=True))

    op.create_table(
        "counterparty_folders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["counterparty_folders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "counterparties",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("folder_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=255), nullable=True),
        sa.Column("product_group", sa.String(length=255), nullable=True),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("login", sa.String(length=255), nullable=True),
        sa.Column("password", sa.String(length=255), nullable=True),
        sa.Column("messenger", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("order_day_of_week", sa.Integer(), nullable=True),
        sa.Column("order_deadline_time", sa.Time(), nullable=True),
        sa.Column("delivery_day_of_week", sa.Integer(), nullable=True),
        sa.Column("defect_notes", sa.Text(), nullable=True),
        sa.Column("inn", sa.String(length=32), nullable=True),
        sa.Column("kpp", sa.String(length=32), nullable=True),
        sa.Column("ogrn", sa.String(length=32), nullable=True),
        sa.Column("legal_address", sa.String(length=512), nullable=True),
        sa.Column("bank_name", sa.String(length=255), nullable=True),
        sa.Column("bank_bik", sa.String(length=32), nullable=True),
        sa.Column("account", sa.String(length=64), nullable=True),
        sa.Column("corr_account", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["folder_id"], ["counterparty_folders.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "counterparty_auto_task_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("counterparty_id", sa.Integer(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False, server_default="order_request"),
        sa.Column("recurrence_type", sa.String(length=32), nullable=False),
        sa.Column("recurrence_interval", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("recurrence_days_of_week", sa.String(length=32), nullable=True),
        sa.Column("recurrence_end_date", sa.Date(), nullable=False),
        sa.Column("primary_assignee_user_id", sa.Integer(), nullable=False),
        sa.Column("primary_text", sa.Text(), nullable=False),
        sa.Column("primary_due_time", sa.Time(), nullable=True),
        sa.Column("review_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("review_assignee_user_id", sa.Integer(), nullable=True),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("review_due_time", sa.Time(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["counterparty_id"], ["counterparties.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["primary_assignee_user_id"], ["auth_users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["review_assignee_user_id"], ["auth_users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "counterparty_auto_task_bindings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=False),
        sa.Column("primary_master_task_id", sa.String(length=36), nullable=True),
        sa.Column("review_master_task_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["rule_id"], ["counterparty_auto_task_rules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["primary_master_task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["review_master_task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_id"),
    )

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
        [{"id": "counterparties", "name": "counterparties", "title": "Контрагенты", "path": "counterparties", "order": 3, "is_primary": False}],
    )

    role_modules_table = sa.table("auth_role_modules", sa.column("role_id", sa.Integer), sa.column("module_id", sa.String))
    op.bulk_insert(role_modules_table, [{"role_id": 1, "module_id": "counterparties"}, {"role_id": 2, "module_id": "counterparties"}])


def downgrade() -> None:
    op.drop_column("tasks", "source_trigger_id")
    op.drop_column("tasks", "source_counterparty_id")
    op.drop_column("tasks", "source_module")

    op.execute(sa.text("DELETE FROM auth_role_modules WHERE module_id = 'counterparties'"))
    op.execute(sa.text("DELETE FROM platform_modules WHERE id = 'counterparties'"))
    op.drop_table("counterparty_auto_task_bindings")
    op.drop_table("counterparty_auto_task_rules")
    op.drop_table("counterparties")
    op.drop_table("counterparty_folders")
