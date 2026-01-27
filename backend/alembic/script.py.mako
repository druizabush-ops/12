"""Шаблон миграции Alembic.
Файл существует как минимальный шаблон для новых миграций.
Минимальность: только обязательные секции без лишней логики.
"""
"""${message}

Идентификатор ревизии: ${up_revision}
Предыдущая ревизия: ${down_revision | comma,n}
Дата создания: ${create_date}
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    """Поднимает схему.
    Это место для минимальных SQLAlchemy операций миграции.
    """

    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Откатывает схему.
    Оставлено пустым, если миграция не требует отката.
    """

    ${downgrades if downgrades else "pass"}
