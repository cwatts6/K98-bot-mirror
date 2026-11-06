# Codex Chat Starter - Command Platform Phase 2 Validator And Inventory Tooling Enhancement

Status: complete. Implemented in PR 132 (`codex/command-platform-phase-2-validator-inventory`),
smoke tested successfully, merged, and pushed to production. This starter remains as the execution
record for Phase 2 of the Command Platform Audit & Optimisation Programme.

Source programme documents:

- `docs/task_packs/Codex Task Pack - Command Platform Audit & Optimisation Programme.md`
- `docs/task_packs/Codex Task Pack - Command Platform Phase 2 Validator And Inventory Tooling Enhancement.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Phase 1, Permission Decorator Standardisation, was completed in PR 131
(`codex/command-platform-phase-1-permission-decorators`), smoke tested successfully, merged, and
pushed to production. Phase 2 then retired the unused disabled secondary command declarations and
updated validator reporting in PR 132, which was also smoke tested, merged, and pushed to
production. The current command-platform baseline is:

```text
primary=82 grouped_subcommands_detected=22 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=82
```

This next phase must not change user-facing command paths. Grouping resumes only after the
validator and inventory tooling report active, disabled, duplicate, and grouped command surfaces
clearly.

## Copy/Paste Starter

Codex, begin Phase 2 of the Command Platform Audit & Optimisation Programme: Validator And
Inventory Tooling Enhancement.

This follows the completed Phase 1 permission decorator standardisation PR:

- PR 131: `codex/command-platform-phase-1-permission-decorators`
- Result: smoke tested successfully, merged, pushed to production
- Command baseline preserved:

```text
primary=82 grouped_subcommands_detected=21 secondary_cogs=5 secondary_subscribe=1 total_unique=82
```

The objective for this phase is to improve command-platform registration and inventory reporting
before any further command grouping. The validator should make it clear which command surfaces are
active, which are disabled legacy declarations, which duplicates are true startup-sync risks, and
which grouped subcommands are attached through helpers.

## 1. Task Header

- Task name: Command Platform Phase 2 - Validator And Inventory Tooling Enhancement
- Date: 2026-06-01
- Owner/context: Command Platform Audit & Optimisation Programme
- Task type: deferred optimisation batch / tooling refactor
- One-pass approved: no

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
- `docs/task_packs/Codex Task Pack - Command Platform Audit & Optimisation Programme.md`
- `docs/task_packs/Codex Task Pack - Command Platform Phase 2 Validator And Inventory Tooling Enhancement.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Also review:

- `scripts/validate_command_registration.py`
- `commands/command_inventory.py`
- `core/command_lifecycle.py`
- `bot_helpers.py`
- `tests/test_command_registration_smoke.py`
- existing validator, command inventory, and command lifecycle tests

## 3. Objective

Improve command-platform registration and inventory reporting before further grouping.

This phase should:

- distinguish active authoritative command paths from disabled secondary surfaces
- detect helper-attached grouped subcommands, especially `/prekvk import_history`
- make duplicate warnings clear and actionable
- preserve the current command baseline and all command paths
- add focused tests for the reporting changes

Implemented result:

- retired unused disabled secondary declarations in `cogs/commands.py` and root `subscribe.py`
- detected `/prekvk import_history` as a helper-attached grouped subcommand
- preserved all active command paths and the active top-level command count
- updated validator output to report no active duplicate risks
- captured the stale `DL_bot.py` startup audit summary follow-up for Phase 3

## 4. Scope

### In Scope

- `scripts/validate_command_registration.py`
- `commands/command_inventory.py`
- focused command registration/inventory/lifecycle tests
- small command-platform documentation updates if output terminology changes

### Out Of Scope

- command grouping
- command renaming
- command retirement
- aliases or migration messaging
- permission-decorator changes
- SQL schema changes
- production promotion or deployment

## 5. Mandatory Workflow

1. Review/scope Phase 2 and stop for approval.
2. Map current validator and inventory behavior.
3. Confirm exact target reporting semantics.
4. Present implementation plan and stop for approval.
5. Implement approved tooling changes only.
6. Add/update focused tests.
7. Run validation.
8. Run or justify skipping Codex Security before PR handoff.

Proceed in one pass only if the user explicitly approves one-pass implementation in the new chat.

## 6. Acceptance Criteria

- [ ] Validator output distinguishes active command surfaces from disabled secondary surfaces.
- [ ] Duplicate warnings identify active startup-sync risk versus disabled legacy code.
- [ ] Helper-attached grouped subcommands are reported accurately or a precise deferred item is
      captured.
- [ ] Current command baseline remains unchanged.
- [ ] Command paths, groups, options, descriptions, and versions remain unchanged.
- [ ] Focused tests cover the new validator/inventory behavior.
- [ ] Command-platform docs reflect the new validator terminology and output.

## 7. Suggested Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_command_inventory.py tests\test_command_lifecycle.py
```

Before PR handoff, run or justify skipping:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security may be skipped with explicit rationale if the implementation is pure reporting and
does not touch permission checks, Discord interaction behavior, startup command sync behavior, file
handling, or user-controlled input.

## 8. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. SQL Changes
4. Helpers Reused
5. Refactor Findings
6. Test Plan And Results
7. AI Review Gates
8. Deployment / Rollback Notes
9. Deferred Optimisations
