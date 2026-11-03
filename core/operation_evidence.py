"""Optional process-local observations. These values confer no recovery authority."""

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
import os
import re
import threading
from uuid import UUID, uuid4

_current = ContextVar("operation_observation", default=None)
try:
    _incarnation = uuid4().hex  # Diagnostic incarnation, NOT native process creation evidence.
except Exception:
    _incarnation = None
_labels = re.compile(r"[a-zA-Z_][a-zA-Z_0-9]{0,79}\Z")
_slots = threading.BoundedSemaphore(256)
_owners = {}
_owners_lock = threading.Lock()
STAGES = frozenset(
    {
        "operation",
        "configuration_attempt",
        "worker_execution",
        "worker_observer",
        "worker_queue_wait",
        "proc_config_import",
        "build_player_stats_cache",
        "warm_profile_cache",
        "warm_name_cache",
        "acknowledgement",
        "interaction_age_at_entry",
        "private_callback",
        "private_response",
        "private_operation",
        "mge_dataset_prepare",
        "mge_roster_thread_wait",
        "mge_roster_owner_wait",
        "mge_board_owner_wait",
        "mge_review_read",
        "mge_awards_read",
        "discord_message_fetch",
        "discord_message_edit",
        "sync_event_signup_embed",
        "sync_event_awards_embed",
        "sync_event_leadership_embed",
        "unavailable",
    }
)
STATES = frozenset(
    {
        "running",
        "observed",
        "entered",
        "settled",
        "completed",
        "interrupted",
        "failed",
        "confirmed",
        "already_acknowledged",
        "unconfirmed",
        "cancelled_draining",
        "result_returned",
        "deadline_elapsed_draining",
        "deadline_elapsed_pending",
        "deadline_elapsed_outcome_unconfirmed",
        "cancelled_outcome_unconfirmed",
        "completed_after_deadline",
        "verification_unavailable",
        "unavailable",
    }
)


def optional(function, *args, **kwargs):
    """Only for ancillary synchronous diagnostics; never wrap business/receipt writes."""
    try:
        return function(*args, **kwargs)
    except Exception:
        return None


def label(value):
    return value if type(value) is str and _labels.fullmatch(value) else "unavailable"


def result_facts(result):
    """Never copy arbitrary result/report text, errors, payloads or paths."""
    facts = {}
    report = None
    if type(result) is bool:
        facts["reported_success"] = result
    elif type(result) is tuple and len(result) == 2:
        ok, report = result
        if type(ok) is bool:
            facts["reported_success"] = ok
    if type(report) is dict:
        for key in ("attempt_id", "operation_id"):
            value = report.get(key)
            if type(value) is str and len(value) <= 36:
                try:
                    facts[key] = str(UUID(value))
                except ValueError:
                    pass
        for key, allowed in {
            "attempt_recording": {"recorded", "unrecorded"},
            "attempt_outcome": {
                "unconfirmed",
                "reported_success",
                "failed_before_inputs",
                "failed_after_inputs",
            },
        }.items():
            value = report.get(key)
            if type(value) is str and value in allowed:
                facts[key] = value
        if type(report.get("import_reported_success")) is bool:
            facts["import_reported_success"] = report["import_reported_success"]
    return facts


class Observation:
    def __init__(self, enabled=True):
        self.reference = uuid4().hex if enabled else None
        self.worker_result = {}
        self.references = {}


_disabled = Observation(enabled=False)


def _lost_scope():
    from services.operation_diagnostics import note_context_loss

    note_context_loss()


@contextmanager
def scope():
    existing = _current.get()
    if existing is not None:
        yield existing
        return
    admitted = False
    try:
        admitted = _slots.acquire(blocking=False)
        observation = Observation(enabled=admitted)
        token = _current.set(observation)
    except Exception:
        if admitted:
            optional(_slots.release)
        optional(_lost_scope)
        yield _disabled
        return
    if not admitted:
        optional(_lost_scope)
    try:
        yield observation
    except BaseException:
        emit("operation", "interrupted")
        raise
    else:
        # Scope settlement is not a domain success/receipt. It only ends retention
        # protection for scopes with no recorded failure.
        emit("operation", "settled")
    finally:
        optional(_current.reset, token)
        if admitted:
            optional(_slots.release)


def reference():
    current = _current.get()
    return current.reference if current is not None else None


def owner_wait(resource, stage):
    """Observe an existing local lock holder; never acquire that business lock."""
    holder = None
    if _owners_lock.acquire(blocking=False):
        try:
            entry = _owners.get(id(resource))
            holder = entry[0] if entry is not None and entry[1] else None
        finally:
            _owners_lock.release()
    emit(stage, "observed", holder=holder)


@contextmanager
def local_owner(resource, stage):
    """Called inside the real owner; bounded diagnostic registry is not authority."""
    identifier = reference()
    entry = None
    if identifier is not None and _owners_lock.acquire(blocking=False):
        try:
            for key, old in list(_owners.items()):
                if not old[1]:
                    del _owners[key]
            if id(resource) not in _owners and len(_owners) < 256:
                entry = [identifier, True]
                _owners[id(resource)] = entry
        finally:
            _owners_lock.release()
    emit(stage, "entered", holder=identifier)
    try:
        yield
    finally:
        # Invalidate before attempting cleanup: no wait, and no stale attribution
        # if the registry is busy and Python later reuses the resource identity.
        if entry is not None:
            entry[1] = False
            if _owners_lock.acquire(blocking=False):
                try:
                    if _owners.get(id(resource)) is entry:
                        _owners.pop(id(resource), None)
                finally:
                    _owners_lock.release()
        emit(stage, "settled", holder=identifier)


def bind_attempt(attempt_id, operation_id):
    current = _current.get()
    if current is not None:
        current.references.update(
            attempt_id=str(UUID(attempt_id)), operation_id=str(UUID(operation_id))
        )
        emit("configuration_attempt", "observed")


def worker_result(result):
    current = _current.get()
    if current is not None:
        facts = result_facts(result)
        if facts:
            current.worker_result = facts
        emit("worker_execution", "settled", facts=current.worker_result)


def emit(stage, state, *, elapsed_ms=None, facts=None, error=None, holder=None):
    """Bounded, non-waiting offer; no I/O, formatting or arbitrary callbacks here."""
    optional(_emit, stage, state, elapsed_ms=elapsed_ms, facts=facts, error=error, holder=holder)


def _emit(stage, state, *, elapsed_ms=None, facts=None, error=None, holder=None):
    from services.operation_diagnostics import offer

    current = _current.get()
    if current is None or current.reference is None:
        return
    # All facts are produced by result_facts, never caller dictionaries.
    event = dict(
        reference=current.reference,
        stage=stage if type(stage) is str and stage in STAGES else "unavailable",
        state=state if type(state) is str and state in STATES else "unavailable",
        observed_utc=datetime.now(UTC).isoformat(),
        process_incarnation=_incarnation,
        pid=os.getpid(),
        thread_id=threading.get_ident(),
        native_process_creation="unavailable_not_collected",
        sql_holder="unavailable_P02",
        **current.references,
    )
    if _incarnation is None:
        event.pop("process_incarnation")
    if type(elapsed_ms) in (int, float) and 0 <= elapsed_ms <= 1e12:
        event["elapsed_ms"] = elapsed_ms
        event["timing_scope"] = "inclusive"
    if holder is not None:
        event["local_holder_reference"] = holder
    if facts is not None:
        event.update(
            {
                key: value
                for key, value in facts.items()
                if key
                in {
                    "reported_success",
                    "attempt_id",
                    "operation_id",
                    "attempt_recording",
                    "attempt_outcome",
                    "import_reported_success",
                }
            }
        )
    if error is not None:
        event["error_type"] = label(type(error).__name__)
        # Inspect bounded primitive driver args; never format an exception or read
        # traceback source files while the business owner is held.
        current_error = error
        for _ in range(4):
            for arg in current_error.args[:8]:
                if type(arg) is str:
                    if re.fullmatch(r"[0-9A-Z]{5}", arg):
                        event.setdefault("sqlstate", arg)
                    match = re.search(r"\((\d{1,9})\)", arg[:4096])
                    if match:
                        event.setdefault("native_error", int(match.group(1)))
            current_error = current_error.__cause__ or current_error.__context__
            if current_error is None:
                break
        frame = error.__traceback__
        for _ in range(32):
            if frame is None:
                break
            event["failure_function"] = label(frame.tb_frame.f_code.co_name)
            event["failure_line"] = frame.tb_lineno
            frame = frame.tb_next
    offer(event)
