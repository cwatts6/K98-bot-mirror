# stats_alerts/allkingdoms.py
import logging

from constants import OUR_KINGDOM
from file_utils import cursor_row_to_dict, fetch_one_dict, get_conn_with_retries

logger = logging.getLogger(__name__)


def load_allkingdom_blocks(kvk_no: int) -> dict[str, list[dict]]:
    conn = get_conn_with_retries()
    with conn:
        c = conn.cursor()

        def _run_topN(query: str, params: tuple) -> list[dict]:
            c.execute(query, params)
            rows = [cursor_row_to_dict(c, row) for row in c.fetchall()]
            return rows

        player_q = """
        SELECT TOP 5 p.name, p.kingdom, p.campid,
               (p.t4 + p.t5) AS kills_gain,
               p.deads,
               p.healed_troops,
               p.KP AS kp_gain,
               (p.t4*w.X + p.t5*w.Y + p.deads*w.Z) AS dkp
        FROM dbo.fn_KVK_Player_Aggregated(?) p
        CROSS APPLY (
            SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
            FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
        ) w
        ORDER BY kills_gain DESC;
        """
        p_kills = _run_topN(player_q, (kvk_no, kvk_no))

        player_q_deads = player_q.replace("ORDER BY kills_gain DESC", "ORDER BY p.deads DESC")
        p_deads = _run_topN(player_q_deads, (kvk_no, kvk_no))

        player_q_dkp = player_q.replace("ORDER BY kills_gain DESC", "ORDER BY dkp DESC")
        p_dkp = _run_topN(player_q_dkp, (kvk_no, kvk_no))

        # Our kingdom top players (use aggregated fn so we have kp/healed/dkp)
        c.execute(
            """
            SELECT TOP 5 p.name, p.kingdom, p.campid,
                   (p.t4 + p.t5) AS kills_gain,
                   p.deads,
                   p.healed_troops,
                   p.KP AS kp_gain,
                   (p.t4*w.X + p.t5*w.Y + p.deads*w.Z) AS dkp
            FROM dbo.fn_KVK_Player_Aggregated(?) p
            CROSS APPLY (
                SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
                FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
            ) w
            WHERE p.kingdom = ?
            ORDER BY kills_gain DESC;
            """,
            (kvk_no, kvk_no, OUR_KINGDOM),
        )
        our_players_top5 = [cursor_row_to_dict(c, row) for row in c.fetchall()]

        # Our kingdom aggregated stats
        c.execute(
            """
            WITH W AS (SELECT WindowName FROM KVK.KVK_Windows WHERE KVK_NO=? AND StartScanID IS NOT NULL),
                 Agg AS (
                   SELECT SUM(ISNULL(t4_kills,0)) AS t4, SUM(ISNULL(t5_kills,0)) AS t5, SUM(ISNULL(deads,0)) AS deads,
                          SUM(ISNULL(healed_troops,0)) AS healed_troops,
                          SUM(ISNULL(kp_gain,0)) AS kp_gain
                   FROM KVK.KVK_Kingdom_Windowed kw
                   JOIN W ON W.WindowName = kw.WindowName
                   WHERE kw.KVK_NO=? AND kw.kingdom=?
                 ),
                 Wt AS (
                   SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
                   FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
                 )
            SELECT (a.t4+a.t5) AS kills_gain, a.deads, a.healed_troops, a.kp_gain,
                   (a.t4*X + a.t5*Y + a.deads*Z) AS dkp
            FROM Agg a CROSS JOIN Wt;
            """,
            (kvk_no, kvk_no, OUR_KINGDOM, kvk_no),
        )
        our_kingdom = [cursor_row_to_dict(c, row) for row in c.fetchall()]

        kingdoms_q = """
        SELECT TOP 5 a.kingdom,
               (a.t4 + a.t5) AS kills_gain,
               a.deads,
               a.KP AS kp_gain,
               a.healed_troops,
               (a.t4*w.X + a.t5*w.Y + a.deads*w.Z) AS dkp
        FROM dbo.fn_KVK_Kingdom_Aggregated(?) a
        CROSS APPLY (
            SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
            FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
        ) w
        ORDER BY kills_gain DESC;
        """
        k_kills = _run_topN(kingdoms_q, (kvk_no, kvk_no))
        kingdoms_q_deads = kingdoms_q.replace("ORDER BY kills_gain DESC", "ORDER BY a.deads DESC")
        k_deads = _run_topN(kingdoms_q_deads, (kvk_no, kvk_no))
        kingdoms_q_dkp = kingdoms_q.replace("ORDER BY kills_gain DESC", "ORDER BY dkp DESC")
        k_dkp = _run_topN(kingdoms_q_dkp, (kvk_no, kvk_no))

        camps_q = """
        SELECT TOP 5 a.campid, a.camp_name,
               (a.t4 + a.t5) AS kills_gain, a.deads,
               a.KP AS kp_gain,
               a.healed_troops,
               (a.t4*w.X + a.t5*w.Y + a.deads*w.Z) AS dkp
        FROM dbo.fn_KVK_Camp_Aggregated(?) a
        CROSS APPLY (
            SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
            FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
        ) w
        ORDER BY kills_gain DESC;
        """
        c_kills = _run_topN(camps_q, (kvk_no, kvk_no))
        camps_q_deads = camps_q.replace("ORDER BY kills_gain DESC", "ORDER BY a.deads DESC")
        c_deads = _run_topN(camps_q_deads, (kvk_no, kvk_no))
        camps_q_dkp = camps_q.replace("ORDER BY kills_gain DESC", "ORDER BY dkp DESC")
        c_dkp = _run_topN(camps_q_dkp, (kvk_no, kvk_no))

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
                   SELECT SUM(ISNULL(t4_kills,0)) AS t4, SUM(ISNULL(t5_kills,0)) AS t5, SUM(ISNULL(deads,0)) AS deads,
                          SUM(ISNULL(healed_troops,0)) AS healed_troops,
                          SUM(ISNULL(kp_gain,0)) AS kp_gain
                   FROM KVK.KVK_Camp_Windowed cw
                   JOIN W ON W.WindowName = cw.WindowName
                   WHERE cw.KVK_NO=? AND cw.campid=?
                 ),
                 Wt AS (
                   SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
                   FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
                 )
            SELECT (a.t4+a.t5) AS kills_gain, a.deads, a.healed_troops, a.kp_gain,
                   (a.t4*X + a.t5*Y + a.deads*Z) AS dkp
            FROM Agg a CROSS JOIN Wt;
            """,
                (kvk_no, kvk_no, our_camp_id, kvk_no),
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
        "our_top_players": our_players_top5,
        "our_kingdom": our_kingdom,
        "our_camp": [{"camp_name": our_camp_name, **our_camp[0]}] if our_camp else [],
    }
