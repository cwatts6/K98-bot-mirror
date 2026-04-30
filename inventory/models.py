from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
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

