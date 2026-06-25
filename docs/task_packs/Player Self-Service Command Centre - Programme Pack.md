# Player Self-Service Command Centre — Programme Pack

## 1. Programme Header

- Programme name: `Player Self-Service Command Centre`
- Date: `2026-06-22`
- Owner/context: K98 Bot player self-service redesign following completion of the KVK Player Experience Redesign programme
- Programme type: Product UX / Discord command architecture / visual output redesign / player workflow consolidation / deferred optimisation programme
- One-pass approved: No
- Headline: **Every player now has a personal command centre.**

## Current Programme Status

Status as of 2026-06-25:

- Phase 1 audit and design is complete and archived as a historical execution record.
- Phase 2 `/me` command shell and navigation foundation is delivered in mirror PR #164 and
  production PR #472 and smoke tested successfully.
- Phase 3 Modern Account Centre is delivered in mirror PR #165, smoke tested successfully by the
  operator on 2026-06-22, and preserved for later account-flow simplification.
- Phase 4 Modern Reminder Centre is delivered in mirror PR #166 and production PR #474, smoke
  tested successfully by the operator.
- Phase 5 Visual `/me dashboard` Card and First-Pass Preferences is delivered in production PR
  #475 and smoke tested successfully by the operator on desktop, mobile, and iPad.
- Phase 6 Guided Management Cards and Workflow Simplification is delivered in mirror PR #168 and
  smoke tested successfully by the operator on 2026-06-24.
- Phase 7 Unified Reminder Centre and Dashboard Card Alignment is delivered in production PR
  #477 and smoke tested successfully by the operator on 2026-06-25.
- The delivered `/me` surface now includes a private command-centre shell, a generated dashboard
  card with safe embed fallback, generated cards for Accounts, Reminders, Preferences, and
  Exports, account-centre lookup/register/replace/remove management, unified KVK/calendar
  reminder status and management, KVK reminder autosave and remove-all management, calendar
  reminder autosave/remove-all management, inventory visibility and Governor VIP controls, export
  guidance, graceful timeout handling, and return navigation. Legacy account, reminder, inventory,
  calendar reminder, and export commands remain live.
- Next active implementation phase: Phase 8 Exports Launchpad and Quick Launch Expansion.

Phase 2 manual smoke evidence:

- `/me dashboard` responds privately and shows the expected dashboard sections and controls.
- Quick Launch works and shows guidance for KVK stats, KVK targets, KVK history, KVK rankings,
  inventory, and exports.
- `/me exports` opens the exports page with page navigation only; the dashboard Quick Launch menu
  remains dashboard-only by design.
- Existing legacy commands still work.

Phase 3 manual smoke evidence:

- `/me accounts` remained private and opened the modern account centre.
- Governor ID lookup, registration, replacement, removal with confirmation, and return navigation
  were smoke tested successfully.
- Legacy account commands remained registered and usable.
- Review-feedback hardening preserved interaction fallback behavior, timeout message references,
  all 26 account slots, and stale-removal confirmation safety.

Phase 3 process-learning for later phases:

- The path from `Find ID` to `Register` still has too much friction: players can look up a
  Governor ID by name or partial name, but then need another click and must remember or manually
  re-enter the 9-digit ID to register the account.
- A later account-centre optimisation should carry selected lookup results into register/replace
  flows.
- Every later phase should actively optimise player process: fewer buttons, fewer repeated inputs,
  fewer memory steps, and no legacy-command-shaped button piles.

Phase 4 manual smoke evidence:

- `/me reminders` remained private and opened the modern reminder centre.
- Players could review current reminder setup.
- Subscribe/update through event and timing selectors worked.
- Unsubscribe required confirmation.
- Legacy reminder commands remained registered and usable.
- Final reminder category logic matched the intended KVK model: `Ruins` means non-fight ruins,
  `Altars` means altar fights, `Major` means all major events, and `Fights` means altar fights
  plus major events marked `FIGHT`, with overlapping selections normalized to prevent duplicate
  reminder DMs.

Phase 5 manual smoke evidence:

- `/me dashboard` remained private and delivered a generated visual dashboard card.
- The card summarized account, reminder, inventory preference, and export privacy status.
- The card rendered reliably on desktop, mobile, and iPad after the final embed-image delivery and
  stacked mobile-friendly layout refinements.
- Dashboard text was simplified: timestamp-only header metadata, `Linked: multiple`,
  no system-only DM status, and `Exports: private`.
- The old duplicate embed/card information was removed so the dashboard shows one primary visual
  summary plus Discord-native controls.
- Accounts, Reminders, and Preferences opened private pages as expected.
- Dashboard Quick Launch remained dashboard-only; `/me exports` continued to open the exports page
  without the dashboard Quick Launch menu.

Phase 6 manual smoke evidence:

- `/me accounts`, `/me reminders`, `/me preferences`, and `/me exports` remained private and
  rendered generated visual cards with safe embed fallback.
- Account controls were simplified around one primary `Manage` journey.
- Account lookup results could continue into register/replace flows without manual Governor ID
  re-entry.
- Account duplicate/invalid Governor ID checks were surfaced earlier in the guided flow.
- Reminder controls were simplified around one primary `Manage` journey.
- Reminder event-type and reminder-time changes auto-saved, refreshed the card, and preserved the
  Phase 4 KVK reminder semantics.
- Reminder remove-all/unsubscribe used confirmation and behaved correctly.
- Preference controls used a single inventory visibility toggle and opened the existing Governor
  VIP update path.
- Preference cards showed account VIP levels where available.
- Exports gained a generated private card but intentionally remained a guidance page without
  dashboard Quick Launch.
- Main `/me` cards and reminder child selector windows timed out gracefully with disabled controls.
- Legacy account, KVK reminder, inventory preference, VIP update, and export commands remained
  live.
- Smoke feedback captured two important follow-ups: calendar reminders remain separate from the
  KVK reminder centre, and the Phase 5 dashboard card now looks visually out of step with the new
  Phase 6 subpage cards.

Phase 5 process-learning for later phases:

- `/me accounts` and `/me reminders` still expose too many separate controls for the intended
  "Manage" journey. The next phase should collapse those into guided flows.
- The switch from a dashboard card to embed-only subpages makes the user experience feel mixed.
  Subpages should move to generated cards with safe embed fallback.
- Reminder saves can leave an older dashboard card visible above the refreshed reminder page until
  the player returns to Dashboard. Later work should define refresh behavior so visible cards do
  not show stale state.
- Discord image regions cannot be clicked directly. The closest practical UX is a card-like
  visual layout paired with native buttons/selects whose labels and order match the card sections.

## 2. Programme Vision

Create a premium, app-like player self-service layer inside Discord that lets every player manage their identity, accounts, reminders, preferences, and personal outputs from one coherent place.

The end state should feel like a small player portal inside Discord, not a list of legacy commands. Players should be able to open one obvious command group, understand their setup status immediately, and move into the right action without needing to remember old command names.

The programme must be ambitious in output quality, but deliberately restrained in navigation complexity. The dashboard should be clear, calm, and guided. Detailed actions should live one layer deeper so the first screen never becomes a control panel nobody understands.

## 3. Why This Programme Exists

The KVK player command surface has now been redesigned into a unified, highly visual, modern suite. `/kvk stats`, `/kvk targets`, `/kvk history`, and `/kvk rankings` now have a consistent product feel and have set a new quality bar for player-facing bot output.

The remaining player self-service commands are still split across development-era entry points. Players currently need to remember separate commands for account registration, Governor ID lookup, account review, subscription setup, reminder changes, inventory preferences, personal exports, and older personal stats flows.

This creates three problems:

- **Discoverability** — players do not always know which command to use.
- **Fragmentation** — account identity, reminders, preferences, and outputs feel unrelated even though they are part of the same player setup.
- **Future drag** — new player-facing features will keep adding commands unless there is a strong self-service home.

This programme turns the remaining player self-service surface into a coherent product journey.

## 4. Product Goal

Give every player a single personal command centre that answers:

- Who am I registered as?
- Are my accounts set up correctly?
- Am I subscribed to the reminders I need?
- What are my current preferences?
- Where do I go next for KVK stats, targets, history, rankings, inventory, and exports?
- What action do I need to take if something is missing?

The key product promise is:

```text
Run /me dashboard. Everything personal starts there.
```

## 5. Target Command Model

### Proposed new player command group

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me exports
```

### Command purpose

| Command | Purpose |
|---|---|
| `/me dashboard` | The premium personal home screen: setup status, key identity information, reminder status, and quick launch controls. |
| `/me accounts` | Modern account centre replacing separate lookup/register/review/modify habits. |
| `/me reminders` | Modern reminder centre replacing separate subscribe/modify/unsubscribe habits. |
| `/me preferences` | First-pass personal settings hub, including inventory visibility and output privacy defaults. |
| `/me exports` | Guided personal export launchpad for existing stats and inventory export flows. |

### Legacy command paths to evaluate for consolidation or redirect

```text
/register_governor
/modify_registration
/my_registrations
/mygovernorid
/subscribe
/modify_subscription
/unsubscribe
/inventory_preferences
/my_stats_export
/export_inventory
```

### Related commands to link, not redesign in the first build

```text
/kvk stats
/kvk targets
/kvk history
/kvk rankings
/myinventory
/my_stats
/player_profile
/mykvkcrystaltech
```

The first build should not remove useful legacy commands immediately. It should introduce the new `/me` experience in parallel, prove it is easier to use, then redirect or retire old commands through a controlled migration phase.

## 6. Navigation Model

The main design principle is **progressive disclosure**.

### `/me dashboard` should be simple

The dashboard should have no more than three primary sections:

1. **Accounts**
2. **Reminders**
3. **Preferences / Quick Links**

It should show status, not every possible action.

Example dashboard controls:

```text
[Accounts] [Reminders] [Preferences]
Quick Launch: select menu or compact buttons for KVK / Inventory / Exports
```

### `/me accounts` should handle account work

Account actions should sit behind the account centre:

```text
Review accounts
Register account
Modify account
Remove account
Find Governor ID
Set default/main account
```

### `/me reminders` should handle reminder work

Reminder actions should sit behind the reminder centre:

```text
View current reminder setup
Subscribe
Change event types
Change reminder times
Unsubscribe
Check DM status / troubleshooting guidance
```

### `/me preferences` should stay lightweight

The first pass should focus only on preferences that already exist or are clearly needed:

```text
Inventory visibility
Default output privacy where supported
Preferred account / main account behaviour
Future: timezone/local-time preferences if the calendar stack supports it
```

### `/me exports` should be a launchpad, not a rewrite

The first pass should guide users to existing export capability. It should not redesign the full export generation logic unless Phase 1 proves there is a strong reason to do so.

## 7. Target User Journeys

### Journey A — New player setup

A new player runs `/me dashboard`.

The bot should show:

- no registered accounts
- clear explanation of why registration matters
- one obvious action: **Register Account**
- optional **Find Governor ID** action if they do not know their ID
- reminder setup as incomplete but not overwhelming

Success means the player can go from no setup to linked main account without needing to know `/register_governor` or `/mygovernorid`.

### Journey B — Existing player review

An existing player runs `/me dashboard`.

The bot should show:

- their registered accounts in a compact identity summary
- whether they have a main/default account
- whether reminders are enabled
- current reminder types and times
- quick launch buttons/selects for KVK stats, targets, history, rankings, inventory, and exports

Success means the player can confirm their setup in under ten seconds.

### Journey C — Player changes account

A player runs `/me accounts`.

The bot should show account slots and actions. The player should be able to select a slot, enter or search for a Governor ID, confirm the replacement, and return to the account centre.

Success means account changes are guided, validated, and reversible through clear confirmation.

### Journey D — Player changes reminders

A player runs `/me reminders`.

The bot should show whether they are subscribed, what event types they receive, what reminder times they receive, and whether DMs appear available. They should be able to update choices or unsubscribe in the same interaction.

Success means `/subscribe`, `/modify_subscription`, and `/unsubscribe` become one understandable reminder journey.

### Journey E — Player launches outputs

A player runs `/me dashboard`, then chooses a quick launch.

The bot should route them to existing high-quality outputs where possible:

- `/kvk stats`
- `/kvk targets`
- `/kvk history`
- `/kvk rankings`
- `/myinventory`
- export options

Success means `/me` does not duplicate every feature. It becomes the route map.

## 8. Visual Direction

The new visual language should be consistent with the modern KVK cards without making every screen feel like KVK.

Target direction:

- premium player identity card
- Discord avatar / player identity header
- KD98/K98 Bot branding
- compact status panels
- account completeness indicator
- reminder status indicator
- preference status chips
- quick launch area
- clean footer showing data freshness / privacy note

Recommended first visual card shape:

```text
1180 x 640 px
Landscape rectangle
Opaque PNG
sRGB/RGB
Same broad card language as KVK stats/targets/history/rankings
```

The visual card should be calm and uncluttered. It should not contain every account slot, every reminder type, and every quick link at full detail. The first screen should be a summary with a clear next action.

## 9. Design Principles

1. **One personal home** — players should know `/me dashboard` is the starting point.
2. **Not busy by default** — the dashboard shows status and primary actions, not every option.
3. **Progressive disclosure** — detailed actions live inside `/me accounts`, `/me reminders`, `/me preferences`, and `/me exports`.
4. **Player-first language** — command names and card wording should match user questions, not implementation history.
5. **No sudden removals** — legacy commands remain during rollout, then redirect/deprecate after validation and communication.
6. **Consistent with KVK visual quality** — use the same polish, hierarchy, and interaction discipline as the KVK redesign.
7. **Commands and views stay thin** — orchestration belongs in services; data access belongs in repositories/DAL.
8. **No misleading setup status** — only show completion, DM state, account validity, or preferences when the underlying source is trustworthy.
9. **Website-ready thinking** — data shapes and card components should prepare for the longer-term KD98 webapp direction.
10. **Discord-safe UX** — response visibility, button limits, select menus, timeouts, and restart-sensitive views must be designed explicitly.

## 10. Programme Phases

### Phase 1 — Audit and Design Only

Status: complete and archived.

Audit the current player self-service commands, views, services, storage, usage, docs, tests, and player journeys before implementation.

Deliver:

- current command map
- legacy command consolidation options
- proposed `/me` command model
- dashboard information architecture
- account centre journey
- reminder centre journey
- preferences/export first-pass journey
- visual wireframe / card layout proposal
- interaction model and button/select budget
- migration/deprecation plan
- implementation phase plan
- first implementation task pack recommendation

No runtime code changes.

### Phase 2 — `/me` Command Shell and Navigation Foundation

Status: delivered in mirror PR #164 and production PR #472, and smoke tested successfully.

Create the new `/me` command group and safe navigation shell in parallel with legacy commands.

Likely target commands:

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me exports
```

Delivered scope:

- `/me dashboard`, `/me accounts`, `/me reminders`, `/me preferences`, and `/me exports`
- read-only player self-service summary service
- private dashboard embed with account, reminder, and preference status
- page navigation buttons with ownership checks and timeout handling
- dashboard Quick Launch guidance for KVK outputs, inventory, and exports
- command governance and canonical command reference updates
- focused command, service, view, inventory preference, and command-registration tests
- player/operator briefing

This phase proved command registration, permissions, response visibility, navigation, fallback
behaviour, and basic service boundaries before deeper account/reminder mutation or generated
visual-card work.

### Phase 3 — Modern Account Centre

Status: delivered in mirror PR #165 and smoke tested successfully on 2026-06-22.

Replace fragmented account behaviours with one account centre journey.

Target consolidation:

```text
/register_governor
/modify_registration
/my_registrations
/mygovernorid
```

Delivered scope:

- account summary view
- register / replace / remove flows
- Governor ID lookup from the account centre
- duplicate ownership handling
- slot management
- confirmation for replacement and removal
- return navigation to Account Centre and Dashboard
- service-owned account decisions and registry-service-backed writes
- focused service/view/command tests, full pytest, pre-commit, and Codex Security review

Legacy account commands remain live until redirects are separately approved.

Known follow-up from Phase 3 smoke:

- Optimise the player journey from Governor ID lookup to registration/replacement so a selected
  lookup result can carry forward instead of requiring manual ID recall and re-entry.

### Phase 4 — Modern Reminder Centre

Status: delivered in mirror PR #166 and production PR #474, and smoke tested successfully by the
operator.

Replace fragmented reminder behaviours with one reminder centre journey.

Target consolidation:

```text
/subscribe
/modify_subscription
/unsubscribe
```

Delivered scope:

- current subscription summary
- event type selector
- reminder time selector
- unsubscribe flow
- best-effort confirmation DM after successful save/unsubscribe
- service-backed reminder state and mutation models
- reminder selector normalization to avoid duplicate DMs
- scheduler matching fix for `Fights` event semantics
- process simplification review so players do not repeat selections or copy values between steps

Legacy `/subscribe`, `/modify_subscription`, and `/unsubscribe` remain registered and usable until
redirects or removal are separately approved.

### Phase 5 — Visual `/me dashboard` Card and First-Pass Preferences

Status: delivered in production PR #475 and smoke tested successfully on 2026-06-23.

Built the premium dashboard card and extended the lightweight preferences hub where an existing
service-backed persistence path was available.

Delivered scope:

- Pillow-generated private `/me dashboard` card.
- Safe embed fallback when rendering or image delivery fails.
- Desktop and mobile/iPad-readable dashboard layouts.
- Account, reminder, preference, and export/privacy status summary.
- Simplified player-facing card copy and consistent status pills.
- Inventory report visibility preference management through the existing service-backed path.
- Dashboard-only Quick Launch preserved.
- `/me exports` preserved as page navigation without Quick Launch.
- Focused renderer, service, view, preference, and command tests.
- Deferred Phase 6 capture for guided management flows, subpage cards, and stale-card refresh.

No new preference categories were added without a reliable persistence contract. Legacy commands
remain live.

### Phase 6 — Guided Management Cards and Workflow Simplification

Status: delivered in mirror PR #168 and smoke tested successfully on 2026-06-24.

Converted the remaining `/me` pages into a coherent card-based management journey.

Delivered scope:

- generated visual cards for `/me accounts`, `/me reminders`, `/me preferences`, and `/me exports`
  with safe embed fallback
- one primary Account `Manage` flow for Governor ID lookup, register, replace, and remove
- selected Governor ID lookup results carried into register/replace slot selection
- earlier duplicate/invalid Governor ID feedback during account registration and replacement
- one primary Reminder `Manage` flow for KVK event reminder autosave and remove-all/unsubscribe
- automatic save/update behavior for reminder event types and reminder times
- refreshed visible cards after account, reminder, and preference mutations
- generated Preferences card with inventory visibility toggle and Governor VIP update access
- generated Exports card preserving private export guidance without dashboard Quick Launch
- graceful timeout handling for main cards and reminder child selector windows
- focused card-rendering, interaction, service, and regression tests

Phase 6 preserved Phase 3 account safety checks, Phase 4 KVK reminder semantics, Phase 5
dashboard behavior, dashboard Quick Launch boundaries, and all legacy command compatibility.

Phase 6 follow-ups:

- Calendar reminders remain managed through `/calendar_reminder_config` and should be integrated
  into a later unified `/me reminders` phase because players experience KVK event reminders and
  calendar reminders as one reminder domain.
- The Phase 5 dashboard card now looks visually out of step with the Phase 6 Accounts, Reminders,
  Preferences, and Exports cards. The dashboard should be refreshed to the same full-bleed visual
  style while preserving dashboard-only Quick Launch and existing summary data.

### Phase 7 — Unified Reminder Centre and Dashboard Card Alignment

Status: delivered in production PR #477 and smoke tested successfully on 2026-06-25.

Delivered scope:

- audited KVK event reminder state and calendar reminder preference/state code together
- added one `/me reminders` status model for KVK-only, calendar-only, both, and neither states
- surfaced calendar reminder status on `/me reminders`
- added calendar reminder management through the same `/me reminders` Manage journey while
  preserving the event-calendar preference store, scheduler semantics, lead-time semantics, and
  legacy `/calendar_reminder_config` compatibility
- preserved Phase 4/6 KVK reminder event semantics, autosave behavior, remove-all confirmation,
  and legacy `/subscribe`, `/modify_subscription`, and `/unsubscribe` compatibility
- refreshed `/me dashboard` to the full-bleed Phase 6 card style, then refined row layout and text
  sizing after smoke feedback
- kept card text directly on the card background with no black boxes or text panels
- preserved dashboard-only Quick Launch and `/me exports` no-Quick-Launch behavior
- kept command code thin and persistence writes in service-backed paths
- added focused service, renderer, view, calendar reminder config, command-registration, and full
  pytest validation

Phase 7 follow-ups:

- Export launchpad and Quick Launch expansion are intentionally deferred to Phase 8.
- Broader preferences hub expansion remains Phase 9.
- Legacy redirects/removal remain Phase 10 and require separate operator approval.
- Shared visual-card renderer helper consolidation remains a deferred optimisation item.

### Phase 8 — Exports Launchpad and Quick Launch Expansion

Extend the delivered `/me exports` launchpad without redesigning all export logic.

Likely deliverables:

- `/me exports`
- stats export route
- inventory export route
- personal output guidance
- format explanations
- privacy and file-delivery warnings
- an explicit Quick Launch plan for KVK stats, targets, history, rankings, inventory, and exports
  after the guided management pages are stable

Phase 2 delivered first-pass export guidance, Phase 6 added a generated export card, and Phase 7
confirmed the dashboard/reminder card model and dashboard-only Quick Launch boundary. Phase 8
should only add direct export or launch actions if existing service-backed authorization, private
file delivery, channel/visibility rules, and Discord interaction safety are preserved.

### Phase 9 — Preferences Hub Expansion

Expand `/me preferences` only after the persistence and product model are clear.

Likely deliverables:

- preference inventory across inventory, stats, exports, account behavior, local time, and
  notification-like settings
- SQL/JSON persistence validation for each candidate preference
- service-backed mutations only where privacy, restart safety, and legacy compatibility are
  preserved
- player-facing copy that avoids "coming soon" controls
- tests for every new preference write path

Phase 9 should not add preferences that cannot be saved safely.

### Phase 10 — Legacy Redirects, Briefing, and Cleanup

After the new `/me` journeys are validated and player communication is complete, redirect or remove legacy paths only with operator approval.

Likely legacy paths:

```text
/register_governor
/modify_registration
/my_registrations
/mygovernorid
/subscribe
/modify_subscription
/unsubscribe
/inventory_preferences
/my_stats_export
/export_inventory
```

Final removal should remain a separate cleanup step after a no-feedback window.

## 11. In Scope for the Programme

- New `/me` command group.
- New visual `/me dashboard` card.
- New account centre replacing separate registration/review/modify/lookup journeys.
- New reminder centre replacing separate subscribe/modify/unsubscribe journeys.
- Card-based subpages and guided Manage flows for accounts, reminders, preferences, and exports.
- Launch links/buttons/selects into the modern `/kvk` commands.
- First-pass preferences hub for inventory visibility, followed by later approved preference
  expansion where persistence exists.
- First-pass export launchpad and later direct export/Quick Launch improvements.
- Shared visual-card renderer/helper consolidation for the `/me` visual-card model and adjacent
  KVK, PreKvK, and inventory renderers after the player self-service card surfaces are stable.
- Refresh behavior that prevents visible dashboard/subpage cards from showing stale state after
  account, reminder, or preference mutations.
- Legacy redirects and player briefing after validation.
- Command inventory, canonical command reference, docs, smoke tests, usage tracking updates.
- Architecture review of commands, views, services, repositories/DAL, caches, and persisted state.

## 12. Out of Scope for the First Build

- Full redesign of `/my_stats`.
- Full redesign of inventory cards.
- Full public calendar redesign.
- Ark/MGE/admin workflows.
- SQL schema changes unless Phase 1 proves they are required and separately approves them.
- Removing legacy commands without rollout approval.
- Building a website or web dashboard.
- Rewriting the KVK command outputs.
- Adding complex recommendation/prediction logic.

## 13. Likely Source Commands and Areas

### Player-facing commands to audit

```text
/register_governor
/modify_registration
/my_registrations
/mygovernorid
/subscribe
/modify_subscription
/unsubscribe
/my_stats
/my_stats_export
/myinventory
/inventory_preferences
/export_inventory
/mykvkcrystaltech
/player_profile
/calendar_reminder_config
```

### Related modern commands to link

```text
/kvk stats
/kvk targets
/kvk history
/kvk rankings
```

### Likely modules to audit

```text
commands/registry_cmds.py
commands/subscriptions_cmds.py
commands/telemetry_cmds.py
commands/stats_cmds.py
commands/inventory_cmds.py
commands/calendar_cmds.py
commands/events_cmds.py
commands/kvk_cmds.py
services/governor_account_service.py
registry/registry_service.py
registry/account_slots.py
target_utils.py
subscription_tracker.py
event_scheduler.py
reminder_task_registry.py
dm_tracker_utils.py
inventory/
ui/views/registry_views.py
ui/views/subscription_views.py
ui/views/inventory_report_views.py
ui/views/kvk_personal_views.py
scripts/validate_command_registration.py
docs/reference/canonical_command_reference.md
docs/reference/deferred_optimisations.md
```

### SQL repo areas to validate if needed

```text
C:\K98-bot-SQL-Server
```

Likely SQL-backed areas:

- registry tables/procedures
- player/latest stats views used by account validation
- active player views used by audits
- usage tracking tables if command usage review is SQL-backed
- any subscription persistence if migrated from JSON in a later phase

## 14. Cross-Programme Constraints

- Do not make the dashboard busy.
- Do not turn `/me dashboard` into every command bolted onto one message.
- Do not remove old commands until explicitly approved.
- Do not break the new `/kvk` command suite.
- Do not redesign `/my_stats` or inventory cards in the first build.
- Do not move admin/operator workflows into `/me`.
- Do not put SQL in command or view modules.
- Do not add `/me` without command registration governance approval because it is a new top-level command group.
- Preserve `@versioned()`, `@safe_command`, `@track_usage()`, permission decorators, response visibility, autocomplete/options, usage-log identity, and command-cache behaviour.
- Preserve privacy expectations: account management and reminder preferences should default to private/ephemeral interaction.
- Ensure any public quick-launch output follows the target command's existing visibility/channel rules.
- Capture out-of-scope findings as structured deferred optimisations.

## 15. Programme-Level Validation Strategy

Each implementation phase should consider:

- command registration validation
- command inventory tests
- focused command tests
- interaction/view tests
- permission and response-visibility tests
- service/DAL contract tests where touched
- JSON/persistence tests where subscriptions or trackers are touched
- SQL validation where SQL-backed contracts are changed or depended on
- architecture boundary validation
- deferred item validation
- visual artifact review for card phases
- manual Discord smoke testing for interactive flows
- Codex Security review where permissions, user input, persistence, or SQL/data access are touched

Baseline commands to consider:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

## 16. Programme Acceptance Criteria

The programme is complete when:

- players have a clear `/me` command group for personal self-service
- `/me dashboard` is the obvious player home screen
- account lookup, registration, review, modification, and removal are consolidated into a coherent account centre
- reminder subscription, modification, and unsubscribe are consolidated into a coherent reminder centre
- accounts, reminders, preferences, and exports use a coherent card-based visual model
- preferences and exports have a first-pass guided home plus approved service-backed mutations
- players can launch the modern `/kvk` outputs from the personal command centre without command confusion
- the visual output quality matches the new KVK suite without becoming cluttered
- legacy commands are safely redirected or retired through an approved rollout
- command registration validation remains green
- privacy, permission, and channel constraints are preserved
- documentation and player briefing are updated
- no new direct SQL exists in command/view layers
- new deferred findings are captured structurally

## 17. Deferred / Future Opportunities

Do not include these in the first build unless separately approved:

- full `/my_stats` visual redesign
- full inventory visual redesign
- public calendar/KVK calendar redesign outside the player reminder-centre integration
- Ark/MGE self-service redesign
- full website implementation
- live web dashboard
- personalised recommendations
- predictive setup or performance guidance
- cross-feature notification inbox
- player achievement/badges profile
- account ownership dispute tooling
- shared visual-card renderer/helper consolidation across KVK, PreKvK, inventory, and player
  self-service renderers
- Quick Launch expansion beyond dashboard-only guidance; keep it in this programme but require a
  fresh audit of target command channel, visibility, permission, and privacy rules.
- Legacy export command redirect or removal for `/my_stats_export` and `/export_inventory`; keep it
  in this programme and require operator approval plus a no-feedback window.
- Export schema and format redesign; treat this as a separate export-output programme unless a
  later task explicitly narrows one compatible file-format improvement into this programme.

## 18. Suggested Next Action

Start Phase 8:

```text
Codex Task Pack - Player Self-Service Command Centre Phase 8 Exports Launchpad and Quick Launch Expansion.md
```

Phase 8 should turn `/me exports` from passive guidance into a safer, clearer launchpad where the
existing export authorization and private file-delivery paths support it. It should also decide how
Quick Launch should evolve after Phase 7 confirmed the dashboard-only boundary: preserve the
dashboard-only model unless the audit proves an expanded launch surface can respect every target
command's visibility, channel, permission, and privacy rules.
