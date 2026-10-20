import hashlib
import json
from unittest.mock import Mock

import pytest

from core.export_deployment_handoff import (
    RecordedTermination,
    acknowledge_deployment,
    previous_termination,
    record_termination,
    requested_release,
    termination_path,
)
from core.export_startup_windows import TerminatedPair


def request_fixture(tmp_path):
    previous = dict(sequence=2, publication={"plan_sha256": "b" * 64})
    value = dict(
        version=1,
        release_id="cd981d3e-457e-47a7-bdba-5a1c2fbcfe6a",
        policy_sha256="a" * 64,
        **previous,
    )
    path = tmp_path / "deployment-request.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path, value, previous


def test_no_deployment_keeps_normal_restart(tmp_path):
    inspect = Mock()
    assert requested_release(tmp_path, "a" * 64, {}, inspect) is None
    inspect.assert_not_called()


@pytest.mark.parametrize("damage", [None, "sequence", "policy_sha256", "publication", "command"])
def test_deployment_is_bound_to_exact_incarnation(tmp_path, damage):
    path, value, previous = request_fixture(tmp_path)
    if damage:
        value[damage] = "untrusted"
        path.write_text(json.dumps(value), encoding="utf-8")
    inspect = Mock(side_effect=lambda p, **kw: p)
    if damage:
        with pytest.raises(ValueError):
            requested_release(tmp_path, "a" * 64, previous, inspect)
    else:
        result = requested_release(tmp_path, "a" * 64, previous, inspect)
        assert result["request"] == value
        assert result["request_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    inspect.assert_called_once_with(path, private=True)


def test_unprotected_request_is_never_used(tmp_path):
    _, _, previous = request_fixture(tmp_path)
    with pytest.raises(PermissionError):
        requested_release(tmp_path, "a" * 64, previous, Mock(side_effect=PermissionError))


@pytest.mark.parametrize("terminated", [True, False])
def test_receipt_requires_native_termination(tmp_path, monkeypatch, terminated):
    _, _, previous = request_fixture(tmp_path)
    request = requested_release(tmp_path, "a" * 64, previous, lambda p, **kw: p)
    previous["bindings"] = {}
    native = Mock(side_effect=None if terminated else ValueError("still alive"))
    monkeypatch.setattr(TerminatedPair, "verify", native)
    write = Mock()
    args = dict(
        previous=previous,
        termination=TerminatedPair({}),
        state_directory=tmp_path,
        write_file=write,
    )
    if terminated:
        receipt = acknowledge_deployment(request, **args)
        assert receipt["stage"] == "deployment_drained"
        assert json.loads(write.call_args.args[1]) == receipt
    else:
        with pytest.raises(ValueError, match="still alive"):
            acknowledge_deployment(request, **args)
        write.assert_not_called()


def test_clean_stop_receipt_allows_same_boot_restart_without_reinventing_proof(
    tmp_path, monkeypatch
):
    previous = dict(sequence=2, bindings={"fixture": "identity"}, publication={"fixture": "commit"})
    native = Mock()
    monkeypatch.setattr(TerminatedPair, "verify", native)
    record_termination(
        tmp_path,
        previous,
        TerminatedPair(previous["bindings"], {"fixture": "native-handle"}),
        lambda path, raw: path.write_bytes(raw),
    )
    native.assert_called_once()
    inspect = Mock(side_effect=lambda p, **kw: p)
    proof = previous_termination(tmp_path, previous, inspect)
    assert isinstance(proof, RecordedTermination)
    proof.verify()
    # Durable proof is immutable and revalidated, not an inferred missing PID.
    termination_path(tmp_path, previous).write_text("{}")
    with pytest.raises(ValueError, match="differs"):
        proof.verify()


def test_missing_stop_receipt_still_requires_native_or_reboot_proof(tmp_path):
    previous = dict(sequence=2, bindings={})
    assert type(previous_termination(tmp_path, previous, Mock())) is TerminatedPair


def test_unprotected_stop_receipt_cannot_authorize_restart(tmp_path):
    previous = dict(sequence=2, bindings={})
    termination_path(tmp_path, previous).write_text("{}")
    with pytest.raises(PermissionError):
        previous_termination(tmp_path, previous, Mock(side_effect=PermissionError))


def test_stop_receipt_cannot_be_generated_from_missing_handles(tmp_path):
    write = Mock()
    with pytest.raises(ValueError, match="retained native"):
        record_termination(tmp_path, {"sequence": 2}, TerminatedPair({}), write)
    write.assert_not_called()


def test_stop_receipt_rejects_another_pairs_native_proof(tmp_path, monkeypatch):
    native = Mock()
    monkeypatch.setattr(TerminatedPair, "verify", native)
    write = Mock()
    previous = dict(sequence=2, bindings={"pair": "expected"})
    termination = TerminatedPair({"pair": "different"}, {"native": "handles"})
    with pytest.raises(ValueError, match="another process pair"):
        record_termination(tmp_path, previous, termination, write)
    with pytest.raises(ValueError, match="another process pair"):
        acknowledge_deployment(
            {},
            previous=previous,
            termination=termination,
            state_directory=tmp_path,
            write_file=write,
        )
    native.assert_not_called()
    write.assert_not_called()
