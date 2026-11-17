"""Fixed read-only discovery and blank-file verification for guided replacements.

The authority builds this plan from the sealed proposal and installed policy.
Admin input supplies file identities, never provider operations or grid ranges.
Every successful observation is independently replayed from the private journal.
"""

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import re

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_enrollment_service import EnrollmentEvidence, EnrollmentPlan
from services.export_execution_protocol import decode, encode, uuid_text
from services.export_manual_enrollment import (
    manual_requests,
    verify_blank_workbook,
    verify_direct_permission_details,
)

METADATA = ("sheets.get", {"includeGridData": False})
MAX_PLAN_SQL_BYTES = 2 * 1024 * 1024


def verification_plan(
    registration, proposal, *, verification_id, manifest_hash, profile_hash, project_id
):
    """Derive all destinations and access policy from the sealed admin choice."""
    value = registration.value()
    mapping = proposal["mapping"]
    configuration_targets = set(mapping) & set(
        value["legacy_configuration"]["config"]["destinations"]
    )
    policies = []
    for old, fresh in sorted(mapping.items()):
        pool = next(
            (p for p in value["pools"] if old in {p["index_file_id"], *p["slot_file_ids"]}), None
        )
        legacy = value.get("legacy_file_access", {}).get(old)
        policies.append(
            dict(
                file_id=fresh,
                audience=(
                    legacy["audience"]
                    if legacy
                    else (
                        "anyone_reader"
                        if pool and pool["audience"] == "public_viewer"
                        else "private"
                    )
                ),
                editors=legacy["editors"] if legacy else [value["service_account_email"]],
            )
        )
        if configuration_targets:
            policies[-1]["kind"] = (
                "configuration_output" if old in configuration_targets else "output"
            )
    return ReplacementVerificationPlan(
        dict(
            version=5 if configuration_targets else 4,
            purpose="output_enrollment",
            account=value["account"],
            storage_owner=value["storage_owner"],
            owner_email=proposal["owner_email"],
            editor_email=value["service_account_email"],
            project_id=project_id,
            credential_profile_sha256=profile_hash,
            manifest_sha256=manifest_hash,
            file_count=len(policies),
            plan_id=verification_id,
            replacement_id=proposal["replacement_id"],
            files=policies,
        )
    )


def discovered_grid(file_id, response):
    """Derive a bounded grid from metadata before requesting any cell content."""
    if not isinstance(response, dict) or response.get("spreadsheetId") != file_id:
        raise SourceConflict("Replacement metadata belongs to another file.")
    sheets = response.get("sheets")
    if not isinstance(sheets, list) or len(sheets) != 1:
        raise SourceConflict("Use a new spreadsheet with exactly one empty worksheet.")
    if any(response.get(k) for k in ("namedRanges", "developerMetadata", "dataSources")):
        raise SourceConflict("The replacement has existing workbook configuration.")
    tab = sheets[0]
    if not isinstance(tab, dict) or set(tab) != {"properties"}:
        raise SourceConflict("Replacement worksheet metadata is incomplete or configured.")
    props = tab["properties"]
    if not isinstance(props, dict):
        raise SourceConflict("Replacement worksheet properties are unavailable.")
    grid = props.get("gridProperties")
    if (
        not isinstance(grid, dict)
        or type(props.get("sheetId")) is not int
        or not 0 <= props["sheetId"] < 2**31
        or not isinstance(props.get("title"), str)
        or not re.fullmatch(r"[A-Za-z0-9 _-]{1,100}", props["title"])
        or props.get("sheetType", "GRID") != "GRID"
        or props.get("hidden", False) is not False
        or any(
            type(grid.get(k)) is not int or not 1 <= grid[k] <= 10000
            for k in ("rowCount", "columnCount")
        )
        or grid["rowCount"] * grid["columnCount"] > 50000
        or any(grid.get(k, 0) for k in ("frozenRowCount", "frozenColumnCount"))
    ):
        raise SourceConflict("Use one visible, unfrozen blank worksheet with at most 50,000 cells.")
    return dict(
        file_id=file_id,
        sheet_id=props["sheetId"],
        title=props["title"],
        rows=grid["rowCount"],
        columns=grid["columnCount"],
    )


def replacement_requests(file):
    """Four exact checks after metadata discovery; cell requests are bounded."""
    requests = list(manual_requests(file, version=3))
    requests[2] = ("sheets.get", {"includeGridData": True, "ranges": requests[3][1]["ranges"]})
    return tuple(requests)


def discover_replacement(policy, response):
    if policy.get("kind") == "configuration_output":
        from services.export_replacement_configuration import configuration_grids

        return configuration_grids(policy["file_id"], response)
    return discovered_grid(policy["file_id"], response)


def verification_requests(grid):
    if "configuration_grids" in grid:
        from services.export_replacement_configuration import configuration_requests

        return configuration_requests(grid)
    return replacement_requests(grid)


def file_request_count(policy):
    return 19 if policy.get("kind") == "configuration_output" else 5


@dataclass(frozen=True, init=False)
class ReplacementVerificationPlan:
    document: bytes

    def __init__(self, value):
        value = decode(encode(value))
        if set(value) != {
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
            "replacement_id",
            "files",
        }:
            raise SourceConflict("Exact replacement verification plan required.")
        if type(value["version"]) is not int or value["version"] not in (4, 5):
            raise SourceConflict("Version 4 or 5 replacement verification required.")
        # Share the established identity/profile validation; the replacement
        # count is independently checked below because legacy groups can be one file.
        identity = {k: v for k, v in value.items() if k not in {"replacement_id", "files"}}
        identity.update(version=1, file_count=3)
        EnrollmentPlan(identity)
        uuid_text(value["replacement_id"])
        files = value["files"]
        if (
            type(value["file_count"]) is not int
            or not 1 <= value["file_count"] <= 1024
            or not isinstance(files, list)
            or len(files) != value["file_count"]
        ):
            raise SourceConflict("Complete bounded replacement file list required.")
        ids = []
        for file in files:
            if (
                not isinstance(file, dict)
                or set(file)
                != (
                    {"file_id", "audience", "editors"}
                    | ({"kind"} if value["version"] == 5 else set())
                )
                or (
                    value["version"] == 5
                    and file.get("kind") not in {"output", "configuration_output"}
                )
                or not isinstance(file["file_id"], str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{6,128}", file["file_id"])
                or file["audience"] not in {"private", "anyone_reader", "anyone_writer"}
            ):
                raise SourceConflict(
                    "Exact replacement identity and installed access policy required."
                )
            from core.export_file_access_policy import validate_legacy_file_access

            validate_legacy_file_access(
                {
                    file["file_id"]: dict(
                        editors=file["editors"],
                        audience=file["audience"],
                        coordination_scope="application_writers_only",
                    )
                },
                legacy_ids={file["file_id"]},
                pool_ids=set(),
                authority_email=value["editor_email"],
            )
            if value["owner_email"] in file["editors"]:
                raise SourceConflict("Owner and Editor identities must be distinct.")
            ids.append(file["file_id"])
        if (
            len(set(ids)) != len(ids)
            or len(encode(value).decode().encode("utf-16-le")) > MAX_PLAN_SQL_BYTES
        ):
            raise SourceConflict("Replacement verification membership exceeds its bound.")
        object.__setattr__(self, "document", encode(value))

    def value(self):
        return decode(self.document)

    @property
    def verification_request_count(self):
        return sum(file_request_count(f) for f in self.value()["files"])

    @property
    def sql_json(self):
        return self.document.decode()

    @property
    def digest(self):
        return hashlib.sha256(self.sql_json.encode("utf-16-le")).digest()

    def authorize_scope(self, scope):
        phase = EnrollmentPlan.authorize_scope(self, scope)
        expected = sorted(
            ["account:" + self.value()["account"]]
            + ["destination:" + f["file_id"] for f in self.value()["files"]]
        )
        if (
            phase != dict(phase="verify", ordinal=self.value()["file_count"])
            or [r["key"] for r in decode(scope["ScopeJson"].encode())["resources"]] != expected
        ):
            raise SourceConflict("Replacement verification requires the complete proposal.")
        return phase

    def authorize_request(self, request, *, phase, ordinal):
        if (
            phase != "verify"
            or ordinal != self.value()["file_count"]
            or request.mutation
            or request.target not in {f["file_id"] for f in self.value()["files"]}
        ):
            raise SourceConflict("Replacement verification permits only scoped reads.")
        fixed = manual_requests(dict(title="Sheet1", rows=1, columns=1), version=3)[:2]
        if (request.operation, request.arguments) == METADATA or (
            request.operation,
            request.arguments,
        ) in fixed:
            return
        # ProviderRequest validates every rectangle and the 50,000-cell limit.
        # The verifier below additionally binds these ranges to observed metadata.
        if (
            request.operation == "sheets.get"
            and set(request.arguments) == {"includeGridData", "ranges"}
            and request.arguments["includeGridData"] is True
        ):
            return
        if (
            request.operation == "sheets.values.batchGet"
            and set(request.arguments) == {"ranges", "valueRenderOption", "dateTimeRenderOption"}
            and request.arguments["valueRenderOption"] == "FORMULA"
            and request.arguments["dateTimeRenderOption"] == "SERIAL_NUMBER"
        ):
            return
        raise SourceConflict("Replacement verification request differs from its fixed read policy.")


def replacement_readback(plan, policy, grid, responses):
    """Reuse blank-file checks while requiring the exact installed legacy ACL."""
    value = plan.value()
    metadata, acl, *observations = deepcopy(responses)
    permissions = acl.get("permissions")
    if not isinstance(permissions, list) or acl.get("nextPageToken"):
        raise SourceConflict("Complete replacement permissions are required.")
    expected = {("user", value["owner_email"], "owner")}
    expected.update(("user", e, "writer") for e in policy["editors"] if e != "anyone")
    if policy["audience"] != "private":
        expected.add(
            ("anyone", None, "writer" if policy["audience"] == "anyone_writer" else "reader")
        )
    seen, identifiers = set(), set()
    for permission in permissions:
        if not isinstance(permission, dict):
            raise SourceConflict("Typed replacement permissions required.")
        key = (permission.get("type"), permission.get("emailAddress"), permission.get("role"))
        identifier = permission.get("id")
        if (
            any(x is not None and not isinstance(x, str) for x in key)
            or not isinstance(identifier, str)
            or not identifier
            or identifier in identifiers
            or key not in expected
            or key in seen
            or permission.get("deleted", False) is not False
            or permission.get("pendingOwner", False) is not False
            or any(k in permission for k in ("expirationTime", "domain", "view"))
            or (key[0] == "anyone" and permission.get("allowFileDiscovery") is not False)
            or (key[0] != "anyone" and "allowFileDiscovery" in permission)
        ):
            raise SourceConflict("Replacement permissions differ from the approved access policy.")
        verify_direct_permission_details(permission, owner_email=value["owner_email"])
        seen.add(key)
        identifiers.add(identifier)
    if seen != expected:
        raise SourceConflict("Replacement is missing an approved owner, Editor or audience grant.")
    # ACL has been checked above. Existing manual validation checks all remaining
    # metadata, complete grid contents and formula readback without modifying files.
    if policy.get("kind") == "configuration_output":
        from services.export_replacement_configuration import configuration_readback

        return configuration_readback(value, grid, responses)
    sheet, cells = observations
    verify_blank_workbook(value, grid, metadata, sheet, cells)


class ReplacementVerificationEvidence(EnrollmentEvidence):
    def configuration_tables(self, plan, stream_id):
        """Reconstruct private import inputs from the same authenticated transcript."""
        from services.export_replacement_configuration import _table_values

        self.eligibility(plan, stream_id)
        _, records = self.transcript(plan, stream_id)
        result, offset = {}, 0
        for policy in plan.value()["files"]:
            count = file_request_count(policy)
            group = records[offset : offset + count]
            offset += count
            if policy.get("kind") != "configuration_output":
                continue
            grid = discover_replacement(policy, group[0][1])
            tables = {}
            for index, member in enumerate(grid["configuration_grids"]):
                if member["title"] != "Sheet1":
                    tables[member["title"]] = _table_values(
                        member["title"],
                        member,
                        group[3 + index * 2][1],
                        group[4 + index * 2][1],
                        include_rows=True,
                    )
            result[policy["file_id"]] = tables
        return result

    def eligibility(self, plan, stream_id):
        stream, records = self.transcript(plan, stream_id)
        files = []
        offset = 0
        for policy in plan.value()["files"]:
            count = file_request_count(policy)
            group = records[offset : offset + count]
            offset += count
            if len(group) != count or (group[0][0].operation, group[0][0].arguments) != METADATA:
                raise SourceConflict("Complete replacement discovery and verification required.")
            grid = discover_replacement(policy, group[0][1])
            if any(r.target != policy["file_id"] for r, _, _ in group) or [
                (r.operation, r.arguments) for r, _, _ in group[1:]
            ] != list(verification_requests(grid)):
                raise SourceConflict("Replacement reads differ from the discovered full grid.")
            summary = replacement_readback(plan, policy, grid, [body for _, body, _ in group[1:]])
            if summary is not None:
                grid["configuration_summary"] = summary
            files.append(grid)
        return dict(
            version=plan.value()["version"],
            replacement_id=plan.value()["replacement_id"],
            plan_sha256=plan.digest.hex(),
            files=files,
            stream_id=stream_id,
            closure_sha256=bytes(stream["ClosureHash"]).hex(),
        )
