from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def kb_AdminBack(back_to: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text='‹ Назад',
        callback_data=back_to
    ))

    return builder.as_markup()


async def kb_AdminMain() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text='Игроки',
        callback_data='admin_players'
    ))

    builder.row(InlineKeyboardButton(
        text='Матчи',
        callback_data='admin_matches'
    ))

    builder.row(InlineKeyboardButton(
        text='Рассылка',
        callback_data='admin_mail'
    ))

    builder.row(InlineKeyboardButton(
        text='Статистика',
        callback_data='admin_statistics'
    ))

    return builder.as_markup()


async def kb_AdminMatches(match_list: list, back_to: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for match in match_list:
        try:
            builder.row(InlineKeyboardButton(
                text=f'id: {match["id"]} ({match["status"]})',
                callback_data='admin_matches|{}'.format(match["id"])
            ))
        except Exception as e:
            print(e)
            continue

    builder.row(InlineKeyboardButton(
        text='‹ Назад',
        callback_data=back_to
    ))

    return builder.as_markup()


async def kb_AdminPlayerManage(back_to: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text='Выдать эло',
        callback_data='admin_player_set_elo'
    ))

    builder.row(InlineKeyboardButton(
        text='Выдать Наказание',
        callback_data='admin_player_set_ban'
    ))

    builder.row(InlineKeyboardButton(
        text='‹ Назад',
        callback_data=back_to
    ))

    return builder.as_markup()


async def kb_AdminPlayerManageElo(back_to: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    elo_positions = ((15, 30, 45, 60, 100), (-15, -30, -45, -60, -100))

    for position in elo_positions[0]:
        prefix = '' if position < 0 else '+'

        builder.add(
            InlineKeyboardButton(
                text=f'{prefix}{position}',
                callback_data='admin_player_set_elo|{}'.format(position)
            )
        )

    for position in elo_positions[1]:
        prefix = '' if position < 0 else '+'

        builder.add(
            InlineKeyboardButton(
                text=f'{prefix}{position}',
                callback_data='admin_player_set_elo|{}'.format(position)
            )
        )

    builder.row(InlineKeyboardButton(
        text='‹ Назад',
        callback_data=back_to
    ))

    return builder.as_markup()


async def kb_AdminMatchManage(match_id: int, back_to: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text='Отменить',
        callback_data='cancel_match|{}'.format(match_id)
    ))

    builder.row(
        InlineKeyboardButton(
            text='ТП синей команде',
            callback_data=f'tl_match|{match_id}|1'
        ),
        InlineKeyboardButton(
            text='ТП красной команде',
            callback_data=f'tl_match|{match_id}|2'
        )
    )

    builder.row(InlineKeyboardButton(
        text='‹ Назад',
        callback_data=back_to
    ))

    return builder.as_markup()
