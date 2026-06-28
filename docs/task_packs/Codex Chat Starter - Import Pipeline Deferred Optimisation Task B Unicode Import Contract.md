# Codex Chat Starter - Import Pipeline Deferred Optimisation Task B Unicode Import Contract

Status: active starter for the next import pipeline deferred optimisation slice.

Use this starter to begin Task B with audit/scope only. Do not implement until the audit confirms
the selected Unicode-preserving import design and Chris approves the implementation plan.

## Copy/Paste Starter

```text
Begin Task B - Import Pipeline Deferred Optimisation: Unicode Import Contract.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md

Task A is complete and archived here:
C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md

Start with audit/scope only.

Confirmed Task A baseline:
- Full fallback imports work with Credit.
- Full fallback imports work with Conduct Score.
- Interim auto partial fallback imports work from the same monitored Discord folder.
- Partial fallback rows overlay the latest full KingdomScanData4 snapshot and preserve absent fields.
- Location import works.
- shield_time_left is stored as ShieldEndsAtUnix / ShieldEndsAtUtc and visible on v_PlayerProfile.
- The current Task A hotfix uses ASCII-safe text formatting for the SQL bulk CSV path to avoid SQL Server BULK INSERT failures on padded/non-ASCII Name values.

Task B first-slice goal:
Replace the temporary ASCII-safe fallback CSV workaround with a Unicode-preserving SQL import path, while preserving all Task A behavior.

Audit these before proposing implementation:
- C:\discord_file_downloader\stats_module.py
- C:\discord_file_downloader\services\fallback_import_schema.py
- C:\discord_file_downloader\tests\test_fallback_import_schema.py
- C:\discord_file_downloader\tests\test_stats_module.py
- C:\K98-bot-SQL-Server\sql_schema\dbo.IMPORT_STAGING_CSV.Table.sql
- C:\K98-bot-SQL-Server\sql_schema\dbo.IMPORT_STAGING_PROC.StoredProcedure.sql
- C:\K98-bot-SQL-Server\sql_schema\dbo.UPDATE_ALL2.StoredProcedure.sql
- C:\K98-bot-SQL-Server\sql_schema\dbo.FallbackImportBatchControl.Table.sql if present
- SQL migrations related to Task A fallback imports

Evaluate these Unicode-preserving options:
1. UTF-16/widechar bulk import.
2. Raw text staging table plus explicit typed conversion.
3. Parameterized/batched pyodbc loader.

Prefer the smallest safe design. Do not broaden into service extraction or durable batch audit unless the selected Unicode-safe import path requires it. Capture any remaining import architecture cleanup as deferred follow-up.

Required output from the audit:
- Scope summary.
- Affected Python and SQL files.
- Confirmed SQL object shapes.
- Recommended Unicode import option and why.
- Risks and rollback.
- Tests to add/update.
- Exact implementation plan.
- Open questions or approval needed.

Stop for approval before code or SQL changes.
```

## Expected First Response Shape

```markdown
**Scope Summary**
<what Task B will change and what remains out of scope>

**Current Task A Contract**
<evidence from code and SQL repo>

**SQL / Import Options**
<widechar vs raw staging vs pyodbc batch, with recommendation>

**Recommended First Slice**
<smallest safe implementation plan>

**Validation Plan**
<bot tests, SQL repo validation, smoke tests>

**Approval Needed**
<specific decision for Chris>
```
