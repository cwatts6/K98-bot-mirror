SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

/*
Inventory Image Import - Phase 1B schema support

Canonical SQL Server schema changes should be promoted through the SQL Server
repository. This app-side script documents the Python DAL contract for persistent
/myinventory visibility preferences.
*/

IF OBJECT_ID(N'dbo.InventoryReportPreference', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.InventoryReportPreference
    (
        DiscordUserID BIGINT NOT NULL
            CONSTRAINT PK_InventoryReportPreference PRIMARY KEY CLUSTERED,
        Visibility NVARCHAR(32) NOT NULL,
        CreatedAtUtc DATETIME2(3) NOT NULL
            CONSTRAINT DF_InventoryReportPreference_CreatedAtUtc DEFAULT SYSUTCDATETIME(),
        UpdatedAtUtc DATETIME2(3) NOT NULL
            CONSTRAINT DF_InventoryReportPreference_UpdatedAtUtc DEFAULT SYSUTCDATETIME(),
        CONSTRAINT CK_InventoryReportPreference_Visibility
            CHECK (Visibility IN (N'only_me', N'public'))
    );
END
GO
