"""S3A T21-T30/T34/T36 plus precision and source isolation regressions."""

from dataclasses import replace
from decimal import Decimal, localcontext

import pytest

from kvk.models.new_source_reporting import PeriodKind
from kvk.schemas.new_source_schema import BIGINT_MAX, MetricState
from kvk.services.new_source_calculation import calculate_period
from kvk.services.new_source_window_resolver import resolve_window
from tests.kvk_source_fixtures import (
    calculation_config,
    calculation_event,
    player_row,
    worked_calculation_inputs,
)


def test_t21_t26_exact_endpoints_roster_and_metric_cohorts():
    b0, start, middle, end = worked_calculation_inputs()
    config = calculation_config()
    final = calculate_period(resolve_window(config, (start, end)), b0)
    assert final == calculate_period(resolve_window(config, (start, middle, end)), b0)
    players = {p.governor_id: p for p in final.players}
    a = players[1001]
    for key, expected in {
        "t4_kills": 40,
        "t5_kills": 50,
        "dead": 10,
        "dkp": 1800,
        "kp_t4_t5": 1400,
        "total_kill_points": 1500,
        "power": -2000000,
        "kills_gain": 90,
        "starting_power": 100000000,
    }.items():
        assert a.metric(key).value == expected
    assert a.metric("dkp_power_ratio").value == Decimal("0.000018")
    assert players[1002].metric("dkp").value == 0
    assert players[1003].metric("dkp").state == MetricState.MISSING_START
    assert players[1004].metric("dkp").value == 0
    assert 9999 not in players
    assert dict(players[1002].ranks)["kp_t4_t5"].rank == 2
    assert dict(players[1004].ranks)["kp_t4_t5"].rank == 3
    assert dict(a.ranks)["kp_t4_t5"].population == 3
    assert final.eligible_count == 4 and final.paired_count == 3 and final.excluded_count == 1
    interim = calculate_period(resolve_window(config, (start, middle)), b0).players[0]
    assert interim.metric("dkp").value == 1000
    assert interim.metric("total_kill_points").value == 850


@pytest.mark.parametrize(
    "start_rows,end_rows,expected",
    [
        ([], [player_row()], MetricState.MISSING_START),
        ([player_row()], [], MetricState.MISSING_END),
        ([], [], MetricState.MISSING_START),
        ([player_row(**{"T4 Kills": None})], [player_row()], MetricState.MISSING_START),
        ([player_row()], [player_row(**{"T4 Kills": None})], MetricState.MISSING_END),
        ([player_row()], [player_row(**{"T4 Kills": "=1+2"})], MetricState.INVALID_SOURCE_VALUE),
        ([player_row(**{"T4 Kills": 5})], [player_row()], MetricState.COUNTER_REGRESSION),
    ],
)
def test_t22_t23_t27_missing_invalid_regression_propagates(start_rows, end_rows, expected):
    # Keep another synthetic row so parser accepts the observation even if 1001 is absent.
    start = calculation_event(10, rows=[*start_rows, player_row(2000)])
    end = calculation_event(13, day=7, rows=[*end_rows, player_row(2000)])
    b0 = calculation_event(1, day=1, rows=[player_row()])
    result = calculate_period(resolve_window(calculation_config(), (start, end)), b0).players[0]
    assert result.metric("t4_kills").state == expected
    assert result.metric("dkp").state == expected
    assert result.metric("kp_t4_t5").state == expected
    if start_rows and end_rows:
        assert result.metric("t5_kills").value == 0
        assert result.metric("power").value == 0


@pytest.mark.parametrize("power", [0, None])
def test_t28_dkp_has_no_power_gate(power):
    _, start, _, end = worked_calculation_inputs()
    b0 = calculation_event(1, day=1, rows=[player_row(Power=power)])
    result = calculate_period(resolve_window(calculation_config(), (start, end)), b0).players[0]
    assert result.metric("dkp").value == 1800
    assert result.metric("dkp_power_ratio").value is None
    without_weights = calculate_period(
        resolve_window(calculation_config(weights=None), (start, end)), b0
    ).players[0]
    assert without_weights.metric("dkp").state == MetricState.MISSING_CONFIGURATION
    assert without_weights.metric("kp_t4_t5").value == 1400


def test_t30_b0_attribution_and_name_fallback():
    b0 = calculation_event(1, day=1, rows=[player_row(Name="Baseline")])
    start = calculation_event(10, rows=[player_row(Name="Start", Power=50)])
    end = calculation_event(13, day=7, rows=[player_row(kingdom=102, Name="End")])
    selected = resolve_window(calculation_config(), (start, end))
    result = calculate_period(selected, b0).players[0]
    assert (result.name, result.b0_kingdom, result.camp_id) == ("End", 101, 1)
    assert result.observed_kingdom_changed
    assert result.metric("starting_power").value == 1
    assert result.metric("fight_start_power").value == 50
    for end_name, start_name, expected in [(None, "Start", "Start"), (None, None, "Baseline")]:
        start2 = calculation_event(10, rows=[player_row(Name=start_name)])
        end2 = calculation_event(13, day=7, rows=[player_row(Name=end_name)])
        assert (
            calculate_period(resolve_window(calculation_config(), (start2, end2)), b0)
            .players[0]
            .name
            == expected
        )


def test_t34_no_fight_zero_has_no_ranks():
    b0 = calculation_event(1, day=1, periods=("no_fight:baseline",))
    config = calculation_config(
        period_id="baseline",
        period_key="no_fight:baseline",
        period_kind=PeriodKind.NO_FIGHT,
        start_scan_id=1,
        end_scan_id=1,
    )
    result = calculate_period(resolve_window(config, (b0,)), b0)
    assert all(p.metric("dkp").value == 0 and not p.ranks for p in result.players)


def test_t36_overall_is_b0_to_selected_end_never_fight_sum():
    b0, start, _, end = worked_calculation_inputs()
    config = calculation_config(
        period_id="overall",
        period_key="overall",
        period_kind=PeriodKind.OVERALL,
        start_scan_id=1,
        end_scan_id=None,
    )
    result = calculate_period(resolve_window(config, (b0, start, end)), b0)
    assert result.players[0].metric("dkp").value == 8730
    wrong = resolve_window(replace(config, start_scan_id=10), (start, end))
    with pytest.raises(ValueError, match="exact B0"):
        calculate_period(wrong, b0)


@pytest.mark.parametrize("token", ["NaN", "Infinity", "1e26", "0.0000000000001", "bad"])
def test_invalid_or_lossy_weight_rejected(token):
    weights = calculation_config().weights
    with pytest.raises(ValueError):
        replace(weights, x_source=token)


def test_precision_overflow_and_ambient_context():
    b0, start, _, end = worked_calculation_inputs()
    config = calculation_config()
    selection = resolve_window(config, (start, end))
    expected = calculate_period(selection, b0)
    with localcontext() as context:
        context.prec = 3
        assert calculate_period(selection, b0) == expected
    weights = replace(config.weights, x_source="0.000000000001", y_source="0", z_source="0")
    result = calculate_period(resolve_window(replace(config, weights=weights), (start, end)), b0)
    assert result.players[0].metric("dkp").reason == "decimal_precision_or_overflow"
    weights = replace(weights, x_source="99999999999999999999999999")
    big_end = calculation_event(13, day=7, rows=[player_row(**{"T4 Kills": str(BIGINT_MAX)})])
    result = calculate_period(
        resolve_window(replace(config, weights=weights), (start, big_end)), b0
    )
    assert result.players[0].metric("dkp").value is None


def test_unavailable_total_kp_does_not_remove_tier_rank_and_highest_not_substituted():
    b0 = calculation_event(1, day=1)
    start = calculation_event(10)
    end = calculation_event(
        13,
        day=7,
        rows=[
            player_row(
                **{
                    "Total Kill Points": None,
                    "Acclaim": None,
                    "Highest Acclaim": 100,
                }
            )
        ],
    )
    result = calculate_period(resolve_window(calculation_config(), (start, end)), b0).players[0]
    assert "kp_t4_t5" in dict(result.ranks)
    assert "total_kill_points" not in dict(result.ranks)
    assert result.metric("acclaim").value is None
    assert result.metric("highest_acclaim").value == 99
    assert result.metric("t4_t5_dead").state == MetricState.UNSUPPORTED
