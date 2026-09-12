"""Transactional source admission. Connections are injected; writes are never replayed."""

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
import hashlib
import json
import logging
from uuid import uuid4

from kvk.models.new_source_reporting import require_utc
from kvk.schemas.new_source_schema import INT_MAX, PLAYER_HEADERS, SOURCE_KEY
from kvk.services.new_source_artifact_store import ArtifactStore, StoredArtifact
from kvk.services.new_source_parser import parse_aggregate_workbook, parse_player_workbook

logger = logging.getLogger(__name__)


class SourceConflict(ValueError):
    """A stale, conflicting or unauthorized transition; safe to show without row data."""


class UncertainCommit(RuntimeError):
    """Read the durable operation identity before deciding whether to retry."""


def canonical(value) -> str:
    def convert(item):
        if isinstance(item, (datetime, Decimal)):
            return item.isoformat() if isinstance(item, datetime) else str(item)
        raise TypeError("Unsupported source serialization value.")

    return json.dumps(value, default=convert, sort_keys=True, separators=(",", ":"))


def digest(value) -> bytes:
    return hashlib.sha256(canonical(value).encode("utf-8")).digest()


UUID_COLUMNS = frozenset(
    (
        "AttemptID",
        "ObservationID",
        "RevisionID",
        "SelectedRevisionID",
        "SupersedesObservationID",
        "SupersedesRevisionID",
        "ObservationRevisionID",
        "AggregateRevisionID",
        "ReportID",
        "AggregateReportID",
        "ConfigVersionID",
        "BaseConfigVersionID",
        "DesiredConfigVersionID",
        "RosterID",
        "B0RevisionID",
        "PeriodID",
        "DisplayPeriodID",
        "PublicationID",
        "OldPublicationID",
        "NewPublicationID",
        "AppliedPublicationID",
        "RequestID",
        "ActionID",
        "StartRevisionID",
        "EndRevisionID",
        "OwnerID",
    )
)


def mapped(names, row):
    return {
        name: str(value).lower() if value is not None and name in UUID_COLUMNS else value
        for name, value in zip(names, row, strict=True)
    }


def one(cursor):
    row = cursor.fetchone()
    return None if row is None else mapped((c[0] for c in cursor.description), row)


def rows(cursor):
    names = tuple(c[0] for c in cursor.description)
    return [mapped(names, row) for row in cursor.fetchall()]


@contextmanager
def transaction(connect):
    connection = connect()
    try:
        if connection.autocommit:
            raise ValueError("Source operations require a dedicated transactional connection.")
        cursor = connection.cursor()
        cursor.execute("SET XACT_ABORT ON; SET NOCOUNT ON;")
        try:
            yield cursor
        except BaseException:
            connection.rollback()
            raise
        try:
            connection.commit()
        except Exception as exc:
            # Do not replay, or claim rollback when COMMIT may have succeeded.
            raise UncertainCommit("Read the durable operation before retrying.") from exc
    finally:
        connection.close()


def lock_scope(cursor, kvk_no: int):
    if type(kvk_no) is not int or not 1 <= kvk_no <= INT_MAX:
        raise ValueError("Invalid source season.")
    cursor.execute(
        "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?, "
        "@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=10000; "
        "IF @r<0 THROW 51400,'Source transaction lock unavailable',1;",
        f"kvk-source:{SOURCE_KEY}:{kvk_no}",
    )


@dataclass(frozen=True, slots=True)
class Admission:
    guild_id: str
    message_id: str
    attachment_id: str
    action_key: str
    actor: str
    channel_id: str
    reason: str
    received_utc: datetime
    admin_authorized: bool = False
    expected_revision_id: str | None = None
    expected_version: int | None = None

    def __post_init__(self):
        require_utc(self.received_utc)
        for value, limit in (
            (self.guild_id, 32),
            (self.message_id, 32),
            (self.attachment_id, 32),
            (self.action_key, 32),
            (self.actor, 128),
            (self.channel_id, 32),
            (self.reason, 1024),
        ):
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ValueError("Bounded admission identity and reason required.")

    @property
    def replay_key(self):
        return self.guild_id, self.message_id, self.attachment_id, self.action_key


@dataclass(frozen=True, slots=True)
class Acceptance:
    revision_id: str
    identity_id: str
    logical_scan_id: int | None
    duplicate: bool
    selected: bool


PLAYER_COLUMNS = tuple(
    (header, header.lower().replace(" ", "_"))
    for header in PLAYER_HEADERS
    if header not in ("Governor ID", "Kingdom")
)
AGGREGATE_COLUMNS = (
    ("T4 Kills", "t4_kills"),
    ("T5 Kills", "t5_kills"),
    ("KP (T4+T5)", "kp_t4_t5"),
    ("Dead", "dead"),
    ("T4+T5DEAD", "t4_t5_dead"),
    ("Healed", "healed"),
    ("Acclaim", "acclaim"),
    ("DKP", "dkp"),
)


class SourceImportDAL:
    def __init__(self, connect, artifact_store: ArtifactStore):
        self.connect = connect
        self.artifacts = artifact_store

    def _artifact(self, cursor, artifact: StoredArtifact, utc):
        cursor.execute(
            "SELECT ByteCount,StorageKey FROM KVK.SourceArtifact WITH (UPDLOCK,HOLDLOCK) WHERE ArtifactHash=?",
            bytes.fromhex(artifact.sha256),
        )
        existing = one(cursor)
        if existing:
            if (existing["ByteCount"], existing["StorageKey"]) != (
                artifact.byte_count,
                artifact.storage_key,
            ):
                raise SourceConflict("Artifact registry integrity conflict.")
        else:
            cursor.execute(
                "INSERT KVK.SourceArtifact (ArtifactHash,ByteCount,StorageKey,CreatedUTC) VALUES (?,?,?,?)",
                bytes.fromhex(artifact.sha256),
                artifact.byte_count,
                artifact.storage_key,
                utc,
            )

    def read_outcome(self, admission: Admission):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT * FROM KVK.SourceImportAttempt WHERE GuildID=? AND MessageID=? AND AttachmentID=? AND ActionKey=?",
                *admission.replay_key,
            )
            return one(cursor)

    def _replay(self, cursor, prepared, artifact, admission, aggregate):
        cursor.execute(
            "SELECT * FROM KVK.SourceImportAttempt WITH (UPDLOCK,HOLDLOCK) WHERE GuildID=? AND MessageID=? AND AttachmentID=? AND ActionKey=?",
            *admission.replay_key,
        )
        attempt = one(cursor)
        if not attempt:
            return None
        if (
            attempt["SourceKey"],
            attempt["KVK_NO"],
            bytes(attempt["ArtifactHash"]),
            attempt["ActorID"],
        ) != (
            SOURCE_KEY,
            prepared.metadata.candidate.kvk_no,
            bytes.fromhex(artifact.sha256),
            admission.actor,
        ):
            raise SourceConflict("Replay identity has different content or scope.")
        revision = attempt["AggregateRevisionID" if aggregate else "ObservationRevisionID"]
        if not revision:
            raise SourceConflict("Replay has no matching accepted outcome.")
        return str(revision)

    def _attempt(self, cursor, prepared, artifact, admission, revision, duplicate, aggregate):
        c = prepared.metadata.candidate
        cursor.execute(
            "INSERT KVK.SourceImportAttempt (AttemptID,SourceKey,KVK_NO,GuildID,MessageID,AttachmentID,ActionKey,ArtifactHash,ActorID,ChannelID,OriginalFilename,ReceivedUTC,Status,DiagnosticSummary,ObservationRevisionID,AggregateRevisionID,ProvenanceJson) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            str(uuid4()),
            SOURCE_KEY,
            c.kvk_no,
            *admission.replay_key,
            bytes.fromhex(artifact.sha256),
            admission.actor,
            admission.channel_id,
            c.original_filename,
            admission.received_utc.replace(tzinfo=None),
            "duplicate" if duplicate else "accepted",
            "source acceptance",
            None if aggregate else revision,
            revision if aggregate else None,
            canonical(asdict(admission)),
        )

    @staticmethod
    def _correction(admission, selected, version):
        if (
            not admission.admin_authorized
            or admission.expected_revision_id != str(selected)
            or admission.expected_version != version
        ):
            raise SourceConflict("Correction requires authorized exact revision and version.")

    def accept_observation(self, prepared, artifact: StoredArtifact, admission: Admission):
        # Reparse original bytes before SQL references them; forged prepared objects fail closed.
        verified = parse_player_workbook(self.artifacts.read(artifact), prepared.metadata)
        if verified != prepared:
            raise SourceConflict("Prepared observation does not match original.")
        c = prepared.metadata.candidate
        utc = admission.received_utc.replace(tzinfo=None)
        with transaction(self.connect) as cursor:
            lock_scope(cursor, c.kvk_no)
            self._artifact(cursor, artifact, utc)
            replay = self._replay(cursor, prepared, artifact, admission, False)
            cursor.execute(
                "SELECT * FROM KVK.SourceObservation WITH (UPDLOCK,HOLDLOCK) WHERE SourceKey=? AND KVK_NO=? AND ScanStartUTC=? AND TimePrecision=? AND EventDiscriminator=?",
                SOURCE_KEY,
                c.kvk_no,
                c.scan_start_utc.replace(tzinfo=None),
                c.time_precision.value,
                c.event_discriminator,
            )
            observation = one(cursor)
            if replay:
                if not observation:
                    raise SourceConflict("Replay event metadata differs.")
                cursor.execute(
                    "SELECT ObservationID FROM KVK.SourceObservationRevision WHERE RevisionID=?",
                    replay,
                )
                if str(one(cursor)["ObservationID"]) != str(observation["ObservationID"]):
                    raise SourceConflict("Replay event metadata differs.")
            duplicate = None
            if observation:
                cursor.execute(
                    "SELECT RevisionID FROM KVK.SourceObservationRevision WHERE ObservationID=? AND DigestVersion=? AND SchemaVersion=? AND SemanticHash=?",
                    observation["ObservationID"],
                    prepared.digest.canonical_version,
                    prepared.schema_version,
                    bytes.fromhex(prepared.digest.sha256),
                )
                duplicate = one(cursor)
                if replay and (not duplicate or str(duplicate["RevisionID"]) != replay):
                    raise SourceConflict("Replay semantic content differs.")
            if duplicate:
                revision = str(duplicate["RevisionID"])
                identity = str(observation["ObservationID"])
                cursor.execute(
                    "SELECT LogicalScanID FROM KVK.SourceLogicalScan WHERE SourceKey=? AND KVK_NO=? AND ObservationID=?",
                    SOURCE_KEY,
                    c.kvk_no,
                    identity,
                )
                scan = one(cursor)["LogicalScanID"]
                if not replay:
                    self._attempt(cursor, prepared, artifact, admission, revision, True, False)
                result = Acceptance(
                    revision,
                    identity,
                    scan,
                    True,
                    revision == str(observation["SelectedRevisionID"]),
                )
            else:
                if observation:
                    self._correction(
                        admission,
                        observation["SelectedRevisionID"],
                        observation["SelectionVersion"],
                    )
                    identity = str(observation["ObservationID"])
                    cursor.execute(
                        "SELECT MAX(RevisionNo) AS n FROM KVK.SourceObservationRevision WHERE ObservationID=?",
                        identity,
                    )
                    number = one(cursor)["n"] + 1
                    cursor.execute(
                        "SELECT LogicalScanID FROM KVK.SourceLogicalScan WHERE SourceKey=? AND KVK_NO=? AND ObservationID=?",
                        SOURCE_KEY,
                        c.kvk_no,
                        identity,
                    )
                    scan = one(cursor)["LogicalScanID"]
                else:
                    # A reused original cannot silently manufacture a new calendar event.
                    cursor.execute(
                        "SELECT TOP (1) RevisionID FROM KVK.SourceObservationRevision WHERE ArtifactHash=?",
                        bytes.fromhex(artifact.sha256),
                    )
                    if one(cursor):
                        raise SourceConflict("Original already belongs to another observation.")
                    cursor.execute(
                        "SELECT MAX(s.LogicalScanID) AS scan,MAX(o.ScanStartUTC) AS utc FROM KVK.SourceLogicalScan s WITH (UPDLOCK,HOLDLOCK) JOIN KVK.SourceObservation o ON o.ObservationID=s.ObservationID WHERE s.SourceKey=? AND s.KVK_NO=?",
                        SOURCE_KEY,
                        c.kvk_no,
                    )
                    last = one(cursor)
                    if (
                        last["utc"] is not None
                        and c.scan_start_utc.replace(tzinfo=None) <= last["utc"]
                    ):
                        raise SourceConflict(
                            "New player scans must be imported oldest first with increasing UTC."
                        )
                    scan = (last["scan"] or 0) + 1
                    if scan > INT_MAX:
                        raise SourceConflict("Source scan namespace exhausted.")
                    identity, number = str(uuid4()), 1
                    cursor.execute(
                        "INSERT KVK.SourceObservation (ObservationID,SourceKey,KVK_NO,ScanStartUTC,TimePrecision,EventDiscriminator,SelectionVersion) VALUES (?,?,?,?,?,?,?)",
                        identity,
                        SOURCE_KEY,
                        c.kvk_no,
                        c.scan_start_utc.replace(tzinfo=None),
                        c.time_precision.value,
                        c.event_discriminator,
                        1,
                    )
                revision = str(uuid4())
                cursor.execute(
                    "INSERT KVK.SourceObservationRevision (RevisionID,SourceKey,KVK_NO,ObservationID,RevisionNo,SemanticHash,DigestVersion,SchemaVersion,ArtifactHash,SupersedesRevisionID,AcceptanceState,AcceptedUTC,AcceptedBy,Reason,MetadataJson) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    revision,
                    SOURCE_KEY,
                    c.kvk_no,
                    identity,
                    number,
                    bytes.fromhex(prepared.digest.sha256),
                    prepared.digest.canonical_version,
                    prepared.schema_version,
                    bytes.fromhex(artifact.sha256),
                    observation["SelectedRevisionID"] if observation else None,
                    "corrected" if observation else "accepted",
                    utc,
                    admission.actor,
                    admission.reason,
                    canonical(asdict(prepared.metadata)),
                )
                columns = [
                    "RevisionID",
                    "SourceKey",
                    "KVK_NO",
                    "GovernorID",
                    "kingdom",
                    *(column for _, column in PLAYER_COLUMNS),
                    "FieldStatusJson",
                    "RawProfileJson",
                ]
                sql = (
                    "INSERT KVK.SourcePlayerSnapshot ("
                    + ",".join(columns)
                    + ") VALUES ("
                    + ",".join("?" for _ in columns)
                    + ")"
                )
                for row in prepared.rows:
                    values, states = [], {}
                    for header, column in PLAYER_COLUMNS:
                        cell = row.cell(header)
                        value = cell.metric.value
                        if isinstance(value, Decimal):
                            value = int(value)
                        values.append(value)
                        states[column] = cell.metric.state.value
                    cursor.execute(
                        sql,
                        revision,
                        SOURCE_KEY,
                        c.kvk_no,
                        row.key,
                        row.kingdom,
                        *values,
                        canonical(states),
                        canonical(asdict(row)),
                    )
                cursor.execute(
                    "UPDATE KVK.SourceObservation SET SelectedRevisionID=?,SelectionVersion=? WHERE ObservationID=?",
                    revision,
                    observation["SelectionVersion"] + 1 if observation else 1,
                    identity,
                )
                if not observation:
                    cursor.execute(
                        "INSERT KVK.SourceLogicalScan (SourceKey,KVK_NO,LogicalScanID,ObservationID,AllocatedUTC) VALUES (?,?,?,?,?)",
                        SOURCE_KEY,
                        c.kvk_no,
                        scan,
                        identity,
                        utc,
                    )
                self._attempt(cursor, prepared, artifact, admission, revision, False, False)
                result = Acceptance(revision, identity, scan, False, True)
        logger.info(
            "Source player acceptance kvk=%s scan=%s duplicate=%s",
            c.kvk_no,
            result.logical_scan_id,
            result.duplicate,
        )
        return result

    def accept_aggregate(self, prepared, artifact: StoredArtifact, admission: Admission):
        verified = parse_aggregate_workbook(
            self.artifacts.read(artifact), prepared.metadata, prepared.mapping
        )
        if verified != prepared:
            raise SourceConflict("Prepared aggregate does not match original.")
        c = prepared.metadata.candidate
        utc = admission.received_utc.replace(tzinfo=None)
        with transaction(self.connect) as cursor:
            lock_scope(cursor, c.kvk_no)
            self._artifact(cursor, artifact, utc)
            replay = self._replay(cursor, prepared, artifact, admission, True)
            cursor.execute(
                "SELECT * FROM KVK.SourcePeriod WHERE SourceKey=? AND KVK_NO=? AND PeriodKey=?",
                SOURCE_KEY,
                c.kvk_no,
                c.period_key,
            )
            period = one(cursor)
            if not period or period["PeriodKind"] == "no_fight":
                raise SourceConflict("Aggregate needs an explicitly configured combat period.")
            if c.coverage_start_utc.replace(tzinfo=None) != period["CoverageStartUTC"]:
                raise SourceConflict("Aggregate coverage start differs from period.")
            if (
                period["CoverageEndUTC"]
                and c.coverage_end_utc.replace(tzinfo=None) > period["CoverageEndUTC"]
            ):
                raise SourceConflict("Aggregate exceeds period coverage.")
            state = c.report_state.value
            if state != "live":
                if not admission.admin_authorized:
                    raise SourceConflict("Final aggregate requires authorized finalization.")
                if (
                    period["CoverageEndUTC"] is None
                    or c.coverage_end_utc.replace(tzinfo=None) != period["CoverageEndUTC"]
                ):
                    raise SourceConflict("Final aggregate requires exact closed-period coverage.")
            cursor.execute(
                "SELECT * FROM KVK.SourceAggregateReport WITH (UPDLOCK,HOLDLOCK) WHERE SourceKey=? AND KVK_NO=? AND PeriodKey=?",
                SOURCE_KEY,
                c.kvk_no,
                c.period_key,
            )
            family = one(cursor)
            selected = None
            if family:
                cursor.execute(
                    "SELECT * FROM KVK.SourceAggregateRevision WHERE RevisionID=?",
                    family["SelectedRevisionID"],
                )
                selected = one(cursor)
                cursor.execute(
                    "SELECT RevisionID FROM KVK.SourceAggregateRevision WHERE ReportID=? AND SemanticHash=? AND DigestVersion=? AND SchemaVersion=? AND ReportState=? AND ScanStartUTC=? AND TimePrecision=? AND CoverageStartUTC=? AND CoverageEndUTC=? AND AsOfUTC=?",
                    family["ReportID"],
                    bytes.fromhex(prepared.digest.sha256),
                    prepared.digest.canonical_version,
                    prepared.schema_version,
                    state,
                    c.scan_start_utc.replace(tzinfo=None),
                    c.time_precision.value,
                    c.coverage_start_utc.replace(tzinfo=None),
                    c.coverage_end_utc.replace(tzinfo=None),
                    c.as_of_utc.replace(tzinfo=None),
                )
                duplicate = one(cursor)
            else:
                duplicate = None
            if replay and (not duplicate or str(duplicate["RevisionID"]) != replay):
                raise SourceConflict("Replay aggregate metadata differs.")
            if duplicate:
                revision, identity = str(duplicate["RevisionID"]), str(family["ReportID"])
                if not replay:
                    self._attempt(cursor, prepared, artifact, admission, revision, True, True)
                return Acceptance(
                    revision, identity, None, True, revision == str(family["SelectedRevisionID"])
                )
            choose = True
            if selected:
                if state == "corrected_final":
                    self._correction(admission, selected["RevisionID"], family["SelectionVersion"])
                    if selected["ReportState"] not in ("final", "corrected_final"):
                        raise SourceConflict("Final correction requires selected final.")
                elif selected["ReportState"] in ("final", "corrected_final"):
                    if state != "live":
                        raise SourceConflict("Final replacement requires an explicit correction.")
                    choose = False
                elif state == "live":
                    if c.as_of_utc.replace(tzinfo=None) == selected["AsOfUTC"]:
                        self._correction(
                            admission, selected["RevisionID"], family["SelectionVersion"]
                        )
                    choose = c.as_of_utc.replace(tzinfo=None) >= selected["AsOfUTC"]
                else:
                    self._correction(admission, selected["RevisionID"], family["SelectionVersion"])
            elif state == "corrected_final":
                raise SourceConflict("Correction requires an existing final.")
            identity = str(family["ReportID"]) if family else str(uuid4())
            if not family:
                cursor.execute(
                    "INSERT KVK.SourceAggregateReport (ReportID,SourceKey,KVK_NO,PeriodKey,PeriodKind,SelectionVersion) VALUES (?,?,?,?,?,1)",
                    identity,
                    SOURCE_KEY,
                    c.kvk_no,
                    c.period_key,
                    period["PeriodKind"],
                )
            cursor.execute(
                "SELECT ISNULL(MAX(RevisionNo),0)+1 AS n FROM KVK.SourceAggregateRevision WHERE ReportID=?",
                identity,
            )
            number = one(cursor)["n"]
            revision = str(uuid4())
            mapping_hash = digest(asdict(prepared.mapping))
            cursor.execute(
                "INSERT KVK.SourceAggregateRevision (RevisionID,SourceKey,KVK_NO,ReportID,PeriodKind,RevisionNo,ArtifactHash,SemanticHash,DigestVersion,SchemaVersion,ScanStartUTC,TimePrecision,CoverageStartUTC,CoverageEndUTC,AsOfUTC,ReportState,SupersedesRevisionID,AcceptedUTC,AcceptedBy,Reason,MappingDigest,ScopeDigest,MetadataJson) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                revision,
                SOURCE_KEY,
                c.kvk_no,
                identity,
                period["PeriodKind"],
                number,
                bytes.fromhex(artifact.sha256),
                bytes.fromhex(prepared.digest.sha256),
                prepared.digest.canonical_version,
                prepared.schema_version,
                c.scan_start_utc.replace(tzinfo=None),
                c.time_precision.value,
                c.coverage_start_utc.replace(tzinfo=None),
                c.coverage_end_utc.replace(tzinfo=None),
                c.as_of_utc.replace(tzinfo=None),
                state,
                selected["RevisionID"] if selected else None,
                utc,
                admission.actor,
                admission.reason,
                mapping_hash,
                digest(asdict(prepared.metadata.scope)),
                canonical(asdict(prepared.metadata)),
            )
            labels = {camp: label for _, camp, label in prepared.mapping.entries}
            for table, report_rows in (
                ("SourceKingdomReportRow", prepared.kingdom_rows),
                ("SourceCampReportRow", prepared.camp_rows),
            ):
                for row in report_rows:
                    columns = ["RevisionID", "SourceKey", "KVK_NO"]
                    values = [revision, SOURCE_KEY, c.kvk_no]
                    if table == "SourceKingdomReportRow":
                        columns.append("Kingdom")
                        values.append(row.key)
                    columns += ["CampID", "CampLabel", "MappingDigest"]
                    values += [row.camp_id, labels[row.camp_id], mapping_hash]
                    for header, column in AGGREGATE_COLUMNS:
                        metric = row.cell(header).metric
                        columns += [
                            column,
                            column + "_raw",
                            column + "_unit",
                            column + "_precision",
                        ]
                        values += [
                            metric.value,
                            metric.raw_token,
                            metric.displayed_unit,
                            metric.precision_kind,
                        ]
                    columns.append("RawCellsJson")
                    values.append(canonical(asdict(row)))
                    cursor.execute(
                        "INSERT KVK."
                        + table
                        + " ("
                        + ",".join(columns)
                        + ") VALUES ("
                        + ",".join("?" for _ in columns)
                        + ")",
                        *values,
                    )
            if choose:
                cursor.execute(
                    "UPDATE KVK.SourceAggregateReport SET SelectedRevisionID=?,SelectionVersion=? WHERE ReportID=?",
                    revision,
                    family["SelectionVersion"] + 1 if family else 1,
                    identity,
                )
            self._attempt(cursor, prepared, artifact, admission, revision, False, True)
            return Acceptance(revision, identity, None, False, choose)
