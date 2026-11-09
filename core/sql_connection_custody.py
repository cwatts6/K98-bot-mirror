"""Process-local custody for SQL cleanup that has not been acknowledged.

This is not a durable outcome or a recovery action. No automatic close retry,
handle release, provider replay or claim settlement is performed here.
"""

from threading import Lock

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
