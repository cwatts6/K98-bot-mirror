"""Offline manual-registration behavior; no provider, credentials or SQL connections."""

from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from test_export_enrollment_service import FakeChild, MemoryDAL, MemoryStore, plan_value

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_enrollment_service import ManagedOriginVerifier
from services.export_execution_authority import ExecutionUncertain, ExportExecutionAuthority
from services.export_execution_protocol import ProviderRequest, decode, encode
from services.export_manual_enrollment import (
    ManualEnrollmentPlan,
    ManualOutputEnrollment,
    manual_readback,
    manual_requests,
)


def manual_value():
    return plan_value() | dict(
        version=2,
        protected_file_ids=["old-protected"],
        files=[
            dict(
                file_id=f"manual-file-{i}", sheet_id=100 + i, title="Sheet1", rows=1000, columns=26
            )
            for i in range(3)
        ],
    )


def responses(plan, file):
    v = plan.value()
    return [
        dict(
            id=file["file_id"],
            mimeType="application/vnd.google-apps.spreadsheet",
            trashed=False,
            owners=[dict(emailAddress=v["owner_email"])],
            appProperties={},
            description="",
        ),
        dict(
            permissions=[
                dict(id="owner-id", type="user", role="owner", emailAddress=v["owner_email"]),
                dict(id="editor-id", type="user", role="writer", emailAddress=v["editor_email"]),
            ]
        ),
        dict(
            spreadsheetId=file["file_id"],
            sheets=[
                dict(
                    properties=dict(
                        sheetId=file["sheet_id"],
                        title="Sheet1",
                        sheetType="GRID",
                        gridProperties=dict(rowCount=1000, columnCount=26),
                    )
                )
            ],
        ),
        dict(spreadsheetId=file["file_id"], valueRanges=[dict(range="Sheet1!A1:Z1000", values=[])]),
    ]


class ManualDAL(MemoryDAL):
    def transition(self, kind, **v):
        if kind != "manual_enrollment":
            return super().transition(kind, **v)
        self.calls.append((kind, deepcopy(v)))
        if v["Action"] == "begin":
            assert self.claim is None
            plan = ManualEnrollmentPlan(decode(v["PlanJson"].encode()))
            self.claim = dict(
                PreparationID=v["PreparationID"],
                AccountKey=v["AccountKey"],
                OwnerID=v["OwnerID"],
                ConsumerKind="config",
                State="preflight",
                StorageOwner=plan.value()["storage_owner"],
                RequestJson=plan.sql_json,
                RequestHash=plan.digest,
                JobID=None,
                SpoolKey=None,
                Fence=1,
                Version=1,
                ResourcesJson=json.dumps(
                    sorted(
                        [dict(key="account:" + v["AccountKey"], version=2)]
                        + [
                            dict(key="destination:" + f["file_id"], version=2)
                            for f in plan.value()["files"]
                        ],
                        key=lambda r: r["key"],
                    )
                ),
                GenerationJson=json.dumps(
                    dict(session_id=v["SessionID"], phase="verify", next_ordinal=3)
                ),
            )
            for i, f in enumerate(plan.value()["files"]):
                self.origins.append(
                    dict(
                        FileID=f["file_id"],
                        Stage="registered",
                        Ordinal=i,
                        PreparationID=v["PreparationID"],
                        SessionID=v["SessionID"],
                        PlanHash=plan.digest,
                        ProfileHash=bytes.fromhex(plan.value()["credential_profile_sha256"]),
                    )
                )
        else:
            assert v["Action"] == "complete" and v["ExpectedVersion"] == self.claim["Version"]
            assert all(s["State"] == "closed" for s in self.streams.values())
            for r in tuple(self.origins):
                self.origins.append(
                    r
                    | dict(
                        Stage="eligible",
                        VerificationStreamID=v["VerificationStreamID"],
                        VerificationClosureHash=self.streams[v["VerificationStreamID"]][
                            "ClosureHash"
                        ],
                        EligibilityHash=v["EligibilityHash"],
                        EligibilityReference=v["EligibilityReference"],
                    )
                )
            self.claim.update(State="completed", Version=2)
        if self.fail == (kind, v["Action"]):
            raise RuntimeError("Lost SQL acknowledgement")
        return deepcopy(self.claim)


class ManualChild(FakeChild):
    def execute(self, message):
        request = ProviderRequest.parse(
            message
        )  # ordinary service-account child, no creation capability
        self.runtime.sent.append(request)
        if self.runtime.failure == request.operation:
            raise TimeoutError("Uncertain read")
        file = next(f for f in self.runtime.plan.value()["files"] if f["file_id"] == request.target)
        index = [op for op, _ in manual_requests(file)].index(request.operation)
        return responses(self.runtime.plan, file)[index]


def runtime():
    r = SimpleNamespace(
        plan=ManualEnrollmentPlan(manual_value()),
        dal=ManualDAL(),
        store=MemoryStore(),
        sent=[],
        children=[],
        failure=None,
    )

    def create(identity):
        child = ManualChild(identity, r)
        r.children.append(child)
        return child

    r.authority = ExportExecutionAuthority(
        dal=r.dal,
        store=r.store,
        host=SimpleNamespace(create_suspended=create),
        budget_factory=lambda _: Mock(),
        session_id=str(uuid4()),
        enrollment_plan=r.plan,
    )
    r.runner = ManualOutputEnrollment(plan=r.plan, authority=r.authority, dal=r.dal, store=r.store)
    return r


def test_manual_register_then_restart_verification_reuses_ids_without_provider_calls():
    r = runtime()
    seal = r.runner.run(actor="admin", reason="one-time manual setup")
    assert seal["origin_kind"] == "manual" and len(r.sent) == 12
    assert all(not q.mutation for q in r.sent)
    assert len(r.children) == 1 and r.children[0].terminated
    targets = sorted(f["file_id"] for f in r.plan.value()["files"])
    # Multiple later verification/export-admission checks consume the retained registration.
    for _ in range(2):
        assert (
            ManagedOriginVerifier(dal=r.dal, store=r.store).verify(
                account="account-a",
                targets=targets,
                owner_email="owner@example.com",
                editor_email="export@test-project.iam.gserviceaccount.com",
            )
            == seal
        )
    assert len(r.sent) == 12
    with pytest.raises(SourceConflict, match="replay"):
        r.runner.run(actor="admin", reason="second setup")


@pytest.mark.parametrize(
    "failure", ["drive.files.get", "sheets.get", "closure", "begin", "complete"]
)
def test_manual_uncertainty_never_retries_or_releases_unconfirmed_claim(failure):
    r = runtime()
    if failure in {"begin", "complete"}:
        r.dal.fail = ("manual_enrollment", failure)
    else:
        r.failure = failure
    with pytest.raises((ExecutionUncertain, RuntimeError)):
        r.runner.run(actor="admin", reason="setup")
    count = len(r.sent)
    with pytest.raises(SourceConflict):
        r.runner.run(actor="admin", reason="retry")
    assert len(r.sent) == count
    if failure not in {"complete"}:
        assert not any(o["Stage"] == "eligible" for o in r.dal.origins)


@pytest.mark.parametrize(
    "damage",
    [
        "owner",
        "extra_editor",
        "public",
        "inheritance",
        "pagination",
        "content",
        "grid",
        "range",
        "metadata",
    ],
)
def test_wrong_or_incomplete_initial_readback_blocks_registration(damage):
    plan = ManualEnrollmentPlan(manual_value())
    f = plan.value()["files"][0]
    r = responses(plan, f)
    if damage == "owner":
        r[0]["owners"][0]["emailAddress"] = "wrong@example.com"
    elif damage == "extra_editor":
        r[1]["permissions"].append(dict(id="extra", type="user", role="writer"))
    elif damage == "public":
        r[1]["permissions"][1]["type"] = "anyone"
    elif damage == "inheritance":
        r[1]["permissions"][1]["permissionDetails"] = [dict(inherited=True)]
    elif damage == "pagination":
        r[1]["nextPageToken"] = "more"
    elif damage == "content":
        r[3]["valueRanges"][0]["values"] = [["retain this"]]
    elif damage == "grid":
        r[2]["sheets"][0]["properties"]["sheetId"] = 99
    elif damage == "range":
        r[3]["valueRanges"][0]["range"] = "Sheet1!A1:A1"
    else:
        r[2]["sheets"][0]["merges"] = [{}]
    with pytest.raises(SourceConflict):
        manual_readback(plan, f, r)


@pytest.mark.parametrize("damage", ["duplicate", "protected", "huge", "version", "unknown"])
def test_manual_manifest_refuses_ambiguous_or_excessive_targets(damage):
    v = manual_value()
    if damage == "duplicate":
        v["files"][1] = v["files"][0]
    elif damage == "protected":
        v["protected_file_ids"] = [v["files"][0]["file_id"]]
    elif damage == "huge":
        v["files"][0]["rows"] = 10000
        v["files"][0]["columns"] = 10000
    elif damage == "version":
        v["version"] = 1
    else:
        v["unexpected"] = True
    with pytest.raises(SourceConflict):
        ManualEnrollmentPlan(v)


def test_manual_authority_rejects_sharing_mutation_before_dispatch():
    r = runtime()
    r.runner.run(actor="admin", reason="setup")
    request = SimpleNamespace(
        target="manual-file-0", mutation=True, operation="drive.permissions.create", arguments={}
    )
    with pytest.raises(SourceConflict):
        r.plan.authorize_request(request, phase="verify", ordinal=3)


@pytest.mark.parametrize("damage", ["plan", "ordinal", "session", "seal", "incomplete"])
def test_manual_retained_lineage_rejects_damage(damage):
    r = runtime()
    r.runner.run(actor="admin", reason="setup")
    if damage == "plan":
        r.dal.origins[0]["PlanHash"] = bytes(32)
    elif damage == "ordinal":
        r.dal.origins[0]["Ordinal"] = 2
    elif damage == "session":
        r.dal.origins[0]["SessionID"] = str(uuid4())
    elif damage == "seal":
        r.dal.origins[-1]["EligibilityHash"] = bytes(32)
    else:
        r.dal.origins.pop()
    with pytest.raises(SourceConflict):
        ManagedOriginVerifier(dal=r.dal, store=r.store).verify(
            account="account-a",
            targets=sorted(f["file_id"] for f in r.plan.value()["files"]),
            owner_email="owner@example.com",
            editor_email="export@test-project.iam.gserviceaccount.com",
        )


@pytest.mark.parametrize(
    "damage", [None, "owner", "target", "exclusions", "credential", "manifest", "oauth"]
)
def test_entry_binds_manual_plan_to_runtime_registration_and_existing_credentials(damage):
    from test_export_runtime_composition import registration_fixture

    from scripts.enroll_export_output_pool import approved_plan
    from services.export_manual_enrollment import manual_profile

    registration = registration_fixture()
    v = manual_value()
    v.update(
        editor_email=registration["service_account_email"],
        project_id="example",
        storage_owner=registration["storage_owner"],
        protected_file_ids=registration["protected_file_ids"],
    )
    pool = registration["pools"][0]
    for f, identifier in zip(
        v["files"], [pool["index_file_id"], *pool["slot_file_ids"]], strict=True
    ):
        f["file_id"] = identifier
    manifest = dict(
        runtime_registration=registration,
        service_account_email=v["editor_email"],
        project_id=v["project_id"],
        storage_owner=v["storage_owner"],
        deployment_boundary=dict(
            identity=dict(client_id="123", private_key_id="key-id", credential_sha256="a" * 64)
        ),
    )
    raw = encode(manifest)
    v.update(
        manifest_sha256=hashlib.sha256(raw).hexdigest(),
        credential_profile_sha256=hashlib.sha256(encode(manual_profile(manifest))).hexdigest(),
    )
    if damage == "owner":
        v["owner_email"] = "other@example.com"
    elif damage == "target":
        v["files"][0]["file_id"] = "unapproved-file"
    elif damage == "exclusions":
        v["protected_file_ids"] = []
    elif damage == "credential":
        v["credential_profile_sha256"] = "0" * 64
    elif damage == "manifest":
        v["manifest_sha256"] = "0" * 64
    elif damage == "oauth":
        manifest["enrollment_profile"] = {}
    if damage:
        with pytest.raises((SourceConflict, ValueError)):
            approved_plan(manifest, raw, encode(v))
    else:
        assert approved_plan(manifest, raw, encode(v)).value() == v


@pytest.mark.parametrize(
    "damage", [None, "invented_issuance", "extra_key", "old_record", "previous_identity"]
)
def test_existing_identity_record_is_explicitly_versioned_and_keeps_custody_checks(
    tmp_path, damage
):
    from test_export_single_account import shared_deployment

    from core.export_execution_host import DeploymentBoundary, HostBoundaryError

    manifest, records, reads = shared_deployment(tmp_path)
    boundary = manifest["deployment_boundary"]
    boundary["version"] = 3
    boundary["identity"].pop("previous_service_account_email")
    if damage == "previous_identity":
        boundary["identity"]["previous_service_account_email"] = manifest["service_account_email"]
    row = records["identity_issuance"]["observations"][0]
    row.pop("created_utc")
    row["observed_utc"] = row.pop("issued_utc")
    row["reviewing_administrator"] = row.pop("issuing_administrator")
    row["provenance"] = "existing"
    if damage == "invented_issuance":
        row["created_utc"] = row["observed_utc"]
    if damage == "extra_key":
        records["key_inventory"]["observations"][0]["user_managed_key_ids"].append("unknown-key")
    for kind, record in records.items():
        record["version"] = 2 if damage == "old_record" else 3
        reference = boundary["review"]["records"][kind]
        from pathlib import Path

        Path(reference["path"]).write_bytes(encode(record))
        reference["sha256"] = hashlib.sha256(encode(record)).hexdigest()
    if damage:
        with pytest.raises(HostBoundaryError):
            DeploymentBoundary(manifest, **reads)
    else:
        DeploymentBoundary(manifest, **reads).recheck()
