"""Keep historical transition assertions bound through reviewed successors."""

import hashlib
import json

from scripts import p0a_release, prepare_k98_update


def historical_runtime_hash(root, path):
    actual = prepare_k98_update.sha256((root / path).read_bytes().replace(b"\r\n", b"\n"))
    diagnostics = next(
        transition
        for transition in prepare_k98_update.reviewed_transitions()
        if transition["id"] == "authority_diagnostic_capture_v1"
    )
    member = next((m for m in diagnostics["members"] if m["path"] == path), None)
    if member is not None and member["before_sha256"] is not None:
        assert actual == member["after_sha256"], path
        actual = member["before_sha256"]
    pipeline = next(
        transition
        for transition in prepare_k98_update.reviewed_transitions()
        if transition["id"] == "pipeline_decision_bound_v1"
    )
    member = next((m for m in pipeline["members"] if m["path"] == path), None)
    if member is not None:
        assert actual == member["after_sha256"], path
        assert member["before_sha256"] is not None, path
        actual = member["before_sha256"]
    # Walk the release chain newest first. The receipt correction follows the
    # closeout policy, timeout correction and retained report-boundary policy.
    receipt = next(
        transition
        for transition in prepare_k98_update.reviewed_transitions()
        if transition["id"] == "recovery_receipt_roundtrip_v1"
    )
    member = next((m for m in receipt["members"] if m["path"] == path), None)
    if member is not None:
        assert actual == member["after_sha256"], path
        assert member["before_sha256"] is not None, path
        actual = member["before_sha256"]
    successor = next((r for r in p0a_release.specification()["sources"] if r["path"] == path), None)
    if successor is not None:
        assert actual == successor["after"], path
        assert successor["before"] is not None, path
        actual = successor["before"]
    correction = next(
        transition
        for transition in prepare_k98_update.reviewed_transitions()
        if transition["id"] == "report_timeout_monitor_v1"
    )
    member = next((m for m in correction["members"] if m["path"] == path), None)
    if member is not None:
        assert actual == member["after_sha256"], path
        assert member["before_sha256"] is not None, path
        actual = member["before_sha256"]
    # Retained from eced3d1b's policy, not reconstructed from current source.
    boundary_raw = (root / "tests/fixtures/p0_report_boundary_source_pairs.json").read_bytes()
    assert (
        hashlib.sha256(boundary_raw).hexdigest()
        == "44eaa421c2acf8bc33d5bcb3d6b35898497865f30a73e2d3f6b355a05e32334c"
    )
    boundary = next((r for r in json.loads(boundary_raw) if r["path"] == path), None)
    if boundary is not None:
        assert actual == boundary["after"], path
        assert boundary["before"] is not None, path
        actual = boundary["before"]
    # This immutable fixture is the original P0 completion policy's source
    # pairs. A later corrective policy must not redefine historical bundles.
    raw = (root / "tests/fixtures/p0_completion_source_pairs.json").read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "37b591d1d4b9b43833809ceac337936e3a545e7a9632893f1532afbbf44cd4ec"
    )
    historic = next((r for r in json.loads(raw) if r["path"] == path), None)
    if historic is not None:
        assert actual == historic["after"], path
        assert historic["before"] is not None, path
        return historic["before"]
    return actual
