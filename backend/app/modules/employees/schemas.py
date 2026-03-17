from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    login: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    organization_ids: list[int] = Field(default_factory=list)
    position_ids: list[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    is_active: bool | None = None
    organization_ids: list[int] | None = None
    position_ids: list[int] | None = None


class UserSetPassword(BaseModel):
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    id: int
    full_name: str
    login: str
    phone: str | None
    is_active: bool
    is_archived: bool
    created_at: datetime


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=64)


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None


class OrganizationOut(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool
    is_archived: bool


class SwitchOrganizationPayload(BaseModel):
    organization_id: int


class GroupCreate(BaseModel):
    organization_id: int
    parent_group_id: int | None = None
    name: str = Field(min_length=1, max_length=255)
    head_user_id: int | None = None
    sort_order: int = 0


class GroupUpdate(BaseModel):
    parent_group_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    head_user_id: int | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class PositionCreate(BaseModel):
    organization_id: int
    group_id: int
    name: str = Field(min_length=1, max_length=255)
    manager_position_id: int | None = None
    sort_order: int = 0
    role_ids: list[int] = Field(default_factory=list)


class PositionUpdate(BaseModel):
    group_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    manager_position_id: int | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    role_ids: list[int] | None = None


class AssignUserPayload(BaseModel):
    user_id: int


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=64)
    description: str | None = None
    permission_ids: list[int] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None
    permission_ids: list[int] | None = None


class RoleOut(BaseModel):
    id: int
    name: str
    code: str
    description: str | None
    is_system: bool
    is_active: bool
    is_archived: bool


class PermissionOut(BaseModel):
    id: int
    module: str
    action: str
    code: str
    name: str
