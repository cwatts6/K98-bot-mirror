from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from core.export_execution_host import PrivateEvidenceStore
from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit
from services import config_recovery_authority as authority_module
from services.config_read_containment import stream_wire
from services.config_read_recovery_adapter import ConfigReadRecoveryAdapter
from services.export_reconciliation_service import CatalogueVerifier, ClosedStreamVerifier
from services.recovery_service import RecoveryService
from tests.test_config_recovery_guided import authority_fixture
from tests.test_guided_recovery import ACTOR, Store


def private_store(documents):
    def put(raw):
        key = uuid4()
        documents[str(key)] = raw
        return SimpleNamespace(key=key.hex, sha256=hashlib.sha256(raw).hexdigest())

    def read(reference, expected):
        raw = documents[str(reference).lower()]
        assert hashlib.sha256(raw).digest() == bytes(expected)
        return raw

    return SimpleNamespace(put=put, read_reference=read)


def setup(monkeypatch, state="frozen", lost_ack=False):
    client, dal, snapshot, source, docs, stream = authority_fixture(monkeypatch)
    stream.update(
        SessionID=str(uuid4()),
        State=state,
        ActiveAccountKey=None if state == "closed" else "account-a",
    )
    snapshot["streams"] = [stream_wire(stream)]
    docs.clear()  # Historical private bytes are deliberately unavailable.
    client.authority.store = private_store(docs)
    registration = SimpleNamespace(
        value=lambda: dict(
            account="account-a",
            storage_owner="fixture",
            legacy_configuration={"config": {"destinations": ["file-a"]}},
        )
    )
    client.contain_configuration_recovery = lambda key, token, actor, reason: (
        authority_module.apply_configuration_recovery(
            client.authority, registration, key, token, actor, reason, action="contain_read"
        )
    )

    def settle(target, expected, audit, *, containment=None):
        assert expected == snapshot and containment is not None
        assert audit["child_termination_verified"] is False
        seal = containment["streams"][stream["StreamID"]]
        stream.update(
            State="read_contained",
            ActiveAccountKey=None,
            Version=stream["Version"] + 1,
            ClosureHash=bytes.fromhex(containment["sha256"]),
            ClosureReference=containment["reference"],
            EventDigest=bytes.fromhex(seal["event_digest"]),
        )
        snapshot["streams"] = [stream_wire(stream)]
        snapshot["preparation"].update(State="unavailable", GenerationJson=json.dumps(audit))
        snapshot["resources"] = []
        if lost_ack:
            raise UncertainCommit("commit acknowledged by later read")

    dal.settle.side_effect = settle
    adapter = ConfigReadRecoveryAdapter(dal, client, account="account-a", storage_owner="fixture")
    store = Store()
    service = RecoveryService(store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3)
    return client, dal, snapshot, source, stream, docs, service, store


@pytest.mark.parametrize("state", ["open", "frozen", "closed"])
@pytest.mark.parametrize("lost_ack", [False, True])
def test_guided_isolation_is_never_automatic_and_verifies_lost_reply(monkeypatch, state, lost_ack):
    client, dal, snapshot, source, stream, docs, service, store = setup(
        monkeypatch, state, lost_ack
    )
    row = service.review_source(ACTOR, "configuration_read", source)
    assert set(row["evidence"]["actions"]) == {"contain_read"}
    assert service.recover_automatic(row["IncidentID"])["State"] == "open"
    assert not store.actions
    dal.settle.assert_not_called()
    with pytest.raises(SourceConflict):
        client.apply_configuration_recovery(source, row["EvidenceHash"], "admin", "confirm")
    result = service.execute(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "contain_read",
        "Discard this failed read",
    )
    assert result["State"] == "resolved"
    assert len(store.actions) == 1 and store.actions[0]["State"] == "verified"
    assert snapshot["resources"] == [] and stream["State"] == "read_contained"
    assert "no child termination" in result["evidence"]["explanation"]
    service.refresh(row["IncidentID"])
    assert dal.settle.call_count == 1


@pytest.mark.parametrize(
    "damage",
    [
        "owner",
        "fence",
        "membership",
        "mutation",
        "enrollment",
        "sequence",
        "request_mutation",
        "event_gap",
    ],
)
def test_invalid_or_non_read_evidence_never_offers_isolation(monkeypatch, damage):
    client, dal, snapshot, source, stream, docs, service, store = setup(monkeypatch)
    if damage in {"owner", "fence"}:
        snapshot["resources"][0][{"owner": "OwnerID", "fence": "Fence"}[damage]] = "other"
    elif damage == "membership":
        snapshot["membership"].pop()
    elif damage in {"mutation", "enrollment"}:
        stream["Purpose"] = damage
    elif damage == "sequence":
        stream["LastSequence"] = 1
    else:
        request = str(uuid4())
        client.authority.dal.request_ids = lambda _: (x for x in [request])
        client.authority.dal.read_request.return_value = (
            dict(
                RequestID=request,
                StreamID=stream["StreamID"],
                Sequence=1,
                RequestKind="mutation" if damage == "request_mutation" else "read",
                Operation="sheets.values.get",
            ),
            [dict(RequestID=request, EventSequence=2, State="prepared")],
        )
    snapshot["streams"] = [stream_wire(stream)]
    row = service.review_source(ACTOR, "configuration_read", source)
    assert not row["evidence"]["actions"]
    assert not store.actions
    dal.settle.assert_not_called()


def test_contained_read_is_historical_coverage_but_never_fresh_observation(monkeypatch):
    client, dal, snapshot, source, stream, docs, service, store = setup(monkeypatch)
    row = service.review_source(ACTOR, "configuration_read", source)
    service.execute(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "contain_read",
        "Discard read",
    )
    execution = client.authority.dal
    verifier = ClosedStreamVerifier(dal=execution, store=client.authority.store)
    kwargs = dict(account="account-a", registration_hash=stream["RegistrationHash"])
    checked = verifier.verify(
        stream["StreamID"], **kwargs, require_observation=False, allow_failed_reads=True
    )
    assert checked.successful_reads == checked.dispatched_mutations == 0
    with pytest.raises(SourceConflict, match="fresh"):
        verifier.verify(stream["StreamID"], **kwargs)
    execution.read_catalogue = lambda *_: (x for x in [deepcopy(stream)])
    history, _ = CatalogueVerifier(dal=execution, store=client.authority.store)._catalogue(
        account="account-a", targets=["file-a"]
    )
    assert history.count == 1
    stream["SessionID"] = str(uuid4())
    with pytest.raises(SourceConflict, match="identity"):
        verifier.verify(
            stream["StreamID"], **kwargs, require_observation=False, allow_failed_reads=True
        )


def test_stale_confirmation_cannot_release_changed_ownership(monkeypatch):
    client, dal, snapshot, source, stream, docs, service, store = setup(monkeypatch)
    row = service.review_source(ACTOR, "configuration_read", source)
    snapshot["resources"][0]["Version"] += 1
    with pytest.raises(SourceConflict):
        service.execute(
            ACTOR,
            row["IncidentID"],
            row["Revision"],
            row["EvidenceHash"],
            "contain_read",
            "Discard read",
        )
    dal.settle.assert_not_called()


@pytest.mark.parametrize("failure", ["hash", "decrypt"])
def test_real_private_store_failure_offers_confirmed_containment(monkeypatch, tmp_path, failure):
    client, dal, snapshot, source, stream, _, service, store = setup(monkeypatch, "closed")
    win_types = pytest.importorskip("pywintypes") if failure == "decrypt" else None

    def unprotect(raw):
        if failure == "decrypt" and raw == b"unreadable historical evidence":
            raise win_types.error(13, "CryptUnprotectData", "Invalid data")
        return raw

    private = PrivateEvidenceStore(
        tmp_path, "fixture", protect=lambda raw: raw, unprotect=unprotect
    )
    original = private._store.put(b"unreadable historical evidence")
    stream["ClosureReference"] = str(UUID(original.key))
    stream["ClosureHash"] = b"x" * 32
    snapshot["streams"] = [stream_wire(stream)]
    client.authority.store = private
    row = service.review_source(ACTOR, "configuration_read", source)
    assert set(row["evidence"]["actions"]) == {"contain_read"}
    assert service.recover_automatic(row["IncidentID"])["State"] == "open"
    dal.settle.assert_not_called()
    result = service.execute(
        ACTOR, row["IncidentID"], row["Revision"], row["EvidenceHash"],
        "contain_read", "Discard failed read",
    )
    assert result["State"] == "resolved" and store.actions[0]["State"] == "verified"
    assert private._store.read(original) == b"unreadable historical evidence"


def test_sql_runtime_error_is_not_reclassified_as_private_evidence_failure(monkeypatch):
    client, dal, _, source, _, _, _, _ = setup(monkeypatch, "closed")
    client.authority.dal.read_stream.side_effect = RuntimeError("SQL connection lost")
    with pytest.raises(RuntimeError, match="SQL connection lost"):
        client.inspect_configuration_recovery(source)
    dal.settle.assert_not_called()


def test_client_broker_uses_distinct_confirmed_action_and_rechecks_boundary(monkeypatch):
    from scripts.run_export_authority import AuthorityBroker
    from services.export_runtime_composition import AuthorityClient, RuntimeRegistration
    from tests.test_export_runtime_composition import registration_fixture

    source = str(uuid4())
    checked = dict(
        preparation_id=source,
        token="a" * 64,
        eligible=True,
        outcome="read_containment",
        settled_token=None,
        explanation="Read-only ledger",
    )
    apply = Mock(return_value=checked)
    monkeypatch.setattr(authority_module, "apply_configuration_recovery", apply)
    boundary = Mock(fingerprint="d" * 64)
    broker = AuthorityBroker(Mock(), RuntimeRegistration(registration_fixture()), boundary=boundary)
    client = object.__new__(AuthorityClient)
    client._invoke = lambda msg: broker.dispatch(dict(msg, deployment_hash=boundary.fingerprint))
    assert (
        client.contain_configuration_recovery(source, "a" * 64, "admin", "Discard read") == checked
    )
    assert apply.call_args.kwargs == dict(action="contain_read")
    boundary.recheck.assert_called_once()


@pytest.mark.asyncio
async def test_isolation_button_opens_checklist_before_confirmation(monkeypatch):
    from unittest.mock import AsyncMock

    from ui.views import recovery_view as view

    _, dal, _, source, _, _, service, _ = setup(monkeypatch)
    row = service.review_source(ACTOR, "configuration_read", source)
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(view, "call", AsyncMock(return_value=row))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        item
        for item in view.RecoveryIncidentView(row).children
        if item.label == "Isolate read & release"
    )
    await button.callback(interaction)
    view.call.assert_awaited_once_with("review", ACTOR, row["IncidentID"])
    sent = interaction.followup.send.call_args.kwargs
    assert sent["ephemeral"] and isinstance(sent["view"], view.RecoveryConfirmView)
    assert "previously dispatched read may still finish" in sent["embed"].fields[0].value
    assert sent["view"].action == "contain_read"
    dal.settle.assert_not_called()
