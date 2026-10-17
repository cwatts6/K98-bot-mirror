"""Process-local monitor health, never authority for any recovery mutation."""

from datetime import UTC, datetime

_last_success = None
_failure = None


def record_success():
    global _last_success, _failure
    _last_success, _failure = datetime.now(UTC), None


def record_failure(error):
    global _failure
    _failure = type(error).__name__


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
    return healthy, text
