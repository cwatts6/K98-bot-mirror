"""Permanent target fencing in session-local SQL objects; no installed changes.

Authoritative table checks and complete procedure bodies are executed. Foreign
keys to non-fixture objects and the role lookup alone are substituted. This is
transaction/dispatch evidence, not installation or production permission proof.
"""

from datetime import datetime
import json
import os
from pathlib import Path
import re
from types import SimpleNamespace
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import digest

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit local temporary SQL opt-in"
)

TABLES = (
    "dbo.ExportJob",
    "dbo.ExportJobResource",
    "dbo.ExportResource",
    "dbo.ExportPreparation",
    "dbo.ExportPreparationResource",
    "dbo.ExportAttempt",
    "dbo.ExportExecutionSession",
    "dbo.ExportExecutionStream",
    "dbo.ExportProviderRequest",
    "dbo.ExportProviderRequestEvent",
    "dbo.ExportTargetContainment",
    "dbo.ExportContainedTarget",
    "dbo.ExportContainedStream",
    "dbo.ExportManagedFileOrigin",
    "dbo.ExportManualFileOrigin",
    "KVK.SourceOutputPool",
    "KVK.SourceOutputSlot",
    "KVK.SourceOutputOperation",
    "KVK.SourceOutputOperationResource",
    "KVK.SourceDelivery",
)
PROCEDURES = (
    "dbo.usp_ExportJobContainTargets",
    "dbo.usp_ExportExecutionStreamTransition",
    "dbo.usp_ExportProviderRequestEventAppend",
)
ROLE_CHECK = "IF IS_ROLEMEMBER(N'ExportExecutionAuthority')<>1 OR IS_ROLEMEMBER(N'ExportExecutionAuthority') IS NULL"


def local_sql(text):
    for name in sorted((*TABLES, *PROCEDURES), key=len, reverse=True):
        text = re.sub(r"\b" + re.escape(name) + r"\b", "#" + name.split(".")[1], text)
    return text


@pytest.fixture
def contained_job():
    import pyodbc

    root = Path(os.environ["K98_TARGET_CONTAINMENT_SQL_SOURCE"]) / "sql_schema"
    sql = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\\K98DEV;DATABASE=master;"
        "Trusted_Connection=yes;TrustServerCertificate=yes",
        autocommit=True,
        timeout=5,
    )
    try:
        for name in TABLES:
            source = (root / (name + ".Table.sql")).read_text(encoding="utf-8-sig")
            source = "\n".join(line for line in source.splitlines() if "FOREIGN KEY" not in line)
            sql.execute(local_sql(re.sub(r",\s*\);", "\n);", source)))
        for name in PROCEDURES:
            source = (root / (name + ".StoredProcedure.sql")).read_text(encoding="utf-8-sig")
            body = source[source.index("CREATE PROCEDURE") :].strip().removesuffix("GO").strip()
            assert body.count(ROLE_CHECK) == 1
            rewritten = local_sql(body.replace(ROLE_CHECK, "IF 1=0", 1))
            assert not re.search(r"\b(?:dbo|KVK)\.[A-Za-z_]", rewritten)
            sql.execute(rewritten)

        def insert(table, data):
            columns = list(data)
            placeholders = [
                "CAST(? AS binary(32))" if isinstance(data[c], bytes) else "?" for c in columns
            ]
            sql.execute(
                f"INSERT #{table} ({','.join(columns)}) VALUES ({','.join(placeholders)})",
                *data.values(),
            )

        class Cursor:
            def __init__(self):
                self.inner = sql.cursor()

            def execute(self, statement, *args):
                rewritten = local_sql(statement)
                assert not re.search(r"\b(?:dbo|KVK)\.[A-Za-z_]", rewritten)
                self.inner.execute(rewritten, *args)
                return self

            def __getattr__(self, name):
                return getattr(self.inner, name)

        class Connection:
            @property
            def autocommit(self):
                return sql.autocommit

            @autocommit.setter
            def autocommit(self, value):
                sql.autocommit = value

            def cursor(self):
                return Cursor()

            def commit(self):
                sql.commit()

            def rollback(self):
                sql.rollback()

            def close(self):
                pass  # Fixture owns the temporary-table session.

        def connect():
            sql.autocommit = False
            return Connection()

        now = datetime(2026, 10, 1)
        job_id, owner, session, stream, child = (str(uuid4()) for _ in range(5))
        resources = [
            dict(key="account:test-account", version=3),
            dict(key="destination:old-file", version=3),
        ]
        insert(
            "ExportJob",
            dict(
                JobID=job_id,
                ConsumerKind="scan_data",
                AccountKey="test-account",
                DestinationSetHash=digest(["old-file"]),
                InputHash=digest("retained-input"),
                SpoolKey="retained-input",
                SpoolBytes=10,
                StorageOwner="disk",
                EnqueueSequence=1,
                State="uncertain",
                OwnerID=owner,
                Fence=2,
                Version=7,
                CreatedUTC=now,
                UpdatedUTC=now,
                Actor="test",
                Reason="temporary SQL fixture",
                ProvenanceJson="{}",
            ),
        )
        for r in resources:
            insert(
                "ExportResource",
                dict(
                    ResourceKey=r["key"],
                    ResourceKind=r["key"].split(":")[0],
                    ActiveJobID=job_id,
                    OwnerID=owner,
                    Fence=2,
                    Version=r["version"],
                ),
            )
            insert("ExportJobResource", dict(JobID=job_id, ResourceKey=r["key"]))
        insert(
            "ExportExecutionSession",
            dict(
                SessionID=session,
                AuthorityPrincipal=sql.execute("SELECT USER_NAME()").fetchval(),
                HostIdentity="test-host",
                BootID=str(uuid4()),
                ExecutableHash=b"e" * 32,
                ManifestHash=b"m" * 32,
                ProtocolVersion=1,
                State="open",
                Version=1,
                CreatedUTC=now,
            ),
        )
        insert(
            "ExportExecutionStream",
            dict(
                StreamID=stream,
                SessionID=session,
                AccountKey="test-account",
                ActiveAccountKey="test-account",
                JobID=job_id,
                OwnerID=owner,
                Fence=2,
                ClaimVersion=6,
                RegistrationHash=b"r" * 32,
                SnapshotHash=b"s" * 32,
                ScopeJson=json.dumps(dict(resources=resources)),
                Purpose="mutation",
                State="frozen",
                Version=5,
                LastSequence=1,
                ChildIdentity=child,
                CreatedUTC=now,
            ),
        )
        request = str(uuid4())
        insert(
            "ExportProviderRequest",
            dict(
                RequestID=request,
                StreamID=stream,
                Sequence=1,
                Operation="sheets.values.update",
                RequestKind="mutation",
                TargetID="old-file",
                PayloadHash=b"p" * 32,
                PayloadReference=str(uuid4()),
                CreatedUTC=now,
            ),
        )
        for sequence, state in enumerate(("prepared", "dispatch_intent", "unknown"), 1):
            insert(
                "ExportProviderRequestEvent",
                dict(
                    EventID=str(uuid4()),
                    RequestID=request,
                    EventSequence=sequence,
                    State=state,
                    EvidenceHash=b"e" * 32,
                    EvidenceReference=str(uuid4()),
                    CreatedUTC=now,
                ),
            )
        arguments = dict(
            ContainmentID=str(uuid4()),
            AccountKey="test-account",
            JobID=job_id,
            OwnerID=owner,
            Fence=2,
            ExpectedVersion=7,
            SnapshotHash=b"s" * 32,
            ReceiptHash=b"h" * 32,
            ReceiptReference=str(uuid4()),
            ResourcesJson=json.dumps(resources),
            StreamsJson=json.dumps(
                [dict(stream_id=stream, version=5, last_sequence=1, event_digest=(b"d" * 32).hex())]
            ),
            Actor="recovery:test-action",
            Reason="Retire old targets",
            RegistrationHash=b"r" * 32,
            StorageOwner="disk",
        )

        def apply(**changes):
            values = arguments | changes
            # T-SQL EXEC parameters cannot be arbitrary expressions; bind binary
            # values directly through ODBC, which preserves the fixed byte width.
            names = ["@" + key + "=?" for key in values]
            sql.execute("BEGIN TRANSACTION")
            try:
                result = sql.execute(
                    "EXEC #usp_ExportJobContainTargets " + ",".join(names), *values.values()
                ).fetchone()
                sql.execute("COMMIT")
                return result
            except Exception:
                sql.execute("IF @@TRANCOUNT>0 ROLLBACK")
                raise

        yield SimpleNamespace(
            sql=sql,
            connect=connect,
            apply=apply,
            arguments=arguments,
            insert=insert,
            resources=resources,
            job=job_id,
            owner=owner,
            session=session,
            stream=stream,
            request=request,
            child=child,
        )
    finally:
        sql.close()


def assert_untouched(f):
    assert f.sql.execute("SELECT COUNT(*) FROM #ExportTargetContainment").fetchval() == 0
    assert f.sql.execute("SELECT COUNT(*) FROM #ExportContainedTarget").fetchval() == 0
    assert f.sql.execute("SELECT COUNT(*) FROM #ExportContainedStream").fetchval() == 0
    assert f.sql.execute("SELECT State FROM #ExportExecutionStream").fetchval() == "frozen"
    assert (
        f.sql.execute("SELECT COUNT(*) FROM #ExportResource WHERE OwnerID IS NOT NULL").fetchval()
        == 2
    )


def test_retirement_preserves_unknown_write_and_releases_only_exact_reservations(contained_job):
    f = contained_job
    original = [
        tuple(r)
        for r in f.sql.execute("SELECT * FROM #ExportProviderRequestEvent ORDER BY EventSequence")
    ]
    f.apply()
    assert f.sql.execute("SELECT FileID FROM #ExportContainedTarget").fetchval() == "old-file"
    assert tuple(
        f.sql.execute(
            "SELECT State,Version,ActiveAccountKey FROM #ExportExecutionStream"
        ).fetchone()
    ) == ("target_contained", 6, None)
    assert tuple(f.sql.execute("SELECT State,Version,SpoolKey FROM #ExportJob").fetchone()) == (
        "uncertain",
        8,
        "retained-input",
    )
    assert (
        f.sql.execute("SELECT COUNT(*) FROM #ExportResource WHERE OwnerID IS NOT NULL").fetchval()
        == 0
    )
    assert [
        tuple(r)
        for r in f.sql.execute("SELECT * FROM #ExportProviderRequestEvent ORDER BY EventSequence")
    ] == original
    # A lost acknowledgement must be resolved from this immutable decision; it
    # cannot produce another release after somebody else acquires the account.
    next_owner = str(uuid4())
    f.sql.execute(
        "UPDATE #ExportResource SET OwnerID=?,ActiveJobID=?,Fence=3,Version=5 WHERE ResourceKey='account:test-account'",
        next_owner,
        str(uuid4()),
    )
    import pyodbc

    with pytest.raises(pyodbc.Error):
        f.apply()
    assert (
        str(
            f.sql.execute(
                "SELECT OwnerID FROM #ExportResource WHERE ResourceKey='account:test-account'"
            ).fetchval()
        ).lower()
        == next_owner
    )
    assert f.sql.execute("SELECT COUNT(*) FROM #ExportTargetContainment").fetchval() == 1


@pytest.mark.parametrize(
    "change",
    [
        {"ExpectedVersion": 8},
        {"Fence": 3},
        {"AccountKey": "foreign"},
        {"OwnerID": str(uuid4())},
        {"RegistrationHash": b"x" * 32},
        {"StorageOwner": "foreign"},
        {"PoolID": str(uuid4())},
    ],
)
def test_foreign_or_stale_confirmation_is_atomic(contained_job, change):
    import pyodbc

    with pytest.raises(pyodbc.Error):
        contained_job.apply(**change)
    assert_untouched(contained_job)


@pytest.mark.parametrize(
    "fault",
    [
        "short_hash",
        "long_hash",
        "non_hex",
        "duplicate_field",
        "missing_stream",
        "extra_resource",
        "long_resource",
        "wrong_version_type",
    ],
)
def test_exact_json_evidence_cannot_be_truncated_or_coerced(contained_job, fault):
    import pyodbc

    f = contained_job
    streams = json.loads(f.arguments["StreamsJson"])
    resources = json.loads(f.arguments["ResourcesJson"])
    if fault == "short_hash":
        streams[0]["event_digest"] = "ab"
    elif fault == "long_hash":
        streams[0]["event_digest"] += "ab"
    elif fault == "non_hex":
        streams[0]["event_digest"] = "x" * 64
    elif fault == "missing_stream":
        streams = []
    elif fault == "extra_resource":
        resources.append(dict(key="destination:another-file", version=1))
    elif fault == "long_resource":
        resources[1]["key"] += "x" * 256
    elif fault == "wrong_version_type":
        resources[1]["version"] = "3"
    encoded = json.dumps(streams)
    if fault == "duplicate_field":
        encoded = encoded.replace('"version": 5', '"version": 5, "version": 5')
    with pytest.raises(pyodbc.Error):
        f.apply(ResourcesJson=json.dumps(resources), StreamsJson=encoded)
    assert_untouched(f)


def test_late_failure_rolls_back_every_fence_and_release(contained_job):
    import pyodbc

    f = contained_job
    f.sql.execute("ALTER TABLE #ExportJob ADD CHECK (Version=7)")
    with pytest.raises(pyodbc.Error):
        f.apply()
    assert_untouched(f)


@pytest.mark.parametrize("state", ["prepared", "dispatch_intent", "succeeded"])
def test_old_child_cannot_append_after_containment(contained_job, state):
    import pyodbc

    f = contained_job
    f.apply()
    with pytest.raises(pyodbc.Error):
        f.sql.execute(
            "EXEC #usp_ExportProviderRequestEventAppend @SessionID=?,@StreamID=?,@AccountKey='test-account',"
            "@ExpectedVersion=6,@RequestID=?,@EventID=?,@State=?,@EvidenceHash=?,@EvidenceReference=?",
            f.session,
            f.stream,
            f.request,
            str(uuid4()),
            state,
            b"z" * 32,
            str(uuid4()),
        )
    assert f.sql.execute("SELECT COUNT(*) FROM #ExportProviderRequestEvent").fetchval() == 3


def test_new_account_cannot_open_a_stream_for_retired_file(contained_job):
    import pyodbc

    f = contained_job
    f.apply()
    # The permanent global guard runs before owner checks. Changing every owner
    # field still cannot re-admit the physical file.
    with pytest.raises(pyodbc.Error, match="permanently isolated target"):
        f.sql.execute(
            "EXEC #usp_ExportExecutionStreamTransition @Action='open',@SessionID=?,@StreamID=?,"
            "@AccountKey='other-account',@ExpectedVersion=0,@OwnerKind='job',@ObjectID=?,@OwnerID=?,"
            "@Fence=1,@ClaimVersion=1,@Purpose='mutation',@ScopeJson=?,@ChildIdentity=?,@RegistrationHash=?,@SnapshotHash=?",
            f.session,
            str(uuid4()),
            str(uuid4()),
            str(uuid4()),
            json.dumps(
                dict(
                    resources=[
                        dict(key="account:other-account", version=1),
                        dict(key="destination:old-file", version=1),
                    ]
                )
            ),
            str(uuid4()),
            b"r" * 32,
            b"s" * 32,
        )
    assert f.sql.execute("SELECT COUNT(*) FROM #ExportExecutionStream").fetchval() == 1


def test_unrelated_target_can_open_after_atomic_release(contained_job):
    f = contained_job
    f.apply()
    next_job, next_owner, next_stream = (str(uuid4()) for _ in range(3))
    f.sql.execute(
        "INSERT #ExportJob (JobID,ConsumerKind,AccountKey,DestinationSetHash,InputHash,SpoolKey,SpoolBytes,StorageOwner,EnqueueSequence,State,OwnerID,Fence,Version,CreatedUTC,UpdatedUTC,Actor,Reason,ProvenanceJson) "
        "SELECT ?,'scan_data',AccountKey,CAST(? AS binary(32)),InputHash,SpoolKey,SpoolBytes,StorageOwner,2,'running',?,3,1,CreatedUTC,UpdatedUTC,Actor,Reason,'{}' FROM #ExportJob WHERE JobID=?",
        next_job,
        digest(["unrelated-file"]),
        next_owner,
        f.job,
    )
    f.insert(
        "ExportResource",
        dict(
            ResourceKey="destination:unrelated-file",
            ResourceKind="destination",
            ActiveJobID=next_job,
            OwnerID=next_owner,
            Fence=3,
            Version=1,
        ),
    )
    f.sql.execute(
        "UPDATE #ExportResource SET ActiveJobID=?,OwnerID=?,Fence=3,Version=5 WHERE ResourceKey='account:test-account'",
        next_job,
        next_owner,
    )
    for key in ("account:test-account", "destination:unrelated-file"):
        f.insert("ExportJobResource", dict(JobID=next_job, ResourceKey=key))
    f.sql.execute(
        "EXEC #usp_ExportExecutionStreamTransition @Action='open',@SessionID=?,@StreamID=?,"
        "@AccountKey='test-account',@ExpectedVersion=0,@OwnerKind='job',@ObjectID=?,@OwnerID=?,"
        "@Fence=3,@ClaimVersion=1,@Purpose='mutation',@ScopeJson=?,@ChildIdentity=?,@RegistrationHash=?,@SnapshotHash=?",
        f.session,
        next_stream,
        next_job,
        next_owner,
        json.dumps(
            dict(
                resources=[
                    dict(key="account:test-account", version=5),
                    dict(key="destination:unrelated-file", version=1),
                ]
            )
        ),
        str(uuid4()),
        b"n" * 32,
        b"s" * 32,
    )
    assert (
        f.sql.execute(
            "SELECT State FROM #ExportExecutionStream WHERE StreamID=?", next_stream
        ).fetchval()
        == "open"
    )
    assert (
        f.sql.execute(
            "SELECT State FROM #ExportExecutionStream WHERE StreamID=?", f.stream
        ).fetchval()
        == "target_contained"
    )


@pytest.mark.parametrize("foreign", [False, True])
def test_late_request_outside_complete_target_set_keeps_ownership(contained_job, foreign):
    import pyodbc

    f = contained_job
    if foreign:
        f.sql.execute("UPDATE #ExportProviderRequest SET TargetID='foreign-file'")
    else:
        f.sql.execute("UPDATE #ExportProviderRequest SET Operation='sheets.create'")
    with pytest.raises(pyodbc.Error, match="escaped"):
        f.apply()
    assert_untouched(f)


def pool_job(f):
    """Extend the temporary job into a complete registered source pool."""
    pool = str(uuid4())
    choice = str(uuid4())
    now = datetime(2026, 10, 1)
    f.sql.execute(
        "UPDATE #ExportJob SET ConsumerKind='new_source',SourceKey='snapshot_report_v1',IntentID=?,KVK_NO=7,PoolEpoch=4,StorageOwner=NULL,SpoolKey=NULL,SpoolBytes=NULL",
        str(uuid4()),
    )
    f.sql.execute("UPDATE #ExportExecutionStream SET Epoch=4")
    f.insert(
        "SourceOutputPool",
        dict(
            PoolID=pool,
            IndexFileID="old-file",
            IndexFileKind="index",
            RegistrationNo=1,
            AccountKey="test-account",
            AccountResourceKey="account:test-account",
            ExpectedOwner="owner@example.test",
            AudienceJson='{"kind":"private"}',
            SourceKey="snapshot_report_v1",
            ActiveKVK=7,
            ChoiceID=choice,
            Epoch=4,
            PoolState="active",
            Fence=0,
            Version=9,
            CreatedUTC=now,
            UpdatedUTC=now,
            RegistrationHash=b"r" * 32,
            RegistrationJson="{}",
        ),
    )
    for number in (1, 2):
        file_id = f"old-slot-{number}"
        f.insert(
            "SourceOutputSlot",
            dict(
                FileID=file_id,
                FileKind="slot",
                PoolID=pool,
                SlotNo=number,
                Epoch=4,
                State="quarantined",
                Fence=0,
                Version=3,
                QuarantineReason="Original uncertainty",
                CreatedUTC=now,
                UpdatedUTC=now,
            ),
        )
        key = "destination:" + file_id
        f.insert(
            "ExportResource",
            dict(
                ResourceKey=key,
                ResourceKind="destination",
                ActiveJobID=f.job,
                OwnerID=f.owner,
                Fence=2,
                Version=3,
            ),
        )
        f.insert("ExportJobResource", dict(JobID=f.job, ResourceKey=key))
        f.resources.append(dict(key=key, version=3))
    slots = [tuple(r) for r in f.sql.execute("SELECT * FROM #SourceOutputSlot ORDER BY SlotNo")]
    f.sql.execute(
        "UPDATE #ExportExecutionStream SET ScopeJson=?", json.dumps(dict(resources=f.resources))
    )
    f.sql.execute(
        "UPDATE #ExportJob SET DestinationSetHash=CAST(? AS binary(32))",
        digest(["old-file", "old-slot-1", "old-slot-2"]),
    )
    return pool, slots


@pytest.mark.parametrize(
    "dimension", ["version", "epoch", "season", "registration", "membership", None]
)
def test_pool_retirement_requires_exact_identity_and_preserves_slot_history(
    contained_job, dimension
):
    import pyodbc

    f = contained_job
    pool, slots = pool_job(f)
    if dimension == "membership":
        f.sql.execute("UPDATE #SourceOutputPool SET IndexFileID='other-index'")
    changes = dict(
        StorageOwner=None, PoolID=pool, PoolVersion=9, ResourcesJson=json.dumps(f.resources)
    )
    if dimension == "version":
        changes["PoolVersion"] = 10
    elif dimension == "epoch":
        f.sql.execute("UPDATE #SourceOutputPool SET Epoch=5")
    elif dimension == "season":
        f.sql.execute("UPDATE #SourceOutputPool SET ActiveKVK=8")
    elif dimension == "registration":
        f.sql.execute(
            "UPDATE #SourceOutputPool SET RegistrationHash=CAST(? AS binary(32))", b"x" * 32
        )
    if dimension:
        with pytest.raises(pyodbc.Error):
            f.apply(**changes)
        assert f.sql.execute("SELECT COUNT(*) FROM #ExportTargetContainment").fetchval() == 0
        assert (
            f.sql.execute(
                "SELECT COUNT(*) FROM #ExportResource WHERE OwnerID IS NOT NULL"
            ).fetchval()
            == 4
        )
    else:
        f.apply(**changes)
        assert tuple(
            f.sql.execute("SELECT PoolState,Version FROM #SourceOutputPool").fetchone()
        ) == ("blocked", 10)
        assert f.sql.execute("SELECT COUNT(*) FROM #ExportContainedTarget").fetchval() == 3
    assert [
        tuple(r) for r in f.sql.execute("SELECT * FROM #SourceOutputSlot ORDER BY SlotNo")
    ] == slots
