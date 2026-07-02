# Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 12 UPDATE_ALL2 Wrapper Audit Outputs

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C Slice 12 - UPDATE_ALL2 Wrapper Audit Outputs`
- Date: `2026-07-01`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation batch | SQL instrumentation | import audit observability`
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
- `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 11 Import Audit Phase Timestamp Normalization.md`

For SQL-facing validation, use the SQL source of truth:

`C:\K98-bot-SQL-Server`

## 3. Objective

Scope and, after approval, implement the smallest safe non-invasive audit output around
`dbo.UPDATE_ALL2` downstream rebuild work so operators can see durable phase-level timing/status
markers for the fallback SQL rebuild step before any later procedure decomposition is considered.

The slice must preserve fallback import behavior, `SP_TaskStatus` polling behavior, SQL output
tables, player-visible behavior, batch counters, route/importer contracts, and existing
`fallback_update_all2` generic phase semantics unless a tiny, validated compatibility addition is
explicitly approved.

## 4. Background

Task C Slice 2 added generic durable import batch and phase audit tables. Slices 3 through 10
adopted the generic audit model across player-location, Honor, PreKvK, weekly activity, MGE
results, inventory, KVK_ALL, and Rally Forts. Slice 11 normalized generic phase timestamp handling
so new persisted `ImportAuditPhase` rows cannot show `CompletedAtUtc < StartedAtUtc`.

The remaining fallback observability gap is inside `dbo.UPDATE_ALL2`, which still runs as a broad
downstream rebuild procedure. Python currently observes completion through `SP_TaskStatus`
counter/status polling and records one generic `fallback_update_all2` phase. That confirms the SQL
step ran, but it does not explain which internal rebuild section failed or dominated runtime.

## 5. Source Deferred Item Promoted Into This Pack

### Deferred Optimisation
- Area: SQL repo `dbo.UPDATE_ALL2`, `update_all2_log_manager.py`, `stats/dal/fallback_import_dal.py`, `stats_module.py`
- Type: architecture
- Description: `dbo.UPDATE_ALL2` remains a broad downstream rebuild procedure, and Python currently observes completion through `SP_TaskStatus` counter/status polling. There is not yet a durable per-phase audit output that explains which downstream phase failed or dominated runtime.
- Suggested Fix: After Task C Slice 2's generic batch audit foundation is deployed, add a wrapper or non-invasive audit output around `dbo.UPDATE_ALL2` that records start/end, status, duration, and phase-level markers without changing output tables or player-visible behavior. Use the resulting baseline before deciding whether to split the procedure.
- Impact: high
- Risk: medium
- Dependencies: Task C Slice 2 generic import batch audit foundation; SQL validation in `C:\K98-bot-SQL-Server`; no wholesale `UPDATE_ALL2` replacement in this slice.

## 6. Completed Dependencies And Baseline

Confirmed delivered baseline:

- Full fallback imports work with `Credit`.
- Full fallback imports work with `Conduct Score`.
- Interim auto partial fallback imports work from the monitored Discord folder.
- Interim auto partial fallback preserves non-ASCII governor names.
- Partial fallback rows overlay the latest full `KingdomScanData4` snapshot and preserve absent
  fields.
- Location import remains unchanged for player-visible behavior.
- `shield_time_left` is stored as `ShieldEndsAtUnix` / `ShieldEndsAtUtc` and visible on
  `v_PlayerProfile`.
- Task C Slice 1 extracted fallback import orchestration into service/DAL wrappers while
  preserving current behavior.
- Task C Slice 2 added generic durable audit objects and fallback-first audit wiring correlated to
  `dbo.FallbackImportBatchControl`.
- Task C Slice 3 through Slice 10 adopted generic durable audit for the remaining import families.
- Task C Slice 11 normalized generic `ImportAuditPhase` timestamp handling in bot and SQL writer
  boundaries, then smoke testing confirmed new fallback and player-location phase rows no longer
  show `CompletedAtUtc < StartedAtUtc`.

## 7. Scope

### In Scope

- Audit current fallback `UPDATE_ALL2` execution and observation boundaries:
  - `stats_module.py`
  - `services/fallback_import_service.py`
  - `stats/dal/fallback_import_dal.py`
  - `update_all2_log_manager.py`
  - `services/import_audit_service.py`
  - `stats/dal/import_audit_dal.py`
  - SQL repo `dbo.UPDATE_ALL2`
  - SQL repo `SP_TaskStatus` / status objects used by current polling
- Validate whether the safest implementation is:
  - SQL-only internal audit/log output,
  - a compatibility wrapper around `dbo.UPDATE_ALL2`,
  - Python-side durable subphase projection from existing status/log data,
  - or a combined minimal approach.
- Preserve existing fallback import orchestration, queue behavior, route/user-facing behavior,
  current `fallback_update_all2` phase, counters, correlation to `dbo.FallbackImportBatchControl`,
  and `SP_TaskStatus` polling semantics.
- Prefer additive audit markers over procedure decomposition.
- Keep all new output best-effort or explicitly non-disruptive to imports.
- Add focused tests for any Python DAL/service wrapper behavior.
- Add SQL repo migration/source updates only after SQL validation confirms they are necessary.
- Update deferred documentation after delivery.

### Out Of Scope

- `dbo.UPDATE_ALL2` decomposition or wholesale rewrite.
- `dbo.IMPORT_STAGING_PROC` decomposition.
- Changing fallback route UX, embeds, attachment handling, queue behavior, file handling, or import
  worker contracts.
- Changing fallback import data output tables, dashboard/report semantics, or player-visible SQL
  results.
- Changing existing `SP_TaskStatus` behavior in a way that could break current polling.
- Historical production audit backfill.
- New generic audit schema objects unless separately approved.
- Route-specific audit adoption changes for already delivered import families.
- Residual `stats_module.py` cleanup beyond tiny integration needed for the wrapper/output.
- Legacy PreKvK SQL cleanup.
- Weekly cumulative view cleanup.
- Inventory view-orchestration extraction.

## 8. SQL Position To Validate

Validate these SQL objects against `C:\K98-bot-SQL-Server` before implementation:

- `dbo.UPDATE_ALL2`
- `dbo.IMPORT_STAGING_PROC`
- `dbo.SP_TaskStatus` or equivalent status objects used by current fallback polling
- downstream procedures called by `dbo.UPDATE_ALL2`
- existing tables written by `dbo.UPDATE_ALL2`
- generic audit objects if direct SQL audit writes are considered:
  - `dbo.ImportAuditBatch`
  - `dbo.ImportAuditPhase`
  - `dbo.usp_ImportAudit_RecordPhase`

Specific questions:

- What internal phases or procedure calls does `dbo.UPDATE_ALL2` already expose or imply?
- Can per-phase timing/status markers be added without changing output tables or current polling?
- Should audit markers be written to existing generic `ImportAuditPhase`, a current SQL log/status
  object, or a compatibility wrapper consumed by Python?
- Does SQL have enough context to correlate subphase output to the current import audit batch or
  only to `FallbackImportBatchControl` / status counters?
- Is a SQL repo change required before any bot repo change?

## 9. Implementation Boundary Proposal

Start with audit/scope only and stop for approval. After approval, prefer the smallest safe fix:

1. If existing SQL status/log data already has enough phase detail, add Python DAL/service mapping
   that records durable audit subphases without SQL changes.
2. If SQL needs to emit non-invasive markers, add a small SQL wrapper/output change that preserves
   `dbo.UPDATE_ALL2` behavior and current polling.
3. If direct writes to generic audit objects are proposed from SQL, validate the correlation
   contract carefully and keep it additive, idempotent enough for retries, and rollbackable.

Do not decompose `dbo.UPDATE_ALL2` in this slice. The goal is baseline evidence for later
decomposition, not decomposition itself.

## 10. Remaining Slice Map To Preserve

Do not lose these later slices:

1. **Later SQL Slice - `dbo.IMPORT_STAGING_PROC` Responsibility Split**
   - Split only after durable audit evidence and compatibility wrappers are stable.
2. **Later SQL Slice - `dbo.UPDATE_ALL2` Decomposition**
   - Prepare only after wrapper/audit-output evidence identifies phase boundaries and hotspots.
3. **Later Python Slice - Residual `stats_module.py` Import Cleanup**
   - Continue shrinking `stats_module.py` once audit and SQL instrumentation are stable.
4. **Later SQL Cleanup - Legacy PreKvK Phase Object Retirement**
   - `dbo.PreKvk_Phases` retirement remains separate after live dependency review.
5. **Later SQL Cleanup - `dbo.vAllianceActivity_WeeklyCumulative` Review**
   - Confirm downstream/manual usage before correcting or retiring the view.
6. **Later Python Slice - Inventory View Orchestration Extraction**
   - Inventory lifecycle coordination cleanup remains separate after Slice 8 audit adoption.

No new deferred optimisation was identified from Slice 11 smoke testing.

## 11. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Confirm fallback service/DAL/SQL writer boundaries before implementation. |
| `k98-sql-validation` | use | Required because this slice centers on SQL procedure instrumentation. |
| `k98-test-selection` | use | Required before validation command selection. |
| `k98-deferred-optimisation-capture` | use | Required to update resolved/remaining import-pipeline backlog after delivery. |
| `k98-pr-review` | use before PR handoff | Confirm architecture, SQL alignment, tests, deferred tracking, and promotion safety. |
| `k98-promotion-check` | use before production promotion | Required if SQL or deployment sequencing is involved. |
| `codex-security:security-diff-scan` | likely use or explicitly justify | SQL/data-access instrumentation touches audit persistence and fallback import observation. |

## 12. Required First Response

Use this shape and stop for approval before code or SQL changes:

```markdown
**Scope Summary**
<UPDATE_ALL2 wrapper/audit-output objective and why it follows Slice 11 timestamp normalization>

**Current UPDATE_ALL2 Observation State**
<how fallback currently starts, polls, logs, and audits the SQL step>

**SQL Position**
<validated UPDATE_ALL2/status/log/audit objects and whether a SQL repo change appears necessary>

**Implementation Boundary**
<Python-only vs SQL-writer/wrapper vs combined proposal, with behavior-preservation notes>

**Remaining Slice Map**
<IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup, PreKvK legacy SQL cleanup, weekly cumulative view cleanup, inventory orchestration follow-up>

**Validation Plan**
<SQL validation, focused tests, broader checks, smoke expectations, Codex Security decision>

**Open Questions / Approval Needed**
<specific decisions for Chris>
```

## 13. Validation Plan

Baseline validators:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Likely focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_fallback_import_dal.py tests\test_import_audit_service.py tests\test_import_audit_dal.py
```

If `stats_module.py`, fallback orchestration, or worker behavior is touched, include focused
fallback/service tests selected from `scripts/select_tests.py`.

Broader checks when SQL-facing fallback behavior is touched:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

SQL validation if a SQL writer/wrapper/status change is proposed:

```powershell
cd C:\K98-bot-SQL-Server
.\deploy\Validate-SqlRepo.ps1
```

Smoke after deployment:

- Run one full fallback smoke path or inspect a newly completed fallback import audit batch.
- Confirm the existing `fallback_update_all2` phase still completes and correlates as before.
- Confirm any new wrapper/audit-output markers are present, ordered, and non-disruptive.
- Confirm `SP_TaskStatus` polling still reaches the expected terminal state.
- Confirm fallback import user-visible output and batch counters remain unchanged.

## 14. Acceptance Criteria

- [ ] Current `UPDATE_ALL2` execution, polling, and audit behavior is audited before implementation.
- [ ] SQL object behavior is validated against the SQL repo.
- [ ] First response stops for approval before code or SQL changes.
- [ ] The chosen fix adds useful phase-level timing/status evidence without decomposing
      `dbo.UPDATE_ALL2`.
- [ ] Existing fallback import behavior, SQL outputs, counters, polling, and user-visible behavior
      are preserved.
- [ ] Audit writes remain best-effort or otherwise non-disruptive.
- [ ] No historical production audit rows are backfilled.
- [ ] Focused tests and SQL validation pass or any skips are justified.
- [ ] Remaining SQL/Python cleanup items remain documented.
