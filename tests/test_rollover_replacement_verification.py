"""Completion consumes real sealed synthetic phase journals, never just SQL state."""

from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_execution_protocol import CATALOGUE_SEED
from services.export_rollover_evidence import observe_rollover_completion
from services.rollover_replacement import RolloverReplacementContinuation
from tests.test_export_rollover_evidence import probe_arguments, rollover_fixture
from tests.test_kvk_output_rollover import rollover


def completed():
    f = rollover_fixture()
    args, observations = probe_arguments(f)
    observed = observe_rollover_completion(**args)
    op = deepcopy(f.snapshot["operation"])
    stream = f.retain(observations, args["stream_id"], "probe", op["Version"])
    proof_id = str(uuid4())
    body = dict(
        state="completed",
        snapshot_hash=digest(f.snapshot).hex(),
        writer_terminated=True,
        files=json.loads(observed.original_clears_json),
        setup=json.loads(observed.setup_json),
        evidence_id="synthetic-independent-completion",
    )
    membership = json.dumps(
        dict(
            version=2,
            targets=sorted(body["files"]),
            history=dict(count=7, sha256=CATALOGUE_SEED.hex()),
            probe=dict(stream_id=args["stream_id"], version=stream["Version"]),
        )
    )
    row = dict(
        ProofID=proof_id,
        AccountKey=op["AccountKey"],
        ProofKind="rollover_complete",
        Outcome="completed",
        SnapshotHash=bytes.fromhex(body["snapshot_hash"]),
        RegistrationHash=bytes.fromhex(f.snapshot["pool"]["pool"]["RegistrationHash"]),
        EvidenceJson=json.dumps(body),
        MembershipJson=membership,
        MembershipHash=hashlib.sha256(membership.encode("utf-16-le")).digest(),
    )
    progress = json.loads(op["ProgressJson"])
    progress["reconciliation"] = dict(
        actor="recovery:" + str(uuid4()), proof=dict(body, proof_id=proof_id)
    )
    op.update(
        State="completed",
        Phase="complete",
        OwnerID=None,
        ActivePoolID=None,
        ProgressJson=json.dumps(progress),
    )
    f.dal.read_proof = lambda identifier: row if identifier == proof_id else None
    activation = dict(
        registration=dict(
            pools=[
                dict(
                    pool_id=op["PoolID"],
                    index_file_id=f.registration.index_file_id,
                    slot_file_ids=list(f.registration.slot_file_ids),
                    registration_sha256=f.snapshot["pool"]["pool"]["RegistrationHash"],
                )
            ]
        )
    )
    service = RolloverReplacementContinuation(
        dal=SimpleNamespace(read=lambda *_: op), authority=SimpleNamespace(dal=f.dal, store=f.store)
    )
    return f, service, op, activation, row


def test_completed_replacement_requires_intact_private_journals():
    f, service, op, activation, _ = completed()
    calls = len(f.api.calls)
    assert service.inspect("original", activation)["resolved"] is True
    assert len(f.api.calls) == calls
    assert f.trace


@pytest.mark.parametrize("ancestors", [("current",), tuple(str(n) for n in range(32))])
def test_invalid_replacement_ancestry_stops_before_loading_registration(ancestors):
    workflow = pytest.importorskip("services.rollover_replacement_authority").workflow

    owner = Mock()
    with pytest.raises(SourceConflict, match="ancestry cannot be verified"):
        workflow(owner, "current", ancestors=ancestors)
    owner.registrations.assert_not_called()


@pytest.mark.parametrize(
    "fault",
    [
        "proof",
        "phase",
        "owner",
        "wrong_account",
        "wrong_season",
        "membership",
        "missing_phase",
        "private_evidence",
        "foreign_probe",
        "probe_purpose",
        "probe_receipt_missing_from_catalogue",
    ],
)
def test_completion_does_not_hide_missing_or_mismatched_verification(fault):
    f, service, op, activation, row = completed()
    if fault == "proof":
        f.dal.read_proof = lambda _: None
    elif fault == "phase":
        op["Phase"] = "uncertain"
    elif fault == "owner":
        op["OwnerID"] = str(uuid4())
    elif fault == "wrong_account":
        row["AccountKey"] = "other-account"
    elif fault == "wrong_season":
        op["NewKVK"] += 1
    elif fault == "membership":
        row["MembershipHash"] = b"x" * 32
    elif fault == "missing_phase":
        key = next(k for k, v in f.records.items() if v["stream"]["Purpose"] == "mutation")
        del f.records[key]
    elif fault == "private_evidence":
        record = next(iter(f.records.values()))
        record["documents"][record["stream"]["ClosureReference"]] += b" "
    elif fault == "foreign_probe":
        probe = json.loads(row["MembershipJson"])["probe"]["stream_id"]
        f.records[probe]["stream"]["OutputOperationID"] = str(uuid4())
    elif fault == "probe_purpose":
        probe = json.loads(row["MembershipJson"])["probe"]["stream_id"]
        f.records[probe]["stream"]["Purpose"] = "mutation"
    elif fault == "probe_receipt_missing_from_catalogue":
        probe = json.loads(row["MembershipJson"])["probe"]["stream_id"]
        record = f.records[probe]
        record["documents"][record["stream"]["ClosureReference"]] += b" "
        catalogue = f.dal.read_catalogue
        f.dal.read_catalogue = lambda *args: (
            stream for stream in catalogue(*args) if stream["StreamID"] != probe
        )
    with pytest.raises((SourceConflict, KeyError)):
        service.inspect("original", activation)


def test_replacement_worker_stops_for_independent_guided_verification():
    service, repository, _ = rollover()
    operation = repository.operation.return_value
    plan = json.loads(operation["PlanJson"])
    plan["replacement_rollover"] = dict(operation_id=str(uuid4()))
    operation["PlanJson"] = json.dumps(plan)
    repository.files.return_value = ("file-a",)
    repository.phase.side_effect = lambda claim, *_: claim
    service.advance("replacement")
    repository.complete.assert_not_called()
    repository.uncertain.assert_not_called()
    assert repository.phase.call_args.args[1] == "setup_verified"


def test_stale_reconciled_admin_click_cannot_adopt_new_rollover_evidence():
    from services.rollover_replacement_adapter import RolloverReplacementAdapter

    base = Mock()
    base.discovery.rollover.return_value = dict(operation=dict(State="uncertain"))
    adapter = RolloverReplacementAdapter(base, runtime=Mock())
    adapter.inspect = Mock(return_value=({}, "changed", False))
    assert (
        adapter.reconcile("original", dict(ActionKind="verify_rollover", EvidenceHash="old"))
        == "not_applied"
    )
    base.reconcile.assert_not_called()


def test_replacement_verification_rejects_change_between_review_and_snapshot(monkeypatch):
    from services.rollover_replacement_adapter import RolloverReplacementAdapter
    from services.rollover_replacement_dal import RolloverReplacementDAL

    operation = dict(OperationID=str(uuid4()), State="running", Version=7)
    base = Mock()
    base.discovery.rollover.side_effect = [
        dict(operation=dict(State="uncertain")),
        dict(operation=dict(operation, Version=8)),
    ]
    adapter = RolloverReplacementAdapter(base, runtime=Mock())
    adapter.inspect = Mock(
        return_value=(
            dict(
                actions={"verify_replacement_rollover": {}},
                delivery=dict(operation_token=digest(operation).hex()),
            ),
            "reviewed",
            False,
        )
    )
    monkeypatch.setattr(RolloverReplacementDAL, "read", lambda *_: operation)
    with pytest.raises(SourceConflict, match="changed after confirmation"):
        adapter.execute("original", "verify_replacement_rollover", "reviewed", "admin", "confirmed")
    base.execute.assert_not_called()
