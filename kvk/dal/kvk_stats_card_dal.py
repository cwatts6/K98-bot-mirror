from __future__ import annotations

import logging
from typing import Any

from file_utils import cursor_row_to_dict, get_conn_with_retries

logger = logging.getLogger(__name__)


def fetch_kvk_stats_card_context(kvk_no: int | None, governor_id: str) -> dict[str, Any]:
    """Fetch KVK mode and camp context for the player stats card."""
    if not kvk_no:
        return {}

    context: dict[str, Any] = {}
    conn = get_conn_with_retries()
    with conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT TOP 1 KVK_NAME FROM dbo.KVK_Details WHERE KVK_NO = ?",
            (int(kvk_no),),
        )
        row = cur.fetchone()
        if row:
            data = cursor_row_to_dict(cur, row)
            context["kvk_name"] = data.get("KVK_NAME")

        try:
            gov_int = int(str(governor_id).strip())
        except (TypeError, ValueError):
            logger.debug("kvk_stats_card_context_invalid_governor_id governor_id=%r", governor_id)
            return context

        cur.execute(
            """
            SELECT TOP 1
                pw.kingdom,
                pw.campid,
                cm.CampName AS camp_name
            FROM KVK.KVK_Player_Windowed AS pw
            LEFT JOIN KVK.KVK_CampMap AS cm
              ON cm.KVK_NO = pw.KVK_NO
             AND cm.Kingdom = pw.kingdom
            WHERE pw.KVK_NO = ?
              AND pw.governor_id = ?
            ORDER BY
                CASE
                    WHEN pw.WindowName = N'Full' THEN 0
                    WHEN pw.WindowName = N'Baseline' THEN 2
                    ELSE 1
                END,
                pw.last_scan_id DESC
            """,
            (int(kvk_no), gov_int),
        )
        row = cur.fetchone()
        if row:
            data = cursor_row_to_dict(cur, row)
            context["kingdom"] = data.get("kingdom")
            context["camp_id"] = data.get("campid")
            context["camp_name"] = data.get("camp_name")

        try:
            cur.execute(
                """
                SELECT TOP 1
                    overall_kvk_rank,
                    overall_kvk_total_governors,
                    overall_kvk_top_percent
                FROM KVK.vw_Player_Overall_KVK_Rank
                WHERE KVK_NO = ?
                  AND governor_id = ?
                """,
                (int(kvk_no), gov_int),
            )
            row = cur.fetchone()
            if row:
                data = cursor_row_to_dict(cur, row)
                context["overall_kvk_rank"] = data.get("overall_kvk_rank")
                context["overall_kvk_total_governors"] = data.get("overall_kvk_total_governors")
                context["overall_kvk_top_percent"] = data.get("overall_kvk_top_percent")
        except Exception:
            logger.warning(
                "kvk_stats_card_overall_rank_unavailable kvk_no=%s governor_id=%s",
                kvk_no,
                governor_id,
                exc_info=True,
            )
    return context
