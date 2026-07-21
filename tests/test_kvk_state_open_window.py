from __future__ import annotations

from types import SimpleNamespace

import kvk_state
from kvk_state import is_scan_within_open_window, resolve_kvk_scan_state
import stats_alerts.kvk_meta as kvk_meta


def test_open_ended_fighting_window_is_active() -> None:
    state, reason = resolve_kvk_scan_state(
        pass4_start_scan=866,
        kvk_end_scan=None,
        max_scan_order=875,
    )

    assert state == "ACTIVE"
    assert reason == "max_scan_order_within_fighting_window"
    assert is_scan_within_open_window(866, None, 875) is True


def test_known_end_fighting_window_is_active() -> None:
    state, _reason = resolve_kvk_scan_state(
        pass4_start_scan=866,
        kvk_end_scan=900,
        max_scan_order=875,
    )

    assert state == "ACTIVE"
    assert is_scan_within_open_window(866, 900, 875) is True


def test_before_pass4_is_draft() -> None:
    state, reason = resolve_kvk_scan_state(
        pass4_start_scan=866,
        kvk_end_scan=None,
        max_scan_order=850,
    )

    assert state == "DRAFT"
    assert reason == "max_scan_order_before_pass4_start_scan"
    assert is_scan_within_open_window(866, None, 850) is False


def test_after_known_end_is_ended() -> None:
    state, reason = resolve_kvk_scan_state(
        pass4_start_scan=866,
        kvk_end_scan=900,
        max_scan_order=901,
    )

    assert state == "ENDED"
    assert reason == "max_scan_order_after_kvk_end_scan"
    assert is_scan_within_open_window(866, 900, 901) is False


def test_missing_pass4_is_draft() -> None:
    state, reason = resolve_kvk_scan_state(
        pass4_start_scan=None,
        kvk_end_scan=None,
        max_scan_order=875,
    )

    assert state == "DRAFT"
    assert reason == "invalid_pass4_start_scan"
    assert is_scan_within_open_window(None, None, 875) is False


def test_stats_alerts_fighting_gate_allows_null_end_scan(monkeypatch) -> None:
    monkeypatch.setattr(
        kvk_meta,
        "get_kvk_context_today",
        lambda: {
            "kvk_no": 15,
            "matchmaking_scan": 837,
            "pass4_start_scan": 866,
            "kvk_end_scan": None,
            "max_scan_order": 875,
            "state": "ACTIVE",
            "state_reason": "max_scan_order_within_fighting_window",
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
    monkeypatch.setattr(kvk_state, "get_conn_with_retries", lambda: conn)
    monkeypatch.setattr(kvk_state, "fetch_one_dict", lambda _cur: None)

    assert kvk_state.get_latest_kvk_details() is None
    assert "WHERE KVK_NO IS NOT NULL" in conn.cursor_obj.sql


def test_latest_kvk_details_returns_none_for_invalid_kvk_no(monkeypatch) -> None:
    monkeypatch.setattr(kvk_state, "get_conn_with_retries", lambda: _KvkConn())
    monkeypatch.setattr(kvk_state, "fetch_one_dict", lambda _cur: {"KVK_NO": None})

    assert kvk_state.get_latest_kvk_details() is None


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
    monkeypatch.setattr(kvk_state, "get_conn_with_retries", lambda: _ProcConfigConn())
    monkeypatch.setattr(kvk_state, "fetch_one_dict", lambda _cur: {"CurrentKVK": 15})

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
