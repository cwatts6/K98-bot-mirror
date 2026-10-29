"""All-copy loss requires exact backup bytes and a fresh, scoped confirmation."""

from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_evidence_storage import EvidenceCopies
from services.recovery_service import RecoveryService
from tests.test_export_evidence_recovery import recovery as recovery, restore
from tests.test_guided_recovery import ACTOR


def lose_copies(r):
    encrypted = (r.tmp_path / r.receipt.key).read_bytes()
    for key in EvidenceCopies.keys(r.reference):
        (r.tmp_path / key).unlink()
    return encrypted


def stage(r, encrypted):
    (r.tmp_path / EvidenceCopies.backup_key(r.reference)).write_bytes(encrypted)
    return r.service.review_source(ACTOR, "private_evidence", r.reference)


def test_all_copy_loss_has_specific_collection_then_confirmed_restoration(recovery):
    r = recovery
    encrypted = lose_copies(r)
    missing = r.service.review_source(ACTOR, "private_evidence", r.reference)
    assert not missing["evidence"]["actions"]
    steps = " ".join(missing["evidence"]["required_evidence"])
    assert EvidenceCopies.backup_key(r.reference) in steps and r.receipt.sha256 in steps
    assert "evidence_root" in steps and "Recheck" in steps
    row = stage(r, encrypted)
    assert row["State"] == "open"
    assert row["evidence"]["actions"]["restore_evidence"]["label"] == "Restore verified backup"
    assert not (r.tmp_path / r.receipt.key).exists()
    r.service = RecoveryService(
        r.incidents, {r.adapter.kind: r.adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    assert restore(r, row)["State"] == "resolved"
    assert r.private.read(r.receipt) == r.raw
    assert (r.tmp_path / EvidenceCopies.backup_key(r.reference)).read_bytes() == encrypted
    assert restore(r, row)["State"] == "resolved"
    assert len(r.incidents.actions) == 1
    r.broker.replacements.current.assert_not_called()


@pytest.mark.parametrize("damage", ["wrong_hash", "oversized", "decrypt_failure"])
def test_invalid_backup_never_enables_repair(recovery, monkeypatch, damage):
    r = recovery
    encrypted = lose_copies(r)
    if damage == "wrong_hash":
        encrypted = b"foreign content"
    elif damage == "oversized":
        r.private._store.max_bytes = 16
    else:
        monkeypatch.setattr(r.private, "_unprotect", Mock(side_effect=OSError("identity missing")))
    row = stage(r, encrypted)
    assert row["evidence"]["backup_candidate"] == "unavailable"
    assert not row["evidence"]["actions"] and row["State"] == "open"
    assert not (r.tmp_path / r.receipt.key).exists()


def test_changed_backup_rejects_stale_approval(recovery):
    r = recovery
    row = stage(r, lose_copies(r))
    (r.tmp_path / EvidenceCopies.backup_key(r.reference)).write_bytes(b"changed")
    with pytest.raises(SourceConflict, match="changed"):
        restore(r, row)
    assert not (r.tmp_path / r.receipt.key).exists()


def test_backup_requires_admin_even_when_valid(recovery):
    r = recovery
    row = stage(r, lose_copies(r))
    with pytest.raises(SourceConflict, match="configured admin"):
        r.service.execute(
            type(ACTOR)(9, 2, 3),
            row["IncidentID"],
            row["Revision"],
            row["EvidenceHash"],
            "restore_evidence",
            "restore",
        )
    assert not (r.tmp_path / r.receipt.key).exists()


def test_lost_backup_restore_reply_is_verified_without_duplicate_action(recovery, monkeypatch):
    r = recovery
    row = stage(r, lose_copies(r))
    original = r.client.evidence_recovery
    calls = []

    def lost(operation, **values):
        result = original(operation, **values)
        if operation == "restore":
            calls.append(operation)
            raise TimeoutError("acknowledgement lost")
        return result

    monkeypatch.setattr(r.client, "evidence_recovery", lost)
    assert restore(r, row)["State"] == "resolved"
    assert calls == ["restore"] and len(r.incidents.actions) == 1


def test_backup_path_cannot_follow_symlink_or_escape_root(recovery, monkeypatch):
    r = recovery
    lose_copies(r)
    original = r.private._store._path

    def reject(key):
        if key.startswith("backup_"):
            raise ValueError("Spool escapes its registered root.")
        return original(key)

    monkeypatch.setattr(r.private._store, "_path", reject)
    row = r.service.review_source(ACTOR, "private_evidence", r.reference)
    assert not row["evidence"]["actions"]
    with pytest.raises(ValueError):
        EvidenceCopies.backup_key("../outside")


def test_interrupted_two_copy_restore_can_finish_without_replaying_operation(recovery, monkeypatch):
    r = recovery
    row = stage(r, lose_copies(r))
    original = EvidenceCopies._replace
    calls = []

    def interrupted(self, key, data):
        calls.append(key)
        if len(calls) == 2:
            raise OSError("interrupted before replica")
        original(self, key, data)

    monkeypatch.setattr(EvidenceCopies, "_replace", interrupted)
    first = restore(r, row)
    monkeypatch.setattr(EvidenceCopies, "_replace", original)
    current = r.service.review(ACTOR, first["IncidentID"])
    if current["State"] != "resolved":
        action = next(iter(current["evidence"]["actions"]))
        current = r.service.execute(
            ACTOR,
            current["IncidentID"],
            current["Revision"],
            current["EvidenceHash"],
            action,
            "finish exact copies",
        )
    assert current["State"] == "resolved"
    assert r.private.read(r.receipt) == r.raw


@pytest.mark.asyncio
async def test_collection_visible_in_incident_and_report_without_private_contents(recovery):
    from services.recovery_report import incident_report
    from ui.views.recovery_view import incident_embed

    r = recovery
    lose_copies(r)
    row = r.service.review_source(ACTOR, "private_evidence", r.reference)
    display = str(incident_embed(row).to_dict())
    report = incident_report(r.service, row)
    assert "Evidence collection" in display
    assert report["diagnosis"]["required_evidence"] == row["evidence"]["required_evidence"]
    assert "never display this" not in str(report) + display
    assert str(r.tmp_path) not in str(report) + display


@pytest.mark.asyncio
async def test_backup_button_requires_separate_confirmation(recovery, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from ui.views import recovery_view as view

    r = recovery
    row = stage(r, lose_copies(r))

    async def call(method, *args):
        return getattr(r.service, method)(*args)

    monkeypatch.setattr(view, "call", call)
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b for b in view.RecoveryIncidentView(row).children if b.label == "Restore verified backup"
    )
    await button.callback(interaction)
    assert not r.incidents.actions
    confirmation = interaction.followup.send.call_args.kwargs["view"]
    await next(b for b in confirmation.children if b.label.startswith("Confirm")).callback(
        interaction
    )
    assert r.service.refresh(row["IncidentID"])["State"] == "resolved"
    assert len(r.incidents.actions) == 1
