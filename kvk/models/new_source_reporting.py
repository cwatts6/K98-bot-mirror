"""Immutable S3A calculation contracts; no storage, clocks or consumer activation."""

from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, localcontext
from enum import StrEnum

from kvk.models.new_source_observation import (
    CampMapping,
    PreparedAggregateReport,
    PreparedPlayerObservation,
)
from kvk.schemas.new_source_schema import INT_MAX, SOURCE_KEY, MetricState

CALCULATION_VERSION = "snapshot_report_calculation_v1"


class PeriodKind(StrEnum):
    FIGHT = "fight"
    OVERALL = "overall"
    NO_FIGHT = "no_fight"


class StreamState(StrEnum):
    LIVE = "live"
    FINAL = "final"
    CORRECTED_FINAL = "corrected_final"
    MISSING_START = "missing_start"
    MISSING_END = "missing_end"
    MISSING_CONFIGURATION = "missing_configuration"
    NOT_RECEIVED = "not_received"
    VALIDATION_FAILED = "validation_failed"
    NOT_APPLICABLE = "not_applicable"
    FINAL_UNAVAILABLE = "final_unavailable"


TERMINAL_STATES = frozenset(
    (
        StreamState.FINAL,
        StreamState.CORRECTED_FINAL,
        StreamState.NOT_APPLICABLE,
        StreamState.FINAL_UNAVAILABLE,
    )
)


def require_utc(value: datetime) -> None:
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0):
        raise ValueError("An explicit UTC timestamp is required.")
    if value.microsecond:
        raise ValueError("Source timestamps require whole-second precision.")


def fits_decimal(value: Decimal, scale: int) -> bool:
    """Check SQL decimal(38, scale) without rounding or ambient-context dependence."""
    if not isinstance(value, Decimal) or not value.is_finite():
        return False
    with localcontext() as context:
        context.prec = 100
        if abs(value) >= Decimal(10) ** (38 - scale):
            return False
        try:
            return value == value.quantize(Decimal(1).scaleb(-scale))
        except InvalidOperation:
            return False


@dataclass(frozen=True, slots=True)
class FrozenWeights:
    version_id: str
    x_source: str
    y_source: str
    z_source: str
    effective_from_utc: datetime

    def __post_init__(self):
        require_utc(self.effective_from_utc)
        if not self.version_id:
            raise ValueError("Weights require an approved version.")
        for token in (self.x_source, self.y_source, self.z_source):
            if not isinstance(token, str) or not token or len(token) > 128:
                raise ValueError("Weights require bounded source decimal strings.")
            try:
                valid = fits_decimal(Decimal(token), 12)
            except InvalidOperation:
                valid = False
            if not valid:
                raise ValueError("Weight cannot be represented exactly as decimal(38,12).")

    @property
    def coefficients(self) -> tuple[Decimal, Decimal, Decimal]:
        return Decimal(self.x_source), Decimal(self.y_source), Decimal(self.z_source)


@dataclass(frozen=True, slots=True)
class ObservationInput:
    """An accepted, revision-pinned player event; logical IDs never imply chronology."""

    logical_scan_id: int
    observation_id: str
    revision_id: str
    observation: PreparedPlayerObservation
    period_keys: tuple[str, ...]

    def __post_init__(self):
        if type(self.logical_scan_id) is not int or not 1 <= self.logical_scan_id <= INT_MAX:
            raise ValueError("Invalid source logical scan ID.")
        if not self.observation_id or not self.revision_id:
            raise ValueError("Accepted observation and revision identities are required.")
        require_utc(self.scan_start_utc)
        if not isinstance(self.period_keys, tuple):
            raise ValueError("Period associations must be immutable.")

    @property
    def scan_start_utc(self) -> datetime:
        value = self.observation.metadata.candidate.scan_start_utc
        if value is None:
            raise ValueError("Missing validated scan start.")
        return value


@dataclass(frozen=True, slots=True)
class WindowConfig:
    version_id: str
    kvk_no: int
    period_id: str
    period_key: str
    period_kind: PeriodKind
    label: str
    start_scan_id: int | None
    end_scan_id: int | None
    roster_id: str
    b0_revision_id: str
    map_version_id: str
    mapping: CampMapping
    weights: FrozenWeights | None
    closes_at_utc: datetime | None = None
    source_key: str = SOURCE_KEY

    def __post_init__(self):
        if (
            self.source_key != SOURCE_KEY
            or type(self.kvk_no) is not int
            or not 1 <= self.kvk_no <= INT_MAX
        ):
            raise ValueError("Invalid source/season scope.")
        if not all(
            (
                self.version_id,
                self.period_id,
                self.roster_id,
                self.b0_revision_id,
                self.map_version_id,
                self.label,
            )
        ):
            raise ValueError("Pinned configuration identities are required.")
        expected = self.period_kind.value
        if not (
            self.period_key == "overall"
            if expected == "overall"
            else self.period_key.startswith(expected + ":")
        ):
            raise ValueError("Period key/kind mismatch.")
        for scan in (self.start_scan_id, self.end_scan_id):
            if scan is not None and (type(scan) is not int or not 1 <= scan <= INT_MAX):
                raise ValueError("Invalid configured scan ID.")
        if self.start_scan_id is not None and self.end_scan_id is not None:
            if self.end_scan_id < self.start_scan_id:
                raise ValueError("Configured end precedes start slot.")
        if self.closes_at_utc is not None:
            require_utc(self.closes_at_utc)
        entries = self.mapping.entries
        if (
            not isinstance(entries, tuple)
            or not entries
            or len({e[0] for e in entries}) != len(entries)
        ):
            raise ValueError("Require one frozen camp mapping per kingdom.")
        if any(
            type(k) is not int or k <= 0 or type(c) is not int or not 1 <= c <= 8 or not n
            for k, c, n in entries
        ):
            raise ValueError("Invalid camp mapping.")


@dataclass(frozen=True, slots=True)
class EndpointChange:
    """Normal authorized config-import provenance, not a second correction command."""

    request_id: str
    period_id: str
    base_config_id: str
    desired_config_id: str
    old_end_scan_id: int | None
    new_end_scan_id: int | None
    actor: str
    reason: str


@dataclass(frozen=True, slots=True)
class WindowInputSelection:
    config: WindowConfig
    start: ObservationInput | None
    end: ObservationInput | None
    player_state: StreamState
    endpoint_pending: bool
    endpoint_change: EndpointChange | None = None

    def __post_init__(self):
        if self.start is not None:
            if self.start.logical_scan_id != self.config.start_scan_id:
                raise ValueError("Selected start must be the exact configured slot.")
        for event in (self.start, self.end):
            if event is not None and self.config.period_key not in event.period_keys:
                raise ValueError("Selected event must be explicitly mapped to the period.")
        usable = (
            StreamState.LIVE,
            StreamState.FINAL,
            StreamState.CORRECTED_FINAL,
            StreamState.NOT_APPLICABLE,
        )
        if self.player_state in usable and (self.start is None or self.end is None):
            raise ValueError("Usable player streams require both exact endpoints.")
        if self.start is not None and self.end is not None:
            if self.config.period_kind == PeriodKind.NO_FIGHT:
                if self.start != self.end or self.player_state != StreamState.NOT_APPLICABLE:
                    raise ValueError("No-fight requires identical endpoints and no combat state.")
            elif self.end.scan_start_utc <= self.start.scan_start_utc:
                raise ValueError("Player endpoints require increasing event UTC.")
            if self.config.closes_at_utc and self.end.scan_start_utc > self.config.closes_at_utc:
                raise ValueError("Selected end exceeds the configured close.")
        if self.player_state in (StreamState.FINAL, StreamState.CORRECTED_FINAL):
            if self.end.logical_scan_id != self.config.end_scan_id or self.endpoint_pending:
                raise ValueError("Final must satisfy the exact configured end.")
        if self.player_state == StreamState.CORRECTED_FINAL and self.endpoint_change is None:
            raise ValueError("Replacement final requires endpoint request provenance.")


@dataclass(frozen=True, slots=True)
class CalculatedMetric:
    value: Decimal | None
    state: MetricState
    reason: str | None = None

    def __post_init__(self):
        if (self.state == MetricState.AVAILABLE) != (self.value is not None):
            raise ValueError("Availability and numeric value must agree.")
        if self.value is not None and (
            not isinstance(self.value, Decimal) or not self.value.is_finite()
        ):
            raise ValueError("Metrics require finite Decimal values.")


@dataclass(frozen=True, slots=True)
class MetricRank:
    rank: int
    population: int
    top_position_percent: Decimal


@dataclass(frozen=True, slots=True)
class PlayerPeriodResult:
    governor_id: int
    b0_kingdom: int
    camp_id: int
    name: str | None
    metrics: tuple[tuple[str, CalculatedMetric], ...]
    ranks: tuple[tuple[str, MetricRank], ...] = ()
    observed_kingdom_changed: bool = False

    def metric(self, key: str) -> CalculatedMetric:
        return dict(self.metrics)[key]


@dataclass(frozen=True, slots=True)
class PeriodCalculation:
    selection: WindowInputSelection
    players: tuple[PlayerPeriodResult, ...]
    eligible_count: int
    paired_count: int
    missing_start_count: int
    missing_end_count: int
    excluded_count: int
    metric_coverage: tuple[tuple[str, int], ...]
    calculation_version: str = CALCULATION_VERSION


@dataclass(frozen=True, slots=True)
class AggregateSelection:
    report_id: str
    revision_id: str
    report: PreparedAggregateReport


@dataclass(frozen=True, slots=True)
class ComparisonBasis:
    source_key: str
    metric_definition: str
    period_kind: PeriodKind
    cohort_basis: str
    weight_basis: tuple[str, ...]
    precision_basis: str

    def comparable_to(self, other: "ComparisonBasis") -> bool:
        return self == other


@dataclass(frozen=True, slots=True)
class ReportSnapshotV2:
    publication_id: str
    selection_version: int
    generation: int
    requested_config: WindowConfig
    calculation: PeriodCalculation
    aggregate: AggregateSelection | None
    player_state: StreamState
    aggregate_state: StreamState
    period_state: StreamState
    final_unavailable_reason: str | None = None
    schema_version: int = 2

    def __post_init__(self):
        selected = self.calculation.selection.config
        if (
            self.requested_config.source_key,
            self.requested_config.kvk_no,
            self.requested_config.period_id,
            self.requested_config.period_key,
        ) != (selected.source_key, selected.kvk_no, selected.period_id, selected.period_key):
            raise ValueError("Requested and selected periods must match exactly.")
        if not self.publication_id or self.selection_version < 1 or self.generation < 1:
            raise ValueError("Publication identity and positive versions are required.")
        if self.schema_version != 2:
            raise ValueError("Unsupported report schema.")
        if (
            self.requested_config.version_id == selected.version_id
            and self.requested_config != selected
        ):
            raise ValueError("A configuration version cannot describe different contents.")
        if self.player_state != self.calculation.selection.player_state:
            if self.player_state != StreamState.FINAL_UNAVAILABLE:
                raise ValueError("Player state must describe selected endpoints.")
        if StreamState.FINAL_UNAVAILABLE in (self.player_state, self.aggregate_state):
            if not self.final_unavailable_reason or not self.final_unavailable_reason.strip():
                raise ValueError("Terminal unavailability requires an explicit reason.")
        if self.period_state not in (
            StreamState.LIVE,
            StreamState.FINAL,
            StreamState.CORRECTED_FINAL,
        ):
            raise ValueError("Invalid period state.")
        if self.period_state != StreamState.LIVE:
            if (
                self.player_state not in TERMINAL_STATES
                or self.aggregate_state not in TERMINAL_STATES
            ):
                raise ValueError("A reason cannot finalize a live or missing stream.")
        if self.aggregate is None:
            if self.aggregate_state not in (
                StreamState.NOT_RECEIVED,
                StreamState.NOT_APPLICABLE,
                StreamState.VALIDATION_FAILED,
                StreamState.FINAL_UNAVAILABLE,
            ):
                raise ValueError("Aggregate facts are required for an available stream.")
        else:
            report = self.aggregate.report
            meta = report.metadata.candidate
            if not self.aggregate.report_id or not self.aggregate.revision_id:
                raise ValueError("Aggregate revision identity is required.")
            if (meta.source_key, meta.kvk_no, meta.period_key) != (
                selected.source_key,
                selected.kvk_no,
                selected.period_key,
            ):
                raise ValueError("Aggregate belongs to another source/season/period.")
            if report.mapping != selected.mapping or selected.period_kind == PeriodKind.NO_FIGHT:
                raise ValueError("Aggregate mapping or applicability mismatch.")
            if meta.report_state is None or self.aggregate_state.value != meta.report_state.value:
                raise ValueError("Aggregate finality must remain its own supplied state.")
            if selected.period_kind == PeriodKind.OVERALL and self.aggregate_state not in (
                StreamState.FINAL,
                StreamState.CORRECTED_FINAL,
            ):
                raise ValueError("Overall aggregates require their separate final report.")
        if (
            selected.period_kind == PeriodKind.NO_FIGHT
            and self.aggregate_state != StreamState.NOT_APPLICABLE
        ):
            raise ValueError("No-fight aggregates are not applicable.")
        if (
            selected.period_kind != PeriodKind.NO_FIGHT
            and self.aggregate_state == StreamState.NOT_APPLICABLE
        ):
            raise ValueError("Not-applicable aggregates are only valid for no-fight periods.")

    @property
    def is_current(self) -> bool:
        return self.requested_config == self.calculation.selection.config

    @property
    def current_period_state(self) -> StreamState:
        return self.period_state if self.is_current else StreamState.MISSING_CONFIGURATION

    def to_dict(self) -> dict:
        """Serialize report facts only; omit private parser cells and artifact diagnostics."""
        config = self.calculation.selection.config
        selection = self.calculation.selection
        aggregate = self.aggregate

        def endpoint(item):
            if item is None:
                return None
            return {
                "scan_id": item.logical_scan_id,
                "observation_id": item.observation_id,
                "revision_id": item.revision_id,
                "scan_start_utc": item.scan_start_utc,
                "time_precision": item.observation.metadata.candidate.time_precision,
            }

        payload = {
            "schema_version": 2,
            "source_key": config.source_key,
            "kvk_no": config.kvk_no,
            "period_id": config.period_id,
            "period_key": config.period_key,
            "period_kind": config.period_kind,
            "period_label": config.label,
            "publication_id": self.publication_id,
            "selection_version": self.selection_version,
            "generation": self.generation,
            "requested_config_id": self.requested_config.version_id,
            "selected_config_id": config.version_id,
            "requested_end_scan_id": self.requested_config.end_scan_id,
            "selected_config_end_scan_id": config.end_scan_id,
            "roster_id": config.roster_id,
            "map_version_id": config.map_version_id,
            "weights": config.weights,
            "calculation_version": self.calculation.calculation_version,
            "metric_definitions": {
                "counter_deltas": "exact selected end minus exact start; missing is unavailable",
                "power": "signed power-point delta",
                "troops_power": "signed troop-power-point delta",
                "starting_power": "B0 power points, independent of fight start",
                "kills_gain": "T4 plus T5 kill deltas, troops",
                "kp_t4_t5": "10*T4 delta + 20*T5 delta, points; overall player rank basis",
                "total_kill_points": "source Total Kill Points endpoint delta, points",
                "dead": "source total deaths endpoint delta, troops",
                "healed": "source Healed endpoint delta, troops; no intervening maximum",
                "healed_points": "source healed delta * 20, calculated points",
                "dkp": "frozen X*T4 delta + Y*T5 delta + Z*total-deaths delta, points",
                "dkp_power_ratio": "DKP / positive B0 power, exact decimal(38,12) fraction",
                "rank": "descending available value then numeric GovernorID, usable B0 cohort",
                "top_position_percent": "ordinal rank/population*100; 50-digit presentation ratio",
                "aggregate": "supplied report values, raw tokens and units; no recalculation",
            },
            "is_current": self.is_current,
            "current_period_state": self.current_period_state,
            "selected_period_state": self.period_state,
            "player_state": self.player_state,
            "aggregate_state": self.aggregate_state,
            "player_start": endpoint(selection.start),
            "player_end": endpoint(selection.end),
            "endpoint_pending": selection.endpoint_pending or not self.is_current,
            "final_unavailable_reason": self.final_unavailable_reason,
            "coverage": {
                key: getattr(self.calculation, key)
                for key in (
                    "eligible_count",
                    "paired_count",
                    "missing_start_count",
                    "missing_end_count",
                    "excluded_count",
                    "metric_coverage",
                )
            },
            "players": self.calculation.players,
            "aggregate": None,
        }
        if aggregate is not None:
            meta = aggregate.report.metadata.candidate

            def rows(items):
                return tuple(
                    {
                        "key": row.key,
                        "kingdom": row.kingdom,
                        "camp_id": row.camp_id,
                        "metrics": tuple((cell.header, cell.metric) for cell in row.cells),
                    }
                    for row in items
                )

            payload["aggregate"] = {
                "report_id": aggregate.report_id,
                "revision_id": aggregate.revision_id,
                "coverage_start_utc": meta.coverage_start_utc,
                "coverage_end_utc": meta.coverage_end_utc,
                "as_of_utc": meta.as_of_utc,
                "state": self.aggregate_state,
                "kingdom_rows": rows(aggregate.report.kingdom_rows),
                "camp_rows": rows(aggregate.report.camp_rows),
            }
        return _json_value(payload)


def _json_value(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        require_utc(value)
        return value.isoformat()
    if isinstance(value, StrEnum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _json_value(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    raise TypeError("Unsupported report value; binary floats are forbidden.")
