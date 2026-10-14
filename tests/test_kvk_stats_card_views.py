from __future__ import annotations

from dataclasses import replace
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from kvk.models.kvk_stats_card import KvkStatsCardPayload, KvkTargetProgress
from ui.views.kvk_stats_card_views import (
    KvkStatsCardView,
    build_more_stats_embed,
)


def _payload() -> KvkStatsCardPayload:
    return KvkStatsCardPayload(
        governor_id="123",
        governor_name="Card Tester",
        kvk_no=54,
        kvk_name="Tides of War",
        kingdom=1978,
        camp_name="Wind",
        last_refresh=None,
        status="INCLUDED",
        kvk_rank=12,
        matchmaking_power=100_000_000,
        kp_gain=500_000_000,
        kills_gain=300_000_000,
        kill_target=400_000_000,
        kill_progress=KvkTargetProgress(
            current=300_000_000,
            target=400_000_000,
            percent=75.0,
            color_hex="#2ecc71",
            quote="Fight more, still time!",
        ),
        deads=20_000_000,
        dead_target=20_000_000,
        dead_target_percent=100.0,
        power_loss=-5_000_000,
        healed=10_000_000,
        kp_loss=200_000_000,
        tanking_score_percent=40.0,
        acclaim=10,
        dkp=25_000_000,
        dkp_target=50_000_000,
        dkp_target_percent=50.0,
        overall_kvk_rank=42,
        overall_kvk_total_governors=8_734,
        overall_kvk_top_percent=0.48,
        pass_stats={"Pass 4 Kills": 1_000},
        prekvk_rank=7,
        prekvk_points=123_456,
        honor_rank=9,
        honor_points=654_321,
        history_summary={"KVK Played": 3},
        personal_bests={"Most Kills": 900_000_000},
        last_kvk_summary={
            "KVK_NO": 53,
            "Kills": 250_000_000,
            "Kill Target": 300_000_000,
            "Kill Percent": 83.3,
            "Deads": 10_000_000,
            "Dead Target": 12_000_000,
            "Dead Percent": 83.3,
            "DKP": 11_000_000,
            "DKP Target": 12_000_000,
            "DKP Percent": 91.6,
            "KP": 400_000_000,
            "Acclaim": 8,
        },
        matchmaking_snapshot={"MM KP": 100_000_000},
    )


def test_more_stats_embed_uses_payload_context():
    embed = build_more_stats_embed(_payload())

    assert embed.title == "More KVK Stats - Card Tester"
    assert embed.description == "KVK 54 | Tides of War"
    assert (
        next(f.value for f in embed.fields if f.name == "KVK Overall Rank")
        == "#42\nTotal 8.7k / Top 0.5%"
    )
    assert any(field.name == "Passes" for field in embed.fields)


@pytest.mark.asyncio
async def test_stats_card_view_exposes_current_kvk_buttons_only():
    rendered = SimpleNamespace(filename="main.png", image_bytes=BytesIO(b"main-card-bytes"))
    view = KvkStatsCardView(payload=_payload(), rendered=rendered)

    labels = [getattr(child, "label", None) for child in view.children]

    assert labels == ["Main Card", "More Stats"]


class _Response:
    def __init__(self, events: list[str] | None = None):
        self.send_message = AsyncMock()
        self._done = False
        self.events = events if events is not None else []

    def is_done(self):
        return self._done

    async def defer(self):
        self.events.append("defer")
        self._done = True
        return None


class _Message:
    def __init__(self):
        self.id = 42
        self.edits = []

    async def edit(self, **kwargs):
        self.edits.append(kwargs)


def _interaction(message: _Message, events: list[str] | None = None):
    return SimpleNamespace(
        response=_Response(events),
        message=message,
        user=SimpleNamespace(id=1),
        guild=None,
        guild_id=None,
        channel_id=2,
        followup=SimpleNamespace(send=AsyncMock()),
    )


@pytest.mark.asyncio
async def test_more_stats_button_prefers_rendered_card(monkeypatch):
    import ui.views.kvk_stats_card_views as views

    def fake_render(_payload):
        return SimpleNamespace(
            filename="more.png",
            image_bytes=BytesIO(b"more-card-bytes"),
        )

    monkeypatch.setattr(views, "render_kvk_more_stats_card", fake_render)
    rendered = SimpleNamespace(filename="main.png", image_bytes=BytesIO(b"main-card-bytes"))
    view = KvkStatsCardView(payload=_payload(), rendered=rendered)
    message = _Message()
    view.message = message
    view.owner_id = 1
    view.channel_id = 2
    view.payload = replace(view.payload, camp_name=None, overall_kvk_rank=None)
    view._bound_payload = view.payload

    await view._show_more_stats(_interaction(message))

    assert message.edits[-1]["embeds"] == []
    assert message.edits[-1]["files"][0].filename == "more.png"


@pytest.mark.asyncio
async def test_more_stats_button_defers_before_render(monkeypatch):
    import ui.views.kvk_stats_card_views as views

    events: list[str] = []

    def fake_render(_payload):
        events.append("render")
        return SimpleNamespace(
            filename="more.png",
            image_bytes=BytesIO(b"more-card-bytes"),
        )

    monkeypatch.setattr(views, "render_kvk_more_stats_card", fake_render)
    rendered = SimpleNamespace(filename="main.png", image_bytes=BytesIO(b"main-card-bytes"))
    view = KvkStatsCardView(payload=_payload(), rendered=rendered)
    message = _Message()
    view.message = message
    view.owner_id = 1
    view.channel_id = 2
    view.payload = replace(view.payload, camp_name=None, overall_kvk_rank=None)
    view._bound_payload = view.payload

    await view._show_more_stats(_interaction(message, events))

    assert events[:2] == ["defer", "render"]


@pytest.mark.asyncio
async def test_more_stats_button_falls_back_to_embed_when_card_unavailable(monkeypatch):
    import ui.views.kvk_stats_card_views as views

    monkeypatch.setattr(views, "render_kvk_more_stats_card", lambda _payload: None)
    rendered = SimpleNamespace(filename="main.png", image_bytes=BytesIO(b"main-card-bytes"))
    view = KvkStatsCardView(payload=_payload(), rendered=rendered)
    message = _Message()
    view.message = message
    view.owner_id = 1
    view.channel_id = 2
    view.payload = replace(view.payload, camp_name=None, overall_kvk_rank=None)
    view._bound_payload = view.payload

    await view._show_more_stats(_interaction(message))

    assert "files" not in message.edits[-1]
    assert message.edits[-1]["embeds"][0].title == "More KVK Stats - Card Tester"


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["owner", "message", "channel", "guild", "expired", "inputs"])
async def test_stats_buttons_reject_wrong_or_mutated_binding(case):
    rendered = SimpleNamespace(filename="main.png", image_bytes=BytesIO(b"main"))
    view = KvkStatsCardView(payload=_payload(), rendered=rendered, owner_id=1)
    message = _Message()
    view.message = message
    view.channel_id = 2
    interaction = _interaction(message)
    if case == "owner":
        interaction.user.id = 3
    if case == "message":
        interaction.message = SimpleNamespace(id=99)
    if case == "channel":
        interaction.channel_id = 3
    if case == "guild":
        interaction.guild_id = 3
    if case == "expired":
        view._expired = True
    if case == "inputs":
        view.payload = replace(view.payload, kills_gain=999)
    assert not await view.interaction_check(interaction)
    assert not message.edits
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_stats_buttons_recheck_permission_after_render(monkeypatch):
    import ui.views.kvk_stats_card_views as views

    payload = replace(_payload(), camp_name=None, overall_kvk_rank=None)
    rendered = SimpleNamespace(filename="main.png", image_bytes=BytesIO(b"main"))
    view = KvkStatsCardView(payload=payload, rendered=rendered, owner_id=1)
    message = _Message()
    view.message = message
    view.channel_id = 2
    view.guild_id = 3
    interaction = _interaction(message)
    interaction.guild_id = 3
    permissions = SimpleNamespace(view_channel=True, send_messages=True)
    interaction.guild = SimpleNamespace(fetch_member=AsyncMock(return_value=interaction.user))
    interaction.channel = SimpleNamespace(permissions_for=lambda _: permissions)

    def render(_):
        permissions.send_messages = False
        return rendered

    monkeypatch.setattr(views, "render_kvk_more_stats_card", render)
    await view._show_more_stats(interaction)
    assert not message.edits
    assert interaction.guild.fetch_member.await_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "channel", [None, SimpleNamespace(), SimpleNamespace(permissions_for=None)]
)
async def test_card_destination_rejects_missing_permission_channel(channel):
    from ui.views.kvk_stats_card_views import require_card_destination

    guild = SimpleNamespace(fetch_member=AsyncMock())
    context = SimpleNamespace(guild=guild, channel=channel, user=SimpleNamespace(id=1))
    with pytest.raises(PermissionError, match="destination is unavailable"):
        await require_card_destination(context)
    guild.fetch_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_card_view_missing_channel_reports_unavailable_without_editing():
    rendered = SimpleNamespace(filename="main.png", image_bytes=BytesIO(b"main"))
    view = KvkStatsCardView(payload=_payload(), rendered=rendered, owner_id=1)
    message = _Message()
    view.message = message
    view.channel_id = 2
    view.guild_id = 3
    interaction = _interaction(message)
    interaction.guild_id = 3
    interaction.guild = SimpleNamespace(fetch_member=AsyncMock())
    interaction.channel = None
    assert not await view.interaction_check(interaction)
    interaction.response.send_message.assert_awaited_once()
    interaction.guild.fetch_member.assert_not_awaited()
    assert not message.edits
