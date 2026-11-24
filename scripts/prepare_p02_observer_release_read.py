"""Seal a bounded read-only native check, never run it or install SQL."""

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import zipfile

from services.export_observer_contract import MIGRATION_ID, PROFILE_SHA256

ENTRY = r"""from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

packet = Path(__file__).resolve().parents[2]
manifest = json.loads((packet / 'manifest.json').read_bytes())
if os.environ.get('COMPUTERNAME') != 'MINI_AMD' or manifest['stage'] != 'observer-release-preflight-read' or manifest['production_eligible'] is not False:
    raise ValueError('Exact read-only VM packet required')
for name, digest in manifest['files'].items():
    member = (packet / name).resolve()
    if not member.is_relative_to(packet) or hashlib.sha256(member.read_bytes()).hexdigest() != digest:
        raise ValueError('Sealed read-only member differs')
command = [r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(packet / 'qualification/p02_observer/release_read.ps1')]
process = subprocess.Popen(command, cwd=packet)
try:
    code = process.wait(timeout=90)
except subprocess.TimeoutExpired:
    (packet / 'progress.json').write_text(json.dumps(dict(state='retained-running', pid=process.pid, replay_allowed=False)))
    raise SystemExit(2)
raise SystemExit(code)
"""


def prepare(sql_root, evidence):
    sql_root, evidence = Path(sql_root), Path(evidence)
    previous = evidence / "packet-20261120132838937/receipt.json"
    if (
        hashlib.sha256(previous.read_bytes()).hexdigest()
        != "062c8cc7ddf90d8862fa690e168c479e7920d30aab77b755a81c5bcaba9f6a14"
    ):
        raise ValueError("Exact completed read milestone required; do not replay it")
    members = {"qualification/p02_observer/application.py": ENTRY.encode()}
    for name in (
        "deploy/SqlDeploy.ModuleRelease.ps1",
        "deploy/SqlDeploy.P02ObserverRelease.ps1",
        "qualification/p02_observer/release_read.ps1",
    ):
        target = name if name.startswith("qualification/") else "sql/" + name
        members[target] = (sql_root / name).read_bytes()
    for suffix in (".sql", ".before.sql", ".after.sql", ".release.json"):
        name = "migrations/" + MIGRATION_ID + suffix
        members["sql/" + name] = (sql_root / name).read_bytes()
    if (
        hashlib.sha256(members["sql/migrations/" + MIGRATION_ID + ".release.json"]).hexdigest()
        != PROFILE_SHA256
    ):
        raise ValueError("Exact candidate observer profile required")
    manifest = dict(
        version=1,
        stage="observer-release-preflight-read",
        production_eligible=False,
        database="ROK_TRACKER",
        database_id=12,
        profile_sha256=PROFILE_SHA256,
        vm_id="2ac1b401-7076-4965-af71-de36ee0f9f9c",
        sql_changes=0,
        business_operations=0,
        files={name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(members.items())},
    )
    return seal(members, manifest, evidence)


def seal(members, manifest, evidence):
    members["manifest.json"] = json.dumps(manifest, indent=2).encode()
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")[:17]
    output = evidence / ("packet-" + stamp)
    output.mkdir()
    with zipfile.ZipFile(output / "packet.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(members.items()):
            archive.writestr(name, raw)
    seal = dict(
        archive=str((output / "packet.zip").resolve()),
        sha256=hashlib.sha256((output / "packet.zip").read_bytes()).hexdigest(),
        guest_directory="Q:\\P02Observer\\" + stamp,
        database="ROK_TRACKER",
        stage=manifest["stage"],
    )
    (output / "seal.json").write_text(json.dumps(seal, indent=2), encoding="utf-8")
    return seal


def prepare_fixture_source(sql_root, evidence):
    """Inspect an existing backup header; no restore, rename or installation."""
    sql_root, evidence = Path(sql_root), Path(evidence)
    previous = evidence / "packet-20261120145838497/receipt.json"
    digest = hashlib.sha256(previous.read_bytes()).hexdigest()
    if digest != "d89967ba597178fc0a7b92ce372fc6afe73123621e22cfc515e5a6fac6e03920":
        raise ValueError("Exact retained native inventory required")
    retained = json.loads(previous.read_bytes())
    if (
        retained["connections_closed"] != 1
        or retained["dispatches"] != 9
        or not all(row["passed"] for row in retained["checks"])
    ):
        raise ValueError("Completed native reads and clean closure required")
    stage = "observer-release-fixture-read"
    entry = ENTRY.replace("observer-release-preflight-read", stage).replace(
        "release_read.ps1", "fixture_read.ps1"
    )
    members = {
        "qualification/p02_observer/application.py": entry.encode(),
        "qualification/p02_observer/fixture_read.ps1": (
            sql_root / "qualification/p02_observer/fixture_read.ps1"
        ).read_bytes(),
    }
    manifest = dict(
        version=1,
        stage=stage,
        production_eligible=False,
        database="ROK_TRACKER",
        database_id=12,
        vm_id="2ac1b401-7076-4965-af71-de36ee0f9f9c",
        sql_changes=0,
        business_operations=0,
        purpose="Read genuine pre-P02 backup metadata and storage; no restore, rename, replay or integrity claim",
        prior_native_inventory_sha256=digest,
        backup_path=r"C:\Program Files\Microsoft SQL Server\MSSQL16.MSSQLSERVER\MSSQL\DATA\P021_PreImport_20261107_inputs\ROK_TRACKER_full_20261103.bak",
        files={name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(members.items())},
    )
    return seal(members, manifest, evidence)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql-root", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--fixture-source", action="store_true")
    args = parser.parse_args()
    build = prepare_fixture_source if args.fixture_source else prepare
    print(json.dumps(build(args.sql_root, args.evidence), indent=2))
