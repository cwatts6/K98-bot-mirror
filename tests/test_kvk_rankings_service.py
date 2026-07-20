import csv
from datetime import UTC, datetime
from decimal import Decimal
import io

import pytest

from kvk.models.kvk_rankings import HallOfFameMetric, RankingPayload, RankingRow
from kvk.rendering import kvk_rankings_csv
from kvk.services import kvk_rankings_export_service, kvk_rankings_service
from prekvk.models import PreKvkReportPayload, PreKvkReportRow, PreKvkReportSort
from services import governor_account_service


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
    assert (
        kvk_rankings_service.normalize_current_ranking_metric("kvk", "Kill Points", limit=10)
        == "killpoints"
    )
    assert (
        kvk_rankings_service.normalize_current_ranking_metric("kvk", "heals", limit=10) == "healed"
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
        "killpoints",
        "healed",
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
                "Deads_Delta": 0,
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
                "Deads_Delta": 0,
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
            "Deads_Delta": 0,
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
            "Deads_Delta": 0,
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
            "Deads_Delta": 0,
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
            "Deads_Delta": 0,
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
    kill_points_payload = kvk_rankings_service.build_kvk_rankings_payload_from_rows(
        rows,
        metric="killpoints",
        limit=10,
    )
    healed_payload = kvk_rankings_service.build_kvk_rankings_payload_from_rows(
        rows,
        metric="healed",
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
    assert tanking_payload.rows[0].value == 500
    assert tanking_payload.total_rows == 2
    assert kill_points_payload.metric_label == "Kill Points"
    assert [row.governor_name for row in kill_points_payload.rows] == [
        "NoHeals",
        "Bravo",
        "Alpha",
        "NoKp",
    ]
    assert kill_points_payload.rows[0].value == 12_000
    assert healed_payload.metric_label == "Healed"
    assert [row.governor_name for row in healed_payload.rows] == [
        "NoHeals",
        "Bravo",
        "Alpha",
    ]
    assert healed_payload.rows[0].value == 0


def test_build_kvk_rankings_payload_empty_cache_is_unavailable():
    payload = kvk_rankings_service.build_kvk_rankings_payload_from_rows(
        [], metric="power", limit=10
    )

    assert payload.source_state == "unavailable"
    assert payload.rows == []
    assert "No stats cache" in (payload.empty_message or "")


def test_tanking_and_healed_use_competition_ranks() -> None:
    rows = [
        {
            "GovernorID": str(governor_id),
            "GovernorName": f"G{governor_id}",
            "Starting Power": 100_000_000 - governor_id,
            "T4&T5_Kills": 100,
            "Deads_Delta": 100,
            "HealedTroopsDelta": 10 if governor_id < 3 else 20,
            "KillPointsDelta": 1_000 if governor_id < 3 else 500,
            "STATUS": "INCLUDED",
        }
        for governor_id in (1, 2, 3)
    ]

    tanking = kvk_rankings_service.build_kvk_rankings_payload_from_rows(
        rows, metric="tanking_score", include_all=True
    )
    healed = kvk_rankings_service.build_kvk_rankings_payload_from_rows(
        rows, metric="healed", include_all=True
    )

    assert [row.rank for row in tanking.rows] == [1, 1, 3]
    assert [row.rank for row in healed.rows] == [1, 1, 3]


def test_tanking_and_healed_exclude_missing_but_keep_genuine_zero_values() -> None:
    rows = [
        {
            "GovernorID": "1",
            "GovernorName": "MissingHealed",
            "Starting Power": 50_000_000,
            "T4&T5_Kills": 100,
            "Deads_Delta": 10,
            "KillPointsDelta": 1_000,
            "STATUS": "INCLUDED",
        },
        {
            "GovernorID": "2",
            "GovernorName": "ZeroHealed",
            "Starting Power": 50_000_000,
            "T4&T5_Kills": 100,
            "Deads_Delta": 10,
            "HealedTroopsDelta": 0,
            "KillPointsDelta": 1_000,
            "STATUS": "INCLUDED",
        },
        {
            "GovernorID": "3",
            "GovernorName": "MissingDeads",
            "Starting Power": 50_000_000,
            "T4&T5_Kills": 100,
            "HealedTroopsDelta": 10,
            "KillPointsDelta": 1_000,
            "STATUS": "INCLUDED",
        },
    ]

    tanking = kvk_rankings_service.build_kvk_rankings_payload_from_rows(
        rows, metric="tanking_score", include_all=True
    )
    healed = kvk_rankings_service.build_kvk_rankings_payload_from_rows(
        rows, metric="healed", include_all=True
    )

    assert [row.governor_name for row in tanking.rows] == ["ZeroHealed"]
    assert [row.governor_name for row in healed.rows] == ["ZeroHealed", "MissingDeads"]
    assert healed.rows[0].value == 0


def test_build_kvk_rankings_payload_can_keep_full_internal_rank_set():
    rows = [
        {
            "GovernorID": str(index),
            "GovernorName": f"Player {index}",
            "Starting Power": 50_000_000 + index,
            "T4&T5_Kills": 10_000 - index,
            "STATUS": "INCLUDED",
        }
        for index in range(1, 12)
    ]

    public_payload = kvk_rankings_service.build_kvk_rankings_payload_from_rows(
        rows,
        metric="kills",
        limit=10,
    )
    internal_payload = kvk_rankings_service.build_kvk_rankings_payload_from_rows(
        rows,
        metric="kills",
        limit=10,
        include_all=True,
    )

    assert len(public_payload.rows) == 10
    assert len(internal_payload.rows) == 11
    assert internal_payload.limit == 10
    assert internal_payload.rows[-1].rank == 11
    assert internal_payload.total_rows == 11


def test_current_rankings_csv_export_uses_player_columns_and_safe_cells():
    payload = RankingPayload(
        mode="kvk",
        mode_label="KVK",
        metric="kills",
        metric_label="Kills",
        limit=10,
        generated_at_utc=datetime(2026, 6, 19, 12, 30, 5, tzinfo=UTC),
        freshness_label="2026-06-19 12:00 UTC",
        source_note="+1198_honor.csv",
        filters=("@filter", "STATUS = INCLUDED"),
        total_rows=1,
        rows=[
            RankingRow(
                rank=1,
                governor_id=123,
                governor_name="=Bad\nName",
                value=1000,
                supporting_values={
                    "Power": 100_000_000,
                    "Kills": 1000,
                    "% K/T": 125,
                    "Deads": 50,
                    "DKP": 10_000,
                    "Acclaim": 500,
                    "Tanking Score": 20,
                    "Kill Points": 2000,
                    "KP Loss": 2000,
                    "Healed": 100,
                },
            )
        ],
    )

    export = kvk_rankings_export_service.build_current_rankings_csv_export_from_payload(payload)
    text = export.csv_bytes.getvalue().decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))

    assert export.filename == "kvk_rankings_full_list_kvk_kills_20260619_123005.csv"
    assert export.row_count == 1
    assert list(rows[0]) == [
        "Rank",
        "GovernorID",
        "GovernorName",
        "Power",
        "Kills",
        "PercentKillTarget",
        "Deads",
        "DKP",
        "Acclaim",
        "TankingScore",
        "KillPoints",
        "KPLoss",
        "Healed",
    ]
    assert rows[0]["GovernorID"] == "123"
    assert rows[0]["GovernorName"] == "'=Bad Name"
    assert "SelectedValue" not in rows[0]
    assert rows[0]["PercentKillTarget"] == "125"
    assert rows[0]["TankingScore"] == "20"
    assert rows[0]["KillPoints"] == "2000"
    assert rows[0]["KPLoss"] == "2000"
    assert rows[0]["Healed"] == "100"


def test_current_rankings_csv_headers_are_mode_specific():
    base_kwargs = {
        "metric": "honor",
        "metric_label": "Honor",
        "limit": 10,
        "rows": [],
    }

    honor_headers = kvk_rankings_csv.current_rankings_csv_headers(
        RankingPayload(mode="honor", mode_label="Honor", **base_kwargs)
    )
    prekvk_headers = kvk_rankings_csv.current_rankings_csv_headers(
        RankingPayload(
            mode="prekvk",
            mode_label="PreKvK",
            metric="overall",
            metric_label="Overall",
            limit=10,
            rows=[],
        )
    )

    kvk_headers = kvk_rankings_csv.current_rankings_csv_headers(
        RankingPayload(
            mode="kvk",
            mode_label="KVK",
            metric="kills",
            metric_label="Kills",
            limit=10,
            rows=[],
        )
    )

    assert honor_headers == ("Rank", "GovernorID", "GovernorName", "Honor", "KVK")
    assert kvk_headers == (
        "Rank",
        "GovernorID",
        "GovernorName",
        "Power",
        "Kills",
        "PercentKillTarget",
        "Deads",
        "DKP",
        "Acclaim",
        "TankingScore",
        "KillPoints",
        "KPLoss",
        "Healed",
    )
    assert prekvk_headers == (
        "Rank",
        "GovernorID",
        "GovernorName",
        "Power",
        "Stage1",
        "Stage2",
        "Stage3",
        "Overall",
    )


@pytest.mark.asyncio
async def test_build_current_rankings_csv_export_fetches_full_payload(monkeypatch):
    calls = {}
    payload = RankingPayload(
        mode="prekvk",
        mode_label="PreKvK",
        metric="stage1",
        metric_label="Stage 1",
        limit=25,
        rows=[
            RankingRow(
                rank=1,
                governor_id=456,
                governor_name="Pre",
                value=500,
                supporting_values={"Stage 1": 500},
            )
        ],
    )

    async def fake_payload(**kwargs):
        calls.update(kwargs)
        return payload

    monkeypatch.setattr(kvk_rankings_service, "build_current_rankings_payload", fake_payload)

    export = await kvk_rankings_export_service.build_current_rankings_csv_export(
        mode="prekvk",
        metric="stage1",
        limit=25,
    )

    assert calls == {
        "mode": "prekvk",
        "metric": "stage1",
        "limit": 25,
        "include_all": True,
    }
    assert export.row_count == 1
    assert export.filename.startswith("kvk_rankings_full_list_prekvk_stage1_")


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


@pytest.mark.asyncio
async def test_build_honor_rankings_payload_fetches_internal_lookup_limit(monkeypatch):
    calls = []

    async def fake_honor_top(limit):
        calls.append(limit)
        return [
            {
                "GovernorID": index,
                "GovernorName": f"Honor {index}",
                "HonorPoints": 1000 - index,
            }
            for index in range(12)
        ]

    monkeypatch.setattr(kvk_rankings_service, "get_latest_honor_top", fake_honor_top)

    payload = await kvk_rankings_service.build_honor_rankings_payload(
        limit=10,
        include_all=True,
    )

    assert calls == [kvk_rankings_service.INTERNAL_RANK_LOOKUP_LIMIT]
    assert len(payload.rows) == 12


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


@pytest.mark.asyncio
async def test_build_current_rankings_payload_dispatches_prekvk_full_lookup(monkeypatch):
    calls = {}

    async def fake_report(**kwargs):
        calls.update(kwargs)
        return PreKvkReportPayload(
            kvk_no=17,
            sort_by=PreKvkReportSort.OVERALL,
            limit=3,
            rows=[
                PreKvkReportRow(
                    rank=index,
                    governor_id=index,
                    governor_name=f"Pre {index}",
                    power=50_000_000,
                    stage1_points=0,
                    stage2_points=0,
                    stage3_points=0,
                    overall_points=100 - index,
                )
                for index in range(1, 4)
            ],
        )

    monkeypatch.setattr(
        kvk_rankings_service.report_service,
        "build_prekvk_report_payload",
        fake_report,
    )

    payload = await kvk_rankings_service.build_current_rankings_payload(
        mode="prekvk",
        metric="overall",
        limit=10,
        include_all=True,
    )

    assert calls["limit"] is None
    assert len(payload.rows) == 3
    assert payload.limit == 10


@pytest.mark.asyncio
async def test_build_my_rank_lookup_result_finds_registered_single_account(monkeypatch):
    async def fake_summary(user_id):
        assert user_id == 42
        return governor_account_service.summarize_accounts(
            {
                "Main": {
                    "GovernorID": "123",
                    "GovernorName": "Ranked",
                }
            }
        )

    async def fake_payload(**kwargs):
        assert kwargs == {
            "mode": "kvk",
            "metric": "kills",
            "limit": 10,
            "include_all": True,
        }
        return RankingPayload(
            mode="kvk",
            mode_label="KVK",
            metric="kills",
            metric_label="Kills",
            limit=10,
            total_rows=3,
            rows=[
                RankingRow(rank=1, governor_id=111, governor_name="Ahead", value=100),
                RankingRow(rank=2, governor_id=123, governor_name="Ranked", value=80),
                RankingRow(rank=3, governor_id=222, governor_name="Behind", value=50),
            ],
        )

    monkeypatch.setattr(
        kvk_rankings_service.governor_account_service,
        "get_account_summary_for_user",
        fake_summary,
    )
    monkeypatch.setattr(kvk_rankings_service, "build_current_rankings_payload", fake_payload)

    result = await kvk_rankings_service.build_my_rank_lookup_result(
        discord_user_id=42,
        mode="kvk",
        metric="kills",
        limit=10,
    )

    assert result.status == "found"
    assert result.row is not None
    assert result.row.rank == 2
    assert result.row_above is not None
    assert result.row_above.governor_id == 111
    assert result.row_below is not None
    assert result.row_below.governor_id == 222
    assert result.gap_to_next_value == 20
    assert result.total_rows == 3


@pytest.mark.asyncio
async def test_build_my_rank_lookup_result_prompts_for_multi_account(monkeypatch):
    fetched = False

    async def fake_summary(_user_id):
        return governor_account_service.summarize_accounts(
            {
                "Main": {"GovernorID": "123", "GovernorName": "Main"},
                "Alt": {"GovernorID": "456", "GovernorName": "Alt"},
            }
        )

    async def fake_payload(**_kwargs):
        nonlocal fetched
        fetched = True
        raise AssertionError("payload should not be fetched before account selection")

    monkeypatch.setattr(
        kvk_rankings_service.governor_account_service,
        "get_account_summary_for_user",
        fake_summary,
    )
    monkeypatch.setattr(kvk_rankings_service, "build_current_rankings_payload", fake_payload)

    result = await kvk_rankings_service.build_my_rank_lookup_result(
        discord_user_id=42,
        mode="honor",
    )

    assert fetched is False
    assert result.status == "multi_account"
    assert [choice.governor_id for choice in result.account_choices] == [123, 456]


@pytest.mark.asyncio
async def test_build_my_rank_lookup_result_rejects_unregistered_selected_account(monkeypatch):
    async def fake_summary(_user_id):
        return governor_account_service.summarize_accounts(
            {"Main": {"GovernorID": "123", "GovernorName": "Main"}}
        )

    monkeypatch.setattr(
        kvk_rankings_service.governor_account_service,
        "get_account_summary_for_user",
        fake_summary,
    )

    result = await kvk_rankings_service.build_my_rank_lookup_result(
        discord_user_id=42,
        mode="kvk",
        governor_id="999",
    )

    assert result.status == "not_registered"
    assert "not registered" in result.message


@pytest.mark.asyncio
async def test_build_my_rank_lookup_result_reports_not_ranked_and_missing_data(monkeypatch):
    async def fake_summary(_user_id):
        return governor_account_service.summarize_accounts(
            {"Main": {"GovernorID": "123", "GovernorName": "Main\n`Name` @everyone <@123>"}}
        )

    payloads = [
        RankingPayload(
            mode="prekvk",
            mode_label="PreKvK",
            metric="stage2",
            metric_label="Stage 2",
            limit=25,
            total_rows=1,
            rows=[RankingRow(rank=1, governor_id=999, governor_name="Other", value=50)],
        ),
        RankingPayload(
            mode="prekvk",
            mode_label="PreKvK",
            metric="stage2",
            metric_label="Stage 2",
            limit=25,
            rows=[],
            empty_message="No PreKvK import found.",
        ),
    ]

    async def fake_payload(**kwargs):
        assert kwargs["mode"] == "prekvk"
        assert kwargs["metric"] == "stage2"
        assert kwargs["limit"] == 25
        assert kwargs["include_all"] is True
        return payloads.pop(0)

    monkeypatch.setattr(
        kvk_rankings_service.governor_account_service,
        "get_account_summary_for_user",
        fake_summary,
    )
    monkeypatch.setattr(kvk_rankings_service, "build_current_rankings_payload", fake_payload)

    not_ranked = await kvk_rankings_service.build_my_rank_lookup_result(
        discord_user_id=42,
        mode="prekvk",
        metric="stage2",
        limit=25,
    )
    missing = await kvk_rankings_service.build_my_rank_lookup_result(
        discord_user_id=42,
        mode="prekvk",
        metric="stage2",
        limit=25,
    )

    assert not_ranked.status == "not_ranked"
    assert not_ranked.total_rows == 1
    assert "Main 'Name'" in not_ranked.message
    assert "@everyone" not in not_ranked.message
    assert "<@123>" not in not_ranked.message
    assert missing.status == "unavailable"
    assert missing.message == "No PreKvK import found."


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


def test_hall_of_fame_healed_uses_lower_is_better_label() -> None:
    payload = kvk_rankings_service.build_hall_of_fame_payload_from_rows(
        HallOfFameMetric.HEALED,
        [],
    )

    assert payload.metric_label == "Lowest Healed"
    assert payload.source_note == "Single-KVK performances across finalized KVK outputs"


@pytest.mark.asyncio
async def test_build_hall_of_fame_payload_fetches_dal_rows(monkeypatch):
    calls = {}

    def fake_fetch(metric, finalized_kvks, *, limit):
        calls["metric"] = metric
        calls["finalized_kvks"] = finalized_kvks
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
    monkeypatch.setattr(
        kvk_rankings_service.kvk_history_service,
        "get_finalized_kvks",
        lambda: [12, 15],
    )

    payload = await kvk_rankings_service.build_hall_of_fame_payload(
        metric="honor",
        limit=25,
    )

    assert calls == {
        "metric": HallOfFameMetric.HONOR,
        "finalized_kvks": [12, 15],
        "limit": 10,
    }
    assert payload.rows[0].governor_name == "Bob"
    assert payload.metric_label == "Honor"
    assert payload.limit == 10
    assert payload.total_rows == 18
