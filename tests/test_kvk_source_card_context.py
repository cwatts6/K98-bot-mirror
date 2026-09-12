from dataclasses import replace
from unittest.mock import Mock

import pytest

from kvk.dal import kvk_stats_card_dal
from kvk.models.kvk_stats_card import KvkStatsCardContext
from kvk.services import kvk_stats_card_service
from kvk.services.new_source_reporting_service import card_context
from tests.test_kvk_source_reporting import PERIOD, load_synthetic


def test_card_context_requires_independent_overall_and_current_config(monkeypatch):
    report, _, _, _ = load_synthetic(monkeypatch)
    with pytest.raises(ValueError, match="overall"):
        card_context(report, 1001)
    report, _, _, _ = load_synthetic(monkeypatch, overall=True)
    context = card_context(report, 1001)["source_context"]
    assert context["available"] and context["period"] == "overall"
    assert context["rank"] == 1 and "B0" in context["basis"]
    assert context["as_of_utc"] == report["player_end_utc"]
    report["is_current"] = False
    assert not card_context(report, 1001)["source_context"]["available"]


@pytest.mark.asyncio
async def test_source_card_loader_bypasses_legacy_rank_queries(monkeypatch):
    report, _, envelope, _ = load_synthetic(monkeypatch, overall=True)
    monkeypatch.setattr(kvk_stats_card_dal, "fetch_source_card_report", lambda **kw: envelope)
    display = Mock(
        return_value=dict(kvk_name="Tides of War", kingdom=98, camp_id=1, camp_name="Wind")
    )
    monkeypatch.setattr(
        kvk_stats_card_dal,
        "fetch_kvk_stats_card_context",
        display,
    )
    context = await kvk_stats_card_service.load_kvk_stats_card_context(
        16, "1001", source_period_id=PERIOD, connect=Mock()
    )
    assert context.source_context["publication_id"] == report["publication_id"]
    assert context.overall_kvk_rank is None
    assert context.kvk_name == "Tides of War" and context.camp_name == "Wind"
    assert display.call_args.kwargs["include_overall_rank"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("received", [True, False])
async def test_source_card_preserves_display_and_renders_without_legacy_rank(monkeypatch, received):
    from unittest.mock import MagicMock

    from kvk.rendering.kvk_stats_card_renderer import (
        render_kvk_more_stats_card,
        render_kvk_stats_card,
    )

    report, _, envelope, _ = load_synthetic(monkeypatch, overall=True, received=received)
    monkeypatch.setattr(kvk_stats_card_dal, "fetch_source_card_report", lambda **kw: envelope)
    cursor = MagicMock()
    display_rows = iter(
        [{"KVK_NAME": "Tides of War"}, {"kingdom": 98, "campid": 1, "camp_name": "Wind"}]
    )

    def execute(query, params):
        assert "vw_Player_Overall_KVK_Rank" not in query
        assert "?" in query
        row = next(display_rows)
        cursor.description = [(key,) for key in row]
        cursor.fetchone.return_value = tuple(row.values())

    cursor.execute.side_effect = execute
    conn = MagicMock()
    conn.cursor.return_value = cursor
    context = await kvk_stats_card_service.load_kvk_stats_card_context(
        16, "1001", source_period_id=PERIOD, connect=lambda: conn
    )
    assert context.source_context["available"] == received
    assert (context.kvk_name, context.kingdom, context.camp_id, context.camp_name) == (
        "Tides of War",
        98,
        1,
        "Wind",
    )
    conn.close.assert_called_once()
    payload = await kvk_stats_card_service.build_kvk_stats_card_payload(
        {"GovernorID": "1001", "KVK_NO": 16, "T4&T5_Kills": 123, "Kill Target": 200},
        context=context,
    )
    assert payload.kills_gain == 123 and payload.kill_target == 200
    assert payload.overall_kvk_rank is None
    assert render_kvk_stats_card(payload) is not None
    assert render_kvk_more_stats_card(payload) is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("kvk_no", [None, True, 0, -1, "16", 2147483648])
async def test_source_card_rejects_invalid_season_before_io(kvk_no):
    connect = Mock(side_effect=AssertionError("No SQL"))
    with pytest.raises(ValueError, match="positive SQL KVK"):
        await kvk_stats_card_service.load_kvk_stats_card_context(
            kvk_no, "1001", source_period_id=PERIOD, connect=connect
        )
    connect.assert_not_called()


@pytest.mark.asyncio
async def test_t60_ks4_values_targets_and_rank_stay_independent(monkeypatch):
    report, _, _, _ = load_synthetic(monkeypatch, overall=True)
    row = {
        "GovernorID": "1001",
        "KVK_NO": 16,
        "T4&T5_Kills": 123,
        "Kill Target": 200,
        "DKP_SCORE": 17,
        "DKP_Target": 40,
        "KVK_RANK": 99,
    }
    old = await kvk_stats_card_service.build_kvk_stats_card_payload(
        row, context=KvkStatsCardContext()
    )
    new = await kvk_stats_card_service.build_kvk_stats_card_payload(
        row, context=KvkStatsCardContext(**card_context(report, 1001))
    )
    assert replace(new, source_context=None, generated_at_utc=old.generated_at_utc) == old
    assert new.kills_gain == 123 and new.kill_target == 200 and new.kvk_rank == 99
    assert new.overall_kvk_rank is None  # Safe for existing fallback renderers too.
