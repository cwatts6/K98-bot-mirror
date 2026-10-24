"""No replay or release, including lost acknowledgements across each boundary."""

from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from test_legacy_export_closeout import recovery as legacy_recovery  # noqa: F401

from kvk.dal.new_source_import_dal import SourceConflict
from services.config_read_containment import stream_wire
from services.export_execution_protocol import encode
from services.stranded_export_recovery import StrandedExportRecovery


class Journal:
    def __init__(self):
        self.values = {}

    def read(self, name):
        return deepcopy(self.values.get(name))

    def write(self, name, value):
        assert name not in self.values or self.values[name] == value
        self.values[name] = deepcopy(value)


@pytest.fixture
def stranded(legacy_recovery):  # noqa: F811
    closeout, state, stream, request, events, docs = legacy_recovery
    job = state["job"]
    job.update(State="running", Version=6)
    state.update(attempts=[], foreign_streams=[])
    for resource in state["resources"]:
        resource["BlockedReason"] = None
    stream.update(
        State="open",
        Version=3,
        ActiveAccountKey=job["AccountKey"],
        CreatedUTC="2026-10-01T00:00:00",
        ClosedUTC=None,
        ClosureHash=None,
        ClosureReference=None,
        EventDigest=None,
    )
    birth = dict(
        child_id=stream["ChildIdentity"],
        pid=1234,
        job_name="Global\\K98ExportChild-" + "a" * 64,
        machine=dict(machine_guid=str(uuid4()), hostname="fixture"),
        authority_sid="S-1-5-21-123",
        limit_flags=0x2000,
        assigned=True,
    )
    birth_raw = encode(
        dict(
            kind="provider_child_birth/1",
            stream_id=stream["StreamID"],
            session_id=stream["SessionID"],
            account=job["AccountKey"],
            host=birth,
        )
    )
    reference = str(uuid4())
    docs[reference] = birth_raw
    scope = json.loads(stream["ScopeJson"])
    scope["host_birth"] = dict(reference=reference, sha256=hashlib.sha256(birth_raw).hexdigest())
    stream["ScopeJson"] = json.dumps(scope)

    def snapshot(_):
        state["streams"] = [stream_wire(stream)]
        return deepcopy(state)

    closeout.dal.snapshot = snapshot
    execution = closeout.execution
    execution.read_session = Mock(
        return_value=dict(
            SessionID=stream["SessionID"],
            State="open",
            AuthorityPrincipal=state["principal"],
            ManifestHash=b"m" * 32,
        )
    )

    def transition(kind, **args):
        assert kind == "stream" and args["ExpectedVersion"] == stream["Version"]
        assert args["StreamID"] == stream["StreamID"] and args["SessionID"] == stream["SessionID"]
        if args["Action"] == "freeze":
            assert stream["State"] == "open"
            stream.update(State="frozen", Version=stream["Version"] + 1)
        else:
            assert args["Action"] == "close" and stream["State"] == "frozen"
            stream.update(
                State="closed",
                Version=stream["Version"] + 1,
                ActiveAccountKey=None,
                ClosedUTC="2026-10-01T01:00:00",
                **{
                    k: args[k]
                    for k in ("ClosureHash", "ClosureReference", "EventDigest", "LastSequence")
                },
            )
        return deepcopy(stream)

    execution.transition = Mock(side_effect=transition)

    def fail(claim, *, retain_claims):
        assert retain_claims and stream["State"] == "closed" and job["State"] == "running"
        assert claim.job_id == job["JobID"] and claim.version == job["Version"]
        job.update(State="uncertain", Version=job["Version"] + 1, UpdatedUTC="2026-10-01T01:00:01")
        for resource in state["resources"]:
            resource.update(
                Version=resource["Version"] + 1, BlockedReason="Outcome requires reconciliation"
            )

    coordinator = SimpleNamespace(fail=Mock(side_effect=fail))
    child = Mock()
    child.__enter__ = Mock(return_value=child)
    child.__exit__ = Mock(return_value=False)
    child.terminate_and_observe.return_value = dict(
        child_id=birth["child_id"], pid=birth["pid"], job_empty=True, process_signaled=True
    )
    host = SimpleNamespace(retain=Mock(return_value=child), verify_terminated=Mock())
    expected = dict(
        job_id=job["JobID"],
        owner_id=job["OwnerID"],
        fence=job["Fence"],
        job_version=job["Version"],
        stream_id=stream["StreamID"],
        session_id=stream["SessionID"],
        child_id=stream["ChildIdentity"],
        stream_version=stream["Version"],
        last_sequence=1,
        configuration_sha256=stream["RegistrationHash"].hex(),
        destination_count=1,
        manifest_sha256=(b"m" * 32).hex(),
    )
    service = StrandedExportRecovery(
        closeout=closeout,
        execution=execution,
        coordinator=coordinator,
        store=closeout.store,
        host=host,
        journal=Journal(),
        check_boundary=Mock(),
        expected=expected,
    )
    return SimpleNamespace(
        service=service,
        state=state,
        stream=stream,
        child=child,
        execution=execution,
        coordinator=coordinator,
        events=events,
        docs=docs,
    )


def test_inspection_never_changes_execution_or_claims(stranded):
    s = stranded
    review = s.service.inspect()
    assert review["original"]["job"]["State"] == "running"
    s.execution.transition.assert_not_called()
    s.child.terminate_and_observe.assert_not_called()
    s.coordinator.fail.assert_not_called()


def test_exact_closure_then_failure_retains_all_reservations(stranded):
    s = stranded
    before = deepcopy(s.state["job"])
    review = s.service.inspect()
    result = s.service.apply(review, s.service.token(review))
    assert result["stage"] == "CLOSURE_VERIFIED_CLOSEOUT_REQUIRED"
    assert not result["reservations_released"] and result["provider_requests"] == 0
    assert s.state["job"]["InputHash"] == before["InputHash"]
    assert s.state["job"]["ProvenanceJson"] == before["ProvenanceJson"]
    assert all(r["ActiveJobID"] == before["JobID"] for r in s.state["resources"])
    s.service.closeout.dal.settle.assert_not_called()
    s.service.apply(review, s.service.token(review))
    assert s.child.terminate_and_observe.call_count == 1
    assert s.coordinator.fail.call_count == 1


@pytest.mark.parametrize("boundary", ["freeze", "close", "fail"])
def test_lost_acknowledgement_resumes_from_readback_without_repeating(boundary, stranded):
    s = stranded
    review = s.service.inspect()
    operation = s.coordinator.fail if boundary == "fail" else s.execution.transition
    original = operation.side_effect
    tripped = False

    def lost(*args, **kwargs):
        nonlocal tripped
        result = original(*args, **kwargs)
        if not tripped and (boundary == "fail" or kwargs["Action"] == boundary):
            tripped = True
            raise RuntimeError("lost acknowledgement")
        return result

    operation.side_effect = lost
    with pytest.raises(RuntimeError, match="lost acknowledgement"):
        s.service.apply(review, s.service.token(review))
    result = s.service.apply(review, s.service.token(review))
    assert result["stage"] == "CLOSURE_VERIFIED_CLOSEOUT_REQUIRED"
    assert s.child.terminate_and_observe.call_count == 1


@pytest.mark.parametrize(
    "change", ["owner", "membership", "session", "foreign", "attempt", "birth", "token"]
)
def test_changed_identity_or_scope_never_freezes_or_kills(change, stranded):
    s = stranded
    review = s.service.inspect()
    token = s.service.token(review)
    if change == "owner":
        s.state["job"]["OwnerID"] = str(uuid4())
    elif change == "membership":
        s.state["membership"].append("destination:unrelated")
    elif change == "session":
        s.execution.read_session.return_value["ManifestHash"] = b"x" * 32
    elif change == "foreign":
        s.state["foreign_streams"] = [dict(State="open")]
    elif change == "attempt":
        s.state["attempts"] = [dict(AttemptID=str(uuid4()))]
    elif change == "birth":
        scope = json.loads(s.stream["ScopeJson"])
        s.docs[scope["host_birth"]["reference"]] = b"tampered"
    else:
        token = "0" * 64
    with pytest.raises((SourceConflict, ValueError)):
        s.service.apply(review, token)
    s.execution.transition.assert_not_called()
    s.child.terminate_and_observe.assert_not_called()


def test_unverified_provider_history_never_reclassifies_or_releases_job(stranded):
    s = stranded
    review = s.service.inspect()
    s.events[-1]["State"] = "unknown"
    with pytest.raises(SourceConflict, match="Unknown request outcome"):
        s.service.apply(review, s.service.token(review))
    assert s.state["job"]["State"] == "running"
    s.coordinator.fail.assert_not_called()
    s.service.closeout.dal.settle.assert_not_called()


def test_changed_sequence_after_freeze_is_not_hidden(stranded):
    s = stranded
    review = s.service.inspect()
    s.execution.stream_digest.return_value = (2, b"d" * 32)
    with pytest.raises(SourceConflict, match="Request membership changed"):
        s.service.apply(review, s.service.token(review))
    assert s.stream["State"] == "frozen"
    s.coordinator.fail.assert_not_called()


def test_uppercase_odbc_owner_ids_keep_exact_ownership(stranded):
    s = stranded
    s.state["job"]["OwnerID"] = s.state["job"]["OwnerID"].upper()
    s.stream["OwnerID"] = s.stream["OwnerID"].upper()
    for resource in s.state["resources"]:
        resource["OwnerID"] = resource["OwnerID"].upper()
    review = s.service.inspect()
    assert s.service.apply(review, s.service.token(review))["outcome"] == "unconfirmed"


def test_private_store_failure_keeps_termination_receipt_and_never_kills_twice(stranded):
    s = stranded
    review = s.service.inspect()
    put = s.service.store.put
    s.service.store.put = Mock(side_effect=OSError("fixture write failure"))
    with pytest.raises(OSError):
        s.service.apply(review, s.service.token(review))
    assert s.service.journal.read("termination") is not None
    assert s.stream["State"] == "frozen"
    s.service.store.put = put
    s.service.apply(review, s.service.token(review))
    assert s.child.terminate_and_observe.call_count == 1
    s.service.host.verify_terminated.assert_called_once()


def test_journal_is_immutable_and_partial_json_is_not_treated_as_absence(tmp_path):
    from scripts.recover_stranded_export import RecoveryJournal

    journal = RecoveryJournal(tmp_path, Mock())
    journal.write("intent", {"original": "retained"})
    journal.write("intent", {"original": "retained"})
    with pytest.raises(ValueError, match="conflict"):
        journal.write("intent", {"original": "changed"})
    with pytest.raises(ValueError, match="Fixed"):
        journal.read("../another-record")
    (tmp_path / "closure.json").write_text('{"partial":')
    with pytest.raises(json.JSONDecodeError):
        journal.read("closure")
