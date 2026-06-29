# Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 3 Non-Fallback Audit Adoption

Status: archived after Task C Slice 3 delivery.

Task C Slice 3 was delivered in mirror PR #183 and production PR #491. Slice 3A and Slice 4 are
also complete and archived. Do not reuse this starter for new work. Use the active Slice 5 starter
for the next import audit slice:

`docs/task_packs/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 5 PreKvK Import Audit Adoption.md`

The copy/paste starter below is preserved as historical execution context and still references the
completed Slice 3 pack.

Use this starter to begin the next import pipeline slice. Start with audit/scope and
implementation-boundary confirmation; do not implement code or SQL until the boundary is approved.

## Copy/Paste Starter

```text
Begin Task C Slice 3 - Import Pipeline Deferred Optimisation: Non-Fallback Audit Adoption.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3 Non-Fallback Audit Adoption.md

Completed dependencies:
- Task A:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md
- Task B:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md
- Task C Slice 1:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Import Architecture and Service DAL Wrappers.md
- Task C Slice 2:
  C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation.md

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
- Task C Slice 2 added dbo.ImportAuditBatch, dbo.ImportAuditPhase, SQL-owned audit writer procedures, bot audit DAL/service wrappers, and fallback-first audit wiring correlated to dbo.FallbackImportBatchControl.
- Task C Slice 2 preserved route, command, queue, CSV/XLSX, staging, SQL procedure, and output behavior.
- Task C Slice 2 smoke testing on 2026-06-29 confirmed completed audit batches and phase rows for full fallback and interim auto partial fallback imports.

Start with audit/scope and implementation-boundary confirmation only.

Next-slice goal:
- Map current non-fallback import state surfaces for location, honor, PreKvK, weekly activity, MGE, and inventory imports.
- Confirm the generic audit taxonomy for ImportKind, SourceType, phase names, row counters, and ExternalBatchTable / ExternalBatchId correlation.
- Propose player location import as the first non-fallback audit wiring target.
- Reuse existing Task C Slice 2 SQL audit objects and stored procedures unless a gap is found and separately approved.
- Preserve route, command, queue, embed, file, staging, cache refresh, SQL procedure, and output behavior.
- Treat audit writes as best-effort.
- Decide whether batch-level RowsInSource normalization should be included now or captured as a later SQL/DAL follow-up.

Explicitly out of scope unless separately approved:
- Discord command changes.
- Upload route UX or embed text changes.
- Queue UX/embed behavior changes.
- Fallback import behavior changes.
- Wiring Honor, PreKvK, weekly activity, MGE, or inventory in the same implementation slice.
- Changing inventory's existing domain audit/history model except for generic audit correlation mapping.
- New SQL schema objects.
- Splitting dbo.IMPORT_STAGING_PROC.
- Adding the dbo.UPDATE_ALL2 wrapper/audit-output layer.
- Decomposing or replacing dbo.UPDATE_ALL2.
- Historical production data backfill.
- Operator UI/reporting dashboards for audit history.

Audit these before proposing implementation:
- C:\discord_file_downloader\services\import_audit_service.py
- C:\discord_file_downloader\stats\dal\import_audit_dal.py
- C:\discord_file_downloader\upload_routes\player_location_route.py
- C:\discord_file_downloader\services\location_import_service.py
- C:\discord_file_downloader\location_importer.py
- C:\discord_file_downloader\upload_routes\honor_route.py
- C:\discord_file_downloader\honor_importer.py
- C:\discord_file_downloader\upload_routes\prekvk_route.py
- C:\discord_file_downloader\prekvk_importer.py
- C:\discord_file_downloader\prekvk\dal\import_history_dal.py
- C:\discord_file_downloader\upload_routes\weekly_activity_route.py
- C:\discord_file_downloader\weekly_activity_importer.py
- C:\discord_file_downloader\upload_routes\mge_results_route.py
- C:\discord_file_downloader\mge\mge_results_import.py
- C:\discord_file_downloader\mge\dal\mge_results_dal.py
- C:\discord_file_downloader\upload_routes\inventory_route.py
- C:\discord_file_downloader\ui\views\inventory_views.py
- C:\discord_file_downloader\inventory\inventory_service.py
- C:\discord_file_downloader\inventory\dal\inventory_dal.py
- C:\discord_file_downloader\inventory\audit_service.py
- C:\discord_file_downloader\inventory\dal\inventory_audit_dal.py
- focused tests for the audited/wired routes and services.
- C:\K98-bot-SQL-Server SQL definitions for Task C Slice 2 audit tables and writer procedures.
- existing SQL/domain batch tables used by location, honor, PreKvK, weekly activity, MGE, and inventory paths.

Required first response:
- Scope summary.
- Current non-fallback import state surfaces.
- Audit taxonomy proposal for ImportKind, SourceType, phase names, row counters, and external batch correlation.
- Location-first implementation proposal and rollback plan.
- SQL position, including whether RowsInSource normalization needs a writer-procedure change.
- Remaining slices for Honor/PreKvK/weekly/MGE/inventory adoption, UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, and residual stats_module cleanup.
- Validation plan including SQL validation, focused tests, smoke tests, and Codex Security review.
- Open questions or approval needed.

Stop for approval before code or SQL changes.
```

## Expected First Response Shape

```markdown
**Scope Summary**
<non-fallback audit adoption objective, proposed location-first boundary, explicit exclusions>

**Current Non-Fallback Import State Surfaces**
<location/honor/PreKvK/weekly/MGE/inventory queue, file, staging, procedure, output, cache, domain batch, and error state>

**Audit Taxonomy Proposal**
<ImportKind/SourceType/phase names/external batch correlation/counter policy for each import kind>

**Location-First Implementation Proposal**
<exact files, service/DAL ownership, best-effort audit behavior, rollback plan>

**SQL Position**
<reuse existing Slice 2 objects, whether row-counter writer change is needed, SQL validation plan>

**Remaining Slices**
<Honor/PreKvK/weekly/MGE/inventory adoption, UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup>

**Validation Plan**
<focused pytest, SQL validation, smoke tests, security review, promotion checks>

**Open Questions / Approval Needed**
<specific decisions for Chris>
```
