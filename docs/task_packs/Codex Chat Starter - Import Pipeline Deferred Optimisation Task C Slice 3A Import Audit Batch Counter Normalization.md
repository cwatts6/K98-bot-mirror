# Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 3A Import Audit Batch Counter Normalization

Use this starter to begin Task C Slice 3A after Task C Slice 3 player-location audit adoption is
merged, deployed, and smoke tested.

```markdown
# Files mentioned by the user:

## Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3A Import Audit Batch Counter Normalization.md: C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3A Import Audit Batch Counter Normalization.md

## My request for Codex:
Begin Task C Slice 3A - Import Pipeline Deferred Optimisation: Import Audit Batch Counter Normalization.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3A Import Audit Batch Counter Normalization.md

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

Confirmed delivered baseline:
- Full fallback imports work with Credit.
- Full fallback imports work with Conduct Score.
- Interim auto partial fallback imports work from the monitored Discord folder.
- Interim auto partial fallback preserves non-ASCII governor names.
- Partial fallback rows overlay the latest full KingdomScanData4 snapshot and preserve absent fields.
- Location import remains unchanged for player-visible behavior.
- shield_time_left is stored as ShieldEndsAtUnix / ShieldEndsAtUtc and visible on v_PlayerProfile.
- Task B uses raw text SQL staging plus explicit typed conversion for the Unicode-preserving fallback import path.
- Task C Slice 1 extracted fallback import orchestration into service/DAL wrappers while preserving all current behavior.
- Task C Slice 2 added dbo.ImportAuditBatch, dbo.ImportAuditPhase, SQL-owned audit writer procedures, bot audit DAL/service wrappers, and fallback-first audit wiring correlated to dbo.FallbackImportBatchControl.
- Task C Slice 2 preserved route, command, queue, CSV/XLSX, staging, SQL procedure, and output behavior.
- Task C Slice 2 smoke testing on 2026-06-29 confirmed completed audit batches and phase rows for full fallback and interim auto partial fallback imports.
- Task C Slice 3 mapped current non-fallback import state surfaces for location, Honor, PreKvK, weekly activity, MGE, and inventory.
- Task C Slice 3 wired player-location generic audit for the auto scan_1198.csv route and /location import command merge path.
- Task C Slice 3 preserved route, command, queue, embed, file, staging, cache refresh, SQL procedure, output behavior, and user-facing refresh failure semantics.
- Task C Slice 3 production smoke testing on 2026-06-29 confirmed player_location audit batch 3 completed with 301 staged/written rows and phases location_csv_parse, location_sql_replace, and location_post_import_refresh completed.
- Task C Slice 3 production smoke testing also confirmed no-valid-row scan_1198.csv creates a skipped player_location audit batch with location_csv_parse skipped and NoValidLocationRows.

Start with audit/scope and SQL implementation-boundary confirmation only.

Next-slice goal:
- Normalize batch-level RowsInSource for generic import audit batches when the source row count is known only after dbo.usp_ImportAudit_StartBatch.
- Validate the current SQL writer procedure contract for dbo.usp_ImportAudit_CompleteBatch and dbo.usp_ImportAudit_FailBatch.
- Propose the smallest SQL-owned writer-procedure change, expected to be an optional @RowsInSource int = NULL parameter on terminal writer procedures, unless SQL validation finds a better existing contract.
- Thread RowsInSource through bot DAL/service wrappers and already wired fallback/player-location callers only after approval.
- Preserve route, command, queue, embed, file, staging, cache refresh, SQL procedure output, and user-facing behavior.
- Keep audit writes best-effort.
- Avoid historical production backfill unless separately approved.
- Confirm this slice completes the RowsInSource normalization deferred item before Honor, PreKvK, weekly activity, MGE, and inventory adoption continue.

Explicitly out of scope unless separately approved:
- Discord command changes.
- Upload route UX or embed text changes.
- Queue UX/embed behavior changes.
- Fallback import behavior changes.
- Wiring Honor, PreKvK, weekly activity, MGE, or inventory generic audit adoption.
- Changing inventory's existing domain audit/history model.
- New SQL schema tables or new generic audit objects.
- Splitting dbo.IMPORT_STAGING_PROC.
- Adding the dbo.UPDATE_ALL2 wrapper/audit-output layer.
- Decomposing or replacing dbo.UPDATE_ALL2.
- Historical production data backfill.
- Operator UI/reporting dashboards for audit history.

Audit these before proposing implementation:
- C:\discord_file_downloader\services\import_audit_service.py
- C:\discord_file_downloader\stats\dal\import_audit_dal.py
- C:\discord_file_downloader\services\fallback_import_service.py
- C:\discord_file_downloader\stats\dal\fallback_import_dal.py
- C:\discord_file_downloader\stats_module.py
- C:\discord_file_downloader\services\location_import_service.py
- C:\discord_file_downloader\upload_routes\player_location_route.py
- C:\discord_file_downloader\commands\location_cmds.py
- C:\discord_file_downloader\tests\test_import_audit_service.py
- C:\discord_file_downloader\tests\test_import_audit_dal.py
- C:\discord_file_downloader\tests\test_location_import_service.py
- C:\discord_file_downloader\tests\test_player_location_upload_route.py
- C:\K98-bot-SQL-Server SQL definitions for dbo.ImportAuditBatch, dbo.usp_ImportAudit_CompleteBatch, and dbo.usp_ImportAudit_FailBatch.
- C:\K98-bot-SQL-Server migrations README and SQL deployment/promotion guardrails.

Required first response:
- Scope summary.
- Current counter state for RowsInSource, RowsStaged, RowsWritten, RowsSkipped, phase counters, and details JSON.
- SQL position and writer-procedure compatibility proposal.
- Bot DAL/service position and best-effort behavior.
- Remaining slice map for Honor, PreKvK, weekly activity, MGE, inventory, UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, and residual stats_module cleanup.
- Validation plan including SQL validation, focused tests, smoke tests, and Codex Security review.
- Open questions or approval needed.

Stop for approval before code or SQL changes.
```
