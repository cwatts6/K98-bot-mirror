# Codex Task Pack - Command Platform Phase 6 Canonical Command Documentation

## 1. Task Header

- Task name: Command Platform Phase 6 - Canonical Command Documentation
- Date: 2026-06-02
- Owner/context: Command Platform Audit & Optimisation Programme
- Task type: documentation / governance preparation
- One-pass approved: no
- Status: complete. Delivered in PR 137 (`codex/command-platform-phase-6-canonical-docs`),
  merged, marked complete, and pushed to production on 2026-06-02.

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
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Also review:

- `commands/command_inventory.py`
- `scripts/validate_command_registration.py`
- command registration, inventory, lifecycle, and validator tests
- current command docs and smoke references for Ark, ops, registry, stats/KVK, inventory,
  calendar/events, subscriptions, CrystalTech, honor, location, activity, MGE, PreKvK, and
  telemetry commands

## 3. Objective

Create a canonical maintained command reference after the Phase 5A path migrations.

The reference should make command ownership, path status, permissions, response visibility,
versioning, usage tracking, and migration/disposition discoverable without requiring maintainers
to inspect every command module.

Completion note: Phase 6 created `docs/reference/canonical_command_reference.md`, updated active
command docs and smoke references after Phase 5A path changes, archived completed Phase 5A
task-pack records, and set Phase 7 governance/CI guardrails as the final command-platform phase.

## 4. Background

Phase 5A was completed in PR 136 (`codex/command-platform-phase-5a-admin-grouping`), smoke tested
successfully, merged, and pushed to production on 2026-06-02.

Current validator baseline:

```text
primary=39 grouped_subcommands_detected=76 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=39
```

Grouped command summary:

| Group | Statically detected subcommands |
|---|---:|
| `/activity` | 1 |
| `/ark` | 14 |
| `/crystaltech` | 3 |
| `/events` | 2 |
| `/honor` | 1 |
| `/inventory` | 2 |
| `/kvk` | 7 |
| `/location` | 2 |
| `/mge` | 6 |
| `/ops` | 25 |
| `/prekvk` | 2 |
| `/registry` | 7 |
| `/stats` | 1 |
| `/subscriptions` | 3 |

Phase 5A preserved player self-service and public calendar/KVK calendar commands as flat paths.
Those workflows remain deferred and should not be moved by Phase 6.

## 5. Scope

### In Scope

- Create or update a canonical command reference covering every active slash command.
- For each command, document:
  - current path
  - owner module
  - command group/top-level status
  - permission model
  - response visibility
  - version/usage tracking expectations
  - migration status or disposition
  - operator-facing notes where relevant
- Update stale docs and smoke references that still mention old Phase 3, Phase 4, or Phase 5A flat
  paths.
- Add command-design guidance for new work:
  - group-first design
  - standard permission decorators
  - command-count impact
  - minimum command registration and smoke-test expectations
- Keep the validator baseline and grouped command summary aligned with
  `scripts/validate_command_registration.py`.
- Capture any out-of-scope command UX redesign findings as deferred optimisations.

### Out Of Scope

- Moving, renaming, retiring, or adding slash commands.
- Player self-service workflow redesign.
- Public calendar/KVK calendar UX redesign.
- SQL schema changes.
- Permission behavior changes.
- Runtime command implementation changes beyond documentation-only corrections.
- Production promotion or deployment.

## 6. Mandatory Workflow

1. Review/scope Phase 6 and stop for approval.
2. Inventory existing command docs and smoke references.
3. Propose the canonical command reference shape and stop for approval.
4. Implement documentation updates only.
5. Run focused documentation and validator checks.
6. Open a ready-for-review PR against `K98-bot-mirror`.

## 7. Suggested Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_inventory.py tests\test_command_registration_smoke.py
```

Before PR handoff, run or justify skipping:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
```

Codex Security review is usually optional for documentation-only Phase 6 work. Run it if the phase
expands into permissions, command runtime behavior, SQL/data access, file handling, secrets/config,
deployment, network calls, or restart-sensitive persistence.

## 8. Required Delivery Output

1. Summary
2. File Manifest
3. SQL Changes
4. Helpers Reused
5. Refactor Findings
6. Test Plan And Results
7. AI Review Gates
8. Deployment / Rollback Notes
9. Deferred Optimisations
