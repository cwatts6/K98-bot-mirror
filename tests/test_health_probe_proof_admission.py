"""A health observation cannot reserve resources underneath an owned proof."""

from threading import Event, Thread
from unittest.mock import Mock
from uuid import uuid4

import pytest

from services.export_runtime_composition import (
    AuthorityClient,
    AuthorityStream,
    LocalAuthorityClient,
)
from services.legacy_export_snapshot_service import ConfigurationAdmissionDeferred
from tests.test_legacy_export_snapshot import producer_runtime
from tests.test_publication_proof_progress import endpoint


def runtime_with_admission(tmp_path, client):
    runtime, dal = producer_runtime(
        tmp_path, configuration={"config": {"destinations": ["file-a"]}}
    )
    runtime.configuration_admission = client.configuration_admission
    return runtime, dal


def test_running_publication_defers_health_before_any_ticket_and_releases_after_completion(
    tmp_path,
):
    broker, client, _ = endpoint()
    runtime, dal = runtime_with_admission(tmp_path, client)
    entered, finish = Event(), Event()
    results = []

    def issue(**kwargs):
        entered.set()
        assert finish.wait(5)
        return dict(state="confirmed", snapshot_hash="a" * 64, proof_id=str(uuid4()))

    broker.issuer.issue.side_effect = issue
    worker = Thread(
        target=lambda: results.append(client.prove("publication", str(uuid4()), "a" * 64))
    )
    worker.start()
    try:
        assert entered.wait(5)
        with pytest.raises(ConfigurationAdmissionDeferred):
            with runtime.configuration_requests():
                pytest.fail("Deferred probe entered")
        dal.request.assert_not_called()
        dal.claim.assert_not_called()
        dal.uncertain.assert_not_called()
    finally:
        finish.set()
        worker.join(5)
    assert not worker.is_alive() and results[0]["state"] == "confirmed"
    with runtime.configuration_requests():
        pass
    dal.request.assert_called_once()
    dal.transition.assert_called_once()


def test_existing_configuration_read_blocks_proof_until_settlement(tmp_path):
    client = object.__new__(AuthorityClient)
    runtime, dal = runtime_with_admission(tmp_path, client)
    entered, finish, proving = Event(), Event(), Event()
    client._prove = Mock(side_effect=lambda *a, **k: proving.set())

    def read():
        with runtime.configuration_requests():
            entered.set()
            assert finish.wait(5)

    reader = Thread(target=read)
    reader.start()
    assert entered.wait(5)
    proof = Thread(target=lambda: client.prove("publication", str(uuid4()), "a" * 64))
    proof.start()
    try:
        assert not proving.wait(0.05)
        # The authority's internal observational stream is not a competing Bot
        # read. It must not deadlock on the Bot thread waiting for its receipt.
        with object.__new__(LocalAuthorityClient).configuration_admission(wait_for_admission=False):
            pass
    finally:
        finish.set()
        reader.join(5)
        proof.join(5)
    assert not reader.is_alive() and not proof.is_alive() and proving.is_set()
    dal.transition.assert_called_once()


def test_uncertain_proof_reply_releases_only_local_scheduling_gate(tmp_path):
    from services.export_execution_authority import ExecutionUncertain

    client = object.__new__(AuthorityClient)
    client._invoke = Mock(side_effect=ExecutionUncertain("Lost reply"))
    with pytest.raises(ExecutionUncertain):
        client.prove("publication", str(uuid4()), "a" * 64)
    runtime, dal = runtime_with_admission(tmp_path, client)
    # SQL still decides admission; the local gate cannot release its holds.
    dal.claim.return_value = None
    with pytest.raises(ConfigurationAdmissionDeferred):
        with runtime.configuration_requests():
            pytest.fail("SQL-refused read entered")
    dal.claim.assert_called_once()
    dal.uncertain.assert_not_called()
    dal.transition.assert_not_called()


@pytest.mark.parametrize("lost_reply", [False, True])
def test_admitted_probe_retains_same_claim_through_authenticated_busy(
    tmp_path, monkeypatch, lost_reply
):
    from services.export_execution_authority import ExecutionUncertain
    from services.export_proof_progress import AuthorityProofBusy

    client = object.__new__(AuthorityClient)
    runtime, dal = runtime_with_admission(tmp_path, client)
    transport = Mock()
    transport.open_stream.side_effect = [
        AuthorityProofBusy("An earlier owned proof is still finishing"),
        ExecutionUncertain("Lost reply") if lost_reply else None,
    ]
    runtime.authority_stream = lambda claim, scope: AuthorityStream(transport, {"Purpose": "probe"})
    runtime.dal.execution_evidence = runtime.coordinator.execution_evidence = True
    monkeypatch.setattr("time.sleep", lambda _: None)

    def probe():
        with runtime.configuration_requests():
            pass

    if lost_reply:
        with pytest.raises(ExecutionUncertain):
            probe()
        dal.uncertain.assert_called_once_with(dal.claim.return_value)
        dal.transition.assert_not_called()
    else:
        probe()
        dal.uncertain.assert_not_called()
        dal.transition.assert_called_once()
        transport.close_stream.assert_called_once()
    dal.request.assert_called_once()
    dal.claim.assert_called_once()
    assert len({call.args[0] for call in transport.open_stream.call_args_list}) == 1
