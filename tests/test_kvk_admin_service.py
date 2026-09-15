from __future__ import annotations

from datetime import UTC, datetime
import logging

import pytest

from kvk.dal import kvk_admin_dal
from kvk.services import kvk_admin_service


def test_legacy_manual_export_is_queued_without_calling_old_runner(monkeypatch):
    from unittest.mock import Mock

    from services.legacy_export_snapshot_service import use_runtime

    runtime, runner = Mock(), Mock(side_effect=AssertionError("old exporter"))
    runtime.submit.return_value = "exact-job"
    monkeypatch.setattr(
        kvk_admin_dal, "read_admin_source", lambda _: {"KVK_NO": 7, "SourceKey": "legacy_full_data"}
    )
    with use_runtime(runtime):
        result = kvk_admin_service.run_export_all(
            kvk_no=7,
            sheet_name="KVK LIST",
            server="",
            database="",
            username="",
            password="",
            credentials_file="",
            alert_channel=None,
            event_loop=None,
            runner=runner,
        )
    assert result.job_id == "exact-job" and result.ok is False
    runtime.validate_destination.assert_called_once_with(kvk_no=7, sheet_name="KVK LIST")
    runner.assert_not_called()


def test_ordinary_export_all_dispatches_new_source_to_operator_service(monkeypatch):
    from unittest.mock import Mock

    from kvk.services import source_export_operator_service as operator
    from kvk.services.new_source_admin_service import SourceActor

    actor = SourceActor(1, 2, 3, frozenset())
    service = Mock()
    service.export.return_value = dict(job_id="exact-source-job", state="confirmed")
    monkeypatch.setattr(operator, "configured_operator_service", lambda: service)
    monkeypatch.setattr(
        kvk_admin_dal,
        "read_admin_source",
        lambda _: dict(KVK_NO=16, SourceKey="snapshot_report_v1"),
    )
    runner = Mock(side_effect=AssertionError("No legacy exporter"))
    result = kvk_admin_service.run_export_all(
        kvk_no=16,
        sheet_name="legacy title",
        server="",
        database="",
        username="",
        password="",
        credentials_file="",
        alert_channel=None,
        event_loop=None,
        runner=runner,
        actor=actor,
    )
    assert result.job_id == "exact-source-job" and result.ok is True
    service.export.assert_called_once_with(actor, 16)
    runner.assert_not_called()


def test_normalize_sheet_name_uses_default_for_blank_values() -> None:
    assert kvk_admin_service.normalize_sheet_name("", "Default") == "Default"
    assert kvk_admin_service.normalize_sheet_name("  Custom  ", "Default") == "Custom"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "action", ["status", "resume", "accept", "finalize", "correct", "configure", "roster"]
)
async def test_source_group_registers_real_options_and_private_service_handoff(monkeypatch, action):
    roster_mode = action == "roster"
    action = "configure" if roster_mode else action
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, Mock

    from commands import stats_cmds
    from kvk.services import new_source_admin_service as source
    from tests.test_kvk_source_admin import ACCESS
    from tests.test_kvk_source_import_view import interaction

    groups = []
    bot = SimpleNamespace(
        add_application_command=groups.append, slash_command=lambda **kw: lambda fn: fn
    )
    monkeypatch.setattr(stats_cmds, "track_usage", lambda: lambda fn: fn)
    stats_cmds.register_stats(bot)
    group = next(g for g in groups if g.name == "kvk_admin")
    command = next(c for c in group.subcommands if c.name == "source")
    options = {o["name"]: o for o in command.to_dict()["options"]}
    assert [choice["value"] for choice in options["action"]["choices"]] == list(source.ACTIONS)
    assert not options["receipt"]["required"]
    assert options["file_1"]["type"] == options["file_2"]["type"] == 11
    assert not options["review"]["required"]
    assert options["expected_revision_version"]["type"] == 4
    assert options["roster_correction"]["type"] == 5
    assert len(options) <= 25
    assert command.callback.__version__ == "v1.01"
    assert len(group.subcommands) == 8
    row = {
        "AttemptID": "00000000-0000-4000-8000-000000000001",
        "ActorID": "10",
        "Status": "received",
        "payload": {"version": 1, "candidate": {}},
    }
    service = SimpleNamespace(
        access=ACCESS,
        receipt=Mock(return_value=row),
        roster_preview=Mock(return_value=row),
        summary=lambda r: "Private receipt",
    )
    monkeypatch.setattr(source, "access_from_config", lambda: ACCESS)
    monkeypatch.setattr(source, "configured_service", lambda: service)
    monkeypatch.setattr(stats_cmds, "safe_defer", AsyncMock(return_value=True))
    inter = interaction()
    inter.data = {
        "options": [
            {"name": "action", "type": 3, "value": action},
            {"name": "receipt", "type": 3, "value": row["AttemptID"]},
        ]
    }
    if roster_mode:
        inter.data["options"].append({"name": "roster_correction", "type": 5, "value": True})
    ctx = SimpleNamespace(
        user=inter.user,
        guild=inter.guild,
        channel=inter.channel,
        interaction=inter,
        command=command,
    )
    await command._invoke(ctx)
    service.receipt.assert_called_once()
    assert service.receipt.call_args.args[1:] == (row["AttemptID"], action)
    reply = inter.response.send_message.call_args
    assert reply.kwargs["ephemeral"] is True
    assert reply.kwargs["allowed_mentions"].to_dict() == {"parse": []}
    if roster_mode:
        service.roster_preview.assert_called_once()
        assert reply.kwargs["view"].roster_correction


def test_extract_count_preserves_zero_meta_count() -> None:
    result = kvk_admin_service.KvkCacheRefreshResult(
        main=kvk_admin_service.KvkCacheBuildOutcome(
            label="Player stats cache",
            count=kvk_admin_service._extract_count({"_meta": {"count": 0}, "count": 5}),
            duration_seconds=0.1,
        ),
        last_kvk=kvk_admin_service.KvkCacheBuildOutcome(
            label="Last-KVK cache",
            count=0,
            duration_seconds=0.1,
        ),
    )

    message = kvk_admin_service.format_cache_refresh_message(result)

    assert result.main.count == 0
    assert "Player stats cache refreshed (0 records)" in message


@pytest.mark.parametrize("source", ["legacy_full_data", "snapshot_report_v1"])
@pytest.mark.parametrize("method", ["run_export_test", "run_export_all"])
def test_exports_reject_without_invoking_runner(monkeypatch, source, method):
    from unittest.mock import Mock

    from kvk.dal.new_source_import_dal import SourceConflict

    monkeypatch.setattr(
        kvk_admin_service.kvk_admin_dal,
        "read_admin_source",
        lambda _: {"KVK_NO": 16, "SourceKey": source},
    )
    runner = Mock(side_effect=AssertionError("No provider execution"))
    kwargs = dict(
        kvk_no=16,
        sheet_name="synthetic",
        server="unused",
        database="unused",
        username="unused",
        password="unused",
        credentials_file="unused",
        runner=runner,
    )
    kwargs.update(
        dict(create_primary=True, export_pass4=True, export_altar=True, export_pass7=True)
        if method == "run_export_test"
        else dict(alert_channel=None, event_loop=None)
    )
    with pytest.raises(SourceConflict, match="No export started"):
        getattr(kvk_admin_service, method)(**kwargs)
    runner.assert_not_called()


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
    assert result.last_kvk.error == "RuntimeError"
    assert "Success: Player stats cache refreshed (10 records)" in message
    assert "Warning: Last-KVK cache build failed" in message
    assert "Last-KVK cache refresh failed" in caplog.text
    assert "cache unavailable" not in caplog.text
    assert "Traceback" not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "expected_prefix"),
    [
        ("refreshed", "Success:"),
        ("last_known_good", "Warning:"),
        ("skipped", "Warning:"),
    ],
)
async def test_cache_admin_reports_source_refresh_status(status, expected_prefix) -> None:
    async def builder():
        return {
            "_meta": {
                "count": 415,
                "source_refresh_status": status,
                "source_kvk_no": 16,
                "source_last_refresh": "2026-08-28T08:12:00",
                "cache_write_status": "written",
            }
        }

    outcome = await kvk_admin_service._run_cache_builder("Player stats cache", builder)
    message = kvk_admin_service._format_cache_outcome(outcome)

    assert message.startswith(expected_prefix)
    assert "KVK 16" in message
    assert "2026-08-28T08:12:00" in message
    if status == "last_known_good":
        assert "last-known-good SQL" in message
    if status == "skipped":
        assert "refresh was skipped" in message


@pytest.mark.asyncio
async def test_cache_admin_reports_failed_refresh_and_preserved_json() -> None:
    async def builder():
        return {
            "_meta": {
                "count": 0,
                "source_refresh_status": "failed",
                "source_refresh_error_code": "source_kvk_mismatch",
                "cache_write_status": "preserved_existing",
                "existing_json_preserved": True,
            }
        }

    outcome = await kvk_admin_service._run_cache_builder("Player stats cache", builder)
    message = kvk_admin_service._format_cache_outcome(outcome)

    assert outcome.error == "source_kvk_mismatch"
    assert message.startswith("Failed:")
    assert "Existing JSON was preserved" in message


@pytest.mark.asyncio
async def test_cache_admin_reports_metadata_fallback_write() -> None:
    async def builder():
        return {
            "_meta": {
                "count": 0,
                "source_refresh_status": "failed",
                "source_refresh_error_code": "source_snapshot_empty",
                "cache_write_status": "fallback_written",
                "existing_json_preserved": False,
            }
        }

    outcome = await kvk_admin_service._run_cache_builder("Player stats cache", builder)
    message = kvk_admin_service._format_cache_outcome(outcome)

    assert message.startswith("Failed:")
    assert "A metadata-only fallback JSON was written" in message
    assert "No safe replacement was written" not in message


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
    monkeypatch.setattr(
        kvk_admin_service.kvk_admin_dal,
        "read_admin_source",
        lambda n: {"KVK_NO": n or 16, "SourceKey": "legacy_full_data"},
    )

    def fake_recompute(kvk_no: int | None = None) -> int:
        assert kvk_no == 16
        return 17

    monkeypatch.setattr(kvk_admin_service.kvk_admin_dal, "recompute_windows", fake_recompute)

    result = kvk_admin_service.recompute_kvk_windows(0)

    assert result.kvk_no == 17
    assert result.duration_seconds >= 0


def test_list_recent_scans_clamps_limit_and_formats_message(monkeypatch) -> None:
    monkeypatch.setattr(
        kvk_admin_service.kvk_admin_dal,
        "read_admin_source",
        lambda n: {"KVK_NO": n or 16, "SourceKey": "legacy_full_data"},
    )
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
    monkeypatch.setattr(
        kvk_admin_service.kvk_admin_dal,
        "read_admin_source",
        lambda n: {"KVK_NO": n or 16, "SourceKey": "legacy_full_data"},
    )
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
    assert "table lines not shown" in table


def test_new_source_recompute_inspects_without_legacy_write(monkeypatch):
    from unittest.mock import Mock

    dal = kvk_admin_service.kvk_admin_dal
    monkeypatch.setattr(
        dal, "read_admin_source", lambda _: {"KVK_NO": 16, "SourceKey": "snapshot_report_v1"}
    )
    monkeypatch.setattr(dal, "fetch_source_windows", lambda _: [{"PeriodKey": "overall"}])
    write = Mock(side_effect=AssertionError("No recompute"))
    monkeypatch.setattr(dal, "recompute_windows", write)
    result = kvk_admin_service.recompute_kvk_windows(16)
    assert result.inspection_only and len(result.rows) == 1
    write.assert_not_called()


def test_new_source_scans_preserve_unused_registry_and_do_not_load_legacy(monkeypatch):
    from unittest.mock import Mock

    dal = kvk_admin_service.kvk_admin_dal
    monkeypatch.setattr(
        dal, "read_admin_source", lambda _: {"KVK_NO": 16, "SourceKey": "snapshot_report_v1"}
    )
    rows = [dict(ScanID=7, ScanTimestampUTC="2026-09-01T12:34:56Z", TimePrecision="second")]
    monkeypatch.setattr(dal, "fetch_source_recent_scans", lambda connect, kvk, limit: rows)
    legacy = Mock(side_effect=AssertionError("No legacy scans"))
    monkeypatch.setattr(dal, "fetch_recent_scans", legacy)
    result = kvk_admin_service.list_recent_scans(16, 200)
    assert result.limit == 100 and result.rows == rows
    text = kvk_admin_service.format_recent_scans_message(result)
    assert "unused" in text and "12:34:56Z" in text
    legacy.assert_not_called()


def test_private_preview_detects_same_config_pending_update_and_stale_response(monkeypatch):
    from kvk.dal.new_source_import_dal import SourceConflict

    dal = kvk_admin_service.kvk_admin_dal
    monkeypatch.setattr(
        dal, "read_admin_source", lambda _: {"KVK_NO": 16, "SourceKey": "snapshot_report_v1"}
    )
    rows = [
        dict(
            PeriodKey="overall",
            PublicationID="pub",
            SelectedConfigVersionID="config",
            DesiredConfigVersionID="config",
            PendingUpdateID="pending",
            PendingUpdateState="waiting_aggregate",
        )
    ]
    monkeypatch.setattr(dal, "fetch_source_windows", lambda _: rows.copy())
    result = kvk_admin_service.load_window_preview(16)
    assert "previous / waiting_aggregate" in kvk_admin_service.format_window_preview_table(result)
    kvk_admin_service.require_admin_result_current(result)
    rows = [{**rows[0], "PendingUpdateID": "replacement"}]
    with pytest.raises(SourceConflict, match="selection changed"):
        kvk_admin_service.require_admin_result_current(result)


@pytest.mark.parametrize("source", ["legacy_full_data", "snapshot_report_v1"])
def test_recompute_dal_holds_admission_to_commit_and_rejects_new_source(monkeypatch, source):
    from kvk.dal.new_source_import_dal import SourceConflict
    from tests.test_kvk_source_card_context import CardStore

    dal = kvk_admin_service.kvk_admin_dal

    class Store(CardStore):
        def route(self, sql, args, connection):
            if "sp_KVK_Recompute_Windows" in sql:
                assert connection not in self.closed
                self.events.append((connection, sql, args))
                return []
            return super().route(sql, args, connection)

    store = Store()
    store.choice["SourceKey"] = source
    store.install(monkeypatch)
    monkeypatch.setattr(dal, "get_conn_with_retries", store.connect)
    monkeypatch.setattr(dal, "resolve_current_kvk_no_from_cursor", lambda *_: 16)
    if source == "legacy_full_data":
        assert dal.recompute_windows(16) == 16
    else:
        with pytest.raises(SourceConflict):
            dal.recompute_windows(16)
    assert any("sp_KVK_Recompute_Windows" in sql for _, sql, _ in store.events) == (
        source == "legacy_full_data"
    )
    assert store.closed == {1}
