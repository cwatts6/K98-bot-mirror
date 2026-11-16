"""Closed typed IPC contract; no caller-provided targets or ownership."""

from copy import deepcopy
from unittest.mock import Mock
from uuid import uuid4

import pytest

from scripts.run_export_authority import AuthorityBroker
from services import export_target_recovery_authority as module
from services.export_execution_authority import ExecutionUncertain
from services.export_runtime_composition import AuthorityClient, RuntimeRegistration
from tests.test_export_runtime_composition import registration_fixture


@pytest.fixture
def endpoint(monkeypatch):
    job_id = str(uuid4())
    checked = dict(
        job_id=job_id,
        token="a" * 64,
        outcome="unknown_write",
        eligible=True,
        targets=["old-file"],
        actor=None,
        reason=None,
        explanation="Verified exact targets",
    )
    boundary = Mock(fingerprint="d" * 64)
    authority = Mock()
    broker = AuthorityBroker(
        authority, RuntimeRegistration(registration_fixture()), boundary=boundary
    )
    inspect = Mock(return_value=checked)
    apply = Mock(return_value=checked)
    monkeypatch.setattr(module, "inspect_target_recovery", inspect)
    monkeypatch.setattr(module, "isolate_export_targets", apply)
    client = object.__new__(AuthorityClient)
    client._invoke = lambda message: broker.dispatch(
        dict(message, deployment_hash=boundary.fingerprint)
    )
    return client, job_id, checked, boundary, inspect, apply, authority, broker.registration


def test_typed_inspection_and_action_recheck_protected_boundary(endpoint):
    client, job_id, checked, boundary, inspect, apply, authority, registration = endpoint
    assert client.inspect_target_recovery(job_id) == checked
    inspect.assert_called_once_with(authority, registration, job_id)
    actor = "recovery:" + str(uuid4())
    client.isolate_export_targets(job_id, "a" * 64, actor, "Replace these outputs")
    apply.assert_called_once_with(
        authority, registration, job_id, "a" * 64, actor, "Replace these outputs"
    )
    assert boundary.recheck.call_count == 2


@pytest.mark.parametrize(
    "extra",
    ["server", "database", "targets", "owner", "fence", "receipt", "resources", "registration"],
)
def test_bot_cannot_supply_its_own_target_or_release_proof(endpoint, extra):
    client, job_id, _, _, inspect, apply, _, _ = endpoint
    with pytest.raises(ValueError):
        client._invoke(
            dict(
                version=1,
                action="isolate_export_targets",
                job_id=job_id,
                token="a" * 64,
                actor="recovery:" + str(uuid4()),
                reason="Approved",
                **{extra: "caller supplied"},
            )
        )
    inspect.assert_not_called()
    apply.assert_not_called()


@pytest.mark.parametrize(
    "change",
    [
        {"job_id": str(uuid4())},
        {"targets": ["bad/id"]},
        {"targets": ["old-file", "old-file"]},
        {"targets": []},
        {"eligible": False},
        {"token": "short"},
        {"actor": "injected"},
        {"outcome": "resolved"},
        {"reason": "unexpected"},
        {
            "outcome": "targets_isolated",
            "eligible": False,
            "actor": "recovery:" + "-" * 36,
            "reason": "invalid UUID",
        },
        {
            "outcome": "targets_isolated",
            "eligible": False,
            "actor": "recovery:" + str(uuid4()),
            "reason": "ok" + " " * 512,
        },
    ],
)
def test_unbound_or_malformed_reply_remains_uncertain(endpoint, change):
    client, job_id, checked, *_ = endpoint
    checked.update(deepcopy(change))
    with pytest.raises(ExecutionUncertain):
        client.inspect_target_recovery(job_id)
