from pydantic import BaseModel, Field


class RoleDto(BaseModel):
    id: int
    name: str
    can_manage_access: bool
    module_ids: list[str] = Field(default_factory=list)


class RoleCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ModuleAccessPayload(BaseModel):
    has_access: bool


class PermissionItem(BaseModel):
    name: str
    is_allowed: bool


class PermissionsDto(BaseModel):
    role_id: int
    module_id: str
    permissions: list[PermissionItem] = Field(default_factory=list)


class PermissionsUpdatePayload(BaseModel):
    permissions: list[PermissionItem] = Field(default_factory=list)


class UserRolesDto(BaseModel):
    id: int
    username: str
    role_ids: list[int] = Field(default_factory=list)


class UserRolesUpdatePayload(BaseModel):
    role_ids: list[int] = Field(default_factory=list)


class AffectedUserDto(BaseModel):
    id: int
    username: str


class ChangeImpactDto(BaseModel):
    message: str
    affected_users: list[AffectedUserDto] = Field(default_factory=list)


class SessionActionPayload(BaseModel):
    user_ids: list[int] = Field(default_factory=list)
    mode: str
