"""Transport-independent contracts for fixed season sources and sealed updates."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from kvk.models.new_source_reporting import require_utc

SOURCES = frozenset(("legacy_full_data", "snapshot_report_v1"))
SEASON_STATES = ("planned", "open", "closing", "closed")
EXPORT_SCHEMA = "kvk-complete-vector-v1"
REVIEW_KINDS = frozenset(("choose_source", "intake", "match_update", "configuration"))


def review_payload(value):
    """Canonical bounded review data; no attachment bytes or floating point authority."""
    import json

    def check(item):
        if isinstance(item, float):
            raise ValueError("Review decimals must retain their source text.")
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise ValueError("Review keys must be text.")
                check(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                check(child)

    if not isinstance(value, dict):
        raise ValueError("Review payload must be an object.")
    check(value)
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(text.encode("utf-16-le")) > 65536:
        raise ValueError("Review exceeds the durable payload limit.")
    return text


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


# Reader protocol only. A matching database string is necessary, not deployment approval.
PUBLIC_REPORT_CAPABILITY = "kvk-public-report-v1"


@dataclass(frozen=True, slots=True)
class SeasonRead:
    """One authoritative read identity; never a source-selection instruction."""

    kvk_no: int
    source_key: str | None = None
    choice_id: str | None = None
    season_version: int | None = None
    routing_version: int | None = None
    capabilities_version: str | None = None
    period_id: str | None = None
    update_id: str | None = None
    update_version: int | None = None
    publication_id: str | None = None
    public_selection_version: int | None = None
    selected_config_id: str | None = None
    desired_config_id: str | None = None
    roster_id: str | None = None
    pending_update_id: str | None = None
    pending_update_version: int | None = None
    availability: str = "unavailable"
    reason: str = "source_unavailable"

    def __post_init__(self):
        if type(self.kvk_no) is not int or not 1 <= self.kvk_no <= 2147483647:
            raise ValueError("Invalid season read identity.")
        if self.source_key is not None and self.source_key not in SOURCES:
            raise ValueError("Invalid season read source.")
        for name in (
            "choice_id",
            "period_id",
            "update_id",
            "publication_id",
            "selected_config_id",
            "desired_config_id",
            "roster_id",
            "pending_update_id",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, identity(value))
        for name in (
            "season_version",
            "routing_version",
            "update_version",
            "public_selection_version",
            "pending_update_version",
        ):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 1):
                raise ValueError("Invalid season read version.")
        if self.availability not in {"unavailable", "legacy", "current", "previous_complete"}:
            raise ValueError("Invalid season read availability.")
        bounded_text(self.reason, 128)
        if self.capabilities_version is not None:
            bounded_text(self.capabilities_version, 64)
        if self.available and (not self.choice_id or self.season_version is None):
            raise ValueError("Available reads require an explicit season choice.")
        if self.availability == "legacy" and self.source_key != "legacy_full_data":
            raise ValueError("Legacy read requires the fixed legacy source.")
        if self.availability in {"current", "previous_complete"} and (
            self.source_key != "snapshot_report_v1"
            or self.capabilities_version != PUBLIC_REPORT_CAPABILITY
            or any(
                getattr(self, name) is None
                for name in (
                    "routing_version",
                    "period_id",
                    "update_id",
                    "update_version",
                    "publication_id",
                    "public_selection_version",
                    "selected_config_id",
                    "desired_config_id",
                    "roster_id",
                )
            )
        ):
            raise ValueError("Public source reads require the complete selection identity.")

    @property
    def available(self):
        return self.availability != "unavailable"

    def as_dict(self):
        from dataclasses import asdict

        return asdict(self)

    @property
    def cache_key(self):
        """Includes availability authority; independent caches never use this key."""
        return (PUBLIC_REPORT_CAPABILITY, *self.as_dict().values())


class LegacyReportingBlocks(dict):
    """Preserve legacy block keys while carrying resolved provenance to the renderer."""

    def __init__(self, blocks, read):
        super().__init__(blocks)
        self.read = read
