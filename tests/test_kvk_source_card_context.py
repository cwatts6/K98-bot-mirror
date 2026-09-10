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
    monkeypatch.setattr(
        kvk_stats_card_dal,
        "fetch_kvk_stats_card_context",
        Mock(side_effect=AssertionError("legacy source")),
    )
    context = await kvk_stats_card_service.load_kvk_stats_card_context(
        16, "1001", source_period_id=PERIOD, connect=Mock()
    )
    assert context.source_context["publication_id"] == report["publication_id"]
    assert context.overall_kvk_rank is None


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
