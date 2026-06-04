# KVK Player Experience Redesign — Phase 2 New `/kvk` Player Command Group Scaffold Task Pack Draft

> Superseded: this combined Phase 2 draft is replaced by the approved split into Phase 2A admin collision resolution and Phase 2B player `/kvk` scaffold. Keep this file only as historical planning context unless it is archived or removed later.

## 1. Task Header

- Task name: `KVK Player Experience Redesign — Phase 2 New /kvk Player Command Group Scaffold`
- Date: `2026-06-03`
- Owner/context: K98 Bot KVK player command migration programme
- Task type: `feature / command-surface refactor / UX migration scaffold`
- One-pass approved: `no`
- Status: `draft — do not start until Phase 1 audit/design is complete and approved`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`.

Also read:

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/task_packs/KVK Player Experience Redesign - Phase 1 Audit and Design Task Pack.md`
- the Phase 1 audit/design output and approval notes
- `docs/reference/canonical_command_reference.md`
- command registration validation documentation and tests
- current KVK command tests
- current KVK service/DAL documentation

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

```text
C:\K98-bot-SQL-Server
```

## 3. Objective

Create the new player-facing `/kvk` command group in parallel with the existing legacy KVK commands.

This scaffold phase should improve command discovery and prepare the migration path without changing output design, SQL semantics, KVK import/recompute/export behaviour, or removing old commands.

The new group should initially delegate to existing services/output paths wherever safe.

## 4. Background

Phase 1 should have confirmed the target player command model:

```text
/kvk stats
/kvk targets
/kvk history
/kvk rankings
```

This Phase 2 draft assumes that Phase 1 approved creating the `/kvk` group as the first implementation step.

The purpose of Phase 2 is not to modernise the visual output yet. It is to create a safe new command surface that can be tested by admins/players while legacy commands remain live.

## 5. Scope

### In Scope

- Create or update the approved `/kvk` player command group.
- Add the following grouped subcommands if approved by Phase 1:
  - `/kvk stats`
  - `/kvk targets`
  - `/kvk history`
  - `/kvk rankings`
- Reuse existing command logic, services, DAL calls, and output rendering where practical.
- Preserve legacy command paths unchanged.
- Add lightweight navigation/help text where appropriate.
- Add command usage tracking for the new subcommands.
- Preserve existing player permissions and channel behaviour unless Phase 1 explicitly approves changes.
- Add focused tests for command registration, command delegation, permissions, and output parity.
- Update canonical command reference and any command inventory docs.
- Update command registration validation baseline if a new top-level `/kvk` group is introduced.
- Capture any blockers or remaining migration gaps as deferred optimisations.

### Out of Scope

- No visual card redesign.
- No generated image implementation.
- No old command removal.
- No old command redirect/deprecation behaviour unless explicitly approved as a tiny help-only addition.
- No `/kvk_admin` implementation.
- No SQL schema/procedure/view/function changes.
- No KVK import/recompute/export changes.
- No Google Sheets output contract changes.
- No Discord reporting display changes outside the new command wrappers.
- No Basic Data or summary tab ingestion.
- No new metric formulas or renamed metric semantics.
- No website implementation.

## 6. Source Deferred Items

### Deferred Optimisation
- Area: KVK player self-service command surface
- Type: architecture
- Description: KVK player commands are spread across legacy command paths and old output patterns. Players should have a coherent `/kvk` journey for stats, targets, history, and rankings.
- Suggested Fix: Introduce a new `/kvk` player command group in parallel with existing commands, then migrate outputs and deprecate legacy commands in later phases.
- Impact: high
- Risk: medium
- Dependencies: Phase 1 audit/design approval, command registration governance, usage review, operator approval.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before changing command surface and delegation boundaries. |
| `k98-discord-command-feature` | use | This task creates grouped slash commands and may add command callbacks/options. |
| `k98-sql-validation` | use | Even if SQL is not changed, command outputs depend on SQL-backed KVK stats, targets, history, and rankings. |
| `k98-test-selection` | use | Required to select command, service, and regression tests. |
| `k98-deferred-optimisation-capture` | use | Any migration gaps or direct SQL findings must be captured structurally. |
| `k98-pr-review` | use | Required before PR handoff/merge. |
| `k98-promotion-check` | use | Required before production promotion because command registration and player-facing paths change. |
| `codex-security:security-scan` | use | User-facing commands, SQL-backed data access, permissions, and interaction surfaces are touched. |

## 8. Mandatory Workflow

1. Confirm Phase 1 audit/design was completed and approved.
2. Confirm exact approved command paths and options.
3. Audit current implementation locations for legacy command logic.
4. Design a minimal delegation scaffold.
5. Stop for approval before implementation if Phase 1 did not already approve the exact implementation approach.
6. Implement `/kvk` group and subcommands.
7. Add/update tests.
8. Update command docs and command registration validation baseline.
9. Run validation.
10. Produce rollout notes and legacy-command status.
11. Stop before any old command removal or visual redesign.

## 9. Audit Requirements

Before implementation, confirm:

- whether `/kvk` already exists
- whether adding `/kvk` changes top-level command count
- whether command-count validation requires an approved baseline update
- exact current modules/functions for each legacy command
- whether existing logic is reusable without copying large command handlers
- whether existing services/DAL boundaries are sufficient
- whether any current command has direct SQL or presentation/business logic that should not be duplicated
- whether output visibility should remain the same as legacy commands
- whether autocomplete/governor selection should be reused or improved in this scaffold
- whether `/kvk rankings` should be a single command with a `type` option or an initial command with buttons/selects
- whether old commands should mention the new group in help text now or later

## 10. Architecture Targets

| Concern | Target |
|---|---|
| New slash command group | `commands/kvk_cmds.py` or approved existing command module |
| Legacy command paths | remain unchanged in their current modules |
| Business logic | existing services, `kvk/services/`, target services, stats services |
| SQL access | existing DAL/repository modules only |
| Views/buttons/selects | `ui/views/`, only if approved for rankings/type navigation |
| Command docs | `docs/reference/canonical_command_reference.md` and relevant user docs |
| Tests | command registration, command callback, output parity, permission boundaries |

## 11. Likely Files

### Review

- Phase 1 audit/design output
- `commands/stats_cmds.py`
- `commands/registry_cmds.py`
- current ranking command modules
- current honor/prekvk command modules
- `kvk/services/`
- `kvk/dal/`
- `target_utils.py`
- `player_stats_cache.py`
- `governor_registry.py`
- `account_picker.py`
- `scripts/validate_command_registration.py`
- `docs/reference/canonical_command_reference.md`
- `tests/test_command_inventory.py`
- `tests/test_command_registration_smoke.py`
- SQL repo objects used by current KVK outputs

### Modify

- approved command module for new `/kvk` group
- command registration validation baseline, if needed
- canonical command reference
- command tests
- selected existing tests if command inventory expectations change

### Create

Potentially:

- `commands/kvk_cmds.py`
- `tests/test_kvk_cmds.py`
- `tests/test_kvk_command_group.py`

Exact files should follow Phase 1 design and current repo conventions.

## 12. Implementation Requirements

### 12.1 `/kvk stats`

Initial scaffold should call the existing personal KVK stats behaviour.

Requirements:

- preserve existing user-visible data and error handling
- preserve governor selection/lookup behaviour unless Phase 1 approved a better option
- preserve visibility/public/ephemeral behaviour or document approved change
- add usage tracking under the new command identity
- do not introduce new visual card output yet

### 12.2 `/kvk targets`

Initial scaffold should call existing KVK target lookup behaviour.

Requirements:

- preserve existing conditional states:
  - off-season / targets unavailable
  - power too low
  - exempt
  - not active during matchmaking
  - Governor ID not found
- preserve target source-of-truth
- preserve existing SQL/sheet/cache behaviour
- do not change target formula or target values

### 12.3 `/kvk history`

Initial scaffold should call existing KVK history behaviour.

Requirements:

- preserve existing output shape
- preserve governor/account selection behaviour
- preserve historical data source
- do not add new charting yet

### 12.4 `/kvk rankings`

Initial scaffold should consolidate access to the ranking surfaces approved in Phase 1.

Possible MVP options:

Option A:

```text
/kvk rankings type:<kvk|honor|prekvk>
```

Option B:

```text
/kvk rankings
```

with a select menu/buttons to choose:

- KVK rankings
- Honor rankings
- PreKVK rankings

Codex must implement the option approved by Phase 1.

Requirements:

- preserve existing ranking calculations
- preserve existing ranking data sources
- preserve existing permissions/visibility
- preserve pagination where present
- avoid duplicating ranking logic in command handlers

### 12.5 Legacy command preservation

Legacy commands must remain live and unchanged unless Phase 1 explicitly approved a non-breaking help notice.

No legacy command should be removed in this phase.

### 12.6 Command Surface Governance

- [ ] State whether the task changes top-level command count, grouped subcommand count, or neither.
- [ ] If `/kvk` is a new top-level command, document why an existing command group is not suitable.
- [ ] Record operator approval for `/kvk` as a new top-level command if required.
- [ ] Update `scripts/validate_command_registration.py::APPROVED_TOP_LEVEL_COMMANDS` if required.
- [ ] Update `docs/reference/canonical_command_reference.md`.
- [ ] Update relevant user/operator docs and smoke references.
- [ ] Preserve `@versioned()`, `@safe_command`, `@track_usage()`, permission decorators, response visibility, autocomplete/options, usage-log identity, and command-cache behavior.
- [ ] Run command registration validation.

## 13. Refactor Decisions

Classify each issue found during implementation:

| Issue | Decision | Reason |
|---|---|---|
| Legacy command contains reusable service call | reuse now | Avoid duplicate logic. |
| Legacy command contains heavy presentation logic | wrap now, redesign later | Visual redesign is Phase 3+. |
| Direct SQL in legacy command, if found | do not duplicate; defer or extract only if necessary | Keep Phase 2 scaffold focused. |
| Missing ranking type abstraction | minimal adapter now or defer | Depends on Phase 1 approved `/kvk rankings` design. |
| Old command deprecation | defer | No removals in Phase 2. |
| Visual card generation | defer | Phase 3. |

Add further rows based on actual findings.

## 14. Testing Requirements

Cover or justify:

- happy path for each `/kvk` subcommand
- invalid governor / not found path where applicable
- target conditional states where practical
- ranking type selection
- permission boundaries
- command registration
- command inventory
- old commands still registered
- output parity with legacy commands where expected
- no SQL changes
- no visual/card generation changes

Suggested focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_cmds.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_inventory.py tests\test_command_registration_smoke.py tests\test_validate_command_registration.py
```

Suggested validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m ruff check commands tests
.\.venv\Scripts\python.exe -m black --check commands tests
.\.venv\Scripts\python.exe -m pyright commands tests
```

Run the full suite if practical:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

## 15. Acceptance Criteria

- [ ] Phase 1 audit/design approval is confirmed.
- [ ] `/kvk` player command group exists if approved.
- [ ] `/kvk stats` works and preserves existing stats behaviour.
- [ ] `/kvk targets` works and preserves existing target behaviour.
- [ ] `/kvk history` works and preserves existing history behaviour.
- [ ] `/kvk rankings` works for the approved MVP ranking types.
- [ ] Legacy commands remain registered and functional.
- [ ] No old command is removed.
- [ ] No visual/card redesign is mixed into this scaffold phase.
- [ ] No SQL schema/procedure/view/function changes are made.
- [ ] No new direct SQL is added to commands or views.
- [ ] Command registration validation is updated and passes.
- [ ] Canonical command docs are updated.
- [ ] Focused tests cover delegation, permissions, and command registration.
- [ ] Deferred optimisations are captured structurally.
- [ ] Rollout notes explain that this is a parallel scaffold, not the final visual redesign.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Command Surface Changes
7. Legacy Command Status
8. Helpers Reused
9. Refactor Findings
10. Test Plan and Results
11. AI Review Gates
12. Deployment Steps
13. Rollout Notes
14. Deferred Optimisations

## 17. PR Summary Template

```md
## Summary

- Added the new `/kvk` player command group scaffold in parallel with legacy commands.
- Added `/kvk stats`, `/kvk targets`, `/kvk history`, and `/kvk rankings` backed by existing behaviour.
- Preserved legacy KVK command paths for safe migration.

## Changes

- <command module changes>
- <tests>
- <docs/command registration updates>

## Tests

- <commands/results>

## AI Review Gates

- Codex Security: <run/skipped with reason>

## Deferred Optimisations

- <none or structured items>

## Risk / Rollback

- Risk: new command group registration and duplicate command-surface confusion during parallel rollout.
- Rollback: revert the `/kvk` command group registration and docs updates; legacy commands remain unchanged.
```
