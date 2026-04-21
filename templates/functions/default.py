import asyncio
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest, TelegramNetworkError, TelegramForbiddenError
from config.bot import bot


async def mailling(max_users, users, message, method, **kwargs):
    successfull_sended = 0
    failed_sended = 0

    for user in users:
        if successfull_sended >= max_users:
            break
        try:
            await getattr(bot, method)(chat_id=user['telegram_id'],
                                       **kwargs)
            successfull_sended += 1
        except TelegramRetryAfter as e:
            print(f'Flood control: жду {e.retry_after} секунд...')
            await asyncio.sleep(e.retry_after)
            await getattr(bot, method)(chat_id=user['telegram_id'], **kwargs)
            successfull_sended += 1
        except (TelegramBadRequest, TelegramNetworkError, TelegramForbiddenError):
            failed_sended += 1
            continue
        await asyncio.sleep(0.5)

    await message.reply(f"<b>Рассылка завершена</b>\n"
                        f"Успешно отправлено: <b>{successfull_sended} / {len(users)}</b>\n"
                        f"Ошибок: <b>{failed_sended}</b>")
