from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import time

import pytest

from core.recovery_sql_snapshot import recovery_snapshot
from core.sql_observation import ObservationBusy
from tests.sql_snapshot_fixture import snapshot_database as _database


@pytest.fixture
def snapshot_database():
    yield from _database.__wrapped__()


ROOT = Path("C:/K98-bot-SQL-Server/sql_schema")


def drain(cursor):
    while cursor.nextset():
        pass


@pytest.fixture
def database(snapshot_database):
    import pyodbc

    connect = lambda: pyodbc.connect(snapshot_database.connection_string, autocommit=True)
    owner = connect()
    try:
        for name in (
            "MaintenanceWork.Table",
            "usp_MaintenanceDue.StoredProcedure",
            "usp_MaintenanceImport.StoredProcedure",
            "usp_MaintenancePostImport.StoredProcedure",
            "usp_RunMaintenance.StoredProcedure",
            "usp_update_stats.StoredProcedure",
        ):
            for batch in re.split(r"(?im)^GO\s*$", (ROOT / ("dbo." + name + ".sql")).read_text()):
                if batch.strip():
                    owner.execute(batch)
        drain(
            owner.execute(
                "SET NOCOUNT ON; CREATE TABLE dbo.KingdomScanData5 (GovernorID int); CREATE TABLE dbo.PlayerScanMeta (GovernorID int); "
                "CREATE TABLE dbo.KingdomScanData4 (ScanOrder int, GovernorID uniqueidentifier, Payload char(800)); "
                "CREATE CLUSTERED INDEX CIX_KS4_ScanOrder_Governor ON dbo.KingdomScanData4(ScanOrder,GovernorID); "
                "INSERT dbo.KingdomScanData5 VALUES(1); INSERT dbo.PlayerScanMeta VALUES(1); "
                "DECLARE @i int=0; WHILE @i<3000 BEGIN INSERT dbo.KingdomScanData4 VALUES(1,NEWID(),REPLICATE(CHAR(65),800)); "
                "SET @i+=1; END;"
            )
        )
        # Owned disposable fixture headroom, not a production admission bypass.
        owner.execute("CHECKPOINT")
        assert (
            owner.execute(
                "SELECT used_log_space_in_percent FROM sys.dm_db_log_space_usage"
            ).fetchval()
            < 70
        )
        yield owner, connect
    finally:
        owner.close()


def state(owner):
    return tuple(
        owner.execute(
            "SELECT DueGeneration,CompletedGeneration,KS4DueGeneration,KS4CompletedGeneration,State FROM dbo.MaintenanceWork WHERE Kind='import'"
        ).fetchone()
    )


def frag(owner):
    return owner.execute(
        "SELECT MAX(avg_fragmentation_in_percent) FROM sys.dm_db_index_physical_stats(DB_ID(),OBJECT_ID('dbo.KingdomScanData4'),NULL,NULL,'LIMITED')"
    ).fetchval()


def test_real_conditional_import_child(database):
    owner, _ = database
    before = frag(owner)
    assert before >= 30
    owner.execute("EXEC dbo.usp_MaintenanceDue @Kind='import',@ImportKS4=0")
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'import'"))
    assert state(owner) == (1, 1, 0, 0, "complete")
    assert frag(owner) == before
    owner.execute("EXEC dbo.usp_MaintenanceDue @Kind='import',@ImportKS4=1")
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'import'"))
    assert state(owner) == (2, 2, 2, 2, "complete")
    assert frag(owner) < before
    assert owner.execute("SELECT COUNT(*) FROM dbo.KingdomScanData4").fetchval() == 3000


def test_reader_first_defers_actual_rebuild_and_preserves_raw_history(database):
    owner, connect = database
    reader = connect()
    try:
        reader.execute(
            "SET TRANSACTION ISOLATION LEVEL SNAPSHOT; BEGIN TRAN; DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource='K98:maintenance-schema:v1',@LockMode='Shared',@LockOwner='Transaction',@LockTimeout=0; IF @r<0 THROW 50000,'fixture lock',1;"
        )
        assert reader.execute("SELECT COUNT(*) FROM dbo.KingdomScanData4").fetchval() == 3000
        before = frag(owner)
        owner.execute("EXEC dbo.usp_MaintenanceDue @Kind='import',@ImportKS4=1")
        drain(owner.execute("EXEC dbo.usp_RunMaintenance 'import'"))
        assert state(owner) == (1, 0, 1, 0, "pending")
        assert frag(owner) == before
        assert reader.execute("SELECT COUNT(*) FROM dbo.KingdomScanData4").fetchval() == 3000
        reader.execute("ROLLBACK")
        drain(owner.execute("EXEC dbo.usp_RunMaintenance 'import'"))
        assert state(owner) == (1, 1, 1, 1, "complete")
        assert frag(owner) < before
    finally:
        reader.close()


def test_import_scope_rolls_back_with_business_transaction(database):
    owner, _ = database
    owner.execute("BEGIN TRAN; EXEC dbo.usp_MaintenanceDue @Kind='import',@ImportKS4=1; ROLLBACK")
    assert state(owner) == (0, 0, 0, 0, "complete")


def wait_running(owner):
    until = time.monotonic() + 5
    while time.monotonic() < until:
        if state(owner)[-1] == "running":
            return
        time.sleep(0.01)
    pytest.fail("Fixture worker never claimed its import generation")


def test_actual_managed_reader_first_keeps_producer_admission_independent(
    database, snapshot_database
):
    import pyodbc

    owner, _ = database
    factory = lambda: pyodbc.connect(snapshot_database.connection_string, autocommit=False)
    owner.execute("EXEC dbo.usp_MaintenanceDue @Kind='import',@ImportKS4=1")
    before = frag(owner)
    with recovery_snapshot(factory) as cursor:
        assert cursor.execute("SELECT COUNT(*) FROM dbo.KingdomScanData4").fetchval() == 3000
        assert (
            owner.execute(
                "SELECT APPLOCK_TEST('public','k98-legacy-output-snapshot','Exclusive','Session')"
            ).fetchval()
            == 1
        )
        drain(owner.execute("EXEC dbo.usp_RunMaintenance 'import'"))
        assert state(owner)[-1] == "pending"
        assert cursor.execute("SELECT COUNT(*) FROM dbo.KingdomScanData4").fetchval() == 3000
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'import'"))
    assert state(owner)[-1] == "complete"
    assert frag(owner) < before


def test_maintenance_first_refuses_managed_reader_and_leaves_new_generation_due(
    database, snapshot_database
):
    import pyodbc

    owner, connect = database
    factory = lambda: pyodbc.connect(snapshot_database.connection_string, autocommit=False)
    source = (
        (ROOT / "dbo.usp_MaintenanceImport.StoredProcedure.sql").read_text().split("GO\n", 1)[-1]
    )
    # Fixture delay establishes an observable real running child. Actual index
    # work remains unchanged and runs after this bounded test-only delay.
    owner.execute(
        source.replace("    SET NOCOUNT ON;", "    SET NOCOUNT ON; WAITFOR DELAY '00:00:01';", 1)
    )
    owner.execute("EXEC dbo.usp_MaintenanceDue @Kind='import',@ImportKS4=1")
    before = frag(owner)

    def run():
        worker = connect()
        try:
            drain(worker.execute("EXEC dbo.usp_RunMaintenance 'import'"))
        finally:
            worker.close()

    with ThreadPoolExecutor(max_workers=1) as pool:
        task = pool.submit(run)
        wait_running(owner)
        with pytest.raises(ObservationBusy):
            with recovery_snapshot(factory):
                pytest.fail("Reader entered during schema maintenance")
        owner.execute("EXEC dbo.usp_MaintenanceDue @Kind='import',@ImportKS4=1")
        task.result(timeout=5)
    assert state(owner) == (2, 1, 2, 1, "pending")
    assert frag(owner) < before
    with recovery_snapshot(factory) as cursor:
        assert cursor.execute("SELECT COUNT(*) FROM dbo.KingdomScanData4").fetchval() == 3000
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'import'"))
    assert state(owner) == (2, 2, 2, 2, "complete")
