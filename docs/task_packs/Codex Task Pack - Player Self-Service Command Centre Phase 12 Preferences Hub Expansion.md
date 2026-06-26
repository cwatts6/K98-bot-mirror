# Codex Task Pack - Player Self-Service Command Centre Phase 12 Preferences Hub Expansion

## 1. Task Header

- Task name: `Player Self-Service Command Centre Phase 12 Preferences Hub Expansion`
- Date: `2026-06-26`
- Owner/context: Player Self-Service Command Centre programme after Phase 11 Shared Visual-Card Renderer Consolidation was delivered in production PR #483 and smoke tested successfully
- Task type: `Discord interaction feature | preferences product model | service-backed persistence | player self-service UX`
- One-pass approved: `no`
- Status: `Slice 1 delivered in mirror PR #176 and smoke tested successfully by the operator on 2026-06-26`

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
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 11 Shared Visual-Card Renderer Consolidation.md`
- `docs/player_self_service_command_centre_briefing.md`

Conditionally read:

- `docs/reference/Promotion Guide.md` only for promotion or deployment sequencing.
- `docs/reference/K98 Bot - SQL Data Access Standards.md` only if the audit proposes SQL-facing persistence changes.
- Existing preference, inventory, export, reminder, account, and `/me` view tests before changing their behavior.

Validate SQL-backed preference assumptions against `C:\K98-bot-SQL-Server` before relying on table, view, procedure, or column names. Do not infer persistence contracts from Python usage alone.

## 3. Objective

Expand `/me preferences` from the current first-pass controls into a coherent player preference
hub, but only where settings have a clear product purpose and safe service-backed persistence.

Phase 12 should not add placeholder controls, "coming soon" toggles, or settings that cannot be
saved reliably across restarts. The goal is a practical preferences centre that helps players
manage self-service defaults without changing unrelated command behavior.

## 4. Background

Delivered context:

- Phase 2 created the private `/me` command-centre shell.
- Phase 5 added the generated private dashboard card and first-pass Preferences page.
- Phase 6 made `/me preferences` service-backed for Inventory report visibility and Inventory VIP
  updates while preserving `/inventory_preferences`.
- Phase 7 aligned dashboard and subpage cards.
- Phase 8 and Phase 9 delivered `/me exports` and safe private dashboard handoffs without changing
  export schemas.
- Phase 10 added `/me inventory` while preserving the detailed `/myinventory` report journey.
- Phase 11 completed shared visual-card renderer consolidation across `/me`, KVK, PreKvK
  compatibility, and Inventory report rendering.

The active deferred preference item was promoted into this Phase 12 task pack. Phase 12 started
with an audit of preference-like state and persistence ownership before deciding which settings
belonged in `/me preferences`.

## 5. Scope

### In Scope

- Start with an audit/scope pass before coding.
- Map current preference-like behavior and persistence across:
  - `/me preferences`
  - `/inventory_preferences`
  - Inventory report visibility
  - Inventory VIP level updates
  - `/me exports` option-window defaults and export delivery assumptions
  - `/me reminders` KVK and calendar reminder preference saves
  - account selection or main-account behavior
  - local time or timezone behavior if an existing persistence contract is available
- Identify which settings are:
  - already persisted safely and can be surfaced or refined in `/me preferences`
  - useful but missing a persistence contract and should be deferred
  - command-specific controls that should remain outside `/me preferences`
  - operator/admin settings that should not move into player self-service
- Preserve current behavior for:
  - Inventory report visibility and `/inventory_preferences`
  - Inventory VIP update prompts and persistence
  - `/myinventory`, `/me inventory`, `/me exports`, and legacy export commands
  - reminder subscription/update/remove behavior
  - command registration
  - public/private Discord response rules
  - export schemas and generated file contracts
- Add service-backed preference mutations only when persistence, restart safety, validation, and
  fallback behavior are clear.
- Keep command modules and views thin; use `player_self_service` services or existing domain
  services for mutation logic.
- Refresh the `/me preferences` generated card and fallback embed only as needed to reflect real
  settings.
- Add focused tests for every new preference read/write path, view callback, card copy change, and
  failure state.
- Update docs, briefing, canonical command notes if the user-visible preference surface changes.

### Out of Scope

- Adding controls that do not persist.
- Adding a new SQL schema without explicit approval after the audit.
- Redesigning export schemas, CSV/XLSX layouts, or generated file contracts.
- Redirecting or removing `/inventory_preferences`, `/my_stats_export`, `/export_inventory`, or
  other legacy commands.
- Changing KVK, Inventory, stats, account, reminder, or export command visibility rules.
- Reopening Phase 11 renderer consolidation.
- Building a website or external settings dashboard.

## 6. Candidate Preference Categories

Codex should audit these categories, then recommend only the ones that are safe to implement:

| Candidate | Current signal | Phase 12 decision needed |
| --- | --- | --- |
| Inventory report visibility | Already service-backed through `inventory.reporting_service` and `/me preferences` | Deliver in Slice 1; preserve the existing mutation path and legacy `/inventory_preferences`. |
| Inventory VIP levels | Already surfaced from `/me preferences` through the Inventory VIP prompt | Deliver in Slice 1; preserve the existing Inventory VIP update handoff. |
| Export defaults | `/me exports` has option windows but no persisted player-default model | Keep out of `/me preferences`; current system defaults are adequate for low-frequency use. |
| Stats output defaults/privacy | Existing stats export behavior is intentionally ephemeral | Keep out of `/me preferences`; do not add a persisted store. |
| Main account behavior | Account centre owns registration and main-account behavior | Keep in `/me accounts`; do not treat as a preference setting. |
| Local time/timezone | Session timezone behavior supports players away from their usual location | Defer stored timezone to Phase 12B for planning insight only; do not replace the current session local-time toggle. |
| Location country | Useful future planning signal, but no player preference store exists | Defer to Phase 12B as Discord-user-level profile data. |
| Preferred language | Useful future localization signal, but no player preference store exists | Defer to Phase 12B as Discord-user-level profile data. |
| Notification/reminder preferences | `/me reminders` already owns reminder-specific event/time preferences | Keep reminder-specific configuration in `/me reminders` and legacy reminder paths. |

## 7. Architecture Direction

- Commands should remain thin and delegate to existing `/me` views or services.
- `ui/views/player_self_service_views.py` may own button/select wiring, but not persistence rules.
- `player_self_service/preference_service.py` should own `/me preferences` mutation orchestration
  where a setting belongs to the preferences hub.
- Existing domain services should continue to own domain-specific persistence:
  - `inventory/reporting_service.py` for Inventory report visibility
  - `inventory/profile_service.py` for Inventory VIP levels
  - `player_self_service/reminder_service.py` for reminder subscription preferences
  - export services for export delivery behavior
- New repository or DAL calls require SQL validation and an explicit audit decision.
- Generated card copy should remain concise and show only actionable, persisted settings.

## 8. Suggested Validation

Run or justify skipping:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_preference_service.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_service.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_page_cards.py
```

Add focused inventory, export, reminder, account, or local-time tests only for the preference
categories touched by the approved implementation.

## 9. Manual Smoke

Slice 1 smoke test completed successfully on 2026-06-26:

- `/me preferences` remained private and rendered the generated Inventory Preferences card.
- Inventory visibility still saved and refreshed correctly.
- Inventory VIP update handoff still worked.
- `/inventory_preferences`, `/myinventory`, `/me inventory`, `/me dashboard`, `/me accounts`,
  `/me reminders`, and `/me exports` remained behavior-compatible.
- No timezone, location country, preferred language, export-default, stats-privacy, reminder, or
  main-account controls were exposed.

## 10. Acceptance Criteria

- Phase 12 starts with audit/scope unless implementation is explicitly approved.
- Candidate preferences are mapped before any new controls are added.
- Every shipped preference has a clear product purpose and service-backed persistence.
- No placeholder or unsaved preference controls are introduced.
- Existing Inventory visibility, VIP, report, export, reminder, command registration, and
  public/private behavior is preserved.
- Focused service, view, card, and failure-path tests pass.
- Standard validators pass.
- Docs and the player briefing describe only delivered behavior.
- Any useful but unsafe candidate preferences are captured as deferred optimisation items using
  the required structure.

## 11. Phase 12B Follow-Up

Phase 12B is split into its own task pack and starter:

- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 12B Discord User Preference Profile Store.md`
- `docs/task_packs/Codex Chat Starter - Player Self-Service Command Centre Phase 12B Discord User Preference Profile Store.md`

Phase 12B should add timezone, location country, and preferred language only as
Discord-user-level data backed by a dedicated SQL preference/profile store. Do not duplicate these
values on `dbo.DiscordGovernorRegistry`, and do not replace the current session-based local-time
toggle.
