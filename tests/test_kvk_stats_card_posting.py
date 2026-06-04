from __future__ import annotations

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
