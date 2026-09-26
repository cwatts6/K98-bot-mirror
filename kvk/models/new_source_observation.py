"""Immutable offline facts; no allocation, roster selection or publication state."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from kvk.schemas.new_source_schema import (
    SOURCE_KEY,
    MetricState,
    ReportState,
    SourceKind,
    TimePrecision,
)


@dataclass(frozen=True, slots=True)
class MetadataCandidate:
    original_filename: str = ""
    source_key: str = SOURCE_KEY
    kind: SourceKind | None = None
    kvk_no: int | None = None
    scan_start_utc: datetime | None = None
    time_precision: TimePrecision | None = None
    event_discriminator: str = "main"
    period_key: str | None = None
    coverage_start_utc: datetime | None = None
    coverage_end_utc: datetime | None = None
    as_of_utc: datetime | None = None
    report_state: ReportState | None = None
    ambiguity: str | None = None


@dataclass(frozen=True, slots=True)
class MetadataConfirmation:
    """Explicit supplied fields, plus actor/time/reason for reviewable overrides."""

    values: tuple[tuple[str, object], ...] = ()
    confirmed_fields: tuple[str, ...] = ()
    actor: str = ""
    confirmed_at_utc: datetime | None = None
    reason: str = ""


@dataclass(frozen=True, slots=True)
class SourceScope:
    kvk_no: int
    kingdoms: tuple[int, ...]
    period_keys: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidatedSourceMetadata:
    candidate: MetadataCandidate
    scope: SourceScope
    confirmation: MetadataConfirmation

    @property
    def event_identity(self) -> tuple[object, ...]:
        c = self.candidate
        return (
            c.source_key,
            c.kvk_no,
            c.kind,
            c.scan_start_utc,
            c.time_precision,
            c.event_discriminator,
            c.period_key,
        )


@dataclass(frozen=True, slots=True)
class CampMapping:
    """Caller-supplied frozen mapping: (kingdom, camp ID, camp display name)."""

    entries: tuple[tuple[int, int, str], ...]


@dataclass(frozen=True, slots=True)
class MetricValue:
    value: Decimal | str | None
    state: MetricState
    raw_token: str | None
    displayed_unit: Decimal | None = None
    precision_kind: str | None = None


@dataclass(frozen=True, slots=True)
class TypedCell:
    header: str
    cell_type: str
    raw_value: str | None
    numeric_value: Decimal | None
    number_format: str
    metric: MetricValue


@dataclass(frozen=True, slots=True)
class SourceRow:
    sheet: str
    key: int
    cells: tuple[TypedCell, ...]
    kingdom: int | None = None
    camp_id: int | None = None

    def cell(self, header: str) -> TypedCell:
        return next(cell for cell in self.cells if cell.header == header)


@dataclass(frozen=True, slots=True)
class ParseDiagnostic:
    code: str
    sheet: str
    count: int
    cell_range: str | None = None


@dataclass(frozen=True, slots=True)
class SemanticDigest:
    sha256: str
    canonical_version: str = "semantic_digest_v1"


@dataclass(frozen=True, slots=True)
class PreparedPlayerObservation:
    metadata: ValidatedSourceMetadata
    rows: tuple[SourceRow, ...]
    artifact_sha256: str
    schema_version: str
    digest: SemanticDigest
    diagnostics: tuple[ParseDiagnostic, ...]


@dataclass(frozen=True, slots=True)
class PreparedAggregateReport:
    metadata: ValidatedSourceMetadata
    kingdom_rows: tuple[SourceRow, ...]
    camp_rows: tuple[SourceRow, ...]
    mapping: CampMapping
    artifact_sha256: str
    schema_version: str
    digest: SemanticDigest
    diagnostics: tuple[ParseDiagnostic, ...]
