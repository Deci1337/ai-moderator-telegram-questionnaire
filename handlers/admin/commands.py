from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards.inline import admin as kb_admin
from filters.is_admin import IsAdmin

router = Router()


@router.message(Command("admin"), IsAdmin(True))
async def cmd_admin(message: Message):
    await message.answer(
        text="Выберите меню",
        reply_markup=await kb_admin.kb_AdminMain()
    )
