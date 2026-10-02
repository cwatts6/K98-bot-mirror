"""Explicit registration of admin-created files; no provider mutation or OAuth.

Historical API-created origins remain readable through the legacy verifier.
A registration is one non-resumable, fenced observation of an explicit manifest.
"""

import re
from uuid import UUID, uuid4

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_enrollment_service import (
    EnrollmentEvidence,
    EnrollmentPlan,
    OutputEnrollment,
    verification_requests,
)
from services.export_execution_protocol import decode, encode


def manual_profile(manifest):
    """Nonsecret existing service identity, bound to the reviewed credential bytes."""
    if "enrollment_profile" in manifest or not isinstance(
        manifest.get("deployment_boundary"), dict
    ):
        raise SourceConflict(
            "Manual registration requires existing service credentials, not OAuth."
        )
    identity = manifest["deployment_boundary"]["identity"]
    return dict(
        version=1,
        service_account_email=manifest["service_account_email"],
        project_id=manifest["project_id"],
        client_id=identity["client_id"],
        private_key_id=identity["private_key_id"],
        credential_sha256=identity["credential_sha256"],
    )


class ManualEnrollmentPlan(EnrollmentPlan):
    def __init__(self, value):
        raw = encode(value)
        value = decode(raw)
        version = value.get("version")
        if type(version) is not int or version not in (2, 3):
            raise SourceConflict("Version 2 or 3 manual registration required.")
        if (version == 2 and "access_policy" in value) or (
            version == 3 and value.get("access_policy") != "public_viewer_link_v1"
        ):
            raise SourceConflict("Exact versioned manual access policy required.")
        legacy = {
            k: v
            for k, v in value.items()
            if k not in {"files", "protected_file_ids", "access_policy"}
        }
        legacy["version"] = 1
        super().__init__(legacy)
        files, protected = value.get("files"), value.get("protected_file_ids")
        if not isinstance(files, list) or len(files) != value["file_count"]:
            raise SourceConflict("Exact manual file manifest required.")
        if (
            not isinstance(protected, list)
            or any(
                not isinstance(x, str) or not re.fullmatch(r"[A-Za-z0-9_-]{3,128}", x)
                for x in protected
            )
            or protected != sorted(set(protected))
        ):
            raise SourceConflict("Canonical protected exclusion list required.")
        ids = []
        for f in files:
            if (
                not isinstance(f, dict)
                or set(f) != {"file_id", "sheet_id", "title", "rows", "columns"}
                or not isinstance(f["file_id"], str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{3,128}", f["file_id"])
                or type(f["sheet_id"]) is not int
                or not 0 <= f["sheet_id"] < 2**31
                or not isinstance(f["title"], str)
                or not re.fullmatch(r"[A-Za-z0-9 _-]{1,100}", f["title"])
                or any(type(f[k]) is not int or not 1 <= f[k] <= 10000 for k in ("rows", "columns"))
                or f["rows"] * f["columns"] > 50000
            ):
                raise SourceConflict("Bounded exact initial grid required.")
            ids.append(f["file_id"])
        if len(set(ids)) != len(ids) or set(ids) & set(protected):
            raise SourceConflict("Duplicate or protected manual destination.")
        object.__setattr__(self, "document", raw)

    def authorize_scope(self, scope):
        phase = super().authorize_scope(scope)
        resources = decode(scope["ScopeJson"].encode())["resources"]
        expected = sorted(
            ["account:" + self.value()["account"]]
            + ["destination:" + f["file_id"] for f in self.value()["files"]]
        )
        if (
            phase != {"phase": "verify", "ordinal": self.value()["file_count"]}
            or [r["key"] for r in resources] != expected
        ):
            raise SourceConflict("Manual registration requires the entire declared file set.")
        return phase

    def authorize_request(self, request, *, phase, ordinal):
        value = self.value()
        target = next((f for f in value["files"] if f["file_id"] == request.target), None)
        if (
            phase != "verify"
            or ordinal != value["file_count"]
            or target is None
            or request.mutation
            or (request.operation, request.arguments)
            not in manual_requests(target, version=value["version"])
        ):
            raise SourceConflict("Manual registration permits only exact readback requests.")


def _range_suffix(file):
    column, number = "", file["columns"]
    while number:
        number, remainder = divmod(number - 1, 26)
        column = chr(65 + remainder) + column
    return "!A1:" + column + str(file["rows"])


def manual_requests(file, *, version=2):
    if type(version) is not int or version not in (2, 3):
        raise SourceConflict("Unknown manual request version.")
    base = list(verification_requests("")[1:4])
    base[1] = (
        "drive.permissions.list",
        {
            "fields": "permissions(id,type,role,emailAddress,deleted,pendingOwner,permissionDetails,expirationTime),nextPageToken",
            "pageSize": 1000,
        },
    )
    if version == 3:
        base[1] = (
            "drive.permissions.list",
            {
                "fields": "permissions(id,type,role,emailAddress,deleted,pendingOwner,permissionDetails,expirationTime,allowFileDiscovery,domain,view),nextPageToken",
                "pageSize": 100,
            },
        )
    # Version 2 request bytes remain unchanged for historical transcript replay.
    # Full initial grid is deliberately bounded by the manifest; never fetch unrelated cells.
    return (
        *base,
        (
            "sheets.values.batchGet",
            {
                "ranges": ["'" + file["title"] + "'" + _range_suffix(file)],
                "valueRenderOption": "FORMULA",
                "dateTimeRenderOption": "SERIAL_NUMBER",
            },
        ),
    )


def _private_manual_permissions(value, acl):
    permissions = acl.get("permissions")
    expected = {(value["owner_email"], "owner"), (value["editor_email"], "writer")}
    if (
        not isinstance(permissions, list)
        or len(permissions) != 2
        or any(
            not isinstance(p, dict)
            or p.get("type") != "user"
            or not p.get("id")
            or p.get("deleted", False) is not False
            or p.get("pendingOwner", False) is not False
            or p.get("permissionDetails")
            or p.get("expirationTime")
            for p in permissions
        )
        or {(p.get("emailAddress"), p.get("role")) for p in permissions} != expected
        or len({p["id"] for p in permissions}) != 2
    ):
        raise SourceConflict("Exact initial private owner/Editor permissions required.")


def _public_manual_permissions(value, acl):
    """Exact link-viewer policy; same-owner inherited roles add no principal."""
    permissions = acl.get("permissions")
    if not isinstance(permissions, list) or len(permissions) != 3:
        raise SourceConflict("Exact owner, direct Editor and public Viewer required.")
    expected = {
        ("user", value["owner_email"], "owner"),
        ("user", value["editor_email"], "writer"),
        ("anyone", None, "reader"),
    }
    observed, ids = set(), set()
    for permission in permissions:
        if not isinstance(permission, dict):
            raise SourceConflict("Typed permission required.")
        identity = (
            permission.get("type"),
            permission.get("emailAddress"),
            permission.get("role"),
        )
        permission_id = permission.get("id")
        if (
            any(x is not None and not isinstance(x, str) for x in identity)
            or not isinstance(permission_id, str)
            or not permission_id
            or permission_id in ids
            or permission.get("deleted", False) is not False
            or permission.get("pendingOwner", False) is not False
            or "expirationTime" in permission
            or "domain" in permission
            or "view" in permission
        ):
            raise SourceConflict("Unexpected or incomplete manual permission.")
        if identity not in expected or identity in observed:
            raise SourceConflict("Unexpected or duplicate permission principal/role.")
        if identity[0] == "anyone":
            if permission.get("allowFileDiscovery") is not False:
                raise SourceConflict("Explicit link-only Viewer access required.")
        elif "allowFileDiscovery" in permission:
            raise SourceConflict("Unexpected discovery flag on user permission.")
        details = permission.get("permissionDetails")
        if not isinstance(details, list) or not 1 <= len(details) <= 4:
            raise SourceConflict("Direct permission details required.")
        seen, direct = set(), 0
        for detail in details:
            if (
                not isinstance(detail, dict)
                or set(detail) != {"permissionType", "role", "inherited"}
                or detail["permissionType"] != "file"
                or not isinstance(detail["role"], str)
                or type(detail["inherited"]) is not bool
            ):
                raise SourceConflict("Malformed or unscoped permission details.")
            entry = (detail["role"], detail["inherited"])
            if entry in seen:
                raise SourceConflict("Duplicate permission details.")
            seen.add(entry)
            if not detail["inherited"]:
                if detail["role"] != identity[2]:
                    raise SourceConflict("Direct role differs from permission.")
                direct += 1
            elif identity != ("user", value["owner_email"], "owner") or detail["role"] not in {
                "reader",
                "commenter",
                "writer",
            }:
                raise SourceConflict("Only subordinate same-owner inheritance is allowed.")
        if direct != 1:
            raise SourceConflict("Exactly one matching direct grant required.")
        ids.add(permission_id)
        observed.add(identity)
    if observed != expected:
        raise SourceConflict("Manual access policy differs.")


def manual_readback(plan, file, responses):
    metadata, acl, sheet, cells = responses
    value = plan.value()
    if (
        metadata.get("id") != file["file_id"]
        or metadata.get("mimeType") != "application/vnd.google-apps.spreadsheet"
        or metadata.get("trashed") is not False
        or metadata.get("driveId") is not None
        or metadata.get("owners") != [{"emailAddress": value["owner_email"]}]
        or metadata.get("appProperties", {})
        or metadata.get("description", "")
        or acl.get("nextPageToken")
    ):
        raise SourceConflict("Manual owner or file metadata differs.")
    if value["version"] == 3:
        _public_manual_permissions(value, acl)
    else:
        _private_manual_permissions(value, acl)
    sheets = sheet.get("sheets")
    if (
        sheet.get("spreadsheetId") != file["file_id"]
        or not isinstance(sheets, list)
        or len(sheets) != 1
        or any(sheet.get(k) for k in ("namedRanges", "developerMetadata", "dataSources"))
    ):
        raise SourceConflict("Manual workbook structure differs.")
    tab = sheets[0]
    props = tab.get("properties", {})
    grid = props.get("gridProperties", {})
    if (
        props.get("sheetId") != file["sheet_id"]
        or type(props.get("sheetId")) is not int
        or props.get("title") != file["title"]
        or props.get("sheetType", "GRID") != "GRID"
        or props.get("hidden", False) is not False
        or any(type(grid.get(k)) is not int for k in ("rowCount", "columnCount"))
        or grid.get("rowCount") != file["rows"]
        or grid.get("columnCount") != file["columns"]
        or any(grid.get(k, 0) for k in ("frozenRowCount", "frozenColumnCount"))
        or set(tab) - {"properties", "data"}
    ):
        raise SourceConflict("Manual grid identity or shape differs.")
    data = tab.get("data", [])
    if not isinstance(data, list):
        raise SourceConflict("Full manual grid readback required.")
    for block in data:
        if (
            not isinstance(block, dict)
            or set(block) - {"startRow", "startColumn", "rowData", "rowMetadata", "columnMetadata"}
            or block.get("startRow", 0) != 0
            or block.get("startColumn", 0) != 0
        ):
            raise SourceConflict("Unexpected grid readback offsets/metadata.")
        rows = block.get("rowData", [])
        if (
            not isinstance(rows, list)
            or len(rows) > file["rows"]
            or any(
                not isinstance(r, dict)
                or set(r) - {"values"}
                or not isinstance(r.get("values", []), list)
                or len(r.get("values", [])) > file["columns"]
                or any(c != {} for c in r.get("values", []))
                for r in rows
            )
        ):
            raise SourceConflict("Initial file must be empty; no automatic clearing.")
        for key, limit in (
            ("rowMetadata", file["rows"]),
            ("columnMetadata", file["columns"]),
        ):
            items = block.get(key, [])
            if (
                not isinstance(items, list)
                or len(items) > limit
                or any(not isinstance(x, dict) or set(x) - {"pixelSize"} for x in items)
            ):
                raise SourceConflict("Unexpected hidden grid metadata.")
    suffix = _range_suffix(file)
    ranges = cells.get("valueRanges")
    if (
        cells.get("spreadsheetId") != file["file_id"]
        or not isinstance(ranges, list)
        or len(ranges) != 1
        or not isinstance(ranges[0], dict)
        or ranges[0].get("range")
        not in {file["title"] + suffix, "'" + file["title"] + "'" + suffix}
        or ranges[0].get("values", [])
    ):
        raise SourceConflict("Complete blank initial value readback required.")


class ManualEnrollmentEvidence(EnrollmentEvidence):
    def eligibility(self, plan, stream_id, origins=None):
        stream, records = self.transcript(plan, stream_id)
        files = plan.value()["files"]
        if len(records) != 4 * len(files):
            raise SourceConflict("Complete manual verification transcript required.")
        for i, file in enumerate(files):
            group = records[4 * i : 4 * (i + 1)]
            if [(r.operation, r.arguments) for r, _, _ in group] != list(
                manual_requests(file, version=plan.value()["version"])
            ) or any(r.target != file["file_id"] for r, _, _ in group):
                raise SourceConflict("Manual verification order/target differs.")
            manual_readback(plan, file, [body for _, body, _ in group])
        return dict(
            version=plan.value()["version"],
            origin_kind="manual",
            plan_sha256=plan.digest.hex(),
            files=files,
            stream_id=stream_id,
            closure_sha256=bytes(stream["ClosureHash"]).hex(),
        )


class ManualOutputEnrollment(OutputEnrollment):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not isinstance(self.plan, ManualEnrollmentPlan):
            raise SourceConflict("Manual plan required.")
        self.evidence = ManualEnrollmentEvidence(dal=self.dal, store=self.store)

    def run(self, *, actor, reason):
        if self.started:
            raise SourceConflict("No enrollment replay or automatic resume.")
        self.started = True
        if (
            not isinstance(actor, str)
            or not 1 <= len(actor) <= 128
            or not isinstance(reason, str)
            or not 1 <= len(reason) <= 1024
        ):
            raise SourceConflict("Bounded manual actor/reason required.")
        common = dict(
            SessionID=self.authority.session_id,
            PreparationID=str(uuid4()),
            AccountKey=self.plan.value()["account"],
            OwnerID=str(uuid4()),
        )
        claim = self.dal.transition(
            "manual_enrollment",
            Action="begin",
            ExpectedVersion=0,
            PlanJson=self.plan.sql_json,
            Actor=actor,
            Reason=reason,
            **common,
        )
        with self._stream(claim) as stream_id:
            for file in self.plan.value()["files"]:
                for operation, arguments in manual_requests(
                    file, version=self.plan.value()["version"]
                ):
                    self._request(stream_id, operation, file["file_id"], arguments)
        sealed = self.evidence.eligibility(self.plan, stream_id)
        receipt = self.store.put(encode(sealed))
        self.dal.transition(
            "manual_enrollment",
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


def verify_manual_origin(*, dal, store, rows, account, targets, owner_email, editor_email):
    if len(rows) != 2 * len(targets):
        raise SourceConflict("Complete manual registration lineage required.")
    grouped = {(r["FileID"], r["Stage"]): r for r in rows}
    if len(grouped) != len(rows) or set(grouped) != {
        (f, s) for f in targets for s in ("registered", "eligible")
    }:
        raise SourceConflict("Manual origin membership differs.")
    first = grouped[(targets[0], "registered")]
    plan = ManualEnrollmentPlan(decode(first["RequestJson"].encode()))
    v = plan.value()
    if (
        sorted(f["file_id"] for f in v["files"]) != targets
        or v["account"] != account
        or v["owner_email"] != owner_email
        or v["editor_email"] != editor_email
    ):
        raise SourceConflict("Manual origin target/owner/account differs.")
    session = dal.read_session(str(first["SessionID"]).lower())
    if (
        session is None
        or str(session["SessionID"]).lower() != str(first["SessionID"]).lower()
        or session["ProtocolVersion"] != 1
        or bytes(session["ManifestHash"]).hex() != v["manifest_sha256"]
    ):
        raise SourceConflict("Original manual registration session differs.")
    seal = None
    for ordinal, file in enumerate(v["files"]):
        registered, eligible = (grouped[(file["file_id"], s)] for s in ("registered", "eligible"))
        for row in (registered, eligible):
            if (
                row["PreparationState"] != "completed"
                or row["RequestJson"] != plan.sql_json
                or bytes(row["RequestHash"]) != plan.digest
                or bytes(row["PlanHash"]) != plan.digest
                or bytes(row["ProfileHash"]).hex() != v["credential_profile_sha256"]
                or row["PreparationID"] != first["PreparationID"]
                or row["SessionID"] != first["SessionID"]
                or row["Ordinal"] != ordinal
            ):
                raise SourceConflict("Manual registration immutable lineage differs.")
        current = decode(
            store.read_reference(eligible["EligibilityReference"], eligible["EligibilityHash"])
        )
        if (
            current.get("stream_id") != str(eligible["VerificationStreamID"]).lower()
            or current.get("closure_sha256") != bytes(eligible["VerificationClosureHash"]).hex()
            or (seal is not None and encode(current) != encode(seal))
        ):
            raise SourceConflict("Manual eligibility closure differs.")
        seal = current
    actual = ManualEnrollmentEvidence(dal=dal, store=store).eligibility(plan, seal["stream_id"])
    if encode(actual) != encode(seal):
        raise SourceConflict("Manual eligibility differs from retained readback.")
    return actual
