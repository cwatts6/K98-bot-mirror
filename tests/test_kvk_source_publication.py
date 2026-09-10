from dataclasses import replace
from decimal import Decimal

import pytest

from kvk.dal.new_source_publication_dal import result_digest, result_values
from kvk.models.new_source_reporting import CalculatedMetric
from kvk.schemas.new_source_schema import MetricState
from kvk.services.new_source_calculation import calculate_period
from kvk.services.new_source_window_resolver import resolve_window
from tests.kvk_source_fixtures import calculation_config, worked_calculation_inputs


def test_storage_preserves_zero_missing_and_exact_decimal():
    b0, start, _, end = worked_calculation_inputs()
    result = calculate_period(resolve_window(calculation_config(), (start, end)), b0)
    row = result_values(result.players[0])
    assert row["dkp"] == Decimal(1800)
    assert row["power"] == -2000000
    assert result_digest([row]) == result_digest([{**row, "dkp": Decimal("1800.000000")}])


def test_lossy_result_rejected_before_sql():
    b0, start, _, end = worked_calculation_inputs()
    player = calculate_period(resolve_window(calculation_config(), (start, end)), b0).players[0]
    metrics = dict(player.metrics)
    metrics["dkp"] = CalculatedMetric(Decimal("1.0000001"), MetricState.AVAILABLE)
    with pytest.raises(ValueError, match="precision"):
        result_values(replace(player, metrics=tuple(metrics.items())))


def test_equal_fight_endpoints_score_zero_for_all_b0_members():
    b0, start, _, _ = worked_calculation_inputs()
    config = calculation_config(end_scan_id=10)
    result = calculate_period(resolve_window(config, (start,)), b0)
    assert len(result.players) == 4
    assert result.selection.player_state.value == "not_applicable"
    for player in result.players:
        for key in ("dkp", "kp_t4_t5", "t4_kills", "dead", "healed_points", "dkp_power_ratio"):
            assert player.metric(key).value == 0
            assert player.metric(key).state == MetricState.AVAILABLE
        assert not player.ranks
    assert (
        result.missing_start_count == 1
    )  # Raw coverage remains truthful despite no-fight scoring.
