# Codex Chat Starter - Player Self-Service Command Centre Phase 8 Exports Launchpad and Quick Launch Expansion

Status: active starter for the next Player Self-Service Command Centre phase.

Phase 1 audit/design is complete and archived.

Phase 2 `/me` Command Shell and Navigation Foundation is delivered in mirror PR #164 and
production PR #472, smoke tested successfully, and remains the command shell foundation.

Phase 3 Modern Account Centre is delivered in mirror PR #165 and smoke tested successfully by the
operator on 2026-06-22. `/me accounts` supports private account review, Governor ID lookup,
registration, replacement, removal with confirmation, and return navigation. Legacy account
commands remain live.

Phase 4 Modern Reminder Centre is delivered in mirror PR #166 and production PR #474. Smoke
testing confirmed `/me reminders` supports private KVK reminder review, subscribe/update through
event/time selectors, unsubscribe with confirmation, and best-effort confirmation DMs. Legacy KVK
reminder commands remain live.

Important KVK reminder semantics to preserve:

- `Ruins` means non-fight ruins events.
- `Altars` means altar fights.
- `Major` means all major timeline events.
- `Fights` means altar fights plus major events whose title/description contains `FIGHT`.
- `fights + altars` saves as `fights`.
- `major + fights` keeps both.
- `ruins + major + fights` saves as `all`.
- `ruins + major + altars` saves as `all`.

Phase 5 Visual Dashboard Card and Preferences Hub is delivered in production PR #475 and smoke
tested successfully on desktop, mobile, and iPad. `/me dashboard` gained a generated private
dashboard card with safe embed fallback. `/me preferences` can update inventory report visibility
through the existing service-backed persistence path.

Phase 6 Guided Management Cards and Workflow Simplification is delivered in mirror PR #168 and
smoke tested successfully on 2026-06-24. Accounts, Reminders, Preferences, and Exports use
generated private cards with safe embed fallback. Accounts and KVK reminders are simplified around
one primary `Manage` journey each. KVK reminder event/time selections auto-save and refresh the
card. Preferences include inventory visibility toggle and Governor VIP update access. Exports
remain private guidance without dashboard Quick Launch.

Phase 7 Unified Reminder Centre and Dashboard Card Alignment is delivered in production PR #477
and smoke tested successfully on 2026-06-25. `/me reminders` now represents KVK-only,
calendar-only, both, and neither states. The reminder Manage journey can switch in-place between
KVK reminder and calendar reminder management. Calendar reminder selections auto-save through the
event-calendar preference service, while `/calendar_reminder_config` remains live. `/me dashboard`
now uses the Phase 6 full-bleed card style, with large row-based text directly on the card.
Dashboard Quick Launch remains dashboard-only and `/me exports` intentionally does not include it.

Source documents:

- `docs/task_packs/Player Self-Service Command Centre - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 8 Exports Launchpad and Quick Launch Expansion.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 7 Unified Reminder Centre and Dashboard Card Alignment.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

## Copy/Paste Starter

```text
Codex, start Phase 8 of the Player Self-Service Command Centre: Exports Launchpad and Quick
Launch Expansion.

Phase 1 audit/design is complete and archived.

Phase 2 is delivered and smoke tested successfully in mirror PR #164 and production PR #472. The
delivered `/me` shell includes `/me dashboard`, `/me accounts`, `/me reminders`,
`/me preferences`, and `/me exports`. It is private. Dashboard Quick Launch works and shows
guidance. `/me exports` opens only the exports page and intentionally does not include the
dashboard Quick Launch menu. Existing legacy commands still work.

Phase 3 Modern Account Centre is delivered in mirror PR #165 and smoke tested successfully by the
operator on 2026-06-22. `/me accounts` supports private account review, Governor ID lookup,
registration, replacement, removal with confirmation, and return navigation. Legacy account
commands remain live.

Phase 4 Modern Reminder Centre is delivered in mirror PR #166 and production PR #474. Smoke testing
confirmed it is working correctly. `/me reminders` supports private KVK reminder review,
subscribe/update through event/time selectors, unsubscribe with confirmation, and best-effort
confirmation DMs. Legacy reminder commands remain live.

Important KVK reminder semantics to preserve:
- `Ruins` means non-fight ruins events.
- `Altars` means altar fights.
- `Major` means all major timeline events.
- `Fights` means altar fights plus major events whose title/description contains `FIGHT`.
- `fights + altars` saves as `fights`.
- `major + fights` keeps both.
- `ruins + major + fights` saves as `all`.
- `ruins + major + altars` saves as `all`.

Phase 5 Visual Dashboard Card and Preferences Hub is delivered in production PR #475 and smoke
tested successfully on desktop, mobile, and iPad. `/me dashboard` has a generated private dashboard
card with safe embed fallback. `/me preferences` can update inventory report visibility through
the existing service-backed persistence path.

Phase 6 Guided Management Cards and Workflow Simplification is delivered in mirror PR #168 and
smoke tested successfully on 2026-06-24. Accounts, Reminders, Preferences, and Exports use
generated private cards with safe embed fallback. Accounts and KVK reminders are simplified around
one primary `Manage` journey each. KVK reminder event/time selections auto-save and refresh the
card. Preferences include a single inventory visibility toggle and Governor VIP update access.
Exports remain private guidance without dashboard Quick Launch. Main cards and reminder child
selector windows timeout gracefully. Legacy self-service commands remain live.

Phase 7 Unified Reminder Centre and Dashboard Card Alignment is delivered in production PR #477
and smoke tested successfully on 2026-06-25. `/me dashboard` uses the Phase 6 full-bleed card
style with large row-based text directly on the card. `/me reminders` now covers both KVK event
reminders and calendar reminders, including KVK-only, calendar-only, both, and neither states.
KVK and calendar reminder management switch in-place inside the same private child window, and
their Remove All buttons align consistently. Calendar reminder preferences save through the
existing event-calendar preference service. Dashboard Quick Launch remains dashboard-only and
`/me exports` intentionally does not include it.

Phase 8 objective:
Turn `/me exports` from passive private guidance into a safe personal export launchpad where the
existing export services support it, and decide whether Quick Launch should remain dashboard-only
or expand into a richer launch surface.

Start with audit/scope only unless I explicitly approve one-pass implementation.

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
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 8 Exports Launchpad and Quick Launch Expansion.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 7 Unified Reminder Centre and Dashboard Card Alignment.md
- docs/player_self_service_command_centre_briefing.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation if SQL-backed export contracts are touched
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- codex-security security review or documented skip before PR handoff

Scope:
1. Audit current personal export paths, especially `/my_stats_export` and `/export_inventory`.
2. Map export authorization, file generation, private delivery, error handling, cooldown or
   long-running behavior, and Discord interaction timing before designing direct controls.
3. Design one `/me exports` status/action model for unavailable, guidance-only, and actionable
   export states.
4. Add direct `/me exports` export actions only where existing service-backed authorization and
   private file delivery are validated.
5. Preserve `/my_stats_export`, `/export_inventory`, and all other legacy commands.
6. Preserve dashboard-only Quick Launch unless expansion is explicitly approved and validated.
7. If Quick Launch expands, preserve every target command's existing channel, visibility,
   permission, and privacy rules.
8. Keep `commands/me_cmds.py` thin.
9. Keep service/export logic Discord-type-free except adapter/view code.
10. Update `/me exports` card copy and controls to match the Phase 7 card style.
11. Capture out-of-scope preference expansion, legacy redirect/removal, export schema redesign,
    public output redesign, and renderer-helper consolidation structurally.

Most effective delivery order:
1. Audit export authorization and file-delivery contracts.
2. Design `/me exports` statuses and action model.
3. Refresh the `/me exports` card copy/control layout.
4. Add direct export controls only if the audit proves the service-backed private delivery path is
   safe for this phase.
5. Decide Quick Launch expansion only after target command channel/visibility rules are mapped.

Likely files:
- commands/me_cmds.py
- commands/stats_cmds.py
- commands/inventory_cmds.py
- player_self_service/service.py
- player_self_service/page_cards.py
- ui/views/player_self_service_views.py
- inventory/
- stats/
- services/
- tests/test_me_cmds.py
- tests/test_player_self_service_service.py
- tests/test_player_self_service_views.py
- tests/test_player_self_service_page_cards.py
- tests/test_inventory_*.py
- tests/test_stats_export*.py
- tests/test_my_stats_export_command.py
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Suggested validation:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_views.py tests\test_player_self_service_page_cards.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_stats_export.py tests\test_my_stats_export_command.py tests\test_stats_exporter_csv.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_*.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py

Acceptance criteria:
- Phase 8 begins with audit/scope unless one-pass implementation is explicitly approved.
- Export authorization, private file delivery, interaction timing, and legacy compatibility are
  mapped before direct actions are designed.
- `/me exports` can represent unavailable, guidance-only, and actionable export states without
  misleading users.
- Direct export controls are implemented only where service-backed authorization and private
  delivery are validated.
- No export persistence, SQL, or file generation logic is added to commands or views.
- Dashboard Quick Launch remains dashboard-only unless expansion is explicitly approved and
  validated.
- Legacy export commands remain live.
- Existing target command visibility, channel, and permission rules are preserved.
- Focused tests and standard validators pass.
- Codex Security is run or explicitly justified.
```
