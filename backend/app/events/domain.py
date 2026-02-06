"""Доменная модель события для event spine.
Содержит только факт и не включает никакой UI-логики.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class DomainEvent:
    """Единый формат доменного события.

    Событие описывает факт истории и может обрабатываться разными
    backend-обработчиками для обновления read-агрегатов.
    """

    id: str
    type: str
    entity: str
    entity_id: str
    payload: dict[str, Any]
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        *,
        type: str,
        entity: str,
        entity_id: str,
        payload: dict[str, Any],
        occurred_at: datetime | None = None,
    ) -> "DomainEvent":
        """Создаёт событие с техническими полями по умолчанию."""

        event_time = occurred_at or datetime.now(timezone.utc)
        return cls(
            id=str(uuid4()),
            type=type,
            entity=entity,
            entity_id=entity_id,
            payload=payload,
            occurred_at=event_time,
        )
