from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from utils.play_service import GetAvailableMatches, CancelMatch, MatchTechLose, GetMatches
from keyboards.inline import admin as kb_admin
from filters.is_admin import IsAdmin
from filters.is_can import IsCan
from aiogram.filters.state import State
from .fsm import PlayerEntity, Mailling

from config.access import CAN_MAIL

from utils.user_service import GetUsersCount

router = Router()


@router.callback_query(State('*'), F.data == 'admin_main', IsAdmin(True))
async def call_admin_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        text="Выберите меню",
        reply_markup=await kb_admin.kb_AdminMain()
    )


@router.callback_query(F.data == 'admin_statistics', IsAdmin(True))
async def call_admin_statistics(call: CallbackQuery):
    users_count = await GetUsersCount()
    matches = await GetMatches()
    completed_matches = [item for item in matches if item['status'] == 'completed']
    cancelled_matches = [item for item in matches if item['status'] == 'cancelled']

    await call.message.edit_text(
        text=f'Количество пользователей: {users_count}\n'
             f'Количество завершенных матчей: {len(completed_matches)}\n'
             f'Количество отмененных матчей: {len(cancelled_matches)}\n',
        reply_markup=await kb_admin.kb_AdminBack('admin_main')
    )


@router.callback_query(F.data == 'admin_mail', IsCan(CAN_MAIL))
async def call_admin_statistics(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        text='Введите количество пользователей, которым будет отправлена рассылка',
        reply_markup=await kb_admin.kb_AdminBack('admin_main')
    )
    await state.set_state(Mailling.count)


@router.callback_query(F.data == 'admin_players', IsAdmin(True))
async def call_admin_players(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введите TelegramID/# игрока", reply_markup=await kb_admin.kb_AdminBack('admin_main'))
    await state.set_state(PlayerEntity.entity)


@router.callback_query(F.data == 'admin_matches', IsAdmin(True))
async def call_admin_matches(call: CallbackQuery):
    match_list = await GetAvailableMatches()

    await call.message.edit_text(
        text=f"Выберите матч ({len(match_list)})",
        reply_markup=await kb_admin.kb_AdminMatches(match_list=match_list, back_to='admin_main')
    )


@router.callback_query(F.data.startswith('admin_matches'), IsAdmin(True))
async def call_admin_match_manage(call: CallbackQuery):
    match_id = int(call.data.split('|')[1])

    await call.message.edit_text(
        text=f"Матч (id: {match_id})\n\nВыберите действие",
        reply_markup=await kb_admin.kb_AdminMatchManage(match_id=match_id, back_to='admin_matches')
    )


@router.callback_query(F.data.startswith('cancel_match'), IsAdmin(True))
async def call_cancel_match(call: CallbackQuery):
    match_id = int(call.data.split('|')[1])

    result = await CancelMatch(match_id=match_id)
    if result is True:

        await call.message.edit_text(
            text=f"Матч (id: {match_id}) успешо отменен",
            reply_markup=await kb_admin.kb_AdminBack(back_to='admin_matches')
        )
    else:
        await call.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith('tl_match'), IsAdmin(True))
async def call_tl_match(call: CallbackQuery):
    match_id = int(call.data.split('|')[1])
    tl_team = int(call.data.split('|')[2])

    team_winner = 1 if tl_team == 2 else 2

    result = await MatchTechLose(match_id=match_id, team_winner=team_winner)
    if result is True:

        await call.message.edit_text(
            text=f"Матч (id: {match_id}) успешо выдано ТП команде {tl_team}",
            reply_markup=await kb_admin.kb_AdminBack(back_to='admin_matches')
        )
    else:
        await call.answer("Произошла ошибка", show_alert=True)
