from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.config_preparation_recovery_service import ConfigPreparationRecovery, RecoveryTarget
from services.export_execution_protocol import encode
from tests.test_export_reconciliation_service import closed_stream_fixture


def fixture():
    verifier, stream, request, events, documents = closed_stream_fixture(purpose="probe")
    prep, owner = str(uuid4()), str(uuid4())
    target = RecoveryTarget(
        "fixture",
        "disposable",
        prep,
        "account-a",
        owner,
        10,
        3,
        (("account:account-a", 22), ("destination:file-a", 19)),
        (stream["StreamID"],),
    )
    empty_hash = hashlib.sha256(b"").digest()
    stream.update(
        PreparationID=prep,
        OwnerID=owner,
        Fence=10,
        ClaimVersion=2,
        JobID=None,
        OutputOperationID=None,
        NestedToken=None,
        Epoch=None,
        ScopeJson=json.dumps(
            {"resources": [{"key": k, "version": v - 1} for k, v in target.resources]}
        ),
        LastSequence=0,
        EventDigest=empty_hash,
    )
    closure = json.loads(documents[stream["ClosureReference"]])
    closure.update(last_sequence=0, event_digest=empty_hash.hex())
    documents[stream["ClosureReference"]] = encode(closure)
    stream["ClosureHash"] = hashlib.sha256(documents[stream["ClosureReference"]]).digest()
    verifier.dal.stream_digest.return_value = (0, empty_hash)
    verifier.dal.request_ids = lambda _: (x for x in ())
    p = dict(
        PreparationID=prep,
        AccountKey=target.account,
        OwnerID=owner,
        Fence=10,
        Version=3,
        ConsumerKind="config",
        State="uncertain",
        KVK_NO=None,
        StorageOwner="fixture",
        JobID=None,
        GenerationJson=None,
        SpoolKey=None,
        SpoolBytes=None,
        SpoolHash=None,
        RequestJson="{}",
        RequestHash=digest({}).hex(),
    )
    from kvk.dal.source_output_pool_dal import _wire

    snapshot = dict(
        server="fixture",
        database="disposable",
        preparation=p,
        membership=[k for k, _ in target.resources],
        streams=[_wire(stream)],
        request_count=0,
        event_count=0,
        resources=[
            dict(
                ResourceKey=k,
                Version=v,
                ActivePreparationID=prep,
                OwnerID=owner,
                Fence=10,
                ActiveJobID=None,
                ActiveOutputOperationID=None,
                BlockedReason="Preparation requires authoritative reconciliation",
            )
            for k, v in target.resources
        ],
    )
    dal = Mock()
    dal.snapshot.side_effect = lambda _: deepcopy(snapshot)
    service = ConfigPreparationRecovery(
        dal=dal,
        execution=verifier.dal,
        store=verifier.store,
        target=target,
        registration_hash=(b"r" * 32).hex(),
        storage_owner="fixture",
    )
    return service, snapshot, stream, documents


def test_empty_closed_stream_recovers_only_as_unavailable_and_retains_audit():
    service, snapshot, _, _ = fixture()
    report = service.inspect()
    service.dal.settle.assert_not_called()
    assert report["provider_observation"] is False
    audit = service.apply(
        approved_snapshot_sha256=report["snapshot_sha256"], actor="operator", reason="verified"
    )
    assert audit["before"] == snapshot
    assert audit["outcome"] == "abandoned_before_dispatch"
    assert audit["closures"][0]["request_count"] == 0
    service.dal.settle.assert_called_once_with(service.target, snapshot, audit)


@pytest.mark.parametrize(
    "damage",
    [
        "server",
        "owner",
        "fence",
        "version",
        "membership",
        "extra_resource",
        "extra_stream",
        "active_stream",
        "request",
        "event",
        "write",
        "hash",
        "scope",
    ],
)
def test_mismatches_remain_blocked(damage):
    service, snapshot, _, _ = fixture()
    if damage == "server":
        snapshot["server"] = "other"
    elif damage in {"owner", "fence", "version"}:
        snapshot["preparation"][
            {"owner": "OwnerID", "fence": "Fence", "version": "Version"}[damage]
        ] = "changed"
    elif damage == "membership":
        snapshot["membership"].pop()
    elif damage == "extra_resource":
        snapshot["resources"].append(snapshot["resources"][0])
    elif damage == "extra_stream":
        snapshot["streams"].append(snapshot["streams"][0])
    elif damage == "active_stream":
        snapshot["streams"][0]["State"] = "open"
    elif damage == "request":
        snapshot["request_count"] = 1
    elif damage == "event":
        snapshot["event_count"] = 1
    elif damage == "write":
        snapshot["streams"][0]["Purpose"] = "mutation"
    elif damage == "hash":
        snapshot["streams"][0]["RegistrationHash"] = "ff" * 32
    elif damage == "scope":
        snapshot["streams"][0]["ScopeJson"] = "{}"
    with pytest.raises(SourceConflict):
        service.apply(
            approved_snapshot_sha256=digest(snapshot).hex(), actor="operator", reason="test"
        )
    service.dal.settle.assert_not_called()


@pytest.mark.parametrize(
    "damage", ["missing", "hash", "child", "job", "signaled", "digest", "version"]
)
def test_private_closure_is_mandatory(damage):
    service, snapshot, stream, documents = fixture()
    ref = stream["ClosureReference"]
    body = json.loads(documents[ref])
    if damage == "missing":
        documents.pop(ref)
    elif damage == "hash":
        documents[ref] = b"{}"
    else:
        if damage == "child":
            body["closure"]["child_id"] = str(uuid4())
        elif damage == "job":
            body["closure"]["job_empty"] = False
        elif damage == "signaled":
            body["closure"]["process_signaled"] = False
        elif damage == "digest":
            body["event_digest"] = "ee" * 32
        elif damage == "version":
            body["version"] -= 1
        documents[ref] = encode(body)
        stream["ClosureHash"] = hashlib.sha256(documents[ref]).digest()
    with pytest.raises((SourceConflict, KeyError)):
        service.inspect()
    service.dal.settle.assert_not_called()


def test_snapshot_race_and_unapproved_snapshot_refuse_settlement():
    service, snapshot, _, _ = fixture()
    changed = deepcopy(snapshot)
    changed["resources"][0]["Version"] += 1
    service.dal.snapshot.side_effect = [snapshot, changed]
    with pytest.raises(SourceConflict, match="changed"):
        service.inspect()
    service.dal.settle.assert_not_called()
    service, _, _, _ = fixture()
    with pytest.raises(SourceConflict, match="Approved"):
        service.apply(approved_snapshot_sha256="00" * 32, actor="operator", reason="test")
    service.dal.settle.assert_not_called()


def test_unknown_read_verification_cannot_be_used_as_health_or_write_finality():
    verifier, stream, request, events, documents = closed_stream_fixture(purpose="probe")
    events[-1]["State"] = "unknown"
    result = verifier.verify(
        stream["StreamID"],
        account="account-a",
        registration_hash=b"r" * 32,
        require_observation=False,
        allow_failed_reads=True,
    )
    assert result.successful_reads == result.dispatched_mutations == 0
    with pytest.raises(SourceConflict):
        verifier.verify(stream["StreamID"], account="account-a", registration_hash=b"r" * 32)
    stream["Purpose"] = "mutation"
    with pytest.raises(SourceConflict):
        verifier.verify(
            stream["StreamID"],
            account="account-a",
            registration_hash=b"r" * 32,
            require_observation=False,
            allow_failed_reads=True,
        )


def test_automatic_recovery_never_adopts_an_old_stream():
    from services.config_preparation_recovery_service import recover_owned_configuration

    authority = SimpleNamespace(_lock=__import__("threading").RLock(), _streams={})
    with pytest.raises(SourceConflict, match="this authority"):
        recover_owned_configuration(authority, Mock(), str(uuid4()))


def test_current_authority_recovery_verifies_private_closure_before_settlement(monkeypatch):
    import threading

    from services.config_preparation_recovery_service import recover_owned_configuration
    from services.legacy_export_snapshot_service import configuration_digest

    service, snapshot, stream, _ = fixture()
    config = {"destinations": ["file-a"]}
    stream["SessionID"] = str(uuid4())
    stream["RegistrationHash"] = bytes.fromhex(configuration_digest(config))
    snapshot["streams"][0]["RegistrationHash"] = stream["RegistrationHash"].hex()
    service.dal.identity.return_value = {"server": "fixture", "database": "disposable"}
    service.verifier.dal.connect = Mock()
    authority = SimpleNamespace(
        _lock=threading.RLock(),
        session_id=stream["SessionID"],
        _streams={
            stream["StreamID"]: SimpleNamespace(
                closed=True,
                purpose="probe",
                child=SimpleNamespace(identity=stream["ChildIdentity"]),
            )
        },
        dal=service.verifier.dal,
        store=service.verifier.store,
    )
    monkeypatch.setattr(
        "services.config_preparation_recovery_dal.ConfigPreparationRecoveryDAL",
        lambda _: service.dal,
    )
    registration = SimpleNamespace(
        value=lambda: {
            "account": "account-a",
            "storage_owner": "fixture",
            "legacy_configuration": {"config": config},
        }
    )
    result = recover_owned_configuration(authority, registration, stream["StreamID"])
    assert result["state"] == "unavailable" and result["provider_observation"] is False
    service.dal.settle.assert_called_once()
    audit = service.dal.settle.call_args.args[2]
    assert audit["actor"] == "system:configuration_recovery"
    assert audit["closures"][0]["request_count"] == 0
