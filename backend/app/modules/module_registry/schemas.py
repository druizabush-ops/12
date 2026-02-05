"""Pydantic-схемы для платформенного реестра модулей.
Описывают контракт BLOCK 13 между backend и frontend.
"""

from pydantic import BaseModel, ConfigDict, Field


class ModuleDto(BaseModel):
    """DTO модуля платформы.
    Используется как единый формат ответа backend.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    title: str
    path: str
    order: int
    is_primary: bool
    has_access: bool
    permissions: dict[str, bool] = Field(default_factory=dict)


class ModulePrimaryUpdate(BaseModel):
    """Запрос на обновление основного модуля.
    module_id=None сбрасывает текущий основной модуль.
    """

    module_id: str | None = None


class ModuleOrderUpdate(BaseModel):
    """Запрос на обновление порядка модулей.
    ordered_ids содержит полный список идентификаторов.
    """

    ordered_ids: list[str] = Field(default_factory=list)
