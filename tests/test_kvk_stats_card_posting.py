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
        user=SimpleNamespace(id=1, mention="<@1>"),
    )
    assert posted and used == "orig_channel"
    assert len(channel.sent) == 1 and "files" not in channel.sent[0]
    embed = channel.sent[0]["embeds"][0]
    assert "200" in embed.fields[0].value
    assert "123" in next(f.value for f in embed.fields if "KILLS" in f.name)
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
        user=SimpleNamespace(id=1, mention="<@1>"),
        row={"GovernorID": "1001", "KVK_NO": 16, "T4&T5_Kills": 123},
    )
    assert posted and len(channel.sent) == 1
    assert "files" not in channel.sent[0]
    assert "123" in next(f.value for f in channel.sent[0]["embeds"][0].fields if "KILLS" in f.name)


@pytest.mark.parametrize("failure", ["disabled", "render_none", "render_error", "stale", "send"])
@pytest.mark.parametrize("fallback_chain", [False, True])
async def test_fallback_preserves_history_and_tiers_without_source_context(
    monkeypatch, failure, fallback_chain
):
    from dataclasses import replace
    import json

    import commands.kvk_stats_card_posting as posting
    from kvk.services.kvk_stats_card_service import build_kvk_stats_card_payload
    from tests.test_kvk_source_card_context import CardStore

    store = CardStore()
    store.install(monkeypatch)
    row = {
        "GovernorID": "1001",
        "GovernorName": "Independent Player",
        "KVK_NO": 16,
        "T4_KILLS": 1234,
        "T5_KILLS": 2345,
        "T4&T5_Kills": 3579,
        "T4_Deads": 3456,
        "T5_Deads": 4567,
        "Deads_Delta": 8023,
        "Kill Target": 6000,
        "Dead_Target": 9000,
        "DKP_SCORE": 5678,
        "AutarchTimes": 3,
        "KvKPlayed": 7,
        "HighestAcclaim": 6789,
        "MostKvKKill": 7890,
        "MostKvKDead": 8901,
        "MostKvKHeal": 9012,
        "Starting_KillPoints": 12345,
        "Starting_T4&T5_KILLS": 23456,
        "Starting_Deads": 34567,
        "Starting_HealedTroops": 45678,
        "last_kvk": {"KVK_NO": 15, "T4&T5_Kills": 5432, "Kill Target": 6500},
        "camp_name": "FORBIDDEN CAMP",
        "overall_kvk_rank": "FORBIDDEN RANK",
    }
    payload = await build_kvk_stats_card_payload(row)
    payload = replace(payload, camp_name="FORBIDDEN CAMP", overall_kvk_rank=987654)

    async def saved_payload(_row):
        return payload

    async def current(_payload):
        if failure == "stale":
            raise RuntimeError("selection changed")

    def render(*args, **kwargs):
        if failure == "render_none":
            return None
        if failure == "render_error":
            raise RuntimeError("renderer unavailable")
        return SimpleNamespace(filename="card.png", image_bytes=BytesIO(b"context"))

    monkeypatch.setattr(posting, "build_kvk_stats_card_payload", saved_payload)
    monkeypatch.setattr(posting, "require_card_current", current)
    monkeypatch.setattr(posting, "render_kvk_stats_card", render)
    monkeypatch.setenv("KVK_STATS_CARD_ENABLED", "0" if failure == "disabled" else "1")
    channel = RejectsFilesChannel()
    user = SimpleNamespace(id=1, mention="<@1>")
    posted, _ = await posting.post_kvk_stats_output(
        bot=None,
        ctx=SimpleNamespace(channel=channel, user=user),
        row=row,
        user=user,
        use_fallback_chain=fallback_chain,
    )
    assert posted
    sent = channel.sent[-1]
    assert not sent.get("files") and not sent.get("view")
    assert len(sent["embeds"]) == 3
    serialized = json.dumps([embed.to_dict() for embed in sent["embeds"]])
    for expected in [
        "T4:",
        "T5:",
        "1.2k",
        "2.3k",
        "3.5k",
        "4.6k",
        "Autarch: 3",
        "KvK Played: 7",
        "Highest Acclaim:",
        "Most Kills:",
        "Most Deads:",
        "Most Heal:",
        "Last KVK Summary",
        "KVK 15",
        "5.4k",
        "MatchMaking Snapshot",
        "MM KP:",
        "12.3k",
        "MM Kills:",
        "23.5k",
        "MM Deads:",
        "34.6k",
        "MM Healed:",
        "45.7k",
        "suppressed",
    ]:
        assert expected in serialized
    for forbidden in ["FORBIDDEN", "987654", "attachment://", "thumbnail", "source_read"]:
        assert forbidden not in serialized
    assert payload.camp_name == "FORBIDDEN CAMP"  # Suppression never mutates the saved input.
