from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field, model_validator

TaskStatus = Literal["active", "done_pending_verify", "done"]
TaskPriority = Literal["normal", "urgent", "very_urgent"]
RecurrenceType = Literal["daily", "weekly", "monthly", "yearly"]
RecurrenceState = Literal["active", "paused", "stopped"]


class CalendarDayDto(BaseModel):
    date: date
    count: int


def _validate_recurrence(payload: "TaskCreatePayload") -> "TaskCreatePayload":
    if not payload.is_recurring:
        return payload

    if (payload.recurrence_interval or 0) < 1:
        raise ValueError("recurrence_interval_must_be_positive")

    if payload.recurrence_type == "weekly":
        values = [item.strip() for item in (payload.recurrence_days_of_week or "").split(",") if item.strip()]
        if not values:
            raise ValueError("weekly_requires_days")
        valid_days = {str(index) for index in range(1, 8)}
        if any(value not in valid_days for value in values):
            raise ValueError("weekly_days_out_of_range")

    return payload


class TaskCreatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    due_date: date | None = None
    due_time: time | None = None
    priority: TaskPriority | None = None
    verifier_user_id: int | None = None
    assignee_user_ids: list[int] = Field(default_factory=list)
    source_type: str | None = None
    source_id: str | None = None
    is_recurring: bool = False
    recurrence_type: RecurrenceType | None = None
    recurrence_interval: int | None = None
    recurrence_days_of_week: str | None = None
    recurrence_end_date: date | None = None

    @model_validator(mode="after")
    def validate_recurrence(self) -> "TaskCreatePayload":
        return _validate_recurrence(self)


class TaskUpdatePayload(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    due_date: date | None = None
    due_time: time | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    verifier_user_id: int | None = None
    assignee_user_ids: list[int] | None = None


class RecurrenceActionPayload(BaseModel):
    action: Literal["pause", "resume", "stop"]


class TaskDto(BaseModel):
    id: str
    title: str
    description: str | None
    due_date: date | None
    due_time: time | None
    status: TaskStatus
    priority: TaskPriority | None
    verifier_user_id: int | None
    created_by_user_id: int
    created_by_name: str
    created_at: datetime
    completed_at: datetime | None
    verified_at: datetime | None
    source_type: str | None
    source_id: str | None
    assignee_user_ids: list[int] = Field(default_factory=list)
    assignee_names: list[str] = Field(default_factory=list)
    verifier_name: str | None = None
    is_overdue: bool
    is_recurring: bool
    recurrence_type: RecurrenceType | None
    recurrence_interval: int | None
    recurrence_days_of_week: str | None
    recurrence_end_date: date | None
    recurrence_master_task_id: str | None
    recurrence_state: RecurrenceState
    is_hidden: bool


class TaskBadgesDto(BaseModel):
    pending_verify_count: int
    fresh_completed_flag: bool
