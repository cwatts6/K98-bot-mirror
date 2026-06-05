from __future__ import annotations

from dataclasses import replace
from io import BytesIO
from types import SimpleNamespace

import pytest

from kvk.models.kvk_stats_card import KvkStatsCardPayload, KvkTargetProgress
from ui.views.kvk_stats_card_views import (
    KvkStatsCardView,
    build_history_embed,
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
        playstyle="Sniping Kills",
        acclaim=10,
        dkp=25_000_000,
        dkp_target=50_000_000,
        dkp_target_percent=50.0,
        overall_kvk_rank=42,
        overall_kvk_total_governors=8_734,
        overall_kvk_percentile=0.48,
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
    assert embed.fields[0].name == "KVK Overall Rank"
    assert embed.fields[0].value == "#42\nTotal 8.7k / Top 0.5%"
    assert any(field.name == "Passes" for field in embed.fields)


def test_history_embed_includes_last_kvk_summary():
    embed = build_history_embed(_payload())

    assert embed.title == "Historic KVK Data - Card Tester"
    assert any(field.name == "Last KVK Summary - KVK 53" for field in embed.fields)
    assert all(field.name != "Matchmaking Snapshot" for field in embed.fields)


def test_history_embed_filters_zero_summary_and_personal_best_rows():
    payload = replace(
        _payload(),
        history_summary={"Autarch": 0, "KVK Played": 0, "Highest Acclaim": 0},
        personal_bests={"Most Kills": 0, "Most Deads": 0, "Most Heal": 0},
        last_kvk_summary={},
        matchmaking_snapshot={"MM KP": 100_000_000},
    )

    embed = build_history_embed(payload)
    field_names = [field.name for field in embed.fields]

    assert "Summary" not in field_names
    assert "Personal Bests" not in field_names
    assert "Matchmaking Snapshot" not in field_names
    assert field_names == ["Last KVK Summary"]


class _Response:
    def __init__(self, events: list[str] | None = None):
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
        self.edits = []

    async def edit(self, **kwargs):
        self.edits.append(kwargs)


def _interaction(message: _Message, events: list[str] | None = None):
    return SimpleNamespace(response=_Response(events), message=message)


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

    await view._show_more_stats(_interaction(message, events))

    assert events[:2] == ["defer", "render"]


@pytest.mark.asyncio
async def test_more_stats_button_falls_back_to_embed_when_card_unavailable(monkeypatch):
    import ui.views.kvk_stats_card_views as views

    monkeypatch.setattr(views, "render_kvk_more_stats_card", lambda _payload: None)
    rendered = SimpleNamespace(filename="main.png", image_bytes=BytesIO(b"main-card-bytes"))
    view = KvkStatsCardView(payload=_payload(), rendered=rendered)
    message = _Message()

    await view._show_more_stats(_interaction(message))

    assert "files" not in message.edits[-1]
    assert message.edits[-1]["embeds"][0].title == "More KVK Stats - Card Tester"


@pytest.mark.asyncio
async def test_history_button_prefers_rendered_card(monkeypatch):
    import ui.views.kvk_stats_card_views as views

    def fake_render(_payload):
        return SimpleNamespace(
            filename="history.png",
            image_bytes=BytesIO(b"history-card-bytes"),
        )

    monkeypatch.setattr(views, "render_kvk_history_card", fake_render)
    rendered = SimpleNamespace(filename="main.png", image_bytes=BytesIO(b"main-card-bytes"))
    view = KvkStatsCardView(payload=_payload(), rendered=rendered)
    message = _Message()

    await view._show_history(_interaction(message))

    assert message.edits[-1]["embeds"] == []
    assert message.edits[-1]["files"][0].filename == "history.png"


@pytest.mark.asyncio
async def test_history_button_defers_before_render(monkeypatch):
    import ui.views.kvk_stats_card_views as views

    events: list[str] = []

    def fake_render(_payload):
        events.append("render")
        return SimpleNamespace(
            filename="history.png",
            image_bytes=BytesIO(b"history-card-bytes"),
        )

    monkeypatch.setattr(views, "render_kvk_history_card", fake_render)
    rendered = SimpleNamespace(filename="main.png", image_bytes=BytesIO(b"main-card-bytes"))
    view = KvkStatsCardView(payload=_payload(), rendered=rendered)
    message = _Message()

    await view._show_history(_interaction(message, events))

    assert events[:2] == ["defer", "render"]
