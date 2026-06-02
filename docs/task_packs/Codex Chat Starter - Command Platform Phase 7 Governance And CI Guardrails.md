# Codex Chat Starter - Command Platform Phase 7 Governance And CI Guardrails

Use this starter to begin the final planned Command Platform Audit & Optimisation Programme phase.

Source programme documents:

- `docs/task_packs/Codex Task Pack - Command Platform Audit & Optimisation Programme.md`
- `docs/task_packs/Codex Task Pack - Command Platform Phase 7 Governance And CI Guardrails.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Phase 6 was completed in PR 137 (`codex/command-platform-phase-6-canonical-docs`), merged, marked
complete, and pushed to production on 2026-06-02.

Current validator baseline:

```text
primary=39 grouped_subcommands_detected=76 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=39
```

## Copy/Paste Starter

Codex, begin Command Platform Phase 7: Governance And CI Guardrails.

This follows the completed Phase 6 documentation PR:

- PR 137: `codex/command-platform-phase-6-canonical-docs`
- Result: merged, marked complete, and pushed to production
- Current validator baseline:

```text
primary=39 grouped_subcommands_detected=76 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=39
```

The objective for this phase is governance and guardrail preparation. Add or update validation,
CI/pre-commit wiring, command-design guidance, and task-pack checklist material so the command
surface does not drift back toward Discord's command limit. Do not move, rename, retire, or add
slash commands in Phase 7.

Phase 7 is expected to be the final phase of the Command Platform Audit & Optimisation Programme.
Player self-service workflow redesign and public calendar/KVK calendar redesign remain separate
deferred optimisation programmes.

## 1. Task Header

- Task name: Command Platform Phase 7 - Governance And CI Guardrails
- Date: 2026-06-02
- Owner/context: Command Platform Audit & Optimisation Programme
- Task type: governance / validation tooling / CI preparation
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
- `docs/task_packs/Codex Task Pack - Command Platform Phase 7 Governance And CI Guardrails.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Also review:

- `commands/command_inventory.py`
- `scripts/validate_command_registration.py`
- command registration, inventory, lifecycle, validator, and CI/pre-commit tests
- existing CI, pre-commit, and local validation configuration

## 3. Objective

Complete the Command Platform Audit & Optimisation Programme by adding governance and guardrails
that prevent future command-limit drift and keep the canonical command reference maintainable.

## 4. Out Of Scope

Do not move, rename, retire, or add slash commands.

Also out of scope:

- player self-service workflow redesign
- public calendar/KVK calendar UX redesign
- SQL schema changes
- permission behavior changes
- runtime command handler implementation changes
- production promotion or deployment

## 5. Mandatory Workflow

1. Review/scope Phase 7 and stop for approval.
2. Inventory existing validator, CI, pre-commit, and command-governance docs.
3. Present the proposed guardrail design and stop for approval.
4. Implement approved governance/tooling/docs updates.
5. Run focused validation.
6. Open a ready-for-review PR against `K98-bot-mirror`.

## 6. Suggested Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
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
10. Programme Closure Recommendation
