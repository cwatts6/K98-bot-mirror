"""Sealed input associations and atomic complete-selection/export-vector persistence."""

from dataclasses import asdict
import json
from uuid import uuid4

from kvk.dal.new_source_config_dal import locked_period
from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from kvk.dal.season_source_dal import audit_json, require_source
from kvk.models.source_integration import EXPORT_SCHEMA, CompleteSelectionResult, identity
from kvk.schemas.new_source_schema import SOURCE_KEY

INPUT_COLUMNS = (
    "StartScanID",
    "EndScanID",
    "StartRevisionID",
    "EndRevisionID",
    "AggregateReportID",
    "AggregateRevisionID",
)
CONTEXT_COLUMNS = (
    "SourceKey",
    "KVK_NO",
    "PeriodID",
    "PeriodKey",
    "ChoiceID",
    "ConfigVersionID",
    "RosterID",
    "CoverageStartUTC",
    "CoverageEndUTC",
    "AsOfUTC",
    "UpdateKind",
)


def update_hash(record):
    return digest({key: record[key] for key in (*CONTEXT_COLUMNS, *INPUT_COLUMNS)})


def load_update(cursor, update_id):
    cursor.execute("SELECT * FROM KVK.SourceUpdate WHERE UpdateID=?", identity(update_id))
    row = one(cursor)
    if row is None:
        raise SourceConflict("Unknown source update.")
    return row


def validate_update(cursor, update, *, complete=False, sealed=False):
    """Validate relationships not established by the static scoped foreign keys."""
    if update["SourceKey"] != SOURCE_KEY:
        raise SourceConflict("Unknown update source.")
    cursor.execute(
        "SELECT c.RosterID,c.MappingDigest,r.B0RevisionID,w.StartScanID,w.EndScanID,p.PeriodKind,p.CoverageStartUTC,p.CoverageEndUTC "
        "FROM KVK.SourceConfigVersion c JOIN KVK.SourceRoster r ON r.RosterID=c.RosterID "
        "JOIN KVK.SourceWindowConfig w ON w.ConfigVersionID=c.ConfigVersionID "
        "JOIN KVK.SourcePeriod p ON p.SourceKey=w.SourceKey AND p.KVK_NO=w.KVK_NO AND p.PeriodKey=w.PeriodKey "
        "WHERE c.SourceKey=? AND c.KVK_NO=? AND c.ConfigVersionID=? AND p.PeriodID=? AND p.PeriodKey=?",
        SOURCE_KEY,
        update["KVK_NO"],
        update["ConfigVersionID"],
        update["PeriodID"],
        update["PeriodKey"],
    )
    config = one(cursor)
    if (
        not config
        or config["RosterID"] != update["RosterID"]
        or update.get("PeriodKind", config["PeriodKind"]) != config["PeriodKind"]
        or not (
            config["PeriodKind"] == update["UpdateKind"]
            or (config["PeriodKind"] == "fight" and update["UpdateKind"] == "no_fight")
        )
    ):
        raise SourceConflict("Update configuration, roster or period differs.")
    if update["UpdateKind"] == "no_fight" and (
        config["StartScanID"] != config["EndScanID"]
        or update["AggregateReportID"] is not None
        or update["AggregateRevisionID"] is not None
        or (
            update["StartScanID"] is not None
            and update["EndScanID"] is not None
            and (
                update["StartScanID"] != update["EndScanID"]
                or update["StartRevisionID"] != update["EndRevisionID"]
            )
        )
    ):
        raise SourceConflict("No-fight requires configured equal endpoints and no aggregate.")
    if update["CoverageStartUTC"] != config["CoverageStartUTC"] or (
        config["CoverageEndUTC"] is not None and update["CoverageEndUTC"] > config["CoverageEndUTC"]
    ):
        raise SourceConflict("Update coverage exceeds the configured period.")
    if complete and (
        not update["StartRevisionID"]
        or not update["EndRevisionID"]
        or (update["UpdateKind"] != "no_fight" and not update["AggregateRevisionID"])
    ):
        raise SourceConflict("Both intended streams are required before sealing.")
    if complete:
        cursor.execute(
            "SELECT u.* FROM KVK.SourceCompleteSelection s JOIN KVK.SourceUpdate u ON u.UpdateID=s.UpdateID WHERE s.SourceKey=? AND s.KVK_NO=? AND s.PeriodID=?",
            SOURCE_KEY,
            update["KVK_NO"],
            update["PeriodID"],
        )
        prior = one(cursor)
        # BaseUpdateID is the persisted per-period CAS context, not a base guessed
        # by a restarted builder. Semantic replay may return its prior outcome.
        if (
            prior
            and update_hash(prior) != update_hash(update)
            and update.get("BaseUpdateID") != prior["UpdateID"]
        ):
            raise SourceConflict(
                "Complete update base CAS is stale; confirm against the current complete update."
            )
        if not prior and update.get("BaseUpdateID"):
            raise SourceConflict("Complete update base no longer exists.")
        if json.loads(update["ConfirmationJson"]).get("action") == "configure":
            if not prior or update.get("BaseUpdateID") != prior["UpdateID"]:
                raise SourceConflict("Display configuration requires the current complete base.")
            if any(
                update[k] != prior[k]
                for k in (*INPUT_COLUMNS, "CoverageStartUTC", "CoverageEndUTC", "AsOfUTC")
            ):
                raise SourceConflict("Display configuration must reuse the exact complete inputs.")
            cursor.execute(
                "SELECT c.ConfigVersionID,c.ConfigVersion,c.RosterID,c.MappingDigest,c.WeightDigest,w.StartScanID,w.EndScanID,w.WindowName "
                "FROM KVK.SourceConfigVersion c JOIN KVK.SourceWindowConfig w ON w.ConfigVersionID=c.ConfigVersionID "
                "WHERE c.ConfigVersionID IN (?,?)",
                prior["ConfigVersionID"],
                update["ConfigVersionID"],
            )
            configs = {r["ConfigVersionID"]: r for r in rows(cursor)}
            old, new = configs.get(prior["ConfigVersionID"]), configs.get(update["ConfigVersionID"])
            if (
                not old
                or not new
                or new["ConfigVersion"] <= old["ConfigVersion"]
                or any(
                    old[k] != new[k]
                    for k in (
                        "RosterID",
                        "MappingDigest",
                        "WeightDigest",
                        "StartScanID",
                        "EndScanID",
                    )
                )
            ):
                raise SourceConflict(
                    "Display-only configuration cannot change calculation or endpoint authority."
                )
        if prior and update_hash(prior) != update_hash(update):
            action = json.loads(update["ConfirmationJson"]).get("action", "publish")
            if (
                not update.get("RequestID")
                and action == "publish"
                and (
                    update["EndScanID"] < prior["EndScanID"]
                    or update["AsOfUTC"] < prior["AsOfUTC"]
                    or update["CoverageEndUTC"] < prior["CoverageEndUTC"]
                )
            ):
                raise SourceConflict("An older ready update cannot replace the complete selection.")
            same_players = all(prior[k] == update[k] for k in INPUT_COLUMNS[:4])
            same_aggregate = bool(
                update["AggregateRevisionID"]
                and prior["AggregateRevisionID"] == update["AggregateRevisionID"]
            )
            if (same_players or same_aggregate) and update["UpdateKind"] != "no_fight":
                required = (
                    update["AggregateRevisionID"] if same_aggregate else update["EndRevisionID"]
                )
                if (
                    update.get("BaseUpdateID") != prior["UpdateID"]
                    or update.get("CounterpartRevisionID") != required
                ):
                    raise SourceConflict(
                        "Reusing an unchanged stream requires explicit base/counterpart confirmation."
                    )
    base = None
    counterpart = update.get("CounterpartRevisionID")
    if counterpart:
        base = load_update(cursor, update["BaseUpdateID"])
        cursor.execute(
            "SELECT UpdateID FROM KVK.SourceCompleteSelection WHERE SourceKey=? AND KVK_NO=? AND PeriodID=?",
            SOURCE_KEY,
            update["KVK_NO"],
            update["PeriodID"],
        )
        selected = one(cursor)
        # Selected successors retain valid provenance on retry, but new successors require
        # the exact confirmed base to remain current.
        if not selected or selected["UpdateID"] not in (base["UpdateID"], update["UpdateID"]):
            raise SourceConflict("Counterpart confirmation base is stale.")
        if any(base[k] != update[k] for k in ("SourceKey", "KVK_NO", "PeriodID", "RosterID")):
            raise SourceConflict("Counterpart has incompatible season, period or roster.")
        if counterpart not in (
            base["StartRevisionID"],
            base["EndRevisionID"],
            base["AggregateRevisionID"],
        ):
            raise SourceConflict("Counterpart is not a retained base revision.")
        confirmation = json.loads(update["ConfirmationJson"]).get("counterpart")
        expected = {
            "base_update_id": base["UpdateID"],
            "revision_id": counterpart,
            "config_version_id": update["ConfigVersionID"],
            "roster_id": update["RosterID"],
            "coverage_start_utc": update["CoverageStartUTC"].isoformat(),
            "coverage_end_utc": update["CoverageEndUTC"].isoformat(),
            "as_of_utc": update["AsOfUTC"].isoformat(),
            "actor": update["ConfirmedBy"],
        }
        if confirmation != expected:
            raise SourceConflict("Explicit exact-context counterpart confirmation is required.")
    events = {}
    for role in ("Start", "End"):
        revision = update[role + "RevisionID"]
        if revision is None:
            continue
        cursor.execute(
            "SELECT s.LogicalScanID,o.ScanStartUTC,o.SelectedRevisionID,r.MetadataJson "
            "FROM KVK.SourceObservationRevision r JOIN KVK.SourceObservation o ON o.ObservationID=r.ObservationID "
            "JOIN KVK.SourceLogicalScan s ON s.ObservationID=o.ObservationID "
            "WHERE r.SourceKey=? AND r.KVK_NO=? AND r.RevisionID=?",
            SOURCE_KEY,
            update["KVK_NO"],
            revision,
        )
        event = one(cursor)
        if not event or event["LogicalScanID"] != update[role + "ScanID"]:
            raise SourceConflict("Logical scan and observation revision do not match.")
        if update["PeriodKey"] not in json.loads(event["MetadataJson"])["scope"]["period_keys"]:
            raise SourceConflict("Observation is not associated with this period.")
        if (
            not sealed
            and event["SelectedRevisionID"] != revision
            and revision != config["B0RevisionID"]
        ):
            raise SourceConflict("Observation revision or counterpart confirmation is stale.")
        events[role] = event
    if events:
        if update["StartScanID"] != config["StartScanID"]:
            raise SourceConflict("Update requires the exact configured start.")
        if config["EndScanID"] is not None and update["EndScanID"] > config["EndScanID"]:
            raise SourceConflict("Update exceeds the intended endpoint.")
        if (
            update["UpdateKind"] == "overall"
            and update["StartRevisionID"] != config["B0RevisionID"]
        ):
            raise SourceConflict("Overall must start at the frozen B0 revision.")
        if update["StartScanID"] == update["EndScanID"]:
            if (
                update["UpdateKind"] != "no_fight"
                or update["StartRevisionID"] != update["EndRevisionID"]
                or config["EndScanID"] != config["StartScanID"]
            ):
                raise SourceConflict("Equal endpoints require the typed no-fight update.")
        elif events["End"]["ScanStartUTC"] <= events["Start"]["ScanStartUTC"]:
            raise SourceConflict("Player scan starts must increase in UTC.")
    if update["AggregateRevisionID"]:
        if update["UpdateKind"] == "no_fight":
            raise SourceConflict("No-fight updates cannot contain aggregate reports.")
        cursor.execute(
            "SELECT r.*,f.PeriodKey,f.SelectedRevisionID FROM KVK.SourceAggregateRevision r "
            "JOIN KVK.SourceAggregateReport f ON f.ReportID=r.ReportID "
            "WHERE r.SourceKey=? AND r.KVK_NO=? AND r.ReportID=? AND r.RevisionID=?",
            SOURCE_KEY,
            update["KVK_NO"],
            update["AggregateReportID"],
            update["AggregateRevisionID"],
        )
        aggregate = one(cursor)
        if (
            not aggregate
            or aggregate["PeriodKey"] != update["PeriodKey"]
            or aggregate["PeriodKind"] != update["UpdateKind"]
        ):
            raise SourceConflict("Aggregate report family differs.")
        if (
            not sealed and aggregate["SelectedRevisionID"] != update["AggregateRevisionID"]
        ) or bytes(aggregate["MappingDigest"]) != bytes(config["MappingDigest"]):
            raise SourceConflict("Aggregate revision or frozen mapping is stale.")
        if not counterpart or counterpart != update["AggregateRevisionID"]:
            if any(
                aggregate[k] != update[k] for k in ("CoverageStartUTC", "CoverageEndUTC", "AsOfUTC")
            ):
                raise SourceConflict("Aggregate coverage requires explicit counterpart authority.")
        for table in ("SourceKingdomReportRow", "SourceCampReportRow"):
            cursor.execute(
                "SELECT COUNT_BIG(*) AS n FROM KVK." + table + " WHERE RevisionID=?",
                update["AggregateRevisionID"],
            )
            if not one(cursor)["n"]:
                raise SourceConflict("Both aggregate tabs must be present.")
    if update.get("RequestID"):
        cursor.execute(
            "SELECT DesiredConfigVersionID,RequestState FROM KVK.SourceConfigRequest WHERE SourceKey=? AND KVK_NO=? AND PeriodID=? AND RequestID=?",
            SOURCE_KEY,
            update["KVK_NO"],
            update["PeriodID"],
            update["RequestID"],
        )
        request = one(cursor)
        if (
            not request
            or request["RequestState"] == "rejected"
            or request["DesiredConfigVersionID"] != update["ConfigVersionID"]
        ):
            raise SourceConflict("Endpoint authority does not match this update.")
    return config["PeriodKind"]


def validate_sealed_snapshot(cursor, snapshot, b0, update_id, expected_version):
    from kvk.dal.new_source_publication_dal import validate_snapshot_inputs

    update = load_update(cursor, update_id)
    if update["Version"] != expected_version or update["UpdateState"] not in ("ready", "selected"):
        raise SourceConflict("Sealed update CAS lost.")
    selection = snapshot.calculation.selection
    expected = dict(
        SourceKey=selection.config.source_key,
        KVK_NO=selection.config.kvk_no,
        PeriodID=selection.config.period_id,
        ConfigVersionID=selection.config.version_id,
        RosterID=selection.config.roster_id,
        StartScanID=selection.start.logical_scan_id if selection.start else None,
        EndScanID=selection.end.logical_scan_id if selection.end else None,
        StartRevisionID=selection.start.revision_id if selection.start else None,
        EndRevisionID=selection.end.revision_id if selection.end else None,
        AggregateReportID=snapshot.aggregate.report_id if snapshot.aggregate else None,
        AggregateRevisionID=snapshot.aggregate.revision_id if snapshot.aggregate else None,
    )
    if any(update[k] != v for k, v in expected.items()) or bytes(
        update["ContentHash"]
    ) != update_hash(update):
        raise SourceConflict("Publication does not describe its sealed update.")
    validate_update(cursor, update, complete=True, sealed=True)
    # Full immutable fact/count/config verification stays in the existing validator.
    # Selection freshness is governed by the explicit tuple above, never global MAX.
    validate_snapshot_inputs(cursor, snapshot, b0, require_selected=False)
    return update


class SourceUpdateDAL:
    def __init__(self, connect):
        self.connect = connect

    def read(self, update_id):
        with transaction(self.connect) as cursor:
            return load_update(cursor, update_id)

    def selected_result(self, update_id):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (1) PublicationID,PublicSelectionVersion FROM KVK.SourceExportIntentPublication WHERE UpdateID=? ORDER BY PublicSelectionVersion",
                update_id,
            )
            selected = one(cursor)
            if not selected:
                raise SourceConflict("Selected update has no retained intent vector.")
            return read_complete_result(
                cursor, update_id, selected["PublicationID"], selected["PublicSelectionVersion"]
            )

    def create(self, context, *, authorized, admin_authorized=False):
        if authorized is not True:
            raise PermissionError("Explicit update metadata confirmation is required.")
        confirmation = json.loads(context.confirmation_json)
        action = confirmation.get("action", "publish")
        if action not in ("publish", "correct", "finalize", "configure"):
            raise ValueError("Invalid confirmed update action.")
        if action != "publish" and admin_authorized is not True:
            raise PermissionError(
                "Correction/finalization/configuration requires administrative authority."
            )
        evidence = audit_json(confirmation)
        record = dict(
            zip(
                CONTEXT_COLUMNS,
                (
                    SOURCE_KEY,
                    context.kvk_no,
                    context.period_id,
                    context.period_key,
                    context.choice_id,
                    context.config_version_id,
                    context.roster_id,
                    context.coverage_start_utc.replace(tzinfo=None),
                    context.coverage_end_utc.replace(tzinfo=None),
                    context.as_of_utc.replace(tzinfo=None),
                    context.update_kind,
                ),
                strict=True,
            )
        )
        record.update(dict.fromkeys(INPUT_COLUMNS))
        record.update(
            UpdateID=context.update_id,
            BaseUpdateID=context.base_update_id,
            RequestID=context.request_id,
            ConfirmedBy=context.actor,
            ConfirmedUTC=context.confirmed_utc.replace(tzinfo=None),
            ConfirmationJson=evidence,
            CounterpartRevisionID=None,
        )
        with transaction(self.connect) as cursor:
            locked_period(cursor, context.kvk_no, context.period_id)
            choice = require_source(cursor, context.kvk_no, SOURCE_KEY)
            if choice["ChoiceID"] != context.choice_id:
                raise SourceConflict("Update belongs to a different audited choice.")
            cursor.execute("SELECT * FROM KVK.SourceUpdate WHERE UpdateID=?", context.update_id)
            existing = one(cursor)
            if existing:
                if any(
                    existing[k] != record[k]
                    for k in (
                        *CONTEXT_COLUMNS,
                        "BaseUpdateID",
                        "RequestID",
                        "ConfirmedBy",
                        "ConfirmedUTC",
                        "ConfirmationJson",
                    )
                ):
                    raise SourceConflict("Update identity cannot be retagged.")
                return existing
            # Classification comes from the immutable scoped period, never caller metadata.
            # It is functionally determined by PeriodID and is not a new semantic-hash input.
            record["PeriodKind"] = validate_update(cursor, record)
            columns = [
                *CONTEXT_COLUMNS,
                "PeriodKind",
                "UpdateID",
                "BaseUpdateID",
                "RequestID",
                "ConfirmedBy",
                "ConfirmedUTC",
                "ConfirmationJson",
            ]
            cursor.execute(
                "INSERT KVK.SourceUpdate ("
                + ",".join(columns)
                + ",ContentHash,UpdateState,Version) VALUES ("
                + ",".join("?" for _ in columns)
                + ",?,'waiting_player',1)",
                *(record[k] for k in columns),
                update_hash(record),
            )
            return load_update(cursor, context.update_id)

    def resume_endpoint(self, update_id):
        """Resolve only the endpoint slot named by retained explicit confirmation."""
        from kvk.models.source_integration import PlayerRevisions

        update = self.read(update_id)
        if update["UpdateState"] != "waiting_player" or not update["RequestID"]:
            return update
        pending = json.loads(update["ConfirmationJson"]).get("pending_player")
        if not isinstance(pending, dict) or set(pending) != {
            "start_scan_id",
            "start_revision_id",
            "end_scan_id",
        }:
            return update
        with transaction(self.connect) as cursor:
            locked_period(cursor, update["KVK_NO"], update["PeriodID"])
            cursor.execute(
                "SELECT NewStartScanID,NewEndScanID,DesiredConfigVersionID,RequestState FROM KVK.SourceConfigRequest WHERE RequestID=?",
                update["RequestID"],
            )
            request = one(cursor)
            if (
                not request
                or request["RequestState"] == "rejected"
                or (
                    request["NewStartScanID"],
                    request["NewEndScanID"],
                    request["DesiredConfigVersionID"],
                )
                != (pending["start_scan_id"], pending["end_scan_id"], update["ConfigVersionID"])
            ):
                raise SourceConflict(
                    "Pending endpoint authority differs from retained confirmation."
                )
            cursor.execute(
                "SELECT o.SelectedRevisionID FROM KVK.SourceLogicalScan s JOIN KVK.SourceObservation o ON o.ObservationID=s.ObservationID WHERE s.SourceKey=? AND s.KVK_NO=? AND s.LogicalScanID=?",
                SOURCE_KEY,
                update["KVK_NO"],
                pending["end_scan_id"],
            )
            endpoint = one(cursor)
            if endpoint is None:
                return update
        return self.associate(
            update_id,
            expected_version=update["Version"],
            player=PlayerRevisions(
                pending["start_scan_id"],
                pending["end_scan_id"],
                pending["start_revision_id"],
                endpoint["SelectedRevisionID"],
            ),
            authorized=True,
        )

    def associate(
        self,
        update_id,
        *,
        expected_version,
        player=None,
        aggregate=None,
        counterpart_revision_id=None,
        authorized,
    ):
        if authorized is not True:
            raise PermissionError("Explicit input association authority is required.")
        initial = self.read(update_id)
        with transaction(self.connect) as cursor:
            locked_period(cursor, initial["KVK_NO"], initial["PeriodID"])
            require_source(cursor, initial["KVK_NO"], SOURCE_KEY)
            update = load_update(cursor, update_id)
            proposed = dict(update)
            if player:
                proposed.update(dict(zip(INPUT_COLUMNS[:4], asdict(player).values(), strict=True)))
            if aggregate:
                proposed.update(
                    AggregateReportID=aggregate.report_id, AggregateRevisionID=aggregate.revision_id
                )
            if counterpart_revision_id:
                proposed["CounterpartRevisionID"] = identity(counterpart_revision_id)
            if proposed == update:
                return update
            if update["Version"] != expected_version or update["UpdateState"] not in (
                "waiting_player",
                "waiting_aggregate",
            ):
                raise SourceConflict("Update is sealed or association CAS lost.")
            if any(
                update[k] is not None and update[k] != proposed[k]
                for k in (*INPUT_COLUMNS, "CounterpartRevisionID")
            ):
                raise SourceConflict("An attached revision cannot be replaced.")
            complete = bool(
                proposed["StartRevisionID"]
                and proposed["EndRevisionID"]
                and (proposed["AggregateRevisionID"] or proposed["UpdateKind"] == "no_fight")
            )
            validate_update(cursor, proposed, complete=complete)
            state = (
                "ready"
                if complete
                else ("waiting_aggregate" if proposed["StartRevisionID"] else "waiting_player")
            )
            content_hash = update_hash(proposed)
            duplicate = None
            if complete:
                if json.loads(proposed["ConfirmationJson"]).get("action") == "configure":
                    base = load_update(cursor, proposed["BaseUpdateID"])
                    cursor.execute(
                        "SELECT WindowName FROM KVK.SourceWindowConfig WHERE ConfigVersionID IN (?,?)",
                        base["ConfigVersionID"],
                        proposed["ConfigVersionID"],
                    )
                    names = rows(cursor)
                    if len(names) == 2 and names[0]["WindowName"] == names[1]["WindowName"]:
                        duplicate = base
                if duplicate is None:
                    cursor.execute(
                        "SELECT * FROM KVK.SourceUpdate WHERE SourceKey=? AND KVK_NO=? AND PeriodID=? AND ContentHash=? AND UpdateState IN ('ready','selected')",
                        SOURCE_KEY,
                        proposed["KVK_NO"],
                        proposed["PeriodID"],
                        content_hash,
                    )
                    duplicate = one(cursor)
                if duplicate:
                    # Retain this identity and its confirmed inputs, but stop recovery
                    # from rediscovering a request already satisfied by another update.
                    state = "superseded"
            for scan in (proposed["StartScanID"], proposed["EndScanID"]):
                if scan is not None:
                    cursor.execute(
                        "IF NOT EXISTS (SELECT 1 FROM KVK.SourceScanBinding WHERE ConfigVersionID=? AND LogicalScanID=?) "
                        "INSERT KVK.SourceScanBinding (ConfigVersionID,SourceKey,KVK_NO,LogicalScanID) VALUES (?,?,?,?)",
                        proposed["ConfigVersionID"],
                        scan,
                        proposed["ConfigVersionID"],
                        SOURCE_KEY,
                        proposed["KVK_NO"],
                        scan,
                    )
            columns = (*INPUT_COLUMNS, "CounterpartRevisionID")
            cursor.execute(
                "UPDATE KVK.SourceUpdate SET "
                + ",".join(k + "=?" for k in columns)
                + ",ContentHash=?,UpdateState=?,Version=Version+1 OUTPUT inserted.* WHERE UpdateID=? AND Version=?",
                *(proposed[k] for k in columns),
                content_hash,
                state,
                update_id,
                expected_version,
            )
            result = one(cursor)
            if not result:
                raise SourceConflict("Association CAS lost.")
            return duplicate if duplicate is not None else result


def commit_complete(
    cursor, *, update, publication_id, expected_public_version, expected_update_version
):
    """Caller holds all season/selection/config locks and owns the only commit."""
    cursor.execute(
        "SELECT * FROM KVK.SourceCompleteSelection WHERE SourceKey=? AND KVK_NO=? ORDER BY PeriodID",
        SOURCE_KEY,
        update["KVK_NO"],
    )
    vector = rows(cursor)
    previous = next((r for r in vector if r["PeriodID"] == update["PeriodID"]), None)
    version = previous["PublicSelectionVersion"] if previous else 0
    if version != expected_public_version:
        raise SourceConflict("Complete selection CAS lost.")
    if update["Version"] != expected_update_version or update["UpdateState"] != "ready":
        raise SourceConflict("Only an unchanged ready update may advance complete selection.")
    validate_update(cursor, update, complete=True, sealed=True)
    cursor.execute(
        "SELECT * FROM KVK.SourcePublication WHERE PublicationID=? AND SourceKey=? AND KVK_NO=? AND PeriodID=?",
        publication_id,
        SOURCE_KEY,
        update["KVK_NO"],
        update["PeriodID"],
    )
    publication = one(cursor)
    if (
        not publication
        or publication["BuildState"] != "complete"
        or any(publication[k] != update[k] for k in (*INPUT_COLUMNS, "ConfigVersionID", "RosterID"))
    ):
        raise SourceConflict("Complete candidate and sealed update differ.")
    if previous:
        cursor.execute(
            "UPDATE KVK.SourceCompleteSelection SET UpdateID=?,PublicationID=?,PublicSelectionVersion=PublicSelectionVersion+1,SelectedUTC=SYSUTCDATETIME() "
            "OUTPUT inserted.PublicSelectionVersion WHERE SourceKey=? AND KVK_NO=? AND PeriodID=? AND PublicSelectionVersion=?",
            update["UpdateID"],
            publication_id,
            SOURCE_KEY,
            update["KVK_NO"],
            update["PeriodID"],
            version,
        )
        if one(cursor) is None:
            raise SourceConflict("Complete selection CAS lost.")
    else:
        cursor.execute(
            "INSERT KVK.SourceCompleteSelection (SourceKey,KVK_NO,PeriodID,UpdateID,PublicationID,PublicSelectionVersion,SelectedUTC) VALUES (?,?,?,?,?,1,SYSUTCDATETIME())",
            SOURCE_KEY,
            update["KVK_NO"],
            update["PeriodID"],
            update["UpdateID"],
            publication_id,
        )
    cursor.execute(
        "UPDATE KVK.SourceUpdate SET UpdateState='selected',Version=Version+1 OUTPUT inserted.Version WHERE UpdateID=? AND Version=? AND UpdateState='ready'",
        update["UpdateID"],
        expected_update_version,
    )
    if one(cursor) is None:
        raise SourceConflict("Sealed update CAS lost.")
    cursor.execute(
        "SELECT s.PeriodID,s.UpdateID,s.PublicationID,s.PublicSelectionVersion,u.ConfigVersionID,p.ManifestHash "
        "FROM KVK.SourceCompleteSelection s JOIN KVK.SourceUpdate u ON u.UpdateID=s.UpdateID "
        "JOIN KVK.SourcePublication p ON p.PublicationID=s.PublicationID "
        "WHERE s.SourceKey=? AND s.KVK_NO=? ORDER BY s.PeriodID",
        SOURCE_KEY,
        update["KVK_NO"],
    )
    complete_vector = rows(cursor)
    if len(complete_vector) != len(vector) + (0 if previous else 1):
        raise SourceConflict("Complete vector membership changed.")
    for old in vector:
        if old["PeriodID"] == update["PeriodID"]:
            continue
        retained = next((r for r in complete_vector if r["PeriodID"] == old["PeriodID"]), None)
        if not retained or any(
            retained[k] != old[k] for k in ("UpdateID", "PublicationID", "PublicSelectionVersion")
        ):
            raise SourceConflict("An unchanged complete period was lost.")
    for member in complete_vector:
        from kvk.dal.new_source_publication_dal import publication_results, result_digest

        cursor.execute(
            "SELECT * FROM KVK.SourcePublication WHERE PublicationID=?", member["PublicationID"]
        )
        stored_publication = one(cursor)
        stored_update = load_update(cursor, member["UpdateID"])
        stored_results = publication_results(cursor, member["PublicationID"])
        if (
            stored_update["UpdateState"] != "selected"
            or stored_update["ConfigVersionID"] != member["ConfigVersionID"]
            or bytes(stored_update["ContentHash"]) != update_hash(stored_update)
            or stored_publication["BuildState"] != "complete"
            or len(stored_results) != stored_publication["EligibleCount"]
            or len(stored_results) != stored_publication["ResultCount"]
            or result_digest(stored_results) != bytes(stored_publication["ManifestHash"])
            or any(
                stored_update[k] != stored_publication[k]
                for k in (*INPUT_COLUMNS, "ConfigVersionID", "RosterID")
            )
        ):
            raise SourceConflict("Unchanged vector member has invalid sealed publication identity.")
    vector_hash = digest(
        [{**r, "ManifestHash": bytes(r["ManifestHash"]).hex()} for r in complete_vector]
    )
    cursor.execute(
        "SELECT * FROM KVK.SourceExportIntent WHERE SourceKey=? AND KVK_NO=? AND VectorHash=? AND ExportSchemaVersion=?",
        SOURCE_KEY,
        update["KVK_NO"],
        vector_hash,
        EXPORT_SCHEMA,
    )
    intent = one(cursor)
    if intent is None:
        cursor.execute(
            "SELECT ISNULL(MAX(CommitSequence),0)+1 AS n FROM KVK.SourceExportIntent WHERE SourceKey=? AND KVK_NO=?",
            SOURCE_KEY,
            update["KVK_NO"],
        )
        sequence = one(cursor)["n"]
        intent_id = str(uuid4())
        cursor.execute(
            "INSERT KVK.SourceExportIntent (IntentID,SourceKey,KVK_NO,ChoiceID,CommitSequence,VectorHash,ExportSchemaVersion,IntentState,CreatedUTC) VALUES (?,?,?,?,?,?,?,'waiting_destination',SYSUTCDATETIME())",
            intent_id,
            SOURCE_KEY,
            update["KVK_NO"],
            update["ChoiceID"],
            sequence,
            vector_hash,
            EXPORT_SCHEMA,
        )
        for member in complete_vector:
            cursor.execute(
                "INSERT KVK.SourceExportIntentPublication (IntentID,PeriodID,SourceKey,KVK_NO,UpdateID,PublicationID,PublicSelectionVersion,ConfigVersionID) VALUES (?,?,?,?,?,?,?,?)",
                intent_id,
                member["PeriodID"],
                SOURCE_KEY,
                update["KVK_NO"],
                member["UpdateID"],
                member["PublicationID"],
                member["PublicSelectionVersion"],
                member["ConfigVersionID"],
            )
    else:
        intent_id, sequence = intent["IntentID"], intent["CommitSequence"]
    cursor.execute(
        "SELECT PeriodID,UpdateID,PublicationID,PublicSelectionVersion,ConfigVersionID FROM KVK.SourceExportIntentPublication WHERE IntentID=? ORDER BY PeriodID",
        intent_id,
    )
    actual = rows(cursor)
    expected = [
        {
            k: r[k]
            for k in (
                "PeriodID",
                "UpdateID",
                "PublicationID",
                "PublicSelectionVersion",
                "ConfigVersionID",
            )
        }
        for r in complete_vector
    ]
    if actual != expected:
        raise SourceConflict("Persisted export vector differs from complete selection.")
    return CompleteSelectionResult(
        update["UpdateID"], publication_id, version + 1, intent_id, sequence, vector_hash.hex()
    )


def read_complete_result(cursor, update_id, publication_id, public_version):
    cursor.execute(
        "SELECT TOP (1) i.IntentID,i.CommitSequence,i.VectorHash FROM KVK.SourceExportIntent i "
        "JOIN KVK.SourceExportIntentPublication v ON v.IntentID=i.IntentID "
        "WHERE v.UpdateID=? AND v.PublicationID=? AND v.PublicSelectionVersion=? ORDER BY i.CommitSequence",
        update_id,
        publication_id,
        public_version,
    )
    row = one(cursor)
    if row is None:
        raise SourceConflict("Complete selection audit has no durable export intent.")
    return CompleteSelectionResult(
        update_id,
        publication_id,
        public_version,
        row["IntentID"],
        row["CommitSequence"],
        bytes(row["VectorHash"]).hex(),
    )
