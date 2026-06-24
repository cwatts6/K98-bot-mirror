# Codex Task Pack - Player Self-Service Command Centre Phase 6 Guided Management Cards and Workflow Simplification

## 1. Task Header

- Task name: `Player Self-Service Command Centre Phase 6 Guided Management Cards and Workflow Simplification`
- Date: `2026-06-23`
- Owner/context: Player Self-Service Command Centre programme after Phase 5 dashboard card and preferences delivery
- Task type: `Discord command feature | visual card rendering | player workflow simplification`
- One-pass approved: `no`
- Status: `ready for next phase`

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
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 5 Visual Dashboard Card and Preferences Hub.md`
- `docs/task_packs/archive/Player Self-Service Command Centre - Phase 1 Audit and Design Report.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 2 Command Shell and Navigation Foundation.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 3 Modern Account Centre.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 4 Modern Reminder Centre.md`
- `docs/player_self_service_command_centre_briefing.md`

For account, reminder, preference, export, or stats data contracts, validate the live source
contracts before implementation. Use the SQL repo only when SQL-backed data is touched or depended
on.

## 3. Objective

Turn the Phase 5 dashboard into a coherent end-to-end self-service experience by converting the
remaining `/me` pages to generated visual cards and simplifying Accounts and Reminders around one
primary `Manage` journey each.

Phase 6 should make the UI feel intentional:

- dashboard card first
- card-based subpages with visuals similar in style to the `/kvk rankings` cards, using
  backgrounds from `assets/me/cards/`
- one obvious account management path
- one obvious reminder management path
- no stale visible card state after player mutations

## 4. Background

Phase 5 delivered a private generated `/me dashboard` card and a first-pass `/me preferences`
inventory report visibility write through an existing service-backed persistence path. Smoke
testing confirmed the dashboard works and renders reliably on desktop, mobile, and iPad.

Phase 5 smoke testing also exposed the next UX gap:

- `/me accounts` says the next action is `Manage`, but the page still presents separate `Find ID`,
  `Register`, `Replace`, and `Remove` controls.
- `/me reminders` has a primary `Manage` control plus a separate top-level `Unsubscribe` button.
- Subpages are still embed-only, so the user experience changes abruptly after the dashboard card.
- Reminder updates can leave an older dashboard card visible above the reminder page until the
  player returns to Dashboard.
- Discord bitmap regions are not interactive. Clickable card sections should be approximated with
  Discord-native buttons/selects whose labels and order match the visual card sections.

Important Phase 3 follow-up:

- The path from `Find ID` to `Register` is still too manual. Players can look up an ID by name or
  partial name, but then need another click and must remember or re-enter the 9-digit ID. Phase 6
  should carry selected lookup results into register/replace flows if the audit confirms a safe
  design.

Important Phase 4 reminder semantics to preserve:

- `Ruins` means non-fight ruins events.
- `Altars` means altar fights.
- `Major` means all major timeline events.
- `Fights` means altar fights plus major events whose title/description contains `FIGHT`.
- `fights + altars` saves as `fights`.
- `major + fights` keeps both.
- `ruins + major + fights` saves as `all`.
- `ruins + major + altars` saves as `all`.

## 5. Scope

### In Scope

- Audit current `/me accounts`, `/me reminders`, `/me preferences`, and `/me exports` page data,
  view behavior, fallback behavior, and button/select budget.
- Design generated visual cards for Accounts, Reminders, Preferences, and Exports pages.
- Add safe embed fallback for every new generated subpage card path.
- Keep `commands/me_cmds.py` thin.
- Keep service and renderer logic Discord-type-free except view/adapter code.
- Preserve the Phase 5 dashboard card, dashboard Quick Launch, and dashboard-only Quick Launch
  boundary.
- Replace account button sprawl with one primary Account `Manage` journey.
- Support account lookup-to-register/replace carry-forward where safe.
- Preserve duplicate ownership protection, stale confirmation protection, account slot limits, and
  removal confirmation.
- Replace reminder top-level manage/unsubscribe split with one primary Reminder `Manage` journey.
- Support reminder save/update and remove-all/unsubscribe inside the guided reminder journey.
- Preserve Phase 4 reminder semantics and best-effort confirmation DMs.
- Define and implement refresh behavior so visible dashboard/subpage cards do not show stale state
  after account, reminder, or preference mutations.
- Update focused tests for card rendering, fallback behavior, view navigation, guided flows, and
  service handoff.
- Update player/operator briefing and command docs.
- Capture any remaining visual polish, preference expansion, export redesign, or legacy cleanup as
  structured deferred optimisations.

### Out of Scope

- Removing, redirecting, or deprecating legacy commands.
- Adding new preference categories without an existing reliable persistence and service path.
- Rewriting export generation or file delivery.
- Full `/my_stats`, inventory report, or KVK output redesign.
- SQL schema changes unless separately approved after audit.
- Building a website or web dashboard.
- Literal clickable regions inside a generated Discord image.
- Shared renderer-helper consolidation across unrelated KVK/PreKvK/inventory renderers unless a
  tiny helper extraction is required for Phase 6 and approved.

## 6. Product Requirements

- `/me dashboard` remains the private home screen.
- Accounts, Reminders, Preferences, and Exports subpages should visually belong to the same command
  centre as the dashboard.
- Each subpage should have one obvious primary action.
- Account management should reduce memory steps and repeated typing.
- Reminder management should keep unsubscribe/remove-all inside the same guided journey as
  save/update.
- Fallback embeds must be complete enough to use if image rendering fails.
- No persistence writes may be added to commands or views.
- No setting should be shown as mutable unless the save path already exists and is service-backed.

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

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Phase 6 crosses views, services, renderers, persistence boundaries, and docs. |
| `k98-discord-command-feature` | use | `/me` page navigation and guided Manage journeys are Discord interaction flows. |
| `k98-sql-validation` | use if SQL-backed contracts are touched | Validate any SQL-backed account, stats, export, or preference data. |
| `k98-test-selection` | use | Select focused renderer/service/view tests plus standard validators. |
| `k98-deferred-optimisation-capture` | use | Capture out-of-scope preference/export/legacy/renderer work structurally. |
| `k98-pr-review` | use before handoff | Review architecture, command safety, tests, docs, and rollout boundaries. |
| `codex-security:security-diff-scan` | run or justify before PR handoff | Discord interactions, user input, image artifacts, and persistence-sensitive flows are touched. |

## 8. Mandatory Workflow

1. Start with audit/scope only unless the operator explicitly approves one-pass implementation.
2. Map current page data, render options, interaction flows, fallback behavior, and stale-card
   behavior.
3. Validate account/reminder/preference persistence contracts before designing mutations.
4. Present the implementation and test plan for approval.
5. Implement the approved Phase 6 slice.
6. Add or update focused tests.
7. Run selected validators and tests.
8. Run Codex Security or explicitly justify skipping.
9. Update mirror/production PR branches only after local validation if requested.

## 9. Likely Files

```text
commands/me_cmds.py
player_self_service/service.py
player_self_service/account_service.py
player_self_service/reminder_service.py
player_self_service/preference_service.py
player_self_service/dashboard_card.py
player_self_service/page_cards.py
ui/views/player_self_service_views.py
ui/views/player_self_service_account_views.py
ui/views/player_self_service_reminder_views.py
tests/test_me_cmds.py
tests/test_player_self_service_service.py
tests/test_player_self_service_views.py
tests/test_player_self_service_dashboard_card.py
tests/test_player_self_service_preference_service.py
docs/player_self_service_command_centre_briefing.md
docs/reference/deferred_optimisations.md
```

Create a focused renderer module only if it keeps the existing renderer clean and the tests
discoverable.

## 10. Suggested Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_views.py tests\test_player_self_service_dashboard_card.py tests\test_player_self_service_preference_service.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py
```

If reminder/account flows are materially changed, add the focused account/reminder tests selected
by `scripts/select_tests.py`. Use full pytest when flow changes are broad or tests touch shared
fixtures.

## 11. Manual Smoke Checklist

- `/me dashboard` remains private and still renders the Phase 5 card.
- Dashboard Quick Launch remains dashboard-only.
- `/me accounts` opens a private visual card or safe fallback embed.
- Account `Manage` supports lookup, register/replace carry-forward where implemented, and removal
  confirmation.
- `/me reminders` opens a private visual card or safe fallback embed.
- Reminder `Manage` supports save/update and remove-all/unsubscribe without a separate top-level
  unsubscribe button.
- Reminder category semantics still match Phase 4.
- `/me preferences` opens a private visual card or safe fallback embed.
- `/me exports` opens a private visual card or safe fallback embed and does not gain dashboard
  Quick Launch unless Phase 7 is explicitly pulled forward.
- After account/reminder/preference changes, visible card state refreshes or routes the player to a
  refreshed page so stale state is not misleading.
- Legacy account, reminder, inventory preference, and export commands remain live.

## 12. Acceptance Criteria

- [ ] `/me dashboard` remains private and keeps the delivered Phase 5 card behavior.
- [ ] `/me accounts`, `/me reminders`, `/me preferences`, and `/me exports` have generated visual
  cards or an approved documented deferral.
- [ ] Every new generated card has a safe embed fallback.
- [ ] Account page controls are simplified around one primary `Manage` journey.
- [ ] Account lookup-to-register/replace friction is removed or explicitly deferred with a precise
  blocker.
- [ ] Reminder page controls are simplified around one primary `Manage` journey.
- [ ] Reminder save/update and remove-all/unsubscribe preserve Phase 4 semantics.
- [ ] Visible card state does not remain misleadingly stale after successful mutations.
- [ ] Dashboard Quick Launch behavior is preserved.
- [ ] `/me exports` does not gain dashboard Quick Launch behavior unless separately approved.
- [ ] Legacy self-service commands remain live.
- [ ] No persistence writes are added to commands or views.
- [ ] No new preference writes are added without service-backed persistence.
- [ ] Focused tests and standard validators pass.
- [ ] Codex Security is run or explicitly justified.
- [ ] Deferred findings are captured structurally.

## 13. PR Summary Template

```md
## Summary

- Added Phase 6 visual cards for `/me` subpages with safe fallback.
- Simplified account/reminder management around guided `Manage` journeys.
- Preserved Phase 5 dashboard behavior, Quick Launch boundaries, and legacy commands.

## Changes

- <cards/renderers>
- <account manage flow>
- <reminder manage flow>
- <refresh behavior>
- <docs/tests>

## Tests

- <commands run>

## Manual Smoke

- <desktop/mobile smoke notes>

## AI Review Gates

- Codex Security: <run or skipped with reason>

## Risk / Rollback

- Roll back by reverting the guided subpage/card changes while keeping the Phase 5 dashboard and
  legacy commands live.
```
