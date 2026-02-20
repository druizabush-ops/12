from pydantic import BaseModel


class SidebarSettingsDto(BaseModel):
    modules_order: list[str] | None = None


class SidebarModulesOrderUpdate(BaseModel):
    modules_order: list[str]
