SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

/*
Inventory Image Import - Phase 2 Materials multi-image status support

Adds the 'awaiting_more_material' status to InventoryImportBatch so that
additional Materials screenshots are only merged when the user explicitly
clicks "Add Another Image". Requires dropping and recreating the CHECK
constraint and the unique active-governor index.

Canonical SQL Server schema changes should be promoted through the SQL Server
repository. This app-side script documents the Python DAL contract.
*/

IF EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE name = N'CK_InventoryImportBatch_Status'
      AND parent_object_id = OBJECT_ID(N'dbo.InventoryImportBatch')
)
BEGIN
    ALTER TABLE dbo.InventoryImportBatch
    DROP CONSTRAINT CK_InventoryImportBatch_Status;
END
GO

ALTER TABLE dbo.InventoryImportBatch
ADD CONSTRAINT CK_InventoryImportBatch_Status
    CHECK (Status IN (
        N'awaiting_upload',
        N'analysed',
        N'awaiting_more_material',
        N'approved',
        N'rejected',
        N'cancelled',
        N'failed'
    ));
GO

IF EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_InventoryImportBatch_ActiveGovernor'
      AND object_id = OBJECT_ID(N'dbo.InventoryImportBatch')
)
BEGIN
    DROP INDEX UX_InventoryImportBatch_ActiveGovernor
    ON dbo.InventoryImportBatch;
END
GO

CREATE UNIQUE NONCLUSTERED INDEX UX_InventoryImportBatch_ActiveGovernor
ON dbo.InventoryImportBatch (GovernorID)
WHERE Status IN (N'awaiting_upload', N'analysed', N'awaiting_more_material');
GO
