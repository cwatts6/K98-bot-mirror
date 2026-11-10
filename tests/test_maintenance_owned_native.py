"""Real maintenance procedures in an explicitly owned disposable SQL database."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import subprocess
import sys
import time
from uuid import uuid4

import pytest

from services.maintenance_dal import run_maintenance
from tests.sql_snapshot_fixture import snapshot_database as _snapshot_database

snapshot_database = _snapshot_database

SQL_ROOT = Path("C:/K98-bot-SQL-Server/sql_schema")


@pytest.fixture
def maintenance_database(snapshot_database):
    import pyodbc

    def connect():
        return pyodbc.connect(snapshot_database.connection_string, autocommit=True, timeout=5)

    owner = connect()
    try:
        owner.execute("DROP TABLE IF EXISTS dbo.MaintenanceWork")
        for name in (
            "dbo.MaintenanceWork.Table.sql",
            "dbo.usp_MaintenanceDue.StoredProcedure.sql",
            "dbo.usp_MaintenancePostImport.StoredProcedure.sql",
            "dbo.usp_RunMaintenance.StoredProcedure.sql",
            "dbo.usp_update_stats.StoredProcedure.sql",
        ):
            source = (SQL_ROOT / name).read_text(encoding="utf-8-sig")
            for batch in re.split(r"(?im)^GO\s*$", source):
                if batch.strip():
                    owner.execute(batch)
        yield owner, connect
    finally:
        owner.close()


def state(connection, kind="post_import"):
    row = connection.execute(
        "SELECT DueGeneration,CompletedGeneration,State,ClaimID,FirstErrorNumber "
        "FROM dbo.MaintenanceWork WHERE Kind=?",
        kind,
    ).fetchone()
    return tuple(row)


def drain(cursor):
    while cursor.nextset():
        pass


def test_real_post_import_child_and_durable_receipt(maintenance_database):
    owner, connect = maintenance_database
    request = str(uuid4())
    receipt = run_maintenance(connect, request_id=request)
    assert receipt["request_id"] == request
    assert receipt["maintenance"][0]["State"] == "complete"
    assert state(owner)[:3] == (1, 1, "complete")
    # Exact acknowledgement loss readback never dispatches a second child.
    old_claim = state(owner)[3]
    run_maintenance(connect, request_id=request)
    assert state(owner)[3] == old_claim
    assert owner.execute("SELECT COUNT(*) FROM dbo.MaintenanceWork").fetchval() == 6


def test_business_rollback_removes_due_and_nested_commit_does_not_publish(maintenance_database):
    owner, connect = maintenance_database
    reader = connect()
    try:
        owner.execute("BEGIN TRAN; BEGIN TRAN; EXEC dbo.usp_MaintenanceDue 'configuration'; COMMIT")
        assert owner.execute("SELECT @@TRANCOUNT").fetchval() == 1
        reader.execute("SET LOCK_TIMEOUT 0")
        with pytest.raises(Exception, match="1222"):
            state(reader, "configuration")
        owner.execute("ROLLBACK")
        assert state(reader, "configuration")[:3] == (0, 0, "complete")
    finally:
        reader.close()


def test_exact_live_claim_blocks_then_orphan_becomes_unknown_without_replay(maintenance_database):
    owner, connect = maintenance_database
    owner.execute("EXEC dbo.usp_MaintenanceDue 'post_import'")
    owner.execute(
        "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource='K98:post-import-stats:v1',"
        "@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; IF @r<0 THROW 50000,'fixture',1;"
        "UPDATE dbo.MaintenanceWork SET State='running',ClaimID=NEWID(),ClaimedGeneration=1 "
        "WHERE Kind='post_import'"
    )
    worker = connect()
    try:
        drain(worker.execute("EXEC dbo.usp_RunMaintenance 'post_import'"))
        assert state(owner)[2] == "running"
        owner.execute(
            "EXEC sys.sp_releaseapplock @Resource='K98:post-import-stats:v1',@LockOwner='Session'"
        )
        drain(worker.execute("EXEC dbo.usp_RunMaintenance 'post_import'"))
        assert state(owner)[:3] == (1, 0, "unknown")
        owner.execute("EXEC dbo.usp_MaintenanceDue 'post_import'")
        drain(worker.execute("EXEC dbo.usp_RunMaintenance 'post_import'"))
        assert state(owner)[:3] == (2, 0, "unknown")
    finally:
        worker.close()


def test_busy_producer_defers_without_claiming(maintenance_database):
    owner, connect = maintenance_database
    owner.execute(
        "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource='k98-legacy-output-snapshot',"
        "@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; IF @r<0 THROW 50000,'fixture',1"
    )
    try:
        receipt = run_maintenance(connect)
        assert receipt["maintenance"][0]["State"] == "pending"
        assert state(owner)[3] is None
    finally:
        owner.execute(
            "EXEC sys.sp_releaseapplock @Resource='k98-legacy-output-snapshot',@LockOwner='Session'"
        )


def test_missing_child_refused_and_not_retried(maintenance_database):
    owner, connect = maintenance_database
    # The fixed dispatcher rejects an uninstalled child after persisting a claim.
    owner.execute("EXEC dbo.usp_MaintenanceDue 'import'")
    worker = connect()
    try:
        with pytest.raises(Exception, match="51963"):
            drain(worker.execute("EXEC dbo.usp_RunMaintenance 'import'"))
    finally:
        worker.close()
    assert state(owner, "import")[2] == "failed"
    assert state(owner, "import")[4] == 51963
    owner.execute("EXEC dbo.usp_MaintenanceDue 'import'")
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'import'"))
    assert state(owner, "import")[:3] == (2, 0, "failed")


def test_transactional_worker_refused_before_dispatch(maintenance_database):
    owner, _ = maintenance_database
    owner.execute("BEGIN TRAN")
    try:
        with pytest.raises(Exception, match="51962"):
            owner.execute("EXEC dbo.usp_update_stats")
    finally:
        owner.execute("ROLLBACK")
    assert state(owner)[:3] == (0, 0, "complete")


def gated_child(owner):
    owner.execute(
        "DROP TABLE IF EXISTS dbo.MaintenanceTestGate; CREATE TABLE dbo.MaintenanceTestGate(Entered bit,Released bit); INSERT dbo.MaintenanceTestGate VALUES(0,0)"
    )
    source = (
        (SQL_ROOT / "dbo.usp_MaintenancePostImport.StoredProcedure.sql")
        .read_text()
        .split("GO\n", 1)[-1]
    )
    source = source.replace(
        "EXEC sys.sp_updatestats;",
        """
        UPDATE dbo.MaintenanceTestGate SET Entered=1;
        DECLARE @attempt int=0;
        WHILE (SELECT Released FROM dbo.MaintenanceTestGate)=0 AND @attempt<100
        BEGIN
            WAITFOR DELAY '00:00:00.100';
            SET @attempt+=1;
        END;
        IF @attempt=100 THROW 50001,'Fixture gate timeout',1;
        EXEC sys.sp_updatestats;
    """,
    )
    owner.execute(source)


def await_entered(owner):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if owner.execute("SELECT Entered FROM dbo.MaintenanceTestGate").fetchval():
            return
        time.sleep(0.02)
    pytest.fail("The actual maintenance child did not enter its fixture gate")


def test_new_due_during_real_child_and_reverse_writer_arrival(maintenance_database):
    owner, connect = maintenance_database
    gated_child(owner)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(run_maintenance, connect)
        try:
            await_entered(owner)
            result = owner.execute(
                "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource='k98-legacy-output-snapshot',"
                "@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; SELECT @r"
            ).fetchval()
            assert result == -1
            owner.execute("EXEC dbo.usp_MaintenanceDue 'post_import'")
            drain(owner.execute("EXEC dbo.usp_RunMaintenance 'post_import'"))
            assert state(owner)[:3] == (2, 0, "running")
        finally:
            owner.execute("UPDATE dbo.MaintenanceTestGate SET Released=1")
        response = future.result(10)
    assert response["maintenance"][0]["State"] == "pending"
    assert state(owner)[:3] == (2, 1, "pending")
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'post_import'"))
    assert state(owner)[:3] == (2, 2, "complete")


def test_process_death_after_claim_keeps_unknown_outcome(maintenance_database, snapshot_database):
    owner, _ = maintenance_database
    gated_child(owner)
    program = (
        "import pyodbc; pyodbc.pooling=False; "
        f"c=pyodbc.connect({snapshot_database.connection_string!r},autocommit=True); "
        "q=c.execute('EXEC dbo.usp_update_stats'); "
        "\nwhile q.nextset(): pass\n"
    )
    child = subprocess.Popen(
        [sys.executable, "-c", program], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        await_entered(owner)
        assert state(owner)[2] == "running"
    finally:
        child.kill()
        child.communicate(timeout=5)
        owner.execute("UPDATE dbo.MaintenanceTestGate SET Released=1")
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        drain(owner.execute("EXEC dbo.usp_RunMaintenance 'post_import'"))
        if state(owner)[2] != "running":
            break
        time.sleep(0.02)
    # A real disconnected worker may finish before SQL notices disconnect.
    # Either durable completion or an unconfirmed claim is truthful; no replay.
    assert state(owner)[2] in {"unknown", "complete"}
    claim = state(owner)[3]
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'post_import'"))
    assert state(owner)[3] == claim


def test_child_fault_keeps_first_failure_and_releases_only_on_close(maintenance_database):
    owner, connect = maintenance_database
    source = (
        (SQL_ROOT / "dbo.usp_MaintenancePostImport.StoredProcedure.sql")
        .read_text()
        .split("GO\n", 1)[-1]
    )
    owner.execute(
        source.replace("EXEC sys.sp_updatestats;", "THROW 50002,'Injected child failure',1;")
    )
    with pytest.raises(Exception, match="50002"):
        run_maintenance(connect)
    assert state(owner)[2:] == ("failed", state(owner)[3], 50002)
    claim = state(owner)[3]
    owner.execute("EXEC dbo.usp_MaintenanceDue 'post_import'")
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'post_import'"))
    assert state(owner)[2:] == ("failed", claim, 50002)
