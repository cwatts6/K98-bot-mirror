# Codex Task Pack - Player Self-Service Command Centre Phase 1 Audit and Design Only

Status: completed execution pack. Phase 1 produced the audit/design report and recommended the
Phase 2 `/me` command shell foundation. This pack is retained as a historical record.

## 1. Task Header

- Task name: `Player Self-Service Command Centre Phase 1 Audit and Design Only`
- Date: `2026-06-22`
- Owner/context: K98 Bot player self-service redesign epic
- Task type: `deferred optimisation batch | product UX audit | Discord command architecture`
- One-pass approved: `no`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`.

Also read:

- `docs/reference/deferred_optimisations.md`
- `docs/reference/canonical_command_reference.md`
- `docs/task_packs/Player Self-Service Command Centre - Programme Pack.md`
- `docs/task_packs/archive/KVK Player Experience Redesign - Programme Pack.md`
- any current player briefing or command deprecation docs linked from the canonical command reference

For SQL-facing review, validate schema, procedure, view, index, and persistence details against:

```text
C:\K98-bot-SQL-Server
```

Do not change SQL in this phase.

## 3. Objective

Audit and design the new **Player Self-Service Command Centre** before implementation.

The output should define a premium, app-like `/me` player self-service layer that lets players manage accounts, reminders, preferences, and personal outputs from one coherent place, while keeping the first screen simple enough that players do not get lost.

No runtime code changes should be made in this phase.

## 4. Background

The KVK player command redesign is complete and has established the new quality bar for player-facing command output.

The next opportunity is the broader player self-service surface. Current registration, Governor ID lookup, account review, subscription, reminder, preference, and export commands are useful but fragmented. The strategic direction is:

```text
Every player now has a personal command centre.
```

The programme should start with registration and subscriptions, but as a radical player identity and settings redesign rather than command grouping.

The main watchout is navigation complexity. The final design must not become a busy control panel. It must use progressive disclosure: simple dashboard first, detailed actions one layer deeper.

## 5. Scope

### In Scope

- Audit current player self-service command surface:
  - `/register_governor`
  - `/modify_registration`
  - `/my_registrations`
  - `/mygovernorid`
  - `/subscribe`
  - `/modify_subscription`
  - `/unsubscribe`
  - `/inventory_preferences`
  - `/my_stats_export`
  - `/export_inventory`
  - `/my_stats`
  - `/myinventory`
  - `/mykvkcrystaltech`
  - `/calendar_reminder_config` if present
- Audit related modern `/kvk` launch targets:
  - `/kvk stats`
  - `/kvk targets`
  - `/kvk history`
  - `/kvk rankings`
- Audit current registration/account services, views, modals, validation, persistence, duplicate checks, and admin support paths.
- Audit current subscription/reminder services, views, DM trackers, scheduled/sent trackers, persistence, restart safety, and failure paths.
- Review SQL-backed command usage if available.
- Review command registration baseline and top-level command count impact of a new `/me` group.
- Design the target `/me` command model.
- Design the dashboard information architecture.
- Design the account centre journey.
- Design the reminder centre journey.
- Design first-pass preferences and exports journeys.
- Propose visual card direction and interaction model.
- Define anti-busy UX rules, including button/select/modal budgets.
- Define migration/deprecation approach for legacy commands.
- Define implementation phases and recommend the first implementation task pack.
- Capture out-of-scope issues as structured deferred optimisations.

### Out of Scope

- Any runtime code change.
- Creating the `/me` command group.
- Changing command registration.
- Changing SQL schema, procedures, views, or persistence contracts.
- Full redesign of `/my_stats`.
- Full redesign of inventory cards.
- Full public calendar redesign.
- Ark/MGE/admin workflow redesign.
- Removing or redirecting legacy commands.
- Building a website/webapp.
- Adding recommendation or prediction logic.
- Changing KVK command behaviour.

## 6. Source Deferred Items

```md
### Deferred Optimisation
- Area: `commands/registry_cmds.py`, `commands/telemetry_cmds.py`, `commands/stats_cmds.py`, `commands/inventory_cmds.py`, `commands/subscriptions_cmds.py`, `commands/calendar_cmds.py`, player self-service command docs/tests
- Type: architecture
- Description: Player self-service commands are still split across development-era entry points instead of being designed as complete user workflows. The affected paths include `/register_governor`, `/modify_registration`, `/my_registrations`, `/mygovernorid`, `/my_stats`, `/my_stats_export`, `/mykvkcrystaltech`, `/myinventory`, `/inventory_preferences`, `/export_inventory`, `/subscribe`, `/modify_subscription`, `/unsubscribe`, and `/calendar_reminder_config`. Phase 7 has already moved `/mykvkstats`, `/mykvktargets`, and `/mykvkhistory` into deprecated redirect-only compatibility paths with final removal tracked separately, so those paths are no longer part of the future self-service redesign scope. These remaining commands are high-discoverability, likely high-traffic commands that players use for critical self-service tasks, and simple path grouping could preserve a fragmented user model while still forcing players to relearn command names.
- Suggested Fix: Scope a dedicated player self-service workflow redesign outside the command-count programme. Review each block as a user journey before choosing command paths. For registry/account flows, specifically evaluate whether lookup, register, review, and modify should be consolidated into a coherent Governor ID/account command surface rather than four separate commands. Review SQL-backed command usage, transition/announcement needs, Discord alias limitations, docs/smoke references, permission and channel behavior, and focused regression tests before any implementation.
- Impact: high
- Risk: medium
- Dependencies: Phase 5A admin/leadership/operator grouping is complete; requires operator approval, SQL-backed usage review, user-facing briefing, and a fresh task pack.
```

## 7. Codex Skills To Use

| Skill | Use when |
|---|---|
| `k98-architecture-scope` | Use before implementation planning. This phase is architecture/design-only and must map affected layers, SQL/persistence implications, approval checkpoints, tests, and deferred findings. |
| `k98-discord-command-feature` | Use because the programme will change slash commands, views, modals, buttons, selects, interaction callbacks, response visibility, command registration, and user-facing bot flows. |
| `k98-sql-validation` | Use in review mode only where current registration, stats, active-player, usage, or persistence contracts depend on SQL. Do not change SQL in this phase. |
| `k98-test-selection` | Use to define the validation approach for later implementation phases and identify focused tests for account, subscription, command, view, and persistence work. |
| `k98-deferred-optimisation-capture` | Use to capture debt discovered during audit that is not part of the first build. |
| `k98-pr-review` | Use before handoff if this audit/design pack is committed as documentation. |
| `k98-promotion-check` | Not applicable unless this documentation is promoted through the normal production repo process. |
| `codex-security:security-scan` | Use as a risk review trigger for future implementation phases. For this documentation-only task, record a skip reason unless security-sensitive docs or workflows are changed. |

### Skill Decisions

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | `use` | Required to map command/view/service/DAL/persistence boundaries before implementation. |
| `k98-discord-command-feature` | `use` | The target programme changes player command and interaction design. |
| `k98-sql-validation` | `use` | Review SQL dependencies only; no SQL changes. |
| `k98-test-selection` | `use` | Required to propose focused implementation validation. |
| `k98-deferred-optimisation-capture` | `use` | Audit may find out-of-scope debt. |
| `k98-pr-review` | `use` | Use before documentation handoff if committed. |
| `k98-promotion-check` | `not applicable` | No production runtime change in this audit phase. |
| `codex-security:security-scan` | `not applicable` | Documentation-only phase; include future security triggers in the report. |

## 8. Mandatory Workflow

This task is design-only.

1. Audit current command surface and user journeys.
2. Audit architecture and persistence touchpoints.
3. Review usage evidence where available.
4. Draft target `/me` command model and design options.
5. Evaluate options against usability, command governance, implementation risk, and consistency with the KVK redesign.
6. Recommend the target design and phased implementation plan.
7. Stop for approval before any implementation.

Do not proceed into code changes in this task.

## 9. Audit Requirements

Review the touched area for:

- direct SQL in commands or views
- business logic in interaction layers
- duplicate account lookup/register helpers
- duplicate subscription/unsubscribe logic
- legacy commands that can redirect later
- weak validation or unclear player errors
- weak logging on account/reminder changes
- DM failure handling
- cache and persistence safety
- restart safety for reminders and views
- command registration count impact
- response visibility and privacy consistency
- channel restrictions and admin overrides
- docs/reference gaps
- test coverage gaps

Map the likely:

- commands
- slash command groups
- services
- repositories / DAL modules
- SQL objects or contracts
- views, modals, buttons, and selects
- JSON files or persisted state
- caches
- restart implications
- telemetry / usage tracking
- conditional reference docs

## 10. Architecture Targets

The design should preserve or propose clean ownership boundaries.

| Concern | Target |
|---|---|
| Slash commands | `commands/me_cmds.py` or equivalent new player self-service command boundary |
| Account centre services | `player_self_service/` or existing `services/governor_account_service.py` plus registry service boundaries |
| Reminder centre services | existing subscription/reminder services or a new thin orchestration service |
| Views / modals | `ui/views/player_self_service_views.py`, `ui/views/registry_views.py`, `ui/views/subscription_views.py`, or equivalent |
| Visual card rendering | `player_self_service/rendering/` or shared card-rendering location if approved |
| Repository / DAL | existing registry/subscription persistence layers; new DAL only if audit proves needed |
| Shared helpers | existing `core/`, account picker helpers, registry helpers, interaction safety helpers |
| Operational tooling | command inventory and registration validators |
| Documentation | `docs/reference/`, `docs/task_packs/`, player/operator briefing docs |
| SQL schema | SQL repo only if later approved; no SQL changes in Phase 1 |
| Tests | `tests/` focused command, service, view, registration, persistence, and docs tests for later phases |

## 11. Likely Files

### Review

- `commands/registry_cmds.py`
- `commands/subscriptions_cmds.py`
- `commands/telemetry_cmds.py`
- `commands/stats_cmds.py`
- `commands/inventory_cmds.py`
- `commands/calendar_cmds.py`
- `commands/events_cmds.py`
- `commands/kvk_cmds.py`
- `services/governor_account_service.py`
- `registry/registry_service.py`
- `registry/account_slots.py`
- `target_utils.py`
- `subscription_tracker.py`
- `event_scheduler.py`
- `reminder_task_registry.py`
- `dm_tracker_utils.py`
- `inventory/`
- `ui/views/registry_views.py`
- `ui/views/subscription_views.py`
- `ui/views/inventory_report_views.py`
- `ui/views/kvk_personal_views.py`
- `scripts/validate_command_registration.py`
- `scripts/select_tests.py`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- relevant command smoke tests and command inventory tests

### Modify

Documentation only, if this task is committed:

- `docs/task_packs/Player Self-Service Command Centre - Phase 1 Audit and Design Report.md`
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 2 <recommended implementation>.md`
- optionally `docs/reference/deferred_optimisations.md` if new structured deferred items are discovered

### Create

Recommended outputs:

- `docs/task_packs/Player Self-Service Command Centre - Phase 1 Audit and Design Report.md`
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 2 <recommended implementation>.md`

Do not create runtime files in this phase.

## 12. Implementation Requirements

This task has no runtime implementation.

The audit/design output must:

- Keep the dashboard simple and avoid designing a busy control panel.
- Recommend a clear `/me` command model.
- Explain why `/me` should or should not be a new top-level command group.
- Identify legacy commands to keep, redirect, or retire later.
- Design account and reminder centres as workflows, not just renamed commands.
- Preserve command/view/service/DAL boundaries.
- Preserve existing KVK command behaviours.
- Preserve privacy and response visibility expectations.
- Identify SQL/data dependencies without changing them.
- Identify restart-safety implications for reminder/view state.
- Define testing and rollout requirements for later phases.
- Capture new out-of-scope findings as structured deferred optimisations.

### Command Surface Governance

- [ ] State whether the proposed programme changes top-level command count, grouped subcommand count, or neither.
- [ ] If `/me` is recommended, treat it as a new top-level command group.
- [ ] Document why an existing command group is not suitable for the player command centre.
- [ ] Record that operator approval is required before adding `/me`.
- [ ] Plan updates to `scripts/validate_command_registration.py::APPROVED_TOP_LEVEL_COMMANDS`.
- [ ] Plan updates to `docs/reference/canonical_command_reference.md`.
- [ ] Plan updates to player/operator docs and smoke references.
- [ ] Preserve or explicitly update `@versioned()`, `@safe_command`, `@track_usage()`, permission decorators, response visibility, autocomplete/options, usage-log identity, and command-cache behavior.
- [ ] Identify required command registration validation commands for implementation phases.

## 13. UX Requirements

The target design must include explicit anti-busy rules.

Minimum rules to define:

- maximum number of visible primary dashboard sections
- maximum number of initial buttons
- use of select menus vs buttons
- when to use modals
- when to use ephemeral responses
- how users return to dashboard
- how timeouts are handled
- how account/reminder errors are explained
- how legacy command users are guided
- how quick launch links avoid duplicating full command output

Recommended starting policy:

```text
Dashboard = status and top-level navigation only.
Accounts = account actions.
Reminders = reminder actions.
Preferences = defaults and privacy.
Exports = file/output launchpad.
```

## 14. Expected Delivery Output

Create a Phase 1 audit/design report with this structure:

1. Executive Summary
2. Current Command Surface Map
3. Current User Journey Audit
4. Current Architecture and Persistence Map
5. Usage and Discoverability Review
6. Pain Points and Opportunity Assessment
7. Target `/me` Command Model Options
8. Recommended `/me` Command Model
9. Dashboard Information Architecture
10. Account Centre Journey Design
11. Reminder Centre Journey Design
12. Preferences and Exports First-Pass Design
13. Visual Direction and Wireframe Notes
14. Interaction Model and Anti-Busy Rules
15. Legacy Migration and Deprecation Plan
16. Architecture Target State
17. SQL/Data Dependency Notes
18. Testing and Validation Strategy
19. Risks and Rollback/Containment
20. Proposed Implementation Phases
21. Recommended Next Task Pack
22. Deferred Optimisations

## 15. Testing Requirements

This is a documentation/audit task, so runtime tests are not required unless Codex modifies repository scripts, docs validators, or references that are covered by tests.

Still define the implementation validation strategy for later phases.

Suggested validation commands for later implementation phases:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
```

Focused tests to identify or propose:

- command registration tests
- command inventory tests
- `/me` command smoke tests
- account summary service tests
- account register/modify/remove view tests
- Governor ID lookup flow tests
- subscription view tests
- reminder persistence/restart tests
- DM failure-path tests
- preference persistence tests
- dashboard renderer/output-shape tests
- legacy redirect tests
- permission/visibility tests

## 16. Acceptance Criteria

- [ ] Current player self-service command surface is fully mapped.
- [ ] Current account registration/lookup/review/modify journey is documented.
- [ ] Current subscription/reminder journey is documented.
- [ ] Pain points and player confusion risks are clearly described.
- [ ] Target `/me` command model is recommended with alternatives considered.
- [ ] Dashboard design is intentionally simple and includes anti-busy rules.
- [ ] Account centre journey is designed as a coherent workflow.
- [ ] Reminder centre journey is designed as a coherent workflow.
- [ ] Preferences and exports first-pass scope is defined.
- [ ] Visual direction is aligned with the modern KVK suite.
- [ ] Legacy migration/deprecation approach is defined.
- [ ] Command registration governance impact is documented.
- [ ] SQL/data dependencies are identified without changing SQL.
- [ ] Implementation phases are proposed.
- [ ] Next task pack recommendation is included.
- [ ] Deferred optimisations are captured structurally.
- [ ] No runtime code changes were made.

## 17. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Helpers Reused
7. Refactor Findings
8. Test Plan
9. AI Review Gates
10. Deployment Steps
11. Deferred Optimisations

For this documentation-only work, state that no runtime code, SQL, helper reuse, or restart behaviour changed.

## 18. PR Summary Template

```md
## Summary

- Completed the Player Self-Service Command Centre Phase 1 audit and design.
- Recommended the target `/me` command model and implementation sequence.
- Defined dashboard, account centre, reminder centre, preferences, exports, and legacy migration strategy.

## Changes

- Added Phase 1 audit/design report.
- Added recommended next implementation task pack.
- Captured deferred findings where applicable.

## Tests

- Documentation-only change.
- Runtime tests not required unless validators or command references were modified.
- If docs/reference files changed: include relevant validation commands.

## AI Review Gates

- Codex Security: skipped for documentation-only audit, or run if security-sensitive implementation details were changed.

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Low runtime risk because this is design-only.
- Rollback by reverting documentation changes.
```
