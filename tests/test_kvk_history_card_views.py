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


class _Flags:
    def __init__(self, *, ephemeral: bool = False):
        self.ephemeral = ephemeral


class _Message:
    def __init__(self, *, fail: bool = False, ephemeral: bool = False):
        self.edits = []
        self.fail = fail
        self.flags = _Flags(ephemeral=ephemeral)

    async def edit(self, **kwargs):
        if self.fail:
            raise RuntimeError("message missing")
        self.edits.append(kwargs)


class _Followup:
    def __init__(self):
        self.messages = []

    async def send(self, content=None, **kwargs):
        self.messages.append({"content": content, **kwargs})


class _Interaction:
    def __init__(self, *, message: _Message | None = None, fail_original: bool = False):
        self.user = SimpleNamespace(id=42)
        self.response = _Response()
        self.message = message
        self.followup = _Followup()
        self.original_edits = []
        self.fail_original = fail_original

    async def edit_original_response(self, **kwargs):
        if self.fail_original:
            raise RuntimeError("original missing")
        self.original_edits.append(kwargs)


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


@pytest.mark.asyncio
async def test_edit_host_message_falls_back_to_original_response_when_source_edit_fails():
    view = _view()
    interaction = _Interaction(message=_Message(fail=True))

    edited = await view._edit_host_message(interaction, content="fallback", view=view)

    assert edited is True
    assert interaction.original_edits == [{"content": "fallback", "view": view}]
    assert interaction.followup.messages == []


@pytest.mark.asyncio
async def test_edit_host_message_rebuilds_payload_for_retry():
    view = _view()
    interaction = _Interaction(message=_Message(fail=True))
    calls = []

    def build_kwargs():
        calls.append(len(calls) + 1)
        return {"files": [SimpleNamespace(token=calls[-1])], "view": view}

    edited = await view._edit_host_message(interaction, build_kwargs=build_kwargs)

    assert edited is True
    assert calls == [1, 2]
    assert interaction.original_edits[-1]["files"][0].token == 2


@pytest.mark.asyncio
async def test_edit_host_message_uses_original_response_for_ephemeral_messages():
    view = _view()
    message = _Message(fail=True, ephemeral=True)
    interaction = _Interaction(message=message)

    edited = await view._edit_host_message(interaction, content="ephemeral edit", view=view)

    assert edited is True
    assert message.edits == []
    assert interaction.original_edits == [{"content": "ephemeral edit", "view": view}]


@pytest.mark.asyncio
async def test_edit_host_message_sends_notice_when_message_is_gone():
    view = _view()
    interaction = _Interaction(message=_Message(fail=True), fail_original=True)

    edited = await view._edit_host_message(interaction, content="fallback", view=view)

    assert edited is False
    assert interaction.followup.messages == [
        {
            "content": "This history card message is no longer available. Run `/kvk history` again.",
            "ephemeral": True,
        }
    ]


@pytest.mark.asyncio
async def test_export_csv_sends_ephemeral_file(monkeypatch):
    import ui.views.kvk_history_card_views as views

    captured_ids = []

    def fake_fetch(governor_ids):
        captured_ids.extend(governor_ids)
        return "history-frame"

    def fake_csv(df, filename):
        assert df == "history-frame"
        assert filename == "kvk_history.csv"
        return "history.csv", b"Governor,KVK\nTester,15\n"

    monkeypatch.setattr(views.kvk_history_service, "fetch_history_export_for_governors", fake_fetch)
    monkeypatch.setattr(views, "build_history_csv", fake_csv)

    view = _view()
    followup = _Followup()
    interaction = SimpleNamespace(
        user=SimpleNamespace(id=42),
        response=_Response(),
        followup=followup,
    )

    await view._export_csv(interaction)

    assert captured_ids == ["2441482"]
    assert followup.messages[-1]["content"] == "Here's your CSV export."
    assert followup.messages[-1]["ephemeral"] is True
    assert followup.messages[-1]["file"].filename == "history.csv"


@pytest.mark.asyncio
async def test_export_csv_sends_ephemeral_failure_message(monkeypatch):
    import ui.views.kvk_history_card_views as views

    def fake_fetch(_governor_ids):
        raise RuntimeError("export unavailable")

    monkeypatch.setattr(views.kvk_history_service, "fetch_history_export_for_governors", fake_fetch)

    view = _view()
    followup = _Followup()
    interaction = SimpleNamespace(
        user=SimpleNamespace(id=42),
        response=_Response(),
        followup=followup,
    )

    await view._export_csv(interaction)

    assert followup.messages[-1] == {
        "content": "Failed to build CSV export.",
        "ephemeral": True,
    }
