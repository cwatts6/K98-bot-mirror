SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

IF COL_LENGTH('dbo.MGE_Events', 'AwardRemindersMessageId') IS NULL
BEGIN
    ALTER TABLE dbo.MGE_Events
        ADD AwardRemindersMessageId BIGINT NULL;
END
GO
IF COL_LENGTH('dbo.MGE_Events', 'AwardRemindersChannelId') IS NULL
BEGIN
    ALTER TABLE dbo.MGE_Events
        ADD AwardRemindersChannelId BIGINT NULL;
END
GO
