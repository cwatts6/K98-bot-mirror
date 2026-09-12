# Codex Chat Starter - Player Self-Service Command Centre Phase 7 Unified Reminder Centre and Dashboard Card Alignment

Status: historical starter. Phase 7 is delivered in production PR #477 and smoke tested
successfully on 2026-06-25. Use
`docs/task_packs/Codex Chat Starter - Player Self-Service Command Centre Phase 8 Exports Launchpad and Quick Launch Expansion.md`
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

Important Phase 4 reminder semantics to preserve:

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
the existing service-backed persistence path. Dashboard Quick Launch remains dashboard-only.

Phase 6 Guided Management Cards and Workflow Simplification is delivered in mirror PR #168 and
smoke tested successfully by the operator on 2026-06-24.

Delivered Phase 6 scope:

- `/me accounts`, `/me reminders`, `/me preferences`, and `/me exports` render generated private
  cards with safe embed fallback.
- Account controls are simplified around one primary `Manage` journey.
- Governor ID lookup results can continue into register/replace slot selection.
- Duplicate/invalid Governor ID feedback is surfaced earlier in the account journey.
- KVK reminder event type and reminder time selections save automatically.
- Reminder card refresh works after autosave.
- Remove All/unsubscribe uses confirmation.
- Preferences use one inventory visibility toggle and can open the existing Governor VIP update
  flow.
- Preference cards show account VIP levels where available.
- Exports remain private guidance and do not gain dashboard Quick Launch.
- Main cards and reminder child selector windows timeout gracefully.
- Legacy self-service commands remain live.

Important Phase 6 follow-ups for Phase 7:

- Calendar reminders are still managed through `/calendar_reminder_config`. They are distinct from
  KVK event reminders in code, but players experience KVK reminders and calendar reminders as the
  same reminder domain. A player can have KVK reminders, calendar reminders, both, or neither.
- `/me dashboard` now looks visually out of step with the newer Accounts, Reminders, Preferences,
  and Exports cards. Refresh the dashboard to the same visual style while preserving dashboard
  Quick Launch.

Source documents:

- `docs/task_packs/Player Self-Service Command Centre - Programme Pack.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 7 Unified Reminder Centre and Dashboard Card Alignment.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 6 Guided Management Cards and Workflow Simplification.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/events_and_dm_reminders.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

## Copy/Paste Starter

```text
Codex, start Phase 7 of the Player Self-Service Command Centre: Unified Reminder Centre and
Dashboard Card Alignment.

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

Important Phase 4 KVK reminder semantics to preserve:
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
the existing service-backed persistence path. Dashboard Quick Launch remains dashboard-only, and
`/me exports` intentionally does not include it.

Phase 6 Guided Management Cards and Workflow Simplification is delivered in mirror PR #168 and
smoke tested successfully on 2026-06-24. Accounts, Reminders, Preferences, and Exports now use
generated private cards with safe embed fallback. Accounts and KVK reminders are simplified around
one primary `Manage` journey each. KVK reminder event/time selections auto-save and refresh the
card. Preferences include a single inventory visibility toggle and Governor VIP update access.
Exports remain private guidance without dashboard Quick Launch. Main cards and reminder child
selector windows timeout gracefully. Legacy self-service commands remain live.

Phase 7 objective:
Make `/me reminders` account for both KVK event reminders and calendar reminders, while refreshing
`/me dashboard` so the command-centre home matches the Phase 6 card style.

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
- docs/reference/events_and_dm_reminders.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md
- docs/task_packs/Player Self-Service Command Centre - Programme Pack.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 7 Unified Reminder Centre and Dashboard Card Alignment.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 6 Guided Management Cards and Workflow Simplification.md
- docs/player_self_service_command_centre_briefing.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation if SQL-backed contracts are touched
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- codex-security security review or documented skip before PR handoff

Scope:
1. Audit KVK event reminder state and calendar reminder preference/state code together.
2. Map persistence, scheduler, restart, timezone/lead-time, and legacy command compatibility for
   calendar reminders before designing write controls.
3. Design one `/me reminders` status model for users with KVK-only reminders, calendar-only
   reminders, both, or neither.
4. Add calendar reminder status to `/me reminders` where the audit confirms a safe read path.
5. Add calendar reminder management through `/me reminders` only where service-backed persistence,
   restart safety, timezone/lead-time semantics, and legacy compatibility are validated.
6. Preserve Phase 4/6 KVK reminder semantics and autosave behavior.
7. Refresh `/me dashboard` to match the Phase 6 full-bleed subpage card style.
8. Preserve dashboard-only Quick Launch and `/me exports` no-Quick-Launch behavior.
9. Keep `commands/me_cmds.py` thin.
10. Keep service and renderer logic Discord-type-free except view/adapter code.
11. Preserve `/calendar_reminder_config`, `/subscribe`, `/modify_subscription`, `/unsubscribe`,
    and all other legacy commands.
12. Capture out-of-scope export launchpad, preference expansion, legacy redirect/removal, public
    calendar redesign, and renderer-helper consolidation structurally.

Most effective delivery order:
1. Audit and design the unified reminder model.
2. Refresh the dashboard card visual style because it is low-risk and highly visible.
3. Add read-only calendar reminder status to `/me reminders`.
4. Add calendar reminder mutation controls only if the audit proves the persistence/restart model
   is safe for this phase.

Likely files:
- commands/me_cmds.py
- commands/calendar_cmds.py
- player_self_service/service.py
- player_self_service/reminder_service.py
- player_self_service/dashboard_card.py
- player_self_service/page_cards.py
- event_calendar/reminder_prefs.py
- event_calendar/reminder_prefs_store.py
- event_calendar/reminders.py
- ui/views/player_self_service_views.py
- ui/views/player_self_service_reminder_views.py
- ui/views/reminder_config.py
- tests/test_me_cmds.py
- tests/test_player_self_service_service.py
- tests/test_player_self_service_reminder_service.py
- tests/test_player_self_service_views.py
- tests/test_player_self_service_dashboard_card.py
- tests/test_player_self_service_page_cards.py
- tests/test_calendar_reminder_prefs.py
- tests/test_calendar_reminders.py
- tests/test_calendar_reminders_dispatch.py
- tests/test_calendar_views.py
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Suggested validation:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_reminder_service.py tests\test_player_self_service_views.py tests\test_player_self_service_dashboard_card.py tests\test_player_self_service_page_cards.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_calendar_reminder_prefs.py tests\test_calendar_reminders.py tests\test_calendar_reminders_dispatch.py tests\test_calendar_views.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py

Acceptance criteria:
- Phase 7 begins with audit/scope unless one-pass implementation is explicitly approved.
- KVK reminder and calendar reminder persistence/state contracts are mapped before mutation
  controls are designed.
- `/me reminders` can represent KVK-only, calendar-only, both, and neither states.
- Calendar reminder management is implemented only if service-backed persistence and restart
  safety are validated; otherwise it is explicitly deferred with a precise blocker.
- KVK reminder semantics and autosave behavior remain intact.
- Calendar reminder timezone/lead-time/scheduler semantics remain intact.
- `/me dashboard` is visually aligned with Phase 6 subpage cards.
- Dashboard Quick Launch remains dashboard-only.
- Legacy self-service and calendar reminder commands remain live.
- No persistence writes are added to commands or views.
- Focused tests and standard validators pass.
- Codex Security is run or explicitly justified.
```
