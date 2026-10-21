"""Restart decisions must preserve the admin's exact confirmed action."""

from contextlib import nullcontext
from copy import deepcopy
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.configuration_continuation import ConfigurationContinuation


def fixture(action_kind="keep_prior"):
    state = dict(marker=None, child=None, current={"scan_data": {"destinations": ["sheet"]}})
    action = dict(ActionID=str(uuid4()), ActionKind=action_kind, EvidenceHash=digest(state).hex())
    dal = Mock()
    dal.serialized.side_effect = lambda _: nullcontext()
    dal.snapshot.side_effect = lambda _: deepcopy(state)

    def record(source, token, marker):
        assert token == digest(state).hex()
        state["marker"] = deepcopy(marker)

    dal.record.side_effect = record
    return state, action, dal, ConfigurationContinuation(dal, Mock(), Mock())


def test_restarted_keep_prior_records_exact_choice_without_dispatch_or_reservation():
    state, action, dal, adapter = fixture()
    assert adapter.reconcile("source", action) == "verified"
    restarted = ConfigurationContinuation(dal, adapter.producer, adapter.runner)
    assert restarted.reconcile("source", action) == "verified"
    assert state["marker"]["choice"] == "keep_prior"
    assert state["marker"]["action"] == action["ActionID"]
    dal.record.assert_called_once()
    dal.reserve_for_reconciliation.assert_not_called()
    dal.close_uncommitted.assert_not_called()
    adapter.runner.assert_not_called()
    adapter.producer.inspect.assert_not_called()


def test_stale_keep_prior_claim_cannot_replace_current_evidence():
    state, action, dal, adapter = fixture()
    state["current"]["scan_data"]["destinations"] = ["changed"]
    assert adapter.reconcile("source", action) == "not_applied"
    dal.record.assert_not_called()
    dal.reserve_for_reconciliation.assert_not_called()
    adapter.runner.assert_not_called()


@pytest.mark.parametrize(
    "kind,choice",
    [("keep_prior", "retry"), ("retry_configuration", "keep_prior"), ("keep_prior", "unknown")],
)
def test_conflicting_saved_choice_cannot_dispatch_or_claim_verification(kind, choice):
    state, action, dal, adapter = fixture(kind)
    state["marker"] = dict(action=action["ActionID"], token=action["EvidenceHash"], choice=choice)
    with pytest.raises(SourceConflict, match="choice differs"):
        adapter.reconcile("source", action)
    dal.record.assert_not_called()
    dal.reserve_for_reconciliation.assert_not_called()
    adapter.runner.assert_not_called()


def test_unacknowledged_retry_retains_tombstone_without_replaying_runner():
    state, action, dal, adapter = fixture("retry_configuration")
    dal.reserve_for_reconciliation.return_value = "child"
    dal.close_uncommitted.return_value = True
    assert adapter.reconcile("source", action) == "not_applied"
    assert state["marker"]["choice"] == "retry"
    dal.close_uncommitted.assert_called_once_with("child", state["marker"])
    adapter.runner.assert_not_called()


def test_new_approval_saves_configuration_only_intent_before_runner(monkeypatch):
    from services.producer_recovery_intent import current_intent

    state, action, dal, adapter = fixture("retry_configuration")
    adapter.inspect = Mock(
        return_value=({"actions": {"retry_configuration": {}}}, action["EvidenceHash"], False)
    )
    monkeypatch.setattr(
        "services.legacy_export_snapshot_service.use_runtime", lambda _: nullcontext()
    )
    captured = []

    def run():
        assert state["marker"]["export_disposition"] == "configuration_only_v1"
        captured.append(dict(current_intent()))

    adapter.runner = run
    source = str(uuid4())
    adapter.execute(
        source,
        "retry_configuration",
        action["EvidenceHash"],
        "recovery:" + action["ActionID"],
        "Confirmed",
    )
    assert captured[0]["export_disposition"] == "configuration_only_v1"
    assert captured[0]["parent"] == source
    assert captured[0]["operation"] == action["ActionID"]
    assert current_intent() is None
