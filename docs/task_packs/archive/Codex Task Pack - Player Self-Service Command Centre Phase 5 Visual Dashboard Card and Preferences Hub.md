# Codex Task Pack - Player Self-Service Command Centre Phase 5 Visual Dashboard Card and Preferences Hub

## 1. Task Header

- Task name: `Player Self-Service Command Centre Phase 5 Visual Dashboard Card and Preferences Hub`
- Date: `2026-06-23`
- Owner/context: Player Self-Service Command Centre programme after Phase 4 Modern Reminder Centre delivery and smoke test
- Task type: `Discord command feature | visual card rendering | player preference workflow`
- One-pass approved: `no`
- Status: `complete; delivered in production PR #475 and smoke tested successfully on desktop, mobile, and iPad`

## Completion Note

Phase 5 is complete.

Delivered scope:

- `/me dashboard` remains private and now sends a generated visual dashboard card.
- The dashboard card summarizes account, reminder, preference, and export/privacy status.
- The card has a safe embed fallback if image rendering or image delivery fails.
- The final layout renders reliably on desktop, mobile, and iPad.
- Card copy was simplified after smoke feedback:
  - timestamp-only header metadata
  - `Linked: multiple`
  - no system-only `DMs: best effort` row
  - `Exports: private`
- Duplicate dashboard embed/card content was removed so the card is the primary dashboard summary.
- Dashboard Quick Launch remains dashboard-only.
- `/me exports` remains a separate private page and intentionally does not include dashboard Quick
  Launch controls.
- `/me preferences` remains private and supports inventory report visibility updates through the
  existing service-backed persistence path.
- Legacy account, reminder, inventory preference, and export commands remain live.

Phase 5 explicitly deferred:

- card-based visual output for `/me accounts`, `/me reminders`, `/me preferences`, and
  `/me exports`
- a single guided Account `Manage` journey that carries lookup results into register/replace
- a single guided Reminder `Manage` journey with save/update and remove-all/unsubscribe actions
- refresh behavior for visible dashboard/subpage cards after account or reminder mutations
- additional preference categories without a proven persistence contract
- legacy command redirects or removal

Use the Phase 6 task pack for the next implementation phase:

`docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 6 Guided Management Cards and Workflow Simplification.md`

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
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 4 Modern Reminder Centre.md`
- `docs/player_self_service_command_centre_briefing.md`

For preference persistence, export behavior, inventory visibility, or SQL-facing output data, validate
the live source contracts before implementation. If a Phase 5 slice uses only existing JSON/service
preference paths, document that explicitly.

## 3. Objective

Turn the private `/me dashboard` from an embed-only status page into a premium generated visual
dashboard card, and extend `/me preferences` into a first-pass private preferences hub only where
safe service-backed preference writes already exist.

The dashboard card should make player setup status obvious at a glance without becoming a dense
control panel. Phase 5 must preserve the delivered `/me` navigation, account centre, reminder
centre, legacy commands, and quick-launch behavior.

## 4. Background

Phase 1 audit/design is complete and archived.

Phase 2 delivered the private `/me` shell in mirror PR #164 and production PR #472:

- `/me dashboard`
- `/me accounts`
- `/me reminders`
- `/me preferences`
- `/me exports`
- private dashboard/page navigation
- dashboard Quick Launch guidance

Phase 3 delivered the modern `/me accounts` account centre in mirror PR #165 and was smoke tested
successfully by the operator on 2026-06-22.

Phase 4 delivered the modern `/me reminders` reminder centre in mirror PR #166 and production PR
#474. Smoke testing confirmed:

- `/me reminders` remains private.
- players can review reminder setup.
- players can subscribe and update event types/timings through the Manage flow.
- unsubscribe requires confirmation.
- confirmation DMs are best-effort and non-blocking.
- legacy reminder commands remain live.
- event-type logic now matches the intended KVK model:
  - `Ruins` means non-fight ruins events.
  - `Altars` means altar fights.
  - `Major` means all major timeline events.
  - `Fights` means altar fights plus major events whose title/description is marked `FIGHT`.
  - overlapping selections are normalized to avoid duplicate reminders.

Known follow-up from Phase 3 remains active:

- account-centre lookup results should later carry into register/replace flows so players do not
  have to remember or re-enter a Governor ID after lookup.

Known follow-up from Phase 4 remains active:

- legacy reminder commands can later be routed through the modern reminder service, then redirected
  or removed only after separate operator approval.

## 5. Scope

### In Scope

- Audit the current `/me dashboard` summary data contract and visual-card render options before
  coding.
- Design and implement a generated private `/me dashboard` card if approved after audit.
- Keep the card calm and summary-first:
  - identity header
  - linked-account status
  - main account status
  - reminder status and summary
  - inventory visibility/preference status
  - exports/privacy note
  - clear next actions
- Preserve existing dashboard buttons/selects and Quick Launch behavior.
- Add or extend a renderer/service layer for card data shaping; do not put rendering/business
  logic in `commands/me_cmds.py`.
- Extend `/me preferences` only for preference writes backed by existing service/persistence paths,
  with inventory visibility as the likely first candidate.
- Preserve `/inventory_preferences` and existing inventory visibility behavior until redirects are
  separately approved.
- Update tests for card payload/rendering, preference service handoff, command/view behavior, and
  fallback behavior.
- Update player/operator briefing and command docs.
- Capture out-of-scope visual polish, preference expansion, and legacy cleanup structurally.

### Out of Scope

- Removing, redirecting, or deprecating legacy commands.
- Reworking `/me accounts`, `/me reminders`, or `/me exports` beyond integration with the dashboard
  summary.
- Full `/my_stats`, inventory report, or export redesign.
- SQL schema changes unless a separately approved persistence contract requires them.
- Building a website or web dashboard.
- Adding new preference categories without an existing reliable persistence and service path.
- Public dashboard output.
- Complex recommendation, achievement, badge, or notification-inbox features.

## 6. Product Requirements

The first screen should feel like a personal command centre, not a list of legacy command names.

Dashboard card requirements:

- private only
- compact, readable, and status-first
- no oversized marketing hero or decorative filler
- no busy grid of every action
- visually aligned with the modern KVK card quality bar
- robust fallback to embed-only output if image rendering fails
- no misleading setup status when a source is unavailable
- no text overlap at typical Discord desktop and mobile preview sizes

Preferences hub requirements:

- private only
- service-backed writes only
- clear current status before mutation
- confirmation where a setting materially changes visibility/privacy
- no persistence writes directly from commands or views
- no "coming soon" controls

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Phase 5 crosses command shell, services, views, generated visual artifacts, preferences, persistence, and tests. |
| `k98-discord-command-feature` | use | `/me dashboard` output and `/me preferences` interactions are Discord user-facing flows. |
| `k98-sql-validation` | use if SQL-backed contracts are touched | Validate if dashboard/preference data depends on SQL views, procedures, exports, reports, or DAL queries. |
| `k98-test-selection` | use | Select focused service/view/rendering tests plus standard validators. |
| `k98-deferred-optimisation-capture` | use | Capture out-of-scope visual polish, preference expansion, account lookup carry-forward, and legacy cleanup. |
| `k98-pr-review` | use before handoff | Review architecture, command safety, tests, docs, and rollout boundaries. |
| `k98-promotion-check` | use only before production promotion | Not needed for initial mirror PR unless promotion is requested. |
| `codex-security:security-scan` | consider before PR handoff | Required if user-controlled inputs, preference/privacy writes, file/image handling, or Discord interaction security surfaces change. |

## 8. Mandatory Workflow

1. Start with audit/scope only unless the operator explicitly approves one-pass implementation.
2. Map current `/me dashboard` data, renderer options, view behavior, and fallback behavior.
3. Map current `/me preferences` data and existing inventory preference persistence/write paths.
4. Validate SQL contracts if any SQL-backed status/output/preference data is used.
5. Present implementation and test plan for approval.
6. Implement the approved Phase 5 slice.
7. Add or update focused tests.
8. Run selected validators and tests.
9. Run or explicitly justify Codex Security review.
10. Update both mirror and production PR branches only after local validation if requested.

## 9. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | Keep `commands/me_cmds.py` thin. |
| Dashboard data | Existing `player_self_service/service.py` summary contract, or a focused dashboard service if needed. |
| Card rendering | A focused renderer/helper module; no rendering logic in command callbacks. |
| Preferences | Existing inventory/preference service paths; no ad hoc persistence in views. |
| Views | `ui/views/player_self_service_views.py` or a focused preferences view module if complexity grows. |
| Legacy commands | Preserve `/inventory_preferences`, account commands, reminder commands, export commands, and KVK outputs. |
| Tests | Focused command, service, view, renderer, preference, import, and command-registration tests. |
| Documentation | Programme pack, briefing, command reference, task-pack README. |

Services and renderers must not depend on Discord `ctx`/`Interaction` objects unless they are
explicitly view/adapter code. Commands and views must not own business rules or persistence writes.

## 10. Likely Files

### Review

- `commands/me_cmds.py`
- `player_self_service/service.py`
- `player_self_service/account_service.py`
- `player_self_service/reminder_service.py`
- `ui/views/player_self_service_views.py`
- `ui/views/player_self_service_account_views.py`
- `ui/views/player_self_service_reminder_views.py`
- `commands/inventory_cmds.py`
- `inventory/`
- `services/`
- existing KVK card renderers and visual asset helpers
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- `docs/player_self_service_command_centre_briefing.md`

### Likely Modify

- `player_self_service/service.py`
- `ui/views/player_self_service_views.py`
- `tests/test_me_cmds.py`
- `tests/test_player_self_service_service.py`
- `tests/test_player_self_service_views.py`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`

### Likely Create

- `player_self_service/dashboard_card.py` or similar focused renderer module if no existing
  suitable renderer exists.
- `player_self_service/preference_service.py` if preference mutation would make the base service
  too broad.
- `ui/views/player_self_service_preference_views.py` if preference controls become too broad for
  the existing view module.
- `tests/test_player_self_service_dashboard_card.py` for card payload/rendering behavior.
- `tests/test_player_self_service_preference_service.py` if a dedicated service is added.

## 11. Refactor Triggers To Check

| Trigger | Phase 5 decision guidance |
|---|---|
| Direct persistence writes in commands/views | Do not add; route through service/persistence owners. |
| Business logic in views | Keep view callbacks to interaction routing and service calls. |
| Duplicate visual card helpers | Reuse existing render helpers/assets where suitable; defer larger consolidation if risky. |
| Dead legacy flow | Do not remove legacy commands in Phase 5; capture redirect/removal work for a later phase. |
| Fragile preference persistence | Improve if in scope and low risk; otherwise capture structurally. |
| Card rendering failure path | Add safe embed fallback and tests. |
| Process friction | Reduce repeated inputs where possible; capture larger workflow simplifications. |

## 12. Testing Requirements

Run or justify skipping:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
```

Focused tests should cover:

- dashboard summary with no accounts/reminders/preferences
- dashboard summary with active account and reminder data
- generated card payload/render path
- image-render failure fallback to embed output
- `/me dashboard` privacy and command/view handoff
- `/me preferences` current-state display
- any approved preference write path and persistence handoff
- non-owner interaction rejection
- timeout/fallback behavior
- command registration remaining unchanged
- legacy commands remaining registered and usable

Likely pytest commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_preferences.py tests\test_inventory_report_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py
```

Broaden to full pytest before production promotion when practical because dashboard rendering and
preferences touch player-facing workflows.

## 13. AI Review Gate

Run Codex Security before PR handoff or explicitly justify skipping if Phase 5 changes:

- Discord interactions
- preference/privacy writes
- generated file/image handling
- user-controlled display data
- persistence or export behavior

For documentation-only audit or task-pack-only work, document a skip reason.

## 14. Acceptance Criteria

- [ ] `/me dashboard` remains private.
- [ ] Dashboard output includes a generated visual card or an approved documented deferral.
- [ ] Dashboard card summarizes account, reminder, preference, and export/privacy status clearly.
- [ ] Dashboard has a safe embed fallback if image rendering fails.
- [ ] Existing dashboard Quick Launch behavior is preserved.
- [ ] `/me preferences` remains private.
- [ ] Any preference mutation is service-backed and uses existing persistence paths.
- [ ] `/inventory_preferences` and other legacy self-service commands remain live.
- [ ] No persistence writes are added to commands or views.
- [ ] No SQL schema changes are introduced without separate approval and SQL validation.
- [ ] Focused tests and standard validators pass.
- [ ] Visual/card fallback behavior is tested or manually documented where automation is limited.
- [ ] Codex Security is run or explicitly justified.
- [ ] Deferred findings are captured structurally.

## 15. PR Summary Template

```md
## Summary

- Added the Phase 5 visual `/me dashboard` card and/or approved dashboard-card foundation.
- Extended the private preferences hub where service-backed preference writes were approved.
- Preserved delivered account/reminder flows and legacy self-service commands.

## Changes

- <dashboard card / renderer / service changes>
- <preferences changes>
- <docs/tests>

## Tests

- <commands run>

## Visual / Fallback

- <card render notes and fallback behavior>

## AI Review Gates

- Codex Security: <run or skipped with reason>

## Risk / Rollback

- Roll back by disabling the generated dashboard attachment path and falling back to the existing
  embed dashboard while preserving `/me` navigation and legacy commands.
```
