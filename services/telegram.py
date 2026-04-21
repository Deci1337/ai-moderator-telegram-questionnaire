from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from config.bot import bot


async def send_message(chat_id: int, text: str, reply_markup = None, parse_mode = 'html') -> dict:
    """
    Send a message to a specific chat

    Args:
        chat_id: Telegram chat ID
        text: Message text to send

    Returns:
        dict with success status and message info or error
    """
    try:
        message = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
        return {
            "success": True,
            "message_id": message.message_id,
            "chat_id": message.chat.id,
            "text": message.text
        }
    except TelegramForbiddenError:
        raise Exception("Bot was blocked by the user or chat not found")
    except TelegramBadRequest as e:
        raise Exception(f"Bad request: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to send message: {str(e)}")


async def get_chat_member(chat_id: int, user_id: int):
    try:
        result = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return result
    except TelegramBadRequest as e:
        print(f'get_chat_member bad req: {e}')
        raise
    except Exception as e:
        raise Exception(f"Failed to get chat member: {str(e)}")


async def get_chat(chat_id: int):
    try:
        result = await bot.get_chat(chat_id=chat_id)
        return result
    except TelegramBadRequest as e:
        print(f'get_chat bad req: {e}')
        raise
    except Exception as e:
        raise Exception(f"Failed to get chat: {str(e)}")
