"""Real KVK calculation, view, receipt and deferred upkeep in owned databases."""

from pathlib import Path
import re

import pytest

from tests.test_configuration_maintenance_native import (
    database as _configuration_database,
    insert_scan,
    snapshot_database as _snapshot_database,
)
from tests.test_maintenance_owned_native import drain, state

configuration_database = _configuration_database
snapshot_database = _snapshot_database
ROOT = Path("C:/K98-bot-SQL-Server/sql_schema")


@pytest.fixture
def database(configuration_database):
    owner, connect = configuration_database
    tables = (
        "MaintenanceKvkWork",
        "STAGING_STATS",
        "ProcConfig",
        "KVK_Details",
        "KVKFinalReportHeader",
        "PreKvk_Scan",
        "PreKvk_Scores",
        "KVK_Honor_Scan",
        "KVK_Honor_AllPlayers_Raw",
        "ZEROED",
        "HoH_Deads",
    )
    names = [name + ".Table" for name in tables]
    names += ["v_ReportGovernorNames.View"]
    names += [
        name + ".StoredProcedure"
        for name in (
            "sp_Build_Prekvk_And_Honor_Rankings",
            "sp_Refresh_View_EXCEL_FOR_KVK_All",
            "usp_RecordKvkFinalReportCompletion",
            "usp_MaintenanceKvkDue",
            "usp_MaintenanceKvkOutput",
            "sp_ExcelOutput_ByKVK",
        )
    ]
    for name in names:
        text = (ROOT / ("dbo." + name + ".sql")).read_text(encoding="utf-8-sig")
        if "\nALTER PROCEDURE" in text:
            text = text[text.index("ALTER PROCEDURE") :].replace(
                "ALTER PROCEDURE", "CREATE OR ALTER PROCEDURE", 1
            )
        elif "\nCREATE OR ALTER PROCEDURE" in text and "\nGO\n" not in text:
            text = text[text.index("CREATE OR ALTER PROCEDURE") :]
        for batch in re.split(r"(?im)^GO\s*$", text):
            if batch.strip():
                drain(owner.execute(batch))
    for kvk in (1, 2):
        text = (
            (ROOT / "dbo.TARGETS_15.Table.sql")
            .read_text(encoding="utf-8-sig")
            .replace("TARGETS_15", f"TARGETS_{kvk}")
        )
        drain(owner.execute(text))
        owner.execute(
            f"INSERT dbo.TARGETS_{kvk}(GovernorID,Kill_Target,Dead_Target) VALUES(1,100,100)"
        )
        for key, value in (
            ("CURRENTKVK3", kvk),
            ("KVK_END_SCAN", 1),
            ("LASTKVKEND", 0),
            ("PRE_PASS_4_SCAN", 0),
            ("PASS4END", 1),
            ("PASS6END", 1),
            ("PASS7END", 1),
        ):
            owner.execute(
                "INSERT dbo.ProcConfig(KVKVersion,ConfigKey,ConfigValue) VALUES(?,?,?)",
                kvk,
                key,
                value,
            )
    insert_scan(owner)
    owner.execute("UPDATE dbo.KingdomScanData4 SET GovernorName=N'Current Name'")
    yield owner, connect


def publish(owner, kvk=1):
    drain(owner.execute("EXEC dbo.sp_ExcelOutput_ByKVK @KVK=?,@Scan=1", kvk))


def target(owner, kvk=1):
    return tuple(
        owner.execute(
            "SELECT DueGeneration,CompletedGeneration,State FROM dbo.MaintenanceKvkWork WHERE KVKNo=?",
            kvk,
        ).fetchone()
    )


@pytest.mark.parametrize("outer_commit", [None, True, False])
def test_actual_output_view_receipt_and_due_share_transaction(database, outer_commit):
    owner, _ = database
    if outer_commit is not None:
        owner.execute("BEGIN TRAN")
    publish(owner)
    assert owner.execute("SELECT @@TRANCOUNT").fetchval() == int(outer_commit is not None)
    assert tuple(
        owner.execute(
            "SELECT Gov_ID,Governor_Name,[Starting Power] FROM dbo.v_EXCEL_FOR_KVK_All"
        ).fetchone()
    ) == (1, "Current Name", 400)
    assert tuple(
        owner.execute(
            "SELECT Revision,OutputRowCount,FinalScanOrder FROM dbo.KVKFinalReportHeader"
        ).fetchone()
    ) == (1, 1, 1)
    assert target(owner) == (1, 0, "pending")
    assert (
        owner.execute(
            "SELECT COUNT(*) FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.EXCEL_FOR_KVK_1') AND index_id>0"
        ).fetchval()
        == 0
    )
    if outer_commit is not None:
        owner.execute("COMMIT" if outer_commit else "ROLLBACK")
    if outer_commit is False:
        assert owner.execute("SELECT OBJECT_ID('dbo.EXCEL_FOR_KVK_1')").fetchval() is None
        assert owner.execute("SELECT COUNT(*) FROM dbo.MaintenanceKvkWork").fetchval() == 0
        assert state(owner, "kvk_output")[:3] == (0, 0, "complete")


def test_two_targets_complete_one_per_invocation_without_false_aggregate_success(
    database,
):
    owner, _ = database
    publish(owner, 1)
    publish(owner, 2)
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'kvk_output'"))
    assert target(owner, 1) == (1, 1, "complete")
    assert target(owner, 2) == (2, 0, "pending")
    assert state(owner, "kvk_output")[:3] == (2, 0, "pending")
    first_claim = owner.execute(
        "SELECT ClaimID FROM dbo.MaintenanceKvkWork WHERE KVKNo=1"
    ).fetchval()
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'kvk_output'"))
    assert target(owner, 2) == (2, 2, "complete")
    assert state(owner, "kvk_output")[:3] == (2, 2, "complete")
    assert (
        owner.execute("SELECT ClaimID FROM dbo.MaintenanceKvkWork WHERE KVKNo=1").fetchval()
        == first_claim
    )
    for kvk in (1, 2):
        stats = owner.execute(
            f"SELECT p.rows,p.rows_sampled FROM sys.stats s CROSS APPLY sys.dm_db_stats_properties(s.object_id,s.stats_id) p WHERE s.object_id=OBJECT_ID('dbo.EXCEL_FOR_KVK_{kvk}')"
        ).fetchall()
        assert len(stats) >= 2 and all(tuple(row) == (1, 1) for row in stats)
        assert (
            owner.execute(
                f"SELECT COUNT(*) FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.EXCEL_FOR_KVK_{kvk}') AND index_id>0"
            ).fetchval()
            == 2
        )


def test_recreated_output_coalesces_to_exact_latest_identity(database):
    owner, _ = database
    publish(owner)
    first = owner.execute("SELECT DueObjectID FROM dbo.MaintenanceKvkWork").fetchval()
    publish(owner)
    assert owner.execute("SELECT COUNT(*) FROM dbo.MaintenanceKvkWork").fetchval() == 1
    assert owner.execute("SELECT DueHeaderRevision FROM dbo.MaintenanceKvkWork").fetchval() == 2
    assert owner.execute("SELECT DueObjectID FROM dbo.MaintenanceKvkWork").fetchval() != first
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'kvk_output'"))
    assert target(owner) == (2, 2, "complete")


def test_unique_index_is_preserved(database):
    owner, _ = database
    publish(owner)
    owner.execute("CREATE UNIQUE INDEX IX_EXCEL_FOR_KVK_1_GovID ON dbo.EXCEL_FOR_KVK_1(Gov_ID)")
    before = tuple(
        owner.execute(
            "SELECT index_id,is_unique FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.EXCEL_FOR_KVK_1') AND name='IX_EXCEL_FOR_KVK_1_GovID'"
        ).fetchone()
    )
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'kvk_output'"))
    assert (
        tuple(
            owner.execute(
                "SELECT index_id,is_unique FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.EXCEL_FOR_KVK_1') AND name='IX_EXCEL_FOR_KVK_1_GovID'"
            ).fetchone()
        )
        == before
    )


def test_due_scope_failure_rolls_back_output_view_and_receipt(database):
    owner, _ = database
    owner.execute("ALTER TABLE dbo.MaintenanceKvkWork ADD CONSTRAINT RejectScope CHECK(KVKNo<0)")
    with pytest.raises(Exception, match="547"):
        publish(owner)
    assert owner.execute("SELECT @@TRANCOUNT").fetchval() == 0
    assert owner.execute("SELECT OBJECT_ID('dbo.EXCEL_FOR_KVK_1')").fetchval() is None
    assert owner.execute("SELECT COUNT(*) FROM dbo.KVKFinalReportHeader").fetchval() == 0
    assert state(owner, "kvk_output")[:3] == (0, 0, "complete")


def test_direct_due_refuses_unowned_or_noncanonical_scope(database):
    owner, _ = database
    with pytest.raises(Exception, match="51962"):
        owner.execute("EXEC dbo.usp_MaintenanceKvkDue 1")
    owner.execute(
        "BEGIN TRAN; DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource='K98:maintenance-schema:v1',@LockMode='Shared',@LockOwner='Transaction',@LockTimeout=0; IF @r<0 THROW 50000,'fixture',1;"
    )
    try:
        with pytest.raises(Exception, match="51962"):
            owner.execute("EXEC dbo.usp_MaintenanceKvkDue 999")
    finally:
        owner.execute("IF @@TRANCOUNT>0 ROLLBACK")
    assert owner.execute("SELECT COUNT(*) FROM dbo.MaintenanceKvkWork").fetchval() == 0


@pytest.mark.parametrize("fault", ["identity", "ack"])
def test_later_target_failure_keeps_earlier_completion_and_never_replays(database, fault):
    owner, _ = database
    publish(owner, 1)
    publish(owner, 2)
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'kvk_output'"))
    if fault == "identity":
        owner.execute("UPDATE dbo.MaintenanceKvkWork SET DueObjectID=-1 WHERE KVKNo=2")
    else:
        owner.execute(
            "ALTER TABLE dbo.MaintenanceKvkWork ADD CONSTRAINT RejectTargetAck CHECK(KVKNo<>2 OR CompletedGeneration=0)"
        )
    with pytest.raises(Exception, match=r"51968|547"):
        drain(owner.execute("EXEC dbo.usp_RunMaintenance 'kvk_output'"))
    assert target(owner, 1) == (1, 1, "complete")
    assert target(owner, 2) == (2, 0, "failed")
    assert state(owner, "kvk_output")[:3] == (2, 0, "failed")
    assert owner.execute("SELECT COUNT(*) FROM dbo.v_EXCEL_FOR_KVK_All").fetchval() == 2
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'kvk_output'"))
    assert target(owner, 2) == (2, 0, "failed")


def test_live_publication_schema_owner_defers_worker(database):
    owner, connect = database
    publish(owner)
    holder = connect()
    try:
        holder.execute(
            "BEGIN TRAN; DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource='K98:maintenance-schema:v1',@LockMode='Shared',@LockOwner='Transaction',@LockTimeout=0; IF @r<0 THROW 50000,'fixture',1;"
        )
        drain(owner.execute("EXEC dbo.usp_RunMaintenance 'kvk_output'"))
        assert state(owner, "kvk_output")[3] is None
        assert target(owner) == (1, 0, "pending")
    finally:
        holder.execute("ROLLBACK")
        holder.close()


def test_live_maintenance_refuses_actual_standalone_publication_before_mutation(
    database,
):
    owner, connect = database
    holder = connect()
    try:
        holder.execute(
            "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource='K98:maintenance-schema:v1',@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; IF @r<0 THROW 50000,'fixture',1;"
        )
        with pytest.raises(Exception, match="51966"):
            publish(owner)
        assert owner.execute("SELECT @@TRANCOUNT").fetchval() == 0
        assert owner.execute("SELECT OBJECT_ID('dbo.EXCEL_FOR_KVK_1')").fetchval() is None
        assert owner.execute("SELECT COUNT(*) FROM dbo.MaintenanceKvkWork").fetchval() == 0
    finally:
        holder.close()


def test_lost_attempt_becomes_unknown_with_original_target_identity(database):
    owner, _ = database
    publish(owner)
    owner.execute(
        "UPDATE dbo.MaintenanceWork SET State='running',ClaimID=NEWID(),ClaimedGeneration=1 WHERE Kind='kvk_output'; UPDATE dbo.MaintenanceKvkWork SET State='running',ClaimID=NEWID(),ClaimedGeneration=1,ClaimedObjectID=DueObjectID,ClaimedObjectCreateDate=DueObjectCreateDate,ClaimedHeaderRevision=DueHeaderRevision"
    )
    original = tuple(
        owner.execute(
            "SELECT ClaimID,ClaimedObjectID,ClaimedHeaderRevision FROM dbo.MaintenanceKvkWork"
        ).fetchone()
    )
    drain(owner.execute("EXEC dbo.usp_RunMaintenance 'kvk_output'"))
    assert target(owner) == (1, 0, "unknown")
    assert state(owner, "kvk_output")[:3] == (1, 0, "unknown")
    publish(owner)
    assert target(owner) == (2, 0, "unknown")
    assert (
        tuple(
            owner.execute(
                "SELECT ClaimID,ClaimedObjectID,ClaimedHeaderRevision FROM dbo.MaintenanceKvkWork"
            ).fetchone()
        )
        == original
    )
