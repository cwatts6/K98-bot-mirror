"""Real SQL guards/checkpoints with isolated tables and simulated report calculations.

The actual report procedure is separately compiled unchanged. Behavioral tests
replace only its large business calculations with counted transactional writes;
all stage control, guard checks, receipts and final execution update are real SQL.
"""

import os
from pathlib import Path
import re
from types import SimpleNamespace
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.stats_report_continuation import StatsReportContinuation
from services.stats_report_continuation_dal import StatsReportContinuationDAL
from tests.test_import_capture_recovery_sql import recovery as recovery

pytestmark = [
    pytest.mark.skipif(os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Local SQL opt-in"),
    pytest.mark.parametrize("recovery", ["scan_data"], indirect=True),
]


@pytest.fixture
def reports(recovery):
    r = recovery
    schema = Path(os.environ["K98_CAPTURE_SQL_SCHEMA"])
    namespace = uuid4().hex
    names = {
        "dbo." + name: "##Report_" + namespace + "_" + name
        for name in (
            "StatsImportReportContinuation",
            "ProcConfig",
            "KingdomScanData4",
            "KS4_ImportFileClaim",
            "Update_ALL_Complete",
            "StageProbe",
            "StageFailure",
            "usp_S11ValidateStatsReportStage",
            "usp_S11CompleteStatsReportsCore",
            "usp_S11CompleteStatsReports",
            "ARCHIVE_IMPORT_STAGING_FILE",
        )
    }

    def rewrite(sql):
        for source, target in names.items():
            sql = sql.replace(source, target)
        sql = sql.replace(
            "N'S11:stats-import:'", "N'" + r.parameter("S11:stats-import:") + "'"
        ).replace(
            "N'k98-legacy-output-snapshot'",
            "N'" + r.parameter("k98-legacy-output-snapshot") + "'",
        )
        return r.rewrite(sql)

    class Cursor:
        def __init__(self, inner):
            self.inner = inner

        def execute(self, sql, *args):
            self.inner.execute(rewrite(sql), *args)
            return self

        def __getattr__(self, key):
            return getattr(self.inner, key)

    class Connection:
        def __init__(self):
            self.inner = r.connect()

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

    raw = (schema / "dbo.StatsImportReportContinuation.Table.sql").read_text(encoding="utf-8-sig")
    raw = "\n".join(line for line in raw.splitlines() if "FOREIGN KEY" not in line)
    raw = re.sub(r"CONSTRAINT (\w+)", lambda m: "CONSTRAINT " + m[1] + "_" + namespace, raw)
    r.owner.execute(rewrite(raw))
    r.owner.execute(rewrite("""
        CREATE TABLE dbo.ProcConfig(KVKVersion int,ConfigKey varchar(50),ConfigValue float,LastUpdated datetime);
        CREATE TABLE dbo.KingdomScanData4(SCANORDER int);
        CREATE TABLE dbo.KS4_ImportFileClaim(CompletedFileName nvarchar(260),FileDigest binary(32),ClaimStatus nvarchar(24));
        CREATE TABLE dbo.Update_ALL_Complete(CompletionTime datetime);
        CREATE TABLE dbo.StageProbe(Stage int);
        CREATE TABLE dbo.StageFailure(Stage int);
        INSERT dbo.ProcConfig VALUES(16,'MATCHMAKING_SCAN',1,'2026-10-22');
        INSERT dbo.KingdomScanData4 VALUES(1);
        UPDATE dbo.ExportPreparation SET GenerationJson=NULL,State='uncertain';
        UPDATE dbo.StatsImportExecution SET State='partial',ScanOrder=1,LastRunCounter=NULL;
        INSERT dbo.KS4_ImportFileClaim
            SELECT CompletedFileName,CAST(0x01 AS binary(32)),'archived' FROM dbo.StatsImportExecution;
        INSERT dbo.StatsImportReportContinuation
            (PreparationID,InputDigest,ScanOrder,LatestScanOrder,KingdomRank,KingdomSeed,ConfigurationJson,RowsKS5,RowsKS4,ImportStartedUTC)
        SELECT PreparationID,CAST(0x01 AS binary(32)),1,1,1,'A',
            (SELECT KVKVersion,ConfigKey,ConfigValue,LastUpdated FROM dbo.ProcConfig ORDER BY KVKVersion,ConfigKey FOR JSON PATH,INCLUDE_NULL_VALUES),
            10,10,GETDATE() FROM dbo.StatsImportExecution;
    """))
    procedures = []
    try:
        # Syntax/binding compilation of the unchanged business procedure. It is
        # never executed in master and references no real production database.
        raw = (schema / "dbo.usp_S11CompleteStatsReportsCore.StoredProcedure.sql").read_text(
            encoding="utf-8-sig"
        )
        compile_name = "##ReportCompile_" + namespace
        body = raw[raw.index("CREATE OR ALTER PROCEDURE") :].replace(
            "dbo.usp_S11CompleteStatsReportsCore", compile_name, 1
        )
        r.owner.execute(body)
        procedures.append(compile_name)

        guard = (schema / "dbo.usp_S11ValidateStatsReportStage.StoredProcedure.sql").read_text(
            encoding="utf-8-sig"
        )
        guard = guard[guard.index("CREATE OR ALTER PROCEDURE") :]
        guard = guard.replace(
            "EXEC dbo.ACQUIRE_KS4_IMPORT_LOCK @LockTimeout=0,@LockResult=@LockResult OUTPUT;",
            "EXEC @LockResult=sys.sp_getapplock @Resource=N'test:"
            + namespace
            + ":scan-writer',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=0;",
        )
        r.owner.execute(rewrite(guard))
        procedures.append(names["dbo.usp_S11ValidateStatsReportStage"])

        def probe(stage):
            return f"INSERT dbo.StageProbe VALUES({stage}); IF EXISTS(SELECT 1 FROM dbo.StageFailure WHERE Stage={stage}) THROW 51962,'injected report failure',1;"

        start = raw.index("        -- Step 1: CREATE_THE_AVERAGES")
        end = raw.index("            IF @ExportPreparationID IS NOT NULL", start)
        body = (
            raw[:start]
            + "DECLARE @LatestKVK_Upload int=16,@ScanToUse_Upload int=1;\n"
            + probe(1)
            + "\n"
            + raw[end:]
        )
        # Diagnostic DMV/DBCC reads are compiled above with the real procedure;
        # the transaction fault fixture must not checkpoint its host database.
        start = body.index("        -- *** NEW: Check log space at Phase B start ***")
        end = body.index("        IF @CompletedStage=0", start)
        body = body[:start] + body[end:]
        body = body.replace("EXEC dbo.SP_Stats_for_Upload;", "BEGIN " + probe(2) + " END;")
        start = body.index(
            "        ----------------------------------------------------------------\n        -- ⚡⚡⚡"
        )
        end = body.index("        IF @ExportPreparationID IS NOT NULL", start)
        body = (
            body[:start]
            + probe(3)
            + "\nDECLARE @S11CompletionCounters TABLE(LastRunCounter int); INSERT @S11CompletionCounters VALUES(42);\n"
            + body[end:]
        )
        start = body.index("\n        SELECT\n            PhaseName")
        end = body.index("\n    END TRY", start)
        body = body[:start] + body[end:]
        body = body[body.index("CREATE OR ALTER PROCEDURE") :]
        assert not re.search(r"\b(?:dbo|KVK)\.[A-Za-z_]", rewrite(body))
        r.owner.execute(rewrite(body))
        procedures.append(names["dbo.usp_S11CompleteStatsReportsCore"])
        wrapper = (schema / "dbo.usp_S11CompleteStatsReports.StoredProcedure.sql").read_text(
            encoding="utf-8-sig"
        )
        wrapper = wrapper[wrapper.index("CREATE OR ALTER PROCEDURE") :]
        r.owner.execute(rewrite(wrapper))
        procedures.append(names["dbo.usp_S11CompleteStatsReports"])
        r.owner.execute(
            rewrite(
                "CREATE PROCEDURE dbo.ARCHIVE_IMPORT_STAGING_FILE @CompletedFileName nvarchar(260) AS BEGIN RETURN 0; END"
            )
        )
        procedures.append(names["dbo.ARCHIVE_IMPORT_STAGING_FILE"])

        from services.stats_import_outcome_dal import StatsImportOutcomeDAL

        outcomes = StatsImportOutcomeDAL(Connection, account="a", storage_owner="disk-a")
        dal = StatsReportContinuationDAL(outcomes)
        yield SimpleNamespace(
            dal=dal,
            adapter=StatsReportContinuation(dal),
            source=r.source,
            owner=r.owner,
            rewrite=rewrite,
            connect=Connection,
            base=r,
        )
    finally:
        for procedure in reversed(procedures):
            r.owner.execute("DROP PROCEDURE " + procedure)


@pytest.mark.parametrize("failed_stage", [1, 2, 3])
def test_partial_repair_retries_only_uncommitted_stage(reports, failed_stage):
    r = reports
    r.owner.execute(r.rewrite("INSERT dbo.StageFailure VALUES(?)"), failed_stage)
    first = r.dal.inspect(r.source)
    action_id = str(uuid4())
    with pytest.raises(Exception, match="injected report failure"):
        r.dal.run(r.source, first["token"], action_id)
    after = r.dal.inspect(r.source)
    assert after["receipt"]["CompletedStage"] == failed_stage - 1
    assert after["receipt"]["RecoveryState"] == "failed"
    # Same failed action must not retry without another explicit confirmation.
    with pytest.raises(SourceConflict, match="attempt ended"):
        r.dal.run(r.source, first["token"], action_id)
    r.owner.execute(r.rewrite("DELETE dbo.StageFailure"))
    action_id = str(uuid4())
    r.dal.run(r.source, after["token"], action_id)
    assert r.dal.inspect(r.source)["complete"]
    assert [
        row[0]
        for row in r.owner.execute(r.rewrite("SELECT Stage FROM dbo.StageProbe ORDER BY Stage"))
    ] == [1, 2, 3]
    assert (
        r.owner.execute(r.rewrite("SELECT COUNT(*) FROM dbo.Update_ALL_Complete")).fetchval() == 1
    )
    # Lost final acknowledgement is a readback; no summary append repeats.
    r.dal.run(r.source, after["token"], action_id)
    assert r.owner.execute(r.rewrite("SELECT COUNT(*) FROM dbo.StageProbe")).fetchval() == 3


@pytest.mark.parametrize(
    "mutation",
    [
        "UPDATE dbo.ProcConfig SET ConfigValue=2",
        "UPDATE dbo.KingdomScanData4 SET SCANORDER=2",
        "UPDATE dbo.KS4_ImportFileClaim SET FileDigest=CAST(0x02 AS binary(32))",
        "UPDATE dbo.ExportResource SET OwnerID=NEWID()",
        "UPDATE dbo.ExportResource SET ActivePreparationID=NULL,OwnerID=NULL",
    ],
)
def test_changed_inputs_or_released_ownership_never_authorize_reports(reports, mutation):
    r = reports
    token = r.dal.inspect(r.source)["token"]
    r.owner.execute(r.rewrite(mutation))
    with pytest.raises(SourceConflict):
        r.dal.run(r.source, token, str(uuid4()))
    assert r.owner.execute(r.rewrite("SELECT COUNT(*) FROM dbo.StageProbe")).fetchval() == 0


def test_missing_contract_is_not_backfilled_and_stale_confirmation_is_rejected(reports):
    r = reports
    token = r.dal.inspect(r.source)["token"]
    r.owner.execute(r.rewrite("UPDATE dbo.StatsImportReportContinuation SET Version=Version+1"))
    with pytest.raises(SourceConflict, match="evidence changed"):
        r.dal.run(r.source, token, str(uuid4()))
    r.owner.execute(r.rewrite("DELETE dbo.StatsImportReportContinuation"))
    with pytest.raises(SourceConflict, match="Historical partial"):
        r.dal.inspect(r.source)


@pytest.mark.parametrize("arguments", ["", ", @ExportPreparationID=NULL"])
@pytest.mark.parametrize("dynamic", [False, True])
def test_direct_reporting_without_receipt_is_rejected_before_writes(reports, arguments, dynamic):
    r = reports
    statement = "EXEC dbo.usp_S11CompleteStatsReports @CompletedFileName=N'test.csv'" + arguments
    if dynamic:
        statement = "EXEC sys.sp_executesql N'" + statement.replace("'", "''") + "'"
    with pytest.raises(Exception, match="Recovery reporting requires a preparation ID"):
        r.owner.execute(r.rewrite(statement))
    assert r.owner.execute(r.rewrite("SELECT COUNT(*) FROM dbo.StageProbe")).fetchval() == 0
    assert (
        r.owner.execute(r.rewrite("SELECT COUNT(*) FROM dbo.Update_ALL_Complete")).fetchval() == 0
    )
    assert r.owner.execute("SELECT @@TRANCOUNT").fetchval() == 0


def test_nonnull_reporting_still_requires_both_producer_guards(reports):
    r = reports
    with pytest.raises(Exception, match="Both independent producer session guards"):
        r.owner.execute(
            r.rewrite(
                "EXEC dbo.usp_S11CompleteStatsReports "
                "@CompletedFileName=N'test.csv',@ExportPreparationID=?"
            ),
            str(uuid4()),
        )
    assert r.owner.execute(r.rewrite("SELECT COUNT(*) FROM dbo.StageProbe")).fetchval() == 0
    assert r.owner.execute("SELECT @@TRANCOUNT").fetchval() == 0


def test_natural_import_session_uses_both_guards_and_preserves_custody(reports, monkeypatch):
    """Reproduce the split-session refusal, then exercise the corrected borrower.

    Real SQL locks and the deployed validator are used; no import is replayed.
    Business reporting stays on the fixture's counted transactional probes.
    """
    from services import legacy_export_snapshot_service as snapshots
    from services.stats_import_outcome_service import execution_connection

    r = reports
    runtime = object()
    connection = r.connect()
    connection.autocommit = True
    connection.timeout = 15
    owner = SimpleNamespace(connection=connection, runtime=runtime, kind="scan_data", closed=False)
    monkeypatch.setattr(snapshots, "current_owner", lambda: owner)
    monkeypatch.setattr(snapshots, "require_runtime", lambda: runtime)
    snapshot_lock, import_lock = r.dal.guards.guards(r.source)

    def lock(conn, resource):
        cursor = conn.cursor()
        cursor.execute(
            "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; SELECT @r",
            r.base.parameter(resource),
        )
        assert cursor.fetchone()[0] >= 0
        cursor.close()

    def validate(conn):
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute(
                "EXEC dbo.usp_S11ValidateStatsReportStage ?,?",
                r.source,
                "stats_" + "a" * 32 + ".ready.csv",
            )
            while cursor.nextset():
                pass
        finally:
            cursor.execute("IF @@TRANCOUNT>0 ROLLBACK")
            cursor.close()

    try:
        lock(connection, snapshot_lock)
        separate = r.connect()
        separate.autocommit = True
        try:
            lock(separate, import_lock)
            with pytest.raises(Exception, match="Both independent producer session guards"):
                validate(separate)
        finally:
            cursor = separate.cursor()
            cursor.execute(
                "EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'",
                r.base.parameter(import_lock),
            )
            cursor.close()
            separate.close()
        with execution_connection(
            lambda: pytest.fail("separate producer"), timeout_seconds=600
        ) as actual:
            assert actual is connection
            lock(actual, import_lock)
            # Use the fixture's exact immutable filename, not an invented input.
            cursor = actual.cursor()
            cursor.execute(
                "SELECT CompletedFileName FROM dbo.StatsImportExecution WHERE PreparationID=?",
                r.source,
            )
            filename = cursor.fetchone()[0]
            cursor.execute(
                "EXEC dbo.usp_S11CompleteStatsReports @CompletedFileName=?,@ExportPreparationID=?",
                filename,
                r.source,
            )
            while cursor.nextset():
                pass
            cursor.close()
        assert connection.timeout == 15
        cursor = connection.cursor()
        cursor.execute("SELECT APPLOCK_MODE('public',?,'Session')", r.base.parameter(snapshot_lock))
        assert cursor.fetchone()[0] == "Exclusive"
        cursor.close()
        assert r.owner.execute(r.rewrite("SELECT COUNT(*) FROM dbo.StageProbe")).fetchval() == 3
        assert (
            r.owner.execute(
                r.rewrite("SELECT CompletedStage FROM dbo.StatsImportReportContinuation")
            ).fetchval()
            == 3
        )
    finally:
        cursor = connection.cursor()
        for resource in (import_lock, snapshot_lock):
            cursor.execute(
                "EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'",
                r.base.parameter(resource),
            )
        cursor.close()
        connection.close()
