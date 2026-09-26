from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
import logging

from server_activity.activity_models import (
    WINDOWS,
    ActivityEvent,
    ActivityEventType,
    ActivityTopResult,
    ActivityUserSummary,
)
from server_activity.activity_store import fetch_activity_top_async, insert_activity_event_async

logger = logging.getLogger(__name__)


def now_utc() -> datetime:
    return datetime.now(UTC)


def normalize_activity_event(
    *,
    event_type: str | ActivityEventType,
    guild_id: int | None,
    channel_id: int | None,
    user_id: int | None,
    occurred_at_utc: datetime | None = None,
    metadata: dict | None = None,
) -> ActivityEvent | None:
    if not guild_id or not user_id:
        return None

    try:
        normalized_type = (
            event_type
            if isinstance(event_type, ActivityEventType)
            else ActivityEventType(event_type)
        )
    except ValueError:
        logger.warning("activity_event_ignored_unknown_type event_type=%s", event_type)
        return None

    return ActivityEvent(
        occurred_at_utc=occurred_at_utc or now_utc(),
        guild_id=int(guild_id),
        channel_id=int(channel_id) if channel_id is not None else None,
        user_id=int(user_id),
        event_type=normalized_type,
        metadata=metadata or None,
    )


async def record_activity_event(event: ActivityEvent | None) -> bool:
    if event is None:
        return False
    try:
        rowcount = await insert_activity_event_async(event)
        if rowcount < 0:
            logger.debug(
                "activity_event_persist_rowcount_unknown guild_id=%s user_id=%s type=%s rowcount=%s",
                event.guild_id,
                event.user_id,
                event.event_type.value,
                rowcount,
            )
        return True
    except Exception:
        logger.exception(
            "activity_event_persist_crashed guild_id=%s user_id=%s type=%s",
            event.guild_id,
            event.user_id,
            event.event_type.value,
        )
        return False


def resolve_window(window: str) -> str:
    normalized = str(window or "").strip().lower()
    if normalized not in WINDOWS:
        raise ValueError(f"Unsupported activity window: {window!r}")
    return normalized


def cutoff_for_window(window: str, *, as_of_utc: datetime | None = None) -> datetime:
    normalized = resolve_window(window)
    now = as_of_utc or now_utc()
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    return now.astimezone(UTC) - WINDOWS[normalized]


async def get_top_users(
    *,
    guild_id: int,
    window: str,
    limit: int = 10,
    as_of_utc: datetime | None = None,
) -> ActivityTopResult:
    normalized = resolve_window(window)
    since = cutoff_for_window(normalized, as_of_utc=as_of_utc)
    rows = await fetch_activity_top_async(guild_id=int(guild_id), since_utc=since, limit=limit)
    return ActivityTopResult(window=normalized, since_utc=since, rows=rows)


def aggregate_events(
    events: Iterable[ActivityEvent],
    *,
    since_utc: datetime,
    limit: int = 10,
) -> list[ActivityUserSummary]:
    """Pure aggregation helper used by tests and non-SQL callers."""
    if since_utc.tzinfo is None:
        since_utc = since_utc.replace(tzinfo=UTC)
    since_utc = since_utc.astimezone(UTC)

    totals: Counter[int] = Counter()
    messages: Counter[int] = Counter()
    reactions: Counter[int] = Counter()
    voice: Counter[int] = Counter()

    for event in events:
        if event.occurred_at_utc < since_utc:
            continue
        uid = int(event.user_id)
        totals[uid] += 1
        if event.event_type == ActivityEventType.MESSAGE:
            messages[uid] += 1
        elif event.event_type == ActivityEventType.REACTION_ADD:
            reactions[uid] += 1
        elif event.event_type in {
            ActivityEventType.VOICE_JOIN,
            ActivityEventType.VOICE_LEAVE,
            ActivityEventType.VOICE_MOVE,
        }:
            voice[uid] += 1

    summaries = [
        ActivityUserSummary(
            user_id=uid,
            score=score,
            messages=messages[uid],
            reactions=reactions[uid],
            voice_events=voice[uid],
        )
        for uid, score in totals.items()
    ]
    summaries.sort(
        key=lambda row: (-row.score, -row.messages, -row.reactions, -row.voice_events, row.user_id)
    )
    return summaries[: max(1, int(limit))]
