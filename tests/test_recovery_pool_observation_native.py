"""Real recovery/pool tuples in a newly owned disposable snapshot database."""

from pathlib import Path
import re
from types import SimpleNamespace
from uuid import uuid4

import pytest

from kvk.dal import source_output_pool_dal as pools
from kvk.dal.new_source_import_dal import SourceConflict, digest
from services import export_recovery_dal as recovery
from tests import test_queue_observation_native as queue_fixture

EXTRA_TABLES = (
    "dbo.ExportLegacyCloseout",
    "dbo.ExportReplacementPlan",
    "dbo.ExportTargetContainment",
    "dbo.ExportExecutionStream",
    "dbo.ExportContainedTarget",
    "KVK.SeasonSource",
    "KVK.SourceOutputOperationResource",
    "KVK.SourceOutputFile",
)


@pytest.fixture(scope="module")
def database(snapshot_database):
    import pyodbc

    queue_fixture.database.__wrapped__(snapshot_database)
    cn = pyodbc.connect(snapshot_database.connection_string, autocommit=True, timeout=5)
    try:
        for name in EXTRA_TABLES:
            text = (Path("C:/K98-bot-SQL-Server/sql_schema") / (name + ".Table.sql")).read_text(
                encoding="utf-8-sig"
            )
            body = re.search(r"CREATE TABLE " + re.escape(name) + r"\s*\(.*?\n\);", text, re.S)
            assert body, name
            sql = "\n".join(line for line in body[0].splitlines() if "FOREIGN KEY" not in line)
            cn.execute(re.sub(r",\s*\);", "\n);", sql))
    finally:
        cn.close()
    return snapshot_database


@pytest.fixture
def state(database):
    generator = queue_fixture.state.__wrapped__(database)
    s = next(generator)
    try:
        for name in EXTRA_TABLES:
            s.root.execute("DELETE " + name)
        s.root.execute(
            "INSERT KVK.SeasonSource SELECT 16,'snapshot_report_v1',ChoiceID,'test',GETUTCDATE(),'fixture','{}','open',1 FROM KVK.SourceOutputPool"
        )
        op = str(uuid4())
        row = dict(
            OperationID=op,
            PoolID=s.pool,
            AccountKey="a",
            SourceKey="snapshot_report_v1",
            OldKVK=16,
            OldChoiceID=str(uuid4()),
            NewKVK=17,
            NewChoiceID=str(uuid4()),
            OldEpoch=1,
            TargetEpoch=2,
            PlanHash=digest({}),
            PlanJson="{}",
            ConfirmedBy="test",
            GuildID="1",
            ChannelID="1",
            Reason="fixture",
            ConfirmedUTC=s.stamp,
            EnqueueSequence=1,
            State="closing",
            ActivePoolID=s.pool,
            Fence=0,
            Version=1,
            Phase="draining",
            ProgressJson="{}",
            UpdatedUTC=s.stamp,
        )
        s.insert("KVK.SourceOutputOperation", row)
        # Match the registered complete resource set, including its slot.
        s.root.execute("UPDATE dbo.ExportJob SET DestinationSetHash=?", digest(["index", "slot"]))
        s.insert(
            "dbo.ExportResource",
            dict(ResourceKey="destination:slot", ResourceKind="destination", Fence=0, Version=1),
        )
        s.insert("dbo.ExportJobResource", dict(JobID=s.job, ResourceKey="destination:slot"))
        config = dict(
            account="a",
            storage_owner="fixture",
            pools=[dict(pool_id=s.pool, index_file_id="index", slot_file_ids=["slot"])],
        )
        s.recovery = recovery.ExportRecoveryDAL(
            s.dal.connect, registration=SimpleNamespace(value=lambda: config)
        )
        s.pools = pools.SourceOutputPoolDAL(s.dal.connect)
        s.operation = op
        yield s
    finally:
        generator.close()


def assert_closed(state):
    import pyodbc

    for cn in state.handles:
        with pytest.raises(pyodbc.ProgrammingError):
            cn.cursor()


def test_writer_first_all_standalone_reads_are_nonblocking(state):
    s = state
    s.root.execute("BEGIN TRANSACTION")
    try:
        s.root.execute("UPDATE dbo.ExportJob SET Version=2")
        s.root.execute("UPDATE KVK.SourceOutputPool SET Version=2")
        s.root.execute("UPDATE KVK.SourceOutputOperation SET Version=2")
        s.root.execute("UPDATE KVK.SeasonSource SET SeasonVersion=2")
        assert s.recovery.pending_jobs() == [s.job]
        assert s.recovery.published_outputs(after=s.job) == []
        assert s.recovery.pending_rollovers() == [s.operation]
        assert s.recovery.job(s.job)["job"]["Version"] == 1
        assert s.recovery.repairs(s.job) == []
        assert s.pools.snapshot(s.pool)["pool"]["Version"] == 1
        assert s.pools.choice(16)["SourceKey"] == "snapshot_report_v1"
        assert s.pools.resolve(16) == s.pool
        assert s.pools.is_index("index")
        assert s.pools.pending("a") == (s.operation,)
        assert s.pools.completed_setup(s.pool) is None
        assert s.pools.export_context(s.pool)["pool"]["Version"] == 1
        assert s.pools.operation(s.operation)["Version"] == 1
        assert s.pools.operation_snapshot(s.operation)["operation"]["Version"] == 1
        assert s.pools.drain_snapshot(s.operation)["pool"]["Version"] == 1
        assert s.pools.files(s.operation) == ()
        assert_closed(s)
    finally:
        s.root.execute("ROLLBACK")


@pytest.mark.parametrize("kind", ["recovery", "pool"])
def test_observer_first_keeps_complete_tuple_across_commit(state, monkeypatch, kind):
    s = state
    module = recovery if kind == "recovery" else pools
    original = module.one
    fired = False

    def one(cursor):
        nonlocal fired
        row = original(cursor)
        if row and not fired:
            fired = True
            s.root.execute("BEGIN TRANSACTION")
            s.root.execute("UPDATE dbo.ExportJob SET Version=2")
            s.root.execute("UPDATE dbo.ExportResource SET Version=2")
            s.root.execute("UPDATE KVK.SeasonSource SET SeasonVersion=2")
            s.root.execute("UPDATE KVK.SourceOutputPool SET Version=2")
            s.root.execute("UPDATE KVK.SourceOutputOperation SET Version=2")
            s.root.execute("COMMIT")
        return row

    monkeypatch.setattr(module, "one", one)
    if kind == "recovery":
        old = s.recovery.job(s.job)
        new = s.recovery.job(s.job)
        for value, expected in ((old, 1), (new, 2)):
            assert value["job"]["Version"] == value["season"]["SeasonVersion"] == expected
            assert {r["Version"] for r in value["resources"]} == {expected}
    else:
        old = s.pools.operation_snapshot(s.operation)
        new = s.pools.operation_snapshot(s.operation)
        for value, expected in ((old, 1), (new, 2)):
            assert value["operation"]["Version"] == value["pool"]["pool"]["Version"] == expected
    assert_closed(s)


@pytest.mark.parametrize("corruption", ["membership", "account", "plan", "registration"])
def test_scope_and_immutable_hash_checks_remain_closed(state, corruption):
    s = state
    if corruption == "membership":
        s.root.execute("DELETE dbo.ExportJobResource WHERE ResourceKey='destination:slot'")
    elif corruption == "account":
        s.root.execute("UPDATE dbo.ExportJob SET AccountKey='foreign'")
    elif corruption == "plan":
        s.root.execute("UPDATE KVK.SourceOutputOperation SET PlanHash=?", b"x" * 32)
    else:
        s.root.execute("UPDATE KVK.SourceOutputPool SET RegistrationHash=?", b"x" * 32)
    with pytest.raises(SourceConflict):
        if corruption in {"membership", "account"}:
            s.recovery.job(s.job)
        else:
            s.pools.operation_snapshot(s.operation)
    assert_closed(s)


def test_recovery_permission_failure_physically_closes(state):
    import pyodbc

    s = state
    s.root.execute("DENY SELECT ON dbo.ExportContainedTarget TO preview_reader")
    try:
        with pytest.raises(pyodbc.Error):
            s.recovery.job(s.job)
        assert_closed(s)
    finally:
        s.root.execute("REVOKE SELECT ON dbo.ExportContainedTarget TO preview_reader")


def test_stale_pool_preview_cannot_close_admission(state):
    s = state
    old = s.pools.snapshot(s.pool)
    s.root.execute("UPDATE KVK.SourceOutputPool SET Version=2")
    writer = pools.SourceOutputPoolDAL(s.mutation.connect)
    with pytest.raises(SourceConflict, match="Preview is stale"):
        writer.confirm(str(uuid4()), dict(snapshot=old))
    assert s.root.execute("SELECT PoolState FROM KVK.SourceOutputPool").fetchval() == "active"
    assert s.root.execute("SELECT COUNT(*) FROM KVK.SourceOutputOperation").fetchval() == 1
