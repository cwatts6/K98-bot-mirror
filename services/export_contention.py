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
    return result


@contextmanager
def transaction(connect):
    """Mark only failures whose rollback AND connection close acknowledged."""
    try:
        with source_transaction(connect) as cursor:
            yield cursor
    except CoordinationLockRefused as error:
        # Any rollback/close exception replaces the refusal in source_transaction
        # and cannot reach here. A failed commit is UncertainCommit, not this type.
        error.transaction_released = True
        raise


@contextmanager
def contention_budget(deadline):
    previous = _deadline.get()
    token = _deadline.set(min(previous, deadline) if previous is not None else deadline)
    try:
        yield
    finally:
        _deadline.reset(token)


def retry_coordination(function):
    """Retry only explicit timeout refusals from our dedicated transaction wrapper."""

    @wraps(function)
    def run(*args, **kwargs):
        # We do not own rollback or producer work on an external transaction.
        if kwargs.get("external_cursor") is not None:
            return function(*args, **kwargs)
        started = time.monotonic()
        with contention_budget(started + LOCK_BUDGET_SECONDS):
            attempt = 0
            while True:
                attempt += 1
                try:
                    value = function(*args, **kwargs)
                except CoordinationLockRefused as error:
                    remaining = _deadline.get() - time.monotonic()
                    safe = error.result == -1 and error.transaction_released
                    if not safe or remaining <= 0 or attempt >= MAX_ATTEMPTS:
                        logger.warning(
                            "export_contention_result %s",
                            json.dumps(
                                dict(
                                    stage=function.__name__,
                                    outcome="exhausted" if safe else "not_retryable",
                                    attempt=attempt,
                                    elapsed_ms=int((time.monotonic() - started) * 1000),
                                    **sql_error_facts(error),
                                ),
                                sort_keys=True,
                            ),
                        )
                        raise
                    time.sleep(min(0.025 * 2 ** (attempt - 1), 0.25, remaining))
                    # Never start a new transaction after the total deadline.
                    if time.monotonic() >= _deadline.get():
                        logger.warning(
                            "export_contention_result %s",
                            json.dumps(
                                dict(
                                    stage=function.__name__,
                                    outcome="exhausted",
                                    attempt=attempt,
                                    elapsed_ms=int((time.monotonic() - started) * 1000),
                                    **sql_error_facts(error),
                                ),
                                sort_keys=True,
                            ),
                        )
                        raise
                else:
                    if attempt > 1:
                        logger.info(
                            "export_contention_result %s",
                            json.dumps(
                                dict(
                                    stage=function.__name__,
                                    outcome="recovered",
                                    attempt=attempt,
                                    elapsed_ms=int((time.monotonic() - started) * 1000),
                                ),
                                sort_keys=True,
                            ),
                        )
                    return value

    return run
