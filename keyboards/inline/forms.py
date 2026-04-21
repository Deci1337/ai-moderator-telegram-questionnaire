from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config.form import RANKS, TIERS, SEARCHS


async def show_likes():
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text='👀 Смотреть',
            callback_data='watch_likes'
        )
    )

    return builder.as_markup()


async def finish_form():
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text='👀 Смотреть анкеты',
            callback_data='watch_forms'
        )
    )
    builder.row(
        InlineKeyboardButton(
            text='⚙️ Моя анкета',
            callback_data='my_form'
        )
    )

    return builder.as_markup()


async def manage_my_form():
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text='↪️ Заполнить заново',
            callback_data='ankets_fortes'
        )
    )

    return builder.as_markup()


async def make_form():
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text='✅ Начать',
            callback_data='ankets_fortes'
        )
    )

    return builder.as_markup()


async def max_rank():
    builder = InlineKeyboardBuilder()

    for rank in RANKS:
        builder.add(InlineKeyboardButton(
            text=rank['name'],
            callback_data=f'form_rank|{rank["key"]}'
        ))

    builder.adjust(2)

    return builder.as_markup()


async def max_league_rank(back_to: str):
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(
        text='1',
        callback_data='form_league_rank|1'
    ))

    builder.add(InlineKeyboardButton(
        text='2',
        callback_data='form_league_rank|2'
    ))

    builder.add(InlineKeyboardButton(
        text='3',
        callback_data='form_league_rank|3'
    ))

    builder.row(InlineKeyboardButton(
        text='‹ Назад',
        callback_data=back_to
    ))

    return builder.as_markup()


async def tier():
    builder = InlineKeyboardBuilder()

    for tier in TIERS:
        builder.add(InlineKeyboardButton(
            text=tier['name'],
            callback_data=f'form_tier|{tier["key"]}'
        ))

    builder.adjust(2)

    return builder.as_markup()


async def submit():
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text='↪️ Заполнить заново',
            callback_data='ankets_fortes'
        )
    )

    builder.row(
        InlineKeyboardButton(
            text='✅ Подтвердить',
            callback_data='form_submit'
        )
    )

    return builder.as_markup()


async def retry_form():
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text='↪️ Заполнить заново',
            callback_data='ankets_fortes'
        )
    )

    return builder.as_markup()


async def search(active_searchs: list):
    builder = InlineKeyboardBuilder()

    for key in SEARCHS:
        status = ' ✅' if key in active_searchs else ''
        builder.add(InlineKeyboardButton(
            text=f"{SEARCHS[key]['name']}{status}",
            callback_data='form_search|{}'.format(key)
        ))

    builder.adjust(2)

    if len(active_searchs) > 0:
        builder.row(
            InlineKeyboardButton(
                text='📨 Отправить анкету',
                callback_data='send_form'
            )
        )

    return builder.as_markup()
