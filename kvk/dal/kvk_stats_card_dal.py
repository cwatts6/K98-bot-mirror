from __future__ import annotations

from contextlib import closing
import logging
from typing import Any

from file_utils import cursor_row_to_dict, get_conn_with_retries

logger = logging.getLogger(__name__)


def resolve_card_read(kvk_no, *, connect=None):
    """Find overall by its unique season key, never by the display fight or MAX scan."""
    from dataclasses import replace

    from kvk.dal.new_source_import_dal import one, transaction
    from kvk.dal.source_routing_dal import resolve_season_read
    from kvk.models.source_integration import SeasonRead
    from kvk.schemas.new_source_schema import SOURCE_KEY

    read = SeasonRead(kvk_no)
    try:
        with transaction(connect or get_conn_with_retries) as cursor:
            cursor.execute("SELECT KVK_NAME FROM dbo.KVK_Details WHERE KVK_NO=?", kvk_no)
            details = one(cursor) or {}
            cursor.execute(
                "SELECT PeriodID FROM KVK.SourcePeriod WHERE SourceKey=? AND KVK_NO=? "
                "AND PeriodKey='overall' AND PeriodKind='overall'",
                SOURCE_KEY,
                kvk_no,
            )
            period = one(cursor)
        read = resolve_season_read(
            kvk_no, period_id=period["PeriodID"] if period else None, connect=connect
        )
        if read.source_key == SOURCE_KEY and not period:
            read = replace(
                read, availability="unavailable", reason="overall_missing", period_id=None
            )
        return read, details.get("KVK_NAME")
    except Exception as exc:
        logger.warning(
            "card_authority_unavailable kvk_no=%s error_type=%s", kvk_no, type(exc).__name__
        )
        return replace(read, reason="authority_unavailable"), None


def fetch_kvk_stats_card_context(
    kvk_no: int | None, governor_id: str, *, include_overall_rank=True, connect=None
) -> dict[str, Any]:
    """Fetch KVK mode and camp context for the player stats card."""
    if not kvk_no:
        return {}

    context: dict[str, Any] = {}
    conn = (connect or get_conn_with_retries)()
    with closing(conn) if connect is not None else conn:
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

        if not include_overall_rank:
            return context

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
                ORDER BY overall_kvk_rank ASC
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
