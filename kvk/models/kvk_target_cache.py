from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType

from kvk.models.kvk_target_publication import (
    TargetPublicationMetadata,
    TargetPublicationState,
)
from kvk.models.kvk_target_row import TargetRow


class TargetCacheRefreshOutcome(StrEnum):
    """Stable target-cache refresh outcomes for callers and operator telemetry."""

    REUSED = "REUSED"
    REFRESHED = "REFRESHED"
    RETAINED_LAST_KNOWN_GOOD = "RETAINED_LAST_KNOWN_GOOD"
    REJECTED_MISMATCH = "REJECTED_MISMATCH"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED_CLOSED = "FAILED_CLOSED"


@dataclass(frozen=True, slots=True)
class TargetCacheSnapshot:
    """One validated cache snapshot bound to one requested KVK context."""

    requested_kvk_no: int | None
    metadata: TargetPublicationMetadata | None
    rows: tuple[TargetRow, ...]
    publication_state: TargetPublicationState
    publication_reason: str
    cache_written_at_utc: str | None = None
    generated_at: str | None = None
    kvk_fighting_state: str | None = None
    kvk_fighting_state_reason: str | None = None
    by_governor: Mapping[str, TargetRow] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        rows_by_governor = {row.governor_id: row for row in self.rows}
        if len(rows_by_governor) != len(self.rows):
            raise ValueError("Target cache snapshot contains duplicate governor IDs.")
        object.__setattr__(self, "by_governor", MappingProxyType(rows_by_governor))

    @property
    def is_verified(self) -> bool:
        return self.metadata is not None and self.publication_state != "UNKNOWN"

    def target_for(self, governor_id: str) -> TargetRow | None:
        return self.by_governor.get(governor_id)


@dataclass(frozen=True, slots=True)
class TargetCacheRefreshResult:
    """Typed refresh decision plus the safe snapshot available to the caller."""

    outcome: TargetCacheRefreshOutcome
    snapshot: TargetCacheSnapshot
    reason: str
