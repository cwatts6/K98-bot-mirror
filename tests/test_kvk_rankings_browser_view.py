from io import BytesIO
from types import SimpleNamespace

import pytest

from kvk.models.kvk_rankings import (
    MyRankLookupResult,
    RankingAccountChoice,
    RankingPayload,
    RankingRow,
)
from kvk.rendering.kvk_rankings_embed import build_current_rankings_embed, build_my_rank_embed
from ui.views import kvk_rankings_views
from ui.views.kvk_rankings_views import CurrentRankingsBrowserView, _top10_card_file


def _labels(view):
    return [getattr(item, "label", None) for item in view.children if getattr(item, "label", None)]


def _channel_interaction(*, channel_id=100, user_id=200, message=None, followup=None):
    class Response:
        def __init__(self):
            self.sent = []
            self.defer_kwargs = None

        def is_done(self):
            return False

        async def defer(self, **kwargs):
            self.defer_kwargs = kwargs
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
    assert labels == ["Top 10", "Top 25", "Top 50", "My Rank"]
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
async def test_current_rankings_browser_uses_card_metrics_for_kvk_top10():
    view = CurrentRankingsBrowserView(mode="kvk", limit=10)

    assert view.metric == "kills"
    assert view.metric_select is not None
    options = [option.value for option in view.metric_select.options]
    assert options == [
        "kills",
        "pct_kill_target",
        "deads",
        "dkp",
        "acclaim",
        "tanking_score",
    ]
    assert "power" not in options


@pytest.mark.asyncio
async def test_current_rankings_browser_uses_compact_metrics_for_kvk_top25():
    view = CurrentRankingsBrowserView(mode="kvk", metric="power", limit=25)

    assert view.metric == "power"
    assert view.metric_select is not None
    options = [option.value for option in view.metric_select.options]
    assert options == ["power", "kills", "pct_kill_target", "deads", "dkp"]
    assert "acclaim" not in options


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
    view = CurrentRankingsBrowserView(mode="kvk", metric="power", limit=25)

    async def fake_payload(**kwargs):
        assert kwargs == {"mode": "kvk", "metric": "power", "limit": 25}
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
async def test_current_rankings_browser_refresh_swaps_top10_kvk_embed_for_card(monkeypatch):
    monkeypatch.setattr(kvk_rankings_views, "KVK_PLAYER_STATS_CHANNEL_ID", 100)
    payload = RankingPayload(
        mode="kvk",
        mode_label="KVK",
        metric="kills",
        metric_label="Kills",
        limit=10,
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
    view = CurrentRankingsBrowserView(mode="kvk", metric="kills", limit=10)
    fake_file = object()

    async def fake_payload(**kwargs):
        assert kwargs == {"mode": "kvk", "metric": "kills", "limit": 10}
        return payload

    async def fake_card_file(card_payload):
        assert card_payload is payload
        return fake_file

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
    monkeypatch.setattr(kvk_rankings_views, "_top10_card_file", fake_card_file)
    monkeypatch.setattr(
        kvk_rankings_views,
        "build_current_rankings_embed",
        lambda _payload: pytest.fail("embed should not be built on card success"),
    )

    interaction = _channel_interaction(channel_id=100, message=message)

    await view._refresh(interaction)

    assert message.kwargs["content"] is None
    assert message.kwargs["embeds"] == []
    assert message.kwargs["attachments"] == []
    assert message.kwargs["files"] == [fake_file]
    assert message.kwargs["view"] is view


@pytest.mark.asyncio
async def test_current_rankings_card_file_skips_ineligible_payload(monkeypatch):
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
    monkeypatch.setattr(
        kvk_rankings_views,
        "render_current_rankings_top10_card",
        lambda _payload: pytest.fail("renderer should not run for non-card payload"),
    )

    assert await _top10_card_file(payload) is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mode", "metric", "filename"),
    [
        ("honor", "honor", "kvk_rankings_honor_top10_honor.png"),
        ("prekvk", "overall", "kvk_rankings_prekvk_top10_overall.png"),
    ],
)
async def test_current_rankings_card_file_accepts_honor_and_prekvk_top10(
    monkeypatch,
    mode,
    metric,
    filename,
):
    payload = RankingPayload(
        mode=mode,
        mode_label=mode.title(),
        metric=metric,
        metric_label=metric.title(),
        limit=10,
        rows=[
            RankingRow(
                rank=1,
                governor_id=123,
                governor_name="Alpha",
                value=1000,
                supporting_values={},
            )
        ],
    )
    rendered = SimpleNamespace(filename=filename, image_bytes=BytesIO(b"fake-png"))

    monkeypatch.setattr(
        kvk_rankings_views,
        "render_current_rankings_top10_card",
        lambda card_payload: rendered if card_payload is payload else None,
    )

    file = await _top10_card_file(payload)

    assert file is not None
    assert file.filename == filename
    assert rendered.image_bytes.tell() == 0


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


@pytest.mark.asyncio
async def test_current_rankings_browser_my_rank_sends_private_embed(monkeypatch):
    monkeypatch.setattr(kvk_rankings_views, "KVK_PLAYER_STATS_CHANNEL_ID", 100)
    view = CurrentRankingsBrowserView(mode="kvk", metric="kills", limit=10)
    sent = []
    result = MyRankLookupResult(
        status="found",
        mode="kvk",
        metric="kills",
        metric_label="Kills",
        mode_label="KVK",
        message="found",
        row=RankingRow(rank=12, governor_id=123, governor_name="Ranked", value=1000),
    )
    embed = object()

    async def fake_lookup(**kwargs):
        assert kwargs == {
            "discord_user_id": 200,
            "mode": "kvk",
            "metric": "kills",
            "limit": 10,
        }
        return result

    class Followup:
        async def send(self, content=None, **kwargs):
            sent.append((content, kwargs))

    monkeypatch.setattr(
        kvk_rankings_views.kvk_rankings_service,
        "build_my_rank_lookup_result",
        fake_lookup,
    )
    monkeypatch.setattr(kvk_rankings_views, "build_my_rank_embed", lambda lookup: embed)

    interaction = _channel_interaction(channel_id=100, user_id=200, followup=Followup())

    await view.on_my_rank(interaction)

    assert interaction.response.defer_kwargs == {"ephemeral": True}
    assert sent == [(None, {"embed": embed, "ephemeral": True})]


@pytest.mark.asyncio
async def test_current_rankings_browser_my_rank_sends_private_account_selector(monkeypatch):
    monkeypatch.setattr(kvk_rankings_views, "KVK_PLAYER_STATS_CHANNEL_ID", 100)
    view = CurrentRankingsBrowserView(mode="prekvk", metric="stage1", limit=25)
    sent = []
    result = MyRankLookupResult(
        status="multi_account",
        mode="prekvk",
        metric="stage1",
        metric_label="Stage 1",
        mode_label="PreKvK",
        message="Choose an account.",
        account_choices=(
            RankingAccountChoice("Main", 123, "123", "Main"),
            RankingAccountChoice("Alt", 456, "456", "Alt"),
        ),
    )

    async def fake_lookup(**kwargs):
        assert kwargs == {
            "discord_user_id": 200,
            "mode": "prekvk",
            "metric": "stage1",
            "limit": 25,
        }
        return result

    class Followup:
        async def send(self, content=None, **kwargs):
            sent.append((content, kwargs))

    monkeypatch.setattr(
        kvk_rankings_views.kvk_rankings_service,
        "build_my_rank_lookup_result",
        fake_lookup,
    )

    interaction = _channel_interaction(channel_id=100, user_id=200, followup=Followup())

    await view.on_my_rank(interaction)

    assert sent[0][0] == "Choose an account."
    assert sent[0][1]["ephemeral"] is True
    selector_view = sent[0][1]["view"]
    assert isinstance(selector_view, kvk_rankings_views.CurrentRankingsMyRankAccountView)
    select = selector_view.children[0]
    assert [option.value for option in select.options] == ["123", "456"]


@pytest.mark.asyncio
async def test_current_rankings_my_rank_account_selector_includes_all_registered_accounts():
    choices = tuple(
        RankingAccountChoice(
            slot=f"Slot {index}",
            governor_id=1000 + index,
            governor_id_str=str(1000 + index),
            governor_name=f"Governor {index}",
        )
        for index in range(26)
    )

    view = kvk_rankings_views.CurrentRankingsMyRankAccountView(
        requester_id=200,
        mode="kvk",
        metric="kills",
        limit=10,
        choices=choices,
    )

    selects = list(view.children)

    assert len(selects) == 2
    assert len(selects[0].options) == 25
    assert len(selects[1].options) == 1
    assert [option.value for select in selects for option in select.options] == [
        str(1000 + index) for index in range(26)
    ]


@pytest.mark.asyncio
async def test_current_rankings_my_rank_account_selector_is_bound_to_requester(monkeypatch):
    view = kvk_rankings_views.CurrentRankingsMyRankAccountView(
        requester_id=200,
        mode="kvk",
        metric="kills",
        limit=10,
        choices=(RankingAccountChoice("Main", 123, "123", "Main"),),
    )

    async def fake_lookup(**_kwargs):
        raise AssertionError("non-requester should not trigger lookup")

    monkeypatch.setattr(
        kvk_rankings_views.kvk_rankings_service,
        "build_my_rank_lookup_result",
        fake_lookup,
    )

    interaction = _channel_interaction(channel_id=100, user_id=999)

    await view.on_account_selected(interaction, "123")

    assert interaction.response.sent
    assert "Only the requester" in interaction.response.sent[0][0]
    assert interaction.response.sent[0][1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_current_rankings_my_rank_account_selector_sends_private_result(monkeypatch):
    sent = []
    result = MyRankLookupResult(
        status="found",
        mode="kvk",
        metric="kills",
        metric_label="Kills",
        mode_label="KVK",
        message="found",
        row=RankingRow(rank=12, governor_id=123, governor_name="Ranked", value=1000),
    )
    embed = object()
    view = kvk_rankings_views.CurrentRankingsMyRankAccountView(
        requester_id=200,
        mode="kvk",
        metric="kills",
        limit=10,
        choices=(RankingAccountChoice("Main", 123, "123", "Main"),),
    )

    async def fake_lookup(**kwargs):
        assert kwargs == {
            "discord_user_id": 200,
            "mode": "kvk",
            "metric": "kills",
            "limit": 10,
            "governor_id": "123",
        }
        return result

    class Followup:
        async def send(self, content=None, **kwargs):
            sent.append((content, kwargs))

    monkeypatch.setattr(
        kvk_rankings_views.kvk_rankings_service,
        "build_my_rank_lookup_result",
        fake_lookup,
    )
    monkeypatch.setattr(kvk_rankings_views, "build_my_rank_embed", lambda lookup: embed)

    interaction = _channel_interaction(channel_id=100, user_id=200, followup=Followup())

    await view.on_account_selected(interaction, "123")

    assert interaction.response.defer_kwargs == {"ephemeral": True}
    assert sent == [(None, {"embed": embed, "ephemeral": True})]


@pytest.mark.asyncio
async def test_current_rankings_browser_blocks_honor_my_rank_outside_stats_channel_for_admin(
    monkeypatch,
):
    monkeypatch.setattr(kvk_rankings_views, "KVK_PLAYER_STATS_CHANNEL_ID", 100)
    monkeypatch.setattr(kvk_rankings_views, "_is_admin", lambda _user: True)
    fetched = False

    async def fake_lookup(**_kwargs):
        nonlocal fetched
        fetched = True
        raise AssertionError("honor my rank should not be fetched outside stats channel")

    view = CurrentRankingsBrowserView(mode="honor", metric="honor", limit=10)
    monkeypatch.setattr(
        kvk_rankings_views.kvk_rankings_service,
        "build_my_rank_lookup_result",
        fake_lookup,
    )

    interaction = _channel_interaction(channel_id=999, user_id=1)

    await view.on_my_rank(interaction)

    assert fetched is False
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


def test_my_rank_embed_includes_private_rank_context():
    result = MyRankLookupResult(
        status="found",
        mode="kvk",
        metric="kills",
        metric_label="Kills",
        mode_label="KVK",
        message="found",
        row=RankingRow(rank=12, governor_id=123, governor_name="Ranked", value=1000),
        row_above=RankingRow(rank=11, governor_id=111, governor_name="Ahead", value=1200),
        row_below=RankingRow(rank=13, governor_id=222, governor_name="Behind", value=900),
        total_rows=50,
        gap_to_next_value=200,
    )

    embed = build_my_rank_embed(result)

    assert "My Rank - KVK Kills" == embed.title
    assert "**#12 of 50**" in embed.description
    assert "Private result" in embed.footer.text
    assert embed.fields[1].name == "Gap to next"


def test_my_rank_embed_normalizes_governor_names():
    result = MyRankLookupResult(
        status="found",
        mode="kvk",
        metric="kills",
        metric_label="Kills",
        mode_label="KVK",
        message="found",
        row=RankingRow(rank=12, governor_id=123, governor_name="Bad\n`Name`", value=1000),
        row_above=RankingRow(rank=11, governor_id=111, governor_name="Ahead\n`Name`", value=1200),
        row_below=RankingRow(rank=13, governor_id=222, governor_name="Behind\n`Name`", value=900),
        total_rows=50,
    )

    embed = build_my_rank_embed(result)

    assert "Bad 'Name'" in embed.description
    assert "`Name`" not in embed.description
    assert "Ahead 'Name'" in embed.fields[1].value
    assert "Behind 'Name'" in embed.fields[2].value
