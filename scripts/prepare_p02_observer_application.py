"""Prepare a lab-only complete application read; never issue production history."""

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
from uuid import uuid4
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.prepare_p02_observer_fingerprint import BASELINE_ARCHIVE, BASELINE_ROWS
from scripts.verify_k98_update_pair import CONTRACT_ARCHIVE_MEMBERS
from services.application_maintenance_contract import POLICY
from services.application_observation_fingerprint import FORMAT
from services.catalogue_observation_contract import PROTOCOL_SHA256
from services.export_d4_contract import MIGRATION_ID as D4_MIGRATION
from services.export_observer_contract import ACTIVATION_SCOPE_SHA256, MIGRATION_ID
from services.export_phase1_contract import MIGRATION_ID as PHASE1_MIGRATION
from services.export_sql_direct_permissions import application_grant_rows

AREA = ROOT / ".codex_artifacts/p02-observer-proof-20261119"
PREREQUISITES = "packet-20261119175737420/boundary-20261120130032231.json"
PREREQUISITES_SHA = "09d928c8a258af89f89ecc473b6a8a9cd8c947fa5df2150576e4c1a724806159"
BASELINE = Path(
    "C:/Users/cwatt/.codex/worktrees/p02-private-promotion/discord_file_downloader/"
    ".codex_artifacts/p02-native-qualification/Admission-Observation-v2/received-run-01.zip"
)
PRINCIPAL = "S11_ExportApplication_P02ObserverQual"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build():
    prerequisites = (AREA / PREREQUISITES).read_bytes()
    assert sha(prerequisites) == PREREQUISITES_SHA
    observed = json.loads(prerequisites)
    assert observed["connection_closed"] and "failure" not in observed
    assert not observed["reads"]["observer_objects"] and not observed["reads"]["active_sessions"]
    assert not observed["reads"]["lifecycle_permissions"]
    assert all(row["name"] != PRINCIPAL for row in observed["reads"]["lab_logins"])
    # Authenticate the existing installation/restore proof using its established,
    # offline-only lineage verifier. It cannot substitute for production history.
    old_root = "C:/Users/cwatt/.codex/worktrees/p02-private-promotion/discord_file_downloader"
    code = (
        "import sys,json;sys.path.insert(0,sys.argv[1]);"
        "from scripts.p02_restored_baseline import lab_lineage;"
        "print(json.dumps(lab_lineage()))"
    )
    lineage = json.loads(
        subprocess.check_output(
            [sys.executable, "-I", "-c", code, old_root],
            timeout=30,
        )
    )
    assert lineage["accepted"] is True and lineage["productionEligible"] is False
    assert sha(BASELINE.read_bytes()) == BASELINE_ARCHIVE
    with zipfile.ZipFile(BASELINE) as archive:
        raw = archive.read("run-01/observations.jsonl")
    assert sha(raw) == BASELINE_ROWS
    application = next(
        json.loads(row)["observation"]
        for row in raw.splitlines()
        if json.loads(row)["stage"] == "application_sql_contract"
    )
    profile = json.loads(
        (AREA / "source-migration-01" / (MIGRATION_ID + ".release.json")).read_bytes()
    )
    assert profile["predecessor_bodies_utf16le_lf"] == {
        row["ObjectName"]: row["DefinitionSHA256"]
        for row in observed["reads"]["predecessor_bodies"]
    }
    source = (AREA / "source-migration-01" / (MIGRATION_ID + ".sql")).read_bytes()
    assert sha(source) == profile["script"]["sha256"]
    text = source.decode()
    pattern = r"IF NOT EXISTS\(SELECT 1 FROM dbo.SchemaMigrationHistory\n.*?THROW 51973,'Exact successful D4 predecessor receipt required\.',1;\n"
    matches = re.findall(pattern, text, re.S)
    assert len(matches) == 1 and D4_MIGRATION in matches[0]
    # The only lab substitution is this predecessor evidence type. Every object,
    # grant, bootstrap and transaction check stays identical to the candidate.
    text = text.replace(
        matches[0],
        "-- LAB ONLY: authenticated retained_lab_installation_v1; no history row is manufactured.\n",
    )
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")[:17]
    sid = uuid4().hex
    approved: dict[str, Any] = dict(
        version=3,
        server="MINI_AMD",
        database="ROK_TRACKER",
        principal=PRINCIPAL,
        sources=json.loads((ROOT / "deploy/p02_observer_application_sources.json").read_bytes()),
        dynamic_objects=[
            dict(
                name="dbo.EXCEL_EXPORT_KVK_TARGETS_16",
                type="U",
                producer_modules=["dbo.sp_TARGETS_MASTER"],
            ),
            dict(
                name="dbo.EXCEL_FOR_KVK_16", type="U", producer_modules=["dbo.sp_ExcelOutput_ByKVK"]
            ),
            dict(
                name="dbo.EXCEL_OUTPUT_KVK_TARGETS_16",
                type="U",
                producer_modules=["dbo.sp_Prep_ExcelOutputTable"],
            ),
            dict(name="dbo.TARGETS_16", type="U", producer_modules=["dbo.sp_Prep_TargetTable"]),
        ],
        metadata_hash="f575d6a9dfdfa74bc628d2e22e79924c4ce9cec63428321814a6f6b9d8c9994c",
        permissions_hash="0be05a7afb3dd97d135e3bbca1bea01dc13785caac416583a0f747656bf111b4",
        review_id=str(uuid4()),
        phase1_installation=PHASE1_MIGRATION,
        d4_installation=D4_MIGRATION,
        observer_installation=MIGRATION_ID,
        scope_hash=ACTIVATION_SCOPE_SHA256,
        fingerprint_format=FORMAT,
        maintenance_policy=POLICY,
    )
    # These scope values are source requirements, not inferred from the small
    # mechanism fixture or silently narrowed to its three absent output tables.
    assert {row["ObjectName"] for row in observed["reads"]["dynamic_outputs"]} == {
        row["name"] for row in approved["dynamic_objects"]
    }
    assert application["target"]["DatabaseName"] == approved["database"]
    members = {
        "bot/" + name: (ROOT / name).read_bytes()
        for name in set(CONTRACT_ARCHIVE_MEMBERS)
        | {
            "services/application_observation_admission.py",
            "core/__init__.py",
            "core/recovery_sql_snapshot.py",
            "core/sql_observation.py",
            "event_calendar/__init__.py",
            "event_calendar/sql_lifecycle.py",
        }
    }
    members.update(
        {
            "qualification/p02_observer/application.py": (
                ROOT / "scripts/prove_p02_observer_application.py"
            ).read_bytes(),
            "Verify-RunningRelease.py": (
                ROOT / "scripts/verify_k98_running_release.py"
            ).read_bytes(),
            "sql/lab-install.sql": text.encode(),
            "sql/production-candidate.sql": source,
            "evidence/prerequisites.json": prerequisites,
            "evidence/lab-lineage.json": json.dumps(lineage, indent=2).encode(),
        }
    )
    manifest = dict(
        stage="restored-application-observer",
        database="ROK_TRACKER",
        database_id=12,
        created="2026-11-17 17:34:47.357000",
        principal=PRINCIPAL,
        login_sid=sid,
        approved=approved,
        protocol_sha256=PROTOCOL_SHA256,
        snapshot="K98_P02Observer_RokBefore_" + stamp,
        snapshot_file="Q:\\D5eCost-20261115\\P02Observer_RokBefore_" + stamp + ".ss",
        history_sha256=sha(
            json.dumps(observed["reads"]["history"], sort_keys=True, separators=(",", ":")).encode()
        ),
        production_eligible=False,
        qualification_only=True,
        files={name: sha(raw) for name, raw in sorted(members.items())},
    )
    return seal(members, manifest, stamp)


def seal(members, manifest, stamp):
    manifest["files"] = {name: sha(raw) for name, raw in sorted(members.items())}
    members["manifest.json"] = json.dumps(manifest, indent=2).encode()
    output = AREA / ("packet-" + stamp)
    output.mkdir()
    with zipfile.ZipFile(output / "packet.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(members.items()):
            archive.writestr(name, raw)
    sealed = dict(
        archive=str(output / "packet.zip"),
        sha256=sha((output / "packet.zip").read_bytes()),
        guest_directory="Q:\\P02Observer\\" + stamp,
        database="ROK_TRACKER",
        stage=manifest["stage"],
    )
    (output / "seal.json").write_text(json.dumps(sealed, indent=2), encoding="utf-8")
    return sealed


def application_grant_repair(members):
    """Explain missing lab rights from the existing independently pinned profile."""
    prior = AREA / "packet-20261120132151081"
    receipt_raw = (prior / "receipt.json").read_bytes()
    assert sha(receipt_raw) == "0cd8a728d62346c9362d28ffb80a527a60d1fb840e4f5a143a33f5d0594078db"
    receipt = json.loads(receipt_raw)
    assert receipt["outcome"] == "failed" and receipt["installation_replayed"] is False
    assert receipt["failure"]["contract_reason"] == (
        "Whole application effective permissions differ or are unknown."
    )
    assert receipt["connections_closed"] == 2 and receipt["lab_login_cleanup"][0]["is_disabled"]
    observed_raw = (prior / "cold-application-observation.json").read_bytes()
    assert sha(observed_raw) == "733a74f2ede9bc6abec565bdbdc0c88ff2f3fbd3ff0d99c228d56207aae10bf9"
    observed = json.loads(observed_raw)["observation"]
    expected_raw = (AREA / "source-fingerprint-02/expected-permissions.json").read_bytes()
    assert sha(expected_raw) == "0be05a7afb3dd97d135e3bbca1bea01dc13785caac416583a0f747656bf111b4"
    expected = json.loads(expected_raw)
    application_grant_rows()  # Authenticate the existing profile, not live inferred grants.
    plan = json.loads((ROOT / "deploy/s11_application_grants.json").read_bytes())
    assert observed["schema_permissions"] == expected["schema_permissions"]
    key = lambda r: (r["ObjectName"], r["PermissionName"], r["Subentity"])
    actual_keys = {key(r) for r in observed["object_permissions"]}
    expected_keys = {key(r) for r in expected["object_permissions"]}
    assert len(actual_keys) == len(observed["object_permissions"])
    assert len(expected_keys) == len(expected["object_permissions"])
    assert actual_keys < expected_keys
    missing = expected_keys - actual_keys
    selected = [
        r for r in plan["grants"] if (r["object"], r["permission"], r.get("column", "")) in missing
    ]
    roots = {(r["object"], r["permission"], r.get("column", "")) for r in selected}
    assert len(selected) == len(roots) == 126
    assert all((n, p, c) in roots or (n, p, "") in roots for n, p, c in missing)
    assert len(observed["column_permissions"]) == len(expected["column_permissions"])
    for actual, wanted in zip(
        observed["column_permissions"], expected["column_permissions"], strict=True
    ):
        if actual == wanted:
            continue
        assert dict(actual, Allowed=1) == wanted and actual["Allowed"] == 0
        n, p, c = (wanted[k] for k in ("ObjectName", "PermissionName", "ColumnName"))
        assert (n, p, c) in roots or (n, p, "") in roots
    sources = {
        row["name"]: row
        for row in json.loads((ROOT / "deploy/p02_observer_application_sources.json").read_bytes())
    }
    statements = []
    checked = {}
    for row in selected:
        name, permission = row["object"], row["permission"]
        assert permission in {"SELECT", "INSERT", "UPDATE", "DELETE", "EXECUTE", "REFERENCES"}
        parts = name.split(".")
        assert len(parts) == 2 and all(re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", p) for p in parts)
        source = sources[name]
        raw = (Path("C:/K98-bot-SQL-Server") / source["path"]).read_bytes().replace(b"\r\n", b"\n")
        assert sha(raw) == source["sha256"], name
        checked[name] = source["sha256"]
        column = row.get("column")
        assert column is None or re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", column)
        if column:
            assert re.search(r"\b" + re.escape(column) + r"\b", raw.decode("utf-8-sig")), name
        minor = f"COLUMNPROPERTY(OBJECT_ID(N'{name}'),N'{column}','ColumnId')" if column else "0"
        target = ".".join("[" + p + "]" for p in parts)
        suffix = " ([" + column + "])" if column else ""
        statements.append(
            f"IF OBJECT_ID(N'{name}') IS NULL OR {minor} IS NULL "
            "THROW 51973,'Lab grant target missing.',1;\n"
            "IF EXISTS(SELECT 1 FROM sys.database_permissions WHERE class=1 "
            f"AND major_id=OBJECT_ID(N'{name}') AND minor_id={minor} "
            f"AND grantee_principal_id=USER_ID(N'{PRINCIPAL}') AND permission_name=N'{permission}') "
            "THROW 51973,'Lab grant preimage changed; no replay.',1;\n"
            f"GRANT {permission} ON OBJECT::{target}{suffix} TO [{PRINCIPAL}];"
        )
    repair = dict(
        grant_count=len(statements),
        objects=len(checked),
        source_sha256=checked,
        profile_sha256=sha((ROOT / "deploy/s11_application_grants.json").read_bytes()),
        batches=["\n".join(statements[i : i + 16]) for i in range(0, len(statements), 16)],
    )
    members["evidence/permission-failure-receipt.json"] = receipt_raw
    members["evidence/permission-failure-observation.json"] = observed_raw
    members["qualification/p02_observer/lab-grant-repair.json"] = json.dumps(
        repair, indent=2
    ).encode()
    return dict(grants=126, objects=len(checked), source="existing_application_profile")


def continue_read(*, repair_grants=False):
    prior = AREA / "packet-20261120131206690"
    raw = (prior / "receipt.json").read_bytes()
    assert sha(raw) == "80706721d3f95d7d6fd7a184ca144ec46f3b5a3044f1882d95cb6927acf04e00"
    receipt = json.loads(raw)
    assert receipt["outcome"] == "failed" and receipt["failure"] == {"error_type": "SourceConflict"}
    assert receipt["connections_closed"] == 2 and receipt["lab_login_cleanup"][0]["is_disabled"]
    assert receipt["stages"][-1]["name"] == "candidate-commit-acknowledged"
    binding_raw = (prior / "lab-installation.json").read_bytes()
    assert sha(binding_raw) == "fa15b23b2179ccb254d9e35b5d1863c76e7b06f0746f976ecc96647dd3b1221e"
    binding = json.loads(binding_raw)["binding"]
    packed = (prior / "packet.zip").read_bytes()
    assert sha(packed) == "23d63cb474a3bf5df2722ba0b56fca74dc3e79e0fd90ab57f007357b08eef3f8"
    with zipfile.ZipFile(prior / "packet.zip") as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert set(archive.namelist()) == {"manifest.json", *manifest["files"]}
        assert all(sha(archive.read(n)) == h for n, h in manifest["files"].items())
        members = {n: archive.read(n) for n in manifest["files"] if not n.startswith("sql/")}
    members["qualification/p02_observer/application_setup.py"] = members.pop(
        "qualification/p02_observer/application.py"
    )
    members["qualification/p02_observer/application.py"] = (
        ROOT / "scripts/continue_p02_observer_application.py"
    ).read_bytes()
    members["evidence/prior-application-receipt.json"] = raw
    members["evidence/committed-lab-installation.json"] = binding_raw
    manifest["continuation"] = dict(
        guest_directory=r"Q:\P02Observer\20261120131206690",
        credential_sha256=receipt["stages"][1]["credential_sha256"],
        binding=binding,
    )
    if repair_grants:
        manifest["grant_repair"] = application_grant_repair(members)
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")[:17]
    return seal(members, manifest, stamp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--continue-read", action="store_true")
    parser.add_argument("--repair-grants", action="store_true")
    args = parser.parse_args()
    if args.repair_grants and not args.continue_read:
        parser.error("--repair-grants requires --continue-read")
    print(
        json.dumps(
            continue_read(repair_grants=args.repair_grants) if args.continue_read else build(),
            indent=2,
        )
    )
