"""Service layer for leadership review pool retrieval and sorting."""

from __future__ import annotations

import logging
from typing import Any

from mge.dal import mge_review_dal
from mge.mge_simplified_flow_service import sort_review_rows
from mge.mge_summary_service import build_review_summary

logger = logging.getLogger(__name__)


def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_review_row(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)

    gov = (
        _as_text(
            row.get("GovernorNameSnapshot")
            or row.get("GovernorName")
            or row.get("GovernorDisplayName")
            or row.get("Governor")
        )
        or "Unknown"
    )

    commander = _as_text(row.get("RequestedCommanderName")) or "Unknown"
    priority = _as_text(row.get("RequestPriority")) or "Unknown"

    out["GovernorNameDisplay"] = gov
    out["CommanderNameDisplay"] = commander
    out["PriorityDisplay"] = priority.title() if priority != "Unknown" else "Unknown"

    return out


def get_signup_review_pool(event_id: int) -> list[dict[str, Any]]:
    """
    Return leadership review rows sorted by simplified-flow signup order:
      1) High > Medium > Low
      2) lower/better KVK rank first
      3) missing KVK rank last within bucket
      4) signup timestamp ascending
      5) SignupId ascending as a stable tie-breaker
    """
    rows = mge_review_dal.fetch_signup_review_rows(event_id)
    ordered = sort_review_rows(rows)
    normalized = [_normalize_review_row(row) for row in ordered]
    logger.info("mge_review_service_pool_ready event_id=%s count=%s", event_id, len(normalized))
    return normalized


def get_review_pool_with_summary(event_id: int) -> dict[str, Any]:
    """
    Return sorted review rows plus summary payload.

    Response shape:
    {
      "event_id": int,
      "rows": list[dict[str, Any]],
      "summary": {
        "total_rows": int,
        "by_priority": dict[str, int],
        "by_commander": dict[str, int],
        "by_role": dict[str, int],
        "warnings": dict[str, int],
      },
    }
    """
    rows = get_signup_review_pool(event_id)
    summary = build_review_summary(rows)
    payload: dict[str, Any] = {
        "event_id": int(event_id),
        "rows": rows,
        "summary": summary,
    }
    logger.info(
        "mge_review_service_pool_with_summary_ready event_id=%s row_count=%s",
        event_id,
        len(rows),
    )
    return payload
