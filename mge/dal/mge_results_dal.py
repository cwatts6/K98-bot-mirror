from __future__ import annotations

from datetime import UTC, datetime
import json
from typing import Any, Literal

from stats_alerts.db import exec_with_cursor, run_query, run_scalar


def _require_tx_result(val: Any, action: str) -> Any:
    if val is None:
        raise RuntimeError(
            f"{action} failed: no transaction result returned "
            "(underlying DB exception may be logged by stats_alerts.db.exec_with_cursor)."
        )
    return val


def is_event_completed(event_id: int) -> bool:
    rows = run_query(
        """
        SELECT TOP 1 1 AS Found
        FROM dbo.MGE_Events
        WHERE EventId = ? AND Status = 'completed'
        """,
        params=(event_id,),
    )
    return bool(rows)


def get_last_completed_event_id() -> int | None:
    rows = run_query("""
        SELECT TOP 1 EventId
        FROM dbo.MGE_Events
        WHERE Status = 'completed'
        ORDER BY EndUtc DESC, EventId DESC
        """)
    return int(rows[0]["EventId"]) if rows else None


def get_event_mode(event_id: int) -> str:
    rows = run_query("SELECT EventMode FROM dbo.MGE_Events WHERE EventId = ?", params=(event_id,))
    if not rows:
        raise ValueError(f"Event not found: {event_id}")
    return str(rows[0]["EventMode"])


def has_successful_import_for_event(event_id: int) -> bool:
    rows = run_query(
        """
        SELECT TOP 1 1 AS Found
        FROM dbo.MGE_ResultImports
        WHERE EventId = ? AND ImportStatus = 'completed'
        """,
        params=(event_id,),
    )
    return bool(rows)


def has_successful_import_for_event_filehash(event_id: int, file_hash: str) -> bool:
    rows = run_query(
        """
        SELECT TOP 1 1 AS Found
        FROM dbo.MGE_ResultImports
        WHERE EventId = ? AND FileHashSha256 = ? AND ImportStatus = 'completed'
        """,
        params=(event_id, file_hash),
    )
    return bool(rows)


def create_import_batch(
    event_id: int,
    event_mode: str,
    source: str,
    filename: str,
    file_hash: str,
    actor_discord_id: int | None,
) -> int:
    now = datetime.now(UTC)
    payload = {
        "source": source,
        "filename": filename,
        "hash": file_hash,
    }

    def _tx(cursor):
        cursor.execute(
            """
            INSERT INTO dbo.MGE_ResultImports
            (
                EventId, EventMode, SourceType, Filename, FileHashSha256,
                ImportStatus, ActorDiscordId, DetailsJson, CreatedUtc, UpdatedUtc
            )
            VALUES (?, ?, ?, ?, ?, 'started', ?, ?, ?, ?)
            """,
            (
                event_id,
                event_mode,
                source,
                filename,
                file_hash,
                actor_discord_id,
                json.dumps(payload, ensure_ascii=False),
                now,
                now,
            ),
        )
        cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS BIGINT) AS ImportId")
        row = cursor.fetchone()
        if not row:
            raise RuntimeError("create_import_batch failed: SCOPE_IDENTITY returned no row.")
        return int(row[0])

    val = exec_with_cursor(_tx)
    return int(_require_tx_result(val, "create_import_batch"))


def replace_event_results(
    import_id: int, event_id: int, event_mode: str, rows: list[dict[str, Any]]
) -> int:
    now = datetime.now(UTC)

    def _tx(cursor):
        cursor.execute("DELETE FROM dbo.MGE_FinalResults WHERE EventId = ?", (event_id,))
        inserted = 0
        for row in rows:
            cursor.execute(
                """
                INSERT INTO dbo.MGE_FinalResults
                (
                    ImportId, EventId, EventMode, Rank, PlayerId, PlayerName, Score,
                    ReconciliationStatus, CreatedUtc, UpdatedUtc
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    import_id,
                    event_id,
                    event_mode,
                    row["rank"],
                    row["player_id"],
                    row["player_name"],
                    row["score"],
                    "pending" if event_mode == "controlled" else "not_required",
                    now,
                    now,
                ),
            )
            inserted += 1
        return inserted

    val = exec_with_cursor(_tx)
    return int(_require_tx_result(val, "replace_event_results"))


def _update_import_status(
    import_id: int,
    *,
    status: Literal["completed", "failed"],
    row_count: int | None = None,
    error_text: str | None = None,
) -> None:
    now = datetime.now(UTC)

    def _tx(cursor):
        if status == "completed":
            cursor.execute(
                """
                UPDATE dbo.MGE_ResultImports
                SET ImportStatus = 'completed',
                    RowCount = ?,
                    UpdatedUtc = ?
                WHERE ImportId = ?;
                SELECT @@ROWCOUNT AS Affected;
                """,
                (int(row_count or 0), now, import_id),
            )
        elif status == "failed":
            cursor.execute(
                """
                UPDATE dbo.MGE_ResultImports
                SET ImportStatus = 'failed',
                    ErrorText = ?,
                    UpdatedUtc = ?
                WHERE ImportId = ?;
                SELECT @@ROWCOUNT AS Affected;
                """,
                ((error_text or "")[:1000], now, import_id),
            )
        else:
            raise ValueError(f"Unsupported status: {status}")

        row = cursor.fetchone()
        return int(row[0]) if row else 0

    affected = exec_with_cursor(_tx)
    if affected is None:
        raise RuntimeError(f"_update_import_status failed for ImportId={import_id} status={status}")
    if int(affected) == 0:
        raise RuntimeError(
            f"_update_import_status updated 0 rows for ImportId={import_id} status={status}"
        )


def mark_import_completed(import_id: int, row_count: int) -> None:
    _update_import_status(import_id, status="completed", row_count=row_count)


def mark_import_failed(import_id: int, error_text: str) -> None:
    _update_import_status(import_id, status="failed", error_text=error_text)


def fetch_open_top_15(event_id: int) -> list[dict[str, Any]]:
    return run_query(
        """
        SELECT TOP 15 Rank, PlayerId, PlayerName, Score
        FROM dbo.MGE_FinalResults
        WHERE EventId = ?
        ORDER BY Rank ASC
        """,
        params=(event_id,),
    )


def fetch_controlled_awarded_vs_actual(event_id: int) -> list[dict[str, Any]]:
    return run_query(
        """
        SELECT
            a.AwardedRank,
            a.GovernorId,
            COALESCE(a.GovernorNameSnapshot, fr.PlayerName) AS GovernorName,
            fr.Rank AS ActualRank,
            fr.Score AS ActualScore
        FROM dbo.MGE_Awards a
        LEFT JOIN dbo.MGE_FinalResults fr
          ON fr.EventId = a.EventId
         AND fr.PlayerId = a.GovernorId
        WHERE a.EventId = ? AND a.IsActive = 1
        ORDER BY a.AwardedRank ASC
        """,
        params=(event_id,),
    )


def count_player_open_result_events(player_id: int) -> int:
    v = run_scalar(
        """
        SELECT COUNT(DISTINCT EventId)
        FROM dbo.MGE_FinalResults
        WHERE PlayerId = ?
        """,
        params=(player_id,),
    )
    return int(v or 0)
