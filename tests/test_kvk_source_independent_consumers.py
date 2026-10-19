"""S7-T16: reporting changes never replace independent KS4/target/history owners."""

from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from kvk.dal import source_routing_dal


@pytest.fixture(autouse=True)
def forbid_combat_routing(monkeypatch):
    monkeypatch.setattr(
        source_routing_dal,
        "resolve_season_read",
        Mock(side_effect=AssertionError("Independent consumer entered combat routing")),
    )


@pytest.mark.asyncio
async def test_personal_ks4_row_preserves_independent_numbers(monkeypatch):
    from services.kvk_personal_service import load_kvk_personal_stats
    import utils

    row = dict(GovernorID=100, kills=123, dkp=456, source="KS4")
    fetch = Mock(return_value=row)
    monkeypatch.setattr(utils, "load_stat_row", fetch)
    assert await load_kvk_personal_stats("100") is row
    fetch.assert_called_once_with("100")


def test_daily_scanorder_reads_ks4_not_logical_scans(monkeypatch):
    from kvk.dal import kvk_lifecycle_dal

    connection = MagicMock()
    cursor = connection.__enter__.return_value.cursor.return_value.__enter__.return_value
    cursor.description = [("MaxScanOrder",)]
    cursor.fetchone.return_value = (1122,)
    monkeypatch.setattr(kvk_lifecycle_dal, "get_conn_with_retries", lambda: connection)
    assert kvk_lifecycle_dal.fetch_max_scan_order() == 1122
    query = cursor.execute.call_args.args[0]
    assert "MAX(ScanOrder)" in query and "kingdomscandata4" in query
    assert "SourceLogicalScan" not in query


def test_finalized_history_preserves_nulls_and_final_header_scope(monkeypatch):
    from kvk.dal import kvk_history_dal

    connection = MagicMock()
    cursor = connection.__enter__.return_value.cursor.return_value
    cursor.description = [("Gov_ID",), ("KVK_NO",), ("DKP_SCORE",)]
    cursor.fetchall.return_value = [(100, 15, None)]
    monkeypatch.setattr(kvk_history_dal, "get_conn_with_retries", lambda: connection)
    result = kvk_history_dal.fetch_modern_history_rows_for_governors([100], [15])
    assert result == [dict(Gov_ID=100, KVK_NO=15, DKP_SCORE=None)]
    query, parameters = cursor.execute.call_args.args
    assert "v_EXCEL_FOR_KVK_Started" in query and "OUTPUT_COMPLETE" in query
    assert parameters == [100, 15]


@pytest.mark.parametrize(
    "path,authority",
    [
        ("kvk/target_cache_repository.py", "fetch_current_publication_metadata"),
        ("kvk/services/kvk_rankings_service.py", "load_stat_cache"),
        ("player_self_service/stats_service.py", "personal_stats_dal"),
        ("player_self_service/governor_dashboard_dal.py", "KingdomScanData4"),
        ("leadership_player_review/dal.py", "usp_GetLeadershipPlayerKvkHistory"),
        ("daily_KVK_overview_embed.py", "event_cache"),
    ],
)
def test_independent_owner_dependencies_remain_explicit(path, authority):
    text = (Path(__file__).resolve().parents[1] / path).read_text(encoding="utf-8")
    assert authority.lower() in text.lower()
    assert "source_routing_service" not in text and "source_routing_dal" not in text


def test_consumer_inventory_has_explicit_slice_owners():
    """Coverage inventory includes preserved and later-slice paths, not migration claims."""
    owners = {
        "accepted_intake": {*range(1, 15), 62},
        "s9a_reporting": {*range(15, 29), 39},
        "s9b_cards_admin": {*range(35, 39), 40, 42, 43},
        "s10_exports": {*range(29, 35)},
        "independent": {41, *range(44, 61), 63, 64},
        "preserved_config_recovery": {61, 65},
    }
    assert set.union(*owners.values()) == set(range(1, 66))
    assert sum(map(len, owners.values())) == 65
    indirect = {
        "accepted_intake": {1},
        "s9a": {5, 7},
        "s9b": {6, 11},
        "s10": {2, 3, 4, 12},
        "preserved": {8, 9, 10},
    }
    assert set.union(*indirect.values()) == set(range(1, 13))
