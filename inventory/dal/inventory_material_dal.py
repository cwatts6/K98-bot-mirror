from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from inventory.material_calculations import (
    MATERIAL_RARITIES,
    legendary_equivalent,
)

logger = logging.getLogger(__name__)


def _get_conn():
    from file_utils import get_conn_with_retries

    return get_conn_with_retries()


def _rows_to_dicts(cursor) -> list[dict[str, Any]]:
    rows = cursor.fetchall()
    if not rows:
        return []
    cols = [item[0] for item in cursor.description]
    return [dict(zip(cols, row, strict=True)) for row in rows]


def insert_material_records(
    *,
    import_batch_id: int,
    governor_id: int,
    scan_utc: datetime,
    materials: dict[str, dict[str, int]],
) -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        for kind, rarities in materials.items():
            for rarity in MATERIAL_RARITIES:
                quantity = int(rarities.get(rarity) or 0)
                cur.execute(
                    """
                    INSERT INTO dbo.GovernorMaterialInventory
                    (
                        ImportBatchID, GovernorID, ScanUtc, MaterialKind,
                        Rarity, Quantity, LegendaryEquivalent
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(import_batch_id),
                        int(governor_id),
                        scan_utc,
                        kind,
                        rarity,
                        quantity,
                        float(legendary_equivalent(quantity, rarity)),
                    ),
                )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.exception("inventory_insert_material_records_failed batch_id=%s", import_batch_id)
        raise
    finally:
        conn.close()


def approve_material_batch(
    *,
    import_batch_id: int,
    governor_id: int,
    scan_utc: datetime,
    materials: dict[str, dict[str, int]],
    corrected_json: str | None = None,
    final_json: str | None = None,
) -> None:
    now = datetime.now(UTC)
    conn = _get_conn()
    try:
        cur = conn.cursor()
        for kind, rarities in materials.items():
            for rarity in MATERIAL_RARITIES:
                quantity = int(rarities.get(rarity) or 0)
                cur.execute(
                    """
                    INSERT INTO dbo.GovernorMaterialInventory
                    (
                        ImportBatchID, GovernorID, ScanUtc, MaterialKind,
                        Rarity, Quantity, LegendaryEquivalent
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(import_batch_id),
                        int(governor_id),
                        scan_utc,
                        kind,
                        rarity,
                        quantity,
                        float(legendary_equivalent(quantity, rarity)),
                    ),
                )
        cur.execute(
            """
            UPDATE dbo.InventoryImportBatch
            SET Status = N'approved',
                ApprovedAtUtc = ?,
                RejectedAtUtc = NULL,
                CorrectedJson = COALESCE(?, CorrectedJson),
                FinalJson = COALESCE(?, FinalJson),
                ErrorJson = NULL
            WHERE ImportBatchID = ?
            """,
            (now, corrected_json, final_json, int(import_batch_id)),
        )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.exception("inventory_approve_material_batch_failed batch_id=%s", import_batch_id)
        raise
    finally:
        conn.close()


def fetch_material_rows(governor_id: int, *, lookback_days: int = 370) -> list[dict[str, Any]]:
    since_utc = datetime.now(UTC) - timedelta(days=int(lookback_days))
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT m.ImportBatchID,
                   m.GovernorID,
                   m.ScanUtc,
                   m.MaterialKind,
                   m.Rarity,
                   m.Quantity,
                   m.LegendaryEquivalent
            FROM dbo.GovernorMaterialInventory AS m
            INNER JOIN dbo.InventoryImportBatch AS b
                ON b.ImportBatchID = m.ImportBatchID
            WHERE m.GovernorID = ?
              AND b.Status = N'approved'
              AND b.ImportType = N'materials'
              AND m.ScanUtc >= ?
            ORDER BY m.ScanUtc ASC, m.MaterialKind ASC, m.Rarity ASC
            """,
            (int(governor_id), since_utc),
        )
        return _rows_to_dicts(cur)
    finally:
        conn.close()


def fetch_latest_approved_material_values(governor_id: int) -> dict[str, dict[str, int]]:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            WITH LatestBatch AS (
                SELECT TOP 1 ImportBatchID
                FROM dbo.InventoryImportBatch
                WHERE GovernorID = ?
                  AND ImportType = N'materials'
                  AND Status = N'approved'
                ORDER BY ApprovedAtUtc DESC, ImportBatchID DESC
            )
            SELECT m.MaterialKind,
                   m.Rarity,
                   m.Quantity
            FROM dbo.GovernorMaterialInventory AS m
            INNER JOIN LatestBatch AS b
                ON b.ImportBatchID = m.ImportBatchID
            ORDER BY m.MaterialKind ASC, m.Rarity ASC
            """,
            (int(governor_id),),
        )
        rows = _rows_to_dicts(cur)
    finally:
        conn.close()

    grouped: dict[str, dict[str, int]] = {}
    for row in rows:
        kind = str(row.get("MaterialKind") or "").lower()
        rarity = str(row.get("Rarity") or "").lower()
        grouped.setdefault(kind, {})[rarity] = int(row.get("Quantity") or 0)
    return grouped


def fetch_material_export_rows(
    governor_ids: list[int], *, lookback_days: int = 366
) -> list[dict[str, Any]]:
    if not governor_ids:
        return []
    since_utc = datetime.now(UTC) - timedelta(days=int(lookback_days))
    placeholders = ",".join("?" for _ in governor_ids)
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT b.ImportBatchID,
                   b.GovernorID,
                   p.VipLevelCode,
                   p.VipLevelLabel,
                   b.DiscordUserID,
                   b.FlowType,
                   b.ApprovedAtUtc,
                   b.CreatedAtUtc,
                   m.ScanUtc,
                   m.MaterialKind,
                   m.Rarity,
                   m.Quantity,
                   m.LegendaryEquivalent,
                   m.SourceImageIndex
            FROM dbo.GovernorMaterialInventory AS m
            INNER JOIN dbo.InventoryImportBatch AS b
                ON b.ImportBatchID = m.ImportBatchID
            LEFT JOIN dbo.GovernorInventoryProfile AS p
                ON p.GovernorID = b.GovernorID
            WHERE m.GovernorID IN ({placeholders})
              AND b.Status = N'approved'
              AND b.ImportType = N'materials'
              AND m.ScanUtc >= ?
            ORDER BY m.GovernorID ASC, m.ScanUtc DESC, m.MaterialKind ASC, m.Rarity ASC
            """,
            (*[int(item) for item in governor_ids], since_utc),
        )
        return _rows_to_dicts(cur)
    finally:
        conn.close()
