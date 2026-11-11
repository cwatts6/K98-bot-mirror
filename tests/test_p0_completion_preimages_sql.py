"""Exercise exact P0 metadata guards on an explicitly prepared local clone.

The fixture is prepared separately from reviewed source and retained grants.
This test never creates production permissions or executes business procedures.
"""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from uuid import uuid4

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("K98_P0_PREIMAGE_SQL_TESTS") != "1", reason="Prepared local SQL clone opt-in"
)


def test_exact_preimages_preserve_grants_and_refuse_drift(tmp_path):
    pyodbc = pytest.importorskip("pyodbc")
    database = os.environ["K98_P0_PREIMAGE_DATABASE"]
    assert re.fullmatch(r"K98_P0_Completion_[a-f0-9]{12}", database)
    sql_repo = Path(os.environ["K98_P0_PREIMAGE_SQL_REPO"])
    root = Path(__file__).resolve().parents[1]
    spec = json.loads((root / "scripts/p0a_release_spec.json").read_text())
    sql = spec["sql"]
    sha = lambda raw: hashlib.sha256(raw).hexdigest()
    for member in sql["members"]:
        raw = subprocess.check_output(
            ["git", "-C", str(sql_repo), "show", sql["commit"] + ":" + member["path"]]
        )
        assert sha(raw) == member["sha256"]
        (tmp_path / Path(member["path"]).name).write_bytes(raw)
    profile = deepcopy(sql["profile"])
    profile.update(
        database_collation="Latin1_General_CI_AS",
        tempdb_collation="SQL_Latin1_General_CP1_CI_AS",
        compatibility_level=160,
    )
    profile_path = tmp_path / (profile["migration_id"] + ".release.json")
    release = str(uuid4())
    connection = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER=lpc:localhost\\K98DEV;DATABASE="
        + database
        + ";Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes",
        autocommit=True,
        timeout=5,
    )
    connection.timeout = 15

    def execute(text):
        cursor = connection.cursor()
        try:
            cursor.execute(text)
            while cursor.nextset():
                pass
        finally:
            cursor.close()

    def history():
        return list(
            connection.execute(
                "SELECT MigrationId,ChecksumSha256,GitCommit,DeploymentId,Status,AppliedAtUtc "
                "FROM dbo.SchemaMigrationHistory WHERE MigrationId IN (?,?) ORDER BY MigrationId",
                profile["migration_id"],
                profile["scripts"][0]["id"],
            )
        )

    def run(operation, expected=0, selected=None):
        raw = (json.dumps(selected or profile, sort_keys=True, indent=2) + "\n").encode()
        profile_path.write_bytes(raw)
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(tmp_path / "Deploy-SqlMigration.ps1"),
                "-ServerName",
                "lpc:localhost\\K98DEV",
                "-DatabaseName",
                database,
                "-MigrationId",
                profile["migration_id"],
                "-ProfilePath",
                str(profile_path),
                "-ProfileSHA256",
                sha(raw),
                "-ExpectedCommit",
                sql["commit"],
                "-ReleaseId",
                release,
                "-Operation",
                operation,
            ],
            capture_output=True,
            text=True,
            timeout=90,
        )
        assert result.returncode == expected, result.stdout + result.stderr
        return result.stdout + result.stderr

    try:
        assert tuple(
            connection.execute(
                "SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')),DB_NAME()"
            ).fetchone()
        ) == ("9SX2VF4\\K98DEV", database)
        assert history() == []
        previous = deepcopy(profile)
        old = {
            "dbo.UPDATE_ALL2": "78d4db9dec9a22601631651a01043acf7c7c2b1a8944ec211149926b30417759",
            "dbo.usp_update_stats": "49471caec57e50a88d49745f4f9ac44a623c98eeafe3e4c8a0b56507ee92af44",
        }
        for row in previous["images"]:
            if row["name"] in old:
                row["before"] = old[row["name"]]
        refused = run("Preflight", 20, previous)
        assert "Recovery preimage differs" in refused
        assert all(name in refused for name in old)
        assert history() == []
        run("Preflight")
        mutations = [
            (
                "GRANT ALTER ON OBJECT::dbo.UPDATE_ALL2 TO SHEETS_USER;",
                "REVOKE ALTER ON OBJECT::dbo.UPDATE_ALL2 FROM SHEETS_USER;",
            ),
            (
                "REVOKE EXECUTE ON OBJECT::dbo.usp_update_stats FROM ImportProcUser;",
                "GRANT EXECUTE ON OBJECT::dbo.usp_update_stats TO ImportProcUser;",
            ),
        ]
        for change, restore in mutations:
            execute(change)
            try:
                assert "Recovery preimage differs" in run("Preflight", 20)
                assert history() == []
            finally:
                execute(restore)
            run("Preflight")
        original = connection.execute(
            "SELECT OBJECT_DEFINITION(OBJECT_ID(N'dbo.UPDATE_ALL2'))"
        ).fetchval()
        alter = re.sub(
            r"^(?:CREATE OR ALTER|CREATE|ALTER)\s+PROCEDURE", "ALTER PROCEDURE", original
        )
        execute(alter + "\n-- unexpected fixture-only body change")
        try:
            assert "Recovery preimage differs" in run("Preflight", 20)
        finally:
            execute(alter)
        run("Preflight")
        run("Verify", 10)
        run("Apply")
        run("Verify")
        receipts = history()
        assert len(receipts) == 2
        run("Apply")
        run("Verify")
        assert history() == receipts
        for name, principal in [
            ("dbo.UPDATE_ALL2", "SHEETS_USER"),
            ("dbo.usp_update_stats", "SHEETS_USER"),
            ("dbo.usp_update_stats", "ImportProcUser"),
        ]:
            assert (
                connection.execute(
                    "SELECT COUNT(*) FROM sys.database_permissions WHERE class=1 "
                    "AND major_id=OBJECT_ID(?) AND grantee_principal_id=USER_ID(?) "
                    "AND minor_id=0 AND type='EX' AND state='G'",
                    name,
                    principal,
                ).fetchval()
                == 1
            )
        execute("REVOKE EXECUTE ON OBJECT::dbo.usp_update_stats FROM SHEETS_USER;")
        try:
            assert "Recovery postimage differs" in run("Verify", 20)
        finally:
            execute("GRANT EXECUTE ON OBJECT::dbo.usp_update_stats TO SHEETS_USER;")
        run("Verify")
        assert history() == receipts
    finally:
        connection.close()
