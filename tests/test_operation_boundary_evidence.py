"""P01.1 real worker, overload, persistence and diagnostic failure qualification."""

import ast
import asyncio
from datetime import UTC, datetime
import json
from pathlib import Path
import threading
from unittest.mock import Mock
from uuid import uuid4

import pytest

from core import (
    operation_evidence as evidence,
    operation_timing as timing,
    startup_diagnostics as startup,
)
from core.owned_work import drain_thread
from services import operation_diagnostics as diagnostics
from services.configuration_attempt_recovery import verify_startup_import


def successful_result():
    return True, dict(
        attempt_id=str(uuid4()),
        attempt_recording="recorded",
        attempt_outcome="reported_success",
        secret="do-not-copy",
    )


def event(reference=None, state="observed", **extra):
    return dict(
        reference=reference or uuid4().hex,
        stage="proc_config_import",
        state=state,
        observed_utc=datetime.now(UTC).isoformat(),
        **extra,
    )


@pytest.mark.parametrize("missing", ["reference", "stage", "state", "observed_utc"])
def test_incomplete_restored_event_cannot_poison_later_publication(tmp_path, missing):
    malformed = event(state="settled")
    malformed["stage"] = "operation"
    del malformed[missing]
    path = tmp_path / "observations.json"
    path.write_text(
        json.dumps(
            {
                "schema": "operation-observations/1",
                "operations": [{"transitions": [malformed]}],
            }
        ),
        encoding="utf-8",
    )
    sink = diagnostics.DiagnosticSink(tmp_path).start()
    fresh = event(state="failed")
    assert sink.offer(fresh)
    sink.close()
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["sink_failures"] == 1
    assert [row["reference"] for row in document["operations"]] == [fresh["reference"]]
    assert document["operations"][0]["first_failure"] == fresh
    assert document["status"] == "closed"


@pytest.fixture
def capture(monkeypatch):
    events = []
    monkeypatch.setattr(diagnostics, "offer", events.append)
    monkeypatch.setattr(startup, "_steps", {})
    return events


@pytest.mark.asyncio
@pytest.mark.parametrize("fault", ["clock", "emitter", "projection"])
async def test_optional_fault_never_prevents_entry_or_replaces_result_error(monkeypatch, fault):
    broken = Mock(side_effect=RuntimeError("diagnostic failure"))
    if fault == "clock":
        monkeypatch.setattr(timing, "perf_counter", broken)
    elif fault == "emitter":
        monkeypatch.setattr(diagnostics, "offer", broken)
    else:
        monkeypatch.setattr(evidence, "result_facts", broken)
    result = successful_result()
    calls = []

    def work():
        calls.append(1)
        return result

    original = ValueError("original business error")

    def fail():
        calls.append(2)
        raise original

    with timing.timing_scope():
        assert await drain_thread(work) is result
        with pytest.raises(ValueError) as caught:
            await drain_thread(fail)
        assert caught.value is original
        with pytest.raises(ValueError) as caught, timing.timed_stage("private_response"):
            raise original
        assert caught.value is original
    assert calls == [1, 2]


@pytest.mark.asyncio
async def test_late_startup_preserves_tuple_and_mandatory_receipt(capture):
    entered, release = threading.Event(), threading.Event()
    result = successful_result()
    calls = []

    def work():
        calls.append(1)
        entered.set()
        assert release.wait(5)
        return result

    task = asyncio.create_task(
        startup.run(
            drain_thread(work),
            0.001,
            "proc_config_import",
            cancel_on_deadline=False,
            completion_check=verify_startup_import,
        )
    )
    try:
        for _ in range(1000):
            if entered.is_set() and startup.report()[0]["state"] == "deadline_elapsed_pending":
                break
            await asyncio.sleep(0.001)
        assert not task.done()
    finally:
        release.set()
    assert await task is result
    assert calls == [1]
    row = startup.report()[0]
    assert row["state"] == "completed_after_deadline"
    assert row["completion"]["attempt_id"] == result[1]["attempt_id"]
    assert len({item["reference"] for item in capture}) == 1
    assert "do-not-copy" not in str(capture) + str(row)


@pytest.mark.asyncio
async def test_repeated_shutdown_cancel_drains_and_keeps_worker_attempt(capture):
    entered, release, finished = threading.Event(), threading.Event(), threading.Event()
    result = successful_result()

    def work():
        entered.set()
        assert release.wait(5)
        finished.set()
        return result

    task = asyncio.create_task(
        startup.run(
            drain_thread(work),
            60,
            "proc_config_import",
            cancel_on_deadline=False,
            completion_check=verify_startup_import,
        )
    )
    try:
        for _ in range(1000):
            if entered.is_set():
                break
            await asyncio.sleep(0.001)
        for _ in range(3):
            task.cancel()
            await asyncio.sleep(0.001)
            assert not task.done()
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert finished.is_set()
    row = startup.report()[0]
    assert row["observer"] == "cancelled" and row["physical"] == "settled"
    assert row["worker_result"]["attempt_id"] == result[1]["attempt_id"]
    assert row["worker_result"]["reported_success"] is True
    assert not row["returned"]  # Child success is not parent verification.


@pytest.mark.asyncio
async def test_verification_failure_and_diagnostic_failure_do_not_erase_result(
    monkeypatch, capture
):
    result = successful_result()

    async def work():
        return result

    async def verify(value):
        assert value is result
        raise OSError("private readback failure")

    assert await startup.run(work(), 10, "proc_config_import", completion_check=verify) is result
    row = startup.report()[0]
    assert row["state"] == "verification_unavailable"
    assert row["result"]["attempt_id"] == result[1]["attempt_id"]
    assert row["returned"]
    monkeypatch.setattr(startup, "_record", Mock(side_effect=OSError()))
    assert await startup.run(work(), 10, "proc_config_import", completion_check=verify) is result


@pytest.mark.asyncio
async def test_cancel_during_verification_keeps_completed_import(capture):
    result = successful_result()
    entered, release = threading.Event(), threading.Event()

    async def work():
        return result

    def readback():
        entered.set()
        assert release.wait(5)

    async def verify(_):
        await drain_thread(readback)

    task = asyncio.create_task(
        startup.run(work(), 10, "proc_config_import", completion_check=verify)
    )
    try:
        for _ in range(1000):
            if entered.is_set():
                break
            await asyncio.sleep(0.001)
        task.cancel()
        await asyncio.sleep(0.001)
        assert not task.done()
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    row = startup.report()[0]
    assert row["returned"] and row["result"]["attempt_id"] == result[1]["attempt_id"]


def test_bounded_ingress_reserves_terminal_capacity_and_rejects_payloads():
    sink = diagnostics.DiagnosticSink(capacity=8, reserve=2)
    for _ in range(6):
        assert sink.offer(event())
    assert not sink.offer(event())
    assert sink.offer(event(state="failed"))
    assert sink.offer(event(state="settled"))
    assert not sink.offer(event(state="failed"))
    assert not sink.offer(event(secret="x" * 1000000))
    with sink.lock:
        assert not sink.offer(event())  # No lock wait, including the caller thread.
    assert len(sink.queue) == 8 and sink.dropped == 4
    sink.start()
    sink.close()
    assert not sink.thread.is_alive()


def test_restart_preserves_first_failure_correlation_and_late_result(tmp_path):
    sink = diagnostics.DiagnosticSink(tmp_path)
    reference = uuid4().hex
    first = event(
        reference, "failed", error_type="ProgrammingError", sqlstate="42000", native_error=51421
    )
    sink.offer(first)
    for n in range(40):
        sink.offer(event(reference, "entered" if n % 2 else "observed"))
    result = successful_result()
    sink.offer(event(reference, "settled", **evidence.result_facts(result)))
    sink.offer(event(reference, "cancelled_outcome_unconfirmed"))
    sink.start().close()
    restored = diagnostics.DiagnosticSink(tmp_path).start()
    restored.close()
    row = restored.report()["operations"][0]
    assert row["reference"] == reference and row["first_failure"] == first
    assert row["result"]["attempt_id"] == result[1]["attempt_id"]
    assert row["latest"]["state"] == "cancelled_outcome_unconfirmed"
    assert row["omitted"] >= 10 and not row["complete"]
    assert len(restored.records[reference]["transitions"]) <= 32
    assert "do-not-copy" not in (tmp_path / "observations.json").read_text()


@pytest.mark.parametrize("fault", ["corrupt", "oversize", "replace"])
def test_bad_persistence_degrades_diagnostics_only(tmp_path, monkeypatch, fault):
    path = tmp_path / "observations.json"
    if fault == "corrupt":
        path.write_text('{"secret":"private", bad')
    elif fault == "oversize":
        monkeypatch.setattr(diagnostics, "MAX_FILE", 500)
        path.write_bytes(b"x" * 501)
    else:
        monkeypatch.setattr(diagnostics.os, "replace", Mock(side_effect=PermissionError()))
    sink = diagnostics.DiagnosticSink(tmp_path)
    sink.offer(event(state="failed"))
    sink.start().close()
    report = sink.report()
    assert report["sink_failures"] >= 1
    assert report["authority"] == "diagnostic_only"
    assert "private" not in str(report)


def test_stalled_sink_does_not_block_business_but_remains_owned_until_join(tmp_path, monkeypatch):
    entered, release, stopped = threading.Event(), threading.Event(), threading.Event()
    sink = diagnostics.DiagnosticSink(tmp_path)
    original = sink._publish

    def stalled():
        entered.set()
        assert release.wait(5)
        original()

    monkeypatch.setattr(sink, "_publish", stalled)
    sink.start()
    assert entered.wait(5)
    assert sink.offer(event())
    closer = threading.Thread(target=lambda: (sink.close(), stopped.set()))
    closer.start()
    try:
        assert not stopped.wait(0.02)
        assert sink.report()["worker_alive"]
    finally:
        release.set()
        closer.join(5)
    assert stopped.is_set() and not sink.thread.is_alive()


def test_projection_capacity_keeps_unresolved_first_failures_and_report_is_bounded(monkeypatch):
    sink = diagnostics.DiagnosticSink()
    monkeypatch.setattr(diagnostics, "MAX_OPERATIONS", 16)
    first = event(state="failed")
    sink._accept(first)
    for _ in range(15):
        sink._accept(event(state="failed"))
    sink._accept(event())
    sink._publish()
    assert sink.dropped == 1 and first["reference"] in sink.records
    assert len(json.dumps(sink.report(), indent=2).encode()) < 16384
    snapshot = sink.report()
    snapshot["operations"].clear()
    assert sink.report()["operations"]


@pytest.mark.asyncio
async def test_known_mge_holder_is_attributed_without_changing_serialization(capture):
    from mge.mge_board_ownership import presentation_owner

    entered, release = asyncio.Event(), asyncio.Event()
    bot = object()
    holder = None

    async def first():
        nonlocal holder
        with evidence.scope():
            holder = evidence.reference()
            async with presentation_owner(bot, 1):
                entered.set()
                await release.wait()

    async def second():
        with evidence.scope():
            async with presentation_owner(bot, 1):
                return "done"

    first_task = asyncio.create_task(first())
    await entered.wait()
    second_task = asyncio.create_task(second())
    await asyncio.sleep(0)
    try:
        assert not second_task.done()
        assert any(
            row.get("local_holder_reference") == holder and row["reference"] != holder
            for row in capture
        )
    finally:
        release.set()
    await first_task
    assert await second_task == "done"


@pytest.mark.asyncio
async def test_actual_boot_wrapper_keeps_report_and_never_falls_back_after_entry():
    source = Path(__file__).resolve().parents[1] / "bot_instance.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    definition = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_proc_import_wrapper"
    )
    result = successful_result()
    calls = []

    async def offload(**_):
        calls.append(1)
        return result

    fallback = Mock(side_effect=AssertionError("must not replay"))
    namespace = dict(run_proc_config_import_offload=offload, run_blocking=fallback)
    exec(compile(ast.Module(body=[definition], type_ignores=[]), str(source), "exec"), namespace)
    assert await namespace["_proc_import_wrapper"]() is result

    async def failed(**_):
        raise OSError("unknown execution")

    namespace["run_proc_config_import_offload"] = failed
    with pytest.raises(OSError):
        await namespace["_proc_import_wrapper"]()
    fallback.assert_not_called()
    schedule = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "schedule_bg"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "proc_config_import"
    )
    assert any(
        kw.arg == "cancel_on_deadline" and kw.value.value is False for kw in schedule.keywords
    )


@pytest.mark.asyncio
async def test_unrecorded_terminal_receipt_still_fails_verification(capture):
    result = successful_result()
    result[1]["attempt_recording"] = "unrecorded"
    result[1]["import_reported_success"] = True

    async def work():
        return result

    assert (
        await startup.run(work(), 10, "proc_config_import", completion_check=verify_startup_import)
        is result
    )
    row = startup.report()[0]
    assert row["state"] == "failed"
    assert row["result"]["import_reported_success"] is True
    assert row["result"]["attempt_recording"] == "unrecorded"


@pytest.mark.asyncio
async def test_diagnostic_uuid_failure_keeps_business_entry_and_releases_slot(monkeypatch):
    from services import cache_admission_diagnostics as admission

    sink = diagnostics.DiagnosticSink()
    monkeypatch.setattr(diagnostics, "_sink", sink)
    slots = threading.BoundedSemaphore(1)
    monkeypatch.setattr(evidence, "_slots", slots)
    broken = Mock(side_effect=OSError("entropy unavailable"))
    monkeypatch.setattr(evidence, "uuid4", broken)
    monkeypatch.setattr(admission, "uuid4", broken)
    calls = []

    async def work():
        calls.append(1)
        assert admission.identity()["correlation_id"] is None
        return "original result"

    assert await startup.run(work(), 10, "proc_config_import") == "original result"
    assert calls == [1]
    assert slots.acquire(blocking=False)  # Initialization failure returned its slot.
    slots.release()
    assert sink.report()["context_losses"] == 1


@pytest.mark.asyncio
async def test_context_capacity_loss_is_visible_and_does_not_limit_business(monkeypatch):
    sink = diagnostics.DiagnosticSink()
    monkeypatch.setattr(diagnostics, "_sink", sink)
    monkeypatch.setattr(evidence, "_slots", threading.BoundedSemaphore(1))
    entered, release = asyncio.Event(), asyncio.Event()

    async def holder():
        with evidence.scope():
            entered.set()
            await release.wait()

    pending = asyncio.create_task(holder())
    await entered.wait()
    try:
        with evidence.scope() as observation:
            assert observation.reference is None
            assert await drain_thread(lambda: "still executes") == "still executes"
        assert sink.report()["context_losses"] == 1
    finally:
        release.set()
        await pending


def test_restart_load_preserves_losses_already_recorded_by_new_producers(tmp_path, monkeypatch):
    previous = diagnostics.DiagnosticSink(tmp_path)
    previous.dropped, previous.failures = 11, 13
    previous.evicted, previous.context_losses = 17, 19
    previous.start().close()

    restored = diagnostics.DiagnosticSink(tmp_path)
    monkeypatch.setattr(diagnostics, "_sink", restored)
    # Offers can arrive before the writer finishes loading its old projection.
    assert not restored.offer({"unsafe": object()})
    diagnostics.note_context_loss()
    diagnostics.note_context_loss()
    restored.failures, restored.evicted = 1, 3
    restored.start().close()
    expected = dict(dropped=12, sink_failures=14, evicted=20, context_losses=21)
    assert {name: restored.report()[name] for name in expected} == expected
    again = diagnostics.DiagnosticSink(tmp_path).start()
    again.close()
    assert {name: again.report()[name] for name in expected} == expected


def test_saturated_diagnostic_counter_stays_readable_after_restart(tmp_path):
    previous = diagnostics.DiagnosticSink(tmp_path)
    previous.dropped = 2**63 - 1
    previous.start().close()
    restored = diagnostics.DiagnosticSink(tmp_path)
    assert not restored.offer({"unsafe": object()})
    restored.start().close()
    again = diagnostics.DiagnosticSink(tmp_path).start()
    again.close()
    assert again.report()["dropped"] == 2**63 - 1
    assert again.report()["sink_failures"] == 0


def test_projection_batches_offers_and_close_interrupts_publish_delay(tmp_path, monkeypatch):
    sink = diagnostics.DiagnosticSink(tmp_path)
    waiting = threading.Event()
    wait = sink.closing.wait
    published = []
    publish = sink._publish

    def batch_wait(timeout):
        waiting.set()
        return wait(timeout)

    def record_publish():
        published.append(len(sink.records))
        publish()

    monkeypatch.setattr(diagnostics, "PUBLISH_INTERVAL", 60)
    monkeypatch.setattr(sink.closing, "wait", batch_wait)
    monkeypatch.setattr(sink, "_publish", record_publish)
    sink.start()
    try:
        assert waiting.wait(5)
        for _ in range(20):
            assert sink.offer(event(state="failed"))
        assert published == []
    finally:
        # A 60-second configured test delay is interrupted, never waited out.
        sink.close()
    assert published == [20]
    assert not sink.thread.is_alive()
    assert len(sink.report()["operations"]) > 0
