# Codex Chat Starter - Command Platform Phase 6 Canonical Command Documentation

Archived starter for completed Command Platform Phase 6.

Phase 6 was delivered in PR 137 (`codex/command-platform-phase-6-canonical-docs`), merged, marked
complete, and pushed to production on 2026-06-02. Use the Phase 7 starter for the next and final
command-platform programme phase.

Historical starter content follows.

Source programme documents:

- `docs/task_packs/Codex Task Pack - Command Platform Audit & Optimisation Programme.md`
- `docs/task_packs/Codex Task Pack - Command Platform Phase 6 Canonical Command Documentation.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Phase 5A was completed in PR 136 (`codex/command-platform-phase-5a-admin-grouping`), smoke tested
successfully, merged, and pushed to production on 2026-06-02.

Current validator baseline:

```text
primary=39 grouped_subcommands_detected=76 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=39
```

## Copy/Paste Starter

Codex, begin Command Platform Phase 6: Canonical Command Documentation.

This follows the completed Phase 5A implementation PR:

- PR 136: `codex/command-platform-phase-5a-admin-grouping`
- Result: smoke tested successfully, merged, and pushed to production
- Current validator baseline:

```text
primary=39 grouped_subcommands_detected=76 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=39
```

The objective for this phase is documentation and governance preparation only. Create the
canonical maintained command reference after Phase 5A path changes, and update stale command docs
and smoke references. Do not move, rename, retire, or add commands in Phase 6.

## 1. Task Header

- Task name: Command Platform Phase 6 - Canonical Command Documentation
- Date: 2026-06-02
- Owner/context: Command Platform Audit & Optimisation Programme
- Task type: documentation / governance preparation
- One-pass approved: no

## 2. Required Reading

Before implementation or documentation changes, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/task_packs/Codex Task Pack - Command Platform Audit & Optimisation Programme.md`
- `docs/task_packs/Codex Task Pack - Command Platform Phase 6 Canonical Command Documentation.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Also review:

- `commands/command_inventory.py`
- `scripts/validate_command_registration.py`
- command registration, inventory, lifecycle, and validator tests
- existing command docs and smoke references for every active command domain

## 3. Objective

Create or update a canonical command reference that documents every active command's current path,
owner module, permission model, response visibility, grouping/top-level status, version/usage
tracking expectations, and migration/disposition notes.

## 4. Out Of Scope

Do not move, rename, retire, or add slash commands.

Also out of scope:

- player self-service workflow redesign
- public calendar/KVK calendar UX redesign
- SQL schema changes
- permission behavior changes
- runtime command implementation changes
- production promotion or deployment

## 5. Mandatory Workflow

1. Review/scope Phase 6 and stop for approval.
2. Inventory existing command docs and smoke references.
3. Present the canonical command reference shape and stop for approval.
4. Implement documentation updates only.
5. Run focused validation.
6. Open a ready-for-review PR against `K98-bot-mirror`.

## 6. Suggested Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_inventory.py tests\test_command_registration_smoke.py
.\.venv\Scripts\python.exe -m pre_commit run -a
```

## 7. Required Delivery Output

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
