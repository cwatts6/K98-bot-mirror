# Codex Task Pack - Player Self-Service Command Centre v2 Phase 5D Premium Reminders Summary Card

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 5D Premium Reminders Summary Card`
- Date: `2026-07-14`
- Owner/context: Follow-on from completed and operator-accepted GovernorOS v2 Phase 5C Accounts.
- Task type: `audit and product workshop | premium Reminders renderer | Discord interaction`
- One-pass approved: `No`
- Implementation approved: `No - product and visual workshop must complete first`
- Status: `next active GovernorOS slice - workshop ready`
- Current runtime backdrop: `assets/me/cards/me reminders.png` (`1702 x 924`)

Phase 5D starts with the operator's improvement ideas. Do not lock the information hierarchy,
backdrop treatment, metrics, guidance, or exact controls before the workshop records explicit
decisions. Repository inspection and visual/product options are approved; runtime implementation is
not.

## 2. Required Reading

Read first:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 4 Modern Reminder Centre.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 7 Unified Reminder Centre and Dashboard Card Alignment.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- `docs/reference/events_and_dm_reminders.md`
- the GovernorOS Visual Design Bible where present

Read the current code and focused tests listed in section 9 before proposing product options.

## 3. Objective

Workshop and then, only after approval, deliver a materially improved private `/me reminders`
summary card that matches the premium GovernorOS standard established by Phase 5C while making the
combined KVK and calendar reminder state easier to understand and manage.

The outcome must preserve the two existing reminder systems and their restart-safe management
workflows unless a later explicitly approved scope changes them.

## 4. Current Authoritative Flow

```text
/me reminders
-> commands/me_cmds.py
-> ui/views/player_self_service_views.py
-> player_self_service/service.py builds PlayerSelfServiceSummary
   -> legacy KVK config through subscription_tracker/get_user_config
   -> calendar config through event_calendar.reminder_config_service
-> player_self_service/page_cards.py renders the current 1702x924 card
-> current successful page is presented through an embed-wrapped attachment
-> concise private embed is the fallback

Manage
-> player_self_service/reminder_service.py builds current KVK ReminderCentreState
-> ui/views/player_self_service_reminder_views.py
   -> KVK event/time autosave and confirmation DM
   -> Calendar Settings handoff
   -> Remove All confirmation and current-state revalidation
-> successful mutation refreshes the host Reminders summary
```

The current summary exposes:

- KVK reminder state, event summary, and reminder times;
- calendar reminder state, event summary, and lead times;
- combined state and next-action guidance;
- one `Manage` entry into the existing guided child flow.

## 5. Locked Programme Baseline

These points are inherited from accepted phases and are not workshop choices:

- `/me reminders` is private/ephemeral and author-gated.
- It is scoped to the invoking Discord user's reminder configuration, not to one governor.
- It has no implicit selected-governor filter and never displays `Change Governor`.
- An optional validated dashboard governor may be retained only so `Dashboard` can return to that
  governor; it must not alter reminder data.
- Successful premium output defaults to a standalone `1702x924` private attachment with stable
  `me_reminders_<discord_user_id>.png` filename unless the workshop explicitly approves another
  tested dimension.
- The best-effort invoking-user Discord avatar at the upper left is the accepted personal-summary
  default. Reads remain author-validated and timeout-bounded, with a clean fallback.
- Rendering stays off the event loop. Rendering/delivery failure uses the same already-authorized
  payload and does not trigger a second data fetch.
- Every transition deliberately replaces attachments and closes image/file streams on success,
  fallback, timeout, cancellation, stale suppression, and delivery failure.
- Timeout preserves the private report, visibly disables controls, rejects later interactions, and
  gives concise rerun guidance.
- Real Discord components provide navigation and actions; no fake controls are painted into the
  image.
- Do not create a broad renderer/view framework as part of this page slice.

## 6. Reminder Behaviour To Preserve By Default

Until a workshop decision explicitly expands scope, preserve:

- the combined legacy KVK subscription and event-calendar reminder systems;
- current event types, time/lead-time choices, normalization, and duplicate avoidance;
- KVK autosave/update wording and confirmation DM behavior;
- Calendar Settings event/lead-time management;
- Remove All confirmation, current-state revalidation, task cancellation, scheduled/sent tracker
  cleanup, and unsubscribe wording;
- persisted legacy KVK subscription/scheduled/sent state and calendar preference/delivery state;
- scheduler, rehydration, duplicate-send prevention, retry, DM, and event-source behavior;
- current redirects from legacy subscription/calendar-reminder commands;
- command registration, privacy, logging, and service ownership.

No SQL schema/table/view/index, reminder persistence redesign, event source change, scheduler change,
lead-time change, DM policy change, or calendar behavior change is approved by this pack.

## 7. Product And Visual Workshop Agenda

The workshop must decide and record:

1. The primary question the Reminders card should answer in five seconds.
2. The state vocabulary and hierarchy across KVK and calendar reminders.
3. Which genuine existing values deserve headline treatment and which belong in supporting detail.
4. Whether any additional value, such as next scheduled event or next DM, has an authoritative
   existing source and stable freshness contract; do not infer or invent it.
5. The deterministic guidance/insight priority for off, incomplete, partially configured,
   unavailable, and fully configured states.
6. Whether the existing `assets/me/cards/me reminders.png` backdrop is retained, adjusted through
   layout only, or replaced by a separately approved runtime asset.
7. Exact avatar position, typography, spacing, populated/no-data balance, and UTC refresh wording.
8. Exact component rows. Start from blue Accounts/Reminders/Preferences navigation, page-relevant
   secondary navigation, and the existing Manage action; do not copy an irrelevant Accounts button
   merely for symmetry.
9. Whether the single Manage journey remains the only child action or whether clearer KVK/Calendar
   entry points are worth a separately approved workflow change.
10. Original-size, Discord desktop, and Discord mobile examples for configured, partial/off, and
    unavailable states.

Do not substitute the current renderer layout for a product decision. Do not pre-approve a new
metric merely because there is empty space.

## 8. Governor Dropdown And Context Matrix

Phase 5D must follow the programme matrix:

| Surface | Scope | Governor control |
|---|---|---|
| Reminders summary | Discord user | No Change Governor |
| Reminder Manage / Calendar Settings | Discord user | No Change Governor |
| Dashboard | Selected governor | Paged Change Governor when multiple are linked |
| Resources / Materials / Speedups | Selected governor | Paged Change Governor when multiple are linked |
| Preferences summary | Discord user | No Change Governor; Update VIP resolves governor explicitly |
| Inventory summary | All linked / user | No Change Governor; Open Report resolves governor explicitly |
| Exports summary | User/all-linked under current contract | No Change Governor; Phase 6 owns any selected-export decision |
| Future History | Selected governor | Change Governor under the accepted selected-governor contract |

## 9. Likely Files

### Review

- `commands/me_cmds.py`
- `ui/views/player_self_service_views.py`
- `ui/views/player_self_service_reminder_views.py`
- `player_self_service/service.py`
- `player_self_service/reminder_service.py`
- `player_self_service/page_cards.py`
- `event_calendar/reminder_config_service.py`
- `event_calendar/reminder_prefs.py`
- `event_calendar/reminder_prefs_store.py`
- `event_calendar/reminder_state.py`
- `event_calendar/reminders.py`
- `subscription_tracker.py`
- `event_scheduler.py`
- `reminder_task_registry.py`
- `tests/test_player_self_service_views.py`
- `tests/test_player_self_service_service.py`
- `tests/test_player_self_service_reminder_service.py`
- `tests/test_player_self_service_page_cards.py`
- `tests/test_calendar_reminder_config_service.py`
- `tests/test_calendar_reminder_prefs.py`
- `tests/test_calendar_reminders.py`
- `tests/test_calendar_reminders_dispatch.py`

### Modify After Workshop Approval

- renderer/view/service/model/test/docs files proven necessary by the approved design only.

### Create

- A dedicated typed Reminders renderer/payload module only if the approved design cannot remain
  cleanly owned by the existing service/page-card boundaries. Do not create it speculatively.

## 10. Skills

- `k98-architecture-scope`
- `k98-discord-command-feature`
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review`
- `codex-security:security-scan` when implementation touches the Discord/persistence/file surfaces

Use `k98-sql-validation` only if an approved field or design genuinely introduces a SQL dependency.
Use `k98-promotion-check` only at the later production-promotion gate.

## 11. Audit And Escalation Gates

Escalate before implementation when:

- an approved headline field has no authoritative source;
- the desired design requires reminder scheduling, event source, DM, persistence, calendar, or SQL
  behavior to change;
- the current 1702x924 asset is rejected or another asset is required;
- Discord component limits make the approved controls impossible;
- current reminder scope is discovered to be governor-specific contrary to repository evidence;
- a restart-safety or duplicate-send defect must be fixed to deliver the visual change safely.

Capture useful out-of-scope findings in `docs/reference/deferred_optimisations.md` using the required
structured format. Do not silently expand Phase 5D.

## 12. Validation Contract After Implementation Approval

At minimum cover:

- direct `/me reminders` entry and navigation from a selected Dashboard;
- author, foreign, stale, forged, concurrent, timeout, and cancellation paths;
- KVK on/off/incomplete/unavailable and calendar on/off/incomplete/unavailable combinations;
- long/Unicode display names and honest missing values;
- same-payload fallback, render failure, delivery failure, attachment replacement, and stream close;
- Manage entry, KVK autosave, Calendar Settings, confirmation DM, Remove All confirmation,
  current-state revalidation, host refresh, and existing wording contracts;
- restart/persistence, unsubscribe cancellation, and duplicate-send regressions if touched;
- original 1702x924, Discord desktop, and Discord mobile samples for meaningful states;
- architecture/deferred/test selection gates, focused tests, pre-commit, full pytest where runtime
  code changes, command registration, smoke imports, and Codex Security review.

## 13. Acceptance Criteria

- [ ] Current command/view/service/persistence/renderer flow is mapped with repository evidence.
- [ ] Operator improvement ideas are recorded and converted into explicit product decisions.
- [ ] Information hierarchy, genuine values, guidance priority, avatar/backdrop, and controls are
  approved before implementation.
- [ ] Reminders stays Discord-user-scoped and has no Change Governor.
- [ ] Existing KVK/calendar management and restart behavior remain unchanged unless separately
  approved and tested.
- [ ] Successful output follows the accepted standalone premium format with same-payload fallback
  and complete attachment/stream cleanup.
- [ ] Focused/full validation, security review, visual samples, and operator smoke are recorded.
- [ ] Programme, briefing, canonical reference, task-pack index, and deferred backlog reflect the
  delivered outcome.

## 14. First Workshop Output

Before any code change, provide:

1. concise current-flow and data-source map;
2. current-card visual critique at original/desktop/mobile size;
3. the operator's ideas grouped into content, hierarchy, actions, and visual treatment;
4. two or three coherent design options with tradeoffs;
5. explicit decisions still needed;
6. proposed locked implementation contract after those decisions are approved.
