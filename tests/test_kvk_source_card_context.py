from dataclasses import replace
from unittest.mock import Mock

import pytest

from kvk.dal import kvk_stats_card_dal
from kvk.dal.new_source_import_dal import SourceConflict
from kvk.models.kvk_stats_card import KvkStatsCardContext
from kvk.services import kvk_stats_card_service
from kvk.services.new_source_reporting_service import card_context
from tests.test_kvk_public_routing import RoutingStore
from tests.test_kvk_source_pairs import uid
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


class CardStore(RoutingStore):
    def __init__(self):
        super().__init__(overall=True)
        self.has_overall = True
        self.routing["DisplayPeriodID"] = uid(99)  # A fight, never the card's overall.

    def route(self, sql, args, connection):
        if "SELECT KVK_NAME" in sql:
            self.events.append((connection, sql, args))
            return [{"KVK_NAME": "Tides of War"}]
        if "SELECT PeriodID FROM KVK.SourcePeriod" in sql:
            self.events.append((connection, sql, args))
            assert "PeriodKind='overall'" in sql
            return [{"PeriodID": uid(2)}] if self.has_overall else []
        if "KVK.KVK_Player_Windowed" in sql or "vw_Player_Overall" in sql:
            raise AssertionError("No legacy camp or rank fallback")
        if "FROM KVK.SourcePlayerResult" in sql:
            assert set(range(1, connection)).issubset(
                self.closed
            ), "Authority transaction retained during rows"
        return super().route(sql, args, connection)

    def install(self, monkeypatch):
        super().install(monkeypatch)
        import file_utils

        monkeypatch.setattr(file_utils, "get_conn_with_retries", self.connect)
        monkeypatch.setattr(kvk_stats_card_dal, "get_conn_with_retries", self.connect)


@pytest.fixture
def card_store(monkeypatch):
    store = CardStore()
    store.install(monkeypatch)
    return store


@pytest.mark.asyncio
async def test_ordinary_card_uses_complete_overall_b0_without_injection(card_store):
    payload = await kvk_stats_card_service.build_kvk_stats_card_payload(
        {"GovernorID": "1001", "KVK_NO": 16, "T4&T5_Kills": 123, "Kill Target": 200}
    )
    assert payload.source_context["available"]
    assert payload.source_read["period_id"] == uid(2)
    assert payload.source_read["update_id"] == uid(1)
    assert payload.camp_name and payload.kingdom
    assert payload.kills_gain == 123 and payload.kill_target == 200
    assert payload.overall_kvk_rank is None
    await kvk_stats_card_service.require_card_current(payload)
    assert not any("KVK_Player_Windowed" in sql for _, sql, _ in card_store.events)
    # One immutable row load; revalidation only reads authority and metadata.
    assert sum("SourcePlayerResult" in sql for _, sql, _ in card_store.events) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case,reason",
    [
        ("missing", "overall_missing"),
        ("disabled", "serving_disabled"),
        ("capability", "capability_unsupported"),
        ("pair", "waiting_pair"),
        ("choice", "season_choice_missing"),
        ("stale", "configuration_pending"),
    ],
)
async def test_ordinary_context_unavailable_preserves_numbers(card_store, case, reason):
    if case == "missing":
        card_store.has_overall = False
    if case == "disabled":
        card_store.routing["Enabled"] = False
    if case == "capability":
        card_store.routing["CapabilitiesVersion"] = "unsupported"
    if case == "pair":
        card_store.selection = None
    if case == "choice":
        card_store.choice = None
    if case == "stale":
        card_store.requested = dict(DesiredConfigVersionID=uid(40), ConfigVersion=2)
    payload = await kvk_stats_card_service.build_kvk_stats_card_payload(
        {"GovernorID": "1001", "KVK_NO": 16, "DKP_SCORE": 99, "DKP_Target": 500}
    )
    assert payload.source_context["reason"] == reason
    assert not payload.source_context["available"] and payload.camp_name is None
    assert payload.dkp == 99 and payload.dkp_target == 500
    assert not any("SourcePlayerResult" in sql for _, sql, _ in card_store.events)


@pytest.mark.asyncio
async def test_card_revalidation_rejects_new_selection_without_retarget(card_store):
    payload = await kvk_stats_card_service.build_kvk_stats_card_payload(
        {"GovernorID": "1001", "KVK_NO": 16}
    )
    card_store.selection["PublicSelectionVersion"] += 1
    with pytest.raises(SourceConflict, match="changed"):
        await kvk_stats_card_service.require_card_current(payload)
    assert payload.source_read["public_selection_version"] == 7


@pytest.mark.asyncio
async def test_card_missing_member_does_not_use_legacy_camp(card_store):
    context = await kvk_stats_card_service.load_kvk_stats_card_context(16, "999999")
    assert context.camp_name is None
    assert context.source_context["reason"] == "outside_frozen_cohort"


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["RoutingVersion", "Enabled", "CapabilitiesVersion"])
async def test_card_saved_identity_rejects_routing_change(card_store, field):
    payload = await kvk_stats_card_service.build_kvk_stats_card_payload(
        {"GovernorID": "1001", "KVK_NO": 16}
    )
    card_store.routing[field] = {
        "RoutingVersion": 99,
        "Enabled": False,
        "CapabilitiesVersion": "unsupported",
    }[field]
    with pytest.raises(SourceConflict):
        await kvk_stats_card_service.require_card_current(payload)


@pytest.mark.asyncio
async def test_ordinary_legacy_card_keeps_legacy_context(monkeypatch, card_store):
    card_store.choice["SourceKey"] = "legacy_full_data"
    fetch = Mock(return_value={"camp_name": "Legacy camp", "overall_kvk_rank": 3})
    monkeypatch.setattr(kvk_stats_card_dal, "fetch_kvk_stats_card_context", fetch)
    payload = await kvk_stats_card_service.build_kvk_stats_card_payload(
        {"GovernorID": "1001", "KVK_NO": 16}
    )
    assert payload.camp_name == "Legacy camp" and payload.overall_kvk_rank == 3
    assert payload.source_context is None and payload.source_read["availability"] == "legacy"
    await kvk_stats_card_service.require_card_current(payload)
    fetch.assert_called_once()
    assert not any("SourcePlayerResult" in sql for _, sql, _ in card_store.events)


@pytest.mark.asyncio
async def test_context_cannot_be_reused_for_another_season(card_store):
    payload = await kvk_stats_card_service.build_kvk_stats_card_payload(
        {"GovernorID": "1001", "KVK_NO": 16}
    )
    with pytest.raises(SourceConflict, match="season differs"):
        await kvk_stats_card_service.require_card_current(replace(payload, kvk_no=17))
