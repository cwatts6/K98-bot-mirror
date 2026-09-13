# Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 13 UPDATE_ALL2 Phase Evidence Review and SUMMARY_PROC Scope Audit

> **Completed — 2026-09-01:** The mandatory post-August gate was satisfied against the
> authoritative SQL repository and a read-only Production sample. The July object map and batch
> `67` timing sample remain historical only. The refreshed repository map is:
>
> - `dbo.IMPORT_STAGING_PROC` is the public no-caller-transaction entry point; it calls
>   `dbo.CLAIM_KS4_IMPORT_FILE` and delegates staging/receipt work to
>   `dbo.IMPORT_STAGING_PROC_CORE`;
> - Python invokes `dbo.UPDATE_ALL2` separately through `update_all2_log_manager.py`; the procedure
>   emits `update_all2_*` rows and calls `dbo.SUMMARY_PROC` as one downstream phase;
> - `dbo.SUMMARY_PROC` calls the current Power/Kills/Deads/Healed/Ranged summary helpers;
> - the refresh must account for the immutable handoff, claim ACL hardening, serialized delta
>   preprocessing, and stats-publication provenance migrations delivered after the July sample.
>
> The refreshed nine-batch sample confirms `update_all2_summary_proc` as the consistent visible
> hotspot. It does not yet justify SQL tuning or decomposition; the next boundary is a longer,
> read-only `SUMMARY_PROC` responsibility/performance audit.

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C Slice 13 - UPDATE_ALL2 Phase Evidence Review and SUMMARY_PROC Scope Audit`
- Date: `2026-07-09`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation batch | SQL observability analysis | performance scope audit`
- One-pass approved: `no`
- Status: `complete — evidence gate satisfied; no SQL implementation approved`
- Object map last verified: `2026-09-01 against C:\K98-bot-SQL-Server`

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
`dbo.UPDATE_ALL2`, `dbo.SUMMARY_PROC`, or `dbo.IMPORT_STAGING_PROC_CORE` unless a separate
implementation slice is approved after the audit.

## 4. Background

Task C Slice 12 delivered non-invasive `dbo.UPDATE_ALL2` phase audit outputs:

- SQL emits internal `update_all2_*` phase rows while preserving output tables, `SP_TaskStatus`
  polling, and the final 8-column result set.
- Bot code parses optional phase-shaped result sets and writes durable generic
  `ImportAuditPhase` rows while preserving the existing coarse `fallback_update_all2` phase.
- Historical Production smoke on 2026-07-09 confirmed batch `67` recorded 13 `update_all2_*`
  subphase rows. It must not be used as the current baseline.
- That historical sample showed `update_all2_summary_proc` at about 78 seconds, making it the
  visible dominant phase in that run only; current dominance is unverified.
- The July review-follow-up intended to remove `_update_all2_phase_results` from coarse phase and
  batch details. The refreshed Production sample found the internal payload absent from batch-level
  details but still present in all nine coarse `fallback_update_all2` rows. Slice 13 therefore
  includes a bounded bot-only hygiene fix that removes the key before the coarse audit write while
  retaining the local rows for durable subphase projection.

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
- `dbo.IMPORT_STAGING_PROC_CORE` decomposition.
- SQL output table behavior changes.
- Importer route, Discord UX, embed text, queue behavior, attachment/file handling, or import contract changes.
- New generic audit schema objects.
- Historical production audit backfill.
- Residual `stats_module.py` cleanup outside evidence-query support.
- Legacy PreKvK SQL cleanup.
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
4. **Later SQL Slice - `dbo.IMPORT_STAGING_PROC_CORE` Responsibility Split**
   - Split only after durable audit evidence and compatibility wrappers are stable.
5. **Later Python Slice - Residual `stats_module.py` Import Cleanup**
   - Continue shrinking `stats_module.py` once audit and SQL instrumentation are stable.
6. **Later SQL Cleanup - Legacy PreKvK Phase Object Retirement**
   - Keep separate after live dependency review.
7. **Later Python Slice - Inventory View Orchestration Extraction**
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
<what the historical 2026-07-09 smoke showed, the post-August sample now shows, and any missing timing gap>

**SQL Position**
<which SQL objects/procedures must be validated and whether a SQL repo change appears necessary>

**Implementation Boundary**
<audit/query-only vs helper script vs SQL view/procedure vs later decomposition proposal>

**Remaining Slice Map**
<SUMMARY_PROC audit/decomposition, UPDATE_ALL2 decomposition, IMPORT_STAGING_PROC_CORE split, stats_module cleanup, PreKvK cleanup, inventory orchestration follow-up>

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

- [x] Recent fallback phase evidence is gathered from production or supplied operator extracts.
- [x] Evidence includes at least several Slice 12-era batches where possible.
- [x] `update_all2_summary_proc` dominance is confirmed, rejected, or marked inconclusive.
- [x] Coarse-to-subphase timing gaps are quantified.
- [x] SQL source definitions for `dbo.SUMMARY_PROC` and relevant helper procedures are reviewed before recommending implementation.
- [x] No procedure decomposition or runtime SQL change is made without a later approved slice.
- [x] Remaining deferred optimisation slices remain documented and ordered.
- [x] Any new follow-up work is captured using the Deferred Optimisation Framework.

## 14. Completion Evidence — 2026-09-01

### Production Sample

The authorised read-only Production review covered nine completed fallback batches, IDs `306`
through `345`, from `2026-08-30T08:12:12.571Z` through `2026-09-01T06:29:56.390Z`.

- Every batch recorded the expected 13 `update_all2_*` rows: 117 subphase rows in total.
- All sampled batches and subphases completed; no failure or skip was present.
- No null/reversed timestamp, negative duration, duration mismatch greater than 5 ms, duplicate
  subphase name, missing coarse row, or missing `update_all2_summary_proc` row was found.
- `RowsInSource` and `RowsWritten` both ranged from 405 to 422.

| Measure | Minimum | Average | Maximum |
|---|---:|---:|---:|
| Fallback batch duration | 103.4 s | 121.6 s | 139.2 s |
| Coarse `fallback_update_all2` | 100.0 s | 118.0 s | 136.5 s |
| Sum of emitted subphases | 64.9 s | 73.6 s | 82.3 s |
| Coarse minus emitted subphases | 35.9 s | 45.2 s | 62.2 s |
| Coarse start to first subphase | 11.4 s | 12.2 s | 12.9 s |
| Last subphase to coarse completion | 24.1 s | 32.5 s | 49.2 s |
| `update_all2_summary_proc` | 62.1 s | 69.0 s | 75.8 s |

`update_all2_summary_proc` was the longest emitted subphase in all nine batches and represented
91.5% to 95.6% of measured subphase time (93.8% on average). On average it represented about 58%
of the coarse SQL phase, so the uninstrumented coarse-to-subphase gap remains material and must not
be attributed to `SUMMARY_PROC` without further evidence.

### SQL Repository Position

The current definitions in `C:\K98-bot-SQL-Server` confirm:

- `dbo.IMPORT_STAGING_PROC` is the public no-caller-transaction claim wrapper and delegates to
  `dbo.IMPORT_STAGING_PROC_CORE`;
- Python invokes `dbo.UPDATE_ALL2` separately through `update_all2_log_manager.py`;
- `dbo.UPDATE_ALL2` emits 13 `update_all2_*` phase rows, calls `dbo.SUMMARY_PROC`, preserves its
  final result shape, and preserves `SP_TaskStatus` polling behavior;
- `dbo.SUMMARY_PROC` sequentially calls the current Deads, Power, combined Kills, T4, T5,
  KillPoints, Healed, and Ranged summary helpers over shared procedure state.

The review accounted for the post-July immutable-handoff, claim-ACL, delta-serialization, and
stats-provenance migrations. SQL repository validation passed. No SQL repository change is
necessary or justified in Slice 13.

### Decision And Handoff

- Close Slice 13 after the bounded bot-only coarse-detail hygiene fix and focused validation.
- Collect naturally occurring fallback evidence for 10–14 days and at least 30 completed batches,
  whichever is later. Target the next formal audit for `2026-09-15`.
- Advance early if any batch has a missing/failed/skipped subphase, a phase count other than 13, a
  timestamp anomaly, `update_all2_summary_proc` above 90 seconds, or an unexplained coarse gap above
  75 seconds.
- Run the next slice as a read-only `SUMMARY_PROC` responsibility/performance audit. If helper-level
  attribution is unavailable from existing Query Store or DMV evidence, prepare a separate
  non-invasive instrumentation proposal rather than tuning or decomposing the procedure.
