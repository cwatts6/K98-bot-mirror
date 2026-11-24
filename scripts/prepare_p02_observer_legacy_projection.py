"""Derive the successor legacy expectation from accepted rows and reviewed source.

The required new Applied receipt is an expectation, never inserted or represented
as observed evidence. This preparation cannot issue a production configuration.
"""

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.prepare_p02_observer_contract_sources import _definition
from scripts.prepare_p02_observer_fingerprint import (
    AMENDED,
    BASELINE_ARCHIVE,
    BASELINE_ROWS,
    sha,
)
from services.application_observation_fingerprint import PROCEDURES, reviewed_procedure_hashes
from services.catalogue_observation_dal import canonical_module
from services.export_contract_resources import read_contract_resource
from services.export_d4_contract import MIGRATION_ID as D4_MIGRATION
from services.export_execution_protocol import encode
from services.export_observer_contract import (
    LEGACY_FINGERPRINT_FORMAT,
    MIGRATION_ID,
    PROFILE_SHA256,
    canonical_legacy_observation,
)
from services.export_phase1_contract import MIGRATION_ID as PHASE1_MIGRATION
from services.export_runtime_composition import verify_legacy_installation_contract
from services.export_sql_direct_permissions import (
    DIRECT_MIGRATION,
    FILE_VISIBILITY_MIGRATION,
    P0_RECEIPT_MIGRATION,
    STATS_OUTCOME_ENCODING_MIGRATION,
)

BASELINE_LEGACY = "3f5f2cf133ca092a0721928546e4dce5300f0d2c3c60578112ef8b8de45ee713"


def prepare(baseline_archive, sql_root, output):
    baseline_archive, sql_root, output = map(Path, (baseline_archive, sql_root, output))
    if output.exists():
        raise ValueError("New legacy projection directory required")
    assert sha(baseline_archive.read_bytes()) == BASELINE_ARCHIVE
    with zipfile.ZipFile(baseline_archive) as archive:
        raw = archive.read("run-01/observations.jsonl")
    assert sha(raw) == BASELINE_ROWS
    before = next(
        row["observation"]
        for row in map(json.loads, raw.splitlines())
        if row["stage"] == "legacy_sql_contract"
    )
    assert sha(encode(before)) == BASELINE_LEGACY
    expected = deepcopy(before)
    source = json.loads(read_contract_resource("p02_observer_legacy_source.json"))
    pinned = reviewed_procedure_hashes()
    objects = {row["ObjectName"]: row for row in expected["modules"]}
    assert AMENDED <= objects.keys() and not (PROCEDURES - AMENDED) & objects.keys()
    for row in source["modules"]:
        if row["name"] not in PROCEDURES:
            continue
        raw = (sql_root / row["path"]).read_bytes().replace(b"\r\n", b"\n")
        assert sha(raw) == row["source_sha256"]
        body = _definition(raw, "PROCEDURE")
        assert sha(canonical_module(body).encode("utf-16-le")) == pinned[row["name"]]
        descriptor = dict(
            ObjectName=row["name"],
            ObjectType="P",
            AnsiNulls=1,
            QuotedIdentifier=1,
            ExecuteAsPrincipal=None,
            OwnerName="dbo",
        )
        if row["name"] in AMENDED:
            assert {
                k: v for k, v in objects[row["name"]].items() if k != "ModuleDefinition"
            } == descriptor
        objects[row["name"]] = dict(descriptor, ModuleDefinition=body)
    expected["modules"] = [objects[name] for name in sorted(objects)]
    for name in sorted(PROCEDURES - AMENDED):
        expected["module_permissions"].extend(
            dict(ObjectName=name, PermissionName=right, Allowed=int(right in {"ALTER", "EXECUTE"}))
            for right in ("ALTER", "CONTROL", "EXECUTE", "TAKE OWNERSHIP")
        )
    expected["module_permissions"].sort(key=lambda row: (row["ObjectName"], row["PermissionName"]))
    for row in source["grants"]:
        if row.get("state") != "D" and row["target"] not in PROCEDURES - AMENDED:
            continue
        expected["grants"].append(
            dict(
                DatabaseName=row["database"],
                PrincipalName=row["principal"],
                SecurableClass=row["securable_class"],
                TargetName=row["target"],
                PermissionName=row["permission"],
                GrantState=row.get("state", "G"),
                MinorID=0,
            )
        )
    expected["grants"].sort(
        key=lambda row: tuple(
            row[k]
            for k in (
                "DatabaseName",
                "PrincipalName",
                "SecurableClass",
                "TargetName",
                "PermissionName",
                "GrantState",
                "MinorID",
            )
        )
    )
    expected["migration"].append(
        dict(MigrationId=MIGRATION_ID, ChecksumSha256=PROFILE_SHA256, Status="Applied")
    )
    expected["migration"].sort(key=lambda row: row["MigrationId"])
    # Other rows, including failed historical receipts, remain exactly intact.
    for category in set(before) - {"modules", "module_permissions", "grants", "migration"}:
        assert expected[category] == before[category]
    target = before["target"][0]
    approved = dict(
        version=2,
        server=target["ServerName"],
        database=target["DatabaseName"],
        principal=target["Principal"],
        login_sid=target["LoginSID"],
        source=source,
        migration_hash=next(
            row["ChecksumSha256"]
            for row in before["migration"]
            if row["MigrationId"] == DIRECT_MIGRATION
        ),
        metadata_hash=sha(encode(canonical_legacy_observation(expected))),
        recovery_installation=P0_RECEIPT_MIGRATION,
        module_amendment=FILE_VISIBILITY_MIGRATION,
        outcome_installation=dict(
            migration_id=STATS_OUTCOME_ENCODING_MIGRATION,
            predecessor_status="Failed",
            collation_predecessor_status="Failed",
        ),
        phase1_installation=PHASE1_MIGRATION,
        d4_installation=D4_MIGRATION,
        observer_installation=MIGRATION_ID,
        fingerprint_format=LEGACY_FINGERPRINT_FORMAT,
    )
    verify_legacy_installation_contract(expected, approved, profile="application")
    output.mkdir()
    (output / "expected-legacy.json").write_bytes(encode(expected))
    # Clearly a template: only a protected release issuer may adopt it after
    # migration/identity qualification and actual three-contract comparisons.
    (output / "legacy-contract-template.json").write_bytes(encode(approved))
    report = dict(
        status="candidate_not_release_authority",
        before_sha256=BASELINE_LEGACY,
        expected_raw_sha256=sha(encode(expected)),
        expected_metadata_sha256=approved["metadata_hash"],
        added_modules=sorted(PROCEDURES - AMENDED),
        modified_modules=sorted(AMENDED),
        added_permission_rows=6,
        added_module_permission_rows=12,
        required_new_migration=dict(migration_id=MIGRATION_ID, checksum_sha256=PROFILE_SHA256),
        full_comparator_on_source_expectation_passed=True,
        native_comparison_completed=False,
        issued=False,
        production_operations=0,
    )
    (output / "projection.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-archive", required=True)
    parser.add_argument("--sql-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.baseline_archive, args.sql_root, args.output), indent=2))
