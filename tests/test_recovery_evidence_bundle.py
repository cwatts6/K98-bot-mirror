"""Real archive, milestones, access and ownership qualification for P01.2a."""

import asyncio
from datetime import UTC, datetime
import hashlib
import io
import json
import threading
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4
import zipfile

import pytest

from core import startup_diagnostics as startup
from core.owned_work import drain_thread
from services import operation_diagnostics as diagnostics, recovery_evidence_bundle as bundle
from services.recovery_service import RecoveryActor, SourceConflict
from tests.test_guided_recovery import ACTOR
from tests.test_recovery_report import report_service


def event(reference, state="observed", stage="proc_config_import", **facts):
    return (
        dict(
            schema="operation-boundary/2",
            event_id=uuid4().hex,
            sequence=0,
            role="parent",
            origin="code_owned",
            actor="unavailable_not_collected",
            reference=reference,
            stage=stage,
            state=state,
            observed_utc=datetime.now(UTC).isoformat(),
        )
        | facts
    )


def test_published_generation_is_isolated_from_writer_and_report_reader():
    sink = diagnostics.DiagnosticSink()
    ref, child = uuid4().hex, uuid4().hex
    sink._accept(event(ref, "entered", "operation"))
    sink._accept(
        event(
            ref,
            "entered",
            "worker_execution",
            role="child",
            child_reference=child,
            parent_reference=ref,
        )
    )
    sink._publish()
    generation = sink.snapshot
    original = diagnostics.encoded(generation)
    sink._accept(
        event(
            ref,
            "failed",
            "worker_execution",
            role="child",
            child_reference=child,
            parent_reference=ref,
            error_type="OSError",
        )
    )
    sink._accept(event(ref, "deadline_elapsed_pending"))
    sink._publish()
    assert diagnostics.encoded(generation) == original
    row = sink.full_snapshot()["operations"][0]
    assert row["children"][child]["failure"] is True
    row["children"][child]["failure"] = False
    row["milestones"]["failure"]["error_type"] = "changed"
    row["transitions"].clear()
    assert sink.full_snapshot()["operations"][0]["first_failure"]["error_type"] == "OSError"
    assert sink.full_snapshot()["operations"][0]["children"][child]["failure"] is True
    for frozen, size in sink._published_rows.values():
        assert size == len(diagnostics.encoded(frozen))


def test_published_row_cache_evicts_with_retention(monkeypatch):
    monkeypatch.setattr(diagnostics, "MAX_OPERATIONS", 2)
    sink = diagnostics.DiagnosticSink()
    for _ in range(4):
        ref = uuid4().hex
        sink._accept(event(ref, "settled", "operation"))
        sink._publish()
    assert len(sink._published_rows) == len(sink.records) == 2
    assert set(sink._published_rows) == set(sink.records)
    assert not sink._dirty_rows


def test_chunked_publication_keeps_exact_json_bytes_and_prewrite_bound(tmp_path, monkeypatch):
    document = {
        "schema": "test",
        "operations": [{"value": 'quote" slash\\ snowman\u2603'}],
        "nested": {"values": [True, None, 1.25]},
        "tail": "last",
    }
    assert b"".join(diagnostics.encoded_document_parts(document)) == diagnostics.encoded(document)
    sink = diagnostics.DiagnosticSink(tmp_path)
    sink._accept(event(uuid4().hex, "settled", "operation"))
    sink._publish()
    original = (tmp_path / "observations-v2.json").read_bytes()
    acknowledged = sink.publication["v2"]["last_success"]
    monkeypatch.setattr(diagnostics, "MAX_FILE", 20)
    sink._write("v2", "observations-v2.json", document)
    assert (tmp_path / "observations-v2.json").read_bytes() == original
    assert sink.publication["v2"]["last_success"] == acknowledged
    assert sink.publication["v2"]["status"] == "failed"
    assert not (tmp_path / "observations-v2.tmp").exists()


@pytest.mark.asyncio
async def test_false_children_parent_verification_and_real_archive(monkeypatch, tmp_path):
    sink = diagnostics.DiagnosticSink(tmp_path)
    monkeypatch.setattr(diagnostics, "_sink", sink)
    monkeypatch.setattr(startup, "_steps", {})

    async def work():
        assert await drain_thread(lambda: False) is False
        assert await drain_thread(lambda: True) is True
        return {"restoration_status": "complete", "attached": 21}

    async def verify(result):
        return result

    result = await startup.run(work(), 10, "rehydrate_tracked_views", completion_check=verify)
    assert result["attached"] == 21
    sink.start().close()
    row = sink.full_snapshot()["operations"][0]
    assert len(row["children"]) == 2
    assert {c["value_boolean"] for c in row["children"].values()} == {False, True}
    assert row["milestones"]["parent_return"]["value_kind"] == "dict"
    assert row["milestones"]["verification"]["feature_outcome"] == "succeeded"
    service, _, records = report_service(21)
    report = service.download_complete_report(ACTOR)
    assert hashlib.sha256(report["content"]).hexdigest() == report["sha256"]
    with zipfile.ZipFile(io.BytesIO(report["content"])) as archive:
        meta = json.loads(archive.read("manifest.json"))
        assert meta["schema"] == "k98-evidence-bundle/1" and not meta["atomic_snapshot"]
        for name in archive.namelist():
            if name != "manifest.json":
                data = archive.read(name)
                assert len(data) == meta["components"][name]["bytes"]
                assert hashlib.sha256(data).hexdigest() == meta["components"][name]["sha256"]
        rows = [json.loads(line) for line in archive.read("operations.jsonl").splitlines()]
        assert rows[0]["milestones"]["verification"]["feature_outcome"] == "succeeded"
        assert len(archive.read("incidents.jsonl").splitlines()) == len(records)


def test_milestones_survive_detail_and_restart_without_count_inflation(tmp_path):
    sink = diagnostics.DiagnosticSink(tmp_path)
    sink.directory.mkdir(exist_ok=True)
    ref = uuid4().hex
    events = [
        event(ref, "entered", "operation"),
        event(ref, "entered", "worker_execution"),
        event(ref, "deadline_elapsed_pending"),
        event(ref, "cancelled_draining"),
        event(ref, "failed", error_type="OSError"),
        event(ref, "result_returned", value_kind="boolean", value_boolean=False),
        event(ref, "completed", feature_outcome="succeeded"),
        event(ref, "settled", "operation"),
    ]
    for item in events:
        sink._accept(item)
    for index in range(2000):
        sink._accept(event(ref, "observed" if index % 2 else "running"))
    sink._publish()
    before = sink.records[ref]
    assert set(before["milestones"]) == diagnostics.SLOTS
    assert before["first_failure"] == events[4] and not before["complete"]
    assert len(diagnostics.encoded(before)) <= 32768
    assert before["trimmed"] > 1900
    restored = diagnostics.DiagnosticSink(tmp_path)
    restored._load()
    assert restored.records[ref]["milestones"] == before["milestones"]
    assert restored.records[ref]["trimmed"] == before["trimmed"]
    assert restored.records[ref]["omitted"] == before["omitted"]
    restored._accept(events[2])
    assert restored.records[ref]["deadline_count"] == 1


def test_v2_failure_keeps_memory_and_v1_publication_independent(monkeypatch, tmp_path):
    sink = diagnostics.DiagnosticSink(tmp_path)
    sink._accept(event(uuid4().hex, "failed", error_type="ValueError"))
    original = diagnostics.os.replace

    def replace(source, target):
        if target.name == "observations-v2.json":
            raise PermissionError("private")
        return original(source, target)

    monkeypatch.setattr(diagnostics.os, "replace", replace)
    sink._publish()
    assert sink.full_snapshot()["operations"]
    health = sink.report()["publication"]
    assert health["v2"]["status"] == "failed" and "last_success" not in health["v2"]
    assert health["v1"]["status"] == "published"
    assert "private" not in str(health)


def test_corrupt_original_preserved_and_occupied_slot_refuses_overwrite(tmp_path):
    path = tmp_path / "observations-v2.json"
    path.write_bytes(b"broken one")
    sink = diagnostics.DiagnosticSink(tmp_path)
    sink._load()
    assert (tmp_path / "observations-v2.invalid").read_bytes() == b"broken one"
    path.write_bytes(b"broken two")
    again = diagnostics.DiagnosticSink(tmp_path)
    again._load()
    again._accept(event(uuid4().hex))
    again._publish()
    assert path.read_bytes() == b"broken two"
    assert again.report()["publication"]["v2"]["status"] == "failed"


def test_optional_sources_fail_independently_and_store_is_not_empty(monkeypatch):
    monkeypatch.setattr(diagnostics, "full_snapshot", Mock(side_effect=OSError()))
    monkeypatch.setattr(startup, "report", Mock(side_effect=ValueError()))
    service, store, _ = report_service(1)
    store.report_page.side_effect = OSError("password=do-not-export")
    report = service.download_complete_report(ACTOR)
    assert not report["complete"] and report["incident_continuation"]
    with zipfile.ZipFile(io.BytesIO(report["content"])) as archive:
        meta = json.loads(archive.read("manifest.json"))
        assert meta["components"]["incidents.jsonl"]["status"] == "unavailable"
        assert meta["components"]["operations.jsonl"]["status"] == "unavailable"
        assert meta["components"]["startup.json"]["status"] == "unavailable"
        assert "diagnostic-health.json" in archive.namelist()
        assert b"do-not-export" not in archive.read("manifest.json")


def test_continuations_are_bound_single_use_expire_and_reconstruct(monkeypatch):
    service, _, _ = report_service()
    original = b'{"row":"' + b"a" * 32000 + b'"}\n'
    with bundle.report_request():
        token = bundle.retain(service, ACTOR, {"operations.jsonl": original * 3}, {})
    with pytest.raises(SourceConflict):
        service.download_diagnostic_part(RecoveryActor(9, 2, 3), token, 65536)
    result, previous = b"", None
    while token:
        old = token
        report = service.download_diagnostic_part(ACTOR, token, 65536)
        with zipfile.ZipFile(io.BytesIO(report["content"])) as archive:
            meta = json.loads(archive.read("manifest.json"))
            assert meta["previous_sha256"] == previous
            result += archive.read("operations.jsonl")
        previous = report["sha256"]
        token = report["diagnostic_token"]
        with pytest.raises(SourceConflict):
            service.download_diagnostic_part(ACTOR, old, 65536)
    assert result == original * 3
    with bundle.report_request():
        tokens = [bundle.retain(service, ACTOR, {"startup.json": b"{}"}, {}) for _ in range(3)]
    assert tokens[0] not in bundle._sessions and len(bundle._sessions) == 2
    monkeypatch.setattr(bundle.time, "monotonic", lambda: 1e20)
    with pytest.raises(SourceConflict):
        service.download_diagnostic_part(ACTOR, tokens[1])


def test_report_admission_zero_queue_and_stale_context():
    with bundle.report_request():
        result = []

        def competing():
            try:
                with bundle.report_request():
                    result.append("incorrectly entered")
            except SourceConflict:
                result.append("busy")

        thread = threading.Thread(target=competing)
        thread.start()
        thread.join(1)
        assert result == ["busy"]
    with bundle.report_request():
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize("cancellations", [1, 3])
@pytest.mark.parametrize("worker_outcome", ["success", "lease_check", "error"])
async def test_cancelled_report_retains_slot_until_physical_settlement(
    monkeypatch, cancellations, worker_outcome
):
    from ui.views import recovery_view as view

    entered, release = threading.Event(), threading.Event()

    def work():
        entered.set()
        release.wait(5)
        if worker_outcome == "lease_check":
            bundle._active.check()
        elif worker_outcome == "error":
            raise ValueError("Worker failed while cancellation was draining")
        return {}

    async def call(*_):
        return await drain_thread(work)

    monkeypatch.setattr(view, "call", call)
    pending = asyncio.create_task(view.report_call("download_report"))
    while not entered.is_set():
        await asyncio.sleep(0.001)
    try:
        for _ in range(cancellations):
            pending.cancel()
            await asyncio.sleep(0.001)
            assert not pending.done()
            with pytest.raises(SourceConflict):
                with bundle.report_request():
                    pass
        assert bundle._active.cancelled.is_set()
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await pending
    with bundle.report_request():
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome", ["succeeded", "partial", "unknown"])
async def test_late_verification_replaces_provisional_milestone_after_trim_and_restore(
    monkeypatch, tmp_path, outcome
):
    sink = diagnostics.DiagnosticSink(tmp_path)
    monkeypatch.setattr(diagnostics, "_sink", sink)
    monkeypatch.setattr(startup, "_steps", {})
    checking, release = asyncio.Event(), asyncio.Event()

    async def work():
        return True

    async def verify(_):
        checking.set()
        await release.wait()
        if outcome == "unknown":
            raise OSError("Verifier unavailable")
        return {
            "kind": "player_cache_readback",
            "last_kvk_state": "succeeded" if outcome == "succeeded" else "failed",
            "last_kvk_verification": "original_snapshot",
        }

    pending = asyncio.create_task(
        startup.run(
            work(),
            0.01,
            "build_player_stats_cache",
            cancel_on_deadline=False,
            completion_check=verify,
        )
    )

    async def observe_deadline():
        await checking.wait()
        while startup.report()[0]["state"] != "deadline_elapsed_pending":
            await asyncio.sleep(0)

    try:
        await asyncio.wait_for(observe_deadline(), 1)
        assert startup.report()[0]["feature"]["feature_outcome"] == "not_checked"
    finally:
        release.set()
        await pending
    assert startup.report()[0]["feature"]["feature_outcome"] == outcome
    sink.start().close()
    ref = startup.report()[0]["reference"]
    for index in range(80):
        sink._accept(event(ref, "observed" if index % 2 else "running"))
    sink._publish()
    row = sink.records[ref]
    assert row["trimmed"] > 0
    assert row["milestones"]["deadline"]["feature_outcome"] == "not_checked"
    assert row["milestones"]["verification"]["feature_outcome"] == outcome
    restored = diagnostics.DiagnosticSink(tmp_path)
    restored._load()
    assert restored.records[ref]["milestones"]["verification"]["feature_outcome"] == outcome


@pytest.mark.asyncio
async def test_final_authorization_and_attachment_cleanup(monkeypatch):
    from ui.views import recovery_view as view

    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    seen = []

    async def send(**kw):
        seen.append(kw["file"].fp)
        raise RuntimeError("send failed")

    interaction = SimpleNamespace(followup=SimpleNamespace(send=send))
    with pytest.raises(RuntimeError):
        await view.send_report_attachment(
            interaction, ACTOR, {"content": b"{}", "filename": "report.json"}, "Report", None
        )
    assert seen[0].closed
    monkeypatch.setattr(view, "actor_for", Mock(side_effect=SourceConflict("changed config")))
    with pytest.raises(SourceConflict):
        await view.send_report_attachment(
            interaction, ACTOR, {"content": b"{}", "filename": "report.json"}, "Report", None
        )
    assert len(seen) == 1


def test_nonwaiting_runtime_registration_and_default_ownership(monkeypatch):
    from services import export_runtime_composition as runtime

    legacy = object()
    owner = runtime.RuntimeLifetime(legacy)
    monkeypatch.setattr(runtime, "_installed", owner)
    monkeypatch.setattr(runtime, "_runtime_stopped", False)
    with owner.reconfigure():
        with pytest.raises(SourceConflict):
            with runtime.report_caller_scope():
                pass
    with runtime.report_caller_scope() as observed:
        assert observed is legacy and len(owner._calls) == 1
    assert not owner._calls
    with owner.owned():
        assert len(owner._calls) == 1


def test_incident_overflow_discards_prefix_and_does_not_rescan(monkeypatch):
    import random

    service, store, records = report_service(2)
    random_text = random.Random(12).randbytes(400000).hex()
    records[0]["evidence"]["explanation"] = random_text
    report = service.download_complete_report(ACTOR, max_bytes=65536)
    assert not report["complete"] and report["count"] == 0 and report["incident_continuation"]
    assert store.report_page.call_count == 1
    with zipfile.ZipFile(io.BytesIO(report["content"])) as archive:
        meta = json.loads(archive.read("manifest.json"))
        assert meta["incident_after"] is None
        assert "incidents.jsonl" not in archive.namelist()
    # The normal budget still accommodates the largest contract-sized item.
    records[0]["evidence"]["explanation"] = random_text[:450000]
    report = service.download_complete_report(ACTOR)
    assert report["complete"] and report["count"] == 2


def test_summary_cardinality_bound_is_contributions_not_invented_distinct_count():
    service, _, records = report_service(300)
    for index, row in enumerate(records):
        row["evidence"]["outcome"] = "status_" + str(index)
    report = service.download_complete_report(ACTOR)
    with zipfile.ZipFile(io.BytesIO(report["content"])) as archive:
        summary = json.loads(archive.read("summary.json"))
        assert len(summary["groups"]) == 256
        assert summary["omitted_groups"] == "unknown"
        assert summary["other_contributions"]["groups"] == 44


def test_authorization_change_during_collection_emits_no_artifact():
    service, store, _ = report_service(21)
    original = store.report_page.side_effect

    def page(**kwargs):
        result = original(**kwargs)
        service.admin_id = 999
        return result

    store.report_page.side_effect = page
    with pytest.raises(SourceConflict):
        service.download_complete_report(ACTOR)
    assert store.report_page.call_count == 1


def test_deadline_stops_between_pages_without_native_detach(monkeypatch):
    service, store, _ = report_service(21)
    original = store.report_page.side_effect

    def page(**kwargs):
        result = original(**kwargs)
        bundle._active.deadline = 0
        return result

    store.report_page.side_effect = page
    report = service.download_complete_report(ACTOR)
    assert not report["complete"] and report["count"] == 0
    assert store.report_page.call_count == 1
    assert bundle._active is None


def test_runtime_absence_keeps_passive_diagnostics_without_activation(monkeypatch):
    import bot_config
    from services import export_runtime_composition as runtime, recovery_runtime as recovery

    for key, value in (("ADMIN_USER_ID", 1), ("GUILD_ID", 2), ("NOTIFY_CHANNEL_ID", 3)):
        monkeypatch.setattr(bot_config, key, value)
    monkeypatch.setattr(runtime, "_installed", None)
    monkeypatch.setattr(runtime, "_recovery_bundle", None)
    activate = Mock(side_effect=AssertionError("Must not activate"))
    monkeypatch.setattr(runtime, "install_configured_runtime", activate)
    monkeypatch.setattr(recovery, "_retry_admission", activate)
    result = recovery.call_recovery("download_complete_report", ACTOR)
    assert not result["complete"]
    activate.assert_not_called()
    with zipfile.ZipFile(io.BytesIO(result["content"])) as archive:
        assert "diagnostic-health.json" in archive.namelist()


def test_prior_acknowledgement_is_not_self_certification(tmp_path):
    sink = diagnostics.DiagnosticSink(tmp_path)
    sink._accept(event(uuid4().hex))
    sink._publish()
    first = json.loads((tmp_path / "observations-v2.json").read_bytes())
    assert "last_success" not in first["publication"]["v2"]
    acknowledged = sink.publication["v2"]["last_success"]
    sink._publish()
    second = json.loads((tmp_path / "observations-v2.json").read_bytes())
    assert second["publication"]["v2"]["last_success"] == acknowledged
    assert acknowledged["generation"] < second["generation"]
    restored = diagnostics.DiagnosticSink(tmp_path)
    restored._load()
    assert restored.publication["v2"]["prior_acknowledged"] == acknowledged
    assert "last_success" not in restored.publication["v2"]


def test_child_capacity_retains_first_failing_child_and_exact_omissions():
    sink = diagnostics.DiagnosticSink()
    reference = uuid4().hex
    for index in range(20):
        child = uuid4().hex
        for state in ("entered", "failed" if index == 19 else "settled"):
            value = event(reference, state, "worker_execution")
            value.update(role="child", child_reference=child, parent_reference=reference)
            sink._accept(value)
    row = sink.records[reference]
    assert len(row["children"]) == 16
    assert row["milestones"]["failure"]["child_reference"] == child
    assert row["children"][child]["failure"]
    assert sink.children_omitted == 4


def test_health_keeps_publication_facts_without_reembedding_operations(monkeypatch, tmp_path):
    sink = diagnostics.DiagnosticSink(tmp_path)
    sink._accept(event(uuid4().hex, "failed", error_type="OSError"))
    sink._publish()
    sink._publish()
    monkeypatch.setattr(diagnostics, "_sink", sink)
    components, _, _ = bundle.collect_components()
    health = json.loads(components["diagnostic-health.json"])["sink"]
    assert health["coverage"]["status"] == "available"
    assert "operations" not in health["observation"]
    assert health["observation"]["publication"]["v2"]["last_success"]


def test_initial_zip_anchors_frozen_continuation_and_full_component_hash(monkeypatch):
    import random

    payload = b"".join(
        bundle.encode({"detail": random.Random(index).randbytes(12000).hex()}) + b"\n"
        for index in range(4)
    )
    monkeypatch.setattr(
        bundle, "collect_components", lambda **_: ({"operations.jsonl": payload}, {}, {})
    )
    service, _, _ = report_service(1)
    initial = service.download_complete_report(ACTOR, max_bytes=65536)
    assert initial["diagnostic_token"]
    with zipfile.ZipFile(io.BytesIO(initial["content"])) as archive:
        first = json.loads(archive.read("manifest.json"))
        assert first["part"] == 0 and first["previous_sha256"] is None
        assert "summary.json" in archive.namelist()
    part = service.download_diagnostic_part(ACTOR, initial["diagnostic_token"], max_bytes=65536)
    with zipfile.ZipFile(io.BytesIO(part["content"])) as archive:
        second = json.loads(archive.read("manifest.json"))
        assert second["generation"] == first["generation"]
        assert second["part"] == 1 and second["previous_sha256"] == initial["sha256"]
        assert second["components"]["operations.jsonl"]["component_sha256"] == bundle.sha(payload)


def test_minimum_archive_keeps_summary_when_full_summary_needs_continuation(monkeypatch):
    from services import recovery_complete_report as complete

    original = complete.zlib.compress

    def force_summary_bound(data, level):
        if b'"format":"k98-recovery-complete-report-v1"' in data:
            return bytes(65536)
        return original(data, level)

    monkeypatch.setattr(complete.zlib, "compress", force_summary_bound)
    service, _, _ = report_service(1)
    result = service.download_complete_report(ACTOR, max_bytes=65536)
    with zipfile.ZipFile(io.BytesIO(result["content"])) as archive:
        summary = json.loads(archive.read("summary.json"))
        assert summary["included_incidents"] == 1
        assert summary["summary_continuation"] and result["diagnostic_token"]


@pytest.mark.asyncio
async def test_child_identity_failure_does_not_reuse_parent_context(monkeypatch):
    from core import operation_evidence as evidence

    sink = diagnostics.DiagnosticSink()
    monkeypatch.setattr(diagnostics, "_sink", sink)
    available = evidence._slots._value
    with evidence.scope() as parent:
        monkeypatch.setattr(evidence, "uuid4", Mock(side_effect=OSError("no identity")))
        assert await drain_thread(lambda: False) is False
        assert evidence._current.get() is parent
        assert parent.worker_result == {} and parent.references == {}
    assert evidence._slots._value == available
    assert sink.context_losses == 1


@pytest.mark.parametrize("completed", [True, False])
def test_restore_capacity_accounts_for_v1_only_roots(monkeypatch, tmp_path, completed):
    monkeypatch.setattr(diagnostics, "MAX_OPERATIONS", 2)
    sink = diagnostics.DiagnosticSink(tmp_path)
    for _ in range(2):
        ref = uuid4().hex
        sink._accept(event(ref, "entered", "operation"))
        sink._accept(event(ref, "settled" if completed else "failed", "operation"))
    sink._publish()
    legacy = diagnostics.DiagnosticSink()
    reference = uuid4().hex
    legacy._accept(event(reference, "failed", "operation"))
    row = next(iter(legacy.records.values()))
    (tmp_path / "observations.json").write_bytes(
        bundle.encode({"schema": "operation-observations/1", "operations": [row]})
    )
    restored = diagnostics.DiagnosticSink(tmp_path)
    restored._load()
    assert len(restored.records) == 2
    if completed:
        assert reference in restored.records and restored.evicted == 1
    else:
        assert reference not in restored.records
        assert restored.refused_operations == restored.dropped == 1


def test_empty_milestones_still_restore_v2_schema():
    sink = diagnostics.DiagnosticSink()
    sink._accept(event(uuid4().hex))
    row = next(iter(sink.records.values()))
    assert row["milestones"] == {}
    assert sink._restore_row(row)["schema"] == "operation-projection/2"


def test_redaction_cache_is_bounded_digest_keyed_and_request_scoped(monkeypatch):
    original = bundle.redact_diagnostic_text
    redactor = Mock(wraps=original)
    monkeypatch.setattr(bundle, "redact_diagnostic_text", redactor)
    with bundle.report_request() as lease:
        secret = "password=never-retain-this"
        for _ in range(2):
            assert bundle.redact_report_text(secret) == original(secret)
        assert redactor.call_count == 1
        assert secret not in str(lease.redactions)
        for index in range(200):
            assert bundle.redact_report_text(str(index)) == str(index)
        assert len(lease.redactions) == 128
        assert all(type(key) is bytes and len(key) == 32 for key in lease.redactions)
        assert all(len(value.encode("utf-8")) <= 512 for value in lease.redactions.values())
    assert lease.redactions == {}


def test_identifier_fast_path_matches_canonical_redaction():
    import random

    randomizer = random.Random(19)
    values = ["".join(randomizer.choices("0123456789abcdefABCDEF-", k=36)) for _ in range(1000)]
    values += [
        str(uuid4()),
        "password=" + str(uuid4()),
        "Bearer " + str(uuid4()),
        "https://example.invalid/?token=" + str(uuid4()),
        "authorization: " + str(uuid4()),
    ]
    with bundle.report_request():
        for value in values:
            assert bundle.redact_report_text(value) == bundle.redact_diagnostic_text(value)


def test_oversize_incident_reports_required_bytes_without_advancing_cursor():
    service, store, records = report_service(1)
    records[0]["evidence"]["explanation"] = "x" * 100000
    with pytest.raises(
        SourceConflict, match=r"requires at least \d+ bytes.*cursor has not advanced"
    ):
        service.download_report(ACTOR, max_bytes=65536)
    assert store.report_page.call_count == 1
    assert store.report_page.call_args.kwargs["after"] is None


@pytest.mark.asyncio
async def test_cancelled_delivery_closes_buffer_and_releases_report_lease(monkeypatch):
    from ui.views import recovery_view as view

    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    entered = asyncio.Event()
    buffers = []

    async def send(**kwargs):
        buffers.append(kwargs["file"].fp)
        entered.set()
        await asyncio.Event().wait()

    interaction = SimpleNamespace(followup=SimpleNamespace(send=send))

    async def deliver():
        with bundle.report_request():
            await view.send_report_attachment(
                interaction, ACTOR, {"content": b"{}", "filename": "report.json"}, "Report", None
            )

    task = asyncio.create_task(deliver())
    await entered.wait()
    with pytest.raises(SourceConflict):
        with bundle.report_request():
            pass
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert buffers[0].closed
    with bundle.report_request():
        pass
