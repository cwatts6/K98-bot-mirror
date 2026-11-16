"""An unfinished configuration stage retains its separately approved export intent."""

from contextlib import nullcontext
from copy import deepcopy
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.configuration_continuation import ConfigurationContinuation
from tests.test_configuration_continuation import fixture

ACTION = "continue_configuration_export"


def pipeline_fixture():
    state, action, dal, adapter = fixture(ACTION)
    state.update(blocker=None, original_export_disposition="pipeline_export_v1")
    action["EvidenceHash"] = digest(state).hex()
    return state, action, dal, adapter


def test_pipeline_choice_requires_original_durable_intent():
    state, _, _, adapter = pipeline_fixture()
    assert ACTION in adapter.inspect("source")[0]["actions"]
    for disposition in (None, "not_recorded", "configuration_only_v1", "cache_only_v1"):
        state["original_export_disposition"] = disposition
        assert ACTION not in adapter.inspect("source")[0]["actions"]


def test_pipeline_choice_waits_for_blocking_owner():
    state, _, _, adapter = pipeline_fixture()
    state["blocker"] = dict(owner={"kind": "configuration_read", "source_id": str(uuid4())})
    evidence, _, resolved = adapter.inspect("source")
    assert ACTION not in evidence["actions"]
    assert evidence["recovery_links"][0]["source_id"] == state["blocker"]["owner"]["source_id"]
    assert not resolved


def test_pipeline_choice_saves_intent_before_dispatch_and_restores_context(monkeypatch):
    from services.producer_recovery_intent import configuration_import_intent, current_intent

    state, action, dal, adapter = pipeline_fixture()
    monkeypatch.setattr(
        "services.legacy_export_snapshot_service.use_runtime", lambda _: nullcontext()
    )
    captured = []

    @configuration_import_intent
    def run():
        assert state["marker"]["export_disposition"] == "pipeline_export_v1"
        captured.append(deepcopy(current_intent()))

    adapter.runner = run
    adapter.execute(
        str(uuid4()), ACTION, action["EvidenceHash"], "recovery:" + action["ActionID"], "Confirmed"
    )
    assert captured[0]["export_disposition"] == "pipeline_export_v1"
    assert current_intent() is None


def test_restart_without_dispatch_closes_exact_child_without_replay():
    state, action, dal, adapter = pipeline_fixture()
    dal.reserve_for_reconciliation.return_value = "child"
    dal.close_uncommitted.return_value = True
    assert adapter.reconcile("source", action) == "not_applied"
    assert state["marker"]["export_disposition"] == "pipeline_export_v1"
    restarted = ConfigurationContinuation(dal, adapter.producer, adapter.runner)
    assert restarted.reconcile("source", action) == "not_applied"
    dal.record.assert_called_once()
    adapter.runner.assert_not_called()


def test_pipeline_action_cannot_reinterpret_sql_only_saved_approval():
    state, action, dal, adapter = pipeline_fixture()
    state["marker"] = dict(
        action=action["ActionID"],
        token=action["EvidenceHash"],
        choice="retry",
        export_disposition="configuration_only_v1",
    )
    with pytest.raises(SourceConflict, match="export intent"):
        adapter.reconcile("source", action)
    dal.reserve_for_reconciliation.assert_not_called()


def test_changed_registration_invalidates_pipeline_confirmation():
    state, action, _, adapter = pipeline_fixture()
    state["current"]["scan_data"] = {"destinations": ["changed"]}
    with pytest.raises(SourceConflict, match="changed"):
        adapter.execute(
            str(uuid4()),
            ACTION,
            action["EvidenceHash"],
            "recovery:" + action["ActionID"],
            "Confirmed",
        )
    adapter.runner.assert_not_called()
