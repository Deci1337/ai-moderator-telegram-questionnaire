from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.telegram import send_message, get_chat_member, get_chat

from aiogram.exceptions import TelegramBadRequest

router = APIRouter()


class SendMessageRequest(BaseModel):
    chat_id: int
    text: str


@router.post("/send-message")
async def send_message_controller(request: SendMessageRequest):
    """
    Send a message to a specific Telegram chat
    """
    try:
        result = await send_message(request.chat_id, request.text)
        return {
            "success": True,
            "message": "Message sent successfully",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": str(e)
            }
        )


class SponsorChannel(BaseModel):
    ID: int
    Link: str
    Name: str


class CheckSponsorsSubscribeRequest(BaseModel):
    telegram_id: int
    sponsors: List[SponsorChannel]


@router.post("/sponsors/check/subscribe")
async def check_sponsor_subscribe_controller(request: CheckSponsorsSubscribeRequest):
    try:
        await get_chat(chat_id=request.telegram_id)
    except TelegramBadRequest:
        print("User not found or bot doesn't have access to user")
        return {"result": False}
    except Exception as e:
        print(f"Unexpected error in get_chat: {e}")
        return {"result": False}

    try:
        result = True

        for sponsor in request.sponsors:
            try:
                response = await get_chat_member(
                    chat_id=sponsor.ID,
                    user_id=request.telegram_id
                )

                if response.status == 'left':
                    result = False
                    break

            except TelegramBadRequest:
                pass

        return {"result": result}

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=400,
            detail={"error": str(e)}
        )

