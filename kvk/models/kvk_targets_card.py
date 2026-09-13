from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from io import BytesIO
from typing import Any

from kvk.models.kvk_target_row import TargetRow


@dataclass(frozen=True)
class KvkTargetMetricProgress:
    label: str
    current: int | None
    target: int | None
    percent: float | None
    remaining: int | None
    note: str | None = None
    comparison_target: int | None = None

    @property
    def has_target(self) -> bool:
        return bool(self.target and self.target > 0)

    @property
    def is_complete(self) -> bool:
        return (
            self.has_target
            and self.current is not None
            and self.current >= int(self.comparison_denominator or 0)
        )

    @property
    def comparison_denominator(self) -> int | None:
        """Target that applied to the historical value, falling back compatibly."""
        if self.comparison_target and self.comparison_target > 0:
            return self.comparison_target
        return self.target


@dataclass(frozen=True)
class KvkTargetsCardPayload:
    governor_id: str
    governor_name: str
    kvk_no: int | None
    kvk_name: str | None
    camp_name: str | None
    progress_state: str
    status_label: str
    status_detail: str
    next_action: str
    power: int | None
    metrics: tuple[KvkTargetMetricProgress, ...]
    min_kill_target: int | None = None
    last_refreshed: str | None = None
    publication_state: str = "UNKNOWN"
    publication_reason: str | None = None
    target_source_scan: int | None = None
    target_source_type: str | None = None
    target_published_at: str | None = None
    publication_version: int | None = None
    publication_signature: str | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)
    generated_at_utc: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def target_state(self) -> str:
        """Compatibility alias for the card's progress/status state."""
        return self.progress_state

    @property
    def source_state(self) -> str:
        """Compatibility alias for the target publication state."""
        return self.publication_state

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
class KvkTargetsPresentationInput:
    """Service-owned target result shared by modern and compatibility output paths."""

    payload: KvkTargetsCardPayload
    target_row: TargetRow | None = None
    last_kvk: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class RenderedKvkTargetsCard:
    filename: str
    image_bytes: BytesIO
