"""Private source intake policy. Durable receipts are authoritative; views are disposable."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import json
import logging
from pathlib import Path
import re
from uuid import UUID

from kvk.dal.new_source_import_dal import Admission, SourceConflict, canonical
from kvk.models.new_source_observation import CampMapping, MetadataConfirmation, SourceScope
from kvk.models.new_source_reporting import FrozenWeights, require_utc
from kvk.schemas.new_source_schema import INT_MAX, ReportState, SourceKind, TimePrecision
from kvk.services.new_source_artifact_store import ArtifactStore, StoredArtifact
from kvk.services.new_source_metadata import parse_filename_metadata, validate_source_metadata
from kvk.services.new_source_parser import parse_aggregate_workbook, parse_player_workbook

logger = logging.getLogger(__name__)
ACTIONS = ("status", "resume", "accept", "finalize", "correct", "configure")
CONFIRM_SECONDS = 300


def utc_now():
    return datetime.now(UTC).replace(microsecond=0)


def utc_text(value):
    try:
        stamp = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        require_utc(stamp)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("Enter a whole-second UTC time, for example 2000-01-01T12:00Z.") from exc
    return stamp


def positive(value):
    if isinstance(value, bool) or not re.fullmatch(r"[1-9][0-9]{0,9}", str(value)):
        raise ValueError("A positive scan or KVK number is required.")
    number = int(value)
    if number > INT_MAX:
        raise ValueError("Number exceeds the source namespace.")
    return number


@dataclass(frozen=True)
class SourceActor:
    user_id: int
    guild_id: int
    channel_id: int
    role_ids: frozenset[int]


@dataclass(frozen=True)
class SourceAccess:
    enabled: bool
    guild_id: int
    channel_id: int
    admin_id: int
    uploader_roles: frozenset[int]
    admin_channels: frozenset[int]
    collision_channels: frozenset[int] = frozenset()

    def authorize(self, actor, action="accept", *, upload=False):
        if not self.enabled:
            raise PermissionError("KVK source intake is disabled.")
        if self.channel_id <= 0 or self.channel_id in self.collision_channels:
            raise PermissionError(
                "KVK source channel configuration is invalid or collides with another route."
            )
        if self.guild_id <= 0 or actor.guild_id != self.guild_id or actor.user_id <= 0:
            raise PermissionError("This source action requires the configured guild.")
        admin = self.admin_id > 0 and actor.user_id == self.admin_id
        channels = (
            {self.channel_id} if upload or not admin else {self.channel_id, *self.admin_channels}
        )
        if actor.channel_id not in channels:
            raise PermissionError("Use the private source intake or an authorized admin channel.")
        if action not in ACTIONS or (action in ("finalize", "correct", "configure") and not admin):
            raise PermissionError("This action requires the configured KVK administrator.")
        if not admin and not actor.role_ids.intersection(self.uploader_roles):
            raise PermissionError("The source uploader role is required.")
        return admin


def access_from_config():
    import bot_config as c

    collisions = frozenset(
        {
            *c.CHANNEL_IDS,
            c.PROKINGDOM_CHANNEL_ID,
            c.INVENTORY_UPLOAD_CHANNEL_ID,
            c.PLAYER_LOCATION_CHANNEL_ID,
            c.MGE_DATA_CHANNEL_ID,
            c.PREKVK_CHANNEL_ID,
            c.HONOR_CHANNEL_ID,
            c.ACTIVITY_UPLOAD_CHANNEL_ID,
            c.FORT_RALLY_CHANNEL_ID,
        }
    )
    return SourceAccess(
        c.KVK_SOURCE_INTAKE_ENABLED,
        c.GUILD_ID,
        c.KVK_SOURCE_CHANNEL_ID,
        c.ADMIN_USER_ID,
        frozenset(c.KVK_SOURCE_UPLOADER_ROLE_IDS),
        frozenset({c.NOTIFY_CHANNEL_ID}),
        collisions,
    )


def configured_service():
    """No SQL, credentials or artifact directory is required while disabled."""
    import bot_config as c
    from kvk.dal.new_source_admin_dal import SourceAdminDAL, configured_connection

    access = access_from_config()
    if not access.enabled:
        raise PermissionError("KVK source intake is disabled.")
    if not c.KVK_SOURCE_ARTIFACT_ROOT:
        raise PermissionError("Configure a private artifact root before using source intake.")
    store = ArtifactStore(Path(c.KVK_SOURCE_ARTIFACT_ROOT))
    return SourceAdminService(access, SourceAdminDAL(configured_connection, store), store)


def _wire(value):
    return json.loads(canonical(value))


class SourceAdminService:
    def __init__(self, access, repository, artifacts, now=utc_now):
        self.access, self.repository, self.artifacts, self.now = access, repository, artifacts, now

    def receipt(self, actor, receipt_id, action="status"):
        self.access.authorize(actor, action)
        key = str(UUID(str(receipt_id)))
        row = self.repository.read_receipt(key, str(actor.user_id), str(actor.guild_id))
        candidate = (
            row["payload"].get("proposal", {}).get("candidate", row["payload"].get("candidate", {}))
        )
        row["current_context"] = self.repository.context(row["KVK_NO"], candidate)
        return row

    def stage_upload(self, actor, *, filename, content, message_id, attachment_id, season=None):
        self.access.authorize(actor, upload=True)
        if not filename.lower().endswith(".xlsx"):
            raise ValueError("Source intake supports XLSX workbooks only.")
        candidate = parse_filename_metadata(filename)
        kvk_no = candidate.kvk_no or positive(season)
        if season is not None and positive(season) != kvk_no:
            raise ValueError("Caption KVK conflicts with the filename.")
        artifact = self.artifacts.persist_artifact(content)
        admission = Admission(
            str(actor.guild_id),
            str(message_id),
            str(attachment_id),
            "s5a_draft",
            str(actor.user_id),
            str(actor.channel_id),
            "Private upload receipt",
            self.now(),
        )
        return self.repository.create_receipt(
            artifact=artifact,
            admission=admission,
            filename=filename,
            kvk_no=kvk_no,
            payload={"version": 1, "candidate": _wire(asdict(candidate)), "history": []},
        )

    def _metadata(self, row, fields, actor, reason, *, saved_guard=None):
        candidate = parse_filename_metadata(row["OriginalFilename"])
        values = {
            "kvk_no": row["KVK_NO"],
            "kind": SourceKind(fields["kind"]),
            "scan_start_utc": utc_text(fields["scan_start"]),
            "time_precision": TimePrecision(fields.get("precision", "minute")),
            "period_key": fields["period"].strip() or None,
        }
        if values["kind"] == SourceKind.AGGREGATE:
            values.update(
                coverage_start_utc=utc_text(fields["coverage_start"]),
                coverage_end_utc=utc_text(fields["coverage_end"]),
                as_of_utc=utc_text(fields["as_of"]),
                report_state=ReportState(fields["state"]),
            )
        # Conflicts are shown to the owner for a second explicit confirmation, with reason.
        confirmation = MetadataConfirmation(
            tuple(values.items()), tuple(values), str(actor.user_id), self.now(), reason
        )
        kingdoms = tuple(sorted(positive(x.strip()) for x in fields["kingdoms"].split(",")))
        scope = SourceScope(
            row["KVK_NO"], kingdoms, (values["period_key"],) if values["period_key"] else ()
        )
        metadata = validate_source_metadata(candidate, confirmation, scope)
        guard = (
            saved_guard
            if saved_guard is not None
            else self.repository.context(row["KVK_NO"], _wire(asdict(metadata.candidate)))
        )
        mapping = CampMapping(
            tuple((r["Kingdom"], r["CampID"], r["CampName"]) for r in guard["mapping"])
        )
        if mapping.entries and tuple(k for k, _, _ in mapping.entries) != kingdoms:
            raise SourceConflict("Kingdom scope differs from the approved configuration.")
        if not mapping.entries and actor.user_id != self.access.admin_id:
            raise PermissionError("Initial source scope requires administrator approval.")
        return metadata, mapping, guard

    def _prepared(self, row, metadata, mapping):
        artifact = StoredArtifact(
            bytes(row["ArtifactHash"]).hex(), row["ByteCount"], row["StorageKey"]
        )
        content = self.artifacts.read(artifact)
        if metadata.candidate.kind == SourceKind.PLAYERS:
            prepared = parse_player_workbook(content, metadata)
        else:
            prepared = parse_aggregate_workbook(content, metadata, mapping)
        return prepared, artifact

    def prepare_metadata(
        self,
        actor,
        receipt_id,
        version,
        fields,
        *,
        action="accept",
        reason="",
        expected_revision=None,
        expected_revision_version=None,
    ):
        admin = self.access.authorize(actor, action)
        row = self.receipt(actor, receipt_id, action)
        if action not in ("accept", "finalize", "correct"):
            raise ValueError("Choose accept, finalize or correct for workbook metadata.")
        if not reason.strip() or len(reason) > 512:
            raise ValueError("A nonempty audit reason of at most 512 characters is required.")
        metadata, mapping, guard = self._metadata(row, fields, actor, reason)
        state = metadata.candidate.report_state
        if action == "accept" and state not in (None, ReportState.LIVE):
            raise PermissionError(
                "Use the administrator finalize or correct action for final reports."
            )
        if action == "finalize" and (
            metadata.candidate.kind != SourceKind.AGGREGATE or state != ReportState.FINAL
        ):
            raise ValueError(
                "Finalize selects an aggregate final; player finality uses exact configured endpoints."
            )
        if (
            action == "correct"
            and metadata.candidate.kind == SourceKind.AGGREGATE
            and state not in (ReportState.LIVE, ReportState.CORRECTED_FINAL)
        ):
            raise ValueError("A final source correction must be explicitly marked corrected_final.")
        selected = guard["revision"]
        if action == "correct" or (action == "finalize" and selected):
            if (
                not admin
                or not selected
                or (expected_revision, expected_revision_version)
                != (selected["SelectedRevisionID"], selected["SelectionVersion"])
            ):
                raise SourceConflict(
                    "Supply the current source revision and revision version for this action."
                )
        prepared, _ = self._prepared(row, metadata, mapping)
        if (
            metadata.candidate.kind == SourceKind.AGGREGATE
            and guard["config"]
            and guard["config"]["StartScanID"] == guard["config"]["EndScanID"]
        ):
            raise SourceConflict("Aggregate reports are not applicable to equal-endpoint windows.")
        count = (
            len(prepared.rows)
            if metadata.candidate.kind == SourceKind.PLAYERS
            else len(prepared.kingdom_rows) + len(prepared.camp_rows)
        )
        proposal = {
            "action": action,
            "fields": fields,
            "reason": reason,
            "candidate": _wire(asdict(metadata.candidate)),
            "guard": _wire(guard),
            "expected_revision": expected_revision,
            "expected_revision_version": expected_revision_version,
            "confirmed_at": self.now().isoformat(),
            "expires": (self.now() + timedelta(seconds=CONFIRM_SECONDS)).isoformat(),
            "count": count,
            "digest": prepared.digest.sha256,
        }
        return self.repository.prepare(
            receipt_id, str(actor.user_id), str(actor.guild_id), version, proposal
        )

    def prepare_configuration(
        self, actor, receipt_id, version, *, window, coverage, mapping, weights, reason
    ):
        self.access.authorize(actor, "configure")
        row = self.receipt(actor, receipt_id, "configure")
        b0_revision = row["ObservationRevisionID"] or (
            row["payload"].get("proposal", {}).get("b0_revision")
        )
        if not b0_revision:
            raise ValueError("Configuration requires this owner's accepted B0 player receipt.")
        if not reason.strip() or len(reason) > 512:
            raise ValueError("Configuration approval requires a bounded audit reason.")
        period, label, start, end = (x.strip() for x in window.split("|"))
        if (
            not re.fullmatch(r"overall|(?:fight|no_fight):[a-z][a-z0-9_-]{0,63}", period)
            or not 0 < len(label) <= 40
        ):
            raise ValueError("Enter a valid period key and a label of at most 40 characters.")
        start, end = positive(start), positive(end) if end else None
        if end is not None and end < start:
            raise ValueError("EndScanID must be greater than or equal to StartScanID.")
        if period.startswith("no_fight:") and start != end:
            raise ValueError("A no-fight window requires equal endpoints.")
        candidate = {"kind": "players", "period_key": period}
        guard = self.repository.context(row["KVK_NO"], candidate)
        spec = {"period_key": period, "label": label, "start": start, "end": end}
        if guard["config"]:
            if mapping.strip() or weights.strip() or coverage.strip():
                raise ValueError(
                    "Endpoint updates retain the approved map, weights and coverage; leave those fields empty."
                )
        else:
            begin, finish = (x.strip() for x in coverage.split("|"))
            begin, finish = utc_text(begin), utc_text(finish) if finish else None
            if finish and finish < begin:
                raise ValueError("Coverage end must not precede coverage start.")
            entries = []
            for line in mapping.splitlines():
                k, c, n = (x.strip() for x in line.split("|"))
                if not n or len(n) > 40 or not 1 <= positive(c) <= 8:
                    raise ValueError("Camp names must be bounded and IDs must be 1 through 8.")
                entries.append((positive(k), positive(c), n))
            if not entries or len({e[0] for e in entries}) != len(entries):
                raise ValueError("Provide exactly one map entry per kingdom.")
            camp_names = {}
            for _, camp, name in entries:
                key = " ".join(name.split()).casefold()
                if camp in camp_names and camp_names[camp] != key:
                    raise ValueError("Camp labels must agree across the map.")
                camp_names[camp] = key
            if len(set(camp_names.values())) != len(camp_names):
                raise ValueError("Camp labels must identify one camp each.")
            x, y, z, effective = (s.strip() for s in weights.split("|"))
            weight = FrozenWeights("pending approval", x, y, z, utc_text(effective))
            proposals = [row["payload"].get("proposal", {})] + [
                h.get("proposal") or {} for h in reversed(row["payload"].get("history", []))
            ]
            accepted = next((p for p in proposals if "fields" in p), {})
            scope = tuple(
                sorted(positive(x.strip()) for x in accepted["fields"]["kingdoms"].split(","))
            )
            if tuple(sorted(e[0] for e in entries)) != scope:
                raise ValueError("Configuration mapping must cover exactly the accepted B0 scope.")
            spec.update(
                mapping=sorted(entries),
                weights=[x, y, z, weight.effective_from_utc.isoformat()],
                coverage_start=begin.isoformat(),
                coverage_end=finish.isoformat() if finish else None,
            )
        proposal = {
            "action": "configure",
            "configuration": spec,
            "candidate": candidate,
            "guard": _wire(guard),
            "reason": reason,
            "receipt_id": receipt_id,
            "b0_revision": b0_revision,
            "expires": (self.now() + timedelta(seconds=CONFIRM_SECONDS)).isoformat(),
        }
        return self.repository.prepare(
            receipt_id, str(actor.user_id), str(actor.guild_id), version, proposal
        )

    def prepare_roster_correction(self, actor, receipt_id, version, *, reason, publication_plan):
        self.access.authorize(actor, "configure")
        row = self.receipt(actor, receipt_id, "configure")
        revision = row["ObservationRevisionID"] or row["payload"].get("proposal", {}).get(
            "b0_revision"
        )
        if not revision or not reason.strip() or len(reason) > 512:
            raise ValueError(
                "An accepted B0 correction receipt and bounded audit reason are required."
            )
        candidate = {"roster_revision": revision}
        guard = self.repository.context(row["KVK_NO"], candidate)
        if not any(guard["diff"].values()):
            raise SourceConflict(
                "The proposed roster has no membership or baseline-attribution change."
            )
        plan = {}
        for line in publication_plan.splitlines():
            if not line.strip():
                continue
            publication, decision = (part.strip() for part in line.split("|"))
            publication = str(UUID(publication))
            if publication in plan or decision != "retain":
                raise ValueError("Use each affected publication UUID once with | retain.")
            plan[publication] = decision
        if set(plan) != {p["PublicationID"] for p in guard["publications"]}:
            raise SourceConflict(
                "Review every listed publication and explicitly retain its current selection."
            )
        proposal = {
            "action": "configure",
            "mode": "roster",
            "candidate": candidate,
            "b0_revision": revision,
            "guard": _wire(guard),
            "reason": reason,
            "receipt_id": receipt_id,
            "publication_plan": plan,
            "expires": (self.now() + timedelta(seconds=CONFIRM_SECONDS)).isoformat(),
        }
        return self.repository.prepare(
            receipt_id, str(actor.user_id), str(actor.guild_id), version, proposal
        )

    def roster_preview(self, actor, receipt_id):
        self.access.authorize(actor, "configure")
        row = self.receipt(actor, receipt_id, "configure")
        revision = row["ObservationRevisionID"] or row["payload"].get("proposal", {}).get(
            "b0_revision"
        )
        if not revision:
            raise ValueError("Use your accepted correction of the original B0 observation.")
        row["roster_preview"] = self.repository.context(
            row["KVK_NO"], {"roster_revision": revision}
        )
        return row

    def confirm(self, actor, receipt_id, version):
        row = self.receipt(actor, receipt_id)
        proposal = row["payload"].get("proposal")
        if not proposal:
            raise ValueError("Prepare metadata before accepting the workbook.")
        admin = self.access.authorize(actor, proposal["action"])

        def operation(locked, importer, cursor):
            saved = locked["payload"]["proposal"]
            if self.now() >= utc_text(saved["expires"]):
                raise SourceConflict("Confirmation expired; resume and prepare it again.")
            if saved["action"] == "configure":
                if saved.get("mode") == "roster":
                    return self.repository.correct_roster(
                        cursor,
                        kvk_no=locked["KVK_NO"],
                        proposal=saved,
                        actor=str(actor.user_id),
                        reason=saved["reason"],
                        utc=self.now(),
                    )
                result = self.repository.onboard(
                    cursor,
                    kvk_no=locked["KVK_NO"],
                    proposal=saved,
                    b0_revision_id=saved["b0_revision"],
                    actor=str(actor.user_id),
                    reason=saved["reason"],
                    utc=self.now(),
                )
                return {**result, "observation_revision_id": saved["b0_revision"]}
            # Reparse the retained original on final action, never trust a view's prepared object.
            metadata, mapping, _ = self._metadata(
                locked, saved["fields"], actor, saved["reason"], saved_guard=saved["guard"]
            )
            prepared, artifact = self._prepared(locked, metadata, mapping)
            if prepared.digest.sha256 != saved["digest"]:
                raise SourceConflict("Prepared original changed; confirmation cannot proceed.")
            action_key = (
                "s5a_"
                + hashlib.sha256(f"{receipt_id}:{version}:{saved['action']}".encode()).hexdigest()[
                    :24
                ]
            )
            admission = Admission(
                locked["GuildID"],
                locked["MessageID"],
                locked["AttachmentID"],
                action_key,
                str(actor.user_id),
                locked["ChannelID"],
                saved["reason"],
                self.now(),
                admin_authorized=admin and saved["action"] != "accept",
                expected_revision_id=saved["expected_revision"],
                expected_version=saved["expected_revision_version"],
            )
            method = (
                importer.accept_observation
                if metadata.candidate.kind == SourceKind.PLAYERS
                else importer.accept_aggregate
            )
            accepted = method(prepared, artifact, admission)
            return {
                "state": "duplicate" if accepted.duplicate else "accepted; not published",
                "observation_revision_id": (
                    accepted.revision_id if metadata.candidate.kind == SourceKind.PLAYERS else None
                ),
                "aggregate_revision_id": (
                    accepted.revision_id
                    if metadata.candidate.kind == SourceKind.AGGREGATE
                    else None
                ),
                "scan_id": accepted.logical_scan_id,
                "selected": accepted.selected,
            }

        result = self.repository.confirm(
            receipt_id, str(actor.user_id), str(actor.guild_id), version, operation
        )
        logger.info(
            "KVK source action actor=%s receipt=%s action=%s utc=%s",
            actor.user_id,
            receipt_id,
            proposal["action"],
            self.now().isoformat(),
        )
        return result

    @staticmethod
    def summary(row):
        payload = row["payload"]
        proposal = payload.get("proposal", {})
        outcome = payload.get("outcome")
        lines = [
            f"Receipt: {row['AttemptID']}",
            f"KVK {row['KVK_NO']} | version {payload['version']}",
            f"State: {outcome['state'] if outcome else row['Status']}",
        ]
        candidate = proposal.get("candidate", payload.get("candidate", {}))
        for key in (
            "kind",
            "scan_start_utc",
            "time_precision",
            "period_key",
            "coverage_start_utc",
            "coverage_end_utc",
            "as_of_utc",
            "report_state",
        ):
            if candidate.get(key) is not None:
                lines.append(f"{key}: {candidate[key]}")
        if proposal.get("configuration"):
            spec = proposal["configuration"]
            lines.append(
                f"Window: {spec['period_key']} | {spec['start']} to {spec['end'] if spec['end'] is not None else 'pending'}"
            )
            if spec.get("mapping"):
                lines.append(
                    f"Approve frozen B0 and {len(spec['mapping'])} kingdom mappings; weights X/Y/Z: {' / '.join(spec['weights'][:3])}."
                )
                lines.extend(f"{k} -> camp {c}: {n}" for k, c, n in spec["mapping"])
                lines.append(
                    f"Coverage: {spec['coverage_start']} to {spec['coverage_end'] or 'open'}"
                )
        roster = row.get("roster_preview") or (
            proposal.get("guard") if proposal.get("mode") == "roster" else None
        )
        if roster:
            lines.append(
                f"Roster correction: version {roster['roster']['RosterVersion']} -> {roster['roster']['RosterVersion'] + 1}; {roster['member_count']} members"
            )
            lines.append(
                "Diff: "
                + ", ".join(f"{key}={len(values)}" for key, values in roster["diff"].items())
            )
            lines.append(
                "Review all affected publications; each remains pinned until a separate publication correction."
            )
            for publication in roster["publications"]:
                lines.append(
                    f"{publication['PublicationID']} | retain (selection {publication['SelectionVersion']}, {publication['PeriodState']})"
                )
            if not roster["publications"]:
                lines.append("No selected publications; leave the publication plan empty.")
        revision = row.get("current_context", proposal.get("guard", {})).get("revision")
        if revision:
            lines.append(
                f"Source revision: {revision['SelectedRevisionID']} | version {revision['SelectionVersion']}"
            )
        if proposal.get("count") is not None:
            lines.append(f"Validated rows: {proposal['count']}")
        if outcome:
            for key in (
                "observation_revision_id",
                "aggregate_revision_id",
                "scan_id",
                "config_id",
                "config_request_id",
                "roster_id",
                "roster_version",
            ):
                if outcome.get(key) is not None:
                    lines.append(f"{key}: {outcome[key]}")
        lines.append("Serving activation and delivery are separate. No public output is implied.")
        return "\n".join(lines)
