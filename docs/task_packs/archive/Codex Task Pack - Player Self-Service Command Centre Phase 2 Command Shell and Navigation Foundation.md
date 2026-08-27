# Codex Task Pack - Player Self-Service Command Centre Phase 2 Command Shell and Navigation Foundation

Status: completed execution pack. Phase 2 delivered the `/me` command shell and navigation
foundation in mirror PR #164 and production PR #472, passed manual smoke testing, and is retained
here as a historical record while manual merge/promotion completes.

## 1. Task Header

- Task name: `Player Self-Service Command Centre Phase 2 Command Shell and Navigation Foundation`
- Date: `2026-06-22`
- Programme: `Player Self-Service Command Centre`
- Task type: `Discord command architecture | player UX foundation | command governance`
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
- `docs/task_packs/Player Self-Service Command Centre - Phase 1 Audit and Design Report.md`

Use SQL validation only to confirm existing contracts. Do not change SQL in this phase.

## 3. Objective

Add the `/me` command group as a safe, read-only but polished player self-service foundation in
parallel with all current legacy player self-service commands.

Target command shell:

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me exports
```

Phase 2 should prove command registration, decorators, response visibility, polished dashboard
navigation, status loading, and service/view boundaries before deeper account/reminder mutation or
generated visual card work begins. It must feel like the first version of a premium player command
centre, not a plain help menu.

### Product Quality Bar

Phase 2 is not just a command shell. It is the first player-visible product foundation for the
personal command centre.

The first `/me dashboard` release must be:

- status-first, not command-first
- understandable within five seconds
- private and calm rather than busy
- no more than three visible dashboard sections
- state plus next action in every section
- no wall of buttons
- no full account matrix, reminder matrix, or export form on the dashboard
- no dead buttons whose only purpose is "coming soon"
- no misleading "ready" or "complete" labels when a source is unavailable
- visually consistent with the modern KVK suite through wording, layout discipline, and navigation
  style, even before the generated PNG dashboard card exists

Players should come away with a clear mental model: `/me` is where they manage themselves.

## 4. Explicit Approval Required

`/me` is a new top-level slash command group. Do not implement until the operator approves:

- adding `/me`
- updating `scripts/validate_command_registration.py::APPROVED_TOP_LEVEL_COMMANDS`
- updating `docs/reference/canonical_command_reference.md`
- adding command registration and smoke coverage

Expected command count after approval:

```text
primary=41
grouped_subcommands_detected=85
```

The exact grouped subcommand total should be verified by
`scripts/validate_command_registration.py` after implementation.

## 5. In Scope

- Create `commands/me_cmds.py`.
- Register `/me` from `commands/register_all()` using existing registrar patterns.
- Add the `/me` top-level group to command registration governance.
- Add `/me dashboard`, `/me accounts`, `/me reminders`, `/me preferences`, and `/me exports`.
- Add a read-only player self-service summary service.
- Add polished private/ephemeral views for navigation.
- Show account/reminder/preference/export status summaries where existing sources are trustworthy.
- Build a polished `/me dashboard` embed MVP with three status-led sections and concise next
  actions.
- Add quick-launch guidance to existing `/kvk` commands, inventory, and exports without duplicating
  their behavior.
- Add tests for registration, decorators, shell behavior, status service, view ownership, timeout,
  no-mutation guarantees, and player journey acceptance checks.
- Update command reference and draft player/operator briefing text.

## 6. Out of Scope

- Registering, modifying, or removing governor accounts through `/me`.
- Subscribing, modifying, or unsubscribing reminders through `/me`.
- Changing inventory preferences through `/me` unless explicitly approved as a tiny service-backed
  preference action.
- Generating or redesigning stats/inventory exports.
- Building the visual PNG dashboard card.
- Changing SQL schema, stored procedures, views, indexes, or persistence contracts.
- Removing, redirecting, or deprecating legacy commands.
- Changing `/kvk` output behavior.
- Changing subscription scheduler or DM tracker behavior.

## 7. Target Files

Likely create:

- `commands/me_cmds.py`
- `player_self_service/__init__.py`
- `player_self_service/service.py`
- `ui/views/player_self_service_views.py`
- `tests/test_me_cmds.py`
- `tests/test_player_self_service_service.py`
- `tests/test_player_self_service_views.py`

Likely modify:

- `commands/__init__.py`
- `scripts/validate_command_registration.py`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md` only if new out-of-scope findings are discovered
- player/operator briefing doc under `docs/` if a suitable location exists

Do not modify runtime SQL files.

## 8. Architecture Direction

Commands:

- validate only Discord command entry assumptions
- defer safely and privately
- call player self-service services
- render or hand off to views
- use `@versioned()`, `@safe_command`, and `@track_usage()`

Service:

- loads account summary through `services.governor_account_service`
- reads reminder config through existing subscription/calendar stores
- reads inventory visibility through `inventory.reporting_service`
- returns renderer-independent summary models
- contains no Discord types

Views:

- own buttons, selects, back-navigation, ownership checks, timeout disabling, and stale interaction
  handling
- call services for summaries
- do not write account/reminder/export state in Phase 2

DAL:

- no new DAL unless audit during implementation proves a read-only repository is necessary
- no SQL in commands or views

## 9. User Experience Requirements

Dashboard:

- private/ephemeral by default
- at most three primary sections: Accounts, Reminders, Preferences and Quick Links
- at most three primary buttons: Accounts, Reminders, Preferences
- quick launch uses a select menu or compact secondary controls
- no full account list, full reminder matrix, or export form on the first screen
- status-led layout rather than a command index
- every section shows current state plus one next useful action
- unknown source states show as `unknown` or `not available`, not guessed
- primary copy should avoid legacy command names unless needed for transition safety

Required Phase 2 dashboard MVP shape:

```text
Header:
K98 Personal Command Centre
Private setup dashboard for <player>

Accounts:
- Main: set / not set
- Linked: 0 / 1 / multiple
- Next action: Register / Review / Manage

Reminders:
- KVK reminders: on / off / unknown
- Times: concise summary such as 24h, 4h, 1h
- Next action: Set up / Manage

Preferences:
- Inventory visibility: private / public / not set / unknown
- Exports: available through private export tools
- Next action: Review preferences

Controls:
Accounts | Reminders | Preferences
Quick Launch select: KVK stats, KVK targets, KVK history, KVK rankings, Inventory, Exports
```

Accounts page:

- show current account count and main slot if available
- include navigation controls for future register/modify/find flows
- in Phase 2, prefer useful status and next-action guidance over placeholder controls
- if a legacy command route is still needed, keep it secondary and transitional rather than the
  main dashboard experience

Reminders page:

- show subscribed/not subscribed and concise event/time summary if available
- include future subscribe/update/unsubscribe entry points without mutating in Phase 2
- do not show dead "coming soon" buttons; prefer clear status and transition guidance

Preferences page:

- show inventory visibility if readable
- show unknown/unset states honestly

Exports page:

- list stats export and inventory export paths
- warn that file exports are private
- do not generate files in Phase 2

## 10. Command Governance Requirements

- Add `/me` to `APPROVED_TOP_LEVEL_COMMANDS`.
- Add `/me` to `docs/reference/canonical_command_reference.md`.
- Update grouped command summary with `/me` and 5 subcommands.
- Document why existing groups are unsuitable: `/me` coordinates account, reminder, preferences,
  exports, and KVK launch surfaces across multiple domains.
- Ensure grouped usage tracking records qualified paths such as `me dashboard`.
- Run command registration validation and focused command inventory tests.

## 11. SQL/Data Review

Use existing sources only:

- registry: `dbo.DiscordGovernorRegistry` and registry stored procedures through existing service
  and DAL
- Governor lookup: `dbo.vw_All_Governors_Clean` only through existing helper/service paths
- stats export status: existing stats export service/DAL only if status needs it
- inventory preference: `dbo.InventoryReportPreference` through inventory reporting service
- usage: `dbo.BotCommandUsage` through existing usage tracking
- reminders: JSON-backed subscription/calendar stores through existing helpers

No SQL changes are expected.

## 12. Refactor Triggers To Check

Check and report:

- direct SQL in any new command/view code
- business logic creeping into `commands/me_cmds.py`
- service code importing Discord types
- view code performing account/reminder writes
- duplicate dashboard/account/reminder summary helpers
- misleading status when data source errors
- insufficient logging for status load failures
- tests that assert legacy command names in new user-facing copy

Fix only in-scope Phase 2 issues. Capture broader account/reminder extraction work as deferred
optimisations.

## 12A. Phase Gates For Later Mutation

Phase 2 must not copy old command bodies into new `/me` buttons.

Record these gates clearly in the delivery notes:

- Do not implement `/me accounts` write actions until account centre service ownership is complete.
- Do not implement `/me reminders` write actions until reminder centre service ownership is
  complete.
- Do not expose preference write actions through `/me preferences` unless there is an existing
  service-backed persistence path and the UX remains simple.
- Do not trigger file exports directly from the dashboard shell in Phase 2.

## 13. Testing Plan

Required validators:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
```

Focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_inventory.py tests\test_command_registration_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_views.py
```

Risk-based additions:

- account summary states: no accounts, single account, multiple accounts, registry unavailable
- reminder states: unsubscribed, subscribed, invalid/empty file fallback
- preference states: unset, private, public, read failure
- view ownership and timeout
- no-mutation guarantee for dashboard/accounts/reminders/preferences/exports shell actions
- usage/decorator expectations for every subcommand

Player journey acceptance checks:

- New player with no accounts can run `/me dashboard` and understand how to get started without
  already knowing `/mygovernorid` or `/register_governor`.
- Existing player with one account can immediately see their main account and setup status.
- Existing player with multiple accounts can see that multiple accounts are linked without being
  shown a dense full-slot matrix on the dashboard.
- Subscribed player can see what KVK reminders they have enabled without opening
  `/modify_subscription`.
- Unsubscribed player can understand how to set reminders without being shown a dense
  configuration screen.
- Player never sees full account details, full reminder details, and export forms on the same
  screen.
- Unknown source states are visible and honest, not hidden behind false "ready" language.

Run full pytest before production promotion when practical because this command group crosses
multiple player-facing subsystems.

## 14. AI Review Gate

Codex Security should be considered before PR handoff because Phase 2 touches Discord commands,
interactions, user-controlled input, permissions/visibility, and status reads from data-backed
subsystems. If skipped, document that Phase 2 is read-only and performs no account/reminder/export
mutation.

## 15. Acceptance Criteria

- [ ] Operator approval for `/me` is recorded.
- [ ] `/me` command group registers with 5 subcommands.
- [ ] Legacy commands remain unchanged and live.
- [ ] Dashboard is private, simple, read-only, and status-led.
- [ ] Dashboard does not read like a command index.
- [ ] Dashboard uses no more than three primary sections and each section has state plus next action.
- [ ] Account/reminder/preferences/exports pages are private and read-only.
- [ ] Phase 2 avoids dead "coming soon" buttons and prefers useful transition guidance.
- [ ] Commands are thin and decorated.
- [ ] Services own summary/status logic and import no Discord types.
- [ ] Views own only interaction routing and call services.
- [ ] No SQL is added to commands or views.
- [ ] Command registration validation is green.
- [ ] Focused service/view/command tests pass.
- [ ] Command reference and briefing docs are updated.
- [ ] Deferred findings are captured structurally.

## 16. PR Summary Template

```md
## Summary

- Added the `/me` player self-service command group shell.
- Added a polished read-only `/me dashboard` plus account, reminder, preference, and export navigation.
- Updated command governance docs/tests for the new top-level group.

## Changes

- New player self-service command module, service, and views.
- Dashboard MVP presents status plus next action for accounts, reminders, and preferences.
- Command registration validator and canonical command reference updated.
- Focused tests added for command registration, summary service, views, and no-mutation behavior.

## Tests

- <commands run>

## AI Review Gates

- Codex Security: <run or skipped with reason>

## Risk / Rollback

- Runtime risk is controlled because Phase 2 is read-only and legacy commands remain live.
- Rollback by removing `/me` registration and docs/tests updates.
```
