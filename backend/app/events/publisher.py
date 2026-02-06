"""Публикация доменных событий в event core.
Записывает факты в БД и синхронно запускает обработчики read-агрегатов.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.events.domain import DomainEvent
from app.events.handlers import EventHandlerRegistry
from app.events.models import DomainEventRecord

logger = logging.getLogger("event_core")


class EventPublisher:
    """Простой синхронный publisher для event spine."""

    def __init__(self, registry: EventHandlerRegistry) -> None:
        self._registry = registry

    def publish(self, db: Session, event: DomainEvent) -> None:
        """Публикует событие: сохраняет факт и выполняет handlers."""

        logger.info(
            "EVENT_CORE | publish event_id=%s type=%s entity=%s entity_id=%s",
            event.id,
            event.type,
            event.entity,
            event.entity_id,
        )

        db.add(
            DomainEventRecord(
                id=event.id,
                type=event.type,
                entity=event.entity,
                entity_id=event.entity_id,
                payload=event.payload,
                occurred_at=event.occurred_at,
            )
        )
        self._registry.dispatch(db, event)
