import os
import re
import base64
import logging
import io
import asyncio
import json
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

# Patterns that are always rejected without calling OpenAI
_TEXT_BAN_RE = re.compile(
    r"(https?://|t\.me/|@|\+?[78][\s\-]?\(?\d{3}\)?"
    r"[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})",
    re.IGNORECASE,
)

# Flood: same char repeated 6+ times
_FLOOD_RE = re.compile(r"(.)\1{5,}")


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def _check_text_rules(text: str) -> tuple[bool, str]:
    """Fast regex pre-check — no AI needed for obvious violations."""
    if _TEXT_BAN_RE.search(text):
        return False, "Запрещены ссылки, теги (@...) и номера телефонов"
    if _FLOOD_RE.search(text):
        return False, "Текст содержит флуд"
    if len(text) > 500:
        return False, "Описание слишком длинное (максимум 500 символов)"
    return True, ""


async def _download_telegram_photo(file_id: str) -> bytes:
    """Download photo bytes from Telegram and resize to save tokens."""
    from config.bot import bot
    file = await bot.get_file(file_id)
    result = await bot.download_file(file.file_path)
    raw = result.read()

    try:
        from PIL import Image
        img = Image.open(io.BytesIO(raw))
        img.thumbnail((384, 384), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=60)
        return buf.getvalue()
    except Exception:
        return raw


async def moderate_photo(file_id: str) -> tuple[bool, str]:
    try:
        photo_bytes = await _download_telegram_photo(file_id)
        b64_image = base64.b64encode(photo_bytes).decode("utf-8")

        client = _get_client()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Модератор анкет для Brawl Stars. "
                                "ПРИНЯТЬ ТОЛЬКО если на фото виден реальный интерфейс игры Brawl Stars: "
                                "экран профиля игрока с никнеймом/трофеями/бравлерами, статистика аккаунта, "
                                "экран боя/результатов матча, коллекция бравлеров. "
                                "ОТКЛОНИТЬ если: просто логотип или надпись 'Brawl Stars', фан-арт, арт персонажа без интерфейса, "
                                "лицо человека, мем, случайное фото, NSFW, насилие. "
                                "JSON: {\"ok\":bool,\"reason\":\"\"}"
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_image}",
                                "detail": "low",
                            },
                        },
                    ],
                }
            ],
            max_tokens=60,
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)
        return bool(data.get("ok", False)), str(data.get("reason", ""))

    except Exception as e:
        logger.warning("Photo moderation error: %s — allowing", e)
        return True, ""


async def moderate_text(description: str) -> tuple[bool, str]:
    if not description or not description.strip():
        return True, ""

    # Fast rules first — no API call needed
    ok, reason = _check_text_rules(description)
    if not ok:
        return False, reason

    # Only call AI for ad/spam/NSFW detection that regex can't catch
    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Модератор Brawl Stars. "
                        "ОТКЛОНИТЬ только если: реклама/продажа аккаунтов, угрозы, NSFW. "
                        "Всё остальное — ПРИНЯТЬ. "
                        "JSON: {\"ok\":bool,\"reason\":\"\"}"
                    ),
                },
                {"role": "user", "content": description[:300]},
            ],
            max_tokens=60,
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)
        return bool(data.get("ok", False)), str(data.get("reason", ""))

    except Exception as e:
        logger.warning("Text moderation error: %s — allowing", e)
        return True, ""


async def moderate_form(photo_file_id: str, description: str) -> tuple[bool, str]:
    # Pre-check text with regex — if already bad, skip photo AI call too
    text_ok, text_reason = _check_text_rules(description)
    if not text_ok:
        return False, f"Описание не прошло проверку: {text_reason}"

    # Run both AI checks in parallel
    photo_result, text_result = await asyncio.gather(
        moderate_photo(photo_file_id),
        moderate_text(description),
    )

    photo_ok, photo_reason = photo_result
    text_ok, text_reason = text_result

    if not photo_ok and not text_ok:
        return False, f"Фото: {photo_reason}. Текст: {text_reason}"
    if not photo_ok:
        return False, f"Фото не прошло проверку: {photo_reason}"
    if not text_ok:
        return False, f"Описание не прошло проверку: {text_reason}"

    return True, ""
