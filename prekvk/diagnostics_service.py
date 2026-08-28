from __future__ import annotations

import logging
from typing import Any

from prekvk.dal.import_history_dal import fetch_recent_import_history, record_import_history

logger = logging.getLogger(__name__)


def _sanitize_for_discord_inline(value: Any, *, max_len: int | None = None) -> str:
    """Sanitize user-controlled text for inline Discord markdown usage."""
    text = str(value or "").strip()
    text = text.replace("\r", " ").replace("\n", " ")
    text = text.replace("<", "‹").replace(">", "›")
    # Break mention tokens (e.g. @everyone / <@123>) so output cannot ping users.
    text = text.replace("@", "@\u200b")
    text = text.replace("*", "＊").replace("_", "＿")
    text = text.replace("`", "｀").replace("~", "～")
    text = text.replace("|", "｜")
    if max_len is not None:
        return text[:max_len]
    return text


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
        created = _sanitize_for_discord_inline(row.get("CreatedUTC") or "unknown", max_len=64)
        status = _sanitize_for_discord_inline(row.get("ImportStatus") or "unknown", max_len=32)
        kvk_no = _sanitize_for_discord_inline(row.get("KVK_NO") or "?", max_len=32)
        filename = _sanitize_for_discord_inline(row.get("Filename") or "unknown file", max_len=255)
        row_count = row.get("RowCount")
        scan_id = row.get("ScanID")
        phase = _sanitize_for_discord_inline(row.get("Phase"), max_len=64)
        err = _sanitize_for_discord_inline(row.get("ErrorType") or row.get("ErrorText"), max_len=80)

        bits = [f"`{created}`", f"KVK `{kvk_no}`", f"**{status}**", f"`{filename}`"]
        if row_count is not None:
            bits.append(f"rows `{row_count}`")
        if scan_id is not None:
            bits.append(f"scan `{scan_id}`")
        if phase:
            bits.append(f"phase `{phase}`")
        if err:
            bits.append(f"error `{err}`")
        lines.append(" - ".join(bits))

    body = "\n".join(lines)
    return body[:3900]
