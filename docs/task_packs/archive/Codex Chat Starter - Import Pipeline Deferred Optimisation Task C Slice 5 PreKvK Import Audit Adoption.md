# Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 5 PreKvK Import Audit Adoption

Archived: Task C Slice 5 was delivered in mirror PR #186 and production PR #494, then production
smoke tested successfully on 2026-06-29. Use the Slice 6 weekly activity starter in
`docs/task_packs/` for the next import-audit adoption slice.

The historical starter below is preserved as the Slice 5 initiation record.

```markdown
# Files mentioned by the user:

## Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 5 PreKvK Import Audit Adoption.md: C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 5 PreKvK Import Audit Adoption.md

## My request for Codex:
Begin Task C Slice 5 - Import Pipeline Deferred Optimisation: PreKvK Import Audit Adoption.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 5 PreKvK Import Audit Adoption.md

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

Start with audit/scope and SQL implementation-boundary confirmation only.

Next-slice goal:
- Adopt generic durable import audit for the PreKvK upload/import path only.
- Validate the current PreKvK route, parser/importer, SQL domain tables/history objects/views/procedures, ranking/report refresh, telemetry, duplicate/rejection semantics, and tests.
- Validate accepted-import external batch correlation for dbo.PreKvk_Scan, expected as ExternalBatchTable=dbo.PreKvk_Scan and ExternalBatchId=<KVK_NO>:<ScanID>, unless SQL validation finds a better stable contract.
- Validate whether duplicate/rejected/failed outcomes should correlate to dbo.PreKvk_ImportHistory.HistoryID if that can be propagated safely without changing user-facing behavior.
- Reuse existing Task C Slice 2 / Slice 3A audit DAL/service wrappers and SQL-owned writer procedures.
- Preserve PreKvK upload route UX, embed text, file handling, importer transaction behavior, duplicate/rejection behavior, import-history semantics, ranking/report refresh, telemetry, SQL outputs, and user-facing behavior.
- Keep audit writes best-effort.
- Avoid new SQL schema objects unless validation finds a blocker and approval is granted.

Explicitly out of scope unless separately approved:
- Discord command changes, including /prekvk import_history.
- Upload route UX or embed text changes.
- Queue UX/embed behavior changes.
- Fallback, player-location, Honor, weekly activity, MGE, or inventory behavior changes.
- Wiring weekly activity, MGE, or inventory generic audit adoption.
- Changing PreKvK ranking/report semantics, output files, or channel gating.
- Replacing dbo.PreKvk_ImportHistory with generic audit history.
- Retiring dbo.PreKvk_Phases or other legacy PreKvK SQL objects.
- New SQL schema tables or new generic audit objects.
- Adding the dbo.UPDATE_ALL2 wrapper/audit-output layer.
- Splitting dbo.IMPORT_STAGING_PROC.
- Decomposing or replacing dbo.UPDATE_ALL2.
- Historical production data backfill.
- Operator UI/reporting dashboards for audit history.

Audit these before proposing implementation:
- C:\discord_file_downloader\upload_routes\prekvk_route.py
- C:\discord_file_downloader\prekvk_importer.py
- C:\discord_file_downloader\prekvk\diagnostics_service.py
- C:\discord_file_downloader\prekvk\dal\import_history_dal.py
- C:\discord_file_downloader\prekvk\dal\report_dal.py
- C:\discord_file_downloader\prekvk\report_service.py
- C:\discord_file_downloader\services\import_audit_service.py
- C:\discord_file_downloader\stats\dal\import_audit_dal.py
- C:\discord_file_downloader\tests\test_prekvk_upload_route.py
- C:\discord_file_downloader\tests\test_prekvk_importer.py
- C:\discord_file_downloader\tests\test_prekvk_diagnostics.py
- C:\discord_file_downloader\tests\test_import_audit_service.py
- C:\discord_file_downloader\tests\test_import_audit_dal.py
- C:\K98-bot-SQL-Server SQL definitions for generic audit objects and PreKvK domain/history objects.
- C:\K98-bot-SQL-Server migrations README and SQL deployment/promotion guardrails if SQL changes are proposed.

Required first response:
- Scope summary.
- Current PreKvK import state.
- SQL position and external batch correlation proposal.
- Audit taxonomy proposal.
- Implementation proposal.
- Remaining slice map for weekly activity, MGE, inventory, UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup, and PreKvK legacy SQL cleanup.
- Validation plan including SQL validation, focused tests, broad checks, smoke tests, and Codex Security review.
- Open questions or approval needed.

Stop for approval before code or SQL changes.
```
