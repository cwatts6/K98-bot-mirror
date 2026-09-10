"""Synthetic S4A consumer contracts; no SQL connections or external deliveries."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from kvk.dal import kvk_admin_dal, new_source_reporting_dal
from kvk.dal.new_source_import_dal import SourceConflict
from kvk.dal.new_source_publication_dal import result_values
from kvk.schemas.new_source_schema import SOURCE_KEY
from kvk.services import new_source_reporting_service as service
from kvk.services.new_source_calculation import calculate_period
from kvk.services.new_source_window_resolver import resolve_window
from tests.kvk_source_fixtures import calculation_config, worked_calculation_inputs

PERIOD = "00000000-0000-0000-0000-000000000001"
PUBLICATION = "00000000-0000-0000-0000-000000000002"


def source_inputs(*, end_scan=13, desired_end=None, overall=False, aggregate=True):
    b0, start, middle, end = worked_calculation_inputs()
    config = calculation_config(end_scan_id=end_scan)
    calculation = calculate_period(resolve_window(config, (start, middle, end)), b0)
    no_fight = end_scan == 10
    state = calculation.selection.player_state.value
    window = dict(
        SourceKey=SOURCE_KEY,
        KVK_NO=16,
        PeriodKey="overall" if overall else "fight:pass4",
        PeriodKind="overall" if overall else "fight",
        WindowName="Overall" if overall else "Pass 4",
        StartScanID=10,
        EndScanID=end_scan,
    )
    pub = dict(
        PublicationID=PUBLICATION,
        Generation=4,
        ConfigVersionID="c1",
        PeriodKey=window["PeriodKey"],
        StartScanID=10,
        EndScanID=calculation.selection.end.logical_scan_id,
        PlayerState=state,
        PeriodState="live",
        AggregateState="not_applicable" if no_fight else "final" if aggregate else "not_received",
        EligibleCount=4,
        RosterID="b0",
        CalculationVersion="v1",
        AggregateRevisionID="a1" if aggregate and not no_fight else None,
    )

    def agg(camp, kingdom=None):
        row = dict(CampID=camp, CampLabel=f"Camp {camp}", Kingdom=kingdom)
        for key in ("t4_kills", "t5_kills", "kp_t4_t5", "dead", "healed", "acclaim", "dkp"):
            row.update(
                {
                    key: Decimal("25300000"),
                    key + "_raw": "25.3M",
                    key + "_unit": Decimal("100000"),
                    key + "_precision": "reported_abbreviated",
                }
            )
        return row

    mapping = [dict(Kingdom=k, CampID=c, CampName=n) for k, c, n in config.mapping.entries]
    selected_end = calculation.selection.end.scan_start_utc
    meta = dict(
        configs=dict(
            selected=window,
            requested=dict(window, EndScanID=desired_end) if desired_end is not None else window,
        ),
        endpoints=dict(
            start=dict(ScanStartUTC=start.scan_start_utc), end=dict(ScanStartUTC=selected_end)
        ),
        camps=mapping,
        aggregate=(
            dict(
                CoverageStartUTC=start.scan_start_utc,
                CoverageEndUTC=selected_end,
                AsOfUTC=datetime(2026, 9, 9, tzinfo=UTC),
            )
            if aggregate and not no_fight
            else None
        ),
    )
    envelope = dict(
        source_key=SOURCE_KEY,
        kvk_no=16,
        period_id=PERIOD,
        publication=pub,
        selection=dict(SelectionVersion=7),
        desired_config_id="c2" if desired_end is not None else "c1",
        is_current=desired_end is None,
        current_period_state="missing_configuration" if desired_end is not None else "live",
        players=[result_values(p) for p in calculation.players],
        aggregates=dict(
            SourceKingdomReportRow=(
                [agg(mapping[0]["CampID"], mapping[0]["Kingdom"])]
                if aggregate and not no_fight
                else []
            ),
            SourceCampReportRow=[agg(mapping[0]["CampID"])] if aggregate and not no_fight else [],
        ),
    )
    return envelope, meta


def load_synthetic(monkeypatch, **options):
    envelope, meta = source_inputs(**options)
    loader = Mock(return_value=envelope)
    monkeypatch.setattr(new_source_reporting_dal, "load_snapshot", loader)
    monkeypatch.setattr(kvk_admin_dal, "fetch_source_report_metadata", lambda *args: meta)
    report = service.load_report_v2(
        connect=Mock(side_effect=AssertionError("SQL forbidden")),
        kvk_no=16,
        period_id=PERIOD,
        our_kingdom=meta["camps"][0]["Kingdom"],
    )
    return report, loader, envelope, meta


def test_t35_t39_t52_all_blocks_one_snapshot_and_supplied_precision(monkeypatch):
    report, loader, envelope, _ = load_synthetic(monkeypatch)
    assert tuple(report["blocks"]) == service.BLOCK_KEYS
    loader.assert_called_once()
    assert report["blocks"]["camps_by_dkp"][0]["dkp"] == Decimal("25300000")
    assert report["blocks"]["camps_by_dkp"][0]["reported"]["dkp"]["raw"] == "25.3M"
    assert report["blocks"]["camps_by_dkp"][0]["kp_gain"] is None
    assert report["blocks"]["camps_by_dkp"][0]["states"]["kp_gain"] == "unsupported"
    assert report["aggregate_as_of_utc"] != report["player_end_utc"]
    envelope["publication"]["Generation"] = 5
    assert report["generation"] == 4


def test_b0_missing_zero_and_selected_cohort(monkeypatch):
    report, _, envelope, _ = load_synthetic(monkeypatch)
    assert len(report["players"]) == report["eligible_count"] == 4
    missing = [p for p in report["players"] if p["dkp"] is None]
    assert missing and missing[0]["states"]["dkp"] != "available"
    ranked = report["blocks"]["players_by_dkp"]
    assert any(p["dkp"] == 0 for p in ranked)
    assert all(p["population"] == len(ranked) for p in ranked)
    assert {r["governor_id"] for r in report["players"]} == {
        r["GovernorID"] for r in envelope["players"]
    }


@pytest.mark.parametrize("end_scan", [None, 13, 14, 10])
def test_endpoint_states_and_equal_endpoint_scores(monkeypatch, end_scan):
    report, _, _, _ = load_synthetic(monkeypatch, end_scan=end_scan)
    if end_scan == 10:
        assert all(p["dkp"] == 0 for p in report["players"])
        assert all(p["rank"] is None for p in report["blocks"]["players_by_dkp"])
        assert report["aggregate_state"] == "not_applicable"
        assert report["blocks"]["camps_by_dkp"] == []
    elif end_scan == 13:
        assert report["player_state"] == "final"
    else:
        assert report["player_state"] == "live"
        assert report["endpoint_pending"]


def test_t70_pending_endpoint_never_current_final(monkeypatch):
    report, _, _, _ = load_synthetic(monkeypatch, desired_end=14)
    assert not report["is_current"]
    assert report["requested_end_scan_id"] == 14
    assert report["selected_end_scan_id"] == 13
    assert report["current_period_state"] == "missing_configuration"


def test_t36_t37_overall_stays_independent(monkeypatch):
    report, _, _, _ = load_synthetic(monkeypatch, overall=True, aggregate=False)
    assert report["period_key"] == "overall"
    assert report["aggregate_state"] == "not_received"
    assert report["blocks"]["kingdoms_by_dkp"] == []
    assert report["players"]


def test_no_publication_and_wrong_scope_fail_without_legacy(monkeypatch):
    monkeypatch.setattr(
        new_source_reporting_dal,
        "load_snapshot",
        lambda **kw: dict(source_key=SOURCE_KEY, kvk_no=16, period_id=PERIOD, publication=None),
    )
    report = service.load_report_v2(connect=Mock(), kvk_no=16, period_id=PERIOD, our_kingdom=98)
    assert report["schema_version"] == 2 and report["publication_id"] is None
    with pytest.raises(SourceConflict, match="publication changed"):
        service.load_report_v2(
            connect=Mock(), kvk_no=16, period_id=PERIOD, our_kingdom=98, publication_id=PUBLICATION
        )


def test_high_precision_ranking_does_not_round():
    a = dict(governor_id=2, dkp=Decimal("10000000000000000000000000000.000002"))
    b = dict(governor_id=1, dkp=Decimal("10000000000000000000000000000.000001"))
    assert service._ranked([a, b], "dkp", "governor_id")[0]["governor_id"] == 2


def test_admin_source_diagnostics_never_recompute_or_retarget(monkeypatch):
    from kvk.services import kvk_admin_service

    report, _, _, _ = load_synthetic(monkeypatch, desired_end=14)
    monkeypatch.setattr(
        kvk_admin_dal, "recompute_windows", Mock(side_effect=AssertionError("writes forbidden"))
    )
    diagnostic = kvk_admin_service.load_source_diagnostic(
        action="recompute", connect=Mock(), kvk_no=16, period_id=PERIOD
    )
    assert diagnostic["publication_id"] == report["publication_id"]
    assert diagnostic["requested_end_scan_id"] == 14
    assert "players" not in diagnostic
