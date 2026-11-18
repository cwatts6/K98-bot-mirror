"""Opt-in migration metadata test; creates only a session-local temporary procedure."""

import hashlib
import os
from pathlib import Path
import re

import pytest


@pytest.mark.skipif(os.getenv("K98_CONFIG_RECOVERY_SQL") != "1", reason="Local SQL fixture opt-in")
def test_actual_engine_definition_matches_migration_postimage_after_narrow_normalization():
    import pyodbc

    root = Path(os.environ["K98_CONFIG_RECOVERY_SQL_SOURCE"])
    migration = (root / "migrations/20261015_001_failed_read_history.sql").read_text(
        encoding="utf-8-sig"
    )
    body = re.search(
        r"DECLARE @Apply nvarchar\(max\)=N'(.*?)';\nEXEC sys.sp_executesql @Apply;", migration, re.S
    )[1].replace("''", "'")
    blocks = re.findall(r"SET @Installed=CASE\n.*?ELSE @Installed END;", migration, re.S)
    assert len(blocks) == 2 and blocks[0] == blocks[1]
    expected = bytes.fromhex("b3bcf377f9c5710042134e0b08c71219ee4451ff810b8c5d58e85f778a72a4b8")
    name = "dbo.usp_ExportReconciliationProofIssue"
    temporary = "#K98ReadHistoryDefinition"
    connection = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\\K98DEV;DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes",
        autocommit=True,
        timeout=5,
    )
    try:
        connection.execute(body.replace(name, temporary, 1))
        definition = connection.execute(
            "SELECT definition FROM tempdb.sys.sql_modules WHERE object_id=OBJECT_ID('tempdb..#K98ReadHistoryDefinition')"
        ).fetchval()
        definition = definition.replace(temporary, name, 1).replace("\r\n", "\n")
        assert hashlib.sha256(definition.encode("utf-16-le")).digest() != expected
        query = (
            "DECLARE @Installed nvarchar(max)=?; "
            + blocks[0]
            + " SELECT HASHBYTES('SHA2_256',CONVERT(varbinary(max),@Installed));"
        )
        assert bytes(connection.execute(query, definition).fetchval()) == expected
        assert (
            bytes(connection.execute(query, definition + "\n-- changed body").fetchval())
            != expected
        )
    finally:
        connection.close()
