# Codex Task Pack - Command Platform Phase 3 Low-Risk Ops Consolidation And Startup Audit Log Alignment

## 1. Task Header

- Task name: Command Platform Phase 3 - Low-Risk Ops Consolidation And Startup Audit Log Alignment
- Date: 2026-06-01
- Owner/context: Command Platform Audit & Optimisation Programme
- Task type: deferred optimisation batch / command-surface migration
- One-pass approved: no
- Status: complete; delivered in PR 133, smoke tested successfully, merged, and pushed to
  production

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
- `DL_bot.py`
- `Commands.py`
- `commands/admin_cmds.py`
- `tests/test_command_registration_smoke.py`
- `tests/test_validate_command_registration.py`
- `tests/test_command_inventory.py`
- `tests/test_command_lifecycle.py`
- existing admin command, command cache, and command registration tests

## 3. Objective

Recover low-risk command headroom by grouping selected operational/reporting commands under
`/ops`, and fix the stale startup command-audit log so restart smoke evidence shows the correct
command surface.

This phase should:

- fix or remove the misleading `DL_bot.py` startup audit summary that currently logs
  `primary=0 ... total_unique=0`
- migrate approved low-risk operational commands under the existing `/ops` group
- preserve command behavior, permissions, options, descriptions, versions, usage tracking, and
  response behavior
- reduce active top-level command count without touching public/player domain paths beyond the
  explicitly approved low-risk ops/reporting set
- update tests and docs for any moved paths

## 4. Background

Phase 1 was completed in PR 131 and pushed to production. It standardised active command
permission gates onto decorators while preserving command paths and registration count.

Phase 2 was completed in PR 132 and pushed to production. It retired unused disabled secondary
command declarations, detected helper-attached grouped subcommands, and established this baseline:

```text
primary=82 grouped_subcommands_detected=22 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=82
```

Phase 2 production smoke confirmed restart and `/ops validate_command_cache` were green, but the
restart log exposed a stale `DL_bot.py` startup audit line:

```text
[COMMAND AUDIT] registration summary: primary=0 secondary_cogs=0 secondary_subscribe=0 total_unique=0
```

That log is confusing because the authoritative static validator correctly reports 82 active
top-level commands. Phase 3 must address this before the command-platform programme is considered
log-clean.

Phase 3 implementation result:

```text
primary=75 grouped_subcommands_detected=29 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=75
```

The `/ops` group now has 21 statically detected subcommands, including `/ops summary`,
`/ops weeksummary`, `/ops history`, `/ops failures`, `/ops usage`, `/ops usage_detail`, and
`/ops test_embed`.

## 5. Scope

### In Scope

- Correcting startup command-audit logging in `DL_bot.py`, either by reusing authoritative
  inventory semantics or by removing stale count output and pointing to the validator-backed
  command surface.
- Grouping low-risk ops/reporting command candidates under `/ops`, subject to review and approval:
  - `/history` -> `/ops history`
  - `/failures` -> `/ops failures`
  - `/usage` -> `/ops usage`
  - `/usage_detail` -> `/ops usage_detail`
  - `/test_embed` -> `/ops test_embed` or explicitly defer/retire after review
  - `/summary` -> `/ops summary` only if public/operator visibility is approved
  - `/weeksummary` -> `/ops weeksummary` only if public/operator visibility is approved
- Updating command registration, command cache/version tests, and docs for approved moved paths.
- Preserving existing `/ops` grouped command behavior and Phase 2 validator semantics.

### Out Of Scope

- Ark command grouping.
- Public/player domain grouping across registry, KVK/stats, inventory, calendar, subscriptions,
  honor, location, activity, or CrystalTech.
- Command aliases or migration messaging unless explicitly approved.
- SQL schema changes.
- Permission-decorator changes except to preserve existing gates during movement.
- Production promotion or deployment.

## 6. Mandatory Workflow

1. Review/scope Phase 3 and stop for approval.
2. Map the stale startup audit log path and exact low-risk ops command candidates.
3. Confirm which candidate commands are approved for grouping, especially `/summary` and
   `/weeksummary` public visibility.
4. Present implementation plan and stop for approval.
5. Implement approved startup-log and ops-grouping changes only.
6. Add/update focused tests and docs.
7. Run validation.
8. Run Codex Security review or justify skipping before PR handoff.

Proceed in one pass only if the user explicitly approves one-pass implementation in the new chat.

## 7. Acceptance Criteria

- [ ] Startup command audit logs no longer show `primary=0 ... total_unique=0` for a healthy bot.
- [ ] Startup smoke expectations identify the authoritative command surface clearly.
- [ ] Approved low-risk ops commands are grouped under `/ops` without behavior regressions.
- [ ] Unapproved public/player command paths remain unchanged.
- [ ] Command descriptions, options, versions, usage tracking, and permissions are preserved.
- [ ] `scripts/validate_command_registration.py` reports the expected reduced active top-level
      command count after approved grouping.
- [ ] Focused tests cover startup audit log semantics and moved command registration/cache names.
- [ ] Command-platform docs reflect the new paths and baseline.
- [ ] Any deferred command-platform findings are captured structurally.

## 8. Suggested Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_registration_smoke.py tests\test_command_inventory.py tests\test_command_lifecycle.py
```

Add focused admin command tests based on the exact moved commands, likely including:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_admin_command_cache_paths.py
```

Before PR handoff, run or justify skipping:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security is likely required if this phase changes Discord command paths, permissions,
public/admin command visibility, or startup command sync behavior. If the final implementation is
limited to log wording and pure reporting, document a skip rationale.

## 9. Required Delivery Output

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
