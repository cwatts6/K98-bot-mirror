from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any

from mge.dal import mge_completion_dal

logger = logging.getLogger(__name__)

_ALLOWED_COMPLETE_STATUSES = {"signup_open", "signup_closed", "published", "reopened"}


def _now_utc() -> datetime:
    return datetime.now(UTC)


def complete_event(
    event_id: int,
    actor_discord_id: int | None = None,
    source: str = "manual",
    completed_at_utc: datetime | None = None,
) -> dict[str, Any]:
    """Mark event completed if eligible and not already completed."""
    context = mge_completion_dal.fetch_event_completion_context(event_id)
    if not context:
        raise ValueError(f"MGE event {event_id} not found")

    status = str(context.get("Status") or "")
    if status == "completed":
        return {"ok": True, "changed": False, "reason": "already_completed", "event_id": event_id}

    if status not in _ALLOWED_COMPLETE_STATUSES:
        return {
            "ok": False,
            "changed": False,
            "reason": "invalid_status",
            "status": status,
            "event_id": event_id,
        }

    stamp = completed_at_utc or _now_utc()
    changed = mge_completion_dal.mark_event_completed(
        event_id=event_id,
        actor_discord_id=actor_discord_id,
        completed_at_utc=stamp,
    )
    logger.info(
        "mge_event_complete",
        extra={
            "event_id": event_id,
            "source": source,
            "actor_discord_id": actor_discord_id,
            "status_before": status,
            "changed": changed,
        },
    )
    return {"ok": True, "changed": bool(changed), "event_id": event_id}


def reopen_event(event_id: int, actor_discord_id: int) -> dict[str, Any]:
    """Reopen a completed event for admin correction."""
    context = mge_completion_dal.fetch_event_completion_context(event_id)
    if not context:
        raise ValueError(f"MGE event {event_id} not found")

    status = str(context.get("Status") or "")
    if status != "completed":
        return {"ok": False, "changed": False, "reason": "not_completed", "event_id": event_id}

    changed = mge_completion_dal.reopen_event(
        event_id=event_id,
        actor_discord_id=actor_discord_id,
        reopened_at_utc=_now_utc(),
    )
    logger.info(
        "mge_event_reopen",
        extra={"event_id": event_id, "actor_discord_id": actor_discord_id, "changed": changed},
    )
    return {"ok": bool(changed), "changed": bool(changed), "event_id": event_id}


def auto_complete_due_events(as_of_utc: datetime | None = None) -> dict[str, Any]:
    """Auto-complete all due events where now >= StartUtc + 6 days."""
    now = as_of_utc or _now_utc()
    due_ids = mge_completion_dal.fetch_due_event_ids_for_completion(now)
    completed = 0

    for event_id in due_ids:
        result = complete_event(
            event_id=event_id,
            actor_discord_id=None,
            source="scheduler",
            completed_at_utc=now,
        )
        if result.get("changed"):
            completed += 1

    logger.info(
        "mge_auto_complete_sweep",
        extra={
            "as_of_utc": now.isoformat(),
            "due_count": len(due_ids),
            "completed_count": completed,
        },
    )
    return {"ok": True, "due_count": len(due_ids), "completed_count": completed}
