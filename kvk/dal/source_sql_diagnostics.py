"""Bounded source SQL diagnostics. Never log SQL text, parameters or exception text."""

from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps
import hashlib
import logging
import re
from uuid import uuid4

import pyodbc

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SqlFailure:
    stage: str
    statement_id: str
    error_type: str
    sqlstate: str
    native_code: str


@dataclass
class _Operation:
    correlation: str
    failure: SqlFailure | None = None


_active: ContextVar[_Operation | None] = ContextVar("source_sql_diagnostic", default=None)


def _failure(exc, stage, statement_id):
    sqlstate, native = "unknown", "unknown"
    if isinstance(exc, pyodbc.Error):
        args = exc.args
        if args and isinstance(args[0], str) and re.fullmatch(r"[A-Z0-9]{5}", args[0]):
            sqlstate = args[0]
        # Read only bounded driver diagnostics; do not stringify arbitrary objects.
        for arg in args[1:5]:
            if isinstance(arg, str):
                match = re.search(r"\((-?\d{1,10})\) \(SQL[A-Za-z]{1,40}\)(?:;|$)", arg[:4096])
                if match:
                    native = match[1]
                    break
    name = type(exc).__name__
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", name):
        name = "Exception"
    return SqlFailure(stage, statement_id, name, sqlstate, native)


def diagnostic_call(stage, call, *args, statement_id="none"):
    """Record the first failure without replacing it when rollback/close also fails."""
    try:
        return call(*args)
    except Exception as exc:
        operation = _active.get()
        if operation is not None and operation.failure is None:
            operation.failure = _failure(exc, stage, statement_id)
        raise


def diagnosed_source_operation(call):
    """One correlation across nested receipt/import transactions, with no retry."""

    @wraps(call)
    def run(*args, **kwargs):
        if _active.get() is not None:
            return call(*args, **kwargs)
        operation = _Operation(uuid4().hex)
        token = _active.set(operation)
        try:
            return call(*args, **kwargs)
        except Exception as exc:
            failure = operation.failure
            if failure is not None:
                # A generated opaque reference is the only new Discord-facing detail.
                exc.source_sql_correlation = operation.correlation
                logger.warning(
                    "Source SQL failure correlation=%s stage=%s statement=%s type=%s "
                    "sqlstate=%s native=%s",
                    operation.correlation,
                    failure.stage,
                    failure.statement_id,
                    failure.error_type,
                    failure.sqlstate,
                    failure.native_code,
                )
            raise
        finally:
            _active.reset(token)

    return run


def failure_reference(exc):
    value = getattr(exc, "source_sql_correlation", None)
    return value if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{32}", value) else None


class _DiagnosticCursor:
    def __init__(self, cursor):
        self._cursor = cursor
        self._statement_id = "none"

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def execute(self, statement, *parameters):
        # Fingerprints identify the exact template without exposing its contents.
        self._statement_id = hashlib.sha256(statement.encode("utf-8")).hexdigest()[:16]
        diagnostic_call(
            "execute", self._cursor.execute, statement, *parameters, statement_id=self._statement_id
        )
        return self

    def fetchone(self):
        return diagnostic_call("fetchone", self._cursor.fetchone, statement_id=self._statement_id)

    def fetchall(self):
        return diagnostic_call("fetchall", self._cursor.fetchall, statement_id=self._statement_id)


def diagnostic_cursor(cursor):
    if _active.get() is None or isinstance(cursor, _DiagnosticCursor):
        return cursor
    return _DiagnosticCursor(cursor)
