> **Archived 9 November 2026:** The brought-forward summary audit and rewrite are delivered in Phase 1. This is historical evidence, not an instruction to collect another workload. [Current P02 scope](../Startup%20Import%20Export%20Reliability%20-%20P02%20Remaining%20Work%20Handover%20-%202026-11-09.md) retains whole-flow acceptance and remaining maintenance obligations.

# Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 14 SUMMARY_PROC Responsibility and Performance Audit

> **Approved rewrite implemented and locally qualified — 7 November 2026.** The approved SQL rewrite covers all eight metrics and the alternate healed entry point; 30 focused local SQL tests passed. Canonical SQL-repo `docs/archive/p021-summary-implementation.md` records source, local-only install/rollback, output/state/permission parity and remaining qualification. Existing limits remain unchanged. Production activation, external cache-consumer clearance, signing/source pins and full rehearsal qualification remain separate. Older implementation-pending blocks below are historical.


> **Complete retained evidence and rewrite proposal — 7 November 2026.** All 192 plans are complete and the 184 summary cost records are unchanged. SQL-repo `docs/archive/p021-summary-optimisation-proposal.md` now defines the preferred temporary endpoint calculation, all eight metrics plus the alternate healed path, preserved report/state outputs, explicit intermediate-cache consumer/rollback conditions, alternatives and qualification. No further collector or diagnostic import is needed for this decision. Local rewrite implementation awaits approval; production activation, cache-table deletion, incident recovery and budget changes remain outside this proposal. Earlier evidence gaps below are historical.


> **Statement attribution available — 7 November 2026.** Retained ON Query Store evidence attributes 118.841 of the 127.589 summary seconds to 32 history/window cache rebuilds. All 56 cache write pairs are captured, with parent/child definition hashes unchanged. Complete the bounded saved-plan and incoming-consumer reads before selecting the SQL rewrite; do not execute the previously proposed extra diagnostic import merely to collect costs already available. SQL-repo `docs/archive/p021-summary-cost-evidence.md` records measured costs, caps, limitations and the next read-only collector. No summary implementation or budget change is approved by this update.


> **Approved early audit — 7 November 2026.** The P02.1 isolated snapshot-enabled
> rehearsal's SUMMARY_PROC stage took 127.589 seconds and observed version store
> reached 1,843,712 KiB against the 524,288 KiB budget. The operator approved
> bringing this existing audit forward, plus a separate deterministic historical-name
> fix. The earlier 30-production-batch sample has not been manufactured or claimed.
> Current source/dependency audit and bounded measurement proposal are in SQL-repo
> `docs/archive/p021-summary-audit.md`; name implementation/qualification is in
> `docs/archive/p021-deterministic-names.md` on `codex/p021-deterministic-names`.
> The eight-child/56-cache write shape is confirmed, but per-statement costs remain
> unattributed. Existing cached/Query Store evidence is the next read-only step;
> a validated private collector is prepared. No summary rewrite, new full VM replay,
> production change or higher budget is approved by this checkpoint. Historical
> signing/source-pin integration remains an explicit release gate for the name fix.
> The historical scope and observations below remain as dated evidence.


> **Evidence-collection gate — 2026-09-01:** Do not tune, decompose, or repeatedly execute
> `dbo.SUMMARY_PROC` in Production. Collect naturally occurring fallback evidence for 10–14 days
> and at least 30 completed batches, whichever is later. The target formal audit date is
> `2026-09-15`.

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C Slice 14 - SUMMARY_PROC Responsibility and Performance Audit`
- Date: `2026-09-01`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation batch | read-only SQL responsibility audit | performance evidence`
- One-pass approved: `no`
- Status: `evidence collection active — formal audit gated by sample size and date window`

## 2. Objective

Determine which current `dbo.SUMMARY_PROC` responsibilities and helper procedures account for its
observed runtime, and whether the evidence supports a later instrumentation, tuning, or
decomposition task. Preserve all fallback import behavior and make no runtime SQL or bot change in
this slice.

## 3. Entry Evidence From Slice 13

The post-August Production refresh covered nine completed fallback batches, IDs `306` through
`345`, between 2026-08-30 and 2026-09-01:

- all nine recorded 13 completed `update_all2_*` rows;
- `update_all2_summary_proc` was the longest emitted subphase in 9/9 batches;
- its minimum/average/maximum duration was 62.1/69.0/75.8 seconds;
- it represented 91.5%–95.6% of measured subphase time, averaging 93.8%;
- the coarse `fallback_update_all2` phase still exceeded the emitted subphase sum by
  35.9–62.2 seconds, averaging 45.2 seconds.

This establishes a stable audit target, not permission to optimize it. Batch `67` and its roughly
78-second July observation remain historical evidence only.

## 4. Mandatory Collection Gate

Run the formal analysis only after both conditions are satisfied:

1. at least 10 days of naturally occurring post-Slice-13 fallback evidence has accrued; and
2. at least 30 completed fallback batches with the expected phase rows are available.

Prefer 14 days when operationally convenient. At the observed rate, this should yield roughly
45–65 batches. Re-audit sooner if any of these alert conditions occurs:

- a failed, skipped, missing, or duplicate `update_all2_*` phase;
- a sampled batch has a subphase count other than 13;
- a null, reversed, negative, or materially inconsistent timestamp/duration appears;
- `update_all2_summary_proc` exceeds 90 seconds;
- coarse duration minus emitted subphases exceeds 75 seconds;
- the source row scale materially exceeds the current 405–422 range; or
- `update_all2_summary_proc` is no longer the dominant emitted phase.

## 5. Required Reading And Source Of Truth

Read the repository-required engineering references and:

- the archived Slice 13 evidence pack;
- `docs/reference/deferred_optimisations.md`;
- the current definitions under `C:\K98-bot-SQL-Server\sql_schema` for `dbo.UPDATE_ALL2`,
  `dbo.SUMMARY_PROC`, its helper procedures, and any objects needed to interpret helper state;
- post-July immutable-handoff, claim-ACL, delta-serialization, and stats-provenance migrations when
  validating the current map.

The SQL repository is authoritative. Do not infer stored-procedure behavior from Python callers.

## 6. In Scope

- Re-run read-only `ImportAuditBatch`/`ImportAuditPhase` trend and integrity queries over the gated
  sample.
- Quantify batch, coarse phase, subphase, leading-gap, trailing-gap, and unexplained-gap
  distributions, including row-volume correlation and outliers.
- Revalidate `dbo.SUMMARY_PROC` call order, helper responsibilities, shared temporary tables/state,
  and output dependencies.
- Inspect existing read-only Query Store and relevant DMV evidence, if available and sufficiently
  attributable, for the current summary procedure and helper objects.
- Record current database compatibility/configuration facts only where they materially affect the
  interpretation of existing evidence.
- Decide whether the next boundary is:
  - no change and continued observation;
  - a separate non-invasive instrumentation proposal;
  - a focused helper-level tuning task;
  - a responsibility/decomposition design task.

## 7. Out Of Scope Unless Separately Approved

- Any `dbo.SUMMARY_PROC`, helper, `dbo.UPDATE_ALL2`, or `dbo.IMPORT_STAGING_PROC_CORE` change.
- New or changed table, view, index, stored procedure, audit object, Query Store configuration, SQL
  Agent job, Extended Events session, or trace.
- Repeated direct Production execution of stateful procedures for benchmarking.
- Production actual-plan, `STATISTICS IO`, or `STATISTICS TIME` experiments that execute stateful
  work. Use a controlled representative restore/clone or a separately approved safe window.
- Bot, DAL, parser, importer, route, UX, file-handling, polling, output, or counter changes.
- Historical audit backfill.
- Residual `stats_module.py`, PreKvK, or inventory orchestration cleanup.

## 8. Evidence Method

1. Use authorised RDP/SSMS access and read-only queries against Production.
2. Establish sample integrity before calculating performance distributions.
3. Compare the new sample with Slice 13 without mixing the historical July batch into the current
   baseline.
4. Use existing Query Store/runtime metadata only when the statement/object attribution is clear.
5. Treat DMV or Query Store absence, aggregation, eviction, or attribution ambiguity as an explicit
   limitation rather than guessing which helper dominates.
6. If helper attribution remains inconclusive, hand off a separately approved instrumentation pack;
   do not infer a decomposition boundary from the outer procedure duration alone.

## 9. Required Outputs

- Sample window, batch IDs/count, row-volume range, and completeness/integrity results.
- Minimum/average/median/p95/maximum for batch, coarse, every subphase, and timing gaps.
- Per-batch dominance and outlier table for `update_all2_summary_proc`.
- Current `SUMMARY_PROC` responsibility/call map with shared-state constraints.
- Existing Query Store/DMV evidence and its attribution limitations.
- One evidence-backed implementation boundary, or a clear recommendation to wait.
- Updated deferred backlog and a separate implementation task pack only if approved.

## 10. Remaining Slice Map

1. **Task C Slice 14 — this read-only `SUMMARY_PROC` audit.**
2. **Possible instrumentation slice** — only if existing read-only evidence cannot attribute helper
   cost; separately approved because server-state changes may be required.
3. **Possible `SUMMARY_PROC` tuning/responsibility slice** — only for a proven helper or boundary.
4. **Later `UPDATE_ALL2` decomposition** — after stable phase boundaries and hotspots are proven.
5. **Later `IMPORT_STAGING_PROC_CORE` responsibility split.**
6. **Later residual `stats_module.py` orchestration cleanup.**
7. **Later legacy PreKvK SQL cleanup.**
8. **Later inventory view-orchestration extraction.**

## 11. Validation And Security Decision

For this audit-only slice:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
cd C:\K98-bot-SQL-Server
.\deploy\Validate-SqlRepo.ps1
```

- Validate SQL evidence query joins, sample counts, duplicates, duration arithmetic, and timestamp
  invariants before interpreting performance.
- No runtime smoke execution of `SUMMARY_PROC` is expected in Production.
- Codex Security may be documented as skipped for read-only analysis/docs with no executable or SQL
  change. Any later working-tree code or SQL diff requires a fresh K98 routing decision and normally
  a Changes-only review of the affected repository.

## 12. Acceptance Criteria

- [ ] At least 10 days and 30 completed fallback batches are included, or an alert condition
  justifies an earlier audit.
- [ ] Current SQL definitions and post-July migrations are revalidated.
- [ ] Phase/timestamp integrity and timing distributions are reported.
- [ ] `SUMMARY_PROC` responsibilities and shared-state constraints are documented.
- [ ] Helper attribution is evidence-backed or explicitly marked inconclusive.
- [ ] No stateful Production benchmark or runtime mutation occurs without separate approval.
- [ ] A specific next boundary is recommended, or continued observation is justified.
- [ ] No SQL implementation begins without a new approved task pack.
