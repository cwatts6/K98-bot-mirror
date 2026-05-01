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
