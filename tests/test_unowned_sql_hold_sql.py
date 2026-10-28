"""Unowned SQL blocker disposition never adopts foreign or uncertain work."""

from datetime import datetime
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryActor, RecoveryService
from services.unowned_sql_hold_dal import RESOURCE, UnownedSqlHoldDAL
from services.unowned_sql_hold_recovery import UnownedSqlHoldRecovery
from tests import test_export_target_containment_sql as fixtures
from tests.test_export_target_containment import recovery as recovery
from tests.test_export_target_containment_sql import contained_job as contained_job
from tests.test_guided_recovery import ACTOR, Store

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Local SQL opt-in"
)


@pytest.fixture
def held(monkeypatch, request):
    monkeypatch.setattr(
        fixtures,
        "TABLES",
        (
            *fixtures.TABLES,
            "dbo.ExportPreparationResource",
            "dbo.StatsImportExecution",
            "dbo.ExportUnownedHoldDisposition",
        ),
    )
    containment, f, docs = request.getfixturevalue("recovery")
    original = containment.inspect(f.job)
    containment.apply(
        f.job,
        token=original["token"],
        actor="recovery:" + str(uuid4()),
        reason="Retain unknown old writer",
    )
    root = Path(os.environ["K98_TARGET_CONTAINMENT_SQL_SOURCE"]) / "sql_schema"
    raw = (root / "dbo.ACQUIRE_KS4_IMPORT_LOCK.StoredProcedure.sql").read_text(encoding="utf-8-sig")
    body = raw[raw.index("CREATE OR ALTER PROCEDURE") :].strip().removesuffix("GO").strip()
    body = body.replace(
        "CREATE OR ALTER PROCEDURE [dbo].[ACQUIRE_KS4_IMPORT_LOCK]",
        "CREATE PROCEDURE #ACQUIRE_KS4_IMPORT_LOCK",
    )
    # Temporary master fixtures use public as the lock namespace. The installed
    # principal/permission boundary is covered by the migration rehearsal.
    body = body.replace("N'K98ImportLockPrincipal'", "N'public'")
    f.sql.execute(body)
    monkeypatch.setattr(
        fixtures, "PROCEDURES", (*fixtures.PROCEDURES, "dbo.ACQUIRE_KS4_IMPORT_LOCK")
    )
    f.sql.execute(
        "INSERT #ExportResource(ResourceKey,ResourceKind,Fence,Version,BlockedReason) VALUES(?,'sql_snapshot',9,4,'Legacy block without an owner')",
        RESOURCE,
    )
    runtime = SimpleNamespace(
        dal=SimpleNamespace(connect=f.connect),
        account="test-account",
        store=SimpleNamespace(storage_owner="disk"),
    )
    dal = UnownedSqlHoldDAL(runtime)
    adapter = UnownedSqlHoldRecovery(dal)
    journal = Store()
    service = RecoveryService(
        journal,
        {adapter.kind: adapter},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    return SimpleNamespace(**locals())


def confirm(r, row, actor=ACTOR):
    return r.service.execute(
        actor,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "clear_unowned_hold",
        "Preserve unknown effects; clear obsolete unowned blocker",
    )


@pytest.mark.asyncio
async def test_unowned_hold_real_admin_confirmation(held, monkeypatch):
    from tests.p0_attestation_ui_harness import confirm_through_view

    row = held.service.review_source(ACTOR, held.adapter.kind, held.dal.source_id)
    current = await confirm_through_view(monkeypatch, held.service, row, "clear_unowned_hold")
    assert current["evidence"]["original_outcome"] == "unknown"


def test_guided_unowned_block_disposition_verifies_lost_ack_and_keeps_unknown_work(
    held, monkeypatch
):
    r = held
    before = r.containment.dal.snapshot(r.f.job, account="test-account")
    row = r.service.review_source(ACTOR, r.adapter.kind, r.dal.source_id)
    assert set(row["evidence"]["actions"]) == {"clear_unowned_hold"}
    with pytest.raises(SourceConflict, match="configured admin"):
        confirm(r, row, RecoveryActor(9, 2, 3))
    clear = r.dal.clear
    calls = []

    def lost(*args, **kwargs):
        clear(*args, **kwargs)
        calls.append(1)
        raise TimeoutError("Lost disposition commit reply")

    monkeypatch.setattr(r.dal, "clear", lost)
    result = confirm(r, row)
    assert result["State"] == "resolved"
    assert result["evidence"]["original_outcome"] == "unknown"
    assert confirm(r, row)["State"] == "resolved"
    assert calls == [1] and r.journal.actions[0]["State"] == "verified"
    assert r.containment.dal.snapshot(r.f.job, account="test-account") == before
    assert (
        r.f.sql.execute(
            "SELECT BlockedReason FROM #ExportResource WHERE ResourceKey=?", RESOURCE
        ).fetchval()
        is None
    )
    assert (
        r.f.sql.execute(
            "SELECT Fence FROM #ExportResource WHERE ResourceKey=?", RESOURCE
        ).fetchval()
        == 9
    )
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportUnownedHoldDisposition").fetchval() == 1


@pytest.mark.parametrize(
    "mutation",
    [
        "UPDATE #ExportResource SET Version=Version+1 WHERE ResourceKind='sql_snapshot'",
        "UPDATE #ExportResource SET ActiveJobID=NEWID(),OwnerID=NEWID() WHERE ResourceKind='sql_snapshot'",
        "UPDATE #ExportExecutionStream SET State='frozen',ActiveAccountKey=AccountKey,ClosedUTC=NULL,ClosureHash=NULL,ClosureReference=NULL,EventDigest=NULL",
    ],
)
def test_stale_foreign_and_live_ownership_never_clear_the_block(held, mutation):
    r = held
    row = r.service.review_source(ACTOR, r.adapter.kind, r.dal.source_id)
    r.f.sql.execute(mutation)
    with pytest.raises(SourceConflict):
        confirm(r, row)
    assert r.f.sql.execute(
        "SELECT BlockedReason FROM #ExportResource WHERE ResourceKey=?", RESOURCE
    ).fetchval()
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportUnownedHoldDisposition").fetchval() == 0


@pytest.mark.parametrize(
    "guard",
    [
        "k98-legacy-output-snapshot",
        "K98:post-import-stats:v1",
        "K98:KingdomScanData4:ImportPipeline:v1",
    ],
)
def test_actual_worker_lock_prevents_unowned_disposition(held, guard):
    import pyodbc

    r = held
    row = r.service.review_source(ACTOR, r.adapter.kind, r.dal.source_id)
    connection = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\\K98DEV;DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes",
        autocommit=True,
    )
    try:
        connection.execute(
            "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; IF @r<0 THROW 51959,'Fixture guard unavailable',1",
            guard,
        )
        result = confirm(r, row)
        assert result["State"] != "resolved"
        assert r.f.sql.execute(
            "SELECT BlockedReason FROM #ExportResource WHERE ResourceKey=?", RESOURCE
        ).fetchval()
        assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportUnownedHoldDisposition").fetchval() == 0
    finally:
        connection.execute("EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'", guard)
        connection.close()


@pytest.mark.parametrize("foreign", [False, True])
@pytest.mark.parametrize(
    "state",
    [
        "writing",
        "uncertain",
        "unavailable_with_prepared_import",
        "unavailable_with_running_import",
        "unavailable_with_partial_import",
    ],
)
def test_detached_durable_producer_still_blocks_disposition(held, foreign, state):
    r = held
    key, owner = str(uuid4()), str(uuid4())
    r.f.insert(
        "ExportPreparation",
        dict(
            PreparationID=key,
            AccountKey="foreign" if foreign else "test-account",
            ConsumerKind="scan_data",
            RequestHash=b"r" * 32,
            EnqueueSequence=999,
            State="unavailable" if state.endswith("import") else state,
            OwnerID=owner,
            Fence=4,
            Version=5,
            StorageOwner="disk",
            RequestJson="{}",
            Actor="fixture",
            Reason="unknown producer",
            CreatedUTC=datetime(2026, 1, 1),
            UpdatedUTC=datetime(2026, 1, 1),
        ),
    )
    r.f.insert("ExportPreparationResource", dict(PreparationID=key, ResourceKey=RESOURCE))
    if state.endswith("import"):
        import_state = state.removeprefix("unavailable_with_").removesuffix("_import")
        r.f.insert(
            "StatsImportExecution",
            dict(
                PreparationID=key,
                CompletedFileName="stats_" + uuid4().hex + ".ready.csv",
                OwnerID=owner,
                Fence=4,
                State=import_state,
                ScanOrder=17 if import_state == "partial" else None,
            ),
        )
    evidence, token, resolved = r.adapter.inspect(r.dal.source_id)
    assert not resolved and not evidence["actions"]
    assert bool(evidence["recovery_links"]) is not foreign
    with pytest.raises(SourceConflict):
        r.adapter.execute(
            r.dal.source_id,
            "clear_unowned_hold",
            token,
            "recovery:" + str(uuid4()),
            "Cannot infer safety from missing pointer",
        )
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportUnownedHoldDisposition").fetchval() == 0
