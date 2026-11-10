"""Actual delta business transaction and deferred child in owned local databases."""

from pathlib import Path
import re

import pytest

from tests.sql_snapshot_fixture import snapshot_database as _database

ROOT = Path("C:/K98-bot-SQL-Server/sql_schema")
DELTAS = (
    "T4KillDelta",
    "T5KillDelta",
    "T4T5KillDelta",
    "POWERDelta",
    "KillPointsDelta",
    "DeadsDelta",
    "HelpsDelta",
    "RSSASSISTDelta",
    "RSSGatheredDelta",
    "HealedTroopsDelta",
    "RangedPointsDelta",
    "DeltaMetrics",
)


def drain(cursor):
    while cursor.nextset():
        pass


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
        names = [
            name + ".Table"
            for name in (
                *DELTAS,
                "KingdomScanData4",
                "MaintenanceWork",
                "MaintenanceConfigurationWork",
            )
        ]
        names += [
            name + ".StoredProcedure"
            for name in (
                "usp_MaintenanceDue",
                "usp_MaintenanceConfigurationDue",
                "usp_MaintenanceConfiguration",
                "usp_RunMaintenance",
                "CREATE_DELTA_TABLES",
            )
        ]
        for name in names:
            text = (ROOT / ("dbo." + name + ".sql")).read_text(encoding="utf-8-sig")
            if name == "KingdomScanData4.Table":
                # The repository references KS4_UNO_SEQ but has no sequence
                # definition. Omit only that default in this owned fixture and
                # provide explicit SCAN_UNO values; do not invent its contract.
                text = re.sub(
                    r"IF NOT EXISTS \(SELECT \* FROM sys.objects WHERE object_id = OBJECT_ID\(N'\[dbo\].\[DF_KS4_SCAN_UNO\]'\).*?\nEND\n",
                    "",
                    text,
                    flags=re.S,
                )
            if name == "CREATE_DELTA_TABLES.StoredProcedure":
                text = text[text.index("ALTER PROCEDURE") :].replace(
                    "ALTER PROCEDURE", "CREATE OR ALTER PROCEDURE", 1
                )
            for batch in re.split(r"(?im)^GO\s*$", text):
                if batch.strip():
                    drain(owner.execute(batch))
        owner.execute("SET NOCOUNT ON")
        yield owner, connect
    finally:
        owner.close()


def insert_scan(owner, scan=1):
    owner.execute(
        "INSERT dbo.KingdomScanData4 (GovernorID,SCANORDER,T4_Kills,T5_Kills,[T4&T5_KILLS],"
        "[Power],KillPoints,Deads,Helps,RSSAssistance,RSS_Gathered,HealedTroops,RangedPoints,"
        "PowerRank,T1_Kills,T2_Kills,T3_Kills,ScanDate,SCAN_UNO) "
        "VALUES (1,?,100,200,300,400,500,600,700,800,900,1000,1100,1,0,0,0,GETDATE(),?)",
        scan,
        scan,
    )


def state(owner):
    return tuple(
        owner.execute(
            "SELECT DueGeneration,CompletedGeneration,State FROM dbo.MaintenanceWork WHERE Kind='configuration'"
        ).fetchone()
    )


@pytest.mark.parametrize("outer_commit", [None, False, True])
def test_actual_delta_due_obeys_standalone_and_outer_transaction(database, outer_commit):
    owner, connect = database
    insert_scan(owner)
    if outer_commit is not None:
        owner.execute("BEGIN TRAN")
    drain(owner.execute("EXEC dbo.CREATE_DELTA_TABLES"))
    assert owner.execute("SELECT @@TRANCOUNT").fetchval() == int(outer_commit is not None)
    assert all(owner.execute(f"SELECT COUNT(*) FROM dbo.{name}").fetchval() == 1 for name in DELTAS)
    assert state(owner) == (1, 0, "pending")
    if outer_commit is not None:
        observer = connect()
        try:
            observer.execute("SET LOCK_TIMEOUT 0")
            with pytest.raises(Exception, match="1222"):
                state(observer)
        finally:
            observer.close()
        owner.execute("COMMIT" if outer_commit else "ROLLBACK")
    assert state(owner) == ((0, 0, "complete") if outer_commit is False else (1, 0, "pending"))
    assert owner.execute("SELECT DueRows FROM dbo.MaintenanceConfigurationWork").fetchval() == (
        0 if outer_commit is False else 1
    )


def test_no_new_rows_does_not_create_due_or_retain_delta_owner(database):
    owner, _ = database
    drain(owner.execute("EXEC dbo.CREATE_DELTA_TABLES"))
    assert state(owner) == (0, 0, "complete")
    assert (
        owner.execute(
            "SELECT APPLOCK_MODE('public','K98:TargetPublication:DeltaPreprocessing','Session')"
        ).fetchval()
        == "NoLock"
    )


def install_log(owner):
    drain(
        owner.execute((ROOT / "dbo.DeltaProcessingLog.Table.sql").read_text(encoding="utf-8-sig"))
    )


@pytest.mark.parametrize("log", [False, True])
def test_actual_child_and_optional_log_remain_after_business_commit(database, log):
    owner, _ = database
    if log:
        install_log(owner)
    insert_scan(owner)
    drain(owner.execute("EXEC dbo.CREATE_DELTA_TABLES"))
    if log:
        assert owner.execute("SELECT COUNT(*) FROM dbo.DeltaProcessingLog").fetchval() == 0
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'configuration'"))
    assert state(owner) == (1, 1, "complete")
    assert (
        owner.execute(
            "SELECT UpkeepCompletedGeneration FROM dbo.MaintenanceConfigurationWork"
        ).fetchval()
        == 1
    )
    if log:
        assert tuple(
            owner.execute(
                "SELECT RowsProcessed,MaintenanceRan FROM dbo.DeltaProcessingLog"
            ).fetchone()
        ) == (1, True)
    assert owner.execute("SELECT COUNT(*) FROM dbo.DeltaMetrics").fetchval() == 1


def test_optional_log_failure_preserves_business_and_upkeep_evidence(database):
    owner, _ = database
    install_log(owner)
    owner.execute(
        "ALTER TABLE dbo.DeltaProcessingLog ADD CONSTRAINT RejectTimingLog CHECK (RowsProcessed<0)"
    )
    insert_scan(owner)
    drain(owner.execute("EXEC dbo.CREATE_DELTA_TABLES"))
    with pytest.raises(Exception, match="547"):
        drain(owner.execute("EXEC dbo.usp_RunMaintenance 'configuration'"))
    assert state(owner) == (1, 0, "failed")
    assert tuple(
        owner.execute(
            "SELECT UpkeepCompletedGeneration,FirstLogErrorNumber FROM dbo.MaintenanceConfigurationWork"
        ).fetchone()
    ) == (1, 547)
    assert owner.execute("SELECT COUNT(*) FROM dbo.DeltaMetrics").fetchval() == 1
    # Exact failed packet is not automatically replayed to repair a timing log.
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'configuration'"))
    assert state(owner) == (1, 0, "failed")


def test_standalone_delta_owner_defers_maintenance_before_claim(database):
    owner, connect = database
    insert_scan(owner)
    drain(owner.execute("EXEC dbo.CREATE_DELTA_TABLES"))
    holder = connect()
    try:
        holder.execute(
            "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource='K98:TargetPublication:DeltaPreprocessing',@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; IF @r<0 THROW 50000,'fixture',1;"
        )
        drain(owner.execute("EXEC dbo.usp_RunMaintenance 'configuration'"))
        assert state(owner) == (1, 0, "pending")
        assert (
            owner.execute(
                "SELECT ClaimID FROM dbo.MaintenanceWork WHERE Kind='configuration'"
            ).fetchval()
            is None
        )
    finally:
        holder.close()
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'configuration'"))
    assert state(owner) == (1, 1, "complete")


def queue_rows(owner, rows):
    """Fixture producer exercises the real typed due helper under its mutex."""
    owner.execute(
        "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource='K98:TargetPublication:DeltaPreprocessing',@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; IF @r<0 THROW 50000,'fixture',1;"
    )
    try:
        owner.execute(
            "BEGIN TRAN; EXEC dbo.usp_MaintenanceConfigurationDue @RowsProcessed=?,@LastScan=1; COMMIT",
            rows,
        )
    finally:
        owner.execute(
            "EXEC sys.sp_releaseapplock @Resource='K98:TargetPublication:DeltaPreprocessing',@LockOwner='Session'"
        )


@pytest.mark.parametrize(
    "hours,prior_rows,expected", [(167, 4999, False), (168, 0, True), (1, 5000, True)]
)
def test_existing_week_and_row_thresholds(database, hours, prior_rows, expected):
    owner, _ = database
    install_log(owner)
    owner.execute(
        "INSERT dbo.DeltaProcessingLog(ExecutionTime,RowsProcessed,MaintenanceRan) VALUES(DATEADD(HOUR,-?,SYSUTCDATETIME()),0,1)",
        hours,
    )
    owner.execute(
        "INSERT dbo.DeltaProcessingLog(RowsProcessed,MaintenanceRan) VALUES(?,0)", prior_rows
    )
    queue_rows(owner, 1)
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'configuration'"))
    assert (
        owner.execute(
            "SELECT TOP 1 MaintenanceRan FROM dbo.DeltaProcessingLog ORDER BY LogID DESC"
        ).fetchval()
        == expected
    )


@pytest.mark.parametrize("batches,expected", [([2500, 2500, 1], False), ([5000, 1], True)])
def test_missing_optional_log_preserves_individual_batch_threshold(database, batches, expected):
    owner, _ = database
    for rows in batches:
        queue_rows(owner, rows)
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'configuration'"))
    assert owner.execute(
        "SELECT UpkeepDisposition FROM dbo.MaintenanceConfigurationWork"
    ).fetchval() == ("complete" if expected else "ineligible")
    assert owner.execute(
        "SELECT CompletedRows FROM dbo.MaintenanceConfigurationWork"
    ).fetchval() == sum(batches)


def test_coalesced_prior_batches_count_toward_logged_row_threshold(database):
    owner, _ = database
    install_log(owner)
    owner.execute(
        "INSERT dbo.DeltaProcessingLog(ExecutionTime,RowsProcessed,MaintenanceRan) VALUES(DATEADD(HOUR,-1,SYSUTCDATETIME()),0,1)"
    )
    for rows in (2500, 2500, 1):
        queue_rows(owner, rows)
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'configuration'"))
    assert tuple(
        owner.execute(
            "SELECT TOP 1 RowsProcessed,MaintenanceRan FROM dbo.DeltaProcessingLog ORDER BY LogID DESC"
        ).fetchone()
    ) == (5001, True)


@pytest.mark.parametrize("fault", [False, True])
def test_real_large_fragmented_delta_index_is_rebuilt(database, fault):
    owner, _ = database
    owner.execute(
        "ALTER TABLE dbo.T4KillDelta ADD FixturePayload char(800) NULL; CREATE CLUSTERED INDEX [IX_D3d]]Fixture] ON dbo.T4KillDelta(GovernorID)"
    )
    drain(
        owner.execute(
            "SET NOCOUNT ON; DECLARE @i int=0; WHILE @i<11000 BEGIN INSERT dbo.T4KillDelta(GovernorID,DeltaOrder,T4KILLSDelta,FixturePayload) VALUES(CHECKSUM(NEWID()),1,1,REPLICATE(CHAR(65),800)); SET @i+=1; END; CHECKPOINT;"
        )
    )
    query = "SELECT avg_fragmentation_in_percent,page_count FROM sys.dm_db_index_physical_stats(DB_ID(),OBJECT_ID('dbo.T4KillDelta'),1,NULL,'LIMITED')"
    before, pages = owner.execute(query).fetchone()
    assert before > 50 and pages > 1000
    queue_rows(owner, 11000)
    if fault:
        source = (
            (ROOT / "dbo.usp_MaintenanceConfiguration.StoredProcedure.sql")
            .read_text()
            .split("GO\n", 1)[-1]
        )
        owner.execute(
            source.replace(
                "EXEC sp_executesql @SQL;",
                "EXEC sp_executesql @SQL; THROW 50042,'Fixture child failure',1;",
            )
        )
        with pytest.raises(Exception, match="50042"):
            drain(owner.execute("EXEC dbo.usp_RunMaintenance 'configuration'"))
        assert state(owner)[-1] == "failed"
        assert owner.execute("SELECT CURSOR_STATUS('global','index_cursor')").fetchval() == -3
        assert (
            owner.execute(
                "SELECT FirstErrorNumber FROM dbo.MaintenanceWork WHERE Kind='configuration'"
            ).fetchval()
            == 50042
        )
    else:
        drain(owner.execute("EXEC dbo.usp_RunMaintenance 'configuration'"))
        assert state(owner)[-1] == "complete"
    assert owner.execute(query).fetchone()[0] < before
    assert owner.execute("SELECT COUNT(*) FROM dbo.T4KillDelta").fetchval() == 11000


def test_failed_summary_ack_rolls_back_completion_without_replaying_upkeep(database):
    owner, _ = database
    install_log(owner)
    insert_scan(owner)
    drain(owner.execute("EXEC dbo.CREATE_DELTA_TABLES"))
    owner.execute(
        "ALTER TABLE dbo.MaintenanceConfigurationWork ADD CONSTRAINT RejectAck CHECK(CompletedRows=0)"
    )
    with pytest.raises(Exception, match="547"):
        drain(owner.execute("EXEC dbo.usp_RunMaintenance 'configuration'"))
    assert owner.execute("SELECT @@TRANCOUNT").fetchval() == 0
    assert state(owner) == (1, 0, "failed")
    assert tuple(
        owner.execute(
            "SELECT CompletedRows,UpkeepCompletedGeneration FROM dbo.MaintenanceConfigurationWork"
        ).fetchone()
    ) == (0, 1)
    assert owner.execute("SELECT COUNT(*) FROM dbo.DeltaProcessingLog").fetchval() == 1
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'configuration'"))
    assert owner.execute("SELECT COUNT(*) FROM dbo.DeltaProcessingLog").fetchval() == 1


def test_actual_child_failure_does_not_relabel_committed_delta_data(database):
    import pyodbc

    owner, _ = database
    install_log(owner)
    insert_scan(owner)
    drain(owner.execute("EXEC dbo.CREATE_DELTA_TABLES"))
    owner.execute("DROP TABLE dbo.T5KillDelta")
    with pytest.raises(pyodbc.Error):
        drain(owner.execute("EXEC dbo.usp_RunMaintenance 'configuration'"))
    assert state(owner) == (1, 0, "failed")
    assert (
        owner.execute(
            "SELECT FirstErrorNumber FROM dbo.MaintenanceWork WHERE Kind='configuration'"
        ).fetchval()
        is not None
    )
    assert (
        owner.execute(
            "SELECT UpkeepCompletedGeneration FROM dbo.MaintenanceConfigurationWork"
        ).fetchval()
        == 0
    )
    assert owner.execute("SELECT COUNT(*) FROM dbo.DeltaMetrics").fetchval() == 1
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'configuration'"))
    assert state(owner) == (1, 0, "failed")
