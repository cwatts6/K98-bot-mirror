# offload_monitor_lib.py
"""
Offload registry monitoring helpers adapted to reuse existing infrastructure.

This module intentionally:
- Uses the project's logging configuration (logging_setup.py) and telemetry logger.
- Exposes lightweight synchronous helpers (compute_offload_stats, rotate_registry_file, check_and_mark_stale)
  and async coroutines (monitor_once_coro, monitor_loop_coro) that can be scheduled via the
  project's TaskMonitor (bot_instance.task_monitor.create).
- Does NOT start its own Prometheus server by default; provide a thin integration point
  instead if you want to wire metrics into your monitoring stack.

Usage (within bot process):
- from offload_monitor_lib import monitor_loop_coro
- task_monitor.create("offload_monitor", lambda: monitor_loop_coro(interval_seconds=300, ...))

Usage (standalone script):
- python scripts/offload_monitor.py --once
- python scripts/offload_monitor.py --interval 300

Notes:
- This module uses file_utils.list_offloads / mark_offload_complete so the persistent registry
  semantics remain centralised.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
import json
import logging
import os
from typing import Any

from constants import DATA_DIR
from file_utils import (
    emit_telemetry_event,
    list_offloads,
    mark_offload_complete,
    pid_alive,
)

logger = logging.getLogger(__name__)
telemetry = logging.getLogger("telemetry")


def compute_offload_stats(entries: list[dict[str, Any]]) -> dict[str, int]:
    """
    Compute simple counts from offload entries.
    """
    total = len(entries)
    active = 0
    completed = 0
    stale = 0
    cancel_requested = 0
    cancel_failed = 0
    timeouts = 0

    for e in entries:
        status = (e.get("status") or "").lower()
        if status == "completed":
            completed += 1
        else:
            pid = e.get("pid")
            if pid:
                try:
                    if pid_alive(int(pid)):
                        active += 1
                    else:
                        stale += 1
                except Exception:
                    stale += 1
            else:
                active += 1

        if e.get("cancel_requested"):
            cancel_requested += 1
            if e.get("ok") is False:
                cancel_failed += 1

        out = (e.get("output_snippet") or "") or ""
        if isinstance(out, str) and ("timed out" in out.lower() or "timeout" in out.lower()):
            timeouts += 1

    return {
        "total": total,
        "active": active,
        "completed": completed,
        "stale": stale,
        "cancel_requested": cancel_requested,
        "cancel_failed": cancel_failed,
        "timeouts": timeouts,
    }


def check_and_mark_stale(note_prefix: str | None = "marked_stale") -> list[dict[str, Any]]:
    """
    Inspect registry entries and mark entries whose pid is not alive as completed/failed.

    Returns a list of small dicts describing entries that were marked stale.
    """
    entries = list_offloads()
    stale_marked = []
    for ent in entries:
        try:
            off_id = ent.get("offload_id")
            if not off_id:
                continue
            status = (ent.get("status") or "").lower()
            if status == "completed":
                continue
            pid = ent.get("pid")
            if not pid:
                # nothing to check
                continue
            try:
                alive = pid_alive(int(pid))
            except Exception:
                alive = False
            if not alive:
                note = f"{note_prefix}:pid_dead:{pid}"
                try:
                    mark_offload_complete(off_id, ok=False, output_snippet=note, worker_parsed=None)
                    emit_telemetry_event(
                        {
                            "event": "offload_monitor.stale_detected",
                            "offload_id": off_id,
                            "pid": pid,
                            "note": note,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                except Exception:
                    logger.exception("Failed to mark offload %s stale", off_id)
                stale_marked.append({"offload_id": off_id, "pid": pid, "note": note})
        except Exception:
            logger.exception("Error while checking offload entry for staleness: %r", ent)
    return stale_marked


def rotate_registry_file(
    file_path: str, retention_days: int = 30, max_entries: int = 2000
) -> dict[str, int]:
    """
    Trim the persistent registry JSON file to implement retention and a max-entry cap.

    Returns: dict with keys removed_count, before_count, after_count.

    Behavior:
    - Remove entries older than retention_days (by end_time, then start_time).
    - If still above max_entries, drop oldest completed entries until within limit.
    - Performs atomic overwrite.
    """
    try:
        if not os.path.exists(file_path):
            return {"removed_count": 0, "before_count": 0, "after_count": 0}

        with open(file_path, encoding="utf-8") as fh:
            data = json.load(fh) or {}
        if not isinstance(data, dict):
            return {"removed_count": 0, "before_count": 0, "after_count": 0}

        items = list(data.values())
        before = len(items)
        # Use timezone-aware UTC cutoff to safely compare with parsed datetimes
        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        keep = []
        removed = []

        for ent in items:
            ts = ent.get("end_time") or ent.get("start_time")
            if not ts:
                keep.append(ent)
                continue
            try:
                t = datetime.fromisoformat(str(ts))
            except Exception:
                keep.append(ent)
                continue

            # Normalize parsed time to timezone-aware UTC for safe comparison
            try:
                if t.tzinfo is None:
                    # assume naive timestamps are UTC
                    t = t.replace(tzinfo=UTC)
                else:
                    t = t.astimezone(UTC)
            except Exception:
                keep.append(ent)
                continue

            if t < cutoff:
                removed.append(ent)
            else:
                keep.append(ent)

        # If still too many entries, remove oldest completed entries first
        if len(keep) > max_entries:
            # build sorted by start_time (fallback to end_time or empty string)
            def keyfn(e):
                return e.get("start_time") or e.get("end_time") or ""

            keep_sorted = sorted(keep, key=keyfn)
            to_remove = []
            # remove completed first
            for ent in keep_sorted:
                if len(keep_sorted) - len(to_remove) <= max_entries:
                    break
                if (ent.get("status") or "").lower() == "completed":
                    to_remove.append(ent)
            # if still over, remove oldest remaining
            if len(keep_sorted) - len(to_remove) > max_entries:
                extra = (len(keep_sorted) - len(to_remove)) - max_entries
                to_remove += keep_sorted[:extra]
            remaining = [e for e in keep_sorted if e not in to_remove]
            removed += to_remove
            keep = remaining

        # Write back keyed by offload_id
        newd = {}
        for ent in keep:
            oid = ent.get("offload_id")
            if not oid:
                # ensure unique key
                oid = f"unknown-{len(newd)+1}"
            newd[oid] = ent

        tmp = f"{file_path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(newd, fh, default=str, indent=2)
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except Exception:
                pass
        os.replace(tmp, file_path)
        return {"removed_count": len(removed), "before_count": before, "after_count": len(keep)}
    except Exception:
        logger.exception("rotate_registry_file failed for %s", file_path)
        return {"removed_count": 0, "before_count": 0, "after_count": 0}


# --- Async helpers intended to be scheduled by TaskMonitor in bot_instance.py ---


async def monitor_once_coro(
    mark_note_prefix: str | None = "marked_stale",
    rotate_days: int = 30,
    max_entries: int = 2000,
) -> dict[str, Any]:
    """
    One-shot async monitor: checks for stale offloads, emits summary telemetry and runs rotation.

    Returns a dict summary of actions performed.
    """
    registry_path = os.path.join(DATA_DIR, "offload_registry.json")

    # 1) check & mark stale
    stale = check_and_mark_stale(note_prefix=mark_note_prefix)

    # 2) compute stats & emit telemetry
    entries = list_offloads()
    stats = compute_offload_stats(entries)
    emit_telemetry_event(
        {
            "event": "offload_monitor.summary",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

    # 3) rotate registry file
    rotate_res = rotate_registry_file(
        registry_path, retention_days=rotate_days, max_entries=max_entries
    )
    if rotate_res.get("removed_count", 0) > 0:
        emit_telemetry_event({"event": "offload_monitor.rotate", "result": rotate_res})

    return {"stale_marked": len(stale), "stats": stats, "rotate": rotate_res}


async def monitor_loop_coro(
    interval_seconds: int = 300,
    mark_note_prefix: str | None = "marked_stale",
    rotate_days: int = 30,
    max_entries: int = 2000,
    alert_stale_threshold: int = 5,
):
    """
    Long-running monitor loop intended to be scheduled in-process via TaskMonitor.

    Example:
      task_monitor.create("offload_monitor", lambda: monitor_loop_coro(...))

    This coroutine never returns (looping forever) unless cancelled.
    """
    while True:
        try:
            res = await monitor_once_coro(
                mark_note_prefix=mark_note_prefix, rotate_days=rotate_days, max_entries=max_entries
            )
            stats = res.get("stats", {})
            # Emit an alert telemetry event if stale exceeds threshold
            if stats.get("stale", 0) >= alert_stale_threshold:
                emit_telemetry_event(
                    {
                        "event": "offload_monitor.alert",
                        "reason": "stale_threshold_exceeded",
                        "stale": stats.get("stale", 0),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
        except asyncio.CancelledError:
            logger.info("offload monitor loop cancelled; exiting")
            raise
        except Exception:
            logger.exception("offload monitor loop iteration failed")
        await asyncio.sleep(interval_seconds)
