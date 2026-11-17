"""Opt-in real restricted-login transitions in a fresh local synthetic database.

Uses the existing guarded fixture. Full procedure bodies/roles/checks run; unrelated
table foreign keys are omitted. No provider calls or production evidence are used.
"""

import json
import os
from threading import Thread
from time import perf_counter, sleep
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from test_export_target_containment_sql import contained_job  # noqa: F401
from test_legacy_export_closeout_sql import installed  # noqa: F401

from kvk.dal.new_source_import_dal import UncertainCommit
from services.export_coordination_dal import _mutex
from services.export_execution_protocol import encode
from services.export_runtime_composition import RuntimeRegistration
from services.export_saved_result_recovery import SavedResultRecovery
from services.export_saved_result_recovery_dal import (
    RecoveryConnections,
    RecoveryWaiting,
    SavedResultRecoveryDAL,
    journal_digest,
)
from services.legacy_export_closeout import LegacyExportCloseout
from services.legacy_export_closeout_dal import LegacyExportCloseoutDAL
from services.legacy_export_snapshot_service import configuration_digest

pytestmark = pytest.mark.skipif(
    os.getenv("K98_SAVED_RESULT_SQL") != "LOCAL_SYNTHETIC_ONLY",
    reason="Explicit local synthetic SQL authorization required",
)


@pytest.mark.parametrize(
    "fault",
    ["normal", "event_reply", "stream_reply", "closeout_reply", "contention", "large_history"],
)
def test_real_saved_result_full_verification_and_restarted_closeout(
    installed, fault, tmp_path  # noqa: F811
):
    f = installed
    from core.export_execution_host import PrivateEvidenceStore

    private = tmp_path / "evidence"
    private.mkdir()
    store = PrivateEvidenceStore(private, "disk")

    def put(raw):
        marker = store.put(raw)
        return SimpleNamespace(key=str(UUID(marker.key)), sha256=marker.sha256)

    config = dict(consumer="scan_data", destinations=["old-file"])
    reg = SimpleNamespace(
        value=lambda: dict(
            account="test-account",
            storage_owner="disk",
            pools=[],
            legacy_configuration={"scan_data": config},
        )
    )
    reg.authorize_scope = lambda scope: RuntimeRegistration.authorize_scope(reg, scope)
    reg_hash = configuration_digest(config)
    f.owner.execute(
        "UPDATE dbo.ExportJob SET ProvenanceJson=?", json.dumps(dict(registration_sha256=reg_hash))
    )
    f.owner.execute(
        "UPDATE dbo.ExportExecutionStream SET State='frozen',ActiveAccountKey=AccountKey,Version=4,ClosureReference=NULL,ClosureHash=NULL,EventDigest=NULL,ClosedUTC=NULL,RegistrationHash=?",
        bytes.fromhex(reg_hash),
    )
    payload = put(
        encode(
            dict(
                version=1,
                stream_id=f.f.stream,
                request_id=f.f.request,
                operation="sheets.values.clear",
                target="old-file",
                arguments=dict(range="A1", body={}),
            )
        )
    )
    f.owner.execute(
        "UPDATE dbo.ExportProviderRequest SET Operation='sheets.values.clear',PayloadReference=?,PayloadHash=?",
        payload.key,
        bytes.fromhex(payload.sha256),
    )
    f.owner.execute("DELETE dbo.ExportProviderRequestEvent WHERE EventSequence=3")
    for index in (1, 2):
        body = dict(request_id=f.f.request)
        if index == 1:
            body["payload_hash"] = payload.sha256
        marker = put(encode(body))
        f.owner.execute(
            "UPDATE dbo.ExportProviderRequestEvent SET EvidenceReference=?,EvidenceHash=? WHERE EventSequence=?",
            marker.key,
            bytes.fromhex(marker.sha256),
            index,
        )
    response = put(
        encode(
            dict(
                request_id=f.f.request,
                response=dict(spreadsheetId="old-file", clearedRange="Sheet1!A1"),
            )
        )
    )
    count = 177 if fault == "large_history" else 1
    if count > 1:
        f.owner.execute("UPDATE dbo.ExportProviderRequest SET Sequence=?", count)
        f.owner.execute("UPDATE dbo.ExportExecutionStream SET LastSequence=?", count)
        for sequence in range(1, count):
            identifier = str(uuid4())
            raw_payload = dict(
                version=1,
                stream_id=f.f.stream,
                request_id=identifier,
                operation="sheets.values.clear",
                target="old-file",
                arguments=dict(range="A1", body={}),
            )
            payload_marker = put(encode(raw_payload))
            f.owner.execute(
                "INSERT dbo.ExportProviderRequest(RequestID,StreamID,Sequence,Operation,RequestKind,TargetID,PayloadHash,PayloadReference,CreatedUTC) VALUES(?,?,?,'sheets.values.clear','mutation','old-file',?,?,SYSUTCDATETIME())",
                identifier,
                f.f.stream,
                sequence,
                bytes.fromhex(payload_marker.sha256),
                payload_marker.key,
            )
            for ordinal, state in enumerate(("prepared", "dispatch_intent", "succeeded"), 1):
                body = dict(request_id=identifier)
                if state == "prepared":
                    body["payload_hash"] = payload_marker.sha256
                if state == "succeeded":
                    body["response"] = dict(spreadsheetId="old-file", clearedRange="Sheet1!A1")
                marker = put(encode(body))
                f.owner.execute(
                    "INSERT dbo.ExportProviderRequestEvent(EventID,RequestID,EventSequence,State,EvidenceHash,EvidenceReference,CreatedUTC) VALUES(?,?,?,?,?,?,SYSUTCDATETIME())",
                    str(uuid4()),
                    identifier,
                    ordinal,
                    state,
                    bytes.fromhex(marker.sha256),
                    marker.key,
                )
    connections = RecoveryConnections(f.connect)
    dal = LegacyExportCloseoutDAL(connections.connect, account="test-account", storage_owner="disk")
    execution = SavedResultRecoveryDAL(dal)
    assert execution.stream_digest(f.f.stream) == journal_digest(
        execution.request_records(f.f.stream)
    )
    seal = put(
        encode(
            dict(
                stream_id=f.f.stream,
                version=4,
                last_sequence=count,
                event_digest=execution.stream_digest(f.f.stream)[1].hex(),
                closure=dict(child_id=f.f.child, job_empty=True, process_signaled=True),
            )
        )
    )
    target = dict(
        job_id=f.f.job,
        owner_id=f.f.owner,
        fence=2,
        job_version=7,
        stream_id=f.f.stream,
        session_id=f.f.session,
        child_id=f.f.child,
        stream_version=4,
        last_sequence=count,
        request_id=f.f.request,
        registration_sha256=reg_hash,
        manifest_sha256=(b"m" * 32).hex(),
        response_reference=response.key,
        response_sha256=response.sha256,
        closure_reference=seal.key,
        closure_sha256=seal.sha256,
    )
    closeout = LegacyExportCloseout(dal=dal, execution=execution, store=store, registration=reg)
    from scripts.recover_stranded_export import RecoveryJournal

    journal_root = tmp_path / "journal"
    journal_root.mkdir()
    journal = RecoveryJournal(journal_root, lambda *args, **kwargs: None)
    journal.names = frozenset({"review", "intent", "closure", "closeout-intent", "verified"})

    def service():
        return SavedResultRecovery(
            closeout=closeout,
            execution=execution,
            store=store,
            journal=journal,
            check_boundary=lambda: None,
            target=target,
        )

    review = service().inspect()
    token = service().token(review)
    stages = []
    stage_costs = []
    injected = False

    def step():
        nonlocal injected
        value = service().step(review, token)
        lose = {
            "event_reply": "RESULT_RECORDED",
            "stream_reply": "STREAM_CLOSED",
            "closeout_reply": "CLOSEOUT_RECORDED",
        }
        if not injected and value["stage"] == lose.get(fault):
            injected = True
            raise UncertainCommit("deliberately discard real committed reply")
        return value

    holder = None
    releaser = None
    if fault == "contention":
        holder = f.connect()
        holder.autocommit = True
        holder.execute("BEGIN TRANSACTION")
        _mutex(holder.cursor(), "account:test-account")

        def release():
            sleep(3)
            holder.execute("ROLLBACK")

        releaser = Thread(target=release)
        releaser.start()
    started = perf_counter()
    waits = 0
    try:
        for _ in range(32):
            try:
                before_step = perf_counter()
                result = connections.checkpoint(step)
                stage_costs.append(perf_counter() - before_step)
                stages.append(result["stage"])
                if result["stage"] == "PARTIAL_EXPORT_CLOSED":
                    break
            except RecoveryWaiting:
                waits += 1
                sleep(0.25)
        else:
            pytest.fail("Native recovery failed to converge")
    finally:
        if releaser:
            releaser.join(10)
        if holder:
            holder.close()
    assert waits > 0 if fault not in {"normal", "large_history"} else waits == 0
    assert stages[-1] == "PARTIAL_EXPORT_CLOSED"
    assert (
        max(stage_costs) < 15
    )  # Per owned step, not a cancellation deadline for the whole recovery.
    print(
        {
            "case": fault,
            "seconds": round(perf_counter() - started, 3),
            "stage_seconds": [round(x, 3) for x in stage_costs],
            "waits": waits,
        }
    )
    assert service().step(review, token) == result
    assert tuple(
        f.owner.execute("SELECT State,Version FROM dbo.ExportExecutionStream").fetchone()
    ) == ("closed", 6)
    assert tuple(f.owner.execute("SELECT State,Version FROM dbo.ExportJob").fetchone()) == (
        "failed",
        8,
    )
    assert (
        f.owner.execute("SELECT COUNT(*) FROM dbo.ExportProviderRequestEvent").fetchval()
        == count * 3
    )
    assert f.owner.execute("SELECT COUNT(*) FROM dbo.ExportLegacyCloseout").fetchval() == 1
    assert (
        f.owner.execute(
            "SELECT COUNT(*) FROM dbo.ExportResource WHERE ActiveJobID IS NOT NULL"
        ).fetchval()
        == 0
    )
