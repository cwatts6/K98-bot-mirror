"""Data-access helpers for KVK all-kingdom reporting blocks."""

from __future__ import annotations

import logging
from typing import Any, Literal

from file_utils import cursor_row_to_dict, fetch_one_dict, get_conn_with_retries

logger = logging.getLogger(__name__)

TopSort = Literal["kills", "deads", "dkp"]


def _fetch_all(cursor: Any) -> list[dict[str, Any]]:
    return [cursor_row_to_dict(cursor, row) for row in cursor.fetchall()]


def _player_order_clause(sort_by: TopSort) -> str:
    clause = {
        "kills": "kills_gain DESC",
        "deads": "p.deads DESC",
        "dkp": "dkp DESC",
    }.get(sort_by)
    if clause is None:
        raise ValueError(
            f"Invalid player sort_by value: {sort_by!r}. Expected one of: 'kills', 'deads', 'dkp'."
        )
    return clause


def _kingdom_order_clause(sort_by: TopSort) -> str:
    clause = {
        "kills": "kills_gain DESC",
        "deads": "a.deads DESC",
        "dkp": "dkp DESC",
    }.get(sort_by)
    if clause is None:
        raise ValueError(
            f"Invalid kingdom sort_by value: {sort_by!r}. Expected one of: 'kills', 'deads', 'dkp'."
        )
    return clause


def _camp_order_clause(sort_by: TopSort) -> str:
    clause = {
        "kills": "kills_gain DESC",
        "deads": "a.deads DESC",
        "dkp": "dkp DESC",
    }.get(sort_by)
    if clause is None:
        raise ValueError(
            f"Invalid camp sort_by value: {sort_by!r}. Expected one of: 'kills', 'deads', 'dkp'."
        )
    return clause


def fetch_top_players(
    cursor: Any,
    kvk_no: int,
    *,
    sort_by: TopSort,
    kingdom: int | None = None,
) -> list[dict[str, Any]]:
    """Return top player reporting rows, including structured contribution fields."""
    where_clause = "WHERE p.kingdom = ?" if kingdom is not None else ""
    params: tuple[Any, ...]
    if kingdom is not None:
        params = (kvk_no, kvk_no, kvk_no, kingdom)
    else:
        params = (kvk_no, kvk_no, kvk_no)

    cursor.execute(
        f"""
        SELECT TOP 5 p.name, p.kingdom, p.campid,
               (p.t4 + p.t5) AS kills_gain,
               p.deads,
               p.healed_troops,
               p.KP AS kp_gain,
               (p.t4*w.X + p.t5*w.Y + p.deads*w.Z) AS dkp,
               ISNULL(contrib.acclaim_gain, 0) AS acclaim_gain
        FROM dbo.fn_KVK_Player_Aggregated(?) p
        OUTER APPLY (
            SELECT SUM(ISNULL(pw.cur_contribute_gain, 0)) AS acclaim_gain
            FROM KVK.KVK_Player_Windowed pw
            JOIN KVK.KVK_Windows ww
              ON ww.KVK_NO = pw.KVK_NO
             AND ww.WindowName = pw.WindowName
             AND ww.StartScanID IS NOT NULL
            WHERE pw.KVK_NO = ?
              AND pw.governor_id = p.governor_id
        ) contrib
        CROSS APPLY (
            SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
            FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
        ) w
        {where_clause}
        ORDER BY {_player_order_clause(sort_by)};
        """,
        params,
    )
    return _fetch_all(cursor)


def fetch_top_kingdoms(cursor: Any, kvk_no: int, *, sort_by: TopSort) -> list[dict[str, Any]]:
    """Return top kingdom reporting rows, including structured contribution fields."""
    cursor.execute(
        f"""
        SELECT TOP 5 a.kingdom,
               (a.t4 + a.t5) AS kills_gain,
               a.deads,
               a.KP AS kp_gain,
               a.healed_troops,
               (a.t4*w.X + a.t5*w.Y + a.deads*w.Z) AS dkp,
               ISNULL(contrib.acclaim_gain, 0) AS acclaim_gain
        FROM dbo.fn_KVK_Kingdom_Aggregated(?) a
        OUTER APPLY (
            SELECT SUM(ISNULL(kw.cur_contribute_gain, 0)) AS acclaim_gain
            FROM KVK.KVK_Kingdom_Windowed kw
            JOIN KVK.KVK_Windows ww
              ON ww.KVK_NO = kw.KVK_NO
             AND ww.WindowName = kw.WindowName
             AND ww.StartScanID IS NOT NULL
            WHERE kw.KVK_NO = ?
              AND kw.kingdom = a.kingdom
        ) contrib
        CROSS APPLY (
            SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
            FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
        ) w
        ORDER BY {_kingdom_order_clause(sort_by)};
        """,
        (kvk_no, kvk_no, kvk_no),
    )
    return _fetch_all(cursor)


def fetch_top_camps(cursor: Any, kvk_no: int, *, sort_by: TopSort) -> list[dict[str, Any]]:
    """Return top camp reporting rows, including structured contribution fields."""
    cursor.execute(
        f"""
        SELECT TOP 5 a.campid, a.camp_name,
               (a.t4 + a.t5) AS kills_gain, a.deads,
               a.KP AS kp_gain,
               a.healed_troops,
               (a.t4*w.X + a.t5*w.Y + a.deads*w.Z) AS dkp,
               ISNULL(contrib.acclaim_gain, 0) AS acclaim_gain
        FROM dbo.fn_KVK_Camp_Aggregated(?) a
        OUTER APPLY (
            SELECT SUM(ISNULL(cw.cur_contribute_gain, 0)) AS acclaim_gain
            FROM KVK.KVK_Camp_Windowed cw
            JOIN KVK.KVK_Windows ww
              ON ww.KVK_NO = cw.KVK_NO
             AND ww.WindowName = cw.WindowName
             AND ww.StartScanID IS NOT NULL
            WHERE cw.KVK_NO = ?
              AND cw.campid = a.campid
        ) contrib
        CROSS APPLY (
            SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
            FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
        ) w
        ORDER BY {_camp_order_clause(sort_by)};
        """,
        (kvk_no, kvk_no, kvk_no),
    )
    return _fetch_all(cursor)


def fetch_kingdom_summary(cursor: Any, kvk_no: int, kingdom: int) -> list[dict[str, Any]]:
    """Return the existing own-kingdom aggregate row plus contribution fields."""
    cursor.execute(
        """
        WITH W AS (SELECT WindowName FROM KVK.KVK_Windows WHERE KVK_NO=? AND StartScanID IS NOT NULL),
             Agg AS (
               SELECT SUM(ISNULL(t4_kills,0)) AS t4, SUM(ISNULL(t5_kills,0)) AS t5, SUM(ISNULL(deads,0)) AS deads,
                      SUM(ISNULL(healed_troops,0)) AS healed_troops,
                      SUM(ISNULL(kp_gain,0)) AS kp_gain,
                      SUM(ISNULL(cur_contribute_gain,0)) AS acclaim_gain
               FROM KVK.KVK_Kingdom_Windowed kw
               JOIN W ON W.WindowName = kw.WindowName
               WHERE kw.KVK_NO=? AND kw.kingdom=?
             ),
             Wt AS (
               SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
               FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
             )
        SELECT (a.t4+a.t5) AS kills_gain, a.deads, a.healed_troops, a.kp_gain,
               (a.t4*X + a.t5*Y + a.deads*Z) AS dkp,
               a.acclaim_gain
        FROM Agg a CROSS JOIN Wt;
        """,
        (kvk_no, kvk_no, kingdom, kvk_no),
    )
    return _fetch_all(cursor)


def fetch_camp_mapping(cursor: Any, kvk_no: int, kingdom: int) -> dict[str, Any] | None:
    cursor.execute(
        "SELECT TOP 1 CampID, CampName FROM KVK.KVK_CampMap WHERE KVK_NO=? AND Kingdom=?",
        (kvk_no, kingdom),
    )
    return fetch_one_dict(cursor)


def fetch_camp_summary(cursor: Any, kvk_no: int, camp_id: int) -> list[dict[str, Any]]:
    """Return the existing own-camp aggregate row plus contribution fields."""
    cursor.execute(
        """
        WITH W AS (SELECT WindowName FROM KVK.KVK_Windows WHERE KVK_NO=? AND StartScanID IS NOT NULL),
             Agg AS (
               SELECT SUM(ISNULL(t4_kills,0)) AS t4, SUM(ISNULL(t5_kills,0)) AS t5, SUM(ISNULL(deads,0)) AS deads,
                      SUM(ISNULL(healed_troops,0)) AS healed_troops,
                      SUM(ISNULL(kp_gain,0)) AS kp_gain,
                      SUM(ISNULL(cur_contribute_gain,0)) AS acclaim_gain
               FROM KVK.KVK_Camp_Windowed cw
               JOIN W ON W.WindowName = cw.WindowName
               WHERE cw.KVK_NO=? AND cw.campid=?
             ),
             Wt AS (
               SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
               FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
             )
        SELECT (a.t4+a.t5) AS kills_gain, a.deads, a.healed_troops, a.kp_gain,
               (a.t4*X + a.t5*Y + a.deads*Z) AS dkp,
               a.acclaim_gain
        FROM Agg a CROSS JOIN Wt;
        """,
        (kvk_no, kvk_no, camp_id, kvk_no),
    )
    return _fetch_all(cursor)


def fetch_allkingdom_reporting_rows(
    kvk_no: int, our_kingdom: int
) -> dict[str, list[dict[str, Any]]]:
    """Fetch all raw row sets needed for the all-kingdom KVK report."""
    conn = get_conn_with_retries()
    with conn:
        cursor = conn.cursor()
        logger.info("[KVK REPORTING] loading all-kingdom rows kvk_no=%s", kvk_no)
        rows = {
            "players_by_kills": fetch_top_players(cursor, kvk_no, sort_by="kills"),
            "players_by_deads": fetch_top_players(cursor, kvk_no, sort_by="deads"),
            "players_by_dkp": fetch_top_players(cursor, kvk_no, sort_by="dkp"),
            "kingdoms_by_kills": fetch_top_kingdoms(cursor, kvk_no, sort_by="kills"),
            "kingdoms_by_deads": fetch_top_kingdoms(cursor, kvk_no, sort_by="deads"),
            "kingdoms_by_dkp": fetch_top_kingdoms(cursor, kvk_no, sort_by="dkp"),
            "camps_by_kills": fetch_top_camps(cursor, kvk_no, sort_by="kills"),
            "camps_by_deads": fetch_top_camps(cursor, kvk_no, sort_by="deads"),
            "camps_by_dkp": fetch_top_camps(cursor, kvk_no, sort_by="dkp"),
            "our_top_players": fetch_top_players(
                cursor, kvk_no, sort_by="kills", kingdom=our_kingdom
            ),
            "our_kingdom": fetch_kingdom_summary(cursor, kvk_no, our_kingdom),
        }

        camp_mapping = fetch_camp_mapping(cursor, kvk_no, our_kingdom)
        if camp_mapping:
            values = list(camp_mapping.values())
            camp_id = int(values[0]) if values and values[0] is not None else None
            camp_name = str(values[1]) if len(values) > 1 and values[1] is not None else "Our Camp"
        else:
            camp_id = None
            camp_name = "Our Camp"

        camp_rows = fetch_camp_summary(cursor, kvk_no, camp_id) if camp_id is not None else []
        rows["our_camp"] = [{"camp_name": camp_name, **camp_rows[0]}] if camp_rows else []
        return rows
