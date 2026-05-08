SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sp_Build_Prekvk_And_Honor_Rankings]') AND type in (N'P', N'PC'))
BEGIN
EXEC dbo.sp_executesql @statement = N'CREATE PROCEDURE [dbo].[sp_Build_Prekvk_And_Honor_Rankings] AS'
END
GO
ALTER PROCEDURE [dbo].[sp_Build_Prekvk_And_Honor_Rankings]
WITH EXECUTE AS CALLER
AS
BEGIN
    SET NOCOUNT ON;

    -------------------------------------------------------
    -- 1) Build PreKvk_Scores_Ranked: per KVK, per Governor:
    --    MaxPreKvkPoints (bigint), PreKvk_Rank (bigint),
    --    direct stage points/ranks, KVK_NO, GovernorID,
    --    GovernorName, ScanID, ScanTimestampUTC
    -------------------------------------------------------
    DROP TABLE IF EXISTS dbo.PreKvk_Scores_Ranked;

    ;WITH MaxPerGov AS (
        SELECT KVK_NO, GovernorID, MAX(Points) AS MaxPoints
        FROM dbo.PreKvk_Scores
        GROUP BY KVK_NO, GovernorID
    ),
    BestScans AS (
        -- all rows where Points = MaxPoints (may be multiple scan entries)
        SELECT p.KVK_NO,
               p.GovernorID,
               p.GovernorName,
               p.Points,
               p.Stage1Points,
               p.Stage2Points,
               p.Stage3Points,
               p.ScanID
        FROM dbo.PreKvk_Scores p
        JOIN MaxPerGov m
          ON p.KVK_NO = m.KVK_NO
         AND p.GovernorID = m.GovernorID
         AND p.Points = m.MaxPoints
    ),
    Picked AS (
        -- pick a single ScanID when duplicates; capture GovName and ScanID
        SELECT
            b.KVK_NO,
            b.GovernorID,
            MAX(b.GovernorName) AS GovernorName,
            CAST(MAX(b.Points) AS bigint) AS MaxPreKvkPoints,
            CAST(MAX(b.Stage1Points) AS bigint) AS Stage1Points,
            CAST(MAX(b.Stage2Points) AS bigint) AS Stage2Points,
            CAST(MAX(b.Stage3Points) AS bigint) AS Stage3Points,
            MIN(b.ScanID) AS ScanID
        FROM BestScans b
        GROUP BY b.KVK_NO, b.GovernorID
    ),
    WithTS AS (
        -- attach ScanTimestampUTC from PreKvk_Scan
        SELECT p.KVK_NO, p.GovernorID, p.GovernorName, p.MaxPreKvkPoints,
               p.Stage1Points, p.Stage2Points, p.Stage3Points,
               p.ScanID, s.ScanTimestampUTC
        FROM Picked p
        LEFT JOIN dbo.PreKvk_Scan s
          ON s.KVK_NO = p.KVK_NO AND s.ScanID = p.ScanID
    ),
    Ranked AS (
        SELECT w.*,
               RANK() OVER (PARTITION BY w.KVK_NO ORDER BY w.MaxPreKvkPoints DESC, w.GovernorID ASC) AS PreRank,
               RANK() OVER (PARTITION BY w.KVK_NO ORDER BY w.Stage1Points DESC, w.GovernorID ASC) AS Stage1RankRaw,
               RANK() OVER (PARTITION BY w.KVK_NO ORDER BY w.Stage2Points DESC, w.GovernorID ASC) AS Stage2RankRaw,
               RANK() OVER (PARTITION BY w.KVK_NO ORDER BY w.Stage3Points DESC, w.GovernorID ASC) AS Stage3RankRaw
        FROM WithTS w
    )
    SELECT
        KVK_NO,
        GovernorID,
        GovernorName,
        MaxPreKvkPoints,
        CAST(PreRank AS bigint) AS PreKvk_Rank,
        Stage1Points,
        CASE WHEN Stage1Points IS NULL THEN NULL ELSE CAST(Stage1RankRaw AS bigint) END AS Stage1Rank,
        Stage2Points,
        CASE WHEN Stage2Points IS NULL THEN NULL ELSE CAST(Stage2RankRaw AS bigint) END AS Stage2Rank,
        Stage3Points,
        CASE WHEN Stage3Points IS NULL THEN NULL ELSE CAST(Stage3RankRaw AS bigint) END AS Stage3Rank,
        ScanID,
        ScanTimestampUTC
    INTO dbo.PreKvk_Scores_Ranked
    FROM Ranked;

    -- optional index for faster joins (GovernorID lookup & KVK lookup)
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.PreKvk_Scores_Ranked') AND name = N'IX_PreKvkScoresRanked_KvK_Gov')
    BEGIN
        CREATE NONCLUSTERED INDEX IX_PreKvkScoresRanked_KvK_Gov ON dbo.PreKvk_Scores_Ranked (KVK_NO, GovernorID) INCLUDE (MaxPreKvkPoints, PreKvk_Rank, Stage1Points, Stage1Rank, Stage2Points, Stage2Rank, Stage3Points, Stage3Rank, ScanID);
    END

    -------------------------------------------------------
    -- 2) Build KVK_Honor_Ranked: per KVK, per Governor:
    --    MaxHonorPoints (bigint), Honor_Rank (bigint),
    --    KVK_NO, GovernorID, GovernorName, ScanID, ScanTimestampUTC
    -------------------------------------------------------
    DROP TABLE IF EXISTS dbo.KVK_Honor_Ranked;

    ;WITH MaxHonorPerGov AS (
        SELECT KVK_NO, GovernorID, MAX(HonorPoints) AS MaxHonor
        FROM dbo.KVK_Honor_AllPlayers_Raw
        GROUP BY KVK_NO, GovernorID
    ),
    BestHonorScans AS (
        SELECT h.KVK_NO, h.GovernorID, h.GovernorName, h.HonorPoints, h.ScanID
        FROM dbo.KVK_Honor_AllPlayers_Raw h
        JOIN MaxHonorPerGov m
          ON h.KVK_NO = m.KVK_NO
         AND h.GovernorID = m.GovernorID
         AND h.HonorPoints = m.MaxHonor
    ),
    PickedHonor AS (
        SELECT
            b.KVK_NO,
            b.GovernorID,
            MAX(b.GovernorName) AS GovernorName,
            CAST(MAX(b.HonorPoints) AS bigint) AS MaxHonorPoints,
            MIN(b.ScanID) AS ScanID
        FROM BestHonorScans b
        GROUP BY b.KVK_NO, b.GovernorID
    ),
    WithHonorTS AS (
        SELECT p.KVK_NO, p.GovernorID, p.GovernorName, p.MaxHonorPoints,
               p.ScanID, s.ScanTimestampUTC
        FROM PickedHonor p
        LEFT JOIN dbo.KVK_Honor_Scan s
          ON s.KVK_NO = p.KVK_NO AND s.ScanID = p.ScanID
    )
    SELECT
        KVK_NO,
        GovernorID,
        GovernorName,
        MaxHonorPoints,
        CAST(HonorRank AS bigint) AS Honor_Rank,
        ScanID,
        ScanTimestampUTC
    INTO dbo.KVK_Honor_Ranked
    FROM (
        SELECT w.*,
               RANK() OVER (PARTITION BY w.KVK_NO ORDER BY w.MaxHonorPoints DESC, w.GovernorID ASC) AS HonorRank
        FROM WithHonorTS w
    ) x;

    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.KVK_Honor_Ranked') AND name = N'IX_KVKHonorRanked_KvK_Gov')
    BEGIN
        CREATE NONCLUSTERED INDEX IX_KVKHonorRanked_KvK_Gov ON dbo.KVK_Honor_Ranked (KVK_NO, GovernorID) INCLUDE (MaxHonorPoints, Honor_Rank, ScanID);
    END

    RETURN 0;
END
