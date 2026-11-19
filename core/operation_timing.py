"""Correlated, observational timing only; never admission, timeout or retry policy.

Stages are inclusive wall times and can overlap. Context propagates through owned
tasks and asyncio.to_thread. No interaction IDs, payloads or exception text are logged.
"""

from contextlib import contextmanager
from time import perf_counter

from core.operation_evidence import emit, optional, scope


@contextmanager
def timing_scope():
    with scope():
        yield


def record_timing(stage, elapsed_seconds, disposition="completed"):
    if type(elapsed_seconds) in (int, float):
        emit(stage, disposition, elapsed_ms=elapsed_seconds * 1000)


def clock():
    return optional(perf_counter)


def elapsed(stage, started, disposition="completed"):
    ended = clock()
    if type(started) in (int, float) and type(ended) in (int, float):
        optional(record_timing, stage, ended - started, disposition)


@contextmanager
def timed_stage(stage):
    started = clock()
    disposition = "completed"
    try:
        yield
    except BaseException:
        disposition = "interrupted"
        raise
    finally:
        elapsed(stage, started, disposition)
