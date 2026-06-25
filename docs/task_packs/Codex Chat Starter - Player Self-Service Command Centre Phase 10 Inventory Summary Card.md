# Codex Chat Starter - Player Self-Service Command Centre Phase 10 Inventory Summary Card

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
tested successfully on desktop, mobile, and iPad. `/me dashboard` has a generated private dashboard
card with safe embed fallback. `/me preferences` can update inventory report visibility through
the existing service-backed persistence path.

Phase 6 Guided Management Cards and Workflow Simplification is delivered in mirror PR #168 and
smoke tested successfully on 2026-06-24. Accounts, Reminders, Preferences, and Exports use
generated private cards with safe embed fallback. Accounts and KVK reminders are simplified around
one primary `Manage` journey each. KVK reminder event/time selections auto-save and refresh the
card. Preferences include a single inventory visibility toggle and Governor VIP update access.
Main cards and reminder child selector windows timeout gracefully. Legacy self-service commands
remain live.

Phase 7 Unified Reminder Centre and Dashboard Card Alignment is delivered in production PR #477
and smoke tested successfully on 2026-06-25. `/me dashboard` uses the Phase 6 full-bleed card
style with large row-based text directly on the card. `/me reminders` covers both KVK event
reminders and calendar reminders, including KVK-only, calendar-only, both, and neither states.
KVK and calendar reminder management switch in-place inside the same private child window.
Calendar reminder preferences save through the existing event-calendar preference service.
Dashboard Quick Launch remains dashboard-only.

Phase 8 Exports Launchpad is delivered in production PR #478 and smoke tested successfully on
2026-06-25. `/me exports` can send default private Stats Excel, Stats CSV, Inventory Excel, and
Inventory CSV files. All outputs are ephemeral/private. `/me dashboard` does not have a direct
export button. Quick Launch `Exports` opens the `/me exports` card correctly. `/my_stats_export`
and `/export_inventory` still work. Export schema and file-format redesign was explicitly left out
of scope.

Phase 9 Quick Launch and Export Options is delivered in production PR #479 and smoke tested
successfully on 2026-06-25. `/me dashboard` no longer includes risky KVK Quick Launch targets for
`/kvk stats`, `/kvk targets`, `/kvk history`, or `/kvk rankings`. Inventory and Exports are the
safe private dashboard handoffs. `/me exports` is the preferred export route with private Stats
and Inventory option windows. `/my_stats_export` and `/export_inventory` remain live. Smoke
testing confirmed Inventory works and cards are produced as expected, but Inventory now needs its
own `/me` summary card so it is not only represented as a report/export handoff.

Source documents:

- `docs/task_packs/Player Self-Service Command Centre - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 10 Inventory Summary Card.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 9 Quick Launch Expansion and Legacy Export Rollout.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

## Copy/Paste Starter

```text
Codex, start Phase 10 of the Player Self-Service Command Centre: Inventory Summary Card.

Phase 1 audit/design is complete and archived.

Phase 2 is delivered and smoke tested successfully in mirror PR #164 and production PR #472. The
delivered `/me` shell includes `/me dashboard`, `/me accounts`, `/me reminders`,
`/me preferences`, and `/me exports`. It is private. Existing legacy commands still work.

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
Main cards and reminder child selector windows timeout gracefully. Legacy self-service commands
remain live.

Phase 7 Unified Reminder Centre and Dashboard Card Alignment is delivered in production PR #477
and smoke tested successfully on 2026-06-25. `/me dashboard` uses the Phase 6 full-bleed card
style with large row-based text directly on the card. `/me reminders` covers both KVK event
reminders and calendar reminders, including KVK-only, calendar-only, both, and neither states.
KVK and calendar reminder management switch in-place inside the same private child window.
Calendar reminder preferences save through the existing event-calendar preference service.
Dashboard Quick Launch remains dashboard-only.

Phase 8 Exports Launchpad is delivered in production PR #478 and smoke tested successfully on
2026-06-25. `/me exports` can send default private Stats Excel, Stats CSV, Inventory Excel, and
Inventory CSV files. All outputs are ephemeral/private. `/my_stats_export` and
`/export_inventory` still work. Export schema and file-format redesign was explicitly left out of
scope.

Phase 9 Quick Launch and Export Options is delivered in production PR #479 and smoke tested
successfully on 2026-06-25. `/me dashboard` now has safe private Inventory and Exports handoffs
and no KVK Quick Launch targets. `/me exports` has private Stats and Inventory option windows with
Download/Cancel. Main `/me` pages have consistent navigation/button styling and graceful timeout
behavior. `/my_stats_export`, `/export_inventory`, and legacy self-service commands remain live.

Phase 10 objective:
Create an Inventory summary card so Inventory feels like a first-class `/me` destination. Use the
prepared `assets/me/cards/me inventory.png` background. The card should summarize latest approved
inventory data across three rows: resources and values, speedups and values, and materials and
values. If a player has no approved inventory data, point them toward the inventory upload
channel/process. Preserve the existing `/myinventory` report journey, timescale controls, report
visibility behavior, and export buttons.

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
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 10 Inventory Summary Card.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 9 Quick Launch Expansion and Legacy Export Rollout.md
- docs/player_self_service_command_centre_briefing.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation if SQL-backed inventory assumptions are touched
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- codex-security security review or documented skip before PR handoff

Scope:
1. Audit current inventory data sources, approved-data rules, service/DAL boundaries, report
   helpers, export helpers, and `/myinventory` defaults.
2. Validate any SQL-backed inventory table/view/procedure/column assumptions against
   `C:\K98-bot-SQL-Server`.
3. Decide whether to add `/me inventory` as a sixth private subcommand or keep Inventory as a
   private navigation page only.
4. Add a private generated Inventory summary card using `assets/me/cards/me inventory.png` and safe
   embed fallback.
5. Summarize resources, speedups, and materials with values where latest approved data exists.
6. Handle no-account, no-approved-data, partial-data, and unavailable-data states without leaking
   private data.
7. Point players with no approved inventory data toward the inventory upload channel/process.
8. Preserve `/myinventory`, report visibility preferences, report timescale controls, and report
   export buttons.
9. Keep command modules and views thin; keep business logic in service/DAL layers.
10. Keep shared visual-card renderer consolidation, legacy export redirects/removal, export
    schema redesign, and broader preferences expansion out of Phase 10.
11. Update command reference, briefing, programme docs, tests, and deferred backlog.

Likely files:
- commands/me_cmds.py
- commands/inventory_cmds.py
- player_self_service/service.py
- player_self_service/page_cards.py
- player_self_service/dashboard_card.py
- ui/views/player_self_service_views.py
- ui/views/inventory_report_views.py
- inventory/
- assets/me/cards/me inventory.png
- tests/test_me_cmds.py
- tests/test_player_self_service_service.py
- tests/test_player_self_service_views.py
- tests/test_player_self_service_page_cards.py
- tests/test_inventory_*.py
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
- .\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_*.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py

Acceptance criteria:
- Phase 10 begins with audit/scope unless one-pass implementation is explicitly approved.
- Inventory data sources, approved-data rules, and SQL-backed assumptions are mapped before card
  values are designed.
- `/me` Inventory behavior is decided explicitly: new `/me inventory` subcommand or navigation
  page only.
- The Inventory summary card uses `assets/me/cards/me inventory.png`.
- Summary rows cover resources, speedups, and materials with values where available.
- No-account and no-approved-data states guide players without leaking private data.
- Existing `/myinventory` report behavior, timescale controls, visibility preference, and export
  buttons are preserved.
- No inventory import OCR/review redesign, report schema redesign, export schema redesign, or
  shared renderer consolidation is included.
- Focused tests and standard validators pass.
- Codex Security is run or explicitly justified.
```
