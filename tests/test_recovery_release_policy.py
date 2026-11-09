"""Pilot boundaries apply to real service dispatch, forms, alerts and receipts."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryService
from tests.test_guided_recovery import ACTOR, Store, execute, setup


def pilot(service):
    return RecoveryService(
        service.store,
        service.adapters,
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )


def test_partial_reporting_has_explicit_disposition_without_completion_claim():
    original, dal, store, old_row = setup("partial")
    service = pilot(original)
    current = service.review(ACTOR, old_row["IncidentID"])
    assert current["State"] == "open"
    assert set(current["evidence"]["actions"]) == {"supersede_partial"}
    choice = current["evidence"]["actions"]["supersede_partial"]
    assert "unfinished or unknown" in choice["check"]
    assert "not a completion receipt" in choice["effect"]
    assert current["EvidenceHash"] == old_row["EvidenceHash"]
    # Presentation must not remove original evidence from durable history.
    assert "supersede_partial" in store.get(old_row["IncidentID"])["evidence"]["actions"]
    result = execute(service, current)
    assert result["State"] == "resolved"
    assert result["evidence"]["outcome"] == "partial"
    assert len(dal.calls) == 1


def test_previously_accepted_repair_reconciles_after_pilot_boundary_changes():
    original, dal, store, old_row = setup("partial")
    store.lose_claim_ack = True
    with pytest.raises(Exception, match="lost intent commit"):
        execute(original, old_row)
    assert dal.calls == []
    assert len(store.actions) == 1
    current = pilot(original).review(ACTOR, old_row["IncidentID"])
    assert current["State"] == "resolved"
    assert store.actions[0]["State"] == "verified"
    assert len(dal.calls) == 1
    assert "release_notice" not in current
    pilot(original).review(ACTOR, old_row["IncidentID"])
    assert len(dal.calls) == 1


def test_pilot_allows_verified_rollback_settlement():
    original, dal, store, old_row = setup("rolled_back")
    current = execute(pilot(original), old_row, action="release_failure")
    assert current["State"] == "resolved"
    assert store.actions[0]["State"] == "verified"
    assert len(dal.calls) == 1


def test_partially_released_export_explains_available_and_withheld_choices():
    row = dict(
        SourceKind="export_job",
        State="open",
        evidence=dict(
            actions={
                "isolate_targets": {"label": "Retire affected outputs"},
                "future_unqualified_repair": {"label": "Future repair"},
            }
        ),
    )
    current = p0a_presentation(row)
    assert set(current["evidence"]["actions"]) == {"isolate_targets"}
    assert "buttons shown here are available" in current["release_notice"]
    assert "Additional repairs" in current["release_notice"]
    assert set(row["evidence"]["actions"]) == {"isolate_targets", "future_unqualified_repair"}


def withheld(kind="export_rollover"):
    store = Store()
    evidence = dict(
        title="Blocked operation",
        explanation="The outcome is uncertain.",
        outcome="unknown",
        actions={
            "replace": dict(label="Replace", check="Check it", effect="Replace it", input=True)
        },
        recovery_links=[dict(label="Review blocker", kind="configuration_read", source_id="r")],
    )
    adapter = SimpleNamespace(
        inspect=Mock(return_value=(evidence, "a" * 64, False)),
        reconcile=Mock(return_value=None),
        execute=Mock(),
        input_fields=Mock(),
        pending_recovery=Mock(return_value=["s"]),
        automatic_action="replace",
    )
    row = store.observe(kind, "s", evidence, "a" * 64)
    service = RecoveryService(
        store,
        {kind: adapter},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    return service, store, adapter, row


@pytest.mark.parametrize("kind", ["export_rollover", "private_evidence", "future_adapter"])
def test_unqualified_kind_preserves_diagnosis_links_and_blocks_all_dispatch_routes(kind):
    service, store, adapter, row = withheld(kind)
    current = service.review(ACTOR, row["IncidentID"])
    assert current["State"] == "open"
    assert current["evidence"]["outcome"] == "unknown"
    assert current["evidence"]["recovery_links"] == row["evidence"]["recovery_links"]
    with pytest.raises(SourceConflict, match="not enabled"):
        service.execute(
            ACTOR, row["IncidentID"], row["Revision"], row["EvidenceHash"], "replace", "ok"
        )
    with pytest.raises(SourceConflict, match="no longer available"):
        service.input_page(ACTOR, row["IncidentID"], "replace")
    with pytest.raises(SourceConflict):
        service.execute_input(
            ACTOR, row["IncidentID"], row["Revision"], row["EvidenceHash"], "replace", 0
        )
    service.recover_automatic(row["IncidentID"])
    adapter.execute.assert_not_called()
    adapter.input_fields.assert_not_called()
    assert store.actions == []


def test_monitor_still_discovers_and_presents_unqualified_incidents(monkeypatch):
    from contextlib import contextmanager

    from services import recovery_runtime

    service, store, adapter, row = withheld()
    store.scope = ("account", "storage", 2)
    store.list_open = lambda **kwargs: [store.get(row["IncidentID"])]
    store.has_failed_checks = lambda: False
    store.alerts_due = lambda: [row["IncidentID"]]

    @contextmanager
    def scope():
        yield service

    monkeypatch.setattr(recovery_runtime, "recovery_service", scope)
    monkeypatch.setattr(recovery_runtime, "_cursors", {})
    monkeypatch.setattr(recovery_runtime, "_incident_cursor", None)
    monkeypatch.setattr(recovery_runtime, "_retry_admission", lambda: True)
    assert recovery_runtime.observe_recovery() == []
    adapter.pending_recovery.assert_called_once_with(after=None)
    alert = service.present(store.get(row["IncidentID"]))
    assert alert["State"] == "open"
    assert alert["release_notice"]
    assert alert["evidence"]["actions"] == {}


@pytest.mark.asyncio
async def test_private_view_explains_release_boundary_and_retains_recheck_and_links():
    from ui.views.recovery_view import RecoveryIncidentView, incident_embed

    service, store, adapter, row = withheld()
    before = deepcopy(store.row)
    current = service.present(row)
    embed = incident_embed(current)
    labels = [button.label for button in RecoveryIncidentView(current).children]
    assert "Replace" not in labels
    assert "Recheck" in labels
    assert "Review blocker" in labels
    assert any(field.name == "Release coverage" and "P0b" in field.value for field in embed.fields)
    assert not any(field.name == "Recovery checks" for field in embed.fields)
    assert store.row == before
