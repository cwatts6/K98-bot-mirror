"""Opt-in local restricted-login test of the real SQL account-lock protocol.

The procedure fixture uses the authoritative request procedure's unchanged role,
ambient-transaction and account-lock prologue, then a synthetic receipt table.
It does not run a business producer, provider call or production recovery.
"""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
from pathlib import Path
import re
import secrets
from threading import Event
from time import monotonic
from types import SimpleNamespace
from uuid import uuid4

import pytest

from services.export_coordination_dal import ExportCoordinationDAL, _mutex
from services.export_execution_dal import EvidenceCommitUnknown, ExportExecutionDAL

pytestmark = pytest.mark.skipif(
    os.getenv("K98_EXECUTION_LOCK_SQL") != "LOCAL_SYNTHETIC_ONLY",
    reason="Explicit local synthetic SQL validation required",
)


@pytest.fixture
def restricted_lock():
    import pyodbc

    suffix = uuid4().hex
    database, login = "K98LockTest_" + suffix, "K98LockApp_" + suffix
    password = secrets.token_urlsafe(32) + "aA1!"
    prefix = r"DRIVER={ODBC Driver 17 for SQL Server};SERVER=lpc:localhost\K98DEV;"
    admin = pyodbc.connect(
        prefix + "DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes",
        autocommit=True,
        timeout=5,
    )
    assert admin.execute("SELECT @@SERVERNAME").fetchval().lower() == r"9sx2vf4\k98dev"
    owner = None
    try:
        admin.execute(f"CREATE DATABASE [{database}]")
        owner = pyodbc.connect(
            prefix + f"DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes",
            autocommit=True,
            timeout=5,
        )
        owner.execute(
            "CREATE TABLE dbo.SyntheticCheckpoint(StreamID uniqueidentifier NOT NULL PRIMARY KEY,Version bigint NOT NULL)"
        )
        owner.execute("CREATE ROLE ExportExecutionAuthority")
        admin.execute(f"CREATE LOGIN [{login}] WITH PASSWORD='{password}',CHECK_POLICY=ON")
        owner.execute(f"CREATE USER LockAuthority FOR LOGIN [{login}]")
        owner.execute("ALTER ROLE ExportExecutionAuthority ADD MEMBER LockAuthority")
        source = Path(
            "C:/K98-bot-SQL-Server/sql_schema/dbo.usp_ExportProviderRequestEventAppend.StoredProcedure.sql"
        ).read_text(encoding="utf-8-sig")
        prologue = source[source.index(" SET NOCOUNT ON;") : source.index(" DECLARE @OwnerKind")]
        # No permission or lock semantics are weakened in this extracted prologue.
        assert (
            "@LockTimeout=0" in prologue
            and "IS_ROLEMEMBER(N'ExportExecutionAuthority')" in prologue
        )
        owner.execute(
            "CREATE PROCEDURE dbo.usp_ExportProviderRequestEventAppend @AccountKey varchar(128),@StreamID uniqueidentifier AS BEGIN\n"
            + prologue
            + "INSERT dbo.SyntheticCheckpoint VALUES(@StreamID,1); SELECT Version FROM dbo.SyntheticCheckpoint WHERE StreamID=@StreamID; COMMIT; "
            "END TRY BEGIN CATCH IF XACT_STATE()<>0 ROLLBACK;THROW;END CATCH;END"
        )
        owner.execute(
            "GRANT EXECUTE ON dbo.usp_ExportProviderRequestEventAppend TO ExportExecutionAuthority"
        )

        def connect():
            cn = pyodbc.connect(
                prefix
                + f"DATABASE={database};UID={login};PWD={password};TrustServerCertificate=yes",
                autocommit=False,
                timeout=5,
            )
            cn.timeout = 5
            return cn

        with connect() as cn:
            assert tuple(
                cn.execute(
                    "SELECT IS_SRVROLEMEMBER('sysadmin'),IS_ROLEMEMBER('db_owner'),HAS_PERMS_BY_NAME('dbo.SyntheticCheckpoint','OBJECT','INSERT')"
                ).fetchone()
            ) == (0, 0, 0)
        yield SimpleNamespace(owner=owner, connect=connect, account="synthetic-" + suffix)
    finally:
        if owner is not None:
            owner.close()
        assert re.fullmatch(r"K98LockTest_[0-9a-f]{32}", database)
        if admin.execute("SELECT DB_ID(?)", database).fetchval() is not None:
            admin.execute(
                f"ALTER DATABASE [{database}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [{database}]"
            )
        if admin.execute("SELECT SUSER_ID(?)", login).fetchval() is not None:
            admin.execute(f"DROP LOGIN [{login}]")
        admin.close()


def test_original_refusal_then_restricted_checkpoint_waits_and_commits_once(restricted_lock):
    import pyodbc

    f = restricted_lock
    f.owner.execute("BEGIN TRAN")
    _mutex(f.owner.cursor(), "account:" + f.account)
    original = f.connect()
    original.autocommit = True
    request = str(uuid4())
    try:
        with pytest.raises(pyodbc.Error, match="Export admission busy"):
            original.execute(
                "EXEC dbo.usp_ExportProviderRequestEventAppend @AccountKey=?,@StreamID=?",
                f.account,
                request,
            )
        assert tuple(original.execute("SELECT @@TRANCOUNT,XACT_STATE()").fetchone()) == (0, 0)
        started = Event()

        def run():
            started.set()
            return ExportExecutionDAL(f.connect).transition(
                "event", AccountKey=f.account, StreamID=request
            )

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(run)
            assert started.wait(2)
            f.owner.execute("WAITFOR DELAY '00:00:00.150'; ROLLBACK")
            assert future.result(timeout=4) == {"Version": 1}
        assert (
            f.owner.execute(
                "SELECT COUNT(*) FROM dbo.SyntheticCheckpoint WHERE StreamID=?", request
            ).fetchval()
            == 1
        )
        key = "k98-export:" + hashlib.sha256(("account:" + f.account).encode()).hexdigest()
        assert (
            f.owner.execute("SELECT APPLOCK_TEST('public',?,'Exclusive','Session')", key).fetchval()
            == 1
        )
    finally:
        f.owner.execute("IF @@TRANCOUNT>0 ROLLBACK")
        original.close()


def test_permanent_contention_is_bounded_and_never_executes_checkpoint(restricted_lock):
    f = restricted_lock
    f.owner.execute("BEGIN TRAN")
    _mutex(f.owner.cursor(), "account:" + f.account)
    started = monotonic()
    try:
        with pytest.raises(EvidenceCommitUnknown):
            ExportExecutionDAL(f.connect).transition(
                "event", AccountKey=f.account, StreamID=str(uuid4())
            )
        assert monotonic() - started < 3
        assert f.owner.execute("SELECT COUNT(*) FROM dbo.SyntheticCheckpoint").fetchval() == 0
    finally:
        f.owner.execute("ROLLBACK")


def test_worker_account_boundary_waits_without_replaying_transaction(restricted_lock):
    f = restricted_lock
    f.owner.execute("BEGIN TRAN")
    _mutex(f.owner.cursor(), "account:" + f.account)
    started = Event()

    def run():
        started.set()
        with ExportCoordinationDAL(f.connect)._account(f.account) as cursor:
            return cursor.execute("SELECT 1").fetchval()

    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(run)
        assert started.wait(2)
        f.owner.execute("WAITFOR DELAY '00:00:00.150'; ROLLBACK")
        assert pending.result(timeout=4) == 1


def test_lost_commit_reply_never_replays_durable_checkpoint(restricted_lock):
    f = restricted_lock
    request = str(uuid4())
    connections = []

    class Cursor:
        def __init__(self, inner):
            self.inner, self.procedure = inner, False

        def execute(self, sql, *args):
            self.procedure = sql.startswith("EXEC dbo.usp_ExportProvider")
            self.inner.execute(sql, *args)
            return self

        def nextset(self):
            result = self.inner.nextset()
            if self.procedure:
                raise OSError("synthetic missing commit reply")
            return result

        def __getattr__(self, name):
            return getattr(self.inner, name)

    class Connection:
        def __init__(self):
            self.inner = f.connect()
            connections.append(self)

        @property
        def autocommit(self):
            return self.inner.autocommit

        @autocommit.setter
        def autocommit(self, value):
            self.inner.autocommit = value

        def cursor(self):
            return Cursor(self.inner.cursor())

        def close(self):
            self.inner.close()

    with pytest.raises(EvidenceCommitUnknown):
        ExportExecutionDAL(Connection).transition("event", AccountKey=f.account, StreamID=request)
    assert len(connections) == 1
    assert (
        f.owner.execute(
            "SELECT COUNT(*) FROM dbo.SyntheticCheckpoint WHERE StreamID=?", request
        ).fetchval()
        == 1
    )
