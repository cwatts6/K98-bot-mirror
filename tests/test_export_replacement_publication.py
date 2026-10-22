"""Final incident settlement verifies the exact replacement receipt and stream scope."""

from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_replacement_authority import ReplacementAuthority
from services.legacy_export_snapshot_service import configuration_digest
from tests.test_export_replacement_content import expected_hash, legacy_records
from tests.test_export_runtime_composition import registration_fixture


@pytest.fixture
def published(monkeypatch):
    registration = registration_fixture()
    file_id = "legacy-scan_data"
    job_id, attempt_id, stream_id, owner = (str(uuid4()) for _ in range(4))
    part = dict(
        FileID=file_id,
        Role="output",
        ManifestHash="c" * 64,
        GridCount=1,
        RowCount=2,
        CellCount=4,
        PartNo=1,
        VerificationState="verified",
    )
    document = dict(
        generation=dict(export_key="retained-report"),
        parts=[
            dict(file_id=file_id, role="output", manifest_hash="c" * 64, grids=1, rows=2, cells=4)
        ],
    )
    receipt = dict(
        export_key="retained-report",
        attempt_id=attempt_id,
        fence=7,
        files=[file_id],
        audience="private",
        remote_id="verified-output",
    )
    attempt = dict(
        JobID=job_id,
        AttemptID=attempt_id.upper(),
        Phase="published",
        ManifestJson=json.dumps(document),
        ManifestHash=digest(document).hex(),
        PartCount=1,
        ReceiptJson=json.dumps(receipt),
    )
    job = dict(
        JobID=job_id,
        State="confirmed",
        AccountKey="account-a",
        OwnerID=owner,
        Fence=7,
        Version=9,
        ConsumerKind="scan_data",
        ProvenanceJson=json.dumps(
            dict(replacement=dict(original_job_id="original", original_input_sha256="a" * 64))
        ),
    )
    snapshot = dict(job=job, attempts=[attempt], streams=[dict(StreamID=stream_id)], resources=[])
    stream = dict(
        JobID=job_id,
        AccountKey="account-a",
        Fence=7,
        OwnerID=owner.upper(),
        StreamID=stream_id,
        SessionID=str(uuid4()),
        ChildIdentity=str(uuid4()),
        ClosureReference=str(uuid4()),
        NestedToken=None,
        OutputOperationID=None,
        RegistrationHash=bytes.fromhex(
            configuration_digest(registration["legacy_configuration"]["scan_data"])
        ),
        Epoch=None,
        Purpose="mutation",
        ScopeJson=json.dumps(
            dict(
                resources=[
                    dict(key="account:account-a", version=1),
                    dict(key="destination:" + file_id, version=1),
                ]
            )
        ),
    )
    verifier = Mock()
    monkeypatch.setattr(
        "services.export_reconciliation_service.ClosedStreamVerifier", Mock(return_value=verifier)
    )
    monkeypatch.setattr(
        "services.export_replacement_delivery_dal.ReplacementDeliveryDAL.publication_parts",
        lambda self, job: [part],
    )
    authority = ReplacementAuthority.__new__(ReplacementAuthority)
    authority.connect = Mock(side_effect=AssertionError("No live SQL"))
    authority.authority = SimpleNamespace(
        dal=SimpleNamespace(read_stream=lambda key: deepcopy(stream)), store=object()
    )
    records = legacy_records()
    for request, _ in records:
        request.target = file_id
    monkeypatch.setattr(
        "services.export_replacement_publication.publication_records", lambda *args: records
    )
    return SimpleNamespace(
        service=authority,
        snapshot=snapshot,
        stream=stream,
        verifier=verifier,
        receipt=receipt,
        part=part,
        activation=dict(
            registration=registration,
            mapping={"old-file": file_id},
            input_commitment=dict(
                JobID="original",
                AccountKey="account-a",
                ConsumerKind="scan_data",
                InputHash="a" * 64,
                IntentID=None,
                ProvenanceJson=json.dumps(dict(output_sha256=expected_hash())),
            ),
        ),
    )


def test_matching_receipt_requires_original_closed_journal(published):
    p = published
    p.service.verify_delivery(p.snapshot, p.activation)
    p.verifier.verify.assert_called_once()
    p.verifier.verify.side_effect = SourceConflict("Missing original closure")
    with pytest.raises(SourceConflict, match="closure"):
        p.service.verify_delivery(p.snapshot, p.activation)


@pytest.mark.parametrize(
    "field,value",
    [
        ("files", ["other-file"]),
        ("fence", 8),
        ("export_key", "different-input"),
        ("remote_id", ""),
        ("attempt_id", str(uuid4())),
    ],
)
def test_receipt_mismatch_cannot_close_incident(published, field, value):
    p = published
    p.receipt[field] = value
    p.snapshot["attempts"][0]["ReceiptJson"] = json.dumps(p.receipt)
    with pytest.raises(SourceConflict, match="receipt"):
        p.service.verify_delivery(p.snapshot, p.activation)
    p.verifier.verify.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("OwnerID", str(uuid4())),
        ("Fence", 8),
        ("RegistrationHash", b"x" * 32),
    ],
)
def test_closed_stream_cannot_belong_to_another_owner_or_registration(published, field, value):
    p = published
    p.stream[field] = value
    with pytest.raises(SourceConflict):
        p.service.verify_delivery(p.snapshot, p.activation)
    p.verifier.verify.assert_not_called()


def test_unverified_parts_and_retained_resource_keep_incident_open(published):
    p = published
    p.part["VerificationState"] = "pending"
    with pytest.raises(SourceConflict, match="receipt"):
        p.service.verify_delivery(p.snapshot, p.activation)
    p.part["VerificationState"] = "verified"
    p.snapshot["resources"].append(dict(ActiveJobID=p.snapshot["job"]["JobID"]))
    with pytest.raises(SourceConflict, match="ownership"):
        p.service.verify_delivery(p.snapshot, p.activation)


@pytest.mark.parametrize("damage", ["missing", "hash", "activation", "mapping", "input"])
def test_waiting_private_decision_cannot_be_missing_or_substituted(published, damage):
    from services.export_execution_protocol import encode

    p = published
    activation_id = str(uuid4())
    p.activation.update(queued_continuation=True, activation_id=activation_id)
    evidence = dict(reference=str(uuid4()), sha256="d" * 64)
    decision = dict(
        kind="replacement_waiting_input/1",
        activation_id=activation_id,
        mapping=deepcopy(p.activation["mapping"]),
        input_commitment=deepcopy(p.activation["input_commitment"]),
    )
    lineage = json.loads(p.snapshot["job"]["ProvenanceJson"])
    lineage["replacement"]["input_evidence"] = evidence
    store = Mock()
    p.service.authority.store = store
    store.read_reference.return_value = encode(decision)
    p.snapshot["job"]["ProvenanceJson"] = json.dumps(lineage)
    assert p.service.verify_input(p.snapshot, p.activation) == decision["input_commitment"]
    if damage == "missing":
        lineage["replacement"].pop("input_evidence")
    elif damage == "hash":
        evidence["sha256"] = "not-a-hash"
    elif damage == "activation":
        decision["activation_id"] = str(uuid4())
    elif damage == "mapping":
        decision["mapping"]["old-file"] = "another-file"
    else:
        decision["input_commitment"]["InputHash"] = "b" * 64
    store.read_reference.return_value = encode(decision)
    p.snapshot["job"]["ProvenanceJson"] = json.dumps(lineage)
    with pytest.raises(SourceConflict):
        p.service.verify_input(p.snapshot, p.activation)
