from __future__ import annotations

from typing import Any

from inventory.vip_levels import persisted_vip_code, vip_label


def _get_conn():
    from file_utils import get_conn_with_retries

    return get_conn_with_retries()


def fetch_inventory_profile(governor_id: int) -> dict[str, Any] | None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TOP 1 GovernorID,
                   VipLevelCode,
                   VipLevelLabel,
                   UpdatedByDiscordUserID,
                   CreatedAtUtc,
                   UpdatedAtUtc
            FROM dbo.GovernorInventoryProfile
            WHERE GovernorID = ?
            """,
            (int(governor_id),),
        )
        row = cur.fetchone()
        if not row:
            return None
        cols = [item[0] for item in cur.description]
        return dict(zip(cols, row, strict=True))
    finally:
        conn.close()


def upsert_inventory_vip(
    *, governor_id: int, vip_level_code: str | None, updated_by_discord_user_id: int
) -> None:
    persisted_code = persisted_vip_code(vip_level_code)
    label = vip_label(persisted_code)
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            MERGE dbo.GovernorInventoryProfile AS target
            USING (
                SELECT ? AS GovernorID,
                       ? AS VipLevelCode,
                       ? AS VipLevelLabel,
                       ? AS UpdatedByDiscordUserID
            ) AS source
               ON target.GovernorID = source.GovernorID
            WHEN MATCHED THEN
                UPDATE SET VipLevelCode = source.VipLevelCode,
                           VipLevelLabel = source.VipLevelLabel,
                           UpdatedByDiscordUserID = source.UpdatedByDiscordUserID,
                           UpdatedAtUtc = SYSUTCDATETIME()
            WHEN NOT MATCHED THEN
                INSERT (
                    GovernorID,
                    VipLevelCode,
                    VipLevelLabel,
                    UpdatedByDiscordUserID,
                    CreatedAtUtc,
                    UpdatedAtUtc
                )
                VALUES (
                    source.GovernorID,
                    source.VipLevelCode,
                    source.VipLevelLabel,
                    source.UpdatedByDiscordUserID,
                    SYSUTCDATETIME(),
                    SYSUTCDATETIME()
                );
            """,
            (
                int(governor_id),
                persisted_code,
                label,
                int(updated_by_discord_user_id),
            ),
        )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()
