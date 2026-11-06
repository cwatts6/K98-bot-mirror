"""Operator-facing report contracts at realistic population and delivery boundaries."""

import io
import json
from unittest.mock import AsyncMock, Mock
from uuid import uuid4
import zipfile

import pytest

from core import startup_diagnostics
from services import recovery_evidence_bundle as bundle, recovery_report
from tests.test_guided_recovery import ACTOR
from tests.test_recovery_report import report_service


def startup_rows(count=8):
    return [
        dict(
            step=f"startup_step_{i}",
            reference=uuid4().hex,
            state="completed_after_deadline",
            observed_utc="2026-11-04T12:15:00+00:00",
            observer="observed",
            physical="settled",
            returned=True,
            parent_return={"value_kind": "dict", "value_meaning": "unclassified_return"},
            worker_result={"reported_success": False},
            feature={
                "feature_outcome": "succeeded",
                "verification_source": "rehydrate_tracked_views",
                "verification_reason": "verified",
                "restoration_outcome": "complete",
                "attached": 21,
            },
            verification_state="checked",
        )
        for i in range(count)
    ]


def test_full_reports_keep_eight_startup_rows_and_coverage(monkeypatch):
    rows = startup_rows()
    monkeypatch.setattr(startup_diagnostics, "_steps", {r["step"]: r for r in rows})
    service, _, _ = report_service()
    ordinary = json.loads(service.download_report(ACTOR)["content"])
    complete = service.download_complete_report(ACTOR)
    assert ordinary["monitor"]["startup"] == rows
    with zipfile.ZipFile(io.BytesIO(complete["content"])) as archive:
        assert ordinary["monitor"]["startup"] == json.loads(archive.read("startup.json"))
    assert ordinary["monitor"]["component_coverage"]["startup"]["included"] == 8


@pytest.mark.parametrize("invalid", [object(), "x" * 8193], ids=["object", "oversize"])
def test_invalid_startup_row_keeps_valid_neighbors_in_both_reports(monkeypatch, invalid):
    rows = startup_rows(3)
    rows[1]["step"] = invalid
    original = bundle.loaded_call
    monkeypatch.setattr(
        bundle,
        "loaded_call",
        lambda module, function: (
            rows if module == "core.startup_diagnostics" else original(module, function)
        ),
    )
    service, _, _ = report_service()
    ordinary = json.loads(service.download_report(ACTOR)["content"])
    complete = service.download_complete_report(ACTOR)
    expected = [rows[0], rows[2]]
    assert ordinary["monitor"]["startup"] == expected
    with zipfile.ZipFile(io.BytesIO(complete["content"])) as archive:
        assert json.loads(archive.read("startup.json")) == expected
        manifest = json.loads(archive.read("manifest.json"))
    for coverage in (
        ordinary["monitor"]["component_coverage"]["startup"],
        manifest["components"]["startup.json"],
    ):
        assert coverage["status"] == "partial"
        assert coverage["reason"] == "startup_rows_invalid_or_bound"
        assert (coverage["available"], coverage["included"], coverage["omitted"]) == (3, 2, 1)


def test_aggregate_omission_updates_delivered_cache_coverage(monkeypatch):
    monkeypatch.setattr(bundle, "monitor_snapshot", lambda **_: ({"detail": "m" * 4000}, {}))
    rows = startup_rows(64)

    def loaded(module, function):
        if module == "core.startup_diagnostics":
            return rows
        if module in {"services.player_stats_cache_service", "profile_cache", "target_utils"}:
            return {"rows": ["x" * 40] * 20}
        return {"rows": ["x" * 40] * 40}

    monkeypatch.setattr(bundle, "loaded_call", loaded)
    result = recovery_report._monitor_report()
    omitted = [
        k
        for k, v in result["cache_outcomes_v1"].items()
        if v.get("status") == "omitted_report_budget"
    ]
    assert omitted
    for name in omitted:
        assert result["source_coverage"][name] == "partial"
        assert result["component_coverage"][name]["source_status"] == "available"
        assert result["component_coverage"][name]["reason"] == "ordinary_report_byte_bound"
    assert len(recovery_report.encode(result)) <= 32768


def test_monitor_cannot_crowd_out_fitting_incident(monkeypatch):
    service, _, _ = report_service()
    monkeypatch.setattr(recovery_report, "_monitor_report", lambda: {"detail": "m" * 10000})
    monkeypatch.setattr(recovery_report, "incident_report", lambda *_: {"detail": "i" * 56000})
    result = service.download_report(ACTOR, max_bytes=65536)
    assert len(result["content"]) <= 65536
    document = json.loads(result["content"])
    assert document["included_incidents"] == 1
    assert document["monitor"]["status"] == "omitted_attachment_budget"


def test_expired_collection_keeps_returned_page_and_exact_cursor(monkeypatch):
    service, store, records = report_service(25)
    original = store.report_page.side_effect
    clock = [0.0]
    monkeypatch.setattr(bundle.time, "monotonic", lambda: clock[0])

    def slow_page(**kwargs):
        page = original(**kwargs)
        clock[0] += 31
        return page

    store.report_page.side_effect = slow_page
    report = service.download_complete_report(ACTOR)
    assert report["count"] == 10
    assert report["incident_after"] == records[9]["IncidentID"]
    with zipfile.ZipFile(io.BytesIO(report["content"])) as archive:
        assert len(archive.read("incidents.jsonl").splitlines()) == 10
        manifest = json.loads(archive.read("manifest.json"))
        assert (
            manifest["components"]["incidents.jsonl"]["reason"] == "incident_collection_time_bound"
        )
    store.report_page.side_effect = original
    rest = json.loads(
        service.download_report(ACTOR, report["incident_after"], report["through"], 2)["content"]
    )
    assert [r["incident_id"] for r in rest["incidents"]] == [r["IncidentID"] for r in records[10:]]


def test_continuation_retry_returns_identical_frozen_part(monkeypatch):
    service, store, _ = report_service()
    token = bundle.retain(service, ACTOR, {"startup.json": b"x" * 70000}, {})
    first = service.download_diagnostic_part(ACTOR, token, 65536)
    store.report_page = Mock(side_effect=AssertionError("Retry must not recollect"))
    retry = service.download_diagnostic_part(ACTOR, token, 65536)
    assert retry == first
    assert retry["diagnostic_token"] is not None
    assert retry["sha256"] == bundle.sha(retry["content"])


def test_population_limit_is_explicit_not_whole_source_loss(monkeypatch):
    monkeypatch.setattr(
        startup_diagnostics, "_steps", {str(i): r for i, r in enumerate(startup_rows(64))}
    )
    result = recovery_report._monitor_report()
    assert isinstance(result["startup"], list) and result["startup"]
    coverage = result["component_coverage"]["startup"]
    assert coverage["available"] == 64
    assert coverage["included"] + coverage["omitted"] == 64
    assert len(recovery_report.encode(result)) <= 32768


def test_later_oversize_row_preserves_prefix_without_skipping(monkeypatch):
    import random

    service, _, records = report_service(3)
    records[1]["evidence"]["explanation"] = random.Random(42).randbytes(100000).hex()
    report = service.download_complete_report(ACTOR, max_bytes=65536)
    assert report["count"] == 1
    assert report["incident_after"] == records[0]["IncidentID"]
    with zipfile.ZipFile(io.BytesIO(report["content"])) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        component = manifest["components"]["incidents.jsonl"]
        assert component["sha256"] == bundle.sha(archive.read("incidents.jsonl"))
        assert component["included"] + component["omitted"] == component["available"] == 3
    remainder = json.loads(
        service.download_report(ACTOR, report["incident_after"], report["through"], 2)["content"]
    )
    assert [r["incident_id"] for r in remainder["incidents"]] == [
        r["IncidentID"] for r in records[1:]
    ]


def test_retry_is_authorized_bounded_and_not_extended(monkeypatch):
    from services.recovery_service import RecoveryActor, SourceConflict

    service, _, _ = report_service()
    clock = [0.0]
    monkeypatch.setattr(bundle.time, "monotonic", lambda: clock[0])
    token = bundle.retain(service, ACTOR, {"startup.json": b"x" * 70000}, {})
    first = service.download_diagnostic_part(ACTOR, token, 65536)
    with pytest.raises(SourceConflict):
        service.download_diagnostic_part(RecoveryActor(9, 2, 3), token, 65536)
    second = service.download_diagnostic_part(ACTOR, first["diagnostic_token"], 65536)
    with pytest.raises(SourceConflict):
        service.download_diagnostic_part(ACTOR, token, 65536)
    assert service.download_diagnostic_part(ACTOR, first["diagnostic_token"], 65536) == second
    clock[0] = 601
    with pytest.raises(SourceConflict):
        service.download_diagnostic_part(ACTOR, first["diagnostic_token"], 65536)
    bundle.drain_reports()
    assert not bundle._sessions and not bundle._deliveries


@pytest.mark.asyncio
async def test_failed_discord_send_can_retry_same_frozen_part(monkeypatch):
    from ui.views import recovery_backlog_view as ui, recovery_view

    service, _, _ = report_service()
    token = bundle.retain(service, ACTOR, {"startup.json": b"x" * 70000}, {})
    monkeypatch.setattr(ui, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(ui, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(ui, "report_error", AsyncMock())

    async def call(method, actor, token, limit):
        return service.download_diagnostic_part(actor, token, limit)

    monkeypatch.setattr(recovery_view, "report_call", call)
    send = AsyncMock(side_effect=[RuntimeError("failed delivery"), None])
    monkeypatch.setattr(recovery_view, "send_report_attachment", send)
    from types import SimpleNamespace

    interaction = SimpleNamespace(guild=SimpleNamespace(filesize_limit=65536))
    await ui.show_complete_report(interaction, token=token)
    await ui.show_complete_report(interaction, token=token)
    first, second = [c.args[2] for c in send.await_args_list]
    assert first["content"] == second["content"]
    assert first["sha256"] == second["sha256"]
    assert first["diagnostic_token"] == second["diagnostic_token"]
    assert bundle._active is None


@pytest.mark.asyncio
async def test_incident_continuation_view_keeps_delivered_prefix(monkeypatch):
    from ui.views import recovery_view
    from ui.views.recovery_backlog_view import EvidenceReportPartsView

    show = AsyncMock()
    monkeypatch.setattr(recovery_view, "show_report", show)
    view = EvidenceReportPartsView(
        dict(incident_after="last-delivered", through="cutoff", incident_continuation=True)
    )
    interaction = object()
    await view.incidents.callback(interaction)
    show.assert_awaited_once_with(interaction, after="last-delivered", through="cutoff", part=2)


def test_malformed_summary_key_never_advances_bytes_ahead_of_cursor():
    service, _, records = report_service(3)
    records[1]["evidence"]["outcome"] = {"unexpected": "shape"}
    report = service.download_complete_report(ACTOR)
    with zipfile.ZipFile(io.BytesIO(report["content"])) as archive:
        rows = [json.loads(line) for line in archive.read("incidents.jsonl").splitlines()]
        assert len(rows) == report["count"] == 1
        assert rows[-1]["incident_id"] == report["incident_after"] == records[0]["IncidentID"]
    rest = json.loads(
        service.download_report(ACTOR, report["incident_after"], report["through"], 2)["content"]
    )
    assert [r["incident_id"] for r in rows + rest["incidents"]] == [
        r["IncidentID"] for r in records
    ]


def test_archive_failure_preserves_original_error_and_closes_buffers(monkeypatch):
    from services import recovery_complete_report as complete

    seen = []
    original = complete.BoundedArchive

    class FailedArchive(original):
        def __init__(self, limit):
            super().__init__(limit)
            seen.append(self)

        def write(self, data):
            raise OSError("injected archive write failure")

    monkeypatch.setattr(complete, "BoundedArchive", FailedArchive)
    service, _, _ = report_service()
    with pytest.raises(OSError, match="injected archive write failure"):
        service.download_complete_report(ACTOR)
    assert seen and all(buffer.closed for buffer in seen)
    assert bundle._active is None


def test_invalid_operation_neighbor_does_not_hide_valid_reference(monkeypatch):
    from services import operation_diagnostics as diagnostics
    from tests.test_recovery_evidence_bundle import event

    sink = diagnostics.DiagnosticSink()
    for _ in range(2):
        sink._accept(event(uuid4().hex, "entered", "operation"))
    sink._publish()
    source = sink.report()
    good = source["operations"][1]["reference"]
    source["operations"][0]["milestones"]["scope_entry"]["stage"] = "unknown_stage"
    monkeypatch.setattr(diagnostics, "report", lambda: source)
    result = recovery_report._operation_report()
    assert [r["reference"] for r in result["operations"]] == [good]
    assert result["coverage"]["rejected"] == 1
    assert result["coverage"]["included"] == 1
    assert len(recovery_report.encode(result)) <= 16384


def test_operation_coverage_metadata_is_inside_final_component_limit(monkeypatch):
    from services import operation_diagnostics as diagnostics

    # All source fields are individually valid primitives and fit before coverage.
    source = {"schema": "operation-observations/2", "operations": [], "padding": ["x" * 4000] * 4}
    base = len(recovery_report.encode(source))
    source["tail"] = "x" * (16330 - base - len(recovery_report.encode({"tail": ""})))
    assert 16200 < len(recovery_report.encode(source)) < 16384
    monkeypatch.setattr(diagnostics, "report", lambda: source)
    result = recovery_report._operation_report()
    assert result["status"] == "unavailable"
    assert result["reason"] == "source_unavailable_invalid_or_bound"
    assert len(recovery_report.encode(result)) < 16384


def test_exact_timestamp_rendering_matches_canonical_redaction():
    from datetime import UTC, datetime, timedelta, timezone

    for offset in (-86399, -18000, 0, 19800, 86399):
        for year in (1, 1900, 2026, 9999):
            value = datetime(
                year, 11, 4, 12, 34, 56, 789012, tzinfo=timezone(timedelta(seconds=offset))
            )
            assert bundle.redact_report_text(value) == bundle.redact_diagnostic_text(value)
    value = datetime(2026, 11, 4)
    assert bundle.redact_report_text(value) == bundle.redact_diagnostic_text(value)

    class CredentialTimestamp(datetime):
        def __str__(self):
            return "password=not-a-timestamp"

    value = CredentialTimestamp(2026, 11, 4, tzinfo=UTC)
    assert "not-a-timestamp" not in bundle.redact_report_text(value)


def test_long_repeated_text_cache_retains_only_bounded_redacted_output(monkeypatch):
    canonical = bundle.redact_diagnostic_text
    wrapped = Mock(wraps=canonical)
    monkeypatch.setattr(bundle, "redact_diagnostic_text", wrapped)
    secret = "x" * 300 + " password=never-retain-original"
    with bundle.report_request() as lease:
        assert bundle.redact_report_text(secret) == canonical(secret)
        assert bundle.redact_report_text(secret) == canonical(secret)
        assert wrapped.call_count == 1
        assert "never-retain-original" not in str(lease.redactions)
        assert all(type(key) is bytes and len(key) == 32 for key in lease.redactions)
        assert all(len(value.encode("utf-8")) <= 512 for value in lease.redactions.values())
    assert lease.redactions == {}
