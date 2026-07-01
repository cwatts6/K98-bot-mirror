# Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 11 Import Audit Phase Timestamp Normalization

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C Slice 11 - Import Audit Phase Timestamp Normalization`
- Date: `2026-07-01`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation batch | import audit consistency | timestamp normalization`
- One-pass approved: `no`
- Status: `active next-slice task pack, starts with audit/scope and SQL implementation-boundary confirmation`

## 2. Required Reading

Before implementation, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/deferred_optimisations.md`

For SQL-facing validation, use the SQL source of truth:

`C:\K98-bot-SQL-Server`

## 3. Objective

Normalize generic import-audit phase timestamp handling so persisted `dbo.ImportAuditPhase` rows
cannot show `CompletedAtUtc` earlier than `StartedAtUtc`, while preserving current best-effort
audit behavior, phase status semantics, duration semantics, route/user-facing behavior, importer
contracts, and SQL object contracts unless a blocker is validated and approved.

This is a small audit-polish slice after fallback, player-location, Honor, PreKvK, weekly
activity, MGE results, inventory, KVK_ALL, and Rally Forts have all adopted generic durable import
audit.

## 4. Background

Task C Slice 9 production smoke testing for KVK_ALL showed some `ImportAuditPhase` rows where
`CompletedAtUtc` was one to three milliseconds earlier than `StartedAtUtc`, while terminal batch
state, counters, external correlation, phase duration, and route behavior were correct. The
condition appears to be a timestamp-boundary issue between caller-supplied `StartedAtUtc`,
SQL-owned completion timestamps, Python-side completion timestamps, and/or precision rounding.

Task C Slice 10 then completed Rally Forts generic durable audit adoption, so the generic
phase-heavy audit surface is now broad enough to normalize centrally without blocking route
adoption.

## 5. Completed Dependencies And Baseline

Delivered import audit baseline:

- Task C Slice 2 created `dbo.ImportAuditBatch`, `dbo.ImportAuditPhase`, SQL-owned audit writer
  procedures, and bot DAL/service wrappers.
- Task C Slice 3A normalized terminal batch-level `RowsInSource` through SQL-owned complete/fail
  procedures and bot wrappers.
- Task C Slices 3 through 10 adopted generic durable audit for player-location, Honor, PreKvK,
  weekly activity, MGE results, inventory, KVK_ALL, and Rally Forts.
- Rally Forts Slice 10 smoke testing was reported successful on `2026-07-01`.

Current known timestamp issue:

- `ImportAuditPhase.StartedAtUtc` can be caller-supplied by route/import helper code.
- `ImportAuditPhase.CompletedAtUtc` can be supplied by service callers or defaulted by SQL-owned
  writer behavior, depending on route/helper path.
- Millisecond-level clock/precision boundary differences can persist a completion timestamp
  before the recorded start timestamp.
- No user-visible import behavior, terminal counter, external correlation, or SQL import output
  defect has been reported from this timestamp polish item.

## 6. Source Deferred Item Promoted Into This Pack

### Deferred Optimisation
- Area: `services/import_audit_service.py`, `stats/dal/import_audit_dal.py`, import upload route audit phase callers, SQL repo `dbo.usp_ImportAudit_RecordPhase`
- Type: consistency
- Description: KVK_ALL production smoke testing for Task C Slice 9 showed some `ImportAuditPhase` rows with `CompletedAtUtc` one to three milliseconds earlier than `StartedAtUtc`, while `DurationMs`, terminal batch state, counters, and external correlation were correct. This appears to be timestamp-boundary polish in the generic phase writer/caller contract rather than a route behavior defect.
- Suggested Fix: Scope a small import-audit timestamp-normalization slice after Rally Forts adoption. Validate whether the mismatch comes from caller-supplied `StartedAtUtc`, SQL-owned completion time, or clock/rounding precision, then normalize the writer/service contract so persisted phase rows cannot have `CompletedAtUtc < StartedAtUtc` while preserving existing best-effort audit behavior and duration semantics.
- Impact: low
- Risk: medium
- Dependencies: Generic import audit objects from Task C Slice 2; phase-heavy route adoption through KVK_ALL and Rally Forts; SQL validation against `C:\K98-bot-SQL-Server`.

## 7. Scope

### In Scope

- Audit the generic import audit phase write path before implementation:
  - `services/import_audit_service.py`
  - `stats/dal/import_audit_dal.py`
  - `dbo.usp_ImportAudit_RecordPhase`
  - representative route/helper callers that supply `StartedAtUtc`, `CompletedAtUtc`, or
    `DurationMs`.
- Validate live SQL definitions for:
  - `dbo.ImportAuditPhase`
  - `dbo.usp_ImportAudit_RecordPhase`
  - related audit writer defaults and precision.
- Decide the safest normalization layer:
  - Python service/DAL normalization,
  - SQL writer normalization,
  - or a minimal combined contract if SQL validation proves it is necessary.
- Preserve best-effort audit behavior: audit failures must not fail imports.
- Preserve existing phase names, statuses, counters, details JSON, terminal batch writers, and
  external correlation contracts.
- Add focused tests proving persisted or submitted phase timestamps cannot have
  `CompletedAtUtc < StartedAtUtc`.
- Update deferred documentation after delivery.

### Out Of Scope

- Route-specific audit adoption changes for already delivered import families.
- Discord route UX, embed text, attachment handling, importer contracts, SQL import procedure
  behavior, exports, reports, dashboards, Google Sheets behavior, or user-facing behavior.
- Historical production data backfill or mutation of already written audit rows.
- New generic audit tables or new route-specific audit objects.
- Changing batch terminal writer semantics except where strictly necessary to keep phase
  timestamps consistent.
- `dbo.UPDATE_ALL2` wrapper/audit-output instrumentation.
- `dbo.IMPORT_STAGING_PROC` decomposition.
- `dbo.UPDATE_ALL2` decomposition.
- Residual `stats_module.py` cleanup.
- Legacy PreKvK SQL cleanup.
- Weekly cumulative view cleanup.
- Inventory view-orchestration extraction.

## 8. SQL Position To Validate

Validate these SQL objects against `C:\K98-bot-SQL-Server` before implementation:

- `dbo.ImportAuditPhase`
- `dbo.usp_ImportAudit_RecordPhase`
- `dbo.usp_ImportAudit_StartBatch`
- `dbo.usp_ImportAudit_CompleteBatch`
- `dbo.usp_ImportAudit_FailBatch`

Specific questions:

- What precision and defaults are used for `StartedAtUtc` and `CompletedAtUtc`?
- Does `dbo.usp_ImportAudit_RecordPhase` already default or coerce completion timestamps?
- Can the SQL writer safely set `CompletedAtUtc = StartedAtUtc` when a supplied/defaulted
  completion would otherwise be earlier?
- Would Python-side normalization be enough without SQL changes?
- Would a SQL change require a SQL repo PR/deployment before bot rollout?

## 9. Implementation Proposal

Start with audit/scope only and stop for approval. After approval, prefer the smallest safe fix:

1. Normalize in the generic service/DAL layer if the bot is the only source of inconsistent phase
   timestamps and SQL validation confirms no writer-side default can reintroduce the issue.
2. If SQL-owned defaults can still create `CompletedAtUtc < StartedAtUtc`, prepare a small SQL
   writer-procedure change in `C:\K98-bot-SQL-Server` that clamps completion to start time only
   when needed.
3. Keep route helpers unchanged unless a caller is demonstrably passing an invalid timestamp
   contract and the fix is a tiny local correction.

No route UX, import behavior, SQL import procedure, or historical audit data changes are expected.

## 10. Remaining Slice Map To Preserve

Do not lose these later slices:

1. **Later SQL Slice - `dbo.UPDATE_ALL2` Wrapper/Audit Outputs**
   - Add non-invasive audit output around downstream rebuild phases before procedure decomposition.
2. **Later SQL Slice - `dbo.IMPORT_STAGING_PROC` Responsibility Split**
   - Split only after durable audit evidence and compatibility wrappers are stable.
3. **Later SQL Slice - `dbo.UPDATE_ALL2` Decomposition**
   - Prepare only after wrapper/audit-output evidence identifies phase boundaries and hotspots.
4. **Later Python Slice - Residual `stats_module.py` Import Cleanup**
   - Continue shrinking `stats_module.py` once audit and SQL instrumentation are stable.
5. **Later SQL Cleanup - Legacy PreKvK Phase Object Retirement**
   - `dbo.PreKvk_Phases` retirement remains separate after live dependency review.
6. **Later SQL Cleanup - `dbo.vAllianceActivity_WeeklyCumulative` Review**
   - Confirm downstream/manual usage before correcting or retiring the view.
7. **Later Python Slice - Inventory View Orchestration Extraction**
   - Inventory lifecycle coordination cleanup remains separate now that Slice 8 audit adoption is
     delivered and smoke tested.

No new deferred optimisation was identified from Rally Forts smoke testing. The backup scheduling
`RowsOut=NULL` consistency issue found during production review was fixed in Slice 10 follow-up
commits before this pack was prepared.

## 11. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Confirm generic audit service/DAL/SQL writer boundaries before implementation. |
| `k98-sql-validation` | use | Validate audit table/procedure timestamp precision/defaults and SQL deployment impact. |
| `k98-test-selection` | use | Required before validation command selection. |
| `k98-deferred-optimisation-capture` | use | Required to update the import-audit backlog after delivery. |
| `k98-pr-review` | use before PR handoff | Confirm architecture, SQL alignment, tests, deferred tracking, and promotion safety. |
| `k98-promotion-check` | use before production promotion | Required if SQL or deployment sequencing is involved. |
| `codex-security:security-diff-scan` | likely skip if docs/tests-only; use if code/SQL changes touch SQL/data audit behavior | Timestamp writer changes touch SQL/data audit persistence, so run or explicitly justify. |

## 12. Files To Audit

Bot repo:

- `services/import_audit_service.py`
- `stats/dal/import_audit_dal.py`
- representative import audit helper services:
  - `services/kvk_all_import_audit_service.py`
  - `services/rally_forts_import_audit_service.py`
  - `services/weekly_activity_import_audit_service.py`
  - `services/prekvk_import_audit_service.py`
  - `services/honor_import_audit_service.py`
- representative route tests and audit tests:
  - `tests/test_import_audit_service.py`
  - `tests/test_import_audit_dal.py`
  - route-specific tests only as needed to prove no caller behavior changes.

SQL repo:

- `C:\K98-bot-SQL-Server\sql_schema\dbo.ImportAuditPhase.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_RecordPhase.StoredProcedure.sql`
- terminal writer procedure definitions only if the audit finds shared timestamp assumptions.

## 13. Required First Response

Use this shape and stop for approval before code or SQL changes:

```markdown
**Scope Summary**
<generic ImportAuditPhase timestamp normalization objective and why it follows Rally Forts closure>

**Current Audit Timestamp State**
<where StartedAtUtc, CompletedAtUtc, and DurationMs are supplied/defaulted today>

**SQL Position**
<validated SQL object precision/default/coercion behavior and whether a SQL repo change is needed>

**Implementation Boundary**
<Python-only vs SQL-writer vs combined proposal, with behavior-preservation notes>

**Remaining Slice Map**
<UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup, PreKvK legacy SQL cleanup, weekly cumulative view cleanup, inventory orchestration follow-up>

**Validation Plan**
<SQL validation, focused audit tests, broader checks, smoke expectations, Codex Security decision>

**Open Questions / Approval Needed**
<specific decisions for Chris>
```

## 14. Validation Plan

Baseline validators:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Likely focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_import_audit_service.py tests\test_import_audit_dal.py
```

If helper services or route callers are touched, include the relevant route-focused tests, for
example:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_all_upload_route.py tests\test_rally_forts_upload_route.py
```

Broader checks when generic audit wrappers or SQL-facing behavior are touched:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

SQL validation if a SQL writer change is proposed:

```powershell
cd C:\K98-bot-SQL-Server
.\deploy\Validate-SqlRepo.ps1
```

Smoke after deployment:

- Run one already-safe import smoke path or inspect a newly produced import-audit phase row.
- Confirm no phase row produced by the updated writer has `CompletedAtUtc < StartedAtUtc`.
- Confirm import route UX/output remains unchanged.
- Confirm batch terminal counters and external correlation remain unchanged.

## 15. Acceptance Criteria

- [ ] Current generic audit timestamp behavior is audited before implementation.
- [ ] SQL object precision/default/coercion behavior is validated against the SQL repo.
- [ ] First response stops for approval before code or SQL changes.
- [ ] The chosen fix prevents new `ImportAuditPhase` rows from persisting `CompletedAtUtc < StartedAtUtc`.
- [ ] `DurationMs` semantics are preserved or explicitly normalized with tests.
- [ ] Audit writes remain best-effort.
- [ ] No route UX/import behavior changes are introduced.
- [ ] No historical production audit rows are backfilled.
- [ ] Focused import-audit tests pass.
- [ ] Remaining SQL/Python cleanup items remain documented.
