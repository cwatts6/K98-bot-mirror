from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from copy import deepcopy
from dataclasses import dataclass
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

StartupCoroutine = Callable[[], Awaitable[Any]]
TaskMonitorCreate = Callable[..., Any]
TaskMonitorIsRunning = Callable[[str], bool]


@dataclass(frozen=True)
class EventTaskMember:
    name: str
    action: Callable
    registration: bool = False
    needs_events: bool = False
    observation_seconds: float = 10.0


class EventTaskBundle:
    """Process-local startup accounting, never a Discord delivery receipt.

    Only proven pre-registration failures retry. Entered one-shots are observed
    once, including past their deadline; cancellation/uncertainty never replays.
    """

    def __init__(self, members, *, snapshot, is_running, clock=time.monotonic):
        self.members = tuple(members)
        self.snapshot = snapshot
        self.is_running = is_running
        self.clock = clock
        self.closed = False
        self.entries = {member.name: {"state": "not_started", "attempts": 0} for member in members}
        self.owned = {}
        self.lock = asyncio.Lock()

    async def tick(self):
        async with self.lock:
            if self.closed:
                return self.report()
            snapshot = self.snapshot()
            for member in self.members:
                entry = self.entries[member.name]
                if member.name in self.owned:
                    task = self.owned[member.name]
                    if not task.done():
                        if self.clock() - entry["entered_at"] >= member.observation_seconds:
                            entry["state"] = "pending_after_deadline"
                        continue
                    if task.cancelled():
                        entry["state"] = "cancelled_outcome_unconfirmed"
                    else:
                        try:
                            outcome = task.result()
                            entry["state"] = (
                                "completed"
                                if isinstance(outcome, dict) and outcome.get("status") == "complete"
                                else "partial"
                            )
                            entry["outcome"] = (
                                outcome if isinstance(outcome, dict) else {"status": "unverified"}
                            )
                        except Exception as exc:
                            entry.update(state="outcome_unconfirmed", error=type(exc).__name__)
                    continue
                if entry["state"] in {
                    "running",
                    "already_running",
                    "registration_unconfirmed",
                    "failed",
                    "cancelled",
                    "outcome_unconfirmed",
                }:
                    continue
                if not snapshot.ok:
                    entry["state"] = "waiting_for_cache"
                    continue
                if member.needs_events and not snapshot.events:
                    entry["state"] = "waiting_for_events"
                    continue
                if self.clock() < entry.get("retry_at", 0):
                    continue
                if member.registration:
                    if self.is_running(member.name):
                        entry["state"] = "already_running"
                        continue
                    entry["attempts"] += 1
                    try:
                        member.action()
                        entry["state"] = (
                            "running"
                            if self.is_running(member.name)
                            else "registration_unconfirmed"
                        )
                    except Exception as exc:
                        running = self.is_running(member.name)
                        entry.update(
                            error=type(exc).__name__,
                            state=(
                                "running"
                                if running
                                else ("failed_before_entry" if entry["attempts"] < 3 else "failed")
                            ),
                        )
                        entry["retry_at"] = self.clock() + (1 if entry["attempts"] == 1 else 5)
                else:
                    entry.update(state="running_once", attempts=1, entered_at=self.clock())
                    try:
                        self.owned[member.name] = asyncio.create_task(
                            member.action(), name=f"event_startup:{member.name}"
                        )
                    except Exception as exc:
                        entry.update(state="outcome_unconfirmed", error=type(exc).__name__)
        return self.report()

    def report(self):
        pending = {
            "not_started",
            "waiting_for_cache",
            "waiting_for_events",
            "failed_before_entry",
            "running_once",
            "pending_after_deadline",
        }
        members = deepcopy(self.entries)
        for member in self.members:
            if member.registration:
                # Registration evidence and present runtime state are separate.
                members[member.name]["currently_running"] = self.is_running(member.name)
        return {
            "status": (
                "pending"
                if any(row["state"] in pending for row in self.entries.values())
                else (
                    "complete"
                    if all(
                        row["state"] in {"running", "already_running", "completed"}
                        for row in self.entries.values()
                    )
                    else "partial"
                )
            ),
            "needs_observation": not self.closed
            and any(row["state"] in pending for row in self.entries.values()),
            "admission_closed": self.closed,
            "members": members,
        }

    def close_admission(self):
        self.closed = True

    async def shutdown(self):
        self.close_admission()
        for task in self.owned.values():
            if not task.done():
                task.cancel()
        drain = asyncio.gather(*self.owned.values(), return_exceptions=True)
        while not drain.done():
            try:
                await asyncio.shield(drain)
            except asyncio.CancelledError:
                continue
        for name, task in self.owned.items():
            if task.cancelled():
                self.entries[name]["state"] = "cancelled_outcome_unconfirmed"
        for row in self.entries.values():
            if row["state"] in {
                "waiting_for_cache",
                "waiting_for_events",
                "not_started",
                "failed_before_entry",
            }:
                row["state"] = "cancelled"


_event_bundle = None


def event_startup_report():
    return (
        _event_bundle.report()
        if _event_bundle is not None
        else {"status": "not_started", "members": {}}
    )


def install_event_bundle(bundle):
    global _event_bundle
    if _event_bundle is None:
        _event_bundle = bundle
    return _event_bundle


async def _start_event_tasks_when_ready(
    *,
    start_event_scheduler_tasks: StartupCoroutine,
    wait_for_events: Callable[[int], Awaitable[bool]],
    max_wait_seconds: int,
) -> None:
    try:
        while True:
            ready = await wait_for_events(max_wait_seconds)
            if ready:
                result = await start_event_scheduler_tasks()
                if not isinstance(result, dict) or not result.get("needs_observation"):
                    return
            # Observe state only. Never fetch or replay a bundle here.
            await asyncio.sleep(1)
    except Exception:
        logger.exception("[BOOT] event_tasks_when_ready failed")


async def run_ready_event_scheduler_tasks(
    *,
    start_event_scheduler_tasks: StartupCoroutine,
    wait_for_events: Callable[[int], Awaitable[bool]],
    task_monitor_create: TaskMonitorCreate,
    ready_wait_seconds: int = 10,
    deferred_wait_seconds: int = 300,
) -> None:
    """Start event-cache-dependent scheduler tasks after event readiness."""
    ready = await wait_for_events(ready_wait_seconds)
    if ready:
        logger.info("[BOOT] Starting event-dependent scheduler task bundle.")
        result = await start_event_scheduler_tasks()
        if not isinstance(result, dict) or not result.get("needs_observation"):
            return

    logger.warning(
        "[BOOT] Event startup remains pending; will observe in background and start "
        "unfinished event-dependent startup work when its inputs are available."
    )
    task_monitor_create(
        "event_tasks_when_ready",
        lambda: _start_event_tasks_when_ready(
            start_event_scheduler_tasks=start_event_scheduler_tasks,
            wait_for_events=wait_for_events,
            max_wait_seconds=deferred_wait_seconds,
        ),
    )


async def run_ready_domain_scheduler_tasks(
    *,
    task_monitor_create: TaskMonitorCreate,
    task_monitor_is_running: TaskMonitorIsRunning,
    schedule_ark_lifecycle: StartupCoroutine,
    refresh_mge_caches_on_startup: StartupCoroutine,
    schedule_mge_lifecycle: StartupCoroutine,
    schedule_voting_lifecycle: StartupCoroutine | None = None,
) -> None:
    """Register domain scheduler tasks that run after event/view readiness."""
    try:
        task_monitor_create("ark_scheduler", schedule_ark_lifecycle)
        logger.info("[BOOT] Ark scheduler started")
    except Exception:
        logger.exception("[BOOT] Failed to start Ark scheduler")

    try:
        if not task_monitor_is_running("refresh_mge_caches_on_startup"):
            task_monitor_create(
                "refresh_mge_caches_on_startup",
                refresh_mge_caches_on_startup,
                replace=False,
            )
            logger.info("[BOOT] MGE cache refresh scheduled")
        else:
            logger.info("[BOOT] MGE cache refresh already running")
    except Exception:
        logger.exception("[BOOT] Failed to schedule MGE cache refresh")

    try:
        if not task_monitor_is_running("mge_lifecycle"):
            task_monitor_create(
                "mge_lifecycle",
                schedule_mge_lifecycle,
                replace=False,
            )
            logger.info("[BOOT] MGE scheduler started")
        else:
            logger.info("[BOOT] MGE scheduler already running")
    except Exception:
        logger.exception("[BOOT] Failed to start MGE scheduler")

    if schedule_voting_lifecycle is None:
        return

    try:
        if not task_monitor_is_running("voting_lifecycle"):
            task_monitor_create(
                "voting_lifecycle",
                schedule_voting_lifecycle,
                replace=False,
            )
            logger.info("[BOOT] Voting scheduler started")
        else:
            logger.info("[BOOT] Voting scheduler already running")
    except Exception:
        logger.exception("[BOOT] Failed to start Voting scheduler")


async def start_event_cache_refresh_loop(*, refresh_event_cache_task: Any) -> None:
    """Start the long-running event cache refresh loop at its existing startup point."""
    try:
        if not refresh_event_cache_task.is_running():
            refresh_event_cache_task.start()
        else:
            logger.info("[BOOT] refresh_event_cache_task already running; skipping start.")
    except Exception:
        logger.exception("[BOOT] Failed to start refresh_event_cache_task")


async def start_legacy_reminder_cleanup(
    *,
    task_monitor_create: TaskMonitorCreate,
    reminder_cleanup_loop: StartupCoroutine,
) -> None:
    """Register the legacy reminder cleanup loop at its existing startup point."""
    try:
        task_monitor_create("reminder_cleanup", reminder_cleanup_loop)
        logger.info("[BOOT] Reminder cleanup task started")
    except Exception:
        logger.exception("[BOOT] Failed to start reminder_cleanup_loop")


async def run_ready_calendar_scheduler_tasks(
    *,
    task_monitor_create: TaskMonitorCreate,
    task_monitor_is_running: TaskMonitorIsRunning,
    schedule_daily_pinned_calendar_refresh: StartupCoroutine,
    calendar_reminder_task: StartupCoroutine,
) -> None:
    """Register calendar scheduler tasks that run after pinned calendar rehydration."""
    try:
        task_monitor_create(
            "daily_pinned_calendar_refresh",
            schedule_daily_pinned_calendar_refresh,
        )
        logger.info("[BOOT] daily pinned calendar refresh started")
    except Exception:
        logger.exception("[BOOT] failed to start daily pinned calendar refresh")

    try:
        if not task_monitor_is_running("calendar_reminder_loop"):
            task_monitor_create(
                "calendar_reminder_loop",
                calendar_reminder_task,
                replace=False,
            )
            logger.info("[CALENDAR][REMINDER] reminder loop armed")
        else:
            logger.info("[CALENDAR][REMINDER] reminder loop already running; skipping")
    except Exception:
        logger.exception("[BOOT] failed to start calendar reminder loop")
