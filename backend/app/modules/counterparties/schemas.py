from __future__ import annotations

from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, Field

CounterpartyStatus = Literal["active", "inactive"]
CounterpartyAutoTaskKind = Literal["MAKE_ORDER", "SEND_ORDER"]
CounterpartyAutoTaskState = Literal["active", "paused", "stopped"]


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


class CounterpartyAutoTaskRuleCreatePayload(BaseModel):
    task_kind: CounterpartyAutoTaskKind
    title_template: str = Field(min_length=1, max_length=255)
    description_template: str | None = None
    assignee_user_ids: list[int] = Field(default_factory=list)
    verifier_user_ids: list[int] | None = None
    is_enabled: bool = True
    schedule_weekday: int = Field(ge=1, le=7)
    schedule_due_time: time | None = None
    horizon_days: int = Field(default=15, ge=1, le=30)


class CounterpartyAutoTaskRulePatchPayload(BaseModel):
    task_kind: CounterpartyAutoTaskKind | None = None
    title_template: str | None = Field(default=None, min_length=1, max_length=255)
    description_template: str | None = None
    assignee_user_ids: list[int] | None = None
    verifier_user_ids: list[int] | None = None
    is_enabled: bool | None = None
    schedule_weekday: int | None = Field(default=None, ge=1, le=7)
    schedule_due_time: time | None = None
    horizon_days: int | None = Field(default=None, ge=1, le=30)


class CounterpartyAutoTaskRuleDto(BaseModel):
    id: int
    counterparty_id: int
    task_kind: CounterpartyAutoTaskKind
    title_template: str
    description_template: str | None
    assignee_user_ids: list[int]
    verifier_user_ids: list[int] | None
    is_enabled: bool
    schedule_weekday: int
    schedule_due_time: time | None
    horizon_days: int
    linked_task_master_id: str | None
    state: CounterpartyAutoTaskState
    created_at: datetime
    updated_at: datetime


class CounterpartyTaskCreatorSettingsPayload(BaseModel):
    task_creator_user_id: int | None = None


class CounterpartyTaskCreatorSettingsDto(BaseModel):
    task_creator_user_id: int | None
