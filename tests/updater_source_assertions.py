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


def before_portable_fingerprint_hash(root, path):
    """Authenticate the reviewed runtime successor for historical tests only.

    This does not amend installed updater authority or reinterpret a SQL receipt.
    Unknown successor edits still fail rather than learning hashes from checkout.
    """
    actual = prepare_k98_update.sha256((root / path).read_bytes().replace(b"\r\n", b"\n"))
    fixture = root / "tests/fixtures/portable_fingerprint_source_pairs.json"
    if not fixture.exists():
        return actual  # Standalone historical fixtures authenticate their own bytes.
    raw = fixture.read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "0118393100c6408b5258099fbbcb300f55837d891e1195933f5fec566ec5ad86"
    )
    member = next((m for m in json.loads(raw) if m["path"] == path), None)
    if member:
        assert actual == member["after"], path
        return member["before"]
    return actual


def before_finalisation_hash(root, path):
    """Exact local successor evidence only; does not change updater admission."""
    actual = before_portable_fingerprint_hash(root, path)
    fixture = root / "tests/fixtures/p1_mge_finalisation_source_pairs.json"
    if not fixture.exists():
        return actual  # Historical standalone fixtures still authenticate themselves.
    raw = fixture.read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "26913524929d935e19dbb47922cbfbfa2a763065985383d0be045048efd76675"
    )
    member = next((m for m in json.loads(raw) if m["path"] == path), None)
    if member:
        assert actual == member["after"], path
        return member["before"]
    return actual


def before_a1b_hash(root, path):
    """Authenticate the exact A1b successor before walking historical source pins."""
    actual = before_finalisation_hash(root, path)
    fixture = root / "tests/fixtures/p1_a1b_source_pairs.json"
    if not fixture.exists():
        return actual
    raw = fixture.read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "f3dddb07c5f4197af706517a269df5ba9ec1f0b9b75b2b756e15ca97cd6eb5f5"
    )
    member = next((m for m in json.loads(raw) if m["path"] == path), None)
    if member:
        assert actual == member["after"], path
        return member["before"]
    return actual


def before_a1a_hash(root, path):
    """Local source bridge only; production admission remains unchanged."""
    actual = before_a1b_hash(root, path)
    fixture = root / "tests/fixtures/p1_a1a_source_pairs.json"
    if not fixture.exists():
        return actual  # Unchanged historical fixtures still authenticate themselves.
    raw = fixture.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == (
        "305cfee33d63c60bf4a014fb74533dfbfa2ab4d8f94b718a91d762f41a649ae5"
    )
    member = next((m for m in json.loads(raw) if m["path"] == path), None)
    if member:
        assert actual == member["after"], path
        return member["before"]
    return actual


def before_mge_lifecycle_hash(root, path):
    """Exact test-only successor bridge; grants no installation capability."""
    actual = before_a1a_hash(root, path)
    raw = (root / "tests/fixtures/p1_mge_lifecycle_source_pairs.json").read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "e191e881c76d1351c93c07d817be827f16e0326cc10a5909b0a84f5eb03635ca"
    )
    member = next((m for m in json.loads(raw) if m["path"] == path), None)
    if member:
        assert actual == member["after"], path
        return member["before"]
    return actual


def before_checkpoint_observation_hash(root, path):
    actual = before_mge_lifecycle_hash(root, path)
    raw = (root / "tests/fixtures/checkpoint_observation_source_pairs.json").read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "c2c517c94537f0398032ff76fa1f748201ff14eabe44939c4333811798bf50f8"
    )
    member = next((m for m in json.loads(raw) if m["path"] == path), None)
    if member:
        assert actual == member["after"], path
        return member["before"]
    return actual


def before_health_activity_hash(root, path):
    actual = before_checkpoint_observation_hash(root, path)
    raw = (root / "tests/fixtures/health_activity_source_pairs.json").read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "106af81ec95787d6286314722f6001edfe3c424de7c29c1391e21d537df4fab6"
    )
    member = next((m for m in json.loads(raw) if m["path"] == path), None)
    if member:
        assert actual == member["after"], path
        return member["before"]
    return actual


def before_coordination_lifecycle_hash(root, path):
    """Authenticate the exact successor; this fixture grants no install authority."""
    actual = before_health_activity_hash(root, path)
    raw = (root / "tests/fixtures/coordination_lifecycle_source_pairs.json").read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "5994d9946eb523c4c50977c9b6ca805ab094e13336180f126300fe5992fd395f"
    )
    member = next((m for m in json.loads(raw) if m["path"] == path), None)
    if member:
        assert actual == member["after"], path
        return member["before"]
    return actual


def before_procconfig_admission_hash(root, path):
    """Test-only proof of this successor; never deployment authority."""
    actual = before_coordination_lifecycle_hash(root, path)
    raw = (root / "tests/fixtures/procconfig_admission_source_pairs.json").read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "9a22fddadd7829b98f07f0628a4bdc1f78a8f75a0bc7e00c548a05df5ba3c4c4"
    )
    member = next((m for m in json.loads(raw) if m["path"] == path), None)
    if member:
        assert actual == member["after"], path
        return member["before"]
    return actual


def before_monitoring_hash(root, path):
    """Exact test-only successor proof; never an installed updater capability."""
    actual = before_procconfig_admission_hash(root, path)
    raw = (root / "tests/fixtures/p1_monitoring_source_pairs.json").read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "9ba7e4bba75c055e5eb9928a2733727a8ff5199642ed7c1fc02411b7e0efcf04"
    )
    member = next((m for m in json.loads(raw) if m["path"] == path), None)
    if member:
        assert actual == member["after"], path
        return member["before"]
    return actual


def before_event_delivery_hash(root, path):
    actual = before_monitoring_hash(root, path)
    fixture = root / "tests/fixtures/p1_event_delivery_source_pairs.json"
    if not fixture.exists():
        return actual
    raw = fixture.read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "58e35e7e683ed612cbdf4391a518e224e39d8a19d1b933b78e89d58f9d5079a3"
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
