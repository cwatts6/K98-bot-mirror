"""Disposable report stand-ins: driver limits, cancellation and physical cleanup."""

from inspect import unwrap
from threading import Event, Thread
from time import monotonic, sleep
from unittest.mock import Mock

import pytest

import player_stats_cache as cache
from services.legacy_export_snapshot_dal import LegacySnapshotDAL
from services.player_report_sql import player_connection


@pytest.fixture
def report_fixture(snapshot_database, monkeypatch):
    import pyodbc

    admin = pyodbc.connect(snapshot_database.connection_string, autocommit=True, timeout=5)
    admin.timeout = 3
    admin.execute("CREATE TABLE dbo.D2PlayerProbe(Value int NOT NULL)")
    monkeypatch.setattr(cache, "current_owner", lambda: None)
    monkeypatch.setattr(cache, "record_writer_completion", Mock())
    import services.legacy_export_snapshot_service as legacy

    for name in ("verify_producer_cursor", "begin_writer_transaction", "record_writer_stage"):
        monkeypatch.setattr(legacy, name, Mock())
    connections = []

    def connect(**_):
        cn = pyodbc.connect(snapshot_database.connection_string, autocommit=False, timeout=5)
        cn.timeout = 15
        connections.append(cn)
        return cn

    monkeypatch.setattr("file_utils.get_conn_with_retries", connect)
    try:
        yield admin, connections
    finally:
        for cn in connections:
            try:
                cn.close()
            except pyodbc.ProgrammingError:
                pass
        admin.execute("DROP TABLE dbo.D2PlayerProbe")
        admin.close()


def assert_closed(cn):
    import pyodbc

    with pytest.raises(pyodbc.ProgrammingError):
        cn.cursor()


def test_nested_sixty_second_lock_wait_cannot_exceed_fifteen_second_statement(
    report_fixture, monkeypatch
):
    import pyodbc

    admin, connections = report_fixture
    admin.execute(
        "EXEC sys.sp_getapplock @Resource='D2PlayerBudget',@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0"
    )
    monkeypatch.setattr(cache, "_SP_EXECUTION_TIMEOUT", 300)
    monkeypatch.setattr(
        cache,
        "_SQL_EXEC_SP",
        "INSERT dbo.D2PlayerProbe VALUES(1); DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource='D2PlayerBudget',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=60000; SELECT @r;",
    )
    try:
        started = monotonic()
        with pytest.raises(pyodbc.Error) as caught:
            with player_connection(operation="guided_player_report") as cn:
                unwrap(cache._execute_sp_with_retries)(cn, retries=1)
        elapsed = monotonic() - started
        assert 12 <= elapsed < 22
        assert caught.value.args[0] in {"HYT00", "HYT01"}
        assert_closed(connections[0])
        assert admin.execute("SELECT COUNT(*) FROM dbo.D2PlayerProbe").fetchval() == 0
    finally:
        admin.execute("EXEC sys.sp_releaseapplock @Resource='D2PlayerBudget',@LockOwner='Session'")


def test_driver_cancel_is_not_replayed_and_connection_physically_closes(
    report_fixture, monkeypatch
):
    import pyodbc

    admin, connections = report_fixture
    monkeypatch.setattr(
        cache, "_SQL_EXEC_SP", "INSERT dbo.D2PlayerProbe VALUES(1); WAITFOR DELAY '00:00:10';"
    )
    monkeypatch.setattr(cache, "_SP_EXECUTION_TIMEOUT", 15)
    from services import player_report_sql

    original = player_report_sql.player_report_cursor
    from contextlib import contextmanager

    ready, done = Event(), Event()
    cursors = []
    errors = []
    session = []

    @contextmanager
    def observed(cn, **kwargs):
        session.append(cn.execute("SELECT @@SPID").fetchval())
        with original(cn, **kwargs) as pair:
            cursors.append(pair[0])
            ready.set()
            yield pair

    monkeypatch.setattr(player_report_sql, "player_report_cursor", observed)

    def run():
        try:
            with player_connection(operation="player_stats_cache") as cn:
                unwrap(cache._execute_sp_with_retries)(cn, retries=3)
        except BaseException as error:
            errors.append(error)
        finally:
            done.set()

    worker = Thread(target=run)
    worker.start()
    try:
        assert ready.wait(3)
        deadline = monotonic() + 3
        while monotonic() < deadline:
            waiting = admin.execute(
                "SELECT wait_type FROM sys.dm_exec_requests WHERE session_id=?", session[0]
            ).fetchone()
            if waiting and waiting[0] == "WAITFOR":
                break
            sleep(0.01)
        else:
            pytest.fail("Owned report never entered fixture WAITFOR")
        assert not done.is_set()
        cursors[0].cancel()
        worker.join(3)
        assert done.is_set() and len(cursors) == 1
        assert (
            len(errors) == 1
            and isinstance(errors[0], pyodbc.Error)
            and errors[0].args[0] == "HY008"
        )
        assert_closed(connections[0])
        assert admin.execute("SELECT COUNT(*) FROM dbo.D2PlayerProbe").fetchval() == 0
    finally:
        if worker.is_alive():
            cursors[0].cancel()
            worker.join(20)
        assert not worker.is_alive()


def test_lost_writer_guard_grant_reply_releases_actual_owned_guard(snapshot_database):
    import pyodbc

    cn = pyodbc.connect(snapshot_database.connection_string, autocommit=True, timeout=5)
    peer = pyodbc.connect(snapshot_database.connection_string, autocommit=True, timeout=5)
    raw = cn.cursor()
    first = OSError("lost grant acknowledgement")

    class Cursor:
        def __getattr__(self, name):
            return getattr(raw, name)

        def execute(self, sql, *args):
            raw.execute(sql, *args)
            if "sp_getapplock" in sql:
                raise first
            return self

    class Connection:
        autocommit = True

        def cursor(self):
            return Cursor()

    dal = LegacySnapshotDAL(Mock())
    dal.authorize = Mock()
    try:
        with pytest.raises(OSError) as caught:
            with dal.session("claim", Connection()):
                pytest.fail("Unacknowledged admission entered")
        assert caught.value is first
        result = peer.execute(
            "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource='k98-legacy-output-snapshot',@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; SELECT @r"
        ).fetchval()
        assert result >= 0
    finally:
        cn.close()
        peer.close()
