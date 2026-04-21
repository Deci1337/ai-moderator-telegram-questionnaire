from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton


async def delete():
    return ReplyKeyboardRemove()


async def manage_form():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="❤️"),
                KeyboardButton(text="👎")
            ],
            [
                KeyboardButton(text="🔄 Сменить поиски")
            ]
        ],
        resize_keyboard=True
    )

    return kb
