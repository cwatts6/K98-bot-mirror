from decimal import Decimal

import pytest

from kvk.models.kvk_rankings import HallOfFameMetric
from kvk.services import kvk_rankings_service
from prekvk.models import PreKvkReportPayload, PreKvkReportRow, PreKvkReportSort


def test_normalize_ranking_limit_allows_primary_limits_only():
    assert kvk_rankings_service.normalize_ranking_limit(10) == 10
    assert kvk_rankings_service.normalize_ranking_limit(25) == 25
    assert kvk_rankings_service.normalize_ranking_limit(50) == 50
    assert kvk_rankings_service.normalize_ranking_limit(100) == 10


def test_normalize_hall_of_fame_limit_is_top_10_only():
    assert kvk_rankings_service.normalize_hall_of_fame_limit(None) == 10
    assert kvk_rankings_service.normalize_hall_of_fame_limit(10) == 10
    assert kvk_rankings_service.normalize_hall_of_fame_limit(25) == 10
    assert kvk_rankings_service.normalize_hall_of_fame_limit(50) == 10


def test_parse_hall_of_fame_metric_accepts_aliases():
    assert kvk_rankings_service.parse_hall_of_fame_metric("kp") == HallOfFameMetric.KILL_POINTS
    assert (
        kvk_rankings_service.parse_hall_of_fame_metric("PreKvK Points") == HallOfFameMetric.PREKVK
    )


def test_normalize_current_ranking_metric_is_mode_aware():
    assert kvk_rankings_service.normalize_current_ranking_metric("kvk", "kills") == "kills"
    assert (
        kvk_rankings_service.normalize_current_ranking_metric("kvk", "% kill target")
        == "pct_kill_target"
    )
    assert kvk_rankings_service.normalize_current_ranking_metric("kvk", None) == "kills"
    assert (
        kvk_rankings_service.normalize_current_ranking_metric("kvk", "power", limit=10) == "kills"
    )
    assert (
        kvk_rankings_service.normalize_current_ranking_metric("kvk", "power", limit=25) == "power"
    )
    assert (
        kvk_rankings_service.normalize_current_ranking_metric("kvk", "acclaim", limit=25) == "kills"
    )
    assert kvk_rankings_service.normalize_current_ranking_metric("honor", "power") == "honor"
    assert kvk_rankings_service.normalize_current_ranking_metric("prekvk", "Stage 2") == "stage2"


def test_current_ranking_metric_labels_are_limit_aware_for_kvk():
    assert list(kvk_rankings_service.current_ranking_metric_labels("kvk", limit=10)) == [
        "kills",
        "pct_kill_target",
        "deads",
        "dkp",
        "acclaim",
        "tanking_score",
    ]
    assert list(kvk_rankings_service.current_ranking_metric_labels("kvk", limit=25)) == [
        "power",
        "kills",
        "pct_kill_target",
        "deads",
        "dkp",
    ]


def test_build_kvk_rankings_payload_filters_sorts_and_preserves_metadata():
    payload = kvk_rankings_service.build_kvk_rankings_payload_from_rows(
        [
            {
                "GovernorID": "1",
                "GovernorName": "LowPower",
                "Starting Power": 30_000_000,
                "T4&T5_Kills": 99_000_000,
                "LAST_REFRESH": "2026-06-18T09:00:00+00:00",
                "STATUS": "INCLUDED",
            },
            {
                "GovernorID": "2",
                "GovernorName": "Alpha",
                "Starting Power": 100_000_000,
                "T4&T5_Kills": 10_000,
                "Acclaim": 5_000,
                "HealedTroopsDelta": 500,
                "KillPointsDelta": 10_000,
                "LAST_REFRESH": "2026-06-18T09:00:00+00:00",
                "STATUS": "INCLUDED",
            },
            {
                "GovernorID": "3",
                "GovernorName": "Bravo",
                "Starting Power": 90_000_000,
                "T4&T5_Kills": 20_000,
                "Acclaim": 4_000,
                "HealedTroopsDelta": 250,
                "KillPointsDelta": 5_000,
                "LAST_REFRESH": "2026-06-18T10:00:00+00:00",
                "STATUS": "INCLUDED",
            },
            {
                "GovernorID": "4",
                "GovernorName": "Excluded",
                "Starting Power": 120_000_000,
                "T4&T5_Kills": 999_000,
                "STATUS": "EXEMPT",
            },
        ],
        metric="kills",
        limit=10,
    )

    assert payload.mode == "kvk"
    assert payload.metric == "kills"
    assert payload.metric_label == "Kills (T4+T5)"
    assert payload.filters == ("STATUS = INCLUDED", "Starting Power >= 40M")
    assert payload.freshness_label == "2026-06-18 10:00 UTC"
    assert payload.total_rows == 2
    assert [row.governor_name for row in payload.rows] == ["Bravo", "Alpha"]
    assert payload.rows[0].supporting_values["Power"] == 90_000_000
    assert payload.rows[0].supporting_values["Acclaim"] == 4_000
    assert payload.rows[0].supporting_values["Tanking Score"] == 100
    assert payload.rows[0].supporting_values["Kill Points"] == 5_000
    assert payload.rows[0].supporting_values["Healed"] == 250


def test_build_kvk_rankings_payload_supports_card_only_metrics():
    rows = [
        {
            "GovernorID": "1",
            "GovernorName": "Alpha",
            "Starting Power": 100_000_000,
            "T4&T5_Kills": 10_000,
            "Acclaim": 9_000,
            "HealedTroopsDelta": 250,
            "KillPointsDelta": 5_000,
            "STATUS": "INCLUDED",
        },
        {
            "GovernorID": "2",
            "GovernorName": "Bravo",
            "Starting Power": 90_000_000,
            "T4&T5_Kills": 20_000,
            "Acclaim": 4_000,
            "HealedTroopsDelta": 100,
            "KillPointsDelta": 10_000,
            "STATUS": "INCLUDED",
        },
        {
            "GovernorID": "3",
            "GovernorName": "NoHeals",
            "Starting Power": 110_000_000,
            "T4&T5_Kills": 30_000,
            "Acclaim": 10_000,
            "HealedTroopsDelta": 0,
            "KillPointsDelta": 12_000,
            "STATUS": "INCLUDED",
        },
        {
            "GovernorID": "4",
            "GovernorName": "NoKp",
            "Starting Power": 120_000_000,
            "T4&T5_Kills": 40_000,
            "Acclaim": 11_000,
            "HealedTroopsDelta": 200,
            "KillPointsDelta": 0,
            "STATUS": "INCLUDED",
        },
    ]

    acclaim_payload = kvk_rankings_service.build_kvk_rankings_payload_from_rows(
        rows,
        metric="acclaim",
        limit=10,
    )
    tanking_payload = kvk_rankings_service.build_kvk_rankings_payload_from_rows(
        rows,
        metric="tanking_score",
        limit=10,
    )

    assert acclaim_payload.metric_label == "Acclaim"
    assert [row.governor_name for row in acclaim_payload.rows] == [
        "NoKp",
        "NoHeals",
        "Alpha",
        "Bravo",
    ]
    assert tanking_payload.metric_label == "Tanking Score"
    assert [row.governor_name for row in tanking_payload.rows] == ["Bravo", "Alpha"]
    assert tanking_payload.rows[0].value == 20
    assert tanking_payload.total_rows == 2


def test_build_kvk_rankings_payload_empty_cache_is_unavailable():
    payload = kvk_rankings_service.build_kvk_rankings_payload_from_rows(
        [], metric="power", limit=10
    )

    assert payload.source_state == "unavailable"
    assert payload.rows == []
    assert "No stats cache" in (payload.empty_message or "")


def test_build_honor_rankings_payload_preserves_scan_context():
    payload = kvk_rankings_service.build_honor_rankings_payload_from_rows(
        [
            {
                "KVK_NO": 17,
                "ScanID": 3,
                "ScanTimestampUTC": "2026-06-18T08:30:00+00:00",
                "SourceFileName": "1198_honor.xlsx",
                "GovernorID": 123,
                "GovernorName": "",
                "HonorPoints": 5000,
            }
        ],
        limit=25,
    )

    assert payload.mode == "honor"
    assert payload.limit == 25
    assert payload.kvk_no == 17
    assert payload.freshness_label == "2026-06-18 08:30 UTC"
    assert payload.rows[0].governor_name == "123"
    assert payload.rows[0].supporting_values["Honor"] == 5000
    assert payload.rows[0].supporting_values["Governor ID"] == "123"
    assert payload.rows[0].supporting_values["KVK"] == 17


def test_build_prekvk_rankings_payload_from_report_uses_report_rows():
    report_payload = PreKvkReportPayload(
        kvk_no=17,
        sort_by=PreKvkReportSort.STAGE2,
        limit=10,
        rows=[
            PreKvkReportRow(
                rank=1,
                governor_id=456,
                governor_name="PrePlayer",
                power=100_000_000,
                stage1_points=10,
                stage2_points=40,
                stage3_points=20,
                overall_points=70,
            )
        ],
        scan_timestamp_utc="2026-06-18T07:00:00+00:00",
        source_filename="prekvk.xlsx",
    )

    payload = kvk_rankings_service.build_prekvk_rankings_payload_from_report(report_payload)

    assert payload.mode == "prekvk"
    assert payload.metric == "stage2"
    assert payload.metric_label == "Stage 2"
    assert payload.kvk_no == 17
    assert payload.freshness_label == "2026-06-18 07:00 UTC"
    assert payload.source_note == "prekvk.xlsx"
    assert payload.total_rows is None
    assert payload.rows[0].value == 40
    assert payload.rows[0].supporting_values["Overall"] == 70


@pytest.mark.asyncio
async def test_build_current_rankings_payload_dispatches_prekvk(monkeypatch):
    async def fake_report(**kwargs):
        assert kwargs["sort_by"] == PreKvkReportSort.STAGE3
        return PreKvkReportPayload(
            kvk_no=17,
            sort_by=PreKvkReportSort.STAGE3,
            limit=10,
            rows=[],
        )

    monkeypatch.setattr(
        kvk_rankings_service.report_service,
        "build_prekvk_report_payload",
        fake_report,
    )

    payload = await kvk_rankings_service.build_current_rankings_payload(
        mode="prekvk",
        metric="stage3",
        limit=100,
    )

    assert payload.mode == "prekvk"
    assert payload.metric == "stage3"
    assert payload.limit == 10


def test_build_hall_of_fame_payload_from_rows_preserves_single_kvk_records():
    rows = [
        {
            "RecordRank": 1,
            "GovernorID": 123,
            "GovernorName": "Alice",
            "KVK_NO": 17,
            "KVK_NAME": "Light vs Dark",
            "MetricValue": Decimal("1234567.00"),
            "TotalRecordsCount": 42,
        },
        {
            "RecordRank": 2,
            "GovernorID": 123,
            "GovernorName": "Alice",
            "KVK_NO": 16,
            "KVK_NAME": "Strife",
            "MetricValue": Decimal("999999.00"),
        },
    ]

    payload = kvk_rankings_service.build_hall_of_fame_payload_from_rows(
        HallOfFameMetric.KILLS,
        rows,
        limit=10,
    )

    assert payload.mode == "records"
    assert payload.metric == "kills"
    assert payload.metric_label == "Kills"
    assert [row.governor_id for row in payload.rows] == [123, 123]
    assert payload.rows[0].kvk_name == "Light vs Dark"
    assert payload.rows[0].value == 1_234_567
    assert payload.total_rows == 42


@pytest.mark.asyncio
async def test_build_hall_of_fame_payload_fetches_dal_rows(monkeypatch):
    calls = {}

    def fake_fetch(metric, *, limit):
        calls["metric"] = metric
        calls["limit"] = limit
        return [
            {
                "RecordRank": 1,
                "GovernorID": 456,
                "GovernorName": "Bob",
                "KVK_NO": 15,
                "MetricValue": 5000,
                "TotalRecordsCount": 18,
            }
        ]

    monkeypatch.setattr(
        kvk_rankings_service.kvk_rankings_dal, "fetch_hall_of_fame_records", fake_fetch
    )

    payload = await kvk_rankings_service.build_hall_of_fame_payload(
        metric="honor",
        limit=25,
    )

    assert calls == {"metric": HallOfFameMetric.HONOR, "limit": 10}
    assert payload.rows[0].governor_name == "Bob"
    assert payload.metric_label == "Honor"
    assert payload.limit == 10
    assert payload.total_rows == 18
