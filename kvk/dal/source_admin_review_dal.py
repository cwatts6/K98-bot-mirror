"""Owner-scoped durable reviews; operations join one caller-owned transaction."""

from datetime import UTC
import hashlib
import json
from uuid import uuid4

from kvk.dal.new_source_admin_dal import _BorrowedConnection
from kvk.dal.new_source_import_dal import SourceConflict, lock_scope, one, rows, transaction
from kvk.models.source_integration import REVIEW_KINDS, identity, review_payload


class SourceAdminReviewDAL:
    def __init__(self, connect):
        self.connect = connect

    def read_update(self, update_id):
        from kvk.dal.source_update_dal import SourceUpdateDAL

        return SourceUpdateDAL(self.connect).read(update_id)

    @staticmethod
    def _read(cursor, review_id, actor):
        cursor.execute(
            "SELECT * FROM KVK.SourceAdminReview WITH (UPDLOCK,HOLDLOCK) "
            "WHERE ReviewID=? AND ActorID=? AND GuildID=? AND ChannelID=?",
            identity(review_id),
            str(actor.user_id),
            str(actor.guild_id),
            str(actor.channel_id),
        )
        row = one(cursor)
        if row is None:
            raise SourceConflict("Review unavailable for this owner, guild and channel.")
        if bytes(row["PayloadHash"]) != hashlib.sha256(row["PayloadJson"].encode()).digest():
            raise SourceConflict("Retained review payload failed verification.")
        row["payload"] = json.loads(row["PayloadJson"])
        row["ReviewID"] = identity(row["ReviewID"])
        row["outcome"] = json.loads(row["OutcomeJson"]) if row["OutcomeJson"] else None
        return row

    def read(self, review_id, actor):
        with transaction(self.connect) as cursor:
            return self._read(cursor, review_id, actor)

    def create(self, *, actor, kvk_no, kind, payload, now, expires, review_id=None):
        if kind not in REVIEW_KINDS or type(kvk_no) is not int or kvk_no <= 0:
            raise ValueError("Invalid review kind or season.")
        text = review_payload(payload)
        key = identity(review_id) if review_id else str(uuid4())
        with transaction(self.connect) as cursor:
            lock_scope(cursor, kvk_no)
            cursor.execute("SELECT ReviewID FROM KVK.SourceAdminReview WHERE ReviewID=?", key)
            if one(cursor):
                prior = self._read(cursor, key, actor)
                if (prior["KVK_NO"], prior["ReviewKind"], prior["PayloadJson"]) != (
                    kvk_no,
                    kind,
                    text,
                ):
                    raise SourceConflict("Review replay conflicts with retained evidence.")
                return prior
            cursor.execute(
                "INSERT KVK.SourceAdminReview "
                "(ReviewID,KVK_NO,ReviewKind,ActorID,GuildID,ChannelID,Version,ReviewState,"
                "PayloadJson,PayloadHash,CreatedUTC,ExpiresUTC) VALUES (?,?,?,?,?,?,1,'pending',?,?,?,?)",
                key,
                kvk_no,
                kind,
                str(actor.user_id),
                str(actor.guild_id),
                str(actor.channel_id),
                text,
                hashlib.sha256(text.encode()).digest(),
                now.replace(tzinfo=None),
                expires.replace(tzinfo=None),
            )
            return self._read(cursor, key, actor)

    def finish(self, review_id, actor, expected_version, *, now, operation=None, cancel=False):
        # Read the immutable season key before acquiring locks in the common order.
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT KVK_NO FROM KVK.SourceAdminReview WHERE ReviewID=? AND ActorID=? AND GuildID=? AND ChannelID=?",
                identity(review_id),
                str(actor.user_id),
                str(actor.guild_id),
                str(actor.channel_id),
            )
            scope = one(cursor)
            if scope is None:
                raise SourceConflict("Review unavailable for this owner, guild and channel.")
            lock_scope(cursor, scope["KVK_NO"])
            row = self._read(cursor, review_id, actor)
            if row["ReviewState"] != "pending":
                if expected_version not in (row["Version"], row["Version"] - 1):
                    raise SourceConflict("Review version is stale.")
                return row
            if row["Version"] != expected_version:
                raise SourceConflict("Review version is stale; resume it.")
            if not cancel and now >= row["ExpiresUTC"].replace(tzinfo=UTC):
                raise SourceConflict("Review expired; prepare a new review of current state.")
            outcome = (
                {"state": "cancelled; accepted inputs retained"}
                if cancel
                else operation(row, cursor, lambda: _BorrowedConnection(cursor))
            )
            cursor.execute(
                "UPDATE KVK.SourceAdminReview SET ReviewState=?,Version=Version+1,OutcomeJson=?,"
                "CompletedUTC=? OUTPUT inserted.ReviewID WHERE ReviewID=? AND Version=? AND ReviewState='pending'",
                "cancelled" if cancel else "completed",
                review_payload(outcome),
                now.replace(tzinfo=None),
                identity(review_id),
                expected_version,
            )
            if one(cursor) is None:
                raise SourceConflict("Review completion CAS lost.")
            return self._read(cursor, review_id, actor)

    def seasons(self):
        with transaction(self.connect) as cursor:
            cursor.execute("SELECT DISTINCT KVK_NO FROM dbo.KVK_Details ORDER BY KVK_NO DESC")
            return [r["KVK_NO"] for r in rows(cursor)]

    def default_season(self):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (1) KVK_NO FROM KVK.SourceRoster ORDER BY KVK_NO DESC,RosterVersion DESC"
            )
            baseline = one(cursor)
            if baseline:
                return baseline["KVK_NO"]
            cursor.execute("SELECT TOP (1) KVK_NO FROM dbo.KVK_Details ORDER BY KVK_NO DESC")
            season = one(cursor)
            return season["KVK_NO"] if season else None

    @staticmethod
    def imported_configuration(cursor, kvk_no, *, prefer_source=True):
        cursor.execute(
            "SELECT Kingdom,CampID,CampName FROM KVK.KVK_CampMap WHERE KVK_NO=? ORDER BY Kingdom",
            kvk_no,
        )
        mapping = [[r["Kingdom"], r["CampID"], r["CampName"]] for r in rows(cursor)]
        cursor.execute(
            "SELECT TOP (1) WeightT4X,WeightT5Y,WeightDeadsZ,EffectiveFromUTC "
            "FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC",
            kvk_no,
        )
        weight = one(cursor)
        cursor.execute(
            "SELECT WindowName,WindowSeq,StartScanID,EndScanID FROM KVK.KVK_Windows "
            "WHERE KVK_NO=? ORDER BY WindowSeq,WindowName",
            kvk_no,
        )
        windows = rows(cursor)
        # These are explicitly labelled legacy stored values, not original decimal tokens.
        weights = (
            [str(weight[k]) for k in ("WeightT4X", "WeightT5Y", "WeightDeadsZ")] if weight else []
        )
        snapshot = dict(
            mapping=mapping,
            weights=weights,
            effective=(
                weight["EffectiveFromUTC"].replace(tzinfo=UTC).isoformat() if weight else None
            ),
            windows=windows,
            weight_provenance="legacy stored values; explicit review required",
        )
        if prefer_source:
            cursor.execute(
                "SELECT TOP (1) PayloadJson,PayloadHash FROM KVK.SourceAdminReview WHERE KVK_NO=? AND ActorID='system:proc_config_import' AND JSON_VALUE(PayloadJson,'$.import_snapshot')='true' ORDER BY ReviewSequence DESC",
                kvk_no,
            )
            imported = one(cursor)
            if imported:
                if (
                    bytes(imported["PayloadHash"])
                    != hashlib.sha256(imported["PayloadJson"].encode()).digest()
                ):
                    raise SourceConflict("Imported configuration snapshot failed verification.")
                payload = json.loads(imported["PayloadJson"])
                if payload["legacy_snapshot"] != snapshot:
                    raise SourceConflict(
                        "Imported configuration changed outside its retained snapshot; refresh kvk_list."
                    )
                snapshot["weights"] = payload["source_weights"]
                snapshot["weight_provenance"] = "original kvk_list decimal tokens"
        return snapshot

    @staticmethod
    def snapshot_import(cursor, source_weights, *, now):
        """Called inside the existing importer transaction; never grants admin authority."""
        from datetime import timedelta

        from kvk.schemas.new_source_schema import SOURCE_KEY

        cursor.execute("SELECT @@TRANCOUNT")
        if cursor.fetchone()[0] < 1:
            raise ValueError("Configuration snapshots require the importer transaction.")
        for season, coefficients in sorted(source_weights.items()):
            lock_scope(cursor, season)
            cursor.execute("SELECT SourceKey FROM KVK.SeasonSource WHERE KVK_NO=?", season)
            choice = one(cursor)
            if not choice or choice["SourceKey"] != SOURCE_KEY:
                continue
            from decimal import Decimal

            from kvk.models.new_source_reporting import fits_decimal

            if len(coefficients) != 3 or any(
                not isinstance(value, str) or not fits_decimal(Decimal(value), 12)
                for value in coefficients
            ):
                raise ValueError("New-source weights require exact original decimal text.")
            payload = review_payload(
                dict(
                    import_snapshot=True,
                    source_weights=coefficients,
                    legacy_snapshot=SourceAdminReviewDAL.imported_configuration(
                        cursor, season, prefer_source=False
                    ),
                )
            )
            cursor.execute(
                "INSERT KVK.SourceAdminReview (ReviewID,KVK_NO,ReviewKind,ActorID,GuildID,ChannelID,Version,ReviewState,PayloadJson,PayloadHash,CreatedUTC,ExpiresUTC) VALUES (?,?,'configuration','system:proc_config_import','system','system',1,'pending',?,?,?,?)",
                str(uuid4()),
                season,
                payload,
                hashlib.sha256(payload.encode()).digest(),
                now.replace(tzinfo=None),
                (now + timedelta(days=365)).replace(tzinfo=None),
            )

    def configuration(self, kvk_no):
        with transaction(self.connect) as cursor:
            lock_scope(cursor, kvk_no)
            return self.imported_configuration(cursor, kvk_no)

    def configuration_context(self, kvk_no):
        from kvk.dal.new_source_config_dal import locked_period
        from kvk.dal.new_source_recovery_dal import current_config
        from kvk.dal.season_source_dal import require_source
        from kvk.schemas.new_source_schema import SOURCE_KEY

        with transaction(self.connect) as cursor:
            lock_scope(cursor, kvk_no)
            choice = require_source(cursor, kvk_no, SOURCE_KEY)
            snapshot = self.imported_configuration(cursor, kvk_no)
            cursor.execute(
                "SELECT PeriodID,PeriodKey FROM KVK.SourcePeriod WHERE SourceKey=? AND KVK_NO=? ORDER BY PeriodKey",
                SOURCE_KEY,
                kvk_no,
            )
            periods = rows(cursor)
            planned = []
            for period in periods:
                _, selected, requests = locked_period(cursor, kvk_no, period["PeriodID"])
                config_id = current_config(cursor, kvk_no, period["PeriodID"], selected, requests)
                if not config_id:
                    continue
                cursor.execute(
                    "SELECT Kingdom,CampID,CampName FROM KVK.SourceCampConfig WHERE ConfigVersionID=? ORDER BY Kingdom",
                    config_id,
                )
                old_mapping = [[r["Kingdom"], r["CampID"], r["CampName"]] for r in rows(cursor)]
                cursor.execute(
                    "SELECT WeightT4XSource,WeightT5YSource,WeightDeadsZSource FROM KVK.SourceWeightConfig WHERE ConfigVersionID=?",
                    config_id,
                )
                old_weight = one(cursor)
                old_weights = (
                    [
                        old_weight[k]
                        for k in ("WeightT4XSource", "WeightT5YSource", "WeightDeadsZSource")
                    ]
                    if old_weight
                    else []
                )
                cursor.execute(
                    "SELECT WindowName,StartScanID,EndScanID FROM KVK.SourceWindowConfig WHERE ConfigVersionID=? AND PeriodKey=?",
                    config_id,
                    period["PeriodKey"],
                )
                window = one(cursor)
                desired = next(
                    (w for w in snapshot["windows"] if w["WindowName"] == window["WindowName"]),
                    None,
                )
                if desired is None:
                    raise SourceConflict(
                        "An approved window is missing from the import; deletion needs separate review."
                    )
                cursor.execute(
                    "SELECT u.UpdateID,u.StartScanID,u.EndScanID,u.StartRevisionID,u.EndRevisionID,u.AggregateRevisionID,u.CoverageStartUTC,u.CoverageEndUTC,u.AsOfUTC FROM KVK.SourceCompleteSelection s JOIN KVK.SourceUpdate u ON u.UpdateID=s.UpdateID WHERE s.SourceKey=? AND s.KVK_NO=? AND s.PeriodID=?",
                    SOURCE_KEY,
                    kvk_no,
                    period["PeriodID"],
                )
                base = one(cursor)
                if base:
                    for key in ("CoverageStartUTC", "CoverageEndUTC", "AsOfUTC"):
                        base[key] = base[key].replace(tzinfo=UTC).isoformat()
                planned.append(
                    dict(
                        period_id=period["PeriodID"],
                        period_key=period["PeriodKey"],
                        base_config_id=config_id,
                        old_window=window,
                        desired_window=desired,
                        old_mapping=old_mapping,
                        old_weights=old_weights,
                        base_update=base,
                    )
                )
            return dict(snapshot=snapshot, periods=planned, season_version=choice["SeasonVersion"])

    def match_context(self, kvk_no, period_key, end_scan_id, aggregate_revision_id=None):
        from kvk.dal.new_source_config_dal import locked_period
        from kvk.dal.new_source_recovery_dal import current_config
        from kvk.dal.season_source_dal import require_source
        from kvk.schemas.new_source_schema import SOURCE_KEY

        with transaction(self.connect) as cursor:
            lock_scope(cursor, kvk_no)
            choice = require_source(cursor, kvk_no, SOURCE_KEY)
            cursor.execute(
                "SELECT * FROM KVK.SourcePeriod WHERE SourceKey=? AND KVK_NO=? AND PeriodKey=?",
                SOURCE_KEY,
                kvk_no,
                period_key,
            )
            period = one(cursor)
            if not period:
                raise SourceConflict("Configure this reporting window before matching an update.")
            _, selection, requests = locked_period(cursor, kvk_no, period["PeriodID"])
            config_id = current_config(cursor, kvk_no, period["PeriodID"], selection, requests)
            cursor.execute(
                "SELECT c.ConfigVersionID,c.RosterID,w.StartScanID,w.EndScanID FROM KVK.SourceConfigVersion c "
                "JOIN KVK.SourceWindowConfig w ON w.ConfigVersionID=c.ConfigVersionID "
                "WHERE c.ConfigVersionID=? AND w.PeriodKey=?",
                config_id,
                period_key,
            )
            config = one(cursor)
            if not config or config["StartScanID"] is None:
                raise SourceConflict("Set this window's StartScanID before matching.")
            cursor.execute(
                "SELECT s.LogicalScanID,o.SelectedRevisionID FROM KVK.SourceLogicalScan s "
                "JOIN KVK.SourceObservation o ON o.ObservationID=s.ObservationID "
                "WHERE s.SourceKey=? AND s.KVK_NO=? AND s.LogicalScanID IN (?,?)",
                SOURCE_KEY,
                kvk_no,
                config["StartScanID"],
                end_scan_id,
            )
            scans = {str(r["LogicalScanID"]): r["SelectedRevisionID"] for r in rows(cursor)}
            if str(config["StartScanID"]) not in scans:
                raise SourceConflict("The configured start scan has not been accepted.")
            cursor.execute(
                "SELECT UpdateID FROM KVK.SourceCompleteSelection WHERE SourceKey=? AND KVK_NO=? AND PeriodID=?",
                SOURCE_KEY,
                kvk_no,
                period["PeriodID"],
            )
            base = one(cursor)
            aggregate = None
            if aggregate_revision_id:
                cursor.execute(
                    "SELECT ReportID,RevisionID FROM KVK.SourceAggregateRevision "
                    "WHERE SourceKey=? AND KVK_NO=? AND RevisionID=?",
                    SOURCE_KEY,
                    kvk_no,
                    identity(aggregate_revision_id),
                )
                aggregate = one(cursor)
                if not aggregate:
                    raise SourceConflict("Aggregate revision unavailable in this season.")
            request = next((r for r in requests if r["DesiredConfigVersionID"] == config_id), None)
            return dict(
                choice_id=choice["ChoiceID"],
                season_version=choice["SeasonVersion"],
                period_id=period["PeriodID"],
                period_kind=period["PeriodKind"],
                config=config,
                scans=scans,
                aggregate=aggregate,
                base_update_id=base["UpdateID"] if base else None,
                request_id=request["RequestID"] if request else None,
                configuration_review=(
                    json.loads(request["ProvenanceJson"]).get("configuration_review")
                    if request
                    else None
                ),
            )
