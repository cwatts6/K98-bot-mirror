from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from threading import Event
import time

import pytest

from services.profile_cache_service import ProfileCacheService


@pytest.fixture
def cache(tmp_path):
    from file_utils import atomic_json_write

    service = ProfileCacheService()
    args = dict(
        path=str(tmp_path / "profiles.json"),
        ttl=900,
        parse_time=float,
        build=lambda: ({"1": {"GovernorID": 1, "GovernorName": "Ada"}}, ()),
        save=atomic_json_write,
    )
    return service, args


def test_single_flight_and_readers_remain_responsive(cache):
    service, args = cache
    entered, release, joined = Event(), Event(), Event()
    calls = []

    def build():
        calls.append(1)
        entered.set()
        assert release.wait(5)
        return {"1": {"GovernorID": 1}}, ()

    args["build"] = build
    with ThreadPoolExecutor(3) as pool:
        first = pool.submit(service.refresh, **args)
        assert entered.wait(5)
        original_result = service._flight.result

        def result(*a, **kw):
            joined.set()
            return original_result(*a, **kw)

        service._flight.result = result
        second = pool.submit(service.refresh, **args)
        try:
            assert joined.wait(5)
            assert pool.submit(service.stats).result(2)["count"] == 0
            assert pool.submit(service.snapshot).result(2) == {}
        finally:
            release.set()
        assert first.result(5) == second.result(5)
    assert calls == [1]


def test_invalidation_supersedes_entered_candidate_without_disk_write(cache):
    service, args = cache
    entered, release = Event(), Event()
    saves = []

    def build():
        entered.set()
        assert release.wait(5)
        return {"1": {"GovernorID": 1}}, ()

    args.update(build=build, save=lambda *a: saves.append(a))
    with ThreadPoolExecutor() as pool:
        pending = pool.submit(service.refresh, **args)
        try:
            assert entered.wait(5)
            service.invalidate(1)
        finally:
            release.set()
        output = pending.result(5)
    assert output.verification == "superseded"
    assert output.availability == "unavailable"
    assert not saves and service.snapshot() == {}
    with pytest.raises(ValueError, match="superseded"):
        service.verify(output)


def test_failed_persistence_is_memory_only_and_preserves_bytes(cache):
    service, args = cache
    from pathlib import Path

    path = Path(args["path"])
    path.write_bytes(b"previous bytes")

    def fail(*args):
        raise OSError("private details must not appear")

    args["save"] = fail
    output = service.refresh(**args)
    assert output.persistence == "failed_preserved"
    assert output.execution == "succeeded" and service.stats()["count"] == 1
    assert path.read_bytes() == b"previous bytes"
    assert "private" not in str(output.report())
    reused = service.refresh(**args)
    assert reused.source == "memory_reused"
    assert reused.persistence == "failed_preserved"
    assert path.read_bytes() == b"previous bytes"


@pytest.mark.parametrize("players", [[], {"bad": {}}, {"1": {"GovernorID": 2}}])
def test_invalid_candidate_preserves_existing_disk(cache, players):
    service, args = cache
    from pathlib import Path

    path = Path(args["path"])
    path.write_text(json.dumps({"players": {"8": {"GovernorID": 8}}, "generated_at": 1}))
    old = path.read_bytes()
    args["build"] = lambda: (players, ())
    output = service.refresh(**args)
    assert output.execution == "failed"
    assert output.source == "retained_last_known_good"
    assert path.read_bytes() == old and service.stats()["count"] == 1


def test_force_preserves_fresh_disk_reuse_and_copy_isolation(cache):
    service, args = cache
    from pathlib import Path

    Path(args["path"]).write_text(
        json.dumps({"players": {"2": {"GovernorID": 2}}, "generated_at": time.time()})
    )
    args["build"] = lambda: pytest.fail("force historically permits fresh disk reuse")
    outcome = service.refresh(**args, force=True)
    assert outcome.source == "disk_loaded"
    service.snapshot()["2"]["GovernorID"] = 44
    assert service.profile(2)["GovernorID"] == 2
    with pytest.raises(ValueError):
        service.verify(replace(outcome, process_id="previous-process"))


def test_fresh_request_waits_then_builds_its_own_revision(cache):
    service, args = cache
    entered, release, waiting = Event(), Event(), Event()
    calls = []

    def build():
        calls.append(1)
        if len(calls) == 1:
            entered.set()
            assert release.wait(5)
        return {str(len(calls)): {"GovernorID": len(calls)}}, ()

    args["build"] = build
    with ThreadPoolExecutor() as pool:
        old = pool.submit(service.refresh, **args)
        assert entered.wait(5)
        original = service._flight.result

        def join():
            waiting.set()
            return original()

        service._flight.result = join
        new = pool.submit(service.refresh, **args, fresh=True)
        try:
            assert waiting.wait(5)
        finally:
            release.set()
        first, second = old.result(5), new.result(5)
    assert first.invocation_id != second.invocation_id
    assert first.verification == "superseded"
    assert second.generation > first.generation
    assert service.profile(2) == {"GovernorID": 2}
    assert {name for name, _ in second.timings} == {"build", "validate", "persist"}


def test_closed_admission_does_not_build(cache):
    service, args = cache
    service.close()
    args["build"] = lambda: pytest.fail("closed")
    with pytest.raises(RuntimeError, match="admission_closed"):
        service.refresh(**args)


@pytest.mark.parametrize("stamp", [1, float("nan"), float("inf"), -float("inf")])
def test_startup_readback_requires_original_source_stamp(cache, monkeypatch, stamp):
    from pathlib import Path

    import profile_cache
    from services.profile_cache_startup import _verify

    service, args = cache
    monkeypatch.setattr(profile_cache, "_service", service)
    monkeypatch.setattr(profile_cache, "PLAYER_PROFILE_CACHE", args["path"])
    outcome = service.refresh(**args)
    assert _verify(outcome)["disk_verification"] == "original_snapshot"
    path = Path(args["path"])
    data = json.loads(path.read_text())
    data["generated_at"] = stamp
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="readback_differs"):
        _verify(outcome)


@pytest.mark.parametrize("stamp", [float("inf"), float("nan"), 1e100, -1e100])
def test_corrupt_timestamp_is_not_fresh_and_status_remains_readable(cache, stamp):
    from pathlib import Path

    service, args = cache
    Path(args["path"]).write_text(
        json.dumps({"generated_at": stamp, "players": {"2": {"GovernorID": 2}}})
    )
    result = service.refresh(**args)
    assert result.source == "refreshed"
    assert service.stats()["count"] == 1 and service.profile(1) is not None
    service._loaded_at = stamp
    assert service.stats()["loaded_at_iso"] is None


@pytest.mark.asyncio
async def test_late_original_completion_and_repeated_shutdown_drain(cache):
    import asyncio

    from core import startup_diagnostics
    from services.legacy_export_snapshot_service import drain_thread

    service, args = cache
    entered, release = Event(), Event()

    def build():
        entered.set()
        assert release.wait(5)
        return {"1": {"GovernorID": 1}}, ()

    args["build"] = build
    worker = asyncio.create_task(
        startup_diagnostics.run(
            drain_thread(service.refresh, **args), 0, "profile-test", cancel_on_deadline=False
        )
    )
    assert await asyncio.to_thread(entered.wait, 5)
    assert not worker.done()
    worker.cancel()
    await asyncio.sleep(0)
    worker.cancel()
    assert not worker.done()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await worker
    assert service.stats()["count"] == 1
    assert (
        next(x for x in startup_diagnostics.report() if x["step"] == "profile-test")["state"]
        == "cancelled_outcome_unconfirmed"
    )


@pytest.mark.parametrize("failure", ["dump", "fsync", "replace"])
def test_unique_atomic_writer_preserves_previous_file(tmp_path, monkeypatch, failure):
    import file_utils

    path = tmp_path / "profiles.json"
    path.write_bytes(b"previous")
    other = tmp_path / ".atomic.other.tmp"
    other.write_bytes(b"other owner")

    def fail(*a, **kw):
        raise OSError("injected")

    if failure == "dump":
        monkeypatch.setattr(file_utils.json, "dump", fail)
    else:
        monkeypatch.setattr(file_utils.os, failure, fail)
    with pytest.raises(OSError):
        file_utils.atomic_json_write(str(path), {"players": {}})
    assert path.read_bytes() == b"previous"
    assert list(tmp_path.glob(".atomic.*")) == [other]


def test_name_projection_excludes_payloads_and_detaches_search_fields(cache):
    service, _ = cache

    class UncopyablePayload:
        def __deepcopy__(self, memo):
            raise AssertionError("name search must not copy nested profile payloads")

    service._players = {
        "1": {"GovernorName": "Ada", "GovernorID": 1, "KVK": UncopyablePayload()},
        "2": {"GovernorName": ["malformed"], "GovernorID": 2, "KVK": UncopyablePayload()},
    }
    entries = service.name_entries()
    assert entries[0] == ("Ada", 1)
    entries[1][0].append("caller mutation")
    assert service._players["2"]["GovernorName"] == ["malformed"]


def test_name_projection_does_not_hold_reader_lock_during_iteration(cache):
    service, _ = cache
    entered, release = Event(), Event()

    class PausedRow(dict):
        def get(self, key, default=None):
            if key == "GovernorName":
                entered.set()
                assert release.wait(5)
            return super().get(key, default)

    service._players = {"1": PausedRow(GovernorName="Ada", GovernorID=1)}
    with ThreadPoolExecutor(2) as pool:
        projected = pool.submit(service.name_entries)
        try:
            assert entered.wait(5)
            pool.submit(service.invalidate, 1).result(2)
        finally:
            release.set()
        assert projected.result(5) == (("Ada", 1),)
    assert service.name_entries() == ()


def test_autocomplete_projects_names_without_full_profile_snapshot(cache, monkeypatch):
    import profile_cache

    service, _ = cache
    service._players = {
        "1": {"GovernorName": "Ada", "GovernorID": 1, "KVK": [{"nested": [1, 2, 3]}]},
        "2": {"GovernorName": "Ada", "GovernorID": "2"},
        "3": {"GovernorName": None, "GovernorID": 3},
        "4": {"GovernorName": "Ada", "GovernorID": "invalid"},
        "5": {"GovernorName": ["malformed"], "GovernorID": 5},
    }
    monkeypatch.setattr(profile_cache, "_service", service)
    monkeypatch.setattr(profile_cache, "warm_cache", lambda: None)
    monkeypatch.setattr(profile_cache, "HAVE_RAPIDFUZZ", False)

    def full_snapshot_forbidden():
        raise AssertionError("autocomplete must not deep-copy the full profile cache")

    monkeypatch.setattr(service, "snapshot", full_snapshot_forbidden)
    assert profile_cache.autocomplete_choices("Ada") == [("Ada (1)", "1"), ("Ada (2)", "2")]
    assert profile_cache.autocomplete_choices("Ada", limit=1) == [("Ada (1)", "1")]
