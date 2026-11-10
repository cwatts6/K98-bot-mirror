"""Bounded startup observations, never receipts or authority to repeat work."""

import asyncio
from copy import deepcopy
from datetime import UTC, datetime

from core.operation_evidence import emit, optional, result_facts, scope, typed_result
from services.health_observation import Observation
from services.startup_outcome_projection import project

_steps = {}
_health = ()
_HEALTH_STEPS = (
    "warm_profile_cache",
    "warm_name_cache",
    "build_player_stats_cache",
    "proc_config_import",
)


def health_snapshot():
    return _health


def report():
    return deepcopy(list(_steps.values()))


def _record(label, state, seconds, *, error=None, **facts):
    global _health
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
    # Fixed labels/fields only. Arbitrary diagnostic payloads never enter a card.
    if label in _HEALTH_STEPS:
        try:
            feature = row.get("feature", {}).get("feature_outcome")
            feature = (
                feature
                if feature in {"success", "failure", "succeeded", "failed", "partial", "unknown"}
                else "unknown"
            )
            feature = {"succeeded": "success", "failed": "failure"}.get(feature, feature)
            item = Observation(
                "startup",
                label,
                row["observed_utc"],
                (
                    "in_progress"
                    if row.get("physical") == "pending"
                    or state in {"running", "deadline_elapsed_pending", "deadline_elapsed_draining"}
                    else "settled"
                ),
                feature,
                "startup_activity",
                reference=(
                    row.get("reference")
                    if type(row.get("reference")) is str and len(row["reference"]) <= 64
                    else None
                ),
            )
            _health = tuple(r for r in _health if r.scope_label != label) + (item,)
        except Exception:
            pass


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

    with scope(origin="startup", actor="system") as observation:
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
    check_finished = False

    def record(state, **facts):
        outcome = optional(
            project,
            label,
            verified,
            checked=completion_check is not None,
            pending=completion_check is not None and not check_finished,
            not_reached=completion_check is not None
            and not check_finished
            and state
            in {"failed", "cancelled_outcome_unconfirmed", "deadline_elapsed_outcome_unconfirmed"},
            error=type(check_error).__name__ if check_error is not None else False,
        ) or {
            "feature_outcome": "unknown",
            "verification_reason": "projection_unavailable",
            "verification_source": "unavailable",
        }
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
        emit(label, state, error=facts.get("error"), facts=outcome)

    async def observed():
        nonlocal result, returned, verified, check_error, check_finished
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
                except asyncio.CancelledError as exc:
                    check_error = exc
                    raise
                except Exception as exc:
                    check_error = exc
                finally:
                    check_finished = True

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
