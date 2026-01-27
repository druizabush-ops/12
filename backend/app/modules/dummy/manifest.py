"""Манифест тестового модуля.
Файл существует для описания модуля через общий контракт.
Минимальность: только имя и router без инициализации.
"""

from app.modules.base import Module
from app.modules.dummy.api import router

module = Module(name="dummy", router=router)
