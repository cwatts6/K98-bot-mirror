# Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 11 Import Audit Phase Timestamp Normalization

Use this starter to begin the generic import-audit timestamp-normalization slice after Rally Forts
Task C Slice 10 is merged, deployed, and smoke tested.

```markdown
# Files mentioned by the user:

## Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 11 Import Audit Phase Timestamp Normalization.md: C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 11 Import Audit Phase Timestamp Normalization.md

## My request for Codex:
Begin Task C Slice 11 - Import Pipeline Deferred Optimisation: Import Audit Phase Timestamp Normalization.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 11 Import Audit Phase Timestamp Normalization.md

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
- Task C Slice 8 adopted generic durable audit for inventory image uploads, command-session imports, additional-material continuation, approval/reject/cancel/timeout/failure outcomes, and smoke testing confirmed the material continuation image count is now 3 for three imported files.
- Task C Slice 9 adopted generic durable audit for KVK_ALL uploads. Production smoke confirmed completed batch 23 correlated to KVK.KVK_Scan / 15:83 with 9194 rows, and KVK_Details rejection batch 22 correlated to KVK.KVK_Ingest_Diagnostics / 2 with 9194 staged/skipped rows.
- Task C Slice 10 adopted generic durable audit for Rally Forts uploads. Production smoke was reported successful on 2026-07-01. Successful daily/all-time imports correlate to dbo.IngestionLog/<IngestionID>; duplicate/no-row/unrecognized/preflight/failure outcomes remain externally uncorrelated. Review follow-ups sanitized audit source filenames, populated source-file hashes for saved workbooks, and aligned backup-schedule failure rows_out behavior with other upload routes.

Start with audit/scope and SQL implementation-boundary confirmation only.

Next-slice goal:
- Normalize generic ImportAuditPhase timestamp handling so new persisted phase rows cannot show CompletedAtUtc earlier than StartedAtUtc.
- Validate whether the mismatch comes from caller-supplied StartedAtUtc, SQL-owned completion time, Python service/DAL defaults, or clock/precision rounding.
- Preserve best-effort audit behavior, phase status semantics, duration semantics, route/importer contracts, SQL import behavior, user-facing behavior, batch counters, and external correlation contracts.
- Prefer the smallest safe fix in the generic service/DAL or SQL writer procedure after SQL validation.
- Avoid historical production audit backfill.
- Avoid route-specific audit adoption changes unless a caller is demonstrably passing an invalid timestamp contract and the correction is tiny.

Explicitly out of scope unless separately approved:
- Discord route UX or embed text changes.
- Attachment/file handling changes.
- Importer contract changes.
- SQL import procedure/table behavior changes outside generic audit writer timestamp normalization.
- New generic audit schema objects.
- Historical production data backfill.
- dbo.UPDATE_ALL2 wrapper/audit-output instrumentation.
- dbo.IMPORT_STAGING_PROC decomposition.
- dbo.UPDATE_ALL2 decomposition.
- Residual stats_module.py cleanup.
- Legacy PreKvK SQL cleanup.
- Weekly cumulative view cleanup.
- Inventory view-orchestration extraction.

Audit these before proposing implementation:
- C:\discord_file_downloader\services\import_audit_service.py
- C:\discord_file_downloader\stats\dal\import_audit_dal.py
- C:\discord_file_downloader\services\kvk_all_import_audit_service.py
- C:\discord_file_downloader\services\rally_forts_import_audit_service.py
- C:\discord_file_downloader\services\weekly_activity_import_audit_service.py
- C:\discord_file_downloader\services\prekvk_import_audit_service.py
- C:\discord_file_downloader\services\honor_import_audit_service.py
- C:\discord_file_downloader\tests\test_import_audit_service.py
- C:\discord_file_downloader\tests\test_import_audit_dal.py
- C:\K98-bot-SQL-Server SQL definitions for dbo.ImportAuditPhase and dbo.usp_ImportAudit_RecordPhase.

Required first response:
- Scope summary and why this follows Rally Forts closure.
- Current audit timestamp state for StartedAtUtc, CompletedAtUtc, and DurationMs.
- SQL position and whether a SQL repo change appears necessary.
- Implementation-boundary proposal: Python-only, SQL-writer, or combined.
- Remaining slice map for UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup, PreKvK legacy SQL cleanup, weekly cumulative view cleanup, and inventory orchestration follow-up.
- Validation plan including SQL validation, focused audit tests, broader checks, smoke expectations, and Codex Security decision.
- Open questions or approval needed.

Stop for approval before code or SQL changes.
```
