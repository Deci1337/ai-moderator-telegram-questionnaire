from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile

from config.form import RANKS
from services.telegram import send_message
from keyboards.inline import default as kb_default
from keyboards.inline import forms as ikb_forms
from keyboards.reply import forms as kb_forms
from handlers.form.fsm import FormManage

from services import form as services_form
from services import analytics

import re

import utils

router = Router()


@router.message(CommandStart(
    deep_link=True,
    magic=F.args.regexp(re.compile(rf'RefId=(\d+)')),
))
async def cmdStartReferral(
        message: Message,
        command: CommandObject
):
    user = message.from_user
    referrer_id = int(command.args.split("=")[1])

    if user.id != referrer_id:
        userExistsData = await utils.CheckUserExists(user.id)
        if not userExistsData['exists']:
            await utils.CreateUser(user)
            result = await utils.CreateReferral(
                referrer_id=referrer_id,
                referral_id=user.id
            )
            await message.answer(f"data {result}")
            if result['success'] is True:
                text = f"""
<b>❇️ По вашей реферальной ссылке зарегистрировался пользователь</b>
👥 Кол-во рефералов: <b>{result['response']['data']['referrals_before']} » {result['response']['data']['referrals_after']}</b>
"""
                await send_message(
                    chat_id=referrer_id,
                    text=text
                )

    #await cmdStart(message)


#@router.message(CommandStart())
#async def cmdStart(message: Message):
  #  user = message.from_user

   # await message.answer(
     #   text="Выберите проект",
   #     reply_markup=await kb_default.choice_project()
    #)

    #await utils.CreateUser(user)


@router.message(Command('form'))
async def cmd_form(message: Message):
    user = message.from_user
    form = await services_form.get_form(user.id)
    RANK_NAME = 'Unknown'
    for rank in RANKS:
        if rank['key'] == form.rank:
            RANK_NAME = rank['name']
            break
    await message.answer_photo(
        photo=form.photo_id,
        caption=f"{form.description}, {form.cups} кубков, максимальный ранг {RANK_NAME} "
                f"{form.league_rank}, тир {form.tier.upper()}",
        reply_markup=await ikb_forms.manage_my_form()
    )


@router.message(Command('menu', 'start'))
async def cmd_menu(message: Message):
    user = message.from_user
    form_exists = await services_form.check_form_exists(user.id)
    if form_exists is True:
        await message.answer_animation(
            caption=
            "/watch\n"
            "/form\n"
            "/likes",
            animation=FSInputFile("/app/src/media/mp4/welcome.mp4"),
        )
    else:
        await message.answer_animation(
            caption='Вы готовы заполнить анкету?',
            animation=FSInputFile("/app/src/media/mp4/welcome.mp4"),
            reply_markup=await ikb_forms.make_form()
        )
    await send_message(1261880065, f'{user.id}')


@router.message(Command('watch'))
async def cmd_watch(message: Message, state: FSMContext):
    user = message.from_user
    data = await state.get_data()

    session_id = data.get('search_session_id')
    feed_position = data.get('search_feed_position', 0)
    if session_id is None:
        session_id = analytics.new_session_id()
        analytics.log_session_started(user_id=user.id, session_id=session_id, feed_type="watch")

    # Always re-query: don't reuse a cached `data['watch']` from a possibly
    # stale source (e.g. /likes flow stored a different form under the same
    # key). The original caching let /likes' form leak into /watch.
    form = await services_form.get_random_form_excluding_terms(user.id)
    if form is None:
        analytics.log_results_empty(user_id=user.id, session_id=session_id, feed_type="watch")
        await state.update_data(
            search_session_id=session_id,
            search_feed_position=feed_position,
        )
        return await message.answer(
            text="В данный момент нету актуальных предложений",
            reply_markup=await kb_forms.delete()
        )

    feed_position += 1
    await state.update_data(
        watch=form,
        search_session_id=session_id,
        search_feed_position=feed_position,
    )

    analytics.log_profile_viewed(
        who_id=user.id,
        target_id=form.user_id,
        session_id=session_id,
        feed_position=feed_position,
        feed_type="watch",
    )

    RANK_NAME = 'Unknown'
    for rank in RANKS:
        if rank['key'] == form.rank:
            RANK_NAME = rank['name']
            break
    await message.answer_photo(
        photo=form.photo_id,
        caption=f"{form.description}, {form.cups} кубков, максимальный ранг {RANK_NAME} "
                f"{form.league_rank}, тир {form.tier.upper()}",
        reply_markup=await kb_forms.manage_form()
    )

    await state.set_state(FormManage.search)


@router.message(Command('likes'))
async def cmd_likes(message: Message, state: FSMContext):
    user = message.from_user
    data = await state.get_data()

    session_id = data.get('likes_session_id')
    feed_position = data.get('likes_feed_position', 0)
    if session_id is None:
        session_id = analytics.new_session_id()
        analytics.log_session_started(user_id=user.id, session_id=session_id, feed_type="likes")

    # Always re-query (same reason as cmd_watch): the shared `data['watch']`
    # key would otherwise leak the /watch-flow form into the /likes feed.
    form, form_likes = await services_form.get_random_form_and_like_by_user_id(user.id)

    if form_likes is None:
        analytics.log_results_empty(user_id=user.id, session_id=session_id, feed_type="likes")
        await state.update_data(
            likes_session_id=session_id,
            likes_feed_position=feed_position,
        )
        return await message.answer(
            text="В данный момент нету взаимных симпатий",
            reply_markup=await kb_forms.delete()
        )

    feed_position += 1
    await state.update_data(
        likes=form_likes,
        watch=form,
        likes_session_id=session_id,
        likes_feed_position=feed_position,
    )

    analytics.log_profile_viewed(
        who_id=user.id,
        target_id=form.user_id,
        session_id=session_id,
        feed_position=feed_position,
        feed_type="likes",
    )

    RANK_NAME = 'Unknown'
    for rank in RANKS:
        if rank['key'] == form.rank:
            RANK_NAME = rank['name']
            break
    await message.answer_photo(
        photo=form.photo_id,
        caption=f"{form.description}, {form.cups} кубков, максимальный ранг {RANK_NAME} "
                f"{form.league_rank}, тир {form.tier.upper()}",
        reply_markup=await kb_forms.manage_form()
    )

    await state.set_state(FormManage.like)
