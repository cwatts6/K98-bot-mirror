"""Process-local custody for SQL cleanup that has not been acknowledged.

This is not a durable outcome or a recovery action. No automatic close retry,
handle release, provider replay or claim settlement is performed here.
"""

from threading import Lock
from types import SimpleNamespace

from event_calendar.sql_lifecycle import SqlOutcome, error_facts

_guard = Lock()
_holds: dict[int, SqlOutcome] = {}


class SqlCleanupUnknown(RuntimeError):
    """Retain the first failure and consult original durable operation evidence."""


def custody_snapshot():
    """Safe passive counts only; never return connection handles or driver prose."""
    with _guard:
        return {"admission": "closed" if _holds else "open", "unconfirmed": len(_holds)}


def require_sql_admission():
    with _guard:
        if _holds:
            raise SqlCleanupUnknown(
                "SQL cleanup remains unconfirmed; retain ownership for reconciliation."
            )


def connection_retained(connection):
    """Whether this exact connection is fenced by an inner resource owner."""
    with _guard:
        return any(
            outcome.retained_connection is connection
            or getattr(outcome.retained_connection, "connection", None) is connection
            for outcome in _holds.values()
        )


def retain_connection_resource(connection, resource):
    """Attach an outer handle to existing custody without replacing first evidence."""
    with _guard:
        for outcome in _holds.values():
            owner = outcome.retained_connection
            if owner is connection or getattr(owner, "connection", None) is connection:
                if resource is not None and resource is not owner:
                    outcome.retained_connection = SimpleNamespace(
                        connection=connection, owner=owner, resource=resource
                    )
                return True
    return False


def retain_connection(connection, *, effect, first_failure, cleanup_error):
    outcome = SqlOutcome(
        effect=effect,
        cleanup="unconfirmed",
        error=error_facts(first_failure),
        cleanup_error=error_facts(cleanup_error),
        retained_connection=connection,
    )
    with _guard:
        _holds[id(connection)] = outcome


def preserve_failure(first, error, phase):
    if first is None:
        return error
    first.add_note(f"SQL {phase} failed: {type(error).__name__}")
    return first
