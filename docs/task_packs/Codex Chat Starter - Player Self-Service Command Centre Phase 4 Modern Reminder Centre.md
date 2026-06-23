# Codex Chat Starter - Player Self-Service Command Centre Phase 4 Modern Reminder Centre

Status: active starter for the next Player Self-Service Command Centre phase.

Phase 1 audit/design is complete and archived.

Phase 2 `/me` Command Shell and Navigation Foundation is delivered in mirror PR #164 and
production PR #472, smoke tested successfully, and awaiting manual merge or promotion where still
needed by the operator.

Phase 3 Modern Account Centre is delivered in mirror PR #165 and smoke tested successfully by the
operator on 2026-06-22. The operator will manually merge and push the repo updates.

Delivered Phase 3 context:

- `/me accounts` remains private and opens the account centre.
- Players can review accounts, look up Governor IDs, register, replace, and remove accounts.
- Replacement and removal require confirmation.
- Account completion navigation returns to Account Centre or Dashboard.
- Legacy account commands remain live: `/register_governor`, `/modify_registration`,
  `/my_registrations`, and `/mygovernorid`.
- No direct SQL was added to commands or views.
- The final Phase 3 review feedback fixed interaction defer fallback, timeout message refs,
  26-slot selector coverage, and stale removal confirmation revalidation.

Process learning from Phase 3:

- The player path from `Find ID` to `Register` still has friction: lookup can find a Governor ID
  by name or partial name, but the player must then click again and manually remember/re-enter the
  9-digit ID to register the account.
- Later account-centre optimisation should carry selected lookup results into register/replace
  flows.
- Phase 4 must apply the same product principle to reminders: fewer buttons, fewer repeated
  inputs, fewer memory steps, and no legacy-command-shaped button pile.

Source documents:

- `docs/task_packs/Player Self-Service Command Centre - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 4 Modern Reminder Centre.md`
- `docs/task_packs/archive/Player Self-Service Command Centre - Phase 1 Audit and Design Report.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 2 Command Shell and Navigation Foundation.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 3 Modern Account Centre.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

## Copy/Paste Starter

```text
Codex, start Phase 4 of the Player Self-Service Command Centre: Modern Reminder Centre.

Phase 1 audit/design is complete and archived.

Phase 2 is delivered and smoke tested successfully in mirror PR #164 and production PR #472. The
delivered `/me` shell includes `/me dashboard`, `/me accounts`, `/me reminders`,
`/me preferences`, and `/me exports`. It is private. Dashboard Quick Launch works and shows
guidance. `/me exports` opens only the exports page and intentionally does not include the
dashboard Quick Launch menu. Existing legacy commands still work.

Phase 3 Modern Account Centre is delivered in mirror PR #165 and smoke tested successfully by the
operator on 2026-06-22. The operator will manually merge and push the repo updates. `/me accounts`
now supports private account review, Governor ID lookup, registration, replacement, removal with
confirmation, and return navigation. Legacy account commands remain live.

Important process-learning from Phase 3:
The path from `Find ID` to `Register` is still too manual. Players can look up an ID by name or
partial name, but then need another click and must remember/re-enter the 9-digit ID to register the
account. Capture or preserve the later account-centre optimisation to carry lookup selections into
register/replace flows. For Phase 4 reminders, actively look for process optimisation,
simplification, and fewer steps at every point. Less buttons and less repeated input is the goal.

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
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 4 Modern Reminder Centre.md
- docs/task_packs/archive/Player Self-Service Command Centre - Phase 1 Audit and Design Report.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 2 Command Shell and Navigation Foundation.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 3 Modern Account Centre.md
- docs/player_self_service_command_centre_briefing.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation if SQL-backed contracts are touched
- k98-test-selection
- k98-deferred-optimisation-capture for process simplification or out-of-scope debt
- k98-pr-review before handoff
- codex-security security review or documented skip before PR handoff

Phase 4 objective:
Turn the delivered read-only `/me reminders` page into a modern private reminder centre for
reviewing, subscribing, modifying, and unsubscribing from KVK reminders.

Scope:
1. Start with audit/scope only unless I explicitly approve one-pass implementation.
2. Map existing reminder commands, services, views, persistence, scheduler, and restart behavior.
3. Reuse existing reminder/subscription persistence paths; do not invent new storage or write
   persistence logic in commands/views.
4. Keep `commands/me_cmds.py` thin.
5. Keep service logic Discord-type-free.
6. Extend `ui/views/player_self_service_views.py` or create a focused reminder-centre view module
   only if the existing view becomes too broad.
7. Use buttons only for clear actions, selects for event/timing choices, and confirmations for
   unsubscribe or destructive reset.
8. Preserve duplicate subscription, DM delivery, restart, and scheduler behavior.
9. Keep `/subscribe`, `/modify_subscription`, and `/unsubscribe` registered and usable. Do not
   redirect or remove them in Phase 4.
10. Capture out-of-scope cleanup and process simplification structurally.

Likely files:
- commands/me_cmds.py
- commands/subscriptions_cmds.py
- player_self_service/service.py
- player_self_service/reminder_service.py if needed
- ui/views/player_self_service_views.py
- ui/views/player_self_service_reminder_views.py if needed
- ui/views/subscription_views.py
- subscription_tracker.py
- event_scheduler.py
- reminder_task_registry.py
- dm_tracker_utils.py
- tests/test_me_cmds.py
- tests/test_player_self_service_service.py
- tests/test_player_self_service_views.py
- tests/test_player_self_service_reminder_service.py if a dedicated service is added
- tests/test_subscription_views.py
- docs/player_self_service_command_centre_briefing.md

Suggested validation:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_views.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_subscription_views.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py

Acceptance criteria:
- `/me reminders` remains private and opens the modern reminder centre.
- Players can review current reminder setup.
- Players can subscribe through a service-backed flow.
- Players can modify reminder event types and timings through a service-backed flow.
- Players can unsubscribe only after confirmation.
- Reminder flows reduce memory/re-entry steps where practical.
- Legacy reminder commands remain live.
- No persistence writes are added to commands or views.
- Focused tests and standard validators pass.
- Persistence/restart contract validation is documented.
- Codex Security is run or explicitly justified.
```
