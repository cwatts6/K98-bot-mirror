"""Execute the additive failed-job probe gate and exact module postimage in temp SQL."""

import hashlib
import os
from pathlib import Path
import re

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("K98_ABSENT_PROBE_SQL") != "1", reason="Explicit local temporary SQL opt-in"
)


@pytest.fixture(
    params=[
        ("20261015_004_failed_publication_probe.sql", "dbo.usp_ExportExecutionStreamTransition"),
        (
            "20261015_006_failed_probe_request_events.sql",
            "dbo.usp_ExportProviderRequestEventAppend",
        ),
    ]
)
def migration(request):
    root = Path(os.environ["K98_ABSENT_PROBE_SQL_SOURCE"])
    filename, name = request.param
    text = (root / "migrations" / filename).read_text(encoding="utf-8-sig")
    body = re.search(
        r"DECLARE @Apply nvarchar\(max\)=N'((?:''|[^'])*)';\nEXEC sys.sp_executesql @Apply;",
        text,
        re.S,
    )[1].replace("''", "'")
    return root, text, body, name


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
    root, text, body, name = migration
    temporary = "#K98FailedJobProbe"
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
    # The stream source now includes the later read-prefix close migration.
    current_body = body
    if name.endswith("StreamTransition"):
        current_text = (root / "migrations/20261015_005_read_prefix_closure.sql").read_text(
            encoding="utf-8-sig"
        )
        current_body = re.search(
            r"DECLARE @Apply nvarchar\(max\)=N'((?:''|[^'])*)';\nEXEC sys.sp_executesql @Apply;",
            current_text,
            re.S,
        )[1].replace("''", "'")
    source = (root / ("sql_schema/" + name + ".StoredProcedure.sql")).read_text(
        encoding="utf-8-sig"
    )
    assert (
        source[source.index("CREATE PROCEDURE") :].strip().removesuffix("GO").strip()
        == current_body.replace("CREATE OR ALTER PROCEDURE", "CREATE PROCEDURE", 1).strip()
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
    _, _, body, _ = migration
    gate = re.search(r"AND \(\(@Purpose='mutation' AND State='running'\).*?\n", body)[0].strip()[4:]
    query = (
        "DECLARE @Purpose varchar(16)=?; WITH j AS (SELECT CAST(? AS varchar(32)) State) "
        "SELECT CASE WHEN " + gate + " THEN 1 ELSE 0 END FROM j"
    )
    assert bool(sql.execute(query, purpose, state).fetchval()) is allowed


@pytest.mark.parametrize(
    "mismatch", [None, "owner", "account", "fence", "version", "epoch", "nested", "membership"]
)
def test_failed_probe_exact_job_guards(migration, sql, mismatch):
    """Exercise the complete job guard from both open and event append procedures."""
    import uuid

    import pyodbc

    _, _, body, _ = migration
    guard = body[
        body.index(" IF @OwnerKind='job'") : body.index(" ELSE IF @OwnerKind='preparation'")
    ]
    guard = guard.replace("dbo.ExportJobResource", "#JobResource").replace("dbo.ExportJob", "#Job")
    job_id, owner = str(uuid.uuid4()), str(uuid.uuid4())
    sql.execute("""CREATE TABLE #Job(JobID uniqueidentifier,AccountKey varchar(128),OwnerID uniqueidentifier,
        Fence bigint,Version bigint,State varchar(16),PoolEpoch bigint,ProvenanceJson nvarchar(max));
        CREATE TABLE #JobResource(JobID uniqueidentifier,ResourceKey varchar(256));""")
    sql.execute("INSERT #Job VALUES (?,'account',?,7,5,'failed',3,N'{}')", job_id, owner)
    sql.execute("INSERT #JobResource VALUES (?,'account:account')", job_id)
    args = [owner, "account", 7, 5, 3, None, "account:account"]
    if mismatch == "owner":
        args[0] = str(uuid.uuid4())
    if mismatch == "account":
        args[1] = "foreign"
    if mismatch == "fence":
        args[2] += 1
    if mismatch == "version":
        args[3] += 1
    if mismatch == "epoch":
        args[4] += 1
    if mismatch == "nested":
        args[5] = str(uuid.uuid4())
    if mismatch == "membership":
        args[6] = "account:foreign"
    query = (
        """SET NOCOUNT ON; DECLARE @OwnerKind varchar(16)='job',@Purpose varchar(16)='probe',
        @ObjectID uniqueidentifier=?,@OwnerID uniqueidentifier=?,@AccountKey varchar(128)=?,
        @Fence bigint=?,@ClaimVersion bigint=?,@Epoch bigint=?,@NestedToken uniqueidentifier=?;
        DECLARE @Resources TABLE(ResourceKey varchar(256)); INSERT @Resources VALUES (?);
    """
        + guard
    )
    if mismatch:
        with pytest.raises(
            pyodbc.Error, match=r"Job/nested owner CAS conflict|Job membership conflict"
        ):
            sql.execute(query, job_id, *args)
    else:
        sql.execute(query, job_id, *args)


@pytest.mark.parametrize(
    "kind,stream_state,allowed",
    [("read", "open", True), ("mutation", "open", False), ("read", "frozen", False)],
)
def test_probe_prepare_still_forbids_mutation(migration, sql, kind, stream_state, allowed):
    _, _, body, name = migration
    if not name.endswith("EventAppend"):
        return
    predicate = re.search(r"IF (@StreamState<>.*)\n\s+THROW 51700,'Stream cannot prepare", body)[1]
    result = sql.execute(
        "DECLARE @Purpose varchar(16)='probe',@RequestKind varchar(16)=?,@StreamState varchar(16)=?; SELECT CASE WHEN "
        + predicate
        + " THEN 0 ELSE 1 END",
        kind,
        stream_state,
    ).fetchval()
    assert bool(result) is allowed
