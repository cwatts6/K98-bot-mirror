# Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 7 MGE Results Import Audit Adoption

Use this starter to begin Task C Slice 7 after Task C Slice 6 is merged, deployed, and smoke
tested.

```markdown
# Files mentioned by the user:

## Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 7 MGE Results Import Audit Adoption.md: C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 7 MGE Results Import Audit Adoption.md

## My request for Codex:
Begin Task C Slice 7 - Import Pipeline Deferred Optimisation: MGE Results Import Audit Adoption.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 7 MGE Results Import Audit Adoption.md

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
- Task C Slice 3A normalized batch-level RowsInSource through SQL-owned terminal writer procedures and bot DAL/service wrappers.
- Task C Slice 4 adopted generic durable audit for Honor uploads and preserved Honor upload UX/import behavior.
- Task C Slice 5 adopted generic durable audit for PreKvK uploads and preserved PreKvK upload UX/import behavior.
- Task C Slice 6 adopted generic durable audit for weekly activity uploads and preserved weekly activity upload UX/import behavior.
- Task C Slice 6 production smoke testing on 2026-06-29 confirmed weekly activity batches 11 and 12 completed with RowsInSource=816, RowsStaged=816, RowsWritten=816, RowsSkipped=0, ExternalBatchTable=dbo.AllianceActivitySnapshotHeader, ExternalBatchId=440 and 441, and completed weekly_activity_xlsx_parse, weekly_activity_sql_ingest, and weekly_activity_post_import_backup phases.
- Task C Slice 6 production smoke testing on 2026-06-29 confirmed duplicate batch 13 completed with Status=duplicate, RowsInSource=816, RowsSkipped=816, no external correlation, and completed parse plus duplicate ingest phases.

Start with audit/scope and SQL implementation-boundary confirmation only.

Next-slice goal:
- Adopt generic durable import audit for the MGE results upload/import path only.
- Validate the current MGE results route, parser/importer, SQL domain import/final result/event objects, duplicate semantics, manual overwrite semantics, output embeds, report generation, telemetry/logging, and tests.
- Validate accepted-import external batch correlation for dbo.MGE_ResultImports, expected as ExternalBatchTable=dbo.MGE_ResultImports and ExternalBatchId=<ImportId>, unless SQL validation finds a better stable contract.
- Validate whether duplicate pre-check failures or failed outcomes before a domain import row exists should remain uncorrelated.
- Validate whether failed outcomes after dbo.MGE_ResultImports creation can be correlated without changing importer behavior.
- Reuse existing Task C Slice 2 / Slice 3A audit DAL/service wrappers and SQL-owned writer procedures.
- Preserve MGE results upload route UX, embed text, file handling, importer behavior, duplicate/overwrite behavior, report generation, SQL outputs, telemetry/logging, and user-facing behavior.
- Keep audit writes best-effort.
- Avoid new SQL schema objects unless validation finds a blocker and approval is granted.

Explicitly out of scope unless separately approved:
- Discord command changes.
- Upload route UX or embed text changes.
- Queue UX/embed behavior changes.
- Fallback, player-location, Honor, PreKvK, weekly activity, or inventory behavior changes.
- Wiring inventory generic audit adoption.
- Changing MGE SQL table schemas, reporting semantics, output files, event completion behavior, or channel gating.
- Redesigning MGE signup, roster, award, event, or publish workflows.
- New SQL schema tables or new generic audit objects.
- Replacing or redesigning the MGE results importer.
- Adding the dbo.UPDATE_ALL2 wrapper/audit-output layer.
- Splitting dbo.IMPORT_STAGING_PROC.
- Decomposing or replacing dbo.UPDATE_ALL2.
- Historical production data backfill.
- Operator UI/reporting dashboards for audit history.

Audit these before proposing implementation:
- C:\discord_file_downloader\upload_routes\mge_results_route.py
- C:\discord_file_downloader\mge\mge_results_import.py
- C:\discord_file_downloader\mge\mge_xlsx_parser.py
- C:\discord_file_downloader\mge\dal\mge_results_dal.py
- C:\discord_file_downloader\ui\views\mge_results_overwrite_confirm_view.py
- C:\discord_file_downloader\services\import_audit_service.py
- C:\discord_file_downloader\stats\dal\import_audit_dal.py
- C:\discord_file_downloader\tests\test_mge_results_upload_route.py
- C:\discord_file_downloader\tests\test_mge_results_import.py
- C:\discord_file_downloader\tests\test_mge_results_import_service.py
- C:\discord_file_downloader\tests\test_mge_results_overwrite_confirm_view.py
- C:\discord_file_downloader\tests\test_import_audit_service.py
- C:\discord_file_downloader\tests\test_import_audit_dal.py
- C:\K98-bot-SQL-Server SQL definitions for generic audit objects and MGE result domain/reporting objects.
- C:\K98-bot-SQL-Server migrations README and SQL deployment/promotion guardrails if SQL changes are proposed.

Required first response:
- Scope summary.
- Current MGE results import state.
- SQL position and external batch correlation proposal.
- Audit taxonomy proposal.
- Implementation proposal.
- Remaining slice map for inventory, UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup, PreKvK legacy SQL cleanup, and weekly cumulative view cleanup.
- Validation plan including SQL validation, focused tests, broad checks, smoke tests, and Codex Security review.
- Open questions or approval needed.

Stop for approval before code or SQL changes.
```
