"""Реестр обработчиков событий.
Содержит синхронную диспетчеризацию backend-обработчиков без зависимости от UI.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Callable

from sqlalchemy.orm import Session

from app.events.domain import DomainEvent

logger = logging.getLogger("event_core")
EventHandler = Callable[[Session, DomainEvent], None]


class EventHandlerRegistry:
    """Регистрирует и вызывает обработчики по типу события."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Подписывает обработчик на конкретный type события."""

        self._handlers[event_type].append(handler)

    def dispatch(self, db: Session, event: DomainEvent) -> None:
        """Синхронно выполняет обработчики события."""

        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            logger.info(
                "EVENT_CORE | handling event_id=%s type=%s handler=%s",
                event.id,
                event.type,
                handler.__name__,
            )
            handler(db, event)
