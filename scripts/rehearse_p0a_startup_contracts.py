"""Check recovery startup permissions on a fresh retained local SQL database.

This qualification tool uses the separately reviewed SQL fixture and literal
migrations. It never accepts a server/database argument or produces deployable
expected contracts from live production state.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

BOT_ROOT = Path(__file__).resolve().parents[1]
SQL_FIXTURE_COMMIT = "5e5fdb8151c539d8bd12b8df17753526218b5987"


def load_fixture(root, name):
    path = root / "validation" / (name + ".py")
    expected = subprocess.check_output(
        ["git", "-C", str(root), "show", SQL_FIXTURE_COMMIT + ":validation/" + path.name]
    ).replace(b"\r\n", b"\n")
    if path.read_bytes().replace(b"\r\n", b"\n") != expected:
        raise ValueError("Reviewed SQL fixture differs: " + name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql-source", type=Path, required=True)
    parser.add_argument("--allow-disposable-sql", action="store_true", required=True)
    args = parser.parse_args()
    root = args.sql_source.resolve(strict=True)
    sys.path.insert(0, str(BOT_ROOT))
    from services.export_execution_dal import (
        application_installation_snapshot,
        installation_permissions,
    )

    fixture = load_fixture(root, "rehearse_guided_recovery_migrations")
    release = load_fixture(root, "rehearse_guided_recovery_release")
    output = Path(tempfile.mkdtemp(prefix="K98_P0a_Startup_"))

    def qualify(connection, report, report_path):
        release.install_application_baseline(connection)
        history = ("KVK.SourceExportHistory", "KVK.SourceExportHistoryRow")
        for name in history:
            # Both tables belong to the reviewed baseline fixture's FK closure.
            assert connection.execute("SELECT OBJECT_ID(?, 'U')", name).fetchval() is not None
            fixture.execute(
                connection,
                f"GRANT INSERT,SELECT ON OBJECT::{name} TO S11_ExportApplication;",
            )
        fixture.execute(
            connection,
            "GRANT UPDATE ON OBJECT::KVK.SourceExportHistory(AttemptCount,ContentHash) TO S11_ExportApplication;",
        )
        scope = sorted([*release.NAMES, *history])
        # Exact existing schema privileges in the independently reviewed legacy
        # plan. Exercise their inheritance together with the new object DENYs.
        fixture.execute(connection, "GRANT VIEW DEFINITION TO S11_ExportApplication;")
        fixture.execute(
            connection,
            "GRANT SELECT ON OBJECT::sys.sql_expression_dependencies TO S11_ExportApplication;",
        )
        fixture.execute(
            connection,
            "GRANT ALTER,INSERT,SELECT ON SCHEMA::dbo TO ExportLegacyEntryReader;",
        )
        before = application_installation_snapshot(connection.cursor(), scope=scope)
        for mid in fixture.MIGRATIONS:
            fixture.execute(connection, fixture.source(fixture.HEAD, "migrations/" + mid + ".sql"))
        for name, permissions in release.APPLICATION_GRANTS.items():
            fixture.execute(
                connection,
                f"GRANT {','.join(permissions)} ON OBJECT::{name} TO S11_ExportApplication;",
            )
        after = application_installation_snapshot(connection.cursor(), scope=scope)
        old = {row["ObjectName"] for row in before["metadata"]["objects"]}
        new = {row["ObjectName"] for row in after["metadata"]["objects"]} - old
        assert len(new) == 16
        expected = installation_permissions("application", direct=True)
        fixture.execute(connection, "EXECUTE AS USER='S11_ExportApplication';")
        mismatches = []
        checked = 0
        try:
            observed = application_installation_snapshot(connection.cursor(), scope=scope)
            for (name, column, permission), allowed in expected.items():
                if name not in new:
                    continue
                assert column is None
                actual = connection.execute(
                    "SELECT HAS_PERMS_BY_NAME(?,'OBJECT',?)", name, permission
                ).fetchval()
                checked += 1
                if actual != allowed:
                    mismatches.append(
                        dict(object=name, permission=permission, expected=allowed, actual=actual)
                    )
            for row in after["metadata"]["columns"]:
                name = row["ObjectName"]
                if name not in new:
                    continue
                for permission in ("SELECT", "UPDATE"):
                    actual = connection.execute(
                        "SELECT HAS_PERMS_BY_NAME(?,'OBJECT',?,?,'COLUMN')",
                        name,
                        permission,
                        row["ColumnName"],
                    ).fetchval()
                    checked += 1
                    allowed = expected[name, None, permission]
                    if actual != allowed:
                        mismatches.append(
                            dict(
                                object=name,
                                column=row["ColumnName"],
                                permission=permission,
                                expected=allowed,
                                actual=actual,
                            )
                        )
        finally:
            fixture.execute(connection, "REVERT;")
        for name, value in (("before", before), ("after", after), ("application", observed)):
            (output / (name + ".json")).write_text(json.dumps(value, indent=2), encoding="utf-8")
        result = dict(
            database=fixture.DATABASE,
            checked=checked,
            new_objects=sorted(new),
            mismatches=mismatches,
            production_changed=False,
        )
        (output / "qualification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result), flush=True)
        report.update(startup_permission_checks=checked, artifacts=str(output))
        assert not mismatches, mismatches

    sys.argv = [sys.argv[0], "--allow-disposable-sql"]
    fixture.main(qualify)
    print(str(output), flush=True)


if __name__ == "__main__":
    main()
