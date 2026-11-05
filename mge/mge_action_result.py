"""Action evidence for adopted MGE services, separate from delivery and durable receipts.

DAL records only settled return evidence. The opt-in service scope follows nested
preparation/audit/secondary writers without changing shared database helpers.
Legacy result fields remain available; Discord adapters must use ``action``.
"""

from contextvars import ContextVar
from dataclasses import dataclass
from enum import StrEnum
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class ActionDisposition(StrEnum):
    COMPLETED = "completed"
    NOT_ENTERED = "not_entered"
    ROLLED_BACK = "rolled_back"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class WriteEvidence:
    stage: str
    state: str
    count: int = 0
    kind: str = "primary"


@dataclass(frozen=True, slots=True)
class ActionEvidence:
    disposition: ActionDisposition
    steps: tuple[WriteEvidence, ...] = ()

    @property
    def refresh_eligible(self):
        return self.disposition in {
            ActionDisposition.COMPLETED,
            ActionDisposition.PARTIAL,
            ActionDisposition.UNKNOWN,
        }

    @property
    def read_only_refresh(self):
        return self.disposition != ActionDisposition.COMPLETED

    @property
    def confirmed_count(self):
        return sum(
            step.count
            for step in self.steps
            if step.state == "confirmed" and step.kind == "primary"
        )

    def message(self, original):
        if self.disposition in {ActionDisposition.COMPLETED, ActionDisposition.NOT_ENTERED}:
            return original
        if self.disposition == ActionDisposition.ROLLED_BACK:
            return "The change was not saved."
        if self.disposition == ActionDisposition.PARTIAL:
            failed = {
                step.kind for step in self.steps if step.state not in {"confirmed", "not_required"}
            }
            detail = (
                " Its audit could not be confirmed."
                if failed == {"audit"}
                else " The action did not finish completely."
            )
            return (
                "Some changes were saved."
                + detail
                + " Please have leadership check before trying again."
            )
        return "The outcome could not be confirmed. Do not repeat the action until leadership has checked it."


@dataclass(slots=True)
class ActionFailure:
    success: bool
    message: str
    action: ActionEvidence
    award_id: int | None = None
    event_id: int | None = None
    signup_channel_id: int | None = None
    changed: bool = False


_steps: ContextVar[list[WriteEvidence] | None] = ContextVar("mge_action_steps", default=None)


def record_write(stage, state, *, count=0, kind="primary"):
    evidence = WriteEvidence(stage, state, max(0, count), kind)
    steps = _steps.get()
    if steps is not None:
        steps.append(evidence)
    return evidence


def record_affected(stage, affected, *, kind="primary"):
    integer = isinstance(affected, int) and not isinstance(affected, bool)
    state = (
        "confirmed"
        if integer and affected > 0
        else "not_entered" if integer and affected == 0 else "unknown"
    )
    return record_write(stage, state, count=affected if state == "confirmed" else 0, kind=kind)


def record_atomic(stage, result, *, audit=True):
    if isinstance(result, dict) and result.get("ok"):
        count = 0 if result.get("noop") else result.get("changed_count", 1)
        record_write(stage, "confirmed", count=count)
        if audit and count:
            record_write(
                stage + "_audit",
                "confirmed" if result.get("audit_confirmed") else "unknown",
                kind="audit",
            )
    elif isinstance(result, dict) and result.get("error") in {
        "event_mismatch",
        "not_waitlist",
        "roster_full",
        "multiple_rank_conflicts",
        "rank_collision_without_current_rank",
    }:
        record_write(stage, "not_entered")
    else:
        if isinstance(result, dict) and result.get("confirmed_count", 0):
            record_write(stage, "confirmed", count=result["confirmed_count"])
        record_write(stage, "unknown")


def classify(steps, *, success):
    steps = tuple(steps)
    confirmed = any(step.state == "confirmed" and step.count > 0 for step in steps)
    incomplete = any(step.state not in {"confirmed", "not_required"} for step in steps)
    if confirmed and (incomplete or not success):
        disposition = ActionDisposition.PARTIAL
    elif any(step.state in {"unknown", "partial"} for step in steps):
        disposition = ActionDisposition.UNKNOWN
    elif success and steps and not incomplete:
        disposition = ActionDisposition.COMPLETED
    elif not success and not confirmed:
        disposition = ActionDisposition.NOT_ENTERED
    else:
        # An uninstrumented legacy success is deliberately not commit evidence.
        disposition = ActionDisposition.UNKNOWN
    return ActionEvidence(disposition, steps)


def qualified_action(function):
    """Opt adopted services into explicit DAL evidence, including nested writers."""

    @wraps(function)
    def run(*args, **kwargs):
        steps = _steps.get()
        token = None
        if steps is None:
            steps = []
            token = _steps.set(steps)
        start = len(steps)
        try:
            try:
                result = function(*args, **kwargs)
            except Exception as exc:
                record_write(function.__name__, "unknown")
                logger.warning(
                    "mge_action_unconfirmed action=%s error_type=%s",
                    function.__name__,
                    type(exc).__name__,
                )
                evidence = classify(steps[start:], success=False)
                return ActionFailure(
                    False, evidence.message(""), evidence, event_id=kwargs.get("event_id")
                )
            result.action = classify(steps[start:], success=result.success)
            logger.info(
                "mge_action_result action=%s disposition=%s confirmed_count=%s",
                function.__name__,
                result.action.disposition,
                result.action.confirmed_count,
            )
            return result
        finally:
            if token is not None:
                _steps.reset(token)

    return run
