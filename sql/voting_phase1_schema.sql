/*
Purpose: Add SQL-backed Discord vote post tables for Phase 1.
Deployment: Apply before deploying bot code that imports voting.dal.
Rollback: Manual drop in reverse dependency order if no production vote data must be retained.
*/

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;

IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[VotePosts]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[VotePosts](
        [VotePostID] [bigint] IDENTITY(1,1) NOT NULL,
        [GuildID] [bigint] NOT NULL,
        [ChannelID] [bigint] NOT NULL,
        [MessageID] [bigint] NULL,
        [CreatedByDiscordUserID] [bigint] NOT NULL,
        [Title] [nvarchar](180) COLLATE Latin1_General_CI_AS NOT NULL,
        [Description] [nvarchar](2000) COLLATE Latin1_General_CI_AS NULL,
        [Status] [varchar](20) COLLATE Latin1_General_CI_AS NOT NULL,
        [AllowVoteChange] [bit] NOT NULL,
        [LaunchMentionEveryone] [bit] NOT NULL,
        [ReminderMentionEveryone] [bit] NOT NULL,
        [CloseMentionEveryone] [bit] NOT NULL,
        [OpensAtUtc] [datetime2](0) NULL,
        [ClosesAtUtc] [datetime2](0) NOT NULL,
        [ClosedAtUtc] [datetime2](0) NULL,
        [ClosedByDiscordUserID] [bigint] NULL,
        [ClosedReason] [nvarchar](200) COLLATE Latin1_General_CI_AS NULL,
        [BackgroundAssetKey] [nvarchar](260) COLLATE Latin1_General_CI_AS NULL,
        [CreatedAtUtc] [datetime2](0) NOT NULL,
        [UpdatedAtUtc] [datetime2](0) NOT NULL,
        CONSTRAINT [PK_VotePosts] PRIMARY KEY CLUSTERED ([VotePostID] ASC)
    );
END;

IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[VotePostOptions]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[VotePostOptions](
        [OptionID] [bigint] IDENTITY(1,1) NOT NULL,
        [VotePostID] [bigint] NOT NULL,
        [OptionKey] [varchar](32) COLLATE Latin1_General_CI_AS NOT NULL,
        [Label] [nvarchar](80) COLLATE Latin1_General_CI_AS NOT NULL,
        [SortOrder] [int] NOT NULL,
        [ButtonStyle] [varchar](16) COLLATE Latin1_General_CI_AS NULL,
        [CreatedAtUtc] [datetime2](0) NOT NULL,
        CONSTRAINT [PK_VotePostOptions] PRIMARY KEY CLUSTERED ([OptionID] ASC)
    );
END;

IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[VotePostVotes]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[VotePostVotes](
        [VotePostID] [bigint] NOT NULL,
        [DiscordUserID] [bigint] NOT NULL,
        [OptionID] [bigint] NOT NULL,
        [GovernorID] [bigint] NULL,
        [OriginalOptionID] [bigint] NULL,
        [CreatedAtUtc] [datetime2](0) NOT NULL,
        [UpdatedAtUtc] [datetime2](0) NOT NULL,
        CONSTRAINT [PK_VotePostVotes] PRIMARY KEY CLUSTERED ([VotePostID] ASC, [DiscordUserID] ASC)
    );
END;

IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[VotePostReminders]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[VotePostReminders](
        [ReminderID] [bigint] IDENTITY(1,1) NOT NULL,
        [VotePostID] [bigint] NOT NULL,
        [OffsetMinutesBeforeClose] [int] NOT NULL,
        [DueAtUtc] [datetime2](0) NOT NULL,
        [ClaimedAtUtc] [datetime2](0) NULL,
        [SentAtUtc] [datetime2](0) NULL,
        [MessageID] [bigint] NULL,
        [CreatedAtUtc] [datetime2](0) NOT NULL,
        CONSTRAINT [PK_VotePostReminders] PRIMARY KEY CLUSTERED ([ReminderID] ASC)
    );
END;

IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[VotePostAudit]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[VotePostAudit](
        [AuditID] [bigint] IDENTITY(1,1) NOT NULL,
        [VotePostID] [bigint] NOT NULL,
        [ActorDiscordUserID] [bigint] NULL,
        [ActionType] [varchar](40) COLLATE Latin1_General_CI_AS NOT NULL,
        [OptionID] [bigint] NULL,
        [PreviousOptionID] [bigint] NULL,
        [DetailsJson] [nvarchar](max) COLLATE Latin1_General_CI_AS NULL,
        [CreatedAtUtc] [datetime2](0) NOT NULL,
        CONSTRAINT [PK_VotePostAudit] PRIMARY KEY CLUSTERED ([AuditID] ASC)
    );
END;

IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE name = N'DF_VotePosts_Status')
    ALTER TABLE [dbo].[VotePosts] ADD CONSTRAINT [DF_VotePosts_Status] DEFAULT ('Open') FOR [Status];
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE name = N'DF_VotePosts_AllowVoteChange')
    ALTER TABLE [dbo].[VotePosts] ADD CONSTRAINT [DF_VotePosts_AllowVoteChange] DEFAULT ((1)) FOR [AllowVoteChange];
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE name = N'DF_VotePosts_LaunchMentionEveryone')
    ALTER TABLE [dbo].[VotePosts] ADD CONSTRAINT [DF_VotePosts_LaunchMentionEveryone] DEFAULT ((0)) FOR [LaunchMentionEveryone];
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE name = N'DF_VotePosts_ReminderMentionEveryone')
    ALTER TABLE [dbo].[VotePosts] ADD CONSTRAINT [DF_VotePosts_ReminderMentionEveryone] DEFAULT ((0)) FOR [ReminderMentionEveryone];
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE name = N'DF_VotePosts_CloseMentionEveryone')
    ALTER TABLE [dbo].[VotePosts] ADD CONSTRAINT [DF_VotePosts_CloseMentionEveryone] DEFAULT ((0)) FOR [CloseMentionEveryone];
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE name = N'DF_VotePosts_CreatedAtUtc')
    ALTER TABLE [dbo].[VotePosts] ADD CONSTRAINT [DF_VotePosts_CreatedAtUtc] DEFAULT (SYSUTCDATETIME()) FOR [CreatedAtUtc];
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE name = N'DF_VotePosts_UpdatedAtUtc')
    ALTER TABLE [dbo].[VotePosts] ADD CONSTRAINT [DF_VotePosts_UpdatedAtUtc] DEFAULT (SYSUTCDATETIME()) FOR [UpdatedAtUtc];
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE name = N'DF_VotePostOptions_CreatedAtUtc')
    ALTER TABLE [dbo].[VotePostOptions] ADD CONSTRAINT [DF_VotePostOptions_CreatedAtUtc] DEFAULT (SYSUTCDATETIME()) FOR [CreatedAtUtc];
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE name = N'DF_VotePostVotes_CreatedAtUtc')
    ALTER TABLE [dbo].[VotePostVotes] ADD CONSTRAINT [DF_VotePostVotes_CreatedAtUtc] DEFAULT (SYSUTCDATETIME()) FOR [CreatedAtUtc];
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE name = N'DF_VotePostVotes_UpdatedAtUtc')
    ALTER TABLE [dbo].[VotePostVotes] ADD CONSTRAINT [DF_VotePostVotes_UpdatedAtUtc] DEFAULT (SYSUTCDATETIME()) FOR [UpdatedAtUtc];
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE name = N'DF_VotePostReminders_CreatedAtUtc')
    ALTER TABLE [dbo].[VotePostReminders] ADD CONSTRAINT [DF_VotePostReminders_CreatedAtUtc] DEFAULT (SYSUTCDATETIME()) FOR [CreatedAtUtc];
IF NOT EXISTS (SELECT 1 FROM sys.default_constraints WHERE name = N'DF_VotePostAudit_CreatedAtUtc')
    ALTER TABLE [dbo].[VotePostAudit] ADD CONSTRAINT [DF_VotePostAudit_CreatedAtUtc] DEFAULT (SYSUTCDATETIME()) FOR [CreatedAtUtc];

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_VotePostOptions_VotePosts')
    ALTER TABLE [dbo].[VotePostOptions] WITH CHECK ADD CONSTRAINT [FK_VotePostOptions_VotePosts] FOREIGN KEY([VotePostID]) REFERENCES [dbo].[VotePosts] ([VotePostID]);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_VotePostVotes_VotePosts')
    ALTER TABLE [dbo].[VotePostVotes] WITH CHECK ADD CONSTRAINT [FK_VotePostVotes_VotePosts] FOREIGN KEY([VotePostID]) REFERENCES [dbo].[VotePosts] ([VotePostID]);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_VotePostVotes_Options')
    ALTER TABLE [dbo].[VotePostVotes] WITH CHECK ADD CONSTRAINT [FK_VotePostVotes_Options] FOREIGN KEY([OptionID]) REFERENCES [dbo].[VotePostOptions] ([OptionID]);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_VotePostVotes_OriginalOptions')
    ALTER TABLE [dbo].[VotePostVotes] WITH CHECK ADD CONSTRAINT [FK_VotePostVotes_OriginalOptions] FOREIGN KEY([OriginalOptionID]) REFERENCES [dbo].[VotePostOptions] ([OptionID]);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_VotePostReminders_VotePosts')
    ALTER TABLE [dbo].[VotePostReminders] WITH CHECK ADD CONSTRAINT [FK_VotePostReminders_VotePosts] FOREIGN KEY([VotePostID]) REFERENCES [dbo].[VotePosts] ([VotePostID]);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_VotePostAudit_VotePosts')
    ALTER TABLE [dbo].[VotePostAudit] WITH CHECK ADD CONSTRAINT [FK_VotePostAudit_VotePosts] FOREIGN KEY([VotePostID]) REFERENCES [dbo].[VotePosts] ([VotePostID]);

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_VotePosts_Status')
    ALTER TABLE [dbo].[VotePosts] WITH CHECK ADD CONSTRAINT [CK_VotePosts_Status] CHECK ([Status] IN ('Open', 'Closed', 'Cancelled'));
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_VotePosts_Closed')
    ALTER TABLE [dbo].[VotePosts] WITH CHECK ADD CONSTRAINT [CK_VotePosts_Closed] CHECK (([Status] <> 'Closed') OR ([ClosedAtUtc] IS NOT NULL));
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_VotePostReminders_Offset')
    ALTER TABLE [dbo].[VotePostReminders] WITH CHECK ADD CONSTRAINT [CK_VotePostReminders_Offset] CHECK ([OffsetMinutesBeforeClose] > 0);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'[dbo].[VotePosts]') AND name = N'IX_VotePosts_OpenDue')
    CREATE NONCLUSTERED INDEX [IX_VotePosts_OpenDue] ON [dbo].[VotePosts]([Status], [ClosesAtUtc]) INCLUDE([ChannelID], [MessageID], [CloseMentionEveryone]);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'[dbo].[VotePostOptions]') AND name = N'UX_VotePostOptions_Key')
    CREATE UNIQUE NONCLUSTERED INDEX [UX_VotePostOptions_Key] ON [dbo].[VotePostOptions]([VotePostID], [OptionKey]);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'[dbo].[VotePostOptions]') AND name = N'UX_VotePostOptions_Sort')
    CREATE UNIQUE NONCLUSTERED INDEX [UX_VotePostOptions_Sort] ON [dbo].[VotePostOptions]([VotePostID], [SortOrder]);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'[dbo].[VotePostReminders]') AND name = N'IX_VotePostReminders_Due')
    CREATE NONCLUSTERED INDEX [IX_VotePostReminders_Due] ON [dbo].[VotePostReminders]([SentAtUtc], [DueAtUtc]) INCLUDE([VotePostID], [ClaimedAtUtc]);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'[dbo].[VotePostAudit]') AND name = N'IX_VotePostAudit_VotePost')
    CREATE NONCLUSTERED INDEX [IX_VotePostAudit_VotePost] ON [dbo].[VotePostAudit]([VotePostID], [CreatedAtUtc]);
