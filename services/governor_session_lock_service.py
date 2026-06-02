"""Restart-safe governor session locking service."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from registry.dal import governor_session_lock_dal

logger = logging.getLogger(__name__)

DEFAULT_LOCK_SCOPE = "crystaltech"
DEFAULT_TTL = timedelta(minutes=10)


@dataclass(frozen=True, slots=True)
class LockResult:
    acquired: bool
    message: str = ""
    holder_user_id: int | None = None
    expires_at_utc: datetime | None = None


def _aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _holder_from_row(row: dict[str, Any] | None) -> tuple[int | None, datetime | None]:
    if not row:
        return None, None
    holder = row.get("HolderDiscordUserID")
    expires = _aware_utc(row.get("ExpiresAtUTC"))
    try:
        holder_id = int(holder) if holder is not None else None
    except (TypeError, ValueError):
        holder_id = None
    return holder_id, expires


async def claim_governor_session(
    governor_id: str,
    user_id: int,
    *,
    lock_scope: str = DEFAULT_LOCK_SCOPE,
    ttl: timedelta = DEFAULT_TTL,
    now_utc: datetime | None = None,
) -> LockResult:
    """Acquire a governor lock for a user, renewing the lock if the user already holds it."""
    now = _aware_utc(now_utc) or datetime.now(UTC)
    expires = now + ttl
    acquired, holder = await asyncio.to_thread(
        governor_session_lock_dal.acquire_lock,
        lock_scope=lock_scope,
        governor_id=str(governor_id),
        user_id=int(user_id),
        expires_at_utc=expires,
        now_utc=now,
    )
    holder_user_id, holder_expires = _holder_from_row(holder)
    if acquired:
        logger.info(
            "governor_session_lock_claimed scope=%s governor_id=%s user_id=%s expires=%s",
            lock_scope,
            governor_id,
            user_id,
            expires.isoformat(),
        )
        return LockResult(True, holder_user_id=holder_user_id, expires_at_utc=holder_expires)

    return LockResult(
        False,
        "This governor is currently being edited by another user. Try again in a few minutes.",
        holder_user_id=holder_user_id,
        expires_at_utc=holder_expires,
    )


async def refresh_governor_session(
    governor_id: str,
    user_id: int,
    *,
    lock_scope: str = DEFAULT_LOCK_SCOPE,
    ttl: timedelta = DEFAULT_TTL,
    now_utc: datetime | None = None,
) -> bool:
    now = _aware_utc(now_utc) or datetime.now(UTC)
    return await asyncio.to_thread(
        governor_session_lock_dal.refresh_lock,
        lock_scope=lock_scope,
        governor_id=str(governor_id),
        user_id=int(user_id),
        expires_at_utc=now + ttl,
        now_utc=now,
    )


async def release_governor_session(
    governor_id: str,
    user_id: int,
    *,
    lock_scope: str = DEFAULT_LOCK_SCOPE,
) -> bool:
    return await asyncio.to_thread(
        governor_session_lock_dal.release_lock,
        lock_scope=lock_scope,
        governor_id=str(governor_id),
        user_id=int(user_id),
    )


async def cleanup_expired_governor_sessions(*, now_utc: datetime | None = None) -> int:
    now = _aware_utc(now_utc) or datetime.now(UTC)
    return await asyncio.to_thread(governor_session_lock_dal.cleanup_expired, now_utc=now)
