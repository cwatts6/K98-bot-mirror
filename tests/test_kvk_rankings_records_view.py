import pytest

from kvk.models.kvk_rankings import HallOfFameMetric, RankingPayload, RankingRow
from kvk.rendering.kvk_rankings_embed import build_hall_of_fame_embed
from ui.views import kvk_rankings_views
from ui.views.kvk_rankings_views import HallOfFameRecordsView


def test_build_hall_of_fame_embed_mentions_record_rules():
    payload = RankingPayload(
        mode="records",
        metric="kills",
        metric_label="Kills",
        limit=10,
        rows=[
            RankingRow(
                rank=1,
                governor_id=123,
                governor_name="Alice",
                value=1_500_000,
                kvk_no=17,
                kvk_name="Light vs Dark",
            )
        ],
    )

    embed = build_hall_of_fame_embed(payload)

    assert "KD98 Hall of Fame" in embed.title
    assert "Alice" in (embed.description or "")
    assert "KVK 17 - Light vs Dark" in (embed.description or "")
    assert "Single-KVK performances only" in embed.footer.text


@pytest.mark.asyncio
async def test_hall_of_fame_records_view_exposes_metric_selector_only():
    view = HallOfFameRecordsView(metric=HallOfFameMetric.KILLS, limit=50)

    labels = [getattr(item, "label", None) for item in view.children]
    custom_ids = [getattr(item, "custom_id", None) for item in view.children]

    assert "Top 10" not in labels
    assert "Top 25" not in labels
    assert "Top 50" not in labels
    assert "Top 100" not in labels
    assert "kvk_records_top_10" not in custom_ids
    assert view.limit == 10
    assert len(view.metric_select.options) == 8


@pytest.mark.asyncio
async def test_hall_of_fame_records_view_refresh_edits_component_message(monkeypatch):
    payload = RankingPayload(
        mode="records",
        metric="honor",
        metric_label="Honor",
        limit=25,
        rows=[RankingRow(rank=1, governor_id=456, governor_name="Bob", value=5000)],
    )
    view = HallOfFameRecordsView(metric=HallOfFameMetric.HONOR, limit=25)

    async def fake_payload(**kwargs):
        assert kwargs == {"metric": HallOfFameMetric.HONOR, "limit": 10}
        return payload

    class Response:
        async def defer(self):
            return None

    class Message:
        def __init__(self):
            self.kwargs = None

        async def edit(self, **kwargs):
            self.kwargs = kwargs

    message = Message()

    async def wrong_target(**_kwargs):
        raise AssertionError("component message should be edited first")

    interaction = type(
        "Interaction",
        (),
        {
            "response": Response(),
            "message": message,
            "edit_original_response": wrong_target,
        },
    )()
    monkeypatch.setattr(kvk_rankings_views.kvk_rankings_service, "build_hall_of_fame_payload", fake_payload)

    await view._refresh(interaction)

    assert view.message is message
    assert message.kwargs["view"] is view
    assert "KD98 Hall of Fame" in message.kwargs["embed"].title
