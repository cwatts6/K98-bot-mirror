"""Keep historical transition assertions bound through reviewed successors."""

import hashlib
import json

from scripts import p0a_release, prepare_k98_update

# Test-only bridge through this local WS3 source change to the unchanged
# historical release assertions. These pairs do not authorize installation or
# amend the production updater registry. Require exact successor bytes first.
_EVENT_CACHE_READINESS_PAIRS = {
    "bot_instance.py": (
        "730c2c21743d67750576b366f9c49d7ca1e6b62104fd62c1f9767bec016ac14d",
        "ee3aea3c49f14808cc95b43aa1f4aaae716634a9ea3ea39713b2ab5c952b4e03",
    ),
    "services/recovery_health.py": (
        "c275cec2f40189f8a306fc6e544f1d9bcfbe1de2cedb40528e0e8d35e31c7b19",
        "7d98039061a89beed90eb0a3d558bc3f222c34385fb3818928e24215e55e88b4",
    ),
}


def before_event_delivery_hash(root, path):
    actual = prepare_k98_update.sha256((root / path).read_bytes().replace(b"\r\n", b"\n"))
    fixture = root / "tests/fixtures/p1_event_delivery_source_pairs.json"
    if not fixture.exists():
        return actual
    raw = fixture.read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "da85162a33b3c20d0149d9b6edb10683b7b7555ebfa91c9b761690ccfa046376"
    )
    member = next((m for m in json.loads(raw) if m["path"] == path), None)
    if member:
        assert actual == member["after"], path
        return member["before"]
    return actual


def before_startup_foundations_hash(root, path):
    # Test-only exact successor bridge, not an installed updater capability.
    # Authenticate both the immutable mapping and current source before walking
    # the unchanged historical transition chain. Unknown edits still fail.
    raw = (root / "tests/fixtures/p1_startup_source_pairs.json").read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "998f09dcecdf13b762ff1f21b90f38257c4b27f2590d186ed0a0cc70d1be1457"
    )
    actual = before_event_delivery_hash(root, path)
    member = next((m for m in json.loads(raw) if m["path"] == path), None)
    if member is not None:
        assert actual == member["after"], path
        return member["before"]
    return actual


def before_contention_hash(root, path):
    actual = before_startup_foundations_hash(root, path)
    if path in _EVENT_CACHE_READINESS_PAIRS:
        before, after = _EVENT_CACHE_READINESS_PAIRS[path]
        assert actual == after, path
        actual = before
    contention = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "export_contention_handoff_v1"
    )
    member = next((m for m in contention["members"] if m["path"] == path), None)
    if member is not None and member["before_sha256"] is not None:
        assert actual == member["after_sha256"], path
        actual = member["before_sha256"]
    return actual


def historical_runtime_hash(root, path):
    actual = before_contention_hash(root, path)
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
