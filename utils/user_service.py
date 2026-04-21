import aiohttp
import logging
import asyncio
import generators
import os
from typing import Dict, Optional
from aiogram.types import User

logger = logging.getLogger(__name__)


async def GetUsersCount():
    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(
                url='http://api-gateway-service:8000/api/user-service/users/count',
                headers={'Content-Type': 'application/json'},
            ) as response:

                response.raise_for_status()

                data = await response.json()

                if isinstance(data, dict) and data.get("success"):
                    return data.get("data", 0)

                logger.warning(f"Unexpected response structure: {data}")
                return []

        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP error {e.status}: {e.message}")
            return []
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            return []
        except asyncio.TimeoutError:
            logger.error("Request timeout")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []


async def GetUsers():
    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(
                url='http://api-gateway-service:8000/api/user-service/users',
                headers={'Content-Type': 'application/json'},
            ) as response:

                response.raise_for_status()

                data = await response.json()

                if isinstance(data, dict) and data.get("success"):
                    return data.get("data", [])

                logger.warning(f"Unexpected response structure: {data}")
                return []

        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP error {e.status}: {e.message}")
            return []
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            return []
        except asyncio.TimeoutError:
            logger.error("Request timeout")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []


async def CreateUser(user: User) -> bool:
    user_data = {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "language_code": user.language_code,
    }

    tgWebAppData = await generators.generateInitData(
        bot_token=os.getenv("BOT_TOKEN"),
        user_data=user_data
    )

    data = {
        'tgWebAppData': tgWebAppData,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url='http://api-gateway-service:5000/public/user-service/users',
            headers={'Content-Type': 'application/json'},
            json=data,
        ) as response:
            if response.status != 200:
                logger.error(f"Error on create user")
                return False
    return True


async def CreateReferral(referral_id: int, referrer_id: int) -> dict:
    data = {
        'referral_id': referral_id,
        'referrer_id': referrer_id,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url='http://api-gateway-service:5000/api/referral-service/referrals',
            headers={'Content-Type': 'application/json'},
            json=data,
        ) as response:
            if response.status != 200:
                logger.error(f"Error on create referral")
                return {"success": False}

            data = await response.json()

    return {"success": True, "response": data}


async def CheckUserExists(telegram_id: int) -> Dict[str, bool]:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url='http://api-gateway-service:5000/api/user-service/users/check',
            params={'telegram_id': telegram_id}
        ) as response:
            if response.status == 200:
                data = await response.json()
                return {"exists": data.get("exists")}
            else:
                logger.error(f"Error checking user: {response.status}")
                return {"exists": False}
