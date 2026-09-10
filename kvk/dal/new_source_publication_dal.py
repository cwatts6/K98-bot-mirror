"""Immutable candidate facts and short, fenced publication selection transactions."""

from datetime import UTC, datetime
from decimal import Decimal

from kvk.dal.new_source_config_dal import desired_config, locked_period
from kvk.dal.new_source_import_dal import SourceConflict, canonical, digest, one, rows, transaction
from kvk.models.new_source_reporting import fits_decimal
from kvk.schemas.new_source_schema import SOURCE_KEY

RESULT_METRICS = (
    "starting_power",
    "power",
    "troops_power",
    "t1_kills",
    "t2_kills",
    "t3_kills",
    "t4_kills",
    "t5_kills",
    "total_kill_points",
    "dead",
    "healed",
    "acclaim",
    "highest_acclaim",
    "kp_t4_t5",
    "dkp",
    "healed_points",
    "dkp_power_ratio",
)


def result_values(player):
    values, states = {}, {}
    ranks = dict(player.ranks)
    for key in RESULT_METRICS:
        metric = player.metric(key)
        value = metric.value
        if value is not None:
            scale = (
                12
                if key == "dkp_power_ratio"
                else 6 if key in ("kp_t4_t5", "dkp", "healed_points") else 0
            )
            if not fits_decimal(value, scale) or (scale == 0 and not -(2**63) <= value < 2**63):
                raise ValueError("Calculated result cannot be stored without precision loss.")
            if scale == 0:
                value = int(value)
        values[key] = value
        states[key] = metric.state.value
        rank = ranks.get(key)
        values[key + "_rank"] = rank.rank if rank else None
        values[key + "_cohort"] = rank.population if rank else None
    return {
        "GovernorID": player.governor_id,
        "b0_kingdom": player.b0_kingdom,
        "CampID": player.camp_id,
        "name": player.name,
        "FieldStatusJson": canonical(states),
        **values,
    }


def result_digest(result_rows):
    # SQL Decimal scales are normalized before hashing, including genuine zero.
    def normal(value):
        if isinstance(value, Decimal):
            token = format(value, "f")
            return token.rstrip("0").rstrip(".") if "." in token else token
        return value

    return digest(
        [
            {key: normal(value) for key, value in sorted(row.items())}
            for row in sorted(result_rows, key=lambda item: item["GovernorID"])
        ]
    )


def publication_results(cursor, publication_id):
    columns = (
        "GovernorID",
        "b0_kingdom",
        "CampID",
        "name",
        "FieldStatusJson",
        *(column for key in RESULT_METRICS for column in (key, key + "_rank", key + "_cohort")),
    )
    cursor.execute(
        "SELECT "
        + ",".join(columns)
        + " FROM KVK.SourcePlayerResult WHERE PublicationID=? ORDER BY GovernorID",
        publication_id,
    )
    return rows(cursor)


def validate_snapshot_inputs(cursor, snapshot, b0, *, require_selected=True):
    """Bind supplied immutable S3A input objects to the accepted SQL facts/config."""
    from dataclasses import asdict

    config = snapshot.calculation.selection.config
    selection = snapshot.calculation.selection
    cursor.execute(
        "SELECT p.* FROM KVK.SourceSelection s JOIN KVK.SourcePublication p ON p.PublicationID=s.PublicationID WHERE s.SourceKey=? AND s.KVK_NO=? AND s.PeriodID=?",
        SOURCE_KEY,
        config.kvk_no,
        config.period_id,
    )
    prior = one(cursor)
    pinned = set()
    if (
        prior
        and prior["PlayerState"] in ("final", "corrected_final")
        and prior["ConfigVersionID"] == config.version_id
    ):
        pinned = {prior["StartRevisionID"], prior["EndRevisionID"]}
    cursor.execute(
        "SELECT * FROM KVK.SourcePublication WHERE PublicationID=?", snapshot.publication_id
    )
    candidate = one(cursor)
    if candidate:
        expected = {
            "SourceKey": config.source_key,
            "KVK_NO": config.kvk_no,
            "PeriodID": config.period_id,
            "ConfigVersionID": config.version_id,
            "RosterID": config.roster_id,
            "CalculationVersion": snapshot.calculation.calculation_version,
            "StartScanID": selection.start.logical_scan_id if selection.start else None,
            "EndScanID": selection.end.logical_scan_id if selection.end else None,
            "StartRevisionID": selection.start.revision_id if selection.start else None,
            "EndRevisionID": selection.end.revision_id if selection.end else None,
            "AggregateRevisionID": snapshot.aggregate.revision_id if snapshot.aggregate else None,
            "PlayerState": snapshot.player_state.value,
            "AggregateState": snapshot.aggregate_state.value,
            "PeriodState": snapshot.period_state.value,
        }
        if any(candidate[key] != value for key, value in expected.items()):
            raise SourceConflict("Candidate identity cannot describe different pinned inputs.")
    cursor.execute(
        "SELECT c.*,w.StartScanID,w.EndScanID,w.WindowName,p.PeriodKey,p.PeriodKind,p.CoverageEndUTC,r.B0RevisionID,r.MemberCount FROM KVK.SourceConfigVersion c JOIN KVK.SourceWindowConfig w ON w.ConfigVersionID=c.ConfigVersionID JOIN KVK.SourcePeriod p ON p.SourceKey=c.SourceKey AND p.KVK_NO=c.KVK_NO AND p.PeriodKey=w.PeriodKey JOIN KVK.SourceRoster r ON r.RosterID=c.RosterID WHERE c.ConfigVersionID=? AND c.SourceKey=? AND c.KVK_NO=? AND p.PeriodID=?",
        config.version_id,
        SOURCE_KEY,
        config.kvk_no,
        config.period_id,
    )
    stored = one(cursor)
    if not stored or (
        str(stored["RosterID"]),
        str(stored["B0RevisionID"]),
        stored["StartScanID"],
        stored["EndScanID"],
        stored["WindowName"],
        stored["MemberCount"],
    ) != (
        config.roster_id,
        config.b0_revision_id,
        config.start_scan_id,
        config.end_scan_id,
        config.label,
        snapshot.calculation.eligible_count,
    ):
        raise SourceConflict("Candidate differs from approved configuration/roster.")
    if stored["CoverageEndUTC"] != (
        config.closes_at_utc.replace(tzinfo=None) if config.closes_at_utc else None
    ):
        raise SourceConflict("Candidate period close differs from approved coverage.")
    if (stored["PeriodKey"], stored["PeriodKind"]) != (config.period_key, config.period_kind.value):
        raise SourceConflict("Candidate period identity differs from approved period.")
    if require_selected and snapshot.player_state.value not in (
        "final",
        "corrected_final",
        "not_applicable",
    ):
        # Chronological admission makes the exact numeric interval deterministic. Recheck
        # under the season lock, including scans accepted after this candidate was built.
        cursor.execute(
            "SELECT MAX(s.LogicalScanID) AS Latest FROM KVK.SourceLogicalScan s JOIN KVK.SourceObservation o ON o.ObservationID=s.ObservationID WHERE s.SourceKey=? AND s.KVK_NO=? AND s.LogicalScanID>? AND (? IS NULL OR s.LogicalScanID<=?) AND (? IS NULL OR o.ScanStartUTC<=?)",
            SOURCE_KEY,
            config.kvk_no,
            config.start_scan_id,
            config.end_scan_id,
            config.end_scan_id,
            stored["CoverageEndUTC"],
            stored["CoverageEndUTC"],
        )
        latest = one(cursor)["Latest"]
        if latest != (selection.end.logical_scan_id if selection.end else None):
            raise SourceConflict("Newer player input requires rebuilding the candidate.")
    cursor.execute(
        "SELECT Kingdom,CampID,CampName FROM KVK.SourceCampConfig WHERE ConfigVersionID=? ORDER BY Kingdom",
        config.version_id,
    )
    mapping = tuple((r["Kingdom"], r["CampID"], r["CampName"]) for r in rows(cursor))
    if mapping != tuple(sorted(config.mapping.entries)):
        raise SourceConflict("Candidate map differs from approved map.")
    cursor.execute(
        "SELECT * FROM KVK.SourceWeightConfig WHERE ConfigVersionID=?", config.version_id
    )
    weight = one(cursor)
    if (weight is None) != (config.weights is None):
        raise SourceConflict("Candidate weight availability differs.")
    if weight and (
        weight["WeightT4XSource"],
        weight["WeightT5YSource"],
        weight["WeightDeadsZSource"],
        weight["EffectiveFromUTC"],
    ) != (
        config.weights.x_source,
        config.weights.y_source,
        config.weights.z_source,
        config.weights.effective_from_utc.replace(tzinfo=None),
    ):
        raise SourceConflict("Candidate weights differ from approved weights.")
    if (
        weight
        and (weight["WeightT4X"], weight["WeightT5Y"], weight["WeightDeadsZ"])
        != config.weights.coefficients
    ):
        raise SourceConflict("Stored coefficient and original decimal string differ.")
    cursor.execute(
        "SELECT GovernorID,b0_kingdom FROM KVK.SourceRosterMember WHERE RosterID=? ORDER BY GovernorID",
        config.roster_id,
    )
    membership = [(r["GovernorID"], r["b0_kingdom"]) for r in rows(cursor)]
    if membership != [(p.governor_id, p.b0_kingdom) for p in snapshot.calculation.players]:
        raise SourceConflict("Candidate does not match frozen B0 membership.")
    for event in (b0, snapshot.calculation.selection.start, snapshot.calculation.selection.end):
        if event is None:
            continue
        cursor.execute(
            "SELECT r.*,o.ScanStartUTC,o.SelectedRevisionID,s.LogicalScanID FROM KVK.SourceObservationRevision r JOIN KVK.SourceObservation o ON o.ObservationID=r.ObservationID JOIN KVK.SourceLogicalScan s ON s.ObservationID=o.ObservationID WHERE r.RevisionID=? AND r.SourceKey=? AND r.KVK_NO=?",
            event.revision_id,
            SOURCE_KEY,
            config.kvk_no,
        )
        accepted = one(cursor)
        if not accepted or (
            str(accepted["ObservationID"]),
            accepted["LogicalScanID"],
            accepted["ScanStartUTC"],
            bytes(accepted["SemanticHash"]).hex(),
        ) != (
            event.observation_id,
            event.logical_scan_id,
            event.scan_start_utc.replace(tzinfo=None),
            event.observation.digest.sha256,
        ):
            raise SourceConflict("Candidate observation binding differs from accepted input.")
        if (
            require_selected
            and event is not b0
            and event.revision_id not in pinned
            and str(accepted["SelectedRevisionID"]) != event.revision_id
        ):
            raise SourceConflict("Candidate observation revision is no longer selected.")
        cursor.execute(
            "SELECT RawProfileJson FROM KVK.SourcePlayerSnapshot WHERE RevisionID=? ORDER BY GovernorID",
            event.revision_id,
        )
        raw = [r["RawProfileJson"] for r in rows(cursor)]
        if raw != [
            canonical(asdict(row)) for row in sorted(event.observation.rows, key=lambda r: r.key)
        ]:
            raise SourceConflict("Candidate player facts differ from accepted facts.")
    aggregate = snapshot.aggregate
    cursor.execute(
        "SELECT * FROM KVK.SourceAggregateReport WHERE SourceKey=? AND KVK_NO=? AND PeriodKey=?",
        SOURCE_KEY,
        config.kvk_no,
        config.period_key,
    )
    family = one(cursor)
    if require_selected and (str(family["SelectedRevisionID"]) if family else None) != (
        aggregate.revision_id if aggregate else None
    ):
        raise SourceConflict("Candidate aggregate input changed; rebuild both streams.")
    if aggregate:
        cursor.execute(
            "SELECT * FROM KVK.SourceAggregateRevision WHERE RevisionID=? AND ReportID=?",
            aggregate.revision_id,
            aggregate.report_id,
        )
        revision = one(cursor)
        if (
            not revision
            or bytes(revision["SemanticHash"]).hex() != aggregate.report.digest.sha256
            or revision["ReportState"] != snapshot.aggregate_state.value
        ):
            raise SourceConflict("Aggregate identity or finality differs.")
        meta = aggregate.report.metadata.candidate
        for column, value in (
            ("ScanStartUTC", meta.scan_start_utc),
            ("CoverageStartUTC", meta.coverage_start_utc),
            ("CoverageEndUTC", meta.coverage_end_utc),
            ("AsOfUTC", meta.as_of_utc),
        ):
            if revision[column] != value.replace(tzinfo=None):
                raise SourceConflict("Aggregate metadata differs from accepted revision.")
        if (
            not family
            or family["ReportID"] != aggregate.report_id
            or bytes(revision["MappingDigest"]) != digest(asdict(config.mapping))
        ):
            raise SourceConflict("Aggregate period or mapping differs from publication.")
        for table, key, supplied in (
            ("SourceKingdomReportRow", "Kingdom", aggregate.report.kingdom_rows),
            ("SourceCampReportRow", "CampID", aggregate.report.camp_rows),
        ):
            cursor.execute(
                "SELECT RawCellsJson FROM KVK." + table + " WHERE RevisionID=? ORDER BY " + key,
                aggregate.revision_id,
            )
            if [r["RawCellsJson"] for r in rows(cursor)] != [
                canonical(asdict(row)) for row in sorted(supplied, key=lambda r: r.key)
            ]:
                raise SourceConflict("Aggregate facts differ from accepted both-tab revision.")


class PublicationDAL:
    def __init__(self, connect):
        self.connect = connect

    def build_candidate(self, snapshot, *, validate_inputs):
        config = snapshot.calculation.selection.config
        result_rows = [result_values(p) for p in snapshot.calculation.players]
        manifest = result_digest(result_rows)
        with transaction(self.connect) as cursor:
            routing, selected, requests = locked_period(cursor, config.kvk_no, config.period_id)
            current = desired_config(cursor, selected, requests)
            if current is not None and current != config.version_id:
                raise SourceConflict("Candidate configuration is stale.")
            validate_inputs(cursor)
            publication_id = snapshot.publication_id
            cursor.execute(
                "SELECT * FROM KVK.SourcePublication WHERE PublicationID=?", publication_id
            )
            existing = one(cursor)
            if existing:
                if (
                    existing["BuildState"] != "complete"
                    or bytes(existing["ManifestHash"]) != manifest
                    or str(existing["ConfigVersionID"]) != config.version_id
                ):
                    raise SourceConflict("Candidate identity has different or incomplete contents.")
                return existing
            cursor.execute(
                "SELECT ISNULL(MAX(Generation),0)+1 AS n FROM KVK.SourcePublication WITH (UPDLOCK,HOLDLOCK) WHERE SourceKey=? AND KVK_NO=? AND PeriodID=?",
                SOURCE_KEY,
                config.kvk_no,
                config.period_id,
            )
            generation = one(cursor)["n"]
            selection = snapshot.calculation.selection
            for event in (selection.start, selection.end):
                if event is not None:
                    cursor.execute(
                        "IF NOT EXISTS (SELECT 1 FROM KVK.SourceScanBinding WHERE ConfigVersionID=? AND LogicalScanID=?) INSERT KVK.SourceScanBinding (ConfigVersionID,SourceKey,KVK_NO,LogicalScanID) VALUES (?,?,?,?)",
                        config.version_id,
                        event.logical_scan_id,
                        config.version_id,
                        SOURCE_KEY,
                        config.kvk_no,
                        event.logical_scan_id,
                    )
            aggregate = snapshot.aggregate
            utc = datetime.now(UTC).replace(tzinfo=None, microsecond=0)
            cursor.execute(
                "INSERT KVK.SourcePublication (PublicationID,SourceKey,KVK_NO,PeriodID,PeriodKey,Generation,ConfigVersionID,RosterID,CalculationVersion,StartScanID,EndScanID,StartRevisionID,EndRevisionID,AggregateReportID,AggregateRevisionID,PlayerState,AggregateState,PeriodState,BuildState,EligibleCount,ResultCount,KingdomCount,CampCount,CreatedUTC,FinalUnavailableReason) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'building',?,?,?,?,?,?)",
                publication_id,
                SOURCE_KEY,
                config.kvk_no,
                config.period_id,
                config.period_key,
                generation,
                config.version_id,
                config.roster_id,
                snapshot.calculation.calculation_version,
                selection.start.logical_scan_id if selection.start else None,
                selection.end.logical_scan_id if selection.end else None,
                selection.start.revision_id if selection.start else None,
                selection.end.revision_id if selection.end else None,
                aggregate.report_id if aggregate else None,
                aggregate.revision_id if aggregate else None,
                snapshot.player_state.value,
                snapshot.aggregate_state.value,
                snapshot.period_state.value,
                snapshot.calculation.eligible_count,
                0,
                len(aggregate.report.kingdom_rows) if aggregate else 0,
                len(aggregate.report.camp_rows) if aggregate else 0,
                utc,
                snapshot.final_unavailable_reason,
            )
            for result in result_rows:
                columns = [
                    "PublicationID",
                    "SourceKey",
                    "KVK_NO",
                    "ConfigVersionID",
                    "RosterID",
                    *result,
                ]
                cursor.execute(
                    "INSERT KVK.SourcePlayerResult ("
                    + ",".join(columns)
                    + ") VALUES ("
                    + ",".join("?" for _ in columns)
                    + ")",
                    publication_id,
                    SOURCE_KEY,
                    config.kvk_no,
                    config.version_id,
                    config.roster_id,
                    *result.values(),
                )
            persisted = publication_results(cursor, publication_id)
            if (
                len(persisted) != snapshot.calculation.eligible_count
                or result_digest(persisted) != manifest
            ):
                raise SourceConflict("Candidate result count or precision changed in storage.")
            cursor.execute(
                "UPDATE KVK.SourcePublication SET BuildState='complete',ResultCount=?,ManifestHash=?,CompletedUTC=? WHERE PublicationID=? AND BuildState='building'",
                len(persisted),
                manifest,
                utc,
                publication_id,
            )
            cursor.execute(
                "SELECT * FROM KVK.SourcePublication WHERE PublicationID=?", publication_id
            )
            return one(cursor)

    def read_action(self, action_id):
        with transaction(self.connect) as cursor:
            cursor.execute("SELECT * FROM KVK.SourceAction WHERE ActionID=?", action_id)
            return one(cursor)

    def select_publication(
        self,
        *,
        kvk_no,
        period_id,
        publication_id,
        action_id,
        expected_selection_version,
        expected_routing_version,
        actor,
        reason,
        action_type="publish",
        request_id=None,
        destinations=(),
        admin_authorized=False,
        validate_inputs,
    ):
        if action_type not in ("publish", "endpoint_update", "correct", "finalize", "rollback"):
            raise ValueError("Unsupported publication action.")
        if action_type in ("correct", "finalize", "rollback") and not admin_authorized:
            raise PermissionError("Administrative publication authority required.")
        if not actor.strip() or len(actor) > 128 or not reason.strip() or len(reason) > 1024:
            raise ValueError("Publication actor and reason required.")
        if any(
            kind not in ("discord", "sheets", "file")
            or not target.strip()
            or target != target.strip()
            or len(target) > 128
            for kind, target in destinations
        ):
            raise ValueError("Invalid delivery destination identity.")
        with transaction(self.connect) as cursor:
            routing, selection, requests = locked_period(cursor, kvk_no, period_id)
            cursor.execute("SELECT * FROM KVK.SourceAction WHERE ActionID=?", action_id)
            prior = one(cursor)
            if prior:
                if (
                    prior["KVK_NO"],
                    str(prior["PeriodID"]),
                    str(prior["NewPublicationID"]),
                    prior["Actor"],
                    prior["ExpectedSelectionVersion"],
                    prior["ActionType"],
                ) != (
                    kvk_no,
                    period_id,
                    publication_id,
                    actor,
                    expected_selection_version,
                    action_type,
                ):
                    raise SourceConflict("Action replay differs from durable outcome.")
                return prior
            version = selection["SelectionVersion"] if selection else 0
            if (
                version != expected_selection_version
                or (routing["RoutingVersion"] if routing else 0) != expected_routing_version
            ):
                raise SourceConflict("Publication CAS lost; rebuild from the new selection.")
            cursor.execute(
                "SELECT * FROM KVK.SourcePublication WHERE PublicationID=? AND SourceKey=? AND KVK_NO=? AND PeriodID=?",
                publication_id,
                SOURCE_KEY,
                kvk_no,
                period_id,
            )
            candidate = one(cursor)
            if not candidate or candidate["BuildState"] != "complete":
                raise SourceConflict("Only complete same-period candidates can be selected.")
            desired = desired_config(cursor, selection, requests)
            if (
                action_type != "rollback"
                and desired is not None
                and str(candidate["ConfigVersionID"]) != desired
            ):
                raise SourceConflict("Candidate no longer matches desired configuration.")
            result_rows = publication_results(cursor, publication_id)
            if (
                len(result_rows) != candidate["EligibleCount"]
                or len(result_rows) != candidate["ResultCount"]
                or result_digest(result_rows) != bytes(candidate["ManifestHash"])
            ):
                raise SourceConflict("Candidate completeness verification failed.")
            validate_inputs(cursor)
            request = next((r for r in requests if str(r["RequestID"]) == request_id), None)
            if (
                action_type == "endpoint_update"
                and (
                    not request
                    or str(request["DesiredConfigVersionID"]) != str(candidate["ConfigVersionID"])
                )
            ) or (request_id and not request):
                raise SourceConflict("Endpoint request does not authorize this candidate.")
            if selection:
                cursor.execute(
                    "SELECT * FROM KVK.SourcePublication WHERE PublicationID=?",
                    selection["PublicationID"],
                )
                old = one(cursor)
                if action_type == "endpoint_update":
                    cursor.execute(
                        "SELECT RosterID,MappingDigest,WeightDigest FROM KVK.SourceConfigVersion WHERE ConfigVersionID=?",
                        old["ConfigVersionID"],
                    )
                    old_config = one(cursor)
                    cursor.execute(
                        "SELECT RosterID,MappingDigest,WeightDigest FROM KVK.SourceConfigVersion WHERE ConfigVersionID=?",
                        candidate["ConfigVersionID"],
                    )
                    new_config = one(cursor)
                    if (
                        old_config != new_config
                        or (
                            request["OldStartScanID"] == request["NewStartScanID"]
                            and old["StartRevisionID"] != candidate["StartRevisionID"]
                        )
                        or candidate["StartScanID"] != request["NewStartScanID"]
                        or (
                            old["EndScanID"] == candidate["EndScanID"]
                            and old["EndRevisionID"] != candidate["EndRevisionID"]
                        )
                        or str(old["ConfigVersionID"]) != str(request["BaseConfigVersionID"])
                    ):
                        raise SourceConflict(
                            "Endpoint authority cannot change unrequested start, roster, map or weights."
                        )
                if old["PlayerState"] in ("final", "corrected_final") and action_type not in (
                    "correct",
                    "rollback",
                    "endpoint_update",
                ):
                    if (
                        str(old["StartRevisionID"]),
                        str(old["EndRevisionID"]),
                        str(old["ConfigVersionID"]),
                    ) != (
                        str(candidate["StartRevisionID"]),
                        str(candidate["EndRevisionID"]),
                        str(candidate["ConfigVersionID"]),
                    ):
                        raise SourceConflict(
                            "Pinned final player inputs require correction authority."
                        )
                cursor.execute(
                    "UPDATE KVK.SourceSelection SET PublicationID=?,SelectionVersion=?,SelectedUTC=SYSUTCDATETIME() WHERE SourceKey=? AND KVK_NO=? AND PeriodID=? AND SelectionVersion=?",
                    publication_id,
                    version + 1,
                    SOURCE_KEY,
                    kvk_no,
                    period_id,
                    version,
                )
            else:
                cursor.execute(
                    "INSERT KVK.SourceSelection (SourceKey,KVK_NO,PeriodID,PublicationID,SelectionVersion,SelectedUTC) VALUES (?,?,?,?,1,SYSUTCDATETIME())",
                    SOURCE_KEY,
                    kvk_no,
                    period_id,
                    publication_id,
                )
            cursor.execute(
                "INSERT KVK.SourceAction (ActionID,SourceKey,KVK_NO,PeriodID,ActionType,Actor,ExpectedSelectionVersion,NewSelectionVersion,OldPublicationID,NewPublicationID,RequestID,Reason,ActionUTC,ProvenanceJson) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,SYSUTCDATETIME(),?)",
                action_id,
                SOURCE_KEY,
                kvk_no,
                period_id,
                action_type,
                actor,
                version,
                version + 1,
                selection["PublicationID"] if selection else None,
                publication_id,
                request_id,
                reason,
                canonical({"routing_version": expected_routing_version}),
            )
            for kind, destination in sorted(set(destinations)):
                cursor.execute(
                    "IF NOT EXISTS (SELECT 1 FROM KVK.SourceDelivery WHERE PublicationID=? AND DestinationKind=? AND DestinationID=?) INSERT KVK.SourceDelivery (PublicationID,SourceKey,KVK_NO,PeriodID,DestinationKind,DestinationID,DeliveryState,AttemptCount,Fence,CreatedUTC,UpdatedUTC) VALUES (?,?,?,?,?,?,'pending',0,0,SYSUTCDATETIME(),SYSUTCDATETIME())",
                    publication_id,
                    kind,
                    destination,
                    publication_id,
                    SOURCE_KEY,
                    kvk_no,
                    period_id,
                    kind,
                    destination,
                )
            if (
                request
                and candidate["StartScanID"] == request["NewStartScanID"]
                and (
                    request["NewEndScanID"] is None
                    or candidate["EndScanID"] == request["NewEndScanID"]
                )
            ):
                cursor.execute(
                    "UPDATE KVK.SourceConfigRequest SET RequestState='applied',AppliedPublicationID=?,CompletedUTC=SYSUTCDATETIME() WHERE RequestID=?",
                    publication_id,
                    request_id,
                )
            cursor.execute("SELECT * FROM KVK.SourceAction WHERE ActionID=?", action_id)
            return one(cursor)
