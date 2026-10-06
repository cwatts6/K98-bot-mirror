"""Read-only public routing authority. No admission, selection or export writes."""

from dataclasses import replace
import logging

from file_utils import get_conn_with_retries
from kvk.dal.new_source_import_dal import SourceConflict, lock_scope, one, rows, transaction
from kvk.dal.season_source_dal import lock_season
from kvk.dal.source_update_dal import INPUT_COLUMNS, update_hash
from kvk.models.source_integration import PUBLIC_REPORT_CAPABILITY, SeasonRead, identity
from kvk.schemas.new_source_schema import SOURCE_KEY

logger = logging.getLogger(__name__)


def validate_complete(read, selection, update, publication):
    """Verify the sealed tuple, including relationships not guaranteed by SQL FKs.

    Do not call writer eligibility validation here: later desired configuration or
    accepted revisions must not disqualify an immutable previous complete result.
    """
    if not selection or not update or not publication:
        raise SourceConflict("Complete selection is missing its immutable inputs.")
    for record in (selection, update, publication):
        if (
            record["SourceKey"] != SOURCE_KEY
            or record["KVK_NO"] != read.kvk_no
            or identity(record["PeriodID"]) != read.period_id
        ):
            raise SourceConflict("Complete selection scope differs.")
    if (
        identity(update["ChoiceID"]) != read.choice_id
        or identity(selection["UpdateID"]) != identity(update["UpdateID"])
        or identity(selection["PublicationID"]) != identity(publication["PublicationID"])
        or update["UpdateState"] != "selected"
        or publication["BuildState"] != "complete"
        or bytes(update["ContentHash"]) != update_hash(update)
        or any(
            update[k] != publication[k]
            for k in (*INPUT_COLUMNS, "ConfigVersionID", "RosterID", "PeriodKey")
        )
        or not update["StartRevisionID"]
        or not update["EndRevisionID"]
    ):
        raise SourceConflict("Complete selection and sealed publication differ.")
    no_fight = update["UpdateKind"] == "no_fight"
    if no_fight:
        if (
            update["StartScanID"] != update["EndScanID"]
            or update["StartRevisionID"] != update["EndRevisionID"]
            or update["AggregateRevisionID"] is not None
            or update["AggregateReportID"] is not None
            or publication["AggregateState"] != "not_applicable"
        ):
            raise SourceConflict("Invalid complete no-fight result.")
    elif (
        update["UpdateKind"] not in {"fight", "overall"}
        or not update["AggregateRevisionID"]
        or not update["AggregateReportID"]
        or publication["AggregateState"] not in {"live", "final", "corrected_final"}
        or (update["UpdateKind"] == "overall" and publication["AggregateState"] == "live")
    ):
        raise SourceConflict("Complete combat result requires its supplied aggregate.")


def resolve_season_read(kvk_no, *, period_id=None, connect=None):
    """Resolve each request under the writer's season-first lock order.

    Only small authority rows are loaded under the mutex. Immutable result rows,
    verification and presentation are loaded after this transaction has closed.
    Missing schema/database/choice is unavailable, never implicit legacy.
    """
    read = SeasonRead(kvk_no, period_id=period_id)
    try:
        with transaction(connect or get_conn_with_retries) as cursor:
            lock_scope(cursor, kvk_no)
            choice = lock_season(cursor, kvk_no)
            if not choice:
                return replace(read, reason="season_choice_missing")
            read = replace(
                read,
                source_key=choice["SourceKey"],
                choice_id=choice["ChoiceID"],
                season_version=choice["SeasonVersion"],
            )
            if read.source_key == "legacy_full_data":
                return replace(read, availability="legacy", reason="legacy_source")
            cursor.execute(
                "SELECT * FROM KVK.SourceRouting WITH (UPDLOCK,HOLDLOCK) WHERE KVK_NO=?", kvk_no
            )
            routing = one(cursor)
            if not routing or routing["SourceKey"] != SOURCE_KEY:
                return replace(read, reason="routing_missing")
            read = replace(
                read,
                routing_version=routing["RoutingVersion"],
                capabilities_version=routing["CapabilitiesVersion"],
            )
            if not routing["Enabled"]:
                return replace(read, reason="serving_disabled")
            if read.capabilities_version != PUBLIC_REPORT_CAPABILITY:
                return replace(read, reason="capability_unsupported")
            selected_period = period_id or routing["DisplayPeriodID"]
            if selected_period is None:
                return replace(read, reason="display_period_missing")
            read = replace(read, period_id=identity(selected_period))
            # Same ordering as locked_period: component rows, complete rows, then config.
            cursor.execute(
                "SELECT PeriodID FROM KVK.SourceSelection WITH (UPDLOCK,HOLDLOCK) WHERE SourceKey=? AND KVK_NO=? ORDER BY PeriodID",
                SOURCE_KEY,
                kvk_no,
            )
            cursor.fetchall()
            cursor.execute(
                "SELECT * FROM KVK.SourceCompleteSelection WITH (UPDLOCK,HOLDLOCK) WHERE SourceKey=? AND KVK_NO=? ORDER BY PeriodID",
                SOURCE_KEY,
                kvk_no,
            )
            complete = next(
                (r for r in rows(cursor) if identity(r["PeriodID"]) == read.period_id), None
            )
            cursor.execute(
                "SELECT TOP (1) r.DesiredConfigVersionID,c.ConfigVersion FROM KVK.SourceConfigRequest r JOIN KVK.SourceConfigVersion c ON c.ConfigVersionID=r.DesiredConfigVersionID WHERE r.SourceKey=? AND r.KVK_NO=? AND r.PeriodID=? AND r.RequestState<>'rejected' ORDER BY c.ConfigVersion DESC",
                SOURCE_KEY,
                kvk_no,
                read.period_id,
            )
            requested = one(cursor)
            update = publication = None
            if complete:
                cursor.execute(
                    "SELECT * FROM KVK.SourceUpdate WHERE UpdateID=?", complete["UpdateID"]
                )
                update = one(cursor)
                cursor.execute(
                    "SELECT * FROM KVK.SourcePublication WHERE PublicationID=?",
                    complete["PublicationID"],
                )
                publication = one(cursor)
                validate_complete(read, complete, update, publication)
                cursor.execute(
                    "SELECT ConfigVersion FROM KVK.SourceConfigVersion WHERE ConfigVersionID=?",
                    publication["ConfigVersionID"],
                )
                config = one(cursor)
                if not config:
                    raise SourceConflict("Selected configuration is missing.")
                desired = (
                    requested["DesiredConfigVersionID"]
                    if requested and requested["ConfigVersion"] > config["ConfigVersion"]
                    else publication["ConfigVersionID"]
                )
            else:
                desired = requested["DesiredConfigVersionID"] if requested else None
            read = replace(read, desired_config_id=desired)
            base_update = complete["UpdateID"] if complete else None
            cursor.execute(
                "SELECT TOP (1) UpdateID,Version,UpdateState FROM KVK.SourceUpdate WHERE SourceKey=? AND KVK_NO=? AND PeriodID=? AND UpdateState IN ('waiting_player','waiting_aggregate','ready') AND (CAST(? AS uniqueidentifier) IS NULL OR ConfigVersionID=?) AND ((CAST(? AS uniqueidentifier) IS NULL AND BaseUpdateID IS NULL) OR BaseUpdateID=?) ORDER BY ConfirmedUTC DESC,UpdateID",
                SOURCE_KEY,
                kvk_no,
                read.period_id,
                desired,
                desired,
                base_update,
                base_update,
            )
            pending = one(cursor)
            if pending:
                read = replace(
                    read,
                    pending_update_id=pending["UpdateID"],
                    pending_update_version=pending["Version"],
                )
            if not complete:
                return replace(read, reason=pending["UpdateState"] if pending else "waiting_pair")
            current = (
                identity(publication["ConfigVersionID"]) == read.desired_config_id and not pending
            )
            return replace(
                read,
                update_id=update["UpdateID"],
                update_version=update["Version"],
                publication_id=publication["PublicationID"],
                public_selection_version=complete["PublicSelectionVersion"],
                selected_config_id=publication["ConfigVersionID"],
                roster_id=publication["RosterID"],
                availability="current" if current else "previous_complete",
                reason=(
                    "complete"
                    if current
                    else (
                        "configuration_pending"
                        if identity(publication["ConfigVersionID"]) != read.desired_config_id
                        else pending["UpdateState"]
                    )
                ),
            )
    except Exception as exc:
        # Do not expose SQL text, connection details, private confirmation or raw exceptions.
        logger.warning(
            "[KVK ROUTING] unavailable kvk_no=%s error_type=%s", kvk_no, type(exc).__name__
        )
        return replace(read, availability="unavailable", reason="authority_unavailable")
