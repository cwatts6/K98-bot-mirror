"""Combined production-shaped report failures, with real owned worker barriers."""

import asyncio
from contextlib import contextmanager
import io
import json
import os
import threading
import time
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4
import zipfile

import pytest

from core.owned_work import drain_thread
from services import (
    operation_diagnostics as diagnostics,
    recovery_evidence_bundle as bundle,
    recovery_health as health,
)
from tests.test_guided_recovery import ACTOR
from tests.test_recovery_evidence_bundle import event
from tests.test_recovery_report import report_service


def populate(monkeypatch):
    for name in (
        "_last_success",
        "_failure",
        "_failure_detail",
        "_notification_failure",
        "_cycle_started",
        "_progress_at",
        "_stage_started",
        "_logged_checks",
    ):
        monkeypatch.setattr(health, name, getattr(health, name))
    sink = diagnostics.DiagnosticSink()
    reference = uuid4().hex
    sink._accept(event(reference, "entered", "operation"))
    sink._accept(event(reference, "deadline_elapsed_pending"))
    sink._publish()
    monkeypatch.setattr(diagnostics, "_sink", sink)
    # Actual monitor methods create the nested failure frames which depth=4 lost.
    for name in ("_cycle", "_last_completed_cycle", "_last_failed_cycle", "_history"):
        monkeypatch.setattr(health, name, None)
    monkeypatch.setattr(health, "_checks", [])
    health.begin_cycle()
    try:
        raise RuntimeError("password=DO_NOT_EXPORT")
    except RuntimeError as error:
        health.record_check("configuration", error, waiting=True)
    health.record_success()
    return reference


def test_monitor_nested_failure_is_available_and_other_provider_failure_isolated(monkeypatch):
    populate(monkeypatch)
    original = bundle.loaded_call

    def source(module, function):
        if module == "profile_cache":
            raise RuntimeError("password=DO_NOT_EXPORT")
        return original(module, function)

    monkeypatch.setattr(bundle, "loaded_call", source)
    components, _, _ = bundle.collect_components()
    report = json.loads(components["diagnostic-health.json"])
    assert report["monitor"]["coverage"]["status"] == "available"
    monitor = report["monitor"]["observation"]
    assert monitor["last_completed_cycle"]["checks"][0]["frames"][0]["function"]
    assert report["profile_cache"]["coverage"]["status"] == "unavailable"
    assert report["sink"]["coverage"]["status"] == "available"
    service, _, _ = report_service()
    ordinary = json.loads(service.download_report(ACTOR)["content"])
    assert ordinary["monitor"]["coverage"]["status"] == "available"
    assert ordinary["monitor"]["last_completed_cycle"]["waiting_checks"] == 1
    assert b"DO_NOT_EXPORT" not in components["diagnostic-health.json"]


def test_monitor_oversize_history_preserves_state_and_explicit_omissions(monkeypatch):
    monkeypatch.setattr(
        health,
        "observation",
        lambda: {
            "healthy": False,
            "observer_state": "waiting",
            "history": {"records": ["x" * 8000] * 100},
            "check_failure": {"error_type": "OSError"},
        },
    )
    value, coverage = bundle.monitor_snapshot()
    assert value["healthy"] is False and value["observer_state"] == "waiting"
    assert value["check_failure"]["error_type"] == "OSError"
    assert coverage["status"] == "partial" and coverage["omitted_fields"] == ["history"]
    assert len(bundle.encode(value)) <= 12288


def test_large_monitor_cycle_keeps_checkpoint_and_original_failure(monkeypatch):
    monkeypatch.setattr(
        health,
        "observation",
        lambda: {
            "observer_state": "waiting",
            "healthy": False,
            "cycle": {
                "stage": "configuration",
                "in_progress": True,
                "waiting_checks": 100,
                "checks": [{"error_type": "x" * 200}] * 100,
            },
            "check_failure": {"error_type": "OSError"},
        },
    )
    value, coverage = bundle.monitor_snapshot()
    assert value["cycle"]["stage"] == "configuration"
    assert value["cycle"]["waiting_checks"] == 100
    assert value["cycle"]["report_omitted_fields"] == ["checks"]
    assert value["check_failure"]["error_type"] == "OSError"
    assert coverage["trimmed_fields"] == ["cycle"] and coverage["status"] == "partial"


def test_event_cache_object_provider_is_present_in_both_reports(monkeypatch):
    import event_cache
    from services.recovery_report import _monitor_report

    reporter = Mock(return_value={"state": "loaded_empty"})
    monkeypatch.setattr(event_cache.refresh_service, "report", reporter)
    components, _, _ = bundle.collect_components()
    source = json.loads(components["diagnostic-health.json"])["event_cache"]
    assert source["coverage"]["status"] == "available"
    assert source["observation"] == {"state": "loaded_empty"}
    assert _monitor_report()["event_cache"] == {"state": "loaded_empty"}
    assert reporter.call_count == 2


def test_continuation_counts_identify_part_and_whole_component():
    service, _, _ = report_service()
    payload = b'{"row":"' + b"x" * 20000 + b'"}\n'
    with bundle.report_request():
        token = bundle.retain(
            service,
            ACTOR,
            {"operations.jsonl": payload * 3},
            {},
            {"operations.jsonl": {"included": 3, "available": 3, "omitted": 0}},
        )
        part = bundle.continuation(service, ACTOR, token, 65536)
    with zipfile.ZipFile(io.BytesIO(part["content"])) as archive:
        desc = json.loads(archive.read("manifest.json"))["components"]["operations.jsonl"]
    assert desc["included"] == 1 and desc["omitted"] == 2
    assert desc["count_scope"] == "this_part"
    assert desc["component_coverage"] == {"included": 3, "available": 3, "omitted": 0}


def test_cancellation_during_page_yield_prevents_another_read(monkeypatch):
    from services import recovery_complete_report as complete

    service, store, _ = report_service(21)

    def cancel(_):
        assert bundle._active is not None
        bundle._active.cancelled.set()

    monkeypatch.setattr(complete.time, "sleep", cancel)
    with pytest.raises(bundle.SourceConflict):
        service.download_complete_report(ACTOR)
    assert store.report_page.call_count == 1
    assert bundle._active is None


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel", [False, True])
async def test_slow_incidents_monitor_failure_and_pending_boundary_keep_loop_and_ownership(
    monkeypatch, cancel
):
    from ui.views import recovery_view as view

    reference = populate(monkeypatch)
    service, store, _ = report_service(21)
    original = store.report_page.side_effect
    entered, release = threading.Event(), threading.Event()
    hold_seconds = float(os.environ.get("K98_TEST_REPORT_HOLD_SECONDS", "0.05"))

    def page(**kwargs):
        entered.set()
        assert release.wait(hold_seconds + 10)
        # A native call may return after minutes. Only the report census budget
        # expires; it must not cancel the operation represented in the snapshot.
        bundle._active.deadline -= 121
        return original(**kwargs)

    store.report_page.side_effect = page

    async def call(*_):
        return await drain_thread(service.download_complete_report, ACTOR)

    monkeypatch.setattr(view, "call", call)
    pending = asyncio.create_task(view.report_call("download_complete_report", ACTOR))
    try:
        for _ in range(1000):
            if entered.is_set():
                break
            await asyncio.sleep(0.001)
        assert entered.is_set()
        # Heartbeats progress while an actual native thread is blocked.
        until = time.monotonic() + hold_seconds
        ticks = 0
        previous = time.monotonic()
        max_gap = 0.0
        while time.monotonic() < until:
            await asyncio.sleep(0.001)
            now = time.monotonic()
            max_gap = max(max_gap, now - previous)
            previous = now
            ticks += 1
            assert not pending.done()
        assert ticks >= 2
        assert max_gap < 1.0, f"Report wait blocked loop for {max_gap:.3f}s"
        if cancel:
            for _ in range(3):
                pending.cancel()
                await asyncio.sleep(0.001)
                assert not pending.done()
        with pytest.raises(bundle.SourceConflict):
            with bundle.report_request():
                pass
    finally:
        release.set()
    if cancel:
        with pytest.raises(asyncio.CancelledError):
            await pending
    else:
        result = await pending
        with zipfile.ZipFile(io.BytesIO(result["content"])) as archive:
            meta = json.loads(archive.read("manifest.json"))
            assert (
                meta["components"]["incidents.jsonl"]["reason"] == "incident_collection_time_bound"
            )
            assert meta["components"]["operations.jsonl"]["status"] == "available"
            rows = [json.loads(line) for line in archive.read("operations.jsonl").splitlines()]
            assert rows[0]["reference"] == reference
            assert rows[0]["milestones"]["deadline"]["state"] == "deadline_elapsed_pending"
            assert not rows[0]["complete"]
            assert (
                json.loads(archive.read("diagnostic-health.json"))["monitor"]["coverage"]["status"]
                == "available"
            )
            assert meta["incident_after"] is None
            for descriptor in meta["components"].values():
                assert {
                    "schema",
                    "source_kind",
                    "exported_utc",
                    "available",
                    "omitted",
                    "source_observed_utc",
                    "publication_watermark",
                } <= descriptor.keys()
        assert not result["complete"]
    assert store.report_page.call_count == 1 and bundle._active is None


def test_loaded_runtime_authority_identity_uses_actual_legacy_client_contract(monkeypatch):
    from services import export_runtime_composition as runtime, recovery_runtime as recovery

    service, _, _ = report_service()

    @contextmanager
    def scope(**_):
        yield service

    monkeypatch.setattr(recovery, "recovery_service", scope)
    monkeypatch.setattr(recovery, "_authorize_report_actor", Mock())
    call = SimpleNamespace(
        bundle=SimpleNamespace(
            legacy=SimpleNamespace(recovery_client=SimpleNamespace(deployment_hash="a" * 64))
        )
    )
    token = runtime._caller.set(call)
    try:
        result = recovery._call_report("download_complete_report", ACTOR)
    finally:
        runtime._caller.reset(token)
    with zipfile.ZipFile(io.BytesIO(result["content"])) as archive:
        identity = json.loads(archive.read("manifest.json"))["identity"]
    assert identity["authority_deployment_hash"] == "a" * 64
    assert identity["authority_identity_source"] == "authority_deployment_hash_from_loaded_runtime"


@pytest.mark.parametrize(
    "failure", [bundle.SourceConflict("stale caller"), RuntimeError("construction failed")]
)
def test_failed_report_admission_cannot_export_inherited_authority_identity(monkeypatch, failure):
    from services import export_runtime_composition as runtime, recovery_runtime as recovery

    @contextmanager
    def unavailable(**_):
        raise failure
        yield

    monkeypatch.setattr(recovery, "recovery_service", unavailable)
    monkeypatch.setattr(recovery, "_authorize_report_actor", Mock())
    token = runtime._caller.set(
        SimpleNamespace(
            bundle=SimpleNamespace(
                legacy=SimpleNamespace(recovery_client=SimpleNamespace(deployment_hash="b" * 64))
            )
        )
    )
    try:
        result = recovery._call_report("download_complete_report", ACTOR)
    finally:
        runtime._caller.reset(token)
    with zipfile.ZipFile(io.BytesIO(result["content"])) as archive:
        identity = json.loads(archive.read("manifest.json"))["identity"]
    assert "authority_deployment_hash" not in identity
    assert not result["complete"]


def test_current_v2_not_starved_by_restored_legacy_preview(monkeypatch):
    sink = diagnostics.DiagnosticSink()
    for _ in range(40):
        sink._accept(event(uuid4().hex, "settled", "operation"))
    sink._publish()
    for row in sink.snapshot["operations"]:
        row["schema"] = "legacy_projection"
    current = uuid4().hex
    sink._accept(event(current, "entered", "operation"))
    sink._publish()
    # Mark the frozen historical rows as a real restored generation would.
    for row in sink.snapshot["operations"][:-1]:
        row["schema"] = "legacy_projection"
    assert sink.report()["operations"][0]["reference"] == current
    assert sink.report()["omitted_operations"] > 0
