# registry_dal.py
"""
Data Access Layer for dbo.DiscordGovernorRegistry.

Responsibilities:
  - All SQL interaction for the registry table and stored procedures
  - Translate Python types → SQL parameters and SQL rows → plain dicts
  - Return codes match the stored procedure contracts (see below)

Not responsible for:
  - Business rules or validation          (→ registry_service.py)
  - Discord command handling              (→ commands/registry_cmds.py)
  - Import/export file I/O               (→ registry_io.py)

Connection:
  Uses get_conn_with_retries() from file_utils — same helper used by
  stats_alerts/db.py, MGE DAL, and Ark DAL.

Return code contract (matches stored procedures):
  0 = success / inserted
  1 = duplicate active slot  (DiscordUserID + AccountType)
  2 = duplicate active governor (GovernorID already registered to another user)
  3 = no active row found
  4 = skipped (import Skip mode)
  5 = overwritten (import Overwrite mode)
  9 = unexpected error
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------


def _get_conn():
    from file_utils import get_conn_with_retries

    return get_conn_with_retries()


# ---------------------------------------------------------------------------
# pyodbc OUTPUT parameter pattern
#
# pyodbc does not support Oracle-style cursor.var().
# The correct approach for SQL Server OUTPUT params is to wrap EXEC in a
# T-SQL block that DECLAREs local variables and SELECTs them back.
# ---------------------------------------------------------------------------

_SQL_INSERT = """
DECLARE
    @NewRegistrationID  BIGINT,
    @ResultCode         INT,
    @ResultMessage      NVARCHAR(500);

EXEC [dbo].[sp_Registry_Insert]
    @DiscordUserID      = ?,
    @DiscordName        = ?,
    @GovernorID         = ?,
    @GovernorName       = ?,
    @AccountType        = ?,
    @CreatedByDiscordID = ?,
    @Provenance         = ?,
    @NewRegistrationID  = @NewRegistrationID  OUTPUT,
    @ResultCode         = @ResultCode         OUTPUT,
    @ResultMessage      = @ResultMessage      OUTPUT;

SELECT @NewRegistrationID AS NewRegistrationID,
       @ResultCode        AS ResultCode,
       @ResultMessage     AS ResultMessage;
"""

_SQL_SOFT_DELETE = """
DECLARE
    @ResultCode     INT,
    @ResultMessage  NVARCHAR(500);

EXEC [dbo].[sp_Registry_SoftDelete]
    @RegistrationID     = ?,
    @DiscordUserID      = ?,
    @AccountType        = ?,
    @UpdatedByDiscordID = ?,
    @NewStatus          = ?,
    @ResultCode         = @ResultCode    OUTPUT,
    @ResultMessage      = @ResultMessage OUTPUT;

SELECT @ResultCode AS ResultCode, @ResultMessage AS ResultMessage;
"""

_SQL_UPSERT_IMPORT = """
DECLARE
    @NewRegistrationID  BIGINT,
    @ResultCode         INT,
    @ResultMessage      NVARCHAR(500);

EXEC [dbo].[sp_Registry_UpsertFromImport]
    @DiscordUserID      = ?,
    @DiscordName        = ?,
    @GovernorID         = ?,
    @GovernorName       = ?,
    @AccountType        = ?,
    @ActorDiscordID     = ?,
    @Provenance         = ?,
    @ConflictBehaviour  = ?,
    @NewRegistrationID  = @NewRegistrationID  OUTPUT,
    @ResultCode         = @ResultCode         OUTPUT,
    @ResultMessage      = @ResultMessage      OUTPUT;

SELECT @NewRegistrationID AS NewRegistrationID,
       @ResultCode        AS ResultCode,
       @ResultMessage     AS ResultMessage;
"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_output_row(cur) -> tuple[int, str]:
    """
    Read the SP output row and return (result_code, result_message).

    Handles two SP output shapes that exist across the registry SPs:
      3 columns: (NewID, ResultCode, ResultMessage)  — sp_Registry_Insert
      2 columns: (ResultCode, ResultMessage)          — sp_Registry_SoftDelete, sp_Registry_UpsertFromImport

    Returns (9, error_text) for any parse failure so callers always get
    a safe int result_code regardless of SP output shape.
    """
    row = cur.fetchone()
    if row is None:
        return 9, "No output row returned from stored procedure"

    try:
        n = len(row)
        if n >= 3:
            # Insert shape: (NewRegistrationID, ResultCode, ResultMessage)
            result_code = int(row[1]) if row[1] is not None else 9
            result_msg = str(row[2]) if row[2] is not None else ""
        elif n == 2:
            # Delete/update shape: (ResultCode, ResultMessage)
            result_code = int(row[0]) if row[0] is not None else 9
            result_msg = str(row[1]) if row[1] is not None else ""
        elif n == 1:
            # Minimal shape: just ResultCode
            result_code = int(row[0]) if row[0] is not None else 9
            result_msg = ""
        else:
            return 9, "Empty output row returned from stored procedure"
        return result_code, result_msg
    except (ValueError, TypeError, IndexError) as e:
        return 9, f"Failed to parse SP output row: {e!r}  row={row!r}"


def _rows_to_dicts(cursor) -> list[dict[str, Any]]:
    """Convert all fetched rows to list[dict] using column names from cursor.description."""
    rows = cursor.fetchall()
    if not rows:
        return []
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row, strict=True)) for row in rows]


# ---------------------------------------------------------------------------
# Public DAL functions
# ---------------------------------------------------------------------------


def insert(
    discord_user_id: int,
    discord_name: str | None,
    governor_id: int,
    governor_name: str | None,
    account_type: str,
    *,
    created_by: int | None = None,
    provenance: str = "bot_command",
) -> tuple[int, str]:
    """
    Insert a new Active registration via sp_Registry_Insert.

    Returns (result_code, result_message).
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            _SQL_INSERT,
            (
                discord_user_id,
                discord_name,
                governor_id,
                governor_name,
                account_type,
                created_by,
                provenance,
            ),
        )
        code, msg = _read_output_row(cur)
        conn.commit()
        return code, msg
    except Exception as exc:
        logger.exception(
            "[DAL] insert failed DiscordUserID=%s GovernorID=%s AccountType=%s",
            discord_user_id,
            governor_id,
            account_type,
        )
        try:
            conn.rollback()
        except Exception:
            pass
        return 9, str(exc)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def soft_delete(
    *,
    registration_id: int | None = None,
    discord_user_id: int | None = None,
    account_type: str | None = None,
    updated_by: int | None = None,
    new_status: str = "Removed",
) -> tuple[int, str]:
    """
    Soft-delete an Active registration via sp_Registry_SoftDelete.
    Target by registration_id, or by (discord_user_id + account_type).

    Returns (result_code, result_message).
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            _SQL_SOFT_DELETE,
            (registration_id, discord_user_id, account_type, updated_by, new_status),
        )
        code, msg = _read_output_row(cur)
        conn.commit()
        return code, msg
    except Exception as exc:
        logger.exception(
            "[DAL] soft_delete failed DiscordUserID=%s AccountType=%s",
            discord_user_id,
            account_type,
        )
        try:
            conn.rollback()
        except Exception:
            pass
        return 9, str(exc)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_by_discord_id(
    discord_user_id: int, *, status_filter: str = "Active"
) -> list[dict[str, Any]]:
    """
    Return all registrations for a Discord user via sp_Registry_GetByDiscordID.

    Raises on SQL failure — callers must handle explicitly.
    Returning an empty list silently would make SQL unavailability
    indistinguishable from "user has no registrations".
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "EXEC [dbo].[sp_Registry_GetByDiscordID] @DiscordUserID = ?, @StatusFilter = ?",
            (discord_user_id, status_filter),
        )
        return _rows_to_dicts(cur)
    except Exception:
        logger.exception("[DAL] get_by_discord_id failed DiscordUserID=%s", discord_user_id)
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_by_governor_id(governor_id: int, *, status_filter: str = "Active") -> dict[str, Any] | None:
    """
    Return the active registration row for a GovernorID, or None.
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "EXEC [dbo].[sp_Registry_GetByGovernorID] @GovernorID = ?, @StatusFilter = ?",
            (governor_id, status_filter),
        )
        rows = _rows_to_dicts(cur)
        return rows[0] if rows else None
    except Exception:
        logger.exception("[DAL] get_by_governor_id failed GovernorID=%s", governor_id)
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_all_active() -> list[dict[str, Any]]:
    """
    Return all Active registrations via sp_Registry_GetAllActive.

    Raises on SQL failure — callers must handle explicitly.
    Returning an empty list silently would make SQL unavailability
    indistinguishable from "registry is empty", causing audit and export
    commands to produce incorrect output without any indication of failure.
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("EXEC [dbo].[sp_Registry_GetAllActive]")
        return _rows_to_dicts(cur)
    except Exception:
        logger.exception("[DAL] get_all_active failed")
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def upsert_from_import(
    discord_user_id: int,
    discord_name: str | None,
    governor_id: int,
    governor_name: str | None,
    account_type: str,
    *,
    actor_discord_id: int | None = None,
    provenance: str = "import",
    conflict_behaviour: str = "Skip",
) -> tuple[int, str]:
    """
    Insert or replace a registration row via sp_Registry_UpsertFromImport.

    Returns (result_code, result_message).
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            _SQL_UPSERT_IMPORT,
            (
                discord_user_id,
                discord_name,
                governor_id,
                governor_name,
                account_type,
                actor_discord_id,
                provenance,
                conflict_behaviour,
            ),
        )
        code, msg = _read_output_row(cur)
        conn.commit()
        return code, msg
    except Exception as exc:
        logger.exception(
            "[DAL] upsert_from_import failed DiscordUserID=%s GovernorID=%s AccountType=%s",
            discord_user_id,
            governor_id,
            account_type,
        )
        try:
            conn.rollback()
        except Exception:
            pass
        return 9, str(exc)
    finally:
        try:
            conn.close()
        except Exception:
            pass
