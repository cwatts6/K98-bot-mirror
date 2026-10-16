"""Real SQL locking/CAS with isolated global temp tables; no persistent DDL/DML."""

from copy import deepcopy
import os
from pathlib import Path
import re
from types import SimpleNamespace
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.all_kvk_capture_recovery_dal import AllKvkCaptureRecoveryDAL
from services.all_kvk_capture_recovery_service import (
    AllKvkCaptureRecovery,
    AllKvkCaptureRecoveryAdapter,
)
from services.export_snapshot_store import ExportSnapshotStore
from services.import_capture_recovery_service import ImportCaptureRecovery
from services.import_recovery_service import ImportRecoveryAdapter
from services.legacy_export_snapshot_dal import LegacySnapshotDAL
from services.legacy_export_snapshot_service import (
    LegacySnapshot,
    OutputSection,
    SnapshotUnavailable,
)
from services.player_report_recovery_dal import PlayerReportRecoveryDAL
from services.player_report_recovery_service import (
    PlayerReportCaptureRecovery,
    PlayerReportRecoveryAdapter,
)
from services.stats_import_outcome_dal import StatsImportOutcomeDAL
from tests.test_import_capture_recovery import fixture

pytestmark = pytest.mark.skipif(
    os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1",
    reason="Explicit local temp-table SQL opt-in required",
)


@pytest.fixture(params=["scan_data", "all_kvk", "player_report"])
def recovery(tmp_path, request):
    import pyodbc

    namespace = uuid4().hex
    names = {
        "dbo." + name: "##Capture_" + namespace + "_" + name
        for name in (
            "ExportPreparation",
            "ExportResource",
            "StatsImportExecution",
            "ExportExecutionStream",
        )
    }
    cs = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\\K98DEV;DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes"

    def rewrite(sql):
        for source, target in names.items():
            sql = sql.replace(source, target)
        return sql

    def parameter(value):
        if isinstance(value, str) and value.startswith(
            ("S11:stats-import:", "k98-legacy-output-snapshot", "export:account:", "k98-export:")
        ):
            return "test:" + namespace + ":" + value
        return value

    owner = pyodbc.connect(cs, autocommit=True, timeout=5)
    schema = Path(os.getenv("K98_CAPTURE_SQL_SCHEMA", "C:/K98-bot-SQL-Server/sql_schema"))
    try:
        for source in names:
            raw = (schema / (source + ".Table.sql")).read_text(encoding="utf-8-sig")
            raw = "\n".join(line for line in raw.splitlines() if "FOREIGN KEY" not in line)
            raw = re.sub(r",\s*\);", "\n);", raw)
            raw = re.sub(r"CONSTRAINT (\w+)", lambda m: "CONSTRAINT " + m[1] + "_" + namespace, raw)
            owner.execute(rewrite(raw))

        class Cursor:
            def __init__(self, inner):
                self.inner = inner

            def execute(self, sql, *args):
                # The fixture namespaces application locks as well as table names.
                sql = sql.replace(
                    "N'k98-legacy-output-snapshot'",
                    "N'test:" + namespace + ":k98-legacy-output-snapshot'",
                )
                self.inner.execute(rewrite(sql), *(parameter(a) for a in args))
                return self

            def __getattr__(self, key):
                return getattr(self.inner, key)

        class Connection:
            def __init__(self):
                self.inner = pyodbc.connect(cs, autocommit=False, timeout=5)
                self.inner.timeout = 3

            @property
            def autocommit(self):
                return self.inner.autocommit

            @autocommit.setter
            def autocommit(self, value):
                self.inner.autocommit = value

            def cursor(self):
                return Cursor(self.inner.cursor())

            def __getattr__(self, key):
                return getattr(self.inner, key)

        if request.param == "all_kvk":
            from tests.test_all_kvk_capture_recovery import fixture as kvk_fixture

            base, preview, resources = kvk_fixture()
        elif request.param in {"player_report", "configuration_producer"}:
            from tests.test_player_report_recovery import fixture as report_fixture

            base, preview, resources = report_fixture()
            if request.param == "configuration_producer":
                import json

                from kvk.dal.new_source_import_dal import digest
                from services.configuration_producer_recovery import (
                    ConfigurationProducerCapture,
                    ConfigurationProducerDAL,
                )

                prep = preview["preparation"]
                document = json.loads(prep["RequestJson"])
                document["request"]["producer"]["kind"] = "configuration_import"
                generation = json.loads(prep["GenerationJson"])
                generation["producer"]["procedure"] = "ProcConfig and sp_TARGETS_MASTER"
                prep.update(
                    RequestJson=json.dumps(document),
                    RequestHash=digest(document),
                    GenerationJson=json.dumps(generation),
                )
        else:
            base, preview, resources = fixture()
        prep, execution = preview["preparation"], preview["execution"]
        prep.update(EnqueueSequence=1, Actor="test", Reason="isolated recovery test")
        prep.setdefault("RequestHash", b"r" * 32)
        for table, row in (
            ("ExportPreparation", prep),
            ("StatsImportExecution", execution),
            ("ExportResource", dict(resources[0], ResourceKind="sql_snapshot")),
        ):
            if row is None:
                continue
            values = dict(row)
            if table == "ExportPreparation":
                from datetime import datetime

                values.update(CreatedUTC=datetime(2026, 10, 15), UpdatedUTC=datetime(2026, 10, 15))
            columns = list(values)
            placeholders = ["CAST(? AS binary(32))" if c == "RequestHash" else "?" for c in columns]
            owner.execute(
                rewrite(
                    f"INSERT dbo.{table} ({','.join(columns)}) VALUES ({','.join(placeholders)})"
                ),
                *(values[c] for c in columns),
            )

        outcome_type = {
            "all_kvk": AllKvkCaptureRecoveryDAL,
            "scan_data": StatsImportOutcomeDAL,
            "player_report": PlayerReportRecoveryDAL,
        }.get(request.param)
        if request.param == "configuration_producer":
            outcome_type = ConfigurationProducerDAL
        outcomes = outcome_type(Connection, account="a", storage_owner="disk-a")
        state = SimpleNamespace(sections=(OutputSection("output", ("value",), ((7,),)),), fail=None)
        store = ExportSnapshotStore(tmp_path, "disk-a")
        runtime = SimpleNamespace(
            configuration=base.runtime.configuration,
            store=store,
            dal=LegacySnapshotDAL(Connection),
            capture=lambda *_: (
                state.sections,
                dict(consumer=base.consumer, destinations=["registered"]),
            ),
        )

        def verified_snapshot(preparation_id):
            row = outcomes.inspect(preparation_id)["preparation"]
            from services.export_snapshot_store import SnapshotReceipt

            LegacySnapshot.load(
                store.read(
                    SnapshotReceipt(
                        row["SpoolKey"], row["SpoolBytes"], bytes(row["SpoolHash"]).hex(), "disk-a"
                    )
                )
            )
            return row, None, {}

        def enqueue(preparation_id):
            row, _, _ = verified_snapshot(preparation_id)
            if not row["JobID"]:
                owner.execute(
                    rewrite(
                        "UPDATE dbo.ExportPreparation SET State='materialized',JobID=?,Version=Version+1 WHERE PreparationID=? AND State='captured'"
                    ),
                    str(uuid4()),
                    preparation_id,
                )
            if state.fail == "queue":
                state.fail = None
                raise TimeoutError("lost queue acknowledgement")
            return str(outcomes.inspect(preparation_id)["preparation"]["JobID"])

        runtime.enqueue_snapshot = enqueue
        service_type = {
            "all_kvk": AllKvkCaptureRecovery,
            "scan_data": ImportCaptureRecovery,
            "player_report": PlayerReportCaptureRecovery,
        }.get(request.param)
        if request.param == "configuration_producer":
            service_type = ConfigurationProducerCapture
        service = service_type(runtime, outcomes)
        runtime.verified_snapshot = verified_snapshot
        yield SimpleNamespace(
            service=service,
            outcomes=outcomes,
            runtime=runtime,
            state=state,
            source=prep["PreparationID"],
            owner=owner,
            rewrite=rewrite,
            parameter=parameter,
        )
    finally:
        owner.close()


@pytest.mark.parametrize("failure", [None, "adopt", "proof", "spool", "receipt", "queue"])
def test_restart_at_each_acknowledgement_finishes_capture_once(recovery, monkeypatch, failure):
    r = recovery
    token = r.outcomes.inspect(r.source)["token"]
    action_id = str(uuid4())
    actor = "recovery:" + action_id
    action = dict(ActionKind="resume_capture", ActionID=action_id, EvidenceHash=token)
    if failure == "queue":
        r.state.fail = failure
    elif failure:
        target, method = {
            "adopt": (r.service.dal, "adopt"),
            "proof": (r.runtime.dal, "transition"),
            "spool": (r.runtime.store, "put"),
            "receipt": (r.runtime.dal, "captured"),
        }[failure]
        original = getattr(target, method)

        def lose_ack(*args, **kwargs):
            original(*args, **kwargs)
            monkeypatch.setattr(target, method, original)
            raise TimeoutError("lost acknowledgement")

        monkeypatch.setattr(target, method, lose_ack)
    original_execution = deepcopy(r.outcomes.inspect(r.source)["execution"])
    if failure:
        with pytest.raises(TimeoutError):
            r.service.run(r.source, token, actor)
    else:
        r.service.run(r.source, token, actor)
    # New service instances resume only the original persisted action identity.
    restarted = type(r.service)(r.runtime, r.outcomes)
    adapter_type = (
        PlayerReportRecoveryAdapter
        if isinstance(restarted, PlayerReportCaptureRecovery)
        else (
            AllKvkCaptureRecoveryAdapter
            if isinstance(restarted, AllKvkCaptureRecovery)
            else ImportRecoveryAdapter
        )
    )
    adapter = adapter_type(r.outcomes, restarted)
    assert adapter.reconcile(r.source, action) == "verified"
    assert adapter.inspect(r.source)[2]
    final = r.outcomes.inspect(r.source)
    assert final["captured"] and final["preparation"]["JobID"]
    assert final["execution"] == original_execution
    job = final["preparation"]["JobID"]
    assert adapter.reconcile(r.source, action) == "verified"
    assert r.outcomes.inspect(r.source)["preparation"]["JobID"] == job


@pytest.mark.parametrize("lock", ["k98-legacy-output-snapshot", "S11:stats-import:"])
def test_live_original_session_prevents_capture(recovery, lock):
    r = recovery
    if not r.service.dal.stats_execution and lock == "S11:stats-import:":
        # This receipt/guard belongs only to scan-data, not the all-KVK producer.
        return
    token = r.outcomes.inspect(r.source)["token"]
    resource = r.parameter(lock + (r.source if lock.endswith(":") else ""))
    r.owner.execute(
        "EXEC sys.sp_getapplock @Resource=?,@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0",
        resource,
    )
    try:
        with pytest.raises(SourceConflict):
            r.service.run(r.source, token, "recovery:test")
    finally:
        r.owner.execute("EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'", resource)
    assert r.outcomes.inspect(r.source)["token"] == token


def test_completed_hash_cannot_be_overwritten_after_restart(recovery, monkeypatch):
    r = recovery
    token = r.outcomes.inspect(r.source)["token"]
    original = r.runtime.store.put
    monkeypatch.setattr(r.runtime.store, "put", lambda *_: (_ for _ in ()).throw(TimeoutError()))
    with pytest.raises(TimeoutError):
        r.service.run(r.source, token, "recovery:test")
    monkeypatch.setattr(r.runtime.store, "put", original)
    r.state.sections = (OutputSection("output", ("value",), ((999,),)),)
    with pytest.raises(SnapshotUnavailable, match="differs"):
        r.service.run(r.source, token, "recovery:test")
    assert not r.outcomes.inspect(r.source)["captured"]


def test_old_claim_and_different_action_cannot_capture_after_adoption(recovery):
    r = recovery
    token = r.outcomes.inspect(r.source)["token"]
    with r.service.dal.session(r.source) as connection:
        claim, _ = r.service.dal.adopt(
            connection, r.source, token, "recovery:first", r.service.generation
        )
        with pytest.raises(SourceConflict):
            r.service.dal.adopt(
                connection, r.source, token, "recovery:second", r.service.generation
            )
        from dataclasses import replace

        old = replace(
            claim,
            version=claim.version - 1,
            resources=((claim.resources[0][0], claim.resources[0][1] - 1),),
        )
        with pytest.raises(SourceConflict):
            r.runtime.dal.authorize(old)


def test_normal_capture_queue_gap_is_discovered_and_confirmed_once(recovery, monkeypatch):
    r = recovery
    token = r.outcomes.inspect(r.source)["token"]
    original = r.runtime.enqueue_snapshot
    monkeypatch.setattr(
        r.runtime, "enqueue_snapshot", lambda *_: (_ for _ in ()).throw(TimeoutError())
    )
    with pytest.raises(TimeoutError):
        r.service.run(r.source, token, "recovery:capture")
    # A normal producer capture has no recovery marker at all.
    r.owner.execute(
        r.rewrite(
            "UPDATE dbo.ExportPreparation SET GenerationJson=JSON_MODIFY(GenerationJson,"
            "'$.capture_recovery',NULL),UpdatedUTC=DATEADD(minute,-5,SYSUTCDATETIME()) "
            "WHERE PreparationID=?"
        ),
        r.source,
    )
    assert r.source in r.outcomes.pending_recovery()
    adapter_type = (
        PlayerReportRecoveryAdapter
        if isinstance(r.service, PlayerReportCaptureRecovery)
        else (
            AllKvkCaptureRecoveryAdapter
            if isinstance(r.service, AllKvkCaptureRecovery)
            else ImportRecoveryAdapter
        )
    )
    adapter = adapter_type(r.outcomes, r.service)
    evidence, token, resolved = adapter.inspect(r.source)
    assert not resolved and set(evidence["actions"]) == {"queue_capture", "abandon_capture"}
    assert r.outcomes.inspect(r.source)["preparation"]["JobID"] is None
    monkeypatch.setattr(r.runtime, "enqueue_snapshot", original)
    r.state.fail = "queue"
    with pytest.raises(TimeoutError):
        adapter.execute(r.source, "queue_capture", token, "recovery:queue", "continue output")
    job = r.outcomes.inspect(r.source)["preparation"]["JobID"]
    action = dict(ActionKind="queue_capture", EvidenceHash=token, ActionID="queue")
    assert adapter.reconcile(r.source, action) == "verified"
    assert r.outcomes.inspect(r.source)["preparation"]["JobID"] == job
    assert r.source not in r.outcomes.pending_recovery()


def test_capture_discovery_excludes_other_storage_and_account(recovery):
    r = recovery
    r.owner.execute(
        r.rewrite(
            "UPDATE dbo.ExportPreparation SET UpdatedUTC=DATEADD(minute,-5,"
            "SYSUTCDATETIME()) WHERE PreparationID=?"
        ),
        r.source,
    )
    assert r.source in r.outcomes.pending_recovery()
    for account, storage in (("other", "disk-a"), ("a", "other")):
        foreign = type(r.outcomes)(r.outcomes.connect, account=account, storage_owner=storage)
        assert r.source not in foreign.pending_recovery()
        with pytest.raises(SourceConflict):
            foreign.inspect(r.source)
