"""Correlated, observational timing only; never admission, timeout or retry policy.

Stages are inclusive wall times and can overlap. Context propagates through owned
tasks and asyncio.to_thread. No interaction IDs, payloads or exception text are logged.
"""

from contextlib import contextmanager
from contextvars import ContextVar
import logging
from time import perf_counter
from uuid import uuid4

logger = logging.getLogger(__name__)
_reference = ContextVar("operation_timing_reference", default=None)


@contextmanager
def timing_scope():
    if _reference.get() is not None:
        yield
        return
    token = _reference.set(uuid4().hex)
    try:
        yield
    finally:
        _reference.reset(token)


def record_timing(stage, elapsed_seconds, disposition="completed"):
    reference = _reference.get()
    if reference is not None:
        logger.info(
            "operation_stage reference=%s stage=%s elapsed_ms=%.3f disposition=%s",
            reference,
            stage,
            elapsed_seconds * 1000,
            disposition,
            extra={
                "operation_stage": {
                    "reference": reference,
                    "stage": stage,
                    "elapsed_ms": elapsed_seconds * 1000,
                    "disposition": disposition,
                }
            },
        )


@contextmanager
def timed_stage(stage):
    started = perf_counter()
    disposition = "completed"
    try:
        yield
    except BaseException:
        disposition = "interrupted"
        raise
    finally:
        record_timing(stage, perf_counter() - started, disposition)
