SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

/* ---------------------------------------------------------------------------
   K98 Event Calendar Schema (Task 1)
   Target DB: ROK_TRACKER
   Idempotent: YES (safe to re-run)
   --------------------------------------------------------------------------- */

-- Optional safety:
-- USE [ROK_TRACKER];
-- GO

/* =========================
   dbo.EventRecurringRules
   ========================= */
IF OBJECT_ID(N'dbo.EventRecurringRules', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.EventRecurringRules
    (
        RuleID               NVARCHAR(128)  NOT NULL,
        IsActive             BIT            NOT NULL CONSTRAINT DF_EventRecurringRules_IsActive DEFAULT (1),
        Emoji                NVARCHAR(16)   NULL,
        Title                NVARCHAR(200)  NOT NULL,
        EventType            NVARCHAR(64)   NOT NULL,
        Variant              NVARCHAR(64)   NULL,
        RecurrenceType       NVARCHAR(32)   NOT NULL,
        IntervalDays         INT            NULL,
        FirstStartUTC        DATETIME2(0)   NOT NULL,
        DurationDays         INT            NOT NULL,
        RepeatUntilUTC       DATETIME2(0)   NULL,
        MaxOccurrences       INT            NULL,
        AllDay               BIT            NOT NULL CONSTRAINT DF_EventRecurringRules_AllDay DEFAULT (0),
        Importance           NVARCHAR(32)   NULL,
        Description          NVARCHAR(MAX)  NULL,
        LinkURL              NVARCHAR(500)  NULL,
        ChannelID            NVARCHAR(32)   NULL,
        SignupURL            NVARCHAR(500)  NULL,
        Tags                 NVARCHAR(400)  NULL,
        SortOrder            INT            NULL,
        NotesInternal        NVARCHAR(1000) NULL,
        CreatedUTC           DATETIME2(0)   NOT NULL CONSTRAINT DF_EventRecurringRules_CreatedUTC DEFAULT (SYSUTCDATETIME()),
        ModifiedUTC          DATETIME2(0)   NOT NULL CONSTRAINT DF_EventRecurringRules_ModifiedUTC DEFAULT (SYSUTCDATETIME()),
        SourceRowHash        VARBINARY(32)  NULL,
        CONSTRAINT PK_EventRecurringRules PRIMARY KEY CLUSTERED (RuleID)
    );
END
GO

/* =======================
   dbo.EventOneOffEvents
   ======================= */
IF OBJECT_ID(N'dbo.EventOneOffEvents', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.EventOneOffEvents
    (
        EventID              NVARCHAR(128)  NOT NULL,
        IsActive             BIT            NOT NULL CONSTRAINT DF_EventOneOffEvents_IsActive DEFAULT (1),
        Emoji                NVARCHAR(16)   NULL,
        Title                NVARCHAR(200)  NOT NULL,
        EventType            NVARCHAR(64)   NOT NULL,
        Variant              NVARCHAR(64)   NULL,
        StartUTC             DATETIME2(0)   NOT NULL,
        EndUTC               DATETIME2(0)   NOT NULL,
        AllDay               BIT            NOT NULL CONSTRAINT DF_EventOneOffEvents_AllDay DEFAULT (0),
        Importance           NVARCHAR(32)   NULL,
        Description          NVARCHAR(MAX)  NULL,
        LinkURL              NVARCHAR(500)  NULL,
        ChannelID            NVARCHAR(32)   NULL,
        SignupURL            NVARCHAR(500)  NULL,
        Tags                 NVARCHAR(400)  NULL,
        SortOrder            INT            NULL,
        NotesInternal        NVARCHAR(1000) NULL,
        CreatedUTC           DATETIME2(0)   NOT NULL CONSTRAINT DF_EventOneOffEvents_CreatedUTC DEFAULT (SYSUTCDATETIME()),
        ModifiedUTC          DATETIME2(0)   NOT NULL CONSTRAINT DF_EventOneOffEvents_ModifiedUTC DEFAULT (SYSUTCDATETIME()),
        SourceRowHash        VARBINARY(32)  NULL,
        CONSTRAINT PK_EventOneOffEvents PRIMARY KEY CLUSTERED (EventID),
        CONSTRAINT CK_EventOneOffEvents_EndAfterStart CHECK (EndUTC > StartUTC)
    );
END
GO

/* ====================
   dbo.EventOverrides
   ==================== */
IF OBJECT_ID(N'dbo.EventOverrides', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.EventOverrides
    (
        OverrideID                NVARCHAR(128)  NOT NULL,
        IsActive                  BIT            NOT NULL CONSTRAINT DF_EventOverrides_IsActive DEFAULT (1),
        TargetKind                NVARCHAR(16)   NOT NULL,    -- rule | oneoff | instance
        TargetID                  NVARCHAR(128)  NOT NULL,
        TargetOccurrenceStartUTC  DATETIME2(0)   NULL,
        ActionType                NVARCHAR(16)   NOT NULL,    -- cancel | modify
        NewStartUTC               DATETIME2(0)   NULL,
        NewEndUTC                 DATETIME2(0)   NULL,
        NewTitle                  NVARCHAR(200)  NULL,
        NewVariant                NVARCHAR(64)   NULL,
        NewEmoji                  NVARCHAR(16)   NULL,
        NewImportance             NVARCHAR(32)   NULL,
        NewDescription            NVARCHAR(MAX)  NULL,
        NewLinkURL                NVARCHAR(500)  NULL,
        NewChannelID              NVARCHAR(32)   NULL,
        NewSignupURL              NVARCHAR(500)  NULL,
        NewTags                   NVARCHAR(400)  NULL,
        NotesInternal             NVARCHAR(1000) NULL,
        CreatedUTC                DATETIME2(0)   NOT NULL CONSTRAINT DF_EventOverrides_CreatedUTC DEFAULT (SYSUTCDATETIME()),
        ModifiedUTC               DATETIME2(0)   NOT NULL CONSTRAINT DF_EventOverrides_ModifiedUTC DEFAULT (SYSUTCDATETIME()),
        SourceRowHash             VARBINARY(32)  NULL,
        CONSTRAINT PK_EventOverrides PRIMARY KEY CLUSTERED (OverrideID),
        CONSTRAINT CK_EventOverrides_ActionType CHECK (ActionType IN (N'cancel', N'modify')),
        CONSTRAINT CK_EventOverrides_TargetKind CHECK (TargetKind IN (N'rule', N'oneoff', N'instance')),
        CONSTRAINT CK_EventOverrides_NewEndAfterStart CHECK (
            NewEndUTC IS NULL OR NewStartUTC IS NULL OR NewEndUTC > NewStartUTC
        )
    );
END
GO

/* ===================
   dbo.EventInstances
   =================== */
IF OBJECT_ID(N'dbo.EventInstances', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.EventInstances
    (
        InstanceID           BIGINT         NOT NULL IDENTITY(1,1),
        SourceKind           NVARCHAR(16)   NOT NULL,   -- recurring | oneoff
        SourceID             NVARCHAR(128)  NOT NULL,
        StartUTC             DATETIME2(0)   NOT NULL,
        EndUTC               DATETIME2(0)   NOT NULL,
        AllDay               BIT            NOT NULL CONSTRAINT DF_EventInstances_AllDay DEFAULT (0),
        Emoji                NVARCHAR(16)   NULL,
        Title                NVARCHAR(200)  NOT NULL,
        EventType            NVARCHAR(64)   NOT NULL,
        Variant              NVARCHAR(64)   NULL,
        Importance           NVARCHAR(32)   NULL,
        Description          NVARCHAR(MAX)  NULL,
        LinkURL              NVARCHAR(500)  NULL,
        ChannelID            NVARCHAR(32)   NULL,
        SignupURL            NVARCHAR(500)  NULL,
        Tags                 NVARCHAR(400)  NULL,
        SortOrder            INT            NULL,
        IsCancelled          BIT            NOT NULL CONSTRAINT DF_EventInstances_IsCancelled DEFAULT (0),
        GeneratedUTC         DATETIME2(0)   NOT NULL CONSTRAINT DF_EventInstances_GeneratedUTC DEFAULT (SYSUTCDATETIME()),
        EffectiveHash        VARBINARY(32)  NULL,
        CONSTRAINT PK_EventInstances PRIMARY KEY CLUSTERED (InstanceID),
        CONSTRAINT CK_EventInstances_EndAfterStart CHECK (EndUTC > StartUTC),
        CONSTRAINT CK_EventInstances_SourceKind CHECK (SourceKind IN (N'recurring', N'oneoff'))
    );
END
GO

/* ================
   dbo.EventSyncLog
   ================ */
IF OBJECT_ID(N'dbo.EventSyncLog', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.EventSyncLog
    (
        SyncID                 BIGINT         NOT NULL IDENTITY(1,1),
        SyncStartedUTC         DATETIME2(0)   NOT NULL CONSTRAINT DF_EventSyncLog_SyncStartedUTC DEFAULT (SYSUTCDATETIME()),
        SyncCompletedUTC       DATETIME2(0)   NULL,
        SourceName             NVARCHAR(64)   NOT NULL,   -- e.g. google_sheets
        Status                 NVARCHAR(32)   NOT NULL,   -- success/partial_success/failed_*
        RowsReadRecurring      INT            NULL,
        RowsReadOneOff         INT            NULL,
        RowsReadOverrides      INT            NULL,
        RowsUpsertedRecurring  INT            NULL,
        RowsUpsertedOneOff     INT            NULL,
        RowsUpsertedOverrides  INT            NULL,
        InstancesGenerated     INT            NULL,
        ErrorMessage           NVARCHAR(MAX)  NULL,
        CONSTRAINT PK_EventSyncLog PRIMARY KEY CLUSTERED (SyncID)
    );
END
GO

/* =========================
   Required indexes Task 1
   ========================= */
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_EventInstances_StartUTC'
      AND object_id = OBJECT_ID(N'dbo.EventInstances', N'U')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_EventInstances_StartUTC
        ON dbo.EventInstances (StartUTC);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_EventInstances_EventType'
      AND object_id = OBJECT_ID(N'dbo.EventInstances', N'U')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_EventInstances_EventType
        ON dbo.EventInstances (EventType);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_EventInstances_SourceID'
      AND object_id = OBJECT_ID(N'dbo.EventInstances', N'U')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_EventInstances_SourceID
        ON dbo.EventInstances (SourceID);
END
GO