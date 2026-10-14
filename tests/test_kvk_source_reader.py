"""Golden human projection contracts; inputs are synthetic pinned publications."""

from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from uuid import UUID

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.models.new_source_history import HistorySnapshot, encode_fact, hash_row, history_fact
from kvk.models.new_source_reader import ReaderLink, spreadsheet_number
from kvk.schemas.new_source_schema import SOURCE_KEY
from kvk.services.new_source_reader_service import build_reader_projection
from tests.test_kvk_source_exports import export_input

BASE, START, END, AGG, INTENT = [str(UUID(int=i)) for i in range(40, 45)]
NOW = datetime(2026, 10, 13, 10, 11, 12, tzinfo=UTC)
GOLDEN = {
    "Pass 4 Players": (
        "Governor ID",
        "Player Name",
        "Kingdom",
        "Camp",
        "DKP Rank",
        "Player DKP",
        "DKP / Baseline Power",
        "T4+T5 KP",
        "T4 + T5 Kills",
        "T4 Kills",
        "T5 Kills",
        "Deads",
        "Healed Troops",
        "KP Loss",
        "Tanking Score (%)",
        "Acclaim Gained",
        "Baseline Power",
        "Fight-start Power",
        "End Power",
        "Power Change",
        "Data Status",
    ),
    "Pass 4 Kingdoms": (
        "Kingdom",
        "Camp",
        "DKP",
        "T4+T5 KP",
        "T4 + T5 Kills",
        "T4 Kills",
        "T5 Kills",
        "Deads",
        "T4+T5 Deads",
        "Healed Troops",
        "KP Loss",
        "Tanking Score (%)",
        "Acclaim",
        "Data Status",
    ),
    "Report Guide": ("Report", "Purpose", "Period", "Availability"),
    "Scans": (
        "Period",
        "Start Scan",
        "Start (UTC)",
        "End Scan",
        "End (UTC)",
        "Status",
        "Selection Notes",
    ),
    "DKP Weights": ("Period", "T4 Kill Weight", "T5 Kill Weight", "Deads Weight", "Applies To"),
    "Source Files": (
        "Scan",
        "Source File",
        "Data Included",
        "Data Time (UTC)",
        "Imported (UTC)",
        "Records",
        "Import Status",
        "Used In",
        "Notes",
    ),
    "Data Issues": (
        "Period",
        "Report",
        "Governor ID",
        "Player Name",
        "Kingdom",
        "Camp",
        "Affected Metric",
        "Issue",
        "Effect on Report",
    ),
}
GOLDEN["Pass 4 Camps"] = GOLDEN["Pass 4 Kingdoms"][1:]
GOLDEN["Overall Players"] = tuple(c for c in GOLDEN["Pass 4 Players"] if c != "Fight-start Power")
GOLDEN["Overall Kingdoms"] = GOLDEN["Pass 4 Kingdoms"]
GOLDEN["Overall Camps"] = GOLDEN["Pass 4 Camps"]


def reader_input(**options):
    selection, snapshot = export_input(**options)
    pub, meta = snapshot["envelope"]["publication"], snapshot["metadata"]
    pub.update(
        StartRevisionID=START,
        EndRevisionID=END,
        AggregateRevisionID=AGG if pub["AggregateRevisionID"] else None,
    )
    for config in meta["configs"].values():
        config.update(WindowSeq=1, PeriodID=selection.period_id)
    snapshot["reader_context"] = dict(
        publication=deepcopy(pub),
        metadata=deepcopy(meta),
        windows=[deepcopy(meta["configs"]["selected"])],
        revisions=dict(baseline=BASE, start=START, end=END, aggregate=pub["AggregateRevisionID"]),
    )
    snapshot["player_powers"] = [
        dict(
            GovernorID=r["GovernorID"],
            b0_kingdom=r["b0_kingdom"],
            BaselinePower=r["starting_power"],
            StartPower=110_000_000 if r["GovernorID"] == 1001 else 100,
            EndPower=98_000_000 if r["GovernorID"] == 1001 else 100,
            BaselineFieldStatusJson='{"power":"available"}',
            StartFieldStatusJson='{"power":"available"}',
            EndFieldStatusJson='{"power":"available"}',
        )
        for r in snapshot["envelope"]["players"]
    ]
    return selection, snapshot


def history(*, guild="123", season=16):
    facts = []
    for i, (status, revision) in enumerate(
        (
            ("accepted", BASE),
            ("accepted", START),
            ("accepted", END),
            ("accepted", AGG),
            ("duplicate", END),
            ("rejected", None),
            ("received", None),
            ("conflict", None),
            ("validated", None),
            ("accepted", str(UUID(int=80))),
        )
    ):
        facts.append(
            history_fact(
                dict(
                    AttemptID=str(UUID(int=100 + i)),
                    Status=status,
                    OriginalFilename=r"C:\private\=scan.xlsx",
                    ReceivedUTC=NOW,
                    ObservationRevisionID=revision if revision != AGG else None,
                    AggregateRevisionID=AGG if revision == AGG else None,
                    LogicalScanID=i + 1,
                    DataTimeUTC=NOW,
                    RevisionNo=1,
                    PlayerRecords=4 if revision and revision != AGG else None,
                    KingdomRecords=2 if revision == AGG else None,
                    CampRecords=2 if revision == AGG else None,
                )
            )
        )
    snapshot = HistorySnapshot(INTENT, SOURCE_KEY, season, guild, b"v" * 32, NOW, len(facts), b"")
    hasher = snapshot.hasher()
    for fact in facts:
        hash_row(hasher, encode_fact(fact))
    return replace(snapshot, content_hash=hasher.digest()), facts


def build(*inputs, history_pair=None):
    snapshot, rows = history_pair or history()
    return build_reader_projection(
        inputs or (reader_input(),), history_snapshot=snapshot, history_rows=rows
    )


def sheet(projection, title):
    return next(s for s in projection.sheets if s.title == title)


def records(projection, title, *, exact=False):
    table = sheet(projection, title)
    return [
        dict(zip((c.label for c in table.columns), row, strict=True))
        for row in (table.exact_rows if exact else table.rows)
    ]


def sync(snapshot):
    snapshot["reader_context"]["publication"] = deepcopy(snapshot["envelope"]["publication"])
    snapshot["reader_context"]["metadata"] = deepcopy(snapshot["metadata"])


def test_golden_stage3_headers_and_audit_contract():
    projection = build()
    assert len(projection.sheets) == 11
    assert projection.sheets[0].title == "Report Guide"
    assert {s.title: tuple(c.label for c in s.columns) for s in projection.sheets} == GOLDEN
    assert len(projection.audit.tables) == 12
    forbidden = (
        "B0",
        "Reported",
        "Deaths",
        "Total KP",
        "Player Details",
        "context_ref",
        "entity_kind",
        "Time Precision",
    )
    assert not any(
        word in label
        for s in projection.sheets
        for label in (s.title, *(c.label for c in s.columns))
        for word in forbidden
    )


@pytest.mark.parametrize(
    "kind,title,id_key",
    [
        ("SourceKingdomReportRow", "Pass 4 Kingdoms", "Kingdom"),
        ("SourceCampReportRow", "Pass 4 Camps", "CampID"),
    ],
)
def test_aggregate_missing_dkp_sorts_last_without_losing_identity(kind, title, id_key):
    selection, snapshot = reader_input()
    rows = snapshot["envelope"]["aggregates"][kind]
    missing = deepcopy(rows[0])
    missing.update({id_key: 2 if id_key == "CampID" else 102, "dkp": None})
    rows.insert(0, missing)
    from kvk.services.new_source_reader_service import _entity_sheet

    issues = []
    result = _entity_sheet(selection, snapshot, "camp" if id_key == "CampID" else "kingdom", issues)
    values = [dict(zip((c.label for c in result.columns), row, strict=True)) for row in result.rows]
    assert values[0]["DKP"] is not None and values[-1]["DKP"] is None
    assert issues
    # The SQL schema and audit boundary still reject a NULL aggregate DKP.
    with pytest.raises(SourceConflict, match="availability mismatch"):
        build((selection, snapshot))


def test_tier_metrics_power_and_aggregate_authority():
    projection = build()
    player = records(projection, "Pass 4 Players")[0]
    assert (player["T4+T5 KP"], player["T4 + T5 Kills"]) == (1400, 90)
    assert (player["Baseline Power"], player["Fight-start Power"], player["End Power"]) == (
        100_000_000,
        110_000_000,
        98_000_000,
    )
    assert player["Power Change"] == -2_000_000
    aggregate = records(projection, "Pass 4 Kingdoms")[0]
    assert aggregate["DKP"] == aggregate["T4+T5 KP"] == Decimal("25300000")
    assert aggregate["KP Loss"] == Decimal("506000000")
    assert aggregate["Tanking Score (%)"] == Decimal("0.047619047619")
    assert "supplied" in " ".join(sheet(projection, "Pass 4 Camps").notes)
    assert all(r["Tanking Score (%)"] is None for r in records(projection, "Pass 4 Players"))
    assert any(
        "No healed troops" in r["Data Status"] for r in records(projection, "Pass 4 Players")
    )


def test_grouped_endpoint_issues_zero_negative_and_ranks():
    projection = build()
    players = records(projection, "Pass 4 Players")
    assert [(r["Governor ID"], r["DKP Rank"], r["Player DKP"]) for r in players] == [
        ("1001", 1, 1800),
        ("1002", 2, 0),
        ("1004", 3, 0),
        ("1003", None, None),
    ]
    issues = records(projection, "Data Issues")
    missing = [
        r for r in issues if r["Governor ID"] == "1003" and r["Issue"] == "Missing start scan"
    ]
    assert len(missing) == 1 and missing[0]["Affected Metric"] == "Fight metrics"
    assert not any(
        "T1" in r["Affected Metric"] or r["Affected Metric"] == "Power Change" for r in issues
    )
    assert any("ranked population: 3" in n for n in sheet(projection, "Pass 4 Players").notes)


def test_history_all_outcomes_records_revision_uses_and_links():
    projection = build()
    source = records(projection, "Source Files")
    assert len(source) == 10
    assert source[0]["Source File"] == "=scan.xlsx"
    assert source[0]["Used In"] == "Baseline"
    assert source[2]["Used In"] == source[4]["Used In"] == "Pass 4 end"
    assert source[3]["Records"] == 4 and "2 kingdom" in source[3]["Notes"]
    assert source[5]["Records"] is None and source[5]["Used In"] == "Not used"
    assert source[-1]["Used In"] == "Not used"
    assert {r["Import Status"] for r in source} == {
        "Accepted",
        "Duplicate",
        "Rejected",
        "Pending",
        "Conflict",
        "Validated",
    }
    assert source[0]["Imported (UTC)"].second == 12
    targets = {s.key for s in projection.sheets}
    assert all(link.target in targets for s in projection.sheets for link in s.links)
    assert len(sheet(projection, "Report Guide").links) == 10


def test_selected_times_one_pair_not_aggregate_asof():
    projection = build()
    scan = records(projection, "Scans")[0]
    assert "differs" not in scan["Selection Notes"]
    assert (scan["Start Scan"], scan["End Scan"]) == (10, 13)
    assert len(scan) == 7


@pytest.mark.parametrize("aggregate_state", ["not_received", "validation_failed", "live"])
def test_scan_status_includes_unfinished_aggregate_stream(aggregate_state):
    inp = reader_input()
    pub = inp[1]["envelope"]["publication"]
    pub.update(PlayerState="final", AggregateState=aggregate_state, PeriodState="live")
    sync(inp[1])
    assert records(build(inp), "Scans")[0]["Status"] == "Live — provisional"


@pytest.mark.parametrize(
    "state, label", [("final", "Published"), ("corrected_final", "Published — corrected")]
)
def test_scan_status_uses_terminal_publication_state(state, label):
    inp = reader_input()
    inp[1]["envelope"]["publication"].update(PeriodState=state)
    sync(inp[1])
    assert records(build(inp), "Scans")[0]["Status"] == label


@pytest.mark.parametrize("period_state", ["live", "final", "corrected_final"])
@pytest.mark.parametrize(
    "player_unavailable, aggregate_unavailable", [(True, False), (False, True), (True, True)]
)
def test_scan_status_retains_terminal_stream_unavailability(
    period_state, player_unavailable, aggregate_unavailable
):
    inp = reader_input()
    pub = inp[1]["envelope"]["publication"]
    pub.update(PeriodState=period_state)
    if player_unavailable:
        pub["PlayerState"] = "final_unavailable"
    if aggregate_unavailable:
        pub["AggregateState"] = "final_unavailable"
    sync(inp[1])
    expected = (
        "Unavailable" if player_unavailable and aggregate_unavailable else "Partly unavailable"
    )
    assert records(build(inp), "Scans")[0]["Status"] == expected
    inp[1]["envelope"]["is_current"] = False
    assert records(build(inp), "Scans")[0]["Status"] == "Update pending"


def test_actual_coverage_difference_and_pending_selection_are_visible():
    inp = reader_input(desired_end=14)
    inp[1]["metadata"]["aggregate"]["CoverageEndUTC"] = NOW
    sync(inp[1])
    projection = build(inp)
    scan = records(projection, "Scans")[0]
    assert scan["End Scan"] == 13 and scan["Status"] == "Update pending"
    assert "coverage differs" in scan["Selection Notes"]
    assert any(
        r["Affected Metric"] == "Source coverage" for r in records(projection, "Data Issues")
    )


def test_empty_overall_is_useful_and_independent_overall_not_summed():
    projection = build()
    assert not sheet(projection, "Overall Players").rows
    assert sheet(projection, "Overall Players").availability == "Not published"
    overall = reader_input(overall=True)
    actual = build(overall)
    assert len(sheet(actual, "Overall Players").rows) == 4
    assert not any(s.title == "Pass 4 Players" for s in actual.sheets)


def test_equal_endpoint_overall_keeps_empty_sheets_and_exact_unranked_audit():
    inp = reader_input(overall=True, end_scan=10)
    assert all(r["dkp_rank"] is None for r in inp[1]["envelope"]["players"])
    projection = build(inp)
    for title in ("Overall Players", "Overall Kingdoms", "Overall Camps"):
        result = sheet(projection, title)
        assert result.rows == ()
        assert result.availability == "Not applicable"
    audit = next(t for t in projection.audit.tables if t.name == "KVK_Player_Full")
    dkp = [dict(zip(audit.columns, row, strict=True)) for row in audit.rows]
    dkp = [r for r in dkp if r["metric"] == "dkp"]
    assert len(dkp) == 4
    assert all(r["value"] == "0" and r["rank"] == "" for r in dkp)


def test_equal_endpoint_overall_still_rejects_incomplete_roster():
    inp = reader_input(overall=True, end_scan=10)
    inp[1]["envelope"]["players"].pop()
    with pytest.raises(SourceConflict, match="complete published player cohort"):
        build(inp)


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@", " \t=", "\r+", "\n@"])
def test_formula_like_and_unicode_labels_are_literal(prefix):
    inp = reader_input()
    label = prefix + "長い名前⚔" * 30
    inp[1]["envelope"]["players"][0]["name"] = label
    projection = build(inp)
    assert records(projection, "Pass 4 Players")[0]["Player Name"] == label
    assert sheet(projection, "Pass 4 Players").columns[1].kind == "text"
    assert projection.key


@pytest.mark.parametrize(
    "value,safe",
    [
        (0, True),
        (-42, True),
        (999999999999999, True),
        (1000000000000000, False),
        (9223372036854775807, False),
        (Decimal("0.123456789012345"), True),
        (Decimal("0.1234567890123456"), False),
        (Decimal("12.340000"), True),
    ],
)
def test_numeric_precision_boundary(value, safe):
    assert spreadsheet_number(value) is safe


@pytest.mark.parametrize(
    "value", [1.0, True, float("nan"), Decimal("NaN"), Decimal("Infinity"), "12"]
)
def test_non_exact_numbers_rejected(value):
    with pytest.raises(ValueError):
        spreadsheet_number(value)


def test_unsafe_metric_is_blank_flagged_and_preserved_exactly_in_audit():
    inp = reader_input()
    original = Decimal("123456789012345678901234567890.123456")
    row = inp[1]["envelope"]["aggregates"]["SourceCampReportRow"][0]
    row["dkp"] = original
    projection = build(inp)
    assert records(projection, "Pass 4 Camps")[0]["DKP"] is None
    assert records(projection, "Pass 4 Camps", exact=True)[0]["DKP"] == format(original, "f")
    assert "Precision limit" in records(projection, "Pass 4 Camps")[0]["Data Status"]
    assert any(
        r["Issue"] == "Spreadsheet precision limit" for r in records(projection, "Data Issues")
    )


def test_missing_power_is_not_zero_and_does_not_retarget():
    inp = reader_input()
    inp[1]["player_powers"][0]["EndPower"] = None
    projection = build(inp)
    assert records(projection, "Pass 4 Players")[0]["End Power"] is None
    assert records(projection, "Pass 4 Players")[0]["Player DKP"] == 1800


@pytest.mark.parametrize(
    "role, label",
    [("Baseline", "Baseline Power"), ("Start", "Fight-start Power"), ("End", "End Power")],
)
@pytest.mark.parametrize("damage", ["explicit", "malformed", "missing"])
def test_invalid_power_is_distinguished_from_missing_power(role, label, damage):
    inp = reader_input()
    power = inp[1]["player_powers"][0]
    if damage == "explicit":
        power[role + "FieldStatusJson"] = '{"power":"invalid_source_value"}'
    else:
        power[role + "Power"] = "malformed" if damage == "malformed" else None
    projection = build(inp)
    player = records(projection, "Pass 4 Players")[0]
    assert player[label] is None and player["Player DKP"] == 1800
    prefix = "Missing" if damage == "missing" else "Invalid"
    expected = (
        prefix + " " + {"Baseline": "baseline", "Start": "start", "End": "end"}[role] + " power"
    )
    assert any(
        r["Issue"] == expected and label in r["Affected Metric"]
        for r in records(projection, "Data Issues")
    )
    assert expected in player["Data Status"]


@pytest.mark.parametrize(
    "mutation", ["cohort", "rank", "context", "revision", "duplicate_powers", "missing_powers"]
)
def test_wrong_or_incomplete_pins_fail_closed(mutation):
    inp = reader_input()
    snapshot = inp[1]
    if mutation == "cohort":
        snapshot["envelope"]["players"].pop()
    elif mutation == "rank":
        snapshot["envelope"]["players"][0]["dkp_rank"] = 2
    elif mutation == "context":
        snapshot["reader_context"]["publication"]["Generation"] += 1
    elif mutation == "revision":
        snapshot["reader_context"]["revisions"]["end"] = START
    elif mutation == "duplicate_powers":
        snapshot["player_powers"].append(snapshot["player_powers"][0])
    else:
        snapshot["player_powers"].pop()
    with pytest.raises(SourceConflict):
        build(inp)


@pytest.mark.parametrize("mutation", ["season", "row", "missing", "count", "hash"])
def test_history_scope_and_integrity_rejected(mutation):
    snap, rows = history()
    if mutation == "season":
        snap = replace(snap, kvk_no=17)
    elif mutation == "row":
        rows[0]["import_status"] = "Rejected"
    elif mutation == "missing":
        rows.pop()
    elif mutation == "count":
        snap = replace(snap, row_count=0)
    else:
        snap = replace(snap, content_hash=b"wrong")
    with pytest.raises(SourceConflict):
        build(history_pair=(snap, rows))


def test_immutable_deterministic_projection_and_fractional_weight_format():
    inp = reader_input()
    inp[1]["weights"]["WeightT4XSource"] = "10.125000"
    first = build(inp)
    saved = first.key
    inp[1]["envelope"]["players"].reverse()
    inp[1]["player_powers"].reverse()
    assert build(inp).key == saved
    inp[1]["envelope"]["players"][0]["name"] = "changed"
    assert first.key == saved
    assert records(first, "DKP Weights")[0]["T4 Kill Weight"] == Decimal("10.125000")
    columns = {c.label: c for c in sheet(first, "Pass 4 Players").columns}
    assert columns["Tanking Score (%)"].number_format == "0.00%"
    assert columns["DKP / Baseline Power"].number_format == '0.00"×"'


def test_configured_no_fight_remains_in_scans_without_empty_reports():
    inp = reader_input()
    inp[1]["reader_context"]["windows"].append(
        dict(
            PeriodID=str(UUID(int=90)),
            PeriodKey="fight:altar2",
            PeriodKind="fight",
            WindowName="2nd Altar",
            WindowSeq=3,
            StartScanID=30,
            EndScanID=30,
            Notes=None,
        )
    )
    projection = build(inp)
    assert records(projection, "Scans")[1]["Status"] == "No fight"
    assert not any("2nd Altar" in s.title for s in projection.sheets)


def test_logical_links_cannot_target_external_or_missing_sheets():
    projection = build()
    bad = replace(projection.sheets[0], links=(ReaderLink(0, 0, "https://invalid"),))
    with pytest.raises(ValueError, match="resolve"):
        replace(projection, sheets=(bad, *projection.sheets[1:]))


def test_large_id_and_zero_absolute_power_remain_distinct_from_blank():
    inp = reader_input()
    largest = 9223372036854775807
    inp[1]["envelope"]["players"][0]["GovernorID"] = largest
    inp[1]["player_powers"][0].update(GovernorID=largest, EndPower=0)
    projection = build(inp)
    row = records(projection, "Pass 4 Players")[0]
    assert row["Governor ID"] == str(largest) and type(row["Governor ID"]) is str
    assert row["End Power"] == 0


def test_selected_no_fight_does_not_create_fighting_sheets():
    projection = build(reader_input(end_scan=10))
    assert not any(s.title.startswith("Pass 4") for s in projection.sheets)
    assert records(projection, "Scans")[0]["Status"] == "No fight"


def test_missing_both_endpoints_does_not_imply_no_fight():
    inp = reader_input()
    inp[1]["reader_context"]["windows"].append(
        dict(
            PeriodID=str(UUID(int=90)),
            PeriodKey="fight:altar2",
            PeriodKind="fight",
            WindowName="2nd Altar",
            WindowSeq=3,
            StartScanID=None,
            EndScanID=None,
            Notes=None,
        )
    )
    scan = records(build(inp), "Scans")[1]
    assert scan["Status"] == "Not published"


def test_fight_called_overall_does_not_substitute_overall_publication():
    inp = reader_input()
    for c in inp[1]["metadata"]["configs"].values():
        c["WindowName"] = "Overall"
    sync(inp[1])
    projection = build(inp)
    assert len([s for s in projection.sheets if s.title == "Overall Players"]) == 2
    assert next(s for s in projection.sheets if s.key == "overall:player").rows == ()


def test_ranking_must_use_complete_cohort_and_unrounded_values():
    inp = reader_input()
    rows = inp[1]["envelope"]["players"]
    rows[0]["dkp"] = Decimal("1.004000")
    rows[1]["dkp"] = Decimal("1.003000")
    projection = build(inp)
    assert [r["Governor ID"] for r in records(projection, "Pass 4 Players")][:2] == ["1001", "1002"]


def test_percent_is_a_fraction_and_kp_loss_is_derived_for_players():
    inp = reader_input()
    inp[1]["envelope"]["players"][0]["healed"] = 10
    row = records(build(inp), "Pass 4 Players")[0]
    assert row["KP Loss"] == 200
    assert row["Tanking Score (%)"] == Decimal("6.666666666667")


def test_precision_guard_rejects_underflow():
    assert not spreadsheet_number(Decimal("1e-308"))


def test_historical_unavailable_ratio_stays_unavailable_without_republication():
    inp = reader_input()
    row = inp[1]["envelope"]["players"][0]
    row.update(dkp_power_ratio=None, dkp_power_ratio_rank=None, dkp_power_ratio_cohort=None)
    states = json.loads(row["FieldStatusJson"])
    states["dkp_power_ratio"] = "invalid_source_value"
    row["FieldStatusJson"] = json.dumps(states)
    assert records(build(inp), "Pass 4 Players")[0]["DKP / Baseline Power"] is None


def test_input_period_order_does_not_change_projection_identity():
    from kvk.services.new_source_export_service import ExportSelection

    fight = reader_input()
    overall = reader_input(overall=True)
    selected = ExportSelection(16, str(UUID(int=81)), str(UUID(int=82)), 7)
    snap = overall[1]
    snap["envelope"]["period_id"] = selected.period_id
    snap["envelope"]["publication"]["PublicationID"] = selected.publication_id
    for cfg in snap["metadata"]["configs"].values():
        cfg.update(PeriodID=selected.period_id, WindowSeq=2)
    sync(snap)
    snap["reader_context"]["windows"] = [deepcopy(snap["metadata"]["configs"]["selected"])]
    overall = selected, snap
    assert build(fight, overall).key == build(overall, fight).key


@pytest.mark.parametrize(
    "field,value",
    [("guild_id", "456"), ("intent_id", BASE), ("kvk_no", 17), ("vector_hash", b"x" * 32)],
)
def test_loader_rejects_wrong_history_scope_before_consuming_periods(monkeypatch, field, value):
    from kvk.dal import new_source_delivery_dal
    from kvk.services.new_source_reader_service import load_reader_projection

    snapshot, _ = history()
    monkeypatch.setattr(
        new_source_delivery_dal,
        "load_reader_export_inputs",
        lambda **kwargs: ({}, replace(snapshot, **{field: value}), None),
    )
    with pytest.raises(SourceConflict, match="authorised request"):
        load_reader_projection(
            connect=None, intent_id=INTENT, kvk_no=16, guild_id="123", expected_hash=b"v" * 32
        )
