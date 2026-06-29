# Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation

Status: archived after Task C Slice 2 delivery. Use the Slice 3 starter for the next import-audit
slice.

Use this starter to begin the next import pipeline slice. Start with audit/scope and SQL design
only; do not implement code or SQL until the model and first implementation boundary are approved.

## Copy/Paste Starter

```text
Begin Task C Slice 2 - Import Pipeline Deferred Optimisation: Durable Batch Audit Foundation.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation.md

Completed dependencies:
- Task A:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md
- Task B:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md
- Task C Slice 1:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Import Architecture and Service DAL Wrappers.md

Confirmed delivered baseline:
- Full fallback imports work with Credit.
- Full fallback imports work with Conduct Score.
- Interim auto partial fallback imports work from the monitored Discord folder.
- Interim auto partial fallback preserves non-ASCII governor names.
- Partial fallback rows overlay the latest full KingdomScanData4 snapshot and preserve absent fields.
- Location import remains unchanged.
- shield_time_left is stored as ShieldEndsAtUnix / ShieldEndsAtUtc and visible on v_PlayerProfile.
- Task B uses raw text SQL staging plus explicit typed conversion for the Unicode-preserving fallback import path.
- Task C Slice 1 extracted fallback import orchestration into service/DAL wrappers while preserving all current behavior.
- Task C Slice 1 made no SQL, route, or command behavior changes.
- Task C Slice 1 smoke testing completed successfully.

Start with audit/scope and SQL design only.

Next-slice goal:
- Design a generic durable import batch audit model for fallback, location, honor, PreKvK, weekly activity, MGE, and inventory imports.
- Confirm whether the first implementation should create only SQL/DAL/service foundations or also wire fallback imports first.
- Preserve route, command, queue, CSV/XLSX, staging, SQL procedure, and output behavior.
- Treat audit writes as best-effort except where interim partial metadata is required to protect data.
- Preserve FallbackImportBatchControl compatibility unless a replacement/migration is separately approved.

Explicitly out of scope unless separately approved:
- Discord command changes.
- Upload route behavior changes.
- Queue UX/embed behavior changes.
- Non-fallback import behavior changes.
- Splitting dbo.IMPORT_STAGING_PROC.
- Decomposing or replacing dbo.UPDATE_ALL2.
- Historical production data backfill.
- Operator UI/reporting dashboards for audit history.
- Committing real production player files as fixtures.

Audit these before proposing implementation:
- C:\discord_file_downloader\stats_module.py
- C:\discord_file_downloader\services\fallback_import_service.py
- C:\discord_file_downloader\services\fallback_import_schema.py
- C:\discord_file_downloader\stats\dal\fallback_import_dal.py
- C:\discord_file_downloader\upload_routes\fallback_queue_route.py
- relevant location, honor, PreKvK, weekly activity, MGE, and inventory upload route / worker paths
- C:\discord_file_downloader\bot_helpers.py
- C:\discord_file_downloader\update_all2_log_manager.py
- C:\discord_file_downloader\tests\test_fallback_import_schema.py
- C:\discord_file_downloader\tests\test_stats_module.py
- C:\discord_file_downloader\tests\test_fallback_import_dal.py
- C:\K98-bot-SQL-Server\sql_schema\dbo.FallbackImportBatchControl.Table.sql
- C:\K98-bot-SQL-Server\sql_schema\dbo.IMPORT_STAGING_PROC.StoredProcedure.sql
- C:\K98-bot-SQL-Server\sql_schema\dbo.IMPORT_STAGING_CSV.Table.sql
- raw fallback staging table introduced by Task B
- C:\K98-bot-SQL-Server\sql_schema\dbo.IMPORT_STAGING.Table.sql
- C:\K98-bot-SQL-Server\sql_schema\dbo.UPDATE_ALL2.StoredProcedure.sql
- Task A, Task B, and Task C-related SQL migrations

Required first response:
- Scope summary.
- Current import state surfaces across fallback, location, honor, PreKvK, weekly activity, MGE, and inventory.
- SQL design proposal for durable batch/phase/outcome tracking.
- Service/DAL architecture and best-effort audit behavior.
- Proposed first implementation boundary and rollback plan.
- Remaining slices for non-fallback adoption, IMPORT_STAGING_PROC split, UPDATE_ALL2 wrapper, and UPDATE_ALL2 decomposition.
- Validation plan including SQL validation, focused tests, smoke tests, and Codex Security review.
- Open questions or approval needed.

Stop for approval before code or SQL changes.
```

## Expected First Response Shape

```markdown
**Scope Summary**
<generic durable audit objective, implementation boundary, explicit exclusions>

**Current Import State Surfaces**
<fallback/location/honor/PreKvK/weekly/MGE/inventory queue, file, staging, procedure, output, and error state>

**SQL Design Proposal**
<batch/phase/outcome tables or procedures, FallbackImportBatchControl compatibility, migration/rollback>

**Service/DAL Architecture**
<Python module ownership, transaction/error handling, best-effort audit behavior>

**Remaining Slices**
<non-fallback adoption, IMPORT_STAGING_PROC split, UPDATE_ALL2 wrapper, UPDATE_ALL2 decomposition>

**Validation Plan**
<focused pytest, SQL validation, smoke tests, security review, promotion checks>

**Open Questions / Approval Needed**
<specific decisions for Chris>
```
