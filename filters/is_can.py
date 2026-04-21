from aiogram.filters import BaseFilter
from aiogram.types import Message


class IsCan(BaseFilter):
    def __init__(self, can: tuple):
        self.can = can

    async def __call__(self, message: Message) -> bool:
        user = message.from_user
        user_access = user.id in self.can
        if not user_access:
            await message.answer('❎ Данная функция не доступна вам')
        return user_access
