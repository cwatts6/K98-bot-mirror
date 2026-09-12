"""Durable S5A receipts and explicit onboarding over the accepted source schema.

Drafts use their own action key; immutable acceptance attempts keep S3B replay semantics.
No background worker, SQL deployment, serving activation or destination write lives here.
"""

from datetime import datetime
from decimal import Decimal
import json
from typing import Any
from uuid import uuid4

from kvk.dal.new_source_config_dal import snapshot_endpoint_request
from kvk.dal.new_source_import_dal import (
    SourceConflict,
    SourceImportDAL,
    canonical,
    digest,
    lock_scope,
    one,
    rows,
    transaction,
)
from kvk.schemas.new_source_schema import SOURCE_KEY

DRAFT_KEY = "s5a_draft"


def _json(value):
    text = canonical(value)
    if len(text.encode("utf-16-le")) > 65536:
        raise SourceConflict("Receipt history is full; retain it and start a new upload.")
    return text


class _BorrowedConnection:
    """Let S3B join our transaction; the outer context owns commit and rollback."""

    autocommit = False

    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def commit(self):
        return None

    def rollback(self):
        return None

    def close(self):
        return None


class SourceAdminDAL:
    def __init__(self, connect, artifacts):
        self.connect = connect
        self.artifacts = artifacts

    @staticmethod
    def _receipt(cursor, receipt_id, actor, guild_id) -> dict[str, Any]:
        cursor.execute(
            "SELECT d.*,a.ByteCount,a.StorageKey FROM KVK.SourceImportAttempt d "
            "WITH (UPDLOCK,HOLDLOCK) JOIN KVK.SourceArtifact a ON a.ArtifactHash=d.ArtifactHash "
            "WHERE d.AttemptID=? AND d.ActorID=? AND d.GuildID=? AND d.SourceKey=? AND d.ActionKey=?",
            receipt_id,
            actor,
            guild_id,
            SOURCE_KEY,
            DRAFT_KEY,
        )
        row: dict[str, Any] | None = one(cursor)
        if row is None:
            raise SourceConflict("Receipt unavailable for this owner and guild.")
        row["payload"] = json.loads(row["ProvenanceJson"])
        return row

    def read_receipt(self, receipt_id, actor, guild_id):
        with transaction(self.connect) as cursor:
            return self._receipt(cursor, receipt_id, actor, guild_id)

    def create_receipt(self, *, artifact, admission, filename, kvk_no, payload):
        with transaction(self.connect) as cursor:
            lock_scope(cursor, kvk_no)
            SourceImportDAL(self.connect, self.artifacts)._artifact(
                cursor, artifact, admission.received_utc.replace(tzinfo=None)
            )
            cursor.execute(
                "SELECT AttemptID,ActorID,ArtifactHash FROM KVK.SourceImportAttempt "
                "WITH (UPDLOCK,HOLDLOCK) WHERE GuildID=? AND MessageID=? AND AttachmentID=? AND ActionKey=?",
                admission.guild_id,
                admission.message_id,
                admission.attachment_id,
                DRAFT_KEY,
            )
            existing = one(cursor)
            if existing:
                if (
                    existing["ActorID"] != admission.actor
                    or bytes(existing["ArtifactHash"]).hex() != artifact.sha256
                ):
                    raise SourceConflict("Upload replay conflicts with its original receipt.")
                return self._receipt(
                    cursor, existing["AttemptID"], admission.actor, admission.guild_id
                )
            receipt_id = str(uuid4())
            cursor.execute(
                "INSERT KVK.SourceImportAttempt "
                "(AttemptID,SourceKey,KVK_NO,GuildID,MessageID,AttachmentID,ActionKey,ArtifactHash,"
                "ActorID,ChannelID,OriginalFilename,ReceivedUTC,Status,DiagnosticSummary,ProvenanceJson) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?, 'received','Awaiting metadata confirmation',?)",
                receipt_id,
                SOURCE_KEY,
                kvk_no,
                admission.guild_id,
                admission.message_id,
                admission.attachment_id,
                DRAFT_KEY,
                bytes.fromhex(artifact.sha256),
                admission.actor,
                admission.channel_id,
                filename,
                admission.received_utc.replace(tzinfo=None),
                _json(payload),
            )
            return self._receipt(cursor, receipt_id, admission.actor, admission.guild_id)

    @staticmethod
    def _version(row, expected_version):
        if row["payload"]["version"] != expected_version:
            raise SourceConflict(
                "Confirmation is stale; resume the receipt for its current version."
            )

    @staticmethod
    def _save(cursor, row, payload, status, observation=None, aggregate=None):
        cursor.execute(
            "UPDATE KVK.SourceImportAttempt SET ProvenanceJson=?,Status=?,DiagnosticSummary=?,"
            "ObservationRevisionID=?,AggregateRevisionID=? WHERE AttemptID=?",
            _json(payload),
            status,
            "S5A private receipt",
            observation,
            aggregate,
            row["AttemptID"],
        )

    def prepare(self, receipt_id, actor, guild_id, expected_version, proposal):
        with transaction(self.connect) as cursor:
            row = self._receipt(cursor, receipt_id, actor, guild_id)
            self._version(row, expected_version)
            payload = row["payload"]
            if payload.get("proposal") == proposal and row["Status"] == "validated":
                return row
            payload.setdefault("history", []).append(
                {
                    "version": payload["version"],
                    "status": row["Status"],
                    "proposal": payload.get("proposal"),
                    "outcome": payload.get("outcome"),
                }
            )
            payload.update(version=expected_version + 1, proposal=proposal)
            payload.pop("outcome", None)
            self._save(cursor, row, payload, "validated")
            return self._receipt(cursor, receipt_id, actor, guild_id)

    @staticmethod
    def _context(cursor, kvk_no, candidate) -> dict[str, Any]:
        """A receipt guard covers the selected revision, publication and desired config."""
        if candidate.get("roster_revision"):
            return SourceAdminDAL._roster_context(cursor, kvk_no, candidate["roster_revision"])
        period = candidate.get("period_key")
        cursor.execute(
            "SELECT PeriodID,PeriodKind,CoverageStartUTC,CoverageEndUTC FROM KVK.SourcePeriod "
            "WHERE SourceKey=? AND KVK_NO=? AND PeriodKey=?",
            SOURCE_KEY,
            kvk_no,
            period,
        )
        period_row = one(cursor)
        period_id = period_row["PeriodID"] if period_row else None
        cursor.execute(
            "SELECT s.SelectionVersion,s.PublicationID,p.ConfigVersionID FROM KVK.SourceSelection s "
            "JOIN KVK.SourcePublication p ON p.PublicationID=s.PublicationID "
            "WHERE s.SourceKey=? AND s.KVK_NO=? AND s.PeriodID=?",
            SOURCE_KEY,
            kvk_no,
            period_id,
        )
        selection = one(cursor)
        cursor.execute(
            "SELECT TOP (1) r.DesiredConfigVersionID FROM KVK.SourceConfigRequest r "
            "JOIN KVK.SourceConfigVersion c ON c.ConfigVersionID=r.DesiredConfigVersionID "
            "WHERE r.SourceKey=? AND r.KVK_NO=? AND r.PeriodID=? AND r.RequestState<>'rejected' "
            "ORDER BY c.ConfigVersion DESC",
            SOURCE_KEY,
            kvk_no,
            period_id,
        )
        request = one(cursor)
        cursor.execute(
            "SELECT TOP (1) c.ConfigVersionID,w.StartScanID,w.EndScanID FROM KVK.SourceConfigVersion c "
            "JOIN KVK.SourceWindowConfig w ON w.ConfigVersionID=c.ConfigVersionID "
            "WHERE c.SourceKey=? AND c.KVK_NO=? AND w.PeriodKey=? "
            "AND (? IS NULL OR c.ConfigVersionID=?) ORDER BY c.ConfigVersion DESC",
            SOURCE_KEY,
            kvk_no,
            period,
            (request or {}).get("DesiredConfigVersionID")
            or (selection or {}).get("ConfigVersionID"),
            (request or {}).get("DesiredConfigVersionID")
            or (selection or {}).get("ConfigVersionID"),
        )
        config = one(cursor)
        cursor.execute(
            "SELECT Kingdom,CampID,CampName FROM KVK.SourceCampConfig WHERE ConfigVersionID=? ORDER BY Kingdom",
            config["ConfigVersionID"] if config else None,
        )
        mapping = rows(cursor)
        if candidate.get("kind") == "players":
            stamp = candidate.get("scan_start_utc")
            stamp = datetime.fromisoformat(stamp).replace(tzinfo=None) if stamp else None
            cursor.execute(
                "SELECT SelectedRevisionID,SelectionVersion FROM KVK.SourceObservation "
                "WHERE SourceKey=? AND KVK_NO=? AND ScanStartUTC=? AND TimePrecision=? AND EventDiscriminator=?",
                SOURCE_KEY,
                kvk_no,
                stamp,
                candidate.get("time_precision"),
                candidate.get("event_discriminator", "main"),
            )
        else:
            cursor.execute(
                "SELECT SelectedRevisionID,SelectionVersion FROM KVK.SourceAggregateReport "
                "WHERE SourceKey=? AND KVK_NO=? AND PeriodKey=?",
                SOURCE_KEY,
                kvk_no,
                period,
            )
        revision = one(cursor)
        return {
            "period": period_row,
            "selection": selection,
            "config": config,
            "mapping": mapping,
            "revision": revision,
        }

    def context(self, kvk_no, candidate):
        with transaction(self.connect) as cursor:
            lock_scope(cursor, kvk_no)
            return self._context(cursor, kvk_no, candidate)

    def confirm(self, receipt_id, actor, guild_id, expected_version, operation):
        """Receipt and S3B acceptance share one transaction, including uncertain commit."""
        # Obtain season first without holding a draft lock ahead of the season mutex.
        initial = self.read_receipt(receipt_id, actor, guild_id)
        with transaction(self.connect) as cursor:
            lock_scope(cursor, initial["KVK_NO"])
            row = self._receipt(cursor, receipt_id, actor, guild_id)
            self._version(row, expected_version)
            if row["payload"].get("outcome"):
                return row
            if row["Status"] != "validated":
                raise SourceConflict("Prepare and review this receipt before confirmation.")
            proposal = row["payload"]["proposal"]
            current = self._context(cursor, row["KVK_NO"], proposal["candidate"])
            if canonical(current) != canonical(proposal["guard"]):
                raise SourceConflict("Source selection or configuration changed; prepare again.")
            outcome = operation(
                row, SourceImportDAL(lambda: _BorrowedConnection(cursor), self.artifacts), cursor
            )
            payload = row["payload"]
            payload["outcome"] = outcome
            # Config operations retain the original accepted revision as their receipt result.
            self._save(
                cursor,
                row,
                payload,
                "accepted",
                outcome.get("observation_revision_id"),
                outcome.get("aggregate_revision_id"),
            )
            return self._receipt(cursor, receipt_id, actor, guild_id)

    def onboard(self, cursor, *, kvk_no, proposal, b0_revision_id, actor, reason, utc):
        """Initial period/config onboarding; never changes an existing roster or selection."""
        spec = proposal["configuration"]
        if proposal["guard"]["config"]:
            base = proposal["guard"]["config"]["ConfigVersionID"]
            request = snapshot_endpoint_request(
                cursor,
                kvk_no=kvk_no,
                period_id=proposal["guard"]["period"]["PeriodID"],
                base_config_id=base,
                new_start_scan_id=spec["start"],
                new_end_scan_id=spec["end"],
                actor=actor,
                reason=reason,
                requested_utc=utc,
                origin="admin",
                provenance={"receipt": proposal["receipt_id"], "approved_action": "configure"},
            )
            return {
                "config_request_id": request["RequestID"] if request else None,
                "state": "configuration pending" if request else "configuration unchanged",
            }
        cursor.execute(
            "SELECT r.*,s.GovernorID,s.b0_kingdom,s.b0_power FROM KVK.SourceRoster r "
            "JOIN KVK.SourceRosterMember s ON s.RosterID=r.RosterID "
            "WHERE r.SourceKey=? AND r.KVK_NO=? ORDER BY r.RosterVersion DESC,s.GovernorID",
            SOURCE_KEY,
            kvk_no,
        )
        retained = rows(cursor)
        if retained and retained[0]["B0RevisionID"] != b0_revision_id:
            raise SourceConflict(
                "B0 is frozen; roster replacement requires a separately reviewed correction."
            )
        if retained:
            cursor.execute(
                "SELECT TOP (1) c.ConfigVersionID,w.WeightT4X,w.WeightT5Y,w.WeightDeadsZ,w.EffectiveFromUTC "
                "FROM KVK.SourceConfigVersion c JOIN KVK.SourceWeightConfig w "
                "ON w.ConfigVersionID=c.ConfigVersionID WHERE c.SourceKey=? AND c.KVK_NO=? "
                "ORDER BY c.ConfigVersion DESC",
                SOURCE_KEY,
                kvk_no,
            )
            frozen = one(cursor)
            if frozen:
                cursor.execute(
                    "SELECT Kingdom,CampID,CampName FROM KVK.SourceCampConfig "
                    "WHERE ConfigVersionID=? ORDER BY Kingdom",
                    frozen["ConfigVersionID"],
                )
                frozen_map = [(m["Kingdom"], m["CampID"], m["CampName"]) for m in rows(cursor)]
                frozen_weights = [frozen[k] for k in ("WeightT4X", "WeightT5Y", "WeightDeadsZ")]
                if (
                    frozen_map != [tuple(entry) for entry in spec["mapping"]]
                    or frozen_weights != [Decimal(value) for value in spec["weights"][:3]]
                    or frozen["EffectiveFromUTC"]
                    != datetime.fromisoformat(spec["weights"][3]).replace(tzinfo=None)
                ):
                    raise SourceConflict(
                        "A new period must retain the season's approved map and weights."
                    )
        prior_period = proposal["guard"].get("period")
        if prior_period:
            supplied_start = datetime.fromisoformat(spec["coverage_start"]).replace(tzinfo=None)
            supplied_end = (
                datetime.fromisoformat(spec["coverage_end"]).replace(tzinfo=None)
                if spec["coverage_end"]
                else None
            )
            if (
                prior_period["CoverageStartUTC"] != supplied_start
                or prior_period["CoverageEndUTC"] != supplied_end
            ):
                raise SourceConflict("Existing period coverage is immutable.")
        cursor.execute(
            "SELECT p.GovernorID,p.kingdom,p.power FROM KVK.SourcePlayerSnapshot p "
            "JOIN KVK.SourceObservationRevision r ON r.RevisionID=p.RevisionID "
            "WHERE p.SourceKey=? AND p.KVK_NO=? AND p.RevisionID=? ORDER BY p.GovernorID",
            SOURCE_KEY,
            kvk_no,
            b0_revision_id,
        )
        members = rows(cursor)
        if not members or any(
            m["kingdom"] not in {entry[0] for entry in spec["mapping"]} for m in members
        ):
            raise SourceConflict("B0 membership does not match the approved kingdom scope.")
        now = utc.replace(tzinfo=None)
        roster_id = retained[0]["RosterID"] if retained else str(uuid4())
        provenance = _json({"receipt": proposal["receipt_id"], "action": "configure"})
        if not retained:
            cursor.execute(
                "INSERT KVK.SourceRoster (RosterID,SourceKey,KVK_NO,RosterVersion,B0RevisionID,"
                "ScopeDigest,MemberDigest,MemberCount,ApprovedUTC,ApprovedBy,Reason,ProvenanceJson) "
                "VALUES (?,?,?,1,?,?,?,?,?,?,?,?)",
                roster_id,
                SOURCE_KEY,
                kvk_no,
                b0_revision_id,
                digest(spec["mapping"]),
                digest(members),
                len(members),
                now,
                actor,
                reason,
                provenance,
            )
            for member in members:
                cursor.execute(
                    "INSERT KVK.SourceRosterMember (RosterID,SourceKey,KVK_NO,GovernorID,b0_kingdom,b0_power) VALUES (?,?,?,?,?,?)",
                    roster_id,
                    SOURCE_KEY,
                    kvk_no,
                    member["GovernorID"],
                    member["kingdom"],
                    member["power"],
                )
        if proposal["guard"]["period"]:
            period_id = proposal["guard"]["period"]["PeriodID"]
        else:
            period_id = str(uuid4())
            cursor.execute(
                "INSERT KVK.SourcePeriod (PeriodID,SourceKey,KVK_NO,PeriodKey,PeriodKind,CoverageStartUTC,CoverageEndUTC,CreatedUTC) VALUES (?,?,?,?,?,?,?,?)",
                period_id,
                SOURCE_KEY,
                kvk_no,
                spec["period_key"],
                spec["period_key"].split(":")[0],
                datetime.fromisoformat(spec["coverage_start"]).replace(tzinfo=None),
                (
                    datetime.fromisoformat(spec["coverage_end"]).replace(tzinfo=None)
                    if spec["coverage_end"]
                    else None
                ),
                now,
            )
        cursor.execute(
            "SELECT ISNULL(MAX(ConfigVersion),0)+1 AS n FROM KVK.SourceConfigVersion WHERE SourceKey=? AND KVK_NO=?",
            SOURCE_KEY,
            kvk_no,
        )
        version_row = one(cursor)
        if version_row is None:
            raise SourceConflict("Configuration version allocation failed.")
        number = version_row["n"]
        config_id = str(uuid4())
        cursor.execute(
            "INSERT KVK.SourceConfigVersion (ConfigVersionID,SourceKey,KVK_NO,ConfigVersion,RosterID,ConfigContentHash,WindowDigest,MappingDigest,WeightDigest,ApprovedUTC,ApprovedBy,Reason,ProvenanceJson) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            config_id,
            SOURCE_KEY,
            kvk_no,
            number,
            roster_id,
            digest(spec),
            digest((spec["start"], spec["end"])),
            digest({"entries": spec["mapping"]}),
            digest(spec["weights"]),
            now,
            actor,
            reason,
            provenance,
        )
        cursor.execute(
            "INSERT KVK.SourceWindowConfig (ConfigVersionID,SourceKey,KVK_NO,WindowName,WindowSeq,StartScanID,EndScanID,UpdatedAtUTC,PeriodKey) VALUES (?,?,?,?,1,?,?,?,?)",
            config_id,
            SOURCE_KEY,
            kvk_no,
            spec["label"],
            spec["start"],
            spec["end"],
            now,
            spec["period_key"],
        )
        for kingdom, camp, name in spec["mapping"]:
            cursor.execute(
                "INSERT KVK.SourceCampConfig (ConfigVersionID,SourceKey,KVK_NO,Kingdom,CampID,CampName,CampKey) VALUES (?,?,?,?,?,?,?)",
                config_id,
                SOURCE_KEY,
                kvk_no,
                kingdom,
                camp,
                name,
                " ".join(name.split()).casefold(),
            )
        x, y, z, effective = spec["weights"]
        cursor.execute(
            "INSERT KVK.SourceWeightConfig (ConfigVersionID,SourceKey,KVK_NO,WeightT4X,WeightT5Y,WeightDeadsZ,WeightT4XSource,WeightT5YSource,WeightDeadsZSource,EffectiveFromUTC) VALUES (?,?,?,?,?,?,?,?,?,?)",
            config_id,
            SOURCE_KEY,
            kvk_no,
            Decimal(x),
            Decimal(y),
            Decimal(z),
            x,
            y,
            z,
            datetime.fromisoformat(effective).replace(tzinfo=None),
        )
        cursor.execute(
            "INSERT KVK.SourceScanBinding (ConfigVersionID,SourceKey,KVK_NO,LogicalScanID) "
            "SELECT ?,SourceKey,KVK_NO,LogicalScanID FROM KVK.SourceLogicalScan WHERE SourceKey=? AND KVK_NO=?",
            config_id,
            SOURCE_KEY,
            kvk_no,
        )
        cursor.execute("SELECT KVK_NO FROM KVK.SourceRouting WHERE KVK_NO=?", kvk_no)
        if not one(cursor):
            cursor.execute(
                "INSERT KVK.SourceRouting (SourceKey,KVK_NO,Enabled,RoutingVersion) VALUES (?,?,0,1)",
                SOURCE_KEY,
                kvk_no,
            )
        return {
            "config_id": config_id,
            "period_id": period_id,
            "state": "configuration approved; not published",
        }

    @staticmethod
    def _roster_context(cursor, kvk_no, revision_id):
        cursor.execute(
            "SELECT TOP (1) r.RosterID,r.RosterVersion,r.B0RevisionID,b.ObservationID "
            "FROM KVK.SourceRoster r JOIN KVK.SourceObservationRevision b ON b.RevisionID=r.B0RevisionID "
            "WHERE r.SourceKey=? AND r.KVK_NO=? ORDER BY r.RosterVersion DESC",
            SOURCE_KEY,
            kvk_no,
        )
        roster = one(cursor)
        if not roster:
            raise SourceConflict("Approve the initial B0 roster before a roster correction.")
        cursor.execute(
            "SELECT r.ObservationID,o.SelectedRevisionID FROM KVK.SourceObservationRevision r "
            "JOIN KVK.SourceObservation o ON o.ObservationID=r.ObservationID "
            "WHERE r.SourceKey=? AND r.KVK_NO=? AND r.RevisionID=?",
            SOURCE_KEY,
            kvk_no,
            revision_id,
        )
        revision = one(cursor)
        if (
            not revision
            or revision["ObservationID"] != roster["ObservationID"]
            or revision["SelectedRevisionID"] != revision_id
        ):
            raise SourceConflict(
                "Roster correction requires the selected correction of the original B0 observation."
            )
        cursor.execute(
            "SELECT GovernorID,b0_kingdom AS kingdom,b0_power AS power FROM KVK.SourceRosterMember "
            "WHERE RosterID=? ORDER BY GovernorID",
            roster["RosterID"],
        )
        old = rows(cursor)
        cursor.execute(
            "SELECT GovernorID,kingdom,power FROM KVK.SourcePlayerSnapshot "
            "WHERE SourceKey=? AND KVK_NO=? AND RevisionID=? ORDER BY GovernorID",
            SOURCE_KEY,
            kvk_no,
            revision_id,
        )
        new = rows(cursor)
        if not new or {r["kingdom"] for r in new} - {r["kingdom"] for r in old}:
            raise SourceConflict("Roster correction must retain the approved B0 kingdom scope.")
        before, after = ({r["GovernorID"]: r for r in group} for group in (old, new))
        difference = {
            "added": sorted(after.keys() - before.keys()),
            "removed": sorted(before.keys() - after.keys()),
            "changed": [
                key for key in sorted(before.keys() & after.keys()) if before[key] != after[key]
            ],
        }
        cursor.execute(
            "SELECT s.PeriodID,s.PublicationID,s.SelectionVersion,p.RosterID,p.PlayerState,p.PeriodState "
            "FROM KVK.SourceSelection s JOIN KVK.SourcePublication p ON p.PublicationID=s.PublicationID "
            "WHERE s.SourceKey=? AND s.KVK_NO=? ORDER BY s.PeriodID",
            SOURCE_KEY,
            kvk_no,
        )
        return {
            "roster": roster,
            "candidate_revision": revision_id,
            "member_digest": digest(new).hex(),
            "member_count": len(new),
            "diff": difference,
            "publications": rows(cursor),
        }

    def correct_roster(self, cursor, *, kvk_no, proposal, actor, reason, utc):
        """Append a reviewed roster version; never rewrite configs or historical selections."""
        guard = proposal["guard"]
        cursor.execute(
            "SELECT GovernorID,kingdom,power FROM KVK.SourcePlayerSnapshot "
            "WHERE SourceKey=? AND KVK_NO=? AND RevisionID=? ORDER BY GovernorID",
            SOURCE_KEY,
            kvk_no,
            proposal["b0_revision"],
        )
        members = rows(cursor)
        if digest(members).hex() != guard["member_digest"]:
            raise SourceConflict("Reviewed roster input changed.")
        roster_id = str(uuid4())
        cursor.execute(
            "INSERT KVK.SourceRoster (RosterID,SourceKey,KVK_NO,RosterVersion,B0RevisionID,ScopeDigest,"
            "MemberDigest,MemberCount,ApprovedUTC,ApprovedBy,Reason,ProvenanceJson) "
            "SELECT ?,SourceKey,KVK_NO,RosterVersion+1,?,ScopeDigest,?,?,?,?,?,? "
            "FROM KVK.SourceRoster WHERE RosterID=?",
            roster_id,
            proposal["b0_revision"],
            bytes.fromhex(guard["member_digest"]),
            len(members),
            utc.replace(tzinfo=None),
            actor,
            reason,
            _json(
                {
                    "receipt": proposal["receipt_id"],
                    "prior_roster": guard["roster"]["RosterID"],
                    "diff": guard["diff"],
                    "publication_plan": proposal["publication_plan"],
                }
            ),
            guard["roster"]["RosterID"],
        )
        for member in members:
            cursor.execute(
                "INSERT KVK.SourceRosterMember (RosterID,SourceKey,KVK_NO,GovernorID,b0_kingdom,b0_power) VALUES (?,?,?,?,?,?)",
                roster_id,
                SOURCE_KEY,
                kvk_no,
                member["GovernorID"],
                member["kingdom"],
                member["power"],
            )
        return {
            "roster_id": roster_id,
            "roster_version": guard["roster"]["RosterVersion"] + 1,
            "state": "roster correction approved; existing publications retained",
            "observation_revision_id": proposal["b0_revision"],
        }


def configured_connection():
    """Lazy dedicated connection; called only by explicitly enabled private controls."""
    from file_utils import get_conn_with_retries

    connection = get_conn_with_retries()
    connection.autocommit = False
    return connection
