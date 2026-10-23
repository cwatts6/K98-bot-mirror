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


@pytest.mark.parametrize("provenance_bytes", [65534, 65536])
def test_closeout_preserves_full_provenance_without_growing_it(installed, provenance_bytes):
    from services.legacy_export_closeout_dal import LegacyExportCloseoutDAL

    f = installed
    empty = json.dumps({"padding": ""}, separators=(",", ":"))
    original = json.dumps(
        {"padding": "x" * (provenance_bytes // 2 - len(empty))}, separators=(",", ":")
    )
    assert len(original.encode("utf-16le")) == provenance_bytes
    f.owner.execute(
        "UPDATE dbo.ExportJob SET ProvenanceJson=? WHERE JobID=?", original, f.values["JobID"]
    )
    f.apply()
    assert (
        f.owner.execute(
            "SELECT ProvenanceJson FROM dbo.ExportJob WHERE JobID=?", f.values["JobID"]
        ).fetchval()
        == original
    )
    assert f.owner.execute("SELECT COUNT(*) FROM dbo.ExportLegacyCloseout").fetchval() == 1
    assert (
        f.owner.execute(
            "SELECT COUNT(*) FROM dbo.ExportResource WHERE ActiveJobID IS NOT NULL"
        ).fetchval()
        == 0
    )
    dal = LegacyExportCloseoutDAL(f.connect, account="test-account", storage_owner="disk")
    assert dal.receipt_exists(f.values["JobID"])
    assert not LegacyExportCloseoutDAL(
        f.connect, account="another-account", storage_owner="disk"
    ).receipt_exists(f.values["JobID"])


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


def next_job(f, consumer="scan_data"):
    job, owner = str(uuid4()), str(uuid4())
    f.owner.execute(
        "INSERT dbo.ExportJob (JobID,ConsumerKind,AccountKey,DestinationSetHash,InputHash,SpoolKey,SpoolBytes,StorageOwner,EnqueueSequence,State,OwnerID,Fence,Version,CreatedUTC,UpdatedUTC,Actor,Reason,ProvenanceJson,KVK_NO) "
        "SELECT ?,?,AccountKey,DestinationSetHash,CAST(? AS binary(32)),'next-scan-input',SpoolBytes,StorageOwner,2,'running',?,3,1,CreatedUTC,UpdatedUTC,Actor,Reason,'{}',? FROM dbo.ExportJob WHERE JobID=?",
        job,
        consumer,
        b"n" * 32,
        owner,
        16 if consumer == "all_kvk" else None,
        f.f.job,
    )
    f.owner.execute(
        "INSERT dbo.ExportJobResource SELECT ?,ResourceKey FROM dbo.ExportJobResource WHERE JobID=?",
        job,
        f.f.job,
    )
    f.owner.execute(
        "UPDATE dbo.ExportResource SET ActiveJobID=?,OwnerID=?,Fence=3,Version=5", job, owner
    )
    return job, owner


def open_stream(f, object_id, owner, *, kind="job", purpose="mutation", account="test-account"):
    stream = str(uuid4())
    drain(
        f.app.execute(
            "EXEC dbo.usp_ExportExecutionStreamTransition @Action='open',@SessionID=?,@StreamID=?,"
            "@AccountKey=?,@ExpectedVersion=0,@OwnerKind=?,@ObjectID=?,@OwnerID=?,"
            "@Fence=3,@ClaimVersion=1,@Purpose=?,@ScopeJson=?,@ChildIdentity=?,@RegistrationHash=?,@SnapshotHash=?",
            f.f.session,
            stream,
            account,
            kind,
            object_id,
            owner,
            purpose,
            json.dumps(
                dict(
                    resources=[
                        dict(
                            key=(
                                "account:" + account
                                if r["key"].startswith("account:")
                                else r["key"]
                            ),
                            version=5,
                        )
                        for r in f.f.resources
                    ]
                )
            ),
            str(uuid4()),
            b"n" * 32,
            b"s" * 32,
        )
    )
    return stream


def event(
    f, stream, request, state, version, *, read=False, account="test-account", target="old-file"
):
    drain(
        f.app.execute(
            "EXEC dbo.usp_ExportProviderRequestEventAppend @SessionID=?,@StreamID=?,@AccountKey=?,"
            "@ExpectedVersion=?,@RequestID=?,@EventID=?,@State=?,@EvidenceHash=?,@EvidenceReference=?,"
            "@Operation=?,@RequestKind=?,@TargetID=?,@PayloadHash=?,@PayloadReference=?",
            f.f.session,
            stream,
            account,
            version,
            request,
            str(uuid4()),
            state,
            b"e" * 32,
            str(uuid4()),
            "sheets.get" if read else "sheets.values.update",
            "read" if read else "mutation",
            target,
            b"p" * 32,
            str(uuid4()),
        )
    )


@pytest.mark.parametrize(
    "kind,stage",
    [
        (kind, stage)
        for kind in ("job", "preparation")
        for stage in ("open", "prepared", "dispatch_intent")
    ]
    + [("job", "closeout")],
)
def test_other_account_cannot_use_released_target(installed, kind, stage):
    import pyodbc

    f = installed
    contain(f)
    f.apply()
    job, owner = next_job(f)
    object_id = job
    if kind == "preparation":
        object_id = str(uuid4())
        f.owner.execute(
            "INSERT dbo.ExportPreparation (PreparationID,AccountKey,ConsumerKind,RequestHash,EnqueueSequence,State,OwnerID,Fence,Version,StorageOwner,RequestJson,Actor,Reason,CreatedUTC,UpdatedUTC) "
            "VALUES (?,'test-account','config',?,2,'preflight',?,3,1,'disk','{}','test','configuration read',SYSUTCDATETIME(),SYSUTCDATETIME())",
            object_id,
            b"q" * 32,
            owner,
        )
        f.owner.execute(
            "INSERT dbo.ExportPreparationResource SELECT ?,ResourceKey FROM dbo.ExportJobResource WHERE JobID=?",
            object_id,
            job,
        )
        f.owner.execute("UPDATE dbo.ExportResource SET ActiveJobID=NULL,OwnerID=NULL")
    else:
        f.owner.execute(
            "INSERT dbo.ExportAttempt (AttemptID,JobID,ConsumerKind,AttemptNo,OwnerID,Fence,Phase,RemoteSequence,Version,CreatedUTC,UpdatedUTC,ManifestHash,ManifestJson,PartCount) "
            "SELECT NEWID(),JobID,ConsumerKind,1,OwnerID,3,'private_started',1,1,CreatedUTC,UpdatedUTC,CAST(? AS binary(32)),'{}',1 FROM dbo.ExportJob WHERE JobID=?",
            b"m" * 32,
            job,
        )
    purpose = "probe" if kind == "preparation" else "mutation"
    stream = None
    request = str(uuid4())
    if stage != "open":
        stream = open_stream(f, object_id, owner, kind=kind, purpose=purpose)
        if stage == "dispatch_intent":
            event(f, stream, request, "prepared", 1, read=kind == "preparation")
    # Model an otherwise valid account-B owner admitted by an older binary.
    # Only the fixture administrator may construct this historical state.
    f.owner.execute(
        "INSERT dbo.ExportResource (ResourceKey,ResourceKind,ActiveJobID,OwnerID,Fence,Version) "
        "SELECT 'account:other-account',ResourceKind,ActiveJobID,OwnerID,Fence,Version FROM dbo.ExportResource WHERE ResourceKey='account:test-account'"
    )
    f.owner.execute(
        "UPDATE dbo.ExportResource SET ActiveJobID=NULL,OwnerID=NULL,Version=Version+1 WHERE ResourceKey='account:test-account'"
    )
    f.owner.execute("UPDATE dbo.ExportJob SET AccountKey='other-account' WHERE JobID=?", job)
    f.owner.execute(
        "UPDATE dbo.ExportJobResource SET ResourceKey='account:other-account' WHERE JobID=? AND ResourceKey='account:test-account'",
        job,
    )
    if kind == "preparation":
        f.owner.execute(
            "UPDATE dbo.ExportPreparation SET AccountKey='other-account' WHERE PreparationID=?",
            object_id,
        )
        f.owner.execute(
            "UPDATE dbo.ExportPreparationResource SET ResourceKey='account:other-account' WHERE PreparationID=? AND ResourceKey='account:test-account'",
            object_id,
        )
    if stream:
        f.owner.execute(
            "UPDATE dbo.ExportExecutionStream SET AccountKey='other-account',ActiveAccountKey='other-account',ScopeJson=REPLACE(ScopeJson,'account:test-account','account:other-account') WHERE StreamID=?",
            stream,
        )
    before = f.owner.execute("SELECT COUNT(*) FROM dbo.ExportProviderRequestEvent").fetchval()
    if stage == "closeout":
        f.owner.execute(
            "UPDATE dbo.ExportExecutionStream SET State='closed',ActiveAccountKey=NULL,ClosureHash=?,ClosureReference=?,EventDigest=?,ClosedUTC=SYSUTCDATETIME() WHERE StreamID=?",
            b"c" * 32,
            str(uuid4()),
            b"e" * 32,
            stream,
        )
        f.owner.execute("UPDATE dbo.ExportJob SET State='uncertain',Version=2 WHERE JobID=?", job)
    with pytest.raises(
        pyodbc.Error, match="Another containment" if stage == "closeout" else "isolated target"
    ):
        if stage == "open":
            open_stream(f, object_id, owner, kind=kind, purpose=purpose, account="other-account")
        elif stage == "closeout":
            action = str(uuid4())
            f.apply(
                ActionID=action,
                Actor="recovery:" + action,
                JobID=job,
                AccountKey="other-account",
                OwnerID=owner,
                Fence=3,
                ExpectedVersion=2,
                ReceiptReference=str(uuid4()),
            )
        else:
            event(
                f,
                stream,
                request,
                stage,
                2 if stage == "dispatch_intent" else 1,
                read=kind == "preparation",
                account="other-account",
                target="healthy-file" if stage == "dispatch_intent" else "old-file",
            )
    assert (
        f.owner.execute("SELECT COUNT(*) FROM dbo.ExportProviderRequestEvent").fetchval() == before
    )
    assert f.owner.execute("SELECT COUNT(*) FROM dbo.ExportLegacyCloseout").fetchval() == 1


@pytest.mark.parametrize("consumer", ["scan_data", "all_kvk"])
def test_same_url_admission_returns_but_old_execution_remains_disabled(installed, consumer):
    import pyodbc

    f = installed
    contain(f)
    assert (
        f.app.execute("SELECT FileID FROM dbo.ExportActiveContainedTarget").fetchval() == "old-file"
    )
    f.apply()
    assert f.app.execute("SELECT COUNT(*) FROM dbo.ExportActiveContainedTarget").fetchval() == 0
    assert f.app.execute("SELECT FileID FROM dbo.ExportContainedTarget").fetchval() == "old-file"
    next_job_id, next_owner = next_job(f, consumer)
    next_stream = open_stream(f, next_job_id, next_owner)
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
    # A real restricted-account dispatch succeeds to the same old file. This
    # fixture never invokes a provider; it exercises the production SQL boundary.
    f.owner.execute(
        "INSERT dbo.ExportAttempt (AttemptID,JobID,ConsumerKind,AttemptNo,OwnerID,Fence,Phase,RemoteSequence,Version,CreatedUTC,UpdatedUTC,ManifestHash,ManifestJson,PartCount) "
        "SELECT NEWID(),?,?,1,?,3,'private_started',1,1,CreatedUTC,UpdatedUTC,CAST(? AS binary(32)),'{}',1 FROM dbo.ExportJob WHERE JobID=?",
        next_job_id,
        consumer,
        next_owner,
        b"m" * 32,
        next_job_id,
    )
    request = str(uuid4())
    for version, state in enumerate(("prepared", "dispatch_intent", "succeeded"), 1):
        event(f, next_stream, request, state, version)
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
    f.owner.execute(
        "UPDATE dbo.ExportJob SET State='uncertain',Version=2 WHERE JobID=?", next_job_id
    )
    action = str(uuid4())
    f.values.update(
        ActionID=action,
        JobID=next_job_id,
        ExpectedVersion=2,
        OwnerID=next_owner,
        Fence=3,
        ReceiptReference=str(uuid4()),
        Actor="recovery:" + action,
    )
    f.apply()
    assert f.app.execute("SELECT COUNT(*) FROM dbo.ExportLegacyCloseout").fetchval() == 2
    assert f.app.execute("SELECT COUNT(*) FROM dbo.ExportContainedTarget").fetchval() == 1
    assert f.app.execute("SELECT COUNT(*) FROM dbo.ExportProviderRequestEvent").fetchval() == 6


@pytest.mark.parametrize(
    "purpose,enrollment", [("probe", False), ("mutation", False), ("enrollment", True)]
)
def test_released_target_allows_only_configuration_reads(installed, purpose, enrollment):
    import pyodbc

    f = installed
    contain(f)
    f.apply()
    preparation, owner = str(uuid4()), str(uuid4())
    f.owner.execute(
        "INSERT dbo.ExportPreparation (PreparationID,AccountKey,ConsumerKind,RequestHash,EnqueueSequence,State,OwnerID,Fence,Version,StorageOwner,RequestJson,Actor,Reason,CreatedUTC,UpdatedUTC) "
        "VALUES (?,'test-account','config',?,2,'preflight',?,3,1,'disk',?,'test','configuration read',SYSUTCDATETIME(),SYSUTCDATETIME())",
        preparation,
        b"q" * 32,
        owner,
        json.dumps({"purpose": "output_enrollment"} if enrollment else {"kind": "config"}),
    )
    f.owner.execute(
        "INSERT dbo.ExportPreparationResource SELECT ?,ResourceKey FROM dbo.ExportJobResource WHERE JobID=?",
        preparation,
        f.f.job,
    )
    f.owner.execute("UPDATE dbo.ExportResource SET Version=5")
    if purpose != "probe":
        with pytest.raises(pyodbc.Error, match="Historical target isolation"):
            open_stream(f, preparation, owner, kind="preparation", purpose=purpose)
        return
    stream = open_stream(f, preparation, owner, kind="preparation", purpose="probe")
    request = str(uuid4())
    for version, state in enumerate(("prepared", "dispatch_intent", "succeeded"), 1):
        event(f, stream, request, state, version, read=True)
    with pytest.raises(pyodbc.Error, match="Stream cannot prepare"):
        event(f, stream, str(uuid4()), "prepared", 4)


@pytest.mark.parametrize("purpose", ["mutation", "probe"])
def test_managed_stream_cannot_reuse_released_legacy_target(installed, purpose):
    import pyodbc

    f = installed
    contain(f)
    f.apply()
    job, owner = next_job(f)
    f.owner.execute(
        "UPDATE dbo.ExportJob SET ConsumerKind='new_source',SourceKey='snapshot_report_v1',IntentID=?,KVK_NO=16,PoolEpoch=1 WHERE JobID=?",
        str(uuid4()),
        job,
    )
    with pytest.raises(pyodbc.Error, match="Historical target isolation"):
        open_stream(f, job, owner, purpose=purpose)


@pytest.mark.parametrize("state", ["prepared", "dispatch_intent"])
def test_already_open_managed_stream_cannot_dispatch_released_target(installed, state):
    import pyodbc

    f = installed
    contain(f)
    f.apply()
    job, owner = next_job(f)
    stream = open_stream(f, job, owner)
    request = str(uuid4())
    if state == "dispatch_intent":
        event(f, stream, request, "prepared", 1)
    # Construct an already-admitted managed stream at the SQL fixture boundary;
    # event admission must independently reject it before any provider dispatch.
    f.owner.execute(
        "UPDATE dbo.ExportJob SET ConsumerKind='new_source',SourceKey='snapshot_report_v1',IntentID=?,KVK_NO=16,PoolEpoch=1 WHERE JobID=?",
        str(uuid4()),
        job,
    )
    f.owner.execute("UPDATE dbo.ExportExecutionStream SET Epoch=1 WHERE StreamID=?", stream)
    with pytest.raises(pyodbc.Error, match="Historical target isolation"):
        event(f, stream, request, state, 2 if state == "dispatch_intent" else 1)


def test_managed_proof_still_refuses_historical_legacy_target(installed):
    import pyodbc

    f = installed
    contain(f)
    f.apply()
    f.owner.execute(
        "GRANT EXECUTE ON dbo.usp_ExportReconciliationProofIssue TO ExportExecutionAuthority"
    )
    with pytest.raises(pyodbc.Error, match="Isolated targets cannot establish"):
        f.app.execute(
            "EXEC dbo.usp_ExportReconciliationProofIssue @SessionID=?,@ProofID=?,@AccountKey='test-account',"
            "@SnapshotHash=?,@RegistrationHash=?,@ProofKind='publication',@Outcome='confirmed',@MembershipJson=?,@EvidenceJson=?",
            f.f.session,
            str(uuid4()),
            b"s" * 32,
            b"r" * 32,
            json.dumps(dict(version=2, targets=["old-file"], history={}, probe={})),
            json.dumps(dict(state="confirmed", snapshot_hash=(b"s" * 32).hex())),
        )


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
