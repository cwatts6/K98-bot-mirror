"""C1: finite restart inventory, retained cursor and bounded existing-message work."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from mge import mge_embed_manager as boards
from mge.dal import mge_recovery_dal as dal
from mge.dataset_errors import MgeDatasetError
from mge.mge_board_preparation import board_binding, recovered_identity
from mge.mge_recovery import RecoverySweep
from services.event_delivery_store import delivery_key


def row(event_id):
    return {
        "EventId": event_id,
        "Status": "completed",
        "SignupEmbedChannelId": 1,
        "SignupEmbedMessageId": event_id + 100,
        "LeadershipEmbedMessageId": None,
        "AwardEmbedMessageId": None,
    }


@pytest.mark.asyncio
async def test_keyset_highwater_and_poison_target_do_not_starve_later_events(monkeypatch):
    monkeypatch.setattr(dal, "recovery_high_water", lambda: 52)
    pages = []

    def page(after, high_water, **kwargs):
        assert high_water == 52 and kwargs["include_completed"]
        pages.append(after)
        return [row(eid) for eid in range(after + 1, min(after + 50, high_water) + 1)]

    monkeypatch.setattr(dal, "recovery_page", page)
    calls, active, peak = [], 0, 0

    async def sync(**kwargs):
        nonlocal active, peak
        assert (
            kwargs["existing_only"] and kwargs["is_rehydrate"] and not kwargs["announce_everyone"]
        )
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0)
        active -= 1
        calls.append(kwargs["event_id"])
        return kwargs["event_id"] != 3

    monkeypatch.setattr(boards, "sync_event_signup_embed", sync)
    sweep = RecoverySweep(include_completed=True)
    await sweep.advance(object())
    assert sweep.cursor == 50 and not sweep.complete
    await sweep.advance(object())
    assert sweep.complete and sweep.cursor == 52 and pages == [0, 50]
    assert sorted(calls) == list(range(1, 53)) and peak <= 2
    assert sweep.counts == {
        "scanned": 52,
        "eligible": 52,
        "refreshed": 51,
        "held": 0,
        "failed": 1,
        "outstanding": 0,
    }


@pytest.mark.asyncio
async def test_failed_page_does_not_advance_cursor(monkeypatch):
    monkeypatch.setattr(dal, "recovery_high_water", lambda: 100)
    calls = []

    def page(after, high_water, **kwargs):
        calls.append(after)
        if len(calls) == 1:
            raise MgeDatasetError("unavailable", "page")
        return []

    monkeypatch.setattr(dal, "recovery_page", page)
    sweep = RecoverySweep(include_completed=False)
    await sweep.advance(object())
    assert sweep.cursor == 0 and not sweep.complete
    await sweep.advance(object())
    assert calls == [0, 0] and sweep.complete and sweep.counts["failed"] == 1


def receipt_fixture():
    event = {
        "EventId": 7,
        "UpdatedUtc": datetime(2026, 10, 28, tzinfo=UTC),
        "UpdatedUtcToken": "2026-10-28T00:00:00.0000001",
        "Status": "signup_closed",
        "RuleMode": "fixed",
        "PublishVersion": 0,
        "SignupEmbedChannelId": None,
        "SignupEmbedMessageId": None,
    }
    receipt = {
        "key": delivery_key("mge_board", "signup", 7, 1),
        "kind": "mge_signup_board",
        "state": "acknowledged",
        "event": "7",
        "target": "1",
        "channel_id": 1,
        "message_id": 10,
        "event_data": {"board_binding": board_binding(event, "signup", 1)},
    }
    return event, receipt


@pytest.mark.parametrize("change", ["old", "key", "version", "cleared", "entered", "destination"])
def test_historical_or_ambiguous_receipt_cannot_recreate_identity(change):
    event, receipt = receipt_fixture()
    assert recovered_identity(event, "signup", 1, receipt) == 10
    if change == "old":
        receipt.pop("event_data")
    if change == "key":
        receipt["key"] = "wrong"
    if change == "version":
        event["PublishVersion"] = 1
    if change == "cleared":
        event["UpdatedUtcToken"] = "2026-10-29T00:00:00.0000001"
    if change == "entered":
        receipt["state"] = "entered"
    if change == "destination":
        receipt["target"] = "2"
    with pytest.raises(MgeDatasetError):
        recovered_identity(event, "signup", 1, receipt)


@pytest.mark.asyncio
async def test_calendar_failure_and_invalid_default_do_not_disable_recovery(monkeypatch):
    from mge import mge_scheduler as scheduler

    recovery = AsyncMock()
    receipts = AsyncMock()
    monkeypatch.setattr(scheduler.RecoverySweep, "advance", recovery)
    monkeypatch.setattr(scheduler.RecoverySweep, "receipts", receipts)
    monkeypatch.setattr(scheduler, "resolve_public_signup_channel_id", lambda: (0, None, "fixture"))

    def unavailable(**kwargs):
        raise OSError("calendar unavailable")

    monkeypatch.setattr(scheduler, "sync_mge_events_from_calendar", unavailable)
    monkeypatch.setattr(scheduler.mge_finalisation, "sweep", AsyncMock())

    async def stop(_):
        raise asyncio.CancelledError

    monkeypatch.setattr(scheduler.asyncio, "sleep", stop)
    with pytest.raises(asyncio.CancelledError):
        await scheduler.schedule_mge_lifecycle(SimpleNamespace())
    recovery.assert_awaited_once()
    receipts.assert_awaited_once()


@pytest.mark.asyncio
async def test_unavailable_receipt_read_remains_pending_for_next_tick(monkeypatch):
    from mge import mge_scheduler as scheduler
    from mge.mge_recovery import delivery

    receipt_reads = AsyncMock(side_effect=[OSError("offline"), []])
    monkeypatch.setattr(delivery, "receipt_rows", receipt_reads)
    monkeypatch.setattr(dal, "recovery_high_water", lambda: 0)
    monkeypatch.setattr(dal, "recovery_page", lambda *a, **k: [])
    monkeypatch.setattr(scheduler, "resolve_public_signup_channel_id", lambda: (0, None, "fixture"))
    monkeypatch.setattr(
        scheduler,
        "sync_mge_events_from_calendar",
        lambda **_: (_ for _ in ()).throw(OSError("offline")),
    )
    monkeypatch.setattr(scheduler.mge_finalisation, "sweep", AsyncMock())
    ticks = []

    async def tick(_):
        ticks.append(1)
        if len(ticks) == 3:
            raise asyncio.CancelledError

    monkeypatch.setattr(scheduler.asyncio, "sleep", tick)
    with pytest.raises(asyncio.CancelledError):
        await scheduler.schedule_mge_lifecycle(SimpleNamespace())
    assert receipt_reads.await_count == 2
