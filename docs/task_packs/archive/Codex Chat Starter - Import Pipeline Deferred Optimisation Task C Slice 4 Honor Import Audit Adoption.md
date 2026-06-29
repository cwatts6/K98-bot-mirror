# Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 4 Honor Import Audit Adoption

Archived: Task C Slice 4 was delivered in mirror PR #185 and production PR #493, then production
smoke tested successfully on 2026-06-29. Use the Slice 5 PreKvK starter in `docs/task_packs/` for
the next import-audit adoption slice.

Use this historical starter only for context on how Task C Slice 4 was initiated after Task C
Slice 3A was merged, deployed, and smoke tested.

```markdown
# Files mentioned by the user:

## Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 4 Honor Import Audit Adoption.md: C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 4 Honor Import Audit Adoption.md

## honor_scan.md: C:\discord_file_downloader\docs\reference\honor_scan.md

## My request for Codex:
Begin Task C Slice 4 - Import Pipeline Deferred Optimisation: Honor Import Audit Adoption.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 4 Honor Import Audit Adoption.md

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
- Task C Slice 3A did not backfill historical audit rows; earlier production batches retained RowsInSource=NULL.

Start with audit/scope and SQL implementation-boundary confirmation only.

Next-slice goal:
- Adopt generic durable import audit for the KVK Honor upload/import path only.
- Validate the current Honor route, parser, importer, SQL domain tables/views/procedures, ranking refresh, telemetry, and tests.
- Validate the external batch correlation for dbo.KVK_Honor_Scan, expected as ExternalBatchTable=dbo.KVK_Honor_Scan and ExternalBatchId=<KVK_NO>:<ScanID>, unless SQL validation finds a better stable contract.
- Reuse existing Task C Slice 2 / Slice 3A audit DAL/service wrappers and SQL-owned writer procedures.
- Preserve Honor upload route UX, embed text, file handling, importer transaction behavior, ranking refresh, telemetry, SQL outputs, and user-facing behavior.
- Keep audit writes best-effort.
- Avoid new SQL schema objects unless validation finds a blocker and approval is granted.

Explicitly out of scope unless separately approved:
- Discord command changes.
- Upload route UX or embed text changes.
- Queue UX/embed behavior changes.
- Fallback or player-location behavior changes.
- Wiring PreKvK, weekly activity, MGE, or inventory generic audit adoption.
- Changing inventory's existing domain audit/history model.
- New SQL schema tables or new generic audit objects.
- Changing Honor ranking semantics, output files, or channel gating.
- Adding the dbo.UPDATE_ALL2 wrapper/audit-output layer.
- Splitting dbo.IMPORT_STAGING_PROC.
- Decomposing or replacing dbo.UPDATE_ALL2.
- Historical production data backfill.
- Operator UI/reporting dashboards for audit history.

Audit these before proposing implementation:
- C:\discord_file_downloader\upload_routes\honor_route.py
- C:\discord_file_downloader\honor_importer.py
- C:\discord_file_downloader\services\import_audit_service.py
- C:\discord_file_downloader\stats\dal\import_audit_dal.py
- C:\discord_file_downloader\tests\test_honor_upload_route.py
- C:\discord_file_downloader\tests\test_honor_importer.py
- C:\discord_file_downloader\tests\test_import_audit_service.py
- C:\discord_file_downloader\tests\test_import_audit_dal.py
- C:\discord_file_downloader\docs\reference\honor_scan.md
- C:\K98-bot-SQL-Server SQL definitions for generic audit objects and Honor domain objects.
- C:\K98-bot-SQL-Server migrations README and SQL deployment/promotion guardrails if SQL changes are proposed.

Required first response:
- Scope summary.
- Current Honor import state.
- SQL position and external batch correlation proposal.
- Audit taxonomy proposal.
- Implementation proposal.
- Remaining slice map for PreKvK, weekly activity, MGE, inventory, UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, and residual stats_module cleanup.
- Validation plan including SQL validation, focused tests, broad checks, smoke tests, and Codex Security review.
- Open questions or approval needed.

Stop for approval before code or SQL changes.
```
