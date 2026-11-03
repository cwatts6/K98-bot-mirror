"""Real SQL interleavings on unique temp tables, never business tables or procedures."""

import os
from pathlib import Path
import threading
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit
from services.all_kvk_capture_recovery_dal import AllKvkCaptureRecoveryDAL
from services.legacy_export_snapshot_dal import LegacySnapshotDAL, PreparationClaim
from services.player_report_recovery_dal import PlayerReportRecoveryDAL
from services.stats_import_outcome_dal import ImportExecutionActive, StatsImportOutcomeDAL
from services.unreceipted_producer_recovery import UnreceiptedProducerDAL

pytestmark = pytest.mark.skipif(
    os.environ.get("K98_CHECKPOINT_SQL") != "LOCAL_TEMP_ONLY",
    reason="Explicit local temporary-table SQL verification required",
)


@pytest.fixture
def database():
    import pyodbc

    def native():
        cn = pyodbc.connect(
            r"DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\K98DEV;"
            "DATABASE=master;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;",
            autocommit=True,
            timeout=5,
        )
        cn.timeout = 5
        server, db = cn.execute("SELECT @@SERVERNAME,DB_NAME()").fetchone()
        assert server.lower() == r"9sx2vf4\k98dev" and db == "master"
        cn.execute("SET LOCK_TIMEOUT 100")
        return cn

    root = native()
    nonce = uuid4().hex[:12]
    names = {
        name: "##checkpoint_" + nonce + "_" + name
        for name in ("ExportPreparation", "ExportResource", "StatsImportExecution")
    }
    prep, owner = str(uuid4()), str(uuid4())
    filename = "stats_" + uuid4().hex + ".ready.csv"
    account = "checkpoint_" + nonce
    key = "sql_snapshot:legacy_outputs"
    claim = PreparationClaim(prep, account, owner, 1, 1, ((key, 1),))
    hooks = {}
    sessions = []

    class Cursor:
        def __init__(self, cursor):
            self.cursor = cursor
            self.query = ""

        def __getattr__(self, name):
            return getattr(self.cursor, name)

        def execute(self, query, *args):
            self.query = query
            for old, new in names.items():
                query = query.replace("dbo." + old, new)
            try:
                self.cursor.execute(query, *args)
            except Exception:
                if hooks.get("error"):
                    hooks["error"]()
                raise
            return self

        def fetchone(self):
            result = self.cursor.fetchone()
            if hooks.get("row"):
                hooks["row"](self.query)
            return result

    class Connection:
        def __init__(self):
            self.cn = native()
            self.cn.autocommit = False
            self.committed = False
            self.closed = False
            sessions.append(self)

        @property
        def autocommit(self):
            return self.cn.autocommit

        def cursor(self):
            return Cursor(self.cn.cursor())

        def rollback(self):
            self.cn.rollback()

        def commit(self):
            self.cn.commit()
            self.committed = True
            if hooks.get("commit"):
                hooks["commit"]()

        def close(self):
            self.cn.close()
            self.closed = True

    try:
        root.execute(
            f"CREATE TABLE {names['ExportPreparation']} (PreparationID uniqueidentifier PRIMARY KEY,AccountKey varchar(128),StorageOwner varchar(128),ConsumerKind varchar(32),OwnerID uniqueidentifier,Fence bigint,Version bigint,State varchar(24),JobID uniqueidentifier NULL,SpoolKey varchar(128) NULL,GenerationJson nvarchar(max) NULL,UpdatedUTC datetime2 DEFAULT SYSUTCDATETIME())"
        )
        root.execute(
            f"CREATE TABLE {names['ExportResource']} (ResourceKey varchar(256) PRIMARY KEY,ActivePreparationID uniqueidentifier,ActiveJobID uniqueidentifier NULL,ActiveOutputOperationID uniqueidentifier NULL,OwnerID uniqueidentifier,Fence bigint,Version bigint,BlockedReason nvarchar(100) NULL)"
        )
        root.execute(
            f"CREATE TABLE {names['StatsImportExecution']} (PreparationID uniqueidentifier PRIMARY KEY,OwnerID uniqueidentifier,Fence bigint,State varchar(24),Resolution varchar(24) NULL,CompletedFileName nvarchar(260))"
        )
        root.execute(
            f"INSERT {names['ExportPreparation']} (PreparationID,AccountKey,StorageOwner,ConsumerKind,OwnerID,Fence,Version,State) VALUES (?,?,'local','scan_data',?,1,1,'writing')",
            prep,
            account,
            owner,
        )
        root.execute(
            f"INSERT {names['ExportResource']} VALUES (?,?,NULL,NULL,?,1,1,NULL)", key, prep, owner
        )
        root.execute(
            f"INSERT {names['StatsImportExecution']} VALUES (?,?,1,'completed',NULL,?)",
            prep,
            owner,
            filename,
        )
        yield dict(
            root=root,
            names=names,
            native=native,
            connect=Connection,
            claim=claim,
            hooks=hooks,
            sessions=sessions,
            generation=dict(
                completion="committed",
                capture="pending",
                commit_identity=prep,
                producer=dict(procedure="dbo.UPDATE_ALL2", completed_filename=filename),
            ),
        )
    finally:
        for name in reversed(tuple(names.values())):
            root.execute(f"DROP TABLE IF EXISTS {name}")
        root.close()


def checkpoint(db):
    return LegacySnapshotDAL(db["connect"]).transition(
        db["claim"], expected="writing", state="committed", generation=db["generation"]
    )


@pytest.mark.parametrize(
    "observer_type",
    [
        StatsImportOutcomeDAL,
        UnreceiptedProducerDAL,
        AllKvkCaptureRecoveryDAL,
        PlayerReportRecoveryDAL,
    ],
)
def test_writer_guard_excludes_every_observer_through_checkpoint_gap(database, observer_type):
    db = database
    holder = db["native"]()
    holder.execute(
        "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource='k98-legacy-output-snapshot',@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; IF @r<0 THROW 50000,'Test guard unavailable',1;"
    )
    try:
        observer = observer_type(db["connect"], account=db["claim"].account, storage_owner="local")
        with pytest.raises(ImportExecutionActive):
            observer.inspect(db["claim"].preparation_id)
        assert all(c.closed for c in db["sessions"])
        # The exact SQL execution guard is free, but the capture guard still owns work.
        assert checkpoint(db).version == 2
    finally:
        holder.execute(
            "EXEC sys.sp_releaseapplock @Resource='k98-legacy-output-snapshot',@LockOwner='Session'"
        )
        holder.close()


def test_observer_first_serializes_checkpoint_without_opposed_row_wait(database):
    db = database
    entered, release, refused = threading.Event(), threading.Event(), threading.Event()
    outcomes = []

    def pause(query):
        if (
            threading.current_thread().name == "observer"
            and "SELECT * FROM dbo.ExportPreparation" in query
        ):
            entered.set()
            assert release.wait(5)

    db["hooks"].update(row=pause, error=refused.set)

    def observe():
        try:
            outcomes.append(
                StatsImportOutcomeDAL(
                    db["connect"], account=db["claim"].account, storage_owner="local"
                ).inspect(db["claim"].preparation_id)
            )
        except BaseException as error:
            outcomes.append(error)

    def write():
        try:
            outcomes.append(checkpoint(db))
        except BaseException as error:
            outcomes.append(error)

    observer = threading.Thread(target=observe, name="observer")
    writer = threading.Thread(target=write)
    observer.start()
    try:
        assert entered.wait(5)
        writer.start()
        assert refused.wait(5)
    finally:
        release.set()
        observer.join(8)
        if writer.ident:
            writer.join(8)
    assert not observer.is_alive() and not writer.is_alive()
    assert not any(isinstance(r, BaseException) for r in outcomes), outcomes
    assert len(outcomes) == 2 and all(c.closed for c in db["sessions"])
    assert (
        db["root"].execute(f"SELECT Version FROM {db['names']['ExportPreparation']}").fetchval()
        == 2
    )


@pytest.mark.parametrize("change_fence", [False, True])
def test_real_row_timeout_retries_only_checkpoint_and_rechecks_ownership(database, change_fence):
    db = database
    holder = db["native"]()
    holder.execute("BEGIN TRANSACTION")
    holder.execute(
        f"UPDATE {db['names']['ExportPreparation']} SET Fence=Fence+?", int(change_fence)
    )
    timed_out = threading.Event()
    db["hooks"]["error"] = timed_out.set
    results = []

    def write():
        try:
            results.append(checkpoint(db))
        except BaseException as error:
            results.append(error)

    worker = threading.Thread(target=write)
    try:
        worker.start()
        assert timed_out.wait(5)
        holder.execute("COMMIT")
        worker.join(8)
        assert not worker.is_alive()
        assert len(db["sessions"]) >= 2 and all(c.closed for c in db["sessions"])
        if change_fence:
            assert isinstance(results[0], SourceConflict)
        else:
            assert results[0].version == 2
        assert db["root"].execute(
            f"SELECT Version FROM {db['names']['ExportPreparation']}"
        ).fetchval() == (1 if change_fence else 2)
    finally:
        holder.execute("IF @@TRANCOUNT>0 ROLLBACK")
        holder.close()
        worker.join(8)


def test_lost_commit_ack_is_not_retried_and_durable_version_survives_restart(database):
    db = database

    def lose_ack():
        raise OSError("lost acknowledgement")

    db["hooks"]["commit"] = lose_ack
    with pytest.raises(UncertainCommit):
        checkpoint(db)
    assert len(db["sessions"]) == 1 and db["sessions"][0].closed
    assert tuple(
        db["root"]
        .execute(f"SELECT State,Version FROM {db['names']['ExportPreparation']}")
        .fetchone()
    ) == ("committed", 2)
    db["hooks"].clear()
    with pytest.raises(SourceConflict):
        checkpoint(db)  # A fresh DAL cannot overwrite or replay the committed old claim.


def test_diagnostic_sampler_attributes_waiter_and_holder_without_sql_text(database):
    db = database
    script = Path(r"C:\K98-bot-SQL-Server\deploy\recovery\Observe-CheckpointBlocking.sql")
    # Same diagnostic query, scoped to the local temporary-table fixture and one second.
    sql = (
        script.read_text()
        .replace("DB_NAME() <> N'ROK_TRACKER'", "DB_NAME() <> N'master'")
        .replace("DATEADD(second, 15, @Started)", "DATEADD(second, 1, @Started)")
    )
    holder, waiter = db["native"](), db["native"]()
    held_spid = holder.execute("SELECT @@SPID").fetchval()
    wait_spid = waiter.execute("SELECT @@SPID").fetchval()
    waiter.execute("SET LOCK_TIMEOUT 5000")
    holder.execute("BEGIN TRANSACTION")
    holder.execute(f"UPDATE {db['names']['ExportResource']} SET Version=Version")
    errors = []

    def wait_for_row():
        try:
            waiter.execute(f"SELECT Version FROM {db['names']['ExportResource']}").fetchall()
        except BaseException as error:
            errors.append(error)

    worker = threading.Thread(target=wait_for_row)
    try:
        worker.start()
        cursor = db["root"].execute(sql)
        summary = cursor.fetchone()
        assert summary[3] > 0
        assert cursor.nextset()
        columns = [d[0] for d in cursor.description]
        rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
        assert any(
            row["RequestSessionId"] == wait_spid and row["BlockingSessionId"] == held_spid
            for row in rows
        )
        assert not any("text" in name.lower() for name in columns)
        while cursor.nextset():
            cursor.fetchall()
    finally:
        holder.execute("ROLLBACK")
        worker.join(6)
        holder.close()
        waiter.close()
    assert not worker.is_alive() and not errors
