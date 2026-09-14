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


async def test_post_kvk_stats_output_retries_legacy_embeds_without_file(monkeypatch):
    import commands.kvk_stats_card_posting as posting

    channel = RejectsFilesChannel()
    ctx = SimpleNamespace(channel=channel)

    monkeypatch.setenv("KVK_STATS_CARD_ENABLED", "0")
    monkeypatch.setattr(
        posting,
        "build_stats_embed",
        lambda row, user: (["legacy-embed"], SimpleNamespace(fp=None)),
    )

    posted, used = await posting.post_kvk_stats_output(
        bot=None,
        ctx=ctx,
        row={"GovernorID": "123"},
        user=SimpleNamespace(id=1),
    )

    assert posted is True
    assert used == "orig_channel"
    assert channel.sent[0]["files"]
    assert channel.sent[1] == {"embeds": ["legacy-embed"]}


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
