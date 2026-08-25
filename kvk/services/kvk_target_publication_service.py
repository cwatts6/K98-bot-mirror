from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from kvk.models.kvk_target_publication import (
    TargetPublicationDisplay,
    TargetPublicationMetadata,
    TargetPublicationResolution,
)

DRAFT_SOURCE_CONFIRMED = "draft_source_confirmed"
MATCHMAKING_SOURCE_CONFIRMED = "matchmaking_source_confirmed"
OFFICIAL_PUBLICATION_KVK_ENDED = "official_publication_kvk_ended"
MISSING_PUBLICATION_METADATA = "missing_publication_metadata"
PUBLICATION_KVK_MISMATCH = "publication_kvk_mismatch"
MISSING_SOURCE_SCAN = "missing_source_scan"
INVALID_SOURCE_TYPE = "invalid_source_type"
MATCHMAKING_SCAN_MISMATCH = "matchmaking_scan_mismatch"
DRAFT_SCAN_MISMATCH = "draft_scan_mismatch"
ROW_COUNT_MISMATCH = "row_count_mismatch"
PUBLICATION_STATE_MISMATCH = "publication_state_mismatch"
INVALID_PUBLICATION_IDENTITY = "invalid_publication_identity"
OUTPUT_OBJECT_MISMATCH = "output_object_mismatch"
LEGACY_CACHE_UNVERIFIED = "legacy_cache_unverified"
PUBLICATION_READ_FAILED = "publication_read_failed"
CACHE_ROW_INVALID = "cache_row_invalid"


def target_publication_display(
    state: str | None,
    *,
    source_scan_order: int | None = None,
) -> TargetPublicationDisplay:
    normalized = str(state or "").strip().upper()
    scan = _optional_int(source_scan_order)
    if scan is None or scan <= 0:
        return TargetPublicationDisplay(
            state="UNKNOWN",
            label="Unverified",
            source_text="Target source scan could not be verified.",
            warning_text="Do not treat this target set as Official.",
        )
    scan_text = f"scan {scan}"
    if normalized == "DRAFT":
        return TargetPublicationDisplay(
            state="DRAFT",
            label="Draft",
            source_text=f"Draft target set from {scan_text}.",
            warning_text="Draft targets may still change.",
        )
    if normalized == "OFFICIAL":
        return TargetPublicationDisplay(
            state="OFFICIAL",
            label="Official",
            source_text=f"Fixed from exact matchmaking {scan_text}.",
        )
    if normalized == "HISTORIC":
        return TargetPublicationDisplay(
            state="HISTORIC",
            label="Historical",
            source_text=f"Historical official set from matchmaking {scan_text}.",
        )
    return TargetPublicationDisplay(
        state="UNKNOWN",
        label="Unverified",
        source_text="Target source scan could not be verified.",
        warning_text="Do not treat this target set as Official.",
    )


def _first(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping:
            return mapping.get(key)
    return None


def _optional_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


def _optional_datetime_utc(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _optional_signature(value: Any) -> str | None:
    if value in (None, ""):
        return None
    try:
        return str(UUID(str(value).strip()))
    except (ValueError, TypeError, AttributeError):
        return None


def _optional_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def parse_target_publication_metadata(
    mapping: Mapping[str, Any] | None,
) -> TargetPublicationMetadata | None:
    if not isinstance(mapping, Mapping):
        return None
    return TargetPublicationMetadata(
        publication_id=_optional_int(_first(mapping, "PublicationId", "publication_id")),
        kvk_no=_optional_int(_first(mapping, "KVK_NO", "kvk_no")),
        publication_state=_optional_text(
            _first(
                mapping,
                "PublicationState",
                "persisted_publication_state",
                "publication_state",
            )
        ),
        source_scan_order=_optional_int(
            _first(mapping, "SourceScanOrder", "target_source_scan", "source_scan_order")
        ),
        source_scan_type=_optional_text(
            _first(mapping, "SourceScanType", "target_source_type", "source_scan_type")
        ),
        configured_draft_scan=_optional_int(
            _first(mapping, "ConfiguredDraftScan", "configured_draft_scan")
        ),
        configured_matchmaking_scan=_optional_int(
            _first(mapping, "ConfiguredMatchmakingScan", "configured_matchmaking_scan")
        ),
        published_at_utc=_optional_datetime_utc(
            _first(mapping, "PublishedAtUtc", "target_published_at", "published_at_utc")
        ),
        target_row_count=_optional_int(_first(mapping, "TargetRowCount", "target_row_count")),
        output_object_name=_optional_text(
            _first(mapping, "OutputObjectName", "output_object_name")
        ),
        publication_version=_optional_int(
            _first(mapping, "PublicationVersion", "publication_version")
        ),
        publication_signature=_optional_signature(
            _first(mapping, "PublicationSignature", "publication_signature")
        ),
    )


def resolve_target_publication_state(
    metadata: TargetPublicationMetadata | None,
    *,
    requested_kvk_no: int | None,
    fighting_state: str | None,
    observed_row_count: int | None = None,
) -> TargetPublicationResolution:
    if metadata is None:
        return TargetPublicationResolution("UNKNOWN", MISSING_PUBLICATION_METADATA)

    if requested_kvk_no is None or requested_kvk_no <= 0 or metadata.kvk_no != requested_kvk_no:
        return TargetPublicationResolution("UNKNOWN", PUBLICATION_KVK_MISMATCH)

    if (
        metadata.publication_id is None
        or metadata.publication_id <= 0
        or metadata.publication_version is None
        or metadata.publication_version <= 0
        or not metadata.publication_signature
        or metadata.published_at_utc is None
    ):
        return TargetPublicationResolution("UNKNOWN", INVALID_PUBLICATION_IDENTITY)

    if metadata.source_scan_order is None or metadata.source_scan_order <= 0:
        return TargetPublicationResolution("UNKNOWN", MISSING_SOURCE_SCAN)

    if metadata.target_row_count is None or metadata.target_row_count <= 0:
        return TargetPublicationResolution("UNKNOWN", ROW_COUNT_MISMATCH)
    if observed_row_count is not None and observed_row_count != metadata.target_row_count:
        return TargetPublicationResolution("UNKNOWN", ROW_COUNT_MISMATCH)

    expected_output = f"dbo.EXCEL_EXPORT_KVK_TARGETS_{metadata.kvk_no}"
    if metadata.output_object_name != expected_output:
        return TargetPublicationResolution("UNKNOWN", OUTPUT_OBJECT_MISMATCH)

    source_type = (metadata.source_scan_type or "").upper()
    persisted_state = (metadata.publication_state or "").upper()

    if source_type == "DRAFTSCAN":
        if persisted_state != "DRAFT":
            return TargetPublicationResolution("UNKNOWN", PUBLICATION_STATE_MISMATCH)
        if (
            metadata.configured_draft_scan is None
            or metadata.configured_draft_scan <= 0
            or metadata.source_scan_order > metadata.configured_draft_scan
        ):
            return TargetPublicationResolution("UNKNOWN", DRAFT_SCAN_MISMATCH)
        return TargetPublicationResolution("DRAFT", DRAFT_SOURCE_CONFIRMED)

    if source_type == "MATCHMAKING_SCAN":
        if persisted_state != "OFFICIAL":
            return TargetPublicationResolution("UNKNOWN", PUBLICATION_STATE_MISMATCH)
        if (
            metadata.configured_matchmaking_scan is None
            or metadata.configured_matchmaking_scan <= 0
            or metadata.source_scan_order != metadata.configured_matchmaking_scan
        ):
            return TargetPublicationResolution("UNKNOWN", MATCHMAKING_SCAN_MISMATCH)
        if (fighting_state or "").upper() == "ENDED":
            return TargetPublicationResolution("HISTORIC", OFFICIAL_PUBLICATION_KVK_ENDED)
        return TargetPublicationResolution("OFFICIAL", MATCHMAKING_SOURCE_CONFIRMED)

    return TargetPublicationResolution("UNKNOWN", INVALID_SOURCE_TYPE)


def metadata_to_cache_fields(metadata: TargetPublicationMetadata) -> dict[str, Any]:
    return {
        "publication_id": metadata.publication_id,
        "kvk_no": metadata.kvk_no,
        "persisted_publication_state": metadata.publication_state,
        "target_source_scan": metadata.source_scan_order,
        "target_source_type": metadata.source_scan_type,
        "configured_draft_scan": metadata.configured_draft_scan,
        "configured_matchmaking_scan": metadata.configured_matchmaking_scan,
        "target_published_at": (
            metadata.published_at_utc.astimezone(UTC).isoformat()
            if metadata.published_at_utc is not None
            else None
        ),
        "target_row_count": metadata.target_row_count,
        "output_object_name": metadata.output_object_name,
        "publication_version": metadata.publication_version,
        "publication_signature": metadata.publication_signature,
    }
