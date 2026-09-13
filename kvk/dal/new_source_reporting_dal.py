"""One transaction pins desired configuration, routing, selection and immutable rows."""

from kvk.dal.new_source_config_dal import desired_config, locked_period
from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from kvk.dal.new_source_publication_dal import publication_results, result_digest
from kvk.schemas.new_source_schema import SOURCE_KEY


def load_snapshot(connect, *, kvk_no, period_id):
    """Return a private DAL envelope; no cache, fallback, rendering or activation.

    Desired and selected configurations are separate even after restart or lost notification.
    Decimal rows stay Decimal. Consumer DTO construction belongs to the later reader service.
    """
    with transaction(connect) as cursor:
        routing, selected, requests = locked_period(cursor, kvk_no, period_id)
        desired = desired_config(cursor, selected, requests)
        if not selected:
            return {
                "source_key": SOURCE_KEY,
                "kvk_no": kvk_no,
                "period_id": period_id,
                "routing": routing,
                "desired_config_id": desired,
                "publication": None,
                "is_current": False,
                "current_period_state": "not_received",
            }
        cursor.execute(
            "SELECT * FROM KVK.SourcePublication WHERE PublicationID=?", selected["PublicationID"]
        )
        publication = one(cursor)
        if not publication or publication["BuildState"] != "complete":
            raise SourceConflict("Selected publication is incomplete.")
        player_rows = publication_results(cursor, publication["PublicationID"])
        if len(player_rows) != publication["ResultCount"] or result_digest(player_rows) != bytes(
            publication["ManifestHash"]
        ):
            raise SourceConflict("Selected publication failed integrity verification.")
        aggregate = {}
        for table, key in (
            ("SourceKingdomReportRow", "Kingdom"),
            ("SourceCampReportRow", "CampID"),
        ):
            cursor.execute(
                "SELECT * FROM KVK." + table + " WHERE RevisionID=? ORDER BY " + key,
                publication["AggregateRevisionID"],
            )
            aggregate[table] = rows(cursor)
        if (len(aggregate["SourceKingdomReportRow"]), len(aggregate["SourceCampReportRow"])) != (
            publication["KingdomCount"],
            publication["CampCount"],
        ):
            raise SourceConflict("Selected aggregate revision failed completeness verification.")
        current = desired == str(publication["ConfigVersionID"])
        return {
            "source_key": SOURCE_KEY,
            "kvk_no": kvk_no,
            "period_id": period_id,
            "routing": routing,
            "selection": selected,
            "desired_config_id": desired,
            "pending_request": (
                requests[0]
                if requests and requests[0]["RequestState"] in ("pending", "requested")
                else None
            ),
            "publication": publication,
            "players": player_rows,
            "aggregates": aggregate,
            "is_current": current,
            "current_period_state": (
                publication["PeriodState"] if current else "missing_configuration"
            ),
        }
