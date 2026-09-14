SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

/*
Inventory Image Import - Phase 2 Materials schema support

Canonical SQL Server schema changes should be promoted through the SQL Server
repository. This app-side script documents the Python DAL contract for approved
raw equipment material inventory rows.
*/

IF OBJECT_ID(N'dbo.GovernorMaterialInventory', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.GovernorMaterialInventory
    (
        MaterialRecordID BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_GovernorMaterialInventory PRIMARY KEY CLUSTERED,
        ImportBatchID BIGINT NOT NULL,
        GovernorID BIGINT NOT NULL,
        ScanUtc DATETIME2(3) NOT NULL,
        MaterialKind NVARCHAR(32) NOT NULL,
        Rarity NVARCHAR(32) NOT NULL,
        Quantity BIGINT NOT NULL,
        LegendaryEquivalent DECIMAL(18,4) NOT NULL,
        SourceImageIndex INT NULL,
        CreatedAtUtc DATETIME2(3) NOT NULL
            CONSTRAINT DF_GovernorMaterialInventory_CreatedAtUtc DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_GovernorMaterialInventory_ImportBatch
            FOREIGN KEY (ImportBatchID)
            REFERENCES dbo.InventoryImportBatch (ImportBatchID),
        CONSTRAINT CK_GovernorMaterialInventory_MaterialKind
            CHECK (MaterialKind IN (N'choice_chests', N'animal_bone', N'leather', N'ebony', N'iron_ore')),
        CONSTRAINT CK_GovernorMaterialInventory_Rarity
            CHECK (Rarity IN (N'normal', N'advanced', N'elite', N'epic', N'legendary')),
        CONSTRAINT CK_GovernorMaterialInventory_Quantity
            CHECK (Quantity >= 0),
        CONSTRAINT CK_GovernorMaterialInventory_LegendaryEquivalent
            CHECK (LegendaryEquivalent >= 0),
        CONSTRAINT CK_GovernorMaterialInventory_SourceImageIndex
            CHECK (SourceImageIndex IS NULL OR SourceImageIndex >= 1)
    );
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_GovernorMaterialInventory_Governor_ScanUtc'
      AND object_id = OBJECT_ID(N'dbo.GovernorMaterialInventory')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_GovernorMaterialInventory_Governor_ScanUtc
    ON dbo.GovernorMaterialInventory (GovernorID, ScanUtc DESC)
    INCLUDE (ImportBatchID, MaterialKind, Rarity, Quantity, LegendaryEquivalent);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_GovernorMaterialInventory_Governor_Kind_Rarity_ScanUtc'
      AND object_id = OBJECT_ID(N'dbo.GovernorMaterialInventory')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_GovernorMaterialInventory_Governor_Kind_Rarity_ScanUtc
    ON dbo.GovernorMaterialInventory (GovernorID, MaterialKind, Rarity, ScanUtc DESC)
    INCLUDE (ImportBatchID, Quantity, LegendaryEquivalent);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_GovernorMaterialInventory_Batch_Kind_Rarity'
      AND object_id = OBJECT_ID(N'dbo.GovernorMaterialInventory')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_GovernorMaterialInventory_Batch_Kind_Rarity
    ON dbo.GovernorMaterialInventory (ImportBatchID, MaterialKind, Rarity);
END
GO
