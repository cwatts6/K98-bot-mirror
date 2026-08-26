from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _get_conn():
    from file_utils import get_conn_with_retries

    return get_conn_with_retries()


def _loads_json(value: Any) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return None


def _rows_to_dicts(cursor) -> list[dict[str, Any]]:
    rows = cursor.fetchall()
    if not rows:
        return []
    cols = [item[0] for item in cursor.description]
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(zip(cols, row, strict=True))
        for key in ("DetectedJson", "CorrectedJson", "FinalJson", "WarningJson", "ErrorJson"):
            item[key] = _loads_json(item.get(key))
        out.append(item)
    return out


def fetch_import_audit_rows(
    *,
    status: str | None = None,
    import_type: str | None = None,
    governor_id: int | None = None,
    discord_user_id: int | None = None,
    lookback_days: int = 30,
    limit: int = 10,
) -> list[dict[str, Any]]:
    clauses = ["CreatedAtUtc >= ?"]
    params: list[Any] = [datetime.now(UTC) - timedelta(days=max(1, int(lookback_days)))]

    if status and status != "all":
        clauses.append("Status = ?")
        params.append(status)
    if import_type and import_type != "all":
        clauses.append("ImportType = ?")
        params.append(import_type)
    if governor_id is not None:
        clauses.append("GovernorID = ?")
        params.append(int(governor_id))
    if discord_user_id is not None:
        clauses.append("DiscordUserID = ?")
        params.append(int(discord_user_id))

    where = " AND ".join(clauses)
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT TOP (?)
                   ImportBatchID,
                   GovernorID,
                   DiscordUserID,
                   ImportType,
                   FlowType,
                   Status,
                   CreatedAtUtc,
                   ApprovedAtUtc,
                   RejectedAtUtc,
                   ConfidenceScore,
                   VisionModel,
                   FallbackUsed,
                   AdminDebugChannelID,
                   AdminDebugMessageID,
                   DetectedJson,
                   CorrectedJson,
                   FinalJson,
                   WarningJson,
                   ErrorJson
            FROM dbo.InventoryImportBatch
            WHERE {where}
            ORDER BY CreatedAtUtc DESC, ImportBatchID DESC
            """,
            (max(1, min(int(limit), 25)), *params),
        )
        return _rows_to_dicts(cur)
    finally:
        conn.close()
