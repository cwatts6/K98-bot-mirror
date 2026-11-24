"""Prepare a source-bound observer migration; never connect, install or issue approval.

The release coordinator must physically drain first, own the transaction and
write its ordinary migration receipt. The sequence identity returned by this
batch is provisional until commit and a separate postcommit read agree.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.prepare_p02_observer_contract_sources import _definition
from scripts.prepare_p02_observer_fingerprint import (
    AMENDED,
    BASELINE_ARCHIVE,
    BASELINE_OBSERVATION,
    BASELINE_ROWS,
)
from services.application_observation_fingerprint import (
    LEGACY_SOURCE_SHA256,
    PROCEDURES,
    reviewed_procedure_hashes,
)
from services.catalogue_observation_contract import PROTOCOL_SHA256, reviewed_protocol_modules
from services.catalogue_observation_dal import canonical_module
from services.export_contract_resources import read_contract_resource
from services.export_d4_contract import (
    MIGRATION_ID as D4_MIGRATION,
    PROFILE_SHA256 as D4_CHECKSUM,
)
from services.export_execution_protocol import encode

MIGRATION = "20261120_001_p02_catalogue_observer"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def literal(value):
    return "N'" + value.replace("'", "''") + "'"


def prepare(baseline_archive, sql_root, output):
    baseline_archive, sql_root, output = map(Path, (baseline_archive, sql_root, output))
    if output.exists():
        raise ValueError("New migration preparation directory required")
    assert sha(baseline_archive.read_bytes()) == BASELINE_ARCHIVE
    with zipfile.ZipFile(baseline_archive) as archive:
        raw = archive.read("run-01/observations.jsonl")
    assert sha(raw) == BASELINE_ROWS
    before = next(
        row["observation"]
        for row in map(json.loads, raw.splitlines())
        if row["stage"] == "application_sql_contract"
    )
    assert sha(encode(before)) == BASELINE_OBSERVATION
    old = {row["ObjectName"]: row for row in before["metadata"]["objects"]}
    legacy = json.loads(read_contract_resource("p02_observer_legacy_source.json"))
    protocol = json.loads(read_contract_resource("p02_observer_protocol.json"))
    pinned = reviewed_procedure_hashes()
    reviewed_protocol_modules()
    source_files, definitions = {}, {}
    for row in legacy["modules"]:
        if row["name"] not in PROCEDURES:
            continue
        raw = (sql_root / row["path"]).read_bytes().replace(b"\r\n", b"\n")
        assert sha(raw) == row["source_sha256"]
        body = _definition(raw, "PROCEDURE")
        assert sha(canonical_module(body).encode("utf-16-le")) == pinned[row["name"]]
        definitions[row["name"]] = body
        source_files[row["path"]] = sha(raw)
    for row in protocol["modules"]:
        raw = (sql_root / row["path"]).read_bytes()
        assert sha(raw) == row["raw_source_sha256"]
        source_files[row["path"]] = sha(raw.replace(b"\r\n", b"\n"))
        if row["name"].startswith("tr_"):
            assert _definition(raw, "TRIGGER") == row["definition"]
            definitions[row["name"]] = row["definition"]
    sequence = protocol["sequence"]
    raw = (sql_root / sequence["path"]).read_bytes()
    assert sha(raw) == sequence["raw_source_sha256"]
    assert raw.decode("utf-8-sig").replace("\r\n", "\n") == sequence["source"]
    source_files[sequence["path"]] = sha(raw.replace(b"\r\n", b"\n"))
    batches = re.split(r"(?im)^GO\s*$", sequence["source"])
    assert len(batches) == 3 and not batches[-1].strip()

    statements = [f"""/*
MigrationId: {MIGRATION}
Purpose: Install generation-bound catalogue observation over the retained D4 release
Author: Codex (local candidate; deployment separately authorised)
CreatedUtc: 2026-11-20
RequiresBackup: Yes
RiskLevel: High
Rollback: Forward Fix Only
TransactionMode: Required
DataChange: No
DataSafetyPlan: Included
DataSafetyNotes: Release-owned drained transaction; no business rows, queue or publication replay. Precommit failure rolls back. Committed state is not reinstalled.
EstimatedRowsAffected: 0 business rows
*/
SET NOCOUNT ON; SET XACT_ABORT ON; SET ANSI_NULLS ON; SET QUOTED_IDENTIFIER ON;
IF @@TRANCOUNT<>1 OR XACT_STATE()<>1
    THROW 51973,'Observer installation requires the release-owned transaction.',1;
IF DB_NAME()<>N'ROK_TRACKER'
    THROW 51973,'Exact observer installation database required.',1;
IF NOT EXISTS(SELECT 1 FROM dbo.SchemaMigrationHistory
    WHERE MigrationId=N'{D4_MIGRATION}' AND Status='Applied'
      AND LOWER(ChecksumSha256)='{D4_CHECKSUM}')
    THROW 51973,'Exact successful D4 predecessor receipt required.',1;
IF EXISTS(SELECT 1 FROM dbo.SchemaMigrationHistory WHERE MigrationId=N'{MIGRATION}')
    THROW 51973,'Observer history already exists; reconcile without replay.',1;
IF DATABASE_PRINCIPAL_ID(N'ExportLegacyEntryReader') IS NULL
    THROW 51973,'Reviewed application role is missing.',1;
"""]
    preimages = {}
    for name in sorted(AMENDED):
        row = old[name]
        assert row["AnsiNulls"] == row["QuotedIdentifier"] == 1
        assert row["ExecuteAsPrincipal"] is None and row["ObjectType"] == "P"
        preimage = sha(row["ModuleDefinition"].replace("\r\n", "\n").encode("utf-16-le"))
        preimages[name] = preimage
        statements.append(
            f"""IF NOT EXISTS(SELECT 1 FROM sys.sql_modules m JOIN sys.objects o ON o.object_id=m.object_id
    JOIN sys.schemas s ON s.schema_id=o.schema_id
    WHERE o.object_id=OBJECT_ID(N'{name}','P')
      AND m.uses_ansi_nulls=1 AND m.uses_quoted_identifier=1
      AND m.execute_as_principal_id IS NULL
      AND USER_NAME(COALESCE(o.principal_id,s.principal_id))=N'dbo'
      AND LOWER(CONVERT(varchar(64),HASHBYTES('SHA2_256',REPLACE(m.definition,NCHAR(13)+NCHAR(10),NCHAR(10))),2))='{preimage}')
    THROW 51973,'Reviewed observer predecessor body differs: {name}.',1;
"""
        )
    new_objects = sorted((PROCEDURES - AMENDED) | {"dbo.P02ObservationGeneration"})
    new_triggers = sorted(name for name in definitions if name.startswith("tr_"))
    for name in new_objects:
        statements.append(
            f"IF OBJECT_ID(N'{name}') IS NOT NULL THROW 51973,'Observer object already exists: {name}.',1;\n"
        )
    for name in new_triggers:
        statements.append(
            f"IF EXISTS(SELECT 1 FROM sys.triggers WHERE name=N'{name}') THROW 51973,'Observer trigger already exists: {name}.',1;\n"
        )
    for name in ("dbo.KVKFinalReportHeader", "dbo.MaintenanceKvkWork", "dbo.MaintenanceWork"):
        statements.append(
            f"IF EXISTS(SELECT 1 FROM sys.database_permissions WHERE class=1 AND major_id=OBJECT_ID(N'{name}') AND grantee_principal_id=DATABASE_PRINCIPAL_ID(N'ExportLegacyEntryReader') AND permission_name='ALTER') THROW 51973,'Lifecycle ALTER predecessor differs.',1;\n"
        )
    before_check = "\n".join(statements[1:])
    statements.extend(batch + "\n" for batch in batches[:-1])
    order = [
        "dbo.usp_P02BeginCatalogueMutation",
        "dbo.usp_P02EndCatalogueMutation",
        "dbo.usp_P02ReadObservationBoundary",
        *sorted(AMENDED),
        *[name for name in new_triggers if name != "tr_P02CatalogueObservation"],
    ]
    for name in order:
        statements.append("EXEC sys.sp_executesql " + literal(definitions[name]) + ";\n")
    grants = [
        row for row in legacy["grants"] if row.get("state") == "D" or row["target"] in new_objects
    ]
    assert len(grants) == 6
    for row in grants:
        assert row["database"] == "ROK_TRACKER" and row["principal"] == "ExportLegacyEntryReader"
        assert row["securable_class"] == "OBJECT"
        verb = "DENY" if row.get("state") == "D" else "GRANT"
        statements.append(
            f"{verb} {row['permission']} ON OBJECT::{row['target']} TO ExportLegacyEntryReader;\n"
        )
    statements.append(
        "EXEC sys.sp_executesql " + literal(definitions["tr_P02CatalogueObservation"]) + ";\n"
    )
    statements.append("""IF @@TRANCOUNT<>1 OR XACT_STATE()<>1
    THROW 51973,'Observer installation changed the release transaction.',1;
-- The coordinator commits its ordinary receipt before issuing a protected
-- installation binding from an acknowledged postcommit identity read.
""")
    script = "\n".join(statements).encode("utf-8")
    profile = dict(
        version=1,
        profile="p02_catalogue_observer_v1",
        migration_id=MIGRATION,
        database_collation="Latin1_General_CI_AS",
        tempdb_collation="SQL_Latin1_General_CP1_CI_AS",
        compatibility_level=160,
        requires=[dict(migration_id=D4_MIGRATION, sha256=D4_CHECKSUM, status="Applied")],
        script=dict(file=MIGRATION + ".sql", sha256=sha(script)),
        protocol_sha256=PROTOCOL_SHA256,
        legacy_source_sha256=LEGACY_SOURCE_SHA256,
        predecessor_bodies_utf16le_lf=preimages,
        source_files=source_files,
        bootstrap_generation=1,
    )
    from scripts.prepare_p02_observer_release_checks import release_checks

    before_check, after_check = release_checks(before_check, definitions, grants)
    checks = {"before": before_check.encode("utf-8"), "after": after_check.encode("utf-8")}
    profile["checks"] = {
        phase: dict(file=f"{MIGRATION}.{phase}.sql", sha256=sha(raw))
        for phase, raw in checks.items()
    }
    profile_raw = (json.dumps(profile, indent=2) + "\n").encode("utf-8")
    output.mkdir()
    for phase, raw in checks.items():
        (output / f"{MIGRATION}.{phase}.sql").write_bytes(raw)
    (output / (MIGRATION + ".sql")).write_bytes(script)
    (output / (MIGRATION + ".release.json")).write_bytes(profile_raw)
    return dict(
        status="candidate_not_release_authority",
        migration_id=MIGRATION,
        script_sha256=sha(script),
        profile_sha256=sha(profile_raw),
        production_operations=0,
        installed=False,
        coordinator_integration_completed=False,
        rollback_qualification_completed=False,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-archive", required=True)
    parser.add_argument("--sql-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.baseline_archive, args.sql_root, args.output), indent=2))
