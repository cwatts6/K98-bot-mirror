"""Process-local monitor health, never authority for any recovery mutation."""

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import PurePath
import traceback

_last_success = None
_failure = None
_failure_detail = None
_notification_failure = None
_cycle = None
_checks = []


def begin_cycle():
    global _cycle, _checks
    _checks = []
    now = datetime.now(UTC).isoformat()
    _cycle = dict(started_utc=now, progress_utc=now, stage="starting", in_progress=True)


def record_check(stage, error, *, waiting=False):
    """Bounded original call sites; never exception messages or mutation authority."""
    detail = dict(failure_detail(error), stage=stage, waiting=waiting)
    if len(_checks) < 100:
        _checks.append(detail)
    if _cycle:
        key = "waiting_checks" if waiting else "failed_checks"
        _cycle[key] = _cycle.get(key, 0) + 1
    return detail


def record_progress(stage):
    """Diagnostic progress only; it never makes an incomplete check healthy."""
    global _cycle
    if _cycle and _cycle["in_progress"]:
        _cycle = dict(_cycle, progress_utc=datetime.now(UTC).isoformat(), stage=stage)


def _finish_cycle():
    global _cycle
    if _cycle:
        _cycle = dict(_cycle, finished_utc=datetime.now(UTC).isoformat(), in_progress=False)


def failure_detail(error):
    """Retain call sites, never exception text, locals or private payloads."""
    from services.export_failure_diagnostics import failure_record

    facts = failure_record(error)
    return {
        "error_type": type(error).__name__,
        "observed_utc": datetime.now(UTC).isoformat(),
        "exception_types": facts["exception_types"],
        "sqlstates": facts["sqlstates"],
        "sql_numbers": facts["sql_numbers"],
        "frames": [
            {"file": PurePath(frame.filename).name, "line": frame.lineno, "function": frame.name}
            for frame in traceback.extract_tb(error.__traceback__)[-12:]
        ],
    }


def record_notifications(error=None, *, pending=False):
    global _notification_failure
    if error is not None:
        _notification_failure = failure_detail(error)
    elif pending:
        # The durable lease can outlive this process and its original exception.
        # Preserve a known cause, or reconstruct a safe pending-delivery signal.
        if _notification_failure is None:
            _notification_failure = {
                "error_type": "DeliveryPendingVerification",
                "observed_utc": datetime.now(UTC).isoformat(),
                "frames": [],
            }
    else:
        _notification_failure = None


def record_success():
    global _last_success, _failure, _failure_detail
    _last_success, _failure = datetime.now(UTC), None
    _failure_detail = None
    _finish_cycle()


def record_failure(error):
    global _failure, _failure_detail
    _failure = type(error).__name__
    _failure_detail = failure_detail(error)
    _finish_cycle()


def report():
    from core.scheduler_lifecycle import event_startup_report
    from core.startup_diagnostics import report as startup_report
    from event_cache import refresh_service
    from event_scheduler import dm_startup_report
    from profile_cache import get_cache_stats
    from services.cache_admission_diagnostics import report as admission_report
    from services.event_delivery_service import report as event_delivery_report
    from services.player_stats_cache_service import report as stats_report
    from target_utils import name_outcome_report

    healthy, text = status()
    return {
        "healthy": healthy,
        "status": text,
        "last_success_utc": _last_success.isoformat() if _last_success else None,
        "check_failure": _failure_detail,
        "notification_failure": _notification_failure,
        "cycle": dict(_cycle) if _cycle else None,
        "checks": deepcopy(_checks),
        "startup": startup_report(),
        "admission_observations_v1": admission_report(),
        "cache_outcomes_v1": {
            "stats": stats_report(),
            "profile": get_cache_stats()["outcome"],
            "name": name_outcome_report(),
        },
        "event_cache": refresh_service.report(),
        "event_startup": event_startup_report(),
        "event_dm_startup": dm_startup_report(),
        "event_delivery_v1": event_delivery_report(),
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
    if _cycle and _cycle.get("waiting_checks"):
        text += ". Existing SQL work or publication verification is still running; its recovery checks will retry automatically. No completion or release is inferred"
    if not healthy and _cycle and _cycle["in_progress"]:
        text += ". A monitoring cycle is in progress; the downloadable report identifies its latest checkpoint"
    if _notification_failure:
        text += ". Incident notifications need attention; open the recovery centre and download its report"
    return healthy, text
