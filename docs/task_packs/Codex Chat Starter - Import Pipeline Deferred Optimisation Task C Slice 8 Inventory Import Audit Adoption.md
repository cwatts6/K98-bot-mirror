# Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 8 Inventory Import Audit Adoption

Use this starter to begin Task C Slice 8 after Task C Slice 7 is merged, deployed, and smoke
tested.

```markdown
# Files mentioned by the user:

## Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 8 Inventory Import Audit Adoption.md: C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 8 Inventory Import Audit Adoption.md

## My request for Codex:
Begin Task C Slice 8 - Import Pipeline Deferred Optimisation: Inventory Import Audit Adoption.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 8 Inventory Import Audit Adoption.md

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
- Task C Slice 7 adopted generic durable audit for MGE results uploads and manual/overwrite imports through the importer, preserved MGE route/import behavior, correlated accepted imports to dbo.MGE_ResultImports/<ImportId>, left duplicate/pre-domain outcomes uncorrelated, and was reported smoke tested successfully on 2026-06-30.

Start with audit/scope and SQL implementation-boundary confirmation only.

Next-slice goal:
- Adopt generic durable import audit for the inventory image upload/import lifecycle only.
- Validate the current inventory upload route, command-session handoff, image read/vision analysis, batch creation, review/approval/correction/materials/cancel/fail outcomes, SQL ingest, domain audit/history, telemetry/logging, and tests.
- Validate accepted/import-lifecycle external batch correlation for dbo.InventoryImportBatch, expected as ExternalBatchTable=dbo.InventoryImportBatch and ExternalBatchId=<ImportBatchID>, unless SQL validation finds a better stable contract.
- Validate whether pre-batch failures should remain uncorrelated.
- Validate how cancelled, rejected, failed, timeout, and additional-material outcomes should map to generic audit terminal status without changing inventory behavior.
- Reuse existing Task C Slice 2 / Slice 3A audit DAL/service wrappers and SQL-owned writer procedures.
- Preserve inventory upload route UX, /inventory import behavior, image-analysis workflow, correction/modals, additional-material flow, approval/reject/cancel/timeout behavior, admin debug behavior, original upload deletion behavior, inventory's domain audit/history model, SQL outputs, telemetry/logging, and user-facing behavior.
- Keep audit writes best-effort.
- Avoid new SQL schema objects unless validation finds a blocker and approval is granted.

Explicitly out of scope unless separately approved:
- Discord command behavior changes.
- Upload route UX or embed text changes.
- Button, modal, selector, correction, or review-message UX changes.
- Fallback, player-location, Honor, PreKvK, weekly activity, or MGE results behavior changes.
- Replacing inventory's domain audit/history model.
- Redesigning inventory OCR/vision parsing or inventory report/export output.
- Changing inventory SQL table schemas, constraints, reporting semantics, output files, or channel gating.
- New SQL schema tables or new generic audit objects.
- Replacing or redesigning the inventory import workflow.
- Adding the dbo.UPDATE_ALL2 wrapper/audit-output layer.
- Splitting dbo.IMPORT_STAGING_PROC.
- Decomposing or replacing dbo.UPDATE_ALL2.
- Historical production data backfill.
- Operator UI/reporting dashboards for audit history.

Audit these before proposing implementation:
- C:\discord_file_downloader\upload_routes\inventory_route.py
- C:\discord_file_downloader\ui\views\inventory_views.py
- C:\discord_file_downloader\inventory\inventory_service.py
- C:\discord_file_downloader\inventory\dal\inventory_dal.py
- C:\discord_file_downloader\inventory\dal\inventory_material_dal.py
- C:\discord_file_downloader\inventory\audit_service.py
- C:\discord_file_downloader\inventory\dal\inventory_audit_dal.py
- C:\discord_file_downloader\services\import_audit_service.py
- C:\discord_file_downloader\stats\dal\import_audit_dal.py
- C:\discord_file_downloader\tests\test_inventory_upload_route.py
- C:\discord_file_downloader\tests\test_inventory_upload_flow.py
- C:\discord_file_downloader\tests\test_inventory_service.py
- C:\discord_file_downloader\tests\test_inventory_dal.py
- C:\discord_file_downloader\tests\test_inventory_audit_service.py
- C:\discord_file_downloader\tests\test_inventory_views.py
- C:\discord_file_downloader\tests\test_inventory_schema_contract.py
- C:\discord_file_downloader\tests\test_inventory_parsing.py
- C:\discord_file_downloader\tests\test_inventory_reporting_service.py
- C:\discord_file_downloader\tests\test_import_audit_service.py
- C:\discord_file_downloader\tests\test_import_audit_dal.py
- C:\K98-bot-SQL-Server SQL definitions for generic audit objects and inventory batch/resource/speedup/material/audit/history objects.
- C:\K98-bot-SQL-Server migrations README and SQL deployment/promotion guardrails if SQL changes are proposed.

Required first response:
- Scope summary.
- Current inventory import state.
- SQL position and external batch correlation proposal.
- Audit taxonomy proposal.
- Implementation proposal.
- Remaining slice map for UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup, PreKvK legacy SQL cleanup, weekly cumulative view cleanup, and any inventory orchestration follow-up.
- Validation plan including SQL validation, focused tests, broad checks, smoke tests, and Codex Security review.
- Open questions or approval needed.

Stop for approval before code or SQL changes.
```
