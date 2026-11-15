"""Real queue previews against isolated source-defined tables, without provider calls."""

from datetime import datetime
import json
import os
from pathlib import Path
import re
from types import SimpleNamespace
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services import export_coordination_dal as module

TABLES = (
    "dbo.ExportJob",
    "dbo.ExportJobResource",
    "dbo.ExportResource",
    "dbo.ExportAttempt",
    "dbo.ExportAttemptPart",
    "KVK.SourceOutputPool",
    "KVK.SourceOutputSlot",
    "KVK.SourceOutputDisposition",
    "KVK.SourceDelivery",
    "KVK.SourceOutputOperation",
    "KVK.SourceExportIntent",
)


@pytest.fixture(scope="module")
def database(snapshot_database):
    import pyodbc

    root = pyodbc.connect(snapshot_database.connection_string, autocommit=True, timeout=5)
    root.timeout = 5
    try:
        assert (
            root.execute(
                "SELECT used_log_space_in_percent FROM sys.dm_db_log_space_usage"
            ).fetchval()
            < 70
        )
        root.execute("CREATE SCHEMA KVK")
        source = (
            Path(os.environ.get("K98_CONFIG_RECOVERY_SQL_SOURCE", "C:/K98-bot-SQL-Server"))
            / "sql_schema"
        )
        for name in TABLES:
            raw = (source / (name + ".Table.sql")).read_text(encoding="utf-8-sig")
            body = re.search(r"CREATE TABLE " + re.escape(name) + r"\s*\(.*?\n\);", raw, re.S)
            assert body, name
            sql = "\n".join(line for line in body[0].splitlines() if "FOREIGN KEY" not in line)
            root.execute(re.sub(r",\s*\);", "\n);", sql))
        root.execute(
            "CREATE USER preview_reader WITHOUT LOGIN; GRANT SELECT ON SCHEMA::dbo TO preview_reader; GRANT SELECT ON SCHEMA::KVK TO preview_reader"
        )
    finally:
        root.close()
    return snapshot_database


@pytest.fixture
def state(database):
    import pyodbc

    root = pyodbc.connect(database.connection_string, autocommit=True, timeout=5)
    root.timeout = 5
    handles = []
    try:
        for name in reversed(TABLES):
            root.execute("DELETE " + name)
        job, pool, intent, choice, owner = [str(uuid4()) for _ in range(5)]
        stamp = datetime(2026, 10, 15)

        def insert(name, row):
            assert name in TABLES
            root.execute(
                f"INSERT {name} ({','.join('['+c+']' for c in row)}) VALUES ({','.join('?' for _ in row)})",
                *row.values(),
            )

        insert(
            "dbo.ExportJob",
            dict(
                JobID=job,
                ConsumerKind="new_source",
                SourceKey="snapshot_report_v1",
                IntentID=intent,
                AccountKey="a",
                DestinationSetHash=digest(["index"]),
                InputHash=b"i" * 32,
                KVK_NO=16,
                PoolEpoch=1,
                EnqueueSequence=1,
                State="ready",
                Fence=0,
                Version=1,
                CreatedUTC=stamp,
                UpdatedUTC=stamp,
                Actor="test",
                Reason="fixture",
                ProvenanceJson="{}",
            ),
        )
        for key in ("account:a", "destination:index"):
            insert(
                "dbo.ExportResource",
                dict(ResourceKey=key, ResourceKind=key.split(":")[0], Fence=0, Version=1),
            )
            insert("dbo.ExportJobResource", dict(JobID=job, ResourceKey=key))
        insert(
            "KVK.SourceOutputPool",
            dict(
                PoolID=pool,
                IndexFileID="index",
                IndexFileKind="index",
                RegistrationNo=1,
                AccountKey="a",
                AccountResourceKey="account:a",
                ExpectedOwner="fixture",
                AudienceJson="{}",
                SourceKey="snapshot_report_v1",
                ActiveKVK=16,
                ChoiceID=choice,
                Epoch=1,
                PoolState="active",
                Fence=0,
                Version=1,
                CreatedUTC=stamp,
                UpdatedUTC=stamp,
                RegistrationHash=digest({}),
                RegistrationJson="{}",
            ),
        )
        insert(
            "KVK.SourceOutputSlot",
            dict(
                FileID="slot",
                FileKind="slot",
                PoolID=pool,
                SlotNo=1,
                Epoch=1,
                State="free",
                Fence=0,
                Version=1,
                CreatedUTC=stamp,
                UpdatedUTC=stamp,
            ),
        )
        insert(
            "KVK.SourceExportIntent",
            dict(
                IntentID=intent,
                SourceKey="snapshot_report_v1",
                KVK_NO=16,
                ChoiceID=choice,
                CommitSequence=1,
                VectorHash=b"v" * 32,
                ExportSchemaVersion="v1",
                IntentState="pending",
                CreatedUTC=stamp,
            ),
        )

        def connect(reader=True):
            cn = pyodbc.connect(database.connection_string, autocommit=True, timeout=5)
            handles.append(cn)
            cn.timeout = 5
            if reader:
                cn.execute("EXECUTE AS USER='preview_reader'")
            cn.autocommit = False
            return cn

        yield SimpleNamespace(
            root=root,
            job=job,
            pool=pool,
            owner=owner,
            insert=insert,
            stamp=stamp,
            handles=handles,
            dal=module.ExportCoordinationDAL(connect, preparations=True, output_operations=True),
            mutation=module.ExportCoordinationDAL(
                lambda: connect(False), preparations=True, output_operations=True
            ),
        )
    finally:
        for cn in handles:
            try:
                cn.close()
            except pyodbc.ProgrammingError:
                pass
        root.execute("IF @@TRANCOUNT>0 ROLLBACK")
        root.close()


def test_observer_first_keeps_job_resources_pool_and_slots_consistent(state, monkeypatch):
    s = state
    original = module.one
    fired = False

    def one(cursor):
        nonlocal fired
        row = original(cursor)
        if row and "JobID" in row and not fired:
            fired = True
            s.root.execute("BEGIN TRANSACTION")
            module._mutex(s.root.cursor(), "account:a")
            s.root.execute("UPDATE dbo.ExportJob SET Version=2")
            s.root.execute("UPDATE dbo.ExportResource SET Version=2")
            s.root.execute("UPDATE KVK.SourceOutputPool SET Version=2")
            s.root.execute(
                "UPDATE KVK.SourceOutputSlot SET State='quarantined',QuarantineReason='fixture',Version=2"
            )
            s.root.execute("COMMIT")
        return row

    monkeypatch.setattr(module, "one", one)
    old = s.dal.operator_snapshot(s.job)
    assert (
        old["job"]["Version"]
        == old["resources"][0]["Version"]
        == old["pool"]["pool"]["Version"]
        == old["pool"]["slots"][0]["Version"]
        == 1
    )
    new = s.dal.operator_snapshot(s.job)
    assert (
        new["job"]["Version"]
        == new["resources"][0]["Version"]
        == new["pool"]["pool"]["Version"]
        == new["pool"]["slots"][0]["Version"]
        == 2
    )
    with pytest.raises(SourceConflict, match="snapshot changed"):
        s.mutation.reconcile_operator(
            old,
            dict(
                snapshot_hash=digest(old).hex(),
                writer_terminated=True,
                evidence_id="fixture",
                state="absent",
            ),
            actor="test",
        )


def test_writer_first_reads_keep_prior_committed_queue(state):
    s = state
    s.root.execute("BEGIN TRANSACTION")
    try:
        module._mutex(s.root.cursor(), "account:a")
        s.root.execute("UPDATE dbo.ExportJob SET Version=2")
        s.root.execute("UPDATE KVK.SourceExportIntent SET IntentState='blocked'")
        assert s.dal.accounts() == ["a"]
        assert s.dal.pending_intents()[0]["IntentState"] == "pending"
        assert s.dal.pending_source_jobs("a")[0]["Version"] == 1
        assert s.dal.operator_snapshot(s.job)["job"]["Version"] == 1
        assert s.dal.repair_receipt(str(uuid4())) is None
    finally:
        s.root.execute("ROLLBACK")


@pytest.mark.parametrize("corruption", ["hash", "parts", "pool"])
def test_receipt_and_registration_corruption_still_refused(state, corruption):
    s = state
    if corruption == "pool":
        s.root.execute("UPDATE KVK.SourceOutputPool SET RegistrationHash=?", b"x" * 32)
    else:
        manifest = {
            "parts": [
                dict(
                    file_id="slot", role="output", manifest_hash="00" * 32, grids=1, rows=1, cells=1
                )
            ]
        }
        s.insert(
            "dbo.ExportAttempt",
            dict(
                AttemptID=str(uuid4()),
                JobID=s.job,
                ConsumerKind="new_source",
                AttemptNo=1,
                OwnerID=s.owner,
                Fence=1,
                Epoch=1,
                Phase="private_started",
                RemoteSequence=1,
                Version=1,
                CreatedUTC=s.stamp,
                UpdatedUTC=s.stamp,
                ManifestHash=b"x" * 32 if corruption == "hash" else digest(manifest),
                ManifestJson=json.dumps(manifest),
                PartCount=1,
            ),
        )
    with pytest.raises(SourceConflict):
        s.dal.operator_snapshot(s.job)


def test_permission_failure_closes_reader(state):
    import pyodbc

    s = state
    s.root.execute("DENY SELECT ON KVK.SourceOutputSlot TO preview_reader")
    try:
        with pytest.raises(pyodbc.Error):
            s.dal.operator_snapshot(s.job)
        with pytest.raises(pyodbc.ProgrammingError):
            s.handles[-1].cursor()
    finally:
        s.root.execute("REVOKE SELECT ON KVK.SourceOutputSlot TO preview_reader")
