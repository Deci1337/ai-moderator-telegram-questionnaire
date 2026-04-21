from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from utils.user_service import GetUsers

from filters.is_admin import IsAdmin
from filters.is_can import IsCan
from keyboards.inline import admin as kb_admin
from utils.play_service import PlayerSetElo
from templates.functions import default

from config.access import CAN_MAIL


class PlayerEntity(StatesGroup):
    entity = State()


class Mailling(StatesGroup):
    count = State()
    message = State()


router = Router()


@router.message(Mailling.count, F.text, IsCan(CAN_MAIL))
async def fsm_get_MaillingCount(message: Message, state: FSMContext):
    try:
        count = int(message.text)
    except (TypeError, ValueError):
        await message.answer("Отправьте число")
    else:
        await state.update_data(count=count)
        await message.answer("Отправьте сообщение которое будет разослано пользователям")
        await state.set_state(Mailling.message)


@router.message(Mailling.message, F.forward_date, IsCan(CAN_MAIL))
async def fsm_get_MaillingMessage_forward_date(message: Message, state: FSMContext):
    data = await state.get_data()
    users = await GetUsers()
    from_chat_id = message.chat.id
    message_id = message.message_id
    await state.clear()

    await default.mailling(data['count'], users, message, 'forward_message', from_chat_id=from_chat_id,
                           message_id=message_id)


@router.message(Mailling.message, F.text, IsCan(CAN_MAIL))
async def fsm_get_MaillingMessage_text(message: Message, state: FSMContext):
    data = await state.get_data()
    users = await GetUsers()
    await state.clear()

    text = message.text

    await default.mailling(data['count'], users, message, 'send_message', text=text)


@router.message(Mailling.message, F.photo, IsCan(CAN_MAIL))
async def fsm_get_MaillingMessage_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    users = await GetUsers()
    await state.clear()

    photo = message.photo[-1].file_id
    caption = message.caption

    await default.mailling(data['count'], users, message, 'send_photo', photo=photo, caption=caption)


@router.message(Mailling.message, F.video, IsCan(CAN_MAIL))
async def fsm_get_MaillingMessage_video(message: Message, state: FSMContext):
    data = await state.get_data()
    users = await GetUsers()
    await state.clear()

    video = message.video.file_id
    caption = message.caption

    await default.mailling(data['count'], users, message, 'send_video', video=video, caption=caption)


@router.message(Mailling.message, F.document, IsCan(CAN_MAIL))
async def fsm_get_MaillingMessage_document(message: Message, state: FSMContext):
    data = await state.get_data()
    users = await GetUsers()
    await state.clear()

    document = message.document.file_id
    caption = message.caption

    await default.mailling(data['count'], users, message, 'send_document', document=document, caption=caption)


@router.message(Mailling.message, F.animation, IsCan(CAN_MAIL))
async def fsm_get_MaillingMessage_animation(message: Message, state: FSMContext):
    data = await state.get_data()
    users = await GetUsers()
    await state.clear()

    animation = message.animation.file_id
    caption = message.caption

    await default.mailling(data['count'], users, message, 'send_animation', animation=animation, caption=caption)


@router.message(Mailling.message, F.sticker, IsCan(CAN_MAIL))
async def fsm_get_MaillingMessage_sticker(message: Message, state: FSMContext):
    data = await state.get_data()
    users = await GetUsers()
    await state.clear()

    sticker = message.sticker.file_id

    await default.mailling(data['count'], users, message, 'send_sticker', sticker=sticker)


@router.message(PlayerEntity.entity, F.text, IsAdmin(True))
async def got_entity(message: Message, state: FSMContext):
    await state.update_data(entity=message.text)

    await message.answer(
        text="Выберите действие",
        reply_markup=await kb_admin.kb_AdminPlayerManage('admin_players')
    )


@router.callback_query(PlayerEntity.entity, F.data == 'admin_player_manage', IsAdmin(True))
async def call_admin_player_manage(call: CallbackQuery):
    await call.message.edit_text(
        text='Выберите действие',
        reply_markup=await kb_admin.kb_AdminPlayerManage('admin_players')
    )


@router.callback_query(PlayerEntity.entity, F.data == 'admin_player_set_elo', IsAdmin(True))
async def call_admin_player_set_elo(call: CallbackQuery):
    await call.message.edit_text(
        text="Выберите изменение эло",
        reply_markup=await kb_admin.kb_AdminPlayerManageElo('admin_player_manage')
    )


@router.callback_query(PlayerEntity.entity, F.data.startswith('admin_player_set_elo'), IsAdmin(True))
async def call_admin_player_set_elo_position(call: CallbackQuery, state: FSMContext):
    position = int(call.data.split('|')[1])

    data = await state.get_data()

    result = await PlayerSetElo(data['entity'], position)

    if result is True:
        await call.answer('Эло успешно изменено', show_alert=True)
    else:
        await call.answer("Произошла ошибка", show_alert=True)