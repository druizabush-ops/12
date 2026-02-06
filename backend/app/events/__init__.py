"""Инструменты event core (hybrid: events + read aggregates)."""

from app.events.bootstrap import build_event_publisher
from app.events.domain import DomainEvent
from app.events.publisher import EventPublisher

__all__ = ["DomainEvent", "EventPublisher", "build_event_publisher"]
