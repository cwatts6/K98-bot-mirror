"""Actual D3g SQL upkeep and ownership; backup dispatch is always simulated."""

from pathlib import Path
import re
from uuid import uuid4

import pytest

from services import maintenance_backup_dal as backup
from services.maintenance_dal import RELEASE_SESSION
from tests.sql_snapshot_fixture import snapshot_database as _database


@pytest.fixture
def snapshot_database():
    yield from _database.__wrapped__()


@pytest.fixture
def database(snapshot_database):
    import pyodbc

    def connect():
        return pyodbc.connect(snapshot_database.connection_string, autocommit=True)

    owner = connect()
    try:
        root = Path("C:/K98-bot-SQL-Server/sql_schema")
        for name in (
            "MaintenanceWork.Table",
            "MaintenanceBackupWork.Table",
            "MaintenanceKvkWork.Table",
            "usp_MaintenancePostImport.StoredProcedure",
            "usp_update_stats.StoredProcedure",
            "usp_MaintenanceDue.StoredProcedure",
            "usp_MaintenanceFinalStats.StoredProcedure",
            "usp_MaintenanceBackupClaim.StoredProcedure",
            "usp_MaintenanceBackupAcknowledge.StoredProcedure",
            "usp_RunMaintenance.StoredProcedure",
        ):
            for batch in re.split(
                r"(?im)^GO\s*$", (root / ("dbo." + name + ".sql")).read_text(encoding="utf-8-sig")
            ):
                if batch.strip():
                    owner.execute(batch)
        owner.execute("""CREATE TABLE dbo.EXCEL_FOR_DASHBOARD(ID int PRIMARY KEY,Value int);
            CREATE TABLE dbo.ALL_STATS_FOR_DASHBAORD(ID int PRIMARY KEY,Value int);
            INSERT dbo.EXCEL_FOR_DASHBOARD VALUES(1,10),(2,20);
            INSERT dbo.ALL_STATS_FOR_DASHBAORD VALUES(1,10),(2,20);
            CREATE TABLE dbo.LogBackupTriggerQueue(ID int,Processed bit);
            INSERT dbo.LogBackupTriggerQueue VALUES(99,0);""")
        yield owner, connect
    finally:
        owner.execute(RELEASE_SESSION)
        owner.close()


def due(owner, dashboard=0, summary=1):
    owner.execute(
        "BEGIN TRAN; EXEC dbo.usp_MaintenanceDue 'final_stats',@FinalDashboard=?,@FinalSummary=?; COMMIT",
        dashboard,
        summary,
    )


def upkeep(owner):
    cursor = owner.execute("EXEC dbo.usp_RunMaintenance 'final_stats'")
    while cursor.nextset():
        pass


def ledger(owner):
    return tuple(
        owner.execute(
            "SELECT DueGeneration,RequestedGeneration,State,FirstFailure FROM dbo.MaintenanceBackupWork"
        ).fetchone()
    )


def test_actual_upkeep_and_request_ack_are_separate(database):
    owner, _ = database
    due(owner, 1, 1)
    upkeep(owner)
    assert ledger(owner)[:3] == (0, 0, "requested")
    assert tuple(
        owner.execute(
            "SELECT DashboardCompletedGeneration,SummaryCompletedGeneration,State FROM dbo.MaintenanceWork WHERE Kind='final_stats'"
        ).fetchone()
    ) == (1, 1, "complete")
    assert (
        owner.execute(
            "SELECT rows_sampled FROM sys.dm_db_stats_properties(OBJECT_ID('dbo.ALL_STATS_FOR_DASHBAORD'),1)"
        ).fetchval()
        == 2
    )
    receipt = backup.run(owner.cursor(), lambda: {"outcome": "requested"})
    assert receipt["State"] == "requested" and receipt["backup_completed"] is None
    assert ledger(owner)[:3] == (1, 1, "requested")
    assert (
        owner.execute("SELECT Processed FROM dbo.LogBackupTriggerQueue WHERE ID=99").fetchval() == 0
    )


def test_dashboard_only_and_rolled_back_summary_never_request_backup(database):
    owner, _ = database
    due(owner, 1, 0)
    owner.execute("BEGIN TRAN; EXEC dbo.usp_MaintenanceDue 'final_stats',@FinalSummary=1; ROLLBACK")
    upkeep(owner)
    assert ledger(owner)[:3] == (0, 0, "requested")
    assert tuple(
        owner.execute(
            "SELECT DueGeneration,DashboardCompletedGeneration,SummaryCompletedGeneration FROM dbo.MaintenanceWork WHERE Kind='final_stats'"
        ).fetchone()
    ) == (1, 1, 0)


@pytest.mark.parametrize("outcome,state", [("unknown", "unknown"), ("not_attempted", "failed")])
def test_failed_or_unknown_never_replays_and_preserves_first_failure(database, outcome, state):
    owner, _ = database
    due(owner)
    upkeep(owner)
    backup.run(owner.cursor(), lambda: {"outcome": outcome})
    first = ledger(owner)[3]
    owner.execute(RELEASE_SESSION)
    due(owner)
    upkeep(owner)

    def forbidden():
        pytest.fail("Uncertain or failed backup was replayed")

    receipt = backup.run(owner.cursor(), forbidden)
    assert receipt["State"] == state and ledger(owner) == (2, 0, state, first)


def test_live_owner_then_absent_owner_becomes_unknown(database):
    owner, connect = database
    due(owner)
    upkeep(owner)
    claim = str(uuid4())
    owner.execute("EXEC dbo.usp_MaintenanceBackupClaim ?", claim).fetchall()
    worker = connect()
    try:
        assert backup.run(worker.cursor(), lambda: pytest.fail("busy dispatch"))["State"] == "busy"
        owner.execute(RELEASE_SESSION)
        assert (
            backup.run(worker.cursor(), lambda: pytest.fail("lost dispatch"))["State"] == "unknown"
        )
        assert ledger(owner)[3] == "owner_absent"
    finally:
        worker.execute(RELEASE_SESSION)
        worker.close()


def test_ack_is_exact_and_newer_due_remains_pending(database):
    owner, _ = database
    due(owner)
    upkeep(owner)
    claim = str(uuid4())
    owner.execute("EXEC dbo.usp_MaintenanceBackupClaim ?", claim).fetchall()
    with pytest.raises(Exception, match="51964"):
        owner.execute("EXEC dbo.usp_MaintenanceBackupAcknowledge ?,1,'requested'", str(uuid4()))
    owner.execute("UPDATE dbo.MaintenanceBackupWork SET DueGeneration=2")
    owner.execute("EXEC dbo.usp_MaintenanceBackupAcknowledge ?,1,'requested'", claim).fetchall()
    assert ledger(owner)[:3] == (2, 1, "pending")


def test_uncommitted_summary_cannot_dispatch_backup(database):
    owner, _ = database
    owner.execute("UPDATE dbo.MaintenanceBackupWork SET DueGeneration=1,State='pending'")
    assert (
        backup.run(owner.cursor(), lambda: pytest.fail("uncommitted upkeep dispatched"))["State"]
        == "pending"
    )


def test_actual_upkeep_failure_preserves_business_and_no_backup(database):
    owner, _ = database
    due(owner)
    owner.execute("DROP TABLE dbo.ALL_STATS_FOR_DASHBAORD")
    with pytest.raises(Exception, match="ALL_STATS_FOR_DASHBAORD"):
        upkeep(owner)
    assert owner.execute("SELECT COUNT(*) FROM dbo.EXCEL_FOR_DASHBOARD").fetchval() == 2
    assert (
        owner.execute("SELECT State FROM dbo.MaintenanceWork WHERE Kind='final_stats'").fetchval()
        == "failed"
    )
    assert ledger(owner)[:3] == (0, 0, "requested")


def test_unowned_child_and_transactional_backup_claim_refused(database):
    owner, _ = database
    with pytest.raises(Exception, match=r"51962|51961"):
        owner.execute("EXEC dbo.usp_MaintenanceFinalStats 1,1,1,?", str(uuid4()))
    owner.execute("BEGIN TRAN")
    try:
        with pytest.raises(Exception, match="51962"):
            owner.execute("EXEC dbo.usp_MaintenanceBackupClaim ?", str(uuid4()))
    finally:
        owner.execute("ROLLBACK")


def test_full_dal_holds_backup_owner_through_dispatch_and_releases(database, monkeypatch):
    import log_backup
    from services.maintenance_dal import SESSION_STATE, run_maintenance
    from services.maintenance_service import result

    owner, connect = database
    due(owner)
    calls = []

    def dispatch():
        worker = connect()
        try:
            assert (
                backup.run(worker.cursor(), lambda: pytest.fail("second dispatch"))["State"]
                == "busy"
            )
        finally:
            worker.close()
        calls.append(1)
        return {"outcome": "requested"}

    monkeypatch.setattr(log_backup, "trigger_log_backup_sync", dispatch)
    receipt = run_maintenance(connect)
    assert len(calls) == 1 and result(receipt)[0]
    assert receipt["backup_request"]["backup_completed"] is None
    connection = connect()
    try:
        assert tuple(connection.execute(SESSION_STATE).fetchone()) == (
            0,
            "NoLock",
            "NoLock",
            "NoLock",
            "NoLock",
            "NoLock",
        )
    finally:
        connection.close()


def test_lost_durable_ack_retains_unknown_without_second_dispatch(database, monkeypatch):
    import log_backup
    from services.maintenance_dal import run_maintenance

    owner, connect = database
    due(owner)
    owner.execute(
        "CREATE TRIGGER dbo.BackupAckFailure ON dbo.MaintenanceBackupWork AFTER UPDATE AS IF EXISTS(SELECT 1 FROM inserted WHERE RequestedGeneration>0) THROW 50047,'ack injection',1;"
    )
    calls = []
    monkeypatch.setattr(
        log_backup, "trigger_log_backup_sync", lambda: calls.append(1) or {"outcome": "requested"}
    )
    with pytest.raises(Exception, match="50047"):
        run_maintenance(connect)
    assert ledger(owner)[:3] == (1, 0, "running")
    owner.execute("DROP TRIGGER dbo.BackupAckFailure")
    receipt = run_maintenance(connect)
    assert len(calls) == 1 and receipt["backup_request"]["State"] == "unknown"


def test_report_schema_guard_and_maintenance_exclude_both_orders(database):
    owner, connect = database
    root = Path("C:/K98-bot-SQL-Server/sql_schema")
    owner.execute("CREATE ROLE K98ImportLockPrincipal")
    for name in ("ACQUIRE_KS4_IMPORT_LOCK", "usp_S11ValidateStatsReportStage"):
        source = (root / ("dbo." + name + ".StoredProcedure.sql")).read_text(encoding="utf-8-sig")
        source = source[source.index("CREATE OR ALTER PROCEDURE") :]
        for batch in re.split(r"(?im)^GO\s*$", source):
            if batch.strip():
                owner.execute(batch)
    worker = connect()
    try:
        due(owner)
        owner.execute("BEGIN TRAN; EXEC dbo.usp_S11ValidateStatsReportStage NULL,NULL")
        upkeep(worker)
        assert (
            owner.execute(
                "SELECT State FROM dbo.MaintenanceWork WHERE Kind='final_stats'"
            ).fetchval()
            == "pending"
        )
        owner.execute("ROLLBACK")
        worker.execute(
            "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource='K98:maintenance-schema:v1',@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; IF @r<0 THROW 50000,'fixture',1;"
        )
        owner.execute("BEGIN TRAN")
        with pytest.raises(Exception, match="51966"):
            owner.execute("EXEC dbo.usp_S11ValidateStatsReportStage NULL,NULL")
        owner.execute("ROLLBACK")
    finally:
        worker.execute(RELEASE_SESSION)
        worker.close()


def test_high_log_defers_statistics_but_still_requests_backup(database, monkeypatch):
    """Inject only the log observation; execute real dispatch/ownership SQL."""
    import log_backup
    from services.maintenance_dal import run_maintenance
    from services.maintenance_service import result

    owner, connect = database
    source = Path(
        "C:/K98-bot-SQL-Server/sql_schema/dbo.usp_RunMaintenance.StoredProcedure.sql"
    ).read_text(encoding="utf-8-sig")
    observation = "SELECT @log=used_log_space_in_percent FROM sys.dm_db_log_space_usage;"
    assert source.count(observation) == 1
    source = source[source.index("CREATE OR ALTER PROCEDURE") :].replace(
        observation, "SET @log=75.0;"
    )
    owner.execute(source)
    due(owner)
    calls = []
    monkeypatch.setattr(
        log_backup, "trigger_log_backup_sync", lambda: calls.append(1) or {"outcome": "requested"}
    )
    receipt = run_maintenance(connect)
    assert len(calls) == 1
    assert (
        next(row for row in receipt["maintenance"] if row["Kind"] == "final_stats")["State"]
        == "pending"
    )
    assert receipt["backup_request"]["State"] == "requested"
    assert not result(receipt)[0]


def test_backup_eligibility_survives_failed_upkeep(database):
    owner, _ = database
    due(owner)
    owner.execute(
        "UPDATE dbo.MaintenanceWork SET State='failed',FirstErrorNumber=50048 WHERE Kind='final_stats'"
    )
    receipt = backup.run(owner.cursor(), lambda: {"outcome": "requested"})
    assert receipt["State"] == "requested"
    assert (
        owner.execute(
            "SELECT FirstErrorNumber FROM dbo.MaintenanceWork WHERE Kind='final_stats'"
        ).fetchval()
        == 50048
    )
