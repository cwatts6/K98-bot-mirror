from services import kvk_history_service


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
            "Acclaim": None,
            "HighestAcclaim": None,
            "KvKPlayed": 2,
            "MostKvKKill": 100,
            "MostKvKDead": 5,
            "MostKvKHeal": None,
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
            "KvKPlayed": 3,
            "MostKvKKill": 200,
            "MostKvKDead": 7,
            "MostKvKHeal": None,
        },
    ]

    monkeypatch.setattr(
        kvk_history_service.kvk_history_dal, "get_started_kvks", lambda: [13, 14, 15]
    )
    monkeypatch.setattr(
        kvk_history_service.kvk_history_dal,
        "fetch_modern_history_rows_for_governors",
        lambda ids: rows,
    )

    payload = kvk_history_service.build_kvk_history_payload(2441482)

    assert payload.governor_name == "Tester"
    assert payload.last3_kvks == (13, 14, 15)
    assert [row.kvk_no for row in payload.last3_rows] == [13, 14, 15]
    assert payload.last3_rows[0].row_present is True
    assert payload.last3_rows[0].acclaim is None
    assert payload.last3_rows[1].row_present is False
    assert payload.last3_rows[1].kills is None
    assert payload.last3_rows[2].acclaim == 0
    assert payload.last3_rows[2].kills == large_kills
    assert payload.history_summary["Highest Acclaim"] == 0
    assert payload.trends["rank"].direction == "up"
    assert payload.trends["acclaim"].direction == "insufficient"


def test_history_export_dataframe_uses_expanded_null_preserving_columns(monkeypatch):
    rows = [
        {
            "Gov_ID": 1,
            "Governor_Name": "   A   ",
            "KVK_NO": 15,
            "Kingdom_Rank": 5,
            "KVK_RANK": 3,
            "Acclaim": None,
        }
    ]

    monkeypatch.setattr(
        kvk_history_service.kvk_history_dal,
        "fetch_modern_history_rows_for_governors",
        lambda ids: rows,
    )

    df = kvk_history_service.fetch_history_export_for_governors([1])

    assert list(df.columns) == kvk_history_service.HISTORY_EXPORT_COLUMNS
    assert df.loc[0, "Governor_Name"] == "A"
    assert df.loc[0, "KVK_RANK"] == 3
    assert df.loc[0, "Acclaim"] is None
