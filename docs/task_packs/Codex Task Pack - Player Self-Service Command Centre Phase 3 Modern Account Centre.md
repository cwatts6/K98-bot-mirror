# Codex Task Pack - Player Self-Service Command Centre Phase 3 Modern Account Centre

## 1. Task Header

- Task name: `Player Self-Service Command Centre Phase 3 Modern Account Centre`
- Date: `2026-06-22`
- Owner/context: Player Self-Service Command Centre programme after delivered Phase 2 `/me` shell
- Task type: `Discord command feature | player UX consolidation | account workflow service extraction`
- One-pass approved: `no`

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
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/Player Self-Service Command Centre - Programme Pack.md`
- `docs/task_packs/archive/Player Self-Service Command Centre - Phase 1 Audit and Design Report.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 2 Command Shell and Navigation Foundation.md`
- `docs/player_self_service_command_centre_briefing.md`

For SQL-facing account work, validate registry table, view, and stored procedure contracts against:

`C:\K98-bot-SQL-Server`

Do not infer registry schema or stored procedure payloads from Python alone.

## 3. Objective

Turn the delivered read-only `/me accounts` shell into a modern private account centre for player
identity work.

Phase 3 should consolidate the account journey behind `/me accounts` while keeping the legacy
commands live:

```text
/register_governor
/modify_registration
/my_registrations
/mygovernorid
```

The goal is one coherent account centre with service-owned lookup, registration, modification,
removal, duplicate handling, and return-to-dashboard navigation. It must not redirect or retire
legacy commands in this phase.

## 4. Background

Phase 2 delivered and smoke-tested:

- `/me dashboard`, `/me accounts`, `/me reminders`, `/me preferences`, and `/me exports`
- private read-only status summaries
- account/reminder/preference/export navigation
- dashboard Quick Launch guidance
- command governance and focused tests
- legacy command preservation

Smoke testing confirmed:

- `/me dashboard` responds as expected with all controls visible.
- Quick Launch shows guidance for each command.
- `/me exports` opens only the exports page and intentionally omits the dashboard Quick Launch bar.
- Existing commands still work.

Phase 3 should build on that foundation. The account centre should feel like the natural next layer
inside `/me`, not a copy of the old flat commands.

## 5. Scope

### In Scope

- Add or extend account-centre service logic under `player_self_service/`.
- Extend `/me accounts` view to support account actions through buttons, selects, and modals.
- Provide private flows for:
  - account review
  - Governor ID lookup by name
  - registering an account into an available slot
  - modifying/replacing an existing registered slot
  - removing an account with confirmation
  - returning to the `/me dashboard`
- Reuse existing registry service/DAL write paths and stored procedure contracts.
- Preserve duplicate/claim protection and account-slot rules.
- Keep commands and views thin; service owns account journey decisions and confirmation models.
- Add focused tests for service decisions, view routing, command handoff, and regression paths.
- Update player/operator briefing and command documentation where user-facing wording changes.

### Out of Scope

- Removing, redirecting, or deprecating legacy account commands.
- Changing registry SQL schema, stored procedures, views, indexes, or uniqueness rules.
- Rewriting the registry subsystem or registry DAL.
- Moving reminder, preference, export, inventory, KVK, stats, calendar, Ark, MGE, or admin flows.
- Building the generated PNG `/me dashboard` card.
- Adding public account-management output.
- Adding account ownership dispute tooling.

## 6. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Account centre crosses command, service, view, registry, SQL-backed persistence, and tests. |
| `k98-discord-command-feature` | use | `/me accounts` buttons, selects, modals, response visibility, and interaction safety change. |
| `k98-sql-validation` | use | Registry writes depend on SQL stored procedures and views through existing DAL/service paths. |
| `k98-test-selection` | use | Select command/view/service/registry tests plus standard validators. |
| `k98-deferred-optimisation-capture` | use if needed | Capture out-of-scope registry or legacy-command cleanup structurally. |
| `k98-pr-review` | use before handoff | Review command safety, SQL alignment, tests, and migration boundaries before merge. |
| `k98-promotion-check` | use only before production promotion | Not needed for initial mirror PR unless promotion is requested. |
| `codex-security:security-scan` | consider before PR handoff | This phase touches Discord interactions, user input, SQL-backed account persistence, and identity ownership boundaries. |

## 7. Mandatory Workflow

1. Start with audit/scope only unless the operator explicitly approves one-pass implementation.
2. Validate the account SQL contracts in `C:\K98-bot-SQL-Server`.
3. Identify existing registry service/DAL functions to reuse before adding account-centre helpers.
4. Present the implementation plan and test plan for approval.
5. Implement the approved Phase 3 slice.
6. Add or update focused tests.
7. Run selected validators and tests.
8. Run or explicitly justify Codex Security review.
9. Open or update the PR only after local validation.

## 8. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | Keep `commands/me_cmds.py` thin; no account business logic. |
| Account journey service | `player_self_service/` service layer, using renderer-independent models. |
| Registry writes | Existing `registry/registry_service.py` and `registry/dal/registry_dal.py`. |
| Governor lookup | Existing lookup helper/service path, not direct SQL in `/me`. |
| Views/modals | `ui/views/player_self_service_views.py` or focused account-centre view module if complexity justifies it. |
| SQL | SQL repo only; no schema change expected. |
| Tests | Focused command, service, view, registry interaction, and command registration tests. |

Commands and views must not execute SQL directly. Services must not import Discord types.

## 9. Likely Files

### Review

- `commands/me_cmds.py`
- `player_self_service/service.py`
- `ui/views/player_self_service_views.py`
- `commands/registry_cmds.py`
- `ui/views/registry_views.py`
- `services/governor_account_service.py`
- `registry/registry_service.py`
- `registry/dal/registry_dal.py`
- `target_utils.py`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

### Likely Modify

- `player_self_service/service.py`
- `ui/views/player_self_service_views.py`
- `tests/test_player_self_service_service.py`
- `tests/test_player_self_service_views.py`
- `docs/player_self_service_command_centre_briefing.md`

### Likely Create

- `player_self_service/account_service.py` if account mutation makes `service.py` too broad.
- `tests/test_player_self_service_account_service.py` if a dedicated account service is added.

## 10. SQL/Data Review

Validate these contracts before implementation:

- `dbo.DiscordGovernorRegistry`
- `dbo.sp_Registry_Insert`
- `dbo.sp_Registry_SoftDelete`
- `dbo.sp_Registry_GetByDiscordID`
- `dbo.sp_Registry_GetByGovernorID`
- `dbo.sp_Registry_GetAllActive`
- `dbo.vw_All_Governors_Clean`
- `dbo.v_Active_Players`

Expected approach:

- Reuse existing registry service/DAL calls for writes.
- Do not introduce embedded SQL in command or view modules.
- Do not change SQL schema in this phase.
- If a missing SQL capability is discovered, stop and report it instead of guessing a new
  procedure or column.

## 11. Account UX Requirements

`/me accounts` should remain private.

The account centre should support these player paths:

- Review linked accounts and main/default state.
- Find a Governor ID by name.
- Register a new account into an available slot.
- Modify or replace an existing slot.
- Remove an account only after explicit confirmation.
- Return to dashboard after completion.

Interaction requirements:

- Use buttons for clear actions.
- Use selects for account slot choices.
- Use modals for focused text entry such as Governor name or Governor ID.
- Avoid showing every possible command name as the primary UX.
- Make unknown or failed source states explicit.
- Do not create dead "coming soon" controls.
- Use confirmation for destructive removal and replacement actions.
- Keep all account mutation responses ephemeral/private.

## 12. Refactor Triggers To Check

Classify findings as fix now, defer, or not applicable:

| Trigger | Phase 3 decision guidance |
|---|---|
| Direct SQL in command/view path | Do not add; extract or use service/DAL if encountered in touched account path. |
| Business logic in views | Move new account decisions into account service models. |
| Duplicate lookup/register helpers | Reuse existing registry/target helpers where safe; defer larger consolidation if risky. |
| Dead legacy flow | Do not remove legacy commands in Phase 3; capture cleanup for later redirect/removal phase. |
| Restart/persistence fragility | Registry state is SQL-backed; verify no critical account mutation state lives only in view memory beyond short confirmations. |
| Weak logging | Add useful actor/account/slot outcome logs in service-owned mutation paths. |

## 13. Testing Requirements

Run or justify skipping:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
```

Focused tests should cover:

- account centre summary with no accounts, one account, multiple accounts, and source failure
- Governor ID lookup success, no match, and ambiguous/missing input where supported
- register flow service decisions and registry-service handoff
- modify/replace flow confirmation and handoff
- remove flow confirmation and soft-delete handoff
- duplicate/claim protection behavior
- view ownership rejection
- stale/timeout handling
- dashboard return after successful action
- no legacy command removal or redirect

Likely pytest commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_registry_service.py tests\test_registry_dal.py tests\test_registry_views_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py
```

Broaden to the full suite before production promotion when practical because Phase 3 changes
SQL-backed account mutation flows.

## 14. AI Review Gate

Codex Security should be run before PR handoff or explicitly justified because Phase 3 touches:

- Discord interactions
- user-controlled Governor name / Governor ID input
- SQL-backed account identity persistence
- duplicate/claim and ownership boundaries
- destructive account removal

Fix validated issues within the approved Phase 3 scope. Capture larger hardening work as deferred
optimisations.

## 15. Acceptance Criteria

- [ ] `/me accounts` remains private and opens the modern account centre.
- [ ] Players can review linked accounts from `/me accounts`.
- [ ] Players can look up Governor IDs from the account centre.
- [ ] Players can register an account through a service-backed flow.
- [ ] Players can modify or replace an account through a confirmation flow.
- [ ] Players can remove an account only after confirmation.
- [ ] Duplicate/claim protection remains at least as strong as legacy commands.
- [ ] Legacy account commands remain registered and usable.
- [ ] No SQL is added to commands or views.
- [ ] Account journey logic lives in service-layer code, not command/view callbacks.
- [ ] Views own interaction routing, ownership checks, and response sequencing only.
- [ ] Focused tests and standard validators pass.
- [ ] SQL contract validation is documented.
- [ ] Codex Security is run or explicitly justified.
- [ ] Deferred findings are captured structurally.

## 16. PR Summary Template

```md
## Summary

- Added the modern `/me accounts` account centre flows.
- Reused existing registry service/DAL persistence for account registration, modification, and removal.
- Preserved legacy account commands during rollout.

## Changes

- Added service-owned account journey decisions and confirmation models.
- Extended player self-service views with account actions, slot selection, modals, and confirmations.
- Updated briefing/docs for Phase 3 account-centre behavior.

## Tests

- <commands run>

## SQL / Data

- No SQL schema changes.
- Registry SQL contracts validated against `C:\K98-bot-SQL-Server`.

## AI Review Gates

- Codex Security: <run or skipped with reason>

## Risk / Rollback

- Account mutation risk is contained by reusing existing registry service/DAL paths and keeping
  legacy commands live.
- Rollback by disabling the new `/me accounts` mutation controls while preserving Phase 2
  read-only `/me` shell and legacy commands.
```
