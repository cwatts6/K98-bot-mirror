"""Verify the release's first protected publication and three live native identities.

Read-only. Invoke with the pinned installed venv Python after the runner seals this artifact.
No application entry point, recovery or provider work is invoked. With --sql-contracts,
read-only SQL observations are checked by the complete existing startup comparators.
"""

import argparse
from copy import deepcopy
from datetime import UTC, datetime, timedelta
import hashlib
import io
import json
from pathlib import Path
import re
import runpy
import sys
import zipfile


class PairPublicationPending(Exception):
    """A future successor artifact is absent under verified administrative custody."""


def successor_path(path, *, validate):
    candidate = Path(path)
    if candidate.is_absolute() and not candidate.exists():
        # Only the exact successor paths derived from the pinned policy qualify.
        # Missing parents, bad custody, malformed paths and existing corrupt files
        # remain hard verification failures, never a successful startup signal.
        validate(candidate.parent, private=True)
        raise PairPublicationPending(
            "Awaiting protected successor publication; no second start requested."
        )
    return validate(candidate, private=True)


def read(path, expected=None, limit=1048576):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    if not raw or len(raw) > limit:
        raise ValueError("File is empty or exceeds verification bound")
    if expected is not None and hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Pinned bytes differ")
    return raw


CONTRACT_ARCHIVE = "contract_verifier.zip"
CONTRACT_ARCHIVE_LIMIT = 2 * 1024 * 1024
# Installed updater authority for the already-applied, reviewed P016 SQL change.
# Derived from the retained approved catalogue plus the exact migration, and
# independently qualified on local SQL Server. Production reads are comparisons,
# never a source of expected metadata. No SQL migration is replayed here.
P016_APPLICATION_REPAIR = {
    "version": 1,
    "id": "p016_application_contract_v1",
    "predecessor": "8f1023e2d89e2d4da06ddde39da5b4b6df32ff03",
    "sql_commit": "dad628c7a353cc6391868d097a6ae5fb7a8d9e84",
    "migration_id": "20261106_001_personal_stats_daily_read_plan",
    "migration_sha256": "bb0e3161d8c3df96452e2631dfcbb8bbb9e0637877631624716129e76d7129a8",
}
P016_APPLICATION_BEFORE = "e124283154b15e57427626f929aff27c508fd4da20ac95f05f2b24c95da410c3"
P016_APPLICATION_AFTER_METADATA = "b5b33d42b15db44ab2bee1ebefa3dfd54557d9b8a8b1cb3340be30253a540f73"
P016_APPLICATION_REVIEW = "9dcb6602-a4a4-5bf5-9073-d00a6db99f76"

# Exact correction for the already-applied Phase 1 release. The expected rows
# come from its protected predecessor and independently qualified new objects;
# SQL's within-object permission ordering must not be replaced by Python sorting.
PHASE1_PERMISSION_REPAIR = {
    "version": 1,
    "id": "p02_phase1_permission_order_v1",
    "predecessor": "5fe2dbdc203c8d7268271b2baccac9d49915d280",
    "sql_commit": "a202a51440f17233800b49801bd31c3ead2a9227",
    "migration_id": "20261109_001_p02_phase1_sql_exports",
    "migration_sha256": "520b58c1b25d80bd28f32324d99b5fede0d6191ddab93ac93469ed5c1f6e4041",
}
PHASE1_PERMISSION_BEFORE = "820351b6c09660881a5513145c6c8e4e583e5d87090ba28b9cb2d864aeddf62b"
PHASE1_PERMISSION_AFTER = "81d81816c1eeabb6071984890f6ff3f66bc117cee2cac49e2bb90080bfc85697"
PHASE1_PERMISSION_HASH = "e172bc534f02ab73efaee5e663bcb815ce36ec68209b3ba73320b9faab7adf96"
PHASE1_PERMISSION_REVIEW = "ab403c8f-03f4-5b65-aeb6-dbcbdc8f0dd4"

# Source-only correction over the exact installed D6 seed; no SQL replay or
# observed-state adoption. The full structural/permission expectations remain.
P02_MAINTENANCE_REPAIR = {
    "version": 1,
    "id": "p02_maintenance_compatibility_v1",
    "predecessor": "729ece15c2dd665906525a4a457667d53516e805",
    "sql_commit": "8a7aace75c55a6d17c9051edef9026dc25355af8",
    "migration_id": "20261111_001_p02_d4_combined",
    "migration_sha256": "57944777e50b7dc9200220cfcc2ce767edb22a2e0972e02bc2cd6f04e23e8171",
}
P02_MAINTENANCE_BEFORE = {
    "sql_contract": "c257388a8d13e20d7903605f26596e5177d829b661dab1c60a086b4d87e6496c",
    "legacy_sql_contract": "e74042f9ff6dd64da10d5d743104e06c2ac08c6903bd9916f5608fff48aada0f",
    "application_sql_contract": "50fb90ecf0174a336c3f8b88e96a69cc3889ce3454c2608a4124caed04ac3092",
}


def p02_maintenance_transition(before, bot):
    """Authenticate all installed contracts and opt into one reviewed policy."""
    from services.application_maintenance_contract import POLICY
    from services.export_execution_protocol import encode

    if before != P02_MAINTENANCE_REPAIR["predecessor"]:
        raise ValueError("Maintenance compatibility requires the exact deployed predecessor")
    contracts = {}
    for key, expected in P02_MAINTENANCE_BEFORE.items():
        if hashlib.sha256(encode(bot[key])).hexdigest() != expected:
            raise ValueError("Maintenance compatibility predecessor contract differs: " + key)
        contracts[key] = {"before": deepcopy(bot[key]), "after": deepcopy(bot[key])}
    contracts["application_sql_contract"]["after"].update(
        maintenance_policy=POLICY, review_id="3edc8fa5-bb12-5d30-b676-ea2e86af67c2"
    )
    return {"contracts": contracts}


def phase1_permission_transition(before, bot):
    """Correct one reviewed permission ordering without changing SQL rights."""
    from services.export_execution_protocol import encode

    if before != PHASE1_PERMISSION_REPAIR["predecessor"]:
        raise ValueError("Phase 1 permission repair requires the exact installed predecessor")
    application = bot["application_sql_contract"]
    if hashlib.sha256(encode(application)).hexdigest() != PHASE1_PERMISSION_BEFORE:
        raise ValueError("Phase 1 predecessor application contract differs")
    after = deepcopy(application)
    after.update(permissions_hash=PHASE1_PERMISSION_HASH, review_id=PHASE1_PERMISSION_REVIEW)
    if hashlib.sha256(encode(after)).hexdigest() != PHASE1_PERMISSION_AFTER:
        raise ValueError("Phase 1 corrected application contract differs")
    contracts = {
        key: {"before": deepcopy(bot[key]), "after": deepcopy(bot[key])}
        for key in ("sql_contract", "legacy_sql_contract", "application_sql_contract")
    }
    contracts["application_sql_contract"]["after"] = after
    return {"contracts": contracts}


def p016_application_transition(before, bot):
    """Amend one exact predecessor contract, preserving all other expectations."""
    from services.export_execution_protocol import encode

    if before != P016_APPLICATION_REPAIR["predecessor"]:
        raise ValueError("P016 application repair requires the exact deployed predecessor")
    application = bot["application_sql_contract"]
    if hashlib.sha256(encode(application)).hexdigest() != P016_APPLICATION_BEFORE:
        raise ValueError("P016 predecessor application contract differs from reviewed evidence")
    after = deepcopy(application)
    after.update(metadata_hash=P016_APPLICATION_AFTER_METADATA, review_id=P016_APPLICATION_REVIEW)
    return {
        "contracts": {
            key: {"before": deepcopy(bot[key]), "after": deepcopy(bot[key])}
            for key in ("sql_contract", "legacy_sql_contract")
        }
        | {"application_sql_contract": {"before": deepcopy(application), "after": after}}
    }


# Fixed reviewed inventory, including dependencies absent from older applications.
# Only these two core helpers are overlaid; configuration/credential readers keep
# the authenticated application's real root and must never move into the archive.
CONTRACT_ARCHIVE_MEMBERS = (
    "core/sql_connection_custody.py",
    "core/sql_operation_policy.py",
    "deploy/p02_d4_activation_scope.json",
    "deploy/p02_phase1_activation_scope.json",
    "deploy/s11_activation_scope.json",
    "deploy/s11_application_grants.json",
    "kvk/__init__.py",
    "kvk/dal/__init__.py",
    "kvk/dal/new_source_admin_dal.py",
    "kvk/dal/new_source_config_dal.py",
    "kvk/dal/new_source_import_dal.py",
    "kvk/dal/source_sql_diagnostics.py",
    "kvk/models/__init__.py",
    "kvk/models/new_source_observation.py",
    "kvk/models/new_source_reporting.py",
    "kvk/models/source_integration.py",
    "kvk/models/source_receipt_state.py",
    "kvk/schemas/__init__.py",
    "kvk/schemas/new_source_schema.py",
    "kvk/services/__init__.py",
    "kvk/services/new_source_artifact_store.py",
    "kvk/services/new_source_digest.py",
    "kvk/services/new_source_metadata.py",
    "kvk/services/new_source_parser.py",
    "services/__init__.py",
    "services/application_maintenance_contract.py",
    "services/application_maintenance_dal.py",
    "services/event_cache_service.py",
    "services/export_contention.py",
    "services/export_contract_resources.py",
    "services/export_coordination_dal.py",
    "services/export_d4_contract.py",
    "services/export_execution_authority.py",
    "services/export_execution_dal.py",
    "services/export_execution_protocol.py",
    "services/export_phase1_contract.py",
    "services/export_publication_metrics.py",
    "services/export_request_budget.py",
    "services/export_runtime_composition.py",
    "services/export_schema_fingerprint.py",
    "services/export_snapshot_store.py",
    "services/export_sql_direct_permissions.py",
)


def _archive_bytes(members):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, raw in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    return stream.getvalue()


def build_contract_archive(root):
    """Package reviewed checkout bytes; never called by runtime admission."""
    root = Path(root)
    members = {}
    for name in CONTRACT_ARCHIVE_MEMBERS:
        with (root / name).open("rb") as stream:
            content = stream.read(CONTRACT_ARCHIVE_LIMIT + 1)
        if len(content) > CONTRACT_ARCHIVE_LIMIT:
            raise ValueError("Contract archive source exceeds bound")
        members[name] = content.replace(b"\r\n", b"\n")
    raw = _archive_bytes(members)
    validate_contract_archive(raw, hashlib.sha256(raw).hexdigest())
    return raw


def validate_contract_archive(raw, expected):
    """Reject changed, ambiguous or unbounded archives before executable imports."""
    if (
        not isinstance(expected, str)
        or re.fullmatch(r"[0-9a-f]{64}", expected) is None
        or not 0 < len(raw) <= CONTRACT_ARCHIVE_LIMIT
        or hashlib.sha256(raw).hexdigest() != expected
    ):
        raise ValueError("Installed contract archive identity differs")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if tuple(entry.filename for entry in entries) != CONTRACT_ARCHIVE_MEMBERS:
            raise ValueError("Exact contract archive inventory required")
        if (
            any(
                entry.compress_type != zipfile.ZIP_STORED
                or entry.flag_bits != 0
                or entry.file_size != entry.compress_size
                or not 0 <= entry.file_size <= CONTRACT_ARCHIVE_LIMIT
                for entry in entries
            )
            or sum(entry.file_size for entry in entries) > CONTRACT_ARCHIVE_LIMIT
        ):
            raise ValueError("Bounded stored contract archive required")
        members = {entry.filename: archive.read(entry) for entry in entries}
    if _archive_bytes(members) != raw:
        raise ValueError("Canonical contract archive required")
    return raw


def activate_contract_archive(path, expected, application_root):
    """Select the sealed verifier after the caller authenticates source/custody.

    Installed manifest or immutable release bindings supply expected, never an
    acquired target. Native callers retain administrative custody during imports.
    No extraction, module eviction, or live-source fallback is permitted.
    """
    archive, root = Path(path), Path(application_root)
    if not archive.is_absolute() or not root.is_absolute() or not root.is_dir():
        raise ValueError("Absolute installed archive and application root required")
    conflicts = {
        "services",
        "kvk",
        "core",
        "bot_config",
        "constants",
        "file_utils",
        "utils",
        "process_utils",
        "event_cache",
        "event_data_loader",
    }
    if any(name.split(".")[0] in conflicts for name in sys.modules):
        raise ValueError("Application modules loaded before verifier selection")
    raw = read(archive, limit=CONTRACT_ARCHIVE_LIMIT)
    validate_contract_archive(raw, expected)
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(archive), str(root)]
    # The archive deliberately has no core/__init__.py. Keep the authenticated
    # application's package identity and root-relative configuration, while the
    # exact sealed helpers win over missing or older installed versions. ZIP
    # inventory validation above prevents arbitrary core modules being overlaid.
    import core

    if Path(core.__file__).resolve() != (root / "core/__init__.py").resolve():
        raise ValueError("Authenticated application core package required")
    core.__path__[:] = [str(archive / "core"), str(root / "core")]


def activate_release_archive(config, directory):
    expected = config["contract_verifier_sha256"]
    members = [m for m in config["extra_members"] if m["name"] == CONTRACT_ARCHIVE]
    if members != [{"name": CONTRACT_ARCHIVE, "sha256": expected}]:
        raise ValueError("Sealed contract archive binding differs")
    activate_contract_archive(Path(directory) / CONTRACT_ARCHIVE, expected, config["root"])


def verify_live_source(config, *, predecessor=False):
    """Use the real bootstrap's complete inventory and custody checks, read-only."""
    root = Path(config["root"])
    policy_path = (
        Path(config["old_policy"]["Path"])
        if predecessor
        else Path(config["new_seed_directory"]) / "AutomaticStartupPolicy.json"
    )
    policy_hash = config["old_policy"]["SHA256"] if predecessor else config["new_policy_sha256"]
    pins = config["old_pins"] if predecessor else config["new_pins"]
    policy = json.loads(read(policy_path, policy_hash))
    if policy["source_hashes"] != pins or policy["flags"] != config["flags"]:
        raise ValueError("Source policy or flags differ")
    if not predecessor and policy != config["new_policy"]:
        raise ValueError("Successor policy differs")
    authority_path = root / "scripts/run_export_authority.py"
    read(authority_path, pins["scripts/run_export_authority.py"])
    authority = runpy.run_path(str(authority_path))
    authority["bootstrap"](
        str(policy_path), script=str(root / "scripts/run_export_startup_issuer.py")
    )
    return policy


def _admission_utc(value, failure):
    if not isinstance(value, str):
        raise ValueError(failure)
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(failure) from None
    if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
        raise ValueError(failure)
    return timestamp


def startup_admission_result(config, journal, start, *, raw=None):
    """Read bounded existing startup evidence before any successor SQL observer.

    This orders observation only. Exact source/native/SQL checks still establish
    readiness; log text never authorizes a start, retry, recovery or business work.
    """
    if (
        set(start) != {"release_id", "requested_utc", "log_offset"}
        or start["release_id"] != config["release_id"]
        or type(start["log_offset"]) is not int
        or start["log_offset"] < 0
    ):
        raise ValueError("Exact start request required for admission observation")
    requested = _admission_utc(start["requested_utc"], "Malformed admission start timestamp")
    binding = journal["bindings"]["bot"]
    expected = journal["publication"]["manifests"]["bot"]
    if raw is None:
        try:
            with (Path(config["root"]) / "logs" / "log.txt").open("rb") as stream:
                length = stream.seek(0, 2)
                if not 0 <= length - start["log_offset"] <= 8 * 1024 * 1024:
                    raise ValueError("Startup log rotated/exceeded bound; admission unresolved")
                stream.seek(start["log_offset"])
                raw = stream.read(8 * 1024 * 1024 + 1)
        except FileNotFoundError as exc:
            raise PairPublicationPending("Awaiting successor admission evidence") from exc
    # Only the sealed running-release verifier supplies a separately captured
    # interval. Its hash-pinned generation and original offset are checked there.
    # The exact admission parser and ordinary updater behavior remain shared.
    if not isinstance(raw, bytes) or len(raw) > 8 * 1024 * 1024:
        raise ValueError("Startup log exceeds admission observation bound")
    results = []
    marker = b"K98_STARTUP_ADMISSION_RESULT "
    # Ordinary log messages can contain the marker as user-controlled text.
    # Undecodable/unbounded records cannot be attributed to this successor;
    # ignore them and keep waiting for exact evidence within the caller's bound.
    # An in-flight final line is likewise not settled evidence.
    for line in raw.splitlines(keepends=True):
        if marker not in line or not line.endswith(b"\n"):
            continue
        payload = line.split(marker, 1)[1]
        if len(payload) > 32768:
            continue
        try:
            record = json.loads(payload)
        except (ValueError, UnicodeError, RecursionError):
            continue
        if not isinstance(record, dict):
            continue
        if (
            record.get("manifest_sha256") != expected
            or record.get("pid") != binding["pid"]
            or record.get("created_filetime") != binding["created_filetime"]
        ):
            continue
        observed = _admission_utc(
            record.get("observed_utc"), "Malformed admission observation timestamp"
        )
        if (
            type(record.get("version")) is not int
            or record["version"] != 1
            or type(record.get("pid")) is not int
            or type(record.get("created_filetime")) is not int
            or not requested <= observed <= datetime.now(UTC)
            or record.get("outcome") not in {"installed", "failed", "disabled"}
        ):
            raise ValueError("Stale or invalid successor admission result")
        results.append(record)
    if not results:
        raise PairPublicationPending(
            "Awaiting exact successor admission settlement; no SQL queried"
        )
    if any(r["outcome"] == "failed" for r in results):
        raise ValueError(
            "Successor admission failed; preserve its first diagnostic; do not restart"
        )
    if len(results) != 1 or results[0]["outcome"] != "installed":
        raise ValueError("One successful initial admission required; readiness unconfirmed")
    return results[0]


def verify_successor_admission(config, journal):
    from core.export_startup_windows import administrative_path

    path = administrative_path(Path(__file__).parent / "start-requested.json", private=True)
    return startup_admission_result(config, journal, json.loads(read(path)))


def verify_successor_contracts(config, policy, journal, *, sql_contracts=True):
    # The installed verifier also serves authenticated historical successors.
    # Only source policies with the new protocol can emit its settlement marker.
    if "services/runtime_admission_diagnostics.py" in policy["source_hashes"]:
        verify_successor_admission(config, journal)
    if sql_contracts:
        verify_sql_contracts(config, policy)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bindings", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--sql-contracts", action="store_true")
    args = parser.parse_args()
    if not sys.flags.isolated:
        raise ValueError("Isolated Python required")
    config = json.loads(read(args.bindings, args.sha256))
    policy = verify_live_source(config, predecessor=args.preflight)
    activate_release_archive(config, Path(__file__).parent)
    if "application_contract_repair" in config and not args.sql_contracts:
        raise ValueError("P016 application repair requires complete SQL contract verification")
    if args.preflight:
        if args.sql_contracts:
            verify_sql_contracts(config, policy, preflight=True)
        print(
            json.dumps(
                dict(stage="PREDECESSOR_LIVE_SOURCE_VERIFIED", sql_connected=args.sql_contracts)
            )
        )
        return
    policy_path = Path(config["new_seed_directory"]) / "AutomaticStartupPolicy.json"
    from core.export_process_identity import open_pinned_process
    from core.export_startup_windows import administrative_path

    def protected(path, expected=None, *, successor=False):
        checked = (
            successor_path(path, validate=administrative_path)
            if successor
            else administrative_path(path, private=True)
        )
        return read(checked, expected)

    protected(args.bindings, args.sha256)
    protected(policy_path, config["new_policy_sha256"])
    state = successor_path(policy["state_directory"], validate=administrative_path)
    journals = list(Path(state).glob("incarnation-*.json"))
    if not journals:
        raise PairPublicationPending(
            "Awaiting the first protected successor journal; no second start requested."
        )
    if len(journals) != 1:
        raise ValueError("Exactly one first successor required; no second start")
    path = journals[0]
    match = re.fullmatch(
        r"incarnation-([0-9]{20})-([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})\.json",
        path.name,
    )
    if match is None:
        raise ValueError("Canonical journal filename required")
    journal = json.loads(protected(path))
    predecessor = json.loads(
        protected(config["old_journal"]["Path"], config["old_journal"]["SHA256"])
    )
    sequence = predecessor["sequence"] + 1
    if (
        type(journal["sequence"]) is not int
        or journal["sequence"] != sequence
        or int(match[1]) != sequence
        or journal["policy_sha256"] != config["new_policy_sha256"]
    ):
        raise ValueError("Successor sequence or policy differs")
    seed = json.loads(protected(policy["seed_plan"]["path"], policy["seed_plan"]["sha256"]))
    live = Path(seed["commit_file"]).parent.parent / match[2]
    publication = json.loads(protected(live / "commit.json", successor=True))
    if publication != journal["publication"]:
        raise ValueError("Published commit differs from protected history")
    plan = json.loads(
        protected(
            live / "ManualProcessPairPlan-CANDIDATE.json",
            publication["plan_sha256"],
            successor=True,
        )
    )
    if set(publication["manifests"]) != {"authority", "bot"} or set(journal["bindings"]) != {
        "authority",
        "bot",
    }:
        raise ValueError("Exact supervised pair required")
    for role, digest in publication["manifests"].items():
        protected(plan["manifests"][role], digest, successor=True)
    issuer = json.loads(protected(live / "AutomaticIssuer.json", successor=True))
    if issuer["plan_sha256"] != publication["plan_sha256"]:
        raise ValueError("Issuer plan differs from protected publication")
    bindings = [*journal["bindings"].values(), issuer["issuer"]]
    if len({binding["pid"] for binding in bindings}) != 3:
        raise ValueError("Three distinct process identities required")
    handles = []
    try:
        for binding in bindings:
            handles.append(open_pinned_process(binding["pid"], binding))
        verify_successor_contracts(config, policy, journal, sql_contracts=args.sql_contracts)
        print(
            json.dumps(
                dict(
                    stage="RELEASE_FIRST_PAIR_NATIVE_VERIFIED",
                    sequence=sequence,
                    authority_manifest=publication["manifests"]["authority"],
                    discord_ready_verified=False,
                    sql_connected=args.sql_contracts,
                )
            ),
            flush=True,
        )
    finally:
        for handle in handles:
            handle.Close()


def bot_from_policy(policy):
    """Read the protected template through its exact plan and content bindings."""
    from core.export_startup_windows import administrative_path

    plan = json.loads(
        read(
            administrative_path(policy["seed_plan"]["path"], private=True),
            policy["seed_plan"]["sha256"],
        )
    )
    ref = plan["templates"]["bot"]
    return json.loads(
        read(administrative_path(ref["path"], private=True), ref["sha256"], 4 * 1024 * 1024)
    )


def repair_verification_bot(config, predecessor, candidate):
    """Verify exact before/after bindings before comparing already-applied SQL."""
    from services.export_execution_protocol import encode

    repair = config["application_contract_repair"]
    if encode(repair) == encode(P016_APPLICATION_REPAIR):
        build_transition = p016_application_transition
    elif encode(repair) == encode(PHASE1_PERMISSION_REPAIR):
        build_transition = phase1_permission_transition
    elif encode(repair) == encode(P02_MAINTENANCE_REPAIR):
        build_transition = p02_maintenance_transition
    else:
        raise ValueError("Unreviewed application contract repair")
    if "sql" in config or "recovery_seed" in config:
        raise ValueError("Application contract repair cannot replay or combine SQL work")
    transition = build_transition(config["before"], predecessor)
    for key, pair in transition["contracts"].items():
        if encode(candidate[key]) != encode(pair["after"]):
            raise ValueError("Candidate contract differs from exact reviewed amendment")
    return candidate


def verify_sql_contracts(config, policy, *, preflight=False, connection_factory=None):
    """Reuse complete startup comparators without constructing the runtime/IPC."""
    from core.export_startup_windows import administrative_path

    bot = bot_from_policy(policy)
    if "application_contract_repair" in config:
        if preflight:
            # The source is still the authenticated predecessor; the sealed
            # candidate must contain precisely the separately reviewed amendment.
            members = [m for m in config["seed_members"] if m["name"] == "bot-template.json"]
            if len(members) != 1:
                raise ValueError("One sealed candidate Bot template required")
            candidate_path = administrative_path(
                Path(__file__).parent / "bot-template.json", private=True
            )
            candidate = json.loads(read(candidate_path, members[0]["sha256"], 4 * 1024 * 1024))
            bot = repair_verification_bot(config, bot, candidate)
        else:
            old = config["old_policy"]
            predecessor_policy = json.loads(
                read(administrative_path(old["Path"], private=True), old["SHA256"])
            )
            bot = repair_verification_bot(config, bot_from_policy(predecessor_policy), bot)
    if connection_factory is None:
        return verify_bot_sql_contracts(bot)
    return verify_bot_sql_contracts(bot, connection_factory=connection_factory)


def verify_bot_sql_contracts(bot, *, connection_factory=None):
    """Check all three reviewed contracts against actual SQL before recording proof."""
    from datetime import datetime
    from functools import partial

    from kvk.dal.new_source_admin_dal import configured_connection
    from services.export_execution_dal import (
        ExportExecutionDAL,
        installation_migrations,
        legacy_installation_snapshot,
    )
    from services.export_runtime_composition import (
        application_snapshot_for_contract,
        verify_application_installation_contract,
        verify_installation_contract,
        verify_legacy_installation_contract,
    )

    approved = bot["sql_contract"]
    factory = connection_factory or partial(configured_connection, sql_profile=approved["profile"])

    def phase(name):
        # Optional evidence hook on the standalone bounded owner, never a SQL
        # probe or a new requirement on ordinary runtime connection factories.
        observe = getattr(type(factory), "observation_phase", None)
        if observe is not None:
            observe(factory, name)

    phase("export")
    installation = ExportExecutionDAL(factory).installation_snapshot(
        **({"migrations": installation_migrations(approved)} if approved["version"] == 4 else {})
    )
    verify_installation_contract(installation, approved)
    connection = factory()
    try:
        connection.autocommit = True
        cursor = connection.cursor()
        try:
            phase("legacy")
            legacy = legacy_installation_snapshot(cursor, bot["legacy_sql_contract"]["source"])
            verify_legacy_installation_contract(
                legacy,
                bot["legacy_sql_contract"],
                profile=approved["profile"],
            )
            phase("application")
            application = application_snapshot_for_contract(cursor, bot["application_sql_contract"])
            verify_application_installation_contract(application, bot["application_sql_contract"])
        finally:
            from core.sql_connection_custody import connection_retained

            if not connection_retained(connection):
                cursor.close()
    finally:
        from core.sql_connection_custody import connection_retained

        if not connection_retained(connection):
            connection.close()
    print(json.dumps(dict(stage="STARTUP_SQL_CONTRACTS_VERIFIED", business_work=False)))
    # Return the complete actual catalog evidence, not expected contract fields.
    # Callers can retain and reverify this observation; no expectation is adopted
    # from it, and a failed comparator prevents any successful return.
    return dict(
        observed_utc=datetime.now(UTC).isoformat(),
        installation=installation,
        legacy=legacy,
        application=application,
    )


if __name__ == "__main__":
    try:
        main()
    except PairPublicationPending as exc:
        print(
            json.dumps(
                dict(stage="WAITING_FOR_FIRST_PAIR_PUBLICATION", detail=str(exc), verified=False)
            ),
            flush=True,
        )
        raise SystemExit(11)
    except Exception as exc:
        print(
            json.dumps(
                dict(
                    stage="STOP_NEW_PAIR_UNCONFIRMED",
                    failure_type=type(exc).__name__,
                    detail=str(exc),
                )
            ),
            flush=True,
        )
        raise SystemExit(1)
