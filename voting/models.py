from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO


@dataclass(frozen=True)
class VoteOption:
    option_id: int
    vote_post_id: int
    option_key: str
    label: str
    sort_order: int
    button_style: str | None = None
    vote_count: int = 0


@dataclass(frozen=True)
class VoteReminder:
    reminder_id: int
    vote_post_id: int
    offset_minutes_before_close: int
    due_at_utc: datetime
    sent_at_utc: datetime | None = None
    message_id: int | None = None


@dataclass(frozen=True)
class VoteSnapshot:
    vote_post_id: int
    guild_id: int
    channel_id: int
    message_id: int | None
    created_by_discord_user_id: int
    title: str
    description: str | None
    status: str
    allow_vote_change: bool
    launch_mention_everyone: bool
    reminder_mention_everyone: bool
    close_mention_everyone: bool
    opens_at_utc: datetime | None
    closes_at_utc: datetime
    closed_at_utc: datetime | None
    closed_by_discord_user_id: int | None
    closed_reason: str | None
    background_asset_key: str | None
    total_votes: int
    created_at_utc: datetime
    updated_at_utc: datetime
    options: tuple[VoteOption, ...]
    reminders: tuple[VoteReminder, ...] = ()


@dataclass(frozen=True)
class VoteCreateRequest:
    guild_id: int
    channel_id: int
    created_by_discord_user_id: int
    title: str
    description: str | None
    options: tuple[str, ...]
    closes_at_utc: datetime
    reminder_offsets_minutes: tuple[int, ...]
    allow_vote_change: bool = True
    launch_mention_everyone: bool = False
    reminder_mention_everyone: bool = False
    close_mention_everyone: bool = False
    background_asset_key: str | None = None
    opens_at_utc: datetime | None = None


@dataclass(frozen=True)
class VoteCastResult:
    status: str
    vote_post_id: int
    option_id: int | None = None
    previous_option_id: int | None = None
    message: str = ""

    @property
    def accepted(self) -> bool:
        return self.status in {"recorded", "changed"}


@dataclass(frozen=True)
class VoteCloseResult:
    status: str
    vote_post_id: int
    message: str = ""

    @property
    def closed(self) -> bool:
        return self.status == "closed"


@dataclass(frozen=True)
class RenderedVoteCard:
    filename: str
    image_bytes: BytesIO
