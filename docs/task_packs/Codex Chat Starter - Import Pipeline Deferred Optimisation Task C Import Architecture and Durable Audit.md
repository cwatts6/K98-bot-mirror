# Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Import Architecture and Durable Audit

Use this starter to begin Task C with audit/scope only. Do not implement until the audit confirms
the architecture slices and Chris approves the implementation plan.

## Copy/Paste Starter

```text
Begin Task C - Import Pipeline Deferred Optimisation: Import Architecture and Durable Audit.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C.md

Task A is complete and archived here:
C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md

Task B is complete and archived here:
C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md

Start with audit/scope only.

Confirmed delivered baseline:
- Full fallback imports work with Credit.
- Full fallback imports work with Conduct Score.
- Interim auto partial fallback imports work from the monitored Discord folder.
- Interim auto partial fallback preserves non-ASCII governor names.
- Partial fallback rows overlay the latest full KingdomScanData4 snapshot and preserve absent fields.
- Location import remains unchanged.
- shield_time_left is stored as ShieldEndsAtUnix / ShieldEndsAtUtc and visible on v_PlayerProfile.
- Task B uses raw text SQL staging plus explicit typed conversion for the Unicode-preserving fallback import path.

Task C scope to audit:
- broad stats_module.py service extraction for import orchestration
- durable batch audit outcome/status tracking
- upload route and worker boundaries
- command/route behavior impact, with no changes unless explicitly approved
- UPDATE_ALL2 responsibilities and whether to wrap, decompose, or replace in later approved slices

Explicitly out of scope for the first pass:
- code changes
- SQL changes
- Discord command changes
- upload route behavior changes
- durable audit implementation
- broad stats_module.py extraction implementation
- wholesale UPDATE_ALL2 replacement

Audit these before proposing implementation:
- C:\discord_file_downloader\stats_module.py
- C:\discord_file_downloader\services\fallback_import_schema.py
- C:\discord_file_downloader\upload_routes\fallback_queue_route.py
- C:\discord_file_downloader\bot_helpers.py
- C:\discord_file_downloader\update_all2_log_manager.py
- C:\discord_file_downloader\tests\test_fallback_import_schema.py
- C:\discord_file_downloader\tests\test_stats_module.py
- C:\K98-bot-SQL-Server\sql_schema\dbo.IMPORT_STAGING_PROC.StoredProcedure.sql
- C:\K98-bot-SQL-Server\sql_schema\dbo.IMPORT_STAGING_CSV.Table.sql
- raw fallback staging table introduced by Task B
- C:\K98-bot-SQL-Server\sql_schema\dbo.IMPORT_STAGING.Table.sql
- C:\K98-bot-SQL-Server\sql_schema\dbo.FallbackImportBatchControl.Table.sql
- C:\K98-bot-SQL-Server\sql_schema\dbo.UPDATE_ALL2.StoredProcedure.sql
- Task A and Task B SQL migrations

Required output from the audit:
- Scope summary.
- Current import flow.
- Affected Python and SQL files.
- Confirmed SQL object responsibilities.
- Recommended service/DAL and durable audit architecture.
- UPDATE_ALL2 strategy.
- PR-sized implementation slices.
- Risks and rollback.
- Tests to add/update.
- Open questions or approval needed.

Stop for approval before code or SQL changes.
```

## Expected First Response Shape

```markdown
**Scope Summary**
<what Task C covers and what remains out of scope for the first implementation slice>

**Current Import Flow**
<route, worker, stats_module, fallback schema, SQL procedures, metadata/audit>

**SQL Object Responsibilities**
<confirmed table/procedure shapes and ownership>

**Recommended Architecture**
<service/DAL split, durable audit model, UPDATE_ALL2 strategy>

**Implementation Slices**
<PR-sized sequence, each with risks and rollback>

**Validation Plan**
<focused tests, SQL validation, smoke tests, security review>

**Open Questions / Approval Needed**
<specific decisions for Chris>
```
