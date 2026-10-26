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
    }.get(label, "startup_other")
    token = _context.set({"operation": operation, "origin": "startup"})
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
