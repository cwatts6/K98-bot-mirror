"""Current season weights over existing immutable config and complete-update records."""

import json

from kvk.dal.new_source_config_dal import locked_period, snapshot_endpoint_request
from kvk.dal.new_source_import_dal import SourceConflict, one, rows
from kvk.dal.new_source_recovery_dal import current_config
from kvk.models.source_configuration import weight_values
from kvk.schemas.new_source_schema import SOURCE_KEY


def stored_weights(cursor, config_id):
    cursor.execute(
        "SELECT WeightT4X,WeightT5Y,WeightDeadsZ FROM KVK.SourceWeightConfig WHERE ConfigVersionID=?",
        config_id,
    )
    row = one(cursor)
    return tuple(row[k] for k in ("WeightT4X", "WeightT5Y", "WeightDeadsZ")) if row else None


def stale_weight_periods(cursor, season, coefficients):
    cursor.execute(
        "SELECT s.PeriodID,u.ConfigVersionID,w.WeightT4X,w.WeightT5Y,w.WeightDeadsZ FROM KVK.SourceCompleteSelection s "
        "JOIN KVK.SourceUpdate u ON u.UpdateID=s.UpdateID LEFT JOIN KVK.SourceWeightConfig w ON w.ConfigVersionID=u.ConfigVersionID "
        "WHERE s.SourceKey=? AND s.KVK_NO=?",
        SOURCE_KEY,
        season,
    )
    return {
        r["PeriodID"]
        for r in rows(cursor)
        if tuple(r[k] for k in ("WeightT4X", "WeightT5Y", "WeightDeadsZ")) != coefficients
    }


def selected_weights_current(cursor, season, coefficients):
    return not stale_weight_periods(cursor, season, coefficients)


def require_current_export_weights(cursor, intent, vector):
    from kvk.dal.source_admin_review_dal import SourceAdminReviewDAL

    expected = weight_values(
        SourceAdminReviewDAL.imported_configuration(cursor, intent["KVK_NO"])["weights"]
    )
    if any(
        stored_weights(cursor, config_id) != expected
        for config_id in {r["ConfigVersionID"] for r in vector}
    ):
        raise SourceConflict(
            "Export results need the current season weights; refresh the completed results first."
        )


def refresh_requests(cursor, season, imported, now):
    """Snapshot every period's current weights; missing inputs remain durable pending work."""
    coefficients = weight_values(imported["weights"])
    cursor.execute(
        "SELECT PeriodID,PeriodKey FROM KVK.SourcePeriod WHERE SourceKey=? AND KVK_NO=? ORDER BY PeriodID",
        SOURCE_KEY,
        season,
    )
    periods = rows(cursor)
    ready = []
    for period in periods:
        _, selected, requests = locked_period(cursor, season, period["PeriodID"])
        config_id = current_config(cursor, season, period["PeriodID"], selected, requests)
        if not config_id:
            continue
        cursor.execute(
            "SELECT c.RosterID,c.MappingDigest,w.StartScanID,w.EndScanID FROM KVK.SourceConfigVersion c JOIN KVK.SourceWindowConfig w ON w.ConfigVersionID=c.ConfigVersionID WHERE c.ConfigVersionID=? AND w.PeriodKey=?",
            config_id,
            period["PeriodKey"],
        )
        config = one(cursor)
        request = next((r for r in requests if r["DesiredConfigVersionID"] == config_id), None)
        cursor.execute(
            "SELECT u.* FROM KVK.SourceCompleteSelection s JOIN KVK.SourceUpdate u ON u.UpdateID=s.UpdateID WHERE s.SourceKey=? AND s.KVK_NO=? AND s.PeriodID=?",
            SOURCE_KEY,
            season,
            period["PeriodID"],
        )
        base = one(cursor)
        selected_stale = bool(
            base and stored_weights(cursor, base["ConfigVersionID"]) != coefficients
        )
        if stored_weights(cursor, config_id) != coefficients or (
            selected_stale
            and not (request and json.loads(request["ProvenanceJson"]).get("current_weights"))
        ):
            request = snapshot_endpoint_request(
                cursor,
                kvk_no=season,
                period_id=period["PeriodID"],
                base_config_id=config_id,
                new_start_scan_id=config["StartScanID"],
                new_end_scan_id=config["EndScanID"],
                actor="system:current_season_weights",
                reason="Apply current imported season player DKP weights",
                requested_utc=now,
                origin="system",
                provenance={"current_weights": True},
                current_weights=imported,
            )
            config_id = request["DesiredConfigVersionID"]
        if not request or not json.loads(request["ProvenanceJson"]).get("current_weights"):
            continue
        if not base or base["ConfigVersionID"] == config_id:
            continue
        cursor.execute(
            "SELECT c.RosterID,c.MappingDigest,w.StartScanID,w.EndScanID FROM KVK.SourceConfigVersion c JOIN KVK.SourceWindowConfig w ON w.ConfigVersionID=c.ConfigVersionID WHERE c.ConfigVersionID=? AND w.PeriodKey=?",
            base["ConfigVersionID"],
            period["PeriodKey"],
        )
        if one(cursor) != config:
            continue  # An endpoint/map/roster change still needs its compatible matched update.
        ready.append((base, request))
    return ready


def validate_weight_authority(cursor, update):
    """Current weights grant no map, roster, source-fact or implicit window authority."""
    proof = json.loads(update["ConfirmationJson"])
    if not proof.get("current_weights"):
        return False
    cursor.execute(
        "SELECT * FROM KVK.SourceConfigRequest WHERE RequestID=? AND SourceKey=? AND KVK_NO=? AND PeriodID=? AND DesiredConfigVersionID=?",
        update.get("RequestID"),
        SOURCE_KEY,
        update["KVK_NO"],
        update["PeriodID"],
        update["ConfigVersionID"],
    )
    request = one(cursor)
    if (
        not request
        or request["RequestState"] == "rejected"
        or not json.loads(request["ProvenanceJson"]).get("current_weights")
        or proof.get("action") != "correct"
    ):
        raise SourceConflict("Current-weight update lacks its durable configuration request.")
    cursor.execute(
        "SELECT ConfigVersionID,RosterID,MappingDigest,WindowDigest FROM KVK.SourceConfigVersion WHERE ConfigVersionID IN (?,?)",
        request["BaseConfigVersionID"],
        request["DesiredConfigVersionID"],
    )
    configs = rows(cursor)
    if len(configs) != 2 or any(
        configs[0][key] != configs[1][key] for key in ("RosterID", "MappingDigest")
    ):
        raise SourceConflict("Weight authority cannot change roster or mapping.")
    if (request["OldStartScanID"], request["OldEndScanID"]) != (
        request["NewStartScanID"],
        request["NewEndScanID"],
    ):
        raise SourceConflict("Weight authority cannot change scan endpoints.")
    if proof.get("automatic_weight_refresh"):
        cursor.execute(
            "SELECT * FROM KVK.SourceUpdate WHERE UpdateID=?", update.get("BaseUpdateID")
        )
        base = one(cursor)
        from kvk.dal.source_update_dal import INPUT_COLUMNS

        if not base or any(
            base[k] != update[k]
            for k in (
                "SourceKey",
                "KVK_NO",
                "PeriodID",
                "RosterID",
                "CoverageStartUTC",
                "CoverageEndUTC",
                "AsOfUTC",
            )
        ):
            raise SourceConflict("Automatic weight refresh must retain the complete base context.")
        if any(update[k] is not None and update[k] != base[k] for k in INPUT_COLUMNS):
            raise SourceConflict("Automatic weight refresh cannot change accepted source facts.")
        cursor.execute(
            "SELECT c.RosterID,c.MappingDigest,w.StartScanID,w.EndScanID FROM KVK.SourceConfigVersion c JOIN KVK.SourceWindowConfig w ON w.ConfigVersionID=c.ConfigVersionID WHERE c.ConfigVersionID IN (?,?) AND w.PeriodKey=?",
            base["ConfigVersionID"],
            update["ConfigVersionID"],
            update["PeriodKey"],
        )
        windows = rows(cursor)
        if len(windows) != 2 or windows[0] != windows[1]:
            raise SourceConflict("Automatic weight refresh cannot change the published window.")
    return True
