"""Guided evidence restoration across encrypted disk, typed broker and admin actions."""

import asyncio
from contextlib import contextmanager
from threading import Event, RLock
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from core.export_execution_host import PrivateEvidenceStore
from kvk.dal.new_source_import_dal import SourceConflict
from scripts.run_export_authority import AuthorityBroker
from services.export_evidence_recovery import EvidenceRecoveryAdapter
from services.export_evidence_storage import EvidenceCopies
from services.export_execution_authority import ExecutionUncertain
from services.export_runtime_composition import LocalAuthorityClient, RuntimeRegistration
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryService
from tests.test_export_runtime_composition import registration_fixture
from tests.test_guided_recovery import ACTOR, Store


@pytest.fixture
def recovery(tmp_path, monkeypatch):
    private = PrivateEvidenceStore(
        tmp_path, "disk", protect=lambda b: b[::-1], unprotect=lambda b: b[::-1]
    )
    raw = b'{"kind":"private-fixture","value":"never display this"}'
    receipt = private.put(raw)
    reference = str(UUID(receipt.key))
    binding = dict(reference=reference, sha256=receipt.sha256, kinds=["replacement activation"])
    catalog = SimpleNamespace(
        page=lambda after=None: [] if after else [reference],
        get=lambda key: (
            binding
            if key == reference
            else (_ for _ in ()).throw(SourceConflict("outside account"))
        ),
    )
    monkeypatch.setattr("services.export_evidence_recovery.EvidenceCatalogDAL", lambda *_: catalog)
    authority = SimpleNamespace(
        store=private, dal=SimpleNamespace(connect=Mock()), _lock=RLock(), enrollment_plan=None
    )
    boundary = SimpleNamespace(fingerprint="a" * 64, recheck=Mock())
    broker = AuthorityBroker(
        authority, RuntimeRegistration(registration_fixture()), boundary=boundary
    )
    broker.replacements = SimpleNamespace(
        current=Mock(side_effect=SourceConflict("activation receipt unavailable")),
        registrations=Mock(side_effect=SourceConflict("activation receipt unavailable")),
    )
    client = LocalAuthorityClient(broker)
    adapter = EvidenceRecoveryAdapter(client)
    incidents = Store()
    service = RecoveryService(
        incidents,
        {adapter.kind: adapter},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    return SimpleNamespace(**locals())


def damage(r, mode="missing"):
    primary = r.tmp_path / r.receipt.key
    if mode == "missing":
        primary.unlink()
    else:
        primary.write_bytes(b"damaged ciphertext")
    return r.service.review_source(ACTOR, "private_evidence", r.reference)


def restore(r, row):
    return r.service.execute(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "restore_evidence",
        "Confirm exact saved bytes",
    )


@pytest.mark.parametrize("mode", ["missing", "corrupt"])
def test_guided_restore_works_when_registration_is_unavailable_and_survives_restart(recovery, mode):
    r = recovery
    row = damage(r, mode)
    assert row["evidence"]["outcome"] == "recoverable"
    assert set(row["evidence"]["actions"]) == {"restore_evidence"}
    r.service = RecoveryService(
        r.incidents,
        {r.adapter.kind: EvidenceRecoveryAdapter(r.client)},
        admin_id=1,
        guild_id=2,
        channel_id=3,
    )
    result = restore(r, row)
    assert result["State"] == "resolved" and not result["pending_action"]
    assert r.private.read(r.receipt) == r.raw
    assert r.incidents.actions[0]["State"] == "verified"
    assert restore(r, row)["State"] == "resolved" and len(r.incidents.actions) == 1
    r.broker.replacements.registrations.assert_not_called()
    r.broker.replacements.current.assert_not_called()
    if mode == "corrupt":
        assert next(r.tmp_path.glob("damaged_*")).read_bytes() == b"damaged ciphertext"


def test_wrong_hash_both_missing_and_corrupt_replica_never_fabricate_evidence(recovery):
    r = recovery
    row = damage(r)
    (r.tmp_path / ("replica_" + r.receipt.key)).write_bytes(b"another document")
    current = r.service.review(ACTOR, row["IncidentID"])
    assert current["evidence"]["outcome"] == "backup_required"
    assert not current["evidence"]["actions"]
    with pytest.raises(SourceConflict, match="changed"):
        restore(r, row)
    assert not (r.tmp_path / r.receipt.key).exists()


def test_lost_repair_reply_reconciles_without_second_restoration(recovery, monkeypatch):
    r = recovery
    row = damage(r)
    original = r.client.evidence_recovery
    calls = []

    def lost(operation, **values):
        result = original(operation, **values)
        if operation == "restore":
            calls.append(operation)
            raise TimeoutError("lost reply")
        return result

    monkeypatch.setattr(r.client, "evidence_recovery", lost)
    assert restore(r, row)["State"] == "resolved"
    assert calls == ["restore"]
    assert r.incidents.actions[0]["State"] == "verified"


def test_original_verified_copy_requires_confirmation_and_verifies_both_copies(
    recovery, monkeypatch
):
    r = recovery
    # A legacy adapter's opt-in cannot authorize a new automatic mutation, even
    # without a presentation policy. Only verified configuration reads may run.
    monkeypatch.setattr(r.adapter, "automatic_action", "protect_evidence", raising=False)
    r.service.presentation_policy = None
    (r.tmp_path / ("replica_" + r.receipt.key)).unlink()
    row = r.service.review_source(ACTOR, "private_evidence", r.reference)
    result = r.service.recover_automatic(row["IncidentID"])
    assert result["State"] == "open"
    assert r.incidents.actions == []
    result = r.service.execute(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "protect_evidence",
        "Confirm exact-copy restoration",
    )
    assert result["State"] == "resolved"
    assert set(result["evidence"]["copies"].values()) == {"verified"}
    assert r.incidents.actions[0]["Actor"] == "discord:1"
    assert r.incidents.actions[0]["State"] == "verified"


def test_primary_damage_requires_admin_confirmation(recovery):
    r = recovery
    row = damage(r)
    assert r.service.recover_automatic(row["IncidentID"])["State"] == "open"
    assert not r.incidents.actions
    with pytest.raises(SourceConflict, match="configured admin"):
        r.service.execute(
            type(ACTOR)(9, 2, 3),
            row["IncidentID"],
            row["Revision"],
            row["EvidenceHash"],
            "restore_evidence",
            "not authorised",
        )
    assert not (r.tmp_path / r.receipt.key).exists()


def test_catalog_scope_and_exact_protocol_reject_untrusted_selectors(recovery):
    r = recovery
    with pytest.raises(ExecutionUncertain):
        r.client.evidence_recovery("inspect", reference=str(uuid4()))
    with pytest.raises(ExecutionUncertain):
        r.client.evidence_recovery("inspect", reference=r.reference, path="C:/private")
    with pytest.raises(ExecutionUncertain):
        r.client.evidence_recovery(
            "restore", reference=r.reference, token="0" * 64, actor="admin", reason="override"
        )
    assert r.private.read(r.receipt) == r.raw


def test_replica_creation_failure_never_returns_a_sql_usable_receipt(tmp_path, monkeypatch):
    private = PrivateEvidenceStore(tmp_path, "disk", protect=lambda b: b, unprotect=lambda b: b)
    monkeypatch.setattr(EvidenceCopies, "_write", Mock(side_effect=OSError("disk unavailable")))
    with pytest.raises(OSError):
        private.put(b"original")


def test_oversized_corrupt_primary_is_preserved_and_replaced_from_bounded_copy(recovery):
    r = recovery
    r.private._store.max_bytes = 1024
    (r.tmp_path / r.receipt.key).write_bytes(b"x" * 2048)
    row = r.service.review_source(ACTOR, r.adapter.kind, r.reference)
    assert restore(r, row)["State"] == "resolved"
    assert next(r.tmp_path.glob("damaged_*")).stat().st_size == 2048
    assert r.private.read(r.receipt) == r.raw


def test_partial_local_restore_is_safe_to_finish_after_restart(recovery, monkeypatch):
    r = recovery
    row = damage(r)
    import services.export_evidence_storage as storage

    original = storage.os.replace

    def lost(*args):
        original(*args)
        raise OSError("replacement completed but acknowledgement lost")

    monkeypatch.setattr(storage.os, "replace", lost)
    assert restore(r, row)["State"] == "resolved"
    assert r.private.read(r.receipt) == r.raw


@pytest.mark.asyncio
async def test_admin_view_shows_specific_repair_button_and_copy_verification(recovery):
    from ui.views.recovery_view import RecoveryIncidentView, incident_embed

    row = damage(recovery)
    assert "Restore verified evidence" in [
        button.label for button in RecoveryIncidentView(row).children
    ]
    text = str(incident_embed(row).to_dict())
    assert "replica" in text.lower() and "verified" in text
    assert "never display this" not in text and str(recovery.tmp_path) not in text


def test_proactive_monitor_discovers_damage_without_a_new_processing_call(recovery, monkeypatch):
    from services import recovery_runtime

    r = recovery
    (r.tmp_path / r.receipt.key).unlink()
    r.incidents.scope = "test"
    r.incidents.list_open = lambda **_: []
    r.incidents.has_failed_checks = lambda: False
    monkeypatch.setattr(
        "services.recovery_backlog_dal.RecoveryBacklogDAL.pending_repairs", lambda _: []
    )

    @contextmanager
    def service():
        yield r.service

    monkeypatch.setattr(recovery_runtime, "recovery_service", service)
    monkeypatch.setattr(recovery_runtime, "_retry_admission", lambda: True)
    monkeypatch.setattr(recovery_runtime, "_cursors", {})
    monkeypatch.setattr(recovery_runtime, "_incident_cursor", None)
    assert recovery_runtime.observe_recovery() == []
    assert r.incidents.row["State"] == "open"
    assert "restore_evidence" in r.incidents.row["evidence"]["actions"]
    assert not r.incidents.actions


def test_recovery_only_startup_never_publishes_normal_admission_until_history_verifies(monkeypatch):
    import services.export_runtime_composition as composition

    for name, value in (
        ("_installed", None),
        ("_recovery_bundle", None),
        ("_runtime_stopped", False),
        ("_installing", False),
    ):
        monkeypatch.setattr(composition, name, value)
    monkeypatch.setattr("bot_config.EXPORT_COORDINATION_ENABLED", True)
    bundle = composition.ExportRuntime.__new__(composition.ExportRuntime)
    composition.RuntimeLifetime.__init__(bundle, SimpleNamespace())
    bundle.refresh_replacement_registration = Mock(
        side_effect=SourceConflict("private receipt missing")
    )
    factory = Mock(return_value=bundle)
    monkeypatch.setattr(composition, "_prepare_configured_runtime", factory)
    with pytest.raises(SourceConflict, match="private receipt"):
        composition.install_configured_runtime()
    with pytest.raises(SourceConflict, match="readiness"):
        composition.configured_runtime()
    with composition.recovery_caller_scope() as runtime:
        assert runtime is bundle.legacy and runtime.recovery_only
    bundle.refresh_replacement_registration.side_effect = None
    composition.retry_recovery_admission()
    assert composition.configured_runtime() is bundle and not bundle.legacy.recovery_only
    factory.assert_called_once()
    composition.stop_runtime_admission()
    with pytest.raises(SourceConflict, match="closed"):
        with composition.recovery_caller_scope():
            pytest.fail("shutdown admitted recovery")


@pytest.mark.asyncio
async def test_guided_restore_reopens_admission_and_wakes_queued_exports_without_restart(
    recovery, monkeypatch
):
    from services import (
        export_coordination_service as coordinator,
        export_runtime_composition as composition,
    )

    r = recovery
    row = damage(r)
    for name, value in (
        ("_installed", None),
        ("_recovery_bundle", None),
        ("_runtime_stopped", False),
        ("_installing", False),
    ):
        monkeypatch.setattr(composition, name, value)
    monkeypatch.setattr(coordinator, "_worker", None)
    monkeypatch.setattr(coordinator, "_loop", None)
    monkeypatch.setattr("bot_config.EXPORT_COORDINATION_ENABLED", True)
    bundle = composition.ExportRuntime.__new__(composition.ExportRuntime)
    composition.RuntimeLifetime.__init__(bundle, SimpleNamespace())

    def verify_history():
        assert r.private.read(r.receipt) == r.raw

    bundle.refresh_replacement_registration = verify_history
    monkeypatch.setattr(composition, "_prepare_configured_runtime", lambda: bundle)
    with pytest.raises((OSError, SourceConflict)):
        composition.install_configured_runtime()
    attempted, resumed = Event(), Event()

    def admission():
        attempted.set()
        return composition.configured_runtime()

    def process_queue(stop, limit):
        resumed.set()
        stop.set()

    bundle.run_batch = process_queue
    monkeypatch.setattr(coordinator, "configured_coordinator", admission)
    monitor = Mock()
    monitor.is_running.return_value = False
    worker = coordinator.register_exports(monitor)
    assert worker is not None and not resumed.is_set()
    monitor.is_running.return_value = True
    assert coordinator.register_exports(monitor) is worker
    monitor.create.assert_called_once()
    task = asyncio.create_task(worker.run())
    try:
        assert await asyncio.to_thread(attempted.wait, 2)
        # Drain the failed factory's continuation before the repair wake; no
        # polling interval elapses in this test (the normal interval is 30s).
        await asyncio.sleep(0.02)
        assert not resumed.is_set()
        assert restore(r, row)["State"] == "resolved"
        composition.retry_recovery_admission()
        assert await asyncio.to_thread(resumed.wait, 2)
        await asyncio.wait_for(task, 2)
    finally:
        worker.stop.set()
        coordinator.wake_exports()
        await asyncio.wait_for(task, 2)
