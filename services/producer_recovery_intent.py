"""Typed durable producer inputs, independent of a caller's stack or thread."""

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import json
from uuid import uuid4

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import identity
from services.fallback_import_service import is_completed_filename

_intent = ContextVar("producer_recovery_intent", default=None)
METADATA = frozenset(
    (
        "source_type",
        "source_filename",
        "score_header",
        "columns_present",
        "rows_in_source",
        "rows_written",
    )
)


def stats_inputs(rank, seed, completed_filename, timeout_seconds, metadata):
    value = dict(
        rank=rank,
        seed=seed,
        completed_filename=completed_filename,
        timeout_seconds=timeout_seconds,
        metadata={k: v for k, v in (metadata or {}).items() if k in METADATA},
    )
    validate_inputs(value)
    return json.loads(json.dumps(value, allow_nan=False))


def validate_inputs(value):
    if (
        not isinstance(value, dict)
        or set(value) != {"rank", "seed", "completed_filename", "timeout_seconds", "metadata"}
        or not is_completed_filename(value["completed_filename"])
        or type(value["timeout_seconds"]) is not int
        or not 1 <= value["timeout_seconds"] <= 3600
        or any(type(value[k]) not in (str, int, type(None)) for k in ("rank", "seed"))
        or any(len(str(value[k])) > 128 for k in ("rank", "seed"))
        or not isinstance(value["metadata"], dict)
        or not set(value["metadata"]) <= METADATA
        or len(json.dumps(value, allow_nan=False).encode()) > 32768
    ):
        raise SourceConflict("Exact bounded stats import inputs required for recovery.")


def current_intent():
    return _intent.get()


def player_report_intent(function):
    """Identify the atomic report producer before its writer request is saved."""

    return atomic_producer_intent("player_stats_report")(function)


def player_cache_intent(function):
    """Record cache-only versus pipeline output intent before writer admission."""
    return atomic_producer_intent("player_stats_report", cache_refresh=True)(function)


def configuration_import_intent(function):
    """Record standalone SQL refresh versus collected pipeline output before admission."""
    return atomic_producer_intent("configuration_import", configuration_refresh=True)(function)


def atomic_producer_intent(kind, *, cache_refresh=False, configuration_refresh=False):
    if kind not in {"player_stats_report", "configuration_import"}:
        raise ValueError("Unsupported atomic producer.")

    def decorate(function):
        @wraps(function)
        def run(*args, **kwargs):
            current = _intent.get()
            disposition = None
            if cache_refresh or configuration_refresh:
                from services.legacy_export_snapshot_service import producer_captures_requested

                disposition = (
                    "pipeline_export_v1"
                    if producer_captures_requested()
                    else ("configuration_only_v1" if configuration_refresh else "cache_only_v1")
                )
            if current is not None:
                if current.get("kind") != kind or current.get("atomic_checkpoint") != 1:
                    raise SourceConflict("Execution cannot inherit a different producer intent.")
                # Guided continuations already have a durable approved request.
                # Do not reinterpret its missing disposition at execution time.
                if configuration_refresh and "export_disposition" not in current:
                    return function(*args, **kwargs)
                if disposition and current.get("export_disposition") != disposition:
                    raise SourceConflict("Execution cannot change its original export intent.")
                return function(*args, **kwargs)
            value = dict(kind=kind, atomic_checkpoint=1, operation=str(uuid4()))
            if disposition:
                value["export_disposition"] = disposition
            token = _intent.set(value)
            try:
                return function(*args, **kwargs)
            finally:
                _intent.reset(token)

        return run

    return decorate


@contextmanager
def report_retry_intent(action_id, parent):
    """A separately approved report refresh, never a replay of the failed import."""
    if _intent.get() is not None:
        raise SourceConflict("Report continuation requires its own producer context.")
    value = dict(
        kind="player_stats_report",
        atomic_checkpoint=1,
        operation=identity(action_id),
        parent=identity(parent),
        export_disposition="cache_only_v1",
    )
    token = _intent.set(value)
    try:
        yield value
    finally:
        _intent.reset(token)


@contextmanager
def configuration_retry_intent(action_id, parent):
    if _intent.get() is not None:
        raise SourceConflict("Configuration continuation requires its own producer context.")
    value = dict(
        kind="configuration_import",
        atomic_checkpoint=1,
        operation=identity(action_id),
        parent=identity(parent),
    )
    token = _intent.set(value)
    try:
        yield value
    finally:
        _intent.reset(token)


@contextmanager
def stats_intent(inputs, *, action_id=None, parent=None, registration_recovery=None):
    validate_inputs(inputs)
    current = _intent.get()
    if current is not None and action_id is None:
        if current["kind"] != "stats_import" or current["inputs"] != inputs:
            raise SourceConflict("Inherited producer recovery differs from its saved inputs.")
        yield current
        return
    value = dict(kind="stats_import", inputs=inputs, operation=identity(action_id or str(uuid4())))
    if parent is not None:
        value["parent"] = identity(parent)
    if registration_recovery is not None:
        if parent is None or action_id is None:
            raise SourceConflict("Registration recovery requires a confirmed parent action.")
        value["registration_recovery"] = dict(registration_recovery)
    token = _intent.set(value)
    try:
        yield value
    finally:
        _intent.reset(token)
