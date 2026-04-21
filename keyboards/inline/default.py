from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def subscribe():
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text='Подпишусь',
            callback_data='subscribe_skip'
        )
    )

    builder.row(
        InlineKeyboardButton(
            text='Возможно позже',
            callback_data='subscribe_skip'
        )
    )

    return builder.as_markup()


async def choice_project():
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text='FFA Fortes',
            callback_data='ffa_fortes'
        )
    )

    builder.row(
        InlineKeyboardButton(
            text='Ankets Fortes',
            callback_data='ankets_fortes'
        )
    )

    return builder.as_markup()