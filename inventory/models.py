from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class InventoryImportType(StrEnum):
    RESOURCES = "resources"
    SPEEDUPS = "speedups"
    MATERIALS = "materials"
    UNKNOWN = "unknown"


class InventoryImportStatus(StrEnum):
    AWAITING_UPLOAD = "awaiting_upload"
    ANALYSED = "analysed"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    FAILED = "failed"


class InventoryFlowType(StrEnum):
    COMMAND = "command"
    UPLOAD_FIRST = "upload_first"


class InventoryReportView(StrEnum):
    RESOURCES = "resources"
    SPEEDUPS = "speedups"
    ALL = "all"


class InventoryReportRange(StrEnum):
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    TWELVE_MONTHS = "12M"


class InventoryReportVisibility(StrEnum):
    ONLY_ME = "only_me"
    PUBLIC = "public"


class InventoryExportFormat(StrEnum):
    EXCEL = "excel"
    CSV = "csv"
    GOOGLE_SHEETS = "google_sheets"


class InventoryAuditStatus(StrEnum):
    ALL = "all"
    AWAITING_UPLOAD = "awaiting_upload"
    ANALYSED = "analysed"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True)
class RegisteredGovernor:
    governor_id: int
    governor_name: str
    account_type: str


@dataclass(frozen=True)
class InventoryImagePayload:
    image_bytes: bytes
    filename: str
    content_type: str | None = None
    source_message_id: int | None = None
    source_channel_id: int | None = None
    image_attachment_url: str | None = None


@dataclass(frozen=True)
class InventoryAnalysisSummary:
    ok: bool
    import_type: InventoryImportType
    values: dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    warnings: list[str] = field(default_factory=list)
    model: str = ""
    prompt_version: str = ""
    fallback_used: bool = False
    error: str | None = None
    raw_json: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InventoryValidationResult:
    ok: bool
    warnings: list[str] = field(default_factory=list)
    error: str | None = None
    extreme_change: bool = False


@dataclass(frozen=True)
class InventoryResourcePoint:
    scan_utc: Any
    food: int
    wood: int
    stone: int
    gold: int

    @property
    def total(self) -> int:
        return int(self.food) + int(self.wood) + int(self.stone) + int(self.gold)


@dataclass(frozen=True)
class InventorySpeedupPoint:
    scan_utc: Any
    building_days: float
    research_days: float
    training_days: float
    healing_days: float
    universal_days: float


@dataclass(frozen=True)
class InventoryReportPayload:
    governor_id: int
    governor_name: str
    view: InventoryReportView
    range_key: InventoryReportRange
    resources: list[InventoryResourcePoint] = field(default_factory=list)
    speedups: list[InventorySpeedupPoint] = field(default_factory=list)
    generated_at_utc: Any | None = None


@dataclass(frozen=True)
class InventoryExportFile:
    path: Path
    filename: str
    format: InventoryExportFormat
    row_count: int
    governor_ids: tuple[int, ...]


@dataclass(frozen=True)
class InventoryAuditRecord:
    import_batch_id: int
    governor_id: int
    discord_user_id: int
    import_type: str | None
    flow_type: str
    status: str
    created_at_utc: Any
    approved_at_utc: Any | None = None
    rejected_at_utc: Any | None = None
    confidence_score: float | None = None
    vision_model: str | None = None
    fallback_used: bool = False
    admin_debug_channel_id: int | None = None
    admin_debug_message_id: int | None = None
    warnings: list[str] = field(default_factory=list)
    detected_json: dict[str, Any] | None = None
    corrected_json: dict[str, Any] | None = None
    final_json: dict[str, Any] | None = None
    error_json: dict[str, Any] | None = None

    @property
    def debug_reference(self) -> str:
        if self.admin_debug_channel_id and self.admin_debug_message_id:
            return f"<#{self.admin_debug_channel_id}> / `{self.admin_debug_message_id}`"
        return "none"
