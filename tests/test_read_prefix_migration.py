"""Execute the exact additive migration's gate using disposable SQL fixtures."""

import hashlib
import os
from pathlib import Path
import re

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("K98_READ_PREFIX_SQL") != "1", reason="Local temporary SQL opt-in"
)


@pytest.fixture
def migration():
    root = Path(os.environ["K98_READ_PREFIX_SQL_SOURCE"])
    text = (root / "migrations/20261015_003_read_prefix_history.sql").read_text(
        encoding="utf-8-sig"
    )
    body = re.search(
        r"DECLARE @Apply nvarchar\(max\)=N'(.*?)';\nEXEC sys.sp_executesql @Apply;", text, re.S
    )[1].replace("''", "'")
    return text, body


@pytest.fixture
def sql():
    import pyodbc

    connection = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\\K98DEV;DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes",
        autocommit=True,
        timeout=5,
    )
    try:
        yield connection
    finally:
        connection.close()


def test_read_prefix_migration_actual_engine_postimage_and_source_match(migration, sql):
    text, body = migration
    name, temporary = "dbo.usp_ExportReconciliationProofIssue", "#K98ReadPrefixDefinition"
    sql.execute(body.replace(name, temporary, 1))
    definition = (
        sql.execute(
            "SELECT definition FROM tempdb.sys.sql_modules WHERE object_id=OBJECT_ID('tempdb..#K98ReadPrefixDefinition')"
        )
        .fetchval()
        .replace(temporary, name, 1)
        .replace("\r\n", "\n")
    )
    blocks = re.findall(r"SET @Installed=CASE\n.*?ELSE @Installed END;", text, re.S)
    assert len(blocks) == 2 and blocks[0] == blocks[1]
    query = (
        "DECLARE @Installed nvarchar(max)=?; "
        + blocks[0]
        + " SELECT HASHBYTES('SHA2_256',CONVERT(varbinary(max),@Installed));"
    )
    expected = hashlib.sha256(
        body.replace("CREATE OR ALTER PROCEDURE", "CREATE PROCEDURE", 1).encode("utf-16-le")
    ).digest()
    assert bytes(sql.execute(query, definition).fetchval()) == expected
    assert bytes(sql.execute(query, definition + "\n-- drift").fetchval()) != expected
    assert "0x" + expected.hex() in text
    source = (
        Path(os.environ["K98_READ_PREFIX_SQL_SOURCE"])
        / "sql_schema/dbo.usp_ExportReconciliationProofIssue.StoredProcedure.sql"
    ).read_text(encoding="utf-8-sig")
    assert (
        source[source.index("CREATE PROCEDURE") :].strip().removesuffix("GO").strip()
        == body.replace("CREATE OR ALTER PROCEDURE", "CREATE PROCEDURE", 1).strip()
    )


@pytest.mark.parametrize(
    "purpose,kind,state,fresh,blocked",
    [
        ("probe", "read", "prepared", False, 0),
        ("probe", "read", "dispatch_intent", False, 0),
        ("probe", "read", "unknown", False, 0),
        ("probe", "read", "prepared", True, 1),
        ("probe", "read", "dispatch_intent", True, 1),
        ("probe", "read", "unknown", True, 1),
        ("probe", "read", "succeeded", True, 0),
        ("mutation", "mutation", "prepared", False, 1),
        ("mutation", "mutation", "unknown", False, 1),
        ("probe", "mutation", "prepared", False, 1),
        ("mutation", "read", "prepared", False, 1),
    ],
)
def test_sql_history_exception_never_accepts_unknown_writes_or_fresh_failed_reads(
    migration, sql, purpose, kind, state, fresh, blocked
):
    _, body = migration
    start = body.index("IF EXISTS (SELECT 1 FROM @Members m JOIN dbo.ExportProviderRequest r")
    end = body.index("\n  THROW", start)
    gate = body[start + len("IF ") : end]
    query = (
        """
SET NOCOUNT ON;
DECLARE @ProbeID int=?;
DECLARE @Members TABLE(StreamID int);
INSERT @Members VALUES(1);
WITH streams AS (SELECT 1 StreamID, CAST(? AS varchar(16)) Purpose),
requests AS (SELECT 1 StreamID, 2 RequestID, CAST(? AS varchar(16)) RequestKind),
events AS (SELECT 2 RequestID, CAST(? AS varchar(32)) State)
SELECT CASE WHEN """
        + gate.replace("dbo.ExportExecutionStream", "streams")
        .replace("dbo.ExportProviderRequestEvent", "events")
        .replace("dbo.ExportProviderRequest", "requests")
        + " THEN 1 ELSE 0 END;"
    )
    assert sql.execute(query, 1 if fresh else 9, purpose, kind, state).fetchval() == blocked
