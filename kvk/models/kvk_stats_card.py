from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from io import BytesIO


@dataclass(frozen=True)
class KvkStatsCardContext:
    kvk_name: str | None = None
    kingdom: int | None = None
    camp_id: int | None = None
    camp_name: str | None = None


@dataclass(frozen=True)
class KvkTargetProgress:
    current: int
    target: int
    percent: float | None
    color_hex: str
    quote: str
    is_exempt: bool = False


@dataclass(frozen=True)
class KvkStatsCardPayload:
    governor_id: str
    governor_name: str
    kvk_no: int | None
    kvk_name: str | None
    kingdom: int | None
    camp_name: str | None
    last_refresh: str | None
    status: str
    kvk_rank: int | str | None
    matchmaking_power: int | None
    kp_gain: int
    kills_gain: int
    kill_target: int
    kill_progress: KvkTargetProgress
    deads: int
    dead_target: int
    dead_target_percent: float | None
    power_loss: int | None
    healed: int | None
    kp_loss: int | None
    tanking_score_percent: float | None
    playstyle: str | None
    acclaim: int
    dkp: int
    dkp_target: int
    dkp_target_percent: float | None
    kingdom_rank: int | str | None = None
    pass_stats: dict[str, int] = field(default_factory=dict)
    prekvk_rank: int | None = None
    prekvk_points: int | None = None
    honor_rank: int | None = None
    honor_points: int | None = None
    history_summary: dict[str, int] = field(default_factory=dict)
    personal_bests: dict[str, int] = field(default_factory=dict)
    last_kvk_summary: dict[str, int | float | str | None] = field(default_factory=dict)
    matchmaking_snapshot: dict[str, int] = field(default_factory=dict)
    generated_at_utc: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def display_kvk_label(self) -> str:
        if self.kvk_no:
            return f"KVK {self.kvk_no}"
        return "Current KVK"

    @property
    def display_mode(self) -> str:
        return self.kvk_name or "KVK"

    @property
    def display_camp(self) -> str | None:
        return self.camp_name.strip() if self.camp_name else None


@dataclass(frozen=True)
class RenderedKvkStatsCard:
    filename: str
    image_bytes: BytesIO
