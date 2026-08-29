from __future__ import annotations

import pytest

from upload_routes import inventory_route as route


class _FakeChannel:
    def __init__(self, channel_id: int = 10):
        self.id = channel_id
        self.sent = []

    async def send(self, *args, **kwargs):
        self.sent.append((args, kwargs))


class _FakeAuthor:
    id = 123456789


class _FakeMessage:
    def __init__(self, channel_id: int = 10, attachments=None):
        self.id = 987
        self.channel = _FakeChannel(channel_id)
        self.author = _FakeAuthor()
        self.attachments = attachments if attachments is not None else [object()]


def _deps(**overrides):
    calls = []

    async def upload_handler(message, bot):
        calls.append((message, bot))
        if "handler_exception" in overrides:
            raise overrides["handler_exception"]
        return overrides.get("handler_result", True)

    deps = route.InventoryRouteDeps(
        inventory_upload_channel_id=overrides.get("channel_id", 10),
        bot=overrides.get("bot", object()),
        upload_handler=upload_handler,
    )
    return deps, calls


@pytest.mark.asyncio
async def test_inventory_route_ignores_unconfigured_channel():
    deps, calls = _deps(channel_id=0)

    handled = await route.handle_inventory_upload(_FakeMessage(), deps)

    assert handled is False
    assert calls == []


@pytest.mark.asyncio
async def test_inventory_route_ignores_other_channels():
    deps, calls = _deps()

    handled = await route.handle_inventory_upload(_FakeMessage(channel_id=99), deps)

    assert handled is False
    assert calls == []


@pytest.mark.asyncio
async def test_inventory_route_ignores_empty_attachments():
    deps, calls = _deps()

    handled = await route.handle_inventory_upload(_FakeMessage(attachments=[]), deps)

    assert handled is False
    assert calls == []


@pytest.mark.asyncio
async def test_inventory_route_delegates_and_returns_handler_result():
    bot = object()
    message = _FakeMessage()
    deps, calls = _deps(bot=bot, handler_result=False)

    handled = await route.handle_inventory_upload(message, deps)

    assert handled is False
    assert calls == [(message, bot)]


@pytest.mark.asyncio
async def test_inventory_route_exception_sends_existing_fallback_message():
    message = _FakeMessage()
    deps, calls = _deps(handler_exception=RuntimeError("boom"))

    handled = await route.handle_inventory_upload(message, deps)

    assert handled is True
    assert len(calls) == 1
    assert message.channel.sent == [
        (
            ("<@123456789> Inventory import failed unexpectedly. Please try again.",),
            {"delete_after": 120},
        )
    ]
