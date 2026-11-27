"""Run the actual closure gate and CAS against disposable SQL Server objects."""

import hashlib
import json
import os
from pathlib import Path
import re
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("K98_READ_CLOSE_SQL") != "1", reason="Explicit local temporary SQL opt-in"
)


@pytest.fixture
def migration():
    root = Path(os.environ["K98_READ_CLOSE_SQL_SOURCE"])
    text = (root / "migrations/20261015_005_read_prefix_closure.sql").read_text(
        encoding="utf-8-sig"
    )
    body = re.search(
        r"DECLARE @Apply nvarchar\(max\)=N'((?:''|[^'])*)';\nEXEC sys.sp_executesql @Apply;",
        text,
        re.S,
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


def test_actual_module_postimage_and_bot_source_pins(migration, sql):
    root, text, body = migration
    name, temporary = "dbo.usp_ExportExecutionStreamTransition", "#K98ReadPrefixClose"
    sql.execute(body.replace(name, temporary, 1))
    definition = (
        sql.execute(
            "SELECT definition FROM tempdb.sys.sql_modules WHERE object_id=OBJECT_ID('tempdb..#K98ReadPrefixClose')"
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
    canonical = body.replace("CREATE OR ALTER PROCEDURE", "CREATE PROCEDURE", 1)
    expected = hashlib.sha256(canonical.encode("utf-16-le")).digest()
    assert bytes(sql.execute(query, definition).fetchval()) == expected
    assert bytes(sql.execute(query, definition + "\n-- drift").fetchval()) != expected
    assert "0x" + expected.hex() in text
    source = (root / ("sql_schema/" + name + ".StoredProcedure.sql")).read_text(
        encoding="utf-8-sig"
    )
    assert (
        source[source.index("CREATE PROCEDURE") :].strip().removesuffix("GO").strip()
        == canonical.strip()
    )
    bot = Path(__file__).resolve().parents[1]
    manifest = json.loads((bot / "deploy/export_application_schema_source.json").read_text())
    assert (
        next(x["sha256"] for x in manifest if x["name"] == name)
        == hashlib.sha256(source.encode()).hexdigest()
    )
    from services.export_execution_dal import APPLICATION_SCHEMA_SOURCE_HASH

    assert (
        APPLICATION_SCHEMA_SOURCE_HASH
        == hashlib.sha256(
            json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        ).hexdigest()
    )


@pytest.mark.parametrize(
    "purpose,kind,events,allowed",
    [
        ("probe", "read", ["prepared"], True),
        ("probe", "read", ["prepared", "dispatch_intent"], True),
        ("probe", "read", [], False),
        ("probe", "read", ["dispatch_intent"], False),
        ("mutation", "read", ["prepared"], False),
        ("enrollment", "read", ["prepared"], False),
        ("probe", "mutation", ["prepared"], False),
        ("probe", "read", ["prepared", "invalid"], False),
        ("mutation", "mutation", ["prepared", "dispatch_intent"], False),
        ("mutation", "mutation", ["prepared", "dispatch_intent", "unknown"], True),
        ("probe", "read", ["prepared", "succeeded"], True),
        ("mutation", "mutation", ["prepared", "not_sent"], True),
    ],
)
def test_actual_close_preserves_read_history(migration, sql, purpose, kind, events, allowed):
    _exercise_close(migration, sql, purpose, kind, events, allowed)


@pytest.mark.parametrize(
    "mismatch",
    ["SessionID", "ChildIdentity", "AccountKey", "ExpectedVersion", "LastSequence", "State"],
)
def test_read_prefix_does_not_bypass_exact_closure_cas(migration, sql, mismatch):
    _exercise_close(migration, sql, "probe", "read", ["prepared"], False, mismatch)


def _exercise_close(migration, sql, purpose, kind, events, allowed, mismatch=None):
    import pyodbc

    _, _, body = migration
    close = body[
        body.index("   -- Preserve complete abandoned read prefixes;") : body.index(
            "  ELSE THROW 51700,'Unsupported stream action.'"
        )
    ]
    close = close.rsplit("  END", 1)[0]
    for name in ("ExportExecutionStream", "ExportProviderRequestEvent", "ExportProviderRequest"):
        close = close.replace("dbo." + name, "#" + name)
    sql.execute("""
        CREATE TABLE #ExportExecutionStream (StreamID uniqueidentifier,SessionID uniqueidentifier,
         ChildIdentity uniqueidentifier,AccountKey varchar(128),Purpose varchar(16),State varchar(16),
         ActiveAccountKey varchar(128),Version bigint,LastSequence bigint,ClosureHash binary(32),
         ClosureReference uniqueidentifier,EventDigest binary(32),ClosedUTC datetime2);
        CREATE TABLE #ExportProviderRequest (RequestID uniqueidentifier,StreamID uniqueidentifier,RequestKind varchar(16));
        CREATE TABLE #ExportProviderRequestEvent (RequestID uniqueidentifier,State varchar(32));
    """)
    stream, session, child, request = [str(uuid.uuid4()) for _ in range(4)]
    sql.execute(
        "INSERT #ExportExecutionStream VALUES (?,?,?,'account',?,'frozen','account',2,1,NULL,NULL,NULL,NULL)",
        stream,
        session,
        child,
        purpose,
    )
    sql.execute("INSERT #ExportProviderRequest VALUES (?,?,?)", request, stream, kind)
    for state in events:
        sql.execute("INSERT #ExportProviderRequestEvent VALUES (?,?)", request, state)
    arguments = dict(
        SessionID=session,
        ChildIdentity=child,
        AccountKey="account",
        ExpectedVersion=2,
        LastSequence=1,
    )
    if mismatch in ("SessionID", "ChildIdentity"):
        arguments[mismatch] = str(uuid.uuid4())
    elif mismatch == "AccountKey":
        arguments[mismatch] = "foreign"
    elif mismatch in ("ExpectedVersion", "LastSequence"):
        arguments[mismatch] += 1
    elif mismatch == "State":
        sql.execute("UPDATE #ExportExecutionStream SET State='open'")
    query = (
        """SET NOCOUNT ON; DECLARE @StreamID uniqueidentifier=?,@SessionID uniqueidentifier=?,@ChildIdentity uniqueidentifier=?,
        @AccountKey varchar(128)=?,@ExpectedVersion bigint=?,@LastSequence bigint=?,
        @ClosureHash binary(32)=0x01,@ClosureReference uniqueidentifier=NEWID(),@EventDigest binary(32)=0x02;
    """
        + close
    )
    params = (stream, *arguments.values())
    if allowed:
        sql.execute(query, *params)
    else:
        with pytest.raises(pyodbc.Error, match=r"Nonterminal request|Stream close CAS lost"):
            sql.execute(query, *params)
    row = sql.execute(
        "SELECT State,ActiveAccountKey,Version FROM #ExportExecutionStream"
    ).fetchone()
    assert tuple(row) == (
        ("closed", None, 3)
        if allowed
        else ("open" if mismatch == "State" else "frozen", "account", 2)
    )
    assert sorted(
        r[0] for r in sql.execute("SELECT State FROM #ExportProviderRequestEvent")
    ) == sorted(events)
