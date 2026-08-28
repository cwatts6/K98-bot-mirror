SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[PreKvk_ImportHistory]') AND type in (N'U'))
BEGIN
CREATE TABLE [dbo].[PreKvk_ImportHistory](
    [HistoryID] [bigint] IDENTITY(1,1) NOT NULL,
    [KVK_NO] [int] NULL,
    [Filename] [nvarchar](255) COLLATE Latin1_General_CI_AS NOT NULL,
    [FileHashSha256] [char](64) COLLATE Latin1_General_CI_AS NULL,
    [HashPrefix] [char](8) COLLATE Latin1_General_CI_AS NULL,
    [ImportStatus] [varchar](20) COLLATE Latin1_General_CI_AS NOT NULL,
    [Phase] [nvarchar](64) COLLATE Latin1_General_CI_AS NULL,
    [RowCount] [int] NULL,
    [ScanID] [int] NULL,
    [ErrorType] [nvarchar](64) COLLATE Latin1_General_CI_AS NULL,
    [ErrorText] [nvarchar](1000) COLLATE Latin1_General_CI_AS NULL,
    [UploaderDiscordID] [bigint] NULL,
    [ChannelID] [bigint] NULL,
    [MessageID] [bigint] NULL,
    [CreatedUTC] [datetime2](7) NOT NULL,
 CONSTRAINT [PK_PreKvk_ImportHistory] PRIMARY KEY CLUSTERED
(
    [HistoryID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
END

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[DF_PreKvk_ImportHistory_CreatedUTC]') AND type = 'D')
BEGIN
ALTER TABLE [dbo].[PreKvk_ImportHistory] ADD CONSTRAINT [DF_PreKvk_ImportHistory_CreatedUTC] DEFAULT (sysutcdatetime()) FOR [CreatedUTC]
END

IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE object_id = OBJECT_ID(N'[dbo].[CK_PreKvk_ImportHistory_Status]') AND parent_object_id = OBJECT_ID(N'[dbo].[PreKvk_ImportHistory]'))
ALTER TABLE [dbo].[PreKvk_ImportHistory] WITH CHECK ADD CONSTRAINT [CK_PreKvk_ImportHistory_Status] CHECK (([ImportStatus]='accepted' OR [ImportStatus]='rejected' OR [ImportStatus]='duplicate' OR [ImportStatus]='failed'))

IF EXISTS (SELECT * FROM sys.check_constraints WHERE object_id = OBJECT_ID(N'[dbo].[CK_PreKvk_ImportHistory_Status]') AND parent_object_id = OBJECT_ID(N'[dbo].[PreKvk_ImportHistory]'))
ALTER TABLE [dbo].[PreKvk_ImportHistory] CHECK CONSTRAINT [CK_PreKvk_ImportHistory_Status]

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[dbo].[PreKvk_ImportHistory]') AND name = N'IX_PreKvk_ImportHistory_KVK_Status_Created')
CREATE NONCLUSTERED INDEX [IX_PreKvk_ImportHistory_KVK_Status_Created] ON [dbo].[PreKvk_ImportHistory]
(
    [KVK_NO] ASC,
    [ImportStatus] ASC,
    [CreatedUTC] DESC
)
INCLUDE([Filename],[HashPrefix],[RowCount],[ScanID],[ErrorType],[UploaderDiscordID],[ChannelID],[MessageID]) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[dbo].[PreKvk_ImportHistory]') AND name = N'IX_PreKvk_ImportHistory_Created')
CREATE NONCLUSTERED INDEX [IX_PreKvk_ImportHistory_Created] ON [dbo].[PreKvk_ImportHistory]
(
    [CreatedUTC] DESC,
    [HistoryID] DESC
)
INCLUDE([KVK_NO],[Filename],[HashPrefix],[ImportStatus],[RowCount],[ScanID],[ErrorType]) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
