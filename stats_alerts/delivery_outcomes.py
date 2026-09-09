"""In-memory publication evidence. These records never grant dispatch ownership."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from functools import wraps
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeliveryAttempt:
    component: str
    operation: str = "send"
    outcome: str = "unknown"
    reason: str = "no_receipt"
    requested_channel_id: int | None = None
    channel_id: int | None = None
    guild_id: int | None = None
    message_id: int | None = None
    entered: bool = False
    acknowledged: bool = False
    data: str = "unverified"
    includes_summary: bool | None = None
    claim: str = "not_attempted"
    persistence: str = "not_applicable"
    finalization: str | None = None


@dataclass(frozen=True)
class DeliveryResult:
    attempts: tuple[DeliveryAttempt, ...]
    correlation_id: str
    route: str
    is_test: bool = False


def positive_id(value):
    return value if type(value) is int and value > 0 else None


def normalize_result(value, component, *, channel_id=None, is_test=False):
    if isinstance(value, DeliveryResult):
        return value
    return DeliveryResult(
        (DeliveryAttempt(component, requested_channel_id=channel_id, reason="legacy_unverified"),),
        uuid4().hex,
        component,
        is_test,
    )


def _log_delivery(result, *, caller, source_message_id=None):
    """Log only primitive evidence; no payloads, exception text or user filenames."""
    result = normalize_result(result, "legacy")
    for item in result.attempts:
        logger.info(
            "[STATS DELIVERY] correlation=%s caller=%s source_message=%s route=%s "
            "test=%s component=%s operation=%s outcome=%s reason=%s requested_channel=%s "
            "channel=%s guild=%s message=%s entered=%s acknowledged=%s data=%s "
            "includes_summary=%s claim=%s persistence=%s finalization=%s",
            result.correlation_id,
            caller,
            source_message_id,
            result.route,
            result.is_test,
            item.component,
            item.operation,
            item.outcome,
            item.reason,
            item.requested_channel_id,
            item.channel_id,
            item.guild_id,
            item.message_id,
            item.entered,
            item.acknowledged,
            item.data,
            item.includes_summary,
            item.claim,
            item.persistence,
            item.finalization,
        )


def log_delivery(result, *, caller, source_message_id=None):
    """Reporting must not change import completion or erase a Discord receipt."""
    try:
        _log_delivery(result, caller=caller, source_message_id=source_message_id)
    except Exception:
        # A broken logging handler cannot safely report its own failure here.
        return


class DeliveryTracker:
    """Explicitly passed observer; no global context, I/O, admission or retry logic."""

    def __init__(self, component, *, is_test=False):
        self.route = component
        self.is_test = is_test
        self.correlation_id = uuid4().hex
        self.attempts = [DeliveryAttempt(component)]

    def update(self, **changes):
        self.attempts[-1] = replace(self.attempts[-1], **changes)

    def begin(self, component, *, operation="send", channel_id=None):
        item = DeliveryAttempt(component, operation=operation, requested_channel_id=channel_id)
        if len(self.attempts) == 1 and self.attempts[0] == DeliveryAttempt(self.route):
            self.attempts[0] = item
        else:
            self.attempts.append(item)

    def enter(self, channel_id=None, *, operation="send", message_id=None):
        self.update(
            entered=True,
            operation=operation,
            requested_channel_id=positive_id(channel_id),
            message_id=positive_id(message_id),
        )

    def receipt(self, message, channel=None, *, operation="send"):
        message_id = positive_id(getattr(message, "id", None))
        actual = getattr(message, "channel", None)
        # An edit targets a fetched message, whose known channel is also usable.
        if actual is None and operation == "edit":
            actual = channel
        self.update(
            operation=operation,
            acknowledged=message_id is not None,
            outcome=("edited" if operation == "edit" else "sent") if message_id else "unknown",
            reason="acknowledged" if message_id else "missing_receipt",
            message_id=message_id,
            channel_id=positive_id(getattr(actual, "id", None)),
            guild_id=positive_id(getattr(getattr(actual, "guild", None), "id", None)),
        )

    def skip(self, reason):
        self.update(outcome="skipped", reason=reason)

    def failure(self, exc):
        item = self.attempts[-1]
        if item.acknowledged or item.outcome in {"skipped", "failed"}:
            return
        self.update(outcome="unknown" if item.entered else "failed", reason=type(exc).__name__)

    def observe_commit(self, attempt):
        persistence = attempt.persistence_outcome
        if self.attempts[-1].acknowledged and persistence == "not_applicable":
            persistence = "unconfirmed"
        self.update(persistence=persistence, finalization=attempt.finalization_error)

    def result(self):
        return DeliveryResult(tuple(self.attempts), self.correlation_id, self.route, self.is_test)


def delivery_outcome(component):
    """Opt-in results around the original adapter, outside its reservation lifetime.

    Internal observers are shared explicitly and do not catch exceptions. This leaves
    reservation finalization and legacy callers' exception behavior intact.
    """

    def decorate(func):
        @wraps(func)
        async def wrapped(*args, return_outcome=False, **kwargs):
            if return_outcome and kwargs.get("return_receipt"):
                raise ValueError("Choose return_outcome or return_receipt")
            if not return_outcome:
                return await func(*args, **kwargs)
            if kwargs.get("_delivery") is not None:
                raise ValueError("Outcome observer is already supplied")
            tracker = DeliveryTracker(component, is_test=kwargs.get("is_test", False))
            try:
                await func(*args, **kwargs, _delivery=tracker)
            except asyncio.CancelledError as exc:
                tracker.failure(exc)
                raise
            except Exception as exc:
                tracker.failure(exc)
            finally:
                log_delivery(tracker.result(), caller=func.__name__)
            return tracker.result()

        return wrapped

    return decorate
