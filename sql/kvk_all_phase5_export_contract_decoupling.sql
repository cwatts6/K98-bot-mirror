/*
KVK_ALL Schema Modernisation - Phase 5 Export Contract Decoupling

Purpose:
- Preserve the existing KVK.sp_KVK_Get_Exports result-set order and tab names.
- Add Phase 4 contribution outputs to existing player/kingdom/camp export sections.
- Avoid new result sets or spreadsheet tab names in Phase 5.

Rollback:
- Redeploy the previous KVK.sp_KVK_Get_Exports definition without
  max_contribute_gain and cur_contribute_gain in the SELECT lists.
*/

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
        kp_loss, healed_troops, deads, max_contribute_gain, cur_contribute_gain,
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
        kp_loss, healed_troops, deads, max_contribute_gain, cur_contribute_gain, dkp,
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
        kp_loss, healed_troops, deads, max_contribute_gain, cur_contribute_gain, dkp,
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
        kp_loss, healed_troops, deads, max_contribute_gain, cur_contribute_gain,
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
        kp_loss, healed_troops, deads, max_contribute_gain, cur_contribute_gain, dkp,
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
        kp_loss, healed_troops, deads, max_contribute_gain, cur_contribute_gain, dkp,
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
