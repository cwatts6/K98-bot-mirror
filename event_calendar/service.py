from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import json
import logging
from pathlib import Path
from typing import Any

from constants import (
    EVENT_CALENDAR_CACHE_FILE_PATH,
    EVENT_CALENDAR_STALE_DEGRADED_MINUTES,
    EVENT_CALENDAR_STALE_WARN_MINUTES,
)
from event_calendar.cache_publisher import (
    PublishResult,
    publish_event_calendar_cache,
)
from event_calendar.event_generator import (
    GenerationResult,
    generate_calendar_instances,
)
from event_calendar.sheets_sync import SyncResult, sync_sheets_to_sql
from file_utils import emit_telemetry_event

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _parse_iso_utc(v: str | None) -> datetime | None:
    if not v:
        return None
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        return dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    except Exception:
        return None


class CalendarService:
    def __init__(self) -> None:
        # existing (sync) state
        self._last_refresh_utc: datetime | None = None
        self._last_status: str = "not_started"
        self._last_result: dict[str, Any] | None = None

        # new (generate) state
        self._last_generate_utc: datetime | None = None
        self._last_generate_status: str = "not_started"
        self._last_generate_result: dict[str, Any] | None = None

        # new (publish) state
        self._last_publish_utc: datetime | None = None
        self._last_publish_status: str = "not_started"
        self._last_publish_result: dict[str, Any] | None = None

    async def _calendar_health(self) -> dict[str, Any]:
        cache_path = Path(EVENT_CALENDAR_CACHE_FILE_PATH)
        now = _utcnow()

        cache_age_minutes: int | None = None
        next_upcoming_event_utc: str | None = None
        degraded = False
        warning = False

        if cache_path.exists():
            mtime = datetime.fromtimestamp(cache_path.stat().st_mtime, tz=UTC)
            cache_age_minutes = max(0, int((now - mtime).total_seconds() // 60))
            warning = cache_age_minutes >= EVENT_CALENDAR_STALE_WARN_MINUTES
            degraded = cache_age_minutes >= EVENT_CALENDAR_STALE_DEGRADED_MINUTES

            try:
                payload = json.loads(cache_path.read_text(encoding="utf-8"))
                upcoming = []
                for e in payload.get("events", []):
                    dt = _parse_iso_utc(e.get("start_utc"))
                    if dt and dt >= now:
                        upcoming.append(dt)
                if upcoming:
                    next_upcoming_event_utc = min(upcoming).isoformat()
            except Exception:
                degraded = True

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
            "cache_stale_warning": warning,
            "next_upcoming_event_utc": next_upcoming_event_utc,
            "last_successful_pipeline_utc": (
                pipeline_success.isoformat() if pipeline_success else None
            ),
            "current_degraded_mode": degraded,
        }

    async def get_status(self) -> dict[str, Any]:
        return {
            "mode": "sheets_sql_generate_publish",
            "sync": {
                "status": self._last_status,
                "last_refresh_utc": (
                    self._last_refresh_utc.isoformat() if self._last_refresh_utc else None
                ),
                "last_result": self._last_result,
            },
            "generate": {
                "status": self._last_generate_status,
                "last_generate_utc": (
                    self._last_generate_utc.isoformat() if self._last_generate_utc else None
                ),
                "last_result": self._last_generate_result,
            },
            "publish": {
                "status": self._last_publish_status,
                "last_publish_utc": (
                    self._last_publish_utc.isoformat() if self._last_publish_utc else None
                ),
                "last_result": self._last_publish_result,
            },
            "calendar_health": await self._calendar_health(),
        }

    async def refresh(
        self, *, actor_user_id: int | None = None, sheet_id: str | None = None
    ) -> dict[str, Any]:
        started = _utcnow()
        try:
            if not sheet_id:
                raise ValueError("EVENT_CALENDAR_SHEET_ID is not configured")

            # run blocking HTTP+DB sync off event loop
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
        started = _utcnow()
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
        started = _utcnow()
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

    async def refresh_full(
        self,
        *,
        actor_user_id: int | None = None,
        sheet_id: str | None = None,
        horizon_days: int = 365,
        force_empty: bool = False,
    ) -> dict[str, Any]:
        """
        Optional orchestration helper:
        Sheets sync -> generate instances -> publish cache
        Stops early on failure.
        """
        sync_res = await self.refresh(actor_user_id=actor_user_id, sheet_id=sheet_id)
        if not sync_res.get("ok"):
            return {"ok": False, "stage": "sync", "sync": sync_res}

        gen_res = await self.generate(actor_user_id=actor_user_id, horizon_days=horizon_days)
        if not gen_res.get("ok"):
            return {
                "ok": False,
                "stage": "generate",
                "sync": sync_res,
                "generate": gen_res,
            }

        pub_res = await self.publish_cache(
            actor_user_id=actor_user_id,
            horizon_days=horizon_days,
            force_empty=force_empty,
        )
        if not pub_res.get("ok"):
            return {
                "ok": False,
                "stage": "publish",
                "sync": sync_res,
                "generate": gen_res,
                "publish": pub_res,
            }

        return {
            "ok": True,
            "stage": "done",
            "sync": sync_res,
            "generate": gen_res,
            "publish": pub_res,
        }


_service_singleton: CalendarService | None = None


def get_calendar_service() -> CalendarService:
    global _service_singleton
    if _service_singleton is None:
        _service_singleton = CalendarService()
    return _service_singleton
