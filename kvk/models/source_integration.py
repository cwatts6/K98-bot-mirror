"""Transport-independent contracts for fixed season sources and sealed updates."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from kvk.models.new_source_reporting import require_utc

SOURCES = frozenset(("legacy_full_data", "snapshot_report_v1"))
SEASON_STATES = ("planned", "open", "closing", "closed")
EXPORT_SCHEMA = "kvk-complete-vector-v1"


def identity(value: str) -> str:
    """Normalize UUIDs before hashing or comparing ODBC values."""
    return str(UUID(str(value)))


def bounded_text(value: str, units: int) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value.encode("utf-16-le")) > units * 2
    ):
        raise ValueError("A bounded nonempty audit value is required.")


@dataclass(frozen=True, slots=True)
class UpdateContext:
    update_id: str
    kvk_no: int
    period_id: str
    period_key: str
    choice_id: str
    config_version_id: str
    roster_id: str
    coverage_start_utc: datetime
    coverage_end_utc: datetime
    as_of_utc: datetime
    update_kind: str
    actor: str
    confirmed_utc: datetime
    confirmation_json: str
    request_id: str | None = None
    base_update_id: str | None = None

    def __post_init__(self):
        for name in ("update_id", "period_id", "choice_id", "config_version_id", "roster_id"):
            object.__setattr__(self, name, identity(getattr(self, name)))
        for name in ("request_id", "base_update_id"):
            if getattr(self, name) is not None:
                object.__setattr__(self, name, identity(getattr(self, name)))
        if type(self.kvk_no) is not int or not 1 <= self.kvk_no <= 2147483647:
            raise ValueError("Invalid season.")
        if self.update_kind not in ("fight", "overall", "no_fight"):
            raise ValueError("Invalid update kind.")
        if self.base_update_id == self.update_id:
            raise ValueError("An update cannot supersede itself.")
        bounded_text(self.actor, 128)
        bounded_text(self.period_key, 128)
        for value in (
            self.coverage_start_utc,
            self.coverage_end_utc,
            self.as_of_utc,
            self.confirmed_utc,
        ):
            require_utc(value)
            if value.microsecond:
                raise ValueError("SQL update times require exact seconds.")
        if not self.coverage_start_utc <= self.coverage_end_utc <= self.as_of_utc:
            raise ValueError("Invalid reporting coverage.")


@dataclass(frozen=True, slots=True)
class PlayerRevisions:
    start_scan_id: int
    end_scan_id: int
    start_revision_id: str
    end_revision_id: str

    def __post_init__(self):
        if any(
            type(v) is not int or not 1 <= v <= 2147483647
            for v in (self.start_scan_id, self.end_scan_id)
        ):
            raise ValueError("Invalid logical scan.")
        if self.end_scan_id < self.start_scan_id:
            raise ValueError("Endpoints must increase.")
        for name in ("start_revision_id", "end_revision_id"):
            object.__setattr__(self, name, identity(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class AggregateRevision:
    report_id: str
    revision_id: str

    def __post_init__(self):
        object.__setattr__(self, "report_id", identity(self.report_id))
        object.__setattr__(self, "revision_id", identity(self.revision_id))


@dataclass(frozen=True, slots=True)
class CompleteSelectionResult:
    update_id: str
    publication_id: str
    public_selection_version: int
    intent_id: str
    commit_sequence: int
    vector_hash: str
