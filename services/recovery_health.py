"""Process-local monitor health, never authority for any recovery mutation."""

from datetime import UTC, datetime
from pathlib import PurePath
import traceback

_last_success = None
_failure = None
_failure_detail = None
_notification_failure = None


def failure_detail(error):
    """Retain call sites, never exception text, locals or private payloads."""
    return {
        "error_type": type(error).__name__,
        "observed_utc": datetime.now(UTC).isoformat(),
        "frames": [
            {"file": PurePath(frame.filename).name, "line": frame.lineno, "function": frame.name}
            for frame in traceback.extract_tb(error.__traceback__)[-12:]
        ],
    }


def record_notifications(error=None):
    global _notification_failure
    _notification_failure = failure_detail(error) if error else None


def record_success():
    global _last_success, _failure, _failure_detail
    _last_success, _failure = datetime.now(UTC), None
    _failure_detail = None


def record_failure(error):
    global _failure, _failure_detail
    _failure = type(error).__name__
    _failure_detail = failure_detail(error)


def report():
    return {
        "healthy": status()[0],
        "status": status()[1],
        "last_success_utc": _last_success.isoformat() if _last_success else None,
        "check_failure": _failure_detail,
        "notification_failure": _notification_failure,
    }


def status():
    healthy = (
        _last_success is not None
        and _failure is None
        and (datetime.now(UTC) - _last_success).total_seconds() <= 90
    )
    text = (
        "Monitoring active"
        if healthy
        else "Monitoring unavailable or stale; recovery status is not established"
    )
    if _last_success:
        text += f". Last successful check: {_last_success.isoformat()}"
    if _notification_failure:
        text += ". Incident notifications need attention; open the recovery centre and download its report"
        healthy = False
    return healthy, text
