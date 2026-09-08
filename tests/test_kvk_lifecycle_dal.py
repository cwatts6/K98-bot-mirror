from __future__ import annotations

import datetime as dt
from types import SimpleNamespace

import pytest

from kvk.dal import kvk_lifecycle_dal as dal


class _Cursor:
    def __init__(self, fetchall_rows=None) -> None:
        self.executions: list[tuple[str, object | None]] = []
        self.fetchall_rows = list(fetchall_rows or [])

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, sql, params=None):
        self.executions.append((sql, params))

    def fetchall(self):
        return self.fetchall_rows


class _Connection:
    def __init__(self, cursor: _Cursor) -> None:
        self.cursor_obj = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def cursor(self):
        return self.cursor_obj


def _install_connection(monkeypatch, *, fetchall_rows=None) -> _Cursor:
    cursor = _Cursor(fetchall_rows)
    connection = _Connection(cursor)
    monkeypatch.setattr(dal, "get_conn_with_retries", lambda: connection)
    return cursor


def test_latest_details_query_and_named_mapping_are_exact(monkeypatch) -> None:
    cursor = _install_connection(monkeypatch)
    monkeypatch.setattr(
        dal,
        "fetch_one_dict",
        lambda _cursor: {
            "KVK_NO": "16",
            "KVK_NAME": " KVK 16 ",
            "KVK_REGISTRATION_DATE": "2026-08-01",
            "KVK_START_DATE": dt.date(2026, 8, 10),
            "KVK_END_DATE": "2026-09-10T12:00:00",
            "MATCHMAKING_START_DATE": "2026-08-20",
            "FIGHTING_START_DATE": "2026-08-30",
            "NEXT_KVK_NO": 17.0,
            "MATCHMAKING_SCAN": "1059",
            "PASS4_START_SCAN": 1095.0,
            "KVK_END_SCAN": "1205",
        },
    )

    record = dal.fetch_latest_kvk_details_record()

    assert record == dal.KvkLifecycleDetailsRecord(
        kvk_no=16,
        kvk_name=" KVK 16 ",
        registration=dt.date(2026, 8, 1),
        start_date=dt.date(2026, 8, 10),
        end_date=dt.date(2026, 9, 10),
        matchmaking_start_date=dt.date(2026, 8, 20),
        fighting_start_date=dt.date(2026, 8, 30),
        next_kvk_no=17,
        matchmaking_scan=1059,
        pass4_start_scan=1095,
        kvk_end_scan=1205,
    )
    assert cursor.executions == [(dal.LATEST_KVK_DETAILS_SQL, None)]
    assert "FROM dbo.KVK_Details" in dal.LATEST_KVK_DETAILS_SQL
    assert "WHERE KVK_NO IS NOT NULL" in dal.LATEST_KVK_DETAILS_SQL
    assert "ORDER BY KVK_NO DESC" in dal.LATEST_KVK_DETAILS_SQL


def test_latest_details_preserves_positional_and_next_kvk_alias_mapping(monkeypatch) -> None:
    _install_connection(monkeypatch)
    positional_row = {
        "column_0": 16,
        "column_1": "KVK 16",
        "column_2": None,
        "column_3": None,
        "column_4": None,
        "column_5": None,
        "column_6": None,
        "NextKVKNo": "17",
        "column_8": "1059",
        "column_9": "1095",
        "column_10": "1205",
    }
    monkeypatch.setattr(dal, "fetch_one_dict", lambda _cursor: positional_row)

    record = dal.fetch_latest_kvk_details_record()

    assert record is not None
    assert record.kvk_no == 16
    assert record.kvk_name == "KVK 16"
    assert record.next_kvk_no == 17
    assert record.matchmaking_scan == 1059
    assert record.pass4_start_scan == 1095
    assert record.kvk_end_scan == 1205


@pytest.mark.parametrize("row", [None, {}])
def test_latest_details_returns_none_for_absent_row(monkeypatch, row) -> None:
    _install_connection(monkeypatch)
    monkeypatch.setattr(dal, "fetch_one_dict", lambda _cursor: row)

    assert dal.fetch_latest_kvk_details_record() is None


def test_latest_details_maps_malformed_values_to_none(monkeypatch) -> None:
    _install_connection(monkeypatch)
    monkeypatch.setattr(
        dal,
        "fetch_one_dict",
        lambda _cursor: {
            "KVK_NO": "not-an-int",
            "KVK_REGISTRATION_DATE": "not-a-date",
            "NEXT_KVK_NO": object(),
            "MATCHMAKING_SCAN": None,
            "PASS4_START_SCAN": "invalid",
            "KVK_END_SCAN": "",
        },
    )

    record = dal.fetch_latest_kvk_details_record()

    assert record is not None
    assert record.kvk_no is None
    assert record.registration is None
    assert record.next_kvk_no is None
    assert record.matchmaking_scan is None
    assert record.pass4_start_scan is None
    assert record.kvk_end_scan is None


def test_max_scan_query_preserves_named_and_first_value_fallback(monkeypatch) -> None:
    cursor = _install_connection(monkeypatch)
    rows = iter([{"unexpected_alias": "1066"}, {"MaxScanOrder": 1067.0}])
    monkeypatch.setattr(dal, "fetch_one_dict", lambda _cursor: next(rows))

    assert dal.fetch_max_scan_order() == 1066
    assert dal.fetch_max_scan_order() == 1067
    assert cursor.executions == [
        (dal.MAX_SCAN_ORDER_SQL, None),
        (dal.MAX_SCAN_ORDER_SQL, None),
    ]
    assert dal.MAX_SCAN_ORDER_SQL == (
        "SELECT MAX(ScanOrder) AS MaxScanOrder FROM ROK_TRACKER.dbo.kingdomscandata4"
    )


def test_proc_config_window_uses_one_connection_and_exact_parameter_tuple(monkeypatch) -> None:
    cursor = _install_connection(
        monkeypatch,
        fetchall_rows=[
            SimpleNamespace(ConfigKey="MATCHMAKING_SCAN", ConfigValue=1059.0),
            SimpleNamespace(ConfigKey="KVK_END_SCAN", ConfigValue="1205"),
        ],
    )
    monkeypatch.setattr(dal, "fetch_one_dict", lambda _cursor: {"CurrentKVK": 16.0})

    record = dal.fetch_proc_config_window_record()

    assert record == dal.ProcConfigWindowRecord(
        current_kvk=16,
        matchmaking_scan=1059,
        kvk_end_scan=1205,
    )
    assert cursor.executions == [
        (dal.CURRENT_KVK_CONFIG_SQL, None),
        (dal.KVK_WINDOW_CONFIG_SQL, (16,)),
    ]
    assert "WHERE ConfigKey = 'CURRENTKVK3'" in dal.CURRENT_KVK_CONFIG_SQL
    assert "WHERE KVKVersion = ?" in dal.KVK_WINDOW_CONFIG_SQL


def test_proc_config_window_stops_after_missing_current_kvk(monkeypatch) -> None:
    cursor = _install_connection(monkeypatch)
    monkeypatch.setattr(dal, "fetch_one_dict", lambda _cursor: {"CurrentKVK": None})

    record = dal.fetch_proc_config_window_record()

    assert record == dal.ProcConfigWindowRecord(None, None, None)
    assert cursor.executions == [(dal.CURRENT_KVK_CONFIG_SQL, None)]


@pytest.mark.parametrize(
    "reader",
    [
        dal.fetch_latest_kvk_details_record,
        dal.fetch_max_scan_order,
        dal.fetch_proc_config_window_record,
    ],
)
def test_lifecycle_dal_propagates_connection_failures(monkeypatch, reader) -> None:
    def fail_connection():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(dal, "get_conn_with_retries", fail_connection)

    with pytest.raises(RuntimeError, match="database unavailable"):
        reader()
