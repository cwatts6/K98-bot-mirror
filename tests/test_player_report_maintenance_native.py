"""Actual player publication and deferred FULLSCAN in owned local databases."""

from pathlib import Path
import re

import pytest

from tests.sql_snapshot_fixture import snapshot_database as _database
from tests.test_configuration_maintenance_native import insert_scan
from tests.test_maintenance_owned_native import drain, state

ROOT = Path("C:/K98-bot-SQL-Server/sql_schema")


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
        owner.execute("CREATE ROLE K98ImportLockPrincipal; SET NOCOUNT ON")
        names = [
            "KingdomScanData4.Table",
            "STATS_FOR_UPLOAD.Table",
            "ProcConfig.Table",
            "KVKFinalReportHeader.Table",
            "EXEMPT_FROM_STATS.Table",
            "MaintenanceWork.Table",
            "v_ReportGovernorNames.View",
            "ACQUIRE_KS4_IMPORT_LOCK.StoredProcedure",
            "usp_ApplyReportGovernorNames.StoredProcedure",
            "usp_MaintenanceDue.StoredProcedure",
            "usp_MaintenancePlayerReport.StoredProcedure",
            "usp_RunMaintenance.StoredProcedure",
            "SP_Stats_for_Upload.StoredProcedure",
        ]
        for name in names:
            source = (ROOT / ("dbo." + name + ".sql")).read_text(encoding="utf-8-sig")
            if name == "KingdomScanData4.Table":
                # Same documented missing sequence definition as D3d: explicit
                # SCAN_UNO values, with only its unsupported default omitted.
                source = re.sub(
                    r"IF NOT EXISTS \(SELECT \* FROM sys.objects WHERE object_id = OBJECT_ID\(N'\[dbo\].\[DF_KS4_SCAN_UNO\]'\).*?\nEND\n",
                    "",
                    source,
                    flags=re.S,
                )
            if name == "SP_Stats_for_Upload.StoredProcedure":
                source = source[source.index("ALTER PROCEDURE") :].replace(
                    "ALTER PROCEDURE", "CREATE OR ALTER PROCEDURE", 1
                )
            for batch in re.split(r"(?im)^GO\s*$", source):
                if batch.strip():
                    drain(owner.execute(batch))
        insert_scan(owner)
        owner.execute("UPDATE dbo.KingdomScanData4 SET GovernorName=N'Current Name'")
        owner.execute(
            "INSERT dbo.ProcConfig(KVKVersion,ConfigKey,ConfigValue) VALUES(1,'MATCHMAKING_SCAN',1),(1,'KVK_END_SCAN',1)"
        )
        owner.execute(
            "INSERT dbo.KVKFinalReportHeader VALUES(1,SYSUTCDATETIME(),1,1,1,'OUTPUT_COMPLETE','LIVE_OUTPUT')"
        )
        owner.execute("SELECT TOP(0) * INTO dbo.EXCEL_FOR_KVK_1 FROM dbo.STATS_FOR_UPLOAD")
        owner.execute(
            "INSERT dbo.EXCEL_FOR_KVK_1(Gov_ID,Governor_Name,KVK_NO,[Starting Power],[T4_KILLS]) VALUES(1,N'Old Name',1,100,25)"
        )
        owner.execute(
            "INSERT dbo.STATS_FOR_UPLOAD(Gov_ID,Governor_Name,KVK_NO) VALUES(2,N'Previous',1)"
        )
        yield owner, connect
    finally:
        owner.close()


@pytest.mark.parametrize("outer_commit", [None, False, True])
def test_actual_publication_and_due_share_real_transaction(database, outer_commit):
    owner, connect = database
    if outer_commit is not None:
        owner.execute("BEGIN TRAN")
    drain(owner.execute("EXEC dbo.SP_Stats_for_Upload"))
    assert owner.execute("SELECT @@TRANCOUNT").fetchval() == int(outer_commit is not None)
    assert tuple(
        owner.execute(
            "SELECT Gov_ID,Governor_Name,[Starting Power],[T4_KILLS] FROM dbo.STATS_FOR_UPLOAD"
        ).fetchone()
    ) == (1, "Current Name", 100, 25)
    assert state(owner, "player_report")[:3] == (1, 0, "pending")
    if outer_commit is not None:
        observer = connect()
        try:
            observer.execute("SET LOCK_TIMEOUT 0")
            with pytest.raises(Exception, match="1222"):
                state(observer, "player_report")
        finally:
            observer.close()
        owner.execute("COMMIT" if outer_commit else "ROLLBACK")
    assert owner.execute("SELECT Gov_ID FROM dbo.STATS_FOR_UPLOAD").fetchval() == (
        2 if outer_commit is False else 1
    )
    assert state(owner, "player_report")[:3] == (
        (0, 0, "complete") if outer_commit is False else (1, 0, "pending")
    )


@pytest.mark.parametrize("fault", ["header", "due"])
def test_actual_business_failure_does_not_publish_or_queue(database, fault):
    owner, _ = database
    if fault == "header":
        owner.execute("UPDATE dbo.KVKFinalReportHeader SET OutputRowCount=2")
    else:
        owner.execute(
            "ALTER TABLE dbo.MaintenanceWork ADD CONSTRAINT RejectDue CHECK(Kind<>'player_report' OR DueGeneration=0)"
        )
    with pytest.raises(Exception, match=r"52811|52819"):
        drain(owner.execute("EXEC dbo.SP_Stats_for_Upload"))
    assert owner.execute("SELECT @@TRANCOUNT").fetchval() == 0
    assert owner.execute("SELECT Gov_ID FROM dbo.STATS_FOR_UPLOAD").fetchval() == 2
    assert state(owner, "player_report")[:3] == (0, 0, "complete")


def test_real_fullscan_occurs_after_successful_report(database):
    owner, _ = database
    drain(owner.execute("EXEC dbo.SP_Stats_for_Upload"))
    assert state(owner, "player_report")[:3] == (1, 0, "pending")
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'player_report'"))
    assert state(owner, "player_report")[:3] == (1, 1, "complete")
    stats = owner.execute(
        "SELECT p.rows,p.rows_sampled FROM sys.stats s CROSS APPLY sys.dm_db_stats_properties(s.object_id,s.stats_id) p WHERE s.object_id=OBJECT_ID('dbo.STATS_FOR_UPLOAD')"
    ).fetchall()
    assert stats and all(tuple(row) == (1, 1) for row in stats)
    assert (
        owner.execute("SELECT Governor_Name FROM dbo.STATS_FOR_UPLOAD").fetchval() == "Current Name"
    )


@pytest.mark.parametrize("kind", ["player_report", "post_import"])
def test_standalone_publication_defers_maintenance_before_claim(database, kind):
    owner, connect = database
    drain(owner.execute("EXEC dbo.SP_Stats_for_Upload"))
    if kind == "post_import":
        owner.execute("EXEC dbo.usp_MaintenanceDue 'post_import'")
    holder = connect()
    try:
        holder.execute(
            "BEGIN TRAN; DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource='K98:StatsForUpload:Publish',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=0; IF @r<0 THROW 50000,'fixture',1;"
        )
        drain(owner.execute("EXEC dbo.usp_RunMaintenance ?", kind))
        assert state(owner, kind)[:3] == (1, 0, "pending")
        assert state(owner, kind)[3] is None
    finally:
        holder.execute("ROLLBACK")
        holder.close()


def test_actual_upkeep_failure_preserves_committed_report_and_cannot_replay(database):
    import pyodbc

    owner, _ = database
    drain(owner.execute("EXEC dbo.SP_Stats_for_Upload"))
    # Retain the committed data while making the actual fixed FULLSCAN fail.
    owner.execute("EXEC sys.sp_rename 'dbo.STATS_FOR_UPLOAD','FixtureRetainedReport'")
    with pytest.raises(pyodbc.Error):
        drain(owner.execute("EXEC dbo.usp_RunMaintenance 'player_report'"))
    assert state(owner, "player_report")[:3] == (1, 0, "failed")
    assert owner.execute("SELECT Gov_ID FROM dbo.FixtureRetainedReport").fetchval() == 1
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'player_report'"))
    assert state(owner, "player_report")[:3] == (1, 0, "failed")
