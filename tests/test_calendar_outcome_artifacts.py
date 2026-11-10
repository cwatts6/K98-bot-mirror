from datetime import UTC, datetime
import hashlib
import io
import json
import os
import zipfile

import pytest

from event_calendar import cache_publisher, service
from event_calendar.cache_publisher import PublishResult
from event_calendar.event_generator import GenerationResult
from event_calendar.mutation_owner import get_owner
from event_calendar.sheets_sync import SyncResult
from services import operation_diagnostics as diagnostics
from tests.test_guided_recovery import ACTOR
from tests.test_recovery_report import report_service


class ReadConnection:
    def rollback(self):
        return None

    def close(self):
        return None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,physical,key,result,arguments",
    [
        (
            "refresh",
            "sync_sheets_to_sql",
            "refreshed_utc",
            SyncResult(True, "success"),
            {"sheet_id": "offline"},
        ),
        (
            "generate",
            "generate_calendar_instances",
            "generated_utc",
            GenerationResult(True, "success"),
            {},
        ),
        (
            "publish_cache",
            "publish_event_calendar_cache",
            "published_utc",
            PublishResult(True, "success"),
            {},
        ),
    ],
)
async def test_standalone_stage_preserves_existing_timestamp_contract(
    monkeypatch, method, physical, key, result, arguments
):
    started = datetime(2026, 11, 5, 19, 0, tzinfo=UTC)
    monkeypatch.setattr(service, "now_utc", lambda: started)
    monkeypatch.setattr(service, physical, lambda *a, **k: result)
    get_owner().audit.close_admission()
    output = await getattr(service.CalendarService(), method)(**arguments)
    assert output["ok"] and output[key] == started.isoformat()


def test_write_counts_are_unavailable_before_stage_entry(monkeypatch):
    from event_calendar import event_generator, sheets_sync

    def unavailable(*args, **kwargs):
        raise RuntimeError("offline fixture")

    monkeypatch.setattr(cache_publisher, "get_conn_with_retries", unavailable)
    monkeypatch.setattr(event_generator, "get_conn_with_retries", unavailable)
    monkeypatch.setattr(sheets_sync, "fetch_sheet_csv", unavailable)
    published = cache_publisher.publish_event_calendar_cache()
    generated = event_generator.generate_calendar_instances()
    synced = sheets_sync.sync_sheets_to_sql("offline")
    assert not published.ok and published.events_written is None
    assert published.primary == "not_attempted"
    assert not generated.ok and generated.instances_written is None
    assert not synced.ok and synced.rows_upserted_recurring is None
    assert synced.rows_upserted_oneoff is None and synced.rows_upserted_overrides is None


@pytest.fixture
def publish_fixture(monkeypatch, tmp_path):
    primary, index = tmp_path / "calendar.json", tmp_path / "index.json"
    primary.write_bytes(b'{"old":"primary"}')
    index.write_bytes(b'{"old":"index"}')
    monkeypatch.setattr(cache_publisher, "_CACHE_PATH", primary)
    monkeypatch.setattr(cache_publisher, "_TYPE_INDEX_PATH", index)
    monkeypatch.setattr(cache_publisher, "get_conn_with_retries", lambda **k: ReadConnection())
    monkeypatch.setattr(
        cache_publisher,
        "load_runtime_instances",
        lambda *a, **k: [
            {
                "instance_id": 1,
                "title": "Café 🦊",
                "type": "war",
                "start_utc": datetime(2099, 1, 1, tzinfo=UTC),
                "end_utc": datetime(2099, 1, 2, tzinfo=UTC),
            }
        ],
    )
    return primary, index


@pytest.mark.parametrize("target", ["primary", "index", "index_build"])
def test_real_files_preserve_acknowledged_effect_and_cleanup_temp(
    monkeypatch, publish_fixture, target
):
    primary, index = publish_fixture
    replace = os.replace

    def fail(source, destination):
        if str(destination) == str(primary if target == "primary" else index):
            raise PermissionError("private path")
        return replace(source, destination)

    if target == "index_build":

        def fail_build(**kwargs):
            raise ValueError("private payload")

        monkeypatch.setattr(cache_publisher, "build_event_type_index_payload", fail_build)
    else:
        monkeypatch.setattr(os, "replace", fail)
    result = cache_publisher.publish_event_calendar_cache()
    assert index.read_bytes() == b'{"old":"index"}'
    assert not list(primary.parent.glob(".atomic.*.tmp"))
    if target == "primary":
        assert not result.ok and result.events_written is None and result.primary == "unknown"
        assert primary.read_bytes() == b'{"old":"primary"}'
    else:
        assert result.ok and result.events_written == 1
        assert result.status == "success_index_warning" and result.index == "old_or_unknown"
        payload = json.loads(primary.read_bytes())
        assert payload["events"][0]["title"] == "Café 🦊"
        expected = json.dumps(payload, indent=2, ensure_ascii=True).replace("\n", os.linesep)
        assert primary.read_bytes() == expected.encode()


@pytest.mark.asyncio
async def test_optional_projection_and_telemetry_cannot_erase_publication(monkeypatch):
    calls = []

    def publish(**kwargs):
        calls.append(1)
        return PublishResult(
            True, "success_index_warning", events_written=12, primary="new", index="old_or_unknown"
        )

    def fail(*args, **kwargs):
        raise ValueError("presentation unavailable")

    monkeypatch.setattr(service, "publish_event_calendar_cache", publish)
    monkeypatch.setattr(service, "_result_projection", fail)
    monkeypatch.setattr(service, "emit_telemetry_event", fail)
    monkeypatch.setattr(service, "clock", lambda: None)
    monkeypatch.setattr(service, "now_utc", fail)
    output = await service.CalendarService().publish_cache()
    assert output["ok"] and output["events_written"] == 12
    assert output["projection"] == "unavailable" and calls == [1]


@pytest.mark.asyncio
async def test_actual_report_zip_preserves_calendar_facts_and_optional_summary(
    monkeypatch, tmp_path
):
    sink = diagnostics.DiagnosticSink(tmp_path)
    monkeypatch.setattr(diagnostics, "_sink", sink)
    monkeypatch.setattr(
        service,
        "publish_event_calendar_cache",
        lambda **k: PublishResult(
            True, "success_index_warning", events_written=12, primary="new", index="old_or_unknown"
        ),
    )
    result = await service.CalendarService().publish_cache()
    assert result["ok"]
    for _ in range(10000):
        sink.uploads.summary("calendar", "failed", 0, "PermissionError", dropped=1, failures=1)
    assert len(sink.uploads.workers) == 1 and not sink.uploads.slots
    sink.start().close()
    snapshot = sink.full_snapshot()
    assert len(snapshot["operations"]) == 1
    payload = json.dumps(snapshot)
    assert '"calendar_written": 12' in payload
    assert '"calendar_index": "old_or_unknown"' in payload
    recovery, _, _ = report_service(1)
    report = recovery.download_complete_report(ACTOR)
    assert hashlib.sha256(report["content"]).hexdigest() == report["sha256"]
    with zipfile.ZipFile(io.BytesIO(report["content"])) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        rows = archive.read("operations.jsonl")
        assert b'"calendar_written":12' in rows
        assert b"old_or_unknown" in rows
        for name in archive.namelist():
            if name != "manifest.json":
                data = archive.read(name)
                assert len(data) == manifest["components"][name]["bytes"]
                assert hashlib.sha256(data).hexdigest() == manifest["components"][name]["sha256"]
        workers = manifest["components"]["operations.jsonl"]["upload_observations"]["workers"]
        assert workers["calendar"]["state"] == "failed"
    assert get_owner().active is None
