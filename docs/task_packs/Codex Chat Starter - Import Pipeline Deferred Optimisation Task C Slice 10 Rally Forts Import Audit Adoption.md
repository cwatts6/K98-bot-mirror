# Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 10 Rally Forts Import Audit Adoption

Use this starter to begin the Rally Forts implementation PR after KVK_ALL Task C Slice 9 is merged,
deployed, and smoke tested.

```markdown
# Files mentioned by the user:

## Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 10 Rally Forts Import Audit Adoption.md: C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 10 Rally Forts Import Audit Adoption.md

## My request for Codex:
Begin Task C Slice 10 - Import Pipeline Deferred Optimisation: Rally Forts Import Audit Adoption.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 10 Rally Forts Import Audit Adoption.md

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
- KVK_ALL route extraction is already complete from DL_bot upload-routing Phase 4 / PR 110.
- Rally Forts route extraction is already complete from DL_bot upload-routing Phase 5C / PR 115.
- Rally Forts generic durable import audit adoption is not yet complete.

Start with audit/scope and SQL implementation-boundary confirmation only.

Next-slice goal:
- Adopt generic durable import audit for the Rally Forts upload route.
- Validate current Rally Forts route/importer behavior, local file staging, SQL staging/current/log objects, daily/all-time result contracts, log-backup scheduling, and tests.
- Confirm Rally Forts external correlation to dbo.IngestionLog/<IngestionID> only if a safe return/lookup helper can expose it without changing behavior.
- Implement only a tiny Rally importer return/lookup change to expose dbo.IngestionLog.IngestionID if tests prove behavior is unchanged.
- Keep Rally duplicate/no-row/unrecognized/preflight failures externally uncorrelated.
- Reuse existing Task C Slice 2 / Slice 3A audit DAL/service wrappers and SQL-owned writer procedures.
- Preserve Rally route UX, embed text, attachment/file handling, importer contracts, SQL table/procedure behavior, log-backup scheduling, telemetry/logging, and user-facing behavior.
- Keep audit writes best-effort.
- Avoid new SQL schema objects unless validation finds a blocker and approval is granted.

Explicitly out of scope unless separately approved:
- Discord route UX or embed text changes.
- Accepted filename/extension changes.
- Replacing the Rally importer or offload mechanics.
- Rally workbook format redesign.
- SQL table schema, stored procedure, view, export, report, Google Sheets, or dashboard behavior changes.
- New SQL schema tables or new generic audit objects.
- Historical production data backfill.
- KVK_ALL implementation changes.
- dbo.UPDATE_ALL2 wrapper/audit-output instrumentation.
- dbo.IMPORT_STAGING_PROC decomposition.
- dbo.UPDATE_ALL2 decomposition.
- Residual stats_module.py cleanup.
- Legacy PreKvK SQL cleanup.
- Weekly cumulative view cleanup.
- Inventory view-orchestration extraction.

Audit these before proposing implementation:
- C:\discord_file_downloader\upload_routes\rally_forts_route.py
- C:\discord_file_downloader\forts_ingest.py
- C:\discord_file_downloader\services\import_audit_service.py
- C:\discord_file_downloader\stats\dal\import_audit_dal.py
- C:\discord_file_downloader\tests\test_rally_forts_upload_route.py
- C:\discord_file_downloader\tests\test_import_audit_service.py
- C:\discord_file_downloader\tests\test_import_audit_dal.py
- C:\K98-bot-SQL-Server SQL definitions for generic audit objects, dbo.IngestionLog, Rally staging/current tables, and Rally import procedures.

Required first response:
- Scope summary, including route-extraction-complete vs generic-audit-not-complete distinction.
- Current Rally Forts route/import state.
- SQL position and external batch correlation proposal.
- Audit taxonomy proposal.
- Implementation proposal.
- Remaining slice map for UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup, PreKvK legacy SQL cleanup, weekly cumulative view cleanup, and inventory orchestration follow-up.
- Validation plan including SQL validation, focused tests, broad checks, smoke tests, and Codex Security review.
- Open questions or approval needed.

Stop for approval before code or SQL changes.
```
