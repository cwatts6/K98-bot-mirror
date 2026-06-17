from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class KvkHistoryRow:
    kvk_no: int
    row_present: bool
    kvk_rank: int | None = None
    kingdom_rank: int | None = None
    kills: int | None = None
    kill_target_percent: float | None = None
    deads: int | None = None
    dead_target_percent: float | None = None
    dkp: int | None = None
    dkp_target_percent: float | None = None
    acclaim: int | None = None


@dataclass(frozen=True)
class KvkHistoryTrend:
    metric: str
    average: float | None
    direction: str
    first_value: float | None = None
    last_value: float | None = None
    value_count: int = 0


@dataclass(frozen=True)
class KvkHistoryPayload:
    governor_id: str
    governor_name: str
    started_kvks: tuple[int, ...]
    last3_kvks: tuple[int, ...]
    rows: tuple[KvkHistoryRow, ...]
    last3_rows: tuple[KvkHistoryRow, ...]
    history_summary: dict[str, int | None] = field(default_factory=dict)
    trends: dict[str, KvkHistoryTrend] = field(default_factory=dict)
    generated_at_utc: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def has_history(self) -> bool:
        return any(row.row_present for row in self.rows)
