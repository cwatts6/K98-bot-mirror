# Codex Task Pack - Player Self-Service Command Centre Phase 7 Unified Reminder Centre and Dashboard Card Alignment

## 1. Task Header

- Task name: `Player Self-Service Command Centre Phase 7 Unified Reminder Centre and Dashboard Card Alignment`
- Date: `2026-06-24`
- Owner/context: Player Self-Service Command Centre programme after Phase 6 guided management cards were smoke tested successfully
- Task type: `Discord command feature | reminder workflow design | visual card rendering | product consistency`
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
- `docs/reference/events_and_dm_reminders.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/Player Self-Service Command Centre - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 6 Guided Management Cards and Workflow Simplification.md`
- `docs/player_self_service_command_centre_briefing.md`

For calendar reminder persistence, scheduled work, or SQL-backed data dependencies, validate the
live source contracts before implementation. Use the SQL repo only when SQL-backed contracts are
touched or depended on.

## 3. Objective

Make `/me reminders` match how players think about reminders by accounting for both KVK event
reminders and calendar reminders, while refreshing `/me dashboard` so the command-centre home
matches the Phase 6 card style.

The most effective next delivery is to combine a careful reminder audit with a low-risk dashboard
visual alignment pass. If calendar reminder writes prove too risky for one PR, deliver dashboard
alignment plus read-only calendar reminder status first and capture the mutation controls with a
precise blocker.

## 4. Background

Phase 6 delivered the guided management card model:

- Accounts, Reminders, Preferences, and Exports now render generated visual cards with safe embed
  fallback.
- Account management is guided through one `Manage` journey with lookup-to-register/replace
  carry-forward.
- KVK event reminder management is guided through one `Manage` journey with autosave and
  remove-all/unsubscribe confirmation.
- Preferences include inventory visibility toggle, Governor VIP update access, and VIP-level
  display.
- Exports remain private guidance without dashboard Quick Launch.
- Main cards and reminder child selector windows timeout gracefully.

Smoke testing confirmed Phase 6 is complete and visually strong. It also exposed two follow-ups:

- Calendar reminders are still managed separately through `/calendar_reminder_config`, even though
  players experience KVK event reminders and calendar reminders as one reminder domain.
- The older Phase 5 dashboard card now looks visually out of step with the Phase 6 full-bleed
  subpage cards.

## 5. Scope

### In Scope

- Audit KVK event reminder state, calendar reminder preference/state code, scheduler behavior,
  persistence, restart safety, and legacy command compatibility.
- Design one `/me reminders` status model that can represent users with KVK-only reminders,
  calendar-only reminders, both, or neither.
- Add calendar reminder status to the `/me reminders` card if the audit confirms a safe read path.
- Add calendar reminder management through `/me reminders` only where service-backed persistence,
  restart safety, timezone/lead-time semantics, and legacy compatibility are validated.
- Preserve Phase 4/6 KVK reminder semantics and autosave behavior.
- Preserve calendar reminder timezone, lead-time, enable/disable, scheduler, and restart-sensitive
  behavior.
- Preserve `/calendar_reminder_config` until redirect/removal is separately approved.
- Refresh `/me dashboard` to match the visual language of the Phase 6 subpage cards.
- Preserve dashboard-only Quick Launch and `/me exports` no-Quick-Launch behavior.
- Keep `commands/me_cmds.py` thin.
- Keep service and renderer logic Discord-type-free except view/adapter code.
- Update focused service, renderer, view, command-registration, and docs tests.
- Capture out-of-scope export launchpad, preference expansion, legacy redirect/removal, and shared
  renderer-helper consolidation structurally.

### Out of Scope

- Removing, redirecting, or deprecating `/calendar_reminder_config` or legacy KVK reminder commands.
- Rewriting the calendar scheduler or public calendar/KVK calendar commands.
- Merging KVK reminder and calendar reminder storage models without a validated design.
- Adding new reminder categories beyond existing KVK event reminders and existing calendar
  reminder preferences.
- Changing dashboard Quick Launch destinations or making Quick Launch available on `/me exports`.
- Export launchpad redesign.
- Preference hub expansion beyond any reminder-facing state explicitly approved for Phase 7.
- SQL schema changes unless separately approved after audit.

## 6. Source Deferred Items

### Deferred Optimisation
- Area: `/me reminders`, `commands/calendar_cmds.py`, `event_calendar/reminder_prefs.py`, `event_calendar/reminder_prefs_store.py`, `ui/views/reminder_config.py`, calendar reminder state files
- Type: architecture
- Description: Phase 6 simplifies `/me reminders` for KVK event reminder subscriptions only. Calendar reminders remain managed through `/calendar_reminder_config` and use distinct event-calendar preference/state code, but from a player perspective KVK event reminders and calendar reminders are two sides of the same reminder experience. Players can reasonably have KVK reminders, calendar reminders, or both, so the reminder centre will still feel incomplete after the KVK subscription flow is modernised.
- Suggested Fix: Audit KVK subscription reminders and calendar reminders together, map both persistence models, and design one `/me reminders` surface that can review and manage both without merging their storage unsafely. Preserve KVK reminder semantics, calendar reminder timezone/lead-time semantics, restart-sensitive scheduled work, and legacy command compatibility. Add focused tests for mixed reminder states and manual smoke covering users with KVK-only, calendar-only, both, and neither.
- Impact: high
- Risk: medium
- Dependencies: Phase 6 KVK reminder manage flow smoke tested; calendar reminder service/state contracts validated before implementation.

### Deferred Optimisation
- Area: `/me dashboard`, `player_self_service/dashboard_card.py`, `player_self_service/page_cards.py`, `assets/me/cards/`
- Type: consistency
- Description: Phase 6 subpage cards for Accounts, Reminders, Preferences, and Exports now use a full-bleed generated visual style with large readable text and native controls aligned to the card sections. Smoke testing confirmed the cards look strong, but it also made the older Phase 5 `/me dashboard` card feel visually out of step with the rest of the command centre.
- Suggested Fix: Refresh `/me dashboard` to match the Phase 6 card style while preserving dashboard summary data, private response behavior, safe embed fallback, dashboard-only Quick Launch, and existing navigation controls. Add renderer tests and manual smoke on desktop/mobile to confirm readability and no Quick Launch regression.
- Impact: medium
- Risk: low
- Dependencies: Phase 6 generated subpage cards smoke tested; dashboard Quick Launch behavior preserved.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Phase 7 crosses reminder services, calendar reminder persistence, views, renderers, docs, and restart safety. |
| `k98-discord-command-feature` | use | `/me reminders`, `/me dashboard`, buttons/selects, timeouts, and legacy command compatibility are Discord interaction flows. |
| `k98-sql-validation` | use if SQL-backed contracts are touched | Validate any SQL-backed calendar, stats, account, or preference data before relying on it. |
| `k98-test-selection` | use | Select focused reminder/calendar/renderer/view tests plus standard validators. |
| `k98-deferred-optimisation-capture` | use | Capture export, preference, legacy redirect, renderer consolidation, or calendar redesign items that remain out of scope. |
| `k98-pr-review` | use before handoff | Review architecture, restart safety, command compatibility, tests, and docs. |
| `k98-promotion-check` | not applicable unless production promotion is requested | Mirror PR work only by default. |
| `codex-security:security-scan` | run or justify before PR handoff | Discord interactions, user input, reminders, and restart-sensitive state are touched. |

## 8. Mandatory Workflow

1. Start with audit/scope only unless the operator explicitly approves one-pass implementation.
2. Map KVK reminder and calendar reminder data, persistence, scheduler, restart, and view flows.
3. Decide whether Phase 7 can safely include calendar reminder mutation controls or should ship
   read-only calendar reminder status first.
4. Design the dashboard visual refresh and reminder card copy before implementation.
5. Implement the approved Phase 7 slice.
6. Add or update focused tests.
7. Run selected validators and tests.
8. Run Codex Security or explicitly justify skipping.
9. Update mirror PR branches only after local validation if requested.

## 9. Likely Files

```text
commands/me_cmds.py
commands/calendar_cmds.py
player_self_service/service.py
player_self_service/reminder_service.py
player_self_service/dashboard_card.py
player_self_service/page_cards.py
event_calendar/reminder_prefs.py
event_calendar/reminder_prefs_store.py
event_calendar/reminders.py
ui/views/player_self_service_views.py
ui/views/player_self_service_reminder_views.py
ui/views/reminder_config.py
tests/test_me_cmds.py
tests/test_player_self_service_service.py
tests/test_player_self_service_reminder_service.py
tests/test_player_self_service_views.py
tests/test_player_self_service_dashboard_card.py
tests/test_player_self_service_page_cards.py
tests/test_calendar_reminder_prefs.py
tests/test_calendar_reminders.py
tests/test_calendar_reminders_dispatch.py
tests/test_calendar_views.py
docs/player_self_service_command_centre_briefing.md
docs/reference/canonical_command_reference.md
docs/reference/deferred_optimisations.md
```

## 10. Suggested Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_reminder_service.py tests\test_player_self_service_views.py tests\test_player_self_service_dashboard_card.py tests\test_player_self_service_page_cards.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_calendar_reminder_prefs.py tests\test_calendar_reminders.py tests\test_calendar_reminders_dispatch.py tests\test_calendar_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py
```

Run full pytest and `scripts/analyse_pytest_log_noise.py` if calendar scheduler, persistence, or
restart-sensitive reminder behavior changes.

## 11. Manual Smoke Checklist

- `/me dashboard` remains private.
- Dashboard renders the refreshed card or safe fallback embed.
- Dashboard Quick Launch remains dashboard-only.
- `/me accounts`, `/me preferences`, and `/me exports` still render their Phase 6 cards.
- `/me exports` does not gain dashboard Quick Launch behavior.
- `/me reminders` shows clear status for KVK reminders, calendar reminders, both, or neither.
- KVK reminder event/time autosave still works and preserves Phase 4 semantics.
- Calendar reminder status and any approved calendar reminder controls preserve existing calendar
  reminder semantics.
- Users with KVK-only reminders, calendar-only reminders, both, and neither get non-misleading
  card copy.
- `/calendar_reminder_config`, `/subscribe`, `/modify_subscription`, and `/unsubscribe` remain
  registered and usable.
- Main and child interaction views timeout gracefully with disabled controls.

## 12. Acceptance Criteria

- [ ] Phase 7 begins with audit/scope unless one-pass implementation is explicitly approved.
- [ ] KVK reminder and calendar reminder persistence/state contracts are mapped before mutation
  controls are designed.
- [ ] `/me reminders` can represent KVK-only, calendar-only, both, and neither states.
- [ ] Calendar reminder management is implemented only if service-backed persistence and restart
  safety are validated; otherwise it is explicitly deferred with a precise blocker.
- [ ] KVK reminder semantics and autosave behavior remain intact.
- [ ] Calendar reminder timezone/lead-time/scheduler semantics remain intact.
- [ ] `/me dashboard` is visually aligned with Phase 6 subpage cards.
- [ ] Dashboard Quick Launch remains dashboard-only.
- [ ] Legacy self-service and calendar reminder commands remain live.
- [ ] No persistence writes are added to commands or views.
- [ ] Focused tests and standard validators pass.
- [ ] Codex Security is run or explicitly justified.
- [ ] Deferred findings are captured structurally.

## 13. PR Summary Template

```md
## Summary

- Aligned `/me dashboard` with the Phase 6 card visual language.
- Extended `/me reminders` toward a unified reminder centre for KVK and calendar reminder state.
- Preserved dashboard Quick Launch boundaries and legacy command compatibility.

## Changes

- <dashboard card alignment>
- <reminder/calendar audit and implementation>
- <views/timeouts/fallbacks>
- <docs/tests>

## Tests

- <commands run>

## Manual Smoke

- <desktop/mobile and mixed reminder-state notes>

## AI Review Gates

- Codex Security: <run or skipped with reason>

## Risk / Rollback

- Roll back by reverting the Phase 7 dashboard/reminder changes while keeping Phase 6 cards and
  all legacy reminder commands live.
```
