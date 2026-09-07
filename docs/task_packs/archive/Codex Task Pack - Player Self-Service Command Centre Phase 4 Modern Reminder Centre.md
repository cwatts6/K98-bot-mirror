# Codex Task Pack - Player Self-Service Command Centre Phase 4 Modern Reminder Centre

## 1. Task Header

- Task name: `Player Self-Service Command Centre Phase 4 Modern Reminder Centre`
- Date: `2026-06-22`
- Owner/context: Player Self-Service Command Centre programme after Phase 3 Modern Account Centre delivery and smoke test
- Task type: `Discord command feature | player UX consolidation | reminder workflow service extraction`
- One-pass approved: `no`
- Status: `complete - delivered in mirror PR #166 and production PR #474, smoke tested successfully`

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
- `docs/task_packs/archive/Player Self-Service Command Centre - Phase 1 Audit and Design Report.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 2 Command Shell and Navigation Foundation.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 3 Modern Account Centre.md`
- `docs/player_self_service_command_centre_briefing.md`

For reminder persistence or SQL-facing work, validate source contracts before implementation. If
the reminder flow remains JSON/service backed, document the persistence source and restart-safety
contract explicitly rather than assuming it.

## 3. Objective

Turn the delivered read-only `/me reminders` page into a modern private reminder centre for
reviewing, subscribing, modifying, and unsubscribing from KVK reminders.

The target experience is a guided reminder workflow that replaces the habit of remembering:

```text
/subscribe
/modify_subscription
/unsubscribe
```

Legacy commands must remain registered and usable during Phase 4.

## 4. Background

Phase 1 audit/design is complete and archived.

Phase 2 delivered the private `/me` command shell:

- `/me dashboard`
- `/me accounts`
- `/me reminders`
- `/me preferences`
- `/me exports`

Phase 3 delivered the modern `/me accounts` account centre in mirror PR #165. Operator smoke
testing completed successfully on 2026-06-22. The Phase 3 smoke path covered private account-centre
access, Governor ID lookup, registration, replacement, removal with confirmation, return
navigation, and legacy account command preservation.

One Phase 3 process-learning item must inform Phase 4 and later phases: the account-centre path
from `Find ID` to `Register` still asks the player to remember or manually re-enter the 9-digit
Governor ID after lookup. That is captured as deferred account-centre UX optimisation, and Phase 4
must actively avoid introducing the same pattern in reminder flows. Fewer buttons, fewer repeated
inputs, and fewer memory steps are part of the product requirement.

## 5. Scope

### In Scope

- Add or extend reminder-centre service logic under `player_self_service/` or a focused reminder
  service module if the existing service becomes too broad.
- Extend `/me reminders` with private reminder actions through buttons, selects, confirmations,
  and modals only where they reduce complexity.
- Provide private flows for:
  - reviewing current reminder subscription status
  - subscribing to supported reminder events
  - changing event types
  - changing reminder timings
  - unsubscribing with confirmation
  - returning to dashboard and reminder centre after completion
- Reuse existing reminder/subscription service and persistence paths.
- Preserve existing duplicate subscription, DM delivery, restart, and scheduler behavior.
- Keep `commands/me_cmds.py` thin.
- Keep service logic Discord-type-free.
- Update player/operator briefing and command documentation where user-facing behavior changes.
- Capture process simplification opportunities structurally when they are outside the approved
  Phase 4 slice.

### Out of Scope

- Removing, redirecting, or deprecating `/subscribe`, `/modify_subscription`, or `/unsubscribe`.
- Changing account-centre flows beyond documentation or explicitly approved low-risk fixes.
- Reworking event calendar publishing, Ark/MGE reminders, or admin reminder tooling.
- SQL schema changes unless a reviewed persistence contract requires a separately approved SQL
  task.
- Generated PNG `/me dashboard` card work.
- Preference, export, inventory, KVK, stats, calendar, Ark, MGE, or admin workflow redesign.
- Adding a public reminder-management output.

## 6. Process Optimisation Requirement

At every step, review whether the flow can be simpler:

- Avoid lookup results that force the user to remember or manually copy a value into the next step.
- Prefer carrying selected values forward through service-backed confirmation models.
- Prefer one clear selector over multiple buttons when it reduces steps.
- Prefer direct `Subscribe`, `Update`, and `Unsubscribe` paths only when the current state makes
  the action obvious.
- Do not add "coming soon" controls.
- Do not turn `/me reminders` into a button copy of legacy commands.

If a simplification is valuable but too large for Phase 4, capture it in
`docs/reference/deferred_optimisations.md` using the required structured format.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Reminder centre crosses commands, services, views, persistence, restart behavior, and tests. |
| `k98-discord-command-feature` | use | `/me reminders` buttons/selects/modals, response visibility, and interaction safety change. |
| `k98-sql-validation` | use if SQL-backed contracts are touched | Validate before implementation if Phase 4 depends on SQL tables/procedures/views. |
| `k98-test-selection` | use | Select command/view/service/reminder tests plus standard validators. |
| `k98-deferred-optimisation-capture` | use | Capture out-of-scope simplification, legacy cleanup, or persistence work structurally. |
| `k98-pr-review` | use before handoff | Review command safety, persistence, tests, deferred items, and rollout boundaries. |
| `k98-promotion-check` | use only before production promotion | Not needed for initial mirror PR unless promotion is requested. |
| `codex-security:security-scan` | consider before PR handoff | Phase 4 touches Discord interactions, DM/reminder preferences, user-controlled selections, and restart-sensitive reminder state. |

## 8. Mandatory Workflow

1. Start with audit/scope only unless the operator explicitly approves one-pass implementation.
2. Map existing subscription/reminder commands, services, views, persistence, scheduler, and
   restart behavior.
3. Validate persistence contracts before implementation. Use SQL repo validation if SQL-backed
   objects are involved.
4. Identify existing service/write paths to reuse before adding reminder-centre helpers.
5. Present implementation and test plan for approval.
6. Implement the approved Phase 4 slice.
7. Add or update focused tests.
8. Run selected validators and tests.
9. Run or explicitly justify Codex Security review.
10. Open or update the PR only after local validation.

## 9. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | Keep `commands/me_cmds.py` thin; no reminder business logic. |
| Reminder journey service | `player_self_service/` service layer or focused reminder service. |
| Existing legacy commands | Preserve `/subscribe`, `/modify_subscription`, and `/unsubscribe`. |
| Persistence | Existing subscription/reminder persistence path; no ad hoc writes from views. |
| Scheduler/restart | Preserve current reminder scheduling and restart behavior. |
| Views/modals | `ui/views/player_self_service_views.py` or focused reminder-centre view module if complexity justifies it. |
| Tests | Focused command, service, view, subscription/reminder, restart/persistence, and command registration tests. |

Commands and views must not own persistence or domain business rules. Services must not import
Discord types.

## 10. Likely Files

### Review

- `commands/me_cmds.py`
- `commands/subscriptions_cmds.py`
- `player_self_service/service.py`
- `ui/views/player_self_service_views.py`
- `ui/views/subscription_views.py`
- `subscription_tracker.py`
- `event_scheduler.py`
- `reminder_task_registry.py`
- `dm_tracker_utils.py`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- `docs/player_self_service_command_centre_briefing.md`

### Likely Modify

- `player_self_service/service.py`
- `ui/views/player_self_service_views.py`
- `tests/test_player_self_service_service.py`
- `tests/test_player_self_service_views.py`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`

### Likely Create

- `player_self_service/reminder_service.py` if reminder mutation makes `service.py` too broad.
- `ui/views/player_self_service_reminder_views.py` if reminder components make the existing view
  module too broad.
- `tests/test_player_self_service_reminder_service.py` if a dedicated service is added.

## 11. Reminder UX Requirements

`/me reminders` should remain private.

The reminder centre should support these player paths:

- Review current reminder state.
- Subscribe when no subscription exists.
- Modify event types and reminder timings.
- Unsubscribe only after explicit confirmation.
- Show DM/troubleshooting guidance where safe and accurate.
- Return to `/me dashboard` after completion.

Interaction requirements:

- Use buttons for clear commands only.
- Use selects for event-type and timing choices.
- Use confirmations for unsubscribe and any destructive reset.
- Carry selected values forward; avoid asking the player to re-enter values already chosen.
- Avoid showing every legacy command name as the primary UX.
- Make unknown or failed reminder source states explicit.
- Keep all reminder mutation responses ephemeral/private.

## 12. Refactor Triggers To Check

Classify findings as fix now, defer, or not applicable:

| Trigger | Phase 4 decision guidance |
|---|---|
| Direct persistence writes in views | Do not add; route through service/persistence owners. |
| Business logic in views | Move new reminder decisions into service-owned models. |
| Duplicate subscribe/modify helpers | Reuse existing helper/service paths where safe; defer larger consolidation if risky. |
| Dead legacy flow | Do not remove legacy commands in Phase 4; capture cleanup for later redirect/removal phase. |
| Restart/persistence fragility | Review reminder tracker and scheduler restart behavior before adding mutations. |
| Weak logging | Add useful actor/reminder outcome logs in service-owned mutation paths. |
| Process friction | Fix low-risk friction in scope; capture larger simplification work structurally. |

## 13. Testing Requirements

Run or justify skipping:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
```

Focused tests should cover:

- reminder centre summary with no subscription, active subscription, modified subscription, and
  source failure
- subscribe flow service decisions and persistence handoff
- modify flow event/timing selection and persistence handoff
- unsubscribe confirmation and handoff
- duplicate subscription protection
- view ownership rejection
- stale/timeout handling
- dashboard/reminder return after successful action
- legacy `/subscribe`, `/modify_subscription`, and `/unsubscribe` remaining registered and usable
- restart/persistence behavior where reminder state is changed

Likely pytest commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_subscription_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py
```

Broaden to the full suite before production promotion when practical because reminder flows touch
restart-sensitive scheduled behavior.

## 14. AI Review Gate

Codex Security should be run before PR handoff or explicitly justified because Phase 4 may touch:

- Discord interactions
- user-controlled reminder selections
- DM delivery preference behavior
- restart-sensitive reminder persistence
- duplicate-action and unsubscribe confirmation boundaries

Fix validated issues within the approved Phase 4 scope. Capture larger hardening work as deferred
optimisations.

## 15. Acceptance Criteria

- [ ] `/me reminders` remains private and opens the modern reminder centre.
- [ ] Players can review current reminder setup.
- [ ] Players can subscribe through a service-backed flow.
- [ ] Players can modify reminder event types and timings through a service-backed flow.
- [ ] Players can unsubscribe only after confirmation.
- [ ] Reminder flows reduce memory/re-entry steps where practical.
- [ ] Legacy reminder commands remain registered and usable.
- [ ] No persistence writes are added to commands or views.
- [ ] Reminder journey logic lives in service-layer code, not command/view callbacks.
- [ ] Views own interaction routing, ownership checks, and response sequencing only.
- [ ] Restart-sensitive reminder behavior is preserved and tested or explicitly documented.
- [ ] Focused tests and standard validators pass.
- [ ] Persistence contract validation is documented.
- [ ] Codex Security is run or explicitly justified.
- [ ] Deferred findings are captured structurally.

## 16. PR Summary Template

```md
## Summary

- Added the modern `/me reminders` reminder centre flows.
- Reused existing reminder/subscription persistence paths.
- Preserved legacy reminder commands during rollout.

## Changes

- Added service-owned reminder journey decisions and confirmation models.
- Extended player self-service views with reminder actions, selections, and confirmations.
- Updated briefing/docs for Phase 4 reminder-centre behavior.

## Tests

- <commands run>

## Persistence / Restart

- <persistence source and restart-safety notes>

## AI Review Gates

- Codex Security: <run or skipped with reason>

## Risk / Rollback

- Reminder mutation risk is contained by reusing existing service/persistence paths and keeping
  legacy commands live.
- Rollback by disabling the new `/me reminders` mutation controls while preserving the Phase 2
  read-only `/me` shell and legacy commands.
```
