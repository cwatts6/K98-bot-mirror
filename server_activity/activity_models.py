from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any


class ActivityEventType(StrEnum):
    MESSAGE = "message"
    REACTION_ADD = "reaction_add"
    VOICE_JOIN = "voice_join"
    VOICE_LEAVE = "voice_leave"
    VOICE_MOVE = "voice_move"


WINDOWS: dict[str, timedelta] = {
    "24h": timedelta(hours=24),
    "3d": timedelta(days=3),
    "7d": timedelta(days=7),
}


@dataclass(frozen=True)
class ActivityEvent:
    occurred_at_utc: datetime
    guild_id: int
    channel_id: int | None
    user_id: int
    event_type: ActivityEventType
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        ts = self.occurred_at_utc
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        object.__setattr__(self, "occurred_at_utc", ts.astimezone(UTC))


@dataclass(frozen=True)
class ActivityUserSummary:
    user_id: int
    score: int
    messages: int = 0
    reactions: int = 0
    voice_events: int = 0


@dataclass(frozen=True)
class ActivityTopResult:
    window: str
    since_utc: datetime
    rows: list[ActivityUserSummary]
