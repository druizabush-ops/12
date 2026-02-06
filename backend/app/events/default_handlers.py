"""Дефолтные обработчики read-агрегатов для event core.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.events.domain import DomainEvent
from app.events.models import CalendarDaySummary


def _extract_event_day(event: DomainEvent) -> date:
    """Определяет дату события для календарного агрегата.

    Если в payload есть поле date (YYYY-MM-DD), используется оно,
    иначе берётся дата occurred_at.
    """

    raw_day = event.payload.get("date")
    if isinstance(raw_day, str):
        return date.fromisoformat(raw_day)
    return event.occurred_at.date()


def update_calendar_day_summary(db: Session, event: DomainEvent) -> None:
    """Обновляет read-агрегат calendar_day_summary по факту события."""

    day = _extract_event_day(event)
    summary = db.get(CalendarDaySummary, day)
    if summary is None:
        db.add(
            CalendarDaySummary(
                day=day,
                events_count=1,
                last_event_at=event.occurred_at,
            )
        )
        return

    summary.events_count += 1
    summary.last_event_at = max(summary.last_event_at, event.occurred_at)
