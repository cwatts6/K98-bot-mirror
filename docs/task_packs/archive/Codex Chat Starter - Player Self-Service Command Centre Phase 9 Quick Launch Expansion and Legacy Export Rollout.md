# Codex Chat Starter - Player Self-Service Command Centre Phase 9 Quick Launch Expansion and Legacy Export Rollout

Status: historical starter. Phase 9 is delivered in production PR #479 and smoke tested
successfully on 2026-06-25. Use
`docs/task_packs/Codex Chat Starter - Player Self-Service Command Centre Phase 10 Inventory Summary Card.md`
for the next active phase.

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
calendar-only, both, and neither states. KVK and calendar reminder management switch in-place
inside the same private child window. Calendar reminder selections save through the
event-calendar preference service. `/me dashboard` uses the full-bleed generated card style.
Dashboard Quick Launch remains dashboard-only.

Phase 8 Exports Launchpad is delivered in production PR #478 and smoke tested successfully on
2026-06-25. `/me exports` can send default Stats Excel, Stats CSV, Inventory Excel, and Inventory
CSV files privately. All outputs are ephemeral/private. `/me dashboard` does not have a direct
export button. Dashboard Quick Launch `Exports` opens the `/me exports` card correctly.
`/my_stats_export` and `/export_inventory` still work. Export schema/format redesign was not
included.

Source documents:

- `docs/task_packs/Player Self-Service Command Centre - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 9 Quick Launch Expansion and Legacy Export Rollout.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 8 Exports Launchpad and Quick Launch Expansion.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

## Copy/Paste Starter

```text
Codex, start Phase 9 of the Player Self-Service Command Centre: Quick Launch Expansion and Legacy
Export Rollout.

Phase 1 audit/design is complete and archived.

Phase 2 is delivered and smoke tested successfully in mirror PR #164 and production PR #472. The
delivered `/me` shell includes `/me dashboard`, `/me accounts`, `/me reminders`,
`/me preferences`, and `/me exports`. It is private. Dashboard Quick Launch works and shows
guidance. Existing legacy commands still work.

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
Inventory CSV files. All outputs are ephemeral/private. `/me dashboard` does not have a direct
export button. Quick Launch `Exports` opens the `/me exports` card correctly. `/my_stats_export`
and `/export_inventory` still work. Export schema and file-format redesign was explicitly left out
of scope.

Phase 9 objective:
Decide whether Dashboard Quick Launch should remain dashboard-only guidance or expand into a
richer launch surface, and decide the first safe rollout step for legacy export commands after
Phase 8 validated `/me exports`.

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
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 9 Quick Launch Expansion and Legacy Export Rollout.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 8 Exports Launchpad and Quick Launch Expansion.md
- docs/player_self_service_command_centre_briefing.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation if SQL-backed usage/export assumptions are touched
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- codex-security security review or documented skip before PR handoff

Scope:
1. Audit Dashboard Quick Launch targets: `/kvk stats`, `/kvk targets`, `/kvk history`,
   `/kvk rankings`, `/myinventory`, and `/me exports`.
2. Map each target command's channel gates, admin overrides, permission model, response
   visibility, output privacy, required parameters, and interaction timing.
3. Decide whether Quick Launch remains dashboard-only guidance, becomes richer dashboard actions,
   becomes reusable on selected `/me` pages, or splits guidance-only/direct-action targets.
4. Implement only launch controls that preserve every target command's existing channel,
   visibility, permission, privacy, and argument rules.
5. Review `/my_stats_export` and `/export_inventory` usage, smoke feedback, player communication,
   and compatibility needs.
6. Decide whether legacy export commands should remain live, redirect to `/me exports`, or enter a
   no-feedback deprecation window.
7. Preserve `/my_stats_export` and `/export_inventory` unless redirect/removal is explicitly
   approved.
8. Keep `commands/me_cmds.py`, command modules, and views thin.
9. Keep service logic Discord-type-free except adapter/view code.
10. Keep shared visual-card renderer consolidation inside this programme but out of Phase 9 unless
    explicitly approved.
11. Keep export schema/format redesign out of this programme by default; treat it as a separate
    export-output programme unless a later approved slice is narrow and backwards-compatible.

Most effective delivery order:
1. Audit Quick Launch target rules and legacy export usage.
2. Recommend the launch model and legacy export rollout option.
3. Stop for approval before direct Quick Launch actions or legacy redirects/removal.
4. Implement the approved Phase 9 slice.
5. Update command reference, briefing, tests, and deferred backlog.

Likely files:
- commands/me_cmds.py
- commands/kvk_cmds.py
- commands/stats_cmds.py
- commands/inventory_cmds.py
- player_self_service/service.py
- player_self_service/page_cards.py
- ui/views/player_self_service_views.py
- ui/views/player_self_service_export_views.py
- tests/test_me_cmds.py
- tests/test_player_self_service_service.py
- tests/test_player_self_service_views.py
- tests/test_player_self_service_page_cards.py
- tests/test_player_self_service_export_views.py
- tests/test_my_stats_export_command.py
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
- .\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_views.py tests\test_player_self_service_page_cards.py tests\test_player_self_service_export_views.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_my_stats_export_command.py tests\test_stats_export.py tests\test_stats_exporter_csv.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_*.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py

Acceptance criteria:
- Phase 9 begins with audit/scope unless one-pass implementation is explicitly approved.
- Every Quick Launch target's channel, visibility, permission, privacy, and argument rules are
  mapped before direct launch controls are designed.
- Dashboard-only Quick Launch remains unchanged unless expansion is explicitly approved and
  validated.
- Any expanded launch path preserves the target command's existing rules.
- `/my_stats_export` and `/export_inventory` remain live unless explicit redirect/removal approval
  is recorded.
- No export schema, file format, SQL, or output redesign is included.
- Shared visual-card renderer consolidation remains captured for a later programme phase.
- Focused tests and standard validators pass.
- Codex Security is run or explicitly justified.
```
