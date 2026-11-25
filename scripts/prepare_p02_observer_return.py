"""Prepare the exact P02 return/reupgrade pair without SQL or release authority.

Return restores the three retained D4 procedures and removes four observer
triggers and six permission amendments. The sequence and three inert helpers
remain, preserving the committed observer incarnation and every history row.
Reupgrade restores those same reviewed hooks; it never repeats observer install.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
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
from scripts.prepare_p02_observer_migration import literal
from scripts.prepare_p02_observer_release_checks import release_checks
from services.application_observation_fingerprint import PROCEDURES, TRIGGERS
from services.catalogue_observation_contract import PROTOCOL_SHA256
from services.export_execution_protocol import encode
from services.export_observer_contract import MIGRATION_ID, PROFILE_SHA256

RETURN_ID = "20261123_001_p02_observer_return"
REUPGRADE_ID = "20261123_002_p02_observer_reupgrade"
PROFILE = "p02_observer_return_v1"
TRIGGER_NAMES = (*sorted(TRIGGERS), "tr_P02CatalogueObservation")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def material(baseline_archive, sql_root):
    """Authenticate historical bodies and the complete committed forward package."""
    raw = Path(baseline_archive).read_bytes()
    require(sha(raw) == BASELINE_ARCHIVE, "Exact retained predecessor archive required")
    with zipfile.ZipFile(baseline_archive) as archive:
        rows = archive.read("run-01/observations.jsonl")
    require(sha(rows) == BASELINE_ROWS, "Exact retained observation rows required")
    observations = [json.loads(line) for line in rows.splitlines()]
    before = next(
        row["observation"] for row in observations if row["stage"] == "application_sql_contract"
    )
    require(sha(encode(before)) == BASELINE_OBSERVATION, "Predecessor observation differs")
    objects = {row["ObjectName"]: row for row in before["metadata"]["objects"]}
    old = {}
    for name in sorted(AMENDED):
        body = objects[name]["ModuleDefinition"]
        require(
            body.startswith("CREATE   PROCEDURE ") and "\r" not in body,
            "Exact native predecessor module header/LF representation required",
        )
        # SQL stores CREATE OR ALTER as CREATE plus three spaces. This exact
        # transport restores the historical body while retaining object IDs/grants.
        old[name] = "CREATE OR ALTER " + body[len("CREATE   ") :]

    sql_root = Path(sql_root)
    raw = (sql_root / "migrations" / (MIGRATION_ID + ".release.json")).read_bytes()
    require(sha(raw) == PROFILE_SHA256, "Exact forward observer profile required")
    profile = json.loads(raw)
    for item in (profile["script"], *profile["checks"].values()):
        require(
            sha((sql_root / "migrations" / item["file"]).read_bytes()) == item["sha256"],
            "Forward package member differs: " + item["file"],
        )
    for path, digest in profile["source_files"].items():
        require(
            sha((sql_root / path).read_bytes().replace(b"\r\n", b"\n")) == digest,
            "Reviewed SQL source differs: " + path,
        )
    definitions = {}
    for name in sorted(PROCEDURES):
        path = sql_root / "sql_schema" / (name + ".StoredProcedure.sql")
        definitions[name] = _definition(path.read_bytes(), "PROCEDURE")
    for name in TRIGGER_NAMES:
        filename = (
            name + ".DatabaseTrigger.sql"
            if name == "tr_P02CatalogueObservation"
            else "dbo." + name + ".Trigger.sql"
        )
        definitions[name] = _definition(
            (sql_root / "sql_schema" / filename).read_bytes(), "TRIGGER"
        )
    return profile, old, definitions


GUARDS = """SET NOCOUNT ON; SET XACT_ABORT ON; SET ANSI_NULLS ON; SET QUOTED_IDENTIFIER ON;
IF DB_NAME()<>N'ROK_TRACKER' OR @@TRANCOUNT<>1 OR XACT_STATE()<>1
 THROW 51977,'Exact target and one release-owned transaction required.',1;
IF COALESCE(APPLOCK_MODE(N'public',N'K98_Module_Release_v1',N'Session'),N'NoLock')<>N'Exclusive'
 THROW 51977,'Existing release coordinator must own this transition.',1;
DECLARE @p02_return_lock int;
EXEC dbo.ACQUIRE_KS4_IMPORT_LOCK @LockTimeout=0,@LockResult=@p02_return_lock OUTPUT;
IF @p02_return_lock IS NULL OR @p02_return_lock NOT IN (0,1)
 THROW 51977,'Import writer is active; preserve and stop.',1;
EXEC @p02_return_lock=sys.sp_getapplock @Resource=N'K98:maintenance-schema:v1',
 @LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=0;
IF @p02_return_lock IS NULL OR @p02_return_lock NOT IN (0,1)
 THROW 51977,'Maintenance/observer owner is active; preserve and stop.',1;
EXEC @p02_return_lock=sys.sp_getapplock @Resource=N'k98-legacy-output-snapshot',
 @LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=0;
IF @p02_return_lock IS NULL OR @p02_return_lock NOT IN (0,1)
 THROW 51977,'Legacy output owner is active; preserve and stop.',1;
IF EXISTS(SELECT 1 FROM dbo.ExportResource WITH (UPDLOCK,HOLDLOCK)
 WHERE OwnerID IS NOT NULL OR ActiveJobID IS NOT NULL OR ActivePreparationID IS NOT NULL
 OR ActiveOutputOperationID IS NOT NULL OR BlockedReason IS NOT NULL)
 THROW 51977,'Durable owner or hold remains; preserve and stop.',1;
IF COALESCE(APPLOCK_TEST(N'public',N'K98:catalogue-mutation:v1',N'Exclusive',N'Transaction'),-999)<>1
 THROW 51977,'Catalogue mutation owner remains; preserve and stop.',1;
-- The outer release gate must keep every enrolled actor drained. These SQL
-- checks do not prove absence of previous business effects or authorise return.
EXEC dbo.usp_P02BeginCatalogueMutation @Owner='Transaction';
"""


def _parked_check(old, definitions):
    retained = {name: old.get(name, definitions[name]) for name in sorted(PROCEDURES)}
    _, check = release_checks("", retained, [])
    statements = [check]
    for name in TRIGGER_NAMES:
        statements.append(
            f"IF EXISTS(SELECT 1 FROM sys.triggers WHERE name=N'{name}')\n"
            " THROW 51977,'Observer hook remains in returned state.',1;\n"
        )
    for name in sorted(PROCEDURES - AMENDED):
        statements.append(
            f"IF EXISTS(SELECT 1 FROM sys.database_permissions WHERE class=1 "
            f"AND major_id=OBJECT_ID(N'{name}') AND minor_id=0 "
            "AND grantee_principal_id=DATABASE_PRINCIPAL_ID(N'ExportLegacyEntryReader'))\n"
            " THROW 51977,'Returned observer helper still has explicit role rights.',1;\n"
        )
    for name in sorted(TRIGGERS.values()):
        statements.append(
            f"IF EXISTS(SELECT 1 FROM sys.database_permissions WHERE class=1 "
            f"AND major_id=OBJECT_ID(N'{name}') AND minor_id=0 "
            "AND grantee_principal_id=DATABASE_PRINCIPAL_ID(N'ExportLegacyEntryReader') "
            "AND permission_name='ALTER')\n"
            " THROW 51977,'Returned lifecycle permission differs from predecessor.',1;\n"
        )
    # Match the exact historical text, not only the observer's normalized form.
    for name, body in sorted(old.items()):
        stored = "CREATE   " + body[len("CREATE OR ALTER ") :]
        digest = sha(stored.encode("utf-16-le"))
        statements.append(
            "IF LOWER(CONVERT(varchar(64),HASHBYTES('SHA2_256',"
            f"OBJECT_DEFINITION(OBJECT_ID(N'{name}'))),2))<>'{digest}'\n"
            " THROW 51977,'Exact historical procedure bytes were not restored.',1;\n"
        )
    return "\n".join(statements)


def build(baseline_archive, sql_root):
    """Pure generation: no expected state is learned from a live database."""
    forward, old, definitions = material(baseline_archive, sql_root)
    on = (Path(sql_root) / "migrations" / forward["checks"]["after"]["file"]).read_bytes()
    parked = _parked_check(old, definitions).encode("utf-8")
    bodies = {}
    off = [GUARDS, "DROP TRIGGER tr_P02CatalogueObservation ON DATABASE;\n"]
    for name in sorted(TRIGGERS):
        off.append(f"DROP TRIGGER dbo.{name};\n")
    off.extend("EXEC sys.sp_executesql " + literal(old[name]) + ";\n" for name in sorted(old))
    for name in sorted(PROCEDURES - AMENDED):
        off.append(f"REVOKE EXECUTE ON OBJECT::{name} FROM ExportLegacyEntryReader;\n")
    for name in sorted(TRIGGERS.values()):
        off.append(f"REVOKE ALTER ON OBJECT::{name} FROM ExportLegacyEntryReader;\n")
    bodies[RETURN_ID] = "\n".join(off)

    restore = [GUARDS]
    for name in (*sorted(AMENDED), *TRIGGER_NAMES):
        restore.append("EXEC sys.sp_executesql " + literal(definitions[name]) + ";\n")
    for name in sorted(PROCEDURES - AMENDED):
        restore.append(f"GRANT EXECUTE ON OBJECT::{name} TO ExportLegacyEntryReader;\n")
    for name in sorted(TRIGGERS.values()):
        restore.append(f"DENY ALTER ON OBJECT::{name} TO ExportLegacyEntryReader;\n")
    bodies[REUPGRADE_ID] = "\n".join(restore)

    files, profiles = {}, {}
    for identifier, action, before, after in (
        (RETURN_ID, "return", on, parked),
        (REUPGRADE_ID, "reupgrade", parked, on),
    ):
        header = f"""/*
MigrationId: {identifier}
Purpose: Exact P02 observer {action}; preserve original incarnation and pending work
Author: Codex
CreatedUtc: 2026-11-23
RequiresBackup: Yes
RiskLevel: High
Rollback: Manual
RollbackScript: N/A - paired operator-controlled release; never repeat a committed identity
TransactionMode: Required
DataChange: No
DataSafetyPlan: Included
DataSafetyNotes: Existing outer drain and no-business return window mandatory. No business DML, sequence replacement, original receipt edit, restore or producer replay.
EstimatedRowsAffected: 0 business rows
PreValidationQuery: {identifier}.before.sql
PostValidationQuery: {identifier}.after.sql
RelatedBotPR: Local candidate; not published
RelatedSQLPR: Local candidate; not published
*/
"""
        script = (header + bodies[identifier]).encode("utf-8")
        profile: dict[str, Any] = dict(
            version=1,
            profile=PROFILE,
            migration_id=identifier,
            action=action,
            database_collation=forward["database_collation"],
            tempdb_collation=forward["tempdb_collation"],
            compatibility_level=forward["compatibility_level"],
            requires=[dict(migration_id=MIGRATION_ID, sha256=PROFILE_SHA256, status="Applied")],
            protocol_sha256=PROTOCOL_SHA256,
            script=dict(file=identifier + ".sql", sha256=sha(script)),
            checks={},
        )
        if action == "reupgrade":
            profile["requires"].append(
                dict(migration_id=RETURN_ID, sha256=profiles[RETURN_ID], status="Applied")
            )
        files[identifier + ".sql"] = script
        for phase, raw in (("before", before), ("after", after)):
            name = identifier + "." + phase + ".sql"
            profile["checks"][phase] = dict(file=name, sha256=sha(raw))
            files[name] = raw
        raw = (json.dumps(profile, indent=2) + "\n").encode("utf-8")
        files[identifier + ".release.json"] = raw
        profiles[identifier] = sha(raw)
    return files, dict(
        profiles=profiles,
        preserved_objects=sorted((PROCEDURES - AMENDED) | {"dbo.P02ObservationGeneration"}),
        restored_procedures=sorted(AMENDED),
        removed_then_restored_triggers=list(TRIGGER_NAMES),
        original_forward_profile_sha256=PROFILE_SHA256,
        historical_archive_sha256=BASELINE_ARCHIVE,
        native_qualified=False,
        deployable=False,
    )


def prepare(baseline_archive, sql_root, output):
    files, receipt = build(baseline_archive, sql_root)
    output = Path(output)
    output.mkdir(exist_ok=False)
    for name, raw in files.items():
        (output / name).write_bytes(raw)
    (output / "preparation.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-archive", required=True)
    parser.add_argument("--sql-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.baseline_archive, args.sql_root, args.output), indent=2))
