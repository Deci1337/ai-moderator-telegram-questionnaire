from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, FSInputFile

from datetime import datetime, timedelta

import services.form
import services.telegram
import services.analytics as analytics

from keyboards.inline import forms as kb_forms
from keyboards.inline import default as kb_default
from config.form import RANKS, SEARCHS

from .. import commands

router = Router()


class Form(StatesGroup):
    rank = State()
    league = State()
    cups = State()
    profile = State()
    tier = State()
    description = State()
    submitting = State()
    search = State()


class FormManage(StatesGroup):
    search = State()
    like = State()


@router.callback_query(Form.rank, F.data.startswith('form_rank'))
async def fsm_form_rank(call: CallbackQuery, state: FSMContext):
    form_rank = call.data.split('|')[1]
    await state.update_data(form_rank=form_rank)

    await call.message.edit_text(
        text='Выберите лигу',
        reply_markup=await kb_forms.max_league_rank('ankets_fortes')
    )

    await state.set_state(Form.league)


@router.callback_query(Form.league, F.data.startswith('form_league_rank'))
async def fsm_form_league_rank(call: CallbackQuery, state: FSMContext):
    form_league_rank = int(call.data.split('|')[1])
    await state.update_data(form_league_rank=form_league_rank)

    await call.message.delete()

    await call.message.answer_animation(
        caption='Укажи свои текущие кубки!',
        animation=FSInputFile("/app/src/media/mp4/current-cups.mp4")
    )

    await state.set_state(Form.cups)


@router.message(Form.cups, F.text)
async def fsm_form_cups(message: Message, state: FSMContext):
    try:
        cups = int(message.text)
    except (TypeError, ValueError):
        await message.answer("Отправьте число")
    else:
        await state.update_data(form_cups=cups)
        await message.answer_animation(
            caption='Укажи свои профиль!',
            animation=FSInputFile("/app/src/media/mp4/profile.mp4")
        )
        await state.set_state(Form.profile)


@router.message(Form.profile, F.photo)
async def fsm_form_profile(message: Message, state: FSMContext):
    photo = message.photo[-1].file_id
    await state.update_data(form_profile=photo)

    await message.answer_animation(
        caption='Укажи свой тир!',
        animation=FSInputFile("/app/src/media/mp4/tier.mp4"),
        reply_markup=await kb_forms.tier()
    )

    await state.set_state(Form.tier)


@router.callback_query(Form.tier, F.data.startswith('form_tier'))
async def fsm_form_tier(call: CallbackQuery, state: FSMContext):
    form_tier = call.data.split('|')[1]
    await state.update_data(form_tier=form_tier)

    await call.message.delete()

    await call.message.answer_animation(
        caption='Расскажи о себе!',
        animation=FSInputFile("/app/src/media/mp4/what-about.mp4"),
    )

    await state.set_state(Form.description)


@router.message(Form.description, F.text)
async def fsm_form_description(message: Message, state: FSMContext):
    await state.update_data(form_description=message.text)

    await message.answer_photo(
        photo=FSInputFile("/app/src/media/png/subscribe.png"),
        caption="<b>Подпишись</b> на канал нашего <b>бота</b>, чтобы быть в курсе <b>новостей</b>! — https://t.me/ffaesp",
        reply_markup=await kb_default.subscribe()
    )


@router.callback_query(Form.submitting, F.data == 'form_submit')
async def fsm_form_submit(call: CallbackQuery, state: FSMContext):
    await call.message.delete()

    await state.update_data(active_searchs=[])

    await call.message.answer(
        text='Что будем искать?',
        reply_markup=await kb_forms.search([])
    )
    await state.set_state(Form.search)


@router.callback_query(Form.search, F.data.startswith('form_search'))
async def fsm_form_search(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    form_search = call.data.split('|')[1]

    new_active_searchs = data['active_searchs']

    if form_search == 'all':
        if form_search in data['active_searchs']:
            new_active_searchs.clear()
        else:
            for search in SEARCHS:
                new_active_searchs.append(search)
    else:
        if form_search in data['active_searchs']:
            new_active_searchs.remove(form_search)
        else:
            new_active_searchs.append(form_search)

    await state.update_data(active_searchs=new_active_searchs)

    await call.message.edit_reply_markup(
        reply_markup=await kb_forms.search(new_active_searchs)
    )


@router.message(FormManage.search, F.text == '❤️')
async def fsm_FormManage_search_like(message: Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user

    target_user_id = data['watch'].user_id
    form_id = data['watch'].id
    session_id = data.get('search_session_id')
    feed_position = data.get('search_feed_position', 0)

    reverse_like = await services.form.get_reverse_like(
        viewer_id=user.id,
        target_id=target_user_id,
    )
    is_mutual = reverse_like is not None

    is_new = await services.form.create_form_like(
        user_id=target_user_id,
        form_id=form_id,
        liked_user_id=user.id
    )

    expiry_date = datetime.now() + timedelta(days=3)

    await services.form.create_form_term(
        user_id=user.id,
        form_id=form_id,
        expiry_date=expiry_date
    )

    analytics.log_like_sent(
        who_id=user.id,
        target_id=target_user_id,
        session_id=session_id,
        feed_type="watch",
        is_duplicate=not is_new,
    )

    if is_new and is_mutual:
        time_to_match_sec = max(
            0.0,
            (datetime.now() - reverse_like.created_at).total_seconds(),
        )
        analytics.log_mutual_match(
            user_a=reverse_like.liked_user_id,
            user_b=user.id,
            initiator_id=reverse_like.liked_user_id,
            time_to_match_sec=time_to_match_sec,
        )

    if is_new:
        notify_text = (
            'У вас есть взаимная симпатия'
            if is_mutual
            else 'Ваша анкета понравилась пользователю — посмотрите в /likes'
        )
        try:
            await services.telegram.send_message(
                chat_id=target_user_id,
                text=notify_text,
                reply_markup=await kb_forms.show_likes()
            )
        except Exception:
            # Target may have blocked the bot, deleted their account, or
            # never started a chat (test/seeded users). Don't let a notify
            # failure unwind the like flow — analytics already fired.
            pass

    await state.clear()
    await state.update_data(
        search_session_id=session_id,
        search_feed_position=feed_position,
    )

    await commands.cmd_watch(message, state)


@router.message(FormManage.search, F.text == '👎')
async def fsm_FormManage_search_dislike(message: Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user

    session_id = data.get('search_session_id')
    feed_position = data.get('search_feed_position', 0)

    expiry_date = datetime.now() + timedelta(days=14)

    await services.form.create_form_term(
        user_id=user.id,
        form_id=data['watch'].id,
        expiry_date=expiry_date
    )

    await state.clear()
    await state.update_data(
        search_session_id=session_id,
        search_feed_position=feed_position,
    )

    await commands.cmd_watch(message, state)


@router.message(FormManage.search, F.text == '🔄 Сменить поиски')
async def fsm_FormManage_search_edit_searchs(message: Message):
    pass


@router.message(FormManage.like, F.text == '❤️')
async def fsm_FormManage_likes_like(message: Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user

    likes_row = data['likes']
    initiator_id = likes_row.liked_user_id
    session_id = data.get('likes_session_id')
    feed_position = data.get('likes_feed_position', 0)

    try:
        await services.telegram.send_message(
            chat_id=initiator_id,
            text=f'У вас есть взаимная симпатия <a href="tg://user?id={user.id}">{user.first_name}</a>'
        )
    except:
        pass

    await message.answer(f'Приятного общения! <a href="tg://user?id={initiator_id}">Пользователь</a>')

    expiry_date = datetime.now() + timedelta(weeks=100)

    await services.form.create_form_term(
        user_id=user.id,
        form_id=data['watch'].id,
        expiry_date=expiry_date
    )

    await services.form.create_form_term(
        user_id=initiator_id,
        form_id=data['watch'].id,
        expiry_date=expiry_date
    )

    analytics.log_like_sent(
        who_id=user.id,
        target_id=initiator_id,
        session_id=session_id,
        feed_type="likes",
        is_duplicate=False,
    )
    time_to_match_sec = max(
        0.0,
        (datetime.now() - likes_row.created_at).total_seconds(),
    )
    analytics.log_mutual_match(
        user_a=initiator_id,
        user_b=user.id,
        initiator_id=initiator_id,
        time_to_match_sec=time_to_match_sec,
    )

    await services.form.delete_likes_by_liked_user_id(
        liked_user_id=initiator_id
    )

    await state.clear()
    await state.update_data(
        likes_session_id=session_id,
        likes_feed_position=feed_position,
    )

    await commands.cmd_likes(message, state)


@router.message(FormManage.like, F.text == '👎')
async def fsm_FormManage_likes_dislike(message: Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user

    session_id = data.get('likes_session_id')
    feed_position = data.get('likes_feed_position', 0)

    expiry_date = datetime.now() + timedelta(days=14)

    await services.form.create_form_term(
        user_id=user.id,
        form_id=data['watch'].id,
        expiry_date=expiry_date
    )

    await services.form.create_form_term(
        user_id=data['likes'].liked_user_id,
        form_id=data['watch'].id,
        expiry_date=expiry_date
    )

    await services.form.delete_likes_by_liked_user_id(
        liked_user_id=data['likes'].liked_user_id
    )

    await state.clear()
    await state.update_data(
        likes_session_id=session_id,
        likes_feed_position=feed_position,
    )

    await commands.cmd_likes(message, state)
