"""T16/T35-T40/T67/T70: authority, independent stream times and truthful finality."""

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json

import pytest

from kvk.models.new_source_reporting import (
    AggregateSelection,
    CalculatedMetric,
    ComparisonBasis,
    PeriodKind,
    ReportSnapshotV2,
    StreamState,
)
from kvk.schemas.new_source_schema import MetricState, ReportState
from kvk.services.new_source_calculation import calculate_period
from kvk.services.new_source_parser import parse_aggregate_workbook
from kvk.services.new_source_window_resolver import resolve_window
from tests.kvk_source_fixtures import (
    MAPPING,
    aggregate_bytes,
    calculation_config,
    metadata,
    worked_calculation_inputs,
)


def snapshot(*, aggregate=True):
    b0, start, _, end = worked_calculation_inputs()
    config = calculation_config()
    calculation = calculate_period(resolve_window(config, (start, end)), b0)
    selection = None
    if aggregate:
        report = parse_aggregate_workbook(aggregate_bytes(), metadata(aggregate=True), MAPPING)
        selection = AggregateSelection("report-pass4", "aggregate-revision-1", report)
    return ReportSnapshotV2(
        "pub-1",
        1,
        1,
        config,
        calculation,
        selection,
        StreamState.FINAL,
        StreamState.LIVE if aggregate else StreamState.NOT_RECEIVED,
        StreamState.LIVE,
    )


def test_t16_t35_t39_aggregate_values_precision_and_independent_timestamps():
    report = snapshot()
    source = report.aggregate.report
    payload = report.to_dict()
    json.dumps(payload, allow_nan=False)
    assert report.aggregate.report is source
    assert source.kingdom_rows[0].cell("DKP").metric.value == Decimal("25300000")
    assert source.camp_rows[0].cell("DKP").metric.value == Decimal("4779000000")
    assert payload["aggregate"]["as_of_utc"] != payload["player_end"]["scan_start_utc"]
    metric = dict(payload["aggregate"]["kingdom_rows"][0]["metrics"])["DKP"]
    assert metric["value"] == str(source.kingdom_rows[0].cell("DKP").metric.value)
    assert metric["raw_token"] == "25.3M"
    assert metric["displayed_unit"] == "100000"
    assert "raw_value" not in json.dumps(payload)
    assert "artifact_sha256" not in json.dumps(payload)
    assert dict(payload["players"][0]["metrics"])["dkp"]["value"] == "1800"


def test_t35_revision_selection_is_pass_through_not_sum():
    old = snapshot()
    for token in ("1.20M", "1.35M", "1.40M"):
        prepared = parse_aggregate_workbook(
            aggregate_bytes(token=token), metadata(aggregate=True), MAPPING
        )
        new = replace(old, aggregate=AggregateSelection("report-pass4", token, prepared))
        assert new.aggregate.report.kingdom_rows[0].cell("DKP").metric.raw_token == token
    assert old.aggregate.revision_id == "aggregate-revision-1"


def test_t40_reason_cannot_finalize_a_live_or_missing_component():
    report = snapshot()
    with pytest.raises(ValueError, match="cannot finalize"):
        replace(report, period_state=StreamState.FINAL, final_unavailable_reason="reason")
    missing = snapshot(aggregate=False)
    with pytest.raises(ValueError, match="cannot finalize"):
        replace(missing, period_state=StreamState.FINAL, final_unavailable_reason="reason")
    terminal = replace(
        missing,
        aggregate_state=StreamState.FINAL_UNAVAILABLE,
        period_state=StreamState.FINAL,
        final_unavailable_reason="reviewed unavailable",
    )
    assert terminal.current_period_state == StreamState.FINAL
    with pytest.raises(ValueError, match="explicit reason"):
        replace(terminal, final_unavailable_reason=" ")


def test_t70_stale_final_is_not_current_against_desired_endpoint():
    report = snapshot(aggregate=False)
    terminal = replace(
        report,
        aggregate_state=StreamState.FINAL_UNAVAILABLE,
        period_state=StreamState.FINAL,
        final_unavailable_reason="reviewed unavailable",
    )
    desired = replace(report.requested_config, version_id="config-2", end_scan_id=14)
    pending = replace(terminal, requested_config=desired)
    assert not pending.is_current
    assert pending.current_period_state == StreamState.MISSING_CONFIGURATION
    payload = pending.to_dict()
    assert payload["requested_end_scan_id"] == 14
    assert payload["selected_config_end_scan_id"] == 13
    assert payload["endpoint_pending"]
    assert terminal.is_current


def test_t37_t38_unverified_or_wrong_period_cannot_supply_aggregate():
    report = snapshot()
    prepared = report.aggregate.report
    for period in (None, "fight:other", "overall"):
        altered = replace(
            prepared,
            metadata=replace(
                prepared.metadata, candidate=replace(prepared.metadata.candidate, period_key=period)
            ),
        )
        with pytest.raises(ValueError, match="another source/season/period"):
            replace(report, aggregate=replace(report.aggregate, report=altered))


def test_t36_t37_overall_requires_own_final_report():
    original = snapshot()
    b0, _, _, end = worked_calculation_inputs()
    config = calculation_config(
        period_id="overall",
        period_key="overall",
        period_kind=PeriodKind.OVERALL,
        start_scan_id=1,
        end_scan_id=13,
    )
    calculation = calculate_period(resolve_window(config, (b0, end)), b0)
    missing = ReportSnapshotV2(
        "overall-pub",
        1,
        1,
        config,
        calculation,
        None,
        StreamState.FINAL,
        StreamState.NOT_RECEIVED,
        StreamState.LIVE,
    )
    assert missing.aggregate is None
    prepared = original.aggregate.report
    prepared = replace(
        prepared,
        metadata=replace(
            prepared.metadata,
            candidate=replace(
                prepared.metadata.candidate, period_key="overall", report_state=ReportState.FINAL
            ),
        ),
    )
    final = replace(
        missing,
        aggregate=AggregateSelection("overall-report", "overall-revision", prepared),
        aggregate_state=StreamState.FINAL,
        period_state=StreamState.FINAL,
    )
    assert final.aggregate.report is prepared
    assert final.aggregate.report.kingdom_rows[0].cell("DKP").metric.value == 25300000
    with pytest.raises(ValueError):
        replace(final, aggregate=original.aggregate, aggregate_state=StreamState.LIVE)


def test_t67_cross_season_comparison_requires_same_metric_cohort_weight_precision_basis():
    basis = ComparisonBasis(
        "snapshot_report_v1",
        "total_deaths_player_dkp",
        PeriodKind.FIGHT,
        "usable_b0",
        ("10", "20", "40"),
        "exact_decimal",
    )
    assert basis.comparable_to(replace(basis))
    for change in (
        {"source_key": "legacy_full_data"},
        {"metric_definition": "tier_kp"},
        {"cohort_basis": "kingdom_only"},
        {"weight_basis": ("1", "2", "3")},
        {"precision_basis": "reported_abbreviated"},
        {"period_kind": PeriodKind.OVERALL},
    ):
        assert not basis.comparable_to(replace(basis, **change))


def test_immutable_and_invalid_metric_contracts():
    metric = CalculatedMetric(Decimal(0), MetricState.AVAILABLE)
    with pytest.raises(FrozenInstanceError):
        metric.value = Decimal(1)
    for value, state in (
        (None, MetricState.AVAILABLE),
        (Decimal(0), MetricState.MISSING_END),
        (1.0, MetricState.AVAILABLE),
        (Decimal("NaN"), MetricState.AVAILABLE),
    ):
        with pytest.raises(ValueError):
            CalculatedMetric(value, state)


def test_forged_endpoint_or_same_version_config_is_rejected():
    report = snapshot()
    selected = report.calculation.selection
    with pytest.raises(ValueError, match="exact configured slot"):
        replace(selected, start=selected.end)
    with pytest.raises(ValueError, match="exact configured end"):
        replace(selected, config=replace(selected.config, end_scan_id=14))
    with pytest.raises(ValueError, match="different contents"):
        replace(report, requested_config=replace(report.requested_config, end_scan_id=14))


@pytest.mark.parametrize("kind", [PeriodKind.FIGHT, PeriodKind.OVERALL])
def test_combat_period_cannot_finalize_with_not_applicable_aggregate(kind):
    original = snapshot(aggregate=False)
    if kind == PeriodKind.OVERALL:
        b0, _, _, end = worked_calculation_inputs()
        config = calculation_config(
            period_id="overall", period_key="overall", period_kind=kind, start_scan_id=1
        )
        calculation = calculate_period(resolve_window(config, (b0, end)), b0)
        original = replace(original, requested_config=config, calculation=calculation)
    with pytest.raises(ValueError, match="only valid for no-fight"):
        replace(
            original, aggregate_state=StreamState.NOT_APPLICABLE, period_state=StreamState.FINAL
        )


def test_no_fight_retains_not_applicable_aggregate():
    from tests.kvk_source_fixtures import calculation_event

    b0 = calculation_event(1, day=1, periods=("no_fight:baseline",))
    config = calculation_config(
        period_id="baseline",
        period_key="no_fight:baseline",
        period_kind=PeriodKind.NO_FIGHT,
        start_scan_id=1,
        end_scan_id=1,
    )
    calculation = calculate_period(resolve_window(config, (b0,)), b0)
    report = ReportSnapshotV2(
        "baseline-pub",
        1,
        1,
        config,
        calculation,
        None,
        StreamState.NOT_APPLICABLE,
        StreamState.NOT_APPLICABLE,
        StreamState.FINAL,
    )
    assert report.period_state == StreamState.FINAL
