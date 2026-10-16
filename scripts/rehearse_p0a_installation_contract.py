"""Qualify the full fixed export installation contract on fresh local SQL.

Uses immutable SQL source and independently reviewed expected metadata. Only the
local database identity is rebound. Does not derive expected hashes from SQL,
deploy to production, or claim the separate whole-application/legacy contracts.
"""

import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import sys
import tempfile
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.p0a_release import specification
from scripts.rehearse_p0a_startup_contracts import load_fixture
from services.export_execution_dal import (
    INSTALLATION_OBJECTS,
    ExportExecutionDAL,
    installation_migrations,
)
from services.export_runtime_composition import verify_installation_contract
from services.export_sql_direct_permissions import application_grant_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql-source", type=Path, required=True)
    parser.add_argument("--allow-disposable-sql", action="store_true", required=True)
    parser.add_argument("--business-output", action="store_true")
    args = parser.parse_args()
    fixture = load_fixture(args.sql_source, "rehearse_guided_recovery_migrations")
    release = load_fixture(args.sql_source, "rehearse_guided_recovery_release")
    original_source = fixture.source

    def historical_shape(revision, path):
        raw = original_source(revision, path)
        if revision == fixture.BASE and path == "sql_schema/dbo.ExportResource.Table.sql":
            # The historical preparation migration appended this column after
            # Version. The consolidated reference snapshot groups it earlier.
            # Reconstruct that documented installation ordering with identical
            # authoritative declarations, types, constraints and indexes.
            column = "    ActivePreparationID uniqueidentifier NULL,\n"
            anchor = "    Version bigint NOT NULL,\n"
            assert raw.count(column) == raw.count(anchor) == 1
            raw = raw.replace(column, "").replace(anchor, anchor + column)
        return raw

    fixture.source = historical_shape
    approved = deepcopy(specification()["contracts"]["sql_contract"]["after"])
    approved.update(server=fixture.EXPECTED_SERVER, database=fixture.DATABASE)
    output = Path(tempfile.mkdtemp(prefix="K98_P0a_Installation_"))
    login = "K98_P0a_Qualification_" + uuid4().hex
    password = uuid4().hex + "_Aa1!"
    assert re.fullmatch(r"K98_P0a_Qualification_[a-f0-9]{32}", login)

    def qualify(connection, report, report_path):
        original_execute = fixture.execute
        mapped = []

        def mapped_user(c, sql):
            declaration = "CREATE USER S11_ExportApplication WITHOUT LOGIN;"
            if declaration in sql:
                assert not mapped and sql.count(declaration) == 1
                mapped.append(True)
                sql = sql.replace(
                    declaration, f"CREATE USER S11_ExportApplication FOR LOGIN [{login}];"
                )
            return original_execute(c, sql)

        fixture.execute = mapped_user
        try:
            release.install_application_baseline(connection)
        finally:
            fixture.execute = original_execute
        assert mapped == [True]
        # Restore all existing evidence-role statements for this fixed object
        # set from the two original installers, not from observed permissions.
        for mid in (
            "20261001_004_export_execution_evidence_installation",
            "20261001_005_manual_export_registration_installation",
        ):
            raw = original_source(fixture.BASE, "migrations/" + mid + ".sql")
            for line in raw.splitlines():
                match = re.fullmatch(
                    r"(?:GRANT|DENY) [A-Z ,]+ ON OBJECT::([A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*) TO (?:public|ExportExecutionAuthority|ExportExecutionReader);",
                    line,
                )
                if match and match[1] in INSTALLATION_OBJECTS:
                    fixture.execute(connection, line)
        for mid in fixture.MIGRATIONS:
            fixture.execute(connection, original_source(fixture.HEAD, "migrations/" + mid + ".sql"))
        fixture.execute(
            connection,
            "GRANT VIEW DEFINITION TO S11_ExportApplication; GRANT SELECT ON OBJECT::dbo.SchemaMigrationHistory TO S11_ExportApplication; GRANT ALTER,INSERT,SELECT ON SCHEMA::dbo TO ExportLegacyEntryReader;",
        )
        for row in application_grant_rows():
            name, permission = row["TargetName"], row["PermissionName"]
            if row["SecurableClass"] != "OBJECT" or name not in INSTALLATION_OBJECTS:
                continue
            assert row["ColumnName"] is None
            assert re.fullmatch(r"(?:dbo|KVK)\.[A-Za-z0-9_]+", name)
            assert permission in {"SELECT", "INSERT", "UPDATE", "DELETE", "EXECUTE"}
            fixture.execute(
                connection, f"GRANT {permission} ON OBJECT::{name} TO S11_ExportApplication;"
            )
        # Synthetic baseline receipts belong only to this fresh qualification
        # database. Literal new migration bodies above must finish successfully.
        for mid, checksum in approved["migration_hashes"].items():
            connection.execute(
                "INSERT dbo.SchemaMigrationHistory(MigrationId,MigrationFile,ChecksumSha256,AppliedAtUtc,Status) VALUES(?,?,?,SYSUTCDATETIME(),'Applied')",
                mid,
                mid + ".sql",
                checksum,
            )

        # A database-only EXECUTE AS USER token cannot enumerate server database
        # permissions. Use a fresh disposable login so the unchanged complete
        # visibility/impersonation query runs under an actual restricted login.
        def restricted():
            c = fixture.connect(fixture.DATABASE)
            try:
                fixture.execute(c, f"EXECUTE AS LOGIN='{login}';")
            except BaseException:
                c.close()
                raise
            return c

        observed = ExportExecutionDAL(restricted).installation_snapshot(
            migrations=installation_migrations(approved)
        )
        (output / "actual-installation.json").write_text(
            json.dumps(observed, indent=2), encoding="utf-8"
        )
        (output / "reviewed-contract.json").write_text(
            json.dumps(approved, indent=2), encoding="utf-8"
        )
        verify_installation_contract(observed, approved)
        result = dict(
            status="FULL_EXPORT_INSTALLATION_CONTRACT_VERIFIED",
            database=fixture.DATABASE,
            objects=len(observed["metadata"]["objects"]),
            columns=len(observed["metadata"]["columns"]),
            permissions=len(observed["permissions"]),
            metadata_hash=approved["metadata_hash"],
            production_changed=False,
            receipts="SYNTHETIC_BASELINE_AND_SUCCESSFULLY_EXECUTED_NEW_MIGRATIONS",
            application_and_legacy_contracts="SEPARATE_QUALIFICATION_REQUIRED",
            output=str(output),
        )
        (output / "qualification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        report.update(installation_contract=result)
        print(json.dumps(result), flush=True)
        if args.business_output:
            from scripts.rehearse_p0a_target_business import qualify as qualify_business

            business = qualify_business(fixture, connection)
            report["target_business"] = business
            (output / "target-business.json").write_text(
                json.dumps(business, indent=2), encoding="utf-8"
            )
            print(json.dumps(business), flush=True)

    sys.argv = [sys.argv[0], "--allow-disposable-sql"]
    # Must precede the first connection, including temporary login creation.
    # Otherwise an impersonated pooled session can retain the disposable login.
    fixture.pyodbc.pooling = False
    with fixture.connect("master") as master:
        fixture.execute(
            master, f"CREATE LOGIN [{login}] WITH PASSWORD='{password}',CHECK_POLICY=ON;"
        )
    try:
        fixture.main(qualify)
    finally:
        with fixture.connect("master") as master:
            fixture.execute(master, f"DROP LOGIN [{login}];")


if __name__ == "__main__":
    main()
