"""One transaction pins desired configuration, routing, selection and immutable rows."""

from kvk.dal.new_source_config_dal import desired_config, locked_period
from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from kvk.dal.new_source_publication_dal import publication_results, result_digest
from kvk.schemas.new_source_schema import SOURCE_KEY


def load_complete_snapshot(connect, *, read):
    """Read the pinned immutable result after releasing routing/selection locks."""
    from kvk.dal.source_routing_dal import validate_complete

    if not read.available or read.source_key != SOURCE_KEY:
        raise SourceConflict("An eligible complete source read is required.")
    with transaction(connect) as cursor:
        cursor.execute(
            "SELECT * FROM KVK.SourcePublication WHERE PublicationID=?", read.publication_id
        )
        publication = one(cursor)
        cursor.execute("SELECT * FROM KVK.SourceUpdate WHERE UpdateID=?", read.update_id)
        update = one(cursor)
        selection = dict(
            SourceKey=read.source_key,
            KVK_NO=read.kvk_no,
            PeriodID=read.period_id,
            UpdateID=read.update_id,
            PublicationID=read.publication_id,
        )
        validate_complete(read, selection, update, publication)
        if (
            str(publication["ConfigVersionID"]).lower() != read.selected_config_id
            or str(publication["RosterID"]).lower() != read.roster_id
            or update["Version"] != read.update_version
        ):
            raise SourceConflict("Pinned update identity changed.")
        player_rows = publication_results(cursor, read.publication_id)
        if (
            len(player_rows) != publication["EligibleCount"]
            or len(player_rows) != publication["ResultCount"]
            or result_digest(player_rows) != bytes(publication["ManifestHash"])
        ):
            raise SourceConflict("Complete player results failed integrity verification.")
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
            raise SourceConflict("Complete aggregate rows failed completeness verification.")
        return dict(
            source_key=SOURCE_KEY,
            kvk_no=read.kvk_no,
            period_id=read.period_id,
            publication=publication,
            selection={"SelectionVersion": read.public_selection_version},
            desired_config_id=read.desired_config_id,
            players=player_rows,
            aggregates=aggregate,
            is_current=read.availability == "current",
            current_period_state=(
                publication["PeriodState"] if read.availability == "current" else read.reason
            ),
        )


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
