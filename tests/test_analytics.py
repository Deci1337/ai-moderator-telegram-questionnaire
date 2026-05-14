"""
Unit tests for the analytics layer.

No real DB, no real bot — `services.analytics.async_session_maker` is
monkey-patched with a fake session that records every add/commit call.
"""
import asyncio
import importlib.util
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Stub out env vars so config.database / config.bot import cleanly.
os.environ.setdefault("DB_USER", "x")
os.environ.setdefault("DB_PASSWORD", "x")
os.environ.setdefault("DB_HOST", "x")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "x")
os.environ.setdefault("BOT_TOKEN", "123456789:AAEhBP0av28cOwlrqzKEHwjqVbz4ECCqJtA")


# ── Fake DB session that records every event ────────────────────────────────


class _FakeSession:
    def __init__(self, log):
        self._log = log

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def add(self, obj):
        self._log.append({
            "event_type": obj.event_type,
            "user_id": obj.user_id,
            "target_id": obj.target_id,
            "session_id": obj.session_id,
            "payload": dict(obj.payload) if obj.payload else {},
        })

    async def commit(self):
        pass


@pytest.fixture
def captured(monkeypatch):
    import services.analytics as analytics

    log: list[dict] = []
    monkeypatch.setattr(analytics, "async_session_maker", lambda: _FakeSession(log))
    return analytics, log


async def _drain(analytics):
    # Yield to the loop until every fire-and-forget task has finished.
    while analytics._pending_tasks:
        await asyncio.sleep(0)


# ── new_session_id ───────────────────────────────────────────────────────────


def test_new_session_id_is_hex_string():
    import services.analytics as analytics

    sid = analytics.new_session_id()
    assert isinstance(sid, str)
    assert re.fullmatch(r"[0-9a-f]{32}", sid)


def test_new_session_id_is_unique():
    import services.analytics as analytics

    ids = {analytics.new_session_id() for _ in range(100)}
    assert len(ids) == 100


# ── log_* writers ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_log_session_started(captured):
    analytics, log = captured
    sid = analytics.new_session_id()
    analytics.log_session_started(user_id=1, session_id=sid, feed_type="watch")
    await _drain(analytics)

    assert len(log) == 1
    assert log[0] == {
        "event_type": "search_session_started",
        "user_id": 1,
        "target_id": None,
        "session_id": sid,
        "payload": {"feed_type": "watch"},
    }


@pytest.mark.asyncio
async def test_log_profile_viewed_carries_feed_position(captured):
    analytics, log = captured
    sid = analytics.new_session_id()
    analytics.log_profile_viewed(
        who_id=10, target_id=20, session_id=sid, feed_position=7, feed_type="likes",
    )
    await _drain(analytics)

    assert log[0]["event_type"] == "profile_viewed"
    assert log[0]["user_id"] == 10
    assert log[0]["target_id"] == 20
    assert log[0]["payload"] == {"feed_position": 7, "feed_type": "likes"}


@pytest.mark.asyncio
async def test_log_like_sent_marks_duplicates(captured):
    analytics, log = captured
    analytics.log_like_sent(who_id=1, target_id=2, session_id="s", is_duplicate=True)
    await _drain(analytics)

    assert log[0]["event_type"] == "like_sent"
    assert log[0]["payload"]["is_duplicate"] is True


@pytest.mark.asyncio
async def test_log_mutual_match_keeps_pair_metadata(captured):
    analytics, log = captured
    analytics.log_mutual_match(user_a=5, user_b=8, initiator_id=5, time_to_match_sec=42.5)
    await _drain(analytics)

    assert log[0]["event_type"] == "mutual_match_created"
    assert log[0]["payload"] == {
        "user_a": 5, "user_b": 8, "initiator_id": 5, "time_to_match_sec": 42.5,
    }


@pytest.mark.asyncio
async def test_log_results_empty(captured):
    analytics, log = captured
    analytics.log_results_empty(user_id=1, session_id="s", feed_type="watch")
    await _drain(analytics)

    assert log[0]["event_type"] == "search_results_empty"
    assert log[0]["payload"] == {"feed_type": "watch"}


@pytest.mark.asyncio
async def test_logging_swallows_db_errors(monkeypatch):
    """If the DB blows up, analytics must not propagate the exception."""
    import services.analytics as analytics

    class _BrokenSession:
        async def __aenter__(self):
            raise RuntimeError("db is down")
        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr(analytics, "async_session_maker", _BrokenSession)
    analytics.log_session_started(user_id=1, session_id="s")
    # Must not raise; just yield and let the safe-wrapper catch it.
    while analytics._pending_tasks:
        await asyncio.sleep(0)


def test_logging_outside_event_loop_drops_silently(monkeypatch):
    """Calling a logger from sync context must not crash the caller."""
    import services.analytics as analytics

    monkeypatch.setattr(analytics, "async_session_maker", lambda: _FakeSession([]))
    # Not inside asyncio.run(...) — no running loop.
    analytics.log_session_started(user_id=1, session_id="s")


# ── export_analytics.flatten ─────────────────────────────────────────────────


@pytest.fixture(scope="module")
def export_mod():
    spec = importlib.util.spec_from_file_location(
        "export_analytics_mod", str(REPO_ROOT / "export_analytics.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _row(event_type, payload, *, user_id=1, target_id=2, session_id="s"):
    return {
        "id": 1,
        "event_type": event_type,
        "user_id": user_id,
        "target_id": target_id,
        "session_id": session_id,
        "payload": payload,
        "created_at": datetime(2026, 5, 14, 12, 30, 45),
    }


def test_flatten_profile_viewed(export_mod):
    out = export_mod.flatten(_row("profile_viewed", {"feed_position": 3, "feed_type": "watch"}))
    assert out == {
        "event_type": "profile_viewed",
        "timestamp": "2026-05-14T12:30:45",
        "who_id": 1,
        "target_id": 2,
        "session_id": "s",
        "feed_position": 3,
        "feed_type": "watch",
    }


def test_flatten_like_sent(export_mod):
    out = export_mod.flatten(_row("like_sent", {"feed_type": "watch", "is_duplicate": False}))
    assert out["event_type"] == "like_sent"
    assert out["who_id"] == 1
    assert out["target_id"] == 2
    assert out["is_duplicate"] is False


def test_flatten_mutual_match(export_mod):
    payload = {"user_a": 2, "user_b": 1, "initiator_id": 2, "time_to_match_sec": 17.0}
    out = export_mod.flatten(_row("mutual_match_created", payload, user_id=2, target_id=1, session_id=None))
    assert out == {
        "event_type": "mutual_match_created",
        "timestamp": "2026-05-14T12:30:45",
        "user_a": 2,
        "user_b": 1,
        "initiator_id": 2,
        "time_to_match_sec": 17.0,
    }


def test_flatten_search_session_started(export_mod):
    out = export_mod.flatten(_row("search_session_started", {"feed_type": "watch"}, target_id=None))
    assert out == {
        "event_type": "search_session_started",
        "timestamp": "2026-05-14T12:30:45",
        "user_id": 1,
        "session_id": "s",
        "feed_type": "watch",
    }


def test_flatten_search_results_empty(export_mod):
    out = export_mod.flatten(_row("search_results_empty", {"feed_type": "likes"}, target_id=None))
    assert out["event_type"] == "search_results_empty"
    assert out["feed_type"] == "likes"


def test_flatten_unknown_event_keeps_payload(export_mod):
    out = export_mod.flatten(_row("weird_event", {"foo": "bar"}))
    assert out["event_type"] == "weird_event"
    assert out["payload"] == {"foo": "bar"}
