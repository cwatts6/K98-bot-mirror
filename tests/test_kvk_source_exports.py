"""Synthetic source export contracts. No live SQL, files, Sheets or Discord."""

from copy import deepcopy
from decimal import Decimal
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.rendering.new_source_export import text_value
from kvk.services.kvk_export_service import KVK_EXPORT_SECTION_NAMES
from kvk.services.new_source_export_service import (
    ExportSelection,
    build_generation,
    load_generation,
)
from tests.test_kvk_source_reporting import PERIOD, PUBLICATION, source_inputs


def export_input(**options):
    envelope, meta = source_inputs(**options)
    envelope["publication"].update(StartRevisionID="start-revision", EndRevisionID="end-revision")
    for family in envelope["aggregates"].values():
        for row in family:
            row.update(
                t4_t5_dead=Decimal("4779000000"),
                t4_t5_dead_raw="4.779B",
                t4_t5_dead_unit=Decimal("1000000"),
                t4_t5_dead_precision="reported_abbreviated",
            )
    snapshot = dict(
        envelope=envelope,
        metadata=meta,
        weights=dict(WeightT4XSource="10", WeightT5YSource="20", WeightDeadsZSource="40"),
    )
    return ExportSelection(16, PERIOD, PUBLICATION, 7), snapshot


def records(generation, name):
    item = next(t for t in generation.tables if t.name == name)
    return [dict(zip(item.columns, row, strict=True)) for row in item.rows]


def test_t16_t55_all_ten_sections_exact_metrics_and_precision():
    generation = build_generation((export_input(),))
    assert tuple(t.name for t in generation.tables[:10]) == KVK_EXPORT_SECTION_NAMES
    rows = records(generation, "KVK_Kingdom_Windowed")
    assert next(r for r in rows if r["metric"] == "dkp")["raw"] == "25.3M"
    dead = next(r for r in rows if r["metric"] == "t4_t5_dead")
    assert (dead["value"], dead["raw"], dead["unit"]) == ("4779000000", "4.779B", "1000000")
    unsupported = next(r for r in rows if r["metric"] == "total_kill_points")
    assert (unsupported["value"], unsupported["status"]) == ("", "unsupported")
    assert all(r["publication_id"] == PUBLICATION for r in rows)


def test_t56_fights_never_fill_overall_or_add_revisions():
    first = export_input()
    second = deepcopy(first)
    second = (
        ExportSelection(
            16,
            "00000000-0000-0000-0000-000000000003",
            "00000000-0000-0000-0000-000000000004",
            7,
        ),
        second[1],
    )
    second[1]["envelope"]["period_id"] = second[0].period_id
    second[1]["envelope"]["publication"]["PublicationID"] = second[0].publication_id
    second[1]["envelope"]["publication"]["PeriodKey"] = "fight:pass7"
    for config in second[1]["metadata"]["configs"].values():
        config["PeriodKey"] = "fight:pass7"
    generation = build_generation((first, second))
    assert records(generation, "KVK_Camp_Full")[0]["status"] == "not_received"
    values = [
        r["value"]
        for r in records(generation, "ALL_WINDOWS")
        if r["entity_kind"] == "camp" and r["metric"] == "dkp"
    ]
    assert values == ["25300000", "25300000"]
    with pytest.raises(SourceConflict, match="one publication"):
        build_generation((first, first))


def test_overall_selects_separate_final_report_and_player_period():
    generation = build_generation((export_input(overall=True),))
    assert records(generation, "KVK_Camp_Windowed") == []
    assert (
        next(r for r in records(generation, "KVK_Camp_Full") if r["metric"] == "dkp")["value"]
        == "25300000"
    )
    assert all(r["period_key"] == "overall" for r in records(generation, "KVK_Player_Full"))


def test_b0_missing_zero_attribution_and_total_deaths_dkp():
    generation = build_generation((export_input(),))
    players = records(generation, "KVK_Player_Windowed")
    dkp = [r for r in players if r["metric"] == "dkp"]
    assert len(dkp) == 4
    assert any(r["value"] == "1800" for r in dkp)
    assert any(r["value"] == "0" and r["status"] == "available" for r in dkp)
    assert any(r["value"] == "" and r["status"] == "missing_start" for r in dkp)
    assert all(r["b0_kingdom"] for r in dkp)


@pytest.mark.parametrize("end_scan", [None, 13, 14, 10])
def test_endpoint_and_equal_endpoint_semantics(end_scan):
    generation = build_generation((export_input(end_scan=end_scan),))
    window = records(generation, "KVK_Windows")[0]
    assert window["selected_start_scan_id"] == "10"
    assert "+00:00" in window["player_start_utc"]
    if end_scan == 10:
        dkp = [r for r in records(generation, "KVK_Player_Windowed") if r["metric"] == "dkp"]
        assert len(dkp) == 4 and all(r["value"] == "0" and r["rank"] == "" for r in dkp)
        assert window["aggregate_state"] == "not_applicable"
    elif end_scan == 13:
        assert window["player_state"] == "final"
    else:
        assert window["player_state"] == "live"


def test_pending_endpoint_does_not_label_old_final_current():
    row = records(build_generation((export_input(desired_end=14),)), "KVK_Windows")[0]
    assert (row["requested_end_scan_id"], row["selected_end_scan_id"]) == ("14", "13")
    assert row["is_current"] == "False"
    assert row["current_period_state"] == "missing_configuration"


def test_t63_formula_protection_and_exact_large_ids_decimal_text():
    selection, snapshot = export_input()
    snapshot["envelope"]["players"][0]["name"] = ' =HYPERLINK("bad")'
    snapshot["envelope"]["players"][0]["GovernorID"] = 9223372036854775807
    snapshot["envelope"]["aggregates"]["SourceCampReportRow"][0]["dkp"] = Decimal(
        "123456789012345678901234567890.123456"
    )
    generation = build_generation(((selection, snapshot),))
    player = next(t for t in generation.tables if t.name == "KVK_Player_Windowed")
    assert "' =HYPERLINK" in player.csv_bytes().decode("utf-8-sig")
    assert "9223372036854775807" in player.csv_bytes().decode("utf-8-sig")
    assert any(' =HYPERLINK("bad")' in row for row in player.raw_values())
    assert (
        next(r for r in records(generation, "KVK_Camp_Windowed") if r["metric"] == "dkp")["value"]
        == "123456789012345678901234567890.123456"
    )


@pytest.mark.parametrize("value", [1.0, float("nan"), float("inf"), Decimal("NaN"), object()])
def test_binary_float_and_nonfinite_rejected(value):
    with pytest.raises(ValueError):
        text_value(value)


def test_t67_comparisons_are_labelled_facts_not_unproved_ranks():
    generation = build_generation((export_input(),))
    assert {r["comparison_status"] for r in records(generation, "COMPARISONS")} == {
        "side_by_side_only"
    }


def test_load_is_explicit_once_and_never_retargets():
    selection, snapshot = export_input()
    connect = Mock(side_effect=AssertionError("No SQL"))
    loader = Mock(return_value=snapshot)
    generation = load_generation(connect=connect, selections=(selection,), snapshot_loader=loader)
    loader.assert_called_once_with(connect=connect, selection=selection)
    assert generation.key == build_generation(((selection, snapshot),)).key
    snapshot["envelope"]["publication"]["PublicationID"] = "changed"
    with pytest.raises(SourceConflict):
        load_generation(connect=connect, selections=(selection,), snapshot_loader=loader)


def test_generation_is_immutable_after_source_mutation():
    selection, snapshot = export_input()
    generation = build_generation(((selection, snapshot),))
    original = generation.key
    snapshot["envelope"]["players"][0]["name"] = "changed label"
    assert generation.key == original
    assert build_generation(((selection, snapshot),)).key != original


@pytest.mark.parametrize(
    "changes",
    [
        dict(kvk_no=True),
        dict(kvk_no=0),
        dict(period_id="bad"),
        dict(publication_id="bad"),
        dict(selection_version=0),
    ],
)
def test_explicit_selection_validation(changes):
    args = dict(kvk_no=16, period_id=PERIOD, publication_id=PUBLICATION, selection_version=7)
    with pytest.raises(ValueError):
        ExportSelection(**(args | changes))


def test_semantic_retry_row_order_does_not_create_a_new_export():
    selection, snapshot = export_input()
    initial = build_generation(((selection, snapshot),))
    snapshot["envelope"]["players"].reverse()
    assert build_generation(((selection, snapshot),)).key == initial.key


@pytest.mark.parametrize(
    "scan_id,expected,state",
    [(11, "1000", "live"), (12, "1000", "live"), (13, "1800", "final"), (14, "1800", "final")],
)
def test_exact_interim_final_and_updated_endpoint_exports(scan_id, expected, state):
    from dataclasses import replace

    from kvk.dal.new_source_publication_dal import result_values
    from kvk.services.new_source_calculation import calculate_period
    from kvk.services.new_source_window_resolver import resolve_window
    from tests.kvk_source_fixtures import calculation_config, worked_calculation_inputs

    b0, start, middle, end = worked_calculation_inputs()
    event = replace(middle if scan_id < 13 else end, logical_scan_id=scan_id)
    config = calculation_config(end_scan_id=scan_id if scan_id >= 13 else None)
    calculation = calculate_period(resolve_window(config, (start, event)), b0)
    selection, snapshot = export_input(end_scan=scan_id if scan_id >= 13 else None)
    snapshot["envelope"]["players"] = [result_values(p) for p in calculation.players]
    snapshot["envelope"]["publication"].update(EndScanID=scan_id, PlayerState=state)
    snapshot["metadata"]["endpoints"]["end"]["ScanStartUTC"] = event.scan_start_utc
    generation = build_generation(((selection, snapshot),))
    dkp = next(
        r
        for r in records(generation, "KVK_Player_Windowed")
        if r["entity_id"] == "1001" and r["metric"] == "dkp"
    )
    assert dkp["value"] == expected
    assert dkp["selected_start_scan_id"] == "10" and dkp["selected_end_scan_id"] == str(scan_id)
    assert dkp["player_state"] == state


@pytest.mark.parametrize("options", [{}, {"end_scan": 10}, {"desired_end": 14}, {"overall": True}])
def test_compact_sheets_roundtrip_preserves_every_fact_and_context(options):
    from kvk.services.new_source_export_service import CONTEXT, compact_sheets_generation

    original = build_generation((export_input(**options),))
    compact = compact_sheets_generation(original)
    windows = records(compact, "KVK_Windows")
    contexts = {r["context_ref"]: {c: r[c] for c in CONTEXT} for r in windows}
    for item in original.tables:
        if "metric" not in item.columns:
            continue
        restored = []
        for row in records(compact, item.name):
            base = {
                **contexts[row["context_ref"]],
                **{k: v for k, v in row.items() if "::" not in k},
            }
            metrics = [c[:-8] for c in row if c.endswith("::status") and row[c]]
            for metric in metrics or [""]:
                value = dict(base, metric=metric)
                if metric:
                    value.update(
                        {
                            field: row.get(metric + "::" + field, "")
                            for field in (
                                "value",
                                "status",
                                "raw",
                                "unit",
                                "precision",
                                "rank",
                                "cohort",
                            )
                        }
                    )
                restored.append(tuple(value.get(c, "") for c in item.columns))
        assert sorted(restored) == sorted(item.rows)
    assert sum(len(t.rows) * len(t.columns) for t in compact.tables) < sum(
        len(t.rows) * len(t.columns) for t in original.tables
    )


def test_load_compact_periods_preserves_separate_overall_and_order():
    from dataclasses import replace

    from kvk.services.new_source_export_service import load_sheets_generation

    first, a = export_input()
    second, b = export_input(overall=True)
    second = replace(
        second,
        period_id="00000000-0000-0000-0000-000000000003",
        publication_id="00000000-0000-0000-0000-000000000004",
    )
    b["envelope"]["period_id"] = second.period_id
    b["envelope"]["publication"]["PublicationID"] = second.publication_id
    lookup = {first: a, second: b}
    loader = lambda **kwargs: lookup[kwargs["selection"]]
    actual = load_sheets_generation(
        connect=None, selections=(first, second), snapshot_loader=loader
    )
    reverse = load_sheets_generation(
        connect=None, selections=(second, first), snapshot_loader=loader
    )
    assert actual.key == reverse.key
    assert all(row["entity_id"] for row in records(actual, "KVK_Player_Full"))
    assert any(
        row["period_key"] == "overall" and row["publication_id"] == second.publication_id
        for row in records(actual, "KVK_Windows")
    )
