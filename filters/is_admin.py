from aiogram.filters import BaseFilter
from aiogram.types import Message
from config.access import ADMINS


class IsAdmin(BaseFilter):
    def __init__(self, is_admin: bool):
        self.is_admin = is_admin

    async def __call__(self, message: Message) -> bool:
        user = message.from_user
        user_admin = user.id in ADMINS
        if user_admin != self.is_admin:
            await message.answer('❎ Данная функция доступна только администраторам бота')
        return user_admin is self.is_admin
