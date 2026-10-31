"""Evidence vocabulary shared by adapters; presentation is a separate outcome."""

from enum import StrEnum


class MutationOutcome(StrEnum):
    NOT_ENTERED = "not_entered"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    UNKNOWN = "unknown"
