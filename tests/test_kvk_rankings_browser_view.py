from types import SimpleNamespace

import pytest

from kvk.models.kvk_rankings import RankingPayload, RankingRow
from kvk.rendering.kvk_rankings_embed import build_current_rankings_embed
from ui.views import kvk_rankings_views
from ui.views.kvk_rankings_views import CurrentRankingsBrowserView


def _labels(view):
    return [getattr(item, "label", None) for item in view.children if getattr(item, "label", None)]


def _channel_interaction(*, channel_id=100, user_id=200, message=None, followup=None):
    class Response:
        def __init__(self):
            self.sent = []

        def is_done(self):
            return False

        async def defer(self):
            return None

        async def send_message(self, content=None, **kwargs):
            self.sent.append((content, kwargs))

    response = Response()
    return SimpleNamespace(
        response=response,
        channel=SimpleNamespace(id=channel_id),
        user=SimpleNamespace(id=user_id),
        message=message,
        followup=followup,
    )


@pytest.mark.asyncio
async def test_current_rankings_browser_exposes_mode_metric_and_primary_limits():
    view = CurrentRankingsBrowserView(mode="prekvk", metric="stage2", limit=25)

    labels = _labels(view)
    assert labels == ["Top 10", "Top 25", "Top 50"]
    assert "Top 100" not in labels
    assert view.mode_select is not None
    assert [option.value for option in view.mode_select.options] == ["kvk", "honor", "prekvk"]
    assert view.metric_select is not None
    assert [option.value for option in view.metric_select.options] == [
        "overall",
        "stage1",
        "stage2",
        "stage3",
    ]


@pytest.mark.asyncio
async def test_current_rankings_browser_disables_single_metric_honor_selector():
    view = CurrentRankingsBrowserView(mode="honor", limit=10)

    assert view.metric_select is not None
    assert view.metric_select.disabled is True
    assert [option.value for option in view.metric_select.options] == ["honor"]


@pytest.mark.asyncio
async def test_current_rankings_browser_refresh_edits_component_message(monkeypatch):
    monkeypatch.setattr(kvk_rankings_views, "KVK_PLAYER_STATS_CHANNEL_ID", 100)
    payload = RankingPayload(
        mode="kvk",
        mode_label="KVK",
        metric="kills",
        metric_label="Kills",
        limit=25,
        rows=[
            RankingRow(
                rank=1,
                governor_id=123,
                governor_name="Alpha",
                value=1000,
                supporting_values={"Kills": 1000},
            )
        ],
    )
    view = CurrentRankingsBrowserView(mode="kvk", metric="power", limit=10)

    async def fake_payload(**kwargs):
        assert kwargs == {"mode": "kvk", "metric": "power", "limit": 10}
        return payload

    class Message:
        def __init__(self):
            self.kwargs = None

        async def edit(self, **kwargs):
            self.kwargs = kwargs

    message = Message()
    monkeypatch.setattr(
        kvk_rankings_views.kvk_rankings_service,
        "build_current_rankings_payload",
        fake_payload,
    )

    interaction = _channel_interaction(channel_id=100, message=message)

    await view._refresh(interaction)

    assert view.message is message
    assert view.metric == "kills"
    assert view.limit == 25
    assert message.kwargs["view"] is view
    assert "Top 25 Kills" in message.kwargs["embed"].title


@pytest.mark.asyncio
async def test_current_rankings_browser_refresh_failure_is_private(monkeypatch):
    monkeypatch.setattr(kvk_rankings_views, "KVK_PLAYER_STATS_CHANNEL_ID", 100)
    view = CurrentRankingsBrowserView(mode="kvk", metric="power", limit=10)
    sent = []

    async def fake_payload(**_kwargs):
        raise RuntimeError("cache failed")

    class Followup:
        async def send(self, content=None, **kwargs):
            sent.append((content, kwargs))

    monkeypatch.setattr(
        kvk_rankings_views.kvk_rankings_service,
        "build_current_rankings_payload",
        fake_payload,
    )

    interaction = _channel_interaction(channel_id=100, followup=Followup())

    await view._refresh(interaction)

    assert sent
    assert "failed to refresh" in sent[0][0]
    assert sent[0][1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_current_rankings_browser_blocks_honor_switch_outside_stats_channel_for_admin(
    monkeypatch,
):
    monkeypatch.setattr(kvk_rankings_views, "KVK_PLAYER_STATS_CHANNEL_ID", 100)
    monkeypatch.setattr(kvk_rankings_views, "_is_admin", lambda _user: True)
    fetched = False

    async def fake_payload(**_kwargs):
        nonlocal fetched
        fetched = True
        raise AssertionError("honor payload should not be fetched")

    view = CurrentRankingsBrowserView(mode="kvk", metric="power", limit=10)
    view.mode_select = SimpleNamespace(values=["honor"])
    monkeypatch.setattr(
        kvk_rankings_views.kvk_rankings_service,
        "build_current_rankings_payload",
        fake_payload,
    )

    interaction = _channel_interaction(channel_id=999, user_id=1)

    await view.on_mode_change(interaction)

    assert fetched is False
    assert view.mode == "kvk"
    assert interaction.response.sent
    assert "<#100>" in interaction.response.sent[0][0]
    assert interaction.response.sent[0][1]["ephemeral"] is True


def test_current_rankings_embed_collapses_control_characters_in_rows():
    payload = RankingPayload(
        mode="prekvk",
        mode_label="PreKvK",
        metric="overall",
        metric_label="Overall",
        limit=10,
        rows=[
            RankingRow(
                rank=1,
                governor_id=123,
                governor_name="Bad\n`Name`",
                value=123456,
                supporting_values={"Power": "45M", "Stage 1": "12\n34"},
            )
        ],
    )

    embed = build_current_rankings_embed(payload)

    assert "Bad 'Name'" in embed.description
    assert "12 34" in embed.description


def test_current_rankings_embed_omits_sorted_metric_from_support_columns():
    payload = RankingPayload(
        mode="kvk",
        mode_label="KVK",
        metric="power",
        metric_label="Power",
        limit=10,
        total_rows=63,
        rows=[
            RankingRow(
                rank=1,
                governor_id=123,
                governor_name="Long Player Name",
                value=127_600_000,
                supporting_values={
                    "Power": 127_600_000,
                    "Kills": 35_400_000,
                    "% K/T": 236,
                    "Deads": 1_600_000,
                    "DKP": 119_200_000,
                },
            )
        ],
    )

    embed = build_current_rankings_embed(payload)
    table_lines = embed.description.removeprefix("```\n").removesuffix("\n```").splitlines()

    assert table_lines[0].count("Power") == 1
    assert table_lines[0] == "Rank Name          Power   Kills % K/T    Dead     DKP"
    assert all(len(line) <= 54 for line in table_lines)
    assert {len(line) for line in table_lines} == {len(table_lines[0])}
    assert "Showing: 1 of 63" in embed.footer.text


def test_current_rankings_embed_uses_top_label_without_true_total():
    payload = RankingPayload(
        mode="prekvk",
        mode_label="PreKvK",
        metric="overall",
        metric_label="Overall",
        limit=10,
        total_rows=None,
        rows=[
            RankingRow(
                rank=1,
                governor_id=123,
                governor_name="PrePlayer",
                value=123456,
                supporting_values={"Power": "45M", "Overall": 123456},
            )
        ],
    )

    embed = build_current_rankings_embed(payload)

    assert "Showing: Top 10" in embed.footer.text
    assert "Showing: 1 of 1" not in embed.footer.text
