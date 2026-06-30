# Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 8 Inventory Import Audit Adoption

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C Slice 8 - Inventory Import Audit Adoption`
- Date: `2026-06-30`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation batch | import audit adoption | inventory image ingestion`
- Depends on:
  - Task A, archived at `docs/task_packs/archive/Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md`
  - Task B, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md`
  - Task C Slice 1, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Import Architecture and Service DAL Wrappers.md`
  - Task C Slice 2, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation.md`
  - Task C Slice 3, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3 Non-Fallback Audit Adoption.md`
  - Task C Slice 3A, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3A Import Audit Batch Counter Normalization.md`
  - Task C Slice 4, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 4 Honor Import Audit Adoption.md`
  - Task C Slice 5, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 5 PreKvK Import Audit Adoption.md`
  - Task C Slice 6, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 6 Weekly Activity Import Audit Adoption.md`
  - Task C Slice 7, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 7 MGE Results Import Audit Adoption.md`
- One-pass approved: `no`
- Status: `active task pack, starts with audit/scope and SQL implementation-boundary confirmation`

## 2. Objective

Adopt the generic durable import audit model for the inventory image upload/import lifecycle only,
after MGE results adoption was delivered and smoke tested in Task C Slice 7.

This slice must start with audit/scope only. Confirm the current inventory upload route, command
session handoff, image analysis service, approval/correction/materials flows, DAL writes, SQL
domain batch tables, duplicate/cancel/reject/fail semantics, admin debug behavior, original upload
cleanup, telemetry/logging, and tests before proposing implementation. The expected
implementation is a behavior-preserving inventory audit wiring slice that reuses the existing
generic audit DAL/service wrappers and SQL-owned audit writer procedures.

## 3. Delivered Baseline

Confirmed delivered import baseline:

- Full fallback imports work with `Credit`.
- Full fallback imports work with `Conduct Score`.
- Interim auto partial fallback imports work from the monitored Discord folder.
- Interim auto partial fallback preserves non-ASCII governor names.
- Partial fallback rows overlay the latest full `KingdomScanData4` snapshot and preserve absent fields.
- Location import remains unchanged for player-visible behavior.
- `shield_time_left` is stored as `ShieldEndsAtUnix` / `ShieldEndsAtUtc` and visible on
  `v_PlayerProfile`.
- Task B uses raw text SQL staging plus explicit typed conversion for the Unicode-preserving
  fallback import path.
- Task C Slice 1 extracted fallback import orchestration into service/DAL wrappers while preserving
  behavior.
- Task C Slice 2 added `dbo.ImportAuditBatch`, `dbo.ImportAuditPhase`, SQL-owned audit writer
  procedures, bot audit DAL/service wrappers, and fallback-first audit wiring correlated to
  `dbo.FallbackImportBatchControl`.
- Task C Slice 3 mapped current non-fallback import state surfaces and wired player-location
  generic audit first.
- Task C Slice 3A added terminal writer support for optional `RowsInSource`, threaded it through
  bot wrappers, and smoke tested fallback/player-location normalization.
- Task C Slice 4 added Honor generic audit adoption and smoke tested Honor audit batch 7 on
  2026-06-29.
- Task C Slice 5 added PreKvK generic audit adoption and smoke tested accepted batch 8, duplicate
  batch 9, and rejected batch 10 on 2026-06-29.
- Task C Slice 6 added weekly activity generic audit adoption and smoke tested completed batches
  11 and 12 plus duplicate batch 13 on 2026-06-29.
- Task C Slice 7 added MGE results generic audit adoption, correlated accepted and post-domain-row
  failures to `dbo.MGE_ResultImports`, preserved manual overwrite behavior, and was reported smoke
  tested successfully on 2026-06-30.

Current inventory baseline to validate:

- `upload_routes/inventory_route.py` is a thin dispatcher for the configured inventory upload
  channel and delegates message handling to `ui.views.inventory_views`.
- `ui/views/inventory_views.py` owns the interaction-heavy upload-first, command-session,
  multi-governor selection, correction, additional-material-image, approve, reject, cancel,
  timeout, admin-debug, and original-upload-cleanup workflow.
- `inventory/inventory_service.py` owns pending session creation, upload-first batch creation,
  image analysis, additional material image analysis, approval, rejection, failure, cancellation,
  original upload deletion marking, and admin debug reference updates.
- `inventory/dal/inventory_dal.py` inserts and updates `dbo.InventoryImportBatch`, inserts
  resource and speedup rows, and approves resource/speedup batches in a transaction.
- `inventory/dal/inventory_material_dal.py` approves material batches and inserts material rows in
  a transaction.
- `inventory/audit_service.py` and `inventory/dal/inventory_audit_dal.py` already provide
  inventory's domain audit/history view over `dbo.InventoryImportBatch`; this slice must not
  replace or redesign that model.
- SQL validation found `dbo.InventoryImportBatch.ImportBatchID` is the stable identity for
  inventory import lifecycle correlation. Resource, speedup, and material inventory tables link
  back to that batch id.

## 4. Source Deferred Item Promoted Into This Pack

### Deferred Optimisation
- Area: `upload_routes/inventory_route.py`, `ui/views/inventory_views.py`, `inventory/inventory_service.py`, `inventory/dal/inventory_dal.py`, `inventory/dal/inventory_material_dal.py`, `services/import_audit_service.py`, `stats/dal/import_audit_dal.py`, SQL repo inventory objects
- Type: consistency
- Description: Task C Slice 3 mapped inventory as the remaining non-fallback import family, Task C Slice 3A normalized the generic audit batch source-row counter, and Slices 4 through 7 delivered Honor, PreKvK, weekly activity, and MGE results generic audit adoption. Inventory still does not create generic `ImportAuditBatch` / `ImportAuditPhase` rows, so operators must use the inventory-specific domain audit/history model and logs rather than the shared durable import audit model for cross-import correlation.
- Suggested Fix: Adopt generic audit for inventory only, using service/DAL-owned best-effort audit wrappers. Validate `dbo.InventoryImportBatch.ImportBatchID` as the external correlation id for outcomes after a domain batch exists. Preserve inventory upload route UX, `/inventory import` behavior, image-analysis workflow, correction/modals, additional-material flow, approval/reject/cancel/timeout behavior, admin debug behavior, original upload deletion behavior, inventory's domain audit/history model, and SQL table behavior.
- Impact: medium
- Risk: medium
- Dependencies: Task C Slice 2 audit foundation; Task C Slice 3 non-fallback surface map; Task C Slice 3A `RowsInSource` terminal writer normalization; Task C Slice 4 Honor audit adoption; Task C Slice 5 PreKvK audit adoption; Task C Slice 6 weekly activity audit adoption; Task C Slice 7 MGE results audit adoption; SQL validation against `C:\K98-bot-SQL-Server`.

## 5. Proposed Implementation Boundary

### In Scope

- Audit current inventory state surfaces:
  - upload route and configured channel gating;
  - command-session and upload-first entry points;
  - supported image attachment validation and attachment read failures;
  - governor resolution, multi-governor selection, and active material-session routing;
  - `InventoryImagePayload` creation;
  - `create_pending_command_session` and `create_upload_first_batch` behavior;
  - resource/speedup and material image analysis;
  - duplicate-day guard behavior for non-admin approved imports;
  - review message, correction modal, approval, rejection, cancel, timeout, and additional-material
    continuation behavior;
  - SQL ingest on approval for resources, speedups, and materials;
  - admin debug embed/file/reference update behavior;
  - original upload deletion marker behavior;
  - existing inventory domain audit/history services;
  - telemetry/logging;
  - existing inventory route, view, service, DAL, parsing, reporting, and schema-contract tests.
- Validate SQL inventory objects against `C:\K98-bot-SQL-Server`, including:
  - `dbo.InventoryImportBatch`
  - `dbo.GovernorResourceInventory`
  - `dbo.GovernorSpeedupInventory`
  - `dbo.GovernorMaterialInventory`
  - indexes and constraints on batch status, flow type, import type, and active/approved duplicate
    guards.
- Reuse existing generic audit objects and bot wrappers from Task C Slice 2 / Slice 3A.
- Propose inventory audit taxonomy:
  - likely `ImportKind = inventory`;
  - likely source types to validate: `discord_upload_image` and/or `discord_command_image`;
  - likely phases: `inventory_image_read`, `inventory_vision_analysis`,
    `inventory_review_transition`, `inventory_approval_sql_ingest`, `inventory_admin_debug_post`,
    `inventory_original_upload_cleanup`, and `inventory_material_merge` where applicable;
  - external correlation candidate after domain batch creation:
    `ExternalBatchTable = dbo.InventoryImportBatch`, `ExternalBatchId = <ImportBatchID>`;
  - pre-batch failures and rejections should remain uncorrelated unless validation finds a stable
    domain batch id that can be propagated without changing behavior.
- Implement inventory generic audit wiring only after approval.
- Preserve existing inventory route, command-session, file/image, parse/vision, approval,
  duplicate, cancel/reject/fail, admin-debug, cleanup, SQL ingest, report/export, telemetry/logging,
  and user-facing behavior.
- Keep audit writes best-effort.
- Update tests and deferred documentation after delivery.

### Out Of Scope

- Discord command behavior changes.
- Upload route UX or embed text changes.
- Button, modal, selector, correction, or review-message UX changes.
- Fallback, player-location, Honor, PreKvK, weekly activity, or MGE results behavior changes.
- Replacing inventory's domain audit/history model.
- Redesigning inventory OCR/vision parsing or inventory report/export output.
- Changing inventory SQL table schemas, constraints, reporting semantics, output files, or channel
  gating.
- New SQL schema tables or new generic audit objects unless audit finds a blocker and approval is
  granted.
- Replacing or redesigning the inventory import workflow.
- Adding the `dbo.UPDATE_ALL2` wrapper/audit-output layer.
- Splitting `dbo.IMPORT_STAGING_PROC`.
- Decomposing or replacing `dbo.UPDATE_ALL2`.
- Historical production data backfill.
- Operator UI/reporting dashboards for audit history.

## 6. Remaining Import Audit And Cleanup Slices To Preserve

Do not lose these later slices:

1. **Later SQL Slice - `dbo.UPDATE_ALL2` Wrapper/Audit Outputs**
   - Add non-invasive audit output around downstream rebuild phases before attempting procedure
     decomposition.
2. **Later SQL Slice - `dbo.IMPORT_STAGING_PROC` Responsibility Split**
   - Split only after durable audit evidence and compatibility wrappers are stable.
3. **Later SQL Slice - `dbo.UPDATE_ALL2` Decomposition**
   - Prepare only after wrapper/audit-output evidence identifies phase boundaries and hotspots.
4. **Later Python Slice - Residual `stats_module.py` Import Cleanup**
   - Continue shrinking `stats_module.py` into service/DAL boundaries once audit and SQL
     instrumentation are stable.
5. **Later SQL Cleanup - Legacy PreKvK Phase Object Retirement**
   - `dbo.PreKvk_Phases` retirement remains a separate SQL cleanup after live dependencies and
     production cycles are reviewed.
6. **Later SQL Cleanup - `dbo.vAllianceActivity_WeeklyCumulative` Review**
   - Confirm downstream/manual usage before correcting or retiring the currently suspicious weekly
     activity cumulative reporting view through the SQL repo process.
7. **Potential Later Python Slice - Inventory View Orchestration Extraction**
   - Inventory interaction lifecycle coordination remains intentionally view-heavy. If Slice 8
     finds audit wiring would be cleaner behind narrower service helpers, capture that as a
     follow-up and preserve current user-facing behavior in Slice 8.

## 7. Required Reading

Before audit work, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/deferred_optimisations.md`
- archived Task C Slice 2, Slice 3, Slice 3A, Slice 4, Slice 5, Slice 6, and Slice 7 task packs

SQL references:

- `C:\K98-bot-SQL-Server\sql_schema\dbo.ImportAuditBatch.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.ImportAuditPhase.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_StartBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_RecordPhase.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_CompleteBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_FailBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.InventoryImportBatch.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.GovernorResourceInventory.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.GovernorSpeedupInventory.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.GovernorMaterialInventory.Table.sql`

## 8. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Confirm route/view/service/DAL/SQL boundaries before implementation. |
| `k98-sql-validation` | use | Validate inventory SQL objects, status semantics, duplicate guards, and generic audit writer compatibility. |
| `k98-test-selection` | use | Required before validation command selection. |
| `k98-deferred-optimisation-capture` | use | Required to update the remaining import-audit backlog after delivery. |
| `k98-pr-review` | use before PR handoff | Confirm architecture, SQL alignment, tests, deferred tracking, and promotion safety. |
| `k98-promotion-check` | use before production promotion | Required if SQL/config/deployment sequencing is involved. |
| `codex-security:security-diff-scan` | use or justify skip | Discord interactions, file/image handling, SQL/data access, user-controlled input, and audit persistence are security-sensitive surfaces. |

## 9. Files And SQL Objects To Audit

Bot repo:

- `upload_routes/inventory_route.py`
- `ui/views/inventory_views.py`
- `inventory/inventory_service.py`
- `inventory/dal/inventory_dal.py`
- `inventory/dal/inventory_material_dal.py`
- `inventory/audit_service.py`
- `inventory/dal/inventory_audit_dal.py`
- `services/import_audit_service.py`
- `stats/dal/import_audit_dal.py`
- `tests/test_inventory_upload_route.py`
- `tests/test_inventory_upload_flow.py`
- `tests/test_inventory_service.py`
- `tests/test_inventory_dal.py`
- `tests/test_inventory_audit_service.py`
- `tests/test_inventory_views.py`
- `tests/test_inventory_schema_contract.py`
- `tests/test_inventory_parsing.py`
- `tests/test_inventory_reporting_service.py`
- `tests/test_import_audit_service.py`
- `tests/test_import_audit_dal.py`

SQL repo:

- generic import audit tables and writer procedures
- inventory batch, resource, speedup, material, status/index/constraint, and audit/history objects
  used by the route/service/DAL path

## 10. Required First Response

Use this shape and stop for approval before code or SQL changes:

```markdown
**Scope Summary**
<inventory-only generic audit adoption objective and explicit no-behavior-change boundary>

**Current Inventory Import State**
<route, command-session handoff, image read/vision analysis, batch creation, review/approval/correction/materials/cancel/fail outcomes, SQL ingest, domain audit/history, telemetry/logging, tests>

**SQL Position**
<validated inventory objects, generic audit writer compatibility, batch correlation proposal, pre-batch/failed/cancelled/rejected terminal status policy>

**Audit Taxonomy Proposal**
<ImportKind, SourceType, phase names, counters, details JSON, terminal status policy>

**Implementation Proposal**
<files to change, service/DAL ownership, best-effort behavior, view/route contract preservation, rollback plan>

**Remaining Slice Map**
<UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup, PreKvK legacy SQL cleanup, weekly cumulative view cleanup, any inventory orchestration follow-up>

**Validation Plan**
<SQL validation, focused tests, broad checks, smoke tests, Codex Security review>

**Open Questions / Approval Needed**
<specific decisions for Chris>
```

## 11. Validation Plan

Baseline commands:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Likely focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_upload_route.py tests\test_inventory_upload_flow.py tests\test_inventory_service.py tests\test_inventory_dal.py tests\test_inventory_audit_service.py tests\test_inventory_views.py tests\test_inventory_schema_contract.py tests\test_import_audit_service.py tests\test_import_audit_dal.py
```

Additional inventory checks when view/service behavior is touched:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_parsing.py tests\test_inventory_reporting_service.py
```

Broad checks when shared audit helpers or upload behavior are touched:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

SQL validation if SQL objects or assumptions are changed:

```powershell
cd C:\K98-bot-SQL-Server
.\deploy\Validate-SqlRepo.ps1
```

Manual smoke after deployment:

- Run an operationally safe inventory image upload/import path and confirm the existing review,
  approval, and success behavior remains unchanged.
- Confirm one completed `inventory` audit batch correlated to
  `dbo.InventoryImportBatch.ImportBatchID`.
- If operationally safe, smoke a material continuation image and confirm the existing materials
  behavior plus generic audit phase markers.
- Exercise cancel/reject/invalid-image/vision-failure paths in tests unless an operator explicitly
  approves production negative-path smoke.

## 12. Acceptance Criteria

- [ ] Inventory route/view/service/DAL/SQL state surfaces are audited before implementation.
- [ ] SQL object names, columns, statuses, constraints, indexes, and domain batch ids are validated
  against the SQL repo.
- [ ] First response stops for approval before code or SQL changes.
- [ ] Inventory generic audit wiring is implemented only after approval.
- [ ] Existing inventory route, command-session, upload-first, image analysis, correction,
  additional-material, approval, duplicate, reject/cancel/fail, admin-debug, original-upload
  cleanup, SQL ingest, report/export, telemetry/logging, and user-facing behavior are preserved.
- [ ] Inventory's existing domain audit/history model is preserved.
- [ ] Audit writes remain best-effort.
- [ ] Batch-level counters use the normalized Slice 3A terminal writer contract where applicable.
- [ ] Focused inventory/import-audit tests pass.
- [ ] Remaining SQL/Python cleanup items remain documented.
