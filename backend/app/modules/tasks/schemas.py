from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field

TaskStatus = Literal["new", "in_progress", "waiting", "done", "canceled"]
TaskUrgency = Literal["normal", "urgent", "very_urgent"]


class CalendarDayDto(BaseModel):
    date: date
    count_active: int
    count_done: int


class FolderDto(BaseModel):
    id: str
    title: str
    created_by_user_id: int
    show_active: bool
    show_overdue: bool
    show_done: bool


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
    folder_id: str | None = None
    is_recurring: bool = False
    recurrence_type: Literal["daily", "weekly", "monthly", "yearly"] | None = None
    recurrence_interval: int | None = None
    recurrence_days_of_week: list[int] = Field(default_factory=list)
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
    folder_id: str | None = None
    is_hidden: bool | None = None


class FolderCreatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class FolderUpdatePayload(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    show_active: bool | None = None
    show_overdue: bool | None = None
    show_done: bool | None = None


class RecurrenceActionPayload(BaseModel):
    action: Literal["pause", "resume", "stop"]


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
    folder_id: str | None
    is_recurring: bool
    recurrence_type: str | None
    recurrence_interval: int | None
    recurrence_days_of_week: list[int] = Field(default_factory=list)
    recurrence_end_date: date | None
    recurrence_master_task_id: str | None
    recurrence_state: str
    is_hidden: bool
    assignee_user_ids: list[int] = Field(default_factory=list)
    is_overdue: bool
    needs_attention_for_verifier: bool
