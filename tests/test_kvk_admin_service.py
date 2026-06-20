from __future__ import annotations

from datetime import UTC, datetime
import logging

import pytest

from kvk.dal import kvk_admin_dal
from kvk.services import kvk_admin_service


def test_normalize_sheet_name_uses_default_for_blank_values() -> None:
    assert kvk_admin_service.normalize_sheet_name("", "Default") == "Default"
    assert kvk_admin_service.normalize_sheet_name("  Custom  ", "Default") == "Custom"


def test_run_export_test_shapes_metadata(monkeypatch) -> None:
    monkeypatch.setattr(kvk_admin_service, "resolve_kvk_no", lambda kvk_no=None: 99)

    def fake_runner(*args):
        assert args[4] == 99
        return {
            "primary": {
                "written_tabs": ["A", "B"],
                "skipped_tabs": ["Empty"],
                "spreadsheet_url": "https://example.invalid/sheet",
            },
            "additional": {
                "PASS4": {
                    "created": True,
                    "written_tabs": ["P4"],
                    "spreadsheet_url": "https://example.invalid/pass4",
                }
            },
        }

    result = kvk_admin_service.run_export_test(
        kvk_no=0,
        sheet_name="KVK",
        server="server",
        database="database",
        username="user",
        password="pass",
        credentials_file="creds.json",
        create_primary=True,
        export_pass4=True,
        export_altar=False,
        export_pass7=False,
        runner=fake_runner,
    )

    assert result.kvk_no == 99
    assert result.sheet_name == "KVK"
    assert result.duration_seconds >= 0
    assert [section.name for section in result.sections] == ["Primary result", "PASS4"]
    assert "Written: 2" in result.sections[0].lines


def test_run_export_all_resolves_kvk_and_invokes_runner(monkeypatch) -> None:
    monkeypatch.setattr(kvk_admin_service, "resolve_kvk_no", lambda kvk_no=None: 42)
    captured = {}

    def fake_runner(*args):
        captured["args"] = args
        return True

    result = kvk_admin_service.run_export_all(
        kvk_no=0,
        sheet_name="KVK",
        server="server",
        database="database",
        username="user",
        password="pass",
        credentials_file="creds.json",
        alert_channel="channel",
        event_loop="loop",
        runner=fake_runner,
    )

    assert result.kvk_no == 42
    assert result.sheet_name == "KVK"
    assert result.ok is True
    assert captured["args"] == (
        "server",
        "database",
        "user",
        "pass",
        42,
        "KVK",
        "creds.json",
        "channel",
        "loop",
    )


@pytest.mark.asyncio
async def test_refresh_stats_caches_reports_partial_failure(caplog) -> None:
    async def build_main():
        return {"_meta": {"count": 10}}

    async def build_last():
        raise RuntimeError("cache unavailable")

    with caplog.at_level(logging.ERROR, logger="kvk.services.kvk_admin_service"):
        result = await kvk_admin_service.refresh_stats_caches(
            build_player_stats_cache=build_main,
            build_lastkvk_player_stats_cache=build_last,
        )
    message = kvk_admin_service.format_cache_refresh_message(result)

    assert result.main.count == 10
    assert result.last_kvk.error == "RuntimeError: cache unavailable"
    assert "Success: Player stats cache refreshed (10 records)" in message
    assert "Warning: Last-KVK cache build failed" in message
    assert "Last-KVK cache refresh failed" in caplog.text
    assert "Traceback" in caplog.text


def test_load_embed_test_context_uses_utc_label_and_checker() -> None:
    captured = {}

    def checker(server, database, username, password):
        captured["args"] = (server, database, username, password)
        return True

    context = kvk_admin_service.load_embed_test_context(
        is_currently_kvk_checker=checker,
        server="server",
        database="database",
        username="user",
        password="pass",
    )

    assert captured["args"] == ("server", "database", "user", "pass")
    assert context.is_kvk is True
    assert context.timestamp_label.endswith(" UTC")


def test_window_preview_sql_brackets_rowcount_alias() -> None:
    assert "AS [RowCount]" in kvk_admin_dal.WINDOW_PREVIEW_SQL
    assert "AS RowCount" not in kvk_admin_dal.WINDOW_PREVIEW_SQL


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


def test_window_preview_table_respects_discord_field_limit() -> None:
    rows = [
        {
            "WindowName": f"Window {index:03d}",
            "StartScanID": index,
            "EndScanID": index + 1,
            "StartTS": datetime(2026, 5, 1, 1, 0),
            "EndTS": datetime(2026, 5, 1, 2, 0),
            "NumScans": 2,
            "RowCount": 1000 + index,
        }
        for index in range(80)
    ]
    result = kvk_admin_service.KvkWindowPreviewResult(
        kvk_no=13,
        rows=rows,
        bad_ranges=[],
        generated_at_utc=datetime(2026, 5, 1, tzinfo=UTC),
    )

    table = kvk_admin_service.format_window_preview_table(result)

    assert len(table) <= kvk_admin_service.DISCORD_EMBED_FIELD_VALUE_LIMIT
    assert table.startswith("```\n")
    assert table.endswith("\n```")
    assert "... truncated ..." in table
