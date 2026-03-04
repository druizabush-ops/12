from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field, model_validator

CounterpartyStatus = Literal["active", "inactive"]
CounterpartyAutoTaskKind = Literal["order_request", "custom"]
RecurrenceType = Literal["daily", "weekly", "monthly", "yearly"]


class CounterpartyFolderCreatePayload(BaseModel):
    parent_id: int | None = None
    name: str = Field(min_length=1, max_length=255)
    sort_order: int = 0


class CounterpartyFolderUpdatePayload(BaseModel):
    parent_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    sort_order: int | None = None


class CounterpartyFolderDto(BaseModel):
    id: int
    parent_id: int | None
    name: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class CounterpartyUpsertPayload(BaseModel):
    folder_id: int
    group_id: int | None = None
    status: CounterpartyStatus = "active"
    sort_order: int = 0
    is_archived: bool = False

    name: str = Field(min_length=1, max_length=255)
    legal_name: str | None = None
    city: str | None = None
    product_group: str | None = None
    department: str | None = None
    website: str | None = None
    login: str | None = None
    password: str | None = None
    messenger: str | None = None
    phone: str | None = None
    email: str | None = None
    order_day_of_week: int | None = None
    order_deadline_time: time | None = None
    delivery_day_of_week: int | None = None
    defect_notes: str | None = None

    inn: str | None = None
    kpp: str | None = None
    ogrn: str | None = None
    legal_address: str | None = None
    bank_name: str | None = None
    bank_bik: str | None = None
    account: str | None = None
    corr_account: str | None = None


class CounterpartyDto(CounterpartyUpsertPayload):
    id: int
    created_at: datetime
    updated_at: datetime


class AutoTaskSchedulePayload(BaseModel):
    recurrence_type: RecurrenceType
    recurrence_interval: int = Field(ge=1)
    recurrence_days_of_week: list[int] = Field(default_factory=list)
    recurrence_end_date: date


class AutoTaskPrimaryPayload(BaseModel):
    assignee_user_id: int
    text: str = Field(min_length=1)
    due_time: time | None = None


class AutoTaskReviewPayload(BaseModel):
    enabled: bool = False
    assignee_user_id: int | None = None
    text: str | None = None
    due_time: time | None = None


class CounterpartyAutoTaskRuleUpsertPayload(BaseModel):
    is_enabled: bool = True
    title: str = Field(min_length=1, max_length=255)
    kind: CounterpartyAutoTaskKind = "order_request"
    schedule: AutoTaskSchedulePayload
    primary_task: AutoTaskPrimaryPayload
    review_task: AutoTaskReviewPayload = Field(default_factory=AutoTaskReviewPayload)
    update_mode: Literal["keep_existing", "replace_existing"] | None = None

    @model_validator(mode="after")
    def validate_review(self) -> "CounterpartyAutoTaskRuleUpsertPayload":
        if self.review_task.enabled and (self.review_task.assignee_user_id is None or not self.review_task.text):
            raise ValueError("review_task_requires_assignee_and_text")
        return self


class CounterpartyAutoTaskBindingDto(BaseModel):
    primary_master_task_id: str
    review_master_task_id: str | None


class CounterpartyAutoTaskRuleDto(BaseModel):
    id: int
    counterparty_id: int
    is_enabled: bool
    title: str
    kind: CounterpartyAutoTaskKind
    schedule: AutoTaskSchedulePayload
    primary_task: AutoTaskPrimaryPayload
    review_task: AutoTaskReviewPayload
    binding: CounterpartyAutoTaskBindingDto | None
    created_at: datetime
    updated_at: datetime
