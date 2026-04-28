SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

IF OBJECT_ID(N'dbo.DiscordServerActivityEvents', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DiscordServerActivityEvents
    (
        ActivityEventId BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_DiscordServerActivityEvents PRIMARY KEY,
        OccurredAtUtc DATETIME2(0) NOT NULL,
        GuildId BIGINT NOT NULL,
        ChannelId BIGINT NULL,
        UserId BIGINT NOT NULL,
        EventType NVARCHAR(32) NOT NULL,
        MetadataJson NVARCHAR(MAX) NULL,
        CreatedAtUtc DATETIME2(0) NOT NULL
            CONSTRAINT DF_DiscordServerActivityEvents_CreatedAtUtc
            DEFAULT SYSUTCDATETIME()
    );

    CREATE INDEX IX_DiscordServerActivityEvents_Window
        ON dbo.DiscordServerActivityEvents (OccurredAtUtc, GuildId, UserId, EventType)
        INCLUDE (ChannelId);
END;
GO
