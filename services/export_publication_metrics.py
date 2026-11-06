"""Bounded diagnostic aggregates for one synchronous publication probe.

These measurements are never receipts, retry inputs, or authorization evidence.
Nested intervals overlap: request_budget includes budget_sql and budget_wait.
Provider-child time includes IPC and validation in the child, not just HTTP.
"""

from contextlib import contextmanager
from contextvars import ContextVar
import sys
from time import monotonic

_active = ContextVar("publication_metrics", default=None)
_STEPS = frozenset(
    {
        "probe_admission",
        "probe_observation",
        "probe_closure",
        "request_lookup",
        "request_payload",
        "request_prepared",
        "request_budget",
        "request_guard",
        "request_dispatch",
        "provider_child",
        "response_validation",
        "request_result",
        "budget_complete",
        "budget_sql",
        "budget_wait",
        "budget_feedback",
    }
)


def _clock():
    try:
        return monotonic()
    except Exception:
        return None  # Unavailable diagnostics cannot prevent or repeat work.


@contextmanager
def measure_publication_step(name):
    values = _active.get()
    if values is None or name not in _STEPS:
        yield
        return
    started = _clock()
    completed = False
    try:
        yield
        completed = True
    finally:
        ended = _clock()
        if started is not None and ended is not None:
            try:
                row = values.setdefault(name, [0, 0, 0])
                row[0] += 1
                row[1] += int(not completed)
                row[2] += max(0, round((ended - started) * 1000))
            except Exception:
                pass  # Diagnostics have no effect on the underlying outcome.


@contextmanager
def publication_details(logger):
    """Record at most one fixed-shape line per known step, including on failure."""
    values = {}
    token = _active.set(values)
    try:
        yield
    finally:
        _active.reset(token)
        for name, (count, failed, duration) in sorted(values.items()):
            try:
                logger.info(
                    "publication_verification_detail step=%s count=%d failed=%d duration_ms=%d",
                    name,
                    count,
                    failed,
                    duration,
                )
            except Exception:
                pass  # Logging failure must not turn success into uncertain work.


@contextmanager
def measured_probe(streams, snapshot):
    """Measure the existing context manager without retrying enter or exit."""
    with measure_publication_step("probe_admission"):
        manager = streams.probe(snapshot)
        stream = manager.__enter__()
    try:
        with measure_publication_step("probe_observation"):
            yield stream
    except BaseException:
        with measure_publication_step("probe_closure"):
            suppressed = manager.__exit__(*sys.exc_info())
        if not suppressed:
            raise
    else:
        with measure_publication_step("probe_closure"):
            manager.__exit__(None, None, None)
