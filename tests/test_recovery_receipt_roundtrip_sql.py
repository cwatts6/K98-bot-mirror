"""Real ODBC -> recovery service -> SQL -> restarted readback, without providers."""

import hashlib
import json
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from test_export_target_containment_sql import contained_job  # noqa: F401
from test_legacy_export_closeout_sql import event, installed, next_job, open_stream  # noqa: F401

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.config_preparation_recovery_dal import ConfigPreparationRecoveryDAL
from services.config_preparation_recovery_service import RecoveryTarget
from services.config_read_containment import ConfigReadContainment
from services.export_coordination_dal import identity
from services.export_execution_dal import ExportExecutionDAL
from services.export_execution_protocol import encode
from services.export_runtime_composition import RuntimeRegistration
from services.export_target_containment import ExportTargetContainment
from services.export_target_containment_dal import ExportTargetContainmentDAL
from services.legacy_export_closeout import ACTION, LegacyExportCloseout
from services.legacy_export_closeout_dal import LegacyExportCloseoutDAL
from services.legacy_export_snapshot_service import configuration_digest

pytestmark = pytest.mark.skipif(
    os.getenv("K98_LEGACY_CLOSEOUT_SQL") != "1", reason="Explicit disposable SQL opt-in"
)


@pytest.fixture
def recovery(installed):  # noqa: F811
    f = installed
    documents = {}

    def put(raw):
        key = str(uuid4())
        documents[key] = raw
        return SimpleNamespace(key=key, sha256=hashlib.sha256(raw).hexdigest())

    def read(reference, expected):
        raw = documents[identity(reference)]
        if hashlib.sha256(raw).digest() != bytes(expected):
            raise SourceConflict("Private hash mismatch")
        return raw

    store = SimpleNamespace(put=put, read_reference=read)
    targets = sorted(["old-file", *(f"unchanged-File-{i:02}" for i in range(10))])
    config = dict(consumer="scan_data", destinations=targets)
    registration_hash = configuration_digest(config)
    registration = SimpleNamespace(
        value=lambda: dict(
            account="test-account",
            storage_owner="disk",
            pools=[],
            legacy_configuration={"scan_data": config},
        )
    )
    registration.authorize_scope = lambda scope: RuntimeRegistration.authorize_scope(
        registration, scope
    )
    for name in targets:
        if name == "old-file":
            continue
        f.owner.execute(
            "INSERT dbo.ExportResource(ResourceKey,ResourceKind,ActiveJobID,OwnerID,Fence,Version) "
            "VALUES (?,'destination',?,?,2,3)",
            "destination:" + name,
            f.f.job,
            f.f.owner,
        )
        f.owner.execute("INSERT dbo.ExportJobResource VALUES (?,?)", f.f.job, "destination:" + name)
    membership = ["account:test-account", *("destination:" + t for t in targets)]
    f.f.resources[:] = [dict(key=k, version=3) for k in membership]
    f.owner.execute(
        "UPDATE dbo.ExportJob SET DestinationSetHash=?,ProvenanceJson=?",
        digest(targets),
        json.dumps(dict(registration_sha256=registration_hash)),
    )
    f.owner.execute(
        "UPDATE dbo.ExportExecutionStream SET RegistrationHash=?,ScopeJson=?",
        bytes.fromhex(registration_hash),
        json.dumps(dict(resources=[dict(key=k, version=3) for k in membership])),
    )
    execution = ExportExecutionDAL(f.connect)
    raw_stream = execution.read_stream(f.f.stream)
    payload = dict(
        version=1,
        stream_id=f.f.stream,
        request_id=f.f.request,
        operation="sheets.values.clear",
        target="old-file",
        arguments={"range": "A1", "body": {}},
    )
    saved = put(encode(payload))
    f.owner.execute(
        "UPDATE dbo.ExportProviderRequest SET Operation=?,PayloadHash=?,PayloadReference=?",
        payload["operation"],
        bytes.fromhex(saved.sha256),
        saved.key,
    )
    for index, state in enumerate(("prepared", "dispatch_intent", "succeeded"), 1):
        body = dict(request_id=f.f.request)
        if state == "prepared":
            body["payload_hash"] = saved.sha256
        if state == "succeeded":
            body["response"] = dict(spreadsheetId="old-file", clearedRange="Sheet1!A1")
        receipt = put(encode(body))
        f.owner.execute(
            "UPDATE dbo.ExportProviderRequestEvent SET EvidenceHash=?,EvidenceReference=? "
            "WHERE EventSequence=?",
            bytes.fromhex(receipt.sha256),
            receipt.key,
            index,
        )
    sequence, event_digest = execution.stream_digest(f.f.stream)
    closure = put(
        encode(
            dict(
                stream_id=f.f.stream,
                version=raw_stream["Version"] - 1,
                last_sequence=sequence,
                event_digest=event_digest.hex(),
                closure=dict(
                    child_id=identity(raw_stream["ChildIdentity"]),
                    job_empty=True,
                    process_signaled=True,
                ),
            )
        )
    )
    f.owner.execute(
        "UPDATE dbo.ExportExecutionStream SET ClosureHash=?,ClosureReference=?,EventDigest=?",
        bytes.fromhex(closure.sha256),
        closure.key,
        event_digest,
    )
    source = (f.root / "sql_schema/dbo.usp_ExportJobContainTargets.StoredProcedure.sql").read_text(
        encoding="utf-8-sig"
    )
    f.owner.execute(source[source.index("CREATE PROCEDURE") :].strip().removesuffix("GO").strip())
    f.owner.execute("GRANT EXECUTE ON dbo.usp_ExportJobContainTargets TO ExportExecutionAuthority")
    dal = LegacyExportCloseoutDAL(f.connect, account="test-account", storage_owner="disk")
    containment = ExportTargetContainment(
        dal=ExportTargetContainmentDAL(f.connect),
        discovery=SimpleNamespace(job=lambda job: dict(job=dal.snapshot(job)["job"])),
        execution=execution,
        store=store,
        registration=registration,
    )
    report = containment.inspect(f.f.job)
    containment.apply(
        f.f.job,
        token=report["token"],
        actor="recovery:" + str(uuid4()),
        reason="Synthetic containment",
    )
    service = LegacyExportCloseout(
        dal=dal, execution=execution, store=store, registration=registration
    )
    return SimpleNamespace(
        f=f,
        dal=dal,
        execution=execution,
        store=store,
        service=service,
        targets=targets,
        documents=documents,
    )


def configuration_read(r):
    f = r.f
    preparation, owner = str(uuid4()), str(uuid4())
    request = dict(read_configuration=str(uuid4()))
    f.owner.execute(
        "INSERT dbo.ExportPreparation (PreparationID,AccountKey,ConsumerKind,RequestHash,EnqueueSequence,State,OwnerID,Fence,Version,StorageOwner,RequestJson,Actor,Reason,CreatedUTC,UpdatedUTC) "
        "VALUES (?,'test-account','config',?,2,'uncertain',?,3,3,'disk',?,'test','abandoned read',SYSUTCDATETIME(),SYSUTCDATETIME())",
        preparation,
        digest(request),
        owner,
        json.dumps(request),
    )
    f.owner.execute(
        "INSERT dbo.ExportPreparationResource SELECT ?,ResourceKey FROM dbo.ExportJobResource",
        preparation,
    )
    f.owner.execute(
        "UPDATE dbo.ExportResource SET ActivePreparationID=?,OwnerID=?,Fence=3,Version=5,"
        "BlockedReason='Preparation requires authoritative reconciliation'",
        preparation,
        owner,
    )
    # Existing DAL needs only these two updates, never evidence-table writes.
    for table in ("ExportPreparation", "ExportResource"):
        f.owner.execute(f"REVOKE UPDATE ON dbo.{table} FROM ExportExecutionAuthority")
        f.owner.execute(f"GRANT UPDATE ON dbo.{table} TO ExportExecutionAuthority")
    dal = ConfigPreparationRecoveryDAL(f.connect)
    data = dal.target_data(preparation, account="test-account", storage_owner="disk")
    sql_identity = dal.identity()
    target = RecoveryTarget(
        sql_identity["server"],
        sql_identity["database"],
        preparation,
        "test-account",
        data["preparation"]["OwnerID"],
        3,
        3,
        tuple((row["ResourceKey"], row["Version"]) for row in data["resources"]),
        tuple(data["stream_ids"]),
    )
    return ConfigReadContainment(
        dal=dal,
        execution=r.execution,
        store=r.store,
        target=target,
        registration_hash=(b"r" * 32).hex(),
        storage_owner="disk",
    )


def test_real_receipts_configuration_settlement_closeout_restart_and_same_urls(recovery):
    r, f = recovery, recovery.f
    # SQL ODBC GUID strings and private JSON UUIDs have different casing.
    raw = f.app.execute(
        "SELECT ContainmentID,ReceiptReference FROM dbo.ExportTargetContainment"
    ).fetchone()
    snapshot = r.dal.snapshot(f.f.job)
    assert snapshot["receipt"]["ContainmentID"] == identity(raw[0])
    assert snapshot["receipt"]["ReceiptReference"] == identity(raw[1])
    before = {
        t: [tuple(row) for row in f.owner.execute("SELECT * FROM dbo." + t)]
        for t in (
            "ExportExecutionStream",
            "ExportProviderRequest",
            "ExportProviderRequestEvent",
            "ExportContainedTarget",
        )
    }
    report = configuration_read(r)
    assert ACTION not in r.service.inspect(f.f.job)[0]["actions"]
    decision = report.inspect()
    assert decision["snapshot"]["streams"] == []
    report.apply(
        approved_snapshot_sha256=decision["snapshot_sha256"],
        actor="test-admin",
        reason="Discard abandoned read",
    )
    assert f.app.execute("SELECT State FROM dbo.ExportPreparation").fetchval() == "unavailable"
    assert f.app.execute("SELECT COUNT(*) FROM dbo.ExportActiveContainedTarget").fetchval() == 11
    evidence, token, done = r.service.inspect(f.f.job)
    assert not done and ACTION in evidence["actions"], evidence
    action = dict(
        ActionID=str(uuid4()),
        ActionKind=ACTION,
        EvidenceHash=token,
        Reason="Next scan uses same URLs",
    )
    r.service.execute(f.f.job, ACTION, token, "recovery:" + action["ActionID"], action["Reason"])
    restarted = LegacyExportCloseout(
        dal=r.dal, execution=r.execution, store=r.store, registration=r.service.registration
    )
    assert restarted.reconcile(f.f.job, action) == "verified"
    assert restarted.inspect(f.f.job)[2]
    assert f.app.execute("SELECT COUNT(*) FROM dbo.ExportActiveContainedTarget").fetchval() == 0
    for table, original in before.items():
        assert [tuple(row) for row in f.owner.execute("SELECT * FROM dbo." + table)] == original
    after = r.dal.snapshot(f.f.job)
    for key in ("InputHash", "SpoolKey", "ProvenanceJson", "DestinationSetHash"):
        assert after["job"][key] == snapshot["job"][key]
    later_job, later_owner = next_job(f)
    later_stream = open_stream(f, later_job, later_owner)
    event(f, later_stream, str(uuid4()), "prepared", 1)
    assert (
        f.app.execute(
            "SELECT COUNT(*) FROM dbo.ExportJobResource WHERE JobID=?", later_job
        ).fetchval()
        == 12
    )


@pytest.mark.parametrize("state", ["open", "frozen"])
def test_live_foreign_stream_still_blocks_configuration_recovery(recovery, state):
    r, f = recovery, recovery.f
    report = configuration_read(r)
    f.owner.execute(
        "UPDATE dbo.ExportExecutionStream SET State=?,ActiveAccountKey=AccountKey,"
        "ClosureHash=NULL,ClosureReference=NULL,EventDigest=NULL,ClosedUTC=NULL",
        state,
    )
    with pytest.raises(SourceConflict, match="membership changed"):
        report.inspect()
    assert f.app.execute("SELECT State FROM dbo.ExportPreparation").fetchval() == "uncertain"


def test_bad_containment_receipt_remains_blocked(recovery):
    r = recovery
    snapshot = r.dal.snapshot(r.f.f.job)
    reference = snapshot["receipt"]["ReceiptReference"]
    r.documents[reference] += b" "
    evidence, _, resolved = r.service.inspect(r.f.f.job)
    assert not resolved and not evidence["actions"]


def test_terminal_foreign_stream_does_not_join_configuration_membership(recovery):
    report = configuration_read(recovery)
    before = recovery.dal.snapshot(recovery.f.f.job)
    decision = report.inspect()
    assert decision["snapshot"]["streams"] == []
    assert recovery.dal.snapshot(recovery.f.f.job) == before
