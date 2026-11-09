"""D2e snapshot and settlement boundaries in an owned disposable database.

Use source columns/checks, omitting external foreign keys. No provider effects,
retained databases or production data are needed for these concurrency checks.
"""

from dataclasses import replace
from datetime import datetime
import os
from pathlib import Path
import re
from types import SimpleNamespace
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services import config_preparation_recovery_dal as module
from services.config_preparation_recovery_service import validate_snapshot
from services.export_coordination_dal import _mutex
from tests.test_config_preparation_recovery import fixture

TABLES = (
    "ExportPreparation",
    "ExportPreparationResource",
    "ExportResource",
    "ExportExecutionStream",
    "ExportProviderRequest",
    "ExportProviderRequestEvent",
)


@pytest.fixture(scope="module")
def database(snapshot_database):
    import pyodbc

    db = snapshot_database
    root = pyodbc.connect(db.connection_string, autocommit=True, timeout=5)
    root.timeout = 5
    try:
        assert (
            root.execute(
                "SELECT used_log_space_in_percent FROM sys.dm_db_log_space_usage"
            ).fetchval()
            < 70
        )
        source = (
            Path(os.environ.get("K98_CONFIG_RECOVERY_SQL_SOURCE", "C:/K98-bot-SQL-Server"))
            / "sql_schema"
        )
        for name in TABLES:
            raw = (source / f"dbo.{name}.Table.sql").read_text(encoding="utf-8-sig")
            body = re.search(r"CREATE TABLE dbo\." + name + r"\s*\(.*?\n\);", raw, re.S)
            assert body, name
            sql = "\n".join(line for line in body[0].splitlines() if "FOREIGN KEY" not in line)
            root.execute(re.sub(r",\s*\);", "\n);", sql))
        root.execute(
            "CREATE USER preview_reader WITHOUT LOGIN; GRANT SELECT ON SCHEMA::dbo TO preview_reader"
        )
    finally:
        root.close()
    return db


@pytest.fixture
def state(database):
    import pyodbc

    root = pyodbc.connect(database.connection_string, autocommit=True, timeout=5)
    root.timeout = 5
    handles = []
    try:
        for name in reversed(TABLES):
            root.execute("DELETE dbo." + name)
        service, snapshot, stream, _ = fixture()
        server = root.execute(
            "SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName'))"
        ).fetchval()
        target = replace(service.target, server=server, database=database.name)
        stamp = datetime(2026, 10, 15)
        snapshot["preparation"].update(
            EnqueueSequence=10, Actor="test", Reason="fixture", CreatedUTC=stamp, UpdatedUTC=stamp
        )
        stream.update(
            SessionID=str(uuid4()), SnapshotHash=b"s" * 32, CreatedUTC=stamp, ClosedUTC=stamp
        )
        binary = {
            "RequestHash",
            "RegistrationHash",
            "SnapshotHash",
            "ClosureHash",
            "EventDigest",
            "SpoolHash",
        }

        def insert(name, row):
            assert name in TABLES
            cols = list(row)
            values = [
                bytes.fromhex(row[k]) if k in binary and isinstance(row[k], str) else row[k]
                for k in cols
            ]
            root.execute(
                f"INSERT dbo.{name} ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
                *values,
            )

        insert("ExportPreparation", snapshot["preparation"])
        for row in snapshot["resources"]:
            insert("ExportResource", row | {"ResourceKind": row["ResourceKey"].split(":")[0]})
            insert(
                "ExportPreparationResource",
                dict(PreparationID=target.preparation_id, ResourceKey=row["ResourceKey"]),
            )
        insert("ExportExecutionStream", stream)

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
            target=target,
            handles=handles,
            insert=insert,
            stream=stream,
            dal=module.ConfigPreparationRecoveryDAL(connect),
            mutation=module.ConfigPreparationRecoveryDAL(lambda: connect(False)),
        )
    finally:
        for cn in handles:
            try:
                cn.close()
            except pyodbc.ProgrammingError:
                pass
        root.execute("IF @@TRANCOUNT>0 ROLLBACK")
        root.close()


@pytest.mark.parametrize("operation", ["snapshot", "target_data"])
def test_observer_first_sees_complete_old_tuple_across_writer_commit(state, monkeypatch, operation):
    s = state
    original = module.one
    committed = False

    def one(cursor):
        nonlocal committed
        row = original(cursor)
        if row and "PreparationID" in row and not committed:
            committed = True
            s.root.execute("BEGIN TRANSACTION")
            _mutex(s.root.cursor(), "account:" + s.target.account)
            s.root.execute("UPDATE dbo.ExportPreparation SET Version=4")
            s.root.execute("UPDATE dbo.ExportResource SET Version=Version+1")
            s.root.execute("COMMIT")
        return row

    monkeypatch.setattr(module, "one", one)

    def read():
        if operation == "snapshot":
            return s.dal.snapshot(s.target)
        return s.dal.target_data(
            s.target.preparation_id, account=s.target.account, storage_owner="fixture"
        )

    old = read()
    assert old["preparation"]["Version"] == 3
    assert [r["Version"] for r in old["resources"]] == [22, 19]
    fresh = read()
    assert fresh["preparation"]["Version"] == 4
    assert [r["Version"] for r in fresh["resources"]] == [23, 20]


def test_writer_first_does_not_block_any_read_route(state):
    s = state
    s.root.execute("BEGIN TRANSACTION")
    try:
        _mutex(s.root.cursor(), "account:" + s.target.account)
        s.root.execute("UPDATE dbo.ExportPreparation SET Version=4")
        assert s.dal.identity()["database"] == s.target.database
        assert s.dal.pending_recovery(account=s.target.account, storage_owner="fixture") == [
            s.target.preparation_id
        ]
        assert (
            s.dal.target_data(
                s.target.preparation_id, account=s.target.account, storage_owner="fixture"
            )["preparation"]["Version"]
            == 3
        )
        assert s.dal.snapshot(s.target)["preparation"]["Version"] == 3
    finally:
        s.root.execute("ROLLBACK")


@pytest.mark.parametrize("damage", ["extra_resource", "foreign_stream", "request_event"])
def test_complete_snapshot_keeps_conflicting_evidence(state, damage):
    s = state
    if damage == "extra_resource":
        s.root.execute(
            "INSERT dbo.ExportResource(ResourceKey,ResourceKind,ActivePreparationID,OwnerID,Fence,Version) VALUES('destination:extra','destination',?,?,10,1)",
            s.target.preparation_id,
            s.target.owner,
        )
    elif damage == "foreign_stream":
        foreign = dict(
            s.stream,
            StreamID=str(uuid4()),
            AccountKey="foreign",
            ActiveAccountKey="foreign",
            PreparationID=str(uuid4()),
            State="open",
            ClosedUTC=None,
            ClosureHash=None,
            ClosureReference=None,
            EventDigest=None,
        )
        s.insert("ExportExecutionStream", foreign)
    else:
        request = str(uuid4())
        s.root.execute(
            "INSERT dbo.ExportProviderRequest VALUES(?,?,1,'sheets.get','read','fixture',?,?,SYSUTCDATETIME())",
            request,
            s.stream["StreamID"],
            b"x" * 32,
            str(uuid4()),
        )
        s.root.execute(
            "INSERT dbo.ExportProviderRequestEvent VALUES(?,?,1,'prepared',?,?,SYSUTCDATETIME())",
            str(uuid4()),
            request,
            b"x" * 32,
            str(uuid4()),
        )
    observed = s.dal.snapshot(s.target)
    if damage == "extra_resource":
        assert len(observed["resources"]) == 3
    elif damage == "foreign_stream":
        assert len(observed["streams"]) == 2
    else:
        assert observed["request_count"] == observed["event_count"] == 1
    with pytest.raises(SourceConflict):
        validate_snapshot(
            observed,
            s.target,
            registration_hash=s.stream["RegistrationHash"].hex(),
            storage_owner="fixture",
        )


def test_stale_snapshot_refused_and_fresh_settlement_retains_fences(state):
    s = state
    old = s.dal.snapshot(s.target)
    s.root.execute(
        "UPDATE dbo.ExportResource SET Version=Version+1 WHERE ResourceKey='destination:file-a'"
    )
    with pytest.raises(SourceConflict, match="raced"):
        s.mutation.settle(s.target, old, {"actor": "test", "reason": "fixture"})
    assert s.root.execute("SELECT State FROM dbo.ExportPreparation").fetchval() == "uncertain"
    fresh_target = replace(
        s.target, resources=(("account:account-a", 22), ("destination:file-a", 20))
    )
    fresh = s.dal.snapshot(fresh_target)
    s.mutation.settle(fresh_target, fresh, {"actor": "test", "reason": "fixture"})
    assert s.root.execute("SELECT State FROM dbo.ExportPreparation").fetchval() == "unavailable"
    assert s.root.execute("SELECT MIN(Fence) FROM dbo.ExportResource").fetchval() == 10
    assert s.root.execute("SELECT MAX(Fence) FROM dbo.ExportResource").fetchval() == 10
    assert (
        s.root.execute(
            "SELECT COUNT(*) FROM dbo.ExportResource WHERE ActivePreparationID IS NOT NULL"
        ).fetchval()
        == 0
    )
    assert s.root.execute("SELECT COUNT(*) FROM dbo.ExportPreparationResource").fetchval() == 2


def test_denied_read_closes_physical_connection(state):
    import pyodbc

    s = state
    s.root.execute("DENY SELECT ON dbo.ExportResource TO preview_reader")
    try:
        with pytest.raises(pyodbc.Error):
            s.dal.snapshot(s.target)
        with pytest.raises(pyodbc.ProgrammingError):
            s.handles[-1].cursor()
    finally:
        s.root.execute("REVOKE SELECT ON dbo.ExportResource TO preview_reader")


def test_foreign_registered_scope_refused(state):
    with pytest.raises(SourceConflict, match="outside"):
        state.dal.target_data(
            state.target.preparation_id, account="foreign", storage_owner="fixture"
        )
