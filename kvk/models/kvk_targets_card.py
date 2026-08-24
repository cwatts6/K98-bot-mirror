from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from io import BytesIO


@dataclass(frozen=True)
class KvkTargetMetricProgress:
    label: str
    current: int | None
    target: int | None
    percent: float | None
    remaining: int | None
    note: str | None = None

    @property
    def has_target(self) -> bool:
        return bool(self.target and self.target > 0)

    @property
    def is_complete(self) -> bool:
        return (
            self.has_target and self.current is not None and self.current >= int(self.target or 0)
        )


@dataclass(frozen=True)
class KvkTargetsCardPayload:
    governor_id: str
    governor_name: str
    kvk_no: int | None
    kvk_name: str | None
    camp_name: str | None
    target_state: str
    status_label: str
    status_detail: str
    next_action: str
    power: int | None
    metrics: tuple[KvkTargetMetricProgress, ...]
    last_refreshed: str | None = None
    source_state: str | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)
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

    @property
    def completion_percent(self) -> float | None:
        percentages = [m.percent for m in self.metrics if m.has_target and m.percent is not None]
        if not percentages:
            return None
        return min(percentages)


@dataclass(frozen=True)
class RenderedKvkTargetsCard:
    filename: str
    image_bytes: BytesIO
