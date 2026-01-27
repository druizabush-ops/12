"""Явный реестр модулей.
Файл существует для централизованного подключения router'ов.
Роль минимальна: только include_router без инициализации модулей.
"""

from fastapi import FastAPI

from app.modules.base import Module
from app.modules.auth import router as auth_router
from app.modules.dummy.manifest import module as dummy_module

modules: list[Module] = [
    Module(name="auth", router=auth_router),
    dummy_module,
]


def include_module_routers(app: FastAPI) -> None:
    """Подключает router'ы модулей к приложению.
    Нужен единый вход для регистрации маршрутов.
    Минимальность: только include_router без startup-логики.
    """

    for module in modules:
        app.include_router(module.router)
