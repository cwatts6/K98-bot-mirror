from copy import deepcopy
import json
from threading import RLock
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit
from services import config_recovery_authority as module
from services.config_read_recovery_adapter import ConfigReadRecoveryAdapter
from services.legacy_export_snapshot_service import configuration_digest
from services.recovery_service import RecoveryService
from tests.test_config_preparation_recovery import fixture
from tests.test_guided_recovery import ACTOR, Store


def authority_fixture(monkeypatch, *, preflight=False, lost_ack=False):
    original, snapshot, stream, documents = fixture()
    scope = {"destinations": ["file-a"]}
    stream["RegistrationHash"] = bytes.fromhex(configuration_digest(scope))
    snapshot["streams"][0]["RegistrationHash"] = stream["RegistrationHash"].hex()
    if preflight:
        snapshot["preparation"].update(State="preflight", Version=2)
        for resource in snapshot["resources"]:
            resource["Version"] -= 1
            resource["BlockedReason"] = None
    dal = original.dal
    original.verifier.dal.connect = Mock()
    dal.identity.return_value = dict(server="fixture", database="disposable")
    dal.target_data.side_effect = lambda *args, **kwargs: deepcopy(
        dict(
            preparation=snapshot["preparation"],
            resources=snapshot["resources"],
            stream_ids=[stream["StreamID"]],
        )
    )

    def settle(target, expected, audit):
        assert snapshot == expected
        snapshot["preparation"].update(State="unavailable", GenerationJson=json.dumps(audit))
        snapshot["resources"] = []
        if lost_ack:
            raise UncertainCommit("committed, acknowledgement lost")

    dal.settle.side_effect = settle
    monkeypatch.setattr(module, "ConfigPreparationRecoveryDAL", lambda connect: dal)
    authority = SimpleNamespace(
        _lock=RLock(), _streams={}, dal=original.verifier.dal, store=original.verifier.store
    )
    registration = SimpleNamespace(
        value=lambda: dict(
            account="account-a", storage_owner="fixture", legacy_configuration={"config": scope}
        )
    )
    source = snapshot["preparation"]["PreparationID"]
    client = SimpleNamespace(
        authority=authority,
        inspect_configuration_recovery=lambda key: module.inspect_configuration_recovery(
            authority, registration, key
        ),
        apply_configuration_recovery=lambda key, token, actor, reason: module.apply_configuration_recovery(
            authority, registration, key, token, actor, reason
        ),
    )
    return client, dal, snapshot, source, documents, stream


def test_monitor_finishes_only_interrupted_locally_owned_read_closure(monkeypatch):
    client, dal, snapshot, source, _, stream = authority_fixture(monkeypatch)
    authority = client.authority
    owned = SimpleNamespace(purpose="probe", frozen=True, uncertain=True)
    authority._streams[stream["StreamID"]] = owned
    stream["State"] = snapshot["streams"][0]["State"] = "frozen"

    def close(_):
        stream["State"] = snapshot["streams"][0]["State"] = "closed"

    authority.recover_owned_closure = Mock(side_effect=close)
    assert client.inspect_configuration_recovery(source)["eligible"]
    authority.recover_owned_closure.assert_called_once_with(stream["StreamID"])
    dal.settle.assert_not_called()
    authority.recover_owned_closure.reset_mock()
    owned.frozen = owned.uncertain = False
    client.inspect_configuration_recovery(source)
    authority.recover_owned_closure.assert_not_called()


@pytest.mark.parametrize("preflight", [False, True])
@pytest.mark.parametrize("lost_ack", [False, True])
def test_restarted_authority_guided_release_verifies_without_adopting_or_replaying(
    monkeypatch, preflight, lost_ack
):
    client, dal, snapshot, source, _, _ = authority_fixture(
        monkeypatch, preflight=preflight, lost_ack=lost_ack
    )
    adapter = ConfigReadRecoveryAdapter(dal, client, account="account-a", storage_owner="fixture")
    store = Store()
    service = RecoveryService(store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3)
    row = service.review_source(ACTOR, adapter.kind, source)
    assert row["evidence"]["actions"]["release_read"]["label"] == "Release abandoned read"
    dal.settle.assert_not_called()  # Investigation and monitor refresh cannot release.
    row = service.execute(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "release_read",
        "Confirmed displayed verification",
    )
    assert row["State"] == "resolved"
    assert store.actions[0]["State"] == "verified"
    dal.settle.assert_called_once()
    service.review(ACTOR, row["IncidentID"])
    dal.settle.assert_called_once()
    assert not snapshot["resources"]


def test_changed_reservation_after_preview_does_not_release(monkeypatch):
    client, dal, snapshot, source, _, _ = authority_fixture(monkeypatch)
    preview = client.inspect_configuration_recovery(source)
    snapshot["resources"][0]["Fence"] += 1
    with pytest.raises(SourceConflict):
        client.apply_configuration_recovery(source, preview["token"], "admin", "confirmed")
    dal.settle.assert_not_called()


def test_missing_private_evidence_or_live_stream_has_no_repair(monkeypatch):
    client, dal, snapshot, source, documents, stream = authority_fixture(monkeypatch)
    stream["State"] = "open"
    snapshot["streams"][0]["State"] = "open"
    preview = client.inspect_configuration_recovery(source)
    assert not preview["eligible"]
    with pytest.raises(SourceConflict):
        client.apply_configuration_recovery(source, preview["token"], "admin", "confirmed")
    dal.settle.assert_not_called()


def test_transient_unverifiable_evidence_does_not_retire_pending_action():
    client = Mock()
    client.inspect_configuration_recovery.return_value = dict(
        eligible=False, outcome="held", token="b" * 64, settled_token=None
    )
    adapter = ConfigReadRecoveryAdapter(Mock(), client, account="a", storage_owner="b")
    assert adapter.reconcile("source", {"EvidenceHash": "a" * 64}) is None
    client.apply_configuration_recovery.assert_not_called()


def test_authorized_automatic_policy_uses_same_durable_receipt_and_verification(monkeypatch):
    client, dal, snapshot, source, _, _ = authority_fixture(monkeypatch, lost_ack=True)
    adapter = ConfigReadRecoveryAdapter(dal, client, account="account-a", storage_owner="fixture")
    store = Store()
    service = RecoveryService(store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3)
    row = service.review_source(ACTOR, adapter.kind, source)
    result = service.recover_automatic(row["IncidentID"])
    assert result["State"] == "resolved"
    assert store.actions[0]["Actor"] == "system:guided_recovery"
    assert store.actions[0]["State"] == "verified"
    assert len(store.actions) == 1
    dal.settle.assert_called_once()


def test_automatic_policy_never_accepts_partial_import_or_unverifiable_read(monkeypatch):
    from tests.test_guided_recovery import setup

    service, import_dal, store, row = setup("partial")
    assert service.recover_automatic(row["IncidentID"])["State"] == "open"
    assert not store.actions and not import_dal.calls
    client, dal, snapshot, source, _, stream = authority_fixture(monkeypatch)
    stream["State"] = snapshot["streams"][0]["State"] = "open"
    adapter = ConfigReadRecoveryAdapter(dal, client, account="account-a", storage_owner="fixture")
    store = Store()
    service = RecoveryService(store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3)
    row = service.review_source(ACTOR, adapter.kind, source)
    assert service.recover_automatic(row["IncidentID"])["State"] == "open"
    assert not store.actions
    dal.settle.assert_not_called()


def test_broker_rejects_caller_authored_targets_and_binds_result(monkeypatch):
    from uuid import uuid4

    from scripts.run_export_authority import AuthorityBroker
    from services.export_runtime_composition import AuthorityClient, RuntimeRegistration
    from tests.test_export_runtime_composition import registration_fixture

    source = str(uuid4())
    boundary = Mock(fingerprint="d" * 64)
    broker = AuthorityBroker(Mock(), RuntimeRegistration(registration_fixture()), boundary=boundary)
    checked = dict(
        preparation_id=source,
        token="a" * 64,
        eligible=True,
        outcome="abandoned_read",
        settled_token=None,
        explanation="Verified read",
    )
    inspect = Mock(return_value=checked)
    monkeypatch.setattr(module, "inspect_configuration_recovery", inspect)
    client = object.__new__(AuthorityClient)
    client._invoke = lambda message: broker.dispatch(
        dict(message, deployment_hash=boundary.fingerprint)
    )
    assert client.inspect_configuration_recovery(source) == checked
    boundary.recheck.assert_called_once()
    for extra in ("resources", "server", "database", "proof", "owner"):
        with pytest.raises(ValueError):
            client._invoke(
                dict(
                    version=1,
                    action="inspect_configuration_recovery",
                    preparation_id=source,
                    **{extra: "caller supplied"},
                )
            )
    checked["preparation_id"] = str(uuid4())
    from services.export_execution_authority import ExecutionUncertain

    with pytest.raises(ExecutionUncertain):
        client.inspect_configuration_recovery(source)
