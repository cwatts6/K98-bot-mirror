# Codex Task Pack - Command Platform Phase 2 Validator And Inventory Tooling Enhancement

## 1. Task Header

- Task name: Command Platform Phase 2 - Validator And Inventory Tooling Enhancement
- Date: 2026-06-01
- Owner/context: Command Platform Audit & Optimisation Programme
- Task type: deferred optimisation batch / tooling refactor
- One-pass approved: no
- Status: implemented

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

Improve command-platform registration and inventory reporting before any further command grouping.

This phase should make the validator easier to trust by separating active authoritative command
paths from disabled secondary surfaces, detecting helper-attached grouped subcommands, and producing
clearer command-count and duplicate-risk output.

## 4. Background

Phase 1 was completed in PR 131 and pushed to production. It standardised active command
permission gates onto decorators while preserving the current command baseline:

```text
primary=82 grouped_subcommands_detected=21 secondary_cogs=5 secondary_subscribe=1 total_unique=82
```

Phase 2 preserved the active command count and active command paths while retiring the unused
disabled secondary command declarations. The validator now reports:

```text
primary=82 grouped_subcommands_detected=22 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=82
```

The next migration phases will move or group command paths. Before that work begins, the validator
and command inventory should clearly report what is active, what is disabled legacy surface, what
is grouped, and which warnings represent real startup-sync risk.

Known current issue:

```md
### Deferred Optimisation
- Area: `scripts/validate_command_registration.py`, `cogs/commands.py`, `subscribe.py`
- Type: cleanup
- Description: Duplicate command warnings do not distinguish disabled legacy surfaces from active startup-sync risk.
- Suggested Fix: Add active/disabled classification or retire disabled declarations after confirmation.
- Impact: medium
- Risk: low
- Dependencies: Confirm secondary cogs are never production-loaded.
```

## 5. Scope

### In Scope

- Enhance command registration validation reporting.
- Review and improve `commands/command_inventory.py` flattening/inventory helpers.
- Distinguish active authoritative command modules from disabled secondary command surfaces.
- Detect and report helper-attached grouped subcommands, especially `/prekvk import_history`.
- Preserve existing hard failure above Discord's 100 top-level command limit.
- Preserve existing warning at 90+ top-level commands.
- Keep the current command baseline unchanged.
- Add or update focused validator/inventory tests.
- Update command-platform docs if validator output or terminology changes.

### Out Of Scope

- Command grouping, renaming, retirement, or aliasing.
- Deleting disabled secondary cogs unless explicitly approved after the audit step.
- Production promotion or deployment.
- SQL schema changes.
- Permission-decorator changes beyond fixing a validator import problem if discovered.
- Business-logic or command-handler refactors.

Approved scope adjustment: after audit confirmed `cogs/commands.py` and root `subscribe.py` were
not loaded or required by startup, the user approved retiring them in this phase.

## 6. Audit Requirements

Map the current validator and inventory behavior:

- Active top-level command count.
- Grouped subcommand count.
- Secondary/disabled command surface detection.
- Duplicate command reporting.
- `/prekvk import_history` static detection gap.
- Exit-code behavior for clean, warning, and failure states.
- Existing test coverage and gaps.

Confirm whether secondary surfaces are production-loaded or intentionally disabled:

- `cogs/commands.py`
- `subscribe.py`
- any related startup/import gating

## 7. Architecture Targets

| Concern | Target |
|---|---|
| Command registration validator | `scripts/validate_command_registration.py` |
| Command flattening/inventory helpers | `commands/command_inventory.py` |
| Command lifecycle signature behavior | `core/command_lifecycle.py` and `bot_helpers.py`, only if needed |
| Tests | focused files under `tests/` |
| Documentation | command-platform docs and this task pack |

## 8. Implementation Requirements

- Do not change command names, paths, groups, options, descriptions, or versions.
- Do not change command registration count.
- Keep validator output deterministic and script-friendly.
- Make disabled-secondary warnings clearly distinct from active duplicate risks.
- Keep hard-fail behavior for active top-level command counts above 100.
- Keep warning behavior for active top-level command counts at 90+.
- Add tests for active vs disabled duplicate classification.
- Add tests for helper-attached grouped subcommand detection if implemented.
- Preserve existing command lifecycle behavior unless a bug is discovered and approved.

## 9. Suggested Test Plan

Run focused tests first:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_inventory.py tests\test_command_lifecycle.py
```

Add or update validator-specific tests as needed, likely:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py
```

Run validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

Before PR handoff, run or justify skipping:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security review is likely not required for documentation-only or pure reporting changes. Run
or justify skipping it if the implementation touches command permissions, Discord interaction
behavior, startup command sync behavior, file handling, or user-controlled input.

## 10. Acceptance Criteria

- [x] Validator output distinguishes active command surfaces from disabled secondary surfaces.
- [x] Duplicate warnings clearly identify active startup-sync risk versus disabled legacy code.
- [x] Helper-attached grouped subcommands are reported accurately or a precise deferred item is
      captured.
- [x] Current active command baseline remains unchanged.
- [x] Command registration paths remain unchanged.
- [x] Focused tests cover the new validator/inventory behavior.
- [x] Command-platform docs reflect the new validator terminology and output.
- [x] Any out-of-scope command-platform findings are captured structurally.

## 11. Required Delivery Output

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

## 12. PR Summary Template

```md
## Summary

- Enhanced command registration and inventory reporting for the command-platform roadmap.
- Preserved command paths and registration count.

## Changes

- <file/change>

## Tests

- <commands run>

## AI Review Gates

- Codex Security: <run/result or skipped with reason>

## Deferred Optimisations

- <none or structured items>

## Risk / Rollback

- Risk: validator/reporting regressions could obscure command-count or duplicate-surface risk.
- Rollback: revert the Phase 2 branch; no command path or SQL migration is involved.
```
