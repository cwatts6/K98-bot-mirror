SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

/*
Inventory Image Import - Phase 1F schema support

Canonical SQL Server schema changes should be promoted through the SQL Server
repository. This app-side script documents the Python DAL contract for
governor-level inventory profile settings used by VIP-aware capacity reports.
*/

IF OBJECT_ID(N'dbo.GovernorInventoryProfile', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.GovernorInventoryProfile
    (
        GovernorID BIGINT NOT NULL
            CONSTRAINT PK_GovernorInventoryProfile PRIMARY KEY CLUSTERED,
        VipLevelCode NVARCHAR(32) NULL,
        VipLevelLabel NVARCHAR(64) NULL,
        UpdatedByDiscordUserID BIGINT NULL,
        CreatedAtUtc DATETIME2(3) NOT NULL
            CONSTRAINT DF_GovernorInventoryProfile_CreatedAtUtc DEFAULT SYSUTCDATETIME(),
        UpdatedAtUtc DATETIME2(3) NOT NULL
            CONSTRAINT DF_GovernorInventoryProfile_UpdatedAtUtc DEFAULT SYSUTCDATETIME(),
        CONSTRAINT CK_GovernorInventoryProfile_VipLevelCode
            CHECK (
                VipLevelCode IS NULL
                OR VipLevelCode IN (
                    N'VIP_14_OR_LESS',
                    N'VIP_15',
                    N'VIP_16',
                    N'VIP_17',
                    N'VIP_18',
                    N'VIP_19',
                    N'SVIP'
                )
            )
    );
END
GO
