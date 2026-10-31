"""Legacy missing-birth recovery with real Windows writer/job handles."""

from copy import deepcopy
import json
import sys
from unittest.mock import Mock

import pytest
from test_stranded_export_custody import custody  # noqa: F401
from test_stranded_export_recovery import legacy_recovery, stranded  # noqa: F401

from core import stranded_export_custody as native
from core.stranded_export_host import RecoveryHost
from kvk.dal.new_source_import_dal import SourceConflict, digest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Native live recovery")


@pytest.fixture
def live(stranded, custody):  # noqa: F811
    args, job, process, _ = custody
    s = stranded
    scope = json.loads(s.stream["ScopeJson"])
    scope.pop("host_birth")
    s.stream["ScopeJson"] = json.dumps(scope)
    s.stream["ChildIdentity"] = args["child_id"]
    s.service.expected.update(child_id=args["child_id"], live_custody="authority_handles_v1")
    s.service.host = RecoveryHost(
        args["binding"],
        custody=native,
        child_script=args["child_script"],
        manifest_path=str(args["manifest_path"]),
    )
    return s, args, job, process


def test_missing_birth_exact_native_closure_preserves_original_scope_and_claims(live):
    import win32event

    s, _, _, process = live
    original_scope = s.stream["ScopeJson"]
    review = s.service.inspect()
    assert review["custody"]["kind"] == "live_writer_custody/1"
    assert "birth" not in review and "birth_sha256" not in review
    assert review["custody_sha256"] == native.custody_hash(review["custody"])
    assert s.service.journal.values == {}
    assert win32event.WaitForSingleObject(process, 0) == 258
    result = s.service.apply(review, s.service.token(review))
    assert result["stage"] == "CLOSURE_VERIFIED_CLOSEOUT_REQUIRED"
    assert result["outcome"] == "unconfirmed" and not result["reservations_released"]
    assert win32event.WaitForSingleObject(process, 0) == 0
    assert s.stream["ScopeJson"] == original_scope
    assert s.state["job"]["State"] == "uncertain"
    assert s.state["attempts"][0]["Phase"] == "uncertain"
    assert all(p["QuarantineState"] == "quarantined" for p in s.state["attempt_parts"])
    assert all(r["ActiveJobID"] == s.state["job"]["JobID"] for r in s.state["resources"])
    s.service.host.retain_live = Mock(side_effect=AssertionError("Do not reopen completed writer"))
    assert s.service.apply(review, s.service.token(review)) == result


def test_missing_birth_requires_explicit_reviewed_packet_mode(live):
    s, _, _, _ = live
    del s.service.expected["live_custody"]
    with pytest.raises(ValueError, match="no bound restart birth"):
        s.service.inspect()
    s.execution.transition.assert_not_called()


def test_changed_native_identity_cannot_rebind_review(live):
    import win32event

    s, _, _, process = live
    review = s.service.inspect()
    review["custody"]["process"]["created_filetime"] += 1
    review["custody_sha256"] = digest(review["custody"]).hex()
    with pytest.raises(SourceConflict, match="Inspection is stale"):
        s.service.apply(review, s.service.token(review))
    assert s.service.journal.values == {}
    s.execution.transition.assert_not_called()
    assert win32event.WaitForSingleObject(process, 0) == 258


@pytest.mark.parametrize("boundary", ["freeze", "close", "fail"])
def test_live_recovery_lost_sql_ack_resumes_only_known_state(live, boundary):
    s, _, _, _ = live
    review = s.service.inspect()
    operation = s.coordinator.fail_reviewed if boundary == "fail" else s.execution.transition
    original = operation.side_effect
    tripped = False

    def lose(*args, **kwargs):
        nonlocal tripped
        result = original(*args, **kwargs)
        if not tripped and (boundary == "fail" or kwargs["Action"] == boundary):
            tripped = True
            raise RuntimeError("lost acknowledgement")
        return result

    operation.side_effect = lose
    with pytest.raises(RuntimeError, match="lost acknowledgement"):
        s.service.apply(review, s.service.token(review))
    assert (
        s.service.apply(review, s.service.token(review))["stage"]
        == "CLOSURE_VERIFIED_CLOSEOUT_REQUIRED"
    )
    assert s.stream["ScopeJson"] == review["original"]["streams"][0]["ScopeJson"]


@pytest.mark.parametrize("saved", [False, True])
def test_interruption_at_termination_receipt_never_infers_success_from_absence(live, saved):
    import win32event

    s, _, _, process = live
    review = s.service.inspect()
    original_write = s.service.journal.write

    def interrupt(name, value):
        if name == "termination":
            if saved:
                original_write(name, value)
            raise RuntimeError("receipt interrupted")
        original_write(name, value)

    s.service.journal.write = interrupt
    with pytest.raises(RuntimeError, match="receipt interrupted"):
        s.service.apply(review, s.service.token(review))
    assert win32event.WaitForSingleObject(process, 0) == 0
    assert s.stream["State"] == "frozen"
    s.service.journal.write = original_write
    if saved:
        s.service.host.retain_live = Mock(side_effect=AssertionError("No PID rediscovery"))
        assert (
            s.service.apply(review, s.service.token(review))["stage"]
            == "CLOSURE_VERIFIED_CLOSEOUT_REQUIRED"
        )
    else:
        with pytest.raises(native.CustodyUnavailable, match="Exactly one original live writer"):
            s.service.apply(review, s.service.token(review))
        assert s.stream["State"] == "frozen"
        assert s.state["job"]["State"] == "running"
        s.coordinator.fail_reviewed.assert_not_called()
        assert "closure" not in s.service.journal.values


def test_query_only_handle_cannot_terminate(live):
    import win32event

    _, args, _, process = live
    with native.retain_writer(**args) as writer:
        with pytest.raises(native.CustodyUnavailable, match="Query-only"):
            writer.terminate_and_observe()
    assert win32event.WaitForSingleObject(process, 0) == 258


def test_termination_handle_requires_matching_review(live):
    _, args, _, _ = live
    with pytest.raises(native.CustodyUnavailable, match="Reviewed live custody"):
        with native.retain_writer(**args, allow_termination=True):
            pytest.fail("Unreviewed termination handle")
    with native.retain_writer(**args) as writer:
        evidence = deepcopy(writer.evidence)
    evidence["process"]["created_filetime"] += 1
    with pytest.raises(native.CustodyUnavailable, match="exact reviewed writer"):
        with native.retain_writer(**args, expected=evidence, allow_termination=True):
            pytest.fail("Changed writer admitted")


def test_saved_receipt_checks_complete_identity_without_opening_pid(live, monkeypatch):
    import win32api

    s, args, _, _ = live
    review = s.service.inspect()
    s.service.apply(review, s.service.token(review))
    receipt = s.service.journal.read("termination")
    monkeypatch.setattr(
        win32api, "OpenProcess", Mock(side_effect=AssertionError("No PID reopening"))
    )
    native.verify_terminated(review["custody"], receipt, args["binding"])
    forged = deepcopy(receipt)
    forged["observed_process"]["created_filetime"] += 1
    with pytest.raises(native.CustodyUnavailable, match="receipt differs"):
        native.verify_terminated(review["custody"], forged, args["binding"])
