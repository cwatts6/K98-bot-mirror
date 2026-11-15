"""Calendar-local transaction acknowledgement and explicit physical custody.

A returned error does not prove rollback; a lost commit reply stays unknown.
The retained connection is deliberately excluded from public result projection.
"""

from dataclasses import dataclass, field
import re
from typing import Any


def error_facts(error: BaseException) -> dict[str, str | int]:
    facts: dict[str, str | int] = {"error_type": type(error).__name__[:80]}
    args = getattr(error, "args", ())
    if args and isinstance(args[0], str) and re.fullmatch(r"[A-Z0-9]{5}", args[0]):
        facts["sqlstate"] = args[0]
    # Only numeric native codes are retained; never driver messages or SQL values.
    if len(args) > 1 and isinstance(args[1], str):
        codes = re.findall(r"\((-?\d{1,10})\)", args[1][:4096])
        if codes:
            facts["native_code"] = int(codes[-1])
    return facts


@dataclass
class SqlOutcome:
    effect: str = "not_started"
    cleanup: str = "not_needed"
    rollback: str = "not_needed"
    error: dict = field(default_factory=dict)
    cleanup_error: dict = field(default_factory=dict)
    rollback_error: dict = field(default_factory=dict)
    retained_connection: Any = field(default=None, repr=False, compare=False)

    def public(self) -> dict:
        return {
            "effect": self.effect,
            "cleanup": self.cleanup,
            "rollback": self.rollback,
            "error": dict(self.error),
            "cleanup_error": dict(self.cleanup_error),
            "rollback_error": dict(self.rollback_error),
        }


class SqlSession:
    """Use on one worker thread. Never invokes the driver's implicit exit commit."""

    def __init__(self, factory, *, read_only=False):
        self.factory = factory
        self.read_only = read_only
        self.outcome = SqlOutcome()
        self.connection = None
        self.cursors = []
        self.commit_attempted = False

    def __enter__(self):
        self.connection = self.factory()
        self.outcome.cleanup = "pending"
        self.outcome.effect = "not_applicable" if self.read_only else "running"
        return self

    def cursor(self):
        cursor = self.connection.cursor()
        self.cursors.append(cursor)
        return cursor

    def commit(self):
        self.commit_attempted = True
        self.outcome.effect = "unknown"
        self.connection.commit()
        self.outcome.effect = "committed"

    def __exit__(self, exc_type, exc, tb):
        if exc is not None:
            self.outcome.error = error_facts(exc)
        if self.outcome.effect != "committed":
            try:
                self.connection.rollback()
                self.outcome.rollback = "confirmed"
                if not self.read_only and not self.commit_attempted:
                    self.outcome.effect = "rolled_back"
            except Exception as error:
                self.outcome.rollback = "unconfirmed"
                self.outcome.rollback_error = error_facts(error)
                if not self.read_only:
                    self.outcome.effect = "unknown"
        for cursor in self.cursors:
            try:
                cursor.close()
            except Exception as error:
                if not self.outcome.cleanup_error:
                    self.outcome.cleanup_error = error_facts(error)
        try:
            self.connection.close()
            self.outcome.cleanup = "settled"
        except Exception as error:
            self.outcome.cleanup = "unconfirmed"
            self.outcome.cleanup_error = error_facts(error)
            self.outcome.retained_connection = self.connection
        return False
