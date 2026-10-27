"""Process-local monitor health, never authority for any recovery mutation."""

from copy import deepcopy
from datetime import UTC, datetime
from functools import wraps
import hashlib
import json
import logging
from pathlib import PurePath
from threading import RLock
import time
import traceback

logger = logging.getLogger(__name__)
_lock = RLock()
# Diagnostic limits only: never cancel, release or replay an operation.
FRESH_SECONDS = 90.0
STALL_SECONDS = 300.0  # Same investigation horizon as the retained HealthProbe.
CYCLE_SECONDS = 900.0
_last_completed_cycle = None
_last_failed_cycle = None
_cycle_started = _progress_at = _stage_started = None
_notifications_started = None
_failure_streak = 0
_history = None
_episode_fingerprint = None
_logged_checks = set()


def synchronized(fn):
    @wraps(fn)
    def locked(*args, **kwargs):
        with _lock:
            return fn(*args, **kwargs)

    return locked


_last_success = None
_failure = None
_failure_detail = None
_notification_failure = None
_cycle = None
_checks = []


@synchronized
def begin_cycle():
    global _cycle, _checks, _cycle_started, _progress_at, _stage_started, _logged_checks
    _checks = []
    _logged_checks = set()
    now = datetime.now(UTC).isoformat()
    _cycle_started = _progress_at = _stage_started = time.monotonic()
    _cycle = dict(
        started_utc=now,
        progress_utc=now,
        stage="starting",
        in_progress=True,
        stages=[],
        checkpoints=0,
        omitted_checks=0,
    )


@synchronized
def record_check(stage, error, *, waiting=False):
    """Retain the original sanitized failure before aggregate wrapping."""
    detail = dict(failure_detail(error), stage=stage, waiting=waiting)
    if len(_checks) < 100:
        _checks.append(detail)
    elif _cycle:
        _cycle["omitted_checks"] += 1
    if _cycle:
        key = "waiting_checks" if waiting else "failed_checks"
        _cycle[key] = _cycle.get(key, 0) + 1
    if not waiting and detail["fingerprint"] not in _logged_checks and len(_logged_checks) < 100:
        # Discovery failures may have no incident. Existing logs preserve their
        # cause across cycles and process restarts without granting authority.
        logger.warning("recovery_check_failed diagnostic=%s", detail)
        _logged_checks.add(detail["fingerprint"])
    return detail


def _stage_end(now):
    if _cycle and _stage_started is not None:
        stages = _cycle.setdefault("stages", [])
        if len(stages) < 100:
            stages.append(
                dict(stage=_cycle["stage"], elapsed_seconds=max(0.0, now - _stage_started))
            )
        else:
            _cycle["omitted_stages"] = _cycle.get("omitted_stages", 0) + 1


@synchronized
def record_progress(stage):
    """Only real checkpoints advance progress; never call this from a timer."""
    global _cycle, _progress_at, _stage_started
    if _cycle and _cycle["in_progress"]:
        now = time.monotonic()
        if stage != _cycle["stage"]:
            _stage_end(now)
            _stage_started = now
        _progress_at = now
        _cycle.update(
            progress_utc=datetime.now(UTC).isoformat(),
            stage=stage,
            checkpoints=_cycle.get("checkpoints", 0) + 1,
        )


def _finish_cycle(outcome):
    global _cycle, _last_completed_cycle, _last_failed_cycle
    if _cycle:
        now = time.monotonic()
        if _cycle.get("in_progress"):
            _stage_end(now)
        _cycle = dict(
            _cycle,
            finished_utc=datetime.now(UTC).isoformat(),
            in_progress=False,
            outcome=outcome,
            checks=deepcopy(_checks),
            elapsed_seconds=max(0.0, now - _cycle_started) if _cycle_started is not None else None,
        )
        _last_completed_cycle = deepcopy(_cycle)
        if outcome == "failed":
            _last_failed_cycle = dict(
                deepcopy(_cycle),
                failure=deepcopy(_failure_detail),
                recovered_utc=None,
                original_history_failure=(
                    deepcopy(_history.get("last_failure")) if _history else None
                ),
            )
        logger.info(
            "recovery_cycle_completed outcome=%s elapsed_seconds=%s checkpoints=%s failed_checks=%s waiting_checks=%s",
            outcome,
            _cycle["elapsed_seconds"],
            _cycle.get("checkpoints", 0),
            _cycle.get("failed_checks", 0),
            _cycle.get("waiting_checks", 0),
        )


@synchronized
def begin_notifications():
    global _notifications_started
    _notifications_started = time.monotonic()


@synchronized
def record_history(coverage):
    global _history
    _history = deepcopy(coverage)


@synchronized
def outage_notification_due():
    """Degrade immediately; coalesce a single transient observation failure."""
    if not _failure:
        return False
    details = [item for item in _checks if not item.get("waiting")] or [_failure_detail]
    transient = all(
        item
        and (
            item["error_type"] in {"TimeoutError", "CoordinationLockRefused"}
            or (item.get("sql_numbers") and set(item["sql_numbers"]) <= {1205, 1222})
        )
        for item in details
    )
    return not transient or _failure_streak >= 2


def failure_detail(error):
    """Retain call sites, never exception text, locals or private payloads."""
    from services.export_failure_diagnostics import failure_record

    facts = failure_record(error)
    detail = {
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
    detail["fingerprint"] = hashlib.sha256(
        json.dumps(
            {k: v for k, v in detail.items() if k != "observed_utc"}, sort_keys=True
        ).encode()
    ).hexdigest()
    return detail


@synchronized
def record_notifications(error=None, *, pending=False):
    global _notification_failure
    if _notifications_started is not None and _last_completed_cycle:
        _last_completed_cycle["notification_seconds"] = max(
            0.0, time.monotonic() - _notifications_started
        )
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


@synchronized
def record_success():
    global _last_success, _failure, _failure_detail, _failure_streak, _episode_fingerprint
    _last_success, _failure = datetime.now(UTC), None
    _failure_detail = None
    _failure_streak = 0
    _episode_fingerprint = None
    _finish_cycle("completed")
    if _last_failed_cycle and _last_failed_cycle.get("recovered_utc") is None:
        _last_failed_cycle["recovered_utc"] = _last_success.isoformat()


@synchronized
def record_failure(error):
    global _failure, _failure_detail, _failure_streak, _episode_fingerprint
    _failure = type(error).__name__
    _failure_detail = failure_detail(error)
    causes = [item for item in _checks if not item.get("waiting")]
    if not causes and _history and _history.get("unconfirmed_failure"):
        causes = [_history["last_failure"]] if _history.get("last_failure") else []
    signature = (
        tuple(sorted((item.get("stage"), item["fingerprint"]) for item in causes))
        or _failure_detail["fingerprint"]
    )
    _failure_streak = _failure_streak + 1 if signature == _episode_fingerprint else 1
    _episode_fingerprint = signature
    _finish_cycle("failed")


def _stalled(now):
    return bool(
        _cycle
        and _cycle.get("in_progress")
        and (
            (_progress_at is not None and now - _progress_at > STALL_SECONDS)
            or (_cycle_started is not None and now - _cycle_started > CYCLE_SECONDS)
        )
    )


def _checks_failed():
    return bool(_failure or (_cycle and _cycle.get("failed_checks")))


def _fresh():
    return (
        _last_success is not None
        and (datetime.now(UTC) - _last_success).total_seconds() <= FRESH_SECONDS
    )


def _advancing(now):
    return bool(
        _cycle and _cycle.get("in_progress") and _progress_at is not None and not _stalled(now)
    )


@synchronized
def observation():
    """Detached coherent monitor snapshot; no SQL, provider or cache work."""
    now = time.monotonic()
    state = "starting" if _last_success is None else "idle"
    if _cycle and _cycle.get("in_progress"):
        state = (
            "stalled"
            if _stalled(now)
            else "waiting" if _cycle.get("waiting_checks") else "progressing"
        )
    healthy, text = status()
    return deepcopy(
        dict(
            healthy=healthy,
            status=text,
            last_success_utc=_last_success.isoformat() if _last_success else None,
            check_failure=_failure_detail,
            notification_failure=_notification_failure,
            cycle=_cycle,
            checks=_checks,
            observer_state=state,
            check_state=(
                "failed"
                if _checks_failed()
                else "fresh" if _fresh() else "unestablished" if _last_success is None else "stale"
            ),
            completed_check_age_seconds=(
                max(0.0, (datetime.now(UTC) - _last_success).total_seconds())
                if _last_success
                else None
            ),
            last_completed_cycle=_last_completed_cycle,
            last_failed_cycle=_last_failed_cycle,
            history=_history,
            no_progress_seconds=(
                max(0.0, now - _progress_at)
                if _cycle and _cycle.get("in_progress") and _progress_at is not None
                else None
            ),
            freshness_seconds=FRESH_SECONDS,
            stall_seconds=STALL_SECONDS,
            cycle_limit_seconds=CYCLE_SECONDS,
        )
    )


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

    snapshot = observation()
    return {
        **snapshot,
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


@synchronized
def status():
    healthy = (
        _last_success is not None
        and not _checks_failed()
        and (_fresh() or _advancing(time.monotonic()))
    )
    text = (
        "Monitoring active"
        if healthy
        else (
            "Monitoring check failed; recovery status is not established"
            if _checks_failed()
            else "Monitoring results are stale or not yet established"
        )
    )
    if healthy and not _fresh():
        text = "Monitoring progressing; current checks are still running, previous completed results are older"
    if _stalled(time.monotonic()):
        healthy = False
        text = "Monitoring stalled; original work remains owned and requires investigation"
    if _last_success:
        text += f". Last successful check: {_last_success.isoformat()}"
    if _cycle and _cycle.get("waiting_checks"):
        text += ". Existing SQL work or publication verification is still running; its recovery checks will retry automatically. No completion or release is inferred"
    if not healthy and _cycle and _cycle["in_progress"]:
        text += ". A monitoring cycle is in progress; the downloadable report identifies its latest checkpoint"
    if _notification_failure:
        text += ". Incident notifications need attention; open the recovery centre and download its report"
    return healthy, text
