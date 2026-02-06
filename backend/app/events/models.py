"""ORM-модели event core и read-агрегатов.
Модели хранят факты событий и агрегированное состояние для чтения.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DomainEventRecord(Base):
    """Хранилище фактов доменных событий."""

    __tablename__ = "domain_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class CalendarDaySummary(Base):
    """Пример read-агрегата календарного дня.

    Таблица содержит только агрегированное состояние и не хранит бизнес-решения.
    """

    __tablename__ = "calendar_day_summary"

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    events_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
