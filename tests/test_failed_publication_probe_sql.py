"""Execute the additive failed-job probe gate and exact module postimage in temp SQL."""

import hashlib
import os
from pathlib import Path
import re

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("K98_ABSENT_PROBE_SQL") != "1", reason="Explicit local temporary SQL opt-in"
)


@pytest.fixture
def migration():
    root = Path(os.environ["K98_ABSENT_PROBE_SQL_SOURCE"])
    text = (root / "migrations/20261015_004_failed_publication_probe.sql").read_text(
        encoding="utf-8-sig"
    )
    body = re.search(
        r"DECLARE @Apply nvarchar\(max\)=N'(.*?)';\nEXEC sys.sp_executesql @Apply;", text, re.S
    )[1].replace("''", "'")
    return root, text, body


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


def test_failed_job_probe_exact_engine_postimage_and_source(migration, sql):
    root, text, body = migration
    name, temporary = "dbo.usp_ExportExecutionStreamTransition", "#K98FailedJobProbe"
    sql.execute(body.replace(name, temporary, 1))
    definition = (
        sql.execute(
            "SELECT definition FROM tempdb.sys.sql_modules WHERE object_id=OBJECT_ID('tempdb..#K98FailedJobProbe')"
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
    source = (root / ("sql_schema/" + name + ".StoredProcedure.sql")).read_text(
        encoding="utf-8-sig"
    )
    assert (
        source[source.index("CREATE PROCEDURE") :].strip().removesuffix("GO").strip()
        == body.replace("CREATE OR ALTER PROCEDURE", "CREATE PROCEDURE", 1).strip()
    )


@pytest.mark.parametrize(
    "purpose,state,allowed",
    [
        ("probe", "failed", True),
        ("mutation", "failed", False),
        ("probe", "uncertain", True),
        ("mutation", "uncertain", False),
        ("probe", "confirmed", True),
        ("mutation", "confirmed", False),
        ("mutation", "running", True),
        ("probe", "running", True),
        ("probe", "cancelled", False),
        ("probe", "ready", False),
    ],
)
def test_actual_sql_state_gate_never_revives_mutation(migration, sql, purpose, state, allowed):
    _, _, body = migration
    gate = re.search(r"AND \(\(@Purpose='mutation' AND State='running'\).*?\n", body)[0].strip()[4:]
    query = (
        "DECLARE @Purpose varchar(16)=?; WITH j AS (SELECT CAST(? AS varchar(32)) State) "
        "SELECT CASE WHEN " + gate + " THEN 1 ELSE 0 END FROM j"
    )
    assert bool(sql.execute(query, purpose, state).fetchval()) is allowed
