"""Opt-in P03a.2 qualification using only the guarded local synthetic SQL fixture."""

from copy import deepcopy
import hashlib
import json
import os
from threading import Thread
from time import perf_counter, sleep
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from test_export_target_containment_sql import contained_job  # noqa: F401
from test_legacy_export_closeout_sql import installed  # noqa: F401

from core.export_execution_host import PrivateEvidenceStore
from services.export_coordination_dal import _mutex
from services.export_execution_dal import ExportExecutionDAL
from services.export_execution_progress import ExecutionProgress
from services.export_execution_protocol import ProviderRequest, encode
from services.export_request_settlement import RequestSettlement

pytestmark = pytest.mark.skipif(
    os.getenv("K98_REQUEST_SETTLEMENT_SQL") != "LOCAL_SYNTHETIC_ONLY",
    reason="Explicit local synthetic SQL authorization required",
)


@pytest.mark.parametrize(
    "fault",
    [
        "normal",
        "event_reply",
        "pacing_reply",
        "account_contention",
        "budget_contention",
        "restart_freeze_reply",
        "restart_close_reply",
    ],
)
def test_native_result_settlement_and_passive_poll(installed, tmp_path, fault):  # noqa: F811
    f = installed
    store = PrivateEvidenceStore(tmp_path, "disk")
    f.owner.execute(
        (f.root / "sql_schema/dbo.ExportRequestBudget.Table.sql").read_text(encoding="utf-8-sig")
    )
    # Match the installed application profile's direct budget permissions;
    # journal/resource writes remain denied to this restricted fixture principal.
    f.owner.execute("GRANT SELECT,INSERT,UPDATE ON dbo.ExportRequestBudget TO CloseoutAuthority")
    f.owner.execute(
        "INSERT dbo.ExportRequestBudget(AccountKey,BudgetKind,NextAllowedUTC,IntervalMilliseconds,PolicyVersion,Version) VALUES('test-account','google_request',SYSUTCDATETIME(),2100,1,1)"
    )
    f.owner.execute(
        "UPDATE dbo.ExportExecutionStream SET State='open',ActiveAccountKey=AccountKey,Version=3,ClosureReference=NULL,ClosureHash=NULL,EventDigest=NULL,ClosedUTC=NULL"
    )
    f.owner.execute("DELETE dbo.ExportProviderRequestEvent WHERE EventSequence=3")
    message = dict(
        version=1,
        request_id=f.f.request,
        stream_id=f.f.stream,
        operation="sheets.values.clear",
        target="old-file",
        arguments=dict(range="A1", body={}),
    )
    payload = store.put(encode(message))
    f.owner.execute(
        "UPDATE dbo.ExportProviderRequest SET Operation='sheets.values.clear',PayloadReference=?,PayloadHash=?",
        str(UUID(payload.key)),
        bytes.fromhex(payload.sha256),
    )
    for sequence in (1, 2):
        body = dict(request_id=f.f.request)
        if sequence == 1:
            body["payload_hash"] = payload.sha256
        receipt = store.put(encode(body))
        f.owner.execute(
            "UPDATE dbo.ExportProviderRequestEvent SET EvidenceReference=?,EvidenceHash=? WHERE EventSequence=?",
            str(UUID(receipt.key)),
            bytes.fromhex(receipt.sha256),
            sequence,
        )
    execution = ExportExecutionDAL(f.connect)
    if fault.startswith("restart_"):
        host = dict(
            child_id=f.f.child,
            pid=123,
            job_name="Global\\K98ExportChild-" + "a" * 64,
            machine=dict(machine_guid=str(uuid4()), hostname="fixture-host"),
            authority_sid="S-1-5-21-1",
            limit_flags=0x2000,
            assigned=True,
        )
        birth = store.put(
            encode(
                dict(
                    kind="provider_child_birth/1",
                    stream_id=f.f.stream,
                    session_id=f.f.session,
                    account="test-account",
                    host=host,
                )
            )
        )
        scope = json.loads(execution.read_stream(f.f.stream)["ScopeJson"])
        scope["host_birth"] = dict(reference=str(UUID(birth.key)), sha256=birth.sha256)
        f.owner.execute("UPDATE dbo.ExportExecutionStream SET ScopeJson=?", json.dumps(scope))
        f.owner.execute(
            "UPDATE dbo.ExportExecutionSession SET HostIdentity='fixture-host',ManifestHash=?",
            b"m" * 32,
        )
    service = RequestSettlement(execution, store, check_boundary=lambda: None)
    predecessor = deepcopy(execution.read_stream(f.f.stream))
    predecessor.update(Version=1, LastSequence=0)
    locator = service.prepare(ProviderRequest.parse(message), payload, predecessor)
    service.save(locator, dict(spreadsheetId="old-file", clearedRange="A1"))
    # A fresh service has no original caller, worker, receipt or provider child.
    service = RequestSettlement(execution, store, check_boundary=lambda: None)
    transition = service.execution.transition
    completed = service.complete_request
    lost = []

    def event(*args, **kwargs):
        result = transition(*args, **kwargs)
        if not lost and (
            fault == "event_reply"
            or (fault == "restart_freeze_reply" and kwargs.get("Action") == "freeze")
            or (fault == "restart_close_reply" and kwargs.get("Action") == "close")
        ):
            lost.append(True)
            raise OSError("synthetic committed reply loss")
        return result

    def pacing(account):
        completed(account)
        if fault == "pacing_reply" and not lost:
            lost.append(True)
            raise RuntimeError("08S01", "synthetic committed budget reply loss")

    service.execution.transition, service.complete_request = event, pacing
    before_job = tuple(
        f.owner.execute("SELECT State,Version,OwnerID,Fence FROM dbo.ExportJob").fetchone()
    )
    before_resources = [
        tuple(row)
        for row in f.owner.execute(
            "SELECT ResourceKey,ActiveJobID,OwnerID,Fence,Version FROM dbo.ExportResource ORDER BY ResourceKey"
        )
    ]
    holder = releaser = None
    if fault.endswith("contention"):
        holder = f.connect()
        holder.autocommit = True
        holder.execute("BEGIN TRANSACTION")
        cursor = holder.cursor()
        _mutex(
            cursor, ("account:" if fault == "account_contention" else "budget:") + "test-account"
        )
        cursor.close()

        def release():
            sleep(3)
            holder.execute("ROLLBACK")

        releaser = Thread(target=release)
        releaser.start()

    def settle(selector, notify):
        if fault.startswith("restart_"):
            from services.export_saved_result_restart import SavedResultRestart

            def retired(birth):
                return dict(
                    child_id=birth["child_id"],
                    pid=birth["pid"],
                    job_empty=True,
                    process_terminated=True,
                    termination_method="named_job_destroyed",
                    job_name_sha256=hashlib.sha256(birth["job_name"].encode()).hexdigest(),
                )

            recovery = SavedResultRestart(
                service, account="test-account", hostname="fixture-host", observe_retired=retired
            )
            assert recovery((b"m" * 32).hex(), SimpleNamespace(verify=lambda: None)) == [f.f.stream]
            assert execution.read_stream(f.f.stream)["State"] == "closed"
            result = dict(restarted=True)
        else:
            result = service.run(selector["request_id"], progress=notify)
        assert service.connections.opened and all(
            connection.closed for connection in service.connections.opened
        )
        return result

    progress = ExecutionProgress(settle)
    selector = dict(action="settlement", request_id=f.f.request)
    started, costs, states = perf_counter(), [], []
    try:
        progress.start(f.f.request, "test-account", selector)
        while perf_counter() - started < 25:
            before = perf_counter()
            value = progress.poll(f.f.request, selector)
            costs.append(perf_counter() - before)
            states.append(value["state"])
            if value["state"] in {"complete", "unavailable"}:
                break
            sleep(0.05)
        assert value["state"] == "complete", value
        assert value["needs_attention"] is False
        if fault.startswith("restart_"):
            assert value["result"] == dict(restarted=True)
        else:
            assert value["result"]["response"]["spreadsheetId"] == "old-file"
        assert max(costs) < 0.1
        if fault == "account_contention":
            assert "waiting" in states
        _, events = execution.read_request(f.f.request)
        assert [row["State"] for row in events] == ["prepared", "dispatch_intent", "succeeded"]
        assert (
            tuple(
                f.owner.execute("SELECT State,Version,OwnerID,Fence FROM dbo.ExportJob").fetchone()
            )
            == before_job
        )
        assert [
            tuple(row)
            for row in f.owner.execute(
                "SELECT ResourceKey,ActiveJobID,OwnerID,Fence,Version FROM dbo.ExportResource ORDER BY ResourceKey"
            )
        ] == before_resources
        print(
            "P03A2_QUALIFICATION "
            + json.dumps(
                dict(
                    fault=fault,
                    elapsed_seconds=round(perf_counter() - started, 3),
                    max_status_ms=round(max(costs) * 1000, 3),
                    terminal_events=1,
                    provider_requests=0,
                    production_changed=False,
                    ownership_unchanged=True,
                )
            )
        )
    finally:
        service.stop.set()
        progress.drain()
        if releaser is not None:
            releaser.join(5)
        if holder is not None:
            holder.close()
