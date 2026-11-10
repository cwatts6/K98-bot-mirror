import asyncio
from collections import Counter
from contextvars import ContextVar
from datetime import date
import json
import threading
import time
import tracemalloc

import pytest

from player_self_service import stats_runtime, stats_service
from player_self_service.stats_models import PersonalStatsUnavailable


@pytest.mark.asyncio
async def test_ten_distinct_key_cycles_have_bounded_retention_and_drain_cost():
    runtime = stats_runtime.get_runtime()
    counts = []
    # Same immutable fixture identity isolates coordinator cost from dataset size.
    fixture = object()
    tracemalloc.start()
    try:
        start = tracemalloc.get_traced_memory()[0]
        for cycle in range(10):
            for index in range(100):
                await stats_service._authorized_dataset(
                    cycle * 100 + index, (1,), lambda *a, **k: fixture, (("Main", 1),)
                )
            counts.append(
                (
                    len(runtime.cache),
                    len(runtime.terminal),
                    len(runtime.jobs),
                    len(runtime.inflight),
                )
            )
        retained = tracemalloc.get_traced_memory()[0] - start
    finally:
        tracemalloc.stop()
    assert counts == [(32, 32, 0, 0)] * 10
    assert retained < 8 * 1024 * 1024
    began = time.perf_counter()
    assert await runtime.drain()
    assert time.perf_counter() - began < 0.25


@pytest.mark.asyncio
async def test_saturated_refusal_cost_and_no_final_check_overcommit():
    runtime = stats_runtime.StatsRuntime()
    release = threading.Event()
    try:
        for index in range(8):
            runtime.submit("dataset", lambda run: release.wait(4), key=(index, (1,)))
        samples = []
        for _ in range(1000):
            began = time.perf_counter()
            with pytest.raises(PersonalStatsUnavailable):
                runtime.submit("registry", lambda run: pytest.fail("ninth SQL entry"))
            samples.append(time.perf_counter() - began)
        assert sorted(samples)[989] <= 0.05
        assert len(runtime.jobs) == 8
    finally:
        release.set()
        assert await runtime.drain()


@pytest.mark.asyncio
async def test_snapshot_keeps_uncertainty_with_max_records_and_truncation():
    runtime = stats_runtime.StatsRuntime()
    runtime.close_admission("cleanup_uncertain")
    for index in range(10):
        run = stats_runtime.ReadRun("dataset" if index < 8 else "render")
        run.outcome.cleanup = "unconfirmed"
        run.error = RuntimeError("private values must never be projected")
        runtime.jobs[id(run)] = run
    for _ in range(32):
        runtime.terminal.append(run.snapshot())
    samples = []
    for _ in range(1000):
        began = time.perf_counter()
        value = runtime.snapshot()
        samples.append(time.perf_counter() - began)
    raw = json.dumps(value)
    assert len(raw.encode()) <= 8192
    assert value["cleanup_uncertain"] and value["admission_closed"]
    assert len(value["reads"]) == 8 and len(value["renders"]) == 2
    assert value["omitted_terminal"] > 0
    assert "private values" not in raw
    assert sorted(samples)[989] <= 0.002


@pytest.mark.asyncio
async def test_real_render_deadline_retains_bounded_job():
    from player_self_service.stats_models import StatsMode
    from player_self_service.stats_renderer import RenderedStatsCard
    from tests.test_player_self_service_stats_views import _payload
    from ui.views.player_self_service_stats_views import _run_renderer

    runtime = stats_runtime.get_runtime()
    release = threading.Event()

    def renderer(*args, **kwargs):
        release.wait(6)
        return RenderedStatsCard("fixture.png", b"png")

    began = time.perf_counter()
    try:
        with pytest.raises(TimeoutError):
            await _run_renderer(
                renderer,
                _payload(),
                mode=StatsMode.OVERVIEW,
                display_name="Fixture",
                avatar_bytes=None,
            )
        assert time.perf_counter() - began <= 3.6
        assert len(runtime.jobs) == 1
    finally:
        release.set()
        assert await runtime.drain()


@pytest.mark.asyncio
async def test_mixed_users_cache_joins_and_final_checks_make_useful_progress(monkeypatch):
    from tests.test_player_self_service_stats_service import _complete_row, _dataset, _summary

    runtime = stats_runtime.get_runtime()
    stage = ContextVar("fixture_registry_stage", default=0)
    refused, completed = Counter(), Counter()
    dataset_calls = 0
    peak = 0
    day = date(2026, 11, 5)
    summary = _summary(("Main", 111, "Fixture"))
    fixture = _dataset(day, _complete_row(111, day))

    def registry(*args, **kwargs):
        time.sleep(0.001)
        return summary

    def dataset(*args, **kwargs):
        nonlocal dataset_calls
        dataset_calls += 1
        time.sleep(0.003)
        return fixture

    original_registry = stats_service._load_registry

    async def load_registry(*args, **kwargs):
        index = stage.get()
        stage.set(index + 1)
        try:
            return await original_registry(*args, **kwargs)
        except PersonalStatsUnavailable:
            refused[("pre", "post", "final")[min(index, 2)]] += 1
            raise

    original_data = stats_service._authorized_dataset

    async def load_dataset(*args, **kwargs):
        try:
            return await original_data(*args, **kwargs)
        except PersonalStatsUnavailable:
            refused["dataset"] += 1
            raise

    monkeypatch.setattr(stats_service, "get_account_summary_for_user_sync", registry)
    monkeypatch.setattr(stats_service, "_load_registry", load_registry)
    monkeypatch.setattr(stats_service, "_authorized_dataset", load_dataset)
    cached_payloads = {}

    async def request(user, mode_only=False):
        nonlocal peak
        stage.set(2 if mode_only else 0)
        try:
            with runtime.journey():
                if mode_only:
                    payload = cached_payloads[user]
                else:
                    payload = await stats_service.build_personal_stats_payload(
                        user, data_loader=dataset
                    )
                peak = max(peak, len(runtime.jobs))
                await stats_service.assert_personal_stats_access(payload)
                cached_payloads[user] = payload
                completed[user] += 1
        except PersonalStatsUnavailable:
            pass

    users = [42] * 4 + [100, 101, 102, 103] + [42] * 4
    for wave in range(32):
        if wave % 4 == 0:
            runtime.invalidate(42)
        await asyncio.gather(
            *(request(user, mode_only=wave % 3 == 2 and user in cached_payloads) for user in users)
        )
    assert all(completed[user] > 0 for user in set(users))
    assert sum(completed.values()) > 32
    assert dataset_calls < sum(completed.values())
    assert peak <= 8 and not runtime.jobs and runtime.observers == 0
    print(
        json.dumps(
            dict(
                mixed_workload=dict(
                    completed=dict(completed),
                    refused=dict(refused),
                    dataset_calls=dataset_calls,
                    peak=peak,
                )
            ),
            sort_keys=True,
        )
    )
