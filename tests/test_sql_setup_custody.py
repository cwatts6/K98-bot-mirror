"""Dedicated factory setup owns failures until physical close is acknowledged."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

import pytest

from core import export_sql_connection as factory


class Session:
    def __init__(self, fail=(), error=None):
        self.fail = set(fail)
        self.error = error or OSError("private setup detail")
        self.events = []
        self._autocommit = True

    def step(self, name):
        self.events.append(name)
        if name in self.fail:
            raise self.error

    @property
    def timeout(self):
        return 15

    @timeout.setter
    def timeout(self, value):
        assert value == 15
        self.step("timeout")

    @property
    def autocommit(self):
        return self._autocommit

    @autocommit.setter
    def autocommit(self, value):
        assert value is False
        self.step("autocommit")
        self._autocommit = value

    def cursor(self):
        self.step("cursor")
        session = self

        class Cursor:
            def execute(self, sql):
                assert sql == "SET LOCK_TIMEOUT 1000"
                session.step("execute")

            def close(self):
                session.step("cursor_close")

        return Cursor()

    def close(self):
        self.step("close")


@pytest.fixture
def connections(monkeypatch):
    import pyodbc

    monkeypatch.setattr(factory, "_setup_holds", {}, raising=False)
    monkeypatch.setattr(
        factory,
        "settings",
        lambda **kw: dict(
            server="synthetic",
            database="ROK_TRACKER",
            username="S11_ExportApplication",
            password="private",
        ),
    )
    sessions, calls = [], []

    def connect(*args, **kwargs):
        calls.append(kwargs)
        return sessions.pop(0)

    monkeypatch.setattr(pyodbc, "connect", connect)
    return sessions, calls


def open_connection():
    return factory.connect(server="synthetic", database="ROK_TRACKER")


@pytest.mark.parametrize("phase", ["timeout", "cursor", "execute", "cursor_close", "autocommit"])
@pytest.mark.parametrize("close_fails", [False, True])
def test_every_setup_failure_closes_or_retains_and_gates(connections, phase, close_fails):
    sessions, calls = connections
    failed = Session([phase, "close"] if close_fails else [phase])
    sessions.extend([failed, Session()])
    with pytest.raises(factory.ExportSqlConfigurationError) as raised:
        open_connection()
    assert "private" not in str(raised.value) and raised.value.__suppress_context__
    assert failed.events[-1] == "close"
    if phase in {"execute", "cursor_close", "autocommit"}:
        assert failed.events.count("cursor_close") == 1
    if close_fails:
        hold = next(iter(factory._setup_holds.values()))
        assert hold.retained_connection is failed and hold.cleanup == "unconfirmed"
        with pytest.raises(factory.ExportSqlConfigurationError, match="cleanup"):
            open_connection()
        assert len(calls) == 1
    else:
        assert not factory._setup_holds
        assert open_connection() is not failed


def test_original_statement_failure_is_not_replaced_by_cursor_cleanup(connections):
    sessions, _ = connections
    session = Session(["execute", "close"], error=ValueError("private original"))
    cursor = session.cursor()

    def fail_cursor_close():
        raise OSError("private cleanup")

    cursor.close = fail_cursor_close
    session.cursor = lambda: cursor
    sessions.append(session)
    with pytest.raises(factory.ExportSqlConfigurationError):
        open_connection()
    hold = next(iter(factory._setup_holds.values()))
    assert hold.error == {"error_type": "ValueError"}
    assert "private" not in str(hold.public())


@pytest.mark.parametrize("close_fails", [False, True])
def test_abrupt_setup_exit_preserves_cancellation_and_attempts_close(connections, close_fails):
    sessions, _ = connections
    error = asyncio.CancelledError()
    session = Session(["execute", "close"] if close_fails else ["execute"], error=error)
    sessions.append(session)
    with pytest.raises(asyncio.CancelledError) as raised:
        open_connection()
    assert raised.value is error and session.events[-2:] == ["cursor_close", "close"]
    assert bool(factory._setup_holds) == close_fails


def test_pending_close_blocks_new_connections_without_holding_reader_lock(connections):
    sessions, calls = connections
    entered, release = Event(), Event()
    session = Session(["execute"])

    def close():
        entered.set()
        assert release.wait(5)

    session.close = close
    sessions.extend([session, Session()])
    with ThreadPoolExecutor(2) as pool:
        pending = pool.submit(open_connection)
        try:
            assert entered.wait(5)
            assert pool.submit(factory.setup_custody_snapshot).result(2) == {
                "admission": "closed",
                "pending": 1,
                "unconfirmed": 0,
            }
            with pytest.raises(factory.ExportSqlConfigurationError, match="cleanup"):
                pool.submit(open_connection).result(2)
            assert len(calls) == 1
        finally:
            release.set()
        with pytest.raises(factory.ExportSqlConfigurationError):
            pending.result(5)
    assert factory.setup_custody_snapshot()["admission"] == "open"
    assert open_connection() is not session


def test_late_success_cannot_escape_an_uncertain_setup_hold(connections):
    sessions, calls = connections
    entered, release = Event(), Event()
    late, failed = Session(), Session(["execute", "close"])
    cursor = late.cursor()
    execute = cursor.execute

    def delayed(sql):
        entered.set()
        assert release.wait(5)
        execute(sql)

    cursor.execute = delayed
    late.cursor = lambda: cursor
    sessions.extend([late, failed])
    with ThreadPoolExecutor(2) as pool:
        pending = pool.submit(open_connection)
        try:
            assert entered.wait(5)
            with pytest.raises(factory.ExportSqlConfigurationError):
                pool.submit(open_connection).result(2)
        finally:
            release.set()
        with pytest.raises(factory.ExportSqlConfigurationError, match="cleanup"):
            pending.result(5)
    assert len(calls) == 2 and late.events[-1] == "close"
    assert len(factory._setup_holds) == 1
    assert next(iter(factory._setup_holds.values())).retained_connection is failed


@pytest.mark.parametrize("fail", [False, True])
def test_parallel_setups_remain_concurrent_and_keep_each_failed_handle(connections, fail):
    sessions, calls = connections
    entered = Barrier(2)
    owned = [Session(["close"] if fail else ()) for _ in range(2)]
    for session in owned:
        cursor = session.cursor()

        def execute(sql):
            entered.wait(5)
            if fail:
                raise ValueError("original setup failure")

        cursor.execute = execute
        session.cursor = lambda cursor=cursor: cursor
    sessions.extend(owned)
    with ThreadPoolExecutor(2) as pool:
        pending = [pool.submit(open_connection) for _ in range(2)]
        if fail:
            for result in pending:
                with pytest.raises(factory.ExportSqlConfigurationError):
                    result.result(6)
            assert {id(v.retained_connection) for v in factory._setup_holds.values()} == {
                id(v) for v in owned
            }
        else:
            assert {id(p.result(6)) for p in pending} == {id(v) for v in owned}
            assert all("close" not in v.events for v in owned)
    assert len(calls) == 2


def test_driver_allocation_failure_keeps_existing_sanitized_contract(connections, monkeypatch):
    import pyodbc

    def fail(*args, **kw):
        raise OSError("private connection string")

    monkeypatch.setattr(pyodbc, "connect", fail)
    with pytest.raises(factory.ExportSqlConfigurationError) as raised:
        open_connection()
    assert "private" not in str(raised.value) and raised.value.__suppress_context__
    assert factory.setup_custody_snapshot() == {"admission": "open", "pending": 0, "unconfirmed": 0}
