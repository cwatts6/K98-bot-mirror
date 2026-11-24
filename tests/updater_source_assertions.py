"""Keep historical transition assertions bound through reviewed successors."""

import hashlib
import json

from scripts import p0a_release, prepare_k98_update

# Exact test-only bridge from the local observer candidate to its Git predecessor.
# It keeps historical transition tests meaningful while the successor is under
# qualification. These pairs neither register a production update nor issue an
# installed contract; the actual updater rehearsal and Changes reviews remain open.
_OBSERVER_SOURCE_PAIRS = {
    "scripts/verify_k98_running_release.py": (
        "ca138803dc70e88981c3fd4c1716247130dc8b33ae0fb2ada52b019d16f4af16",
        "cd77a733a692ad10d92c093192efba0f73ae602935dba8ca79e61767f31665ba",
    ),
    "kvk/dal/kvk_admin_dal.py": (
        "634cf1210a7e6fa67426104b971a67b0e94f1f294e291d5938dd1607e26829bf",
        "141e3cc6314bf1c182924c82d751352695afe827997f78dbf33ad6aa22ac59b3",
    ),
    "kvk/dal/kvk_all_import_dal.py": (
        "e5b6560c27f9c90b6cebd6f874681e01cbc9520e943d5b0f23285cddba894190",
        "c7ebf640b9be8a27e21f3249799fc15fc3a316d24260548b7a2b58fa9166dcfa",
    ),
    "kvk_all_importer.py": (
        "53a8184faea794101e8084e81358dbe707404a9de91096b06b587f1ffcfb1290",
        "1bd8a3d8fdb6578b3d6ae0b8ebe31087b3ba1ea580e0f98e9479551b6fe515a1",
    ),
    "player_stats_cache.py": (
        "2ac4257bb5695c0d2f6b1ef27f63012c9fb58165e5db752fa8594ecec6811ed3",
        "a9947757f3574d5d9e1b5974aa55158ae777295bde372dcab056c3812aeb3920",
    ),
    "proc_config_import.py": (
        "8661fb89b484a4020bf6511803b7f3b48e3baf196a4cb9612e8a1f290f5301ab",
        "da86ec5838e620f798af618f555118158db633a5a4fce856084ad9aa529c97bd",
    ),
    "scripts/p0a_release.py": (
        "b9087b8f048e387688de53555489cfd5e685975bda535ba2235dd48712f24e6c",
        "1dc4e146069a9f200483ce912284da0754080688fc94e72a1c8cce80650e3437",
    ),
    "scripts/recovery_release_seed.py": (
        "e266ea6c4f7c1f714406d5e7ff18e4342d8e298c0626e084f0c6cdf68963221b",
        "9705d9314a26f43da1034a0cf85a9fd92da2800a456c6827fa076793db9e2329",
    ),
    "scripts/verify_k98_update_pair.py": (
        "0ace1f6d6a412cba6b76ce84588b3aefe85fcda802a558c8d8917265e6ffc079",
        "517fcd956d57a160c5b9f8bd5a4bca688679354cdb092f40e2d38145ea836405",
    ),
    "services/application_maintenance_contract.py": (
        "a2a17c772f6ebbe389f0630b26197e6f6e458372add741f099a4a2e04c7c3728",
        "b71930b8e562d20e83b97b16674a91a8341a9d2a848ed43b22b47fcc5c984241",
    ),
    "services/application_maintenance_dal.py": (
        "74d889a920bb1947df49fb1b6020996c77066340cbe2237938b6b3fce57de911",
        "da5321325b1362d7386eeca3a5c49650588b2c80bd20f16575d9d13b0f138957",
    ),
    "services/export_contract_resources.py": (
        "e545f01fe7fab35bbb80f0a8817935143fa8f1bdff67ca124290a4ac1e21b04c",
        "c572ddc2d462d77348f459684117e43e7961180ba05abee33322a488a3e46309",
    ),
    "services/export_execution_dal.py": (
        "b7fbe072b34d35d3b54c84d949dca0d6755c5d26c36008810296749d3945b7e2",
        "43fc41388cd3c9316eee21ae27f9d7d838f98294e7ad199ccf5dec956d2bdd97",
    ),
    "services/export_runtime_composition.py": (
        "32ea5667129f2a8eafad4e1e944a038295ed4598090fa76517c6e9da2f06e1a9",
        "126ad4b0239c7582f765bd5667a1c32b08e9a35f51122f75a951e459450bff5c",
    ),
    "services/export_sql_direct_permissions.py": (
        "02abee1b52097ee242a3bc7e2cdc973e3e683e990042e3f1051ca309b0162694",
        "1f77156a59fb61b4f310d77e377d2e659120a591e72f5dad3cb65536aa4afc3b",
    ),
    "services/legacy_export_snapshot_dal.py": (
        "917e22fd547cf73d66198c0cc3be3ed8d8ff49c8108ead5673ea88bfd366afe6",
        "e737ff1941c41fe400cc23e753e8340687ff5c621cf25a4fabb276bb37f31b71",
    ),
    "services/legacy_export_snapshot_service.py": (
        "59da485a415c381c3f5b124b2e7d3ffc4b021e73df939349f2c2c10c0456809f",
        "88774eec926e0ae90352398dd9c97448426f6cc0385f5a88119a88a1bde715f7",
    ),
    "services/maintenance_dal.py": (
        "347e799e7424f257b3f19109fb041b9a209a1022bbc2748e199b2f1e5bd11360",
        "eb83661cb7ddc492539bfe1200c4e62ff3db788ee43018cadf4c4fba3f7fff87",
    ),
    "services/runtime_admission_diagnostics.py": (
        "5044ffe1b8f1e31d6e7cf95855aa9bf477c92ca4abf559e125bb01ee5fa3d988",
        "d593c8bb0294d764ec33f38dc525ad66f4f2cd535b41fb9e7790ec60ef585ed3",
    ),
}


# Exact qualified reader and local caller/custody candidate bytes.
# Historical observer pairs and production registry pins below remain unchanged.
# This test-only mapping never admits arbitrary or installed source bytes.
_OBSERVER_QUALIFIED_CANDIDATE_PAIRS = {
    "scripts/p0a_release.py": (
        "1dc4e146069a9f200483ce912284da0754080688fc94e72a1c8cce80650e3437",
        "adde16d2cc6cced1e0a6b9376b99627510e28c8448481ffaeeb5fb8f5c6557da",
    ),
    "services/export_execution_dal.py": (
        "43fc41388cd3c9316eee21ae27f9d7d838f98294e7ad199ccf5dec956d2bdd97",
        "7a7337d7f49f6a859baee6b299e03fcda4b74be446a41c42f420ef135c8e7df5",
    ),
    "services/legacy_export_snapshot_dal.py": (
        "e737ff1941c41fe400cc23e753e8340687ff5c621cf25a4fabb276bb37f31b71",
        "7a146d6719022fb8a015a4b624964e07da62216cfc0b779d432e73f922706ac6",
    ),
    "services/legacy_export_snapshot_service.py": (
        "88774eec926e0ae90352398dd9c97448426f6cc0385f5a88119a88a1bde715f7",
        "c5e096838456853565f9db083203c7b87af064ec17ca26dca4ec68334f6832e1",
    ),
    "stats_module.py": (
        "c1a02bf76b5b34475899febc490fd83aae358d96551ce32645b476d9bfdf6e3d",
        "6d292c2783e297a88cdcbea826a9c734579d2b15f41bca3647a27f0cbbd91bca",
    ),
}


def before_observer_hash(root, path):
    actual = prepare_k98_update.sha256((root / path).read_bytes().replace(b"\r\n", b"\n"))
    if path in _OBSERVER_QUALIFIED_CANDIDATE_PAIRS:
        predecessor, candidate = _OBSERVER_QUALIFIED_CANDIDATE_PAIRS[path]
        assert actual == candidate, path
        actual = predecessor
    if path in _OBSERVER_SOURCE_PAIRS:
        predecessor, candidate = _OBSERVER_SOURCE_PAIRS[path]
        assert actual == candidate, path
        return predecessor
    return actual


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


_D4_CONTRACT_PAIRS = {
    "services/export_runtime_composition.py": (
        "6e8bc38bc4d8f12f1881869f070a4bbbf8d66fd43644ad7cfa18fbce2b044611",
        "9737637b5f29f0e1c8ae89f7ad9f8a002ac06ad1cc78a2b658ea2b9b6d03211a",
    ),
    "services/export_execution_dal.py": (
        "908829d695ffdde9e3aeedbc03b33a2c5cc949f9d939fb7ba3856b0da487d2ef",
        "ca568135303c3828e1988c6a7152d4c743c558f5b7fd9b3c150f566804382b0f",
    ),
    "services/export_contract_resources.py": (
        "c77c4e385e81ed1174e91a26482e8be6713238bfc2c3d248bd38fd9bb393785b",
        "e545f01fe7fab35bbb80f0a8817935143fa8f1bdff67ca124290a4ac1e21b04c",
    ),
    "services/export_sql_direct_permissions.py": (
        "4e9c5ba53cd13d1c8f98f447c042aeb60e9b944d725581d098229f35c173d8e0",
        "02abee1b52097ee242a3bc7e2cdc973e3e683e990042e3f1051ca309b0162694",
    ),
}


def before_catalog_cleanup_hash(root, path):
    """Require exact successor bytes without changing historical release evidence."""
    actual = before_observer_hash(root, path)
    if path in prepare_k98_update.P02_CATALOG_PATHS:
        transition = next(
            t
            for t in prepare_k98_update.reviewed_transitions()
            if t["id"] == prepare_k98_update.P02_CATALOG_TRANSITION
        )
        member = next(m for m in transition["members"] if m["path"] == path)
        assert actual == member["after_sha256"], path
        actual = member["before_sha256"]
    return actual


def before_running_verification_hash(root, path):
    """Authenticate the new reader before exposing retained verification hashes."""
    actual = before_catalog_cleanup_hash(root, path)
    if path in prepare_k98_update.P02_VERIFICATION_PATHS:
        transition = next(
            t
            for t in prepare_k98_update.reviewed_transitions()
            if t["id"] == prepare_k98_update.P02_VERIFICATION_TRANSITION
        )
        member = next(m for m in transition["members"] if m["path"] == path)
        assert actual == member["after_sha256"], path
        actual = member["before_sha256"]
    return actual


def before_admission_hash(root, path):
    """Authenticate current admission bytes before exposing their historical hash."""
    actual = before_running_verification_hash(root, path)
    if path in prepare_k98_update.P02_ADMISSION_PATHS:
        transition = next(
            t
            for t in prepare_k98_update.reviewed_transitions()
            if t["id"] == prepare_k98_update.P02_ADMISSION_TRANSITION
        )
        member = next(m for m in transition["members"] if m["path"] == path)
        assert actual == member["after_sha256"], path
        actual = member["before_sha256"]
    return actual


def before_schema_transaction_fix_hash(root, path):
    """Test-only exact bridge; production successor registration is still required."""
    actual = before_admission_hash(root, path)
    if path == "services/application_maintenance_dal.py":
        assert actual == "1e87fba0ab8b6d35311799dd00b8ce66d9925a950cf3a516c526ee2770c99260", path
        return "d712f0436d3358662c73fadd2d431c5cee44755342bc6b0cf062894d24055264"
    return actual


def before_p02_maintenance_hash(root, path):
    """Authenticate this successor before exposing its exact retained predecessor."""
    actual = before_schema_transaction_fix_hash(root, path)
    # Test-only bridge for the exact SQL identifier correction. Preserve the
    # historic MGE transition; a production successor transition is separately
    # required at release pinning. This does not authorize installation.
    if path == "mge/dal/mge_results_dal.py":
        assert actual == "af56bf6f2a748bf4d1040248c22bc17a7032e51bffb80977356a21574dd6b64e", path
        return "d65edd74bd66e4182e5afc46d77947a9b59566653cc3664ce68ab817b3db35da"
    if path not in prepare_k98_update.P02_MAINTENANCE_COMPATIBILITY_PATHS:
        return actual
    # Authenticate the complete new source family before exposing its retained
    # predecessor hash to historical assertions. Never repin historical evidence.
    family = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_maintenance_compatibility_v1"
    )
    for member in family["members"]:
        if member["path"] == path:
            assert actual == member["after_sha256"], path
            actual = member["before_sha256"]
    return actual


def before_d5_qualification_hash(root, path):
    """Authenticate both qualified fixes before checking unchanged historical pins."""
    actual = before_p02_maintenance_hash(root, path)
    pairs = {
        "services/maintenance_dal.py": (
            "588f00f691779af53075ce990e13949cf48a37daa85d93d724ca72a5b525514b",
            "347e799e7424f257b3f19109fb041b9a209a1022bbc2748e199b2f1e5bd11360",
        ),
        "player_self_service/stats_runtime.py": (
            "5d522cce5df87fdb6bfe7101ee14dae6e9596bff73ecd437dd3298de37258aa8",
            "9e6e9f3be2c9dfe261e0d8c4ef512776ebeeb6e5137cb535f1572ed24bc8c010",
        ),
    }
    if path in pairs:
        before, after = pairs[path]
        assert actual == after, path
        return before
    return actual


def before_d4_contract_hash(root, path):
    actual = before_d5_qualification_hash(root, path)
    if path in _D4_CONTRACT_PAIRS:
        before, after = _D4_CONTRACT_PAIRS[path]
        assert actual == after, path
        return before
    return actual


def before_d4_backup_route_hash(root, path):
    """Test-only source bridge; D4's combined installed release is still required."""
    actual = before_d4_contract_hash(root, path)
    if path == "log_backup.py":
        assert actual == "37ec41d36a1f62f9cad569fbaea58cad524fe8887a4525474c585d4d3b929cec", path
        return "bd6a99fbd5eab29ac31528fe2e137b0e1dc1d411ff336b19ec380efeb04dac50"
    return actual


def before_d3_cleanup_hash(root, path):
    """Authenticate D3 cleanup before exposing the unchanged prior release assertion."""
    actual = before_d4_backup_route_hash(root, path)
    if path not in prepare_k98_update.P02_D3_CLEANUP_CUSTODY_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d3_cleanup_custody_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d3g_hash(root, path):
    """Authenticate D3g before exposing the unchanged prior release assertion."""
    actual = before_d3_cleanup_hash(root, path)
    if path not in prepare_k98_update.P02_D3G_FINAL_REPORT_MAINTENANCE_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d3g_final_report_maintenance_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d3e_hash(root, path):
    """Authenticate D3e before exposing the unchanged prior release assertion."""
    actual = before_d3g_hash(root, path)
    if path not in prepare_k98_update.P02_D3E_PLAYER_REPORT_MAINTENANCE_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d3e_player_report_maintenance_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d3d_hash(root, path):
    """Authenticate D3d before exposing the unchanged prior release assertion."""
    actual = before_d3e_hash(root, path)
    if path not in prepare_k98_update.P02_D3D_CONFIGURATION_MAINTENANCE_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d3d_configuration_maintenance_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d3c_hash(root, path):
    """Authenticate D3c before exposing the unchanged prior release assertion."""
    actual = before_d3d_hash(root, path)
    if path not in prepare_k98_update.P02_D3C_IMPORT_MAINTENANCE_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d3c_import_maintenance_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d3b_hash(root, path):
    """Authenticate D3b before exposing the unchanged prior release assertion."""
    actual = before_d3c_hash(root, path)
    if path not in prepare_k98_update.P02_D3B_MAINTENANCE_PATHS:
        return actual
    successor = next(
        t
        for t in prepare_k98_update.reviewed_transitions()
        if t["id"] == "p02_d3b_maintenance_ownership_v1"
    )
    member = next(m for m in successor["members"] if m["path"] == path)
    assert actual == member["after_sha256"], path
    return member["before_sha256"]


def before_d3a_hash(root, path):
    """Authenticate D3a before exposing the unchanged prior release assertion."""
    actual = before_d3b_hash(root, path)
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
