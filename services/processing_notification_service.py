"""Durable processing facts and exact export observation; no Discord rendering."""

import json
import logging
from pathlib import Path
import re
import time
from uuid import uuid4

from services.legacy_export_snapshot_service import caller_runtime, drain_thread
from services.processing_notification_store import NotificationHeld, notification_store

logger = logging.getLogger(__name__)
TERMINAL_EXPORTS = {"confirmed", "failed", "uncertain", "cancelled"}


def event(
    run_id,
    stage,
    outcome,
    action,
    *,
    error=None,
    job_id=None,
    duration=None,
    channel_id=None,
    message_id=None,
):
    try:
        logger.log(
            (
                logging.WARNING
                if outcome in {"held", "failed", "unavailable", "uncertain"}
                else logging.INFO
            ),
            "processing_outcome run_id=%s job_id=%s stage=%s outcome=%s next_action=%s error_type=%s duration_seconds=%s channel_id=%s message_id=%s reason=%s sqlstate=%s",
            run_id,
            job_id,
            stage,
            outcome,
            action,
            type(error).__name__ if error else None,
            duration,
            channel_id,
            message_id,
            str(error) if isinstance(error, NotificationHeld) else None,
            (
                error.args[0]
                if error
                and error.args
                and isinstance(error.args[0], str)
                and re.fullmatch(r"[A-Z0-9]{5}", error.args[0])
                else None
            ),
        )
    except Exception:
        pass


def register_run(*, source_message_id, source_channel_id, summary_channel_id, sheets_channel_id):
    with caller_runtime() as runtime:
        if runtime is None:
            return None
        run_id = str(uuid4())
        notification_store().create(
            run_id,
            source_message_id=source_message_id,
            source_channel_id=source_channel_id,
            summary_channel_id=summary_channel_id,
            sheets_channel_id=sheets_channel_id,
            account=runtime.account,
            storage_owner=runtime.store.storage_owner,
        )
        event(run_id, "registration", "recorded", "await_verified_bot_data")
        return run_id


async def patch_run(run_id, **changes):
    if not run_id:
        return None
    try:
        return await drain_thread(notification_store().patch, run_id, **changes)
    except Exception as exc:
        event(run_id, "journal", "held", "inspect_notification_journal_and_disk", error=exc)
        return None


def cache_generation(output):
    meta = output.get("_meta", {}) if isinstance(output, dict) else {}
    if (
        meta.get("source") != "SQL:dbo.STATS_FOR_UPLOAD"
        or meta.get("source_refresh_status") != "refreshed"
        or meta.get("source_refresh_succeeded") is not True
        or meta.get("cache_write_status") != "written"
        or not isinstance(meta.get("generated_at"), str)
    ):
        return None
    return meta["generated_at"]


def _current_cache_generation():
    from constants import PLAYER_STATS_CACHE

    return cache_generation(json.loads(Path(PLAYER_STATS_CACHE).read_text(encoding="utf-8")))


def observe_export(row):
    from services.processing_notification_dal import read_export_outcome

    if not row.get("preparation_id") or row["sheets"] in {"confirmed", "failed", "cancelled"}:
        return row
    with caller_runtime() as runtime:
        if runtime is None:
            raise NotificationHeld("Protected runtime unavailable.")
        outcome = read_export_outcome(runtime, row)
    state = outcome["state"]
    changes = dict(job_id=outcome["job_id"], sheets=state, links=outcome["links"])
    changes["additional_links"] = outcome.get("additional_links", 0)
    if row["sheets"] == "uncertain" and state not in TERMINAL_EXPORTS:
        return row
    if all(row.get(key) == value for key, value in changes.items()):
        return row
    changed_terminal = state in TERMINAL_EXPORTS and state != row["sheets"]
    if changed_terminal:
        changes.update(
            completed_at=time.time(),
            duration_seconds=round(time.time() - row["created"], 1),
            handoff=True,
        )
    updated = notification_store().patch(row["run_id"], **changes)
    if changed_terminal:
        event(
            row["run_id"],
            "export",
            state,
            "notify_without_repeating_export",
            job_id=outcome["job_id"],
            duration=updated["duration_seconds"],
        )
    return updated


def validate_runtime_scope(row):
    with caller_runtime() as runtime:
        if runtime is None or (row["account"], row["storage_owner"]) != (
            runtime.account,
            runtime.store.storage_owner,
        ):
            raise NotificationHeld(
                "Registered notification belongs to another or unavailable runtime."
            )
