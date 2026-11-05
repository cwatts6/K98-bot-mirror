"""Gated, opt-in SQL observations for the five upload families.

PendingAudit is a local correlation, never a SQL ID. A lost start acknowledgement
suppresses dependent writes. This module never retries or queries to rebind.
"""

from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
import threading
from uuid import UUID, uuid4

from services.optional_upload_transport import OptionalWriter

DOMAINS = {
    "services.honor_import_audit_service": ("honor", "discord_upload_xlsx"),
    "services.prekvk_import_audit_service": ("prekvk", "discord_upload_xlsx"),
    "services.location_import_service": ("player_location", "discord_upload_csv"),
    "services.weekly_activity_import_audit_service": ("weekly_activity", "discord_upload_xlsx"),
    "services.kvk_all_import_audit_service": ("kvk_all", "discord_upload_xlsx"),
}
_scope_handles: ContextVar[list | None] = ContextVar("upload_audit_handles", default=None)


def begin_scope():
    return _scope_handles.set([])


def end_scope(token):
    handles = _scope_handles.get() or ()
    _scope_handles.reset(token)
    for writer, handle in handles:
        # Cancellation may end observation before a SQL terminal offer. Release
        # local context after queued work settles; never invent a SQL outcome.
        if not handle.terminal_requested.is_set():
            handle.terminal_requested.set()
            try:
                writer._project(handle.correlation_id, "failed", 1)
            except Exception:
                writer.dropped += 1


@dataclass(frozen=True, slots=True)
class PendingAudit:
    correlation_id: str
    terminal_requested: threading.Event = field(
        default_factory=threading.Event, compare=False, repr=False
    )


def _primitive(value, budget=None, depth=0):
    budget = [512] if budget is None else budget
    budget[0] -= 1
    if budget[0] < 0 or depth > 8:
        raise ValueError("Audit envelope complexity exceeded")
    if value is None or type(value) in (bool, int, float):
        return value
    if type(value) is str and len(value) <= 8192:
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if type(value) in (list, tuple) and len(value) <= 128:
        return [_primitive(v, budget, depth + 1) for v in value]
    if type(value) is dict and len(value) <= 128 and all(type(k) is str for k in value):
        return {k: _primitive(v, budget, depth + 1) for k, v in value.items()}
    raise ValueError("Audit envelope must contain bounded primitives")


class ImportAuditWriter(OptionalWriter):
    def __init__(self, connection_factory, *, dal=None):
        super().__init__(capacity=128, max_bytes=8192, name="upload-sql-audit")
        if dal is None:
            from stats.dal import import_audit_dal as dal
        self.dal = dal
        self.connection_factory = connection_factory
        self._contexts = {}
        self._contexts_lock = threading.Lock()
        self._cleanup_unconfirmed = None

    def start_batch(self, **values):
        handle = PendingAudit(str(uuid4()))
        if not self._contexts_lock.acquire(blocking=False):
            self.dropped += 1
            return None
        retired = []
        try:
            for identity, context in tuple(self._contexts.items()):
                if context["handle"].terminal_requested.is_set() and context["pending"] == 0:
                    self._contexts.pop(identity)
                    retired.append((identity, context["lost"]))
            if len(self._contexts) >= 256 or self._closed:
                self.dropped += 1
                return None
            self._contexts[handle.correlation_id] = {
                "binding": None,
                "sequence": 0,
                "lost": 0,
                "first_failure": None,
                "latest": "pending",
                "handle": handle,
                "pending": 0,
            }
        finally:
            self._contexts_lock.release()
            for identity, lost in retired:
                self._project(identity, "settled", lost)
        values["correlation_id"] = handle.correlation_id
        self.action(handle, "start", values)
        return handle

    def _project(self, identity, state, lost=0):
        try:
            from services.operation_diagnostics import offer_upload_observation

            offer_upload_observation(identity, state, lost)
            self.observe_settlement()
        except Exception:
            self.observation_unavailable = True

    def observe_settlement(self):
        # The transport calls this after updating its physical outcome counters.
        # Publish even when this is the last SQL operation before an idle period.
        from services.operation_diagnostics import upload_worker_summary

        upload_worker_summary(
            "sql",
            self.latest,
            error_type=self.first_failure,
            dropped=self.dropped,
            failures=self.failures,
        )

    def action(self, handle, action, values):
        if not isinstance(handle, PendingAudit) or action not in {
            "start",
            "phase",
            "complete",
            "fail",
        }:
            self.dropped += 1
            return False
        if action in {"complete", "fail"}:
            handle.terminal_requested.set()
        if not self._contexts_lock.acquire(blocking=False):
            self.dropped += 1
            self._project(handle.correlation_id, "failed", 1)
            return False
        try:
            context = self._contexts.get(handle.correlation_id)
            if context is None:
                self.dropped += 1
                return False
            context["sequence"] += 1
            try:
                payload = json.dumps(
                    {
                        "id": handle.correlation_id,
                        "action": action,
                        "sequence": context["sequence"],
                        "values": _primitive(values),
                    },
                    ensure_ascii=True,
                    allow_nan=False,
                    separators=(",", ":"),
                ).encode()
                offered = self.offer(payload)
            except Exception:
                self.dropped += 1
                offered = False
            if not offered:
                context["lost"] += 1
                context["first_failure"] = context["first_failure"] or "offer_unavailable"
                context["latest"] = "partial"
            else:
                context["latest"] = "pending"
                context["pending"] += 1
            lost = context["lost"]
            if handle.terminal_requested.is_set() and context["pending"] == 0:
                self._contexts.pop(handle.correlation_id, None)
        finally:
            self._contexts_lock.release()
        self._project(handle.correlation_id, "observed" if offered else "failed", lost)
        return offered

    def write(self, payload):
        envelope = json.loads(payload)
        identity, action = envelope["id"], envelope["action"]
        with self._contexts_lock:
            context = self._contexts[identity]
            binding = context["binding"]
        values = envelope["values"]
        details = values.pop("details", None)
        if details is not None:
            values["details_json"] = json.dumps(details, ensure_ascii=True, allow_nan=False)
        values["connection_factory"] = self.connection_factory
        try:
            if action == "start":
                result = self.dal.start_import_audit_batch(**values)
                if (
                    type(result.import_audit_batch_id) is not int
                    or result.import_audit_batch_id <= 0
                    or UUID(result.correlation_id) != UUID(identity)
                ):
                    raise ValueError("Audit start acknowledgement mismatch")
                with self._contexts_lock:
                    context["binding"] = result.import_audit_batch_id
            elif binding is None:
                raise ValueError("Audit start unacknowledged; dependent write suppressed")
            else:
                values["import_audit_batch_id"] = binding
                # Phase details are independent; cannot downgrade aggregate ingestion.
                if action == "phase":
                    values["set_batch_status"] = None
                function = {
                    "phase": self.dal.record_import_audit_phase,
                    "complete": self.dal.complete_import_audit_batch,
                    "fail": self.dal.fail_import_audit_batch,
                }[action]
                function(**values)
        except Exception as exc:
            from stats.dal.import_audit_dal import AuditConnectionCleanupUnconfirmed

            if isinstance(exc, AuditConnectionCleanupUnconfirmed):
                # Keep the failed-close session owned. No more connections may
                # be opened, and shutdown must not certify physical drainage.
                self._cleanup_unconfirmed = exc
                self.request_close()
            with self._contexts_lock:
                context["lost"] += 1
                context["first_failure"] = context["first_failure"] or type(exc).__name__
                context["latest"] = "partial"
            self._project(identity, "failed", context["lost"])
            raise
        else:
            context["latest"] = "partial" if context["lost"] else "bound"
            self._project(identity, "completed", context["lost"])
        finally:
            retired = False
            with self._contexts_lock:
                context["pending"] -= 1
                if context["handle"].terminal_requested.is_set() and context["pending"] == 0:
                    self._contexts.pop(identity, None)
                    retired = True
            if retired:
                self._project(identity, "settled", context["lost"])

    def wait_closed(self):
        # Join before reading pending counts. Discarded envelopes remain counted
        # as pending until this final reconciliation; no queued SQL is replayed.
        if self._started:
            self._thread.join()
        for identity, context in self._contexts.items():
            lost = context["lost"] + context["pending"]
            if context["pending"]:
                self._project(identity, "failed", lost)
            self._project(identity, "settled", lost)
        self._contexts.clear()
        super().wait_closed()


_writer = None
_start_attempted = False
_stopped = False
_startup_error = None
_unavailable_offers = 0
# E91: local native driver, four-configuration and combined physical-drain gates passed.
# A config flag alone cannot bypass this source-controlled adoption gate.
QUALIFIED = True


def configure():
    global _writer, _start_attempted, _startup_error
    if not QUALIFIED or _stopped or _start_attempted:
        return
    _start_attempted = True
    try:
        from stats.dal.import_audit_dal import optional_upload_connection

        _writer = ImportAuditWriter(optional_upload_connection).start()
    except Exception as exc:
        _startup_error = type(exc).__name__
        # Startup remains available; the adopted path never restores awaited SQL.
        # Only the error type is retained/logged, not credentials or exception text.
        try:
            logging.getLogger(__name__).warning(
                "Optional upload audit unavailable after startup failure: %s", _startup_error
            )
        except Exception:
            pass
    _summary()


def _summary():
    from services.operation_diagnostics import upload_worker_summary

    upload_worker_summary(
        "sql",
        _writer.latest if _writer else "unavailable",
        _unavailable_offers,
        _startup_error,
        dropped=_writer.dropped if _writer else 0,
        failures=_writer.failures if _writer else 0,
    )


def request_close():
    global _stopped
    _stopped = True
    if _writer is not None:
        _writer.request_close()


def wait_closed():
    try:
        if _writer is not None:
            _writer.wait_closed()
    finally:
        _summary()


def shutdown():
    request_close()
    wait_closed()


async def run_audit(fallback, function, *args, **kwargs):
    """Only explicitly migrated domain adapters enter this transport.

    Until qualification/adoption, existing synchronous audit semantics remain.
    Once adopted, overload never falls back to synchronous SQL.
    """
    global _unavailable_offers
    if _writer is None and (QUALIFIED or _start_attempted):
        _unavailable_offers = min(_unavailable_offers + 1, 2**63 - 1)
        _summary()
        return None
    if _writer is None:
        return await fallback(function, *args, **kwargs)
    domain = DOMAINS.get(function.__module__)
    if function.__name__.startswith("_start_") and domain is not None:
        context = args[0]
        details = {
            "entry_point": context.entry_point,
            "hash_availability": "unavailable",
            "outcome_version": 1,
        }
        for key in ("sql_operation", "is_test", "kvk_no"):
            if hasattr(context, key):
                details[key] = getattr(context, key)
        handle = _writer.start_batch(
            import_kind=domain[0],
            source_type=getattr(context, "source_type", domain[1]),
            source_filename=context.source_filename,
            source_message_id=context.source_message_id,
            source_channel_id=context.source_channel_id,
            actor_discord_id=context.actor_discord_id,
            details=details,
        )
        handles = _scope_handles.get()
        if handles is not None and handle is not None:
            handles[:] = [
                (writer, old) for writer, old in handles if not old.terminal_requested.is_set()
            ]
            handles.append((_writer, handle))
        return handle
    if args and isinstance(args[0], PendingAudit):
        action = {
            "record_phase_best_effort": "phase",
            "complete_batch_best_effort": "complete",
            "fail_batch_best_effort": "fail",
        }.get(function.__name__)
        return _writer.action(args[0], action, kwargs)
    # A previously bound legacy reference retains its original API/lifetime.
    return await fallback(function, *args, **kwargs)
