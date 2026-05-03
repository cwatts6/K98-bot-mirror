from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from decoraters import _is_admin
from inventory.dal import inventory_dal
from inventory.models import (
    InventoryAnalysisSummary,
    InventoryFlowType,
    InventoryImagePayload,
    InventoryImportStatus,
    InventoryImportType,
    RegisteredGovernor,
)
from inventory.parsing import normalize_final_values
from registry.governor_registry import load_registry
from services.vision_client import InventoryVisionClient

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
SUPPORTED_IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}
LOW_CONFIDENCE_REJECT_THRESHOLD = 0.70
SPEEDUP_DIGIT_LOSS_DAY_THRESHOLD = 45.0
SPEEDUP_DIGIT_LOSS_RATIO = 0.20


def is_supported_image_attachment(filename: str | None, content_type: str | None) -> bool:
    fname = (filename or "").strip().lower()
    ctype = (content_type or "").strip().lower()
    return fname.endswith(SUPPORTED_IMAGE_EXTENSIONS) or ctype in SUPPORTED_IMAGE_CONTENT_TYPES


async def get_registered_governors_for_user(discord_user_id: int) -> list[RegisteredGovernor]:
    registry = await asyncio.to_thread(load_registry)
    block = registry.get(str(discord_user_id)) or registry.get(discord_user_id) or {}
    accounts = block.get("accounts") or {}
    governors: list[RegisteredGovernor] = []
    for account_type, account in accounts.items():
        if not isinstance(account, dict):
            continue
        raw_gid = account.get("GovernorID") or account.get("GovernorId")
        try:
            gid = int(str(raw_gid).strip())
        except (TypeError, ValueError):
            continue
        name = str(account.get("GovernorName") or account.get("Governor") or gid)
        governors.append(
            RegisteredGovernor(
                governor_id=gid,
                governor_name=name,
                account_type=str(account_type),
            )
        )
    return governors


async def user_can_import_for_governor(
    *,
    discord_user_id: int,
    governor_id: int,
    discord_user: Any | None = None,
    is_admin: bool = False,
) -> bool:
    if is_admin or (discord_user is not None and _is_admin(discord_user)):
        return True
    governors = await get_registered_governors_for_user(discord_user_id)
    return any(item.governor_id == int(governor_id) for item in governors)


async def create_pending_command_session(
    *,
    governor_id: int,
    discord_user_id: int,
    discord_user: Any | None = None,
    is_admin: bool = False,
    timeout_minutes: int = 10,
) -> int:
    admin = bool(is_admin or (discord_user is not None and _is_admin(discord_user)))
    if not await user_can_import_for_governor(
        discord_user_id=discord_user_id,
        governor_id=governor_id,
        discord_user=discord_user,
        is_admin=admin,
    ):
        raise PermissionError("You can only import inventory for governors registered to you.")

    await asyncio.to_thread(inventory_dal.expire_stale_batches_for_governor, int(governor_id))
    active = await asyncio.to_thread(inventory_dal.fetch_active_batch_for_governor, governor_id)
    if active:
        raise ValueError("This governor already has an active inventory import session.")

    expires = datetime.now(UTC) + timedelta(minutes=timeout_minutes)
    return await asyncio.to_thread(
        inventory_dal.create_import_batch,
        governor_id=int(governor_id),
        discord_user_id=int(discord_user_id),
        flow_type=InventoryFlowType.COMMAND,
        status=InventoryImportStatus.AWAITING_UPLOAD,
        is_admin_import=admin,
        expires_at_utc=expires,
    )


async def get_pending_command_session(discord_user_id: int) -> dict[str, Any] | None:
    return await asyncio.to_thread(inventory_dal.fetch_pending_upload_for_user, discord_user_id)


async def create_upload_first_batch(
    *,
    governor_id: int,
    discord_user_id: int,
    payload: InventoryImagePayload,
    discord_user: Any | None = None,
    is_admin: bool = False,
) -> int:
    admin = bool(is_admin or (discord_user is not None and _is_admin(discord_user)))
    if not await user_can_import_for_governor(
        discord_user_id=discord_user_id,
        governor_id=governor_id,
        discord_user=discord_user,
        is_admin=admin,
    ):
        raise PermissionError("You can only import inventory for governors registered to you.")

    await asyncio.to_thread(inventory_dal.expire_stale_batches_for_governor, int(governor_id))
    active = await asyncio.to_thread(inventory_dal.fetch_active_batch_for_governor, governor_id)
    if active:
        raise ValueError("This governor already has an active inventory import session.")

    return await asyncio.to_thread(
        inventory_dal.create_import_batch,
        governor_id=int(governor_id),
        discord_user_id=int(discord_user_id),
        flow_type=InventoryFlowType.UPLOAD_FIRST,
        source_message_id=payload.source_message_id,
        source_channel_id=payload.source_channel_id,
        image_attachment_url=payload.image_attachment_url,
        is_admin_import=admin,
    )


def _map_detected_type(raw: str | None) -> InventoryImportType:
    value = (raw or "unknown").strip().lower()
    try:
        return InventoryImportType(value)
    except ValueError:
        return InventoryImportType.UNKNOWN


def _summary_from_vision_result(result: Any) -> InventoryAnalysisSummary:
    summary = InventoryAnalysisSummary(
        ok=bool(result.ok),
        import_type=_map_detected_type(getattr(result, "detected_image_type", None)),
        values=dict(getattr(result, "values", {}) or {}),
        confidence_score=float(getattr(result, "confidence_score", 0.0) or 0.0),
        warnings=list(getattr(result, "warnings", []) or []),
        model=str(getattr(result, "model", "") or ""),
        prompt_version=str(getattr(result, "prompt_version", "") or ""),
        fallback_used=bool(getattr(result, "fallback_used", False)),
        error=getattr(result, "error", None),
        raw_json=dict(getattr(result, "raw_json", {}) or {}),
    )
    return with_inventory_anomaly_warnings(summary)


def with_inventory_anomaly_warnings(
    summary: InventoryAnalysisSummary,
) -> InventoryAnalysisSummary:
    warnings = list(summary.warnings)
    if summary.import_type == InventoryImportType.SPEEDUPS:
        warnings.extend(_speedup_digit_loss_warnings(summary.values))
    if summary.import_type == InventoryImportType.RESOURCES:
        warnings.extend(_resource_consistency_warnings(summary.values))
    deduped = list(dict.fromkeys(item for item in warnings if item))
    if deduped == summary.warnings:
        return summary
    return InventoryAnalysisSummary(
        ok=summary.ok,
        import_type=summary.import_type,
        values=summary.values,
        confidence_score=summary.confidence_score,
        warnings=deduped,
        model=summary.model,
        prompt_version=summary.prompt_version,
        fallback_used=summary.fallback_used,
        error=summary.error,
        raw_json=summary.raw_json,
    )


def _speedup_digit_loss_warnings(values: dict[str, Any]) -> list[str]:
    speedups = values.get("speedups") if isinstance(values, dict) else None
    if not isinstance(speedups, dict):
        return ["Speedup rows are missing from the detected data."]

    parsed_days: dict[str, float] = {}
    warnings: list[str] = []
    for speedup_type in ("building", "research", "training", "healing", "universal"):
        row = speedups.get(speedup_type)
        if not isinstance(row, dict):
            warnings.append(f"{speedup_type.title()} speedup row is missing.")
            continue
        minutes = row.get("total_minutes")
        days = row.get("total_days_decimal")
        hours = row.get("total_hours")
        try:
            minutes_i = int(minutes)
            days_f = float(days)
            hours_f = float(hours)
        except (TypeError, ValueError):
            warnings.append(f"{speedup_type.title()} speedup value could not be validated.")
            continue
        parsed_days[speedup_type] = days_f
        if abs(minutes_i - round(days_f * 1440)) > 2:
            warnings.append(
                f"{speedup_type.title()} speedup days/minutes do not match; please verify."
            )
        if abs(hours_f - (minutes_i / 60)) > 0.1:
            warnings.append(
                f"{speedup_type.title()} speedup hours/minutes do not match; please verify."
            )

    large_values = [
        value for value in parsed_days.values() if value >= SPEEDUP_DIGIT_LOSS_DAY_THRESHOLD
    ]
    if large_values:
        max_days = max(large_values)
        for speedup_type, days in parsed_days.items():
            if 0 < days <= max_days * SPEEDUP_DIGIT_LOSS_RATIO:
                warnings.append(
                    f"{speedup_type.title()} speedup is much lower than other rows; check for a missing digit."
                )
    return warnings


def _resource_consistency_warnings(values: dict[str, Any]) -> list[str]:
    resources = values.get("resources") if isinstance(values, dict) else None
    if not isinstance(resources, dict):
        return ["Resource rows are missing from the detected data."]
    warnings: list[str] = []
    for resource_type in ("food", "wood", "stone", "gold"):
        row = resources.get(resource_type)
        if not isinstance(row, dict):
            warnings.append(f"{resource_type.title()} resource row is missing.")
            continue
        try:
            from_items = int(row.get("from_items_value"))
            total = int(row.get("total_resources_value"))
        except (TypeError, ValueError):
            warnings.append(f"{resource_type.title()} resource value could not be validated.")
            continue
        if total < from_items:
            warnings.append(
                f"{resource_type.title()} total resources are lower than from-items resources."
            )
    return warnings


async def analyse_inventory_image(
    *,
    import_batch_id: int,
    payload: InventoryImagePayload,
    vision_client: InventoryVisionClient | None = None,
) -> InventoryAnalysisSummary:
    client = vision_client or InventoryVisionClient()
    result = await client.analyse_image(
        payload.image_bytes,
        filename=payload.filename,
        content_type=payload.content_type,
        import_type_hint=None,
    )
    summary = _summary_from_vision_result(result)

    status = InventoryImportStatus.ANALYSED if summary.ok else InventoryImportStatus.FAILED
    if summary.import_type == InventoryImportType.UNKNOWN:
        status = InventoryImportStatus.FAILED
    if summary.confidence_score < LOW_CONFIDENCE_REJECT_THRESHOLD:
        status = InventoryImportStatus.FAILED

    await asyncio.to_thread(
        inventory_dal.update_batch_analysis,
        import_batch_id=int(import_batch_id),
        import_type=summary.import_type,
        vision_model=summary.model,
        vision_prompt_version=summary.prompt_version,
        fallback_used=summary.fallback_used,
        confidence_score=summary.confidence_score,
        detected_json=summary.raw_json or {"values": summary.values},
        warning_json=summary.warnings,
        error_json={"error": summary.error} if summary.error else None,
        status=status,
        source_message_id=payload.source_message_id,
        source_channel_id=payload.source_channel_id,
        image_attachment_url=payload.image_attachment_url,
    )
    return summary


async def approve_import(
    *,
    import_batch_id: int,
    governor_id: int,
    summary: InventoryAnalysisSummary,
    final_values: dict[str, Any] | None = None,
    is_admin: bool = False,
    corrected_values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if summary.import_type in {InventoryImportType.MATERIALS, InventoryImportType.UNKNOWN}:
        raise ValueError(
            f"{summary.import_type.value.title()} imports are not available in Phase 1."
        )
    if summary.confidence_score < LOW_CONFIDENCE_REJECT_THRESHOLD:
        raise ValueError("Image confidence is too low to approve.")

    if not is_admin:
        already_imported = await asyncio.to_thread(
            inventory_dal.has_approved_import_today,
            int(governor_id),
            summary.import_type,
        )
        if already_imported:
            raise ValueError("This governor already has an approved import of this type today.")

    normalized = normalize_final_values(summary.import_type, final_values or summary.values)
    scan_utc = datetime.now(UTC)
    await asyncio.to_thread(
        inventory_dal.approve_batch,
        import_batch_id=int(import_batch_id),
        governor_id=int(governor_id),
        scan_utc=scan_utc,
        import_type=summary.import_type,
        normalized=normalized,
        corrected_json=corrected_values,
    )
    logger.info(
        "inventory_import_approved batch_id=%s governor_id=%s import_type=%s",
        import_batch_id,
        governor_id,
        summary.import_type.value,
    )
    return normalized


async def reject_import(import_batch_id: int, *, error: str | None = None) -> None:
    await asyncio.to_thread(
        inventory_dal.mark_status,
        import_batch_id=int(import_batch_id),
        status=InventoryImportStatus.REJECTED,
        error_json={"error": error} if error else None,
    )


async def fail_import(import_batch_id: int, *, error: str | None = None) -> None:
    await asyncio.to_thread(
        inventory_dal.mark_status,
        import_batch_id=int(import_batch_id),
        status=InventoryImportStatus.FAILED,
        error_json={"error": error} if error else None,
    )


async def cancel_import(import_batch_id: int) -> None:
    await asyncio.to_thread(
        inventory_dal.mark_status,
        import_batch_id=int(import_batch_id),
        status=InventoryImportStatus.CANCELLED,
    )


async def mark_original_upload_deleted(import_batch_id: int) -> None:
    await asyncio.to_thread(inventory_dal.mark_original_upload_deleted, int(import_batch_id))


async def update_debug_reference(
    *, import_batch_id: int, admin_debug_channel_id: int, admin_debug_message_id: int
) -> None:
    await asyncio.to_thread(
        inventory_dal.update_debug_reference,
        import_batch_id=int(import_batch_id),
        admin_debug_channel_id=int(admin_debug_channel_id),
        admin_debug_message_id=int(admin_debug_message_id),
    )


def build_admin_debug_payload(
    *,
    summary: InventoryAnalysisSummary | None,
    corrected_json: dict[str, Any] | None = None,
    final_json: dict[str, Any] | None = None,
    error_json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "detected": summary.raw_json if summary else None,
        "corrected": corrected_json,
        "final": final_json,
        "error": error_json,
    }
