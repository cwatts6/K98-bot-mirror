# Codex Chat Starter - Command Platform Phase 4 Ark Command Grouping

Use this starter to begin the next Command Platform Audit & Optimisation Programme phase.

Source programme documents:

- `docs/task_packs/Codex Task Pack - Command Platform Audit & Optimisation Programme.md`
- `docs/task_packs/Codex Task Pack - Command Platform Phase 4 Ark Command Grouping.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Phase 3 was completed in PR 133 (`codex/command-platform-phase-3-ops-startup-audit`), smoke tested
successfully, merged, and pushed to production. Production smoke confirmed:

- startup command audit reports
  `primary=75 grouped_subcommands_detected=29 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=75`
- the stale `primary=0 ... total_unique=0` startup summary is gone
- `/ops validate_command_cache` reports all commands correctly versioned and cached
- the moved `/ops` commands execute correctly

## Copy/Paste Starter

Codex, begin Phase 4 of the Command Platform Audit & Optimisation Programme: Ark Command Grouping.

This follows the completed Phase 3 ops consolidation and startup audit alignment PR:

- PR 133: `codex/command-platform-phase-3-ops-startup-audit`
- Result: smoke tested successfully, merged, pushed to production
- Current validator baseline:

```text
primary=75 grouped_subcommands_detected=29 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=75
```

The objective for this phase is to recover command headroom by grouping approved Ark commands
under `/ark` while preserving behavior, permissions, options, autocomplete, modal/view flows,
versions, usage tracking, and command-cache semantics.

## 1. Task Header

- Task name: Command Platform Phase 4 - Ark Command Grouping
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
- `docs/task_packs/Codex Task Pack - Command Platform Phase 4 Ark Command Grouping.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Also review:

- `commands/ark_cmds.py`
- Ark services, DAL, views, schedulers, and reminder state modules touched by command handlers
- `commands/command_inventory.py`
- `core/command_lifecycle.py`
- `scripts/validate_command_registration.py`
- `tests/test_command_registration_smoke.py`
- `tests/test_validate_command_registration.py`
- `tests/test_command_inventory.py`
- `tests/test_command_lifecycle.py`
- existing Ark command, reminder, ban, draft, cancel, result, registration, and command-cache tests
- Ark docs and smoke/runbook references that mention flat command paths

## 3. Objective

This phase should:

- migrate approved Ark top-level commands under `/ark`
- preserve existing command behavior, permissions, options, autocomplete, descriptions, versions,
  usage tracking, modal/view flows, and response behavior
- public `/ark_reminder_prefs` and `/ark_report_players` are approved for grouping
- leave unapproved public/player command paths unchanged
- reduce active top-level command count without touching non-Ark command domains
- update tests and docs for any moved paths

## 4. Scope

### In Scope

Leadership/admin Ark grouping candidates:

- `/ark_create_match` -> `/ark create_match`
- `/ark_force_announce` -> `/ark force_announce`
- `/ark_amend_match` -> `/ark amend_match`
- `/ark_cancel_match` -> `/ark cancel_match`
- `/ark_set_preference` -> `/ark set_preference`
- `/ark_clear_preference` -> `/ark clear_preference`
- `/ark_ban_add` -> `/ark ban_add`
- `/ark_ban_revoke` -> `/ark ban_revoke`
- `/ark_ban_list` -> `/ark ban_list`
- `/ark_set_result` -> `/ark set_result`
- `/ark_generate_draft` -> `/ark generate_draft`
- `/create_ark_team` -> `/ark create_team`

Public Ark grouping candidates, only if explicitly approved:

- `/ark_reminder_prefs` -> `/ark reminder_prefs`
- `/ark_report_players` -> `/ark report_players`

Also in scope:

- `commands/ark_cmds.py`
- command registration, cache/version, and validator tests
- Ark docs and smoke/runbook updates
- command-platform docs updates

### Out Of Scope

- non-Ark command grouping
- public/player command migration outside approved Ark paths
- aliases or transition messaging unless explicitly approved
- SQL schema changes
- permission-decorator changes except preserving existing gates during movement
- production promotion or deployment

## 5. Mandatory Workflow

1. Review/scope Phase 4 and stop for approval.
2. Map every Ark command handler, decorator, option, autocomplete, usage-tracking version, and
   command-cache path affected by grouping.
3. Public `/ark_reminder_prefs` and `/ark_report_players` are approved for grouping; include a
   simple post-merge Discord briefing note before rollout.
4. Present implementation plan and stop for approval.
5. Implement approved Ark grouping changes only.
6. Add/update focused tests and docs.
7. Run validation.
8. Run Codex Security review before PR handoff.

Proceed in one pass only if explicitly approved in the new chat.

## 6. Acceptance Criteria

- [ ] Approved Ark commands are grouped under `/ark` without behavior regressions.
- [ ] Unapproved public/player command paths remain unchanged.
- [ ] Command descriptions, options, autocomplete, versions, usage tracking, permissions, and
      response behavior are preserved.
- [ ] Modal/view flows still open and respond correctly from grouped handlers.
- [ ] Command cache/version validation recognizes the new grouped paths.
- [ ] `scripts/validate_command_registration.py` reports the expected reduced active top-level
      command count for the approved candidate set.
- [ ] Focused tests cover moved command registration/cache names and high-risk Ark handlers.
- [ ] Ark docs, smoke expectations, and command-platform docs reflect the new paths and baseline.
- [ ] Codex Security review is completed before PR handoff.

## 7. Suggested Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_registration_smoke.py tests\test_command_inventory.py tests\test_command_lifecycle.py tests\test_ark_reminder_prefs_command.py tests\test_ark_preference_commands.py tests\test_ark_ban_commands.py tests\test_ark_cancel_match.py tests\test_ark_phase3a_create_match.py tests\test_ark_phase3b_amend_match.py tests\test_ark_registration_flow.py
```

Before PR handoff, run or justify skipping:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security is required because this phase changes Discord command paths, permissions-sensitive
handlers, public interaction entry points if approved, and restart-sensitive Ark workflows.

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
