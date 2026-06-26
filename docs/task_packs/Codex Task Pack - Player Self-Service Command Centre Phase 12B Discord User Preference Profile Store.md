# Codex Task Pack - Player Self-Service Command Centre Phase 12B Discord User Preference Profile Store

## 1. Task Header

- Task name: `Player Self-Service Command Centre Phase 12B Discord User Preference Profile Store`
- Date: `2026-06-26`
- Owner/context: Player Self-Service Command Centre programme after Phase 12 Slice 1 delivered
  Inventory Preferences copy and documentation in mirror PR #176 and was smoke tested successfully
  by the operator on 2026-06-26
- Task type: `Discord interaction feature | SQL-backed persistence | player profile preferences | player self-service UX`
- One-pass approved: `no`
- Status: `implemented in current branch; validation and PR handoff pending`

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
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 12 Preferences Hub Expansion.md`
- `docs/player_self_service_command_centre_briefing.md`
- `C:\K98-bot-SQL-Server\docs\SQL_DATA_MIGRATION_GUARDRAILS.md`
- `C:\K98-bot-SQL-Server\docs\SQL_PROMOTION_GUIDE.md`
- `C:\K98-bot-SQL-Server\docs\SQL_RELEASE_CHECKLIST.md`

Validate every SQL-facing assumption against `C:\K98-bot-SQL-Server` before relying on table,
column, procedure, view, index, or migration names. Do not infer schema from Python usage alone.

Conditionally read:

- `docs/reference/Promotion Guide.md` only for promotion or deployment sequencing.
- Existing `/me preferences`, inventory preference, command-registration, and player self-service
  tests before changing behavior.
- SQL repo migration/readme standards before adding or changing SQL objects.

## 3. Objective

Add persisted Discord-user-level profile preferences for:

- timezone
- location country
- preferred language

These values should support future planning, event timing analysis, and localization. They should
not be stored per governor, because one Discord user can own multiple governor IDs and the values
should be shared across that user's Main/Alt/Farm slots.

Phase 12B adds `/me preferences` display and Manage add/update/remove controls only for fields
that have service-backed persistence, validation, safe fallback behavior, and restart-safe SQL
storage.

## 4. Product Decisions From Phase 12

Phase 12 Slice 1 delivered the safe Inventory Preferences surface:

- Inventory report visibility remains in `/me preferences` and `/inventory_preferences`.
- Inventory VIP remains in `/me preferences` through the existing Inventory VIP update handoff.
- Export format/day defaults stay out of `/me preferences`; current system defaults are adequate.
- Stats output/privacy defaults stay out of `/me preferences`; stats export remains ephemeral.
- Reminder event/time preferences stay in `/me reminders` and legacy reminder paths.
- Calendar reminder preferences stay in `/me reminders` and `/calendar_reminder_config`.
- Main-account behavior stays in `/me accounts`.

Phase 12B is different because timezone, location country, and preferred language are
Discord-user-level profile preferences. A dedicated SQL-backed Discord user preference/profile
store is preferred over extending `dbo.DiscordGovernorRegistry`, because registry rows represent
governor slots and would duplicate the same profile data across a player's accounts.

The current session-based local-time toggle must remain unchanged. It is useful when a player is
travelling because it reflects the active session timezone. A saved timezone in Phase 12B is
planning/profile metadata unless a later approved feature uses it.

## 5. In Scope

- Start with audit/scope and SQL design before coding.
- Validate current Discord user, governor registry, account, and `/me preferences` persistence
  paths.
- Propose and, only after approval, implement a dedicated SQL-backed Discord user
  preference/profile table keyed by Discord user ID.
- Add repository/DAL and service accessors for reading current values.
- Add service-backed mutations for setting and clearing timezone, location country, and preferred
  language.
- Add validation for accepted timezone, country, and language values before persistence.
- Display delivered values on the `/me preferences` generated card and fallback embed.
- Add Manage controls to add, update, and remove delivered values.
- Preserve unset-value fallback copy without placeholder or "coming soon" controls.
- Preserve existing Inventory report visibility and Inventory VIP behavior.
- Preserve `/inventory_preferences`, `/myinventory`, `/me inventory`, `/me exports`,
  `/my_stats_export`, `/export_inventory`, `/me reminders`, `/calendar_reminder_config`, and
  `/me accounts` behavior.
- Update command reference, programme pack, player briefing, deferred backlog, and focused tests.

## 6. Out of Scope

- Replacing or changing the current session-based local-time toggle.
- Applying saved timezone to calendar/reminder display without a separately approved planning or
  calendar feature.
- Duplicating timezone, location country, or preferred language on `dbo.DiscordGovernorRegistry`
  rows.
- Adding unsaved controls, placeholder controls, or "coming soon" rows.
- Adding export defaults, stats privacy defaults, reminder preferences, calendar reminder
  preferences, or main-account behavior to `/me preferences`.
- Redirecting or removing legacy commands.
- Redesigning export schemas, report schemas, generated file contracts, or visual-card renderer
  primitives.
- Building a website or external settings dashboard.

## 7. SQL Direction

The implemented SQL direction is a dedicated SQL object keyed by Discord user ID:
`dbo.DiscordUserProfilePreference`. The migration and schema script live in
`C:\K98-bot-SQL-Server`, and were designed against the SQL repo migration guardrails, promotion
guide, and release checklist.

Expected properties:

- one row per Discord user ID
- nullable `TimezoneName`, `LocationCountryCode`, and `PreferredLanguageTag` fields
- clear update and clear semantics for each field
- no dependency on a specific governor slot
- safe behavior when no row exists
- validation before writes so arbitrary free-form text is not persisted
- migration and rollback notes in the SQL repo if a new table is added

Validation choices to decide during audit:

- timezone canonical format: IANA timezone identifier validated by runtime `zoneinfo`
- country canonical format: stored two-letter country code with readable display name derived in
  the service and UI
- language canonical format: normalized language tag with readable display name derived from the
  primary language

## 8. Architecture Direction

- Commands stay thin and delegate to `/me` views.
- Views own Discord interaction wiring only.
- Business rules and validation live in `player_self_service` services or a dedicated profile
  preference service.
- SQL access lives in DAL/repository modules, not commands or views.
- Existing inventory services continue to own Inventory report visibility and VIP behavior.
- Card rendering should show only persisted values and conservative unset-state copy.
- All failure states should be private, actionable, and avoid leaking profile data.

## 9. Suggested Validation

Run or justify skipping:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\deploy\Validate-SqlRepo.ps1
.\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_preference_service.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_service.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_page_cards.py
```

Add focused SQL/DAL tests for any new persistence layer. Add failure-path tests for invalid
timezone, country, or language values; SQL save failures; clear/remove actions; missing rows; and
fresh interaction reloads after mutation.

Run or document a Codex Security review before PR handoff because Phase 12B touches
user-controlled input, SQL/data access, Discord interactions, and restart-sensitive persistence.

## 10. Manual Smoke

After implementation, smoke test:

- `/me preferences` remains private and renders the generated card.
- Existing Inventory report visibility still saves, refreshes, and affects report posting.
- Existing Inventory VIP update handoff still works.
- Timezone can be added, updated, removed, and reloaded in a fresh interaction.
- Location country can be added, updated, removed, and reloaded in a fresh interaction.
- Preferred language can be added, updated, removed, and reloaded in a fresh interaction.
- Invalid values are rejected privately with actionable copy.
- Failure states remain private and do not leak data.
- Bot restart expectations are met by SQL persistence.
- The current session-based local-time toggle still behaves as before.
- `/inventory_preferences`, `/myinventory`, `/me inventory`, `/me exports`, `/my_stats_export`,
  `/export_inventory`, `/me reminders`, `/calendar_reminder_config`, and `/me accounts` remain
  behavior-compatible.

## 11. Acceptance Criteria

- Phase 12B starts with audit/scope and SQL validation unless implementation is explicitly
  approved.
- Candidate SQL schema is validated against `C:\K98-bot-SQL-Server` before bot code depends on
  it.
- Timezone, location country, and preferred language are stored once per Discord user, not once per
  governor slot.
- No data is duplicated onto `dbo.DiscordGovernorRegistry` without a separately approved reversal
  of the Phase 12B data-ownership decision.
- Every shipped field has validation, service-backed persistence, clear/remove behavior, restart
  safety, fallback copy, and focused tests.
- `/me preferences` displays and manages only delivered persisted settings.
- Existing Inventory Preferences, inventory report, export, reminder, account, command
  registration, and public/private behavior is preserved.
- Standard validators, SQL repo validation, focused tests, and selected broader tests pass.
- Docs and deferred backlog are updated after implementation.
