SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.objects
    WHERE object_id = OBJECT_ID(N'[dbo].[GovernorSessionLocks]')
      AND type = N'U'
)
BEGIN
    CREATE TABLE [dbo].[GovernorSessionLocks](
        [LockScope] [nvarchar](50) NOT NULL,
        [GovernorID] [nvarchar](50) NOT NULL,
        [HolderDiscordUserID] [bigint] NOT NULL,
        [ExpiresAtUTC] [datetime2](0) NOT NULL,
        [CreatedAtUTC] [datetime2](0) NOT NULL,
        [UpdatedAtUTC] [datetime2](0) NOT NULL,
        CONSTRAINT [PK_GovernorSessionLocks] PRIMARY KEY CLUSTERED
        (
            [LockScope] ASC,
            [GovernorID] ASC
        )
    );
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'[dbo].[GovernorSessionLocks]')
      AND name = N'IX_GovernorSessionLocks_ExpiresAtUTC'
)
BEGIN
    CREATE NONCLUSTERED INDEX [IX_GovernorSessionLocks_ExpiresAtUTC]
    ON [dbo].[GovernorSessionLocks] ([ExpiresAtUTC] ASC)
    INCLUDE ([LockScope], [GovernorID], [HolderDiscordUserID]);
END
GO
