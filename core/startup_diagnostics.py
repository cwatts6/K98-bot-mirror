"""Bounded startup observations, never receipts or authority to repeat work."""

import asyncio
from copy import deepcopy
from datetime import UTC, datetime
import logging

logger = logging.getLogger(__name__)
_steps = {}


def report():
    return deepcopy(list(_steps.values()))


def _record(label, state, seconds, *, error=None):
    if label not in _steps and len(_steps) >= 64:
        return
    _steps[label] = dict(
        step=label,
        state=state,
        observed_utc=datetime.now(UTC).isoformat(),
        deadline_seconds=seconds,
        verification="Feature receipts and recovery checks establish the business outcome; do not repeat work from this observation alone.",
    )
    if error is not None:
        from services.recovery_health import failure_detail

        _steps[label]["diagnostic"] = failure_detail(error)


async def _drain_cancel(task):
    task.cancel()
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            continue
        except Exception:
            break
    if not task.cancelled():
        task.exception()


async def run(coro, seconds, label, *, cancel_on_deadline=True, completion_check=None):
    """Keep cancellation/drain semantics; distinguish a deadline from a failure.

    The default cancels at the deadline. An explicitly observed long-running task
    instead remains pending until it returns; shutdown still cancels and drains it.
    A supplied completion check runs in that same tracked task before success.
    The coroutine is awaited after cancellation and is never replayed. Executor
    callers must track their actual workers: cancelling a proxy future alone
    does not stop its thread. Cancelled business outcomes remain unproven.
    """

    async def observed():
        result = await coro
        summary = await completion_check(result) if completion_check is not None else None
        return result, summary

    task = asyncio.ensure_future(observed())
    _record(label, "running", seconds)
    try:
        done, _ = await asyncio.wait({task}, timeout=seconds)
        if not done:
            _record(
                label,
                "deadline_elapsed_draining" if cancel_on_deadline else "deadline_elapsed_pending",
                seconds,
            )
            logger.warning(
                "[BOOT] %s exceeded %.1fs; waiting for the original task. No retry requested.",
                label,
                seconds,
            )
            if cancel_on_deadline:
                task.cancel()
            # Shield from outer shutdown cancellation so the explicit drain below
            # remains the only cancellation owner, including repeated cancellation.
            await asyncio.shield(asyncio.gather(task, return_exceptions=True))
            if task.cancelled():
                _record(label, "deadline_elapsed_outcome_unconfirmed", seconds)
                logger.warning(
                    "[BOOT] %s startup coroutine cancelled; underlying worker outcome remains unconfirmed. Verify the feature receipt. The deadline does not establish failure or schedule a retry.",
                    label,
                )
                return None
        result, summary = task.result()
        state = "completed" if done else "completed_after_deadline"
        _record(label, state, seconds)
        if summary is not None and label in _steps:
            _steps[label]["completion"] = summary
        logger.info("[BOOT] %s state=%s", label, state)
        return result
    except asyncio.CancelledError:
        await _drain_cancel(task)
        _record(label, "cancelled_outcome_unconfirmed", seconds)
        raise
    except Exception as exc:
        _record(label, "failed", seconds, error=exc)
        logger.warning(
            "[BOOT] %s failed error_type=%s; inspect the private recovery report.",
            label,
            type(exc).__name__,
        )
        return None
