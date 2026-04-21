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

    form = await services_form.get_random_form_excluding_terms(user.id) if data.get('watch') is None else data['watch']
    if form is None:
        return await message.answer(
            text="В данный момент нету актуальных предложений",
            reply_markup=await kb_forms.delete()
        )

    await state.update_data(watch=form)

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

    form, form_likes = (await services_form.get_random_form_and_like_by_user_id(user.id)
                        if data.get('likes') is None or data.get('watch') is None
                        else (data['watch'], data['likes']))

    if form_likes is None:
        return await message.answer(
            text="В данный момент нету взаимных симпатий",
            reply_markup=await kb_forms.delete()
        )

    await state.update_data(likes=form_likes, watch=form)

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
