from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
import os
import re

from voting import dal
from voting.models import (
    VoteCastResult,
    VoteCloseResult,
    VoteCreateRequest,
    VoteLookupChoice,
    VoteSnapshot,
)

logger = logging.getLogger(__name__)


def _option_label_length_from_env() -> int:
    raw = (os.getenv(OPTION_LABEL_LENGTH_ENV) or "").strip()
    if not raw:
        return DEFAULT_OPTION_LABEL_LEN
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{OPTION_LABEL_LENGTH_ENV} must be an integer.") from exc
    if value < 1 or value > DISCORD_OPTION_LABEL_MAX_LEN:
        raise RuntimeError(
            f"{OPTION_LABEL_LENGTH_ENV} must be between 1 and {DISCORD_OPTION_LABEL_MAX_LEN}."
        )
    return value


MAX_OPTIONS = 6
MIN_OPTIONS = 2
DISCORD_OPTION_LABEL_MAX_LEN = 80
DEFAULT_OPTION_LABEL_LEN = 20
OPTION_LABEL_LENGTH_ENV = "VOTE_OPTION_LABEL_MAX_LENGTH"
MAX_OPTION_LABEL_LEN = _option_label_length_from_env()
MAX_TITLE_LEN = 180
MAX_DESCRIPTION_LEN = 2000
MAX_CLOSE_REASON_LEN = 200
DEFAULT_REMINDER_OFFSETS = (60,)
CLOSE_DURATION_CHOICES: dict[str, timedelta] = {
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "2h": timedelta(hours=2),
    "4h": timedelta(hours=4),
    "8h": timedelta(hours=8),
    "12h": timedelta(hours=12),
    "1d": timedelta(days=1),
    "2d": timedelta(days=2),
    "3d": timedelta(days=3),
    "7d": timedelta(days=7),
}


class VoteValidationError(ValueError):
    """Raised when a vote request cannot be accepted."""


def _validate_description(value: str | None, *, blank_as_none: bool = True) -> str | None:
    clean_value = (value or "").strip()
    if len(clean_value) > MAX_DESCRIPTION_LEN:
        raise VoteValidationError(f"Description must be {MAX_DESCRIPTION_LEN} characters or fewer.")
    if blank_as_none and not clean_value:
        return None
    return clean_value


def _validate_close_reason(reason: str) -> str:
    clean_reason = (reason or "").strip() or "closed"
    if len(clean_reason) > MAX_CLOSE_REASON_LEN:
        raise VoteValidationError(
            f"Close reason must be {MAX_CLOSE_REASON_LEN} characters or fewer."
        )
    return clean_reason


def parse_utc_datetime(value: str) -> datetime:
    text = (value or "").strip()
    if not text:
        raise VoteValidationError("Close time is required.")
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                parsed = datetime.strptime(text, fmt).replace(tzinfo=UTC)
                break
            except ValueError:
                continue
        else:
            raise VoteValidationError("Use a UTC time like 2026-07-01 20:30 or ISO format.")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_close_time(value: str, *, now_utc: datetime | None = None) -> datetime:
    now = now_utc or datetime.now(UTC)
    text = (value or "").strip()
    duration = CLOSE_DURATION_CHOICES.get(text.casefold())
    if duration is not None:
        return now + duration
    return parse_utc_datetime(text)


def parse_option_labels(option_labels: tuple[str | None, ...]) -> tuple[str, ...]:
    labels = [str(label or "").strip() for label in option_labels]
    if len(labels) < MIN_OPTIONS or not labels[0] or not labels[1]:
        raise VoteValidationError("Option 1 and Option 2 are required.")

    output: list[str] = []
    found_blank = False
    for index, label in enumerate(labels):
        if not label:
            found_blank = True
            continue
        if found_blank:
            raise VoteValidationError(
                f"Option fields cannot skip a number; fill Option {index} before Option {index + 1}."
            )
        output.append(label)

    return _validate_options(output)


def _validate_options(parts: list[str]) -> tuple[str, ...]:
    if len(parts) < MIN_OPTIONS:
        raise VoteValidationError("Provide at least two options.")
    if len(parts) > MAX_OPTIONS:
        raise VoteValidationError(f"Votes support at most {MAX_OPTIONS} options.")
    seen: set[str] = set()
    output: list[str] = []
    for label in parts:
        if len(label) > MAX_OPTION_LABEL_LEN:
            raise VoteValidationError(
                f"Option labels must be {MAX_OPTION_LABEL_LEN} characters or fewer."
            )
        key = label.casefold()
        if key in seen:
            raise VoteValidationError("Options must be unique after trimming.")
        seen.add(key)
        output.append(label)
    return tuple(output)


def parse_options(raw_options: str) -> tuple[str, ...]:
    parts = [part.strip() for part in re.split(r"[|\n]", raw_options or "") if part.strip()]
    return _validate_options(parts)


def parse_reminder_offsets(raw_offsets: str | None) -> tuple[int, ...]:
    text = (raw_offsets or "").strip()
    if not text:
        return DEFAULT_REMINDER_OFFSETS
    values: set[int] = set()
    for piece in re.split(r"[,| ]+", text):
        if not piece:
            continue
        try:
            value = int(piece)
        except ValueError:
            raise VoteValidationError("Reminder offsets must be whole minutes before close.")
        if value <= 0:
            raise VoteValidationError("Reminder offsets must be positive minutes.")
        if value > 14 * 24 * 60:
            raise VoteValidationError("Reminder offsets cannot be more than 14 days.")
        values.add(value)
    return tuple(sorted(values, reverse=True))


def build_create_request(
    *,
    guild_id: int,
    channel_id: int,
    created_by_discord_user_id: int,
    title: str,
    description: str | None,
    close_time_utc: str,
    reminder_offsets: str | None,
    allow_vote_change: bool,
    launch_mention_everyone: bool,
    reminder_mention_everyone: bool,
    close_mention_everyone: bool,
    raw_options: str | None = None,
    option_labels: tuple[str | None, ...] | None = None,
    background_asset_key: str | None = None,
    now_utc: datetime | None = None,
) -> VoteCreateRequest:
    now = now_utc or datetime.now(UTC)
    normalized_title = (title or "").strip()
    if not normalized_title:
        raise VoteValidationError("Title is required.")
    if len(normalized_title) > MAX_TITLE_LEN:
        raise VoteValidationError(f"Title must be {MAX_TITLE_LEN} characters or fewer.")
    normalized_description = _validate_description(description)
    closes_at = parse_close_time(close_time_utc, now_utc=now)
    if closes_at <= now:
        raise VoteValidationError("Close time must be in the future.")
    offsets = tuple(
        offset
        for offset in parse_reminder_offsets(reminder_offsets)
        if closes_at.timestamp() - (offset * 60) > now.timestamp()
    )
    return VoteCreateRequest(
        guild_id=int(guild_id),
        channel_id=int(channel_id),
        created_by_discord_user_id=int(created_by_discord_user_id),
        title=normalized_title,
        description=normalized_description,
        options=(
            parse_option_labels(option_labels)
            if option_labels is not None
            else parse_options(raw_options or "")
        ),
        closes_at_utc=closes_at,
        reminder_offsets_minutes=offsets,
        allow_vote_change=bool(allow_vote_change),
        launch_mention_everyone=bool(launch_mention_everyone),
        reminder_mention_everyone=bool(reminder_mention_everyone),
        close_mention_everyone=bool(close_mention_everyone),
        background_asset_key=background_asset_key,
    )


async def create_vote_record(req: VoteCreateRequest) -> VoteSnapshot:
    vote_post_id = await dal.create_vote_post(req)
    if vote_post_id <= 0:
        raise RuntimeError("Vote post was not created.")
    snapshot = await dal.get_vote_snapshot(vote_post_id)
    if snapshot is None:
        raise RuntimeError("Vote post was created but could not be loaded.")
    logger.info(
        "vote_created vote_post_id=%s guild_id=%s channel_id=%s actor_discord_id=%s closes_at=%s",
        snapshot.vote_post_id,
        snapshot.guild_id,
        snapshot.channel_id,
        req.created_by_discord_user_id,
        snapshot.closes_at_utc.isoformat(),
    )
    return snapshot


async def attach_vote_message(
    snapshot: VoteSnapshot, *, channel_id: int, message_id: int
) -> VoteSnapshot:
    updated = await dal.update_vote_message(
        snapshot.vote_post_id, channel_id=channel_id, message_id=message_id
    )
    if not updated:
        raise RuntimeError("Vote post message identifiers could not be persisted.")
    refreshed = await dal.get_vote_snapshot(snapshot.vote_post_id)
    if refreshed is None:
        raise RuntimeError("Vote post could not be reloaded after launch.")
    return refreshed


async def cast_vote(
    *,
    vote_post_id: int,
    option_id: int,
    discord_user_id: int,
    now_utc: datetime | None = None,
) -> tuple[VoteCastResult, VoteSnapshot | None]:
    now = now_utc or datetime.now(UTC)
    result = await dal.cast_vote(
        vote_post_id=vote_post_id,
        option_id=option_id,
        discord_user_id=discord_user_id,
        now_utc=now,
    )
    snapshot = await dal.get_vote_snapshot(vote_post_id) if result.accepted else None
    if result.accepted:
        logger.info(
            "vote_cast status=%s vote_post_id=%s option_id=%s previous_option_id=%s actor_discord_id=%s",
            result.status,
            vote_post_id,
            result.option_id,
            result.previous_option_id,
            discord_user_id,
        )
    else:
        logger.info(
            "vote_rejected status=%s vote_post_id=%s option_id=%s actor_discord_id=%s",
            result.status,
            vote_post_id,
            option_id,
            discord_user_id,
        )
    return result, snapshot


async def close_vote(
    *,
    vote_post_id: int,
    actor_discord_user_id: int | None,
    reason: str,
    now_utc: datetime | None = None,
) -> tuple[VoteCloseResult, VoteSnapshot | None]:
    now = now_utc or datetime.now(UTC)
    clean_reason = _validate_close_reason(reason)
    result = await dal.close_vote(
        vote_post_id=vote_post_id,
        actor_discord_user_id=actor_discord_user_id,
        reason=clean_reason,
        now_utc=now,
    )
    snapshot = await dal.get_vote_snapshot(vote_post_id) if result.closed else None
    logger.info(
        "vote_close status=%s vote_post_id=%s actor_discord_id=%s reason=%s",
        result.status,
        vote_post_id,
        actor_discord_user_id,
        clean_reason,
    )
    return result, snapshot


async def cancel_vote_launch_failure(
    *,
    vote_post_id: int,
    actor_discord_user_id: int | None,
    reason: str = "launch failed",
    now_utc: datetime | None = None,
) -> bool:
    clean_reason = _validate_close_reason(reason)
    ok = await dal.cancel_vote_launch_failure(
        vote_post_id=vote_post_id,
        actor_discord_user_id=actor_discord_user_id,
        reason=clean_reason,
        now_utc=now_utc or datetime.now(UTC),
    )
    logger.info(
        "vote_launch_failure_cancelled=%s vote_post_id=%s actor_discord_id=%s reason=%s",
        ok,
        vote_post_id,
        actor_discord_user_id,
        clean_reason,
    )
    return ok


async def get_vote_snapshot(vote_post_id: int) -> VoteSnapshot | None:
    return await dal.get_vote_snapshot(vote_post_id)


async def search_vote_choices(
    query: str | None = None, *, limit: int = 25
) -> list[VoteLookupChoice]:
    return await dal.search_vote_posts(query=query, limit=limit)


async def record_message_edit_failed(
    *,
    vote_post_id: int,
    actor_discord_user_id: int | None,
    source: str,
) -> None:
    await dal.insert_audit(
        vote_post_id=vote_post_id,
        actor_discord_user_id=actor_discord_user_id,
        action_type="MessageEditFailed",
        details={"source": source},
    )


async def update_vote(
    *,
    vote_post_id: int,
    actor_discord_user_id: int,
    title: str | None = None,
    description: str | None = None,
    close_time_utc: str | None = None,
    reminder_offsets: str | None = None,
    reminder_mention_everyone: bool | None = None,
    close_mention_everyone: bool | None = None,
    now_utc: datetime | None = None,
) -> VoteSnapshot:
    now = now_utc or datetime.now(UTC)
    closes_at = parse_close_time(close_time_utc, now_utc=now) if close_time_utc else None
    if closes_at is not None and closes_at <= now:
        raise VoteValidationError("Updated close time must be in the future.")
    offsets = parse_reminder_offsets(reminder_offsets) if reminder_offsets is not None else None
    if offsets is not None:
        close_for_offsets = closes_at
        if close_for_offsets is None:
            current = await dal.get_vote_snapshot(vote_post_id)
            close_for_offsets = current.closes_at_utc if current is not None else None
        if close_for_offsets is not None:
            offsets = tuple(
                offset
                for offset in offsets
                if close_for_offsets.timestamp() - (offset * 60) > now.timestamp()
            )
    clean_title = (title or "").strip() if title is not None else None
    clean_description = (
        _validate_description(description, blank_as_none=False) if description is not None else None
    )
    if clean_title is not None and not clean_title:
        raise VoteValidationError("Title cannot be blank.")
    if clean_title is not None and len(clean_title) > MAX_TITLE_LEN:
        raise VoteValidationError(f"Title must be {MAX_TITLE_LEN} characters or fewer.")
    ok = await dal.update_vote_post(
        vote_post_id=vote_post_id,
        actor_discord_user_id=actor_discord_user_id,
        title=clean_title,
        description=clean_description,
        closes_at_utc=closes_at,
        reminder_offsets_minutes=offsets,
        reminder_mention_everyone=reminder_mention_everyone,
        close_mention_everyone=close_mention_everyone,
    )
    if not ok:
        raise VoteValidationError("Vote was not found or is already closed.")
    snapshot = await dal.get_vote_snapshot(vote_post_id)
    if snapshot is None:
        raise RuntimeError("Vote could not be loaded after update.")
    logger.info(
        "vote_updated vote_post_id=%s actor_discord_id=%s", vote_post_id, actor_discord_user_id
    )
    return snapshot
