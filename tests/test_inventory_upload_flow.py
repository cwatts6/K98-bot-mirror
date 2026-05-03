import types

import pytest

from inventory.models import (
    InventoryAnalysisSummary,
    InventoryImagePayload,
    InventoryImportType,
    RegisteredGovernor,
)
from ui.views import inventory_views

pytestmark = pytest.mark.asyncio


class _Attachment:
    filename = "inventory.png"
    content_type = "image/png"
    url = "https://cdn.test/inventory.png"

    async def read(self):
        return b"image-bytes"


class _Channel:
    def __init__(self, channel_id=555):
        self.id = channel_id
        self.sent = []

    async def send(self, *args, **kwargs):
        self.sent.append((args, kwargs))
        return types.SimpleNamespace(id=999, channel=self, edit=lambda **_k: None)


class _Message:
    def __init__(self):
        self.id = 123
        self.channel = _Channel()
        self.author = types.SimpleNamespace(id=42)
        self.attachments = [_Attachment()]
        self.deleted = False

    async def delete(self):
        self.deleted = True


async def test_upload_first_single_governor_processes_and_deletes(monkeypatch):
    message = _Message()
    calls = {}

    async def _pending(_user_id):
        return None

    async def _governors(_user_id):
        return [RegisteredGovernor(111, "Gov", "Main")]

    async def _process(**kwargs):
        calls.update(kwargs)

    monkeypatch.setattr(inventory_views.inventory_service, "get_pending_command_session", _pending)
    monkeypatch.setattr(
        inventory_views.inventory_service, "get_registered_governors_for_user", _governors
    )
    monkeypatch.setattr(inventory_views, "_process_payload_for_governor", _process)

    handled = await inventory_views.handle_inventory_upload_message(message, bot=object())

    assert handled is True
    assert calls["governor_id"] == 111
    assert calls["payload"].image_bytes == b"image-bytes"
    assert calls["payload"].source_channel_id == message.channel.id


async def test_upload_first_without_governors_sends_guidance(monkeypatch):
    message = _Message()

    async def _pending(_user_id):
        return None

    async def _governors(_user_id):
        return []

    monkeypatch.setattr(inventory_views.inventory_service, "get_pending_command_session", _pending)
    monkeypatch.setattr(
        inventory_views.inventory_service, "get_registered_governors_for_user", _governors
    )

    handled = await inventory_views.handle_inventory_upload_message(message, bot=object())

    assert handled is True
    assert "registered governor" in message.channel.sent[0][0][0]


async def test_confirmation_view_timeout_cancels_active_batch(monkeypatch):
    cancelled = []

    async def _cancel(batch_id):
        cancelled.append(batch_id)

    monkeypatch.setattr(inventory_views.inventory_service, "cancel_import", _cancel)
    view = inventory_views.InventoryConfirmationView(
        bot=object(),
        actor_discord_id=42,
        governor_id=111,
        batch_id=99,
        payload=InventoryImagePayload(image_bytes=b"img", filename="inventory.png"),
        summary=InventoryAnalysisSummary(
            ok=True,
            import_type=InventoryImportType.RESOURCES,
            values={"resources": {}},
            confidence_score=0.95,
        ),
    )

    await view.on_timeout()

    assert cancelled == [99]
