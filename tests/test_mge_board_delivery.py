from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from mge.mge_board_delivery_adapter import send_board_once
from services import event_delivery_service as delivery
from services.event_delivery_store import DeliveryHeld, EventDeliveryStore


@pytest.mark.asyncio
async def test_acknowledged_send_recovers_exact_message_after_sql_save_failure_and_restart(
    tmp_path, monkeypatch
):
    path = tmp_path / "receipts.json"
    monkeypatch.setattr(delivery, "store", EventDeliveryStore(path))
    message = SimpleNamespace(id=123, edit=AsyncMock())
    channel = SimpleNamespace(
        id=456, send=AsyncMock(return_value=message), fetch_message=AsyncMock(return_value=message)
    )
    assert (
        await send_board_once(
            kind="signup",
            event_id=42,
            channel=channel,
            binding={"fixture_revision": 1},
            content="first",
        )
        is message
    )
    # SQL ID save failed after send; reconstruct the journal as a fresh process would.
    monkeypatch.setattr(delivery, "store", EventDeliveryStore(path))
    await send_board_once(
        kind="signup",
        event_id=42,
        channel=channel,
        binding={"fixture_revision": 1},
        content="current",
    )
    channel.send.assert_awaited_once()
    channel.fetch_message.assert_awaited_once_with(123)
    assert message.edit.await_args.kwargs["content"] == "current"
    assert not message.edit.await_args.kwargs["allowed_mentions"].everyone


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["send", "receipt"])
async def test_uncertain_send_or_receipt_is_held_across_restart(tmp_path, monkeypatch, failure):
    path = tmp_path / "receipts.json"
    store = EventDeliveryStore(path)
    monkeypatch.setattr(delivery, "store", store)
    channel = SimpleNamespace(id=456, send=AsyncMock(return_value=SimpleNamespace(id=123)))
    if failure == "send":
        channel.send.side_effect = OSError("lost send acknowledgement")
    else:
        monkeypatch.setattr(
            store, "finish", lambda *a, **k: (_ for _ in ()).throw(OSError("disk unavailable"))
        )
    with pytest.raises(OSError):
        await send_board_once(kind="signup", event_id=42, channel=channel, content="fixture")
    monkeypatch.setattr(delivery, "store", EventDeliveryStore(path))
    with pytest.raises(DeliveryHeld):
        await send_board_once(kind="signup", event_id=42, channel=channel, content="fixture")
    assert channel.send.await_count == 1


@pytest.mark.asyncio
async def test_journal_failure_prevents_external_entry(monkeypatch):
    monkeypatch.setattr(delivery.store, "get", lambda *a: (_ for _ in ()).throw(OSError("corrupt")))
    channel = SimpleNamespace(id=456, send=AsyncMock())
    with pytest.raises(OSError):
        await send_board_once(kind="signup", event_id=42, channel=channel)
    channel.send.assert_not_awaited()
