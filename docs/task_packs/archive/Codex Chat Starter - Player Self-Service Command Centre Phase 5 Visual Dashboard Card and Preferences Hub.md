# Codex Chat Starter - Player Self-Service Command Centre Phase 5 Visual Dashboard Card and Preferences Hub

Status: historical starter. Phase 5 is complete. Phases 6 and 7 are also delivered and archived.
Use
`docs/task_packs/Codex Chat Starter - Player Self-Service Command Centre Phase 8 Exports Launchpad and Quick Launch Expansion.md`
for the next active phase.

Phase 1 audit/design is complete and archived.

Phase 2 `/me` Command Shell and Navigation Foundation is delivered in mirror PR #164 and
production PR #472 and smoke tested successfully.

Phase 3 Modern Account Centre is delivered in mirror PR #165 and smoke tested successfully by the
operator on 2026-06-22. `/me accounts` now supports private account review, Governor ID lookup,
registration, replacement, removal with confirmation, and return navigation. Legacy account
commands remain live.

Phase 4 Modern Reminder Centre is delivered in mirror PR #166 and production PR #474. Operator
smoke testing confirmed the reminder centre is working correctly after the fight-category
normalisation fix.

Delivered Phase 4 context:

- `/me reminders` remains private.
- Players can review reminder setup.
- Players can subscribe and update event types/timings through the Manage flow.
- Unsubscribe requires confirmation.
- Confirmation DMs are best-effort and non-blocking.
- Legacy reminder commands remain live: `/subscribe`, `/modify_subscription`, and `/unsubscribe`.
- Reminder persistence continues to use the existing subscription tracker path.
- Scheduler/restart behavior remains on the existing legacy KVK DM reminder path.
- The KVK reminder event source for this flow is Google Sheets to runtime JSON cache, not SQL.
- Category semantics are now:
  - `Ruins`: non-fight ruins events.
  - `Altars`: altar fights.
  - `Major`: all major timeline events, fight and non-fight.
  - `Fights`: altar fights plus major events whose title/description contains `FIGHT`.
- Overlapping reminder selections are normalized to avoid duplicate DMs:
  - `fights + altars` saves as `fights`.
  - `major + fights` keeps both.
  - `ruins + major + fights` saves as `all`.
  - `ruins + major + altars` saves as `all`.

Known follow-ups to preserve:

- Phase 3 account-centre lookup-to-register flow still needs a future optimization so selected
  lookup results can carry into register/replace flows without manual ID re-entry.
- Phase 4 legacy reminder commands can later be routed through the modern reminder service, then
  redirected or removed only after separate operator approval.

Source documents:

- `docs/task_packs/Player Self-Service Command Centre - Programme Pack.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 5 Visual Dashboard Card and Preferences Hub.md`
- `docs/task_packs/archive/Player Self-Service Command Centre - Phase 1 Audit and Design Report.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 2 Command Shell and Navigation Foundation.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 3 Modern Account Centre.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 4 Modern Reminder Centre.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

## Copy/Paste Starter

```text
Codex, start Phase 5 of the Player Self-Service Command Centre: Visual Dashboard Card and
Preferences Hub.

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

Important Phase 3 follow-up to preserve:
The path from `Find ID` to `Register` is still too manual. Players can look up an ID by name or
partial name, but then need another click and must remember/re-enter the 9-digit ID to register the
account. Preserve this later optimisation item unless Phase 5 explicitly scopes account-centre
process work.

Phase 4 Modern Reminder Centre is delivered in mirror PR #166 and production PR #474. Smoke testing
confirmed it is working correctly. `/me reminders` supports private review, subscribe/update
through event/time selectors, unsubscribe with confirmation, and best-effort confirmation DMs.
Legacy reminder commands remain live.

Important Phase 4 reminder semantics to preserve:
- `Ruins` means non-fight ruins events.
- `Altars` means altar fights.
- `Major` means all major timeline events.
- `Fights` means altar fights plus major events whose title/description contains `FIGHT`.
- `fights + altars` saves as `fights`.
- `major + fights` keeps both.
- `ruins + major + fights` saves as `all`.
- `ruins + major + altars` saves as `all`.

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
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 5 Visual Dashboard Card and Preferences Hub.md
- docs/task_packs/archive/Player Self-Service Command Centre - Phase 1 Audit and Design Report.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 2 Command Shell and Navigation Foundation.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 3 Modern Account Centre.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 4 Modern Reminder Centre.md
- docs/player_self_service_command_centre_briefing.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation if SQL-backed contracts are touched
- k98-test-selection
- k98-deferred-optimisation-capture for process simplification or out-of-scope debt
- k98-pr-review before handoff
- codex-security security review or documented skip before PR handoff

Phase 5 objective:
Turn the private `/me dashboard` from an embed-only status page into a premium generated visual
dashboard card, and extend `/me preferences` into a first-pass private preferences hub only where
safe service-backed preference writes already exist.

Scope:
1. Start with audit/scope only unless I explicitly approve one-pass implementation.
2. Map current `/me dashboard` summary data, renderer options, views, fallback behavior, and quick
   launch controls.
3. Map current `/me preferences` status data and inventory visibility preference persistence.
4. Validate SQL contracts if Phase 5 depends on SQL-backed stats/export/preference data.
5. Keep `commands/me_cmds.py` thin.
6. Keep service and renderer logic Discord-type-free except view/adapter code.
7. Preserve `/me accounts`, `/me reminders`, `/me exports`, dashboard Quick Launch, and legacy
   commands.
8. Do not add preference writes unless an existing service-backed persistence path is reused.
9. Add safe embed fallback for any generated dashboard image path.
10. Capture out-of-scope visual polish, preference expansion, legacy redirect/removal, and process
    simplification structurally.

Likely files:
- commands/me_cmds.py
- player_self_service/service.py
- player_self_service/account_service.py
- player_self_service/reminder_service.py
- player_self_service/dashboard_card.py if a focused renderer is created
- player_self_service/preference_service.py if preference mutation needs a focused service
- ui/views/player_self_service_views.py
- ui/views/player_self_service_preference_views.py if needed
- commands/inventory_cmds.py
- inventory/
- tests/test_me_cmds.py
- tests/test_player_self_service_service.py
- tests/test_player_self_service_views.py
- tests/test_player_self_service_dashboard_card.py if a renderer is created
- tests/test_player_self_service_preference_service.py if a preference service is added
- docs/player_self_service_command_centre_briefing.md

Suggested validation:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_views.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py

Acceptance criteria:
- `/me dashboard` remains private.
- Dashboard output includes a generated visual card or an approved documented deferral.
- Dashboard card summarizes account, reminder, preference, and export/privacy status clearly.
- Dashboard has a safe embed fallback if image rendering fails.
- Existing dashboard Quick Launch behavior is preserved.
- `/me preferences` remains private.
- Any preference mutation is service-backed and uses existing persistence paths.
- Legacy self-service commands remain live.
- No persistence writes are added to commands or views.
- Focused tests and standard validators pass.
- Codex Security is run or explicitly justified.
```
