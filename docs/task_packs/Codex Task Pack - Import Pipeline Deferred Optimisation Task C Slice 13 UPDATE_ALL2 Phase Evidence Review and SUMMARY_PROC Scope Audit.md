# Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 13 UPDATE_ALL2 Phase Evidence Review and SUMMARY_PROC Scope Audit

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C Slice 13 - UPDATE_ALL2 Phase Evidence Review and SUMMARY_PROC Scope Audit`
- Date: `2026-07-09`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation batch | SQL observability analysis | performance scope audit`
- One-pass approved: `no`
- Status: `active next-slice task pack, starts with audit/scope and evidence review only`

## 2. Required Reading

Before implementation or analysis, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 12 UPDATE_ALL2 Wrapper Audit Outputs.md`

For SQL-facing validation, use the SQL source of truth:

`C:\K98-bot-SQL-Server`

## 3. Objective

Use the production `ImportAuditPhase` evidence introduced by Task C Slice 12 to quantify recent
`dbo.UPDATE_ALL2` phase timings, identify any missing timing coverage, and scope whether
`dbo.SUMMARY_PROC` or another downstream boundary should become the next SQL-specific
performance/decomposition slice.

This slice is intentionally evidence-first. It should not rewrite, decompose, or optimize
`dbo.UPDATE_ALL2`, `dbo.SUMMARY_PROC`, or `dbo.IMPORT_STAGING_PROC` unless a separate
implementation slice is approved after the audit.

## 4. Background

Task C Slice 12 delivered non-invasive `dbo.UPDATE_ALL2` phase audit outputs:

- SQL emits internal `update_all2_*` phase rows while preserving output tables, `SP_TaskStatus`
  polling, and the final 8-column result set.
- Bot code parses optional phase-shaped result sets and writes durable generic
  `ImportAuditPhase` rows while preserving the existing coarse `fallback_update_all2` phase.
- Production smoke on 2026-07-09 confirmed batch `67` recorded 13 `update_all2_*` subphase rows.
- The first observed sample showed `update_all2_summary_proc` at about 78 seconds, making it the
  visible dominant phase in that run.
- A review-follow-up fix removed `_update_all2_phase_results` from coarse phase/batch details;
  post-restart smoke confirmed zero rows still containing the internal payload.

The remaining deferred optimisation question is no longer "can we observe UPDATE_ALL2?" It is now
"what does the evidence say is worth changing, and what boundary should be changed first?"

## 5. Source Deferred Item Promoted Into This Pack

### Deferred Optimisation
- Area: SQL repo `dbo.UPDATE_ALL2`, SQL repo `dbo.SUMMARY_PROC`, downstream stats/dashboard rebuild procedures, `update_all2_log_manager.py`, `stats_module.py`
- Type: performance
- Description: `dbo.UPDATE_ALL2` now has durable phase-level audit evidence, but there are not yet enough production samples to justify decomposition. The first smoke sample shows `update_all2_summary_proc` dominates visible subphase runtime, with some time still outside the emitted subphase window.
- Suggested Fix: Collect and analyze a short production baseline of recent fallback imports with `update_all2_*` phase rows. Quantify average/max runtimes, phase ordering, missing coarse-to-subphase timing, failure evidence, and whether `dbo.SUMMARY_PROC` is consistently dominant before preparing any SQL decomposition or optimization task.
- Impact: high
- Risk: medium
- Dependencies: Task C Slice 12 deployed and smoke tested; at least several production fallback imports after the Slice 12 rollout; SQL validation in `C:\K98-bot-SQL-Server`.

## 6. Completed Dependencies And Baseline

Confirmed delivered baseline:

- Full fallback imports work with `Credit`.
- Full fallback imports work with `Conduct Score`.
- Interim auto partial fallback imports work from the monitored Discord folder.
- Interim auto partial fallback preserves non-ASCII governor names.
- Partial fallback rows overlay the latest full `KingdomScanData4` snapshot and preserve absent fields.
- Location import remains unchanged for player-visible behavior.
- `shield_time_left` is stored as `ShieldEndsAtUnix` / `ShieldEndsAtUtc` and visible on `v_PlayerProfile`.
- Task C Slice 1 extracted fallback import orchestration into service/DAL wrappers while preserving behavior.
- Task C Slice 2 added generic durable audit objects and fallback-first audit wiring correlated to `dbo.FallbackImportBatchControl`.
- Task C Slice 3 through Slice 10 adopted generic durable audit for the remaining import families.
- Task C Slice 11 normalized generic `ImportAuditPhase` timestamp handling.
- Task C Slice 12 added durable `UPDATE_ALL2` subphase audit evidence and preserved fallback behavior, SQL outputs, counters, `SP_TaskStatus` polling, and the existing `fallback_update_all2` phase.

## 7. Scope

### In Scope

- Query and analyze recent production `ImportAuditBatch` and `ImportAuditPhase` rows for fallback imports after Slice 12 rollout.
- Confirm whether `update_all2_summary_proc` consistently dominates runtime or whether the first smoke sample was an outlier.
- Quantify:
  - total fallback batch duration,
  - coarse `fallback_update_all2` duration,
  - per-`update_all2_*` duration,
  - coarse duration minus summed subphase durations,
  - first subphase delay after coarse SQL phase start,
  - final subphase-to-coarse-completion delay,
  - failures, skips, and timestamp anomalies.
- Validate SQL source definitions for:
  - `dbo.UPDATE_ALL2`,
  - `dbo.SUMMARY_PROC`,
  - summary helper procedures such as `dbo.POWERSUMMARY_PROC`, `dbo.KILLPOINTSSUMMARY_PROC`,
    `dbo.KILLSSUMMARY_PROC`, `dbo.DEADSSUMMARY_PROC`, `dbo.HEALEDSUMMARY_PROC`,
    `dbo.RANGEDSUMMARY_PROC`, `dbo.KT4SUMMARY_PROC`, and `dbo.KT5SUMMARY_PROC`,
  - status objects used by fallback polling.
- Decide whether the next implementation slice should be:
  - more instrumentation,
  - `dbo.SUMMARY_PROC` performance/decomposition audit,
  - broader `UPDATE_ALL2` decomposition design,
  - or no SQL optimization yet.
- Produce a concise evidence summary and recommendation.

### Out Of Scope Unless Separately Approved

- `dbo.UPDATE_ALL2` decomposition or wholesale rewrite.
- `dbo.SUMMARY_PROC` rewrite, decomposition, or performance tuning.
- `dbo.IMPORT_STAGING_PROC` decomposition.
- SQL output table behavior changes.
- Importer route, Discord UX, embed text, queue behavior, attachment/file handling, or import contract changes.
- New generic audit schema objects.
- Historical production audit backfill.
- Residual `stats_module.py` cleanup outside evidence-query support.
- Legacy PreKvK SQL cleanup.
- Weekly cumulative view cleanup.
- Inventory view-orchestration extraction.

## 8. Evidence Queries To Prepare Or Run

Use production read-only SQL to gather recent fallback samples. Adapt `TOP`/date windows as needed.

```sql
WITH RecentFallback AS (
    SELECT TOP (20)
        b.ImportAuditBatchId,
        b.SourceFilename,
        b.StartedAtUtc AS BatchStartedAtUtc,
        b.CompletedAtUtc AS BatchCompletedAtUtc,
        DATEDIFF(MILLISECOND, b.StartedAtUtc, b.CompletedAtUtc) AS BatchDurationMs,
        b.RowsInSource,
        b.RowsWritten
    FROM dbo.ImportAuditBatch AS b
    WHERE b.ImportKind = N'fallback'
      AND b.Status = N'completed'
    ORDER BY b.ImportAuditBatchId DESC
),
Coarse AS (
    SELECT
        p.ImportAuditBatchId,
        p.StartedAtUtc,
        p.CompletedAtUtc,
        p.DurationMs
    FROM dbo.ImportAuditPhase AS p
    WHERE p.PhaseName = N'fallback_update_all2'
),
Subphase AS (
    SELECT
        p.ImportAuditBatchId,
        p.PhaseName,
        p.StartedAtUtc,
        p.CompletedAtUtc,
        p.DurationMs,
        p.RowsOut,
        p.PhaseStatus
    FROM dbo.ImportAuditPhase AS p
    WHERE p.PhaseName LIKE N'update_all2_%'
)
SELECT
    rf.ImportAuditBatchId,
    rf.SourceFilename,
    rf.RowsInSource,
    rf.RowsWritten,
    rf.BatchDurationMs,
    c.DurationMs AS CoarseUpdateAll2DurationMs,
    SUM(COALESCE(s.DurationMs, 0)) AS SumSubphaseDurationMs,
    c.DurationMs - SUM(COALESCE(s.DurationMs, 0)) AS UnexplainedCoarseMs,
    DATEDIFF(MILLISECOND, c.StartedAtUtc, MIN(s.StartedAtUtc)) AS CoarseStartToFirstSubphaseMs,
    DATEDIFF(MILLISECOND, MAX(s.CompletedAtUtc), c.CompletedAtUtc) AS LastSubphaseToCoarseCompleteMs,
    COUNT(s.ImportAuditBatchId) AS SubphaseCount
FROM RecentFallback AS rf
LEFT JOIN Coarse AS c
  ON c.ImportAuditBatchId = rf.ImportAuditBatchId
LEFT JOIN Subphase AS s
  ON s.ImportAuditBatchId = rf.ImportAuditBatchId
GROUP BY
    rf.ImportAuditBatchId,
    rf.SourceFilename,
    rf.RowsInSource,
    rf.RowsWritten,
    rf.BatchDurationMs,
    c.StartedAtUtc,
    c.CompletedAtUtc,
    c.DurationMs
ORDER BY rf.ImportAuditBatchId DESC;
```

```sql
SELECT
    p.PhaseName,
    COUNT(*) AS SampleCount,
    MIN(p.DurationMs) AS MinDurationMs,
    AVG(CAST(p.DurationMs AS float)) AS AvgDurationMs,
    MAX(p.DurationMs) AS MaxDurationMs,
    SUM(CASE WHEN p.PhaseStatus <> N'completed' THEN 1 ELSE 0 END) AS NonCompletedCount
FROM dbo.ImportAuditPhase AS p
JOIN dbo.ImportAuditBatch AS b
  ON b.ImportAuditBatchId = p.ImportAuditBatchId
WHERE b.ImportKind = N'fallback'
  AND p.PhaseName LIKE N'update_all2_%'
  AND b.StartedAtUtc >= DATEADD(DAY, -7, SYSUTCDATETIME())
GROUP BY p.PhaseName
ORDER BY AvgDurationMs DESC;
```

```sql
SELECT
    p.ImportAuditBatchId,
    p.ImportAuditPhaseId,
    p.PhaseName,
    p.StartedAtUtc,
    p.CompletedAtUtc,
    p.DurationMs,
    p.DetailsJson
FROM dbo.ImportAuditPhase AS p
WHERE p.PhaseName LIKE N'update_all2_%'
  AND p.CompletedAtUtc < p.StartedAtUtc
ORDER BY p.ImportAuditBatchId DESC, p.ImportAuditPhaseId;
```

## 9. Remaining Slice Map To Preserve

Do not lose these later slices:

1. **Task C Slice 13 - UPDATE_ALL2 Evidence Review and SUMMARY_PROC Scope Audit**
   - This pack. Analyze production evidence and decide the next implementation boundary.
2. **Later SQL Slice - `dbo.SUMMARY_PROC` Performance/Responsibility Audit or Decomposition**
   - Only if Slice 13 confirms it consistently dominates runtime or failure evidence.
3. **Later SQL Slice - `dbo.UPDATE_ALL2` Decomposition**
   - Prepare only after evidence identifies stable phase boundaries and hotspots.
4. **Later SQL Slice - `dbo.IMPORT_STAGING_PROC` Responsibility Split**
   - Split only after durable audit evidence and compatibility wrappers are stable.
5. **Later Python Slice - Residual `stats_module.py` Import Cleanup**
   - Continue shrinking `stats_module.py` once audit and SQL instrumentation are stable.
6. **Later SQL Cleanup - Legacy PreKvK Phase Object Retirement**
   - Keep separate after live dependency review.
7. **Later SQL Cleanup - `dbo.vAllianceActivity_WeeklyCumulative` Review**
   - Confirm downstream/manual usage before correcting or retiring the view.
8. **Later Python Slice - Inventory View Orchestration Extraction**
   - Keep separate from fallback SQL evidence work.

## 10. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Confirm evidence/audit boundary before proposing any SQL implementation. |
| `k98-sql-validation` | use | Required because this slice validates SQL procedures and timing evidence. |
| `k98-test-selection` | use | Required if any query/helper docs, scripts, or code are changed. |
| `k98-deferred-optimisation-capture` | use | Required to keep deferred items and follow-up slices aligned. |
| `k98-pr-review` | use if code/docs PR is prepared | Confirm scope, docs, and validation. |
| `k98-promotion-check` | use only if promoting runtime changes | Likely not needed for audit-only evidence collection. |
| `codex-security:security-diff-scan` | usually skip for audit-only docs/query work | Run if code, SQL execution, permissions, or data access behavior changes. |

## 11. Required First Response

Use this shape and stop for approval before code or SQL changes:

```markdown
**Scope Summary**
<why Slice 13 follows Slice 12 and what evidence it will collect>

**Current Evidence State**
<what the 2026-07-09 smoke shows, including SUMMARY_PROC timing and any missing timing gap>

**SQL Position**
<which SQL objects/procedures must be validated and whether a SQL repo change appears necessary>

**Implementation Boundary**
<audit/query-only vs helper script vs SQL view/procedure vs later decomposition proposal>

**Remaining Slice Map**
<SUMMARY_PROC audit/decomposition, UPDATE_ALL2 decomposition, IMPORT_STAGING_PROC split, stats_module cleanup, PreKvK cleanup, weekly view cleanup, inventory orchestration follow-up>

**Validation Plan**
<SQL evidence queries, focused checks, docs/tests if changed, smoke expectations, Codex Security decision>

**Open Questions / Approval Needed**
<specific decisions for Chris>
```

## 12. Validation Plan

For audit-only work:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

If docs only:

- Run `validate_deferred_items.py`.
- Run `select_tests.py`.
- Justify skipping runtime pytest, smoke imports, command registration, and Codex Security.

If a helper script or SQL repo object is added:

```powershell
.\.venv\Scripts\python.exe -m pytest -q <focused tests>
cd C:\K98-bot-SQL-Server
.\deploy\Validate-SqlRepo.ps1
```

Smoke expectations:

- Use read-only SQL evidence queries over recent fallback batches.
- Confirm no timestamp regressions.
- Confirm `fallback_update_all2` and `update_all2_*` rows coexist.
- Confirm terminal batch/coarse phase details do not contain `_update_all2_phase_results`.
- Produce an evidence summary that identifies the next approved implementation candidate or recommends waiting for more samples.

## 13. Acceptance Criteria

- [ ] Recent fallback phase evidence is gathered from production or supplied operator extracts.
- [ ] Evidence includes at least several Slice 12-era batches where possible.
- [ ] `update_all2_summary_proc` dominance is confirmed, rejected, or marked inconclusive.
- [ ] Coarse-to-subphase timing gaps are quantified.
- [ ] SQL source definitions for `dbo.SUMMARY_PROC` and relevant helper procedures are reviewed before recommending implementation.
- [ ] No procedure decomposition or runtime SQL change is made without a later approved slice.
- [ ] Remaining deferred optimisation slices remain documented and ordered.
- [ ] Any new follow-up work is captured using the Deferred Optimisation Framework.
