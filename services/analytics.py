import asyncio
import logging
import uuid
from datetime import datetime, timezone
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
    created_at: datetime,
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
            created_at=created_at,
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

    inner = _safe()
    try:
        task = asyncio.create_task(inner)
    except RuntimeError:
        # No running loop — caller is outside an async context. Drop the
        # event rather than blow up; analytics is best-effort. Close the
        # unscheduled coroutines so they don't show up as "never awaited".
        inner.close()
        close = getattr(coro, "close", None)
        if callable(close):
            close()
        logger.warning("analytics: no running loop, event dropped")
        return
    _pending_tasks.add(task)
    task.add_done_callback(_pending_tasks.discard)


def _now() -> datetime:
    """Wall-clock timestamp captured at the moment the caller emitted the event.

    Stamping Python-side (rather than relying on Postgres' `now()` server-default
    at INSERT time) keeps events strictly ordered in the order they fired,
    regardless of how the fire-and-forget background tasks happen to race
    against each other on the way to the database.
    """
    return datetime.now(timezone.utc)


def log_session_started(*, user_id: int, session_id: str, feed_type: str = "watch") -> None:
    _fire(_persist(
        EVENT_SEARCH_SESSION_STARTED,
        created_at=_now(),
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
        created_at=_now(),
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
        created_at=_now(),
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
        created_at=_now(),
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
        created_at=_now(),
        user_id=user_id,
        session_id=session_id,
        payload={"feed_type": feed_type},
    ))
