from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field

TaskStatus = Literal["active", "done_pending_verify", "done"]
TaskPriority = Literal["normal", "urgent", "very_urgent"]
RecurrenceType = Literal["daily", "weekly", "monthly"]
RecurrenceState = Literal["active", "paused", "stopped"]


class CalendarDayDto(BaseModel):
    date: date
    count: int


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
    created_at: datetime
    completed_at: datetime | None
    verified_at: datetime | None
    source_type: str | None
    source_id: str | None
    assignee_user_ids: list[int] = Field(default_factory=list)
    is_overdue: bool
    is_recurring: bool
    recurrence_type: RecurrenceType | None
    recurrence_interval: int | None
    recurrence_days_of_week: str | None
    recurrence_end_date: date | None
    recurrence_master_task_id: str | None
    recurrence_state: RecurrenceState
    is_hidden: bool
