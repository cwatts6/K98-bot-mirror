SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

/*
Inventory Image Import - Phase 1A schema support

Canonical SQL Server schema changes should be promoted through the SQL Server
repository. This script is included with the bot PR so the app-side DAL contract
is reviewable alongside the Python implementation.
*/

IF OBJECT_ID(N'dbo.InventoryImportBatch', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.InventoryImportBatch
    (
        ImportBatchID BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_InventoryImportBatch PRIMARY KEY CLUSTERED,
        GovernorID BIGINT NOT NULL,
        DiscordUserID BIGINT NOT NULL,
        ImportType NVARCHAR(32) NULL,
        FlowType NVARCHAR(32) NOT NULL,
        SourceMessageID BIGINT NULL,
        SourceChannelID BIGINT NULL,
        ImageAttachmentURL NVARCHAR(2048) NULL,
        AdminDebugChannelID BIGINT NULL,
        AdminDebugMessageID BIGINT NULL,
        Status NVARCHAR(32) NOT NULL,
        CreatedAtUtc DATETIME2(3) NOT NULL
            CONSTRAINT DF_InventoryImportBatch_CreatedAtUtc DEFAULT SYSUTCDATETIME(),
        ApprovedAtUtc DATETIME2(3) NULL,
        RejectedAtUtc DATETIME2(3) NULL,
        RetryCount INT NOT NULL
            CONSTRAINT DF_InventoryImportBatch_RetryCount DEFAULT (0),
        VisionModel NVARCHAR(128) NULL,
        VisionPromptVersion NVARCHAR(128) NULL,
        FallbackUsed BIT NOT NULL
            CONSTRAINT DF_InventoryImportBatch_FallbackUsed DEFAULT (0),
        ConfidenceScore DECIMAL(5,4) NULL,
        DetectedJson NVARCHAR(MAX) NULL,
        CorrectedJson NVARCHAR(MAX) NULL,
        FinalJson NVARCHAR(MAX) NULL,
        WarningJson NVARCHAR(MAX) NULL,
        ErrorJson NVARCHAR(MAX) NULL,
        IsAdminImport BIT NOT NULL
            CONSTRAINT DF_InventoryImportBatch_IsAdminImport DEFAULT (0),
        OriginalUploadDeletedAtUtc DATETIME2(3) NULL,
        ExpiresAtUtc DATETIME2(3) NULL,
        ApprovedDateUtc AS CONVERT(date, ApprovedAtUtc) PERSISTED,
        CONSTRAINT CK_InventoryImportBatch_ImportType
            CHECK (ImportType IS NULL OR ImportType IN (N'resources', N'speedups', N'materials', N'unknown')),
        CONSTRAINT CK_InventoryImportBatch_FlowType
            CHECK (FlowType IN (N'command', N'upload_first')),
        CONSTRAINT CK_InventoryImportBatch_Status
            CHECK (Status IN (N'awaiting_upload', N'analysed', N'approved', N'rejected', N'cancelled', N'failed')),
        CONSTRAINT CK_InventoryImportBatch_ConfidenceScore
            CHECK (ConfidenceScore IS NULL OR (ConfidenceScore >= 0 AND ConfidenceScore <= 1)),
        CONSTRAINT CK_InventoryImportBatch_RetryCount
            CHECK (RetryCount >= 0)
    );
END
GO

IF OBJECT_ID(N'dbo.GovernorResourceInventory', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.GovernorResourceInventory
    (
        ResourceRecordID BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_GovernorResourceInventory PRIMARY KEY CLUSTERED,
        ImportBatchID BIGINT NOT NULL,
        GovernorID BIGINT NOT NULL,
        ScanUtc DATETIME2(3) NOT NULL,
        ResourceType NVARCHAR(32) NOT NULL,
        FromItemsValue BIGINT NOT NULL,
        TotalResourcesValue BIGINT NOT NULL,
        CONSTRAINT FK_GovernorResourceInventory_ImportBatch
            FOREIGN KEY (ImportBatchID)
            REFERENCES dbo.InventoryImportBatch (ImportBatchID),
        CONSTRAINT CK_GovernorResourceInventory_ResourceType
            CHECK (ResourceType IN (N'food', N'wood', N'stone', N'gold')),
        CONSTRAINT CK_GovernorResourceInventory_FromItemsValue
            CHECK (FromItemsValue >= 0),
        CONSTRAINT CK_GovernorResourceInventory_TotalResourcesValue
            CHECK (TotalResourcesValue >= 0)
    );
END
GO

IF OBJECT_ID(N'dbo.GovernorSpeedupInventory', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.GovernorSpeedupInventory
    (
        SpeedupRecordID BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_GovernorSpeedupInventory PRIMARY KEY CLUSTERED,
        ImportBatchID BIGINT NOT NULL,
        GovernorID BIGINT NOT NULL,
        ScanUtc DATETIME2(3) NOT NULL,
        SpeedupType NVARCHAR(32) NOT NULL,
        TotalMinutes BIGINT NOT NULL,
        TotalHours DECIMAL(18,4) NOT NULL,
        TotalDaysDecimal DECIMAL(18,4) NOT NULL,
        CONSTRAINT FK_GovernorSpeedupInventory_ImportBatch
            FOREIGN KEY (ImportBatchID)
            REFERENCES dbo.InventoryImportBatch (ImportBatchID),
        CONSTRAINT CK_GovernorSpeedupInventory_SpeedupType
            CHECK (SpeedupType IN (N'building', N'research', N'training', N'healing', N'universal')),
        CONSTRAINT CK_GovernorSpeedupInventory_TotalMinutes
            CHECK (TotalMinutes >= 0),
        CONSTRAINT CK_GovernorSpeedupInventory_TotalHours
            CHECK (TotalHours >= 0),
        CONSTRAINT CK_GovernorSpeedupInventory_TotalDaysDecimal
            CHECK (TotalDaysDecimal >= 0)
    );
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_InventoryImportBatch_ActiveGovernor'
      AND object_id = OBJECT_ID(N'dbo.InventoryImportBatch')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_InventoryImportBatch_ActiveGovernor
    ON dbo.InventoryImportBatch (GovernorID)
    WHERE Status IN (N'awaiting_upload', N'analysed');
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_InventoryImportBatch_ApprovedDaily'
      AND object_id = OBJECT_ID(N'dbo.InventoryImportBatch')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_InventoryImportBatch_ApprovedDaily
    ON dbo.InventoryImportBatch (GovernorID, ImportType, ApprovedDateUtc)
    WHERE Status = N'approved'
      AND ImportType IS NOT NULL
      AND ApprovedAtUtc IS NOT NULL
      AND IsAdminImport = 0;
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_InventoryImportBatch_Governor_Status_Expires'
      AND object_id = OBJECT_ID(N'dbo.InventoryImportBatch')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_InventoryImportBatch_Governor_Status_Expires
    ON dbo.InventoryImportBatch (GovernorID, Status, ExpiresAtUtc)
    INCLUDE (DiscordUserID, ImportType, CreatedAtUtc);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_InventoryImportBatch_DiscordUser_Status'
      AND object_id = OBJECT_ID(N'dbo.InventoryImportBatch')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_InventoryImportBatch_DiscordUser_Status
    ON dbo.InventoryImportBatch (DiscordUserID, Status, FlowType, ExpiresAtUtc)
    INCLUDE (GovernorID, ImportType, CreatedAtUtc);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_InventoryImportBatch_Audit'
      AND object_id = OBJECT_ID(N'dbo.InventoryImportBatch')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_InventoryImportBatch_Audit
    ON dbo.InventoryImportBatch (Status, ImportType, CreatedAtUtc)
    INCLUDE (GovernorID, DiscordUserID, AdminDebugChannelID, AdminDebugMessageID, ConfidenceScore);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_GovernorResourceInventory_Governor_ScanUtc'
      AND object_id = OBJECT_ID(N'dbo.GovernorResourceInventory')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_GovernorResourceInventory_Governor_ScanUtc
    ON dbo.GovernorResourceInventory (GovernorID, ScanUtc DESC)
    INCLUDE (ResourceType, FromItemsValue, TotalResourcesValue, ImportBatchID);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_GovernorResourceInventory_Batch_Type'
      AND object_id = OBJECT_ID(N'dbo.GovernorResourceInventory')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_GovernorResourceInventory_Batch_Type
    ON dbo.GovernorResourceInventory (ImportBatchID, ResourceType);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_GovernorSpeedupInventory_Governor_ScanUtc'
      AND object_id = OBJECT_ID(N'dbo.GovernorSpeedupInventory')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_GovernorSpeedupInventory_Governor_ScanUtc
    ON dbo.GovernorSpeedupInventory (GovernorID, ScanUtc DESC)
    INCLUDE (SpeedupType, TotalMinutes, TotalHours, TotalDaysDecimal, ImportBatchID);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_GovernorSpeedupInventory_Batch_Type'
      AND object_id = OBJECT_ID(N'dbo.GovernorSpeedupInventory')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_GovernorSpeedupInventory_Batch_Type
    ON dbo.GovernorSpeedupInventory (ImportBatchID, SpeedupType);
END
GO
