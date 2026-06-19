from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from io import BytesIO
from typing import Any

PRIMARY_RANKING_LIMITS = (10, 25, 50)
HALL_OF_FAME_RECORD_LIMIT = 10
CURRENT_RANKING_MODES = ("kvk", "honor", "prekvk")


class HallOfFameMetric(StrEnum):
    KILLS = "kills"
    KILL_POINTS = "killpoints"
    DEADS = "deads"
    DKP = "dkp"
    HEALED = "healed"
    ACCLAIM = "acclaim"
    HONOR = "honor"
    PREKVK = "prekvk"


HALL_OF_FAME_METRIC_LABELS: dict[HallOfFameMetric, str] = {
    HallOfFameMetric.KILLS: "Kills",
    HallOfFameMetric.KILL_POINTS: "KillPoints",
    HallOfFameMetric.DEADS: "Deads",
    HallOfFameMetric.DKP: "DKP",
    HallOfFameMetric.HEALED: "Healed",
    HallOfFameMetric.ACCLAIM: "Acclaim",
    HallOfFameMetric.HONOR: "Honor",
    HallOfFameMetric.PREKVK: "PreKvK",
}


@dataclass(frozen=True)
class RankingRow:
    rank: int
    governor_id: int
    governor_name: str
    value: int | float
    kvk_no: int | None = None
    kvk_name: str | None = None
    supporting_values: dict[str, int | float | str | None] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RankingPayload:
    mode: str
    metric: str
    metric_label: str
    limit: int
    rows: list[RankingRow] = field(default_factory=list)
    generated_at_utc: datetime = field(default_factory=lambda: datetime.now(UTC))
    source_note: str | None = None
    source_state: str = "fresh"
    mode_label: str | None = None
    kvk_no: int | None = None
    freshness_label: str | None = None
    filters: tuple[str, ...] = ()
    page: int = 1
    total_pages: int = 1
    total_rows: int | None = None
    empty_message: str | None = None


@dataclass(frozen=True)
class RenderedRankingCard:
    filename: str
    image_bytes: BytesIO


@dataclass(frozen=True)
class RankingAccountChoice:
    slot: str
    governor_id: int
    governor_id_str: str
    governor_name: str


@dataclass(frozen=True)
class MyRankLookupResult:
    status: str
    mode: str
    metric: str
    metric_label: str
    mode_label: str
    message: str
    payload: RankingPayload | None = None
    row: RankingRow | None = None
    row_above: RankingRow | None = None
    row_below: RankingRow | None = None
    governor_id: int | None = None
    governor_name: str | None = None
    account_choices: tuple[RankingAccountChoice, ...] = ()
    total_rows: int | None = None
    gap_to_next_value: int | float | None = None
