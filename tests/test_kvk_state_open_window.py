from __future__ import annotations

import logging
from types import SimpleNamespace

from kvk.dal import kvk_lifecycle_dal
import kvk_state
from kvk_state import (
    get_kvk_context_today,
    get_kvk_fighting_context_today,
    is_scan_within_open_window,
    resolve_kvk_fighting_state,
    resolve_kvk_scan_state,
)
import stats_alerts.kvk_meta as kvk_meta


def test_open_ended_fighting_window_is_active() -> None:
    state, reason = resolve_kvk_fighting_state(
        pass4_start_scan=866,
        kvk_end_scan=None,
        max_scan_order=875,
    )

    assert state == "ACTIVE"
    assert reason == "max_scan_order_within_fighting_window"
    assert is_scan_within_open_window(866, None, 875) is True


def test_known_end_fighting_window_is_active() -> None:
    state, _reason = resolve_kvk_fighting_state(
        pass4_start_scan=866,
        kvk_end_scan=900,
        max_scan_order=875,
    )

    assert state == "ACTIVE"
    assert is_scan_within_open_window(866, 900, 875) is True


def test_before_pass4_is_draft() -> None:
    state, reason = resolve_kvk_fighting_state(
        pass4_start_scan=866,
        kvk_end_scan=None,
        max_scan_order=850,
    )

    assert state == "DRAFT"
    assert reason == "max_scan_order_before_pass4_start_scan"
    assert is_scan_within_open_window(866, None, 850) is False


def test_after_known_end_is_ended() -> None:
    state, reason = resolve_kvk_fighting_state(
        pass4_start_scan=866,
        kvk_end_scan=900,
        max_scan_order=901,
    )

    assert state == "ENDED"
    assert reason == "max_scan_order_after_kvk_end_scan"
    assert is_scan_within_open_window(866, 900, 901) is False


def test_missing_pass4_is_draft() -> None:
    state, reason = resolve_kvk_fighting_state(
        pass4_start_scan=None,
        kvk_end_scan=None,
        max_scan_order=875,
    )

    assert state == "DRAFT"
    assert reason == "invalid_pass4_start_scan"
    assert is_scan_within_open_window(None, None, 875) is False


def test_fighting_state_boundaries_are_unchanged() -> None:
    assert (
        resolve_kvk_fighting_state(
            pass4_start_scan=866,
            kvk_end_scan=900,
            max_scan_order=865,
        )[0]
        == "DRAFT"
    )
    assert (
        resolve_kvk_fighting_state(
            pass4_start_scan=866,
            kvk_end_scan=900,
            max_scan_order=866,
        )[0]
        == "ACTIVE"
    )
    assert (
        resolve_kvk_fighting_state(
            pass4_start_scan=866,
            kvk_end_scan=900,
            max_scan_order=900,
        )[0]
        == "ACTIVE"
    )
    assert (
        resolve_kvk_fighting_state(
            pass4_start_scan=866,
            kvk_end_scan=900,
            max_scan_order=901,
        )[0]
        == "ENDED"
    )


def test_legacy_resolver_adapter_matches_explicit_fighting_resolver() -> None:
    inputs = {
        "pass4_start_scan": 866,
        "kvk_end_scan": 900,
        "max_scan_order": 875,
    }

    assert resolve_kvk_scan_state(**inputs) == resolve_kvk_fighting_state(**inputs)


def test_legacy_context_adapter_preserves_original_key_shape(monkeypatch) -> None:
    monkeypatch.setattr(
        kvk_state,
        "get_latest_kvk_details",
        lambda today=None: {
            "kvk_no": 16,
            "kvk_name": "KVK 16",
            "registration": None,
            "start_date": None,
            "end_date": None,
            "matchmaking_scan": 1059,
            "kvk_end_scan": 1205,
            "matchmaking_start_date": None,
            "fighting_start_date": None,
            "pass4_start_scan": 1095,
            "next_kvk_no": 17,
            "max_scan_order": 1066,
            "state": "DRAFT",
            "state_reason": "max_scan_order_before_pass4_start_scan",
        },
    )

    fighting = get_kvk_fighting_context_today()
    legacy = get_kvk_context_today()

    assert fighting is not None
    assert fighting["fighting_state"] == "DRAFT"
    assert fighting["fighting_state_reason"] == "max_scan_order_before_pass4_start_scan"
    assert "state" not in fighting
    assert legacy is not None
    assert legacy["state"] == fighting["fighting_state"]
    assert legacy["state_reason"] == fighting["fighting_state_reason"]
    assert "fighting_state" not in legacy


def test_stats_alerts_fighting_gate_allows_null_end_scan(monkeypatch) -> None:
    monkeypatch.setattr(
        kvk_meta,
        "get_kvk_fighting_context_today",
        lambda: {
            "kvk_no": 15,
            "matchmaking_scan": 837,
            "pass4_start_scan": 866,
            "kvk_end_scan": None,
            "max_scan_order": 875,
            "fighting_state": "ACTIVE",
            "fighting_state_reason": "max_scan_order_within_fighting_window",
        },
    )

    assert kvk_meta.is_kvk_fighting_open() is True


class _KvkCursor:
    sql = ""

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, sql, *_params):
        self.sql = sql


class _KvkConn:
    cursor_obj = _KvkCursor()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def cursor(self):
        return self.cursor_obj


def test_latest_kvk_details_filters_null_kvk_no(monkeypatch) -> None:
    conn = _KvkConn()
    monkeypatch.setattr(kvk_lifecycle_dal, "get_conn_with_retries", lambda: conn)
    monkeypatch.setattr(kvk_lifecycle_dal, "fetch_one_dict", lambda _cur: None)

    assert kvk_state.get_latest_kvk_details() is None
    assert "WHERE KVK_NO IS NOT NULL" in conn.cursor_obj.sql


def test_latest_kvk_details_returns_none_for_invalid_kvk_no(monkeypatch) -> None:
    monkeypatch.setattr(kvk_lifecycle_dal, "get_conn_with_retries", lambda: _KvkConn())
    monkeypatch.setattr(kvk_lifecycle_dal, "fetch_one_dict", lambda _cur: {"KVK_NO": None})

    assert kvk_state.get_latest_kvk_details() is None


def test_latest_kvk_details_preserves_sql_failure_warning(monkeypatch, caplog) -> None:
    def fail_read():
        raise RuntimeError("details unavailable")

    monkeypatch.setattr(kvk_lifecycle_dal, "fetch_latest_kvk_details_record", fail_read)

    with caplog.at_level(logging.WARNING, logger=kvk_state.log.name):
        assert kvk_state.get_latest_kvk_details() is None

    assert "[kvk_state] Could not read dbo.KVK_Details: details unavailable" in caplog.messages


def test_max_scan_order_preserves_sql_failure_warning(monkeypatch, caplog) -> None:
    def fail_read():
        raise RuntimeError("scan unavailable")

    monkeypatch.setattr(kvk_lifecycle_dal, "fetch_max_scan_order", fail_read)

    with caplog.at_level(logging.WARNING, logger=kvk_state.log.name):
        assert kvk_state._get_max_scan_order() is None

    assert "[kvk_state] Could not read max ScanOrder: scan unavailable" in caplog.messages


def test_proc_config_window_preserves_sql_failure_warning(monkeypatch, caplog) -> None:
    def fail_read():
        raise RuntimeError("config unavailable")

    monkeypatch.setattr(kvk_lifecycle_dal, "fetch_proc_config_window_record", fail_read)

    with caplog.at_level(logging.WARNING, logger=kvk_state.log.name):
        assert kvk_state._get_proc_config_window(max_scan_order=1066) is None

    assert "[kvk_state] Could not read ProcConfig KVK window: config unavailable" in caplog.messages


def test_latest_kvk_details_preserves_operational_log_message(monkeypatch, caplog) -> None:
    rows = iter(
        [
            {
                "KVK_NO": 16,
                "KVK_NAME": "KVK 16",
                "KVK_REGISTRATION_DATE": None,
                "KVK_START_DATE": None,
                "KVK_END_DATE": None,
                "MATCHMAKING_START_DATE": None,
                "FIGHTING_START_DATE": None,
                "NEXT_KVK_NO": 17,
                "MATCHMAKING_SCAN": 1059,
                "PASS4_START_SCAN": 1095,
                "KVK_END_SCAN": 1205,
            },
            {"MaxScanOrder": 1066},
        ]
    )
    monkeypatch.setattr(kvk_lifecycle_dal, "get_conn_with_retries", lambda: _KvkConn())
    monkeypatch.setattr(kvk_lifecycle_dal, "fetch_one_dict", lambda _cur: next(rows))

    with caplog.at_level(logging.INFO, logger=kvk_state.log.name):
        details = kvk_state.get_latest_kvk_details()

    assert details is not None
    assert (
        "[kvk_state] resolved KVK state kvk_no=16 matchmaking_scan=1059 "
        "pass4_start_scan=1095 kvk_end_scan=1205 max_scan_order=1066 "
        "resolved_state=DRAFT reason=max_scan_order_before_pass4_start_scan" in caplog.messages
    )
    assert "resolved KVK fighting state" not in caplog.text


def test_kvk_window_uses_proc_config_fallback_for_missing_detail_scans(monkeypatch) -> None:
    class _ProcConfigCursor(_KvkCursor):
        def fetchall(self):
            return [
                SimpleNamespace(ConfigKey="MATCHMAKING_SCAN", ConfigValue="837"),
                SimpleNamespace(ConfigKey="KVK_END_SCAN", ConfigValue="900"),
            ]

    class _ProcConfigConn(_KvkConn):
        cursor_obj = _ProcConfigCursor()

    monkeypatch.setattr(
        kvk_state,
        "get_latest_kvk_details",
        lambda: {
            "kvk_no": 15,
            "matchmaking_scan": None,
            "kvk_end_scan": None,
            "pass4_start_scan": None,
            "max_scan_order": 875,
        },
    )
    monkeypatch.setattr(kvk_lifecycle_dal, "get_conn_with_retries", lambda: _ProcConfigConn())
    monkeypatch.setattr(kvk_lifecycle_dal, "fetch_one_dict", lambda _cur: {"CurrentKVK": 15})

    window = kvk_state.get_kvk_window_with_fallback()

    assert window is not None
    assert window["source"] == "ProcConfig"
    assert window["kvk_no"] == 15
    assert window["matchmaking_scan"] == 837
    assert window["kvk_end_scan"] == 900
    assert window["max_scan_order"] == 875


def test_stats_alerts_currently_kvk_uses_fallback_window(monkeypatch) -> None:
    monkeypatch.setattr(
        kvk_meta,
        "get_kvk_window_with_fallback",
        lambda: {
            "kvk_no": 15,
            "matchmaking_scan": 837,
            "kvk_end_scan": 900,
            "pass4_start_scan": None,
            "max_scan_order": 875,
            "source": "ProcConfig",
        },
    )

    assert kvk_meta.is_currently_kvk() is True
