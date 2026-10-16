"""Actual containment procedure on session-local SQL tables; no provider writes."""

from datetime import datetime
import json
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit, digest
from kvk.dal.source_output_pool_dal import SourceOutputPoolDAL
from services.rollover_containment import RolloverContainment
from services.rollover_containment_dal import RolloverContainmentDAL
from tests import test_export_target_containment_sql as fixture_module
from tests.test_export_replacement_pool_sql import recovery as pool_recovery

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)


@pytest.fixture
def contained_job(monkeypatch):
    monkeypatch.setattr(fixture_module, "TEMP_TABLE_PARAMETER_METADATA", True)
    monkeypatch.setattr(fixture_module, "TABLES", (*fixture_module.TABLES, "dbo.ExportAttemptPart"))
    monkeypatch.setattr(
        fixture_module,
        "PROCEDURES",
        (*fixture_module.PROCEDURES, "dbo.usp_ExportRolloverContainTargets"),
    )
    yield from fixture_module.contained_job.__wrapped__()


@pytest.fixture
def recovery(contained_job):
    service, f, docs = pool_recovery.__wrapped__(contained_job)
    f.sql.execute("UPDATE #ExportJob SET State='confirmed'")
    pools = SourceOutputPoolDAL(f.connect, execution_evidence=True)
    pool_id = str(f.sql.execute("SELECT PoolID FROM #SourceOutputPool").fetchval()).lower()
    f.sql.commit()
    before = pools.snapshot(pool_id)
    # The legacy fixture insert helper owns short cursors; use autocommit for
    # seeding so cursor cancellation cannot hide an unconsumed DML result.
    f.sql.autocommit = True
    plan = dict(snapshot=before, new_kvk=8, new_choice_id=str(uuid4()))
    op_id = str(uuid4())
    now = datetime(2026, 10, 1)
    f.insert(
        "SourceOutputOperation",
        dict(
            OperationID=op_id,
            PoolID=pool_id,
            AccountKey="test-account",
            SourceKey="snapshot_report_v1",
            OldKVK=7,
            OldChoiceID=before["pool"]["ChoiceID"],
            NewKVK=8,
            NewChoiceID=plan["new_choice_id"],
            OldEpoch=4,
            TargetEpoch=5,
            PlanHash=digest(plan),
            PlanJson=json.dumps(plan),
            ConfirmedBy="admin",
            GuildID="1",
            ChannelID="2",
            Reason="Synthetic rollover",
            ConfirmedUTC=now,
            EnqueueSequence=2,
            State="uncertain",
            ActivePoolID=pool_id,
            OwnerID=f.owner,
            Fence=2,
            Version=7,
            Phase="uncertain",
            ProgressJson="{}",
            UpdatedUTC=now,
        ),
    )
    for resource in f.resources:
        key = resource["key"]
        file_id = key[12:] if key.startswith("destination:") else None
        f.insert(
            "SourceOutputOperationResource",
            dict(
                OperationID=op_id,
                PoolID=pool_id,
                AccountKey="test-account",
                ResourceKey=key,
                ResourceKind="destination" if file_id else "account",
                FileID=file_id,
                IndexFileID=file_id if file_id == "old-file" else None,
                SlotFileID=file_id if file_id and file_id != "old-file" else None,
            ),
        )
    f.sql.execute("UPDATE #ExportResource SET ActiveJobID=NULL,ActiveOutputOperationID=?", op_id)
    f.sql.execute("UPDATE #SourceOutputPool SET PoolState='closing',OwnerID=?,Fence=2", op_id)
    f.sql.execute("UPDATE #ExportExecutionStream SET JobID=NULL,OutputOperationID=?", op_id)
    f.sql.commit()
    assert (
        f.sql.execute(
            "SELECT COUNT(*) FROM #SourceOutputOperation WHERE OperationID=?", op_id
        ).fetchval()
        == 1
    )
    result = RolloverContainment(
        pools=pools,
        dal=RolloverContainmentDAL(f.connect),
        discovery=service.discovery,
        execution=service.execution,
        store=service.store,
        registration=service.registration,
    )
    f.operation, f.pool = op_id, pool_id
    return result, f, docs


def test_isolates_complete_pool_preserving_uncertain_history(recovery):
    service, f, docs = recovery
    report = service.inspect(f.operation)
    args = dict(
        token=report["token"], actor="recovery:" + str(uuid4()), reason="Retire uncertain pool"
    )
    result = service.apply(f.operation, **args)
    assert result["outcome"] == "targets_isolated" and result["business_resolved"] is False
    assert service.apply(f.operation, **args) == result
    assert len(docs) == 1
    assert f.sql.execute("SELECT COUNT(*) FROM #ExportContainedTarget").fetchval() == 5
    assert (
        f.sql.execute("SELECT COUNT(*) FROM #ExportResource WHERE OwnerID IS NOT NULL").fetchval()
        == 0
    )
    assert tuple(
        f.sql.execute("SELECT State,Phase,Version FROM #SourceOutputOperation").fetchone()
    ) == ("uncertain", "uncertain", 8)
    assert tuple(f.sql.execute("SELECT PoolState,Version FROM #SourceOutputPool").fetchone()) == (
        "blocked",
        10,
    )
    assert result["input_commitment"]["NewKVK"] == 8


def test_lost_reply_reconciles_original_isolation(recovery, monkeypatch):
    service, f, docs = recovery
    report = service.inspect(f.operation)
    settle = service.dal.settle
    calls = []

    def lost(*args, **kwargs):
        calls.append(1)
        settle(*args, **kwargs)
        raise UncertainCommit("Synthetic lost reply")

    monkeypatch.setattr(service.dal, "settle", lost)
    args = dict(
        token=report["token"], actor="recovery:" + str(uuid4()), reason="Retire uncertain pool"
    )
    with pytest.raises(UncertainCommit):
        service.apply(f.operation, **args)
    assert service.apply(f.operation, **args)["outcome"] == "targets_isolated"
    assert len(calls) == len(docs) == 1


@pytest.mark.parametrize("fault", ["owner", "scope", "target", "principal", "version"])
def test_changed_or_incomplete_evidence_never_releases(recovery, fault):
    service, f, docs = recovery
    report = service.inspect(f.operation)
    changes = {
        "owner": "UPDATE #ExportResource SET OwnerID=NEWID() WHERE ResourceKind='destination'",
        "scope": "UPDATE #ExportExecutionStream SET ScopeJson='{}'",
        "target": "UPDATE #ExportProviderRequest SET TargetID='foreign-file'",
        "principal": "UPDATE #ExportExecutionSession SET AuthorityPrincipal='foreign'",
        "version": "UPDATE #SourceOutputOperation SET Version=Version+1",
    }
    f.sql.execute(changes[fault])
    f.sql.commit()
    with pytest.raises((SourceConflict, KeyError)):
        service.apply(
            f.operation,
            token=report["token"],
            actor="recovery:" + str(uuid4()),
            reason="Retire pool",
        )
    assert not docs
    assert f.sql.execute("SELECT COUNT(*) FROM #ExportTargetContainment").fetchval() == 0


def test_crash_before_first_stream_can_isolate_complete_owned_pool(recovery):
    service, f, _ = recovery
    f.sql.execute("DELETE #ExportProviderRequestEvent")
    f.sql.execute("DELETE #ExportProviderRequest")
    f.sql.execute("DELETE #ExportExecutionStream")
    f.sql.commit()
    report = service.inspect(f.operation)
    assert report["seals"] == {}
    assert (
        service.apply(
            f.operation,
            token=report["token"],
            actor="recovery:" + str(uuid4()),
            reason="Retire pool",
        )["outcome"]
        == "targets_isolated"
    )
