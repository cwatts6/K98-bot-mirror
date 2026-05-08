from __future__ import annotations

import logging
from typing import Any

from prekvk.dal.import_history_dal import fetch_recent_import_history, record_import_history

logger = logging.getLogger(__name__)


def record_import_outcome(**kwargs: Any) -> int | None:
    """Best-effort durable audit record for a PreKvK import attempt."""
    try:
        history_id = record_import_history(**kwargs)
        logger.info(
            "[PREKVK] import history recorded history_id=%s status=%s kvk_no=%s file=%s",
            history_id,
            kwargs.get("status"),
            kwargs.get("kvk_no"),
            kwargs.get("filename"),
        )
        return history_id
    except Exception:
        logger.exception(
            "[PREKVK] failed to record import history status=%s kvk_no=%s file=%s",
            kwargs.get("status"),
            kwargs.get("kvk_no"),
            kwargs.get("filename"),
        )
        return None


def get_recent_import_history(
    *, kvk_no: int | None = None, status: str | None = None, limit: int = 10
) -> list[dict[str, Any]]:
    return fetch_recent_import_history(kvk_no=kvk_no, status=status, limit=limit)


def format_history_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No PreKvK import history found."

    lines = []
    for row in rows:
        created = row.get("CreatedUTC") or "unknown"
        status = str(row.get("ImportStatus") or "unknown")
        kvk_no = row.get("KVK_NO") or "?"
        filename = row.get("Filename") or "unknown file"
        row_count = row.get("RowCount")
        scan_id = row.get("ScanID")
        phase = row.get("Phase")
        err = row.get("ErrorType") or row.get("ErrorText")

        bits = [f"`{created}`", f"KVK `{kvk_no}`", f"**{status}**", f"`{filename}`"]
        if row_count is not None:
            bits.append(f"rows `{row_count}`")
        if scan_id is not None:
            bits.append(f"scan `{scan_id}`")
        if phase:
            bits.append(f"phase `{phase}`")
        if err:
            bits.append(f"error `{str(err)[:80]}`")
        lines.append(" - ".join(bits))

    body = "\n".join(lines)
    return body[:3900]
