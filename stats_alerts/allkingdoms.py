# stats_alerts/allkingdoms.py
import logging

from constants import OUR_KINGDOM
from file_utils import cursor_row_to_dict, fetch_one_dict, get_conn_with_retries

logger = logging.getLogger(__name__)


def load_allkingdom_blocks(kvk_no: int) -> dict[str, list[dict]]:
    conn = get_conn_with_retries()
    with conn:
        c = conn.cursor()

        def _run_top3(query: str, params: tuple) -> list[dict]:
            c.execute(query, params)
            rows = [cursor_row_to_dict(c, row) for row in c.fetchall()]
            return rows

        player_q = """
        SELECT TOP 3 p.name, p.kingdom, p.campid,
               (p.t4 + p.t5) AS kills_gain,
               p.deads,
               CAST(((p.t4*w.X + p.t5*w.Y + p.deads*w.Z) / NULLIF(p.sp,0)) AS float) AS dkp
        FROM dbo.fn_KVK_Player_Aggregated(?) p
        CROSS APPLY (
            SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
            FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
        ) w
        ORDER BY kills_gain DESC;
        """
        p_kills = _run_top3(player_q, (kvk_no, kvk_no))

        player_q_deads = player_q.replace("ORDER BY kills_gain DESC", "ORDER BY p.deads DESC")
        p_deads = _run_top3(player_q_deads, (kvk_no, kvk_no))

        player_q_dkp = player_q.replace("ORDER BY kills_gain DESC", "ORDER BY dkp DESC")
        p_dkp = _run_top3(player_q_dkp, (kvk_no, kvk_no))

        c.execute(
            """
            WITH W AS (
              SELECT WindowName FROM KVK.KVK_Windows WHERE KVK_NO=? AND StartScanID IS NOT NULL
            ), Agg AS (
              SELECT p.governor_id,
                     MAX(p.name)    AS name,
                     MAX(p.kingdom) AS kingdom,
                     SUM(ISNULL(p.t4_kills,0) + ISNULL(p.t5_kills,0)) AS kills_gain
              FROM KVK.KVK_Player_Windowed p
              JOIN W ON W.WindowName = p.WindowName
              WHERE p.KVK_NO = ? AND p.kingdom = ?
              GROUP BY p.governor_id
            )
            SELECT TOP 3 name, kills_gain
            FROM Agg
            ORDER BY kills_gain DESC;
            """,
            (kvk_no, kvk_no, OUR_KINGDOM),
        )
        our_players_top3 = [cursor_row_to_dict(c, row) for row in c.fetchall()]

        kingdoms_q = """
        SELECT TOP 3 a.kingdom,
               (a.t4 + a.t5) AS kills_gain,
               a.deads,
               CAST(((a.t4*w.X + a.t5*w.Y + a.deads*w.Z) / NULLIF(a.denom,0)) AS float) AS dkp
        FROM dbo.fn_KVK_Kingdom_Aggregated(?) a
        CROSS APPLY (
            SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
            FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
        ) w
        ORDER BY kills_gain DESC;
        """
        k_kills = _run_top3(kingdoms_q, (kvk_no, kvk_no))
        kingdoms_q_deads = kingdoms_q.replace("ORDER BY kills_gain DESC", "ORDER BY a.deads DESC")
        k_deads = _run_top3(kingdoms_q_deads, (kvk_no, kvk_no))
        kingdoms_q_dkp = kingdoms_q.replace("ORDER BY kills_gain DESC", "ORDER BY dkp DESC")
        k_dkp = _run_top3(kingdoms_q_dkp, (kvk_no, kvk_no))

        camps_q = """
        SELECT TOP 3 a.campid, a.camp_name,
               (a.t4 + a.t5) AS kills_gain, a.deads,
               CAST(((a.t4*w.X + a.t5*w.Y + a.deads*w.Z)/NULLIF(a.denom,0)) AS float) AS dkp
        FROM dbo.fn_KVK_Camp_Aggregated(?) a
        CROSS APPLY (
            SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
            FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
        ) w
        ORDER BY kills_gain DESC;
        """
        c_kills = _run_top3(camps_q, (kvk_no, kvk_no))
        camps_q_deads = camps_q.replace("ORDER BY kills_gain DESC", "ORDER BY a.deads DESC")
        c_deads = _run_top3(camps_q_deads, (kvk_no, kvk_no))
        camps_q_dkp = camps_q.replace("ORDER BY kills_gain DESC", "ORDER BY dkp DESC")
        c_dkp = _run_top3(camps_q_dkp, (kvk_no, kvk_no))

        c.execute(
            "SELECT TOP 1 CampID, CampName FROM KVK.KVK_CampMap WHERE KVK_NO=? AND Kingdom=?",
            (kvk_no, OUR_KINGDOM),
        )
        rowd = fetch_one_dict(c)
        if rowd:
            vals = list(rowd.values())
            our_camp_id = int(vals[0]) if vals and vals[0] is not None else None
            our_camp_name = str(vals[1]) if len(vals) > 1 and vals[1] is not None else "Our Camp"
        else:
            our_camp_id = None
            our_camp_name = "Our Camp"

        if our_camp_id is not None:
            c.execute(
                """
            WITH W AS (SELECT WindowName FROM KVK.KVK_Windows WHERE KVK_NO=? AND StartScanID IS NOT NULL),
                 Agg AS (
                   SELECT SUM(ISNULL(t4_kills,0)) AS t4, SUM(ISNULL(t5_kills,0)) AS t5, SUM(ISNULL(deads,0)) AS deads
                   FROM KVK.KVK_Camp_Windowed cw
                   JOIN W ON W.WindowName = cw.WindowName
                   WHERE cw.KVK_NO=? AND cw.campid=?
                 ),
                 Den AS (
                   SELECT SUM(sp) AS denom
                   FROM (
                     SELECT p.governor_id, MAX(ISNULL(p.starting_power,0)) AS sp
                     FROM KVK.KVK_Player_Windowed p
                     WHERE p.KVK_NO=? AND p.campid=?
                     GROUP BY p.governor_id
                   ) d
                 ),
                 Wt AS (
                   SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
                   FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
                 )
            SELECT (a.t4+a.t5) AS kills_gain, a.deads,
                   CAST(((a.t4*X + a.t5*Y + a.deads*Z)/NULLIF(d.denom,0)) AS float) AS dkp
            FROM Agg a CROSS JOIN Den d CROSS JOIN Wt;
            """,
                (kvk_no, kvk_no, our_camp_id, kvk_no, our_camp_id, kvk_no),
            )
            our_camp = [cursor_row_to_dict(c, row) for row in c.fetchall()]
        else:
            our_camp = []

    return {
        "players_by_kills": p_kills,
        "players_by_deads": p_deads,
        "players_by_dkp": p_dkp,
        "kingdoms_by_kills": k_kills,
        "kingdoms_by_deads": k_deads,
        "kingdoms_by_dkp": k_dkp,
        "camps_by_kills": c_kills,
        "camps_by_deads": c_deads,
        "camps_by_dkp": c_dkp,
        "our_top_players": our_players_top3,
        # Previously this was a placeholder expression that always produced [].
        # Return an empty list (or a populated list of dicts) instead of an int.
        # This keeps the return type consistent with other blocks that are lists
        # and prevents consumer code from indexing into an integer.
        "our_kingdom": [],
        "our_camp": [{"camp_name": our_camp_name, **our_camp[0]}] if our_camp else [],
    }


# New helper for Kingdom Summary (KS table) so embeds can reuse
def load_kingdom_summary() -> dict | None:
    """
    Load a single-row kingdom summary from ROK_TRACKER.dbo.KS.

    Returns a dict with the columns (if present) or None on error / missing data.
    Keys typically present:
      KINGDOM_POWER, Governors, KP, DEAD, KINGDOM_RANK, KINGDOM_SEED
    """
    try:
        conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT TOP (1)
                    [KINGDOM_POWER],
                    [Governors],
                    [KP],
                    [DEAD],
                    [KINGDOM_RANK],
                    [KINGDOM_SEED]
                FROM ROK_TRACKER.dbo.KS
                """
            )
            row = fetch_one_dict(cur)
            return row if row else None
    except Exception:
        logger.exception("[ALLKINGDOMS] Failed to load kingdom summary (KS)")
        return None
