from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import logging
from pathlib import Path
from typing import Any
import uuid

from constants import (
    EVENT_CALENDAR_CACHE_FILE_PATH,
    EVENT_CALENDAR_PIPELINE_BACKOFF_BASE_SECONDS,
    EVENT_CALENDAR_PIPELINE_BACKOFF_CAP_SECONDS,
    EVENT_CALENDAR_PIPELINE_GENERATE_RETRIES,
    EVENT_CALENDAR_PIPELINE_GENERATE_TIMEOUT_SECONDS,
    EVENT_CALENDAR_PIPELINE_PUBLISH_RETRIES,
    EVENT_CALENDAR_PIPELINE_PUBLISH_TIMEOUT_SECONDS,
    EVENT_CALENDAR_PIPELINE_RETRY_ENABLED,
    EVENT_CALENDAR_PIPELINE_SYNC_RETRIES,
    EVENT_CALENDAR_PIPELINE_SYNC_TIMEOUT_SECONDS,
    EVENT_CALENDAR_STALE_DEGRADED_MINUTES,
    EVENT_CALENDAR_STALE_WARN_MINUTES,
)
from event_calendar.cache_publisher import PublishResult, publish_event_calendar_cache
from event_calendar.datetime_utils import now_utc, parse_iso_utc_nullable
from event_calendar.event_generator import GenerationResult, generate_calendar_instances
from event_calendar.reminder_metrics import get_reminder_status_service
from event_calendar.sheets_sync import SyncResult, sync_sheets_to_sql
from file_utils import emit_telemetry_event

logger = logging.getLogger(__name__)


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

            meta = payload.get("meta", {}) if isinstance(payload, dict) else {}
            horizon = meta.get("horizon_days")
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
    end = completed or now_utc()
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

    def _record_latest_error(self, *, stage: str, exc: Exception | None, message: str) -> None:
        error_type = type(exc).__name__ if exc else "ResultFailure"
        self._latest_error = {
            "stage": stage,
            "error_type": error_type,
            "message": message,
            "at_utc": now_utc().isoformat(),
        }

    def _clear_latest_error(self) -> None:
        self._latest_error = None

    async def _calendar_health(self) -> dict[str, Any]:
        cache_path = Path(EVENT_CALENDAR_CACHE_FILE_PATH)
        now = now_utc()

        (
            cache_age_minutes,
            warning,
            degraded,
            next_upcoming_event_utc,
            cache_event_count,
            cache_horizon_days,
        ) = await asyncio.to_thread(_load_cache_state, cache_path, now)

        pipeline_success = None
        if (
            self._last_status == "success"
            and self._last_generate_status == "success"
            and self._last_publish_status in {"success", "skipped_empty_preserve_existing"}
        ):
            pipeline_success = (
                self._last_publish_utc or self._last_generate_utc or self._last_refresh_utc
            )

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
            "sync": {
                "status": self._last_status or "not_started",
                "last_refresh_utc": (
                    self._last_refresh_utc.isoformat() if self._last_refresh_utc else "not_started"
                ),
                "last_result": self._last_result,
            },
            "generate": {
                "status": self._last_generate_status or "not_started",
                "last_generate_utc": (
                    self._last_generate_utc.isoformat()
                    if self._last_generate_utc
                    else "not_started"
                ),
                "last_result": self._last_generate_result,
            },
            "publish": {
                "status": self._last_publish_status or "not_started",
                "last_publish_utc": (
                    self._last_publish_utc.isoformat() if self._last_publish_utc else "not_started"
                ),
                "last_result": self._last_publish_result,
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
                "last_result": self._last_pipeline_result,
            },
            "reminders": get_reminder_status_service().get_status(),
            "latest_error": self._latest_error or {},
            "calendar_health": await self._calendar_health(),
        }

    async def refresh(
        self, *, actor_user_id: int | None = None, sheet_id: str | None = None
    ) -> dict[str, Any]:
        started = now_utc()
        try:
            if not sheet_id:
                raise ValueError("EVENT_CALENDAR_SHEET_ID is not configured")

            result: SyncResult = await asyncio.to_thread(sync_sheets_to_sql, sheet_id)

            self._last_refresh_utc = started
            self._last_status = result.status
            self._last_result = {
                "ok": result.ok,
                "status": result.status,
                "rows_read_recurring": result.rows_read_recurring,
                "rows_read_oneoff": result.rows_read_oneoff,
                "rows_read_overrides": result.rows_read_overrides,
                "rows_upserted_recurring": result.rows_upserted_recurring,
                "rows_upserted_oneoff": result.rows_upserted_oneoff,
                "rows_upserted_overrides": result.rows_upserted_overrides,
                "instances_generated": result.instances_generated,
                "error_message": result.error_message,
            }

            emit_telemetry_event(
                {
                    "event": "calendar_refresh",
                    "actor_user_id": actor_user_id,
                    "status": result.status,
                    "ok": result.ok,
                }
            )

            return {
                "ok": result.ok,
                "status": result.status,
                "refreshed_utc": started.isoformat(),
                "details": result.error_message or "Sync completed.",
                **self._last_result,
            }
        except Exception as e:
            error_type = type(e).__name__
            error_message = f"{error_type}: {e}"

            self._last_refresh_utc = started
            self._last_status = "failed_service"
            self._last_result = {"ok": False, "error_message": error_message}

            logger.exception("[CALENDAR] refresh failed")
            emit_telemetry_event(
                {
                    "event": "calendar_refresh",
                    "actor_user_id": actor_user_id,
                    "status": self._last_status,
                    "ok": False,
                    "error_type": error_type,
                    "error_message": error_message,
                }
            )

            return {
                "ok": False,
                "status": self._last_status,
                "refreshed_utc": started.isoformat(),
                "details": error_message,
            }

    async def generate(
        self, *, actor_user_id: int | None = None, horizon_days: int = 365
    ) -> dict[str, Any]:
        started = now_utc()
        try:
            result: GenerationResult = await asyncio.to_thread(
                generate_calendar_instances, horizon_days=horizon_days
            )

            self._last_generate_utc = started
            self._last_generate_status = result.status
            self._last_generate_result = {
                "ok": result.ok,
                "status": result.status,
                "instances_generated": result.instances_generated,
                "instances_written": result.instances_written,
                "cancelled_count": result.cancelled_count,
                "modified_count": result.modified_count,
                "error_message": result.error_message,
            }

            emit_telemetry_event(
                {
                    "event": "calendar_generate",
                    "actor_user_id": actor_user_id,
                    "ok": result.ok,
                    "status": result.status,
                    "horizon_days": horizon_days,
                    "instances_generated": result.instances_generated,
                    "instances_written": result.instances_written,
                }
            )

            return {
                "ok": result.ok,
                "status": result.status,
                "generated_utc": started.isoformat(),
                "details": result.error_message or "Generation completed.",
                **self._last_generate_result,
            }
        except Exception as e:
            error_type = type(e).__name__
            error_message = f"{error_type}: {e}"

            self._last_generate_utc = started
            self._last_generate_status = "failed_service"
            self._last_generate_result = {"ok": False, "error_message": error_message}

            logger.exception("[CALENDAR] generate failed")
            emit_telemetry_event(
                {
                    "event": "calendar_generate",
                    "actor_user_id": actor_user_id,
                    "ok": False,
                    "status": self._last_generate_status,
                    "error_type": error_type,
                    "error_message": error_message,
                    "horizon_days": horizon_days,
                }
            )

            return {
                "ok": False,
                "status": self._last_generate_status,
                "generated_utc": started.isoformat(),
                "details": error_message,
            }

    async def publish_cache(
        self,
        *,
        actor_user_id: int | None = None,
        horizon_days: int = 365,
        force_empty: bool = False,
    ) -> dict[str, Any]:
        started = now_utc()
        try:
            result: PublishResult = await asyncio.to_thread(
                publish_event_calendar_cache,
                horizon_days=horizon_days,
                force_empty=force_empty,
            )

            self._last_publish_utc = started
            self._last_publish_status = result.status
            self._last_publish_result = {
                "ok": result.ok,
                "status": result.status,
                "events_written": result.events_written,
                "cache_path": result.cache_path,
                "type_index_path": getattr(result, "type_index_path", None),
                "error_message": result.error_message,
            }

            emit_telemetry_event(
                {
                    "event": "calendar_publish_cache",
                    "actor_user_id": actor_user_id,
                    "ok": result.ok,
                    "status": result.status,
                    "events_written": result.events_written,
                    "horizon_days": horizon_days,
                    "force_empty": force_empty,
                }
            )

            return {
                "ok": result.ok,
                "status": result.status,
                "published_utc": started.isoformat(),
                "details": result.error_message or "Publish completed.",
                **self._last_publish_result,
            }
        except Exception as e:
            error_type = type(e).__name__
            error_message = f"{error_type}: {e}"

            self._last_publish_utc = started
            self._last_publish_status = "failed_service"
            self._last_publish_result = {"ok": False, "error_message": error_message}

            logger.exception("[CALENDAR] publish_cache failed")
            emit_telemetry_event(
                {
                    "event": "calendar_publish_cache",
                    "actor_user_id": actor_user_id,
                    "ok": False,
                    "status": self._last_publish_status,
                    "error_type": error_type,
                    "error_message": error_message,
                    "horizon_days": horizon_days,
                    "force_empty": force_empty,
                }
            )

            return {
                "ok": False,
                "status": self._last_publish_status,
                "published_utc": started.isoformat(),
                "details": error_message,
            }

    def _result_retryable(self, *, stage_name: str, result: dict[str, Any]) -> bool:
        status = str(result.get("status") or "").lower()

        retryable_status_by_stage: dict[str, set[str]] = {
            "sync": {"failed_service", "timeout", "transient_error", "retryable_error"},
            "generate": {"failed_service", "timeout", "transient_error", "retryable_error"},
            "publish": {"failed_service", "timeout", "transient_error", "retryable_error"},
        }
        retryable = retryable_status_by_stage.get(stage_name, set())
        return status in retryable

    async def _run_stage_with_policy(
        self,
        *,
        pipeline_run_id: str,
        actor_source: str,
        stage_name: str,
        policy: _StagePolicy,
        stage_call: Callable[[], Awaitable[dict[str, Any]]],
        allow_timeout_retry: bool = False,
    ) -> tuple[dict[str, Any], int, int]:
        attempt = 0
        while True:
            attempt += 1
            stage_started = now_utc()
            emit_telemetry_event(
                {
                    "event": "calendar_pipeline_stage_started",
                    "pipeline_run_id": pipeline_run_id,
                    "actor_source": actor_source,
                    "stage": stage_name,
                    "attempt": attempt,
                    "timeout_seconds": policy.timeout_seconds,
                }
            )

            try:
                result = await asyncio.wait_for(stage_call(), timeout=policy.timeout_seconds)
                dur = _duration_ms(stage_started)

                ok = bool(result.get("ok"))
                status = result.get("status")

                if not ok and EVENT_CALENDAR_PIPELINE_RETRY_ENABLED and attempt <= policy.retries:
                    retryable_result = self._result_retryable(stage_name=stage_name, result=result)
                    if retryable_result:
                        backoff = min(
                            EVENT_CALENDAR_PIPELINE_BACKOFF_CAP_SECONDS,
                            EVENT_CALENDAR_PIPELINE_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)),
                        )
                        emit_telemetry_event(
                            {
                                "event": "calendar_pipeline_retry_scheduled",
                                "pipeline_run_id": pipeline_run_id,
                                "actor_source": actor_source,
                                "stage": stage_name,
                                "attempt": attempt,
                                "sleep_seconds": backoff,
                                "reason": "result_retryable_status",
                                "status": status,
                            }
                        )
                        await asyncio.sleep(backoff)
                        continue

                # Task 8 fix: do not emit "succeeded" when ok=False.
                if ok:
                    emit_telemetry_event(
                        {
                            "event": "calendar_pipeline_stage_succeeded",
                            "pipeline_run_id": pipeline_run_id,
                            "actor_source": actor_source,
                            "stage": stage_name,
                            "attempt": attempt,
                            "duration_ms": dur,
                            "status": status,
                            "ok": True,
                        }
                    )
                else:
                    emit_telemetry_event(
                        {
                            "event": "calendar_pipeline_stage_completed_not_ok",
                            "pipeline_run_id": pipeline_run_id,
                            "actor_source": actor_source,
                            "stage": stage_name,
                            "attempt": attempt,
                            "duration_ms": dur,
                            "status": status,
                            "ok": False,
                        }
                    )

                return result, dur, attempt

            except Exception as e:
                dur = _duration_ms(stage_started)
                error_kind = _classify_error(e)

                can_retry_timeout = allow_timeout_retry and error_kind == "timeout"
                can_retry_exception = error_kind == "exception"
                can_retry = (
                    EVENT_CALENDAR_PIPELINE_RETRY_ENABLED
                    and attempt <= policy.retries
                    and (can_retry_timeout or can_retry_exception)
                )

                emit_telemetry_event(
                    {
                        "event": "calendar_pipeline_stage_failed",
                        "pipeline_run_id": pipeline_run_id,
                        "actor_source": actor_source,
                        "stage": stage_name,
                        "attempt": attempt,
                        "duration_ms": dur,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "error_kind": error_kind,
                        "will_retry": can_retry,
                        "timeout_retry_allowed": allow_timeout_retry,
                    }
                )

                if not can_retry:
                    raise

                backoff = min(
                    EVENT_CALENDAR_PIPELINE_BACKOFF_CAP_SECONDS,
                    EVENT_CALENDAR_PIPELINE_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)),
                )
                emit_telemetry_event(
                    {
                        "event": "calendar_pipeline_retry_scheduled",
                        "pipeline_run_id": pipeline_run_id,
                        "actor_source": actor_source,
                        "stage": stage_name,
                        "attempt": attempt,
                        "sleep_seconds": backoff,
                        "reason": "exception_retry",
                    }
                )
                await asyncio.sleep(backoff)

    async def refresh_pipeline(
        self,
        *,
        actor_user_id: int | None = None,
        sheet_id: str | None = None,
        horizon_days: int = 365,
        force_empty: bool = False,
        actor_source: str | None = None,
    ) -> dict[str, Any]:
        pipeline_started = now_utc()
        pipeline_run_id = uuid.uuid4().hex
        source = actor_source or (f"admin:{actor_user_id}" if actor_user_id else "scheduler")

        emit_telemetry_event(
            {
                "event": "calendar_pipeline_started",
                "pipeline_run_id": pipeline_run_id,
                "actor_source": source,
                "actor_user_id": actor_user_id,
                "horizon_days": horizon_days,
                "force_empty": force_empty,
            }
        )

        policies = {
            "sync": _StagePolicy(
                timeout_seconds=EVENT_CALENDAR_PIPELINE_SYNC_TIMEOUT_SECONDS,
                retries=EVENT_CALENDAR_PIPELINE_SYNC_RETRIES,
            ),
            "generate": _StagePolicy(
                timeout_seconds=EVENT_CALENDAR_PIPELINE_GENERATE_TIMEOUT_SECONDS,
                retries=EVENT_CALENDAR_PIPELINE_GENERATE_RETRIES,
            ),
            "publish": _StagePolicy(
                timeout_seconds=EVENT_CALENDAR_PIPELINE_PUBLISH_TIMEOUT_SECONDS,
                retries=EVENT_CALENDAR_PIPELINE_PUBLISH_RETRIES,
            ),
        }

        stage_status: dict[str, Any] = {}
        stage_durations_ms: dict[str, int] = {}
        errors: list[str] = []

        sync_result: dict[str, Any] | None = None
        gen_result: dict[str, Any] | None = None
        pub_result: dict[str, Any] | None = None

        try:
            sync_result, sync_dur, sync_attempts = await self._run_stage_with_policy(
                pipeline_run_id=pipeline_run_id,
                actor_source=source,
                stage_name="sync",
                policy=policies["sync"],
                stage_call=lambda: self.refresh(actor_user_id=actor_user_id, sheet_id=sheet_id),
                allow_timeout_retry=False,
            )
            stage_status["sync"] = {
                "ok": bool(sync_result.get("ok")),
                "status": sync_result.get("status"),
                "attempts": sync_attempts,
            }
            stage_durations_ms["sync"] = sync_dur

            if not sync_result.get("ok"):
                msg = f"sync failed: {sync_result.get('details') or sync_result.get('status')}"
                errors.append(msg)
                self._record_latest_error(stage="sync", exc=None, message=msg)
                completed = now_utc()
                out = {
                    "ok": False,
                    "stage": "sync",
                    "pipeline_run_id": pipeline_run_id,
                    "actor_source": source,
                    "sheets_sync_success": False,
                    "sql_generation_success": False,
                    "json_export_success": False,
                    "events_generated": 0,
                    "events_written": 0,
                    "errors": errors,
                    "pipeline_started_utc": pipeline_started.isoformat(),
                    "pipeline_completed_utc": completed.isoformat(),
                    "duration_ms": _duration_ms(pipeline_started, completed),
                    "stage_durations_ms": stage_durations_ms,
                    "stage_status": stage_status,
                    "sync": sync_result,
                    "severity": _severity_from_pipeline(
                        ok=False, stage="sync", publish_status=None
                    ),
                }
                self._last_pipeline_utc = completed
                self._last_pipeline_status = "failed_sync"
                self._last_pipeline_result = out
                self._last_pipeline_run_id = pipeline_run_id
                emit_telemetry_event({"event": "calendar_pipeline_failed", **out})
                return out

            gen_result, gen_dur, gen_attempts = await self._run_stage_with_policy(
                pipeline_run_id=pipeline_run_id,
                actor_source=source,
                stage_name="generate",
                policy=policies["generate"],
                stage_call=lambda: self.generate(
                    actor_user_id=actor_user_id,
                    horizon_days=horizon_days,
                ),
                allow_timeout_retry=False,
            )
            stage_status["generate"] = {
                "ok": bool(gen_result.get("ok")),
                "status": gen_result.get("status"),
                "attempts": gen_attempts,
            }
            stage_durations_ms["generate"] = gen_dur

            if not gen_result.get("ok"):
                msg = f"generate failed: {gen_result.get('details') or gen_result.get('status')}"
                errors.append(msg)
                self._record_latest_error(stage="generate", exc=None, message=msg)
                completed = now_utc()
                out = {
                    "ok": False,
                    "stage": "generate",
                    "pipeline_run_id": pipeline_run_id,
                    "actor_source": source,
                    "sheets_sync_success": True,
                    "sql_generation_success": False,
                    "json_export_success": False,
                    "events_generated": 0,
                    "events_written": 0,
                    "errors": errors,
                    "pipeline_started_utc": pipeline_started.isoformat(),
                    "pipeline_completed_utc": completed.isoformat(),
                    "duration_ms": _duration_ms(pipeline_started, completed),
                    "stage_durations_ms": stage_durations_ms,
                    "stage_status": stage_status,
                    "sync": sync_result,
                    "generate": gen_result,
                    "severity": _severity_from_pipeline(
                        ok=False, stage="generate", publish_status=None
                    ),
                }
                self._last_pipeline_utc = completed
                self._last_pipeline_status = "failed_generate"
                self._last_pipeline_result = out
                self._last_pipeline_run_id = pipeline_run_id
                emit_telemetry_event({"event": "calendar_pipeline_failed", **out})
                return out

            pub_result, pub_dur, pub_attempts = await self._run_stage_with_policy(
                pipeline_run_id=pipeline_run_id,
                actor_source=source,
                stage_name="publish",
                policy=policies["publish"],
                stage_call=lambda: self.publish_cache(
                    actor_user_id=actor_user_id,
                    horizon_days=horizon_days,
                    force_empty=force_empty,
                ),
                allow_timeout_retry=False,
            )
            stage_status["publish"] = {
                "ok": bool(pub_result.get("ok")),
                "status": pub_result.get("status"),
                "attempts": pub_attempts,
            }
            stage_durations_ms["publish"] = pub_dur

            pub_ok = _is_publish_success(pub_result)
            if not pub_ok:
                msg = f"publish failed: {pub_result.get('details') or pub_result.get('status')}"
                errors.append(msg)
                self._record_latest_error(stage="publish", exc=None, message=msg)
                completed = now_utc()
                out = {
                    "ok": False,
                    "stage": "publish",
                    "pipeline_run_id": pipeline_run_id,
                    "actor_source": source,
                    "sheets_sync_success": True,
                    "sql_generation_success": True,
                    "json_export_success": False,
                    "events_generated": int(gen_result.get("instances_generated") or 0),
                    "events_written": int(pub_result.get("events_written") or 0),
                    "errors": errors,
                    "pipeline_started_utc": pipeline_started.isoformat(),
                    "pipeline_completed_utc": completed.isoformat(),
                    "duration_ms": _duration_ms(pipeline_started, completed),
                    "stage_durations_ms": stage_durations_ms,
                    "stage_status": stage_status,
                    "sync": sync_result,
                    "generate": gen_result,
                    "publish": pub_result,
                    "publish_reason": pub_result.get("status"),
                    "severity": _severity_from_pipeline(
                        ok=False, stage="publish", publish_status=pub_result.get("status")
                    ),
                }
                self._last_pipeline_utc = completed
                self._last_pipeline_status = "failed_publish"
                self._last_pipeline_result = out
                self._last_pipeline_run_id = pipeline_run_id
                emit_telemetry_event({"event": "calendar_pipeline_failed", **out})
                return out

            completed = now_utc()
            out = {
                "ok": True,
                "stage": "done",
                "pipeline_run_id": pipeline_run_id,
                "actor_source": source,
                "sheets_sync_success": True,
                "sql_generation_success": True,
                "json_export_success": True,
                "events_generated": int(gen_result.get("instances_generated") or 0),
                "events_written": int(pub_result.get("events_written") or 0),
                "errors": [],
                "pipeline_started_utc": pipeline_started.isoformat(),
                "pipeline_completed_utc": completed.isoformat(),
                "duration_ms": _duration_ms(pipeline_started, completed),
                "stage_durations_ms": stage_durations_ms,
                "stage_status": stage_status,
                "sync": sync_result,
                "generate": gen_result,
                "publish": pub_result,
                "publish_reason": pub_result.get("status"),
                "severity": _severity_from_pipeline(
                    ok=True, stage="done", publish_status=pub_result.get("status")
                ),
            }
            self._last_pipeline_utc = completed
            self._last_pipeline_status = "success"
            self._last_pipeline_result = out
            self._last_pipeline_run_id = pipeline_run_id
            self._clear_latest_error()
            emit_telemetry_event({"event": "calendar_pipeline_completed", **out})
            return out

        except Exception as e:
            completed = now_utc()
            err = f"{type(e).__name__}: {e}"
            errors.append(err)
            self._record_latest_error(stage="exception", exc=e, message=err)
            out = {
                "ok": False,
                "stage": "exception",
                "pipeline_run_id": pipeline_run_id,
                "actor_source": source,
                "sheets_sync_success": bool(sync_result and sync_result.get("ok")),
                "sql_generation_success": bool(gen_result and gen_result.get("ok")),
                "json_export_success": bool(pub_result and _is_publish_success(pub_result)),
                "events_generated": int((gen_result or {}).get("instances_generated") or 0),
                "events_written": int((pub_result or {}).get("events_written") or 0),
                "errors": errors,
                "pipeline_started_utc": pipeline_started.isoformat(),
                "pipeline_completed_utc": completed.isoformat(),
                "duration_ms": _duration_ms(pipeline_started, completed),
                "stage_durations_ms": stage_durations_ms,
                "stage_status": stage_status,
                "sync": sync_result,
                "generate": gen_result,
                "publish": pub_result,
                "severity": "failed",
            }
            self._last_pipeline_utc = completed
            self._last_pipeline_status = "failed_exception"
            self._last_pipeline_result = out
            self._last_pipeline_run_id = pipeline_run_id
            logger.exception("[CALENDAR] refresh_pipeline failed")
            emit_telemetry_event({"event": "calendar_pipeline_failed", **out})
            return out

    async def refresh_full(
        self,
        *,
        actor_user_id: int | None = None,
        sheet_id: str | None = None,
        horizon_days: int = 365,
        force_empty: bool = False,
    ) -> dict[str, Any]:
        return await self.refresh_pipeline(
            actor_user_id=actor_user_id,
            sheet_id=sheet_id,
            horizon_days=horizon_days,
            force_empty=force_empty,
        )


_service_singleton: CalendarService | None = None


def get_calendar_service() -> CalendarService:
    global _service_singleton
    if _service_singleton is None:
        _service_singleton = CalendarService()
    return _service_singleton
