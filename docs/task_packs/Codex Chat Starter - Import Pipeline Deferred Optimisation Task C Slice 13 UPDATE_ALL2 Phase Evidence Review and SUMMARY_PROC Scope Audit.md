# Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 13 UPDATE_ALL2 Phase Evidence Review and SUMMARY_PROC Scope Audit

Use this starter after Task C Slice 12 is merged, deployed, restarted, and at least a few
fallback imports have produced `update_all2_*` phase rows.

```markdown
# Files mentioned by the user:

## Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 13 UPDATE_ALL2 Phase Evidence Review and SUMMARY_PROC Scope Audit.md: C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 13 UPDATE_ALL2 Phase Evidence Review and SUMMARY_PROC Scope Audit.md

## My request for Codex:
Begin Task C Slice 13 - Import Pipeline Deferred Optimisation: UPDATE_ALL2 Phase Evidence Review and SUMMARY_PROC Scope Audit.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 13 UPDATE_ALL2 Phase Evidence Review and SUMMARY_PROC Scope Audit.md

Completed dependencies:
- Task A:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md
- Task B:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md
- Task C Slice 1:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Import Architecture and Service DAL Wrappers.md
- Task C Slice 2:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation.md
- Task C Slice 3:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3 Non-Fallback Audit Adoption.md
- Task C Slice 3A:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3A Import Audit Batch Counter Normalization.md
- Task C Slice 4:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 4 Honor Import Audit Adoption.md
- Task C Slice 5:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 5 PreKvK Import Audit Adoption.md
- Task C Slice 6:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 6 Weekly Activity Import Audit Adoption.md
- Task C Slice 7:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 7 MGE Results Import Audit Adoption.md
- Task C Slice 8:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 8 Inventory Import Audit Adoption.md
- Task C Slice 9:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 9 KVK_ALL and Rally Forts Import Audit Adoption.md
- Task C Slice 10:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 10 Rally Forts Import Audit Adoption.md
- Task C Slice 11:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 11 Import Audit Phase Timestamp Normalization.md
- Task C Slice 12:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 12 UPDATE_ALL2 Wrapper Audit Outputs.md

Confirmed delivered baseline:
- Full fallback imports work with Credit.
- Full fallback imports work with Conduct Score.
- Interim auto partial fallback imports work from the monitored Discord folder.
- Interim auto partial fallback preserves non-ASCII governor names.
- Partial fallback rows overlay the latest full KingdomScanData4 snapshot and preserve absent fields.
- Location import remains unchanged for player-visible behavior.
- shield_time_left is stored as ShieldEndsAtUnix / ShieldEndsAtUtc and visible on v_PlayerProfile.
- Task C Slice 1 extracted fallback import orchestration into service/DAL wrappers while preserving all current behavior.
- Task C Slice 2 added dbo.ImportAuditBatch, dbo.ImportAuditPhase, SQL-owned audit writer procedures, bot audit DAL/service wrappers, and fallback-first audit wiring correlated to dbo.FallbackImportBatchControl.
- Task C Slice 3 through Slice 10 adopted generic durable audit for player-location, Honor, PreKvK, weekly activity, MGE, inventory, KVK_ALL, and Rally Forts import families.
- Task C Slice 11 normalized generic ImportAuditPhase timestamp handling.
- Task C Slice 12 added non-invasive dbo.UPDATE_ALL2 phase audit output rows, bot parser/projection, and production smoke confirmed 13 update_all2_* subphase rows on fallback batch 67.
- Slice 12 review follow-up confirmed _update_all2_phase_results no longer leaks into fallback_update_all2 coarse phase details after bot restart.

Start with audit/scope and evidence review only.

Next-slice goal:
- Analyze recent fallback ImportAuditBatch/ImportAuditPhase data now that dbo.UPDATE_ALL2 emits durable update_all2_* phase rows.
- Quantify phase runtimes, missing timing gaps, timestamp anomalies, failures/skips, and whether update_all2_summary_proc consistently dominates runtime.
- Validate SQL repo definitions for dbo.UPDATE_ALL2, dbo.SUMMARY_PROC, and SUMMARY_PROC helper procedures before recommending any implementation slice.
- Preserve fallback import behavior, SQL output tables, SP_TaskStatus polling behavior, user-facing behavior, batch counters, route/importer contracts, and existing fallback_update_all2 semantics.
- Avoid procedure decomposition or tuning until evidence supports a specific next boundary.

Explicitly out of scope unless separately approved:
- dbo.UPDATE_ALL2 decomposition or wholesale rewrite.
- dbo.SUMMARY_PROC rewrite/decomposition/performance tuning.
- dbo.IMPORT_STAGING_PROC decomposition.
- Discord route UX or embed text changes.
- Attachment/file handling changes.
- Importer contract changes.
- SQL import procedure/table behavior changes.
- New generic audit schema objects.
- Historical production audit backfill.
- Residual stats_module.py cleanup outside evidence-query support.
- Legacy PreKvK SQL cleanup.
- Weekly cumulative view cleanup.
- Inventory view-orchestration extraction.

Audit these before proposing implementation:
- Recent production dbo.ImportAuditBatch rows for ImportKind='fallback'.
- Recent production dbo.ImportAuditPhase rows for PhaseName='fallback_update_all2' and PhaseName LIKE 'update_all2_%'.
- C:\K98-bot-SQL-Server\sql_schema\dbo.UPDATE_ALL2.StoredProcedure.sql
- C:\K98-bot-SQL-Server\sql_schema\dbo.SUMMARY_PROC.StoredProcedure.sql
- C:\K98-bot-SQL-Server summary helper procedure definitions used by dbo.SUMMARY_PROC.
- Bot parser/projection boundaries only if evidence suggests missing or malformed phase rows.

Required first response:
- Scope summary and why this follows Slice 12.
- Current evidence state, including the 2026-07-09 smoke and update_all2_summary_proc timing.
- SQL position and whether any SQL repo change appears necessary now.
- Implementation-boundary proposal: audit/query-only, helper script/report, SQL view/procedure, or later decomposition task.
- Remaining slice map for SUMMARY_PROC audit/decomposition, UPDATE_ALL2 decomposition, IMPORT_STAGING_PROC split, stats_module cleanup, PreKvK cleanup, weekly view cleanup, and inventory orchestration.
- Validation plan including SQL evidence queries, focused docs/tests if changed, smoke expectations, and Codex Security decision.
- Open questions or approval needed.

Stop for approval before code or SQL changes.
```
