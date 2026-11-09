"""P02.1 native interleavings in a newly created, uniquely named local database.

Opt-in creates only K98_P021_Disposable_<uuid> on 9SX2VF4\\K98DEV. No business
procedures, provider requests, retained databases or server settings are touched.
The three ownership table bodies come from the authoritative SQL repository;
external resource FKs are outside this metadata/locking qualification.
"""

from contextlib import contextmanager
import os
from pathlib import Path
import re
import threading
from types import SimpleNamespace
from uuid import uuid4

import pytest

from core.recovery_sql_snapshot import recovery_snapshot, require_recovery_snapshot_isolation
from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import _mutex
from services.legacy_snapshot_admission import SnapshotAdmissionRefused, acquire_snapshot_guard
from services.stats_import_outcome_dal import ImportExecutionActive, StatsImportOutcomeDAL

pytestmark = pytest.mark.skipif(
    os.getenv("K98_P021_NATIVE_SQL") != "CREATE_DISPOSABLE_LOCAL_ONLY",
    reason="P02.1 isolated local SQL qualification opt-in required",
)


@pytest.fixture(scope="module")
def database():
    import pyodbc

    pyodbc.pooling = False
    name = "K98_P021_Disposable_" + uuid4().hex
    assert re.fullmatch(r"K98_P021_Disposable_[0-9a-f]{32}", name)
    base = (
        r"DRIVER={ODBC Driver 18 for SQL Server};SERVER=lpc:localhost\K98DEV;"
        "Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;"
    )

    def connect(db, *, reader=False):
        cn = pyodbc.connect(base + "DATABASE=" + db + ";", autocommit=True, timeout=5)
        cn.timeout = 5
        actual = cn.execute("SELECT @@SERVERNAME,DB_NAME()").fetchone()
        assert actual[0].lower() == r"9sx2vf4\k98dev" and actual[1] == db
        if reader:
            cn.execute("EXECUTE AS USER='p021_reader'")
        return cn

    admin = connect("master")
    assert admin.execute("SELECT DB_ID(?)", name).fetchval() is None
    created = False
    try:
        admin.execute(f"CREATE DATABASE [{name}]")
        created = True
        admin.execute(f"ALTER DATABASE [{name}] SET ALLOW_SNAPSHOT_ISOLATION ON")
        setup = connect(name)
        try:
            setup.execute("CREATE TABLE dbo.ExportJob(JobID uniqueidentifier PRIMARY KEY)")
            for table in ("ExportPreparation", "ExportResource", "StatsImportExecution"):
                source = Path("C:/K98-bot-SQL-Server/sql_schema") / f"dbo.{table}.Table.sql"
                text = source.read_text(encoding="utf-8-sig").replace("\\r\\n", "\n")
                body = re.search(r"CREATE TABLE dbo\." + table + r"\s*\(.*?\n\);", text, re.S)
                assert body, table
                setup.execute(body.group())
            setup.execute(
                "CREATE USER p021_reader WITHOUT LOGIN; GRANT SELECT ON SCHEMA::dbo TO p021_reader"
            )
        finally:
            setup.close()
        yield SimpleNamespace(name=name, connect=lambda **kw: connect(name, **kw), admin=admin)
    finally:
        if created:
            # Unique database created by this fixture only; never evict sessions or
            # reuse/alter an existing target. A leaked connection makes cleanup fail.
            admin.execute("SET LOCK_TIMEOUT 1000")
            admin.execute(f"DROP DATABASE [{name}]")
        admin.close()


@pytest.fixture
def state(database):
    db = database
    root = db.connect()
    root.execute(
        "DELETE dbo.StatsImportExecution; DELETE dbo.ExportResource; DELETE dbo.ExportPreparation"
    )
    prep, owner = str(uuid4()), str(uuid4())
    root.execute(
        "INSERT dbo.ExportPreparation(PreparationID,AccountKey,ConsumerKind,RequestHash,"
        "EnqueueSequence,State,OwnerID,Fence,Version,StorageOwner,RequestJson,Actor,Reason,CreatedUTC,UpdatedUTC) "
        "VALUES (?,'a','scan_data',?,1,'writing',?,1,1,'local','{}','test','test',SYSUTCDATETIME(),SYSUTCDATETIME())",
        prep,
        bytes(32),
        owner,
    )
    root.execute(
        "INSERT dbo.ExportResource(ResourceKey,ResourceKind,ActivePreparationID,OwnerID,Fence,Version) "
        "VALUES ('sql_snapshot:legacy_outputs','sql_snapshot',?,?,1,1)",
        prep,
        owner,
    )
    root.execute(
        "INSERT dbo.StatsImportExecution(PreparationID,CompletedFileName,OwnerID,Fence,State) "
        "VALUES (?,?,?,1,'prepared')",
        prep,
        "stats_" + uuid4().hex + ".ready.csv",
        owner,
    )

    def read_connect():
        cn = db.connect(reader=True)
        cn.autocommit = False
        return cn

    def write_connect():
        cn = db.connect()
        cn.autocommit = False
        return cn

    s = SimpleNamespace(
        db=db,
        root=root,
        prep=prep,
        owner=owner,
        read_connect=read_connect,
        write_connect=write_connect,
        dal=StatsImportOutcomeDAL(read_connect, account="a", storage_owner="local"),
    )
    try:
        yield s
    finally:
        root.close()


@contextmanager
def producer(s):
    cn = s.db.connect()
    try:
        acquire_snapshot_guard(cn.cursor())
        yield cn
    finally:
        cn.execute(
            "EXEC sys.sp_releaseapplock @Resource='k98-legacy-output-snapshot',@LockOwner='Session'"
        )
        cn.close()


def test_observer_first_neither_refuses_producer_nor_mixes_committed_versions(state):
    s = state
    with recovery_snapshot(s.read_connect) as cursor:
        cursor.execute("SELECT Version FROM dbo.ExportPreparation WHERE PreparationID=?", s.prep)
        assert cursor.fetchone()[0] == 1
        with producer(s) as writer:
            writer.execute("BEGIN TRANSACTION")
            _mutex(writer.cursor(), "account:a")
            writer.execute(
                "UPDATE dbo.ExportPreparation SET Version=2 WHERE PreparationID=?", s.prep
            )
            writer.execute(
                "UPDATE dbo.StatsImportExecution SET Version=2 WHERE PreparationID=?", s.prep
            )
            writer.execute("COMMIT TRANSACTION")
        # The second table stays on the same snapshot even after a real commit.
        cursor.execute("SELECT Version FROM dbo.StatsImportExecution WHERE PreparationID=?", s.prep)
        assert cursor.fetchone()[0] == 1
    assert s.dal.inspect(s.prep)["execution"]["Version"] == 2


@pytest.mark.parametrize("kind", ["stats", "legacy", "player", "configuration", "all_kvk"])
def test_writer_first_returns_busy_without_waiting_or_retaining_locks(state, kind):
    from services.all_kvk_capture_recovery_dal import AllKvkCaptureRecoveryDAL
    from services.configuration_producer_recovery import ConfigurationProducerDAL
    from services.player_report_recovery_dal import PlayerReportRecoveryDAL
    from services.unreceipted_producer_recovery import UnreceiptedProducerDAL

    s = state
    cls = {
        "stats": StatsImportOutcomeDAL,
        "legacy": UnreceiptedProducerDAL,
        "player": PlayerReportRecoveryDAL,
        "configuration": ConfigurationProducerDAL,
        "all_kvk": AllKvkCaptureRecoveryDAL,
    }[kind]
    if kind == "all_kvk":
        s.root.execute("UPDATE dbo.ExportPreparation SET ConsumerKind='all_kvk',KVK_NO=1")
    dal = cls(s.read_connect, account="a", storage_owner="local")
    with producer(s):
        with pytest.raises(ImportExecutionActive):
            dal.inspect(s.prep)


def test_same_account_admission_is_probed_with_exact_hashed_key(state):
    s = state
    cn = s.write_connect()
    try:
        _mutex(cn.cursor(), "account:a")
        with pytest.raises(ImportExecutionActive):
            s.dal.inspect(s.prep)
    finally:
        cn.rollback()
        cn.close()


def test_stale_snapshot_cannot_release_late_running_work_or_changed_evidence(state):
    s = state
    preview = s.dal.inspect(s.prep)
    mutation = StatsImportOutcomeDAL(s.write_connect, account="a", storage_owner="local")
    with producer(s):
        with pytest.raises(SourceConflict):
            mutation.settle(s.prep, token=preview["token"], actor="admin", reason="test")
    s.root.execute(
        "UPDATE dbo.ExportPreparation SET Version=Version+1 WHERE PreparationID=?", s.prep
    )
    with pytest.raises(SourceConflict, match="Evidence changed"):
        mutation.settle(s.prep, token=preview["token"], actor="admin", reason="test")
    assert s.root.execute("SELECT Resolution FROM dbo.StatsImportExecution").fetchval() is None
    assert (
        s.root.execute("SELECT ActivePreparationID FROM dbo.ExportResource").fetchval() is not None
    )


def test_read_only_principal_cannot_settle_and_scope_is_checked(state):
    import pyodbc

    s = state
    other = StatsImportOutcomeDAL(s.read_connect, account="other", storage_owner="local")
    with pytest.raises(SourceConflict, match="Exact runtime"):
        other.inspect(s.prep)
    preview = s.dal.inspect(s.prep)
    with pytest.raises(pyodbc.ProgrammingError, match=r"\(229\)"):
        s.dal.settle(s.prep, token=preview["token"], actor="admin", reason="test")
    assert s.root.execute("SELECT Resolution FROM dbo.StatsImportExecution").fetchval() is None


def test_snapshot_setting_is_required_without_automatic_change(state):
    s = state
    name = s.db.name
    s.db.admin.execute(f"ALTER DATABASE [{name}] SET ALLOW_SNAPSHOT_ISOLATION OFF")
    try:
        with pytest.raises(RuntimeError, match="SNAPSHOT"):
            require_recovery_snapshot_isolation(s.root.cursor())
        with pytest.raises(Exception) as caught:
            s.dal.inspect(s.prep)
        assert "3952" in str(caught.value)
        assert (
            s.db.admin.execute(
                "SELECT snapshot_isolation_state FROM sys.databases WHERE name=?", name
            ).fetchval()
            == 0
        )
    finally:
        s.db.admin.execute(f"ALTER DATABASE [{name}] SET ALLOW_SNAPSHOT_ISOLATION ON")
    require_recovery_snapshot_isolation(s.root.cursor())


def test_old_observer_guard_reproduces_refusal_with_actual_requester_facts(state):
    s = state
    holder, requester = s.db.connect(), s.db.connect()
    try:
        holder_id = holder.execute("SELECT @@SPID").fetchval()
        requester_id = requester.execute("SELECT @@SPID").fetchval()
        holder.execute(
            "BEGIN TRANSACTION; DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource='k98-legacy-output-snapshot',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=0; IF @r<0 THROW 50000,'Fixture refused',1;"
        )
        with pytest.raises(SnapshotAdmissionRefused) as caught:
            acquire_snapshot_guard(requester.cursor())
        assert caught.value.result == -1
        assert caught.value.session == requester_id != holder_id
    finally:
        holder.execute("IF @@TRANCOUNT>0 ROLLBACK")
        holder.close()
        requester.close()


def test_full_inspector_does_not_hold_application_or_data_locks_between_reads(state):
    s = state
    entered, release = threading.Event(), threading.Event()
    outcome = []

    class Cursor:
        def __init__(self, cursor):
            self.inner, self.query = cursor, ""

        def __getattr__(self, key):
            return getattr(self.inner, key)

        def execute(self, query, *args):
            self.query = query
            self.inner.execute(query, *args)
            return self

        def fetchone(self):
            value = self.inner.fetchone()
            if "SELECT * FROM dbo.ExportPreparation" in self.query:
                entered.set()
                assert release.wait(5)
            return value

    class Connection:
        def __init__(self):
            object.__setattr__(self, "inner", s.read_connect())

        def __getattr__(self, key):
            return getattr(self.inner, key)

        def __setattr__(self, key, value):
            setattr(self.inner, key, value)

        def cursor(self):
            return Cursor(self.inner.cursor())

    def observe():
        try:
            outcome.append(
                StatsImportOutcomeDAL(Connection, account="a", storage_owner="local").inspect(
                    s.prep
                )
            )
        except BaseException as error:
            outcome.append(error)

    thread = threading.Thread(target=observe)
    thread.start()
    try:
        assert entered.wait(5)
        with producer(s) as writer:
            writer.execute("BEGIN TRANSACTION; SET LOCK_TIMEOUT 0")
            _mutex(writer.cursor(), "account:a")
            writer.execute(
                "UPDATE dbo.ExportPreparation SET Version=2; UPDATE dbo.StatsImportExecution SET Version=2; COMMIT"
            )
    finally:
        release.set()
        thread.join(8)
    assert not thread.is_alive()
    assert len(outcome) == 1 and not isinstance(outcome[0], BaseException), outcome
    assert outcome[0]["preparation"]["Version"] == outcome[0]["execution"]["Version"] == 1
