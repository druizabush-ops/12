"""Добавляет event core (BLOCK 22).
Создаёт event spine и пример read-агрегата.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0006_event_core"
down_revision = "0005_module_permissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создаёт таблицы событий и календарного агрегата."""

    op.create_table(
        "domain_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("type", sa.String(length=128), nullable=False),
        sa.Column("entity", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_domain_events_type", "domain_events", ["type"])
    op.create_index("ix_domain_events_entity", "domain_events", ["entity"])
    op.create_index("ix_domain_events_entity_id", "domain_events", ["entity_id"])
    op.create_index("ix_domain_events_occurred_at", "domain_events", ["occurred_at"])

    op.create_table(
        "calendar_day_summary",
        sa.Column("day", sa.Date(), primary_key=True),
        sa.Column("events_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_event_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Удаляет таблицы event core."""

    op.drop_table("calendar_day_summary")
    op.drop_index("ix_domain_events_occurred_at", table_name="domain_events")
    op.drop_index("ix_domain_events_entity_id", table_name="domain_events")
    op.drop_index("ix_domain_events_entity", table_name="domain_events")
    op.drop_index("ix_domain_events_type", table_name="domain_events")
    op.drop_table("domain_events")
