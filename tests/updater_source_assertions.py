"""Keep historical transition assertions bound through reviewed successors."""

import hashlib
import json

from scripts import p0a_release, prepare_k98_update


def installed_contract_archive_hash(root):
    """Pin the real packaged verifier in candidate installed-tool fixtures."""
    from scripts.verify_k98_update_pair import build_contract_archive

    return hashlib.sha256(build_contract_archive(root)).hexdigest()


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


def before_d3a_hash(root, path):
    """Authenticate D3a before exposing the unchanged prior release assertion."""
    actual = prepare_k98_update.sha256((root / path).read_bytes().replace(b"\r\n", b"\n"))
    if path not in prepare_k98_update.P02_D3A_FILE_OWNERSHIP_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d3a_file_ownership_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d2l_hash(root, path):
    """Authenticate D2l before exposing the unchanged prior release assertion."""
    actual = before_d3a_hash(root, path)
    if path not in prepare_k98_update.P02_D2L_OPERATION_POLICY_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d2l_operation_policy_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d2k_hash(root, path):
    """Authenticate D2k before exposing the unchanged prior release assertion."""
    actual = before_d2l_hash(root, path)
    if path not in prepare_k98_update.P02_D2K_HOLDER_DIAGNOSTICS_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d2k_holder_diagnostics_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d2j_hash(root, path):
    """Authenticate D2j before exposing the unchanged prior release assertion."""
    actual = before_d2k_hash(root, path)
    if path not in prepare_k98_update.P02_D2J_OBSERVATION_DISPATCH_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d2j_observation_dispatch_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d2i_hash(root, path):
    """Authenticate D2i before exposing the unchanged prior release assertion."""
    actual = before_d2j_hash(root, path)
    if path not in prepare_k98_update.P02_D2I_SQL_LIFECYCLE_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d2i_sql_lifecycle_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d2h_hash(root, path):
    """Authenticate D2h before exposing the unchanged prior release assertion."""
    actual = before_d2i_hash(root, path)
    if path not in prepare_k98_update.P02_D2H_SEASON_OBSERVATION_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d2h_season_observation_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d2g_hash(root, path):
    """Authenticate D2g before exposing the unchanged prior release assertion."""
    actual = before_d2h_hash(root, path)
    if path not in prepare_k98_update.P02_D2G_RECOVERY_POOL_OBSERVATION_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d2g_recovery_pool_observation_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d2f_hash(root, path):
    """Authenticate D2f before exposing the unchanged prior release assertion."""
    actual = before_d2g_hash(root, path)
    if path not in prepare_k98_update.P02_D2F_QUEUE_OBSERVATION_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d2f_queue_observation_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d2e_hash(root, path):
    """Authenticate D2e before exposing the unchanged prior release assertion."""
    actual = before_d2f_hash(root, path)
    if path not in prepare_k98_update.P02_D2E_CONFIG_OBSERVATION_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d2e_config_observation_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d2d_hash(root, path):
    """Authenticate D2d before exposing the unchanged prior release assertion."""
    actual = before_d2e_hash(root, path)
    if path not in prepare_k98_update.P02_D2D_UNOWNED_HOLD_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d2d_unowned_hold_observation_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d2c_hash(root, path):
    """Authenticate D2c before exposing the unchanged prior release assertion."""
    actual = before_d2d_hash(root, path)
    if path not in prepare_k98_update.P02_D2C_SQL_SETUP_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d2c_sql_setup_custody_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d2b_hash(root, path):
    """Authenticate D2b before exposing the unchanged D2a release assertion."""
    actual = before_d2c_hash(root, path)
    if path not in prepare_k98_update.P02_D2B_PROFILE_CUSTODY_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d2b_profile_sql_custody_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d2a_hash(root, path):
    """Authenticate D2a before exposing the unchanged prior release assertion."""
    actual = before_d2b_hash(root, path)
    if path not in prepare_k98_update.P02_D2A_CONNECTION_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d2a_connection_selection_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_phase1_hash(root, path):
    """Authenticate Phase 1, then expose the immutable P02.1 reference image.

    P02.1 was not installed. Phase 1 is a complete 25-member transition from
    the same original predecessor, not an admission of partial new helpers.
    Historical test bridges never change installed updater policy.
    """
    actual = before_d2a_hash(root, path)
    if path not in prepare_k98_update.P02_PHASE1_SQL_EXPORT_PATHS:
        return actual
    entries = prepare_k98_update.reviewed_transitions()
    successor = next(t for t in entries if t["id"] == "p02_phase1_sql_exports_v1")
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    if path in prepare_k98_update.P021_OBSERVER_SNAPSHOT_PATHS:
        reference = next(t for t in entries if t["id"] == "p021_observer_snapshots_v1")
        return next(m["after_sha256"] for m in reference["members"] if m["path"] == path)
    return member["before_sha256"]


def before_p021_hash(root, path):
    """Authenticate this complete successor before checking immutable history."""
    actual = before_phase1_hash(root, path)
    if path not in prepare_k98_update.P021_OBSERVER_SNAPSHOT_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p021_observer_snapshots_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_p016_render_hash(root, path):
    actual = before_p021_hash(root, path)
    if path not in prepare_k98_update.P016_PERSONAL_STATS_PATHS:
        return actual
    render_successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p016_personal_stats_render_submission_v1"
    )
    render_member = next(m for m in render_successor["members"] if m["path"] == path)
    assert actual == render_member["after_sha256"], path
    return render_member["before_sha256"]


def before_p016_hash(root, path):
    actual = before_p016_render_hash(root, path)
    if path not in prepare_k98_update.P016_PERSONAL_STATS_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p016_personal_stats_ownership_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_p015_hash(root, path):
    actual = before_p016_hash(root, path)
    if path not in prepare_k98_update.P015_CALENDAR_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p015_calendar_ownership_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_p014_hash(root, path):
    actual = before_p015_hash(root, path)
    if path not in prepare_k98_update.P014_UPLOAD_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p014_upload_outcomes_optional_io_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_p013_hash(root, path):
    actual = before_p014_hash(root, path)
    if path in prepare_k98_update.P013_HEALTH_ARCHIVE_PATHS:
        archive = next(
            t
            for t in prepare_k98_update.reviewed_transitions()
            if t["id"] == "p013_health_archive_v1"
        )
        member = next(m for m in archive["members"] if m["path"] == path)
        assert actual == member["after_sha256"], path
        actual = member["before_sha256"]
    if path not in prepare_k98_update.P013_PASSIVE_HEALTH_PATHS:
        return actual
    successor = next(
        (
            t
            for t in prepare_k98_update.reviewed_transitions()
            if t["id"] == "p013_passive_health_v1"
        ),
        None,
    )
    assert successor is not None, "Required p013_passive_health_v1 transition is missing"
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_p012a_recoverable_hash(root, path):
    actual = before_p013_hash(root, path)
    if path not in prepare_k98_update.P012A_RECOVERABLE_REPORT_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p012a_recoverable_reports_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_p012a_contract_hash(root, path):
    actual = before_p012a_recoverable_hash(root, path)
    if path not in prepare_k98_update.P012A_EVIDENCE_CONTRACT_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p012a_evidence_contract_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_p012a_correction_hash(root, path):
    actual = before_p012a_contract_hash(root, path)
    if path not in prepare_k98_update.P012A_REPORT_CORRECTION_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p012a_report_correction_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_p012a_hash(root, path):
    """Authenticate the evidence-bundle successor before historical assertions."""
    actual = before_p012a_correction_hash(root, path)
    if path not in prepare_k98_update.P012A_EVIDENCE_BUNDLE_PATHS:
        return actual
    successor = next(
        (
            t
            for t in prepare_k98_update.reviewed_transitions()
            if t["id"] == "p012a_evidence_bundle_v1"
        ),
        None,
    )
    assert successor is not None, "Required p012a_evidence_bundle_v1 transition is missing"
    member = next((m for m in successor["members"] if m["path"] == path), None)
    if member is not None:
        assert actual == member["after_sha256"], path
        return member["before_sha256"]
    return actual


def before_p011_hash(root, path):
    """Authenticate P01.1 bytes before walking historical source contracts."""
    actual = before_p012a_hash(root, path)
    successor = next(
        (
            t
            for t in prepare_k98_update.reviewed_transitions()
            if t["id"] == "p011_startup_outcomes_v1"
        ),
        None,
    )
    if successor is not None:
        member = next((m for m in successor["members"] if m["path"] == path), None)
        if member is not None:
            assert actual == member["after_sha256"], path
            return member["before_sha256"]
    return actual


def before_startup_evidence_hash(root, path):
    """Authenticate the custody fix before checking its historical predecessor."""
    actual = before_p011_hash(root, path)
    successor = next(
        (
            t
            for t in prepare_k98_update.reviewed_transitions()
            if t["id"] == "startup_evidence_custody_v1"
        ),
        None,
    )
    assert successor is not None, "Required startup_evidence_custody_v1 transition is missing"
    member = next((m for m in successor["members"] if m["path"] == path), None)
    if member is not None:
        assert actual == member["after_sha256"], path
        return member["before_sha256"]
    return actual


def before_settlement_hash(root, path):
    """Authenticate this exact successor before retaining older release assertions."""
    actual = before_startup_evidence_hash(root, path)
    # Historical assertions still require their original bytes after the exact
    # complete request-settlement successor is authenticated.
    successor = next(
        (
            t
            for t in prepare_k98_update.reviewed_transitions()
            if t["id"] == "request_settlement_from_p03a1_v1"
        ),
        None,
    )
    if successor is not None:
        member = next((m for m in successor["members"] if m["path"] == path), None)
        if member is not None:
            assert actual == member["after_sha256"], path
            actual = member["before_sha256"]
    return actual


def before_scoped_index_hash(root, path):
    """Authenticate the exact query successor for tests, never updater admission."""
    actual = before_settlement_hash(root, path)
    fixture = root / "tests/fixtures/scoped_index_metadata_source_pairs.json"
    if not fixture.exists():
        return actual
    raw = fixture.read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "73185ef7d122da6455619a05fdec316c831e59d741dc3404140c83ded91d56fa"
    )
    member = next((m for m in json.loads(raw) if m["path"] == path), None)
    if member:
        assert actual == member["after"], path
        return member["before"]
    return actual


def before_contract_resource_hash(root, path):
    """Test-only exact resource-loader successor; grants no updater admission."""
    actual = before_scoped_index_hash(root, path)
    fixture = root / "tests/fixtures/updater_contract_resource_pairs.json"
    if not fixture.exists():
        return actual
    raw = fixture.read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "e77cc8bfaad532bb5fd9e38e29584ab8c7ea94131d880c7f0b8cdd75ffd92984"
    )
    member = next((m for m in json.loads(raw) if m["path"] == path), None)
    if member:
        assert actual == member["after"], path
        return member["before"]
    return actual


def before_portable_fingerprint_hash(root, path):
    """Authenticate the reviewed runtime successor for historical tests only.

    This does not amend installed updater authority or reinterpret a SQL receipt.
    Unknown successor edits still fail rather than learning hashes from checkout.
    """
    actual = before_contract_resource_hash(root, path)
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


def installed_tool_fixture(directory):
    """Stage the real installer payload for package-generation tests."""
    import base64
    from pathlib import Path
    import re

    from scripts.package_k98_update_tool import package

    result = package(directory / "installer")
    script = Path(result["installer"]).read_text()
    encoded = re.search(r"\$encoded='([^']+)'", script)[1]
    payload = json.loads(base64.b64decode(encoded))
    tools = directory / "installed"
    tools.mkdir()
    for name, content in payload.items():
        (tools / name).write_bytes(base64.b64decode(content))
    manifest = json.loads((tools / "update-tool.json").read_bytes())
    return tools, manifest["files"]["contract_verifier.zip"]
