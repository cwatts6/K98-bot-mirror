"""S5B durable discovery and typed input loading over the accepted S2/S3 schema.

No schema creation, legacy scan allocation, artifact import or external delivery.
The import hook borrows its caller's cursor and never commits it.
"""

from datetime import UTC, datetime
from decimal import Decimal
import json

from kvk.dal.new_source_config_dal import desired_config, locked_period
from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from kvk.models.new_source_observation import (
    CampMapping,
    MetadataCandidate,
    MetadataConfirmation,
    MetricValue,
    PreparedAggregateReport,
    PreparedPlayerObservation,
    SemanticDigest,
    SourceRow,
    SourceScope,
    TypedCell,
    ValidatedSourceMetadata,
)
from kvk.models.new_source_reporting import (
    AggregateSelection,
    FrozenWeights,
    ObservationInput,
    PeriodKind,
    StreamState,
    WindowConfig,
    WindowInputSelection,
)
from kvk.schemas.new_source_schema import (
    AGGREGATE_METRICS,
    PLAYER_SHEET,
    PLAYER_TEXT_HEADERS,
    SOURCE_KEY,
    MetricState,
    ReportState,
    SourceKind,
    TimePrecision,
)
from kvk.services.new_source_config_service import request_endpoint_update


def require_schema(cursor):
    # Resolve columns as well as tables; disabled callers never reach this query.
    cursor.execute(
        "SELECT TOP (0) r.RequestID,r.DesiredConfigVersionID,c.ConfigVersionID,"
        "w.WindowName,p.PeriodID,s.PublicationID,d.Fence,o.SelectedRevisionID "
        "FROM KVK.SourceConfigRequest r CROSS JOIN KVK.SourceConfigVersion c "
        "CROSS JOIN KVK.SourceWindowConfig w CROSS JOIN KVK.SourcePeriod p "
        "CROSS JOIN KVK.SourceSelection s CROSS JOIN KVK.SourceDelivery d "
        "CROSS JOIN KVK.SourceObservation o"
    )
    cursor.fetchall()
    cursor.execute(
        "SELECT TOP (0) s.ChoiceID,u.UpdateID,c.PublicSelectionVersion,i.IntentID,v.ConfigVersionID FROM KVK.SeasonSource s CROSS JOIN KVK.SourceUpdate u CROSS JOIN KVK.SourceCompleteSelection c CROSS JOIN KVK.SourceExportIntent i CROSS JOIN KVK.SourceExportIntentPublication v"
    )
    cursor.fetchall()


def current_config(cursor, kvk_no, period_id, selection, requests):
    identity = desired_config(cursor, selection, requests)
    if identity is None:
        cursor.execute(
            "SELECT TOP (1) c.ConfigVersionID FROM KVK.SourceConfigVersion c "
            "JOIN KVK.SourceWindowConfig w ON w.ConfigVersionID=c.ConfigVersionID "
            "JOIN KVK.SourcePeriod p ON p.SourceKey=w.SourceKey AND p.KVK_NO=w.KVK_NO "
            "AND p.PeriodKey=w.PeriodKey WHERE c.SourceKey=? AND c.KVK_NO=? "
            "AND p.PeriodID=? ORDER BY c.ConfigVersion DESC",
            SOURCE_KEY,
            kvk_no,
            period_id,
        )
        record = one(cursor)
        identity = str(record["ConfigVersionID"]) if record else None
    return identity


def snapshot_import(cursor, windows, *, actor, origin, provenance, requested_utc):
    require_schema(cursor)
    cursor.execute("SELECT @@TRANCOUNT")
    if cursor.fetchone()[0] < 1:
        raise SourceConflict("Source hook requires the existing config transaction.")
    result = []
    for window in sorted(windows, key=lambda w: (w["KVK_NO"], w["WindowName"])):
        season = window["KVK_NO"]
        # Lock before resolving the current desired version, not after a stale read.
        from kvk.dal.new_source_import_dal import lock_scope

        lock_scope(cursor, season)
        cursor.execute(
            "SELECT DISTINCT p.PeriodID FROM KVK.SourceWindowConfig w "
            "JOIN KVK.SourcePeriod p ON p.SourceKey=w.SourceKey AND p.KVK_NO=w.KVK_NO "
            "AND p.PeriodKey=w.PeriodKey WHERE w.SourceKey=? AND w.KVK_NO=? AND w.WindowName=?",
            SOURCE_KEY,
            season,
            window["WindowName"],
        )
        periods = rows(cursor)
        if not periods:
            continue  # Legacy or not onboarded: no new source authority is invented.
        if len(periods) != 1:
            raise SourceConflict("Imported window has ambiguous source period mapping.")
        period = str(periods[0]["PeriodID"])
        _, selected, requests = locked_period(cursor, season, period)
        base = current_config(cursor, season, period, selected, requests)
        if base is None:
            raise SourceConflict("Imported window has no approved source configuration.")
        row = request_endpoint_update(
            cursor,
            authorized=True,
            kvk_no=season,
            period_id=period,
            base_config_id=base,
            new_start_scan_id=window["StartScanID"],
            new_end_scan_id=window["EndScanID"],
            actor=actor,
            origin=origin,
            reason="Authorized Windows endpoint import",
            requested_utc=requested_utc,
            provenance=provenance,
        )
        if row:
            result.append(str(row["RequestID"]))
    return tuple(result)


def _utc(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def endpoint_chain(requests, base, desired):
    """Prove the contiguous authorized chain; rejected/other-period links cannot join."""
    chain, seen = [], set()
    current = str(desired)
    while current != str(base):
        if current in seen:
            raise SourceConflict("Cyclic endpoint request chain.")
        seen.add(current)
        matches = [
            r
            for r in requests
            if str(r["DesiredConfigVersionID"]) == current and r["RequestState"] != "rejected"
        ]
        if len(matches) != 1:
            raise SourceConflict("Incomplete endpoint request chain.")
        row = matches[0]
        if chain and (
            row["SourceKey"],
            row["KVK_NO"],
            str(row["PeriodID"]),
            row["NewStartScanID"],
            row["NewEndScanID"],
        ) != (
            chain[-1]["SourceKey"],
            chain[-1]["KVK_NO"],
            str(chain[-1]["PeriodID"]),
            chain[-1]["OldStartScanID"],
            chain[-1]["OldEndScanID"],
        ):
            raise SourceConflict("Endpoint request chain scope or bounds differ.")
        chain.append(row)
        current = str(row["BaseConfigVersionID"])
    if not chain:
        raise SourceConflict("Endpoint request chain is empty.")
    return tuple(reversed(chain))


def _metadata(payload):
    data = json.loads(payload)
    candidate = data["candidate"]
    for key in ("scan_start_utc", "coverage_start_utc", "coverage_end_utc", "as_of_utc"):
        candidate[key] = _utc(candidate.get(key))
    for key, enum in (
        ("kind", SourceKind),
        ("time_precision", TimePrecision),
        ("report_state", ReportState),
    ):
        if candidate.get(key) is not None:
            candidate[key] = enum(candidate[key])
    scope = data["scope"]
    confirmation = data["confirmation"]
    # Provenance values are not interpreted as new authority by the worker.
    return ValidatedSourceMetadata(
        MetadataCandidate(**candidate),
        SourceScope(scope["kvk_no"], tuple(scope["kingdoms"]), tuple(scope["period_keys"])),
        MetadataConfirmation(
            tuple(tuple(x) for x in confirmation["values"]),
            tuple(confirmation["confirmed_fields"]),
            confirmation["actor"],
            _utc(confirmation["confirmed_at_utc"]),
            confirmation["reason"],
        ),
    )


def _row(payload):
    data = json.loads(payload)
    cells = []
    for raw in data["cells"]:
        metric = raw["metric"]
        numeric = Decimal(raw["numeric_value"]) if raw["numeric_value"] is not None else None
        value = metric["value"]
        # Accepted semantic type is independent of Excel numeric/text storage.
        numeric_metric = (
            raw["header"] not in PLAYER_TEXT_HEADERS
            if data["sheet"] == PLAYER_SHEET
            else raw["header"] in (*AGGREGATE_METRICS, "KD")
        )
        if numeric_metric and value is not None:
            value = Decimal(value)
        cells.append(
            TypedCell(
                raw["header"],
                raw["cell_type"],
                raw["raw_value"],
                numeric,
                raw["number_format"],
                MetricValue(
                    value,
                    MetricState(metric["state"]),
                    metric["raw_token"],
                    (
                        Decimal(metric["displayed_unit"])
                        if metric["displayed_unit"] is not None
                        else None
                    ),
                    metric["precision_kind"],
                ),
            )
        )
    return SourceRow(data["sheet"], data["key"], tuple(cells), data["kingdom"], data["camp_id"])


class RecoveryDAL:
    def __init__(self, connect):
        self.connect = connect

    def check_schema(self):
        with transaction(self.connect) as cursor:
            require_schema(cursor)

    def ready_updates(self, season, period):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT u.* FROM KVK.SourceUpdate u JOIN KVK.SeasonSource s ON s.KVK_NO=u.KVK_NO AND s.ChoiceID=u.ChoiceID "
                "WHERE u.SourceKey=? AND u.KVK_NO=? AND u.PeriodID=? AND u.UpdateState IN ('ready','waiting_player') AND s.SeasonState='open' ORDER BY u.ConfirmedUTC,u.UpdateID",
                SOURCE_KEY,
                season,
                period,
            )
            return rows(cursor)

    def periods(self, after=(0, ""), limit=8):
        if type(limit) is not int or not 1 <= limit <= 32:
            raise ValueError("Invalid recovery batch size.")
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (?) p.KVK_NO,CONVERT(varchar(36),p.PeriodID) AS PeriodID "
                "FROM KVK.SourcePeriod p WHERE p.SourceKey=? AND "
                "(p.KVK_NO>? OR (p.KVK_NO=? AND CONVERT(varchar(36),p.PeriodID)>?)) "
                "AND EXISTS (SELECT 1 FROM KVK.SourceWindowConfig w WHERE w.SourceKey=p.SourceKey "
                "AND w.KVK_NO=p.KVK_NO AND w.PeriodKey=p.PeriodKey) "
                "ORDER BY p.KVK_NO,CONVERT(varchar(36),p.PeriodID)",
                limit,
                SOURCE_KEY,
                after[0],
                after[0],
                after[1],
            )
            return tuple((r["KVK_NO"], str(r["PeriodID"])) for r in rows(cursor))

    @staticmethod
    def _config(cursor, identity, season, period):
        cursor.execute(
            "SELECT c.*,w.WindowName,w.StartScanID,w.EndScanID,p.PeriodKey,p.PeriodKind,"
            "p.CoverageEndUTC,r.B0RevisionID FROM KVK.SourceConfigVersion c "
            "JOIN KVK.SourceWindowConfig w ON w.ConfigVersionID=c.ConfigVersionID "
            "JOIN KVK.SourcePeriod p ON p.SourceKey=w.SourceKey AND p.KVK_NO=w.KVK_NO "
            "AND p.PeriodKey=w.PeriodKey JOIN KVK.SourceRoster r ON r.RosterID=c.RosterID "
            "WHERE c.ConfigVersionID=? AND c.SourceKey=? AND c.KVK_NO=? AND p.PeriodID=?",
            identity,
            SOURCE_KEY,
            season,
            period,
        )
        config = one(cursor)
        if not config:
            raise SourceConflict("Recovery configuration is unavailable.")
        cursor.execute(
            "SELECT Kingdom,CampID,CampName FROM KVK.SourceCampConfig WHERE ConfigVersionID=? ORDER BY Kingdom",
            identity,
        )
        mapping = CampMapping(
            tuple((r["Kingdom"], r["CampID"], r["CampName"]) for r in rows(cursor))
        )
        cursor.execute("SELECT * FROM KVK.SourceWeightConfig WHERE ConfigVersionID=?", identity)
        weight = one(cursor)
        weights = (
            FrozenWeights(
                bytes(config["WeightDigest"]).hex(),
                weight["WeightT4XSource"],
                weight["WeightT5YSource"],
                weight["WeightDeadsZSource"],
                _utc(weight["EffectiveFromUTC"]),
            )
            if weight
            else None
        )
        return WindowConfig(
            identity,
            season,
            period,
            config["PeriodKey"],
            PeriodKind(config["PeriodKind"]),
            config["WindowName"],
            config["StartScanID"],
            config["EndScanID"],
            str(config["RosterID"]),
            str(config["B0RevisionID"]),
            bytes(config["MappingDigest"]).hex(),
            mapping,
            weights,
            _utc(config["CoverageEndUTC"]),
        )

    @staticmethod
    def _observation(cursor, revision):
        cursor.execute(
            "SELECT r.*,s.LogicalScanID FROM KVK.SourceObservationRevision r "
            "JOIN KVK.SourceLogicalScan s ON s.ObservationID=r.ObservationID WHERE r.RevisionID=?",
            revision,
        )
        record = one(cursor)
        if not record:
            raise SourceConflict("Accepted observation unavailable.")
        cursor.execute(
            "SELECT RawProfileJson FROM KVK.SourcePlayerSnapshot WHERE RevisionID=? ORDER BY GovernorID",
            revision,
        )
        facts = tuple(_row(r["RawProfileJson"]) for r in rows(cursor))
        metadata = _metadata(record["MetadataJson"])
        prepared = PreparedPlayerObservation(
            metadata,
            facts,
            bytes(record["ArtifactHash"]).hex(),
            record["SchemaVersion"],
            SemanticDigest(bytes(record["SemanticHash"]).hex(), record["DigestVersion"]),
            (),
        )
        return ObservationInput(
            record["LogicalScanID"],
            str(record["ObservationID"]),
            str(revision),
            prepared,
            metadata.scope.period_keys,
        )

    def load_inputs(self, season, period, *, update=None):
        with transaction(self.connect) as cursor:
            routing, selected, requests = locked_period(cursor, season, period)
            identity = current_config(cursor, season, period, selected, requests)
            if update and json.loads(update["ConfirmationJson"]).get("action") == "configure":
                from kvk.dal.source_update_dal import validate_update

                validate_update(cursor, update, complete=True, sealed=True)
                identity = update["ConfigVersionID"]
            if update and (
                identity != update["ConfigVersionID"]
                or update["KVK_NO"] != season
                or update["PeriodID"] != period
            ):
                raise SourceConflict("Sealed update no longer matches desired scope/configuration.")
            config = self._config(cursor, identity, season, period)
            old = None
            if selected:
                cursor.execute(
                    "SELECT * FROM KVK.SourcePublication WHERE PublicationID=?",
                    selected["PublicationID"],
                )
                old = one(cursor)
            request = (
                requests[0]
                if requests and str(requests[0]["DesiredConfigVersionID"]) == identity
                else None
            )
            b0 = self._observation(cursor, config.b0_revision_id)
            if update is None:
                # Read only required endpoints and latest associated interim, not every full scan.
                cursor.execute(
                    "SELECT TOP (1) r.RevisionID FROM KVK.SourceLogicalScan s "
                    "JOIN KVK.SourceObservation o ON o.ObservationID=s.ObservationID "
                    "JOIN KVK.SourceObservationRevision r ON r.RevisionID=o.SelectedRevisionID "
                    "WHERE s.SourceKey=? AND s.KVK_NO=? AND s.LogicalScanID>? "
                    "AND (? IS NULL OR s.LogicalScanID<=?) AND (? IS NULL OR o.ScanStartUTC<=?) "
                    "AND EXISTS (SELECT 1 FROM OPENJSON(r.MetadataJson,'$.scope.period_keys') WHERE value=?) "
                    "ORDER BY o.ScanStartUTC DESC",
                    SOURCE_KEY,
                    season,
                    config.start_scan_id,
                    config.end_scan_id,
                    config.end_scan_id,
                    config.closes_at_utc.replace(tzinfo=None) if config.closes_at_utc else None,
                    config.closes_at_utc.replace(tzinfo=None) if config.closes_at_utc else None,
                    config.period_key,
                )
                latest = one(cursor)
                cursor.execute(
                    "SELECT o.SelectedRevisionID FROM KVK.SourceLogicalScan s JOIN KVK.SourceObservation o "
                    "ON o.ObservationID=s.ObservationID WHERE s.SourceKey=? AND s.KVK_NO=? AND s.LogicalScanID IN (?,?)",
                    SOURCE_KEY,
                    season,
                    config.start_scan_id,
                    config.end_scan_id,
                )
                revisions = {str(r["SelectedRevisionID"]) for r in rows(cursor)}
                if latest:
                    revisions.add(str(latest["RevisionID"]))
                events = {
                    e.logical_scan_id: e for e in (self._observation(cursor, r) for r in revisions)
                }
            else:
                events = {}
            previous = None
            if old:
                old_config = self._config(cursor, str(old["ConfigVersionID"]), season, period)
                start = (
                    self._observation(cursor, old["StartRevisionID"])
                    if old["StartRevisionID"]
                    else None
                )
                end = (
                    self._observation(cursor, old["EndRevisionID"])
                    if old["EndRevisionID"]
                    else None
                )
                # Finals and endpoint-only requests cannot authorize source-content corrections.
                if (
                    old["PlayerState"] in ("final", "corrected_final")
                    or identity != old_config.version_id
                ):
                    for event in (start, end):
                        if event:
                            events[event.logical_scan_id] = event
                # A corrected-final DTO requires its persisted endpoint provenance.
                from kvk.models.new_source_reporting import EndpointChange

                prior_change = None
                if old["PlayerState"] == "corrected_final" or (
                    request
                    and request["RequestState"] in ("pending", "requested")
                    and str(request["DesiredConfigVersionID"]) == old_config.version_id
                    and old["PlayerState"] == "live"
                ):
                    prior = next(
                        (
                            r
                            for r in requests
                            if str(r["DesiredConfigVersionID"]) == old_config.version_id
                        ),
                        None,
                    )
                    if not prior:
                        raise SourceConflict("Corrected final lacks endpoint provenance.")
                    prior_change = EndpointChange(
                        str(prior["RequestID"]),
                        period,
                        str(prior["BaseConfigVersionID"]),
                        old_config.version_id,
                        prior["OldEndScanID"],
                        prior["NewEndScanID"],
                        prior["Actor"],
                        prior["Reason"],
                        prior["OldStartScanID"],
                        prior["NewStartScanID"],
                    )
                    for event in (start, end):
                        if event:
                            events[event.logical_scan_id] = event
                previous = WindowInputSelection(
                    old_config,
                    start,
                    end,
                    StreamState(old["PlayerState"]),
                    old["PlayerState"] not in ("final", "corrected_final", "not_applicable"),
                    prior_change,
                )
            if update:
                events = {
                    event.logical_scan_id: event
                    for event in (
                        self._observation(cursor, update["StartRevisionID"]),
                        self._observation(cursor, update["EndRevisionID"]),
                    )
                }
                if previous and previous.config.version_id != config.version_id:
                    for event in (previous.start, previous.end):
                        if event:
                            events.setdefault(event.logical_scan_id, event)
            aggregate = None
            if not config.is_no_fight:
                cursor.execute(
                    "SELECT r.* FROM KVK.SourceAggregateReport f JOIN KVK.SourceAggregateRevision r "
                    "ON r.ReportID=f.ReportID WHERE f.SourceKey=? AND f.KVK_NO=? AND f.PeriodKey=? AND r.RevisionID="
                    + ("?" if update else "f.SelectedRevisionID"),
                    SOURCE_KEY,
                    season,
                    config.period_key,
                    *((update["AggregateRevisionID"],) if update else ()),
                )
                record = one(cursor)
                if record:
                    groups = []
                    for table, key in (
                        ("SourceKingdomReportRow", "Kingdom"),
                        ("SourceCampReportRow", "CampID"),
                    ):
                        cursor.execute(
                            "SELECT RawCellsJson FROM KVK."
                            + table
                            + " WHERE RevisionID=? ORDER BY "
                            + key,
                            record["RevisionID"],
                        )
                        groups.append(tuple(_row(r["RawCellsJson"]) for r in rows(cursor)))
                    report = PreparedAggregateReport(
                        _metadata(record["MetadataJson"]),
                        *groups,
                        config.mapping,
                        bytes(record["ArtifactHash"]).hex(),
                        record["SchemaVersion"],
                        SemanticDigest(
                            bytes(record["SemanticHash"]).hex(), record["DigestVersion"]
                        ),
                        (),
                    )
                    aggregate = AggregateSelection(
                        str(record["ReportID"]), str(record["RevisionID"]), report
                    )
            cursor.execute("SELECT SeasonVersion FROM KVK.SeasonSource WHERE KVK_NO=?", season)
            choice = one(cursor)
            cursor.execute(
                "SELECT PublicSelectionVersion FROM KVK.SourceCompleteSelection WHERE SourceKey=? AND KVK_NO=? AND PeriodID=?",
                SOURCE_KEY,
                season,
                period,
            )
            complete = one(cursor)
            return dict(
                config=config,
                observations=tuple(events.values()),
                b0=b0,
                previous=previous,
                aggregate=aggregate,
                request=request,
                requests=requests,
                selected=selected,
                routing=routing,
                season_version=choice["SeasonVersion"] if choice else None,
                public_version=complete["PublicSelectionVersion"] if complete else 0,
            )

    def selections(self, season):
        from kvk.services.new_source_export_service import ExportSelection

        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT PeriodID,PublicationID,PublicSelectionVersion AS SelectionVersion FROM KVK.SourceCompleteSelection WHERE SourceKey=? AND KVK_NO=? ORDER BY PeriodID",
                SOURCE_KEY,
                season,
            )
            return tuple(
                ExportSelection(
                    season, str(r["PeriodID"]), str(r["PublicationID"]), r["SelectionVersion"]
                )
                for r in rows(cursor)
            )
