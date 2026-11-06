from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import logging
from pathlib import Path
from typing import Any

from constants import (
    EVENT_CALENDAR_CACHE_FILE_PATH,
    EVENT_CALENDAR_PIPELINE_GENERATE_TIMEOUT_SECONDS,
    EVENT_CALENDAR_PIPELINE_PUBLISH_TIMEOUT_SECONDS,
    EVENT_CALENDAR_PIPELINE_SYNC_TIMEOUT_SECONDS,
    EVENT_CALENDAR_STALE_DEGRADED_MINUTES,
    EVENT_CALENDAR_STALE_WARN_MINUTES,
)
from core.operation_evidence import emit, optional, scope
from core.operation_timing import clock
from core.owned_work import drain_thread
from event_calendar.cache_publisher import publish_event_calendar_cache
from event_calendar.datetime_utils import now_utc, parse_iso_utc_nullable
from event_calendar.event_generator import generate_calendar_instances
from event_calendar.mutation_owner import get_owner
from event_calendar.reminder_metrics import get_reminder_status_service
from event_calendar.sheets_sync import sync_sheets_to_sql
from event_calendar.sql_lifecycle import error_facts
from file_utils import emit_telemetry_event

logger = logging.getLogger(__name__)


def _observed_now():
    return optional(now_utc) or datetime.now(UTC)


def _load_cache_state(
    cache_path: Path,
    now: datetime,
) -> tuple[int | None, bool, bool, str | None, int | None, int | None]:
    cache_age_minutes: int | None = None
    next_upcoming_event_utc: str | None = None
    degraded = False
    warning = False
    cache_event_count: int | None = None
    cache_horizon_days: int | None = None

    if cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime, tz=UTC)
        cache_age_minutes = max(0, int((now - mtime).total_seconds() // 60))
        warning = cache_age_minutes >= EVENT_CALENDAR_STALE_WARN_MINUTES
        degraded = cache_age_minutes >= EVENT_CALENDAR_STALE_DEGRADED_MINUTES

        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            events = payload.get("events", [])
            if isinstance(events, list):
                cache_event_count = len(events)

            horizon = payload.get("horizon_days")
            if isinstance(horizon, int):
                cache_horizon_days = horizon

            upcoming: list[datetime] = []
            for e in events if isinstance(events, list) else []:
                dt = parse_iso_utc_nullable((e or {}).get("start_utc"))
                if dt and dt >= now:
                    upcoming.append(dt)
            if upcoming:
                next_upcoming_event_utc = min(upcoming).isoformat()
        except Exception:
            degraded = True

    return (
        cache_age_minutes,
        warning,
        degraded,
        next_upcoming_event_utc,
        cache_event_count,
        cache_horizon_days,
    )


def _duration_ms(started: datetime, completed: datetime | None = None) -> int:
    end = completed or _observed_now()
    return max(0, int((end - started).total_seconds() * 1000))


def _classify_error(exc: Exception) -> str:
    # Task 8 fix: isinstance requires tuple, not union expression.
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        return "timeout"
    return "exception"


def _is_publish_success(result: dict[str, Any]) -> bool:
    return bool(result.get("ok")) and result.get("status") in {
        "success",
        "skipped_empty_preserve_existing",
    }


def _severity_from_pipeline(
    *,
    ok: bool,
    stage: str,
    publish_status: str | None,
) -> str:
    if ok:
        if publish_status == "skipped_empty_preserve_existing":
            return "warning"
        return "ok"
    if stage in {"sync", "generate"}:
        return "failed"
    if stage == "publish":
        return "degraded"
    return "failed"


@dataclass(frozen=True)
class _StagePolicy:
    timeout_seconds: int
    retries: int


class CalendarService:
    def __init__(self) -> None:
        self._last_refresh_utc: datetime | None = None
        self._last_status: str = "not_started"
        self._last_result: dict[str, Any] | None = None

        self._last_generate_utc: datetime | None = None
        self._last_generate_status: str = "not_started"
        self._last_generate_result: dict[str, Any] | None = None

        self._last_publish_utc: datetime | None = None
        self._last_publish_status: str = "not_started"
        self._last_publish_result: dict[str, Any] | None = None

        self._last_pipeline_utc: datetime | None = None
        self._last_pipeline_status: str = "not_started"
        self._last_pipeline_result: dict[str, Any] | None = None
        self._last_pipeline_run_id: str | None = None
        self._latest_error: dict[str, Any] | None = None
        self._last_successful_pipeline_utc: datetime | None = None

    def _record_latest_error(self, *, stage: str, exc: Exception | None, message: str) -> None:
        error_type = type(exc).__name__ if exc else "ResultFailure"
        self._latest_error = {
            "stage": stage,
            "error_type": error_type,
            "message": message,
            "at_utc": _observed_now().isoformat(),
        }

    def _clear_latest_error(self) -> None:
        self._latest_error = None

    async def _calendar_health(self) -> dict[str, Any]:
        cache_path = Path(EVENT_CALENDAR_CACHE_FILE_PATH)
        now = _observed_now()

        (
            cache_age_minutes,
            warning,
            degraded,
            next_upcoming_event_utc,
            cache_event_count,
            cache_horizon_days,
        ) = await asyncio.to_thread(_load_cache_state, cache_path, now)

        pipeline_success = self._last_successful_pipeline_utc

        return {
            "cache_age_minutes": cache_age_minutes,
            "cache_event_count": cache_event_count,
            "cache_horizon_days": cache_horizon_days,
            "cache_stale_warning": warning,
            "next_upcoming_event_utc": next_upcoming_event_utc,
            "last_successful_pipeline_utc": (
                pipeline_success.isoformat() if pipeline_success else "not_started"
            ),
            "current_degraded_mode": degraded,
        }

    async def get_status(self) -> dict[str, Any]:
        return {
            "mode": "sheets_sql_generate_publish",
            "ownership": get_owner().snapshot(),
            "sync": {
                "status": self._last_status or "not_started",
                "last_refresh_utc": (
                    self._last_refresh_utc.isoformat() if self._last_refresh_utc else "not_started"
                ),
                "last_result": deepcopy(self._last_result),
            },
            "generate": {
                "status": self._last_generate_status or "not_started",
                "last_generate_utc": (
                    self._last_generate_utc.isoformat()
                    if self._last_generate_utc
                    else "not_started"
                ),
                "last_result": deepcopy(self._last_generate_result),
            },
            "publish": {
                "status": self._last_publish_status or "not_started",
                "last_publish_utc": (
                    self._last_publish_utc.isoformat() if self._last_publish_utc else "not_started"
                ),
                "last_result": deepcopy(self._last_publish_result),
            },
            "pipeline": {
                "status": self._last_pipeline_status or "not_started",
                "last_run_utc": (
                    self._last_pipeline_utc.isoformat()
                    if self._last_pipeline_utc
                    else "not_started"
                ),
                "last_pipeline_utc": (
                    self._last_pipeline_utc.isoformat()
                    if self._last_pipeline_utc
                    else "not_started"
                ),
                "pipeline_run_id": self._last_pipeline_run_id or "not_started",
                "last_result": deepcopy(self._last_pipeline_result),
            },
            "reminders": get_reminder_status_service().get_status(),
            "latest_error": deepcopy(self._latest_error) or {},
            "calendar_health": await self._calendar_health(),
        }

    async def refresh(self, *, actor_user_id=None, sheet_id=None):
        return await self._submit("sync", actor_user_id=actor_user_id, sheet_id=sheet_id)

    async def generate(self, *, actor_user_id=None, horizon_days=365):
        return await self._submit(
            "generate", actor_user_id=actor_user_id, horizon_days=horizon_days
        )

    async def publish_cache(self, *, actor_user_id=None, horizon_days=365, force_empty=False):
        return await self._submit(
            "publish",
            actor_user_id=actor_user_id,
            horizon_days=horizon_days,
            force_empty=force_empty,
        )

    async def refresh_pipeline(
        self,
        *,
        actor_user_id=None,
        actor_source=None,
        sheet_id=None,
        horizon_days=365,
        force_empty=False,
        scheduled=False,
    ):
        return await self._submit(
            "pipeline",
            actor_user_id=actor_user_id,
            actor_source=actor_source,
            sheet_id=sheet_id,
            horizon_days=horizon_days,
            force_empty=force_empty,
            scheduled=scheduled,
        )

    async def refresh_full(self, **kwargs):
        return await self.refresh_pipeline(**kwargs)

    def close_admission(self):
        get_owner().close_admission()

    async def drain(self):
        return await get_owner().drain()

    def admission_open(self):
        return not get_owner().closed

    def record_delivery(self, reference, state, error_type=None):
        """Delivery observations never change business outcomes or authorize replay."""
        if state not in {"succeeded", "failed", "unknown"}:
            return
        from core.operation_evidence import label

        delivery = dict(state=state, error_type=label(error_type) if error_type else None)
        owner = get_owner()
        for run in (owner.active, owner.last):
            if run is not None and run.reference == reference:
                run.result["delivery"] = dict(delivery)
        for result in (
            self._last_result,
            self._last_generate_result,
            self._last_publish_result,
            self._last_pipeline_result,
        ):
            if result and result.get("pipeline_run_id") == reference:
                result["delivery"] = dict(delivery)

    async def _submit(
        self,
        kind,
        *,
        actor_user_id=None,
        actor_source=None,
        sheet_id=None,
        horizon_days=365,
        force_empty=False,
        scheduled=False,
    ):
        owner = get_owner()

        async def execute(run):
            with scope():
                return await self._execute(
                    run, owner, actor_user_id, actor_source, sheet_id, horizon_days, force_empty
                )

        return await owner.execute(kind, execute, scheduled=scheduled)

    async def _execute(self, run, owner, actor, source, sheet_id, horizon, force_empty):
        stages = ("sync", "generate", "publish") if run.kind == "pipeline" else (run.kind,)
        started = _observed_now()
        durations = {}
        for stage in stages:
            if run.stop.is_set() or owner.closed:
                break
            run.stage = stage
            if stage == "sync" and not sheet_id:
                result = dict(
                    ok=False,
                    status="failed_service",
                    cleanup="not_needed",
                    effect="failed_before_effects",
                    details="EVENT_CALENDAR_SHEET_ID is not configured",
                )
            else:
                ticket = (
                    optional(owner.audit.offer, run.reference, started) if stage == "sync" else None
                )
                try:
                    result, duration, _ = await self._run_stage_with_policy(
                        pipeline_run_id=run.reference,
                        actor_source=source or "direct",
                        stage_name=stage,
                        policy=_StagePolicy(
                            {
                                "sync": EVENT_CALENDAR_PIPELINE_SYNC_TIMEOUT_SECONDS,
                                "generate": EVENT_CALENDAR_PIPELINE_GENERATE_TIMEOUT_SECONDS,
                                "publish": EVENT_CALENDAR_PIPELINE_PUBLISH_TIMEOUT_SECONDS,
                            }[stage],
                            0,
                        ),
                        stage_call=lambda: self._physical_stage(
                            run, stage, sheet_id, horizon, force_empty
                        ),
                        run=run,
                    )
                    durations[stage] = duration
                finally:
                    if ticket is not None:
                        terminal = run.results.get(stage) or dict(status="outcome_unknown")
                        optional(owner.audit.finish, ticket, terminal, _observed_now())
            run.results[stage] = result
            result["pipeline_run_id"] = run.reference
            optional(self._save_stage, stage, result, started)
            optional(
                emit_telemetry_event,
                {
                    "event": {
                        "sync": "calendar_refresh",
                        "generate": "calendar_generate",
                        "publish": "calendar_publish_cache",
                    }[stage],
                    "actor_user_id": actor,
                    "ok": result.get("ok"),
                    "status": result.get("status"),
                },
            )
            if not result.get("ok") or run.cleanup_unconfirmed:
                break
        if run.kind != "pipeline":
            result = deepcopy(
                run.results.get(run.kind)
                or dict(ok=False, status="not_started", details="Stopped before physical entry.")
            )
            result.update(
                pipeline_run_id=run.reference, observer=run.observer, audit=owner.audit.snapshot()
            )
            timestamp_key = {
                "sync": "refreshed_utc",
                "generate": "generated_utc",
                "publish": "published_utc",
            }[run.kind]
            result[timestamp_key] = started.isoformat()
            return result
        complete = len(run.results) == 3 and all(r.get("ok") for r in run.results.values())
        publish = run.results.get("publish") or {}
        completed = _observed_now()
        out = dict(
            ok=complete,
            stage="done" if complete else run.stage,
            status=(
                "success"
                if complete
                else (
                    "cleanup_unconfirmed"
                    if run.cleanup_unconfirmed
                    else "stopped" if run.stop.is_set() else "failed_" + run.stage
                )
            ),
            pipeline_run_id=run.reference,
            actor_source=source or "direct",
            sheets_sync_success=bool(run.results.get("sync", {}).get("ok")),
            sql_generation_success=bool(run.results.get("generate", {}).get("ok")),
            json_export_success=bool(publish.get("ok")),
            events_generated=run.results.get("generate", {}).get("instances_generated"),
            events_written=publish.get("events_written"),
            pipeline_started_utc=started.isoformat(),
            pipeline_completed_utc=completed.isoformat(),
            duration_ms=optional(_duration_ms, started, completed),
            stage_durations_ms=durations,
            stage_status={
                k: dict(ok=v.get("ok"), status=v.get("status"), attempts=1)
                for k, v in run.results.items()
            },
            sync=run.results.get("sync"),
            generate=run.results.get("generate"),
            publish=run.results.get("publish"),
            publish_reason=publish.get("status"),
            observer=run.observer,
            cleanup="unconfirmed" if run.cleanup_unconfirmed else "settled",
            remaining_stages=[s for s in stages if s not in run.results],
            audit=owner.audit.snapshot(),
            errors=[
                r.get("details") or r.get("status")
                for r in run.results.values()
                if not r.get("ok") or r.get("cleanup") == "unconfirmed"
            ],
            severity=(
                "warning"
                if complete and publish.get("severity") == "warning"
                else "ok" if complete else "failed"
            ),
        )
        self._last_pipeline_utc = completed
        self._last_pipeline_status = out["status"]
        self._last_pipeline_result = deepcopy(out)
        self._last_pipeline_run_id = run.reference
        if complete:
            self._last_successful_pipeline_utc = completed
            self._clear_latest_error()
        else:
            self._latest_error = dict(
                stage=run.stage, message=(out["errors"] or ["Stopped before remaining stages"])[0]
            )
        optional(
            emit_telemetry_event,
            {
                "event": "calendar_pipeline_completed" if complete else "calendar_pipeline_failed",
                **out,
            },
        )
        return out

    async def _physical_stage(self, run, stage, sheet_id, horizon, force_empty):
        run.phase = "submitted"
        function, args, kwargs = {
            "sync": (sync_sheets_to_sql, (sheet_id,), {}),
            "generate": (generate_calendar_instances, (), {"horizon_days": horizon}),
            "publish": (
                publish_event_calendar_cache,
                (),
                {"horizon_days": horizon, "force_empty": force_empty},
            ),
        }[stage]

        def enter():
            if run.stop.is_set():
                return None
            run.phase = "entered"
            emit("calendar_" + stage, "entered")
            raw = function(*args, **kwargs)
            # Capture before optional projection/telemetry can fail.
            run.raw[stage] = raw
            return raw

        try:
            raw = await drain_thread(enter)
            if raw is None:
                result = dict(
                    ok=False, status="not_started", effect="not_started", cleanup="not_needed"
                )
            else:
                result = _result_projection(raw)
        except Exception as error:
            raw = run.raw.get(stage)
            if raw is not None:
                # Keep acknowledged domain facts even if a presentation adapter failed.
                result = _base_result(raw)
                result["projection"] = "unavailable"
            else:
                result = dict(
                    ok=False,
                    status="failed_service",
                    effect="unknown",
                    cleanup="unconfirmed" if run.phase == "entered" else "not_needed",
                    details=str(error_facts(error)),
                )
        run.results[stage] = result
        run.cleanup_unconfirmed = result.get("cleanup") == "unconfirmed"
        run.phase = "cleanup_unconfirmed" if run.cleanup_unconfirmed else "stage_settled"
        facts = {
            "operation_id": run.reference,
            "reported_success": bool(result.get("ok")),
            "calendar_effect": result.get("effect", "not_applicable"),
            "calendar_cleanup": result.get("cleanup", "not_needed"),
            "calendar_primary": result.get("primary", "not_attempted"),
            "calendar_index": result.get("index", "not_attempted"),
        }
        written = result.get("events_written" if stage == "publish" else "instances_written")
        if stage == "sync":
            counts = [
                result.get("rows_upserted_" + key) for key in ("recurring", "oneoff", "overrides")
            ]
            written = sum(counts) if all(type(v) is int for v in counts) else None
        if type(written) is int:
            facts["calendar_written"] = written
        if not result.get("ok") or run.cleanup_unconfirmed:
            optional(emit, "calendar_" + stage, "failed", facts=facts)
        optional(emit, "calendar_" + stage, "settled", facts=facts)
        return result

    def _save_stage(self, stage, result, started):
        status = result.get("status", "unknown")
        if stage == "sync":
            self._last_refresh_utc, self._last_status = started, status
            self._last_result = deepcopy(result)
        elif stage == "generate":
            self._last_generate_utc, self._last_generate_status = started, status
            self._last_generate_result = deepcopy(result)
        else:
            self._last_publish_utc, self._last_publish_status = started, status
            self._last_publish_result = deepcopy(result)

    async def _run_stage_with_policy(
        self,
        *,
        pipeline_run_id,
        actor_source,
        stage_name,
        policy,
        stage_call,
        allow_timeout_retry=False,
        run=None,
    ):
        # Legacy retry configuration is parse-compatible, never mutation authority.
        started = clock()
        task = asyncio.create_task(stage_call())
        done, _ = await asyncio.wait({task}, timeout=policy.timeout_seconds)
        if not done:
            if run is not None:
                run.observer = "deadline_elapsed_pending"
            optional(emit, "calendar_" + stage_name, "deadline_elapsed_pending")
        result = await asyncio.shield(task)
        if not done and run is not None and not run.stop.is_set():
            run.observer = "completed_after_deadline"
        ended = clock()
        duration = (
            max(0, int((ended - started) * 1000))
            if started is not None and ended is not None
            else None
        )
        optional(
            emit_telemetry_event,
            {
                "event": (
                    "calendar_pipeline_stage_succeeded"
                    if result.get("ok")
                    else "calendar_pipeline_stage_completed_not_ok"
                ),
                "pipeline_run_id": pipeline_run_id,
                "stage": stage_name,
                "attempt": 1,
            },
        )
        return result, duration, 1


def _base_result(raw):
    keys = (
        "ok",
        "status",
        "rows_read_recurring",
        "rows_read_oneoff",
        "rows_read_overrides",
        "rows_upserted_recurring",
        "rows_upserted_oneoff",
        "rows_upserted_overrides",
        "instances_generated",
        "instances_written",
        "cancelled_count",
        "modified_count",
        "events_written",
        "cache_path",
        "type_index_path",
        "error_message",
        "attempted",
        "primary",
        "index",
        "generation",
    )
    result = {k: deepcopy(getattr(raw, k)) for k in keys if hasattr(raw, k)}
    sql = getattr(raw, "sql", None)
    result.update(sql.public() if sql else {"effect": "unavailable", "cleanup": "not_needed"})
    warning = result.get("cleanup") == "unconfirmed" or result.get("status") in {
        "success_index_warning",
        "skipped_empty_preserve_existing",
    }
    result["severity"] = "warning" if warning else "ok" if result.get("ok") else "failed"
    result["details"] = (
        "Business effects are acknowledged. Database cleanup is unconfirmed; further work is blocked."
        if result.get("cleanup") == "unconfirmed" and result.get("ok")
        else (
            "Primary calendar published. The auxiliary type index could not be updated."
            if result.get("status") == "success_index_warning"
            else result.get("error_message") or result.get("status")
        )
    )
    return result


def _result_projection(raw):
    return _base_result(raw)


_service_singleton: CalendarService | None = None


def get_calendar_service() -> CalendarService:
    global _service_singleton
    if _service_singleton is None:
        _service_singleton = CalendarService()
    return _service_singleton
