"""Offline fresh-origin, credential boundary and interrupted-enrollment checks."""

from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_enrollment_service import (
    EnrollmentPlan,
    ManagedOriginVerifier,
    OutputEnrollment,
    verification_requests,
)
from services.export_execution_authority import ExecutionUncertain, ExportExecutionAuthority
from services.export_execution_protocol import (
    ProtocolError,
    ProviderRequest,
    decode,
    encode,
    enrollment_create_arguments,
)


def plan_value():
    return dict(
        version=1,
        purpose="output_enrollment",
        account="account-a",
        storage_owner="authority-a",
        owner_email="owner@example.com",
        editor_email="export@test-project.iam.gserviceaccount.com",
        project_id="test-project",
        credential_profile_sha256="c" * 64,
        manifest_sha256="d" * 64,
        file_count=3,
        plan_id=str(uuid4()),
    )


class MemoryStore:
    def __init__(self):
        self.data = {}

    def put(self, data):
        key = str(uuid4())
        self.data[key] = data
        return SimpleNamespace(key=key, sha256=hashlib.sha256(data).hexdigest())

    def read_reference(self, key, expected_hash):
        raw = self.data[str(key)]
        if hashlib.sha256(raw).digest() != bytes(expected_hash):
            raise SourceConflict("Private bytes differ")
        return raw


class MemoryDAL:
    """Fake acknowledged SQL responses, not a SQL transaction/locking simulation."""

    def __init__(self):
        self.streams, self.requests, self.events, self.origins, self.calls = {}, {}, {}, [], []
        self.claim = None
        self.fail = None

    def transition(self, kind, **v):
        self.calls.append((kind, deepcopy(v)))
        if kind == "enrollment":
            if v["Action"] == "begin":
                assert self.claim is None
                plan = EnrollmentPlan(decode(v["PlanJson"].encode()))
                self.claim = dict(
                    PreparationID=v["PreparationID"],
                    AccountKey=v["AccountKey"],
                    OwnerID=v["OwnerID"],
                    ConsumerKind="config",
                    State="preflight",
                    StorageOwner=plan.value()["storage_owner"],
                    RequestJson=v["PlanJson"],
                    RequestHash=plan.digest,
                    JobID=None,
                    SpoolKey=None,
                    Fence=1,
                    Version=1,
                    ResourcesJson=json.dumps([{"key": "account:" + v["AccountKey"], "version": 2}]),
                    GenerationJson=json.dumps(
                        dict(session_id=v["SessionID"], phase="create", next_ordinal=0)
                    ),
                )
            elif v["Action"] == "bind":
                assert v["ExpectedVersion"] == self.claim["Version"]
                stream = self.streams[v["CreationStreamID"]]
                assert stream["State"] == "closed"
                event = self.events[v["CreationRequestID"]][-1]
                self.origins.append(
                    dict(
                        FileID=v["FileID"],
                        Stage="created",
                        PreparationID=v["PreparationID"],
                        Ordinal=v["Ordinal"],
                        SessionID=v["SessionID"],
                        CreationStreamID=v["CreationStreamID"],
                        CreationRequestID=v["CreationRequestID"],
                        ResponseEventID=v["ResponseEventID"],
                        PlanHash=self.claim["RequestHash"],
                        ProfileHash=bytes.fromhex(
                            json.loads(self.claim["RequestJson"])["credential_profile_sha256"]
                        ),
                        ResponseHash=event["EvidenceHash"],
                        CreationClosureHash=stream["ClosureHash"],
                        OriginHash=v["OriginHash"],
                        OriginReference=v["OriginReference"],
                    )
                )
                resources = json.loads(self.claim["ResourcesJson"])
                resources.append(dict(key="destination:" + v["FileID"], version=2))
                self.claim["ResourcesJson"] = json.dumps(sorted(resources, key=lambda r: r["key"]))
                progress = json.loads(self.claim["GenerationJson"])
                progress["next_ordinal"] += 1
                if progress["next_ordinal"] == json.loads(self.claim["RequestJson"])["file_count"]:
                    progress["phase"] = "verify"
                self.claim["GenerationJson"] = json.dumps(progress)
                self.claim["Version"] += 1
            else:
                assert v["Action"] == "complete"
                assert all(s["State"] == "closed" for s in self.streams.values())
                assert all(e[-1]["State"] == "succeeded" for e in self.events.values())
                for row in tuple(self.origins):
                    self.origins.append(
                        row
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
                self.claim["State"] = "completed"
                self.claim["Version"] += 1
            result = self.claim
        elif kind == "stream":
            if v["Action"] == "open":
                self.streams[v["StreamID"]] = dict(
                    v,
                    PreparationID=v["ObjectID"],
                    JobID=None,
                    OutputOperationID=None,
                    Version=1,
                    LastSequence=0,
                    State="open",
                    ActiveAccountKey=v["AccountKey"],
                )
            else:
                row = self.streams[v["StreamID"]]
                assert row["Version"] == v["ExpectedVersion"]
                row.update(v, Version=row["Version"] + 1)
                row["State"] = "closed" if v["Action"] == "close" else "frozen"
                if row["State"] == "closed":
                    row["ActiveAccountKey"] = None
            result = self.streams[v["StreamID"]]
        else:
            assert kind == "event"
            row = self.streams[v["StreamID"]]
            assert row["Version"] == v["ExpectedVersion"]
            if v["State"] == "prepared":
                row["LastSequence"] += 1
                self.requests[v["RequestID"]] = dict(v, Sequence=row["LastSequence"])
                self.events[v["RequestID"]] = []
            events = self.events[v["RequestID"]]
            events.append(dict(v, EventSequence=len(events) + 1))
            row["Version"] += 1
            result = row
        if self.fail == (kind, v.get("State", v.get("Action"))):
            raise RuntimeError("Lost fake commit acknowledgment")
        return deepcopy(result)

    def read_stream(self, identifier):
        return deepcopy(self.streams.get(identifier))

    def read_session(self, identifier):
        return dict(
            SessionID=identifier,
            ProtocolVersion=1,
            ManifestHash=bytes.fromhex(json.loads(self.claim["RequestJson"])["manifest_sha256"]),
        )

    def read_request(self, identifier):
        return deepcopy(self.requests.get(identifier)), deepcopy(self.events.get(identifier, []))

    def request_ids(self, identifier):
        yield from (k for k, r in self.requests.items() if r["StreamID"] == identifier)

    def stream_digest(self, identifier):
        ids = list(self.request_ids(identifier))
        return (
            len(ids),
            hashlib.sha256(encode({k: [e["State"] for e in self.events[k]] for k in ids})).digest(),
        )

    def read_origins(self, account, targets):
        return [
            r
            | {
                k: self.claim[k]
                for k in ("AccountKey", "RequestJson", "RequestHash", "GenerationJson")
            }
            | {"PreparationState": self.claim["State"]}
            for r in deepcopy(self.origins)
            if r["FileID"] in targets
        ]


class FakeChild:
    def __init__(self, identity, runtime):
        self.identity, self.runtime = identity, runtime
        self.terminated = False

    def resume(self):
        pass

    def terminate_and_observe(self):
        if self.runtime.failure == "closure":
            raise OSError("No closure observation")
        self.terminated = True
        return dict(child_id=self.identity, process_signaled=True, job_empty=True)

    def execute(self, message):
        r = ProviderRequest.parse(message, enrollment=True)
        runtime = self.runtime
        runtime.sent.append(r)
        if runtime.failure == r.operation:
            raise TimeoutError("Lost response")
        v = runtime.plan.value()
        if r.operation == "sheets.create":
            ordinal = r.arguments["ordinal"]
            return dict(
                spreadsheetId=f"new-file-{ordinal}",
                properties=r.arguments["body"]["properties"],
                sheets=r.arguments["body"]["sheets"],
            )
        ordinal = int(r.target.rsplit("-", 1)[-1])
        if r.operation == "drive.permissions.create":
            return dict(
                id="editor-permission", type="user", role="writer", emailAddress=v["editor_email"]
            )
        if r.operation == "drive.files.get":
            return dict(
                id=r.target,
                mimeType="application/vnd.google-apps.spreadsheet",
                trashed=False,
                owners=[{"emailAddress": v["owner_email"]}],
            )
        if r.operation == "drive.permissions.list":
            return dict(
                permissions=[
                    dict(
                        id="owner-permission",
                        type="user",
                        role="owner",
                        emailAddress=v["owner_email"],
                    ),
                    dict(
                        id="editor-permission",
                        type="user",
                        role="writer",
                        emailAddress=v["editor_email"],
                    ),
                ]
            )
        if r.operation == "sheets.get":
            body = enrollment_create_arguments(v["plan_id"], ordinal)["body"]
            return dict(spreadsheetId=r.target, **body)
        return dict(spreadsheetId=r.target, valueRanges=[dict(range="Sheet1!A1:A1", values=[])])


def runtime_fixture():
    runtime = SimpleNamespace(plan=EnrollmentPlan(plan_value()), failure=None, sent=[], children=[])
    runtime.dal, runtime.store = MemoryDAL(), MemoryStore()

    def create(identity):
        child = FakeChild(identity, runtime)
        runtime.children.append(child)
        return child

    budget = Mock()
    runtime.authority = ExportExecutionAuthority(
        dal=runtime.dal,
        store=runtime.store,
        host=SimpleNamespace(create_suspended=create),
        budget_factory=lambda _: budget,
        session_id=str(uuid4()),
        enrollment_plan=runtime.plan,
    )
    runtime.runner = OutputEnrollment(
        plan=runtime.plan, authority=runtime.authority, dal=runtime.dal, store=runtime.store
    )
    return runtime


def complete(runtime):
    return runtime.runner.run(actor="operator", reason="offline fake enrollment")


def test_full_recorded_enrollment_closes_before_append_only_eligibility_and_no_registration():
    r = runtime_fixture()
    result = complete(r)
    assert len(result["origins"]) == 3 and len(r.sent) == 18
    assert all(c.terminated for c in r.children) and len(r.children) == 4
    assert [row["Stage"] for row in r.dal.origins] == ["created"] * 3 + ["eligible"] * 3
    assert {kind for kind, _ in r.dal.calls} == {"enrollment", "stream", "event"}
    assert all(
        v["Action"] in {"begin", "bind", "complete"}
        for kind, v in r.dal.calls
        if kind == "enrollment"
    )
    verified = ManagedOriginVerifier(dal=r.dal, store=r.store).verify(
        account="account-a",
        targets=["new-file-0", "new-file-1", "new-file-2"],
        owner_email=r.plan.value()["owner_email"],
        editor_email=r.plan.value()["editor_email"],
    )
    assert verified == result
    with pytest.raises(SourceConflict, match="replayed"):
        complete(r)
    assert len(r.sent) == 18


@pytest.mark.parametrize(
    "failure",
    [
        "sheets.create",
        "drive.permissions.create",
        "drive.files.get",
        "drive.permissions.list",
        "sheets.get",
        "sheets.values.batchGet",
        "closure",
        "bind",
        "complete",
        "dispatch_intent",
        "succeeded",
    ],
)
def test_interrupted_enrollment_never_replays_or_discards_ownership(failure):
    r = runtime_fixture()
    if failure in {"bind", "complete"}:
        r.dal.fail = ("enrollment", failure)
    elif failure in {"dispatch_intent", "succeeded"}:
        r.dal.fail = ("event", failure)
    else:
        r.failure = failure
    with pytest.raises((ExecutionUncertain, RuntimeError)):
        complete(r)
    original = list(r.sent)
    with pytest.raises(SourceConflict):
        complete(r)
    assert r.sent == original
    # A complete-commit acknowledgement can be lost; it must not be inferred failed.
    if failure != "complete":
        assert r.dal.claim["State"] == "preflight"
        assert not any(row["Stage"] == "eligible" for row in r.dal.origins)
    assert r.dal.claim["OwnerID"] and r.dal.claim["Fence"] > 0
    assert not any(kind == "proof" for kind, _ in r.dal.calls)


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "wrong_file",
        "wrong_request",
        "wrong_response",
        "private_bytes",
        "wrong_profile",
        "mixed_plan",
        "not_completed",
        "unknown_history",
    ],
)
def test_origin_verifier_rejects_forged_partial_or_unproven_history(damage):
    r = runtime_fixture()
    complete(r)
    created = r.dal.origins[0]
    if damage == "missing":
        r.dal.origins.pop()
    elif damage == "wrong_file":
        created["FileID"] = "old-file"
    elif damage == "wrong_request":
        created["CreationRequestID"] = str(uuid4())
    elif damage == "wrong_response":
        created["ResponseHash"] = b"z" * 32
    elif damage == "wrong_profile":
        created["ProfileHash"] = b"z" * 32
    elif damage == "mixed_plan":
        created["PreparationID"] = str(uuid4())
    elif damage == "not_completed":
        r.dal.claim["State"] = "preflight"
    elif damage == "unknown_history":
        r.dal.events[created["CreationRequestID"]][-1]["State"] = "unknown"
    else:
        r.store.data[created["OriginReference"]] = b"{}"
    with pytest.raises(SourceConflict):
        ManagedOriginVerifier(dal=r.dal, store=r.store).verify(
            account="account-a",
            targets=[f"new-file-{n}" for n in range(3)],
            owner_email=r.plan.value()["owner_email"],
            editor_email=r.plan.value()["editor_email"],
        )


@pytest.mark.parametrize(
    "change",
    [
        {"purpose": "config"},
        {"file_count": True},
        {"file_count": 2},
        {"file_count": 18},
        {"owner_email": "sa@project.iam.gserviceaccount.com"},
        {"editor_email": "other@another.iam.gserviceaccount.com"},
        {"credential_profile_sha256": "untrusted"},
        {"extra": True},
    ],
)
def test_plan_rejects_scope_or_identity_expansion(change):
    with pytest.raises((SourceConflict, ProtocolError)):
        EnrollmentPlan(plan_value() | change)


def test_ordinary_protocol_cannot_create_or_grant_editor():
    for operation, arguments, target in [
        ("sheets.create", enrollment_create_arguments(str(uuid4()), 0), str(uuid4())),
        (*verification_requests(plan_value()["editor_email"])[0], "new-file-0"),
    ]:
        message = dict(
            version=1,
            request_id=str(uuid4()),
            stream_id=str(uuid4()),
            operation=operation,
            target=target,
            arguments=arguments,
        )
        with pytest.raises(ProtocolError):
            ProviderRequest.parse(message)
        assert ProviderRequest.parse(message, enrollment=True).mutation


@pytest.mark.parametrize(
    "scopes",
    [
        None,
        [],
        ["https://www.googleapis.com/auth/drive"],
        ["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"],
    ],
)
def test_unknown_or_broad_oauth_grant_prevents_provider_send(scopes):
    from scripts.run_export_provider_child import execute_http

    request = ProviderRequest.parse(
        dict(
            version=1,
            request_id=str(uuid4()),
            stream_id=str(uuid4()),
            operation="sheets.create",
            target=str(uuid4()),
            arguments=enrollment_create_arguments(str(uuid4()), 0),
        ),
        enrollment=True,
    )
    http = Mock()
    with pytest.raises(ProtocolError, match="scope"):
        execute_http(
            request,
            session=http,
            credentials=SimpleNamespace(valid=True, granted_scopes=scopes),
            refresh_request=Mock(),
            enrollment=True,
        )
    http.request.assert_not_called()


def test_creation_uses_fixed_endpoint_and_excludes_internal_identity_arguments():
    from scripts.run_export_provider_child import execute_http

    arguments = enrollment_create_arguments(str(uuid4()), 0)
    request = ProviderRequest.parse(
        dict(
            version=1,
            request_id=str(uuid4()),
            stream_id=str(uuid4()),
            operation="sheets.create",
            target=str(uuid4()),
            arguments=arguments,
        ),
        enrollment=True,
    )
    response = Mock(status_code=200)
    response.json.return_value = dict(spreadsheetId="new-file-0", **arguments["body"])
    http = Mock()
    http.request.return_value = response
    execute_http(
        request,
        session=http,
        credentials=SimpleNamespace(
            valid=True,
            token="offline-fake",
            granted_scopes=["https://www.googleapis.com/auth/drive.file"],
        ),
        refresh_request=Mock(),
        enrollment=True,
    )
    assert http.request.call_args.args == ("POST", "https://sheets.googleapis.com/v4/spreadsheets")
    assert http.request.call_args.kwargs["params"] == {}
    assert http.request.call_args.kwargs["allow_redirects"] is False
    response.close.assert_called_once()


@pytest.mark.parametrize(
    "failure",
    [
        "owner",
        "editor",
        "public",
        "paging",
        "extra_grid",
        "nonempty",
        "unknown_grant",
        "note",
        "chart",
        "hidden_row",
    ],
)
def test_completed_http_requests_cannot_seal_wrong_private_readback(monkeypatch, failure):
    original = FakeChild.execute

    def damaged(child, message):
        result = original(child, message)
        op = message["operation"]
        if failure == "owner" and op == "drive.files.get":
            result["owners"] = [{"emailAddress": "other@example.com"}]
        elif failure == "editor" and op == "drive.permissions.create":
            result["emailAddress"] = "other@test-project.iam.gserviceaccount.com"
        elif failure == "public" and op == "drive.permissions.list":
            result["permissions"].append(dict(id="public", type="anyone", role="reader"))
        elif failure == "paging" and op == "drive.permissions.list":
            result["nextPageToken"] = "more"
        elif failure == "extra_grid" and op == "sheets.get":
            result["sheets"][0]["properties"]["gridProperties"]["rowCount"] = 2
        elif failure == "nonempty" and op == "sheets.values.batchGet":
            result["valueRanges"][0]["values"] = [["=1"]]
        elif failure == "unknown_grant" and op == "drive.permissions.list":
            result["permissions"][1]["id"] = "unrecorded-grant"
        elif failure == "note" and op == "sheets.get":
            result["sheets"][0]["data"] = [
                {"rowData": [{"values": [{"note": "retained content"}]}]}
            ]
        elif failure == "chart" and op == "sheets.get":
            result["sheets"][0]["charts"] = [{"chartId": 1}]
        elif failure == "hidden_row" and op == "sheets.get":
            result["sheets"][0]["data"] = [{"rowMetadata": [{"hiddenByUser": True}]}]
        return result

    monkeypatch.setattr(FakeChild, "execute", damaged)
    r = runtime_fixture()
    with pytest.raises(SourceConflict):
        complete(r)
    assert r.dal.claim["State"] == "preflight"
    assert all(row["Stage"] == "created" for row in r.dal.origins)
    assert all(c.terminated for c in r.children)


@pytest.mark.parametrize("damage", ["scope", "client", "type", "extra", "token_endpoint"])
def test_enrollment_credentials_reject_wrong_profile_without_refresh(damage):
    from scripts.run_export_provider_child import provider_credentials

    profile = dict(
        version=1,
        owner_email="owner@example.com",
        client_id="123-app.apps.googleusercontent.com",
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
    document = dict(
        type="authorized_user",
        client_id=profile["client_id"],
        client_secret="offline-fixture",
        refresh_token="offline-fixture",
        token_uri="https://oauth2.googleapis.com/token",
        scopes=profile["scopes"],
    )
    if damage == "scope":
        document["scopes"] = ["https://www.googleapis.com/auth/drive"]
    elif damage == "client":
        document["client_id"] = "other.apps.googleusercontent.com"
    elif damage == "type":
        document["type"] = "service_account"
    elif damage == "extra":
        document["token"] = "cached-unproven-token"
    else:
        document["token_uri"] = "https://untrusted.invalid/token"
    with pytest.raises(ValueError):
        provider_credentials(document, {"enrollment_profile": profile})


def test_entry_point_requires_explicit_operation_before_reading_files(monkeypatch):
    import scripts.enroll_export_output_pool as launcher

    reader = Mock(side_effect=AssertionError("entry point read a file before explicit operation"))
    monkeypatch.setattr(launcher.Path, "read_bytes", reader)
    with pytest.raises(SystemExit):
        launcher.main(
            [
                "--manifest",
                "not-read",
                "--plan",
                "not-read",
                "--actor",
                "operator",
                "--reason",
                "fixture",
            ]
        )
    reader.assert_not_called()


def test_old_file_cannot_pass_origin_lookup():
    r = runtime_fixture()
    with pytest.raises(SourceConflict, match="Unproven old"):
        ManagedOriginVerifier(dal=r.dal, store=r.store).verify(
            account="account-a",
            targets=["old-file-0", "old-file-1", "old-file-2"],
            owner_email="owner@example.com",
            editor_email=r.plan.value()["editor_email"],
        )


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("audience", ["private", "public_viewer"])
def test_pool_origin_binding_replays_actual_enrollment_without_any_new_request(nested, audience):
    from kvk.dal.new_source_import_dal import digest
    from kvk.services.new_source_export_service import SheetsRegistration
    from services.export_reconciliation_service import PoolOriginVerifier

    r = runtime_fixture()
    complete(r)
    value = r.plan.value()
    registration = SheetsRegistration(
        "new-file-0",
        ("new-file-1", "new-file-2"),
        value["owner_email"],
        value["editor_email"],
        audience,
    )
    context = dict(
        pool=dict(
            AccountKey=value["account"],
            IndexFileID="new-file-0",
            ExpectedOwner=value["owner_email"],
            RegistrationJson="{}",
            RegistrationHash=digest({}).hex(),
        ),
        slots=[dict(FileID=f) for f in registration.slot_file_ids],
    )
    snapshot = dict(pool=context) if nested else context
    verifier = PoolOriginVerifier(dal=r.dal, store=r.store, registration=registration)
    before = (len(r.sent), len(r.dal.calls), len(r.children), deepcopy(r.store.data))
    expected = ManagedOriginVerifier(dal=r.dal, store=r.store).verify(
        account=value["account"],
        targets=[f"new-file-{n}" for n in range(3)],
        owner_email=value["owner_email"],
        editor_email=value["editor_email"],
    )
    assert verifier.verify(snapshot=snapshot, account=value["account"]) == digest(expected).hex()
    assert before == (len(r.sent), len(r.dal.calls), len(r.children), r.store.data)


@pytest.mark.parametrize(
    "damage",
    [
        "account",
        "owner",
        "editor",
        "file",
        "index",
        "duplicate",
        "registration",
        "missing",
        "private_bytes",
    ],
)
def test_pool_origin_binding_rejects_foreign_or_unproven_lineage_without_provider(damage):
    from dataclasses import replace

    from kvk.dal.new_source_import_dal import digest
    from kvk.services.new_source_export_service import SheetsRegistration
    from services.export_reconciliation_service import PoolOriginVerifier

    r = runtime_fixture()
    complete(r)
    value = r.plan.value()
    registration = SheetsRegistration(
        "new-file-0",
        ("new-file-1", "new-file-2"),
        value["owner_email"],
        value["editor_email"],
    )
    snapshot = dict(
        pool=dict(
            AccountKey=value["account"],
            IndexFileID="new-file-0",
            ExpectedOwner=value["owner_email"],
            RegistrationJson="{}",
            RegistrationHash=digest({}).hex(),
        ),
        slots=[dict(FileID=f) for f in registration.slot_file_ids],
    )
    if damage in {"account", "owner", "index", "registration"}:
        key, replacement = {
            "account": ("AccountKey", "other-account"),
            "owner": ("ExpectedOwner", "other@example.com"),
            "index": ("IndexFileID", "other-index"),
            "registration": ("RegistrationHash", "a" * 64),
        }[damage]
        snapshot["pool"][key] = replacement
    elif damage == "editor":
        registration = replace(
            registration, service_account_email="other@test-project.iam.gserviceaccount.com"
        )
    elif damage in {"file", "duplicate"}:
        snapshot["slots"][1]["FileID"] = "other-file" if damage == "file" else "new-file-1"
    elif damage == "missing":
        r.dal.origins.clear()
    else:
        r.store.data[r.dal.origins[0]["OriginReference"]] += b" "
    before = (len(r.sent), len(r.dal.calls), len(r.children), deepcopy(r.store.data))
    verifier = PoolOriginVerifier(dal=r.dal, store=r.store, registration=registration)
    with pytest.raises(SourceConflict):
        verifier.verify(snapshot=snapshot, account=value["account"])
    assert before == (len(r.sent), len(r.dal.calls), len(r.children), r.store.data)


@pytest.mark.parametrize("replacement", [True, 1.0])
def test_origin_receipt_numeric_type_is_byte_exact_even_with_a_matching_hash(replacement):
    r = runtime_fixture()
    complete(r)
    created = r.dal.origins[1]
    data = decode(r.store.data[created["OriginReference"]])
    data["ordinal"] = replacement
    receipt = r.store.put(encode(data))
    for row in r.dal.origins:
        if row["FileID"] == created["FileID"]:
            row.update(OriginReference=receipt.key, OriginHash=bytes.fromhex(receipt.sha256))
    with pytest.raises(SourceConflict, match="Protected origin"):
        ManagedOriginVerifier(dal=r.dal, store=r.store).verify(
            account="account-a",
            targets=[f"new-file-{n}" for n in range(3)],
            owner_email=r.plan.value()["owner_email"],
            editor_email=r.plan.value()["editor_email"],
        )


@pytest.mark.parametrize(
    "change",
    [
        None,
        "owner_email",
        "editor_email",
        "project_id",
        "storage_owner",
        "manifest_sha256",
        "credential_profile_sha256",
    ],
)
def test_entry_plan_is_bound_to_exact_manifest_and_profile(change):
    from scripts.enroll_export_output_pool import approved_plan

    value = plan_value()
    profile = dict(
        version=1,
        owner_email=value["owner_email"],
        client_id="123-app.apps.googleusercontent.com",
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
    manifest = dict(
        enrollment_profile=profile,
        service_account_email=value["editor_email"],
        project_id=value["project_id"],
        storage_owner=value["storage_owner"],
    )
    raw = encode(manifest)
    value["manifest_sha256"] = hashlib.sha256(raw).hexdigest()
    value["credential_profile_sha256"] = hashlib.sha256(encode(profile)).hexdigest()
    if change:
        value[change] = {
            "owner_email": "other@example.com",
            "editor_email": "other@test-project.iam.gserviceaccount.com",
            "project_id": "other-project",
            "storage_owner": "another-owner",
            "manifest_sha256": "f" * 64,
            "credential_profile_sha256": "f" * 64,
        }[change]
        with pytest.raises((SourceConflict, ValueError)):
            approved_plan(manifest, raw, encode(value))
    else:
        assert approved_plan(manifest, raw, encode(value)).value() == value


@pytest.mark.parametrize("damage", [None, "wrong_id", "wrong_manifest", "wrong_protocol"])
def test_origin_requires_original_authority_session_identity(damage):
    r = runtime_fixture()
    complete(r)
    original = r.dal.read_session
    if damage is None:
        r.dal.read_session = lambda _: None
    else:

        def altered(identifier):
            value = original(identifier)
            key, replacement = {
                "wrong_id": ("SessionID", str(uuid4())),
                "wrong_manifest": ("ManifestHash", b"x" * 32),
                "wrong_protocol": ("ProtocolVersion", 2),
            }[damage]
            return value | {key: replacement}

        r.dal.read_session = altered
    with pytest.raises(SourceConflict, match="Origin session"):
        ManagedOriginVerifier(dal=r.dal, store=r.store).verify(
            account="account-a",
            targets=[f"new-file-{n}" for n in range(3)],
            owner_email=r.plan.value()["owner_email"],
            editor_email=r.plan.value()["editor_email"],
        )
