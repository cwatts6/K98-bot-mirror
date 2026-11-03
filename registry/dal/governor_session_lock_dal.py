"""Data access for reusable governor-scoped session locks."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _get_conn():
    from file_utils import get_conn_with_retries

    return get_conn_with_retries()


def _rows_to_dicts(cursor) -> list[dict[str, Any]]:
    while cursor.description is None:
        if not cursor.nextset():
            return []
    rows = cursor.fetchall()
    if not rows:
        return []
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row, strict=True)) for row in rows]


def acquire_lock(
    *,
    lock_scope: str,
    governor_id: str,
    user_id: int,
    expires_at_utc: datetime,
    now_utc: datetime | None = None,
) -> tuple[bool, dict[str, Any] | None]:
    """Acquire or renew a lock. Returns (acquired, current_holder)."""
    now = now_utc or datetime.now(UTC)
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SET XACT_ABORT ON;
            BEGIN TRAN;

            DELETE FROM dbo.GovernorSessionLocks
            WHERE ExpiresAtUTC <= ?;

            UPDATE dbo.GovernorSessionLocks WITH (UPDLOCK, HOLDLOCK)
            SET HolderDiscordUserID = ?,
                ExpiresAtUTC = ?,
                UpdatedAtUTC = ?
            WHERE LockScope = ?
              AND GovernorID = ?
              AND (HolderDiscordUserID = ? OR ExpiresAtUTC <= ?);

            IF @@ROWCOUNT = 0
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM dbo.GovernorSessionLocks WITH (UPDLOCK, HOLDLOCK)
                    WHERE LockScope = ?
                      AND GovernorID = ?
                      AND ExpiresAtUTC > ?
                )
                BEGIN
                    INSERT INTO dbo.GovernorSessionLocks
                        (LockScope, GovernorID, HolderDiscordUserID, ExpiresAtUTC, CreatedAtUTC, UpdatedAtUTC)
                    VALUES (?, ?, ?, ?, ?, ?);
                END
            END

            SELECT LockScope, GovernorID, HolderDiscordUserID, ExpiresAtUTC, CreatedAtUTC, UpdatedAtUTC
            FROM dbo.GovernorSessionLocks
            WHERE LockScope = ?
              AND GovernorID = ?;

            COMMIT;
            """,
            (
                now,
                int(user_id),
                expires_at_utc,
                now,
                lock_scope,
                str(governor_id),
                int(user_id),
                now,
                lock_scope,
                str(governor_id),
                now,
                lock_scope,
                str(governor_id),
                int(user_id),
                expires_at_utc,
                now,
                now,
                lock_scope,
                str(governor_id),
            ),
        )
        rows = _rows_to_dicts(cur)
        conn.commit()
        holder = rows[0] if rows else None
        acquired = bool(holder and int(holder["HolderDiscordUserID"]) == int(user_id))
        return acquired, holder
    except Exception:
        logger.exception(
            "governor_session_lock_acquire_failed scope=%s governor_id=%s user_id=%s",
            lock_scope,
            governor_id,
            user_id,
        )
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def refresh_lock(
    *,
    lock_scope: str,
    governor_id: str,
    user_id: int,
    expires_at_utc: datetime,
    now_utc: datetime | None = None,
) -> bool:
    now = now_utc or datetime.now(UTC)
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE dbo.GovernorSessionLocks
            SET ExpiresAtUTC = ?,
                UpdatedAtUTC = ?
            WHERE LockScope = ?
              AND GovernorID = ?
              AND HolderDiscordUserID = ?
              AND ExpiresAtUTC > ?;
            """,
            (expires_at_utc, now, lock_scope, str(governor_id), int(user_id), now),
        )
        changed = int(getattr(cur, "rowcount", 0) or 0) > 0
        conn.commit()
        return changed
    except Exception:
        logger.exception(
            "governor_session_lock_refresh_failed scope=%s governor_id=%s user_id=%s",
            lock_scope,
            governor_id,
            user_id,
        )
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def release_lock(*, lock_scope: str, governor_id: str, user_id: int) -> bool:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM dbo.GovernorSessionLocks
            WHERE LockScope = ?
              AND GovernorID = ?
              AND HolderDiscordUserID = ?;
            """,
            (lock_scope, str(governor_id), int(user_id)),
        )
        changed = int(getattr(cur, "rowcount", 0) or 0) > 0
        conn.commit()
        return changed
    except Exception:
        logger.exception(
            "governor_session_lock_release_failed scope=%s governor_id=%s user_id=%s",
            lock_scope,
            governor_id,
            user_id,
        )
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def cleanup_expired(*, now_utc: datetime | None = None) -> int:
    now = now_utc or datetime.now(UTC)
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM dbo.GovernorSessionLocks
            WHERE ExpiresAtUTC <= ?;
            """,
            (now,),
        )
        deleted = int(getattr(cur, "rowcount", 0) or 0)
        conn.commit()
        return deleted
    except Exception:
        logger.exception("governor_session_lock_cleanup_failed")
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass
