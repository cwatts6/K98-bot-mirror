"""Verify the release's first protected publication and three live native identities.

Read-only. Invoke with the pinned installed venv Python after the runner seals this artifact.
No application entry point, recovery or provider work is invoked. With --sql-contracts,
read-only SQL observations are checked by the complete existing startup comparators.
"""

import argparse
from datetime import UTC
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
# Fixed reviewed inventory: services/kvk and their metadata resources only.
# core and root configuration retain the authenticated application's .env root.
CONTRACT_ARCHIVE_MEMBERS = (
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
    "services/event_cache_service.py",
    "services/export_contention.py",
    "services/export_contract_resources.py",
    "services/export_coordination_dal.py",
    "services/export_execution_authority.py",
    "services/export_execution_dal.py",
    "services/export_execution_protocol.py",
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
    if args.sql_contracts:
        verify_sql_contracts(config, policy)
    if args.preflight:
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


def verify_sql_contracts(config, policy):
    """Reuse complete startup comparators without constructing the runtime/IPC."""
    from core.export_startup_windows import administrative_path

    plan = json.loads(
        read(
            administrative_path(policy["seed_plan"]["path"], private=True),
            policy["seed_plan"]["sha256"],
        )
    )
    ref = plan["templates"]["bot"]
    bot = json.loads(
        read(administrative_path(ref["path"], private=True), ref["sha256"], 4 * 1024 * 1024)
    )
    verify_bot_sql_contracts(bot)


def verify_bot_sql_contracts(bot):
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
    factory = partial(configured_connection, sql_profile=approved["profile"])
    installation = ExportExecutionDAL(factory).installation_snapshot(
        **({"migrations": installation_migrations(approved)} if approved["version"] == 4 else {})
    )
    verify_installation_contract(installation, approved)
    connection = factory()
    try:
        connection.autocommit = True
        cursor = connection.cursor()
        try:
            legacy = legacy_installation_snapshot(cursor, bot["legacy_sql_contract"]["source"])
            verify_legacy_installation_contract(
                legacy,
                bot["legacy_sql_contract"],
                profile=approved["profile"],
            )
            application = application_snapshot_for_contract(cursor, bot["application_sql_contract"])
            verify_application_installation_contract(application, bot["application_sql_contract"])
        finally:
            cursor.close()
    finally:
        connection.close()
    print(json.dumps(dict(stage="UNCHANGED_STARTUP_SQL_CONTRACTS_VERIFIED", business_work=False)))
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
        raise SystemExit(1)
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
