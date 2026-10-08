from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from kvk.models.kvk_target_row import TargetRow

TargetPublicationState = Literal["DRAFT", "OFFICIAL", "HISTORIC", "UNKNOWN"]
PersistedTargetPublicationState = Literal["DRAFT", "OFFICIAL"]
TargetSourceType = Literal["DRAFTSCAN", "MATCHMAKING_SCAN"]


@dataclass(frozen=True)
class TargetPublicationMetadata:
    publication_id: int | None
    kvk_no: int | None
    publication_state: str | None
    source_scan_order: int | None
    source_scan_type: str | None
    configured_draft_scan: int | None
    configured_matchmaking_scan: int | None
    published_at_utc: datetime | None
    target_row_count: int | None
    output_object_name: str | None
    publication_version: int | None
    publication_signature: str | None

    @property
    def cache_identity(self) -> tuple[int, int, str] | None:
        if (
            self.kvk_no is None
            or self.publication_version is None
            or not self.publication_signature
        ):
            return None
        return (self.kvk_no, self.publication_version, self.publication_signature)


@dataclass(frozen=True)
class TargetPublicationResolution:
    state: TargetPublicationState
    reason: str

    @property
    def is_verified(self) -> bool:
        return self.state != "UNKNOWN"


@dataclass(frozen=True, slots=True)
class TargetPublicationSnapshot:
    metadata: TargetPublicationMetadata
    rows: tuple[TargetRow, ...]


@dataclass(frozen=True)
class TargetPublicationDisplay:
    state: TargetPublicationState
    label: str
    source_text: str
    warning_text: str | None = None
