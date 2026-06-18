from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


PRIMARY_RANKING_LIMITS = (10, 25, 50)
HALL_OF_FAME_RECORD_LIMIT = 10


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
