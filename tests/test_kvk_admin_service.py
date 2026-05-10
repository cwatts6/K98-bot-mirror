from __future__ import annotations

from datetime import UTC, datetime

from kvk.services import kvk_admin_service


def test_recompute_kvk_windows_returns_resolved_kvk_and_duration(monkeypatch) -> None:
    def fake_recompute(kvk_no: int | None = None) -> int:
        assert kvk_no == 0
        return 17

    monkeypatch.setattr(kvk_admin_service.kvk_admin_dal, "recompute_windows", fake_recompute)

    result = kvk_admin_service.recompute_kvk_windows(0)

    assert result.kvk_no == 17
    assert result.duration_seconds >= 0


def test_list_recent_scans_clamps_limit_and_formats_message(monkeypatch) -> None:
    captured = {}

    def fake_fetch(kvk_no: int | None, limit: int):
        captured["args"] = (kvk_no, limit)
        return 12, [
            {
                "ScanID": 44,
                "ScanTimestampUTC": datetime(2026, 5, 1, 2, 3, 4),
                "Row_Count": 123,
                "ImportedAtUTC": datetime(2026, 5, 1, 2, 5, 6),
                "SourceFileName": "sample.xlsx",
            }
        ]

    monkeypatch.setattr(kvk_admin_service.kvk_admin_dal, "fetch_recent_scans", fake_fetch)

    result = kvk_admin_service.list_recent_scans(12, 500)
    message = kvk_admin_service.format_recent_scans_message(result)

    assert captured["args"] == (12, 100)
    assert result.limit == 100
    assert "KVK 12" in message
    assert "Recent Scans (Top 100)" in message
    assert "sample.xlsx" in message
    assert "44" in message


def test_load_window_preview_detects_bad_ranges_and_formats_table(monkeypatch) -> None:
    rows = [
        {
            "WindowName": "Pass 4",
            "StartScanID": 20,
            "EndScanID": 10,
            "StartTS": datetime(2026, 5, 1, 1, 0),
            "EndTS": datetime(2026, 5, 1, 2, 0),
            "NumScans": 0,
            "RowCount": 5,
        },
        {
            "WindowName": "Full",
            "StartScanID": None,
            "EndScanID": None,
            "StartTS": None,
            "EndTS": None,
            "NumScans": None,
            "RowCount": 7,
        },
    ]

    def fake_fetch(kvk_no: int | None):
        assert kvk_no == 13
        return 13, rows

    monkeypatch.setattr(kvk_admin_service.kvk_admin_dal, "fetch_window_preview", fake_fetch)

    result = kvk_admin_service.load_window_preview(13)
    table = kvk_admin_service.format_window_preview_table(result)

    assert result.kvk_no == 13
    assert result.generated_at_utc.tzinfo is UTC
    assert result.bad_ranges == [rows[0]]
    assert "Pass 4" in table
    assert "Full" in table
    assert "open" in table
