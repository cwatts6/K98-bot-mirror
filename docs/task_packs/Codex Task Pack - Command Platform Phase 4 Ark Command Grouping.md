# Codex Task Pack - Command Platform Phase 4 Ark Command Grouping

## 1. Task Header

- Task name: Command Platform Phase 4 - Ark Command Grouping
- Date: 2026-06-01
- Owner/context: Command Platform Audit & Optimisation Programme
- Task type: deferred optimisation batch / command-surface migration
- One-pass approved: yes, after review/scope approval in implementation chat
- Status: implementation approved

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

Recover the largest remaining low-risk command headroom block by grouping approved Ark commands
under `/ark` while preserving existing behavior, permissions, options, autocomplete, modal/view
flows, response behavior, versions, usage tracking, and restart-sensitive Ark workflows.

This phase should:

- migrate approved Ark command paths from flat top-level names to `/ark` subcommands
- preserve leadership/admin decorators and channel restrictions exactly
- preserve public Ark command behavior; public `/ark_reminder_prefs` and `/ark_report_players`
  migration is explicitly approved for this phase
- reduce active top-level command count without touching non-Ark command domains
- update tests and docs for moved paths
- keep command registration validation and startup smoke evidence aligned with the new baseline

## 4. Background

Phase 3 was completed in PR 133 (`codex/command-platform-phase-3-ops-startup-audit`), smoke tested
successfully, merged, and pushed to production. It moved the approved low-risk operational and
reporting commands under `/ops`, fixed the stale startup command-audit summary, and left the active
baseline at:

```text
primary=75 grouped_subcommands_detected=29 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=75
```

The current grouped command summary is:

| Group | Statically detected subcommands |
|---|---:|
| `/ops` | 21 |
| `/mge` | 6 |
| `/prekvk` | 2 |

Ark is now the largest remaining flat command block and is the next planned command-platform
optimisation phase. The public Ark paths are approved for this phase because Ark runs every two
weeks and the public Ark commands are not currently in active use. Add a simple post-merge Discord
briefing note before the next Ark cycle.

## 5. Scope

### In Scope

Create an `/ark` command group and move approved Ark commands:

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

Public Ark paths approved for this phase:

- `/ark_reminder_prefs` -> `/ark reminder_prefs`
- `/ark_report_players` -> `/ark report_players`

Also in scope:

- `commands/ark_cmds.py`
- command inventory, registration, cache/version, and validator tests
- Ark command docs and smoke/runbook references
- Discord briefing note for post-merge operator sharing
- command-platform docs updates
- command-cache validation expectations for grouped Ark paths

### Out Of Scope

- Non-Ark command grouping
- Public/player command migration beyond explicitly approved Ark paths
- aliases or transition messaging unless explicitly approved
- SQL schema changes
- permission-decorator changes except preserving existing gates during movement
- production promotion or deployment

## 6. Baseline And Expected Count

Starting validator baseline:

```text
primary=75 grouped_subcommands_detected=29 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=75
```

All 14 Ark commands are approved, so the expected top-level baseline is:

```text
primary=62 grouped_subcommands_detected=43 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=62
```

Recalculate during implementation only if the final command set changes unexpectedly.

## 7. Mandatory Workflow

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

One-pass implementation was approved after the scope review for the full 14-command Ark grouping.

## 8. Acceptance Criteria

- [ ] Approved Ark commands are grouped under `/ark` without behavior regressions.
- [ ] Unapproved public/player paths remain unchanged.
- [ ] Command descriptions, options, autocomplete, versions, usage tracking, permissions, and
      response behavior are preserved.
- [ ] Modal/view flows still open and respond correctly from grouped handlers.
- [ ] Command cache/version validation recognizes the new grouped paths.
- [ ] `scripts/validate_command_registration.py` reports the expected reduced active top-level
      command count for the approved candidate set.
- [ ] Focused tests cover moved command registration/cache names and high-risk Ark handlers.
- [ ] Ark docs, smoke expectations, and command-platform docs reflect the new paths and baseline.
- [ ] Codex Security review is completed before PR handoff.

## 9. Suggested Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_registration_smoke.py tests\test_command_inventory.py tests\test_command_lifecycle.py
```

Run focused Ark coverage based on the approved paths, likely including:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_ark_reminder_prefs_command.py tests\test_ark_preference_commands.py tests\test_ark_ban_commands.py tests\test_ark_cancel_match.py tests\test_ark_phase3a_create_match.py tests\test_ark_phase3b_amend_match.py tests\test_ark_registration_flow.py
```

Before PR handoff, run or justify skipping:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security is required because this phase changes Discord command paths, permissions-sensitive
handlers, public interaction entry points if approved, and restart-sensitive Ark workflows.

## 10. Required Delivery Output

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
