# Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 6 Weekly Activity Import Audit Adoption

Use this starter to begin Task C Slice 6 after Task C Slice 5 is merged, deployed, and smoke
tested.

```markdown
# Files mentioned by the user:

## Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 6 Weekly Activity Import Audit Adoption.md: C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 6 Weekly Activity Import Audit Adoption.md

## My request for Codex:
Begin Task C Slice 6 - Import Pipeline Deferred Optimisation: Weekly Activity Import Audit Adoption.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 6 Weekly Activity Import Audit Adoption.md

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
- Task C Slice 3 mapped current non-fallback import state surfaces for location, Honor, PreKvK, weekly activity, MGE, and inventory.
- Task C Slice 3 wired player-location generic audit for the auto scan_1198.csv route and /location import command merge path.
- Task C Slice 3 preserved route, command, queue, embed, file, staging, cache refresh, SQL procedure, output behavior, and user-facing refresh failure semantics.
- Task C Slice 3 production smoke testing on 2026-06-29 confirmed completed and skipped player_location audit batches.
- Task C Slice 3A normalized batch-level RowsInSource through SQL-owned terminal writer procedures and bot DAL/service wrappers.
- Task C Slice 3A production smoke testing on 2026-06-29 confirmed fallback batch 5 completed with RowsInSource=374 and player_location batch 6 completed with RowsInSource=302.
- Task C Slice 4 adopted generic durable audit for Honor uploads, fixed the Honor stats-refresh call signature, added terminal audit fallback after post-ingest errors, and preserved Honor upload UX/import behavior.
- Task C Slice 4 production smoke testing on 2026-06-29 confirmed Honor batch 7 completed with RowsInSource=562, RowsStaged=562, RowsWritten=562, RowsSkipped=0, ExternalBatchTable=dbo.KVK_Honor_Scan, ExternalBatchId=15:92, and completed honor_xlsx_parse, honor_sql_ingest, and honor_post_import_refresh phases.
- Task C Slice 5 adopted generic durable audit for PreKvK uploads, added terminal failure audit for refresh failures, and preserved PreKvK upload UX/import behavior.
- Task C Slice 5 production smoke testing on 2026-06-29 confirmed accepted PreKvK batch 8 completed with RowsInSource=1, RowsStaged=1, RowsWritten=1, RowsSkipped=0, ExternalBatchTable=dbo.PreKvk_Scan, ExternalBatchId=15:1095; duplicate batch 9 completed with ExternalBatchTable=dbo.PreKvk_ImportHistory, ExternalBatchId=17, RowsSkipped=1; and rejected batch 10 failed with ErrorType=MissingColumns, ExternalBatchTable=dbo.PreKvk_ImportHistory, ExternalBatchId=18.

Start with audit/scope and SQL implementation-boundary confirmation only.

Next-slice goal:
- Adopt generic durable import audit for the weekly activity upload/import path only.
- Validate the current weekly activity route, parser/importer, SQL snapshot/header/row/delta/daily objects/views, duplicate semantics, output embeds, telemetry/logging, and tests.
- Validate accepted-import external batch correlation for dbo.AllianceActivitySnapshotHeader, expected as ExternalBatchTable=dbo.AllianceActivitySnapshotHeader and ExternalBatchId=<SnapshotId>, unless SQL validation finds a better stable contract.
- Validate whether duplicate/failed outcomes have a stable pre-existing domain correlation candidate or should remain uncorrelated when no snapshot row exists.
- Reuse existing Task C Slice 2 / Slice 3A audit DAL/service wrappers and SQL-owned writer procedures.
- Preserve weekly activity upload route UX, embed text, file handling, importer transaction behavior, duplicate behavior, output tables, telemetry/logging, SQL outputs, and user-facing behavior.
- Keep audit writes best-effort.
- Avoid new SQL schema objects unless validation finds a blocker and approval is granted.

Explicitly out of scope unless separately approved:
- Discord command changes, including /activity.
- Upload route UX or embed text changes.
- Queue UX/embed behavior changes.
- Fallback, player-location, Honor, PreKvK, MGE, or inventory behavior changes.
- Wiring MGE or inventory generic audit adoption.
- Changing weekly activity SQL table schemas, reporting view semantics, output files, or channel gating.
- New SQL schema tables or new generic audit objects.
- Replacing or redesigning the weekly activity importer.
- Adding the dbo.UPDATE_ALL2 wrapper/audit-output layer.
- Splitting dbo.IMPORT_STAGING_PROC.
- Decomposing or replacing dbo.UPDATE_ALL2.
- Historical production data backfill.
- Operator UI/reporting dashboards for audit history.

Audit these before proposing implementation:
- C:\discord_file_downloader\upload_routes\weekly_activity_route.py
- C:\discord_file_downloader\weekly_activity_importer.py
- C:\discord_file_downloader\docs\reference\weekly_activity_importer.md
- C:\discord_file_downloader\services\import_audit_service.py
- C:\discord_file_downloader\stats\dal\import_audit_dal.py
- C:\discord_file_downloader\tests\test_weekly_activity_upload_route.py
- C:\discord_file_downloader\tests\test_import_audit_service.py
- C:\discord_file_downloader\tests\test_import_audit_dal.py
- C:\K98-bot-SQL-Server SQL definitions for generic audit objects and weekly activity domain/reporting objects.
- C:\K98-bot-SQL-Server migrations README and SQL deployment/promotion guardrails if SQL changes are proposed.

Required first response:
- Scope summary.
- Current weekly activity import state.
- SQL position and external batch correlation proposal.
- Audit taxonomy proposal.
- Implementation proposal.
- Remaining slice map for MGE, inventory, UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup, and PreKvK legacy SQL cleanup.
- Validation plan including SQL validation, focused tests, broad checks, smoke tests, and Codex Security review.
- Open questions or approval needed.

Stop for approval before code or SQL changes.
```
