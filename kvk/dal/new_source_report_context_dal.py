"""Exact publication context for the reader projection, with bounded player pages."""

from kvk.dal.kvk_admin_dal import fetch_source_report_metadata
from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from kvk.models.new_source_history import page_size
from kvk.models.source_integration import identity
from kvk.schemas.new_source_schema import INT_MAX, SOURCE_KEY


def load_report_context(*, connect, publication_id, kvk_no):
    """Read labels and revision uses without consulting current selection pointers."""
    publication_id = identity(publication_id)
    if type(kvk_no) is not int or not 1 <= kvk_no <= INT_MAX:
        raise ValueError("Invalid report season.")
    with transaction(connect) as cursor:
        cursor.execute(
            "SELECT * FROM KVK.SourcePublication WHERE PublicationID=? AND SourceKey=? AND KVK_NO=?",
            publication_id,
            SOURCE_KEY,
            kvk_no,
        )
        publication = one(cursor)
        if not publication or publication["BuildState"] != "complete":
            raise SourceConflict("Complete pinned report publication is unavailable.")
        cursor.execute(
            "SELECT B0RevisionID FROM KVK.SourceRoster WHERE RosterID=? AND SourceKey=? AND KVK_NO=?",
            publication["RosterID"],
            SOURCE_KEY,
            kvk_no,
        )
        roster = one(cursor)
        if not roster:
            raise SourceConflict("Pinned report roster is unavailable.")
        cursor.execute(
            "SELECT w.PeriodKey,w.WindowName,w.WindowSeq,w.StartScanID,w.EndScanID,w.Notes,"
            "p.PeriodID,p.PeriodKind FROM KVK.SourceWindowConfig w JOIN KVK.SourcePeriod p "
            "ON p.SourceKey=w.SourceKey AND p.KVK_NO=w.KVK_NO AND p.PeriodKey=w.PeriodKey "
            "WHERE w.ConfigVersionID=? AND w.SourceKey=? AND w.KVK_NO=? "
            "ORDER BY w.WindowSeq,w.PeriodKey",
            publication["ConfigVersionID"],
            SOURCE_KEY,
            kvk_no,
        )
        windows = rows(cursor)
    metadata = fetch_source_report_metadata(
        connect,
        {
            "publication": publication,
            "desired_config_id": publication["ConfigVersionID"],
            "period_id": publication["PeriodID"],
            "source_key": SOURCE_KEY,
            "kvk_no": kvk_no,
        },
    )
    revisions = {
        "baseline": roster["B0RevisionID"],
        "start": publication["StartRevisionID"],
        "end": publication["EndRevisionID"],
        "aggregate": publication["AggregateRevisionID"],
    }
    return {
        "publication": publication,
        "metadata": metadata,
        "windows": windows,
        "revisions": revisions,
    }


def iter_player_powers(*, connect, context, batch_size=250):
    """Roster identity wins; absent endpoints stay absent, not zero or a newer revision.

    Context must come from load_report_context. No live transaction spans yielded pages.
    The accepted source revisions and roster are immutable by the source DAL contract.
    """
    page_size(batch_size)
    pub, revisions = context["publication"], context["revisions"]
    after = 0
    while True:
        with transaction(connect) as cursor:
            cursor.execute(
                "SELECT TOP (?) m.GovernorID,m.b0_kingdom,"
                "b.power AS BaselinePower,b.troops_power AS BaselineTroopsPower,"
                "b.FieldStatusJson AS BaselineFieldStatusJson,"
                "s.power AS StartPower,s.troops_power AS StartTroopsPower,"
                "s.FieldStatusJson AS StartFieldStatusJson,"
                "e.power AS EndPower,e.troops_power AS EndTroopsPower,"
                "e.FieldStatusJson AS EndFieldStatusJson "
                "FROM KVK.SourceRosterMember m "
                "LEFT JOIN KVK.SourcePlayerSnapshot b ON b.GovernorID=m.GovernorID "
                "AND b.RevisionID=? AND b.SourceKey=? AND b.KVK_NO=? "
                "LEFT JOIN KVK.SourcePlayerSnapshot s ON s.GovernorID=m.GovernorID "
                "AND s.RevisionID=? AND s.SourceKey=? AND s.KVK_NO=? "
                "LEFT JOIN KVK.SourcePlayerSnapshot e ON e.GovernorID=m.GovernorID "
                "AND e.RevisionID=? AND e.SourceKey=? AND e.KVK_NO=? "
                "WHERE m.RosterID=? AND m.SourceKey=? AND m.KVK_NO=? AND m.GovernorID>? "
                "ORDER BY m.GovernorID",
                batch_size,
                revisions["baseline"],
                SOURCE_KEY,
                pub["KVK_NO"],
                revisions["start"],
                SOURCE_KEY,
                pub["KVK_NO"],
                revisions["end"],
                SOURCE_KEY,
                pub["KVK_NO"],
                pub["RosterID"],
                SOURCE_KEY,
                pub["KVK_NO"],
                after,
            )
            batch = rows(cursor)
        if not batch:
            return
        yield from batch
        after = batch[-1]["GovernorID"]
