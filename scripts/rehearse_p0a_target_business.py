"""Populated target publication checks inside the disposable P0a SQL fixture.

All business procedures execute literal immutable SQL source. This never connects
independently, sends provider writes, or substitutes a stub for a nested callee.
"""

import re
from uuid import uuid4

from scripts.rehearse_p0a_startup_contracts import SQL_FIXTURE_COMMIT

MODULES = (
    "CREATE_DELTA_TABLES",
    "sp_Build_Prekvk_And_Honor_Rankings",
    "sp_Create_Excel_For_Kvk_Indexes",
    "sp_Refresh_View_EXCEL_FOR_KVK_All",
    "usp_RecordKvkFinalReportCompletion",
    "sp_ExcelOutput_ByKVK",
    "sp_Prep_TargetTable",
    "sp_Prep_ExcelOutputTable",
    "sp_Prep_ExcelExportTable",
)
TABLES = (
    "KVK_Details",
    "KingdomScanData4",
    "DeltaMetrics",
    "DeltaProcessingLog",
    "T4KillDelta",
    "T5KillDelta",
    "T4T5KillDelta",
    "POWERDelta",
    "KillPointsDelta",
    "DeadsDelta",
    "HelpsDelta",
    "RSSASSISTDelta",
    "RSSGatheredDelta",
    "HealedTroopsDelta",
    "RangedPointsDelta",
    "KVKTargetBands",
    "EXEMPT_FROM_STATS",
    "STAGING_STATS",
    "HoH_Deads",
    "ZEROED",
    "KVKFinalReportHeader",
    "KVK_Target_Publication",
    "KVK_Target_Publication_Row",
    "EXCEL_EXPORT_KVK_TARGETS_TEMPLATE",
    "PreKvk_Scan",
    "PreKvk_Scores",
    "KVK_Honor_Scan",
    "KVK_Honor_AllPlayers_Raw",
)


def qualify(fixture, connection):
    assert connection.execute("SELECT DB_NAME()").fetchval() == fixture.DATABASE
    assert fixture.DATABASE.startswith("K98_P0a_Migrations_")
    execute = lambda sql: fixture.execute(connection, sql)
    # SQL source references this pre-existing sequence but does not export its
    # definition. This fixture-only dependency is never evaluated: every scan
    # below supplies SCAN_UNO explicitly. It is not installation/schema evidence.
    execute("CREATE SEQUENCE dbo.KS4_UNO_SEQ AS int START WITH 1 INCREMENT BY 1")
    # Only the tables explicitly needed by the real business call closure.
    for name in TABLES:
        if connection.execute("SELECT OBJECT_ID(?, 'U')", "dbo." + name).fetchval():
            continue
        raw = fixture.source(SQL_FIXTURE_COMMIT, "sql_schema/dbo." + name + ".Table.sql")
        for batch in fixture.batches(raw):
            execute(batch)
    for name in MODULES:
        raw = fixture.source(SQL_FIXTURE_COMMIT, "sql_schema/dbo." + name + ".StoredProcedure.sql")
        declaration = re.search(r"(?m)^(?:CREATE(?: OR ALTER)?|ALTER) PROCEDURE\b", raw)
        assert declaration, name
        body = re.sub(
            r"^(?:CREATE(?: OR ALTER)?|ALTER) PROCEDURE",
            "CREATE OR ALTER PROCEDURE",
            raw[declaration.start() :],
            count=1,
        )
        execute("SET ANSI_NULLS ON; SET QUOTED_IDENTIFIER ON;")
        for batch in fixture.batches(body):
            execute(batch)
    raw = fixture.source(SQL_FIXTURE_COMMIT, "sql_schema/dbo.v_KVK_TARGETS_FOR_BOT.View.sql")
    for batch in fixture.batches(raw):
        execute(batch)

    execute(
        """INSERT dbo.KVK_Details(KVK_NO,KVK_NAME,CreatedAt) VALUES(3,N'Disposable P0a',SYSUTCDATETIME());
INSERT dbo.ProcConfig(KVKVersion,ConfigKey,ConfigValue) VALUES
(3,'DRAFTSCAN',100),(3,'MATCHMAKING_SCAN',101),(3,'CURRENTKVK3',3),
(3,'KVK_END_SCAN',100),(3,'LASTKVKEND',99),(3,'PRE_PASS_4_SCAN',99),
(3,'PASS4END',100),(3,'PASS6END',100),(3,'PASS7END',100);
INSERT dbo.KVKTargetBands(KVKVersion,MinPower,KillTarget,MinKillTarget,DeadTarget)
VALUES(3,0,1000,500,100),(3,50000000,2000,1000,200);
INSERT dbo.EXEMPT_FROM_STATS(GovernorID,Exempt,KVK_NO) VALUES(1003,1,3);
INSERT dbo.KingdomScanData4(PowerRank,GovernorName,GovernorID,Power,KillPoints,Deads,
T1_Kills,T2_Kills,T3_Kills,T4_Kills,T5_Kills,[T4&T5_KILLS],RSSAssistance,Helps,
ScanDate,SCANORDER,SCAN_UNO,[City Hall]) VALUES
(1,N'High band',1001,60000000,50000,100,0,0,0,2000,1000,3000,10,20,'2026-10-01',100,1,25),
(2,N'Low band',1002,30000000,25000,50,0,0,0,1000,500,1500,10,20,'2026-10-01',100,2,25),
(3,N'Exempt',1003,10000000,10000,25,0,0,0,500,250,750,10,20,'2026-10-01',100,3,25);
"""
    )
    preparation, owner = str(uuid4()), str(uuid4())
    request = '{"request":{"producer":{"kind":"configuration_import","atomic_checkpoint":1}}}'
    connection.execute(
        """INSERT dbo.ExportPreparation(PreparationID,AccountKey,ConsumerKind,
RequestHash,EnqueueSequence,State,OwnerID,Fence,Version,StorageOwner,RequestJson,Actor,Reason,CreatedUTC,UpdatedUTC)
VALUES(?,'fixture','scan_data',HASHBYTES('SHA2_256',?),1,'writing',?,1,1,'fixture',?,'fixture','Business qualification',SYSUTCDATETIME(),SYSUTCDATETIME())""",
        preparation,
        preparation,
        owner,
        request,
    )
    execute(
        "INSERT dbo.ExportResource(ResourceKey,ResourceKind,Fence,Version) VALUES('sql_snapshot:legacy_outputs','sql_snapshot',0,1)"
    )
    connection.execute(
        "INSERT dbo.ExportPreparationResource(PreparationID,ResourceKey) VALUES(?,'sql_snapshot:legacy_outputs')",
        preparation,
    )
    connection.execute(
        "UPDATE dbo.ExportResource SET ActivePreparationID=?,OwnerID=?,Fence=1 WHERE ResourceKey='sql_snapshot:legacy_outputs'",
        preparation,
        owner,
    )

    def publish(commit):
        execute("BEGIN TRANSACTION")
        try:
            cursor = connection.execute(
                "EXEC dbo.sp_TARGETS_MASTER @KVK=3,@ExportPreparationID=?", preparation
            )
            while cursor.nextset():
                pass
            assert connection.execute("SELECT @@TRANCOUNT").fetchval() == 1
            rows = [
                tuple(r)
                for r in connection.execute(
                    "SELECT GovernorID,KillTarget,MinimumKillTarget,DeadTarget,DKPTarget FROM dbo.KVK_Target_Publication_Row WHERE PublicationId=(SELECT PublicationId FROM dbo.KVK_Target_Publication WHERE IsCurrent=1 AND KVK_NO=3) ORDER BY GovernorID"
                )
            ]
            assert rows == [(1001, 2000, 1000, 200, 7600), (1002, 1000, 500, 100, 3800)], rows
            assert (
                connection.execute("SELECT COUNT(*) FROM dbo.EXCEL_EXPORT_KVK_TARGETS_3").fetchval()
                == 2
            )
            assert connection.execute("SELECT COUNT(*) FROM dbo.EXCEL_FOR_KVK_3").fetchval() == 3
            execute("COMMIT" if commit else "ROLLBACK")
        except BaseException:
            execute("IF XACT_STATE()<>0 ROLLBACK")
            raise

    publish(False)
    assert connection.execute("SELECT COUNT(*) FROM dbo.KVK_Target_Publication").fetchval() == 0
    assert (
        connection.execute("SELECT OBJECT_ID('dbo.EXCEL_EXPORT_KVK_TARGETS_3')").fetchval() is None
    )
    assert connection.execute("SELECT COUNT(*) FROM dbo.DeltaMetrics").fetchval() == 0
    publish(True)
    assert (
        connection.execute(
            "SELECT PublicationState FROM dbo.KVK_Target_Publication WHERE IsCurrent=1"
        ).fetchval()
        == "DRAFT"
    )
    execute(
        "UPDATE dbo.ProcConfig SET ConfigValue=100 WHERE KVKVersion=3 AND ConfigKey='MATCHMAKING_SCAN'"
    )
    publish(True)
    assert (
        connection.execute(
            "SELECT PublicationState FROM dbo.KVK_Target_Publication WHERE IsCurrent=1"
        ).fetchval()
        == "OFFICIAL"
    )
    publication = tuple(
        connection.execute(
            "SELECT PublicationId,PublicationVersion,PublicationSignature FROM dbo.KVK_Target_Publication WHERE IsCurrent=1"
        ).fetchone()
    )
    publish(True)
    assert (
        tuple(
            connection.execute(
                "SELECT PublicationId,PublicationVersion,PublicationSignature FROM dbo.KVK_Target_Publication WHERE IsCurrent=1"
            ).fetchone()
        )
        == publication
    )
    assert connection.execute("SELECT COUNT(*) FROM dbo.KVK_Target_Publication").fetchval() == 2
    return dict(
        status="POPULATED_TARGET_BUSINESS_VERIFIED",
        real_nested_modules=len(MODULES),
        governors=3,
        target_rows=2,
        cases=["outer_rollback", "draft_commit", "official_commit", "preserve_official"],
        provider_delivery=False,
    )
