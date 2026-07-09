"""Typed contracts for the future /me governor dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

GovernorDashboardViewerMode = Literal["self", "inspect"]
GovernorDashboardResolutionState = Literal[
    "unavailable",
    "requires_setup",
    "requires_selection",
    "selected",
    "denied",
]


@dataclass(frozen=True, slots=True)
class GovernorDashboardOption:
    governor_id: int
    governor_id_str: str
    governor_name: str
    account_type: str
    is_default: bool = False


@dataclass(frozen=True, slots=True)
class GovernorDashboardAccessDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class GovernorDashboardContext:
    viewer_discord_id: int
    viewer_mode: GovernorDashboardViewerMode
    selected_governor_id: int | None
    selected_governor_name: str | None
    is_linked_to_viewer: bool
    account_type_for_self_view: str | None
    access_decision: GovernorDashboardAccessDecision
    privacy_profile: str

    @property
    def access_allowed(self) -> bool:
        return self.access_decision.allowed


@dataclass(frozen=True, slots=True)
class GovernorDashboardResolution:
    state: GovernorDashboardResolutionState
    options: tuple[GovernorDashboardOption, ...]
    context: GovernorDashboardContext | None = None
    default_option: GovernorDashboardOption | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class GovernorDashboardSelfView:
    account_type: str | None
    vip_level_label: str | None


@dataclass(frozen=True, slots=True)
class GovernorDashboardIdentity:
    governor_name: str
    governor_id: int
    alliance: str | None = None
    civilisation: str | None = None


@dataclass(frozen=True, slots=True)
class GovernorDashboardLatestMetrics:
    power: int | None = None
    kill_points: int | None = None
    dead: int | None = None
    helps: int | None = None
    healed: int | None = None


@dataclass(frozen=True, slots=True)
class GovernorDashboardHistoricalHighlights:
    highest_acclaim: int | None = None
    times_named_autarch: int | None = None


@dataclass(frozen=True, slots=True)
class GovernorDashboardActivityHonours:
    ark_joined: int | None = None
    ark_won: int | None = None
    ark_win_ratio: float | None = None
    ark_win_ratio_label: str = "N/A"


@dataclass(frozen=True, slots=True)
class GovernorDashboardProfileStatus:
    conduct_score: float | None = None
    conduct_source_field: str = "Conduct"
    conduct_label: str = "Conduct Score"
    civilisation_source_field: str = "Civilization"
    civilisation_label: str = "Civilisation"


@dataclass(frozen=True, slots=True)
class GovernorDashboardFreshness:
    updated_at_utc: Any | None = None
    scan_order: int | None = None
    source: str | None = None


@dataclass(frozen=True, slots=True)
class GovernorDashboardDataRow:
    governor_id: int
    governor_name: str | None = None
    alliance: str | None = None
    power: int | None = None
    kill_points: int | None = None
    dead: int | None = None
    helps: int | None = None
    healed: int | None = None
    highest_acclaim: int | None = None
    ark_joined: int | None = None
    ark_won: int | None = None
    times_named_autarch: int | None = None
    conduct: float | None = None
    civilization: str | None = None
    updated_at_utc: Any | None = None
    scan_order: int | None = None


@dataclass(frozen=True, slots=True)
class GovernorDashboardPayload:
    context: GovernorDashboardContext
    identity: GovernorDashboardIdentity
    latest_metrics: GovernorDashboardLatestMetrics
    historical_highlights: GovernorDashboardHistoricalHighlights
    activity_honours: GovernorDashboardActivityHonours
    profile_status: GovernorDashboardProfileStatus
    freshness: GovernorDashboardFreshness
    available_actions: tuple[str, ...]
    missing_fields: tuple[str, ...]
    self_view: GovernorDashboardSelfView | None = None
