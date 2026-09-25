"""Authority-only enrollment of new, dedicated private output files.

No default clients, credential access, retry, discovery, cleanup or pool registration.
Creation and eligibility are separate append-only receipts. A process restart never
adopts a claim: incomplete enrollment remains explicit operator reconciliation.
"""

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import re
from uuid import UUID, uuid4

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_execution_protocol import (
    ProviderRequest,
    decode,
    encode,
    enrollment_create_arguments,
    uuid_text,
)
from services.export_reconciliation_service import ClosedStreamVerifier


def verification_requests(editor_email):
    """All requests for one newly created one-cell workbook, in fixed order."""
    return (
        (
            "drive.permissions.create",
            {
                "fields": "id,type,role,emailAddress",
                "sendNotificationEmail": False,
                "body": {"type": "user", "role": "writer", "emailAddress": editor_email},
            },
        ),
        (
            "drive.files.get",
            {
                "fields": "id,mimeType,trashed,driveId,owners(emailAddress),appProperties,description"
            },
        ),
        (
            "drive.permissions.list",
            {
                "fields": "permissions(id,type,role,emailAddress,deleted,pendingOwner),nextPageToken",
                "pageSize": 1000,
            },
        ),
        (
            "sheets.get",
            {"includeGridData": True},
        ),
        (
            "sheets.values.batchGet",
            {
                "ranges": ["'Sheet1'!A1:A1"],
                "valueRenderOption": "FORMULA",
                "dateTimeRenderOption": "SERIAL_NUMBER",
            },
        ),
    )


@dataclass(frozen=True, init=False)
class EnrollmentPlan:
    document: bytes

    def __init__(self, value):
        raw = encode(value)
        value = decode(raw)
        if (
            set(value)
            != {
                "version",
                "purpose",
                "account",
                "storage_owner",
                "owner_email",
                "editor_email",
                "project_id",
                "credential_profile_sha256",
                "manifest_sha256",
                "file_count",
                "plan_id",
            }
            or type(value["version"]) is not int
            or value["version"] != 1
            or value["purpose"] != "output_enrollment"
        ):
            raise SourceConflict("Exact versioned enrollment plan required.")
        for key in ("account", "storage_owner"):
            if not isinstance(value[key], str) or not re.fullmatch(
                r"[A-Za-z0-9_.@:-]{1,128}", value[key]
            ):
                raise SourceConflict("Canonical enrollment account/storage identity required.")
        if (
            not isinstance(value["owner_email"], str)
            or not re.fullmatch(
                r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9.-]+\.[a-z]{2,}", value["owner_email"]
            )
            or len(value["owner_email"]) > 254
            or value["owner_email"].endswith("gserviceaccount.com")
            or not isinstance(value["project_id"], str)
            or not re.fullmatch(r"[a-z0-9-]{1,128}", value["project_id"])
            or not isinstance(value["editor_email"], str)
            or not re.fullmatch(
                r"[a-z0-9-]+@" + re.escape(value["project_id"]) + r"\.iam\.gserviceaccount\.com",
                value["editor_email"],
            )
            or type(value["file_count"]) is not int
            or not 3 <= value["file_count"] <= 17
        ):
            raise SourceConflict(
                "Exact human owner, service-account Editor and 2–16 slots required."
            )
        for key in ("credential_profile_sha256", "manifest_sha256"):
            if not isinstance(value[key], str) or not re.fullmatch(r"[0-9a-f]{64}", value[key]):
                raise SourceConflict("Protected credential/source manifest identities required.")
        uuid_text(value["plan_id"])
        object.__setattr__(self, "document", raw)

    def value(self):
        return decode(self.document)

    @property
    def sql_json(self):
        return self.document.decode("utf-8")

    @property
    def digest(self):
        return hashlib.sha256(self.sql_json.encode("utf-16-le")).digest()

    def authorize_scope(self, scope):
        value = self.value()
        detail = decode(scope["ScopeJson"].encode("utf-8"))
        if (
            scope["Purpose"] != "enrollment"
            or scope["OwnerKind"] != "preparation"
            or scope["AccountKey"] != value["account"]
            or scope["NestedToken"] is not None
            or scope["Epoch"] is not None
            or scope["RegistrationHash"] != self.digest
            or scope["SnapshotHash"] != self.digest
            or set(detail) != {"resources", "enrollment"}
        ):
            raise SourceConflict("Exact protected enrollment scope required.")
        for name in ("ObjectID", "OwnerID"):
            uuid_text(scope[name])
        for name in ("Fence", "ClaimVersion"):
            if type(scope[name]) is not int or not 0 < scope[name] < 2**63:
                raise SourceConflict("Exact enrollment owner/fence/version required.")
        phase, resources = detail["enrollment"], detail["resources"]
        if (
            not isinstance(phase, dict)
            or set(phase) != {"phase", "ordinal"}
            or phase["phase"] not in {"create", "verify"}
            or type(phase["ordinal"]) is not int
            or not 0 <= phase["ordinal"] <= value["file_count"]
            or (phase["phase"] == "create") != (phase["ordinal"] < value["file_count"])
            or not isinstance(resources, list)
            or len(resources) != phase["ordinal"] + 1
        ):
            raise SourceConflict("Exact enrollment phase and growing membership required.")
        keys = []
        for resource in resources:
            if (
                not isinstance(resource, dict)
                or set(resource) != {"key", "version"}
                or not isinstance(resource["key"], str)
                or type(resource["version"]) is not int
                or not 0 < resource["version"] < 2**63
            ):
                raise SourceConflict("Exact enrollment resource versions required.")
            keys.append(resource["key"])
        if (
            keys != sorted(set(keys))
            or keys[0] != "account:" + value["account"]
            or any(not re.fullmatch(r"destination:[A-Za-z0-9_-]{3,128}", k) for k in keys[1:])
        ):
            raise SourceConflict("Enrollment admits only its account and returned destinations.")
        return phase

    def authorize_request(self, request, *, phase, ordinal):
        value = self.value()
        if phase == "create":
            expected = enrollment_create_arguments(value["plan_id"], ordinal)
            if request.operation != "sheets.create" or request.arguments != expected:
                raise SourceConflict("Only the next fixed enrollment creation is admitted.")
        elif (
            phase != "verify"
            or ordinal != value["file_count"]
            or (request.operation, request.arguments)
            not in verification_requests(value["editor_email"])
        ):
            raise SourceConflict("Only the fixed Editor grant and private readback are admitted.")


def enrollment_scope(plan, claim):
    value = plan.value()
    progress = json.loads(claim["GenerationJson"])
    if (
        claim["AccountKey"] != value["account"]
        or claim["StorageOwner"] != value["storage_owner"]
        or claim["ConsumerKind"] != "config"
        or claim["State"] != "preflight"
        or claim["RequestJson"] != plan.sql_json
        or bytes(claim["RequestHash"]) != plan.digest
        or claim["JobID"] is not None
        or claim["SpoolKey"] is not None
    ):
        raise SourceConflict("Enrollment cannot adopt another preparation or plan.")
    scope = dict(
        AccountKey=value["account"],
        OwnerKind="preparation",
        ObjectID=str(claim["PreparationID"]).lower(),
        OwnerID=str(claim["OwnerID"]).lower(),
        Fence=claim["Fence"],
        ClaimVersion=claim["Version"],
        NestedToken=None,
        RegistrationHash=plan.digest,
        Epoch=None,
        SnapshotHash=plan.digest,
        ScopeJson=encode(
            dict(
                resources=json.loads(claim["ResourcesJson"]),
                enrollment=dict(phase=progress["phase"], ordinal=progress["next_ordinal"]),
            )
        ).decode("utf-8"),
        Purpose="enrollment",
    )
    plan.authorize_scope(scope)
    return scope


def _private_readback(plan, ordinal, file_id, responses):
    value = plan.value()
    grant, file, acl, sheet, cells = responses
    expected_title = enrollment_create_arguments(value["plan_id"], ordinal)["body"]["properties"][
        "title"
    ]
    if (
        (grant.get("type"), grant.get("role"), grant.get("emailAddress"))
        != ("user", "writer", value["editor_email"])
        or file.get("id") != file_id
        or file.get("mimeType") != "application/vnd.google-apps.spreadsheet"
        or file.get("trashed") is not False
        or file.get("driveId") is not None
        or file.get("owners") != [{"emailAddress": value["owner_email"]}]
        or file.get("appProperties", {}) != {}
        or file.get("description", "") != ""
        or acl.get("nextPageToken")
        or not isinstance(acl.get("permissions"), list)
        or len(acl["permissions"]) != 2
    ):
        raise SourceConflict("New file owner/private ACL or Editor grant differs.")
    expected = {(value["owner_email"], "owner"), (value["editor_email"], "writer")}
    actual = set()
    for permission in acl["permissions"]:
        if (
            permission.get("type") != "user"
            or permission.get("deleted", False) is not False
            or permission.get("pendingOwner", False) is not False
            or not permission.get("id")
            or (
                permission.get("emailAddress") == value["editor_email"]
                and permission["id"] != grant["id"]
            )
        ):
            raise SourceConflict(
                "Enrollment ACL contains an unapproved principal or pending transfer."
            )
        actual.add((permission.get("emailAddress"), permission.get("role")))
    sheets = sheet.get("sheets")
    if (
        actual != expected
        or sheet.get("spreadsheetId") != file_id
        or sheet.get("properties", {}).get("title") != expected_title
        or (
            not isinstance(sheets, list)
            or len(sheets) != 1
            or any(sheet.get(k) for k in ("namedRanges", "developerMetadata", "dataSources"))
        )
    ):
        raise SourceConflict("Exact private enrollment workbook required.")
    props = sheets[0].get("properties", {})
    grid = props.get("gridProperties", {})
    data = sheets[0].get("data", [])
    if set(sheets[0]) - {"properties", "data"} or not isinstance(data, list):
        raise SourceConflict("Enrollment grid contains additional sheet metadata.")
    for block in data:
        if (
            not isinstance(block, dict)
            or set(block) - {"startRow", "startColumn", "rowData", "rowMetadata", "columnMetadata"}
            or block.get("startRow", 0) != 0
            or block.get("startColumn", 0) != 0
            or not isinstance(block.get("rowData", []), list)
            or len(block.get("rowData", [])) > 1
        ):
            raise SourceConflict("Enrollment full-grid readback differs.")
        for row in block.get("rowData", []):
            if (
                not isinstance(row, dict)
                or set(row) - {"values"}
                or not isinstance(row.get("values", []), list)
                or len(row.get("values", [])) > 1
                or any(cell != {} for cell in row.get("values", []))
            ):
                raise SourceConflict(
                    "Enrollment cell contains data, notes, formatting or metadata."
                )
        for key in ("rowMetadata", "columnMetadata"):
            metadata = block.get(key, [])
            if (
                not isinstance(metadata, list)
                or len(metadata) > 1
                or any(not isinstance(item, dict) or set(item) - {"pixelSize"} for item in metadata)
            ):
                raise SourceConflict("Enrollment contains hidden or additional grid metadata.")
    if (
        type(props.get("sheetId")) is not int
        or props["sheetId"] != 0
        or props.get("title") != "Sheet1"
        or props.get("sheetType", "GRID") != "GRID"
        or props.get("hidden", False) is not False
        or type(grid.get("rowCount")) is not int
        or grid["rowCount"] != 1
        or type(grid.get("columnCount")) is not int
        or grid["columnCount"] != 1
        or cells.get("spreadsheetId") != file_id
        or len(cells.get("valueRanges", [])) != 1
        or any(
            cell not in (None, "")
            for row in cells["valueRanges"][0].get("values", [])
            for cell in row
        )
    ):
        raise SourceConflict("New enrollment must remain the entire private empty one-cell grid.")


class EnrollmentEvidence:
    """Authenticate exact original private journals; never dispatch or repair them."""

    def __init__(self, *, dal, store):
        self.dal, self.store = dal, store
        self.closed = ClosedStreamVerifier(dal=dal, store=store)

    def transcript(self, plan, stream_id):
        self.closed.verify(
            stream_id,
            account=plan.value()["account"],
            registration_hash=plan.digest,
            require_observation=False,
        )
        stream = self.dal.read_stream(stream_id)
        if stream["Purpose"] != "enrollment":
            raise SourceConflict("Exact enrollment transcript required.")
        scope = {
            k: stream[k]
            for k in (
                "AccountKey",
                "OwnerID",
                "Fence",
                "NestedToken",
                "RegistrationHash",
                "Epoch",
                "SnapshotHash",
                "ScopeJson",
                "Purpose",
            )
        }
        scope.update(
            OwnerKind="preparation",
            ObjectID=str(stream["PreparationID"]).lower(),
            ClaimVersion=stream["ClaimVersion"],
        )
        scope["OwnerID"] = str(scope["OwnerID"]).lower()
        phase = plan.authorize_scope(scope)
        expected_count = 1 if phase["phase"] == "create" else 5 * plan.value()["file_count"]
        if stream["LastSequence"] != expected_count:
            raise SourceConflict("Enrollment transcript exceeds the fixed complete request set.")
        records = []
        for request_id in self.dal.request_ids(stream_id):
            request, events = self.dal.read_request(request_id)
            if [e["State"] for e in events] != ["prepared", "dispatch_intent", "succeeded"]:
                raise SourceConflict("Enrollment requires exact successful requests, never retry.")
            typed = ProviderRequest.parse(
                self.closed._document(request["PayloadReference"], request["PayloadHash"]),
                enrollment=True,
            )
            plan.authorize_request(typed, **phase)
            if typed.target not in (
                {scope["ObjectID"]}
                if phase["phase"] == "create"
                else {
                    r["key"].removeprefix("destination:")
                    for r in json.loads(scope["ScopeJson"])["resources"]
                    if r["key"].startswith("destination:")
                }
            ):
                raise SourceConflict("Enrollment transcript targets a different preparation/file.")
            records.append(
                (
                    typed,
                    self.closed._document(
                        events[-1]["EvidenceReference"], events[-1]["EvidenceHash"]
                    )["response"],
                    events[-1],
                )
            )
        return stream, records

    def creation(self, plan, stream_id, request_id, ordinal):
        stream, records = self.transcript(plan, stream_id)
        if (
            len(records) != 1
            or records[0][0].request_id != request_id
            or records[0][0].operation != "sheets.create"
            or records[0][0].arguments["ordinal"] != ordinal
        ):
            raise SourceConflict("One exact original successful creation required.")
        request, response, event = records[0]
        return dict(
            version=1,
            file_id=response["spreadsheetId"],
            preparation_id=str(stream["PreparationID"]).lower(),
            ordinal=ordinal,
            session_id=str(stream["SessionID"]).lower(),
            stream_id=stream_id,
            request_id=request_id,
            response_event_id=str(event["EventID"]).lower(),
            response_sha256=bytes(event["EvidenceHash"]).hex(),
            closure_sha256=bytes(stream["ClosureHash"]).hex(),
            plan_sha256=plan.digest.hex(),
            profile_sha256=plan.value()["credential_profile_sha256"],
        )

    def eligibility(self, plan, stream_id, origins):
        stream, records = self.transcript(plan, stream_id)
        value = plan.value()
        if len(origins) != value["file_count"] or len(records) != 5 * len(origins):
            raise SourceConflict("Complete original file set and fixed transcript required.")
        for ordinal, origin in enumerate(origins):
            if (
                origin["ordinal"] != ordinal
                or origin["preparation_id"] != str(stream["PreparationID"]).lower()
                or origin["session_id"] != str(stream["SessionID"]).lower()
            ):
                raise SourceConflict("Origin set differs from the verification owner/session.")
            group = records[ordinal * 5 : (ordinal + 1) * 5]
            if [(r.operation, r.arguments) for r, _, _ in group] != list(
                verification_requests(value["editor_email"])
            ) or any(r.target != origin["file_id"] for r, _, _ in group):
                raise SourceConflict("Grant/readback order or destination differs.")
            _private_readback(plan, ordinal, origin["file_id"], [body for _, body, _ in group])
        return dict(
            version=1,
            plan_sha256=plan.digest.hex(),
            origins=origins,
            stream_id=stream_id,
            closure_sha256=bytes(stream["ClosureHash"]).hex(),
        )


class OutputEnrollment:
    """One explicit, non-resumable authority-side invocation; all I/O is injected."""

    def __init__(self, *, plan, authority, dal, store):
        if not isinstance(plan, EnrollmentPlan) or authority.enrollment_plan != plan:
            raise SourceConflict("Separately provisioned enrollment authority required.")
        self.plan, self.authority, self.dal, self.store = plan, authority, dal, store
        self.evidence = EnrollmentEvidence(dal=dal, store=store)
        self.started = False

    @contextmanager
    def _stream(self, claim):
        if json.loads(claim["GenerationJson"])["session_id"] != self.authority.session_id:
            raise SourceConflict("Enrollment cannot adopt a preparation from another session.")
        identifier = str(uuid4())
        self.authority.open_stream(stream_id=identifier, scope=enrollment_scope(self.plan, claim))
        try:
            yield identifier
        finally:
            self.authority.close_stream(identifier)

    def _request(self, stream_id, operation, target, arguments):
        request = ProviderRequest.parse(
            dict(
                version=1,
                request_id=str(uuid4()),
                stream_id=stream_id,
                operation=operation,
                target=target,
                arguments=arguments,
            ),
            enrollment=True,
        )
        self.authority.execute(request.message())
        return request.request_id

    def run(self, *, actor, reason):
        if self.started:
            raise SourceConflict("Enrollment invocation cannot be replayed or resumed.")
        self.started = True
        if (
            not isinstance(actor, str)
            or not 0 < len(actor) <= 128
            or not isinstance(reason, str)
            or not 0 < len(reason) <= 1024
        ):
            raise SourceConflict("Bounded enrollment actor/reason required.")
        value = self.plan.value()
        preparation_id, owner_id = str(uuid4()), str(uuid4())
        common = dict(
            SessionID=self.authority.session_id,
            PreparationID=preparation_id,
            AccountKey=value["account"],
            OwnerID=owner_id,
        )
        claim = self.dal.transition(
            "enrollment",
            Action="begin",
            ExpectedVersion=0,
            PlanJson=self.plan.sql_json,
            Actor=actor,
            Reason=reason,
            **common,
        )
        origins = []
        for ordinal in range(value["file_count"]):
            with self._stream(claim) as stream_id:
                request_id = self._request(
                    stream_id,
                    "sheets.create",
                    preparation_id,
                    enrollment_create_arguments(value["plan_id"], ordinal),
                )
            origin = self.evidence.creation(self.plan, stream_id, request_id, ordinal)
            receipt = self.store.put(encode(origin))
            claim = self.dal.transition(
                "enrollment",
                Action="bind",
                ExpectedVersion=claim["Version"],
                Fence=claim["Fence"],
                ResourcesJson=claim["ResourcesJson"],
                Ordinal=ordinal,
                FileID=origin["file_id"],
                CreationStreamID=stream_id,
                CreationRequestID=request_id,
                ResponseEventID=origin["response_event_id"],
                OriginHash=bytes.fromhex(receipt.sha256),
                OriginReference=str(UUID(receipt.key)),
                **common,
            )
            origins.append(origin)
        with self._stream(claim) as stream_id:
            for origin in origins:
                for operation, arguments in verification_requests(value["editor_email"]):
                    self._request(stream_id, operation, origin["file_id"], arguments)
        sealed = self.evidence.eligibility(self.plan, stream_id, origins)
        receipt = self.store.put(encode(sealed))
        self.dal.transition(
            "enrollment",
            Action="complete",
            ExpectedVersion=claim["Version"],
            Fence=claim["Fence"],
            ResourcesJson=claim["ResourcesJson"],
            VerificationStreamID=stream_id,
            EligibilityHash=bytes.fromhex(receipt.sha256),
            EligibilityReference=str(UUID(receipt.key)),
            **common,
        )
        return sealed


class ManagedOriginVerifier:
    """Authenticate one whole enrolled pool; this alone never establishes finality."""

    def __init__(self, *, dal, store):
        self.dal, self.store = dal, store
        self.evidence = EnrollmentEvidence(dal=dal, store=store)

    def verify(self, *, account, targets, owner_email, editor_email):
        if (
            not isinstance(targets, list)
            or not 3 <= len(targets) <= 17
            or targets != sorted(set(targets))
        ):
            raise SourceConflict("Complete canonical enrolled pool required.")
        rows = self.dal.read_origins(account, targets)
        if len(rows) != 2 * len(targets):
            raise SourceConflict("Unproven old files cannot receive fabricated origins.")
        grouped = {}
        for row in rows:
            key = (row["FileID"], row["Stage"])
            if (
                key in grouped
                or key[0] not in targets
                or key[1] not in {"created", "eligible"}
                or row["PreparationState"] != "completed"
            ):
                raise SourceConflict("Origin eligibility or exact membership differs.")
            grouped[key] = row
        created = sorted(
            (grouped[(target, "created")] for target in targets), key=lambda r: r["Ordinal"]
        )
        first = created[0]
        plan = EnrollmentPlan(decode(first["RequestJson"].encode("utf-8")))
        value = plan.value()
        session = self.dal.read_session(str(first["SessionID"]).lower())
        if (
            session is None
            or str(session["SessionID"]).lower() != str(first["SessionID"]).lower()
            or session["ProtocolVersion"] != 1
            or bytes(session["ManifestHash"]).hex() != value["manifest_sha256"]
        ):
            raise SourceConflict("Origin session differs from the original protected manifest.")
        if (value["account"], value["owner_email"], value["editor_email"], value["file_count"]) != (
            account,
            owner_email,
            editor_email,
            len(targets),
        ):
            raise SourceConflict("Origin owner/Editor/account or pool membership differs.")
        receipts, seal = [], None
        immutable = (
            "FileID",
            "PreparationID",
            "Ordinal",
            "SessionID",
            "CreationStreamID",
            "CreationRequestID",
            "ResponseEventID",
            "PlanHash",
            "ProfileHash",
            "ResponseHash",
            "CreationClosureHash",
            "OriginHash",
            "OriginReference",
        )
        for ordinal, row in enumerate(created):
            eligible = grouped[(row["FileID"], "eligible")]
            if (
                row["PreparationID"] != first["PreparationID"]
                or row["Ordinal"] != ordinal
                or row["RequestJson"] != plan.sql_json
                or bytes(row["RequestHash"]) != plan.digest
                or any(row[k] != eligible[k] for k in immutable)
            ):
                raise SourceConflict("Immutable creation/eligibility lineage differs.")
            origin = self.evidence.creation(
                plan,
                str(row["CreationStreamID"]).lower(),
                str(row["CreationRequestID"]).lower(),
                ordinal,
            )
            expected = dict(
                version=1,
                file_id=row["FileID"],
                preparation_id=str(row["PreparationID"]).lower(),
                ordinal=ordinal,
                session_id=str(row["SessionID"]).lower(),
                stream_id=str(row["CreationStreamID"]).lower(),
                request_id=str(row["CreationRequestID"]).lower(),
                response_event_id=str(row["ResponseEventID"]).lower(),
                response_sha256=bytes(row["ResponseHash"]).hex(),
                closure_sha256=bytes(row["CreationClosureHash"]).hex(),
                plan_sha256=bytes(row["PlanHash"]).hex(),
                profile_sha256=bytes(row["ProfileHash"]).hex(),
            )
            original = decode(self.store.read_reference(row["OriginReference"], row["OriginHash"]))
            if encode(original) != encode(origin) or encode(origin) != encode(expected):
                raise SourceConflict("Protected origin differs from the actual creation response.")
            current = decode(
                self.store.read_reference(
                    eligible["EligibilityReference"], eligible["EligibilityHash"]
                )
            )
            if (
                current.get("stream_id") != str(eligible["VerificationStreamID"]).lower()
                or current.get("closure_sha256") != bytes(eligible["VerificationClosureHash"]).hex()
                or (seal is not None and encode(current) != encode(seal))
            ):
                raise SourceConflict("Eligible files require the same exact closed verification.")
            seal = current
            receipts.append(origin)
        actual_seal = self.evidence.eligibility(plan, seal["stream_id"], receipts)
        if encode(seal) != encode(actual_seal):
            raise SourceConflict("Eligibility seal differs from the complete original readback.")
        return actual_seal
