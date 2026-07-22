"""Immutable renderer-independent contracts for leadership player review."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

ReviewPage = Literal["overview", "activity", "kvk", "record"]
FreshnessState = Literal["CURRENT", "STALE", "PARTIAL", "NO DATA"]
LookupStatus = Literal["found", "matches", "not_found", "invalid"]
LastActiveState = Literal["ACTIVE", "INACTIVE", "NOT_RECORDED"]


@dataclass(frozen=True, slots=True)
class LookupCandidate:
    governor_id: int
    governor_name: str
    normalized_name: str
    current_name: str | None
    current_alliance: str | None
    last_scan_at_utc: datetime | None
    present_latest: bool
    is_current_name: bool
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    seen_scan_count: int = 0
    score: float = 100.0


@dataclass(frozen=True, slots=True)
class LookupResult:
    status: LookupStatus
    candidates: tuple[LookupCandidate, ...] = ()
    error: str | None = None

    @property
    def candidate(self) -> LookupCandidate | None:
        return self.candidates[0] if self.status == "found" and self.candidates else None


@dataclass(frozen=True, slots=True)
class ReviewHeader:
    governor_id: int
    governor_name: str | None
    current_alliance: str | None
    current_power: int | None
    city_hall: int | None
    effective_now_utc: datetime
    anchor_date: date | None
    current_start_date: date | None
    current_end_date: date | None
    previous_start_date: date | None
    previous_end_date: date | None
    period_days: int
    latest_complete_scan_order: int | None
    latest_complete_scan_at_utc: datetime | None
    latest_governor_scan_order: int | None
    latest_governor_scan_at_utc: datetime | None
    present_latest: bool
    first_observed_date: date | None
    first_observed_offset_days: int | None
    location_x: int | None
    location_y: int | None
    location_updated_at_utc: datetime | None
    shield_ends_at_utc: datetime | None


@dataclass(frozen=True, slots=True)
class ScanPresence:
    window: str
    complete_scans: int
    present_scans: int
    scanned_days: int
    present_scanned_days: int


@dataclass(frozen=True, slots=True)
class SourceCoverage:
    window: str
    source_code: str
    required: bool
    expected_units: int
    valid_units: int
    missing_units: int
    reset_count: int
    state: str


@dataclass(frozen=True, slots=True)
class ActivityMetric:
    order: int
    code: str
    current_total: Decimal | None
    current_valid_days: int
    current_average: Decimal | None
    previous_total: Decimal | None
    previous_valid_days: int
    previous_average: Decimal | None
    comparison_mode: str
    comparison_percent: Decimal | None
    expected_units: int
    missing_units: int
    reset_count: int
    available: bool
    kingdom_rank: int | None
    cohort_count: int | None
    percentile: Decimal | None
    top_percent: Decimal | None


@dataclass(frozen=True, slots=True)
class ActivityIndex:
    value: Decimal | None
    rank: int | None
    cohort_count: int | None
    components: tuple[tuple[str, Decimal | None], ...]
    availability: str


@dataclass(frozen=True, slots=True)
class HistoryDepth:
    source_code: str
    history_kind: str
    earliest: date | None
    latest: date | None
    observation_count: int
    gap_count: int | None
    longest_gap_days: int | None
    evidence_basis: str


@dataclass(frozen=True, slots=True)
class LastActive:
    governor_id: int
    effective_utc_date: date
    history_start_date: date
    history_end_date: date
    last_active_date: date | None
    activity_state: LastActiveState
    qualifying_source_code: str | None
    qualifying_scan_order: int | None
    compared_complete_scans: int
    history_days: int


@dataclass(frozen=True, slots=True)
class LoadDiagnostics:
    cache_status: str
    total_ms: float
    stage_ms: tuple[tuple[str, float], ...] = ()
    result_rows: tuple[tuple[str, int], ...] = ()
    approximate_result_bytes: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True, slots=True)
class AliasRecord:
    governor_id: int
    governor_name: str
    first_seen: datetime | None
    last_seen: datetime | None
    seen_scan_count: int


@dataclass(frozen=True, slots=True)
class AllianceEpisode:
    governor_id: int
    sequence: int
    alliance: str
    first_observed: date | None
    last_observed: date | None
    observed_scans: int
    current: bool


@dataclass(frozen=True, slots=True)
class LinkedGovernor:
    governor_id: int
    governor_name: str
    current: bool = False


@dataclass(frozen=True, slots=True)
class KvkCandidate:
    kvk_no: int
    kvk_name: str | None
    registration_date: date | None
    start_date: date | None
    end_date: date | None
    matchmaking_scan: int | None
    kvk_end_scan: int | None
    matchmaking_start_date: date | None
    fighting_start_date: date | None
    pass4_start_scan: int | None
    final_data_at_utc: datetime | None
    final_scan_order: int | None
    final_output_state: str | None
    finalization_basis: str | None


@dataclass(frozen=True, slots=True)
class KvkPerformance:
    kvk_no: int
    kvk_name: str | None
    governor_id: int
    governor_name: str | None
    kvk_rank: int | None
    t4_t5_kills: int | None
    kill_target: int | None
    kill_target_percent: Decimal | None
    kill_points: int | None
    deads: int | None
    dead_target: int | None
    dead_target_percent: Decimal | None
    healed: int | None
    kp_loss: int | None
    tanking_score: Decimal | None
    acclaim: int | None
    dkp: int | None
    dkp_target: int | None
    dkp_target_percent: Decimal | None
    prekvk_points: int | None
    prekvk_rank: int | None
    honor_points: int | None
    honor_rank: int | None
    exempt: bool
    engaged: bool
    healed_rank: int | None
    tanking_rank: int | None
    engaged_cohort_count: int | None
    tanking_cohort_count: int | None
    final_data_at_utc: datetime | None
    final_output_state: str | None
    finalization_basis: str | None
    personal_completed_kvk_best_acclaim: int | None = None


@dataclass(frozen=True, slots=True)
class LeadershipPlayerPayload:
    header: ReviewHeader
    freshness: FreshnessState
    period_days: int
    page: ReviewPage
    presence: tuple[ScanPresence, ...]
    coverage: tuple[SourceCoverage, ...]
    metrics: tuple[ActivityMetric, ...]
    activity_index: ActivityIndex
    history_depth: tuple[HistoryDepth, ...]
    aliases: tuple[AliasRecord, ...]
    alliance_episodes: tuple[AllianceEpisode, ...]
    linked_governors: tuple[LinkedGovernor, ...]
    kvk_rows: tuple[KvkPerformance, ...]
    prompts: tuple[str, ...]
    warnings: tuple[str, ...]
    generated_at_utc: datetime
    record_page: int = 0
    last_active: LastActive | None = None
    diagnostics: LoadDiagnostics | None = None

    @property
    def current_presence(self) -> ScanPresence | None:
        return next((row for row in self.presence if row.window == "CURRENT"), None)

    @property
    def latest_kvk(self) -> KvkPerformance | None:
        return self.kvk_rows[0] if self.kvk_rows else None
