"""Service layer for leadership review pool retrieval and sorting."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any

from mge.dal import mge_review_dal
from mge.mge_summary_service import build_review_summary

logger = logging.getLogger(__name__)

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _as_priority_rank(value: Any) -> int:
    return _PRIORITY_ORDER.get(_as_text(value).lower(), 99)


def _as_datetime_utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return datetime.max.replace(tzinfo=UTC)


def _sort_key(row: dict[str, Any]) -> tuple[int, str, int, int, datetime]:
    return (
        _as_priority_rank(row.get("RequestPriority")),
        _as_text(row.get("RequestedCommanderName")).lower(),
        _as_int(row.get("PriorAwardsRequestedCommanderCount"), 0),
        _as_int(row.get("PriorAwardsOverallLast2YearsCount"), 0),
        _as_datetime_utc(row.get("SignupCreatedUtc")),
    )


def get_signup_review_pool(event_id: int) -> list[dict[str, Any]]:
    """
    Return leadership review rows sorted by Task H priority order:
      1) High > Medium > Low
      2) commander name
      3) fewer prior same-commander awards
      4) fewer prior total awards in last 2 years
      5) signup timestamp ascending
    """
    rows = mge_review_dal.fetch_signup_review_rows(event_id)
    ordered = sorted(rows, key=_sort_key)
    logger.info("mge_review_service_pool_ready event_id=%s count=%s", event_id, len(ordered))
    return ordered


def get_review_pool_with_summary(event_id: int) -> dict[str, Any]:
    """
    Task-I-ready adapter returning both sorted review rows and summary payload.

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
