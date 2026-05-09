/*
KVK_ALL Schema Modernisation - Phase 4 Recompute Modernisation

Purpose:
- Apply additive Full Data v2 recompute capacity to production.
- Add internal contribution gain outputs to KVK windowed tables.
- Update recompute source precedence while preserving export result-set order and Google Sheets tab names.

Deployment notes:
- Run against the production ROK_TRACKER database after mirror validation.
- Script is idempotent for additive table columns and uses ALTER PROCEDURE for procedure bodies.
- No destructive table changes are included.
*/


PRINT N'Applying KVK.KVK_Player_Windowed.Table.sql';

SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Player_Windowed]') AND type in (N'U'))
BEGIN
CREATE TABLE [KVK].[KVK_Player_Windowed](
	[KVK_NO] [int] NOT NULL,
	[WindowName] [nvarchar](40) COLLATE Latin1_General_CI_AS NOT NULL,
	[governor_id] [bigint] NOT NULL,
	[name] [nvarchar](64) COLLATE Latin1_General_CI_AS NULL,
	[kingdom] [int] NOT NULL,
	[campid] [tinyint] NULL,
	[kp_gain] [bigint] NOT NULL,
	[kp_gain_recalc] [bigint] NOT NULL,
	[kills_gain] [bigint] NOT NULL,
	[t4_kills] [bigint] NOT NULL,
	[t5_kills] [bigint] NOT NULL,
	[kp_loss] [bigint] NOT NULL,
	[healed_troops] [bigint] NOT NULL,
	[deads] [bigint] NOT NULL,
	[max_contribute_gain] [bigint] NOT NULL,
	[cur_contribute_gain] [bigint] NOT NULL,
	[starting_power] [bigint] NOT NULL,
	[dkp] [float] NOT NULL,
	[last_scan_id] [int] NOT NULL,
	[computed_at_utc] [datetime2](0) NOT NULL,
 CONSTRAINT [PK_KVK_Player_Windowed] PRIMARY KEY CLUSTERED
(
	[KVK_NO] ASC,
	[WindowName] ASC,
	[governor_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
END
IF COL_LENGTH('KVK.KVK_Player_Windowed', 'max_contribute_gain') IS NULL
BEGIN
ALTER TABLE [KVK].[KVK_Player_Windowed] ADD [max_contribute_gain] [bigint] NOT NULL CONSTRAINT [DF_PlayerWin_MaxContrib] DEFAULT ((0)) WITH VALUES
END
IF COL_LENGTH('KVK.KVK_Player_Windowed', 'cur_contribute_gain') IS NULL
BEGIN
ALTER TABLE [KVK].[KVK_Player_Windowed] ADD [cur_contribute_gain] [bigint] NOT NULL CONSTRAINT [DF_PlayerWin_CurContrib] DEFAULT ((0)) WITH VALUES
END
IF NOT EXISTS (
    SELECT 1
    FROM sys.default_constraints dc
    INNER JOIN sys.columns c
        ON c.object_id = dc.parent_object_id
       AND c.column_id = dc.parent_column_id
    WHERE dc.parent_object_id = OBJECT_ID(N'[KVK].[KVK_Player_Windowed]')
      AND c.name = N'max_contribute_gain'
)
BEGIN
ALTER TABLE [KVK].[KVK_Player_Windowed] ADD CONSTRAINT [DF_PlayerWin_MaxContrib] DEFAULT ((0)) FOR [max_contribute_gain]
END
IF NOT EXISTS (
    SELECT 1
    FROM sys.default_constraints dc
    INNER JOIN sys.columns c
        ON c.object_id = dc.parent_object_id
       AND c.column_id = dc.parent_column_id
    WHERE dc.parent_object_id = OBJECT_ID(N'[KVK].[KVK_Player_Windowed]')
      AND c.name = N'cur_contribute_gain'
)
BEGIN
ALTER TABLE [KVK].[KVK_Player_Windowed] ADD CONSTRAINT [DF_PlayerWin_CurContrib] DEFAULT ((0)) FOR [cur_contribute_gain]
END
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Player_Windowed]') AND name = N'IX_KVK_Player_Windowed_KVK_NO_governor_id')
CREATE NONCLUSTERED INDEX [IX_KVK_Player_Windowed_KVK_NO_governor_id] ON [KVK].[KVK_Player_Windowed]
(
	[KVK_NO] ASC,
	[governor_id] ASC
)
INCLUDE([kingdom],[starting_power]) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Player_Windowed]') AND name = N'IX_KVK_Player_Windowed_KVK_NO_Kingdom')
CREATE NONCLUSTERED INDEX [IX_KVK_Player_Windowed_KVK_NO_Kingdom] ON [KVK].[KVK_Player_Windowed]
(
	[KVK_NO] ASC,
	[kingdom] ASC
)
INCLUDE([governor_id],[starting_power]) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
SET ANSI_PADDING ON

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Player_Windowed]') AND name = N'IX_KVK_Player_Windowed_KVK_NO_WindowName')
CREATE NONCLUSTERED INDEX [IX_KVK_Player_Windowed_KVK_NO_WindowName] ON [KVK].[KVK_Player_Windowed]
(
	[KVK_NO] ASC,
	[WindowName] ASC
)
INCLUDE([governor_id],[name],[kingdom],[campid],[t4_kills],[t5_kills],[deads],[starting_power]) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
SET ANSI_PADDING ON

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Player_Windowed]') AND name = N'IX_PlayerWin_Camp')
CREATE NONCLUSTERED INDEX [IX_PlayerWin_Camp] ON [KVK].[KVK_Player_Windowed]
(
	[KVK_NO] ASC,
	[WindowName] ASC,
	[campid] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Player_Windowed]') AND name = N'IX_PlayerWin_Delete_KVKNO')
CREATE NONCLUSTERED INDEX [IX_PlayerWin_Delete_KVKNO] ON [KVK].[KVK_Player_Windowed]
(
	[KVK_NO] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
SET ANSI_PADDING ON

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Player_Windowed]') AND name = N'IX_PlayerWin_Kingdom')
CREATE NONCLUSTERED INDEX [IX_PlayerWin_Kingdom] ON [KVK].[KVK_Player_Windowed]
(
	[KVK_NO] ASC,
	[WindowName] ASC,
	[kingdom] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[KVK].[DF_PlayerWin_At]') AND type = 'D')
BEGIN
ALTER TABLE [KVK].[KVK_Player_Windowed] ADD  CONSTRAINT [DF_PlayerWin_At]  DEFAULT (sysutcdatetime()) FOR [computed_at_utc]
END



GO


PRINT N'Applying KVK.KVK_Kingdom_Windowed.Table.sql';

SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Kingdom_Windowed]') AND type in (N'U'))
BEGIN
CREATE TABLE [KVK].[KVK_Kingdom_Windowed](
	[KVK_NO] [int] NOT NULL,
	[WindowName] [nvarchar](40) COLLATE Latin1_General_CI_AS NOT NULL,
	[kingdom] [int] NOT NULL,
	[kp_gain] [bigint] NOT NULL,
	[kills_gain] [bigint] NOT NULL,
	[t4_kills] [bigint] NOT NULL,
	[t5_kills] [bigint] NOT NULL,
	[kp_loss] [bigint] NOT NULL,
	[healed_troops] [bigint] NOT NULL,
	[deads] [bigint] NOT NULL,
	[max_contribute_gain] [bigint] NOT NULL,
	[cur_contribute_gain] [bigint] NOT NULL,
	[dkp] [float] NOT NULL,
	[last_scan_id] [int] NOT NULL,
	[computed_at_utc] [datetime2](0) NOT NULL,
	[campid] [int] NOT NULL,
	[camp_name] [nvarchar](100) COLLATE Latin1_General_CI_AS NOT NULL,
 CONSTRAINT [PK_KVK_Kingdom_Windowed] PRIMARY KEY CLUSTERED
(
	[KVK_NO] ASC,
	[WindowName] ASC,
	[kingdom] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
END
IF COL_LENGTH('KVK.KVK_Kingdom_Windowed', 'max_contribute_gain') IS NULL
BEGIN
ALTER TABLE [KVK].[KVK_Kingdom_Windowed] ADD [max_contribute_gain] [bigint] NOT NULL CONSTRAINT [DF_KingdomWin_MaxContrib] DEFAULT ((0)) WITH VALUES
END
IF COL_LENGTH('KVK.KVK_Kingdom_Windowed', 'cur_contribute_gain') IS NULL
BEGIN
ALTER TABLE [KVK].[KVK_Kingdom_Windowed] ADD [cur_contribute_gain] [bigint] NOT NULL CONSTRAINT [DF_KingdomWin_CurContrib] DEFAULT ((0)) WITH VALUES
END
IF NOT EXISTS (
    SELECT 1
    FROM sys.default_constraints dc
    INNER JOIN sys.columns c
        ON c.object_id = dc.parent_object_id
       AND c.column_id = dc.parent_column_id
    WHERE dc.parent_object_id = OBJECT_ID(N'[KVK].[KVK_Kingdom_Windowed]')
      AND c.name = N'max_contribute_gain'
)
BEGIN
ALTER TABLE [KVK].[KVK_Kingdom_Windowed] ADD CONSTRAINT [DF_KingdomWin_MaxContrib] DEFAULT ((0)) FOR [max_contribute_gain]
END
IF NOT EXISTS (
    SELECT 1
    FROM sys.default_constraints dc
    INNER JOIN sys.columns c
        ON c.object_id = dc.parent_object_id
       AND c.column_id = dc.parent_column_id
    WHERE dc.parent_object_id = OBJECT_ID(N'[KVK].[KVK_Kingdom_Windowed]')
      AND c.name = N'cur_contribute_gain'
)
BEGIN
ALTER TABLE [KVK].[KVK_Kingdom_Windowed] ADD CONSTRAINT [DF_KingdomWin_CurContrib] DEFAULT ((0)) FOR [cur_contribute_gain]
END
SET ANSI_PADDING ON

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Kingdom_Windowed]') AND name = N'IX_KingWin_KVK')
CREATE NONCLUSTERED INDEX [IX_KingWin_KVK] ON [KVK].[KVK_Kingdom_Windowed]
(
	[KVK_NO] ASC,
	[WindowName] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
SET ANSI_PADDING ON

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Kingdom_Windowed]') AND name = N'IX_KVK_Kingdom_Windowed_KVK_NO_WindowName')
CREATE NONCLUSTERED INDEX [IX_KVK_Kingdom_Windowed_KVK_NO_WindowName] ON [KVK].[KVK_Kingdom_Windowed]
(
	[KVK_NO] ASC,
	[WindowName] ASC
)
INCLUDE([kingdom],[t4_kills],[t5_kills],[deads]) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[KVK].[DF_KingWin_At]') AND type = 'D')
BEGIN
ALTER TABLE [KVK].[KVK_Kingdom_Windowed] ADD  CONSTRAINT [DF_KingWin_At]  DEFAULT (sysutcdatetime()) FOR [computed_at_utc]
END

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[KVK].[DF_KingdomWin_campid]') AND type = 'D')
BEGIN
ALTER TABLE [KVK].[KVK_Kingdom_Windowed] ADD  CONSTRAINT [DF_KingdomWin_campid]  DEFAULT ((0)) FOR [campid]
END

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[KVK].[DF_KingdomWin_campname]') AND type = 'D')
BEGIN
ALTER TABLE [KVK].[KVK_Kingdom_Windowed] ADD  CONSTRAINT [DF_KingdomWin_campname]  DEFAULT (N'') FOR [camp_name]
END



GO


PRINT N'Applying KVK.KVK_Camp_Windowed.Table.sql';

SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Camp_Windowed]') AND type in (N'U'))
BEGIN
CREATE TABLE [KVK].[KVK_Camp_Windowed](
	[KVK_NO] [int] NOT NULL,
	[WindowName] [nvarchar](40) COLLATE Latin1_General_CI_AS NOT NULL,
	[campid] [tinyint] NOT NULL,
	[camp_name] [nvarchar](40) COLLATE Latin1_General_CI_AS NOT NULL,
	[kp_gain] [bigint] NOT NULL,
	[kills_gain] [bigint] NOT NULL,
	[t4_kills] [bigint] NOT NULL,
	[t5_kills] [bigint] NOT NULL,
	[kp_loss] [bigint] NOT NULL,
	[healed_troops] [bigint] NOT NULL,
	[deads] [bigint] NOT NULL,
	[max_contribute_gain] [bigint] NOT NULL,
	[cur_contribute_gain] [bigint] NOT NULL,
	[dkp] [float] NOT NULL,
	[last_scan_id] [int] NOT NULL,
	[computed_at_utc] [datetime2](0) NOT NULL,
 CONSTRAINT [PK_KVK_Camp_Windowed] PRIMARY KEY CLUSTERED
(
	[KVK_NO] ASC,
	[WindowName] ASC,
	[campid] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
END
IF COL_LENGTH('KVK.KVK_Camp_Windowed', 'max_contribute_gain') IS NULL
BEGIN
ALTER TABLE [KVK].[KVK_Camp_Windowed] ADD [max_contribute_gain] [bigint] NOT NULL CONSTRAINT [DF_CampWin_MaxContrib] DEFAULT ((0)) WITH VALUES
END
IF COL_LENGTH('KVK.KVK_Camp_Windowed', 'cur_contribute_gain') IS NULL
BEGIN
ALTER TABLE [KVK].[KVK_Camp_Windowed] ADD [cur_contribute_gain] [bigint] NOT NULL CONSTRAINT [DF_CampWin_CurContrib] DEFAULT ((0)) WITH VALUES
END
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[KVK].[DF_CampWin_MaxContrib]') AND type = 'D')
BEGIN
ALTER TABLE [KVK].[KVK_Camp_Windowed] ADD CONSTRAINT [DF_CampWin_MaxContrib] DEFAULT ((0)) FOR [max_contribute_gain]
END
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[KVK].[DF_CampWin_CurContrib]') AND type = 'D')
BEGIN
ALTER TABLE [KVK].[KVK_Camp_Windowed] ADD CONSTRAINT [DF_CampWin_CurContrib] DEFAULT ((0)) FOR [cur_contribute_gain]
END
SET ANSI_PADDING ON

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Camp_Windowed]') AND name = N'IX_CampWin_KVK')
CREATE NONCLUSTERED INDEX [IX_CampWin_KVK] ON [KVK].[KVK_Camp_Windowed]
(
	[KVK_NO] ASC,
	[WindowName] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
SET ANSI_PADDING ON

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Camp_Windowed]') AND name = N'IX_KVK_Camp_Windowed_KVK_NO_WindowName')
CREATE NONCLUSTERED INDEX [IX_KVK_Camp_Windowed_KVK_NO_WindowName] ON [KVK].[KVK_Camp_Windowed]
(
	[KVK_NO] ASC,
	[WindowName] ASC
)
INCLUDE([campid],[camp_name],[t4_kills],[t5_kills],[deads]) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[KVK].[DF_CampWin_At]') AND type = 'D')
BEGIN
ALTER TABLE [KVK].[KVK_Camp_Windowed] ADD  CONSTRAINT [DF_CampWin_At]  DEFAULT (sysutcdatetime()) FOR [computed_at_utc]
END



GO


PRINT N'Applying KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql';

SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[KVK].[sp_KVK_Recompute_Windows]') AND type in (N'P', N'PC'))
BEGIN
EXEC dbo.sp_executesql @statement = N'CREATE PROCEDURE [KVK].[sp_KVK_Recompute_Windows] AS'
END
ALTER PROCEDURE [KVK].[sp_KVK_Recompute_Windows]
	@KVK_NO [int]
WITH EXECUTE AS CALLER
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    ----------------------------------------------------------------
    -- 0) Validations & setup
    ----------------------------------------------------------------
    IF @KVK_NO IS NULL
        THROW 60001, 'KVK_NO is required.', 1;

    DECLARE @MaxScanID INT;
    SELECT @MaxScanID = MAX(ScanID)
    FROM KVK.KVK_Scan WITH (READCOMMITTEDLOCK)
    WHERE KVK_NO = @KVK_NO;

    IF @MaxScanID IS NULL
        THROW 60002, 'No scans exist for this KVK_NO.', 1;

    DECLARE @X FLOAT, @Y FLOAT, @Z FLOAT;

    SELECT TOP (1)
        @X = WeightT4X, @Y = WeightT5Y, @Z = WeightDeadsZ
    FROM KVK.KVK_DKPWeights WITH (READCOMMITTEDLOCK)
    WHERE KVK_NO = @KVK_NO
    ORDER BY EffectiveFromUTC DESC;

    IF @X IS NULL OR @Y IS NULL OR @Z IS NULL
        THROW 60003, 'DKP weights not defined for this KVK.', 1;

    ----------------------------------------------------------------
    -- 1) Clear existing outputs for this KVK (full overwrite)
	--    Keep Camp/Kingdom single-shot (small), batch Player (largest) for predictability.
    ----------------------------------------------------------------
    DELETE FROM KVK.KVK_Camp_Windowed    WHERE KVK_NO = @KVK_NO;
    DELETE FROM KVK.KVK_Kingdom_Windowed WHERE KVK_NO = @KVK_NO;

    DECLARE @DeleteBatchSize INT = 20000;

    DECLARE @RowsDeleted INT;

    WHILE 1 = 1
    BEGIN
        DELETE TOP (@DeleteBatchSize) p
        FROM KVK.KVK_Player_Windowed p WITH (INDEX(PK_KVK_Player_Windowed), PAGLOCK)
        WHERE p.KVK_NO = @KVK_NO;

        SET @RowsDeleted = @@ROWCOUNT;

        IF @RowsDeleted = 0 BREAK;
        IF @RowsDeleted < @DeleteBatchSize BREAK; -- typically avoids one extra terminal no-op pass
    END;

    ----------------------------------------------------------------
    -- 2) Baseline rows (validation view): zeros + fixed starting_power
    ----------------------------------------------------------------
    ;WITH base AS (
        SELECT b.KVK_NO,
               b.governor_id,
               b.starting_power,
               b.baseline_scan_id,
               r.name,
               r.kingdom
        FROM KVK.KVK_Player_Baseline b
        LEFT JOIN KVK.KVK_AllPlayers_Raw r
               ON r.KVK_NO = b.KVK_NO
              AND r.ScanID = b.baseline_scan_id
              AND r.governor_id = b.governor_id
        WHERE b.KVK_NO = @KVK_NO
    ),
    cm AS (
        SELECT KVK_NO, Kingdom, CampID, CampName
        FROM KVK.KVK_CampMap
        WHERE KVK_NO = @KVK_NO
    )
    INSERT INTO KVK.KVK_Player_Windowed
    (
        KVK_NO, WindowName, governor_id, name, kingdom, campid,
        kp_gain, kp_gain_recalc, kills_gain, t4_kills, t5_kills,
        kp_loss, healed_troops, deads, max_contribute_gain, cur_contribute_gain,
        starting_power, dkp,
        last_scan_id, computed_at_utc
    )
    SELECT  @KVK_NO, N'Baseline', b.governor_id, b.name, b.kingdom,
            ISNULL(cm.CampID, 0),
            0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, b.starting_power, 0.0,
            b.baseline_scan_id, SYSUTCDATETIME()
    FROM base b
    LEFT JOIN cm
      ON cm.KVK_NO = b.KVK_NO AND cm.Kingdom = b.kingdom;

    ----------------------------------------------------------------
    -- 3) Windowed deltas (Start→End, End defaults to MaxScanID)
    --    Window delta = End cumulative - Start cumulative
    ----------------------------------------------------------------
	;WITH W AS (
		SELECT
			RTRIM(w.WindowName) AS WindowName,
			w.StartScanID,
			-- Auto-cap EndScanID to max available scan (prevents future scan references)
			CASE
				WHEN w.EndScanID IS NULL THEN @MaxScanID
				WHEN w.EndScanID > @MaxScanID THEN @MaxScanID  -- ← NEW: Safety cap
				ELSE w.EndScanID
			END AS EndScanID
		FROM KVK.KVK_Windows w WITH (READCOMMITTEDLOCK)
		WHERE w.KVK_NO = @KVK_NO
		  AND w.StartScanID IS NOT NULL
		  AND w.WindowName <> N'Baseline'
	),
    S AS (
        SELECT
            W.WindowName, W.StartScanID, W.EndScanID,
            r.governor_id, r.name, r.kingdom,
            COALESCE(r.kill_points_diff, r.points_difference, r.max_kill_points - r.min_kill_points, 0) AS kp_s,
            COALESCE(r.kills_iv_diff, r.max_kills_iv - r.min_kills_iv, 0) AS t4_s,
            COALESCE(r.kills_v_diff, r.max_kills_v - r.min_kills_v, 0) AS t5_s,
            COALESCE(r.dead_diff, r.max_dead - r.min_dead, 0) AS deads_s,
            COALESCE(r.healed_troops, r.max_units_healed_diff, r.max_units_healed - r.min_units_healed, 0) AS heals_s,
            COALESCE(r.max_contribute_diff, r.max_max_contribute - r.min_max_contribute, 0) AS max_contrib_s,
            COALESCE(r.cur_contribute_diff, r.max_cur_contribute - r.min_cur_contribute, 0) AS cur_contrib_s
        FROM W
        JOIN KVK.KVK_AllPlayers_Raw r
          ON r.KVK_NO = @KVK_NO
         AND r.ScanID = W.StartScanID
    ),
    E AS (
        SELECT
            W.WindowName, W.StartScanID, W.EndScanID,
            r.governor_id, r.name, r.kingdom,
            COALESCE(r.kill_points_diff, r.points_difference, r.max_kill_points - r.min_kill_points, 0) AS kp_e,
            COALESCE(r.kills_iv_diff, r.max_kills_iv - r.min_kills_iv, 0) AS t4_e,
            COALESCE(r.kills_v_diff, r.max_kills_v - r.min_kills_v, 0) AS t5_e,
            COALESCE(r.dead_diff, r.max_dead - r.min_dead, 0) AS deads_e,
            COALESCE(r.healed_troops, r.max_units_healed_diff, r.max_units_healed - r.min_units_healed, 0) AS heals_e,
            COALESCE(r.max_contribute_diff, r.max_max_contribute - r.min_max_contribute, 0) AS max_contrib_e,
            COALESCE(r.cur_contribute_diff, r.max_cur_contribute - r.min_cur_contribute, 0) AS cur_contrib_e
        FROM W
        JOIN KVK.KVK_AllPlayers_Raw r
          ON r.KVK_NO = @KVK_NO
         AND r.ScanID = W.EndScanID
    ),
    U AS (
        -- Full outer join: include govs that appear in Start or End (defensive)
        SELECT
            COALESCE(S.WindowName, E.WindowName) AS WindowName,
            COALESCE(S.StartScanID, E.StartScanID) AS StartScanID,
            COALESCE(S.EndScanID,   E.EndScanID)   AS EndScanID,
            COALESCE(S.governor_id, E.governor_id) AS governor_id,
            COALESCE(E.name, S.name)               AS name,
            COALESCE(E.kingdom, S.kingdom)         AS kingdom,
            -- Deltas
            ISNULL(E.kp_e,0)    - ISNULL(S.kp_s,0)    AS kp_gain,
            (ISNULL(E.t4_e,0)+ISNULL(E.t5_e,0))
          - (ISNULL(S.t4_s,0)+ISNULL(S.t5_s,0))       AS kills_gain,
            ISNULL(E.t4_e,0)   - ISNULL(S.t4_s,0)     AS t4_kills,
            ISNULL(E.t5_e,0)   - ISNULL(S.t5_s,0)     AS t5_kills,
            ISNULL(E.heals_e,0)- ISNULL(S.heals_s,0)  AS healed_troops,
            ISNULL(E.deads_e,0)- ISNULL(S.deads_s,0)  AS deads,
            ISNULL(E.max_contrib_e,0)- ISNULL(S.max_contrib_s,0) AS max_contribute_gain,
            ISNULL(E.cur_contrib_e,0)- ISNULL(S.cur_contrib_s,0) AS cur_contribute_gain
        FROM S
        FULL OUTER JOIN E
          ON E.WindowName = S.WindowName
         AND E.StartScanID = S.StartScanID
         AND E.EndScanID   = S.EndScanID
         AND E.governor_id = S.governor_id
    ),
    B AS (
        SELECT b.governor_id, b.starting_power
        FROM KVK.KVK_Player_Baseline b WITH (READCOMMITTEDLOCK)
        WHERE b.KVK_NO = @KVK_NO
    ),
    CM AS (
        SELECT KVK_NO, Kingdom, CampID, CampName
        FROM KVK.KVK_CampMap WITH (READCOMMITTEDLOCK)
        WHERE KVK_NO = @KVK_NO
    )
    INSERT INTO KVK.KVK_Player_Windowed
    (
        KVK_NO, WindowName, governor_id, name, kingdom, campid,
        kp_gain, kp_gain_recalc, kills_gain, t4_kills, t5_kills,
        kp_loss, healed_troops, deads, max_contribute_gain, cur_contribute_gain,
        starting_power, dkp,
        last_scan_id, computed_at_utc
    )
    SELECT
        @KVK_NO,
        RTRIM(U.WindowName),
        U.governor_id,
        U.name,
        U.kingdom,
        ISNULL(CM.CampID, 0) AS campid,
        -- KP Gain (source-of-truth)
        U.kp_gain,
        -- KP Gain (recalc) = 10*T4 + 20*T5
        (U.t4_kills * 10) + (U.t5_kills * 20) AS kp_gain_recalc,
        U.kills_gain,
        U.t4_kills,
        U.t5_kills,
        -- KP Loss = heals * 20
        (U.healed_troops * 20) AS kp_loss,
        U.healed_troops,
        U.deads,
        U.max_contribute_gain,
        U.cur_contribute_gain,
        ISNULL(B.starting_power, 0) AS starting_power,
        CASE WHEN ISNULL(B.starting_power,0) > 0
             THEN ((U.t4_kills * @X) + (U.t5_kills * @Y) + (U.deads * @Z))
             ELSE 0.0 END AS dkp,
        U.EndScanID,
        SYSUTCDATETIME()
    FROM U
    LEFT JOIN B  ON B.governor_id = U.governor_id
    LEFT JOIN CM ON CM.KVK_NO = @KVK_NO AND CM.Kingdom = U.kingdom;

    ----------------------------------------------------------------
    -- 4) Full KVK (Baseline→MaxScanID): use latest cumulative snapshot
    ----------------------------------------------------------------
    ;WITH E AS (
        SELECT r.governor_id, r.name, r.kingdom,
               COALESCE(r.kill_points_diff, r.points_difference, r.max_kill_points - r.min_kill_points, 0) AS kp,
               COALESCE(r.kills_iv_diff, r.max_kills_iv - r.min_kills_iv, 0) AS t4,
               COALESCE(r.kills_v_diff, r.max_kills_v - r.min_kills_v, 0) AS t5,
               COALESCE(r.dead_diff, r.max_dead - r.min_dead, 0) AS deads,
               COALESCE(r.healed_troops, r.max_units_healed_diff, r.max_units_healed - r.min_units_healed, 0) AS heals,
               COALESCE(r.max_contribute_diff, r.max_max_contribute - r.min_max_contribute, 0) AS max_contribute_gain,
               COALESCE(r.cur_contribute_diff, r.max_cur_contribute - r.min_cur_contribute, 0) AS cur_contribute_gain
        FROM KVK.KVK_AllPlayers_Raw r WITH (READCOMMITTEDLOCK)
        WHERE r.KVK_NO = @KVK_NO
          AND r.ScanID = @MaxScanID
    ),
    B AS (
        SELECT governor_id, starting_power
        FROM KVK.KVK_Player_Baseline WITH (READCOMMITTEDLOCK)
        WHERE KVK_NO = @KVK_NO
    ),
    CM AS (
        SELECT KVK_NO, Kingdom, CampID, CampName
        FROM KVK.KVK_CampMap WITH (READCOMMITTEDLOCK)
        WHERE KVK_NO = @KVK_NO
    )
    INSERT INTO KVK.KVK_Player_Windowed
    (
        KVK_NO, WindowName, governor_id, name, kingdom, campid,
        kp_gain, kp_gain_recalc, kills_gain, t4_kills, t5_kills,
        kp_loss, healed_troops, deads, max_contribute_gain, cur_contribute_gain,
        starting_power, dkp,
        last_scan_id, computed_at_utc
    )
    SELECT
        @KVK_NO,
        N'Full',
        E.governor_id,
        E.name,
        E.kingdom,
        ISNULL(CM.CampID, 0),
        -- Full uses cumulative since baseline (End-only)
        E.kp,
        (E.t4 * 10) + (E.t5 * 20) AS kp_gain_recalc,
        (E.t4 + E.t5)             AS kills_gain,
        E.t4, E.t5,
        (E.heals * 20)            AS kp_loss,
        E.heals,
        E.deads,
        E.max_contribute_gain,
        E.cur_contribute_gain,
        ISNULL(B.starting_power, 0) AS starting_power,
        CASE WHEN ISNULL(B.starting_power,0) > 0
             THEN ((E.t4 * @X) + (E.t5 * @Y) + (E.deads * @Z))
             ELSE 0.0 END AS dkp,
        @MaxScanID,
        SYSUTCDATETIME()
    FROM E
    LEFT JOIN B  ON B.governor_id = E.governor_id
    LEFT JOIN CM ON CM.KVK_NO = @KVK_NO AND CM.Kingdom = E.kingdom;

    ----------------------------------------------------------------
    -- 5) Rollups (Kingdom & Camp) from Player_Windowed just written
    ----------------------------------------------------------------
    -- Kingdom
    ;WITH P AS (
		SELECT *
		FROM KVK.KVK_Player_Windowed WITH (READCOMMITTEDLOCK)
		WHERE KVK_NO = @KVK_NO
	),
	CM AS (
		SELECT KVK_NO, Kingdom, CampID, CampName
		FROM KVK.KVK_CampMap WITH (READCOMMITTEDLOCK)
		WHERE KVK_NO = @KVK_NO
	),
	K AS (
		SELECT
			@KVK_NO AS KVK_NO,
			p.WindowName,
			p.kingdom,
			ISNULL(cm.CampID, 0)        AS campid,
			ISNULL(cm.CampName, N'')    AS camp_name,
			SUM(p.kp_gain)              AS kp_gain,
			SUM(p.kp_gain_recalc)       AS kp_gain_recalc, -- only used for DKP calc here
			SUM(p.kills_gain)           AS kills_gain,
			SUM(p.t4_kills)             AS t4_kills,
			SUM(p.t5_kills)             AS t5_kills,
			SUM(p.kp_loss)              AS kp_loss,
			SUM(p.healed_troops)        AS healed_troops,
			SUM(p.deads)                AS deads,
			SUM(p.max_contribute_gain)  AS max_contribute_gain,
			SUM(p.cur_contribute_gain)  AS cur_contribute_gain,
			SUM(p.starting_power)       AS starting_power_sum,
			MAX(p.last_scan_id)         AS last_scan_id
		FROM P p
		LEFT JOIN CM
		  ON CM.KVK_NO = @KVK_NO
		 AND CM.Kingdom = p.kingdom
		GROUP BY p.WindowName, p.kingdom, ISNULL(cm.CampID, 0), ISNULL(cm.CampName, N'')
	)
	INSERT INTO KVK.KVK_Kingdom_Windowed
	(
		KVK_NO, WindowName, kingdom, campid, camp_name,
		kp_gain, kills_gain, t4_kills, t5_kills,
		kp_loss, healed_troops, deads, max_contribute_gain, cur_contribute_gain, dkp,
		last_scan_id, computed_at_utc
	)
	SELECT
		K.KVK_NO, K.WindowName, K.kingdom, K.campid, K.camp_name,
		K.kp_gain, K.kills_gain, K.t4_kills, K.t5_kills,
		K.kp_loss, K.healed_troops, K.deads, K.max_contribute_gain, K.cur_contribute_gain,
		CASE WHEN K.starting_power_sum > 0
			 THEN ((K.t4_kills * @X) + (K.t5_kills * @Y) + (K.deads * @Z))
			 ELSE 0.0 END AS dkp,
		K.last_scan_id,
		SYSUTCDATETIME()
	FROM K;

    -- Camp
    ;WITH P AS (
        SELECT *
        FROM KVK.KVK_Player_Windowed WITH (READCOMMITTEDLOCK)
        WHERE KVK_NO = @KVK_NO
    ),
    CM AS (
        SELECT KVK_NO, Kingdom, CampID, CampName
        FROM KVK.KVK_CampMap WITH (READCOMMITTEDLOCK)
        WHERE KVK_NO = @KVK_NO
    ),
    C AS (
        SELECT
            @KVK_NO AS KVK_NO,
            p.WindowName,
            ISNULL(cm.CampID, 0)   AS campid,
            ISNULL(cm.CampName, N'') AS camp_name,
            SUM(p.kp_gain)         AS kp_gain,
            SUM(p.kills_gain)      AS kills_gain,
            SUM(p.t4_kills)        AS t4_kills,
            SUM(p.t5_kills)        AS t5_kills,
            SUM(p.kp_loss)         AS kp_loss,
            SUM(p.healed_troops)   AS healed_troops,
            SUM(p.deads)           AS deads,
            SUM(p.max_contribute_gain) AS max_contribute_gain,
            SUM(p.cur_contribute_gain) AS cur_contribute_gain,
            SUM(p.starting_power)  AS starting_power_sum,
            MAX(p.last_scan_id)    AS last_scan_id
        FROM P p
        LEFT JOIN CM
          ON CM.KVK_NO = @KVK_NO AND CM.Kingdom = p.kingdom
        GROUP BY p.WindowName, ISNULL(cm.CampID, 0), ISNULL(cm.CampName, N'')
    )
    INSERT INTO KVK.KVK_Camp_Windowed
    (
        KVK_NO, WindowName, campid, camp_name,
        kp_gain, kills_gain, t4_kills, t5_kills,
        kp_loss, healed_troops, deads, max_contribute_gain, cur_contribute_gain, dkp,
        last_scan_id, computed_at_utc
    )
    SELECT
        C.KVK_NO, C.WindowName, C.campid, C.camp_name,
        C.kp_gain, C.kills_gain, C.t4_kills, C.t5_kills,
        C.kp_loss, C.healed_troops, C.deads, C.max_contribute_gain, C.cur_contribute_gain,
        CASE WHEN C.starting_power_sum > 0
             THEN ((C.t4_kills * @X) + (C.t5_kills * @Y) + (C.deads * @Z))
             ELSE 0.0 END AS dkp,
        C.last_scan_id,
        SYSUTCDATETIME()
    FROM C;

    RETURN 0;
END



GO


PRINT N'Applying KVK.sp_KVK_Get_Exports.StoredProcedure.sql';

SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[KVK].[sp_KVK_Get_Exports]') AND type in (N'P', N'PC'))
BEGIN
EXEC dbo.sp_executesql @statement = N'CREATE PROCEDURE [KVK].[sp_KVK_Get_Exports] AS'
END
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
        Row_Count,               -- note: your column rename
        ImportedAtUTC,
        UploaderDiscordID
    FROM KVK.KVK_Scan
    WHERE KVK_NO = @KVK_NO
    ORDER BY ScanID;

    ----------------------------------------------------------------
    -- 2) KVK_Windows (effective end also shown)
    ----------------------------------------------------------------
    DECLARE @MaxScanID INT = (SELECT MAX(ScanID) FROM KVK.KVK_Scan WHERE KVK_NO=@KVK_NO);

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
    -- 3) KVK_DKP_Weights (latest first)
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
    -- 4) Player Windowed (all windows including Baseline/Full)
    ----------------------------------------------------------------
    SELECT
        KVK_NO, WindowName, governor_id, name, kingdom, campid,
        kp_gain, kp_gain_recalc, kills_gain, t4_kills, t5_kills,
        kp_loss, healed_troops, deads, starting_power, dkp,
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
		kp_loss, healed_troops, deads, dkp,
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
        kp_loss, healed_troops, deads, dkp,
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
        kp_loss, healed_troops, deads, starting_power, dkp,
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
        kp_loss, healed_troops, deads, dkp,
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
        kp_loss, healed_troops, deads, dkp,
        last_scan_id, computed_at_utc
    FROM KVK.KVK_Camp_Windowed
    WHERE KVK_NO = @KVK_NO AND WindowName = N'Full'
    ORDER BY dkp DESC;

    ----------------------------------------------------------------
    -- 10) Negative Corrections (all for this KVK)
    ----------------------------------------------------------------
    SELECT
        KVK_NO, ScanID, governor_id, name, kingdom, campid,
        field_name, value, recorded_at_utc
    FROM KVK.KVK_Ingest_Negatives
    WHERE KVK_NO = @KVK_NO
    ORDER BY ScanID, governor_id, field_name;
END



GO
