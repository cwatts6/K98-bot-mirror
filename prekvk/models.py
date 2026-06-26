from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from io import BytesIO
from typing import Any


class PreKvkReportSort(StrEnum):
    OVERALL = "overall"
    STAGE1 = "stage1"
    STAGE2 = "stage2"
    STAGE3 = "stage3"


PREKVK_REPORT_LIMITS = (10, 25, 50, 100)
PREKVK_PRIMARY_REPORT_LIMITS = (10, 25, 50)


@dataclass(frozen=True)
class PreKvkReportRow:
    rank: int
    governor_id: int
    governor_name: str
    power: int | None
    stage1_points: int | None
    stage2_points: int | None
    stage3_points: int | None
    overall_points: int


@dataclass(frozen=True)
class PreKvkReportPayload:
    kvk_no: int
    sort_by: PreKvkReportSort
    limit: int
    rows: list[PreKvkReportRow] = field(default_factory=list)
    scan_id: int | None = None
    scan_timestamp_utc: Any | None = None
    source_filename: str | None = None
    generated_at_utc: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def has_stage_data(self) -> bool:
        return any(
            row.stage1_points is not None
            or row.stage2_points is not None
            or row.stage3_points is not None
            for row in self.rows
        )


@dataclass(frozen=True)
class PreKvkScheduledTopEntry:
    name: str
    points: int


@dataclass(frozen=True)
class PreKvkScheduledTopBlocks:
    overall: list[PreKvkScheduledTopEntry] = field(default_factory=list)
    p1: list[PreKvkScheduledTopEntry] = field(default_factory=list)
    p2: list[PreKvkScheduledTopEntry] = field(default_factory=list)
    p3: list[PreKvkScheduledTopEntry] = field(default_factory=list)


@dataclass(frozen=True)
class PreKvkScheduledSummary:
    kvk_no: int
    current: PreKvkScheduledTopBlocks = field(default_factory=PreKvkScheduledTopBlocks)
    previous_kvk_no: int | None = None
    previous: PreKvkScheduledTopBlocks = field(default_factory=PreKvkScheduledTopBlocks)
    generated_at_utc: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class RenderedPreKvkReportImage:
    filename: str
    image_bytes: BytesIO
