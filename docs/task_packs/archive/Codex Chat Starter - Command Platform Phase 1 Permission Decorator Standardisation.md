# Codex Chat Starter - Command Platform Phase 1 Permission Decorator Standardisation

Status: implemented in PR 131 (`codex/command-platform-phase-1-permission-decorators`), smoke
tested successfully, merged, and pushed to production. This starter remains as the execution record
for Phase 1 of the Command Platform Audit & Optimisation Programme.

Source programme documents:

- `docs/task_packs/Codex Task Pack - Command Platform Audit & Optimisation Programme.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Phase 1 is intentionally limited to permission decorator standardisation. Do not group, rename,
retire, or otherwise migrate command paths in this phase.

## Copy/Paste Starter

Codex, begin Phase 1 of the Command Platform Audit & Optimisation Programme: Permission Decorator
Standardisation.

This is part of the wider command-platform roadmap documented in
`docs/reference/command_platform_audit.md`. The full programme goal is to make the command platform
scalable, maintainable, discoverable, consistent, well documented, operationally safe,
architecturally aligned, and future-proofed against Discord command registration limits.

The current command-platform baseline is:

```text
primary=82 grouped_subcommands_detected=21 secondary_cogs=5 secondary_subscribe=1 total_unique=82
```

Existing groups:

- `/ops`: 14 statically detected subcommands
- `/mge`: 6 statically detected subcommands
- `/prekvk`: 1 statically detected subcommand, plus `/prekvk import_history` attached through the
  PreKvK admin helper

Important operator decision already made:

- Inline permission checks are not intentional and should be treated as incorrect.
- Permission-sensitive command access must use standard decorators.
- If existing decorators cannot express the current rule safely, create a small standard decorator
  in the existing decorator layer and test it.

This phase must not change user-facing command paths. Grouping begins only after Phase 1 is
complete and approved.

## 1. Task Header

- Task name: Command Platform Phase 1 - Permission Decorator Standardisation
- Date: 2026-05-29
- Owner/context: Command Platform Audit & Optimisation Programme
- Task type: deferred optimisation batch / refactor
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
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Read conditional docs only if the implementation touches that subsystem beyond permission
decorator placement.

## 3. Objective

Move command access control for inline-check commands onto standard decorators while preserving
current behavior, responses, visibility, command names, and command registration count.

This phase should make later grouping migrations safer by making permission boundaries explicit and
testable at the decorator layer.

## 4. Background

The command-platform audit found several permission-sensitive commands using inline user,
leadership, admin, or channel checks inside command handlers. The operator confirmed these are
incorrect and should be standardised.

The relevant deferred optimisation is:

```md
### Deferred Optimisation
- Area: `commands/admin_cmds.py`, `commands/inventory_cmds.py`, `commands/location_cmds.py`, `commands/mge_cmds.py`, `commands/telemetry_cmds.py`
- Type: consistency
- Description: Several permission-sensitive commands rely on inline user/channel checks instead of the standard decorator model. This is inconsistent with the command-platform standard and makes future grouped-path migrations harder to verify.
- Suggested Fix: Replace inline permission checks with standard decorators or create missing standard decorators where existing decorators cannot express the rule. Preserve existing public/ephemeral responses and add focused permission tests before grouping these commands.
- Impact: high
- Risk: medium
- Dependencies: Confirm exact decorator semantics for admin-only, admin-or-leadership, channel-only, and self-service-with-admin-override cases.
```

## 5. Scope

### Implemented Scope

Audit and standardise permission decorators for active command access checks:

- `commands/admin_cmds.py`
  - `/history`
  - `/failures`
  - redundant inline admin gates in `/ops run_sql_proc`, `/ops run_gsheets_export`, and
    `/ops dl_bot_status`
- `commands/inventory_cmds.py`
  - `/import_inventory`
  - `/export_inventory`
  - `/inventory_import_audit`
- `commands/location_cmds.py`
  - `/player_location`
- `commands/mge_cmds.py`
  - `/mge admin_completion`
- `commands/stats_cmds.py`
  - redundant inline admin gate in `/test_kvk_export`
- `commands/telemetry_cmds.py`
  - `/player_profile`

Also in scope:

- Reviewed existing decorators in `decoraters.py`.
- Added standard decorators for admin-only and admin-or-leadership-in-allowed-channels cases.
- Extended `channel_only` with missing-config denial support for configured channel gates.
- Added focused tests for decorator/permission behavior.
- Kept command registration output unchanged.
- Treated `/export_inventory` as service authorization context rather than a command denial gate.
- Captured larger command-platform findings structurally as deferred optimisations.

### Out of Scope

- Command grouping, renaming, retirement, aliases, or migration messaging.
- Ark grouping under `/ark`.
- Public domain grouping for registry, KVK/stats, inventory, calendar/events, subscriptions,
  CrystalTech, Honor, location, or activity.
- Validator enhancement for disabled secondary command surfaces.
- SQL schema changes.
- Business-logic redesign in the touched command handlers.
- Large command documentation rewrite beyond any small note needed for this phase.
- Production promotion or deployment.

## 6. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required first; identify affected command decorators, tests, and behavior boundaries. |
| `k98-discord-command-feature` | use | This touches Discord slash command permissions and interaction behavior. |
| `k98-sql-validation` | not applicable unless discovered | Use only if implementation unexpectedly touches SQL-backed contracts. |
| `k98-test-selection` | use | Select focused permission, command, and registration tests. |
| `k98-deferred-optimisation-capture` | use | Capture command-platform debt outside Phase 1. |
| `k98-pr-review` | use | Required before PR handoff. |
| `k98-promotion-check` | not applicable for local implementation | Use only before production promotion/deployment. |
| `codex-security:security-scan` | use before PR handoff | Permission boundaries and Discord interactions are security-sensitive. |

## 7. Mandatory Workflow

1. Review/scope Phase 1 and stop for approval.
2. Confirm exact permission semantics for each inline-check command.
3. Present implementation plan and stop for approval.
4. Implement approved decorator standardisation only.
5. Add/update focused tests.
6. Run validation.
7. Run or explicitly complete the Codex Security review gate before PR handoff.

Proceed in one pass only if the user explicitly approves one-pass implementation in the new chat.

## 8. Audit Requirements

For each command in scope, map:

- Current command path
- Current inline permission condition
- Existing response on denial
- Existing ephemeral/public behavior
- Existing allowed channels or role/admin semantics
- Existing service handoff behavior
- Target decorator or new decorator requirement
- Test coverage needed

Also review:

- Whether `decoraters.py` already has the correct reusable decorator.
- Whether decorator denial logging/usage tracking semantics match current inline behavior.
- Whether decorator ordering with `@safe_command`, `@track_usage()`, and `@versioned()` preserves
  expected behavior.

## 9. Architecture Targets

| Concern | Target |
|---|---|
| Permission decorators | `decoraters.py` |
| Slash command handlers | existing `commands/<domain>_cmds.py` modules |
| Business logic | existing services only; do not move business logic in this phase |
| Views / modals | unchanged unless a permission test requires import coverage |
| Tests | focused files under `tests/` |
| Documentation | this starter and `docs/reference/command_platform_audit.md` only if needed |

## 10. Likely Files

### Review

- `decoraters.py`
- `commands/admin_cmds.py`
- `commands/inventory_cmds.py`
- `commands/location_cmds.py`
- `commands/mge_cmds.py`
- `commands/telemetry_cmds.py`
- `tests/test_interaction_safety.py`
- existing command/domain tests for the touched modules
- `docs/reference/command_platform_audit.md`

### Modify

- `decoraters.py` if a missing standard decorator is required
- `commands/admin_cmds.py`
- `commands/inventory_cmds.py`
- `commands/location_cmds.py`
- `commands/mge_cmds.py`
- `commands/telemetry_cmds.py`
- focused tests for permission behavior

### Create

- Optional focused test file, such as `tests/test_command_permission_decorators.py`, if extending
  existing tests would scatter coverage too much.

## 11. Implementation Requirements

- Preserve all current command names and paths.
- Preserve current successful command behavior.
- Preserve current denial behavior as closely as practical, including ephemeral responses.
- Preserve `@versioned()`, `@safe_command`, and `@track_usage()` local patterns.
- Keep commands thin; do not move service/business behavior unless required by permission cleanup.
- Do not add direct SQL to commands or views.
- Do not alter command grouping or registration count.
- Do not silently loosen any admin, leadership, or channel restriction.
- Add focused tests proving denied and allowed cases for each changed permission pattern.

## 12. Refactor Decisions

Initial classification:

| Issue | Decision | Reason |
|---|---|---|
| Inline permission checks in active Phase 1 command set | fixed | Explicit operator decision; needed before grouping. |
| Redundant inline admin checks behind existing decorators | fixed | Keeps active command estate clean before grouping. |
| Command grouping / renames | defer | Phase 1 is permission-only. |
| Disabled secondary duplicate command surfaces | defer | Phase 2 validator/tooling scope. |
| Public-domain grouping design | defer | Later roadmap phase requiring operator UX approval. |
| SQL-backed command usage review | defer unless needed | Not required for decorator standardisation. |

## 13. Testing Requirements

Minimum focused coverage:

- Permission denied path for each changed command or reusable decorator pattern.
- Permission allowed path for each reusable decorator pattern.
- Command registration remains at the current baseline.
- Grouped command signatures remain stable.
- No command paths are renamed.

Suggested validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_interaction_safety.py
```

Add focused domain tests depending on actual files changed, likely including one or more of:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_mge_permissions.py tests\test_mge_award_reminder_refresh.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_registry_cmds.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_stats_cmds.py
```

Before PR handoff, run or explicitly document:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security review is required before PR handoff because this phase touches permission
boundaries and Discord interactions.

## 14. Acceptance Criteria

- [x] All Phase 1 inline command permission checks are replaced by standard decorators or a new
      standard decorator.
- [x] No command path, command group, or command registration count changes.
- [x] Existing successful command behavior is preserved.
- [x] Denied users receive safe, ephemeral denial responses.
- [x] Permission tests cover changed patterns.
- [x] Command registration validation remains clean except known disabled-secondary duplicate
      warnings.
- [x] No new direct SQL exists in commands or views.
- [x] New out-of-scope findings are captured structurally.
- [x] Codex Security review is run before PR handoff.

## 15. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. SQL Changes
4. Helpers Reused / Decorators Reused
5. Refactor Findings
6. Test Plan And Results
7. AI Review Gates
8. Deployment / Rollback Notes
9. Deferred Optimisations

## 16. PR Summary Template

```md
## Summary

- Standardised Phase 1 command permission checks onto decorators.
- Preserved command paths and registration count.

## Changes

- <file/change>

## Tests

- <commands run>

## AI Review Gates

- Codex Security: <run/result>

## Deferred Optimisations

- <none or structured items>

## Risk / Rollback

- Risk: permission-boundary regressions if decorator semantics differ from the prior inline checks.
- Rollback: revert the Phase 1 branch; no SQL or command path migration is involved.
```
