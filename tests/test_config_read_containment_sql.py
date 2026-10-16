"""Actual SQL containment/CAS against session-local tables and procedures only."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.config_read_containment import ConfigReadContainment, verify_contained_read
from tests import test_config_preparation_recovery_sql as fixture_module
from tests.test_config_read_containment import private_store

sql_fixture = fixture_module.sql_fixture

pytestmark = pytest.mark.skipif(
    os.environ.get("K98_READ_CONTAINMENT_SQL") != "1", reason="Explicit local temporary SQL opt-in"
)


@pytest.fixture(autouse=True)
def containment_schema(monkeypatch):
    root = Path(os.environ["K98_READ_CONTAINMENT_SQL_SOURCE"])
    monkeypatch.setattr(fixture_module, "SQL_SOURCE", root)
    original = fixture_module.local_sql
    monkeypatch.setattr(
        fixture_module,
        "local_sql",
        lambda text: (
            original(text)
            .replace("dbo.usp_ExportExecutionStreamTransition", "#K98ReadContainment")
            .replace("dbo.ExportExecutionSession", "#ExportExecutionSession")
        ),
    )
    return root


@pytest.fixture
def containment(sql_fixture, containment_schema):
    service, sql = sql_fixture
    # Fixture substitutes the role gate only; no permanent role/login/grant exists.
    raw = (
        containment_schema
        / "sql_schema/dbo.usp_ExportExecutionStreamTransition.StoredProcedure.sql"
    ).read_text(encoding="utf-8-sig")
    body = raw[raw.index("CREATE PROCEDURE") :].strip().removesuffix("GO").strip()
    role = "IF IS_ROLEMEMBER(N'ExportExecutionAuthority')<>1 OR IS_ROLEMEMBER(N'ExportExecutionAuthority') IS NULL"
    assert role in body
    sql.execute(fixture_module.local_sql(body.replace(role, "IF 1=0", 1)))
    sql.execute(
        "CREATE TABLE #ExportExecutionSession (SessionID uniqueidentifier,AuthorityPrincipal sysname,State varchar(16)); "
        "INSERT #ExportExecutionSession SELECT SessionID,USER_NAME(),'open' FROM #ExportExecutionStream;"
    )
    sql.commit()
    repair = ConfigReadContainment(
        dal=service.dal,
        execution=service.execution,
        store=private_store({}),
        target=service.target,
        registration_hash=service.registration_hash,
        storage_owner=service.storage_owner,
    )
    return repair, sql


@pytest.mark.parametrize("state", ["open", "frozen", "closed"])
def test_atomic_fence_release_and_private_historical_verification(containment, state):
    repair, sql = containment
    if state != "closed":
        sql.execute(
            "UPDATE #ExportExecutionStream SET State=?,ActiveAccountKey=AccountKey,ClosureHash=NULL,ClosureReference=NULL,EventDigest=NULL,ClosedUTC=NULL",
            state,
        )
        sql.commit()
    report = repair.inspect()
    repair.apply(
        approved_snapshot_sha256=report["snapshot_sha256"],
        actor="test-admin",
        reason="Discard read",
    )
    row = repair.execution.read_stream(repair.target.stream_ids[0])
    assert row["State"] == "read_contained" and row["ActiveAccountKey"] is None
    seal = verify_contained_read(
        repair.execution,
        repair.store,
        row,
        account=repair.target.account,
        registration_hash=bytes.fromhex(repair.registration_hash),
    )
    assert seal["last_sequence"] == 0
    assert sql.execute("SELECT State FROM #ExportPreparation").fetchval() == "unavailable"
    assert (
        sql.execute("SELECT COUNT(*) FROM #ExportResource WHERE OwnerID IS NOT NULL").fetchval()
        == 0
    )
    assert sql.execute("SELECT COUNT(*) FROM #ExportPreparationResource").fetchval() == 2
    audit = json.loads(sql.execute("SELECT GenerationJson FROM #ExportPreparation").fetchval())
    assert audit["before"] == report["snapshot"] and audit["child_termination_verified"] is False
    # Exercise the actual event API: no late child can admit another request.
    source = (
        fixture_module.SQL_SOURCE
        / "sql_schema/dbo.usp_ExportProviderRequestEventAppend.StoredProcedure.sql"
    ).read_text()
    from uuid import uuid4

    import pyodbc

    body = source[source.index("CREATE PROCEDURE") :].strip().removesuffix("GO").strip()
    body = body.replace(
        "IF IS_ROLEMEMBER(N'ExportExecutionAuthority')<>1 OR IS_ROLEMEMBER(N'ExportExecutionAuthority') IS NULL",
        "IF 1=0",
        1,
    )
    body = fixture_module.local_sql(body).replace(
        "dbo.usp_ExportProviderRequestEventAppend", "#K98ReadContainedEvent", 1
    )
    sql.autocommit = True
    sql.execute(body)
    with pytest.raises(
        pyodbc.Error, match=r"Resource owner/fence/version conflict|Exact open stream"
    ):
        sql.execute(
            "EXEC #K98ReadContainedEvent @SessionID=?,@StreamID=?,@AccountKey=?,@ExpectedVersion=?,"
            "@RequestID=?,@EventID=?,@State='prepared',@EvidenceHash=?,@EvidenceReference=?,"
            "@Operation='sheets.get',@RequestKind='read',@TargetID='file-a',@PayloadHash=?,@PayloadReference=?",
            row["SessionID"],
            row["StreamID"],
            row["AccountKey"],
            row["Version"],
            str(uuid4()),
            str(uuid4()),
            b"x" * 32,
            str(uuid4()),
            b"y" * 32,
            str(uuid4()),
        )
    assert sql.execute("SELECT COUNT(*) FROM #ExportProviderRequest").fetchval() == 0
    from kvk.dal.new_source_import_dal import transaction
    from services.export_coordination_dal import _mutex

    with transaction(repair.execution.connect) as cursor:
        _mutex(cursor, "account:" + repair.target.account)
        repair.execution.assert_no_active_stream(cursor, repair.target.account)


@pytest.mark.parametrize(
    "states",
    [
        ["prepared"],
        ["prepared", "dispatch_intent"],
        ["prepared", "dispatch_intent", "unknown"],
        ["prepared", "dispatch_intent", "succeeded"],
    ],
)
def test_sql_read_prefix_is_contained_without_private_response_bytes(containment, states):
    from uuid import uuid4

    repair, sql = containment
    request = str(uuid4())
    sql.execute(
        "INSERT #ExportProviderRequest (RequestID,StreamID,Sequence,Operation,RequestKind,TargetID,PayloadHash,PayloadReference,CreatedUTC) "
        "VALUES (?,?,1,'sheets.values.get','read','file-a',?,?,SYSUTCDATETIME())",
        request,
        repair.target.stream_ids[0],
        b"x" * 32,
        str(uuid4()),
    )
    for index, state in enumerate(states, 1):
        sql.execute(
            "INSERT #ExportProviderRequestEvent VALUES (?,?,?,?,?,?,SYSUTCDATETIME())",
            str(uuid4()),
            request,
            index,
            state,
            b"y" * 32,
            str(uuid4()),
        )
    sql.execute(
        "UPDATE #ExportExecutionStream SET LastSequence=1,State='frozen',ActiveAccountKey=AccountKey,"
        "ClosureHash=NULL,ClosureReference=NULL,EventDigest=NULL,ClosedUTC=NULL"
    )
    sql.commit()
    report = repair.inspect()
    repair.apply(
        approved_snapshot_sha256=report["snapshot_sha256"], actor="test", reason="Discard read"
    )
    row = repair.execution.read_stream(repair.target.stream_ids[0])
    seal = verify_contained_read(
        repair.execution,
        repair.store,
        row,
        account=repair.target.account,
        registration_hash=bytes.fromhex(repair.registration_hash),
    )
    assert seal["last_sequence"] == 1
    assert [
        r[0]
        for r in sql.execute("SELECT State FROM #ExportProviderRequestEvent ORDER BY EventSequence")
    ] == states
    if states[-1] == "dispatch_intent":
        import pyodbc

        source = (
            fixture_module.SQL_SOURCE
            / "sql_schema/dbo.usp_ExportProviderRequestEventAppend.StoredProcedure.sql"
        ).read_text()
        body = source[source.index("CREATE PROCEDURE") :].strip().removesuffix("GO").strip()
        body = body.replace(
            "IF IS_ROLEMEMBER(N'ExportExecutionAuthority')<>1 OR IS_ROLEMEMBER(N'ExportExecutionAuthority') IS NULL",
            "IF 1=0",
            1,
        )
        body = fixture_module.local_sql(body).replace(
            "dbo.usp_ExportProviderRequestEventAppend", "#K98LateReadResult", 1
        )
        sql.autocommit = True
        sql.execute(body)
        with pytest.raises(pyodbc.Error, match="Request stream CAS lost or closed"):
            sql.execute(
                "EXEC #K98LateReadResult @SessionID=?,@StreamID=?,@AccountKey=?,@ExpectedVersion=?,"
                "@RequestID=?,@EventID=?,@State='unknown',@EvidenceHash=?,@EvidenceReference=?",
                row["SessionID"],
                row["StreamID"],
                row["AccountKey"],
                row["Version"],
                request,
                str(uuid4()),
                b"z" * 32,
                str(uuid4()),
            )
        assert sql.execute("SELECT COUNT(*) FROM #ExportProviderRequestEvent").fetchval() == 2


def test_final_resource_conflict_rolls_back_containment_and_all_releases(containment, monkeypatch):
    import services.config_preparation_recovery_dal as dal_module

    repair, sql = containment
    original = dal_module._cas

    def fail_last(cursor, statement, *args):
        if "UPDATE dbo.ExportResource" in statement and args[0].startswith("destination:"):
            raise SourceConflict("Injected last resource conflict")
        return original(cursor, statement, *args)

    monkeypatch.setattr(dal_module, "_cas", fail_last)
    before = repair.inspect()
    with pytest.raises(SourceConflict):
        repair.apply(
            approved_snapshot_sha256=before["snapshot_sha256"], actor="test", reason="Discard"
        )
    assert repair.dal.snapshot(repair.target) == before["snapshot"]
    assert sql.execute("SELECT State FROM #ExportExecutionStream").fetchval() == "closed"


@pytest.mark.parametrize(
    "damage",
    ["principal", "session", "owner", "fence", "version", "child", "kind", "state", "sequence"],
)
def test_protected_sql_transition_rejects_mismatched_exact_scope(containment, damage):
    import pyodbc

    repair, sql = containment
    report = repair.inspect()
    stream = report["snapshot"]["streams"][0]
    if damage == "principal":
        sql.execute("UPDATE #ExportExecutionSession SET AuthorityPrincipal='not-this-authority'")
        sql.commit()
    values = dict(
        SessionID=stream["SessionID"],
        StreamID=stream["StreamID"],
        Action="contain_read",
        ExpectedVersion=stream["Version"],
        AccountKey=repair.target.account,
        ObjectID=repair.target.preparation_id,
        OwnerID=repair.target.owner,
        Fence=repair.target.fence,
        ClaimVersion=stream["ClaimVersion"],
        ChildIdentity=stream["ChildIdentity"],
        ClosureHash=b"x" * 32,
        ClosureReference=stream["ChildIdentity"],
        EventDigest=b"e" * 32,
        LastSequence=0,
    )
    from uuid import uuid4

    if damage in {"session", "owner", "child"}:
        values[{"session": "SessionID", "owner": "OwnerID", "child": "ChildIdentity"}[damage]] = (
            str(uuid4())
        )
    elif damage in {"fence", "version", "sequence"}:
        values[
            {"fence": "Fence", "version": "ExpectedVersion", "sequence": "LastSequence"}[damage]
        ] += 1
    elif damage == "kind":
        sql.execute("UPDATE #ExportExecutionStream SET Purpose='mutation'")
        sql.commit()
    elif damage == "state":
        sql.execute("UPDATE #ExportPreparation SET State='unavailable'")
        sql.commit()
    sql.autocommit = True
    sql.execute("BEGIN TRANSACTION")
    with pytest.raises(pyodbc.Error):
        sql.execute(
            "EXEC #K98ReadContainment " + ",".join("@" + key + "=?" for key in values),
            *values.values(),
        )
    assert sql.execute("SELECT @@TRANCOUNT").fetchval() == 0
    assert sql.execute("SELECT State FROM #ExportExecutionStream").fetchval() == "closed"
    assert (
        sql.execute("SELECT COUNT(*) FROM #ExportResource WHERE OwnerID IS NOT NULL").fetchval()
        == 2
    )


def test_migration_contains_exact_compiled_modules_and_source_pins(containment_schema, sql_fixture):
    _, sql = sql_fixture
    text = (
        containment_schema / "migrations/20261015_007_read_dispatch_containment.sql"
    ).read_text()
    bodies = re.findall(
        r"SET @Apply=N'((?:''|[^'])*)';\nEXEC sys.sp_executesql @Apply;", text, re.S
    )
    assert len(bodies) == 4
    manifest = json.loads(
        (
            Path(__file__).resolve().parents[1] / "deploy/export_application_schema_source.json"
        ).read_text()
    )
    for index, escaped in enumerate(bodies):
        body = escaped.replace("''", "'")
        name = re.search(r"PROCEDURE (\S+)", body)[1]
        temporary = "#K98ContainmentImage" + str(index)
        sql.execute(body.replace(name, temporary, 1))
        actual = (
            sql.execute(
                "SELECT definition FROM tempdb.sys.sql_modules WHERE object_id=OBJECT_ID(?)",
                "tempdb.." + temporary,
            )
            .fetchval()
            .replace(temporary, name, 1)
            .replace("\r\n", "\n")
        )
        actual = re.sub(
            r"^(?:CREATE OR ALTER|CREATE  |ALTER) PROCEDURE", "CREATE PROCEDURE", actual
        )
        expected = body.replace("CREATE OR ALTER PROCEDURE", "CREATE PROCEDURE", 1)
        assert actual == expected
        assert "0x" + hashlib.sha256(actual.encode("utf-16-le")).hexdigest() in text
        path = "sql_schema/" + name + ".StoredProcedure.sql"
        # This migration's literal postimages remain immutable when later
        # migrations extend the same procedures. Check its own reviewed commit.
        source = (
            subprocess.check_output(
                ["git", "show", "79987f7bd5e40aaecc66a36bcbd8ecdc93522667:" + path],
                cwd=containment_schema,
            )
            .decode("utf-8-sig")
            .replace("\r\n", "\n")
        )
        current = (containment_schema / path).read_text(encoding="utf-8-sig")
        assert (
            source[source.index("CREATE PROCEDURE") :].strip().removesuffix("GO").strip()
            == expected.strip()
        )
        assert (
            next(item["sha256"] for item in manifest if item["name"] == name)
            == hashlib.sha256(current.encode()).hexdigest()
        )
