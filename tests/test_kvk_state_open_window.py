from __future__ import annotations

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
