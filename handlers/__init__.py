from aiogram import Router
from . import commands
from .admin import commands as admin_commands
from .admin import callbacks as admin_callbacks
from .admin import fsm as admin_fsm

from .form import callbacks as form_callbacks
from .form import fsm as form_fsm

__all__ = [
    'commands'
]


def register_handlers() -> Router:
    """
    Регистрация всех хендлеров
    """
    router = Router()

    router.include_router(commands.router)

    router.include_router(admin_commands.router)
    router.include_router(admin_callbacks.router)
    router.include_router(admin_fsm.router)

    router.include_router(form_callbacks.router)
    router.include_router(form_fsm.router)

    return router
