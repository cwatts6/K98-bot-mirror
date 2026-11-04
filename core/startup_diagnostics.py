"""Bounded startup observations, never receipts or authority to repeat work."""

import asyncio
from copy import deepcopy
from datetime import UTC, datetime

from core.operation_evidence import emit, optional, result_facts, scope, typed_result
from services.startup_outcome_projection import project

_steps = {}


def report():
    return deepcopy(list(_steps.values()))


def _record(label, state, seconds, *, error=None, **facts):
    if label not in _steps and len(_steps) >= 64:
        return
    row = dict(
        **facts,
        step=label,
        state=state,
        observed_utc=datetime.now(UTC).isoformat(),
        deadline_seconds=seconds,
        verification="Feature receipts and recovery checks establish the business outcome; do not repeat work from this observation alone.",
    )
    if error is not None:
        from services.recovery_health import failure_detail

        row["diagnostic"] = optional(failure_detail, error) or {"status": "unavailable"}
    _steps[label] = row


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
    """Observe once and retain results; deadline, settlement and verification differ."""
    from services.cache_admission_diagnostics import startup_context

    with scope() as observation:
        return await _run(
            coro, seconds, label, cancel_on_deadline, completion_check, observation, startup_context
        )


async def _run(
    coro, seconds, label, cancel_on_deadline, completion_check, observation, startup_context
):
    result = None
    returned = False
    verified = None
    check_error = None

    def record(state, **facts):
        outcome = optional(
            project,
            label,
            verified,
            checked=completion_check is not None,
            error=type(check_error).__name__ if check_error is not None else False,
        ) or {"feature_outcome": "unknown"}
        optional(
            _record,
            label,
            state,
            seconds,
            reference=observation.reference,
            worker_result=dict(observation.worker_result),
            parent_return=optional(typed_result, result) if returned else None,
            feature=outcome,
            **facts,
        )
        emit(label, state, error=facts.get("error"), facts=outcome if returned else None)

    async def observed():
        nonlocal result, returned, verified, check_error
        with startup_context(label):
            result = await coro
            returned = True
            emit(
                label,
                "result_returned",
                facts={
                    **(optional(result_facts, result) or {}),
                    **(optional(typed_result, result) or {}),
                },
            )
            if completion_check is not None:
                try:
                    verified = await completion_check(result)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    check_error = exc

    task = asyncio.ensure_future(observed())
    record("running", observer="pending", physical="pending", verification_state="pending")
    try:
        done, _ = await asyncio.wait({task}, timeout=seconds)
        if not done:
            record(
                "deadline_elapsed_draining" if cancel_on_deadline else "deadline_elapsed_pending",
                observer="deadline_elapsed",
                physical="pending",
            )
            if cancel_on_deadline:
                task.cancel()
            await asyncio.shield(asyncio.gather(task, return_exceptions=True))
            if task.cancelled():
                record(
                    "deadline_elapsed_outcome_unconfirmed",
                    observer="deadline_elapsed",
                    physical="settled",
                    returned=returned,
                    result=optional(result_facts, result),
                )
                return None
        task.result()  # Worker exceptions are separate from verification exceptions.
        state = "completed" if done else "completed_after_deadline"
        if check_error is not None:
            from services.configuration_attempt_recovery import ProcConfigImportFailed

            state = (
                "failed"
                if isinstance(check_error, ProcConfigImportFailed)
                else "verification_unavailable"
            )
        record(
            state,
            observer="observed",
            physical="settled",
            returned=True,
            result=optional(result_facts, result),
            completion=verified,
            verification_state=(
                "unavailable" if check_error else "checked" if completion_check else "not_requested"
            ),
            error=check_error,
        )
        return result
    except asyncio.CancelledError:
        await _drain_cancel(task)
        record(
            "cancelled_outcome_unconfirmed",
            observer="cancelled",
            physical="settled",
            returned=returned,
            result=optional(result_facts, result),
        )
        raise
    except Exception as exc:
        record("failed", observer="observed", physical="settled", returned=returned, error=exc)
        return None
