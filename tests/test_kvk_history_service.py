import pytest

from services import kvk_history_service


def test_finalized_kvks_require_output_complete_and_canonical_ended_state(monkeypatch):
    candidates = [
        {
            "KVK_NO": 12,
            "PASS4_START_SCAN": 1000,
            "KVK_END_SCAN": 1200,
            "MaxScanOrder": 1200,
            "FinalOutputState": "OUTPUT_COMPLETE",
        },
        {
            "KVK_NO": 11,
            "PASS4_START_SCAN": 800,
            "KVK_END_SCAN": 999,
            "MaxScanOrder": 1200,
            "FinalOutputState": "OUTPUT_COMPLETE",
        },
        {
            "KVK_NO": 10,
            "PASS4_START_SCAN": 600,
            "KVK_END_SCAN": 799,
            "MaxScanOrder": 1200,
            "FinalOutputState": "PENDING",
        },
    ]
    calls = []

    def fake_candidates(*, limit):
        calls.append(limit)
        return candidates

    monkeypatch.setattr(
        kvk_history_service.kvk_history_dal,
        "fetch_output_complete_kvk_candidates",
        fake_candidates,
    )

    assert kvk_history_service.get_finalized_kvks() == [11]
    assert calls == [20]


def test_normalize_governor_ids_accepts_iterables_and_legacy_strings():
    assert kvk_history_service.normalize_governor_ids(["2", 1, None, "bad", 2]) == [1, 2]
    assert kvk_history_service.normalize_governor_ids("dict_keys([2441482])") == [2441482]


def test_build_ordered_account_map_uses_canonical_slot_order():
    accounts = {
        "Farm 1": {"GovernorID": "300", "GovernorName": "Farm"},
        "Alt 1": {"GovernorID": "200", "GovernorName": "Alt"},
        "Main": {"GovernorID": "100", "GovernorName": "Main"},
    }

    result = kvk_history_service.build_ordered_account_map(accounts)

    assert list(result) == ["Main", "Alt 1", "Farm 1"]
    assert kvk_history_service.pick_default_governor_id(result) == "100"


def test_fetch_history_empty_ids_returns_canonical_schema():
    df = kvk_history_service.fetch_history_for_governors([])

    assert list(df.columns) == kvk_history_service.HISTORY_COLUMNS
    assert df.empty


def test_select_last_started_kvks_uses_latest_started_window():
    assert kvk_history_service.select_last_started_kvks([12, 13, 14, 15]) == (13, 14, 15)
    assert kvk_history_service.select_last_started_kvks([15, "13", "bad", 14]) == (13, 14, 15)


def test_modern_payload_preserves_missing_rows_and_null_metrics(monkeypatch):
    large_kills = 9_007_199_254_740_993
    rows = [
        {
            "Gov_ID": 2441482,
            "Governor_Name": "   Tester   ",
            "KVK_NO": 13,
            "KVK_RANK": 10,
            "Kingdom_Rank": 20,
            "T4T5_Kills": 100,
            "KillPct": 80.0,
            "Deads": 5,
            "DeadPct": 50.0,
            "DKP_SCORE": 1000,
            "DKPPct": 60.0,
            "Acclaim": 10,
            "HighestAcclaim": 10,
            "AutarchTimes": 1,
            "KvKPlayed": 2,
            "MostKvKKill": 100,
            "MostKvKDead": 5,
            "MostKvKHeal": None,
            "HealedTroopsDelta": 100,
            "KillPointsDelta": 200,
            "Max_PreKvk_Points": 800,
            "Max_HonorPoints": 900,
        },
        {
            "Gov_ID": 2441482,
            "Governor_Name": "Tester",
            "KVK_NO": 12,
            "KVK_RANK": 9,
            "Kingdom_Rank": 19,
            "T4T5_Kills": 150,
            "KillPct": 90.0,
            "Deads": 6,
            "DeadPct": 60.0,
            "DKP_SCORE": 1500,
            "DKPPct": 70.0,
            "Acclaim": None,
            "HighestAcclaim": None,
            "AutarchTimes": 1,
            "KvKPlayed": 2,
            "MostKvKKill": 150,
            "MostKvKDead": 6,
            "MostKvKHeal": None,
            "HealedTroopsDelta": 0,
            "KillPointsDelta": 500,
            "Max_PreKvk_Points": 900,
            "Max_HonorPoints": 1000,
        },
        {
            "Gov_ID": 2441482,
            "Governor_Name": "Tester",
            "KVK_NO": 15,
            "KVK_RANK": 8,
            "Kingdom_Rank": 18,
            "T4T5_Kills": str(large_kills),
            "KillPct": 100.0,
            "Deads": 7,
            "DeadPct": 70.0,
            "DKP_SCORE": 2000,
            "DKPPct": 90.0,
            "Acclaim": 0,
            "HighestAcclaim": 0,
            "AutarchTimes": 2,
            "KvKPlayed": 3,
            "MostKvKKill": 200,
            "MostKvKDead": 7,
            "MostKvKHeal": None,
            "HealedTroopsDelta": 120,
            "KillPointsDelta": 600,
            "Max_PreKvk_Points": 1800,
            "Max_HonorPoints": 1900,
        },
    ]

    monkeypatch.setattr(kvk_history_service, "get_finalized_kvks", lambda: [12, 13, 14, 15])
    monkeypatch.setattr(
        kvk_history_service.kvk_history_dal,
        "fetch_modern_history_rows_for_governors",
        lambda ids, finalized: rows,
    )
    monkeypatch.setattr(
        kvk_history_service.kvk_history_dal,
        "fetch_history_summary_metric_ranks",
        lambda gid, finalized: [
            {"Metric": "Highest Acclaim", "KVK_NO": 13, "Overall_Rank": 5},
            {"Metric": "Most Kills", "KVK_NO": 15, "Overall_Rank": 2},
            {"Metric": "Highest Tanking Score", "KVK_NO": 12, "Overall_Rank": 11},
        ],
    )

    payload = kvk_history_service.build_kvk_history_payload(2441482)

    assert payload.governor_name == "Tester"
    assert payload.last3_kvks == (13, 14, 15)
    assert [row.kvk_no for row in payload.last3_rows] == [13, 14, 15]
    assert payload.last3_rows[0].row_present is True
    assert payload.last3_rows[0].acclaim == 10
    assert payload.last3_rows[1].row_present is False
    assert payload.last3_rows[1].kills is None
    assert payload.last3_rows[2].acclaim == 0
    assert payload.last3_rows[2].kills == large_kills
    assert payload.history_summary["Highest Rank"] == 8
    assert payload.history_summary["Autarchs"] == 2
    assert payload.history_summary["KVK Played"] == 3
    assert payload.history_summary["Highest Acclaim"] == 10
    assert payload.history_summary["Most Kills"] == large_kills
    assert payload.history_summary["Most KillPoints"] == 600
    assert payload.history_summary["Most Deads"] == 7
    assert payload.history_summary["Lowest Healed"] == 0
    assert payload.history_summary["Most DKP"] == 2000
    assert payload.history_summary["Highest Tanking Score"] == pytest.approx(500 / 6 * 100)
    assert payload.history_summary["Most Pre-KVK"] == 1800
    assert payload.history_summary["Most Honor"] == 1900
    assert payload.history_summary_metrics["Highest Rank"].kvk_no == 15
    assert payload.history_summary_metrics["Most Kills"].kvk_no == 15
    assert payload.history_summary_metrics["Highest Tanking Score"].kvk_no == 12
    assert payload.history_summary_metrics["Highest Acclaim"].overall_rank == 5
    assert payload.history_summary_metrics["Most Kills"].overall_rank == 2
    assert payload.history_summary_metrics["Highest Tanking Score"].overall_rank == 11
    assert payload.trends["rank"].direction == "up"
    assert payload.trends["acclaim"].direction == "down"
    assert payload.trends["heals"].direction == "down"
    assert payload.trends["kill_points"].direction == "up"
    assert payload.trends["tanking_score"].direction == "down"
    assert payload.trends["tanking_score"].first_value == pytest.approx(500 / 6 * 100)
    assert payload.trends["tanking_score"].last_value == pytest.approx(600 / 2407 * 100)
    assert payload.trends["tanking_score"].value_count == 3


def test_history_export_dataframe_uses_expanded_null_preserving_columns(monkeypatch):
    rows = [
        {
            "Gov_ID": 1,
            "Governor_Name": "   A   ",
            "KVK_NO": 15,
            "Kingdom_Rank": 5,
            "KVK_RANK": 3,
            "Acclaim": None,
            "HealedTroopsDelta": 7,
            "KillPointsDelta": 8,
            "Deads": 1,
        }
    ]

    monkeypatch.setattr(
        kvk_history_service.kvk_history_dal,
        "fetch_modern_history_rows_for_governors",
        lambda ids, finalized: rows,
    )
    monkeypatch.setattr(kvk_history_service, "get_finalized_kvks", lambda: [15])

    df = kvk_history_service.fetch_history_export_for_governors([1])

    assert list(df.columns) == kvk_history_service.HISTORY_EXPORT_COLUMNS
    assert df.loc[0, "Governor_Name"] == "A"
    assert df.loc[0, "KVK_RANK"] == 3
    assert df.loc[0, "Acclaim"] is None
    assert df.loc[0, "HealedTroopsDelta"] == 7
    assert df.loc[0, "KillPointsDelta"] == 8
    assert df.loc[0, "TankingScorePct"] == pytest.approx(8 / 141 * 100)
    assert df.loc[0, "KPLoss"] == 140


def test_history_export_tanking_score_pct_stays_blank_for_missing_or_zero_values():
    df = kvk_history_service.add_history_export_derived_columns(
        kvk_history_service.empty_history_export_frame().assign(
            Gov_ID=[1, 1],
            Governor_Name=["A", "A"],
            KVK_NO=[14, 15],
            HealedTroopsDelta=[None, 0],
            KillPointsDelta=[8, 8],
        )
    )

    assert df["TankingScorePct"].isna().all()
    assert df["KPLoss"].isna().iloc[0]
    assert df.loc[1, "KPLoss"] == 0


def test_payload_keeps_last3_kills_trend_separate_from_all_history(monkeypatch):
    rows = [
        {
            "Gov_ID": 2441482,
            "Governor_Name": "Tester",
            "KVK_NO": 10,
            "T4T5_Kills": 300,
        },
        {
            "Gov_ID": 2441482,
            "Governor_Name": "Tester",
            "KVK_NO": 13,
            "T4T5_Kills": 100,
        },
        {
            "Gov_ID": 2441482,
            "Governor_Name": "Tester",
            "KVK_NO": 14,
            "T4T5_Kills": 200,
        },
        {
            "Gov_ID": 2441482,
            "Governor_Name": "Tester",
            "KVK_NO": 15,
            "T4T5_Kills": 250,
        },
    ]

    monkeypatch.setattr(kvk_history_service, "get_finalized_kvks", lambda: [10, 13, 14, 15])
    monkeypatch.setattr(
        kvk_history_service.kvk_history_dal,
        "fetch_modern_history_rows_for_governors",
        lambda ids, finalized: rows,
    )
    monkeypatch.setattr(
        kvk_history_service.kvk_history_dal,
        "fetch_history_summary_metric_ranks",
        lambda gid, finalized: [],
    )

    payload = kvk_history_service.build_kvk_history_payload(2441482)

    assert payload.trends["kills"].direction == "down"
    assert payload.trends["last3_kills"].direction == "up"


def test_healed_trend_treats_lower_values_as_improved(monkeypatch):
    rows = [
        {
            "Gov_ID": 2441482,
            "Governor_Name": "Tester",
            "KVK_NO": 13,
            "HealedTroopsDelta": 300,
        },
        {
            "Gov_ID": 2441482,
            "Governor_Name": "Tester",
            "KVK_NO": 14,
            "HealedTroopsDelta": 200,
        },
    ]

    monkeypatch.setattr(kvk_history_service, "get_finalized_kvks", lambda: [13, 14])
    monkeypatch.setattr(
        kvk_history_service.kvk_history_dal,
        "fetch_modern_history_rows_for_governors",
        lambda ids, finalized: rows,
    )
    monkeypatch.setattr(
        kvk_history_service.kvk_history_dal,
        "fetch_history_summary_metric_ranks",
        lambda gid, finalized: [],
    )

    payload = kvk_history_service.build_kvk_history_payload(2441482)

    assert payload.trends["heals"].direction == "up"


def test_number_trend_direction_matches_compact_display_precision(monkeypatch):
    rows = [
        {
            "Gov_ID": 2441482,
            "Governor_Name": "Tester",
            "KVK_NO": 13,
            "Deads": 1_080_000,
        },
        {
            "Gov_ID": 2441482,
            "Governor_Name": "Tester",
            "KVK_NO": 14,
            "Deads": 1_120_000,
        },
    ]

    monkeypatch.setattr(kvk_history_service, "get_finalized_kvks", lambda: [13, 14])
    monkeypatch.setattr(
        kvk_history_service.kvk_history_dal,
        "fetch_modern_history_rows_for_governors",
        lambda ids, finalized: rows,
    )
    monkeypatch.setattr(
        kvk_history_service.kvk_history_dal,
        "fetch_history_summary_metric_ranks",
        lambda gid, finalized: [],
    )

    payload = kvk_history_service.build_kvk_history_payload(2441482)

    assert payload.trends["deads"].direction == "flat"
