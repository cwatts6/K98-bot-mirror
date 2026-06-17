from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace

import pytest

from kvk.models.kvk_history_payload import KvkHistoryPayload, KvkHistoryRow, RenderedKvkHistoryCard
from ui.views.kvk_history_card_views import KvkHistoryCardView


def _payload() -> KvkHistoryPayload:
    row = KvkHistoryRow(kvk_no=15, row_present=True, kills=1)
    return KvkHistoryPayload(
        governor_id="2441482",
        governor_name="Tester",
        started_kvks=(15,),
        last3_kvks=(15,),
        rows=(row,),
        last3_rows=(row,),
    )


class _Response:
    def __init__(self):
        self._done = False
        self.messages = []

    def is_done(self):
        return self._done

    async def defer(self):
        self._done = True

    async def send_message(self, content, *, ephemeral=False):
        self.messages.append((content, ephemeral))
        self._done = True


class _Message:
    def __init__(self):
        self.edits = []

    async def edit(self, **kwargs):
        self.edits.append(kwargs)


def _view() -> KvkHistoryCardView:
    rendered = RenderedKvkHistoryCard(
        filename="history.png",
        image_bytes=BytesIO(b"history-bytes"),
    )
    return KvkHistoryCardView(
        payload=_payload(),
        rendered=rendered,
        author_id=42,
    )


@pytest.mark.asyncio
async def test_history_card_view_buttons_are_phase_4bii_scope():
    view = _view()

    assert [getattr(child, "label", None) for child in view.children] == [
        "History",
        "Summary",
        "Export CSV",
    ]


@pytest.mark.asyncio
async def test_history_card_view_rejects_other_users():
    view = _view()
    response = _Response()
    interaction = SimpleNamespace(user=SimpleNamespace(id=99), response=response)

    allowed = await view._check_user(interaction)

    assert allowed is False
    assert response.messages == [("This control isn't for you.", True)]


@pytest.mark.asyncio
async def test_history_button_restores_main_card():
    view = _view()
    message = _Message()
    interaction = SimpleNamespace(
        user=SimpleNamespace(id=42),
        response=_Response(),
        message=message,
    )

    await view._show_history(interaction)

    assert message.edits[-1]["files"][0].filename == "history.png"
    assert message.edits[-1]["embeds"] == []
