from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery

from config.form import RANKS
from keyboards.inline import forms as ikb_forms
from keyboards.reply import forms as kb_forms
from .fsm import Form, FormManage
from services import form as services_form
from services.moderation import moderate_form


router = Router()


@router.callback_query(F.data == 'ankets_fortes')
async def call_ankets_fortes(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer(
        text='<b>Начнем заполнение анкеты</b>\n'
             'Ваш максимальный рейтинговый ранг?',
        reply_markup=await ikb_forms.max_rank()
    )
    await state.set_state(Form.rank)


@router.callback_query(StateFilter('*'), F.data == 'send_form')
async def call_send_form(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    user = call.from_user

    await call.message.edit_text(text="⏳ Проверяем анкету...")

    is_ok, reason = await moderate_form(
        photo_file_id=data["form_profile"],
        description=data["form_description"],
    )

    if not is_ok:
        await call.message.edit_text(
            text=(
                f"❌ <b>Анкета не прошла проверку</b>\n\n"
                f"{reason}\n\n"
                f"Пожалуйста, исправьте анкету и попробуйте снова."
            ),
            reply_markup=await ikb_forms.retry_form()
        )
        return

    searchs_str = ', '.join(data["active_searchs"])

    await services_form.create_form(
        user_id=user.id,
        cups=data['form_cups'],
        photo_id=data["form_profile"],
        tier=data["form_tier"],
        description=data["form_description"],
        searchs=searchs_str,
        rank=data["form_rank"],
        league_rank=data["form_league_rank"],
    )

    await state.clear()
    await call.message.edit_text(
        text="✅ Анкета успешно создана",
        reply_markup=await ikb_forms.finish_form()
    )


@router.callback_query(F.data == 'watch_forms')
async def call_watch_forms(call: CallbackQuery, state: FSMContext):
    user = call.from_user
    data = await state.get_data()

    form = await services_form.get_random_form_excluding_terms(user.id) if data.get('watch') is None else data['watch']
    if form is None:
        return await call.message.answer(
            text="В данный момент нету актуальных предложений",
            reply_markup=await kb_forms.delete()
        )

    await state.update_data(watch=form)

    RANK_NAME = 'Unknown'
    for rank in RANKS:
        if rank['key'] == form.rank:
            RANK_NAME = rank['name']
            break
    await call.message.delete()
    await call.message.answer_photo(
        photo=form.photo_id,
        caption=f"{form.description}, {form.cups} кубков, максимальный ранг {RANK_NAME} "
                f"{form.league_rank}, тир {form.tier.upper()}",
        reply_markup=await kb_forms.manage_form()
    )

    await state.set_state(FormManage.search)


@router.callback_query(F.data == 'my_form')
async def call_my_form(call: CallbackQuery):
    user = call.from_user
    form = await services_form.get_form(user.id)
    RANK_NAME = 'Unknown'
    for rank in RANKS:
        if rank['key'] == form.rank:
            RANK_NAME = rank['name']
            break

    await call.message.delete()
    await call.message.answer_photo(
        photo=form.photo_id,
        caption=f"{form.description}, {form.cups} кубков, максимальный ранг {RANK_NAME} "
                f"{form.league_rank}, тир {form.tier.upper()}",
        reply_markup=await ikb_forms.manage_my_form()
    )


@router.callback_query(StateFilter('*'), F.data == 'watch_likes')
async def call_watch_likes(call: CallbackQuery, state: FSMContext):
    user = call.from_user
    data = await state.get_data()

    form, form_likes = (await services_form.get_random_form_and_like_by_user_id(user.id)
                        if data.get('likes') is None or data.get('watch') is None
                        else (data['watch'], data['likes']))

    if form_likes is None:
        return await call.message.answer(
            text="В данный момент нету взаимных симпатий",
            reply_markup=await kb_forms.delete()
        )

    await state.update_data(likes=form_likes, watch=form)

    RANK_NAME = 'Unknown'
    for rank in RANKS:
        if rank['key'] == form.rank:
            RANK_NAME = rank['name']
            break
    await call.message.answer_photo(
        photo=form.photo_id,
        caption=f"{form.description}, {form.cups} кубков, максимальный ранг {RANK_NAME} "
                f"{form.league_rank}, тир {form.tier.upper()}",
        reply_markup=await kb_forms.manage_form()
    )

    await state.set_state(FormManage.like)


@router.callback_query(StateFilter('*'), F.data == 'subscribe_skip')
async def call_subscribe_skip(call: CallbackQuery, state: FSMContext):
    await call.message.delete()

    data = await state.get_data()
    await call.message.answer('Ваша анкета:')
    RANK_NAME = 'Unknown'
    for rank in RANKS:
        if rank['key'] == data['form_rank']:
            RANK_NAME = rank['name']
            break
    await call.message.answer_photo(
        photo=data['form_profile'],
        caption=f"{data['form_description']}, {data['form_cups']} кубков, максимальный ранг {RANK_NAME} "
                f"{data['form_league_rank']}, тир {str(data['form_tier']).upper()}",
        reply_markup=await ikb_forms.submit()
    )
    await state.set_state(Form.submitting)
