from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from stats_alerts.db import exec_with_cursor, run_query

VALID_STATUSES = {"accepted", "rejected", "duplicate", "failed"}


def _clean_text(value: Any, max_len: int) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:max_len]


def record_import_history(
    *,
    kvk_no: int | None,
    filename: str,
    status: str,
    hash_prefix: str | None = None,
    file_hash_sha256: str | None = None,
    phase: str | None = None,
    row_count: int | None = None,
    scan_id: int | None = None,
    error_type: str | None = None,
    error_text: str | None = None,
    uploader_discord_id: int | None = None,
    channel_id: int | None = None,
    message_id: int | None = None,
    created_utc: datetime | None = None,
) -> int | None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Unsupported PreKvK import status: {status}")

    created = created_utc or datetime.now(UTC)
    safe_hash = _clean_text(file_hash_sha256, 64)
    safe_prefix = _clean_text(hash_prefix or (safe_hash[:8] if safe_hash else None), 8)

    def _tx(cursor):
        cursor.execute(
            """
            INSERT INTO dbo.PreKvk_ImportHistory
            (
                KVK_NO,
                Filename,
                FileHashSha256,
                HashPrefix,
                ImportStatus,
                Phase,
                [RowCount],
                ScanID,
                ErrorType,
                ErrorText,
                UploaderDiscordID,
                ChannelID,
                MessageID,
                CreatedUTC
            )
            OUTPUT INSERTED.HistoryID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                int(kvk_no) if kvk_no is not None else None,
                _clean_text(filename, 255) or "",
                safe_hash,
                safe_prefix,
                status,
                _clean_text(phase, 64),
                int(row_count) if row_count is not None else None,
                int(scan_id) if scan_id is not None else None,
                _clean_text(error_type, 64),
                _clean_text(error_text, 1000),
                int(uploader_discord_id) if uploader_discord_id is not None else None,
                int(channel_id) if channel_id is not None else None,
                int(message_id) if message_id is not None else None,
                created,
            ),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else None

    result = exec_with_cursor(_tx)
    if result is None:
        raise RuntimeError("PreKvK import history insert returned no HistoryID")
    return int(result)


def fetch_recent_import_history(
    *, kvk_no: int | None = None, status: str | None = None, limit: int = 10
) -> list[dict[str, Any]]:
    lim = max(1, min(int(limit or 10), 25))
    where = []
    params: list[Any] = []

    if kvk_no is not None:
        where.append("KVK_NO = ?")
        params.append(int(kvk_no))
    if status:
        status_l = str(status).strip().lower()
        if status_l not in VALID_STATUSES:
            raise ValueError(f"Unsupported PreKvK import status: {status}")
        where.append("ImportStatus = ?")
        params.append(status_l)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    return run_query(
        f"""
        SELECT TOP ({lim})
            HistoryID,
            KVK_NO,
            Filename,
            HashPrefix,
            ImportStatus,
            Phase,
            [RowCount] AS RowCount,
            ScanID,
            ErrorType,
            ErrorText,
            UploaderDiscordID,
            ChannelID,
            MessageID,
            CreatedUTC
        FROM dbo.PreKvk_ImportHistory
        {where_sql}
        ORDER BY CreatedUTC DESC, HistoryID DESC;
        """,
        params=tuple(params),
    )
