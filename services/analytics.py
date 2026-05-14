import asyncio
import logging
import uuid
from typing import Any, Awaitable, Optional

from config.database import async_session_maker
from models.analytics_event import AnalyticsEvent

logger = logging.getLogger(__name__)


EVENT_PROFILE_VIEWED = "profile_viewed"
EVENT_LIKE_SENT = "like_sent"
EVENT_MUTUAL_MATCH_CREATED = "mutual_match_created"
EVENT_SEARCH_SESSION_STARTED = "search_session_started"
EVENT_SEARCH_RESULTS_EMPTY = "search_results_empty"


def new_session_id() -> str:
    return uuid.uuid4().hex


async def _persist(
    event_type: str,
    *,
    user_id: Optional[int] = None,
    target_id: Optional[int] = None,
    session_id: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
) -> None:
    async with async_session_maker() as session:
        event = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            target_id=target_id,
            session_id=session_id,
            payload=payload or {},
        )
        session.add(event)
        await session.commit()


# Hold strong refs to in-flight tasks so the GC doesn't collect them mid-flight.
_pending_tasks: set[asyncio.Task] = set()


def _fire(coro: Awaitable[None]) -> None:
    """Fire-and-forget: analytics never blocks UX or breaks the bot."""
    async def _safe() -> None:
        try:
            await coro
        except Exception:
            logger.exception("analytics: failed to persist event")

    try:
        task = asyncio.create_task(_safe())
    except RuntimeError:
        # No running loop — caller is outside an async context. Drop the event
        # rather than blow up; analytics is best-effort.
        logger.warning("analytics: no running loop, event dropped")
        return
    _pending_tasks.add(task)
    task.add_done_callback(_pending_tasks.discard)


def log_session_started(*, user_id: int, session_id: str, feed_type: str = "watch") -> None:
    _fire(_persist(
        EVENT_SEARCH_SESSION_STARTED,
        user_id=user_id,
        session_id=session_id,
        payload={"feed_type": feed_type},
    ))


def log_profile_viewed(
    *,
    who_id: int,
    target_id: int,
    session_id: str,
    feed_position: int,
    feed_type: str = "watch",
) -> None:
    _fire(_persist(
        EVENT_PROFILE_VIEWED,
        user_id=who_id,
        target_id=target_id,
        session_id=session_id,
        payload={"feed_position": feed_position, "feed_type": feed_type},
    ))


def log_like_sent(
    *,
    who_id: int,
    target_id: int,
    session_id: Optional[str],
    feed_type: str = "watch",
    is_duplicate: bool = False,
) -> None:
    _fire(_persist(
        EVENT_LIKE_SENT,
        user_id=who_id,
        target_id=target_id,
        session_id=session_id,
        payload={"feed_type": feed_type, "is_duplicate": is_duplicate},
    ))


def log_mutual_match(
    *,
    user_a: int,
    user_b: int,
    initiator_id: int,
    time_to_match_sec: float,
) -> None:
    _fire(_persist(
        EVENT_MUTUAL_MATCH_CREATED,
        user_id=user_a,
        target_id=user_b,
        payload={
            "user_a": user_a,
            "user_b": user_b,
            "initiator_id": initiator_id,
            "time_to_match_sec": time_to_match_sec,
        },
    ))


def log_results_empty(*, user_id: int, session_id: Optional[str], feed_type: str = "watch") -> None:
    _fire(_persist(
        EVENT_SEARCH_RESULTS_EMPTY,
        user_id=user_id,
        session_id=session_id,
        payload={"feed_type": feed_type},
    ))
