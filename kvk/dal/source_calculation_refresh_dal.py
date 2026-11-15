"""Frozen selected-input authority for an explicit calculation-only correction."""

from datetime import UTC
import json

from kvk.dal.new_source_import_dal import SourceConflict, lock_scope, one, transaction
from kvk.dal.season_source_dal import require_source
from kvk.models.new_source_reporting import CALCULATION_VERSION
from kvk.schemas.new_source_schema import SOURCE_KEY

REFRESH_FIELDS = (
    "UpdateID",
    "PublicationID",
    "CalculationVersion",
    "PublicSelectionVersion",
    "ConfigVersionID",
    "RosterID",
    "StartScanID",
    "EndScanID",
    "StartRevisionID",
    "EndRevisionID",
    "AggregateRevisionID",
    "CoverageStartUTC",
    "CoverageEndUTC",
    "AsOfUTC",
)


def refresh_context(connect, season, period):
    with transaction(connect) as cursor:
        lock_scope(cursor, season)
        require_source(cursor, season, SOURCE_KEY)
        cursor.execute(
            "SELECT u.*,s.PublicationID,s.PublicSelectionVersion,p.CalculationVersion "
            "FROM KVK.SourceCompleteSelection s JOIN KVK.SourceUpdate u ON u.UpdateID=s.UpdateID "
            "JOIN KVK.SourcePublication p ON p.PublicationID=s.PublicationID "
            "WHERE s.SourceKey=? AND s.KVK_NO=? AND u.PeriodKey=? AND p.BuildState='complete'",
            SOURCE_KEY,
            season,
            period,
        )
        row = one(cursor)
        if not row:
            raise SourceConflict("Calculation refresh requires a selected complete publication.")
        result = {k: row[k] for k in REFRESH_FIELDS}
        for k in ("CoverageStartUTC", "CoverageEndUTC", "AsOfUTC"):
            result[k] = result[k].replace(tzinfo=UTC).isoformat()
        return result


def preview_inputs(connect, selected, confirmation_json, actor):
    from kvk.dal.new_source_publication_dal import publication_results
    from kvk.dal.new_source_recovery_dal import RecoveryDAL
    from kvk.dal.source_update_dal import load_update

    with transaction(connect) as cursor:
        update = load_update(cursor, selected["UpdateID"])
        original = publication_results(cursor, selected["PublicationID"])
    # Same explicit period assignment and correction authority as the proposed update.
    update = dict(update, ConfirmationJson=confirmation_json, ConfirmedBy=actor)
    data = RecoveryDAL(connect).load_inputs(update["KVK_NO"], update["PeriodID"], update=update)
    return data, original


def publication_result_hash(connect, publication_id):
    from kvk.dal.new_source_publication_dal import publication_results, result_digest

    with transaction(connect) as cursor:
        return result_digest(publication_results(cursor, publication_id)).hex()


def refresh_proof(record):
    proof = json.loads(record.get("ConfirmationJson") or "{}").get("calculation_refresh")
    if proof is None:
        return None
    if (
        not isinstance(proof, dict)
        or set(proof)
        != {"base_update_id", "base_publication_id", "from_calculation", "to_calculation"}
        or proof["to_calculation"] != CALCULATION_VERSION
        or not isinstance(proof["from_calculation"], str)
        or proof["from_calculation"] == CALCULATION_VERSION
        or proof["base_update_id"] != record.get("BaseUpdateID")
        or json.loads(record["ConfirmationJson"]).get("action") != "correct"
    ):
        raise SourceConflict("Invalid calculation refresh authority.")
    return proof


def validate_refresh(cursor, update, prior):
    from kvk.dal.source_update_dal import CONTEXT_COLUMNS, INPUT_COLUMNS, load_update

    proof = refresh_proof(update)
    if proof is None:
        return
    if not prior or prior["UpdateID"] not in (proof["base_update_id"], update["UpdateID"]):
        raise SourceConflict("Calculation refresh selection changed.")
    base = load_update(cursor, proof["base_update_id"])
    if any(update[k] != base[k] for k in (*CONTEXT_COLUMNS, *INPUT_COLUMNS)):
        raise SourceConflict(
            "Calculation refresh must retain all selected inputs and configuration."
        )
    cursor.execute(
        "SELECT * FROM KVK.SourcePublication WHERE PublicationID=? AND SourceKey=? AND KVK_NO=? AND PeriodID=? AND BuildState='complete'",
        proof["base_publication_id"],
        SOURCE_KEY,
        update["KVK_NO"],
        update["PeriodID"],
    )
    publication = one(cursor)
    if (
        not publication
        or publication["CalculationVersion"] != proof["from_calculation"]
        or any(publication[k] != base[k] for k in (*INPUT_COLUMNS, "ConfigVersionID", "RosterID"))
    ):
        raise SourceConflict("Calculation refresh base publication differs from retained inputs.")
