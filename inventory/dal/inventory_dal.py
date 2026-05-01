from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import logging
from typing import Any

from inventory.models import InventoryFlowType, InventoryImportStatus, InventoryImportType

logger = logging.getLogger(__name__)


def _get_conn():
    from file_utils import get_conn_with_retries

    return get_conn_with_retries()


def _json(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _rows_to_dicts(cursor) -> list[dict[str, Any]]:
    rows = cursor.fetchall()
    if not rows:
        return []
    cols = [item[0] for item in cursor.description]
    return [dict(zip(cols, row, strict=True)) for row in rows]


def create_import_batch(
    *,
    governor_id: int,
    discord_user_id: int,
    flow_type: InventoryFlowType,
    status: InventoryImportStatus = InventoryImportStatus.AWAITING_UPLOAD,
    source_message_id: int | None = None,
    source_channel_id: int | None = None,
    image_attachment_url: str | None = None,
    is_admin_import: bool = False,
    expires_at_utc: datetime | None = None,
) -> int:
    now = datetime.now(UTC)
    expires = expires_at_utc or (now + timedelta(minutes=10))
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO dbo.InventoryImportBatch
            (
                GovernorID, DiscordUserID, FlowType, SourceMessageID, SourceChannelID,
                ImageAttachmentURL, Status, CreatedAtUtc, RetryCount, IsAdminImport,
                ExpiresAtUtc
            )
            OUTPUT INSERTED.ImportBatchID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?);
            """,
            (
                int(governor_id),
                int(discord_user_id),
                str(flow_type.value),
                source_message_id,
                source_channel_id,
                image_attachment_url,
                str(status.value),
                now,
                1 if is_admin_import else 0,
                expires,
            ),
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError("InventoryImportBatch insert returned no identity row.")
        conn.commit()
        return int(row[0])
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.exception(
            "inventory_create_import_batch_failed governor_id=%s discord_user_id=%s",
            governor_id,
            discord_user_id,
        )
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def expire_stale_batches_for_governor(governor_id: int) -> None:
    """Mark any expired awaiting_upload/analysed sessions as cancelled for the given governor."""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE dbo.InventoryImportBatch
            SET Status = 'cancelled'
            WHERE GovernorID = ?
              AND Status IN ('awaiting_upload', 'analysed')
              AND ExpiresAtUtc IS NOT NULL
              AND ExpiresAtUtc <= SYSUTCDATETIME()
            """,
            (int(governor_id),),
        )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.exception("inventory_expire_stale_batches_failed governor_id=%s", governor_id)
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def fetch_active_batch_for_governor(governor_id: int) -> dict[str, Any] | None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TOP 1 *
            FROM dbo.InventoryImportBatch
            WHERE GovernorID = ?
              AND Status IN ('awaiting_upload', 'analysed')
              AND (ExpiresAtUtc IS NULL OR ExpiresAtUtc > SYSUTCDATETIME())
            ORDER BY CreatedAtUtc DESC
            """,
            (int(governor_id),),
        )
        rows = _rows_to_dicts(cur)
        return rows[0] if rows else None
    finally:
        conn.close()


def fetch_pending_upload_for_user(discord_user_id: int) -> dict[str, Any] | None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TOP 1 *
            FROM dbo.InventoryImportBatch
            WHERE DiscordUserID = ?
              AND Status = 'awaiting_upload'
              AND FlowType = 'command'
              AND (ExpiresAtUtc IS NULL OR ExpiresAtUtc > SYSUTCDATETIME())
            ORDER BY CreatedAtUtc DESC
            """,
            (int(discord_user_id),),
        )
        rows = _rows_to_dicts(cur)
        return rows[0] if rows else None
    finally:
        conn.close()


def has_approved_import_today(governor_id: int, import_type: InventoryImportType) -> bool:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TOP 1 1 AS Found
            FROM dbo.InventoryImportBatch
            WHERE GovernorID = ?
              AND ImportType = ?
              AND Status = 'approved'
              AND ApprovedDateUtc = CAST(SYSUTCDATETIME() AS date)
            """,
            (int(governor_id), str(import_type.value)),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def update_batch_analysis(
    *,
    import_batch_id: int,
    import_type: InventoryImportType,
    vision_model: str,
    vision_prompt_version: str,
    fallback_used: bool,
    confidence_score: float,
    detected_json: dict[str, Any],
    warning_json: list[str],
    error_json: dict[str, Any] | None = None,
    status: InventoryImportStatus = InventoryImportStatus.ANALYSED,
    source_message_id: int | None = None,
    source_channel_id: int | None = None,
    image_attachment_url: str | None = None,
) -> None:
    now = datetime.now(UTC)
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE dbo.InventoryImportBatch
            SET ImportType = ?,
                SourceMessageID = COALESCE(?, SourceMessageID),
                SourceChannelID = COALESCE(?, SourceChannelID),
                ImageAttachmentURL = COALESCE(?, ImageAttachmentURL),
                Status = ?,
                VisionModel = ?,
                VisionPromptVersion = ?,
                FallbackUsed = ?,
                ConfidenceScore = ?,
                DetectedJson = ?,
                WarningJson = ?,
                ErrorJson = ?,
                ExpiresAtUtc = ?
            WHERE ImportBatchID = ?
            """,
            (
                str(import_type.value),
                source_message_id,
                source_channel_id,
                image_attachment_url,
                str(status.value),
                vision_model,
                vision_prompt_version,
                1 if fallback_used else 0,
                float(confidence_score or 0.0),
                _json(detected_json),
                _json(warning_json),
                _json(error_json),
                now + timedelta(minutes=15),
                int(import_batch_id),
            ),
        )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.exception("inventory_update_batch_analysis_failed batch_id=%s", import_batch_id)
        raise
    finally:
        conn.close()


def update_debug_reference(
    *, import_batch_id: int, admin_debug_channel_id: int, admin_debug_message_id: int
) -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE dbo.InventoryImportBatch
            SET AdminDebugChannelID = ?, AdminDebugMessageID = ?
            WHERE ImportBatchID = ?
            """,
            (int(admin_debug_channel_id), int(admin_debug_message_id), int(import_batch_id)),
        )
        conn.commit()
    finally:
        conn.close()


def mark_original_upload_deleted(import_batch_id: int) -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE dbo.InventoryImportBatch
            SET OriginalUploadDeletedAtUtc = ?
            WHERE ImportBatchID = ?
            """,
            (datetime.now(UTC), int(import_batch_id)),
        )
        conn.commit()
    finally:
        conn.close()


def mark_status(
    *,
    import_batch_id: int,
    status: InventoryImportStatus,
    corrected_json: dict[str, Any] | None = None,
    final_json: dict[str, Any] | None = None,
    error_json: dict[str, Any] | None = None,
) -> None:
    now = datetime.now(UTC)
    approved_at = now if status == InventoryImportStatus.APPROVED else None
    rejected_at = now if status == InventoryImportStatus.REJECTED else None
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE dbo.InventoryImportBatch
            SET Status = ?,
                ApprovedAtUtc = ?,
                RejectedAtUtc = ?,
                CorrectedJson = COALESCE(?, CorrectedJson),
                FinalJson = COALESCE(?, FinalJson),
                ErrorJson = ?
            WHERE ImportBatchID = ?
            """,
            (
                str(status.value),
                approved_at,
                rejected_at,
                _json(corrected_json),
                _json(final_json),
                _json(error_json),
                int(import_batch_id),
            ),
        )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.exception(
            "inventory_mark_status_failed batch_id=%s status=%s",
            import_batch_id,
            status,
        )
        raise
    finally:
        conn.close()


def insert_resource_records(
    *,
    import_batch_id: int,
    governor_id: int,
    scan_utc: datetime,
    resources: dict[str, dict[str, int]],
) -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        for resource_type, row in resources.items():
            cur.execute(
                """
                INSERT INTO dbo.GovernorResourceInventory
                (
                    ImportBatchID, GovernorID, ScanUtc, ResourceType,
                    FromItemsValue, TotalResourcesValue
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    int(import_batch_id),
                    int(governor_id),
                    scan_utc,
                    resource_type,
                    int(row["from_items_value"]),
                    int(row["total_resources_value"]),
                ),
            )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.exception("inventory_insert_resource_records_failed batch_id=%s", import_batch_id)
        raise
    finally:
        conn.close()


def insert_speedup_records(
    *,
    import_batch_id: int,
    governor_id: int,
    scan_utc: datetime,
    speedups: dict[str, dict[str, int | float]],
) -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        for speedup_type, row in speedups.items():
            cur.execute(
                """
                INSERT INTO dbo.GovernorSpeedupInventory
                (
                    ImportBatchID, GovernorID, ScanUtc, SpeedupType,
                    TotalMinutes, TotalHours, TotalDaysDecimal
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(import_batch_id),
                    int(governor_id),
                    scan_utc,
                    speedup_type,
                    int(row["total_minutes"]),
                    float(row["total_hours"]),
                    float(row["total_days_decimal"]),
                ),
            )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.exception("inventory_insert_speedup_records_failed batch_id=%s", import_batch_id)
        raise
    finally:
        conn.close()


def approve_batch(
    *,
    import_batch_id: int,
    governor_id: int,
    scan_utc: datetime,
    import_type: InventoryImportType,
    normalized: dict[str, Any],
    corrected_json: dict[str, Any] | None = None,
) -> None:
    """Insert inventory records and mark the batch APPROVED in a single transaction."""
    now = datetime.now(UTC)
    conn = _get_conn()
    try:
        cur = conn.cursor()
        if import_type == InventoryImportType.RESOURCES:
            for resource_type, row in normalized["resources"].items():
                cur.execute(
                    """
                    INSERT INTO dbo.GovernorResourceInventory
                    (
                        ImportBatchID, GovernorID, ScanUtc, ResourceType,
                        FromItemsValue, TotalResourcesValue
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(import_batch_id),
                        int(governor_id),
                        scan_utc,
                        resource_type,
                        int(row["from_items_value"]),
                        int(row["total_resources_value"]),
                    ),
                )
        elif import_type == InventoryImportType.SPEEDUPS:
            for speedup_type, row in normalized["speedups"].items():
                cur.execute(
                    """
                    INSERT INTO dbo.GovernorSpeedupInventory
                    (
                        ImportBatchID, GovernorID, ScanUtc, SpeedupType,
                        TotalMinutes, TotalHours, TotalDaysDecimal
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(import_batch_id),
                        int(governor_id),
                        scan_utc,
                        speedup_type,
                        int(row["total_minutes"]),
                        float(row["total_hours"]),
                        float(row["total_days_decimal"]),
                    ),
                )
        cur.execute(
            """
            UPDATE dbo.InventoryImportBatch
            SET Status = ?,
                ApprovedAtUtc = ?,
                RejectedAtUtc = NULL,
                CorrectedJson = COALESCE(?, CorrectedJson),
                FinalJson = COALESCE(?, FinalJson),
                ErrorJson = NULL
            WHERE ImportBatchID = ?
            """,
            (
                str(InventoryImportStatus.APPROVED.value),
                now,
                _json(corrected_json),
                _json(normalized),
                int(import_batch_id),
            ),
        )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.exception("inventory_approve_batch_failed batch_id=%s", import_batch_id)
        raise
    finally:
        conn.close()
