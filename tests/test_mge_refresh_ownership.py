"""R1/L1: controlled barriers exercise ownership, coalescing and shutdown admission."""

import asyncio

import pytest

from mge.mge_refresh_work import RefreshCoordinator


@pytest.mark.asyncio
async def test_dirty_pass_reads_latest_state_and_waits_for_each_reply():
    work = RefreshCoordinator()
    entered, release, gate = asyncio.Event(), asyncio.Event(), asyncio.Event()
    state = {"value": 1}
    reads = []

    async def first():
        reads.append(state["value"])
        entered.set()
        await release.wait()
        return True

    async def latest():
        reads.append(state["value"])
        return True

    one = work.request((7, "public", 1, "silent"), first)
    await entered.wait()
    state["value"] = 2
    two = work.request((7, "public", 1, "silent"), latest, gate=gate)
    release.set()
    assert (await two.observe(0)).status == "pending"
    assert reads == [1]
    gate.set()
    assert (await one.observe()).status == "delivered"
    assert (await two.observe()).status == "delivered"
    assert reads == [1, 2]
    await work.drain()
    assert work.snapshot()["passes"] == 2


@pytest.mark.asyncio
async def test_observer_timeout_and_cancellation_do_not_cancel_shared_pass():
    work = RefreshCoordinator()
    entered, release = asyncio.Event(), asyncio.Event()

    async def refresh():
        entered.set()
        await release.wait()
        return True

    handle = work.request(7, refresh)
    await entered.wait()
    assert (await handle.observe(0)).status == "pending"
    waiter = asyncio.create_task(handle.observe())
    await asyncio.sleep(0)
    waiter.cancel()
    await asyncio.sleep(0)
    assert work.snapshot()["pending"] == 1
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await waiter
    assert (await handle.observe()).status == "delivered"
    await work.drain()


@pytest.mark.asyncio
async def test_no_implicit_retry_after_failed_pass():
    work = RefreshCoordinator()
    calls = []

    async def failing():
        calls.append(1)
        raise OSError("redacted")

    assert (await work.request(7, failing)).status == "failed"
    await work.drain()
    assert calls == [1]
    assert work.snapshot()["failed_passes"] == 1


@pytest.mark.asyncio
async def test_target_and_semantics_are_distinct():
    work = RefreshCoordinator()
    calls = []

    async def refresh(key):
        calls.append(key)
        return True

    keys = [
        (7, "public", 1, "silent"),
        (7, "leadership", 1, "silent"),
        (7, "public", 2, "silent"),
        (7, "public", 1, "recovery"),
    ]
    handles = [work.request(key, lambda key=key: refresh(key)) for key in keys]
    assert all(await asyncio.gather(*(handle.observe() for handle in handles)))
    await work.drain()
    assert set(calls) == set(keys)


@pytest.mark.asyncio
async def test_shutdown_rejects_new_roots_but_drains_entered_continuation():
    work = RefreshCoordinator()
    entered, release = asyncio.Event(), asyncio.Event()
    calls = []

    async def refresh():
        calls.append("delivered")
        return True

    async def primary():
        entered.set()
        await release.wait()
        return await work.request(7, refresh)

    task = asyncio.create_task(work.run_direct(primary))
    await entered.wait()
    work.close_background()
    with pytest.raises(RuntimeError):
        work.request(8, refresh)
    drain = asyncio.create_task(work.drain())
    await asyncio.sleep(0)
    assert not drain.done()
    release.set()
    assert await task
    await drain
    assert calls == ["delivered"]
    assert work.snapshot()["direct"] == work.snapshot()["pending"] == 0


@pytest.mark.asyncio
async def test_group_retains_successful_registration_when_one_target_is_refused(monkeypatch):
    from mge import mge_embed_manager as boards

    original = boards._refreshes.request

    async def delivered(**kwargs):
        return True

    def selective(key, factory, **kwargs):
        if key[2] == "leadership":
            raise RuntimeError("refused")
        return original(key, factory, **kwargs)

    monkeypatch.setattr(boards._refreshes, "request", selective)
    monkeypatch.setattr(boards, "sync_event_signup_embed", delivered)
    group = boards.request_board_refresh(
        bot=object(), event_id=7, signup_channel_id=1, leadership_channel_id=2
    )
    assert not group.registered
    results = await group.observe()
    assert results["public"].status == "delivered"
    assert results["leadership"].status == "refused"
    assert results["awards"].status == "not_requested"
    await boards.drain_refreshes()
