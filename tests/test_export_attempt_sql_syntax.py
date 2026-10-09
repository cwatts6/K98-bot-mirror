"""Opt-in read-only SQL Server grammar regression; never executes the INSERT."""

from contextlib import contextmanager
import os
from uuid import uuid4

import pytest

from services.export_coordination_dal import Claim
from tests.test_kvk_export_coordination import Cursor, part, scripted


def _attempt_part_statement(monkeypatch):
    cursor = Cursor(singles=[None])
    dal = scripted(monkeypatch, cursor)
    claim = Claim(str(uuid4()), "acct", str(uuid4()), 2, 2, (("destination:file-a", 1),))

    @contextmanager
    def owned(_):
        yield cursor, dict(ConsumerKind="scan_data", PoolEpoch=None)

    monkeypatch.setattr(dal, "_owned", owned)
    dal.begin_attempt(claim, {"export_key": "x"}, [part()])
    queries = [
        (query, parameters)
        for query, parameters in cursor.calls
        if query.startswith("INSERT dbo.ExportAttemptPart")
    ]
    assert len(queries) == 1
    return queries[0]


def test_actual_attempt_part_statement_quotes_row_count_and_binds_value(monkeypatch):
    """Runs in ordinary CI without a database; exercises the emitted DAL statement."""
    query, parameters = _attempt_part_statement(monkeypatch)
    columns = query.split("(", 1)[1].split(")", 1)[0].split(",")
    assert columns[7] == "[RowCount]"
    assert len(parameters) == query.count("?") == 9
    assert parameters[7] == part()["rows"]


@pytest.mark.skipif(
    os.environ.get("K98_READ_ONLY_SQL_COMPILER") != "LOCAL_TEMPDB_COMPILE_ONLY",
    reason="Development LPC compiler only; ordinary CI/production runs skip; no DML",
)
def test_actual_attempt_part_insert_compiles_and_binds_row_count(monkeypatch):
    import pyodbc

    query, parameters = _attempt_part_statement(monkeypatch)
    # The variable shape matches authoritative dbo.ExportAttemptPart. It is
    # analyzed inside sp_describe_undeclared_parameters, not created/executed.
    declaration = (
        "DECLARE @Parts TABLE (AttemptID uniqueidentifier,PartNo int,PartCount int,"
        "FileID nvarchar(128),[Role] varchar(32),ManifestHash binary(32),GridCount int,"
        "[RowCount] bigint,CellCount bigint,VerificationState varchar(32),"
        "AclState varchar(32),QuarantineState varchar(32),Version bigint); "
    )
    query = query.replace("dbo.ExportAttemptPart", "@Parts")
    for number in range(1, len(parameters) + 1):
        query = query.replace("?", f"@p{number}", 1)
    with pyodbc.connect(
        r"DRIVER={ODBC Driver 17 for SQL Server};SERVER=lpc:localhost\K98DEV;"
        "DATABASE=tempdb;Trusted_Connection=yes;TrustServerCertificate=yes",
        autocommit=True,
        timeout=5,
    ) as connection:
        server, database = (
            connection.cursor()
            .execute("SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')),DB_NAME()")
            .fetchone()
        )
        assert server.lower() == r"9sx2vf4\k98dev" and database == "tempdb"
        connection.timeout = 5
        result = connection.cursor().execute(
            "EXEC sys.sp_describe_undeclared_parameters @tsql=?", declaration + query
        )
        names = [column[0] for column in result.description]
        described = [dict(zip(names, row, strict=False)) for row in result.fetchall()]
    assert len(described) == len(parameters) == 9
    row_count = next(row for row in described if row["name"] == "@p8")
    assert row_count["suggested_system_type_name"] == "bigint"
    assert parameters[7] == part()["rows"]
