SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
GO

/*
KVK_ALL Schema Modernisation - Phase 8 Ingest Diagnostics & Retention

Purpose:
- Add durable ingest diagnostic visibility for failed/rejected KVK_ALL imports.
- Add an age-based cleanup path for stale staged rows and old diagnostics.
- Preserve current ingest, recompute, export, Google Sheets, admin command, and Discord behaviour.

Retention policy:
- Staged rows are transient and may be cleaned after 24 hours by default.
- Ingest diagnostics are retained for 90 days by default.
- Negative correction diagnostics are retained for 365 days by default.
- Cleanup defaults to dry-run and refuses sub-1-hour stage retention.
*/

IF OBJECT_ID(N'[KVK].[KVK_AllPlayers_Stage]', N'U') IS NULL
    THROW 51001, 'Required table KVK.KVK_AllPlayers_Stage does not exist.', 1;

IF OBJECT_ID(N'[KVK].[KVK_Ingest_Negatives]', N'U') IS NULL
    THROW 51002, 'Required table KVK.KVK_Ingest_Negatives does not exist.', 1;

PRINT N'Applying KVK.KVK_AllPlayers_Stage staged_at_utc retention marker';

IF COL_LENGTH('KVK.KVK_AllPlayers_Stage', 'staged_at_utc') IS NULL
BEGIN
    ALTER TABLE [KVK].[KVK_AllPlayers_Stage]
    ADD [staged_at_utc] [datetime2](0) NOT NULL
        CONSTRAINT [DF_KVK_AllPlayers_Stage_StagedAtUTC] DEFAULT (sysutcdatetime())
        WITH VALUES;
END

IF NOT EXISTS (
    SELECT 1
    FROM sys.default_constraints dc
    INNER JOIN sys.columns c
        ON c.object_id = dc.parent_object_id
       AND c.column_id = dc.parent_column_id
    WHERE dc.parent_object_id = OBJECT_ID(N'[KVK].[KVK_AllPlayers_Stage]')
      AND c.name = N'staged_at_utc'
)
BEGIN
    ALTER TABLE [KVK].[KVK_AllPlayers_Stage]
    ADD CONSTRAINT [DF_KVK_AllPlayers_Stage_StagedAtUTC]
    DEFAULT (sysutcdatetime()) FOR [staged_at_utc];
END

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'[KVK].[KVK_AllPlayers_Stage]')
      AND name = N'IX_KVK_AllPlayers_Stage_StagedAt'
)
CREATE NONCLUSTERED INDEX [IX_KVK_AllPlayers_Stage_StagedAt]
ON [KVK].[KVK_AllPlayers_Stage] ([staged_at_utc] ASC)
INCLUDE ([IngestToken]);

PRINT N'Applying KVK.KVK_Ingest_Diagnostics';

IF OBJECT_ID(N'[KVK].[KVK_Ingest_Diagnostics]', N'U') IS NULL
BEGIN
CREATE TABLE [KVK].[KVK_Ingest_Diagnostics](
    [DiagnosticID] [bigint] IDENTITY(1,1) NOT NULL,
    [CreatedUTC] [datetime2](0) NOT NULL,
    [DiagnosticStatus] [varchar](20) COLLATE Latin1_General_CI_AS NOT NULL,
    [DiagnosticType] [nvarchar](64) COLLATE Latin1_General_CI_AS NOT NULL,
    [IngestToken] [uniqueidentifier] NULL,
    [KVK_NO] [int] NULL,
    [ScanID] [int] NULL,
    [SourceFileName] [nvarchar](255) COLLATE Latin1_General_CI_AS NULL,
    [FileHashSha256] [char](64) COLLATE Latin1_General_CI_AS NULL,
    [UploaderDiscordID] [bigint] NULL,
    [SchemaVersion] [nvarchar](64) COLLATE Latin1_General_CI_AS NULL,
    [SourceSheetName] [nvarchar](128) COLLATE Latin1_General_CI_AS NULL,
    [SourceColumnHash] [char](64) COLLATE Latin1_General_CI_AS NULL,
    [SourceColumnCount] [int] NULL,
    [SourceRowCount] [int] NULL,
    [StagedRowCount] [int] NULL,
    [ErrorText] [nvarchar](1000) COLLATE Latin1_General_CI_AS NULL,
    [ContextJson] [nvarchar](max) COLLATE Latin1_General_CI_AS NULL,
 CONSTRAINT [PK_KVK_Ingest_Diagnostics] PRIMARY KEY CLUSTERED
(
    [DiagnosticID] ASC
) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF,
        ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF)
);
END

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns c
    LEFT JOIN sys.default_constraints dc
        ON dc.parent_object_id = c.object_id
       AND dc.parent_column_id = c.column_id
    WHERE c.object_id = OBJECT_ID(N'[KVK].[KVK_Ingest_Diagnostics]')
      AND c.name = N'CreatedUTC'
      AND dc.object_id IS NOT NULL
)
BEGIN
    ALTER TABLE [KVK].[KVK_Ingest_Diagnostics]
    ADD CONSTRAINT [DF_KVK_IngestDiag_CreatedUTC]
    DEFAULT (sysutcdatetime()) FOR [CreatedUTC];
END

IF NOT EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE object_id = OBJECT_ID(N'[KVK].[CK_KVK_IngestDiag_Status]')
      AND parent_object_id = OBJECT_ID(N'[KVK].[KVK_Ingest_Diagnostics]')
)
ALTER TABLE [KVK].[KVK_Ingest_Diagnostics] WITH CHECK
ADD CONSTRAINT [CK_KVK_IngestDiag_Status]
CHECK ([DiagnosticStatus] IN ('failed', 'rejected', 'cleanup'));

IF EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE object_id = OBJECT_ID(N'[KVK].[CK_KVK_IngestDiag_Status]')
      AND parent_object_id = OBJECT_ID(N'[KVK].[KVK_Ingest_Diagnostics]')
)
ALTER TABLE [KVK].[KVK_Ingest_Diagnostics] CHECK CONSTRAINT [CK_KVK_IngestDiag_Status];

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Ingest_Diagnostics]')
      AND name = N'IX_KVK_IngestDiag_Status_Created'
)
CREATE NONCLUSTERED INDEX [IX_KVK_IngestDiag_Status_Created]
ON [KVK].[KVK_Ingest_Diagnostics] ([DiagnosticStatus] ASC, [CreatedUTC] DESC)
INCLUDE ([DiagnosticType], [KVK_NO], [ScanID], [SourceFileName], [SchemaVersion], [SourceSheetName]);

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Ingest_Diagnostics]')
      AND name = N'IX_KVK_IngestDiag_Token'
)
CREATE NONCLUSTERED INDEX [IX_KVK_IngestDiag_Token]
ON [KVK].[KVK_Ingest_Diagnostics] ([IngestToken] ASC, [CreatedUTC] DESC)
INCLUDE ([DiagnosticStatus], [DiagnosticType], [SourceFileName], [StagedRowCount]);

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Ingest_Diagnostics]')
      AND name = N'IX_KVK_IngestDiag_KVK_Scan'
)
CREATE NONCLUSTERED INDEX [IX_KVK_IngestDiag_KVK_Scan]
ON [KVK].[KVK_Ingest_Diagnostics] ([KVK_NO] ASC, [ScanID] ASC, [CreatedUTC] DESC)
INCLUDE ([DiagnosticStatus], [DiagnosticType], [SourceFileName]);

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'[KVK].[KVK_Ingest_Diagnostics]')
      AND name = N'IX_KVK_IngestDiag_Created'
)
CREATE NONCLUSTERED INDEX [IX_KVK_IngestDiag_Created]
ON [KVK].[KVK_Ingest_Diagnostics] ([CreatedUTC] ASC)
INCLUDE ([DiagnosticStatus], [DiagnosticType]);

PRINT N'Applying KVK.sp_KVK_Ingest_Cleanup';

IF NOT EXISTS (
    SELECT 1
    FROM sys.objects
    WHERE object_id = OBJECT_ID(N'[KVK].[sp_KVK_Ingest_Cleanup]')
      AND type in (N'P', N'PC')
)
BEGIN
    EXEC dbo.sp_executesql @statement = N'CREATE PROCEDURE [KVK].[sp_KVK_Ingest_Cleanup] AS';
END
GO

ALTER PROCEDURE [KVK].[sp_KVK_Ingest_Cleanup]
    @StageRetentionHours [int] = 24,
    @DiagnosticRetentionDays [int] = 90,
    @NegativeRetentionDays [int] = 365,
    @DryRun [bit] = 1,
    @NowUTC [datetime2](0) = NULL
WITH EXECUTE AS CALLER
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    IF @StageRetentionHours IS NULL OR @StageRetentionHours < 1
        THROW 51010, 'Stage retention must be at least 1 hour.', 1;
    IF @DiagnosticRetentionDays IS NULL OR @DiagnosticRetentionDays < 1
        THROW 51011, 'Diagnostic retention must be at least 1 day.', 1;
    IF @NegativeRetentionDays IS NULL OR @NegativeRetentionDays < 1
        THROW 51012, 'Negative diagnostic retention must be at least 1 day.', 1;

    DECLARE @EffectiveNow datetime2(0) = COALESCE(@NowUTC, SYSUTCDATETIME());
    DECLARE @StageCutoff datetime2(0) = DATEADD(hour, -@StageRetentionHours, @EffectiveNow);
    DECLARE @DiagnosticCutoff datetime2(0) = DATEADD(day, -@DiagnosticRetentionDays, @EffectiveNow);
    DECLARE @NegativeCutoff datetime2(0) = DATEADD(day, -@NegativeRetentionDays, @EffectiveNow);

    DECLARE @StageRows int = (
        SELECT COUNT(*)
        FROM KVK.KVK_AllPlayers_Stage WITH (READCOMMITTEDLOCK)
        WHERE staged_at_utc < @StageCutoff
    );
    DECLARE @DiagnosticRows int = (
        SELECT COUNT(*)
        FROM KVK.KVK_Ingest_Diagnostics WITH (READCOMMITTEDLOCK)
        WHERE CreatedUTC < @DiagnosticCutoff
    );
    DECLARE @NegativeRows int = (
        SELECT COUNT(*)
        FROM KVK.KVK_Ingest_Negatives WITH (READCOMMITTEDLOCK)
        WHERE recorded_at_utc < @NegativeCutoff
    );

    IF @DryRun = 0
    BEGIN
        BEGIN TRANSACTION;

        DELETE FROM KVK.KVK_AllPlayers_Stage
        WHERE staged_at_utc < @StageCutoff;
        SET @StageRows = @@ROWCOUNT;

        DELETE FROM KVK.KVK_Ingest_Diagnostics
        WHERE CreatedUTC < @DiagnosticCutoff;
        SET @DiagnosticRows = @@ROWCOUNT;

        DELETE FROM KVK.KVK_Ingest_Negatives
        WHERE recorded_at_utc < @NegativeCutoff;
        SET @NegativeRows = @@ROWCOUNT;

        INSERT INTO KVK.KVK_Ingest_Diagnostics
        (
            DiagnosticStatus, DiagnosticType, ErrorText, ContextJson
        )
        VALUES
        (
            'cleanup',
            N'retention_cleanup',
            N'KVK ingest retention cleanup completed.',
            CONCAT(
                N'{"stage_retention_hours":', @StageRetentionHours,
                N',"diagnostic_retention_days":', @DiagnosticRetentionDays,
                N',"negative_retention_days":', @NegativeRetentionDays,
                N',"stage_rows_deleted":', @StageRows,
                N',"diagnostic_rows_deleted":', @DiagnosticRows,
                N',"negative_rows_deleted":', @NegativeRows,
                N'}'
            )
        );

        COMMIT TRANSACTION;
    END

    SELECT
        CAST(@DryRun AS bit) AS DryRun,
        @StageCutoff AS StageCutoffUTC,
        @DiagnosticCutoff AS DiagnosticCutoffUTC,
        @NegativeCutoff AS NegativeCutoffUTC,
        @StageRows AS StaleStageRows,
        @DiagnosticRows AS StaleDiagnosticRows,
        @NegativeRows AS StaleNegativeRows;
END
GO
