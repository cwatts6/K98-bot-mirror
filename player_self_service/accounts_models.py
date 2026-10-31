"""Typed contracts for the private Accounts portfolio and Account Summary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from kvk.combat_metrics import calculate_combat_metrics

AccountPortfolioState = Literal["READY", "REVIEW", "SETUP"]
AccountDataState = Literal["CURRENT", "STALE", "NO DATA", "UNRESOLVED"]
AccountSummarySection = Literal["overview", "combat", "economy"]
Numeric = int | Decimal


@dataclass(frozen=True, slots=True)
class AccountsScanRow:
    governor_id: int
    governor_name: str | None = None
    civilisation: str | None = None
    city_hall: int | None = None
    vip_level_code: str | None = None
    vip_level_label: str | None = None
    power: int | None = None
    troop_power: int | None = None
    kill_points: int | None = None
    t4_kills: int | None = None
    t5_kills: int | None = None
    deads: int | None = None
    healed_troops: int | None = None
    highest_acclaim: int | None = None
    helps: int | None = None
    rss_gathered: int | None = None
    rss_assistance: int | None = None
    conduct: Numeric | None = None
    location_x: int | None = None
    location_y: int | None = None
    scan_date: datetime | None = None
    latest_scan_date: datetime | None = None

    @property
    def t4_t5_kills(self) -> int | None:
        if self.t4_kills is None or self.t5_kills is None:
            return None
        return self.t4_kills + self.t5_kills


@dataclass(frozen=True, slots=True)
class AccountsInventoryPoint:
    governor_id: int
    total: int
    scan_utc: datetime


@dataclass(frozen=True, slots=True)
class AccountPortfolioRow:
    slot: str
    role: str
    registered_name: str
    governor_id: int | None
    current_governor_name: str | None = None
    civilisation: str | None = None
    city_hall: int | None = None
    vip_level: str | None = None
    power: int | None = None
    troop_power: int | None = None
    kill_points: int | None = None
    t4_kills: int | None = None
    t5_kills: int | None = None
    t4_t5_kills: int | None = None
    deads: int | None = None
    healed_troops: int | None = None
    highest_acclaim: int | None = None
    helps: int | None = None
    rss_gathered: int | None = None
    rss_assistance: int | None = None
    rss_total: int | None = None
    conduct: Numeric | None = None
    location_x: int | None = None
    location_y: int | None = None
    data_state: AccountDataState = "UNRESOLVED"
    last_governor_scan: datetime | None = None
    inventory_as_of: datetime | None = None
    duplicate_governor_id: bool = False

    @property
    def display_name(self) -> str:
        return self.current_governor_name or self.registered_name or "Unknown"

    @property
    def kp_loss(self) -> int | None:
        return calculate_combat_metrics(
            kill_points=self.kill_points,
            healed=self.healed_troops,
            deads=self.deads,
            t4_t5_kills=self.t4_t5_kills,
        ).kp_loss

    @property
    def tanking_score(self) -> Decimal | None:
        return calculate_combat_metrics(
            kill_points=self.kill_points,
            healed=self.healed_troops,
            deads=self.deads,
            t4_t5_kills=self.t4_t5_kills,
        ).tanking_score


@dataclass(frozen=True, slots=True)
class AccountMetricTotal:
    value: int | None
    reporting_count: int
    expected_count: int

    @property
    def has_full_coverage(self) -> bool:
        return self.expected_count > 0 and self.reporting_count == self.expected_count


@dataclass(frozen=True, slots=True)
class AccountsPortfolioPayload:
    discord_user_id: int
    state: AccountPortfolioState
    rows: tuple[AccountPortfolioRow, ...]
    linked_count: int
    main_row: AccountPortfolioRow | None
    role_counts: tuple[tuple[str, int], ...]
    power: AccountMetricTotal
    troop_power: AccountMetricTotal
    t4_t5_kills: AccountMetricTotal
    rss_total: AccountMetricTotal
    insight: str
    refreshed_at_utc: datetime
    latest_scan_date: datetime | None = None
    warnings: tuple[str, ...] = ()

    @property
    def has_linked_governors(self) -> bool:
        return bool(self.rows)


@dataclass(frozen=True, slots=True)
class AccountSummaryPage:
    payload: AccountsPortfolioPayload
    section: AccountSummarySection
    page: int
    page_count: int
    rows: tuple[AccountPortfolioRow, ...]
