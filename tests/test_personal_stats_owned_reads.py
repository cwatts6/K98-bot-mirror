"""Real physical barriers, distinct from fake TimeoutError-only coverage."""

import asyncio
from contextvars import ContextVar
import json
import threading
import time

import pytest

from core.owned_work import drain_thread
from player_self_service import stats_runtime, stats_service
from player_self_service.stats_models import PersonalStatsUnavailable


async def entered(event):
    async with asyncio.timeout(3):
        while not event.is_set():
            await asyncio.sleep(0.001)


@pytest.mark.asyncio
async def test_real_nine_second_timeout_keeps_exact_key_and_physical_capacity():
    runtime = stats_runtime.get_runtime()
    release, started = threading.Event(), threading.Event()
    calls = []

    def loader(ids, **kwargs):
        calls.append(ids)
        started.set()
        assert release.wait(25)
        return "immutable-fixture"

    async def request():
        with runtime.journey():
            return await stats_service._authorized_dataset(42, (111,), loader, (("Main", 111),))

    try:
        with pytest.raises(TimeoutError):
            await request()
        assert started.is_set()
        assert len(runtime.jobs) == len(runtime.inflight) == 1
        first = next(iter(runtime.inflight.values()))
        with pytest.raises(TimeoutError):
            await request()
        assert next(iter(runtime.inflight.values())) is first
        assert len(calls) == 1
        assert runtime.observers == 0
    finally:
        release.set()
        await first.task
    assert not runtime.jobs
    assert len(runtime.cache) == 1


@pytest.mark.asyncio
async def test_thousand_arrivals_bound_observers_and_eight_physical_jobs():
    runtime = stats_runtime.get_runtime()
    release = threading.Event()
    calls = []

    def work(run):
        calls.append(run.key)
        assert release.wait(5)

    async def request(index):
        try:
            with runtime.journey():
                run = runtime.submit("dataset", work, key=(index, (1,)))
                await runtime.observe(run, runtime.deadline(0.04))
        except (TimeoutError, PersonalStatsUnavailable):
            return

    try:
        await asyncio.gather(*(request(i) for i in range(1000)))
        assert len(runtime.jobs) == 8
        assert len(calls) <= 8
        assert runtime.observers == 0
        assert len(runtime.inflight) == 8
    finally:
        release.set()
        assert await runtime.drain()


@pytest.mark.asyncio
async def test_same_key_observers_capped_before_task_allocation():
    runtime = stats_runtime.get_runtime()
    release = threading.Event()
    calls = []

    def work(run):
        calls.append(1)
        release.wait(5)

    async def request():
        with runtime.journey():
            await runtime.observe(
                runtime.submit("dataset", work, key=(42, (1,))), runtime.deadline(4)
            )

    tasks = [asyncio.create_task(request()) for _ in range(1000)]
    try:
        await asyncio.sleep(0.05)
        assert runtime.observers == 32
        assert len(runtime.jobs) == 1
        assert calls == [1]
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        assert runtime.observers == 0
        release.set()
        assert await runtime.drain()


@pytest.mark.asyncio
async def test_cancel_before_entry_never_submits_or_leaks():
    runtime = stats_runtime.get_runtime()
    calls = []
    run = runtime.submit("dataset", lambda run: calls.append(1), key=(42, (1,)))
    run.task.cancel()
    await asyncio.gather(run.task, return_exceptions=True)
    assert calls == []
    assert not runtime.jobs and not runtime.inflight


@pytest.mark.asyncio
async def test_repeated_cancel_and_context_propagation_keep_native_owned():
    flag = ContextVar("fixture", default="missing")
    flag.set("copied")
    release, started = threading.Event(), threading.Event()
    observed = []

    def work():
        observed.append(flag.get())
        started.set()
        release.wait(5)
        observed.append("settled")

    task = asyncio.create_task(drain_thread(work))
    try:
        await entered(started)
        for _ in range(4):
            task.cancel()
            await asyncio.sleep(0.005)
            assert not task.done()
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)
    assert observed == ["copied", "settled"]


@pytest.mark.asyncio
async def test_cache_failure_never_leaks_physically_settled_reservation():
    runtime = stats_runtime.get_runtime()

    def fail(run):
        raise OSError("optional cache failure")

    run = runtime.submit("dataset", lambda run: "result", key=(42, (1,)), publish=fail)
    assert await runtime.observe(run, runtime.deadline(1)) == "result"
    assert not runtime.jobs and not runtime.inflight
    assert runtime.terminal[-1]["cache"] == "publication_failed"


@pytest.mark.asyncio
@pytest.mark.parametrize("invalidate", ["clear", "revoke", "shutdown"])
async def test_late_completion_cannot_repopulate_invalidated_cache(invalidate):
    runtime = stats_runtime.get_runtime()
    release, started = threading.Event(), threading.Event()

    def loader(ids, **kwargs):
        started.set()
        release.wait(4)
        return "fixture"

    task = asyncio.create_task(stats_service._authorized_dataset(42, (1,), loader, (("Main", 1),)))
    try:
        await entered(started)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        run = next(iter(runtime.jobs.values()))
        if invalidate == "shutdown":
            runtime.close_admission()
        else:
            runtime.invalidate(42 if invalidate == "revoke" else None)
        assert len(runtime.jobs) == 1
    finally:
        release.set()
        await run.task
    assert not runtime.cache and not runtime.jobs


@pytest.mark.asyncio
async def test_unknown_cleanup_retains_receipt_and_fails_repeated_drain(monkeypatch):
    # Deliberate uncertainty is isolated; never reset an actual runtime to hide it.
    runtime = stats_runtime.StatsRuntime()
    handle = object()

    def work(run):
        run.outcome.cleanup = "unconfirmed"
        run.outcome.retained_connection = handle
        return "private"

    run = runtime.submit("dataset", work, key=(42, (1,)))
    with pytest.raises(PersonalStatsUnavailable):
        await runtime.observe(run, runtime.deadline(1))
    assert runtime.closed and run.outcome.retained_connection is handle
    assert run.result is None
    assert not await runtime.drain()
    assert not await runtime.drain()
    with pytest.raises(PersonalStatsUnavailable):
        runtime.submit("registry", work)
    report = runtime.snapshot()
    assert report["cleanup_uncertain"]
    assert "private" not in json.dumps(report)
    assert len(json.dumps(report).encode()) <= 8192


@pytest.mark.asyncio
async def test_expired_caller_starts_no_worker_and_lease_is_released():
    runtime = stats_runtime.get_runtime()
    with runtime.journey(expiry=time.monotonic() - 1):
        with pytest.raises(TimeoutError):
            runtime.submit("registry", lambda run: pytest.fail("expired work"))
    assert runtime.observers == 0 and not runtime.jobs


@pytest.mark.asyncio
async def test_final_authorization_real_two_second_deadline_retains_registry_worker(monkeypatch):
    from services.governor_account_service import summarize_accounts
    from tests.test_player_self_service_stats_views import _payload

    runtime = stats_runtime.get_runtime()
    release = threading.Event()

    def registry(*args, **kwargs):
        release.wait(5)
        return summarize_accounts({"Main": {"GovernorID": "111", "GovernorName": "Fixture"}})

    monkeypatch.setattr(stats_service, "get_account_summary_for_user_sync", registry)
    started = time.perf_counter()
    try:
        with pytest.raises(PersonalStatsUnavailable):
            await stats_service.assert_personal_stats_access(_payload())
        assert time.perf_counter() - started <= 2.1
        assert len(runtime.jobs) == 1 and runtime.observers == 0
    finally:
        release.set()
        assert await runtime.drain()


@pytest.mark.asyncio
async def test_payload_deadline_includes_initial_registry_time(monkeypatch):
    from tests.test_player_self_service_stats_service import _summary

    runtime = stats_runtime.get_runtime()
    release = threading.Event()

    async def accounts(user):
        await asyncio.sleep(0.15)
        return _summary(("Main", 111, "Fixture"))

    def dataset(*args, **kwargs):
        release.wait(3)
        return object()

    monkeypatch.setattr(stats_service, "_DATA_TIMEOUT_SECONDS", 0.2)
    began = time.perf_counter()
    try:
        with pytest.raises(PersonalStatsUnavailable):
            await stats_service.build_personal_stats_payload(
                42, account_loader=accounts, data_loader=dataset
            )
        assert time.perf_counter() - began < 0.3
        assert len(runtime.jobs) == 1
    finally:
        release.set()
        assert await runtime.drain()


@pytest.mark.asyncio
async def test_cleanup_time_does_not_refresh_data_ready_ttl(monkeypatch):
    runtime = stats_runtime.get_runtime()
    release, ready = threading.Event(), threading.Event()

    def loader(ids, *, on_data_ready, sql_outcome, **kwargs):
        on_data_ready()
        ready.set()
        assert release.wait(3)
        sql_outcome.cleanup = "settled"
        return "fixture"

    monkeypatch.setattr(stats_service.personal_stats_dal, "fetch_personal_stats_daily", loader)
    task = asyncio.create_task(stats_service._authorized_dataset(42, (1,), loader, ()))
    try:
        await entered(ready)
        run = next(iter(runtime.jobs.values()))
        # Advance only the stored data age; production's 30-second TTL is unchanged.
        run.ready_at -= 31
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    finally:
        release.set()
        await run.task
    assert run.cache == "expired"
    assert not runtime.cache and not runtime.jobs


@pytest.mark.asyncio
async def test_optional_utc_clock_failure_cannot_block_read_or_release(monkeypatch):
    class BrokenClock:
        @staticmethod
        def now(*args):
            raise OSError("clock unavailable")

    monkeypatch.setattr(stats_runtime, "datetime", BrokenClock)
    runtime = stats_runtime.get_runtime()
    run = runtime.submit("dataset", lambda run: "result", key=(42, (1,)))
    assert await runtime.observe(run, runtime.deadline(1)) == "result"
    assert not runtime.jobs and not runtime.inflight
    assert runtime.terminal[-1]["read"] == "completed"


@pytest.mark.asyncio
async def test_complete_zip_contains_passive_personal_stats_evidence(monkeypatch):
    from tests.test_guided_recovery import ACTOR
    from tests.test_p013_complete_archive import read_archive
    from tests.test_recovery_report import report_service

    runtime = stats_runtime.get_runtime()
    runtime.delivery("unknown")
    monkeypatch.setattr(runtime, "submit", lambda *a, **k: pytest.fail("report started work"))
    service, _, _ = report_service(0)
    members, manifest = read_archive(service.download_complete_report(ACTOR))
    diagnostics = json.loads(members["diagnostic-health.json"])
    section = diagnostics["personal_stats"]
    assert section["coverage"]["status"] == "available"
    assert section["observation"]["observed"]
    assert section["observation"]["recent"][-1]["outcome"] == "unknown"
