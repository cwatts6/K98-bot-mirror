# Codex Chat Starter - Player Self-Service Command Centre Phase 11 Shared Visual-Card Renderer Consolidation

Status: archived completed starter for Phase 11. Phase 11A, Phase 11B, and Phase 11C are delivered and
smoke tested, so Phase 11 Shared Visual-Card Renderer Consolidation is complete. The next planned
Player Self-Service slice is Phase 12 Preferences Hub Expansion.

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
Inventory CSV files. All outputs are ephemeral/private. `/my_stats_export` and
`/export_inventory` still work. Export schema and file-format redesign was explicitly left out of
scope.

Phase 9 Quick Launch and Export Options is delivered in production PR #479 and smoke tested
successfully on 2026-06-25. `/me dashboard` now has safe private Inventory and Exports handoffs
and no KVK Quick Launch targets. `/me exports` has private Stats and Inventory option windows with
Download/Cancel. Main `/me` pages have consistent navigation/button styling and graceful timeout
behavior. `/my_stats_export`, `/export_inventory`, and legacy self-service commands remain live.

Phase 10 Inventory Summary Card is delivered in production PR #480 and smoke tested successfully
on 2026-06-26. `/me inventory` is now the sixth private `/me` subcommand. It uses
`assets/me/cards/me inventory.png`, summarizes latest approved resources, speedups, and materials,
handles no-account/no-approved-data/partial-data states privately, and preserves the existing
`/myinventory` report journey, timescale controls, report visibility behavior, and export buttons.
Final smoke feedback confirmed all cards and commands worked; a layout polish moved the Inventory
action block clear of the Materials row.

Phase 11A Shared Visual-Card Renderer Consolidation is delivered in mirror PR #173 and production
PR #481 and smoke tested successfully on 2026-06-26. It extracted `core.visual_text`, migrated
`/me` page cards to the shared text primitives, preserved PreKvK compatibility wrappers, added
focused helper and renderer tests, included the rendered `phase11_me_dashboard_smoke.png` visual
artifact, and kept command, SQL/data, export, preference, and Discord visibility behavior
unchanged.

Source documents:

- `docs/task_packs/Player Self-Service Command Centre - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 11 Shared Visual-Card Renderer Consolidation.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 10 Inventory Summary Card.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

## Copy/Paste Starter

```text
Codex, start Phase 11 of the Player Self-Service Command Centre: Shared Visual-Card Renderer Consolidation.

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

Phase 10 Inventory Summary Card is delivered in production PR #480 and smoke tested successfully
on 2026-06-26. `/me inventory` is private, uses `assets/me/cards/me inventory.png`, summarizes
latest approved inventory resources/speedups/materials, handles no-account/no-data/partial-data
states privately, and preserves `/myinventory`, report visibility, timescale controls, and export
buttons. Final smoke feedback confirmed all cards and commands worked; a layout polish moved the
Inventory action block clear of the Materials row.

Phase 11 objective:
Consolidate stable visual-card rendering primitives now that the `/me` card surfaces are stable.
Audit duplicated Pillow rendering patterns across player self-service, KVK, PreKvK, and inventory
renderers. Extract only stable primitives such as font loading, glyph-safe fallback, text
measurement, fit-to-width sizing, wrapped/shadowed text drawing, badge/pill drawing where reusable,
and PNG/BytesIO output helpers. Migrate one renderer family at a time while preserving visual
output, filenames, dimensions, fallback behavior, Unicode handling, and Discord visibility.

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
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 11 Shared Visual-Card Renderer Consolidation.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 10 Inventory Summary Card.md
- docs/player_self_service_command_centre_briefing.md

Use these skills as applicable:
- k98-architecture-scope
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- codex-security security review or documented skip before PR handoff

Scope:
1. Audit duplicated renderer primitives across `/me`, KVK, PreKvK, and inventory renderers.
2. Decide which primitives are stable enough to share without forcing a single layout framework.
3. Choose one renderer family for the first migration slice, preferably `/me` unless audit shows a
   safer first target.
4. Preserve existing image dimensions, filenames, attachment names, text content, fallback embeds,
   Unicode/player-name handling, and public/private output behavior.
5. Add focused helper and renderer tests.
6. Render at least one representative local PNG for visual inspection.
7. Keep command registration, SQL/data contracts, export schemas, preferences expansion, and
   legacy redirects/removal out of scope.
8. Update docs and deferred backlog.

Likely files:
- player_self_service/page_cards.py
- player_self_service/dashboard_card.py
- core/
- kvk/rendering/
- prekvk/report_image_renderer.py
- inventory/report_image_renderer.py
- tests/test_player_self_service_page_cards.py
- tests/test_player_self_service_dashboard_card.py
- tests/test_kvk_*renderer*.py
- tests/test_inventory_report_image_renderer.py
- tests/test_prekvk_report_image_renderer.py
- docs/player_self_service_command_centre_briefing.md
- docs/reference/deferred_optimisations.md
- docs/task_packs/Player Self-Service Command Centre - Programme Pack.md

Suggested validation:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_page_cards.py tests\test_player_self_service_dashboard_card.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_targets_card_renderer.py tests\test_kvk_stats_card_renderer.py tests\test_kvk_rankings_card_renderer.py tests\test_kvk_history_renderer.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_report_image_renderer.py tests\test_prekvk_report_image_renderer.py

Acceptance criteria:
- Phase 11 starts with audit/scope unless one-pass implementation is explicitly approved.
- Renderer duplication is mapped before shared helpers are introduced.
- Only stable primitives are extracted.
- At most one renderer family is migrated in the first implementation slice unless explicitly
  approved.
- Existing card dimensions, filenames, attachment names, fallback behavior, and visibility are
  preserved.
- No command, SQL, export schema, preference, or legacy redirect behavior changes are included.
- Focused renderer/helper tests and standard validators pass.
- At least one rendered PNG smoke artifact is inspected before handoff.
- Deferred backlog is updated to reflect the completed slice or remaining renderer work.
```
