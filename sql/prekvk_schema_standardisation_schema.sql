SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON

IF COL_LENGTH(N'dbo.PreKvk_Scores', N'KingdomID') IS NULL
ALTER TABLE [dbo].[PreKvk_Scores] ADD [KingdomID] [int] NULL

IF COL_LENGTH(N'dbo.PreKvk_Scores', N'SourceRank') IS NULL
ALTER TABLE [dbo].[PreKvk_Scores] ADD [SourceRank] [int] NULL

IF COL_LENGTH(N'dbo.PreKvk_Scores', N'Stage1Points') IS NULL
ALTER TABLE [dbo].[PreKvk_Scores] ADD [Stage1Points] [int] NULL

IF COL_LENGTH(N'dbo.PreKvk_Scores', N'Stage2Points') IS NULL
ALTER TABLE [dbo].[PreKvk_Scores] ADD [Stage2Points] [int] NULL

IF COL_LENGTH(N'dbo.PreKvk_Scores', N'Stage3Points') IS NULL
ALTER TABLE [dbo].[PreKvk_Scores] ADD [Stage3Points] [int] NULL

IF COL_LENGTH(N'dbo.PreKvk_Scores', N'TotalPoints') IS NULL
ALTER TABLE [dbo].[PreKvk_Scores] ADD [TotalPoints] [int] NULL

IF OBJECT_ID(N'dbo.PreKvk_Scores_Ranked', N'U') IS NOT NULL
   AND COL_LENGTH(N'dbo.PreKvk_Scores_Ranked', N'Stage1Points') IS NULL
ALTER TABLE [dbo].[PreKvk_Scores_Ranked] ADD [Stage1Points] [bigint] NULL

IF OBJECT_ID(N'dbo.PreKvk_Scores_Ranked', N'U') IS NOT NULL
   AND COL_LENGTH(N'dbo.PreKvk_Scores_Ranked', N'Stage1Rank') IS NULL
ALTER TABLE [dbo].[PreKvk_Scores_Ranked] ADD [Stage1Rank] [bigint] NULL

IF OBJECT_ID(N'dbo.PreKvk_Scores_Ranked', N'U') IS NOT NULL
   AND COL_LENGTH(N'dbo.PreKvk_Scores_Ranked', N'Stage2Points') IS NULL
ALTER TABLE [dbo].[PreKvk_Scores_Ranked] ADD [Stage2Points] [bigint] NULL

IF OBJECT_ID(N'dbo.PreKvk_Scores_Ranked', N'U') IS NOT NULL
   AND COL_LENGTH(N'dbo.PreKvk_Scores_Ranked', N'Stage2Rank') IS NULL
ALTER TABLE [dbo].[PreKvk_Scores_Ranked] ADD [Stage2Rank] [bigint] NULL

IF OBJECT_ID(N'dbo.PreKvk_Scores_Ranked', N'U') IS NOT NULL
   AND COL_LENGTH(N'dbo.PreKvk_Scores_Ranked', N'Stage3Points') IS NULL
ALTER TABLE [dbo].[PreKvk_Scores_Ranked] ADD [Stage3Points] [bigint] NULL

IF OBJECT_ID(N'dbo.PreKvk_Scores_Ranked', N'U') IS NOT NULL
   AND COL_LENGTH(N'dbo.PreKvk_Scores_Ranked', N'Stage3Rank') IS NULL
ALTER TABLE [dbo].[PreKvk_Scores_Ranked] ADD [Stage3Rank] [bigint] NULL

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[dbo].[PreKvk_Scores]') AND name = N'IX_PreKvk_Scores_KVK_Scan_Total')
CREATE NONCLUSTERED INDEX [IX_PreKvk_Scores_KVK_Scan_Total] ON [dbo].[PreKvk_Scores]
(
    [KVK_NO] ASC,
    [ScanID] ASC,
    [TotalPoints] DESC,
    [GovernorID] ASC
)
INCLUDE([GovernorName],[Points],[Stage1Points],[Stage2Points],[Stage3Points]) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[dbo].[PreKvk_Scores]') AND name = N'IX_PreKvk_Scores_KVK_Gov')
CREATE NONCLUSTERED INDEX [IX_PreKvk_Scores_KVK_Gov] ON [dbo].[PreKvk_Scores]
(
    [KVK_NO] ASC,
    [GovernorID] ASC
)
INCLUDE([ScanID],[GovernorName],[Points],[TotalPoints],[Stage1Points],[Stage2Points],[Stage3Points]) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
