"""Сборка event core по умолчанию.
"""

from __future__ import annotations

from app.events.default_handlers import update_calendar_day_summary
from app.events.handlers import EventHandlerRegistry
from app.events.publisher import EventPublisher


def build_event_publisher() -> EventPublisher:
    """Создаёт publisher со стандартными read-агрегатами."""

    registry = EventHandlerRegistry()
    registry.subscribe("task.created", update_calendar_day_summary)
    return EventPublisher(registry=registry)
