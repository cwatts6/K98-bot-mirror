from __future__ import annotations

import asyncio
import logging
from typing import Any

from inventory.dal import inventory_audit_dal
from inventory.models import InventoryAuditRecord, InventoryAuditStatus, InventoryImportType

logger = logging.getLogger(__name__)


def parse_audit_status(value: str | None) -> InventoryAuditStatus:
    normalized = (value or InventoryAuditStatus.ALL.value).strip().lower()
    try:
        return InventoryAuditStatus(normalized)
    except ValueError as exc:
        raise ValueError("Audit status must be All, Awaiting Upload, Analysed, Approved, Rejected, Cancelled, or Failed.") from exc


def parse_audit_import_type(value: str | None) -> InventoryImportType | None:
    normalized = (value or "all").strip().lower()
    if normalized == "all":
        return None
    try:
        return InventoryImportType(normalized)
    except ValueError as exc:
        raise ValueError("Audit import type must be All, Resources, Speedups, Materials, or Unknown.") from exc


def _json_dict(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _warnings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def _record_from_row(row: dict[str, Any]) -> InventoryAuditRecord:
    return InventoryAuditRecord(
        import_batch_id=int(row["ImportBatchID"]),
        governor_id=int(row["GovernorID"]),
        discord_user_id=int(row["DiscordUserID"]),
        import_type=row.get("ImportType"),
        flow_type=str(row.get("FlowType") or ""),
        status=str(row.get("Status") or ""),
        created_at_utc=row.get("CreatedAtUtc"),
        approved_at_utc=row.get("ApprovedAtUtc"),
        rejected_at_utc=row.get("RejectedAtUtc"),
        confidence_score=(
            float(row["ConfidenceScore"]) if row.get("ConfidenceScore") is not None else None
        ),
        vision_model=row.get("VisionModel"),
        fallback_used=bool(row.get("FallbackUsed")),
        admin_debug_channel_id=(
            int(row["AdminDebugChannelID"]) if row.get("AdminDebugChannelID") else None
        ),
        admin_debug_message_id=(
            int(row["AdminDebugMessageID"]) if row.get("AdminDebugMessageID") else None
        ),
        warnings=_warnings(row.get("WarningJson")),
        detected_json=_json_dict(row.get("DetectedJson")),
        corrected_json=_json_dict(row.get("CorrectedJson")),
        final_json=_json_dict(row.get("FinalJson")),
        error_json=_json_dict(row.get("ErrorJson")),
    )


async def fetch_inventory_audit(
    *,
    status: InventoryAuditStatus,
    import_type: InventoryImportType | None = None,
    governor_id: int | None = None,
    discord_user_id: int | None = None,
    lookback_days: int = 30,
    limit: int = 10,
) -> list[InventoryAuditRecord]:
    rows = await asyncio.to_thread(
        inventory_audit_dal.fetch_import_audit_rows,
        status=status.value,
        import_type=import_type.value if import_type else None,
        governor_id=governor_id,
        discord_user_id=discord_user_id,
        lookback_days=lookback_days,
        limit=limit,
    )
    records = [_record_from_row(row) for row in rows]
    logger.info(
        "inventory_audit_fetched status=%s import_type=%s governor=%s user=%s rows=%s",
        status.value,
        import_type.value if import_type else "all",
        governor_id,
        discord_user_id,
        len(records),
    )
    return records


def summarize_json_comparison(record: InventoryAuditRecord) -> str:
    parts = []
    if record.detected_json is not None:
        parts.append("detected")
    if record.corrected_json is not None:
        parts.append("corrected")
    if record.final_json is not None:
        parts.append("final")
    if record.error_json is not None:
        parts.append("error")
    return ", ".join(parts) if parts else "none"
