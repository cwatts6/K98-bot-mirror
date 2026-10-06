# Codex Chat Starter - Player Self-Service Command Centre Phase 6 Guided Management Cards and Workflow Simplification

Status: historical starter. Phase 6 is delivered and smoke tested. Phase 7 is also delivered and
archived. Use
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
testing confirmed `/me reminders` supports private review, subscribe/update through event/time
selectors, unsubscribe with confirmation, and best-effort confirmation DMs. Legacy reminder
commands remain live.

Phase 5 Visual Dashboard Card and Preferences Hub is delivered in production PR #475 and smoke
tested successfully on desktop, mobile, and iPad. `/me dashboard` now has a generated private card
with safe embed fallback. `/me preferences` can update inventory report visibility through the
existing service-backed persistence path. Dashboard Quick Launch remains dashboard-only.

Important Phase 3 follow-up to preserve:

The path from `Find ID` to `Register` is still too manual. Players can look up an ID by name or
partial name, but then need another click and must remember/re-enter the 9-digit ID to register
the account. Phase 6 should carry selected lookup results into register/replace flows if the audit
confirms a safe design.

Important Phase 4 reminder semantics to preserve:

- `Ruins` means non-fight ruins events.
- `Altars` means altar fights.
- `Major` means all major timeline events.
- `Fights` means altar fights plus major events whose title/description contains `FIGHT`.
- `fights + altars` saves as `fights`.
- `major + fights` keeps both.
- `ruins + major + fights` saves as `all`.
- `ruins + major + altars` saves as `all`.

Important Phase 5 smoke learnings to preserve:

- The dashboard card works and should remain the private `/me dashboard` home.
- The card should stay as one primary visual summary, not duplicate an embed with the same content.
- Accounts, Reminders, and Preferences open private pages as expected.
- `/me exports` opens the exports page and intentionally does not include dashboard Quick Launch.
- Account and reminder pages still feel too button-heavy for the intended `Manage` journey.
- Subpages are still embed-only, so the shift from dashboard card to subpage embed feels mixed.
- Reminder changes can leave an older dashboard card visible above the refreshed reminder page
  until the player returns to Dashboard.
- Discord image regions are not clickable; use native buttons/selects aligned to the card sections
  instead.

Source documents:

- `docs/task_packs/Player Self-Service Command Centre - Programme Pack.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 6 Guided Management Cards and Workflow Simplification.md`
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
Codex, start Phase 6 of the Player Self-Service Command Centre: Guided Management Cards and
Workflow Simplification.

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
account. Phase 6 should carry selected lookup results into register/replace flows if the audit
confirms a safe design.

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

Phase 5 Visual Dashboard Card and Preferences Hub is delivered in production PR #475 and smoke
tested successfully on desktop, mobile, and iPad. `/me dashboard` now has a generated private
dashboard card with safe embed fallback. `/me preferences` can update inventory report visibility
through the existing service-backed persistence path. Dashboard Quick Launch remains
dashboard-only, and `/me exports` intentionally does not include it.

Important Phase 5 follow-ups to address in Phase 6:
- `/me accounts` says the next action is Manage, but the page still exposes separate Find ID,
  Register, Replace, and Remove controls.
- `/me reminders` has Manage plus a separate Unsubscribe button; this should become one guided
  Manage journey with save/update and remove-all/unsubscribe actions.
- Accounts, Reminders, Preferences, and Exports should move from embed-only subpages to generated
  cards with safe embed fallback.
- Reminder changes can leave an older dashboard card visible above the reminder page until the
  player returns to Dashboard; define and implement non-misleading refresh behavior.
- Discord image regions cannot be clicked directly, so use native buttons/selects aligned with the
  card sections rather than trying to make the bitmap itself interactive.

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
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 6 Guided Management Cards and Workflow Simplification.md
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
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- codex-security security review or documented skip before PR handoff

Phase 6 objective:
Convert the remaining `/me` pages to generated visual cards and simplify Accounts and Reminders
around one primary `Manage` journey each, while preserving the delivered Phase 5 dashboard,
dashboard Quick Launch, legacy commands, account safety checks, and reminder semantics.

Scope:
1. Start with audit/scope only unless I explicitly approve one-pass implementation.
2. Map current `/me accounts`, `/me reminders`, `/me preferences`, and `/me exports` page data,
   views, fallback behavior, and button/select budget.
3. Design generated subpage cards with safe embed fallback. The target is visuals similar in style
   to the `/kvk rankings` cards, using backgrounds from `assets/me/cards/`.
4. Replace account button sprawl with one guided `Manage` flow where safe.
5. Replace reminder Manage/Unsubscribe split with one guided `Manage` flow where safe.
6. Define refresh behavior so visible dashboard/subpage cards do not show stale state after
   successful mutations.
7. Keep `commands/me_cmds.py` thin.
8. Keep service and renderer logic Discord-type-free except view/adapter code.
9. Preserve `/me dashboard`, `/me exports`, dashboard Quick Launch, all legacy commands, and
   existing service-backed persistence boundaries.
10. Do not add preference writes unless an existing service-backed persistence path is reused.
11. Capture out-of-scope export redesign, preference expansion, legacy redirect/removal, and
   renderer-helper consolidation structurally.

Account flow:
There are three main scenarios to incorporate:

1. A user wants to register or add a new account.
   - If they do not know the Governor ID but know all or part of the account name, they should be
     able to search with Find ID, select the governor result, and continue into registration.
   - If they know the Governor ID, they should be guided through registration with only available
     slots displayed.
2. A user wants to replace a registered account, for example when moving accounts around or
   promoting a farm account to an alt. They should be guided through selecting the account to
   replace, adding the new account by Governor ID, and confirming the replacement.
3. A user wants to remove a registered account, for example after the account migrated or was sold.
   They should be guided through selecting the account to remove and confirming the removal.

Throughout all flows, validate that a Governor ID can only be registered once. Preserve duplicate
ownership checks and any other account safety checks identified during audit.

Likely files:
- commands/me_cmds.py
- player_self_service/service.py
- player_self_service/account_service.py
- player_self_service/reminder_service.py
- player_self_service/preference_service.py
- player_self_service/dashboard_card.py
- player_self_service/page_cards.py if a focused subpage renderer is created
- ui/views/player_self_service_views.py
- ui/views/player_self_service_account_views.py
- ui/views/player_self_service_reminder_views.py
- tests/test_me_cmds.py
- tests/test_player_self_service_service.py
- tests/test_player_self_service_views.py
- tests/test_player_self_service_dashboard_card.py
- tests/test_player_self_service_preference_service.py
- docs/player_self_service_command_centre_briefing.md
- docs/reference/deferred_optimisations.md

Suggested validation:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_views.py tests\test_player_self_service_dashboard_card.py tests\test_player_self_service_preference_service.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py

Acceptance criteria:
- `/me dashboard` remains private and keeps the delivered Phase 5 card behavior.
- `/me accounts`, `/me reminders`, `/me preferences`, and `/me exports` have generated visual
  cards or an approved documented deferral.
- Every new generated card has a safe embed fallback.
- Account page controls are simplified around one primary Manage journey.
- Account lookup-to-register/replace friction is removed or explicitly deferred with a precise
  blocker.
- Reminder page controls are simplified around one primary Manage journey.
- Reminder save/update and remove-all/unsubscribe preserve Phase 4 semantics.
- Visible card state does not remain misleadingly stale after successful mutations.
- Dashboard Quick Launch behavior is preserved.
- `/me exports` does not gain dashboard Quick Launch behavior unless separately approved.
- Legacy self-service commands remain live.
- No persistence writes are added to commands or views.
- No new preference writes are added without service-backed persistence.
- Focused tests and standard validators pass.
- Codex Security is run or explicitly justified.
```
