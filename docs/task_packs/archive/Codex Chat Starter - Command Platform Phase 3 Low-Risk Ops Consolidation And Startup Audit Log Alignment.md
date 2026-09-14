# Codex Chat Starter - Command Platform Phase 3 Low-Risk Ops Consolidation And Startup Audit Log Alignment

Status: complete. Phase 3 was delivered in PR 133
(`codex/command-platform-phase-3-ops-startup-audit`), smoke tested successfully, merged, and pushed
to production. This starter remains as the execution record for Phase 3 of the Command Platform
Audit & Optimisation Programme.

Source programme documents:

- `docs/task_packs/Codex Task Pack - Command Platform Audit & Optimisation Programme.md`
- `docs/task_packs/Codex Task Pack - Command Platform Phase 3 Low-Risk Ops Consolidation And Startup Audit Log Alignment.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Phase 1, Permission Decorator Standardisation, was completed in PR 131
(`codex/command-platform-phase-1-permission-decorators`), smoke tested successfully, merged, and
pushed to production.

Phase 2, Validator And Inventory Tooling Enhancement, was completed in PR 132
(`codex/command-platform-phase-2-validator-inventory`), smoke tested successfully, merged, and
pushed to production. Phase 3 then grouped the approved low-risk operational/reporting commands
under `/ops` and aligned startup command-audit logging. The current command-platform baseline is:

```text
primary=75 grouped_subcommands_detected=29 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=75
```

Phase 3 also corrected the stale `DL_bot.py` startup command-audit summary that previously logged
`primary=0 ... total_unique=0`.

## Copy/Paste Starter

Codex, begin Phase 3 of the Command Platform Audit & Optimisation Programme: Low-Risk Ops
Consolidation And Startup Audit Log Alignment.

This follows the completed Phase 2 validator and inventory tooling PR:

- PR 132: `codex/command-platform-phase-2-validator-inventory`
- Result: smoke tested successfully, merged, pushed to production
- Current validator baseline:

```text
primary=82 grouped_subcommands_detected=22 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=82
```

The objective for this phase is to recover low-risk command headroom by grouping approved
operational/reporting commands under `/ops`, and to fix the stale startup command-audit log that
currently reports `primary=0 ... total_unique=0`.

## 1. Task Header

- Task name: Command Platform Phase 3 - Low-Risk Ops Consolidation And Startup Audit Log Alignment
- Date: 2026-06-01
- Owner/context: Command Platform Audit & Optimisation Programme
- Task type: deferred optimisation batch / command-surface migration
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
- `docs/task_packs/Codex Task Pack - Command Platform Phase 3 Low-Risk Ops Consolidation And Startup Audit Log Alignment.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Also review:

- `scripts/validate_command_registration.py`
- `commands/command_inventory.py`
- `core/command_lifecycle.py`
- `DL_bot.py`
- `Commands.py`
- `commands/admin_cmds.py`
- `tests/test_command_registration_smoke.py`
- `tests/test_validate_command_registration.py`
- `tests/test_command_inventory.py`
- `tests/test_command_lifecycle.py`
- existing admin command, command cache, and command registration tests

## 3. Objective

This phase should:

- fix or remove the misleading `DL_bot.py` startup audit summary that currently logs
  `primary=0 ... total_unique=0`
- migrate approved low-risk operational/reporting commands under `/ops`
- preserve existing command behavior, permissions, options, descriptions, versions, usage tracking,
  and response behavior
- reduce active top-level command count without touching public/player domain paths beyond the
  explicitly approved low-risk ops/reporting set
- update tests and docs for any moved paths

## 4. Scope

### In Scope

- `DL_bot.py` startup command-audit log alignment.
- Low-risk `/ops` grouping candidates:
  - `/history`
  - `/failures`
  - `/usage`
  - `/usage_detail`
  - `/test_embed`
  - `/summary`, only if public/operator visibility is approved
  - `/weeksummary`, only if public/operator visibility is approved
- `commands/admin_cmds.py`
- command registration, cache/version, and validator tests
- command-platform docs updates

### Out Of Scope

- Ark command grouping
- public/player domain grouping
- aliases or migration messaging unless explicitly approved
- SQL schema changes
- permission-decorator changes except preserving existing gates during movement
- production promotion or deployment

## 5. Mandatory Workflow

1. Review/scope Phase 3 and stop for approval.
2. Map the stale startup audit log path and exact low-risk ops command candidates.
3. Confirm which candidate commands are approved for grouping, especially `/summary` and
   `/weeksummary`.
4. Present implementation plan and stop for approval.
5. Implement approved startup-log and ops-grouping changes only.
6. Add/update focused tests and docs.
7. Run validation.
8. Run Codex Security review or justify skipping before PR handoff.

Proceed in one pass only if the user explicitly approves one-pass implementation in the new chat.

## 6. Acceptance Criteria

- [ ] Startup command audit logs no longer show `primary=0 ... total_unique=0` for a healthy bot.
- [ ] Startup smoke expectations identify the authoritative command surface clearly.
- [ ] Approved low-risk ops commands are grouped under `/ops` without behavior regressions.
- [ ] Unapproved public/player command paths remain unchanged.
- [ ] Command descriptions, options, versions, usage tracking, and permissions are preserved.
- [ ] `scripts/validate_command_registration.py` reports the expected reduced active top-level
      command count after approved grouping.
- [ ] Focused tests cover startup audit log semantics and moved command registration/cache names.
- [ ] Command-platform docs reflect the new paths and baseline.

## 7. Suggested Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_registration_smoke.py tests\test_command_inventory.py tests\test_command_lifecycle.py tests\test_admin_command_cache_paths.py
```

Before PR handoff, run or justify skipping:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security is likely required if this phase changes Discord command paths, permissions,
public/admin command visibility, or startup command sync behavior.

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
