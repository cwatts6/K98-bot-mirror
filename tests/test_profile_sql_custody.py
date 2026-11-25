"""Separate driver handles expose implicit-exit leaks and owner admission races."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from event_calendar.sql_lifecycle import SqlOutcome
from services.profile_cache_service import ProfileCacheService
from stats.profile_cache_repository import read_profiles


class Cursor:
    description = (("GovernorID",), ("Governor_Name",))

    def __init__(self, connection):
        self.connection = connection

    def execute(self, sql):
        self.connection.events.append("execute")
        if self.connection.body_error:
            raise self.connection.body_error
        self.rows = [(2, "Candidate")] if "v_PlayerProfile" in sql else []

    def fetchall(self):
        return self.rows

    def close(self):
        self.connection.events.append("cursor_close")
        if "cursor_close" in self.connection.fail:
            raise OSError("private cursor details")


class Connection:
    def __init__(self, *, fail=(), body_error=None):
        self.events = []
        self.fail = fail
        self.body_error = body_error

    def __enter__(self):
        self.events.append("driver_enter")
        return self

    def __exit__(self, *args):
        self.events.append("implicit_commit")

    def cursor(self):
        return Cursor(self)

    def rollback(self):
        self.events.append("rollback")
        if "rollback" in self.fail:
            raise OSError("private rollback details")

    def close(self):
        self.events.append("connection_close")
        if "connection_close" in self.fail:
            raise OSError("private close details")


def test_managed_driver_is_rolled_back_and_physically_closed():
    conn, outcome = Connection(), SqlOutcome()
    players, omitted = read_profiles(lambda: conn, sql_outcome=outcome)
    assert players["2"]["GovernorName"] == "Candidate" and not omitted
    assert conn.events == ["execute"] * 3 + ["rollback", "cursor_close", "connection_close"]
    assert outcome.cleanup == "settled" and outcome.rollback == "confirmed"


def test_cursor_close_error_still_attempts_and_acknowledges_connection_close():
    conn, outcome = Connection(fail=("cursor_close",)), SqlOutcome()
    assert read_profiles(lambda: conn, sql_outcome=outcome)[0]["2"]
    assert outcome.cleanup == "settled" and outcome.retained_connection is None
    assert outcome.cleanup_error == {"error_type": "OSError"}


@pytest.mark.parametrize("error", [OSError("original"), asyncio.CancelledError()])
def test_original_error_survives_all_cleanup_failures(error):
    conn = Connection(fail=("rollback", "cursor_close", "connection_close"), body_error=error)
    outcome = SqlOutcome()
    with pytest.raises(type(error)) as raised:
        read_profiles(lambda: conn, sql_outcome=outcome)
    assert raised.value is error
    assert conn.events[-3:] == ["rollback", "cursor_close", "connection_close"]
    assert outcome.retained_connection is conn and outcome.cleanup == "unconfirmed"
    assert "private" not in str(outcome.public())


@pytest.mark.parametrize("failure", ["rollback", "connection_close"])
def test_cleanup_failure_cannot_return_candidate(failure):
    conn, outcome = Connection(fail=(failure,)), SqlOutcome()
    with pytest.raises(RuntimeError, match="profile_sql_"):
        read_profiles(lambda: conn, sql_outcome=outcome)
    assert outcome.cleanup == ("unconfirmed" if failure == "connection_close" else "settled")


@pytest.fixture
def facade(monkeypatch, tmp_path):
    import profile_cache
    from stats import profile_cache_repository

    service = ProfileCacheService()
    monkeypatch.setattr(profile_cache, "_service", service)
    path = tmp_path / "profiles.json"
    monkeypatch.setattr(profile_cache, "PLAYER_PROFILE_CACHE", str(path))
    good = Connection()
    monkeypatch.setattr(profile_cache_repository, "_connect", lambda: good)
    assert profile_cache.refresh_result(fresh=True).execution == "succeeded"
    return profile_cache, profile_cache_repository, service, path


@pytest.mark.parametrize("factory_failure", [False, True])
def test_uncertain_custody_preserves_cache_and_refuses_all_new_sql(
    facade, monkeypatch, factory_failure
):
    api, repository, service, path = facade
    previous, saved = service.snapshot(), path.read_bytes()
    conn = Connection(fail=("connection_close",))
    calls = []

    def connect():
        calls.append(1)
        if factory_failure:
            raise OSError("allocation unconfirmed")
        return conn

    monkeypatch.setattr(repository, "_connect", connect)
    result = api.refresh_result(fresh=True)
    assert result.execution == "failed" and result.diagnostic == "profile_sql_cleanup_unconfirmed"
    assert service.snapshot() == previous and path.read_bytes() == saved
    assert api.get_profile_cached(2) == previous["2"]
    assert api.refresh_result(force=True) == result
    assert api.refresh_result(fresh=True) == result
    with pytest.raises(RuntimeError, match="not_durable"):
        api.build_full_cache()
    service.invalidate(2)
    assert api.refresh_result(fresh=True).verification == "superseded"
    assert calls == [1] and path.read_bytes() == saved
    assert service._sql_hold.cleanup == "unconfirmed"
    assert service._sql_hold.retained_connection is (None if factory_failure else conn)
    assert service.health_snapshot().outcome == "unknown"
    assert service.health_snapshot().reason == "profile_sql_cleanup_unconfirmed"
    assert "private" not in str(service.stats())
    service.close()
    assert service._sql_hold.cleanup == "unconfirmed"


def test_confirmed_close_allows_next_refresh_after_body_or_rollback_failure(facade, monkeypatch):
    api, repository, service, _ = facade
    for conn in (Connection(body_error=OSError("statement")), Connection(fail=("rollback",))):
        monkeypatch.setattr(repository, "_connect", lambda: conn)
        assert api.refresh_result(fresh=True).execution == "failed"
        assert service._sql_hold is None
        monkeypatch.setattr(repository, "_connect", Connection)
        assert api.refresh_result(fresh=True).execution == "succeeded"


def test_cancelled_builder_keeps_uncertain_connection_owned(facade, monkeypatch):
    api, repository, service, path = facade
    previous = path.read_bytes()
    error = asyncio.CancelledError()
    conn = Connection(fail=("connection_close",), body_error=error)
    monkeypatch.setattr(repository, "_connect", lambda: conn)
    with pytest.raises(asyncio.CancelledError) as raised:
        api.refresh_result(fresh=True)
    assert raised.value is error and service._sql_hold.retained_connection is conn
    assert service.stats()["outcome"]["execution"] == "failed"
    assert api.refresh_result(fresh=True).execution == "failed"
    assert path.read_bytes() == previous


def test_abrupt_cleanup_exit_retains_the_actual_handle(facade, monkeypatch):
    api, repository, service, _ = facade
    conn, error = Connection(), asyncio.CancelledError()

    def interrupted_rollback():
        raise error

    conn.rollback = interrupted_rollback
    monkeypatch.setattr(repository, "_connect", lambda: conn)
    with pytest.raises(asyncio.CancelledError) as raised:
        api.refresh_result(fresh=True)
    assert raised.value is error
    assert service._sql_hold.retained_connection is conn
    assert service._sql_hold.cleanup == "pending"
    assert api.refresh_result(fresh=True).execution == "failed"


@pytest.mark.asyncio
@pytest.mark.parametrize("close_fails", [False, True])
@pytest.mark.parametrize("fresh_joiner", [False, True])
async def test_async_cancellation_and_join_wait_for_physical_cleanup(
    facade, monkeypatch, close_fails, fresh_joiner
):
    api, repository, service, _ = facade
    entered, release, joined = Event(), Event(), Event()
    conn = Connection(fail=("connection_close",) if close_fails else ())
    close = conn.close
    calls = []

    def blocked_close():
        entered.set()
        assert release.wait(5)
        close()

    def connect():
        calls.append(1)
        return conn if len(calls) == 1 else Connection()

    conn.close = blocked_close
    monkeypatch.setattr(repository, "_connect", connect)
    task = asyncio.create_task(api.refresh_async(fresh=True))
    assert await asyncio.to_thread(entered.wait, 5)
    original_result = service._flight.result

    def join():
        joined.set()
        return original_result()

    service._flight.result = join
    with ThreadPoolExecutor() as pool:
        other = pool.submit(api.refresh_result, force=True, fresh=fresh_joiner)
        try:
            assert await asyncio.to_thread(joined.wait, 5)
            task.cancel()
            await asyncio.sleep(0)
            task.cancel()
            await asyncio.sleep(0)
            assert not task.done() and not other.done()
            assert service.profile(2) is not None and calls == [1]
        finally:
            release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        result = other.result(5)
    assert result.execution == ("failed" if close_fails else "succeeded")
    assert (service._sql_hold is not None) == close_fails
    assert calls == ([1, 1] if fresh_joiner and not close_fails else [1])
