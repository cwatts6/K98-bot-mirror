"""Actual local migration and restricted-login closeout, never production work.

The source fixture supplies synthetic rows. Tables retain their SQL checks and
indexes; unrelated foreign keys are omitted. New closeout foreign keys and all
module bodies, role checks and grants execute unchanged in a disposable database.
"""

import json
import os
from pathlib import Path
import re
import secrets
import subprocess
from types import SimpleNamespace
from uuid import uuid4

import pytest
from test_export_target_containment_sql import TABLES, contained_job  # noqa: F401

pytestmark = pytest.mark.skipif(
    os.getenv("K98_LEGACY_CLOSEOUT_SQL") != "1", reason="Explicit disposable SQL opt-in"
)


def drain(cursor):
    while cursor.nextset():
        pass


@pytest.fixture
def installed(contained_job):  # noqa: F811
    import pyodbc

    f = contained_job
    root = Path(os.environ["K98_LEGACY_CLOSEOUT_SQL_SOURCE"])
    database = "K98LegacyCloseoutTest_" + uuid4().hex
    login = "K98LegacyCloseout_" + uuid4().hex
    password = "Aa1!" + secrets.token_hex(24)
    prefix = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\\K98DEV;"
    suffix = "Encrypt=yes;TrustServerCertificate=yes;"
    admin = pyodbc.connect(
        prefix + "DATABASE=master;Trusted_Connection=yes;" + suffix, autocommit=True, timeout=5
    )
    assert (
        admin.execute("SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName'))").fetchval()
        == "9SX2VF4\\K98DEV"
    )
    owner = app = None
    try:
        admin.execute(f"CREATE DATABASE [{database}] COLLATE Latin1_General_CI_AS")
        owner = pyodbc.connect(
            prefix + f"DATABASE={database};Trusted_Connection=yes;" + suffix,
            autocommit=True,
            timeout=5,
        )
        owner.execute("CREATE SCHEMA KVK")
        for table in (*TABLES, "dbo.ExportReplacementPlan"):
            if table == "dbo.ExportLegacyCloseout":
                continue  # The real migration creates this with its foreign keys.
            source = (root / "sql_schema" / (table + ".Table.sql")).read_text(encoding="utf-8-sig")
            source = "\n".join(line for line in source.splitlines() if "FOREIGN KEY" not in line)
            owner.execute(re.sub(r",\s*\);", "\n);", source))
        for procedure in (
            "usp_ExportExecutionStreamTransition",
            "usp_ExportProviderRequestEventAppend",
            "usp_ExportReconciliationProofIssue",
        ):
            raw = subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(root),
                    "show",
                    "origin/main:sql_schema/dbo." + procedure + ".StoredProcedure.sql",
                ]
            ).decode("utf-8-sig")
            owner.execute(raw[raw.index("CREATE PROCEDURE") :].strip().removesuffix("GO").strip())
        owner.execute("CREATE ROLE ExportExecutionAuthority; CREATE ROLE ExportExecutionReader;")
        migration = (root / "migrations/20261023_001_legacy_export_closeout.sql").read_text()
        drain(owner.execute(migration))
        drain(owner.execute(migration))  # Exact reviewed postimage must be repeatable.
        admin.execute(f"CREATE LOGIN [{login}] WITH PASSWORD='{password}',CHECK_POLICY=ON")
        owner.execute(
            f"CREATE USER CloseoutAuthority FOR LOGIN [{login}]; ALTER ROLE ExportExecutionAuthority ADD MEMBER CloseoutAuthority;"
        )
        owner.execute(
            "CREATE USER CloseoutReader WITHOUT LOGIN; ALTER ROLE ExportExecutionReader ADD MEMBER CloseoutReader;"
        )
        # Existing installation permissions: this fixture does not grant any
        # direct evidence writes to the authority login.
        for table in (*TABLES, "dbo.ExportReplacementPlan"):
            owner.execute(
                f"GRANT SELECT ON {table} TO ExportExecutionAuthority,ExportExecutionReader"
            )
            owner.execute(
                f"DENY INSERT,UPDATE,DELETE ON {table} TO ExportExecutionAuthority,ExportExecutionReader"
            )
        for procedure in (
            "usp_ExportExecutionStreamTransition",
            "usp_ExportProviderRequestEventAppend",
        ):
            owner.execute(f"GRANT EXECUTE ON dbo.{procedure} TO ExportExecutionAuthority")
        for table in TABLES:
            cursor = f.sql.execute("SELECT * FROM #" + table.split(".")[1])
            columns = [c[0] for c in cursor.description]
            data = cursor.fetchall()
            for row in data:
                owner.execute(
                    f"INSERT {table} ({','.join('[' + c + ']' for c in columns)}) VALUES ({','.join('?' for _ in columns)})",
                    *row,
                )
        owner.execute(
            "UPDATE dbo.ExportExecutionSession SET AuthorityPrincipal='CloseoutAuthority'"
        )
        owner.execute(
            "UPDATE dbo.ExportExecutionStream SET State='closed',ActiveAccountKey=NULL,ClosureHash=?,ClosureReference=?,EventDigest=?,ClosedUTC=SYSUTCDATETIME()",
            b"h" * 32,
            str(uuid4()),
            b"d" * 32,
        )
        owner.execute(
            "UPDATE dbo.ExportProviderRequestEvent SET State='succeeded' WHERE State='unknown'"
        )
        app = pyodbc.connect(
            prefix + f"DATABASE={database};UID={login};PWD={password};" + suffix,
            autocommit=True,
            timeout=5,
        )
        assert tuple(
            app.execute(
                "SELECT IS_SRVROLEMEMBER('sysadmin'),IS_ROLEMEMBER('db_owner'),IS_ROLEMEMBER('ExportExecutionAuthority')"
            ).fetchone()
        ) == (0, 0, 1)
        action = str(uuid4())
        values = dict(
            ActionID=action,
            JobID=f.job,
            AccountKey="test-account",
            StorageOwner="disk",
            ExpectedVersion=7,
            OwnerID=f.owner,
            Fence=2,
            SnapshotHash=b"s" * 32,
            ReceiptHash=b"h" * 32,
            ReceiptReference=str(uuid4()),
            Actor="recovery:" + action,
            Reason="Abandon old partial output; next scan uses unchanged URLs",
        )

        def apply(**changes):
            args = values | changes
            app.execute("BEGIN TRANSACTION")
            try:
                result = app.execute(
                    "EXEC dbo.usp_ExportLegacyCloseout " + ",".join("@" + k + "=?" for k in args),
                    *args.values(),
                ).fetchone()
                app.execute("COMMIT")
                return result
            except Exception:
                app.execute("IF @@TRANCOUNT>0 ROLLBACK")
                raise

        def connect():
            return pyodbc.connect(
                prefix + f"DATABASE={database};UID={login};PWD={password};" + suffix,
                autocommit=False,
                timeout=5,
            )

        yield SimpleNamespace(
            owner=owner,
            app=app,
            connect=connect,
            apply=apply,
            values=values,
            f=f,
            migration=migration,
            root=root,
        )
    finally:
        if app is not None:
            app.close()
        if owner is not None:
            owner.close()
        assert re.fullmatch(r"K98LegacyCloseoutTest_[0-9a-f]{32}", database)
        if admin.execute("SELECT DB_ID(?)", database).fetchval() is not None:
            admin.execute(
                f"ALTER DATABASE [{database}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [{database}]"
            )
        if admin.execute("SELECT SUSER_ID(?)", login).fetchval() is not None:
            admin.execute(f"DROP LOGIN [{login}]")
        admin.close()


def test_restricted_closeout_preserves_input_streams_and_attempts(installed):
    f = installed
    before = {
        t: [tuple(row) for row in f.owner.execute("SELECT * FROM dbo." + t)]
        for t in (
            "ExportExecutionStream",
            "ExportAttempt",
            "ExportProviderRequest",
            "ExportProviderRequestEvent",
        )
    }
    f.apply()
    assert tuple(
        f.owner.execute("SELECT State,Version,SpoolKey FROM dbo.ExportJob").fetchone()
    ) == ("failed", 8, "retained-input")
    assert (
        f.owner.execute(
            "SELECT COUNT(*) FROM dbo.ExportResource WHERE ActiveJobID IS NOT NULL"
        ).fetchval()
        == 0
    )
    assert f.owner.execute("SELECT COUNT(*) FROM dbo.ExportLegacyCloseout").fetchval() == 1
    for table, rows in before.items():
        assert [tuple(row) for row in f.owner.execute("SELECT * FROM dbo." + table)] == rows
    import pyodbc

    with pytest.raises(pyodbc.Error):
        f.apply()
    with pytest.raises(pyodbc.Error):
        f.app.execute("DELETE dbo.ExportLegacyCloseout")


@pytest.mark.parametrize(
    "change",
    [dict(ExpectedVersion=8), dict(Fence=3), dict(AccountKey="other"), dict(OwnerID=str(uuid4()))],
)
def test_stale_confirmation_cannot_release_anything(installed, change):
    import pyodbc

    with pytest.raises(pyodbc.Error):
        installed.apply(**change)
    assert installed.owner.execute("SELECT COUNT(*) FROM dbo.ExportLegacyCloseout").fetchval() == 0
    assert (
        installed.owner.execute(
            "SELECT COUNT(*) FROM dbo.ExportResource WHERE ActiveJobID IS NOT NULL"
        ).fetchval()
        == 2
    )


def contain(f):
    source = (f.root / "sql_schema/dbo.usp_ExportJobContainTargets.StoredProcedure.sql").read_text(
        encoding="utf-8-sig"
    )
    f.owner.execute(source[source.index("CREATE PROCEDURE") :].strip().removesuffix("GO").strip())
    f.owner.execute("GRANT EXECUTE ON dbo.usp_ExportJobContainTargets TO ExportExecutionAuthority")
    args = f.f.arguments
    f.app.execute("BEGIN TRANSACTION")
    drain(
        f.app.execute(
            "EXEC dbo.usp_ExportJobContainTargets " + ",".join("@" + k + "=?" for k in args),
            *args.values(),
        )
    )
    f.app.execute("COMMIT")
    f.values["ExpectedVersion"] = 8


def test_same_url_admission_returns_but_old_execution_remains_disabled(installed):
    import pyodbc

    f = installed
    contain(f)
    assert (
        f.app.execute("SELECT FileID FROM dbo.ExportActiveContainedTarget").fetchval() == "old-file"
    )
    f.apply()
    assert f.app.execute("SELECT COUNT(*) FROM dbo.ExportActiveContainedTarget").fetchval() == 0
    assert f.app.execute("SELECT FileID FROM dbo.ExportContainedTarget").fetchval() == "old-file"
    next_job, next_owner, next_stream = (str(uuid4()) for _ in range(3))
    f.owner.execute(
        "INSERT dbo.ExportJob (JobID,ConsumerKind,AccountKey,DestinationSetHash,InputHash,SpoolKey,SpoolBytes,StorageOwner,EnqueueSequence,State,OwnerID,Fence,Version,CreatedUTC,UpdatedUTC,Actor,Reason,ProvenanceJson) "
        "SELECT ?,ConsumerKind,AccountKey,DestinationSetHash,CAST(? AS binary(32)),'next-scan-input',SpoolBytes,StorageOwner,2,'running',?,3,1,CreatedUTC,UpdatedUTC,Actor,Reason,'{}' FROM dbo.ExportJob WHERE JobID=?",
        next_job,
        b"n" * 32,
        next_owner,
        f.f.job,
    )
    f.owner.execute(
        "INSERT dbo.ExportJobResource SELECT ?,ResourceKey FROM dbo.ExportJobResource WHERE JobID=?",
        next_job,
        f.f.job,
    )
    f.owner.execute(
        "UPDATE dbo.ExportResource SET ActiveJobID=?,OwnerID=?,Fence=3,Version=5",
        next_job,
        next_owner,
    )
    resources = [dict(key=r["key"], version=5) for r in f.f.resources]
    drain(
        f.app.execute(
            "EXEC dbo.usp_ExportExecutionStreamTransition @Action='open',@SessionID=?,@StreamID=?,"
            "@AccountKey='test-account',@ExpectedVersion=0,@OwnerKind='job',@ObjectID=?,@OwnerID=?,"
            "@Fence=3,@ClaimVersion=1,@Purpose='mutation',@ScopeJson=?,@ChildIdentity=?,@RegistrationHash=?,@SnapshotHash=?",
            f.f.session,
            next_stream,
            next_job,
            next_owner,
            json.dumps(dict(resources=resources)),
            str(uuid4()),
            b"n" * 32,
            b"s" * 32,
        )
    )
    assert (
        f.app.execute(
            "SELECT State FROM dbo.ExportExecutionStream WHERE StreamID=?", next_stream
        ).fetchval()
        == "open"
    )
    assert (
        f.app.execute(
            "SELECT State FROM dbo.ExportExecutionStream WHERE StreamID=?", f.f.stream
        ).fetchval()
        == "target_contained"
    )
    for state in ("prepared", "dispatch_intent", "succeeded"):
        with pytest.raises(pyodbc.Error):
            f.app.execute(
                "EXEC dbo.usp_ExportProviderRequestEventAppend @SessionID=?,@StreamID=?,@AccountKey='test-account',"
                "@ExpectedVersion=6,@RequestID=?,@EventID=?,@State=?,@EvidenceHash=?,@EvidenceReference=?",
                f.f.session,
                f.f.stream,
                f.f.request,
                str(uuid4()),
                state,
                b"z" * 32,
                str(uuid4()),
            )
    assert f.app.execute("SELECT COUNT(*) FROM dbo.ExportProviderRequestEvent").fetchval() == 3
    # A later stopped export must remain recoverable without deleting the first
    # export's historical target records or issuing replacement URLs.
    f.owner.execute(
        "UPDATE dbo.ExportExecutionStream SET State='closed',ActiveAccountKey=NULL,"
        "ClosureHash=?,ClosureReference=?,EventDigest=?,ClosedUTC=SYSUTCDATETIME() WHERE StreamID=?",
        b"c" * 32,
        str(uuid4()),
        b"e" * 32,
        next_stream,
    )
    f.owner.execute("UPDATE dbo.ExportJob SET State='uncertain',Version=2 WHERE JobID=?", next_job)
    action = str(uuid4())
    f.values.update(
        ActionID=action,
        JobID=next_job,
        ExpectedVersion=2,
        OwnerID=next_owner,
        Fence=3,
        ReceiptReference=str(uuid4()),
        Actor="recovery:" + action,
    )
    f.apply()
    assert f.app.execute("SELECT COUNT(*) FROM dbo.ExportLegacyCloseout").fetchval() == 2
    assert f.app.execute("SELECT COUNT(*) FROM dbo.ExportContainedTarget").fetchval() == 1
    assert f.app.execute("SELECT COUNT(*) FROM dbo.ExportProviderRequestEvent").fetchval() == 3


@pytest.mark.parametrize(
    "fault", ["unknown", "missing_event", "live", "foreign_owner", "unbound_target"]
)
def test_incomplete_or_conflicting_evidence_keeps_block(installed, fault):
    import pyodbc

    f = installed
    changes = {
        "unknown": "UPDATE dbo.ExportProviderRequestEvent SET State='unknown' WHERE EventSequence=3",
        "missing_event": "DELETE dbo.ExportProviderRequestEvent WHERE EventSequence=3",
        "live": "UPDATE dbo.ExportExecutionStream SET State='open',ActiveAccountKey=AccountKey,ClosureHash=NULL,ClosureReference=NULL,EventDigest=NULL,ClosedUTC=NULL",
        "foreign_owner": "UPDATE dbo.ExportResource SET ActiveJobID=NEWID(),OwnerID=NEWID()",
        "unbound_target": "UPDATE dbo.ExportProviderRequest SET TargetID='other-file'",
    }
    f.owner.execute(changes[fault])
    with pytest.raises(pyodbc.Error):
        f.apply()
    assert f.owner.execute("SELECT COUNT(*) FROM dbo.ExportLegacyCloseout").fetchval() == 0
    assert f.owner.execute("SELECT State FROM dbo.ExportJob").fetchval() == "uncertain"


def test_reader_cannot_closeout_or_rewrite_history(installed):
    f = installed
    f.owner.execute("EXECUTE AS USER='CloseoutReader'")
    try:
        for name, kind, permission in [
            ("dbo.usp_ExportLegacyCloseout", "OBJECT", "EXECUTE"),
            ("dbo.ExportLegacyCloseout", "OBJECT", "INSERT"),
            ("dbo.ExportLegacyCloseout", "OBJECT", "CONTROL"),
        ]:
            assert (
                f.owner.execute(
                    "SELECT HAS_PERMS_BY_NAME(?,?,?)", name, kind, permission
                ).fetchval()
                == 0
            )
    finally:
        f.owner.execute("REVERT")


def test_real_dal_snapshot_and_cas_with_restricted_login(installed):
    from kvk.dal.new_source_import_dal import digest
    from services.legacy_export_closeout_dal import LegacyExportCloseoutDAL

    f = installed
    dal = LegacyExportCloseoutDAL(f.connect, account="test-account", storage_owner="disk")
    snapshot = dal.snapshot(f.f.job)
    dal.settle(
        snapshot,
        action_id=f.values["ActionID"],
        token=digest(snapshot).hex(),
        marker=dict(sha256=(b"h" * 32).hex(), reference=f.values["ReceiptReference"]),
        actor=f.values["Actor"],
        reason=f.values["Reason"],
    )
    assert dal.snapshot(f.f.job)["closeout"]["ActionID"] == f.values["ActionID"]
