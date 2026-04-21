import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)


async def PlayerSetElo(entity: any, elo: int):
    timeout = aiohttp.ClientTimeout(total=10)

    data = {
        'entity': entity,
        "elo": elo
    }

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post(
                url='http://api-gateway-service:8000/api/play-service/players/set-elo',
                json=data,
                headers={'Content-Type': 'application/json'},
            ) as response:

                response.raise_for_status()

                data = await response.json()

                return data.get("success", False)

        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP error {e.status}: {e.message}")
            return {}
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            return {}
        except asyncio.TimeoutError:
            logger.error("Request timeout")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {}


async def CancelMatch(match_id: int):
    timeout = aiohttp.ClientTimeout(total=10)

    data = {
        'match_id': match_id
    }

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post(
                url='http://api-gateway-service:8000/api/play-service/matches/cancel',
                json=data,
                headers={'Content-Type': 'application/json'},
            ) as response:

                response.raise_for_status()

                data = await response.json()

                return data.get("success", False)

        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP error {e.status}: {e.message}")
            return {}
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            return {}
        except asyncio.TimeoutError:
            logger.error("Request timeout")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {}


async def MatchTechLose(match_id: int, team_winner: int):
    timeout = aiohttp.ClientTimeout(total=10)

    data = {
        'match_id': match_id,
        "team_winner": team_winner
    }

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post(
                url='http://api-gateway-service:8000/api/play-service/matches/tech-lose',
                json=data,
                headers={'Content-Type': 'application/json'},
            ) as response:

                response.raise_for_status()

                data = await response.json()

                return data.get("success", False)

        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP error {e.status}: {e.message}")
            return {}
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            return {}
        except asyncio.TimeoutError:
            logger.error("Request timeout")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {}


async def GetMatches():
    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(
                url='http://api-gateway-service:8000/public/play-service/matches',
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


async def GetAvailableMatches():
    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(
                url='http://api-gateway-service:8000/public/play-service/matches/available',
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
