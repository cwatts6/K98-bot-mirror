from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from typing import Any


def _now_utc_iso() -> str:
    return datetime.now(UTC).isoformat()


class ReminderStatusService:
    """
    In-process singleton status store for latest reminder dispatch metrics.
    Thread-safe for loop/task access.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._last: dict[str, Any] = {
            "status": "not_started",
            "ok": None,
            "last_dispatch_utc": "not_started",
            "dry_run": None,
            "candidates": 0,
            "attempted": 0,
            "sent": 0,
            "skipped_prefs": 0,
            "skipped_already_sent": 0,
            "skipped_unknown_type": 0,
            "failures": 0,
            "failed_forbidden": 0,
            "failed_not_found": 0,
            "failed_http_exception": 0,
            "failed_unknown": 0,
        }

    def record_summary(self, *, summary: Any, dry_run: bool) -> None:
        payload = {
            "status": str(getattr(summary, "status", "unknown")),
            "ok": bool(getattr(summary, "ok", False)),
            "last_dispatch_utc": _now_utc_iso(),
            "dry_run": bool(dry_run),
            "candidates": int(getattr(summary, "candidates", 0) or 0),
            "attempted": int(getattr(summary, "attempted", 0) or 0),
            "sent": int(getattr(summary, "sent", 0) or 0),
            "skipped_prefs": int(getattr(summary, "skipped_prefs", 0) or 0),
            "skipped_already_sent": int(getattr(summary, "skipped_already_sent", 0) or 0),
            "skipped_unknown_type": int(getattr(summary, "skipped_unknown_type", 0) or 0),
            "failures": int(getattr(summary, "failures", 0) or 0),
            "failed_forbidden": int(getattr(summary, "failed_forbidden", 0) or 0),
            "failed_not_found": int(getattr(summary, "failed_not_found", 0) or 0),
            "failed_http_exception": int(getattr(summary, "failed_http_exception", 0) or 0),
            "failed_unknown": int(getattr(summary, "failed_unknown", 0) or 0),
        }
        with self._lock:
            self._last = payload

    def record_failure(self, *, status: str, error_message: str, dry_run: bool | None) -> None:
        with self._lock:
            self._last = {
                **self._last,
                "status": str(status or "failed"),
                "ok": False,
                "last_dispatch_utc": _now_utc_iso(),
                "dry_run": dry_run,
                "error_message": str(error_message),
            }

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._last)


_service_singleton: ReminderStatusService | None = None


def get_reminder_status_service() -> ReminderStatusService:
    global _service_singleton
    if _service_singleton is None:
        _service_singleton = ReminderStatusService()
    return _service_singleton
