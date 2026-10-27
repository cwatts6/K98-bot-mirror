# Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 14 SUMMARY_PROC Responsibility and Performance Audit

Use this starter after the Slice 14 collection gate is satisfied, or earlier only when an alert
condition in the task pack is met. One-pass execution is not approved.

## Copy/Paste Starter

```markdown
# Files mentioned by the user:

## Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 14 SUMMARY_PROC Responsibility and Performance Audit.md: C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 14 SUMMARY_PROC Responsibility and Performance Audit.md

## My request for Codex:
Begin Task C Slice 14 - Import Pipeline Deferred Optimisation: SUMMARY_PROC Responsibility and
Performance Audit.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 14 SUMMARY_PROC Responsibility and Performance Audit.md

Completed dependency and baseline:
- Task C Slice 13 is complete and archived at:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 13 UPDATE_ALL2 Phase Evidence Review and SUMMARY_PROC Scope Audit.md
- The refreshed post-August Production sample covered nine completed fallback batches, IDs 306–345.
- Every sampled batch recorded 13 completed update_all2_* phase rows with no missing, failed,
  skipped, duplicated, reversed, negative, or materially inconsistent timing row.
- update_all2_summary_proc dominated 9/9 batches at 62.1–75.8 seconds and averaged 93.8% of
  measured subphase time.
- The coarse fallback_update_all2 phase still exceeded emitted subphases by 35.9–62.2 seconds,
  averaging 45.2 seconds. Do not attribute this gap to SUMMARY_PROC without evidence.
- Batch 67 and the approximately 78-second July observation are historical evidence only.
- The Slice 13 bot hygiene fix removes _update_all2_phase_results from coarse durable details while
  retaining individual subphase projection. Confirm post-deployment naturally occurring evidence;
  do not create a stateful Production import merely to test it.

Mandatory collection gate:
- Use naturally occurring fallback evidence covering at least 10 days and at least 30 completed
  batches, whichever is later.
- The target formal audit date is 2026-09-15.
- Starting earlier is permitted only if the task-pack alert conditions are met: a failed, skipped,
  missing, or duplicate subphase; phase count other than 13; timestamp/duration anomaly;
  update_all2_summary_proc above 90 seconds; unexplained coarse gap above 75 seconds; materially
  higher row scale; or SUMMARY_PROC no longer dominating.
- State explicitly whether the gate is satisfied before continuing.

Start with audit/scope and read-only evidence review only.

Required current-map validation:
- Validate all SQL-facing facts against C:\K98-bot-SQL-Server.
- dbo.IMPORT_STAGING_PROC is the public claim wrapper and delegates to
  dbo.IMPORT_STAGING_PROC_CORE.
- Python invokes dbo.UPDATE_ALL2 separately through update_all2_log_manager.py.
- dbo.UPDATE_ALL2 emits 13 update_all2_* rows and calls dbo.SUMMARY_PROC downstream.
- dbo.SUMMARY_PROC currently calls the Deads, Power, combined Kills, T4, T5, KillPoints, Healed,
  and Ranged helpers over shared procedure state.
- Account for the immutable-handoff, claim-ACL, delta-serialization, and stats-provenance
  migrations delivered after the July sample.

Evidence method:
- Use authorised RDP/SSMS access and read-only Production queries.
- Re-run ImportAuditBatch/ImportAuditPhase integrity and timing queries over the gated sample.
- Report minimum, average, median, p95, and maximum for batch, coarse phase, every subphase, leading
  gap, trailing gap, and unexplained gap.
- Inspect existing Query Store and relevant DMV evidence only when helper/object attribution is
  reliable and access is already authorised.
- Treat missing, aggregated, evicted, or ambiguous Query Store/DMV evidence as a limitation.
- Do not repeatedly execute dbo.SUMMARY_PROC or dbo.UPDATE_ALL2 in Production for benchmarking.
- Actual plans or STATISTICS IO/TIME that execute stateful work require a representative restore or
  clone, or a separately approved safe window.

Explicitly out of scope unless separately approved:
- dbo.SUMMARY_PROC, helper, dbo.UPDATE_ALL2, or dbo.IMPORT_STAGING_PROC_CORE changes.
- SQL tuning, decomposition, indexes, views, procedures, tables, audit objects, migrations, Query
  Store configuration, Extended Events, traces, or SQL Agent changes.
- Bot, DAL, parser, importer, route, UX, file-handling, polling, output, or counter changes.
- Historical audit backfill.
- Residual stats_module.py, PreKvK, or inventory orchestration cleanup.

Required first response:
- Collection-gate verdict, exact sample window, count, batch IDs, and row-volume range.
- Current evidence state versus Slice 13 and the historical July observation.
- Phase/timestamp integrity results and timing distributions.
- Current SUMMARY_PROC responsibility/call map and shared-state constraints.
- Existing Query Store/DMV availability, helper attribution, and limitations.
- Evidence-backed implementation boundary: continue observing, separate instrumentation proposal,
  focused helper tuning task, or responsibility/decomposition design task.
- Remaining slice map for SUMMARY_PROC, UPDATE_ALL2, IMPORT_STAGING_PROC_CORE, stats_module cleanup,
  PreKvK cleanup, and inventory orchestration.
- Validation plan, SQL position, smoke expectations, and Codex Security decision.
- Open questions or approval needed.

Stop for approval before any code, SQL, configuration, instrumentation, or Production-state change.
```
