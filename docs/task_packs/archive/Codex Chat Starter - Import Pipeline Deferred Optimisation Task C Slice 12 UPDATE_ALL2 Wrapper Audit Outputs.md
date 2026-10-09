# Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 12 UPDATE_ALL2 Wrapper Audit Outputs

Use this starter to begin the next import-pipeline slice after Task C Slice 11 timestamp
normalization is merged, deployed, and smoke tested.

```markdown
# Files mentioned by the user:

## Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 12 UPDATE_ALL2 Wrapper Audit Outputs.md: C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 12 UPDATE_ALL2 Wrapper Audit Outputs.md

## My request for Codex:
Begin Task C Slice 12 - Import Pipeline Deferred Optimisation: UPDATE_ALL2 Wrapper Audit Outputs.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 12 UPDATE_ALL2 Wrapper Audit Outputs.md

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
- Task C Slice 3 wired player-location generic audit for the auto scan_1198.csv route and /location import command merge path.
- Task C Slice 3A normalized batch-level RowsInSource through SQL-owned terminal writer procedures and bot DAL/service wrappers.
- Task C Slice 4 adopted generic durable audit for Honor uploads and preserved Honor upload UX/import behavior.
- Task C Slice 5 adopted generic durable audit for PreKvK uploads and preserved PreKvK upload UX/import behavior.
- Task C Slice 6 adopted generic durable audit for weekly activity uploads and preserved weekly activity upload UX/import behavior.
- Task C Slice 7 adopted generic durable audit for MGE results uploads and manual/overwrite imports through the importer.
- Task C Slice 8 adopted generic durable audit for inventory image uploads, command-session imports, additional-material continuation, approval/reject/cancel/timeout/failure outcomes, and material continuation image-count smoke.
- Task C Slice 9 adopted generic durable audit for KVK_ALL uploads.
- Task C Slice 10 adopted generic durable audit for Rally Forts uploads.
- Task C Slice 11 normalized generic ImportAuditPhase timestamp handling in bot service and SQL writer boundaries. Production smoke on 2026-07-01 confirmed new fallback batch 27 and player-location batch 28 phase rows no longer show CompletedAtUtc earlier than StartedAtUtc.

Start with audit/scope and SQL implementation-boundary confirmation only.

Next-slice goal:
- Scope a non-invasive wrapper or audit-output layer around dbo.UPDATE_ALL2 so fallback SQL rebuild work has durable phase-level timing/status evidence before any later decomposition.
- Validate current UPDATE_ALL2 execution, SP_TaskStatus polling, fallback audit phase behavior, and SQL repo procedure boundaries.
- Preserve fallback import behavior, SQL output tables, SP_TaskStatus polling behavior, user-facing behavior, batch counters, route/importer contracts, and the existing fallback_update_all2 phase semantics.
- Prefer additive SQL/Python observability over procedure decomposition.
- Avoid historical production audit backfill.

Explicitly out of scope unless separately approved:
- dbo.UPDATE_ALL2 decomposition or wholesale rewrite.
- dbo.IMPORT_STAGING_PROC decomposition.
- Discord route UX or embed text changes.
- Attachment/file handling changes.
- Importer contract changes.
- SQL import procedure/table behavior changes outside the approved audit-output boundary.
- New generic audit schema objects.
- Historical production data backfill.
- Residual stats_module.py cleanup outside tiny integration needed for this slice.
- Legacy PreKvK SQL cleanup.
- Weekly cumulative view cleanup.
- Inventory view-orchestration extraction.

Audit these before proposing implementation:
- C:\discord_file_downloader\stats_module.py
- C:\discord_file_downloader\services\fallback_import_service.py
- C:\discord_file_downloader\stats\dal\fallback_import_dal.py
- C:\discord_file_downloader\update_all2_log_manager.py
- C:\discord_file_downloader\services\import_audit_service.py
- C:\discord_file_downloader\stats\dal\import_audit_dal.py
- C:\discord_file_downloader\tests\test_import_audit_service.py
- C:\discord_file_downloader\tests\test_import_audit_dal.py
- C:\discord_file_downloader\tests\test_fallback_import_dal.py
- C:\K98-bot-SQL-Server SQL definitions for dbo.UPDATE_ALL2 and SP_TaskStatus/status objects used by fallback polling.

Required first response:
- Scope summary and why this follows Slice 11 timestamp normalization.
- Current UPDATE_ALL2 observation state: how fallback starts, polls, logs, and audits the SQL step.
- SQL position and whether a SQL repo change appears necessary.
- Implementation-boundary proposal: Python-only, SQL wrapper/writer, or combined.
- Remaining slice map for IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup, PreKvK legacy SQL cleanup, weekly cumulative view cleanup, and inventory orchestration follow-up.
- Validation plan including SQL validation, focused tests, broader checks, smoke expectations, and Codex Security decision.
- Open questions or approval needed.

Stop for approval before code or SQL changes.
```
