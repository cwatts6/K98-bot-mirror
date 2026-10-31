"""Bounded passive observations of existing admission calls, never lock authority."""

from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from threading import Lock
from uuid import uuid4

_context = ContextVar("cache_admission_context", default=None)
_records = deque(maxlen=32)
_lock = Lock()


@contextmanager
def startup_context(label):
    # Only known operation names enter shareable diagnostics.
    operation = {
        "build_player_stats_cache": "player_stats",
        "warm_profile_cache": "profile",
        "warm_name_cache": "name",
        "proc_config_import": "configuration_import",
    }.get(label, "startup_other")
    with observation_context(operation, "startup"):
        yield


@contextmanager
def observation_context(operation, origin):
    """Only code-owned labels; correlation is never SQL authority or identity."""
    if operation not in {
        "player_stats",
        "profile",
        "name",
        "startup_other",
        "configuration_import",
        "recovery",
        "health_probe",
    }:
        raise ValueError("Known admission observation required.")
    if origin not in {"startup", "monitor", "health"}:
        raise ValueError("Known admission origin required.")
    token = _context.set({"operation": operation, "origin": origin, "invocation_id": uuid4().hex})
    try:
        yield
    finally:
        _context.reset(token)


def identity():
    return {
        "correlation_id": uuid4().hex,
        "correlation_kind": "process_local",
        **(_context.get() or {"operation": "coordination", "origin": "unspecified"}),
        "sql_session_role": "requesting_session_not_blocker",
    }


def record(facts):
    with _lock:
        _records.append(dict(facts))


def report():
    with _lock:
        return deepcopy(list(_records))
