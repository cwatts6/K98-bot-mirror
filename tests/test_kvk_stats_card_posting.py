from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.asyncio


class RejectsFilesChannel:
    def __init__(self):
        self.sent = []

    async def send(self, **kwargs):
        self.sent.append(kwargs)
        if kwargs.get("files"):
            raise RuntimeError("file uploads disabled")
        return SimpleNamespace(id="message")


async def test_post_kvk_stats_output_fallback_contains_independent_values(monkeypatch):
    import commands.kvk_stats_card_posting as posting

    channel = RejectsFilesChannel()
    monkeypatch.setenv("KVK_STATS_CARD_ENABLED", "0")
    posted, used = await posting.post_kvk_stats_output(
        bot=None,
        ctx=SimpleNamespace(channel=channel),
        row={"GovernorID": "123", "T4&T5_Kills": 123, "Kill Target": 200},
        user=SimpleNamespace(id=1),
    )
    assert posted and used == "orig_channel"
    assert len(channel.sent) == 1 and "files" not in channel.sent[0]
    embed = channel.sent[0]["embeds"][0]
    assert "123 / 200" in embed.fields[0].value
    assert "suppressed" in next(f.value for f in embed.fields if f.name == "Source context")


async def test_build_card_passes_discord_avatar_bytes_to_renderer(monkeypatch):
    import commands.kvk_stats_card_posting as posting

    class FakeAvatar:
        def __init__(self):
            self.size = None

        def with_size(self, size):
            self.size = size
            return self

        async def read(self):
            return b"avatar-bytes"

    captured = {}

    async def fake_payload(_row):
        return SimpleNamespace(governor_id="123")

    def fake_renderer(payload, *, avatar_bytes=None):
        captured["payload"] = payload
        captured["avatar_bytes"] = avatar_bytes
        return SimpleNamespace(filename="card.png", image_bytes=BytesIO(b"png-bytes"))

    monkeypatch.setattr(posting, "build_kvk_stats_card_payload", fake_payload)
    monkeypatch.setattr(posting, "render_kvk_stats_card", fake_renderer)

    user = SimpleNamespace(id=1, display_avatar=FakeAvatar())
    result = await posting._build_card({"GovernorID": "123"}, user)

    assert result is not None
    assert captured["avatar_bytes"] == b"avatar-bytes"
    assert user.display_avatar.size == 128


async def test_selection_change_during_stats_render_sends_only_independent_embed(monkeypatch):
    import commands.kvk_stats_card_posting as posting
    from tests.test_kvk_source_card_context import CardStore

    store = CardStore()
    store.install(monkeypatch)
    channel = RejectsFilesChannel()

    def render(payload, **kwargs):
        assert payload.source_context["available"]
        store.selection["PublicSelectionVersion"] += 1
        return SimpleNamespace(filename="old.png", image_bytes=BytesIO(b"old context"))

    monkeypatch.setattr(posting, "render_kvk_stats_card", render)
    posted, _ = await posting.post_kvk_stats_output(
        bot=None,
        ctx=SimpleNamespace(channel=channel),
        user=SimpleNamespace(id=1),
        row={"GovernorID": "1001", "KVK_NO": 16, "T4&T5_Kills": 123},
    )
    assert posted and len(channel.sent) == 1
    assert "files" not in channel.sent[0]
    assert "123" in channel.sent[0]["embeds"][0].fields[0].value
