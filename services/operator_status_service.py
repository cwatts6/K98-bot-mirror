"""Passive bounded health projection plus explicitly active SQL compatibility API."""

from datetime import UTC, datetime
import sys
import time

from services.gsheets_health_service import HealthProbe
from services.health_observation import PROCESS_ID, Observation, age_seconds

_probe = HealthProbe(label="SQL")


async def check_sql(*, timeout=5.0):
    """Active check. Never called by health presentation or report collection."""
    from services.legacy_export_snapshot_service import drain_thread
    from services.operator_status_dal import check_connection

    return await _probe.observe(
        lambda: drain_thread(check_connection), timeout=timeout, scope=_sql_scope()
    )


def _loaded(module, method):
    source = sys.modules.get(module)
    if source is None:
        return None
    return getattr(source, method)()


def snapshot(now_utc=None, now_monotonic=None):
    """Read published records only. Missing sources never trigger initialization."""
    now = now_utc if now_utc is not None else datetime.now(UTC)
    mono = now_monotonic if now_monotonic is not None else time.monotonic()
    components = {}
    for key, module, method in (
        ("sql", __name__, "sql_snapshot"),
        ("sheets", "services.gsheets_health_service", "health_snapshot"),
        ("profiles", "profile_cache", "health_snapshot"),
        ("recovery", "services.recovery_health", "health_snapshot"),
        ("events", "services.event_delivery_service", "health_snapshot"),
        ("startup", "core.startup_diagnostics", "health_snapshot"),
        ("personal_stats", "player_self_service.stats_runtime", "snapshot"),
    ):
        try:
            value = _loaded(module, method)
            if key == "personal_stats" and type(value) is dict and value.get("observed"):
                uncertain = value.get("cleanup_uncertain") is True
                closed = value.get("admission_closed") is True
                busy = (
                    value.get("sql_owned", 0) >= 8
                    or value.get("render_owned", 0) >= 2
                    or value.get("observers", 0) >= 32
                )
                row = dict(
                    outcome="failure" if uncertain else "unknown",
                    reason=(
                        "stats_cleanup_uncertain"
                        if uncertain
                        else (
                            "stats_shutdown"
                            if closed
                            else "stats_busy" if busy else "stats_available"
                        )
                    ),
                    observed_utc=value.get("captured_utc"),
                    age_seconds=0,
                    sql_owned=value.get("sql_owned", 0),
                    render_owned=value.get("render_owned", 0),
                    observers=value.get("observers", 0),
                )
            elif key == "personal_stats" and type(value) is dict and value.get("observed") is False:
                row = Observation(key, "local evidence", reason="not_observed").project(now)
            elif key in {"sql", "sheets"} and type(value) is tuple and len(value) == 3:
                current, latest, failure = value
                row = current.project(now, now_monotonic=mono)
                row["last_completion"] = latest.project(now) if latest else None
                row["last_failure"] = failure.project(now) if failure else None
            elif key == "recovery" and type(value) is tuple:
                record, last_success, started, progress, failed, notifications = value
                row = record.project(now, freshness_seconds=90)
                age = age_seconds(last_success, now)
                advancing = (
                    type(started) in (int, float)
                    and type(progress) in (int, float)
                    and 0 <= started <= progress <= mono
                )
                stalled = advancing and (mono - progress > 300 or mono - started > 900)
                row.update(
                    last_success_utc=last_success,
                    completed_check_age_seconds=age,
                    reason=(
                        "monitor_stalled"
                        if stalled
                        else (
                            "monitor_failed"
                            if failed
                            else (
                                "monitor_progressing"
                                if advancing
                                else (
                                    "monitor_active"
                                    if age is not None and age <= 90
                                    else "monitor_unestablished"
                                )
                            )
                        )
                    ),
                    outcome=(
                        "failure"
                        if failed or stalled
                        else (
                            "success" if age is not None and (age <= 90 or advancing) else "unknown"
                        )
                    ),
                    notifications_need_attention=notifications,
                )
            elif key == "startup" and type(value) is tuple:
                row = Observation("startup", "historical activity").project(now)
                row["steps"] = [
                    item.project(now) for item in value[:4] if type(item) is Observation
                ]
            elif type(value) is Observation:
                row = value.project(now)
            else:
                row = Observation(key, "local evidence", reason="source_unavailable").project(now)
        except Exception:
            row = Observation(key, "local evidence", reason="source_unavailable").project(now)
        components[key] = row
    return dict(
        schema="health_observations_v1",
        process_id=PROCESS_ID,
        captured_utc=now.isoformat(),
        components=components,
    )


def sql_snapshot():
    if sys.modules.get("constants") is None:
        return (Observation("SQL", "configured check", reason="source_unavailable"), None, None)
    return _probe.snapshot(scope=_sql_scope())


def _sql_scope():
    config = sys.modules.get("constants")
    return ("SQL connectivity", getattr(config, "SERVER", None), getattr(config, "DATABASE", None))


def close_admission():
    _probe.close()


async def shutdown():
    await _probe.shutdown()
