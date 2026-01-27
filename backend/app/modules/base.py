"""Базовый контракт модулей.
Файл существует для единого технического описания модуля.
Роль минимальна: фиксируются только имя и router без логики инициализации.
"""

from dataclasses import dataclass

from fastapi import APIRouter


@dataclass(frozen=True)
class Module:
    """Контракт модуля платформы.
    Нужен для предсказуемого подключения маршрутов.
    Минимальность: только имя и router, без логики старта.
    """

    name: str
    router: APIRouter
