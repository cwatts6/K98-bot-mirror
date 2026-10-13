"""Cumulative and comparison contracts from independently pinned synthetic fights."""

from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path
from uuid import UUID

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.services.new_source_checkpoint_service import build_checkpoint_projection
from kvk.services.new_source_export_service import ExportSelection
from tests.test_kvk_source_reader import history, reader_input, records, sheet, sync

NAMES = ("Pass 4", "1st Altar", "2nd Altar", "3rd Altar", "Pass 7")
KP = (50_000_000, 10_000_000, 0, 20_000_000, 30_000_000)
HEALED = (250_000, 100_000, 0, 50_000, 100_000)
DEADS = (100_000, 20_000, 0, 10_000, 40_000)


def fixture(*, names=NAMES, skip=(), missing=(), overall=False):
    inputs, windows = [], []
    for i, name in enumerate(names):
        sel, snap = reader_input()
        sel = ExportSelection(16, str(UUID(int=200 + i)), str(UUID(int=300 + i)), 7)
        start, end = 10 + i * 10, 13 + i * 10
        if i in skip:
            end = start
        pub = snap["envelope"]["publication"]
        pub.update(
            PublicationID=sel.publication_id,
            PeriodID=sel.period_id,
            PeriodKey=f"fight:{i}",
            StartScanID=start,
            EndScanID=end,
            StartRevisionID=str(UUID(int=400 + i * 3)),
            EndRevisionID=str(UUID(int=401 + i * 3)),
            AggregateRevisionID=str(UUID(int=402 + i * 3)),
        )
        snap["envelope"]["period_id"] = sel.period_id
        for config in snap["metadata"]["configs"].values():
            config.update(
                PeriodID=sel.period_id,
                PeriodKey=f"fight:{i}",
                WindowName=name,
                WindowSeq=i + 1,
                StartScanID=start,
                EndScanID=end,
            )
        start_time = datetime(2026, 9, 1, tzinfo=UTC) + timedelta(days=i * 2)
        end_time = start_time + timedelta(hours=12)
        snap["metadata"]["endpoints"] = dict(
            start=dict(ScanStartUTC=start_time), end=dict(ScanStartUTC=end_time)
        )
        snap["metadata"]["aggregate"] = dict(
            CoverageStartUTC=start_time, CoverageEndUTC=end_time, AsOfUTC=end_time
        )
        kp, healed, dead = KP[i % 5], HEALED[i % 5], DEADS[i % 5]
        row = snap["envelope"]["players"][0]
        row.update(
            name=f"Player name {i+1}",
            t4_kills=kp // 10,
            t5_kills=0,
            healed=healed,
            dead=dead,
            dkp=Decimal(kp + 40 * dead),
            dkp_power_ratio=Decimal(kp + 40 * dead) / Decimal(90_000_000),
            power=Decimal(-1_000_000 - i),
            starting_power=90_000_000,
        )
        for power in snap["player_powers"]:
            if power["GovernorID"] == row["GovernorID"]:
                power.update(
                    BaselinePower=90_000_000,
                    StartPower=100_000_000 + i * 1_000_000,
                    EndPower=99_000_000 + i * 1_000_000 - i,
                )
        for rows in snap["envelope"]["aggregates"].values():
            for agg in rows:
                values = dict(
                    t4_kills=kp // 10 * 2,
                    t5_kills=0,
                    kp_t4_t5=kp * 2,
                    healed=healed * 2,
                    dead=dead * 2,
                    dkp=(kp + 40 * dead) * 3,
                    acclaim=100 + i,
                    t4_t5_dead=dead,
                )
                for key, value in values.items():
                    agg.update(
                        {
                            key: Decimal(value),
                            key + "_raw": str(value),
                            key + "_unit": Decimal(1),
                            key + "_precision": "reported_numeric",
                        }
                    )
        sync(snap)
        snap["reader_context"]["revisions"].update(
            start=pub["StartRevisionID"],
            end=pub["EndRevisionID"],
            aggregate=pub["AggregateRevisionID"],
        )
        windows.append(deepcopy(snap["metadata"]["configs"]["selected"]))
        inputs.append((sel, snap))
    for _, snap in inputs:
        snap["reader_context"]["windows"] = deepcopy(windows)
    inputs = [p for i, p in enumerate(inputs) if i not in set(skip) | set(missing)]
    if overall:
        sel, snap = reader_input(overall=True)
        sel = ExportSelection(16, str(UUID(int=900)), str(UUID(int=901)), 7)
        snap["envelope"]["period_id"] = sel.period_id
        snap["envelope"]["publication"]["PublicationID"] = sel.publication_id
        for cfg in snap["metadata"]["configs"].values():
            cfg.update(PeriodID=sel.period_id, WindowSeq=100)
        sync(snap)
        snap["reader_context"]["windows"] = deepcopy(windows)
        inputs.append((sel, snap))
    return inputs


def build(inputs):
    snapshot, rows = history()
    return build_checkpoint_projection(inputs, history_snapshot=snapshot, history_rows=rows)


@pytest.mark.parametrize("overall", [False, True])
@pytest.mark.parametrize("change", ["move", "add", "remove"])
def test_incompatible_camp_membership_fails_before_cumulative_or_comparison(overall, change):
    inputs = fixture(names=NAMES[:1] if overall else NAMES[:2], overall=overall)
    snap = inputs[-1][1]
    mapping = snap["metadata"]["camps"]
    if change == "move":
        mapping[0]["CampID"] = 8 if mapping[0]["CampID"] != 8 else 1
    elif change == "add":
        mapping.append(dict(mapping[0], Kingdom=9999))
    else:
        mapping.pop()
    sync(snap)
    with pytest.raises(SourceConflict, match="compatible pinned camp membership"):
        build(inputs)


def test_equivalent_camp_membership_allows_config_and_label_changes():
    inputs = fixture(names=NAMES[:2], overall=True)
    for index, (_, snap) in enumerate(inputs):
        config_id = str(UUID(int=700 + index))
        snap["envelope"]["publication"]["ConfigVersionID"] = config_id
        for config in snap["metadata"]["configs"].values():
            config["ConfigVersionID"] = config_id
        snap["metadata"]["camps"].reverse()
        for entry in snap["metadata"]["camps"]:
            entry["CampName"] = "Renamed camp " + str(index)
        sync(snap)
    result = build(inputs)
    assert records(result, "Fights to 1st Altar Camps")[0]["T4+T5 KP"] == 120_000_000
    assert records(result, "Camps T4+T5 KP")[0]["Pass 4"] == 100_000_000
    assert records(result, "Camps T4+T5 KP")[0]["Overall"] is not None


@pytest.mark.parametrize("period_kind", ["fight", "no_fight"])
def test_no_fight_mapping_does_not_participate_in_camp_compatibility(period_kind):
    inputs = fixture(names=NAMES[:2])
    snap = inputs[-1][1]
    start = snap["envelope"]["publication"]["StartScanID"]
    snap["envelope"]["publication"].update(
        EndScanID=start,
        AggregateState="not_applicable",
        AggregateRevisionID=None,
        PeriodKey=period_kind + ":1",
    )
    snap["reader_context"]["revisions"]["aggregate"] = None
    for rows in snap["envelope"]["aggregates"].values():
        rows.clear()
    for config in snap["metadata"]["configs"].values():
        config.update(EndScanID=start, PeriodKind=period_kind, PeriodKey=period_kind + ":1")
    snap["metadata"]["camps"].append(dict(snap["metadata"]["camps"][0], Kingdom=9999))
    sync(snap)
    result = build(inputs)
    assert len(result.checkpoints) == 1
    assert "1st Altar" not in [c.label for c in sheet(result, "Camps DKP").columns]


def test_cumulative_camp_missing_dkp_keeps_the_correct_camp_mapping():
    from kvk.services.new_source_cumulative import entity_records
    from kvk.services.new_source_reader_service import _entity_sheet

    inputs = fixture(names=NAMES[:2])
    for _, snapshot in inputs:
        rows = snapshot["envelope"]["aggregates"]["SourceCampReportRow"]
        missing = deepcopy(rows[0])
        missing.update(CampID=2, CampLabel="South Camp", dkp=None)
        rows.insert(0, missing)
    selection, snapshot = inputs[0]
    result = _entity_sheet(selection, snapshot, "camp", [])
    values = entity_records(snapshot, result, "camp")
    assert values[1]["DKP"] is not None
    assert values[2]["DKP"] is None
    assert values[1]["Camp"] != values[2]["Camp"]


def first(projection, title):
    return next(r for r in records(projection, title) if r.get("Governor ID") == "1001")


def test_five_fight_all_checkpoints_and_27_comparisons():
    result = build(fixture())
    assert len(result.sheets) == 62
    assert len(result.checkpoints) == 5
    assert [len(c.sheet_keys) for c in result.checkpoints] == [3, 6, 6, 6, 6]
    assert len([s for s in result.sheets if s.key.startswith("comparison:")]) == 27
    for i, name in enumerate(NAMES[1:], 1):
        row = first(result, "Fights to " + name + " Players")
        assert row["T4+T5 KP"] == sum(KP[: i + 1])
        assert row["Healed Troops"] == sum(HEALED[: i + 1])
        assert row["KP Loss"] == sum(HEALED[: i + 1]) * 20
        assert row["Deads"] == sum(DEADS[: i + 1])
        assert row["Player DKP"] == sum(KP[: i + 1]) + 40 * sum(DEADS[: i + 1])
        assert row["Baseline Power"] == 90_000_000
        assert row["DKP Rank"] == 1
    row = first(result, "Fights to Pass 7 Players")
    assert row["Player DKP"] == 116_800_000
    assert row["Tanking Score (%)"] == Decimal("10.816125860374")
    assert row["DKP / Baseline Power"] == Decimal("1.297777777778")
    assert row["Fighting Power Change"] == -5_000_010
    assert len(sheet(result, "Fights to Pass 7 Players").columns) == 19
    assert len(sheet(result, "Fights to Pass 7 Kingdoms").columns) == 14
    assert len(sheet(result, "Fights to Pass 7 Camps").columns) == 13
    assert len(result.audit.tables) == 12


def test_aggregate_authority_and_recomputed_not_averaged_score():
    result = build(fixture())
    for kind in ("Kingdoms", "Camps"):
        row = records(result, "Fights to Pass 7 " + kind)[0]
        assert row["DKP"] == 116_800_000 * 3
        assert row["T4+T5 KP"] == 220_000_000
        assert row["KP Loss"] == 20_000_000
        assert row["Tanking Score (%)"] == Decimal("10.816125860374")


def test_skipped_altars_without_publications_and_source_links():
    result = build(fixture(skip=(2, 3)))
    assert len(result.sheets) == 50
    assert all(
        not s.title.startswith(("2nd Altar ", "3rd Altar ", "Fights to 2nd", "Fights to 3rd"))
        for s in result.sheets
    )
    row = first(result, "Fights to Pass 7 Players")
    assert row["T4+T5 KP"] == 90_000_000
    assert [m.status for m in result.checkpoints[-1].members] == [
        "selected",
        "selected",
        "no_fight",
        "no_fight",
        "selected",
    ]
    assert len([r for r in records(result, "Scans") if r["Status"] == "No fight"]) == 2
    assert len([r for r in records(result, "Report Guide") if r["Availability"] == "No fight"]) == 2
    sources = records(result, "Source Files")
    assert "Fights to Pass 7" in sources[0]["Used In"]
    assert any(":cumulative:" in link.target for link in sheet(result, "Source Files").links)


def test_later_fight_does_not_change_earlier_manifest_or_results():
    before, after = build(fixture()), build(fixture(names=(*NAMES, "Pass 8")))
    assert [c.key for c in before.checkpoints] == [c.key for c in after.checkpoints[:5]]
    for s in before.sheets:
        if ":cumulative:" in s.key:
            assert s == next(x for x in after.sheets if x.key == s.key)


def test_missing_fight_not_zero_and_missing_metric_is_independent():
    result = build(fixture(missing=(1,)))
    row = first(result, "Fights to Pass 7 Players")
    assert row["T4+T5 KP"] is None and row["Player DKP"] is None and row["DKP Rank"] is None
    assert "1st Altar" in row["Data Status"]
    inputs = fixture()
    r = inputs[1][1]["envelope"]["players"][0]
    status = json.loads(r["FieldStatusJson"])
    status["healed"] = "missing_end"
    r["FieldStatusJson"] = json.dumps(status)
    row = first(build(inputs), "Fights to Pass 7 Players")
    assert row["Healed Troops"] is None and row["Tanking Score (%)"] is None
    assert row["Player DKP"] == 116_800_000 and row["T4+T5 KP"] == 110_000_000


def test_per_fight_weights_summed_and_cumulative_rank_recomputed():
    inputs = fixture()
    snap = inputs[1][1]
    snap["weights"]["WeightT4XSource"] = "15"
    snap["envelope"]["players"][0]["dkp"] += Decimal(5_000_000)
    result = build(inputs)
    assert first(result, "Fights to Pass 7 Players")["Player DKP"] == 121_800_000
    assert first(result, "Fights to Pass 7 Players")["Player Name"] == "Player name 5"
    assert len(records(result, "Fights to Pass 7 Players")) == 4


@pytest.mark.parametrize("problem", ["overlap", "cumulative", "unknown", "duplicate_revision"])
def test_aggregate_additivity_gate_preserves_player_totals(problem):
    inputs = fixture()
    snap = inputs[1][1]
    if problem in ("overlap", "cumulative"):
        snap["metadata"]["aggregate"]["CoverageStartUTC"] = inputs[0][1]["metadata"]["endpoints"][
            "start"
        ]["ScanStartUTC"]
    elif problem == "unknown":
        snap["metadata"]["aggregate"]["CoverageStartUTC"] = None
    else:
        snap["envelope"]["publication"]["AggregateRevisionID"] = inputs[0][1]["envelope"][
            "publication"
        ]["AggregateRevisionID"]
        snap["reader_context"]["revisions"]["aggregate"] = snap["envelope"]["publication"][
            "AggregateRevisionID"
        ]
    sync(snap)
    result = build(inputs)
    assert records(result, "Fights to Pass 7 Kingdoms")[0]["DKP"] is None
    assert first(result, "Fights to Pass 7 Players")["Player DKP"] == 116_800_000


def test_player_overlap_blocks_and_shared_boundary_is_allowed():
    inputs = fixture()
    a, b = inputs[0][1], inputs[1][1]
    b["metadata"]["endpoints"]["start"] = deepcopy(a["metadata"]["endpoints"]["start"])
    sync(b)
    assert first(build(inputs), "Fights to Pass 7 Players")["Player DKP"] is None
    b["metadata"]["endpoints"]["start"] = deepcopy(a["metadata"]["endpoints"]["end"])
    sync(b)
    assert first(build(inputs), "Fights to Pass 7 Players")["Player DKP"] == 116_800_000


def test_independent_overall_and_comparison_golden_columns():
    result = build(fixture(overall=True))
    row = first(result, "Players DKP")
    assert row["Overall"] == 1800
    assert row["Pass 7"] == 31_600_000
    assert tuple(c.label for c in sheet(result, "Players DKP").columns) == (
        "Governor ID",
        "Player Name",
        "Kingdom",
        "Camp",
        *NAMES,
        "Overall",
        "Data Notes",
    )
    assert first(result, "Overall Players")["Player DKP"] == 1800
    assert all(
        ":cumulative:" not in c.label
        for s in result.sheets
        if s.key.startswith("comparison:")
        for c in s.columns
    )


def test_first_occurring_fight_has_no_redundant_cumulative():
    result = build(fixture(skip=(0, 1)))
    assert len(result.checkpoints[0].sheet_keys) == 3
    assert result.checkpoints[0].name == "2nd Altar"


def test_all_skipped_has_no_fighting_outputs():
    result = build(fixture(skip=range(5), overall=True))
    assert result.checkpoints == ()
    assert not any(
        s.purpose == "This fighting window only" or ":cumulative:" in s.key for s in result.sheets
    )
    assert len([r for r in records(result, "Scans") if r["Status"] == "No fight"]) == 5


@pytest.mark.parametrize("field", ["RosterID", "baseline", "attribution", "BaselinePower"])
def test_incompatible_baseline_fails_closed(field):
    inputs = fixture()
    snap = inputs[1][1]
    if field == "RosterID":
        snap["envelope"]["publication"][field] = "different-roster"
    elif field == "baseline":
        snap["reader_context"]["revisions"][field] = str(UUID(int=999))
    elif field == "attribution":
        snap["envelope"]["players"][0]["CampID"] = 2
    else:
        snap["player_powers"][0][field] += 1
    sync(snap)
    with pytest.raises(SourceConflict):
        build(inputs)


def test_duplicate_and_formula_like_fight_labels_are_literal_unique_columns():
    result = build(fixture(names=("=SUM(A1)", "Overall", "Camp", "Same", "Same")))
    labels = [c.label for c in sheet(result, "Players DKP").columns]
    assert "=SUM(A1)" in labels and len(labels) == len(set(labels))
    assert "Overall (fight 2)" in labels


def test_input_order_and_retry_identity_stable_and_correction_counted_once():
    inputs = fixture()
    assert build(inputs).key == build(list(reversed(deepcopy(inputs)))).key
    before = build(inputs)
    sel, snap = inputs[1]
    sel = replace(sel, publication_id=str(UUID(int=888)), selection_version=8)
    snap["envelope"]["publication"]["PublicationID"] = sel.publication_id
    snap["envelope"]["selection"]["SelectionVersion"] = 8
    sync(snap)
    inputs[1] = sel, snap
    after = build(inputs)
    assert after.key != before.key
    assert first(after, "Fights to Pass 7 Players")["T4+T5 KP"] == 110_000_000
    assert after.checkpoints[-1].members[1].publication_id == sel.publication_id


def test_live_contribution_visible_and_no_absent_endpoints_inferred_as_no_fight():
    inputs = fixture()
    snap = inputs[1][1]
    snap["envelope"]["publication"]["PlayerState"] = "live"
    sync(snap)
    assert "Live" in first(build(inputs), "Fights to Pass 7 Players")["Data Status"]
    inputs = fixture(missing=(1,))
    for _, snap in inputs:
        for w in snap["reader_context"]["windows"]:
            if w["WindowSeq"] == 2:
                w.update(StartScanID=None, EndScanID=None)
    assert build(inputs).checkpoints[-1].members[1].status == "missing"


def test_renamed_and_reordered_configuration_owns_membership():
    inputs = fixture()
    cutoff = inputs[-1][1]
    windows = cutoff["reader_context"]["windows"]
    windows[0]["WindowSeq"], windows[1]["WindowSeq"] = 2, 1
    windows[0]["WindowName"] = "Opening battle"
    result = build(inputs)
    assert [m.period_id for m in result.checkpoints[-1].members[:2]] == [
        inputs[1][0].period_id,
        inputs[0][0].period_id,
    ]
    assert result.checkpoints[-1].members[1].name == "Opening battle"
    assert first(result, "Fights to Pass 7 Players")["T4+T5 KP"] == 110_000_000


@pytest.mark.parametrize(
    "bad", ["duplicate_order", "duplicate_period", "endpoints", "skip_conflict"]
)
def test_ambiguous_membership_rejected(bad):
    inputs = fixture()
    windows = inputs[-1][1]["reader_context"]["windows"]
    if bad == "duplicate_order":
        windows[1]["WindowSeq"] = windows[0]["WindowSeq"]
    elif bad == "duplicate_period":
        windows.append(deepcopy(windows[0]))
    elif bad == "endpoints":
        windows[0]["EndScanID"] += 1
    else:
        windows[0]["EndScanID"] = windows[0]["StartScanID"]
    with pytest.raises(SourceConflict):
        build(inputs)


def test_cumulative_valid_zero_rank_and_numeric_governor_tie_break():
    inputs = fixture()
    result = build(inputs)
    zero = [r for r in records(result, "Fights to Pass 7 Players") if r["Player DKP"] == 0]
    assert [(r["Governor ID"], r["DKP Rank"]) for r in zero] == [("1002", 2), ("1004", 3)]
    assert all(r["KP Loss"] == 0 for r in zero)
    assert all(r["Tanking Score (%)"] is None for r in zero)


def test_missing_entity_does_not_become_zero_or_remove_other_entity_metrics():
    inputs = fixture()
    inputs[1][1]["envelope"]["aggregates"]["SourceKingdomReportRow"] = []
    result = build(inputs)
    assert records(result, "Fights to Pass 7 Kingdoms")[0]["DKP"] is None
    assert records(result, "Fights to Pass 7 Camps")[0]["DKP"] == 350_400_000


def test_large_cumulative_metric_keeps_exact_audit_and_flags_reader_precision():
    inputs = fixture()
    for _, snap in inputs:
        agg = snap["envelope"]["aggregates"]["SourceCampReportRow"][0]
        agg.update(dkp=Decimal("333333333333333"), dkp_raw="333333333333333")
    result = build(inputs)
    row = records(result, "Fights to Pass 7 Camps")[0]
    assert row["DKP"] is None and "Precision limit" in row["Data Status"]
    assert records(result, "Fights to Pass 7 Camps", exact=True)[0]["DKP"] == "1666666666666665"


def test_kvk15_compatible_additive_control_without_legacy_kp_or_identity_rules():
    control = json.loads(
        (Path(__file__).parent / "fixtures/kvk15_cumulative_control.json").read_text()
    )
    inputs = fixture()
    mapping = {
        "dkp": "DKP",
        "kills_gain": "T4 + T5 Kills",
        "t4_kills": "T4 Kills",
        "t5_kills": "T5 Kills",
        "deads": "Deads",
        "kp_loss": "KP Loss",
        "healed_troops": "Healed Troops",
    }
    for i, (_, snap) in enumerate(inputs):
        agg = snap["envelope"]["aggregates"]["SourceCampReportRow"][0]
        for key, metric in control["metrics"].items():
            source = {"deads": "dead", "healed_troops": "healed"}.get(key, key)
            if source in ("kills_gain", "kp_loss"):
                continue
            value = Decimal(metric["fights"][i])
            agg.update(
                {
                    source: value,
                    source + "_raw": str(value),
                    source + "_unit": Decimal(1),
                    source + "_precision": "reported_numeric",
                }
            )
        tier = 10 * agg["t4_kills"] + 20 * agg["t5_kills"]
        agg.update(kp_t4_t5=tier, kp_t4_t5_raw=str(tier))
    row = records(build(inputs), "Fights to Pass 7 Camps")[0]
    for key, label in mapping.items():
        assert row[label] == control["metrics"][key]["cumulative"]


def test_one_fight_has_38_sheets_and_exact_comparison_schema():
    result = build(fixture(names=("Pass 4",)))
    assert len(result.sheets) == 38
    assert tuple(c.label for c in sheet(result, "Kingdoms Tanking Score").columns) == (
        "Kingdom",
        "Camp",
        "Pass 4",
        "Overall",
        "Data Notes",
    )
    assert tuple(c.label for c in sheet(result, "Camps KP Loss").columns) == (
        "Camp",
        "Pass 4",
        "Overall",
        "Data Notes",
    )
