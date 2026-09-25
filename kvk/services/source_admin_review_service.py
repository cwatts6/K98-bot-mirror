"""Explicit setup and pairing reviews over the S8B transaction contracts."""

from dataclasses import asdict
from datetime import UTC, timedelta
import json
from uuid import uuid4

from kvk.dal.new_source_import_dal import SourceConflict, canonical
from kvk.dal.source_admin_review_dal import SourceAdminReviewDAL
from kvk.models.new_source_observation import CampMapping
from kvk.models.new_source_reporting import FrozenWeights
from kvk.models.source_integration import (
    SOURCES,
    AggregateRevision,
    PlayerRevisions,
    UpdateContext,
    bounded_text,
    identity,
)
from kvk.services.new_source_admin_service import CONFIRM_SECONDS, positive, utc_now, utc_text
from kvk.services.season_source_service import SeasonSourceService
from kvk.services.source_update_service import SourceUpdateService


def validated_configuration(snapshot):
    """An import can exist but still be unsuitable for baseline acceptance."""
    if not snapshot["mapping"]:
        raise SourceConflict(
            "Import the season's kingdoms and camps with kvk_list, then Check again."
        )
    mapping = CampMapping(tuple(tuple(entry) for entry in snapshot["mapping"]))
    kingdoms, camps = set(), {}
    for kingdom, camp, name in mapping.entries:
        if (
            type(kingdom) is not int
            or kingdom <= 0
            or kingdom in kingdoms
            or type(camp) is not int
            or not 1 <= camp <= 8
            or not isinstance(name, str)
            or not 0 < len(name.strip()) <= 40
        ):
            raise SourceConflict(
                "Imported kingdom/camp configuration is invalid; correct kvk_list and Check again."
            )
        kingdoms.add(kingdom)
        label = " ".join(name.split()).casefold()
        if camp in camps and camps[camp] != label:
            raise SourceConflict("Imported camp labels disagree.")
        camps[camp] = label
    if len(set(camps.values())) != len(camps):
        raise SourceConflict("Imported camp labels must identify one camp each.")
    if len(snapshot["weights"]) != 3 or not snapshot["effective"]:
        raise SourceConflict("Import all three player DKP weights with kvk_list, then Check again.")
    FrozenWeights("review", *snapshot["weights"], utc_text(snapshot["effective"]))
    return mapping


def configured_review_service():
    from kvk.dal.new_source_admin_dal import configured_connection
    from kvk.services.new_source_admin_service import access_from_config

    return SourceAdminReviewService(
        access_from_config(), SourceAdminReviewDAL(configured_connection)
    )


class SourceAdminReviewService:
    def __init__(self, access, repository, now=utc_now):
        self.access, self.repository, self.now = access, repository, now

    def _create(self, actor, season, kind, payload):
        return self.repository.create(
            actor=actor,
            kvk_no=positive(season),
            kind=kind,
            payload=payload,
            now=self.now(),
            expires=self.now() + timedelta(seconds=CONFIRM_SECONDS),
        )

    def seasons(self, actor):
        self.access.authorize(actor)
        return self.repository.seasons()

    def default_season(self, actor):
        self.access.authorize(actor, upload=True)
        return self.repository.default_season()

    def prepare_choice(self, actor, season, source, reason):
        self.access.authorize(actor, "choose_source")
        season = positive(season)
        bounded_text(reason, 512)
        if source not in SOURCES or season not in self.repository.seasons():
            raise ValueError("Choose an imported season and a supported source.")
        return self._create(actor, season, "choose_source", dict(source=source, reason=reason))

    def prepare_configuration(self, actor, season, reason, *, attest_counterparts=False):
        self.access.authorize(actor, "configure")
        bounded_text(reason, 512)
        context = self.repository.configuration_context(positive(season))
        validated_configuration(context["snapshot"])
        if not context["periods"]:
            raise SourceConflict("Use the accepted B0 receipt to configure the first window.")
        return self._create(
            actor,
            season,
            "configuration",
            dict(
                **context,
                reason=reason,
                attest_counterparts=attest_counterparts is True,
            ),
        )

    def read(self, actor, review_id):
        self.access.authorize(actor, "status")
        return self.repository.read(identity(review_id), actor)

    def update_status(self, actor, update_id):
        self.access.authorize(actor, "match_update")
        row = SourceUpdateService(self.repository.connect).dal.read(identity(update_id))
        return f"UpdateID: {row['UpdateID']} | KVK {row['KVK_NO']} | {row['PeriodKey']}\nState: {row['UpdateState']} | version {row['Version']}"

    def cancel(self, actor, review_id, version):
        self.access.authorize(actor, "cancel")
        return self.repository.finish(review_id, actor, version, now=self.now(), cancel=True)

    def prepare_match(
        self,
        actor,
        *,
        season,
        period,
        end_scan_id,
        coverage_start,
        coverage_end,
        as_of,
        aggregate_revision_id=None,
        counterpart_revision_id=None,
        reason,
        action="publish",
        update_id=None,
    ):
        self.access.authorize(actor, "match_update")
        bounded_text(reason, 512)
        if action not in ("publish", "finalize", "correct"):
            raise ValueError("Invalid matched-update action.")
        season, end = positive(season), positive(end_scan_id)
        context = self.repository.match_context(season, period, end, aggregate_revision_id)
        config = context["config"]
        if end < config["StartScanID"] or (
            config["EndScanID"] is not None and end > config["EndScanID"]
        ):
            raise SourceConflict("The requested end is outside the approved window.")
        no_fight = config["StartScanID"] == config["EndScanID"]
        if no_fight and aggregate_revision_id:
            raise SourceConflict("No-fight has no aggregate counterpart.")
        times = [utc_text(value) for value in (coverage_start, coverage_end, as_of)]
        proof = {"action": action, "reason": reason}
        if context.get("configuration_review"):
            if action != "correct":
                raise SourceConflict(
                    "The reviewed configuration change requires a corrected matched update."
                )
            proof["configuration_review"] = context["configuration_review"]
        proof["period_assignment"] = dict(
            period_id=context["period_id"],
            config_version_id=config["ConfigVersionID"],
            start_scan_id=config["StartScanID"],
            end_scan_id=end,
            actor=str(actor.user_id),
        )
        if counterpart_revision_id:
            if not context["base_update_id"]:
                raise SourceConflict("Counterpart reuse requires a complete base update.")
            proof["counterpart"] = dict(
                base_update_id=context["base_update_id"],
                revision_id=identity(counterpart_revision_id),
                config_version_id=config["ConfigVersionID"],
                roster_id=config["RosterID"],
                coverage_start_utc=times[0].replace(tzinfo=None).isoformat(),
                coverage_end_utc=times[1].replace(tzinfo=None).isoformat(),
                as_of_utc=times[2].replace(tzinfo=None).isoformat(),
                actor=str(actor.user_id),
            )
        if str(end) not in context["scans"]:
            if not context["request_id"] or end != config["EndScanID"]:
                raise SourceConflict("Only an exact pending configured endpoint can be awaited.")
            proof["pending_player"] = dict(
                start_scan_id=config["StartScanID"],
                start_revision_id=context["scans"][str(config["StartScanID"])],
                end_scan_id=end,
            )
        update = UpdateContext(
            str(uuid4()),
            season,
            context["period_id"],
            period,
            context["choice_id"],
            config["ConfigVersionID"],
            config["RosterID"],
            *times,
            "no_fight" if no_fight else context["period_kind"],
            str(actor.user_id),
            self.now(),
            canonical(proof),
            context["request_id"],
            context["base_update_id"],
        )
        if update_id:
            retained = self.repository.read_update(identity(update_id))
            if retained["ConfirmedBy"] != str(actor.user_id) or retained["UpdateState"] not in (
                "waiting_player",
                "waiting_aggregate",
            ):
                raise SourceConflict("Only the confirming owner can complete a waiting UpdateID.")
            fields = {
                "kvk_no": "KVK_NO",
                "period_id": "PeriodID",
                "period_key": "PeriodKey",
                "choice_id": "ChoiceID",
                "config_version_id": "ConfigVersionID",
                "roster_id": "RosterID",
                "coverage_start_utc": "CoverageStartUTC",
                "coverage_end_utc": "CoverageEndUTC",
                "as_of_utc": "AsOfUTC",
                "update_kind": "UpdateKind",
                "request_id": "RequestID",
                "base_update_id": "BaseUpdateID",
            }
            for name, column in fields.items():
                actual = retained[column]
                if name.endswith("_utc"):
                    actual = actual.replace(tzinfo=UTC)
                if getattr(update, name) != actual:
                    raise SourceConflict("A waiting UpdateID cannot change its confirmed context.")
            original_proof = json.loads(retained["ConfirmationJson"])
            if any(
                original_proof.get(key) != proof.get(key)
                for key in ("action", "period_assignment", "counterpart", "configuration_review")
            ):
                raise SourceConflict("A waiting UpdateID cannot change its confirmed authority.")
            expected_end = retained.get("EndScanID") or original_proof.get(
                "pending_player", {}
            ).get("end_scan_id")
            if expected_end != end:
                raise SourceConflict("A waiting UpdateID cannot change its confirmed endpoint.")
            from dataclasses import replace

            update = replace(
                update,
                update_id=identity(update_id),
                confirmed_utc=retained["ConfirmedUTC"].replace(tzinfo=UTC),
                confirmation_json=retained["ConfirmationJson"],
            )
        return self._create(
            actor,
            season,
            "match_update",
            dict(
                context=json.loads(canonical(asdict(update))),
                guard=context,
                end_scan_id=end,
                aggregate_revision_id=aggregate_revision_id,
                counterpart_revision_id=(
                    identity(counterpart_revision_id) if counterpart_revision_id else None
                ),
                reason=reason,
            ),
        )

    def confirm(self, actor, review_id, version):
        row = self.read(actor, review_id)
        self.access.authorize(
            actor, "configure" if row["ReviewKind"] == "configuration" else row["ReviewKind"]
        )

        def operation(locked, cursor, connect):
            payload = locked["payload"]
            if locked["ReviewKind"] == "choose_source":
                if locked["KVK_NO"] not in SourceAdminReviewDAL(connect).seasons():
                    raise SourceConflict("The reviewed season is no longer configured.")
                choice = SeasonSourceService(connect).choose(
                    locked["KVK_NO"],
                    payload["source"],
                    actor=str(actor.user_id),
                    reason=payload["reason"],
                    provenance={"review_id": str(locked["ReviewID"])},
                    authorized=True,
                )
                return dict(
                    state="source fixed; intake setup",
                    choice_id=choice["ChoiceID"],
                    source=choice["SourceKey"],
                )
            if locked["ReviewKind"] != "match_update":
                if locked["ReviewKind"] == "configuration":
                    return self._confirm_configuration(actor, locked, cursor, connect)
                raise ValueError("Unsupported confirmation kind.")
            saved = payload["context"]
            current = SourceAdminReviewDAL(connect).match_context(
                locked["KVK_NO"],
                saved["period_key"],
                payload["end_scan_id"],
                payload["aggregate_revision_id"],
            )
            if current != payload["guard"]:
                raise SourceConflict(
                    "Pair context changed; review the current inputs and versions again."
                )
            values = dict(saved)
            for key in ("coverage_start_utc", "coverage_end_utc", "as_of_utc", "confirmed_utc"):
                values[key] = utc_text(values[key])
            context = UpdateContext(**values)
            service = SourceUpdateService(connect)
            update = service.create(context, authorized=True, admin_authorized=True)
            start, end = current["config"]["StartScanID"], payload["end_scan_id"]
            player = (
                PlayerRevisions(
                    start, end, current["scans"][str(start)], current["scans"][str(end)]
                )
                if str(end) in current["scans"]
                else None
            )
            report = current["aggregate"]
            aggregate = (
                AggregateRevision(report["ReportID"], report["RevisionID"]) if report else None
            )
            update = service.associate(
                update["UpdateID"],
                expected_version=update["Version"],
                player=player,
                aggregate=aggregate,
                counterpart_revision_id=payload["counterpart_revision_id"],
                authorized=True,
            )
            result = service.publish(update["UpdateID"])
            return dict(
                state="complete selected" if result else update["UpdateState"],
                update_id=context.update_id,
                selected_update_id=result.update_id if result else None,
                result=asdict(result) if result else None,
            )

        return self.repository.finish(
            review_id, actor, version, now=self.now(), operation=operation
        )

    def _confirm_configuration(self, actor, locked, cursor, connect):
        from kvk.services.new_source_config_service import request_configuration_update

        payload = locked["payload"]
        current = SourceAdminReviewDAL(connect).configuration_context(locked["KVK_NO"])
        if current != {key: payload[key] for key in ("snapshot", "periods", "season_version")}:
            raise SourceConflict(
                "Imported configuration or affected results changed; review again."
            )
        results = []
        for period in payload["periods"]:
            desired = period["desired_window"]
            request = request_configuration_update(
                cursor,
                authorized=True,
                review_id=str(locked["ReviewID"]),
                snapshot=payload["snapshot"],
                kvk_no=locked["KVK_NO"],
                period_id=period["period_id"],
                base_config_id=period["base_config_id"],
                new_start_scan_id=desired["StartScanID"],
                new_end_scan_id=desired["EndScanID"],
                actor=str(actor.user_id),
                reason=payload["reason"],
                requested_utc=self.now(),
                origin="admin",
                provenance={"configuration_review": str(locked["ReviewID"])},
            )
            results.append(
                dict(
                    period=period["period_key"],
                    request_id=request["RequestID"],
                    state="configuration pending; compatible counterpart required",
                )
            )
            base = period["base_update"]
            if not payload["attest_counterparts"] or not base or desired["StartScanID"] is None:
                continue
            # Explicit confirmation covers the displayed retained counterpart and proposed context.
            # Map/scope changes still require a compatible supplied report; numeric values are never made up.
            cursor.execute(
                "SELECT MappingDigest FROM KVK.SourceConfigVersion WHERE ConfigVersionID IN (?,?) ORDER BY ConfigVersion",
                period["base_config_id"],
                request["DesiredConfigVersionID"],
            )
            from kvk.dal.new_source_import_dal import rows

            mappings = rows(cursor)
            if len(mappings) != 2 or mappings[0]["MappingDigest"] != mappings[1]["MappingDigest"]:
                continue
            service = SourceAdminReviewService(self.access, SourceAdminReviewDAL(connect), self.now)
            end = desired["EndScanID"] or base["EndScanID"]
            review = service.prepare_match(
                actor,
                season=locked["KVK_NO"],
                period=period["period_key"],
                end_scan_id=end,
                coverage_start=base["CoverageStartUTC"],
                coverage_end=base["CoverageEndUTC"],
                as_of=base["AsOfUTC"],
                aggregate_revision_id=base["AggregateRevisionID"],
                counterpart_revision_id=base["AggregateRevisionID"],
                reason=payload["reason"],
                action="correct",
            )
            completed = service.confirm(actor, str(review["ReviewID"]), review["Version"])
            results[-1].update(completed["outcome"])
        return dict(
            state="configuration reviewed; previous results retained until complete replacement",
            periods=results,
        )

    @staticmethod
    def summary(row):
        payload = row["payload"]
        lines = [
            f"Review: {row['ReviewID']} | KVK {row['KVK_NO']} | version {row['Version']}",
            f"State: {row['ReviewState']}",
        ]
        if row["ReviewKind"] == "choose_source":
            lines.append(f"Fix season source: {payload['source']}. This choice cannot be switched.")
        if row["ReviewKind"] == "match_update":
            c = payload["context"]
            lines.extend(
                f"{key}: {c[key]}"
                for key in (
                    "update_id",
                    "period_key",
                    "config_version_id",
                    "roster_id",
                    "coverage_start_utc",
                    "coverage_end_utc",
                    "as_of_utc",
                    "base_update_id",
                )
            )
            lines.append(
                f"Player scans: {payload['guard']['config']['StartScanID']} to {payload['end_scan_id']}"
            )
            lines.append(
                f"Aggregate revision: {payload['aggregate_revision_id'] or 'waiting / not applicable'}"
            )
            lines.append(
                f"Counterpart validity attestation: {payload['counterpart_revision_id'] or 'none'}"
            )
        if row["ReviewKind"] == "configuration":
            lines.append(
                "Imported player DKP weights: " + " / ".join(payload["snapshot"]["weights"])
            )
            lines.append(payload["snapshot"]["weight_provenance"])
            lines.extend(
                f"Kingdom {k} -> camp {c}: {name}" for k, c, name in payload["snapshot"]["mapping"]
            )
            for period in payload["periods"]:
                old, new = period["old_window"], period["desired_window"]
                lines.append(
                    f"{period['period_key']}: {old['StartScanID']}–{old['EndScanID']} -> {new['StartScanID']}–{new['EndScanID']}"
                )
                lines.append("Previous player weights: " + " / ".join(period["old_weights"]))
                before = {k: (c, name) for k, c, name in period["old_mapping"]}
                after = {k: (c, name) for k, c, name in payload["snapshot"]["mapping"]}
                for kingdom in sorted(before.keys() | after.keys()):
                    if before.get(kingdom) != after.get(kingdom):
                        lines.append(
                            f"Kingdom {kingdom}: {before.get(kingdom, 'outside scope')} -> {after.get(kingdom, 'outside scope')}"
                        )
                if period["base_update"]:
                    base = period["base_update"]
                    lines.append(
                        f"Base UpdateID: {base['UpdateID']} | counterpart: {base['AggregateRevisionID']}"
                    )
                    lines.append(
                        f"Coverage/as-of: {base['CoverageStartUTC']} | {base['CoverageEndUTC']} | {base['AsOfUTC']}"
                    )
            lines.append(
                f"Explicit retained-counterpart validity attestation: {payload['attest_counterparts']}"
            )
            lines.append(
                "Kingdom/camp totals and DKP remain supplied authority; incompatible reports leave changes pending."
            )
        if row.get("outcome"):
            lines.extend(
                f"{key}: {value}"
                for key, value in row["outcome"].items()
                if key not in ("result", "periods")
            )
            for period in row["outcome"].get("periods", []):
                lines.append(f"{period['period']}: {period['state']}")
                for key in ("request_id", "update_id", "selected_update_id"):
                    if period.get(key):
                        lines.append(f"{key}: {period[key]}")
        lines.append(f"Reason: {payload.get('reason', '')}")
        return "\n".join(lines)
