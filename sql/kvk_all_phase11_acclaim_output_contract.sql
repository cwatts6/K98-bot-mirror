/*
KVK_ALL Schema Modernisation - Phase 11 Acclaim Output Contract

Purpose:
- Preserve internal contribution storage and recompute semantics.
- Remove Highest Acclaim gain from player-facing outputs.
- Expose current Acclaim gain as acclaim_gain.
- Preserve KVK.sp_KVK_Get_Exports result-set count/order and Google Sheets tab names.

Rollback:
- Redeploy the previous KVK.sp_KVK_Get_Exports and KVK.vw_FightingDataset definitions.
*/

PRINT N'Applying KVK.sp_KVK_Get_Exports.StoredProcedure.sql';
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

IF NOT EXISTS (
    SELECT *
    FROM sys.objects
    WHERE object_id = OBJECT_ID(N'[KVK].[sp_KVK_Get_Exports]')
      AND type in (N'P', N'PC')
)
BEGIN
    EXEC dbo.sp_executesql @statement = N'CREATE PROCEDURE [KVK].[sp_KVK_Get_Exports] AS'
END
GO

ALTER PROCEDURE [KVK].[sp_KVK_Get_Exports]
    @KVK_NO [int]
WITH EXECUTE AS CALLER
AS
BEGIN
    SET NOCOUNT ON;

    ----------------------------------------------------------------
    -- 1) KVK_Scan_Log
    ----------------------------------------------------------------
    SELECT
        KVK_NO,
        ScanID,
        ScanTimestampUTC,
        SourceFileName,
        Row_Count,
        ImportedAtUTC,
        UploaderDiscordID
    FROM KVK.KVK_Scan
    WHERE KVK_NO = @KVK_NO
    ORDER BY ScanID;

    ----------------------------------------------------------------
    -- 2) KVK_Windows
    ----------------------------------------------------------------
    DECLARE @MaxScanID INT = (SELECT MAX(ScanID) FROM KVK.KVK_Scan WHERE KVK_NO = @KVK_NO);

    SELECT
        KVK_NO,
        WindowName,
        WindowSeq,
        StartScanID,
        EndScanID,
        COALESCE(EndScanID, @MaxScanID) AS EffectiveEndScanID,
        Notes,
        UpdatedAtUTC
    FROM KVK.KVK_Windows
    WHERE KVK_NO = @KVK_NO
    ORDER BY ISNULL(WindowSeq, 255), WindowName;

    ----------------------------------------------------------------
    -- 3) KVK_DKP_Weights
    ----------------------------------------------------------------
    SELECT
        KVK_NO,
        WeightT4X,
        WeightT5Y,
        WeightDeadsZ,
        EffectiveFromUTC
    FROM KVK.KVK_DKPWeights
    WHERE KVK_NO = @KVK_NO
    ORDER BY EffectiveFromUTC DESC;

    ----------------------------------------------------------------
    -- 4) Player Windowed
    ----------------------------------------------------------------
    SELECT
        KVK_NO, WindowName, governor_id, name, kingdom, campid,
        kp_gain, kp_gain_recalc, kills_gain, t4_kills, t5_kills,
        kp_loss, healed_troops, deads, cur_contribute_gain AS acclaim_gain,
        starting_power, dkp,
        last_scan_id, computed_at_utc
    FROM KVK.KVK_Player_Windowed
    WHERE KVK_NO = @KVK_NO
    ORDER BY WindowName, dkp DESC;

    ----------------------------------------------------------------
    -- 5) Kingdom Windowed
    ----------------------------------------------------------------
    SELECT
        KVK_NO, WindowName, kingdom, campid, camp_name,
        kp_gain, kills_gain, t4_kills, t5_kills,
        kp_loss, healed_troops, deads, cur_contribute_gain AS acclaim_gain, dkp,
        last_scan_id, computed_at_utc
    FROM KVK.KVK_Kingdom_Windowed
    WHERE KVK_NO = @KVK_NO
    ORDER BY WindowName, dkp DESC;

    ----------------------------------------------------------------
    -- 6) Camp Windowed
    ----------------------------------------------------------------
    SELECT
        KVK_NO, WindowName, campid, camp_name,
        kp_gain, kills_gain, t4_kills, t5_kills,
        kp_loss, healed_troops, deads, cur_contribute_gain AS acclaim_gain, dkp,
        last_scan_id, computed_at_utc
    FROM KVK.KVK_Camp_Windowed
    WHERE KVK_NO = @KVK_NO
    ORDER BY WindowName, dkp DESC;

    ----------------------------------------------------------------
    -- 7) Player Full
    ----------------------------------------------------------------
    SELECT
        KVK_NO, WindowName, governor_id, name, kingdom, campid,
        kp_gain, kp_gain_recalc, kills_gain, t4_kills, t5_kills,
        kp_loss, healed_troops, deads, cur_contribute_gain AS acclaim_gain,
        starting_power, dkp,
        last_scan_id, computed_at_utc
    FROM KVK.KVK_Player_Windowed
    WHERE KVK_NO = @KVK_NO AND WindowName = N'Full'
    ORDER BY dkp DESC;

    ----------------------------------------------------------------
    -- 8) Kingdom Full
    ----------------------------------------------------------------
    SELECT
        KVK_NO, WindowName, kingdom, campid, camp_name,
        kp_gain, kills_gain, t4_kills, t5_kills,
        kp_loss, healed_troops, deads, cur_contribute_gain AS acclaim_gain, dkp,
        last_scan_id, computed_at_utc
    FROM KVK.KVK_Kingdom_Windowed
    WHERE KVK_NO = @KVK_NO AND WindowName = N'Full'
    ORDER BY dkp DESC;

    ----------------------------------------------------------------
    -- 9) Camp Full
    ----------------------------------------------------------------
    SELECT
        KVK_NO, WindowName, campid, camp_name,
        kp_gain, kills_gain, t4_kills, t5_kills,
        kp_loss, healed_troops, deads, cur_contribute_gain AS acclaim_gain, dkp,
        last_scan_id, computed_at_utc
    FROM KVK.KVK_Camp_Windowed
    WHERE KVK_NO = @KVK_NO AND WindowName = N'Full'
    ORDER BY dkp DESC;

    ----------------------------------------------------------------
    -- 10) Negative Corrections
    ----------------------------------------------------------------
    SELECT
        KVK_NO, ScanID, governor_id, name, kingdom, campid,
        field_name, value, recorded_at_utc
    FROM KVK.KVK_Ingest_Negatives
    WHERE KVK_NO = @KVK_NO
    ORDER BY ScanID, governor_id, field_name;
END
GO

PRINT N'Applying KVK.vw_FightingDataset.View.sql';
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

IF NOT EXISTS (SELECT * FROM sys.views WHERE object_id = OBJECT_ID(N'[KVK].[vw_FightingDataset]'))
BEGIN
    EXECUTE dbo.sp_executesql N'CREATE VIEW [KVK].[vw_FightingDataset] AS SELECT 1 AS placeholder'
END
GO

ALTER VIEW [KVK].[vw_FightingDataset]
AS
WITH W AS (
    SELECT KVK_NO, WindowName
    FROM KVK.KVK_Windows
    WHERE StartScanID IS NOT NULL
)
SELECT
    p.KVK_NO,
    p.WindowName,
    p.governor_id,
    p.name,
    p.kingdom,
    p.campid,
    p.kp_gain,
    p.kp_gain_recalc,
    p.kills_gain,
    p.t4_kills,
    p.t5_kills,
    p.kp_loss,
    p.healed_troops,
    p.deads,
    p.starting_power,
    p.dkp,
    p.last_scan_id,
    p.computed_at_utc,
    p.cur_contribute_gain AS acclaim_gain
FROM KVK.KVK_Player_Windowed p
JOIN W ON W.KVK_NO = p.KVK_NO
     AND W.WindowName = p.WindowName;
GO
