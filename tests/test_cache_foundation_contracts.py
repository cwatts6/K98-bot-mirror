from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Event

import pytest


@pytest.mark.parametrize("managed", [False, True])
def test_profile_repository_mapping_and_optional_views(managed):
    from stats.profile_cache_repository import read_profiles

    class Connection:
        closed = False
        cursor_closed = False

        def cursor(self):
            return self

        def execute(self, sql):
            self.queries.append(sql)
            if "v_PlayerProfile" in sql:
                self.description = [
                    (x,) for x in ["GovernorID", "Governor_Name", "City Hall", "PowerRank"]
                ]
                self.rows = [(12, " Ada ", 25, 3)]
            elif "ScanMeta" in sql:
                raise RuntimeError("optional view missing")
            else:
                self.description = [
                    (x,) for x in ["GovernorID", "KVK_NUMBER", "KVK_KILL_RANK", "KillPercent"]
                ]
                self.rows = [(12, 15, 2, "70.5"), (12, 16, 1, "90")]

        def fetchall(self):
            return self.rows

        def close(self):
            self.closed = True

    class Managed(Connection):
        exited = False

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.exited = True

    conn = Managed() if managed else Connection()
    conn.queries = []
    players, omitted = read_profiles(lambda: conn)
    assert players["12"]["GovernorName"] == "Ada"
    assert players["12"]["CityHallLevel"] == 25
    assert players["12"]["PowerRank"] == 3
    assert [x["KVK"] for x in players["12"]["KVK"]] == [16, 15]
    assert omitted == ("scan_meta",) and len(conn.queries) == 3
    assert conn.closed
    if managed:
        assert conn.exited


def test_required_profile_source_failure_does_not_return_empty():
    from stats.profile_cache_repository import read_profiles

    class Connection:
        def cursor(self):
            raise OSError("required source missing")

        def close(self):
            pass

    with pytest.raises(OSError):
        read_profiles(Connection)


def test_name_single_flight_and_failed_refresh_preserves_snapshot(monkeypatch):
    import target_utils as names

    monkeypatch.setattr(names, "_name_closed", False)
    monkeypatch.setattr(names, "_name_flight", None)
    previous = {"rows": [{"GovernorID": "9"}], "names": {}, "norm_to_row": {}, "last_updated": 1}
    monkeypatch.setattr(names, "_name_cache", previous)
    entered, release, joined = Event(), Event(), Event()

    def build():
        entered.set()
        assert release.wait(5)
        return {"rows": [], "names": {}, "norm_to_row": {}, "last_updated": 2}

    monkeypatch.setattr(names, "_build_name_candidate", build)
    with ThreadPoolExecutor() as pool:
        first = pool.submit(names._refresh_name_owned)
        assert entered.wait(5)
        original = names._name_flight.result

        def join():
            joined.set()
            return original()

        names._name_flight.result = join
        second = pool.submit(names._refresh_name_owned)
        try:
            assert joined.wait(5)
            assert names.get_name_cache_status()["rows_count"] == 1
        finally:
            release.set()
        a, b = first.result(5), second.result(5)
    assert a[1] == b[1] and a[1].availability == "loaded_empty"
    published = names._name_cache

    def fail():
        raise ValueError("do not disclose")

    monkeypatch.setattr(names, "_build_name_candidate", fail)
    with pytest.raises(ValueError):
        names.sync_refresh_worker()
    assert names._name_cache is published
    assert "disclose" not in str(names.name_outcome_report())

    monkeypatch.setattr(names, "_name_cache", previous)
    with pytest.raises(ValueError):
        names.sync_refresh_worker()
    failed = names.name_outcome_report()
    assert failed["availability"] == "loaded_populated"
    assert failed["count"] == 1 and failed["source_time"] == 1


@pytest.mark.asyncio
async def test_name_previous_generation_not_completion(monkeypatch):
    from services.cache_outcomes import CacheOutcome
    import target_utils as names

    monkeypatch.setattr(names, "_name_generation", 2)
    outcome = CacheOutcome("name", "startup", execution="succeeded", generation=1)
    with pytest.raises(ValueError):
        await names.verify_name_completion(outcome)
    with pytest.raises(ValueError):
        await names.verify_name_completion(replace(outcome, generation=2, process_id="old"))


def test_passive_reporting_does_not_call_sql_refresh_or_provider(monkeypatch):
    import profile_cache
    from services import cache_admission_diagnostics as admission, recovery_health
    import target_utils

    def forbidden(*a, **kw):
        pytest.fail("report performed work")

    monkeypatch.setattr(profile_cache, "refresh_result", forbidden)
    monkeypatch.setattr(target_utils, "_refresh_name_owned", forbidden)
    admission.record(
        {"correlation_kind": "process_local", "sql_session_role": "requesting_session_not_blocker"}
    )
    result = recovery_health.report()
    assert set(result["cache_outcomes_v1"]) == {"profile", "name", "stats"}
    assert "players" not in str(result["cache_outcomes_v1"])
    assert (
        result["admission_observations_v1"][-1]["sql_session_role"]
        == "requesting_session_not_blocker"
    )
    result["admission_observations_v1"][-1]["sql_session_role"] = "changed"
    assert admission.report()[-1]["sql_session_role"] != "changed"


@pytest.mark.asyncio
async def test_admin_composition_reuses_exact_nested_result():
    from kvk.services.kvk_admin_service import refresh_stats_caches
    from services.player_stats_cache_service import observe_last

    async def main():
        observe_last(lambda: {"_meta": {"count": 4}})
        return {"_meta": {"count": 5}}

    async def last():
        pytest.fail("duplicate last-KVK")

    result = await refresh_stats_caches(
        build_player_stats_cache=main, build_lastkvk_player_stats_cache=last
    )
    assert result.main.count == 5 and result.last_kvk.count == 4


@pytest.mark.asyncio
async def test_ark_empty_name_refresh_has_no_second_worker(monkeypatch):
    from unittest.mock import AsyncMock, Mock

    from ark import ark_preference_service as service
    import target_utils

    monkeypatch.setattr(service, "get_name_cache_rows", lambda: [])
    refresh = AsyncMock()
    second = Mock(side_effect=AssertionError("duplicate worker"))
    monkeypatch.setattr(service, "refresh_name_cache_from_sql", refresh)
    monkeypatch.setattr(target_utils, "sync_refresh_worker", second)
    await service._ensure_governor_cache_ready()
    refresh.assert_awaited_once()
    second.assert_not_called()


def test_refused_admission_retains_process_local_startup_correlation(monkeypatch):
    from services import cache_admission_diagnostics as diagnostics, export_contention as contention

    monkeypatch.setattr(contention, "MAX_ATTEMPTS", 1)
    entered = []

    @contention.retry_coordination
    def request():
        entered.append(1)
        error = contention.CoordinationLockRefused(
            result=-1, session=123, transaction_state=0, transaction_count=0, resource_hash="a" * 64
        )
        error.transaction_released = True
        raise error

    with diagnostics.startup_context("build_player_stats_cache"):
        with pytest.raises(contention.CoordinationLockRefused):
            request()
    record = diagnostics.report()[-1]
    assert entered == [1]
    assert record["native_errors"] == [51400]
    assert record["origin"] == "startup" and record["operation"] == "player_stats"
    assert record["correlation_kind"] == "process_local"
    assert record["sql_session_role"] == "requesting_session_not_blocker"
    assert len(record["correlation_id"]) == 32
