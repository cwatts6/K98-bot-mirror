import asyncio
from itertools import product
import threading

import pytest

from event_calendar import service
from event_calendar.cache_publisher import PublishResult
from event_calendar.event_generator import GenerationResult
from event_calendar.mutation_owner import get_owner
from event_calendar.sheets_sync import SyncResult
from event_calendar.sql_lifecycle import SqlOutcome


@pytest.fixture
def boundaries(monkeypatch):
    calls = []
    for name, cls in (
        ("sync_sheets_to_sql", SyncResult),
        ("generate_calendar_instances", GenerationResult),
        ("publish_event_calendar_cache", PublishResult),
    ):

        def invoke(*args, _name=name, _cls=cls, **kwargs):
            calls.append(_name)
            return _cls(ok=True, status="success")

        monkeypatch.setattr(service, name, invoke)
    return calls


async def invoke(svc, kind, **kwargs):
    if kind in {"sync", "pipeline"}:
        return await getattr(svc, "refresh" if kind == "sync" else "refresh_pipeline")(
            sheet_id="offline", **kwargs
        )
    return await getattr(svc, "generate" if kind == "generate" else "publish_cache")(**kwargs)


async def entered(event):
    for _ in range(2000):
        if event.is_set():
            return
        await asyncio.sleep(0.001)
    raise AssertionError("physical worker did not enter")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "first,second", list(product(("sync", "generate", "publish", "pipeline"), repeat=2))
)
async def test_all_mutation_pairs_share_physical_owner(monkeypatch, boundaries, first, second):
    gate, release = threading.Event(), threading.Event()
    stage = {
        "sync": "sync_sheets_to_sql",
        "generate": "generate_calendar_instances",
        "publish": "publish_event_calendar_cache",
        "pipeline": "sync_sheets_to_sql",
    }[first]
    original = getattr(service, stage)

    def block(*args, **kwargs):
        gate.set()
        assert release.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(service, stage, block)
    first_svc, other_svc = service.CalendarService(), service.CalendarService()
    task = asyncio.create_task(invoke(first_svc, first))
    try:
        await entered(gate)
        refused = await invoke(other_svc, second)
        assert refused["status"] == "busy"
        assert refused["pipeline_run_id"] is None
        assert refused["blocking_run_id"] == get_owner().active.reference
        prior_delivery = dict(get_owner().active.result.get("delivery", {}))
        other_svc.record_delivery(refused["pipeline_run_id"], "succeeded")
        assert get_owner().active.result.get("delivery", {}) == prior_delivery
        assert not boundaries
    finally:
        release.set()
        result = await task
        await get_owner().audit.drain()
    assert result["ok"]


@pytest.mark.asyncio
@pytest.mark.parametrize("blocked", ["sync", "generate", "publish"])
async def test_deadline_repeated_cancel_stops_later_stages(monkeypatch, boundaries, blocked):
    gate, release = threading.Event(), threading.Event()
    attr = {
        "sync": "sync_sheets_to_sql",
        "generate": "generate_calendar_instances",
        "publish": "publish_event_calendar_cache",
    }[blocked]
    original = getattr(service, attr)

    def block(*args, **kwargs):
        gate.set()
        assert release.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(service, attr, block)
    for name in ("SYNC", "GENERATE", "PUBLISH"):
        monkeypatch.setattr(service, "EVENT_CALENDAR_PIPELINE_" + name + "_TIMEOUT_SECONDS", 0.01)
    svc = service.CalendarService()
    task = asyncio.create_task(invoke(svc, "pipeline"))
    try:
        await entered(gate)
        await asyncio.sleep(0.03)
        assert get_owner().active.observer == "deadline_elapsed_pending"
        task.cancel()
        await asyncio.sleep(0.005)
        task.cancel()
        await asyncio.sleep(0.005)
        assert not task.done()
        assert (await svc.generate())["status"] == "busy"
    finally:
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        await get_owner().audit.drain()
    assert boundaries[-1] == attr
    assert len(boundaries) == ("sync", "generate", "publish").index(blocked) + 1
    assert get_owner().active is None


@pytest.mark.asyncio
async def test_one_scheduled_intent_revalidates_after_owner(monkeypatch, boundaries):
    gate, release = threading.Event(), threading.Event()
    original = service.generate_calendar_instances

    def block(**kwargs):
        gate.set()
        assert release.wait(5)
        return original(**kwargs)

    monkeypatch.setattr(service, "generate_calendar_instances", block)
    svc = service.CalendarService()
    active = asyncio.create_task(svc.generate())
    pending = None
    try:
        await entered(gate)
        pending = asyncio.create_task(svc.refresh_pipeline(sheet_id="offline", scheduled=True))
        await asyncio.sleep(0.01)
        assert get_owner().deferred
        assert (await svc.refresh_pipeline(sheet_id="offline", scheduled=True))[
            "status"
        ] == "already_deferred"
        assert (await svc.publish_cache())["status"] == "busy"
    finally:
        release.set()
        await active
        if pending:
            assert (await pending)["ok"]
        await get_owner().audit.drain()
    assert boundaries.count("sync_sheets_to_sql") == 1


@pytest.mark.asyncio
async def test_acknowledged_commit_with_unconfirmed_cleanup_blocks_admission(monkeypatch):
    connection = object()
    result = GenerationResult(
        True,
        "success",
        instances_generated=12,
        instances_written=12,
        sql=SqlOutcome(effect="committed", cleanup="unconfirmed", retained_connection=connection),
    )
    monkeypatch.setattr(service, "generate_calendar_instances", lambda **kwargs: result)
    svc = service.CalendarService()
    output = await svc.generate()
    assert output["ok"] and output["instances_written"] == 12
    assert output["severity"] == "warning"
    assert (await svc.publish_cache())["status"] == "cleanup_unconfirmed"
    assert get_owner().active.raw["generate"].sql.retained_connection is connection
    assert not (await svc.drain())["ok"]


@pytest.mark.asyncio
async def test_cancel_before_executor_entry_prevents_mutation(monkeypatch, boundaries):
    from concurrent.futures import ThreadPoolExecutor

    loop = asyncio.get_running_loop()
    previous = loop._default_executor
    executor = ThreadPoolExecutor(max_workers=1)
    loop.set_default_executor(executor)
    occupied, release = threading.Event(), threading.Event()

    def read():
        occupied.set()
        assert release.wait(5)

    blocker = loop.run_in_executor(None, read)
    task = None
    try:
        await entered(occupied)
        task = asyncio.create_task(service.CalendarService().generate())
        for _ in range(100):
            if get_owner().active and get_owner().active.phase == "submitted":
                break
            await asyncio.sleep(0.001)
        task.cancel()
        await asyncio.sleep(0.01)
        assert not task.done() and not boundaries
    finally:
        release.set()
        await blocker
        if task:
            with pytest.raises(asyncio.CancelledError):
                await task
        if previous is not None:
            loop.set_default_executor(previous)
        else:
            loop._default_executor = None
        executor.shutdown()
    assert not boundaries
    assert get_owner().last.results["generate"]["status"] == "not_started"


@pytest.mark.asyncio
async def test_shutdown_closes_admission_discards_deferred_and_drains_repeated_cancel(
    monkeypatch, boundaries
):
    gate, release = threading.Event(), threading.Event()
    original = service.generate_calendar_instances

    def block(**kwargs):
        gate.set()
        assert release.wait(5)
        return original(**kwargs)

    monkeypatch.setattr(service, "generate_calendar_instances", block)
    svc = service.CalendarService()
    active = asyncio.create_task(svc.refresh_pipeline(sheet_id="offline"))
    await entered(gate)
    pending = asyncio.create_task(svc.refresh_pipeline(sheet_id="offline", scheduled=True))
    await asyncio.sleep(0.01)
    drain = asyncio.create_task(svc.drain())
    try:
        await asyncio.sleep(0.01)
        assert not svc.admission_open() and get_owner().audit.closed
        drain.cancel()
        await asyncio.sleep(0.005)
        drain.cancel()
        await asyncio.sleep(0.005)
        assert not drain.done()
        assert (await svc.generate())["status"] == "admission_closed"
    finally:
        release.set()
        await active
        assert (await pending)["status"] == "admission_closed"
        with pytest.raises(asyncio.CancelledError):
            await drain
    assert boundaries == ["sync_sheets_to_sql", "generate_calendar_instances"]
    assert (await svc.drain())["ok"]
