from app.modules.base import Module
from app.modules.tasks.api import router

module = Module(name="tasks", router=router)
