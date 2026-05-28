# DL_bot Upload Routing - Phase 2B PreKvK SQL Cleanup Audit Statement

We are starting Phase 2B after PR 98 (`dlbot-prekvk-upload-route`) was smoke tested successfully
and pushed to production.

Phase 2A delivered the PreKvK upload route extraction and left `DL_bot.py` as listener/delegation
glue for the PreKvK path. Phase 2B is a SQL cleanup audit and design task for legacy PreKvK phase
objects. It is not an implementation task unless the audit packet, cleanup direction, and
implementation plan are each approved.

## Goal

Audit whether legacy PreKvK SQL phase objects can be replaced, retired, or left in place safely now
that Python reporting uses direct stage columns from `dbo.PreKvk_Scores`.

## Required Reading

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
- `docs/task_packs/DL_bot Upload Routing - Phase 2 PreKvK Initiation Statement.md`
- `docs/task_packs/Codex Task Pack - DL_bot Upload Routing Deferred Optimisation Audit.md`
- `docs/task_packs/prekvk_schema_standardisation_task_pack.md`

Use `C:\K98-bot-SQL-Server` as the SQL source of truth.

## Skills To Use

- `k98-architecture-scope`
- `k98-sql-validation`
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review` before any PR handoff
- `k98-promotion-check` only before production promotion/deployment

## Phase 2B Scope

In scope:

- Read-only SQL dependency audit in `C:\K98-bot-SQL-Server`.
- Bot-code dependency audit for any references to legacy PreKvK phase objects.
- Identify whether each legacy object is:
  - still required
  - replaceable with direct-stage equivalents
  - safe to retire after dependency confirmation
  - unsafe or ambiguous and should remain deferred
- Recommend SQL cleanup direction and deployment order.
- Produce a PR-sized implementation plan only after the audit/scope packet is approved.
- Capture any out-of-scope findings using the Deferred Optimisation format.

Out of scope until separately approved:

- Dropping, renaming, or altering production SQL objects.
- Adding or changing bot-side PreKvK reporting UI.
- Changing `import_prekvk_bytes`, `upload_routes/prekvk_route.py`, or `DL_bot.py` upload behavior.
- Reworking `dbo.PreKvk_Scan`, `dbo.PreKvk_Scores`, `dbo.PreKvk_ImportHistory`, or
  `dbo.PreKvk_Scores_Ranked` except where the audit proves a cleanup dependency.
- Production deployment or bot-machine restart.

## Minimum SQL Objects To Audit

Legacy cleanup candidates:

- `dbo.PreKvk_Phases`
- `dbo.fn_PreKvkPhaseDelta`
- KVK-specific phase views such as `dbo.v_PreKvk13_Phase1`,
  `dbo.v_PreKvk13_Phase2`, and `dbo.v_PreKvk13_Phase3`
- Any other `v_PreKvk*_Phase*` view found in the SQL repo or live schema export

Direct-stage/current objects to cross-check:

- `dbo.PreKvk_Scan`
- `dbo.PreKvk_Scores`
- `dbo.PreKvk_ImportHistory`
- `dbo.PreKvk_Scores_Ranked`
- `dbo.fn_PreKvkLatestOverall`
- `dbo.sp_Build_Prekvk_And_Honor_Rankings`
- `dbo.sp_ExcelOutput_ByKVK`
- any `v_PreKvk*_All` or `v_PreKvk*_Overall` object referenced by legacy phase views

## Required Searches

Run or adapt these searches in the SQL repo:

```powershell
rg "PreKvk_Phases|fn_PreKvkPhaseDelta|v_PreKvk.*Phase" C:\K98-bot-SQL-Server
rg "CREATE.*PreKvk_Phases|CREATE.*fn_PreKvkPhaseDelta|CREATE.*v_PreKvk" C:\K98-bot-SQL-Server
rg "PreKvk_Scan|PreKvk_Scores|PreKvk_Scores_Ranked" C:\K98-bot-SQL-Server
rg "sp_Build_Prekvk_And_Honor_Rankings|sp_ExcelOutput_ByKVK|fn_PreKvkLatestOverall" C:\K98-bot-SQL-Server
rg "PreKvk_Phases|fn_PreKvkPhaseDelta|v_PreKvk.*Phase" C:\discord_file_downloader
```

If live production dependency checks are needed, propose the exact read-only SQL statements first
and stop for approval before running them.

## Step 1 Required Output

Phase 2B Step 1 must produce:

- Audit Summary
- Legacy Object Inventory
- Current Direct-Stage SQL Map
- Bot-Code Dependency Review
- SQL Dependency / Blast-Radius Review
- Cleanup Options
- Recommended Architecture / SQL Direction
- Recommended First PR Scope
- Test And Validation Strategy
- Deferred Optimisation Findings
- Approval Questions
- Explicit Stop Point

Do not write SQL or bot code during Step 1.

## Cleanup Options To Evaluate

Option A - leave legacy objects in place:

- Use when dependencies are ambiguous or still active.
- Update docs/deferred items with evidence and next check point.

Option B - replace with compatibility wrappers:

- Preserve object names but rewrite internals to use direct-stage columns.
- Lower immediate breakage risk for manual/report consumers, but still requires SQL review and
  deployment ordering.

Option C - retire/drop legacy objects:

- Only after proving no bot, SQL procedure, view, report, export, or manual workflow still depends
  on them.
- Requires rollback plan and production deployment approval.

## Validation Requirements

For audit/design-only work:

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

For implementation after approval, choose validation based on the selected cleanup option:

- SQL repo object-definition review.
- Read-only SQL dependency checks where approved.
- Focused tests covering PreKvK stats/reporting assumptions.
- Existing PreKvK importer and diagnostics tests where touched.
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- Full pytest if selector/risk warrants it.

## Acceptance Criteria

- Legacy phase-object dependencies are mapped with file/object evidence.
- SQL cleanup recommendation is evidence-based and separated from Phase 2A route work.
- No destructive SQL changes are made without approval.
- Any proposed SQL implementation includes deployment order and rollback notes.
- Bot behavior and PreKvK upload routing remain unchanged.
- Out-of-scope follow-ups are captured structurally.

## Explicit Stop Point

Stop after the Phase 2B audit/scope packet.

Do not implement SQL cleanup, alter SQL files, change bot code, or open a PR until the audit packet,
cleanup direction, and implementation plan have each been approved.
