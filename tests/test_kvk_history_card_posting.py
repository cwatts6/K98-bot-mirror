from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace

import pytest

from commands.kvk_history_card_posting import (
    _read_avatar_bytes,
    _send_followup,
    post_kvk_history_output,
)
from kvk.models.kvk_history_payload import KvkHistoryPayload, KvkHistoryRow, RenderedKvkHistoryCard


class _Avatar:
    def __init__(self) -> None:
        self.sizes: list[int] = []

    def with_size(self, size: int):
        self.sizes.append(size)
        return self

    async def read(self) -> bytes:
        return b"avatar-bytes"


class _Followup:
    def __init__(self, *, reject_wait: bool = False) -> None:
        self.reject_wait = reject_wait
        self.calls: list[dict] = []

    async def send(self, **kwargs):
        self.calls.append(kwargs)
        if self.reject_wait and kwargs.get("wait") is True:
            raise TypeError("wait is unsupported")
        return SimpleNamespace(id=123)


@pytest.mark.asyncio
async def test_read_avatar_bytes_is_local_to_history_posting():
    avatar = _Avatar()
    user = SimpleNamespace(id=42, display_avatar=avatar)

    result = await _read_avatar_bytes(user)

    assert result == b"avatar-bytes"
    assert avatar.sizes == [128]


@pytest.mark.asyncio
async def test_send_followup_uses_wait_true_to_capture_message():
    followup = _Followup()
    target = SimpleNamespace(followup=followup)

    message = await _send_followup(target, content="hello", ephemeral=True)

    assert message.id == 123
    assert followup.calls == [{"content": "hello", "view": None, "ephemeral": True, "wait": True}]


@pytest.mark.asyncio
async def test_send_followup_falls_back_when_wait_is_unsupported():
    followup = _Followup(reject_wait=True)
    target = SimpleNamespace(followup=followup)

    message = await _send_followup(target, content="hello", ephemeral=False)

    assert message.id == 123
    assert followup.calls == [
        {"content": "hello", "view": None, "ephemeral": False, "wait": True},
        {"content": "hello", "view": None, "ephemeral": False},
    ]


@pytest.mark.asyncio
async def test_post_history_output_sends_view_with_trends_button(monkeypatch):
    import commands.kvk_history_card_posting as posting

    row = KvkHistoryRow(kvk_no=15, row_present=True, kills=1)
    payload = KvkHistoryPayload(
        governor_id="2441482",
        governor_name="Tester",
        started_kvks=(15,),
        last3_kvks=(15,),
        rows=(row,),
        last3_rows=(row,),
    )
    rendered = RenderedKvkHistoryCard(
        filename="history.png",
        image_bytes=BytesIO(b"history-bytes"),
    )

    async def fake_avatar(_user):
        return None

    monkeypatch.setattr(
        posting.kvk_history_service,
        "build_kvk_history_payload",
        lambda _gid: payload,
    )
    monkeypatch.setattr(
        posting,
        "render_kvk_history_last3_card",
        lambda *_args, **_kwargs: rendered,
    )
    monkeypatch.setattr(posting, "_read_avatar_bytes", fake_avatar)

    followup = _Followup()
    target = SimpleNamespace(followup=followup)
    user = SimpleNamespace(id=42)

    await post_kvk_history_output(target, user=user, governor_id="2441482", ephemeral=False)

    sent_view = followup.calls[-1]["view"]
    assert [getattr(child, "label", None) for child in sent_view.children] == [
        "History",
        "Summary",
        "Trends",
        "Export CSV",
    ]
