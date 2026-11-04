"""Semantic contract checks independent of the producer's current defaults."""

import asyncio
from unittest.mock import Mock

import pytest

from core import operation_evidence as evidence, startup_diagnostics as startup
from core.owned_work import drain_thread
from services import operation_diagnostics as diagnostics
from services.startup_outcome_projection import project


@pytest.mark.asyncio
async def test_startup_system_actor_covers_every_parent_and_thread_boundary(monkeypatch):
    events = []
    monkeypatch.setattr(diagnostics, "offer", events.append)

    async def work():
        return await drain_thread(lambda: True)

    assert await startup.run(work(), 5, "proc_config_import") is True
    assert {event["role"] for event in events} == {"parent", "child"}
    assert {(event["actor"], event["origin"]) for event in events} == {("system", "startup")}
    assert events[0]["state"] == "entered" and events[-1]["state"] == "settled"
    events.clear()
    with evidence.scope():
        evidence.emit("proc_config_import", "observed")
    assert {event["actor"] for event in events} == {"unavailable_not_collected"}


@pytest.mark.parametrize("value", [None, True, [], "invalid"])
def test_executed_malformed_checker_is_unknown_with_reason(value):
    result = project("proc_config_import", value, checked=True)
    assert result["feature_outcome"] == "unknown"
    assert result["verification_reason"] == "malformed_result"
    assert result["verification_source"] == "proc_config_import"
    assert project("proc_config_import", value, checked=False)["feature_outcome"] == "not_checked"


@pytest.mark.parametrize("fault", ["identity", "clock", "offer"])
def test_boundary_failure_after_context_allocation_is_visible(monkeypatch, fault):
    sink = diagnostics.DiagnosticSink()
    monkeypatch.setattr(diagnostics, "_sink", sink)
    with evidence.scope():
        with monkeypatch.context() as local:
            failure = Mock(side_effect=OSError("inert diagnostic failure"))
            if fault == "identity":
                local.setattr(evidence, "uuid4", failure)
            elif fault == "clock":
                local.setattr(evidence, "datetime", Mock(now=failure))
            else:
                local.setattr(diagnostics, "offer", failure)
            evidence.emit("proc_config_import", "observed")
        assert sink.report()["emission_failures"] == 1
        assert sink.report()["dropped"] == 1


def test_unknown_stage_count_does_not_export_raw_label(monkeypatch):
    sink = diagnostics.DiagnosticSink()
    monkeypatch.setattr(diagnostics, "_sink", sink)
    with evidence.scope():
        evidence.emit("secret-shaped-arbitrary-stage", "observed")
    assert sink.report()["unknown_stages"] == 1
    assert b"secret-shaped" not in diagnostics.encoded(list(sink.queue))


def test_counter_provenance_separates_previous_incarnations(monkeypatch):
    sink = diagnostics.DiagnosticSink()
    sink.prior_counters = {"dropped": 7}
    sink.dropped = 2
    report = sink.report()
    assert report["dropped"] == 9
    assert report["counter_provenance"]["current"]["dropped"] == 2
    assert report["counter_provenance"]["historical"]["dropped"] == 7


def test_eviction_has_bounded_reason_time_and_incarnation(monkeypatch):
    from uuid import uuid4

    from tests.test_recovery_evidence_bundle import event

    sink = diagnostics.DiagnosticSink()
    monkeypatch.setattr(diagnostics, "MAX_OPERATIONS", 1)
    ref = uuid4().hex
    sink._accept(event(ref, "settled", "operation"))
    sink._accept(event(uuid4().hex, "entered", "operation"))
    evidence_row = sink.report()["eviction_provenance"]["capacity"]
    assert evidence_row["count"] == 1
    assert evidence_row["observed_utc"]
    assert evidence_row["process_incarnation"] == evidence._incarnation
    assert evidence_row["cutoff_utc"] == "not_applicable"


def test_actual_deployed_reader_downgrade_preserves_failure_with_explicit_legacy_loss(tmp_path):
    import hashlib
    from pathlib import Path
    from uuid import uuid4

    from tests.test_recovery_evidence_bundle import event

    path = Path(__file__).parent / "fixtures/p012a_deployed_operation_diagnostics.py.txt"
    source = path.read_bytes()
    assert (
        hashlib.sha256(source).hexdigest()
        == "b3ea2727a1140ccbe971366085d1f643f830b8fa8193fd690db642957cc00e44"
    )
    namespace = {"__name__": "frozen_deployed_diagnostics"}
    exec(compile(source, str(path), "exec"), namespace)
    reference = uuid4().hex
    current = diagnostics.DiagnosticSink(tmp_path)
    current._accept(event(reference, "entered", "operation", actor="system", origin="startup"))
    failure = event(
        reference,
        "failed",
        "worker_execution",
        actor="system",
        origin="startup",
        error_type="OSError",
    )
    current._accept(failure)
    current._publish()
    restored = diagnostics.DiagnosticSink(tmp_path)
    restored._load()
    assert restored.records[reference]["first_failure"]["actor"] == "system"
    old = namespace["DiagnosticSink"](tmp_path)
    old._load()
    # The old reader rejects extended V2 enums, then retains the separately
    # published V1-compatible row. Never call this full V2 compatibility.
    assert old.invalid > 0
    assert old.records[reference]["schema"] == "legacy_projection"
    assert old.records[reference]["first_failure"]["error_type"] == "OSError"
    old._publish()
    upgraded = diagnostics.DiagnosticSink(tmp_path)
    upgraded._load()
    row = upgraded.records[reference]
    assert row["first_failure"]["error_type"] == "OSError"
    assert row["schema"] == "legacy_projection"
    assert row["legacy_loss_split"] == "unknown"
    assert upgraded.report()["counter_provenance"]["historical"]["emission_failures"] == "unknown"


@pytest.mark.asyncio
async def test_real_startup_restore_and_both_reports_keep_semantics(monkeypatch, tmp_path):
    import io
    import json
    import zipfile

    from tests.test_guided_recovery import ACTOR
    from tests.test_recovery_report import report_service

    sink = diagnostics.DiagnosticSink(tmp_path)
    monkeypatch.setattr(diagnostics, "_sink", sink)
    monkeypatch.setattr(startup, "_steps", {})

    async def work():
        return await drain_thread(lambda: False)

    async def malformed(_):
        return None

    assert await startup.run(work(), 5, "proc_config_import", completion_check=malformed) is False
    sink.start().close()
    restored = diagnostics.DiagnosticSink(tmp_path)
    restored._load()
    restored._publish()
    monkeypatch.setattr(diagnostics, "_sink", restored)
    service, _, _ = report_service(1)
    archive = service.download_complete_report(ACTOR)
    with zipfile.ZipFile(io.BytesIO(archive["content"])) as zipped:
        row = json.loads(zipped.read("operations.jsonl").splitlines()[0])
        assert all(e["actor"] == "system" for e in row["milestones"].values())
        assert row["milestones"]["verification"]["feature_outcome"] == "unknown"
        assert row["milestones"]["verification"]["verification_reason"] == "malformed_result"
        health = json.loads(zipped.read("diagnostic-health.json"))
        assert "counter_provenance" in health["sink"]["observation"]
    from services.recovery_report import _operation_report

    ordinary = _operation_report()
    assert ordinary["operations"][0]["milestones"]["scope_entry"]["actor"] == "system"
    assert "counter_provenance" in ordinary


def test_provenance_survives_restarts_without_recounting(tmp_path, monkeypatch):
    from uuid import uuid4

    from tests.test_recovery_evidence_bundle import event

    monkeypatch.setattr(diagnostics, "MAX_OPERATIONS", 1)
    sink = diagnostics.DiagnosticSink(tmp_path)
    sink.dropped = 3
    sink.emission_failures = 2
    sink.unknown_stages = 4
    sink._accept(event(uuid4().hex, "settled", "operation"))
    sink._accept(event(uuid4().hex, "entered", "operation"))
    sink._publish()
    for _ in range(3):
        sink = diagnostics.DiagnosticSink(tmp_path)
        sink._load()
        sink._publish()
        report = sink.report()
        assert report["counter_provenance"]["current"]["dropped"] == 0
        assert report["counter_provenance"]["historical"]["dropped"] == 3
        assert report["emission_failures"] == 2
        assert report["unknown_stages"] == 4
        assert report["eviction_provenance"]["capacity"]["count"] == 1


@pytest.mark.asyncio
async def test_pending_verification_cancellation_and_concurrent_caller_keep_identity(monkeypatch):
    events = []
    checking = asyncio.Event()
    monkeypatch.setattr(diagnostics, "offer", lambda event: events.append(dict(event)))
    monkeypatch.setattr(startup, "_steps", {})

    async def work():
        return await drain_thread(lambda: False)

    async def verify(_):
        checking.set()
        await asyncio.Event().wait()

    running = asyncio.create_task(
        startup.run(
            work(), 0.01, "proc_config_import", cancel_on_deadline=False, completion_check=verify
        )
    )
    try:
        await asyncio.wait_for(checking.wait(), 1)
        async with asyncio.timeout(1):
            while startup.report()[0]["state"] != "deadline_elapsed_pending":
                await asyncio.sleep(0)
        ref = startup.report()[0]["reference"]
        with evidence.scope() as unrelated:
            evidence.emit("proc_config_import", "observed")
            assert unrelated.reference != ref
        running.cancel()
        with pytest.raises(asyncio.CancelledError):
            await running
        assert startup.report()[0]["feature"]["verification_reason"] == "checker_cancelled"
        mine = [e for e in events if e["reference"] == ref]
        assert {e["actor"] for e in mine} == {"system"}
        assert {e["origin"] for e in mine} == {"startup"}
        assert any(e["state"] == "deadline_elapsed_pending" for e in mine)
        assert any(e["state"] == "cancelled_outcome_unconfirmed" for e in mine)
        assert next(e for e in mine if e["state"] == "result_returned")["value_boolean"] is False
        assert {e["actor"] for e in events if e["reference"] == unrelated.reference} == {
            "unavailable_not_collected"
        }
    finally:
        if not running.done():
            running.cancel()
            await asyncio.gather(running, return_exceptions=True)


def test_actual_sink_encoding_failure_is_counted_without_recursion(monkeypatch):
    sink = diagnostics.DiagnosticSink()
    monkeypatch.setattr(diagnostics, "_sink", sink)
    with evidence.scope():
        with monkeypatch.context() as fault:
            fault.setattr(diagnostics, "encoded", Mock(side_effect=OSError("encoding unavailable")))
            evidence.emit("proc_config_import", "failed")
    assert sink.emission_failures == 1
    assert sink.dropped == 1
    assert sink.critical_dropped == 1


def test_oversized_eviction_history_cannot_claim_available():
    sink = diagnostics.DiagnosticSink()
    sink._restore_provenance(
        {"eviction_provenance": {str(i): {} for i in range(5)}, "eviction_history_available": True}
    )
    assert sink.report()["eviction_history_available"] is False
    assert sink.invalid == 1


@pytest.mark.parametrize(
    "label,field",
    [
        ("warm_profile_cache", "execution"),
        ("warm_profile_cache", "availability"),
        ("warm_name_cache", "persistence"),
        ("build_player_stats_cache", "kind"),
        ("build_player_stats_cache", "last_kvk_state"),
        ("build_player_stats_cache", "last_kvk_verification"),
        ("rehydrate_tracked_views", "restoration_status"),
        ("rehydrate_tracked_views", "failed"),
        ("proc_config_import", "import_reported_success"),
    ],
)
@pytest.mark.parametrize("value", [[], {}, object()])
def test_malformed_consumed_fields_are_unknown_without_inspecting_objects(label, field, value):
    result = project(label, {field: value}, checked=True)
    assert result["feature_outcome"] == "unknown"
    assert result["verification_reason"] == "malformed_result"


@pytest.mark.asyncio
async def test_worker_failure_does_not_claim_pending_or_malformed_verification(monkeypatch):
    monkeypatch.setattr(startup, "_steps", {})
    checker = Mock(side_effect=AssertionError("Must not run"))

    async def failed():
        raise OSError("inert original worker failure")

    assert await startup.run(failed(), 5, "proc_config_import", completion_check=checker) is None
    checker.assert_not_called()
    assert startup.report()[0]["feature"]["feature_outcome"] == "unknown"
    assert startup.report()[0]["feature"]["verification_reason"] == "not_reached"


@pytest.mark.asyncio
async def test_failed_optional_projection_preserves_result_and_explains_unknown(monkeypatch):
    monkeypatch.setattr(startup, "_steps", {})
    monkeypatch.setattr(startup, "project", Mock(side_effect=OSError("projection unavailable")))

    async def work():
        return True

    assert await startup.run(work(), 5, "proc_config_import") is True
    assert startup.report()[0]["feature"] == {
        "feature_outcome": "unknown",
        "verification_reason": "projection_unavailable",
        "verification_source": "unavailable",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("stop", ["failure", "cancellation", "deadline"])
async def test_pre_return_verification_reason_survives_restart_and_both_reports(
    monkeypatch, tmp_path, stop
):
    import io
    import json
    import zipfile

    from services.recovery_report import _operation_report
    from tests.test_guided_recovery import ACTOR
    from tests.test_recovery_report import report_service

    sink = diagnostics.DiagnosticSink(tmp_path)
    monkeypatch.setattr(diagnostics, "_sink", sink)
    monkeypatch.setattr(startup, "_steps", {})
    entered = asyncio.Event()
    checker = Mock(side_effect=AssertionError("Unreached checker must not run"))

    async def work():
        entered.set()
        if stop == "failure":
            raise OSError("inert original failure")
        await asyncio.Event().wait()

    running = asyncio.create_task(
        startup.run(
            work(),
            0.01 if stop == "deadline" else 5,
            "proc_config_import",
            completion_check=checker,
        )
    )
    try:
        await asyncio.wait_for(entered.wait(), 1)
        if stop == "cancellation":
            running.cancel()
            with pytest.raises(asyncio.CancelledError):
                await running
        else:
            assert await running is None
    finally:
        if not running.done():
            running.cancel()
            await asyncio.gather(running, return_exceptions=True)
    checker.assert_not_called()
    reference = startup.report()[0]["reference"]
    sink.start().close()
    restored = diagnostics.DiagnosticSink(tmp_path)
    restored._load()
    restored._publish()
    monkeypatch.setattr(diagnostics, "_sink", restored)
    startup._steps.clear()  # No live startup summary survives the simulated restart.
    ordinary = next(r for r in _operation_report()["operations"] if r["reference"] == reference)
    service, _, _ = report_service(1)
    archive = service.download_complete_report(ACTOR)
    with zipfile.ZipFile(io.BytesIO(archive["content"])) as zipped:
        downloaded = next(
            r
            for r in map(json.loads, zipped.read("operations.jsonl").splitlines())
            if r["reference"] == reference
        )
    for row in (ordinary, downloaded):
        verification = row["milestones"]["verification"]
        assert verification["feature_outcome"] == "unknown"
        assert verification["verification_reason"] == "not_reached"
        assert verification["verification_source"] == "proc_config_import"
        assert verification["actor"] == "system"
        assert "parent_return" not in row["milestones"]
        if stop == "failure":
            assert row["first_failure"]["error_type"] == "OSError"
