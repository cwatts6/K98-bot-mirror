"""Protected deployment handoff after native termination; never executes a payload."""

import hashlib
import json
from pathlib import Path

from core.export_startup_windows import TerminatedPair
from services.export_execution_protocol import encode, uuid_text


class RecordedTermination(TerminatedPair):
    """An administrator-protected receipt of the issuer's retained-handle check."""

    def __init__(self, previous, path, inspect):
        super().__init__(previous["bindings"])
        object.__setattr__(self, "previous", previous)
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "inspect", inspect)

    def verify(self):
        path = self.inspect(self.path, private=True)
        if path.stat().st_size > 65536:
            raise ValueError("Termination receipt exceeds its bound.")
        raw = path.read_bytes()
        expected = dict(version=1, stage="pair_terminated", previous=self.previous)
        if len(raw) > 65536 or raw != encode(expected):
            raise ValueError("Termination receipt differs from the previous incarnation.")


def termination_path(state_directory, previous):
    return Path(state_directory) / ("terminated-" + str(previous["sequence"]).zfill(20) + ".json")


def previous_termination(state_directory, previous, inspect):
    if previous is None:
        return None
    path = termination_path(state_directory, previous)
    if path.exists():
        proof = RecordedTermination(previous, path, inspect)
        proof.verify()
        return proof
    return TerminatedPair(previous["bindings"])


def record_termination(state_directory, previous, termination, write_file):
    """Persist only a direct retained-handle observation, not a copied receipt."""
    if type(termination) is not TerminatedPair or termination.handles is None:
        raise ValueError("Original retained native handles required for termination receipt.")
    if termination.bindings != previous["bindings"]:
        raise ValueError("Termination proof belongs to another process pair.")
    termination.verify()
    write_file(
        termination_path(state_directory, previous),
        encode(dict(version=1, stage="pair_terminated", previous=previous)),
    )


def requested_release(state_directory, policy_hash, previous, inspect):
    """Only an administrator can stage this fixed-path, exact-incarnation request."""
    path = Path(state_directory) / "deployment-request.json"
    if not path.exists():
        return None
    trusted = inspect(path, private=True)
    if trusted.stat().st_size > 4096:
        raise ValueError("Deployment request exceeds its bound.")
    raw = trusted.read_bytes()
    value = json.loads(raw)
    if (
        len(raw) > 4096
        or not isinstance(value, dict)
        or set(value) != {"version", "release_id", "policy_sha256", "sequence", "publication"}
        or type(value["version"]) is not int
        or value["version"] != 1
        or value["policy_sha256"] != policy_hash
        or type(value["sequence"]) is not int
        or value["sequence"] != previous["sequence"]
        or value["publication"] != previous["publication"]
    ):
        raise ValueError("Deployment request differs from the running incarnation.")
    uuid_text(value["release_id"])
    return dict(request=value, request_sha256=hashlib.sha256(raw).hexdigest())


def acknowledge_deployment(request, *, previous, termination, state_directory, write_file):
    """Caller has closed the old SQL session; prove native exit again before receipt."""
    if not isinstance(termination, TerminatedPair):
        raise ValueError("Native process-pair termination proof required.")
    if termination.bindings != previous["bindings"]:
        raise ValueError("Termination proof belongs to another process pair.")
    termination.verify()
    receipt = dict(
        version=1,
        release_id=request["request"]["release_id"],
        request_sha256=request["request_sha256"],
        previous=previous,
        stage="deployment_drained",
    )
    path = Path(state_directory) / ("deployment-drained-" + receipt["release_id"] + ".json")
    write_file(path, encode(receipt))
    return receipt
