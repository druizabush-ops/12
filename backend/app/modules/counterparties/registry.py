from app.modules.base import Module
from app.modules.counterparties.api import router

module = Module(name="counterparties", router=router)
