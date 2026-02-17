from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Literal

from pydantic import BaseModel, Field

TaskStatus = Literal["new", "in_progress", "waiting", "done", "canceled"]
TaskUrgency = Literal["normal", "urgent", "very_urgent"]
RecurrenceType = Literal["daily", "weekly", "monthly", "yearly"]
RecurrenceState = Literal["active", "paused", "stopped"]
ApplyScope = Literal["single", "future", "master"]


class CalendarDayDto(BaseModel):
    date: date
    count: int


class TaskCreatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    due_date: date | None = None
    due_time: time | None = None
    urgency: TaskUrgency = "normal"
    requires_verification: bool = False
    verifier_user_id: int | None = None
    assignee_user_ids: list[int] = Field(default_factory=list)
    source_type: str | None = None
    source_id: str | None = None

    is_recurring: bool = False
    recurrence_type: RecurrenceType | None = None
    recurrence_interval: int | None = Field(default=None, ge=1)
    recurrence_days_of_week: list[int] | None = None
    recurrence_end_date: date | None = None


class TaskUpdatePayload(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    due_date: date | None = None
    due_time: time | None = None
    urgency: TaskUrgency | None = None
    status: TaskStatus | None = None
    requires_verification: bool | None = None
    verifier_user_id: int | None = None
    assignee_user_ids: list[int] | None = None
    apply_scope: ApplyScope = "single"


class RecurrenceActionPayload(BaseModel):
    action: Literal["pause", "resume", "stop"]


class TaskFolderCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    filter_json: dict[str, Any] = Field(default_factory=dict)


class TaskFolderUpdatePayload(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    filter_json: dict[str, Any] | None = None


class TaskFolderDto(BaseModel):
    id: str
    name: str
    created_by_user_id: int
    filter_json: dict[str, Any]
    created_at: datetime


class TaskDto(BaseModel):
    id: str
    title: str
    description: str | None
    due_date: date | None
    due_time: time | None
    due_at: datetime | None
    status: TaskStatus
    urgency: TaskUrgency
    requires_verification: bool
    verifier_user_id: int | None
    created_by_user_id: int
    created_at: datetime
    completed_at: datetime | None
    verified_at: datetime | None
    source_type: str | None
    source_id: str | None
    assignee_user_ids: list[int] = Field(default_factory=list)
    is_overdue: bool
    needs_attention_for_verifier: bool

    is_recurring: bool
    recurrence_type: RecurrenceType | None
    recurrence_interval: int | None
    recurrence_days_of_week: list[int] | None
    recurrence_end_date: date | None
    recurrence_master_task_id: str | None
    recurrence_state: RecurrenceState | None
    is_hidden: bool
