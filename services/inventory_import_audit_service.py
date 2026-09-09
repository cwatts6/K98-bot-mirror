"""Service helpers for best-effort inventory import audit writes."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import logging
from typing import Any

from inventory.models import InventoryAnalysisSummary, InventoryFlowType, InventoryImportType
from services import import_audit_service

logger = logging.getLogger(__name__)

INVENTORY_AUDIT_IMPORT_KIND = "inventory"
INVENTORY_AUDIT_UPLOAD_SOURCE_TYPE = "discord_upload_image"
INVENTORY_AUDIT_COMMAND_SOURCE_TYPE = "discord_command_image"
INVENTORY_AUDIT_IMAGE_READ_PHASE = "inventory_image_read"
INVENTORY_AUDIT_BATCH_HANDOFF_PHASE = "inventory_batch_handoff"
INVENTORY_AUDIT_VISION_PHASE = "inventory_vision_analysis"
INVENTORY_AUDIT_REVIEW_PHASE = "inventory_review_transition"
INVENTORY_AUDIT_MATERIAL_MORE_PHASE = "inventory_material_more_requested"
INVENTORY_AUDIT_MATERIAL_MERGE_PHASE = "inventory_material_merge"
INVENTORY_AUDIT_APPROVAL_PHASE = "inventory_approval_sql_ingest"
INVENTORY_AUDIT_ADMIN_DEBUG_PHASE = "inventory_admin_debug_post"
INVENTORY_AUDIT_UPLOAD_CLEANUP_PHASE = "inventory_original_upload_cleanup"
INVENTORY_AUDIT_TERMINAL_PHASE = "inventory_terminal_outcome"
INVENTORY_AUDIT_EXTERNAL_TABLE = "dbo.InventoryImportBatch"

AuditThreadRunner = Callable[..., Awaitable[Any]]


@dataclass(frozen=True, slots=True)
class InventoryImportAuditContext:
    import_batch_id: int
    governor_id: int
    flow_type: str
    source_filename: str | None = None
    source_message_id: int | None = None
    source_channel_id: int | None = None
    actor_discord_id: int | None = None
    entry_point: str = "inventory_upload"

    @property
    def source_type(self) -> str:
        if self.flow_type == InventoryFlowType.COMMAND.value:
            return INVENTORY_AUDIT_COMMAND_SOURCE_TYPE
        return INVENTORY_AUDIT_UPLOAD_SOURCE_TYPE


def audit_timestamp_utc() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def audit_duration_ms(started: datetime) -> int:
    started_utc = started.replace(tzinfo=UTC) if started.tzinfo is None else started.astimezone(UTC)
    return max(0, int((datetime.now(UTC) - started_utc).total_seconds() * 1000))


def inventory_external_batch_id(import_batch_id: int) -> str:
    return str(int(import_batch_id))


def inventory_audit_details(
    context: InventoryImportAuditContext,
    *,
    import_type: InventoryImportType | str | None = None,
    rows_in_source: int | None = None,
    rows_written: int | None = None,
    domain_status: str | None = None,
    terminal_reason: str | None = None,
    screenshot_count: int | None = None,
    admin_debug_status: str | None = None,
    cleanup_deleted: bool | None = None,
    error: str | None = None,
) -> dict[str, object]:
    details: dict[str, object] = {
        "entry_point": context.entry_point,
        "governor_id": int(context.governor_id),
        "flow_type": context.flow_type,
        "import_batch_id": int(context.import_batch_id),
    }
    if import_type:
        details["import_type"] = str(getattr(import_type, "value", import_type))
    if rows_in_source is not None:
        details["rows_in_source"] = int(rows_in_source)
    if rows_written is not None:
        details["rows_written"] = int(rows_written)
    if domain_status:
        details["domain_status"] = domain_status
    if terminal_reason:
        details["terminal_reason"] = terminal_reason
    if screenshot_count is not None:
        details["screenshot_count"] = int(screenshot_count)
    if admin_debug_status:
        details["admin_debug_status"] = admin_debug_status
    if cleanup_deleted is not None:
        details["cleanup_deleted"] = cleanup_deleted
    if error:
        details["error"] = error
    return details


def inventory_row_count(
    import_type: InventoryImportType | str | None, values: dict[str, Any]
) -> int:
    raw_import_type = str(getattr(import_type, "value", import_type or ""))
    if raw_import_type == InventoryImportType.RESOURCES.value:
        rows = values.get("resources") if isinstance(values, dict) else None
        return len(rows) if isinstance(rows, dict) else 0
    if raw_import_type == InventoryImportType.SPEEDUPS.value:
        rows = values.get("speedups") if isinstance(values, dict) else None
        return len(rows) if isinstance(rows, dict) else 0
    if raw_import_type == InventoryImportType.MATERIALS.value:
        rows = values.get("materials", values) if isinstance(values, dict) else None
        if not isinstance(rows, dict):
            return 0
        return sum(len(rarities) for rarities in rows.values() if isinstance(rarities, dict))
    return 0


def image_count_from_summary(summary: InventoryAnalysisSummary | None) -> int:
    if summary is None:
        return 1
    if summary.import_type != InventoryImportType.MATERIALS:
        return 1
    raw_json = summary.raw_json if isinstance(summary.raw_json, dict) else {}
    try:
        return max(1, int(raw_json.get("screenshot_count") or 1))
    except (TypeError, ValueError):
        return 1


def _sha256_hex(content: bytes | None) -> str | None:
    if content is None:
        return None
    try:
        return hashlib.sha256(content).hexdigest()
    except Exception:
        logger.debug("inventory_audit_hash_failed", exc_info=True)
        return None


def _start_inventory_audit_batch_sync(
    context: InventoryImportAuditContext,
    image_bytes: bytes | None,
):
    return import_audit_service.start_batch_best_effort(
        import_kind=INVENTORY_AUDIT_IMPORT_KIND,
        source_type=context.source_type,
        source_filename=context.source_filename,
        source_file_hash_sha256=_sha256_hex(image_bytes),
        source_message_id=context.source_message_id,
        source_channel_id=context.source_channel_id,
        actor_discord_id=context.actor_discord_id,
        external_batch_table=INVENTORY_AUDIT_EXTERNAL_TABLE,
        external_batch_id=inventory_external_batch_id(context.import_batch_id),
        details=inventory_audit_details(context),
    )


async def start_inventory_audit_batch(
    *,
    context: InventoryImportAuditContext,
    image_bytes: bytes | None = None,
    audit_runner: AuditThreadRunner = asyncio.to_thread,
):
    try:
        return await audit_runner(_start_inventory_audit_batch_sync, context, image_bytes)
    except Exception:
        logger.warning("inventory_audit_start_failed; continuing import", exc_info=True)
        return None


async def fetch_inventory_audit_batch(
    *,
    import_batch_id: int,
    audit_runner: AuditThreadRunner = asyncio.to_thread,
):
    try:
        return await audit_runner(
            import_audit_service.fetch_batch_by_external_id_best_effort,
            import_kind=INVENTORY_AUDIT_IMPORT_KIND,
            external_batch_table=INVENTORY_AUDIT_EXTERNAL_TABLE,
            external_batch_id=inventory_external_batch_id(import_batch_id),
        )
    except Exception:
        logger.warning(
            "inventory_audit_lookup_failed batch_id=%s; continuing import",
            import_batch_id,
            exc_info=True,
        )
        return None


async def record_inventory_audit_phase(
    batch_ref,
    *,
    phase_name: str,
    phase_status: str,
    started_at_utc: datetime | None = None,
    rows_in: int | None = None,
    rows_out: int | None = None,
    duration_ms: int | None = None,
    error_type: str | None = None,
    error_text: str | None = None,
    details: object = None,
    set_batch_status: str | None = None,
    audit_runner: AuditThreadRunner = asyncio.to_thread,
) -> None:
    if batch_ref is None:
        return
    try:
        await audit_runner(
            import_audit_service.record_phase_best_effort,
            batch_ref,
            phase_name=phase_name,
            phase_status=phase_status,
            started_at_utc=started_at_utc,
            completed_at_utc=audit_timestamp_utc(),
            rows_in=rows_in,
            rows_out=rows_out,
            duration_ms=duration_ms,
            error_type=error_type,
            error_text=error_text,
            details=details,
            set_batch_status=set_batch_status,
        )
    except Exception:
        logger.warning(
            "inventory_audit_phase_failed phase=%s; continuing import",
            phase_name,
            exc_info=True,
        )


async def complete_inventory_audit_batch(
    batch_ref,
    *,
    status: str = "completed",
    rows_in_source: int | None = None,
    rows_staged: int | None = None,
    rows_written: int | None = None,
    rows_skipped: int | None = None,
    details: object = None,
    audit_runner: AuditThreadRunner = asyncio.to_thread,
) -> None:
    if batch_ref is None:
        return
    try:
        await audit_runner(
            import_audit_service.complete_batch_best_effort,
            batch_ref,
            status=status,
            rows_in_source=rows_in_source,
            rows_staged=rows_staged,
            rows_written=rows_written,
            rows_skipped=rows_skipped,
            details=details,
        )
    except Exception:
        logger.warning("inventory_audit_complete_failed; continuing import", exc_info=True)


async def fail_inventory_audit_batch(
    batch_ref,
    *,
    status: str = "failed",
    error_type: str | None = None,
    error_text: str | None = None,
    rows_in_source: int | None = None,
    rows_staged: int | None = None,
    rows_written: int | None = None,
    rows_skipped: int | None = None,
    details: object = None,
    audit_runner: AuditThreadRunner = asyncio.to_thread,
) -> None:
    if batch_ref is None:
        return
    try:
        await audit_runner(
            import_audit_service.fail_batch_best_effort,
            batch_ref,
            status=status,
            error_type=error_type,
            error_text=error_text,
            rows_in_source=rows_in_source,
            rows_staged=rows_staged,
            rows_written=rows_written,
            rows_skipped=rows_skipped,
            details=details,
        )
    except Exception:
        logger.warning("inventory_audit_fail_failed; continuing import", exc_info=True)
