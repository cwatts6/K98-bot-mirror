"""Real driver timeout, cancellation and lost guard acknowledgements; no business SQL."""

from threading import Event, Thread
from time import monotonic, sleep
from types import SimpleNamespace
from uuid import uuid4

import pytest

from core import sql_connection_custody as custody
from kvk.dal.new_source_import_dal import transaction
from services.import_capture_recovery_dal import ImportCaptureRecoveryDAL


@pytest.fixture
def state(snapshot_database):
    import pyodbc

    connections = []

    def connect():
        cn = pyodbc.connect(snapshot_database.connection_string, autocommit=False, timeout=5)
        cn.timeout = 1
        connections.append(cn)
        return cn

    try:
        yield SimpleNamespace(connect=connect, connections=connections)
    finally:
        for cn in connections:
            try:
                cn.close()
            except pyodbc.ProgrammingError:
                pass


def assert_closed(cn):
    import pyodbc

    with pytest.raises(pyodbc.ProgrammingError):
        cn.cursor()


def test_actual_query_timeout_rolls_back_and_closes(state):
    import pyodbc

    with pytest.raises(pyodbc.Error):
        with transaction(state.connect) as cursor:
            cursor.execute("WAITFOR DELAY '00:00:05'")
    assert_closed(state.connections[0])
    assert custody.custody_snapshot()["unconfirmed"] == 0


def test_cancel_does_not_release_worker_until_driver_unwinds(state):
    import pyodbc

    entered = Event()
    finished = Event()
    held = []
    errors = []

    def work():
        try:
            cn = state.connect()
            cn.timeout = 5
            with transaction(lambda: cn) as cursor:
                held.append((cursor, cursor.execute("SELECT @@SPID").fetchval()))
                entered.set()
                cursor.execute("WAITFOR DELAY '00:00:10'")
        except BaseException as error:
            errors.append(error)
        finally:
            finished.set()

    worker = Thread(target=work)
    worker.start()
    try:
        assert entered.wait(3)
        check = state.connect()
        check.autocommit = True
        try:
            deadline = monotonic() + 2
            while monotonic() < deadline:
                row = check.execute(
                    "SELECT wait_type FROM sys.dm_exec_requests WHERE session_id=?", held[0][1]
                ).fetchone()
                if row and row[0] == "WAITFOR":
                    break
                sleep(0.01)
            else:
                pytest.fail("The owned query did not enter its server wait before cancellation")
        finally:
            check.close()
        assert not finished.is_set()
        held[0][0].cancel()
        assert finished.wait(2)
        worker.join(1)
        assert not worker.is_alive()
        assert len(errors) == 1 and isinstance(errors[0], pyodbc.Error)
        assert errors[0].args[0] == "HY008"
        assert_closed(state.connections[0])
    finally:
        if worker.is_alive():
            if held:
                held[0][0].cancel()
            worker.join(7)
        assert not worker.is_alive()


@pytest.mark.parametrize("lost", ["grant", "release", "close"])
def test_capture_unknown_ack_keeps_guard_or_cleanup_custody(state, lost):

    key = "d2i:" + uuid4().hex
    first = OSError("injected acknowledgement loss")
    actual = []

    class Cursor:
        def __init__(self, cursor):
            self.inner = cursor

        def __getattr__(self, name):
            return getattr(self.inner, name)

        def execute(self, sql, *args):
            self.inner.execute(sql, *args)
            if lost == "grant" and "sp_getapplock" in sql:
                raise first
            if lost == "release" and "sp_releaseapplock" in sql:
                raise first
            return self

    class Connection:
        def __init__(self, cn):
            self.inner = cn

        @property
        def autocommit(self):
            return self.inner.autocommit

        @autocommit.setter
        def autocommit(self, value):
            self.inner.autocommit = value

        def cursor(self):
            return Cursor(self.inner.cursor())

        def close(self):
            if lost == "close":
                raise first
            self.inner.close()

    def connect():
        cn = state.connect()
        actual.append(cn)
        return Connection(cn)

    dal = ImportCaptureRecoveryDAL(SimpleNamespace(connect=connect))
    dal.guards = lambda _: (key,)
    expected = custody.SqlCleanupUnknown if lost in {"release", "close"} else OSError
    with pytest.raises(expected):
        with dal.session(str(uuid4())):
            pass
    if lost in {"release", "close"}:
        assert custody.custody_snapshot()["unconfirmed"] == 1
        with pytest.raises(custody.SqlCleanupUnknown):
            with dal.session(str(uuid4())):
                pytest.fail("Must retain closed admission")
        assert len(actual) == 1
    else:
        assert custody.custody_snapshot()["unconfirmed"] == 0
    # A separate controlled connection proves explicit release of the exact guard,
    # even when the simulated close acknowledgement failed. No force eviction.
    check = state.connect()
    check.autocommit = True
    try:
        assert (
            check.execute(
                "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; SELECT @r",
                key,
            ).fetchval()
            >= 0
        )
        check.execute("EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'", key)
    finally:
        check.close()
    if lost == "close":
        actual[0].close()  # Test fixture owns this still-open handle.
    assert_closed(actual[0])
