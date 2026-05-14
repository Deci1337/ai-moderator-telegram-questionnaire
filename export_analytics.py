#!/usr/bin/env python3
"""
Export pride_academy.analytics_events to a flat JSON file matching the spec.

Usage:
    python export_analytics.py [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--out path.json] [--pretty]

DB connection is read from env vars (.env supported):
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
"""
import argparse
import json
import os
import sys
from datetime import datetime

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="ISO date or datetime; only events at/after this time",
    )
    parser.add_argument(
        "--until",
        type=str,
        default=None,
        help="ISO date or datetime; only events strictly before this time",
    )
    default_out = f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    parser.add_argument("--out", type=str, default=default_out, help="Output JSON path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    return parser.parse_args()


def flatten(row: dict) -> dict:
    payload = row["payload"] or {}
    ts = row["created_at"]
    ts_iso = ts.isoformat() if isinstance(ts, datetime) else str(ts)
    event_type = row["event_type"]
    base = {"event_type": event_type, "timestamp": ts_iso}

    if event_type == "profile_viewed":
        return {
            **base,
            "who_id": row["user_id"],
            "target_id": row["target_id"],
            "session_id": row["session_id"],
            "feed_position": payload.get("feed_position"),
            "feed_type": payload.get("feed_type", "watch"),
        }
    if event_type == "like_sent":
        return {
            **base,
            "who_id": row["user_id"],
            "target_id": row["target_id"],
            "session_id": row["session_id"],
            "feed_type": payload.get("feed_type", "watch"),
            "is_duplicate": payload.get("is_duplicate", False),
        }
    if event_type == "mutual_match_created":
        return {
            **base,
            "user_a": payload.get("user_a", row["user_id"]),
            "user_b": payload.get("user_b", row["target_id"]),
            "initiator_id": payload.get("initiator_id"),
            "time_to_match_sec": payload.get("time_to_match_sec"),
        }
    if event_type == "search_session_started":
        return {
            **base,
            "user_id": row["user_id"],
            "session_id": row["session_id"],
            "feed_type": payload.get("feed_type", "watch"),
        }
    if event_type == "search_results_empty":
        return {
            **base,
            "user_id": row["user_id"],
            "session_id": row["session_id"],
            "feed_type": payload.get("feed_type", "watch"),
        }

    return {
        **base,
        "user_id": row["user_id"],
        "target_id": row["target_id"],
        "session_id": row["session_id"],
        "payload": payload,
    }


def main() -> int:
    load_dotenv()
    args = parse_args()

    required = ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    missing = [v for v in required if v not in os.environ]
    if missing:
        print(f"Missing env vars: {', '.join(missing)}", file=sys.stderr)
        return 1

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME"),
    )
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        sql = (
            "SELECT id, event_type, user_id, target_id, session_id, "
            "       payload, created_at "
            "FROM pride_academy.analytics_events"
        )
        clauses: list[str] = []
        params: list = []
        if args.since:
            clauses.append("created_at >= %s")
            params.append(args.since)
        if args.until:
            clauses.append("created_at < %s")
            params.append(args.until)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at ASC, id ASC"

        cur.execute(sql, params)
        rows = cur.fetchall()

        events = [flatten(dict(r)) for r in rows]

        with open(args.out, "w", encoding="utf-8") as f:
            if args.pretty:
                json.dump(events, f, ensure_ascii=False, indent=2)
            else:
                json.dump(events, f, ensure_ascii=False)
        print(f"Exported {len(events)} events to {args.out}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
