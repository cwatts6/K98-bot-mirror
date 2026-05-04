import asyncio
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
    assert view._expired is True
    assert all(getattr(item, "disabled", False) for item in view.children)


async def test_confirmation_view_timeout_edits_message(monkeypatch):
    async def _cancel(_batch_id):
        return None

    class _ReviewMessage:
        def __init__(self):
            self.edits = []

        async def edit(self, **kwargs):
            self.edits.append(kwargs)

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
    message = _ReviewMessage()
    view.message = message

    await view.on_timeout()

    assert message.edits
    assert "expired" in message.edits[0]["content"]


async def test_confirmation_view_timeout_watch_disables_message(monkeypatch):
    async def _cancel(_batch_id):
        return None

    class _ReviewMessage:
        def __init__(self):
            self.edits = []

        async def edit(self, **kwargs):
            self.edits.append(kwargs)

    monkeypatch.setattr(inventory_views.inventory_service, "cancel_import", _cancel)
    view = inventory_views.InventoryConfirmationView(
        bot=object(),
        actor_discord_id=42,
        governor_id=111,
        batch_id=99,
        payload=InventoryImagePayload(image_bytes=b"img", filename="inventory.png"),
        summary=InventoryAnalysisSummary(
            ok=True,
            import_type=InventoryImportType.SPEEDUPS,
            values={"speedups": {}},
            confidence_score=0.95,
        ),
    )
    message = _ReviewMessage()
    view.message = message

    view.start_timeout_watch(timeout_seconds=0.01)
    await asyncio.sleep(0.03)

    assert view._expired is True
    assert message.edits
    assert all(getattr(item, "disabled", False) for item in view.children)


async def test_interaction_review_followup_gets_ephemeral_delete_after(monkeypatch):
    message = _Message()
    sent = {}

    class _Response:
        def __init__(self):
            self.done = False

        def is_done(self):
            return self.done

        async def defer(self, **_kwargs):
            self.done = True

    class _Followup:
        async def send(self, **kwargs):
            sent.update(kwargs)
            return types.SimpleNamespace(edit=lambda **_k: None)

    interaction = types.SimpleNamespace(
        user=types.SimpleNamespace(id=42),
        response=_Response(),
        followup=_Followup(),
    )
    summary = InventoryAnalysisSummary(
        ok=True,
        import_type=InventoryImportType.SPEEDUPS,
        values={"speedups": {}},
        confidence_score=0.95,
    )

    async def _create_upload_first_batch(**_kwargs):
        return 99

    async def _analyse_inventory_image(**_kwargs):
        return summary

    monkeypatch.setattr(
        inventory_views.inventory_service,
        "create_upload_first_batch",
        _create_upload_first_batch,
    )
    monkeypatch.setattr(
        inventory_views.inventory_service,
        "analyse_inventory_image",
        _analyse_inventory_image,
    )
    monkeypatch.setattr(
        inventory_views.InventoryConfirmationView,
        "start_timeout_watch",
        lambda self: None,
    )

    await inventory_views._process_payload_for_governor(
        bot=object(),
        interaction=interaction,
        governor_id=111,
        actor_discord_id=42,
        payload=InventoryImagePayload(image_bytes=b"img", filename="inventory.png"),
        original_message=message,
        batch_id=None,
        flow_from_pending_command=False,
    )

    assert sent["ephemeral"] is True
    assert sent["delete_after"] == inventory_views.INVENTORY_REVIEW_UI_TIMEOUT_SECONDS
