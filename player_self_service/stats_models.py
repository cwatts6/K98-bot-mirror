"""Discord-free typed contracts for private personal period performance."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum


class StatsMode(StrEnum):
    OVERVIEW = "overview"
    ACTIVITY = "activity"
    COMBAT = "combat"

    @property
    def label(self) -> str:
        return self.value.title()


class StatsPeriod(StrEnum):
    YESTERDAY = "yesterday"
    THIS_WEEK = "this_week"
    LAST_WEEK = "last_week"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    LAST_90_DAYS = "last_90_days"
    LAST_180_DAYS = "last_180_days"

    @property
    def label(self) -> str:
        return {
            self.YESTERDAY: "Yesterday",
            self.THIS_WEEK: "This Week",
            self.LAST_WEEK: "Last Week",
            self.THIS_MONTH: "This Month",
            self.LAST_MONTH: "Last Month",
            self.LAST_90_DAYS: "Last 90 Days",
            self.LAST_180_DAYS: "Last 180 Days",
        }[self]


class StatsScopeType(StrEnum):
    SELECTED = "selected"
    ALL_LINKED = "all_linked"


class StatsResultState(StrEnum):
    READY = "READY"
    PARTIAL = "PARTIAL"
    NO_DATA = "NO DATA"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class StatsWindow:
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise ValueError("Stats window end cannot precede its start")

    @property
    def expected_days(self) -> int:
        return (self.end_date - self.start_date).days + 1


@dataclass(frozen=True, slots=True)
class StatsGovernorOption:
    governor_id: int
    governor_name: str
    slot: str
    is_main: bool = False

    def __post_init__(self) -> None:
        if self.governor_id <= 0:
            raise ValueError("Governor ID must be positive")


@dataclass(frozen=True, slots=True)
class PersonalStatsHeader:
    stats_anchor_date: date | None
    window_start_date: date | None
    window_end_date: date | None
    requested_governor_count: int


@dataclass(frozen=True, slots=True)
class PersonalStatsDailyRow:
    governor_id: int
    as_of_date: date
    has_stats: bool
    previous_stats_date: date | None = None
    power_value: int | None = None
    troop_power_value: int | None = None
    power_delta: int | None = None
    troop_power_delta: int | None = None
    kill_points_delta: int | None = None
    rss_gathered_delta: int | None = None
    rss_assist_delta: int | None = None
    helps_delta: int | None = None
    t4_kills_delta: int | None = None
    t5_kills_delta: int | None = None
    deads_delta: int | None = None
    healed_troops_delta: int | None = None
    has_alliance_activity: bool = False
    previous_activity_date: date | None = None
    build_activity_delta: int | None = None
    tech_donations_delta: int | None = None
    has_forts: bool = False
    forts_total: int | None = None
    forts_launched: int | None = None
    forts_joined: int | None = None


@dataclass(frozen=True, slots=True)
class PersonalStatsDataSet:
    header: PersonalStatsHeader
    rows: tuple[PersonalStatsDailyRow, ...]


@dataclass(frozen=True, slots=True)
class StatsDailyPoint:
    reporting_date: date
    value: int


@dataclass(frozen=True, slots=True)
class StatsMetricSummary:
    total: int | None
    reporting_days: int
    expected_days: int
    daily: tuple[StatsDailyPoint, ...] = ()
    peak_date: date | None = None
    peak_value: int | None = None

    @property
    def average_per_reporting_day(self) -> float | None:
        if self.total is None or self.reporting_days <= 0:
            return None
        return self.total / self.reporting_days


@dataclass(frozen=True, slots=True)
class StatsCoverage:
    expected_dates: int
    stats_reporting_dates: int
    requested_governors: int
    stats_reporting_governors: int
    expected_account_days: int
    stats_account_days: int
    activity_account_days: int
    fort_account_days: int


@dataclass(frozen=True, slots=True)
class PersonalStatsMetrics:
    power_change: StatsMetricSummary
    troop_power_change: StatsMetricSummary
    rss_gathered: StatsMetricSummary
    rss_assisted: StatsMetricSummary
    helps: StatsMetricSummary
    build_activity: StatsMetricSummary
    tech_donations: StatsMetricSummary
    forts_total: StatsMetricSummary
    forts_launched: StatsMetricSummary
    forts_joined: StatsMetricSummary
    kill_points: StatsMetricSummary
    t4_kills: StatsMetricSummary
    t5_kills: StatsMetricSummary
    t4_t5_kills: StatsMetricSummary
    deads: StatsMetricSummary
    healed_troops: StatsMetricSummary
    period_end_power: int | None = None
    period_end_troop_power: int | None = None
    period_end_date: date | None = None

    def summaries(self) -> tuple[StatsMetricSummary, ...]:
        return (
            self.power_change,
            self.troop_power_change,
            self.rss_gathered,
            self.rss_assisted,
            self.helps,
            self.build_activity,
            self.tech_donations,
            self.forts_total,
            self.forts_launched,
            self.forts_joined,
            self.kill_points,
            self.t4_kills,
            self.t5_kills,
            self.t4_t5_kills,
            self.deads,
            self.healed_troops,
        )


@dataclass(frozen=True, slots=True)
class PersonalStatsPayload:
    discord_user_id: int
    period: StatsPeriod
    window: StatsWindow
    stats_anchor_date: date
    scope_type: StatsScopeType
    scope_governor_ids: tuple[int, ...]
    scope_label: str
    governor_options: tuple[StatsGovernorOption, ...]
    duplicate_id_warning: bool
    registry_fingerprint: tuple[tuple[str, int], ...]
    coverage: StatsCoverage
    state: StatsResultState
    metrics: PersonalStatsMetrics
    data_refreshed_at_utc: datetime
    generated_at_utc: datetime

    def __post_init__(self) -> None:
        if self.data_refreshed_at_utc.tzinfo is None:
            raise ValueError("Stats data_refreshed_at_utc must be timezone-aware")
        if self.generated_at_utc.tzinfo is None:
            raise ValueError("Stats generated_at_utc must be timezone-aware")
        if not self.scope_governor_ids:
            raise ValueError("Stats payload requires at least one authorized governor")

    @classmethod
    def now_utc(cls) -> datetime:
        return datetime.now(UTC)


class PersonalStatsAccessChanged(PermissionError):
    """Raised when an interaction no longer targets the current registry linkage."""


class PersonalStatsUnavailable(RuntimeError):
    """Raised when the registry, SQL contract, or required request dependency fails."""


class PersonalStatsNoAccounts(LookupError):
    """Raised when the invoking user has no valid canonical linked governors."""
