# Codex Chat Starter - Player Self-Service Command Centre Phase 12B Discord User Preference Profile Store

Status: historical starter used for Phase 12B. Implementation is now in the current branch.

Phase 12 Slice 1 is complete. Mirror PR #176 delivered the Inventory Preferences copy/docs slice,
was merged, and was smoke tested successfully by the operator on 2026-06-26. `/me preferences`
remains private, renders the generated Inventory Preferences card, preserves the existing
service-backed Inventory report visibility and Inventory VIP flows, and does not expose unsaved
export, stats privacy, reminder, account, timezone, location, or language controls.

Phase 12B adds persisted Discord-user-level profile preferences for timezone, location
country, and preferred language. These values are shared by a Discord user across Main/Alt/Farm
governor slots, so the starting architecture decision is a dedicated SQL-backed Discord user
preference/profile store rather than extending `dbo.DiscordGovernorRegistry`.

Keep the first step audit/scope and SQL design only unless implementation is explicitly approved.

## Copy/Paste Starter

```text
Codex, start Phase 12B of the Player Self-Service Command Centre: Discord User Preference Profile Store.

Phase 12 Slice 1 is complete. Mirror PR #176 delivered the Inventory Preferences copy/docs slice,
was merged, and was smoke tested successfully on 2026-06-26. `/me preferences` remains private,
renders the generated Inventory Preferences card, preserves the existing service-backed Inventory
report visibility and Inventory VIP flows, and does not expose unsaved export, stats privacy,
reminder, account, timezone, location, or language controls.

Phase 12B objective:
Add persisted Discord-user-level profile preferences for timezone, location country, and preferred
language. These values are shared by a Discord user across Main/Alt/Farm governor slots, so the
preferred architecture is a dedicated SQL-backed Discord user preference/profile store keyed by
Discord user ID rather than duplicated values on `dbo.DiscordGovernorRegistry`.

Start with audit/scope and SQL design only unless I explicitly approve implementation.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/reference/K98 Bot - Project Engineering Standards.md
- docs/reference/K98 Bot - Coding Execution Guidelines.md
- docs/reference/K98 Bot - Testing Standards.md
- docs/reference/K98 Bot - Skills & Refactor Triggers.md
- docs/reference/K98 Bot - Deferred Optimisation Framework.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md
- docs/task_packs/Player Self-Service Command Centre - Programme Pack.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 12 Preferences Hub Expansion.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 12B Discord User Preference Profile Store.md
- docs/player_self_service_command_centre_briefing.md
- C:\K98-bot-SQL-Server\docs\SQL_DATA_MIGRATION_GUARDRAILS.md
- C:\K98-bot-SQL-Server\docs\SQL_PROMOTION_GUIDE.md
- C:\K98-bot-SQL-Server\docs\SQL_RELEASE_CHECKLIST.md

Use these skills as applicable:
- k98-architecture-scope
- k98-sql-validation
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- codex-security security review before PR handoff because this phase touches user-controlled
  input, SQL/data access, Discord interactions, and restart-sensitive persistence

Scope:
1. Audit current `/me preferences`, Inventory Preferences, account registry, Discord user IDs,
   and existing SQL-backed persistence before changing code.
2. Validate all SQL-facing assumptions against `C:\K98-bot-SQL-Server`; do not infer table,
   column, stored procedure, index, or migration details from Python usage alone.
3. Confirm the dedicated Discord-user preference/profile store design, including table name,
   columns, constraints, indexes, migration, rollback, and service/DAL ownership.
4. Do not duplicate timezone, location country, or preferred language onto
   `dbo.DiscordGovernorRegistry` unless explicitly re-approved after audit.
5. Preserve the current session-based local-time toggle. Stored timezone is planning/profile
   metadata unless a later approved feature uses it.
6. Add only service-backed mutations with validation, clear/remove behavior, restart safety,
   fallback copy, and legacy compatibility.
7. Display only delivered persisted fields on `/me preferences` generated card and fallback copy.
8. Add Manage controls to add, update, and remove delivered values.
9. Preserve `/inventory_preferences`, `/myinventory`, `/me inventory`, `/me exports`,
   `/my_stats_export`, `/export_inventory`, `/me reminders`, `/calendar_reminder_config`,
   `/me accounts`, command registration, export schemas, generated file contracts, and
   public/private response behavior.
10. Update docs and deferred backlog after implementation.

Suggested validation:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\deploy\Validate-SqlRepo.ps1
- .\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_preference_service.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_views.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_service.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_page_cards.py

Manual smoke after implementation:
- `/me preferences` remains private and renders the generated card.
- Existing Inventory visibility still saves, refreshes, and affects report posting.
- Existing Inventory VIP update handoff still works.
- Timezone can be added, updated, removed, and reloaded in a fresh interaction.
- Location country can be added, updated, removed, and reloaded in a fresh interaction.
- Preferred language can be added, updated, removed, and reloaded in a fresh interaction.
- Invalid values are rejected privately with actionable copy.
- The current session-based local-time toggle still behaves as before.
- `/inventory_preferences`, `/myinventory`, `/me inventory`, `/me exports`, `/my_stats_export`,
  `/export_inventory`, `/me reminders`, `/calendar_reminder_config`, and `/me accounts` remain
  behavior-compatible.

Acceptance criteria:
- Phase 12B starts with audit/scope and SQL validation unless implementation is explicitly
  approved.
- Timezone, location country, and preferred language are stored once per Discord user, not once per
  governor slot.
- Every shipped field has validation, service-backed persistence, clear/remove behavior, restart
  safety, fallback copy, and focused tests.
- No placeholder, "coming soon", or unsaved controls are introduced.
- Existing Inventory Preferences, inventory report, export, reminder, account, command
  registration, and public/private behavior is preserved.
- Standard validators, SQL repo validation, focused tests, and selected broader tests pass.
- Codex Security review is run or explicitly documented before PR handoff.
- Docs and deferred backlog are updated after implementation.
```
