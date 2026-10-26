"""Bounded retry of rolled-back coordination work, never producer execution."""

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import json
import logging
import re
import time

from kvk.dal.new_source_import_dal import transaction as source_transaction

logger = logging.getLogger(__name__)
_retry_window = ContextVar("coordination_retry_window", default=None)
_deadline = ContextVar("export_coordination_deadline", default=None)
admission_diagnostics_enabled = ContextVar("export_admission_diagnostics", default=True)
# Match the existing dedicated SQL connection's 1000ms lock budget. This is
# shared across retries, not another 1000ms allowance for every lock/attempt.
LOCK_BUDGET_SECONDS = 1.0
MAX_ATTEMPTS = 8


class CoordinationLockRefused(RuntimeError):
    """An attributed applock refusal; not evidence of the producer's outcome."""

    def __init__(self, *, result, session, transaction_state, transaction_count, resource_hash):
        super().__init__("Export coordination lock refused; inspect structured diagnostics.")
        self.result = result
        self.session = session
        self.transaction_state = transaction_state
        self.transaction_count = transaction_count
        self.resource_hash = resource_hash
        self.transaction_released = False
        self.phase_timings_ms = None


def sql_error_facts(error):
    """Never include driver prose, SQL values, credentials or filenames."""
    args = getattr(error, "args", ())
    state = args[0] if args and isinstance(args[0], str) else None
    numbers = set()
    for value in args[1:5]:
        if isinstance(value, str):
            numbers.update(int(n) for n in re.findall(r"\((\d{3,6})\)", value[:8192]))
    result = dict(
        error_type=type(error).__name__[:64],
        sqlstate=state if state and re.fullmatch(r"[A-Z0-9]{5}", state) else None,
        native_errors=sorted(numbers)[:8],
    )
    if isinstance(error, CoordinationLockRefused):
        result.update(
            sqlstate="42000",
            native_errors=[51400],
            applock_result=error.result,
            sql_session_id=error.session,
            xact_state=error.transaction_state,
            transaction_count=error.transaction_count,
            resource_sha256=error.resource_hash,
            transaction_released=error.transaction_released,
        )
    if isinstance(error, CoordinationLockRefused) and error.phase_timings_ms is not None:
        result["phase_timings_ms"] = dict(error.phase_timings_ms)
    return result


@contextmanager
def transaction(connect):
    """Mark only failures whose rollback AND connection close acknowledged."""
    timings = {}

    def timed(phase, call, *args):
        started = time.monotonic()
        try:
            return call(*args)
        finally:
            timings[phase] = timings.get(phase, 0) + max(
                0, int((time.monotonic() - started) * 1000)
            )

    class Connection:
        # The body receives the original cursor. Only source_transaction's
        # connection lifecycle calls are observed; their semantics are unchanged.
        def __init__(self, connection):
            self.connection = connection

        def __getattr__(self, name):
            value = getattr(self.connection, name)
            if name in {"cursor", "commit", "rollback", "close"}:
                return lambda *args: timed(name, value, *args)
            return value

    try:
        with source_transaction(lambda: Connection(timed("connect", connect))) as cursor:
            started = time.monotonic()
            try:
                yield cursor
            finally:
                # Includes DAL Python work as well as SQL execution; this is
                # deliberately not labelled lock-held or exact statement time.
                timings["transaction_body"] = max(0, int((time.monotonic() - started) * 1000))
    except CoordinationLockRefused as error:
        # Any rollback/close exception replaces the refusal in source_transaction
        # and cannot reach here. A failed commit is UncertainCommit, not this type.
        error.transaction_released = True
        error.phase_timings_ms = timings
        raise


@contextmanager
def contention_budget(deadline):
    previous = _deadline.get()
    token = _deadline.set(min(previous, deadline) if previous is not None else deadline)
    try:
        yield
    finally:
        _deadline.reset(token)


@contextmanager
def coordination_retry_window(seconds):
    """Opt in a single admission call; inherited deadlines still take precedence."""
    if not 0 < seconds <= 5:
        raise ValueError("Admission retry window must be between zero and five seconds.")
    token = _retry_window.set(seconds)
    try:
        yield
    finally:
        _retry_window.reset(token)


def retry_coordination(function=None, *, budget_seconds=None):
    """Retry only explicit timeout refusals from our dedicated transaction wrapper."""

    if function is None:
        return lambda target: retry_coordination(target, budget_seconds=budget_seconds)
    if budget_seconds is not None and not 0 < budget_seconds <= 5:
        raise ValueError("Bounded coordination retry policy required.")

    @wraps(function)
    def run(*args, **kwargs):
        if kwargs.get("external_cursor") is not None:
            return function(*args, **kwargs)
        from services.cache_admission_diagnostics import identity, record

        correlation = identity()
        started = time.monotonic()

        def emit(outcome, attempt, error=None):
            facts = dict(
                stage=function.__name__,
                outcome=outcome,
                attempt=attempt,
                elapsed_ms=int((time.monotonic() - started) * 1000),
                **correlation,
            )
            if error is not None:
                facts.update(sql_error_facts(error))
            record(facts)
            log = logger.warning if error is not None else logger.info
            log("export_contention_result %s", json.dumps(facts, sort_keys=True))

        with contention_budget(
            started + (budget_seconds or _retry_window.get() or LOCK_BUDGET_SECONDS)
        ):
            attempt = 0
            while True:
                attempt += 1
                try:
                    value = function(*args, **kwargs)
                except CoordinationLockRefused as error:
                    remaining = _deadline.get() - time.monotonic()
                    safe = error.result == -1 and error.transaction_released
                    if not safe or remaining <= 0 or attempt >= MAX_ATTEMPTS:
                        emit("exhausted" if safe else "not_retryable", attempt, error)
                        raise
                    time.sleep(min(0.025 * 2 ** (attempt - 1), 0.25, remaining))
                    if time.monotonic() >= _deadline.get():
                        emit("exhausted", attempt, error)
                        raise
                else:
                    if attempt > 1:
                        emit("recovered", attempt)
                    return value

    return run
