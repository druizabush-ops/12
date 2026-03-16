from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class EmployeeUserDto(BaseModel):
    id: int
    full_name: str
    login: str
    phone: str | None
    is_active: bool
    is_archived: bool
    created_at: datetime | None = None


class EmployeeUserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    login: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    phone: str | None = Field(default=None, max_length=64)
    organization_ids: list[int] = Field(default_factory=list)
    position_ids: list[int] = Field(default_factory=list)


class EmployeeUserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    is_active: bool | None = None
    organization_ids: list[int] | None = None
    position_ids: list[int] | None = None


class SetPasswordDto(BaseModel):
    new_password: str = Field(min_length=6, max_length=128)


class OrganizationDto(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool
    is_archived: bool


class OrganizationCreate(BaseModel):
    name: str
    code: str


class OrganizationUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    is_active: bool | None = None


class GroupDto(BaseModel):
    id: int
    organization_id: int
    parent_group_id: int | None
    name: str
    head_user_id: int | None
    sort_order: int
    is_active: bool
    is_archived: bool


class GroupUpsert(BaseModel):
    organization_id: int
    parent_group_id: int | None = None
    name: str
    head_user_id: int | None = None
    sort_order: int = 0


class PositionDto(BaseModel):
    id: int
    organization_id: int
    group_id: int
    name: str
    manager_position_id: int | None
    sort_order: int
    is_active: bool
    is_archived: bool


class PositionUpsert(BaseModel):
    organization_id: int
    group_id: int
    name: str
    manager_position_id: int | None = None
    sort_order: int = 0
    role_ids: list[int] = Field(default_factory=list)


class AssignUserDto(BaseModel):
    user_id: int


class EmployeeRoleDto(BaseModel):
    id: int
    name: str
    code: str
    description: str | None
    is_system: bool
    is_active: bool
    is_archived: bool


class EmployeeRoleUpsert(BaseModel):
    name: str
    code: str
    description: str | None = None
    permission_ids: list[int] = Field(default_factory=list)


class EmployeeRoleUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    is_active: bool | None = None
    permission_ids: list[int] | None = None


class PermissionDto(BaseModel):
    id: int
    module: str
    action: str
    code: str
    name: str


class SwitchOrganizationDto(BaseModel):
    organization_id: int


class OrgTreeNode(BaseModel):
    id: str
    type: str
    title: str
    archived: bool = False
    children: list["OrgTreeNode"] = Field(default_factory=list)


OrgTreeNode.model_rebuild()
