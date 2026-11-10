"""Native D2d reads and confirmation in a uniquely owned disposable database.

Actual source columns/checks are retained; external FKs and unrelated ownership
objects are excluded. No provider or retained database is used. Legacy #table
tests separately cover the larger containment workflow.
"""

from pathlib import Path
import re
from types import SimpleNamespace
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services import unowned_sql_hold_dal as module
from services.export_coordination_dal import _mutex

TABLES = (
    "ExportResource",
    "ExportPreparation",
    "ExportPreparationResource",
    "StatsImportExecution",
    "ExportExecutionStream",
    "ExportUnownedHoldDisposition",
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
        source = Path("C:/K98-bot-SQL-Server/sql_schema")
        for name in TABLES:
            raw = (source / f"dbo.{name}.Table.sql").read_text(encoding="utf-8-sig")
            body = re.search(r"CREATE TABLE dbo\." + name + r"\s*\(.*?\n\);", raw, re.S)
            assert body, name
            sql = "\n".join(line for line in body[0].splitlines() if "FOREIGN KEY" not in line)
            root.execute(re.sub(r",\s*\);", "\n);", sql))
        root.execute(
            "CREATE USER preview_reader WITHOUT LOGIN; GRANT SELECT ON SCHEMA::dbo TO preview_reader"
        )
        root.execute("CREATE ROLE K98ImportLockPrincipal")
        raw = (source / "dbo.ACQUIRE_KS4_IMPORT_LOCK.StoredProcedure.sql").read_text(
            encoding="utf-8-sig"
        )
        root.execute(
            raw[raw.index("CREATE OR ALTER PROCEDURE") :].strip().removesuffix("GO").strip()
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
        root.execute(
            "INSERT dbo.ExportResource(ResourceKey,ResourceKind,Fence,Version,BlockedReason) VALUES(?,'sql_snapshot',9,4,'retained')",
            module.RESOURCE,
        )

        def connect(*, reader=True):
            cn = pyodbc.connect(database.connection_string, autocommit=True, timeout=5)
            handles.append(cn)
            cn.timeout = 5
            if reader:
                cn.execute("EXECUTE AS USER='preview_reader'")
            cn.autocommit = False
            return cn

        def dal(reader=True):
            return module.UnownedSqlHoldDAL(
                SimpleNamespace(
                    dal=SimpleNamespace(connect=lambda: connect(reader=reader)),
                    account="a",
                    store=SimpleNamespace(storage_owner="local"),
                )
            )

        yield SimpleNamespace(
            root=root, dal=dal(), mutation=dal(False), connect=connect, handles=handles
        )
    finally:
        for cn in handles:
            try:
                cn.close()
            except pyodbc.ProgrammingError:
                pass
        root.execute("IF @@TRANCOUNT>0 ROLLBACK")
        root.close()


def add_producer(root, *, account="foreign", state="writing", execution=None):
    prep, owner = str(uuid4()), str(uuid4())
    root.execute(
        "INSERT dbo.ExportPreparation(PreparationID,AccountKey,ConsumerKind,RequestHash,EnqueueSequence,State,OwnerID,Fence,Version,StorageOwner,RequestJson,Actor,Reason,CreatedUTC,UpdatedUTC) "
        "VALUES (?,?,'scan_data',?,1,?,?,1,1,'local','{}','fixture','fixture',SYSUTCDATETIME(),SYSUTCDATETIME())",
        prep,
        account,
        uuid4().bytes * 2,
        state,
        owner,
    )
    root.execute("INSERT dbo.ExportPreparationResource VALUES(?,?)", prep, module.RESOURCE)
    if execution:
        root.execute(
            "INSERT dbo.StatsImportExecution(PreparationID,CompletedFileName,OwnerID,Fence,State,ScanOrder) VALUES(?,?,?,1,?,17)",
            prep,
            "stats_" + uuid4().hex + ".ready.csv",
            owner,
            execution,
        )
    return prep


def test_observer_first_keeps_one_tuple_across_writer_commit(state, monkeypatch):
    s = state
    original = module.one
    first = True

    def one(cursor):
        nonlocal first
        row = original(cursor)
        if first:
            first = False
            assert row["Version"] == 4
            s.root.execute("BEGIN TRANSACTION")
            _mutex(s.root.cursor(), "account:a")
            _mutex(s.root.cursor(), module.RESOURCE)
            s.root.execute("UPDATE dbo.ExportResource SET Version=5")
            add_producer(s.root)
            s.root.execute("COMMIT TRANSACTION")
        return row

    monkeypatch.setattr(module, "one", one)
    old = s.dal.snapshot(s.dal.source_id)
    assert old["resource"]["Version"] == 4 and old["producers"] == []
    fresh = s.dal.snapshot(s.dal.source_id)
    assert fresh["resource"]["Version"] == 5 and len(fresh["producers"]) == 1
    assert not s.dal.eligible(fresh)


def test_writer_first_does_not_block_preview_or_discovery(state):
    s = state
    s.root.execute("BEGIN TRANSACTION")
    try:
        _mutex(s.root.cursor(), "account:a")
        _mutex(s.root.cursor(), module.RESOURCE)
        s.root.execute("UPDATE dbo.ExportResource SET Version=5,BlockedReason='writer'")
        assert s.dal.pending() == [s.dal.source_id]
        row = s.dal.snapshot(s.dal.source_id)["resource"]
        assert row["Version"] == 4 and row["BlockedReason"] == "retained"
    finally:
        s.root.execute("ROLLBACK")


@pytest.mark.parametrize(
    "owner_state,execution",
    [("writing", None), ("uncertain", None), ("unavailable", "partial")],
)
def test_detached_foreign_owner_remains_a_blocker(state, owner_state, execution):
    s = state
    add_producer(s.root, state=owner_state, execution=execution)
    observed = s.dal.snapshot(s.dal.source_id)
    assert len(observed["producers"]) == 1 and not s.dal.eligible(observed)
    with pytest.raises(SourceConflict):
        s.mutation.clear(
            s.dal.source_id,
            token=digest(observed).hex(),
            actor="recovery:" + str(uuid4()),
            reason="fixture",
        )
    assert s.root.execute("SELECT COUNT(*) FROM dbo.ExportUnownedHoldDisposition").fetchval() == 0


def test_stale_preview_refused_and_fresh_confirmation_keeps_exact_receipt(state):
    s = state
    old = s.dal.snapshot(s.dal.source_id)
    s.root.execute("UPDATE dbo.ExportResource SET Version=5")
    with pytest.raises(SourceConflict, match="changed"):
        s.mutation.clear(
            s.dal.source_id,
            token=digest(old).hex(),
            actor="recovery:" + str(uuid4()),
            reason="fixture",
        )
    fresh = s.dal.snapshot(s.dal.source_id)
    action_id = str(uuid4())
    result = s.mutation.clear(
        s.dal.source_id,
        token=digest(fresh).hex(),
        actor="recovery:" + action_id,
        reason="fixture",
    )
    assert result["AfterVersion"] == 6
    assert s.dal.action(action_id) == result
    assert s.dal.pending() == []
    row = s.dal.snapshot(s.dal.source_id)["resource"]
    assert row["BlockedReason"] is None and row["Fence"] == 9


@pytest.mark.parametrize("guard", ["k98-legacy-output-snapshot", "K98:post-import-stats:v1"])
def test_preview_is_not_permission_to_clear_an_active_physical_owner(state, guard):
    s = state
    s.root.execute(
        "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; IF @r<0 THROW 51959,'Fixture guard refused',1",
        guard,
    )
    try:
        observed = s.dal.snapshot(s.dal.source_id)
        with pytest.raises(SourceConflict):
            s.mutation.clear(
                s.dal.source_id,
                token=digest(observed).hex(),
                actor="recovery:" + str(uuid4()),
                reason="fixture",
            )
        assert (
            s.root.execute("SELECT BlockedReason FROM dbo.ExportResource").fetchval() == "retained"
        )
    finally:
        s.root.execute("EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'", guard)


def test_read_permission_failure_propagates_and_closes_connection(state):
    import pyodbc

    s = state
    s.root.execute("DENY SELECT ON dbo.ExportResource TO preview_reader")
    try:
        with pytest.raises(pyodbc.Error):
            s.dal.snapshot(s.dal.source_id)
        with pytest.raises(pyodbc.ProgrammingError):
            s.handles[-1].cursor()
    finally:
        s.root.execute("REVOKE SELECT ON dbo.ExportResource TO preview_reader")
