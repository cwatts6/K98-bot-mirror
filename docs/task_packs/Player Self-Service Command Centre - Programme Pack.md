# Player Self-Service Command Centre — Programme Pack

## 1. Programme Header

- Programme name: `Player Self-Service Command Centre`
- Date: `2026-06-22`
- Owner/context: K98 Bot player self-service redesign following completion of the KVK Player Experience Redesign programme
- Programme type: Product UX / Discord command architecture / visual output redesign / player workflow consolidation / deferred optimisation programme
- One-pass approved: No
- Headline: **Every player now has a personal command centre.**

## Current Programme Status

Status as of 2026-06-26:

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
- Phase 8 Exports Launchpad is delivered in production PR #478 and smoke tested successfully by
  the operator on 2026-06-25.
- Phase 9 Quick Launch and Export Options is delivered in production PR #479 and smoke tested
  successfully by the operator on 2026-06-25.
- Phase 10 Inventory Summary Card is delivered in production PR #480 and smoke tested
  successfully by the operator on 2026-06-26. It adds `/me inventory` as the sixth private `/me`
  subcommand and keeps the existing `/myinventory` report journey intact.
- The delivered `/me` surface now includes a private command-centre shell, a generated dashboard
  card with safe embed fallback, generated cards for Accounts, Reminders, Preferences, and
  Inventory, and Exports, account-centre lookup/register/replace/remove management, unified KVK/calendar
  reminder status and management, KVK reminder autosave and remove-all management, calendar
  reminder autosave/remove-all management, inventory visibility and Governor VIP controls,
  dashboard Inventory/Exports handoffs, private Inventory summary data, option-window based
  private stats and inventory exports, graceful timeout handling, and return navigation. Legacy
  account, reminder, inventory, calendar reminder, and export commands remain live.
- Next active scope: Phase 11 Shared Visual-Card Renderer Consolidation, promoted from the active
  deferred renderer item now that all `/me` page-level card surfaces are stable.

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
/me inventory
/me exports
```

### Command purpose

| Command | Purpose |
|---|---|
| `/me dashboard` | The premium personal home screen: setup status, key identity information, reminder status, and safe personal handoff controls. |
| `/me accounts` | Modern account centre replacing separate lookup/register/review/modify habits. |
| `/me reminders` | Modern reminder centre replacing separate subscribe/modify/unsubscribe habits. |
| `/me preferences` | First-pass personal settings hub, including inventory visibility and output privacy defaults. |
| `/me inventory` | Private Inventory summary card for latest approved resources, speedups, and materials, with report handoff. |
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
3. **Preferences / Personal Actions**

It should show status, not every possible action.

Example dashboard controls:

```text
[Accounts] [Reminders] [Preferences]
Actions: compact buttons for Inventory / Exports
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
- clear buttons for inventory and exports, while KVK outputs remain in their existing command
  channels

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

A player runs `/me dashboard`, then chooses Inventory or Exports.

The bot should route them to the private personal journeys where safe:

- `/myinventory`
- export options

Success means `/me` does not duplicate every feature or bypass KVK channel/public-output rules.
It becomes the home for private personal setup, inventory, and exports.

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
- personal action area
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

- Export launchpad was delivered in Phase 8.
- Quick Launch expansion moved to Phase 9 after Phase 8 validated `/me exports`.
- Broader preferences hub expansion remains a later phase after launch/legacy decisions.
- Legacy redirects/removal remain later work and require separate operator approval; export-specific
  legacy decisions start in Phase 9.
- Shared visual-card renderer helper consolidation remains a deferred optimisation item.

### Phase 8 — Exports Launchpad and Quick Launch Expansion

Status: delivered in production PR #478 and smoke tested successfully on 2026-06-25.

Delivered scope:

- audited `/my_stats_export`, `/export_inventory`, and their reusable service-backed export paths
- added `/me exports` direct private actions for default Stats Excel, Stats CSV, Inventory Excel,
  and Inventory CSV
- reused existing stats and inventory export services, authorization, cleanup, telemetry, and
  private Discord file delivery
- represented no-account, unavailable, guidance-only, and actionable export states without
  misleading users
- kept export persistence, SQL, and file generation out of commands and views
- refreshed the `/me exports` generated card and fallback embed to the Phase 7 concise card style
- preserved `/my_stats_export`, `/export_inventory`, and all legacy self-service commands
- preserved dashboard-only Quick Launch; `/me exports` does not include the dashboard Quick Launch
  menu
- captured Quick Launch expansion, legacy export redirect/removal, shared renderer consolidation,
  preferences expansion, and export schema/format redesign as separate follow-up decisions

Phase 8 manual smoke evidence:

- Stats Excel, Stats CSV, Inventory Excel, and Inventory CSV all work from `/me exports`.
- All `/me exports` outputs are ephemeral/private.
- The `/me exports` generated card is concise: private pill, action headline, Stats row, and
  Inventory row.
- `/me dashboard` does not have a direct export button.
- Dashboard Quick Launch `Exports` opens the `/me exports` card correctly.
- `/my_stats_export` and `/export_inventory` still work.

Phase 8 follow-ups:

- Phase 9 resolved the Quick Launch question by removing KVK command targets from the dashboard
  launch surface and keeping only safe private Inventory and Exports handoffs.
- Legacy export redirect/removal remains inside this programme and should be evaluated after
  Phase 9 smoke and player communication planning.
- Shared visual-card renderer consolidation remains inside this programme, but should follow a
  dedicated helper-consolidation task rather than being mixed into launch/redirect behavior.
- Export schema and format redesign is not a Player Self-Service phase by default; it should be a
  separate export-output programme unless a later approved slice is intentionally narrow and
  backwards-compatible.

### Phase 9 — Quick Launch Expansion and Legacy Export Rollout

Status: delivered in production PR #479 and smoke tested successfully on 2026-06-25.

Phase 9 decided that Dashboard Quick Launch should not direct-launch `/kvk stats`, `/kvk targets`,
`/kvk history`, or `/kvk rankings` because those commands have channel-gated and sometimes public
output behavior that is safer and clearer in their existing command paths. Players already know
where to use those KVK outputs, so the extra dashboard step does not improve the journey.

Phase 9 also decided that `/me exports` should become the preferred export route before any legacy
export redirect/removal is attempted. `/my_stats_export` and `/export_inventory` remain live for
compatibility until a later operator-approved communication and no-feedback window.

Delivered scope:

- remove KVK command targets from dashboard Quick Launch instead of adding risky direct launch
  controls
- add dashboard `Inventory` and `Exports` buttons that stay inside private `/me`/inventory
  journeys
- route dashboard Inventory into the existing `/myinventory` selector/report journey, including
  the player's current inventory visibility preference
- update `/me exports` to show two primary controls: `Export Stats` and `Export Inventory`
- add a Stats export option window with Format and Days selectors plus Download/Cancel controls
- add an Inventory export option window with Format, View, Governor, and Days selectors plus
  Download/Cancel controls
- keep export generation, authorization, cleanup, and file delivery inside the existing stats and
  inventory export services
- preserve `/my_stats_export` and `/export_inventory` unchanged for compatibility
- update command reference, briefing, deferred backlog, and focused tests

Do not combine this with export schema/format redesign or broad renderer helper consolidation.

Phase 9 manual smoke evidence:

- `/me dashboard` remains private and shows Inventory and Exports controls, not the old KVK Quick
  Launch menu.
- Dashboard Inventory opens the existing `/myinventory` selection/report flow, produces cards as
  expected, and respects the player's inventory visibility preference.
- Dashboard Exports opens `/me exports`.
- `/me exports` opens private Stats and Inventory option windows.
- Stats export defaults to Excel and 90 days; Inventory export defaults to existing inventory
  export defaults.
- Download sends the selected file privately; Cancel closes the child window without a file.
- Main `/me` pages share consistent navigation rows, current-page disabled states, green action
  buttons, and graceful timeout behavior.
- `/my_stats_export` and `/export_inventory` remain registered and usable.
- `/kvk stats`, `/kvk targets`, `/kvk history`, and `/kvk rankings` remain available only through
  their existing command paths and channel rules.

### Phase 10 — Inventory Summary Card and `/me inventory` Alignment

Status: delivered in production PR #480 and smoke tested successfully on 2026-06-26.

Make Inventory feel like a first-class `/me` destination instead of only a direct handoff into the
legacy `/myinventory` report/export journey. Phase 9 proved the private dashboard Inventory
handoff works, but smoke feedback showed it is visually out of step with Accounts, Reminders,
Preferences, and Exports because there is no matching Inventory summary card.

Delivered scope:

- audited current inventory data sources, report services, export services, approval rules, and
  `/myinventory` defaults before designing summary output
- added `/me inventory` as a sixth private `/me` subcommand
- added an Inventory summary card using `assets/me/cards/me inventory.png` and the established
  generated-card plus safe embed fallback pattern
- summarized latest approved inventory data across three player-readable rows:
  - resources and value
  - speedups and value
  - materials and value
- handled one-account, multi-account, no-account, and no-approved-inventory-data states without
  leaking another player's data
- pointed players with no inventory data toward the inventory upload channel/process instead of
  showing an empty or misleading card
- kept the existing `/myinventory` report journey, timescale controls, report visibility behavior,
  and export buttons unchanged
- kept inventory service/DAL logic Discord-type-free and kept views as interaction adapters
- updated command reference, briefing, tests, and deferred backlog

This phase should not redesign inventory import OCR/review, inventory report schema, export file
formats, or the broader shared renderer helper layer.

Phase 10 manual smoke evidence:

- `/me inventory` remained private and rendered the generated Inventory card.
- `/me dashboard` Inventory opened the private `/me inventory` summary card.
- The Inventory card used `assets/me/cards/me inventory.png` and showed latest approved resources,
  speedups, and materials.
- No-approved-data and partial-data states remained private and used conservative coverage copy.
- `Open Report` preserved the existing `/myinventory` selector/report journey, range controls,
  report visibility behavior, and export buttons.
- `/myinventory`, `/export_inventory`, `/me exports`, and other legacy self-service commands
  remained live and behavior-compatible.
- A final card-layout polish moved the Inventory action block clear of the Materials row after
  smoke feedback showed overlap on the partial-data card.

### Phase 11 — Shared Visual-Card Renderer Consolidation

Status: implementation started.

Consolidate stable visual-card primitives after the `/me` Inventory card fills the last obvious
page-level visual gap and launch/legacy decisions are not competing for product attention.

Likely deliverables:

- audit shared rendering patterns across `player_self_service`, KVK, PreKvK, and inventory
  renderers
- extract only stable primitives such as text fitting, badges, PNG wrappers, glyph-safe font
  selection, and common fallback handling
- migrate one renderer family at a time, with Phase 11 not considered complete until `/me`/PreKvK,
  KVK, and inventory renderer families are migrated where practical
- preserve existing card filenames, dimensions, output bytes contracts, fallback behavior, and
  player-name Unicode handling
- add focused renderer tests and at least one visual/PNG smoke artifact for changed renderers

Approved implementation slicing:

- Phase 11A extracts shared glyph-safe text primitives into `core.visual_text` and migrates `/me`
  page cards plus PreKvK compatibility wrappers away from the accidental PreKvK-as-shared-helper
  dependency.
- Phase 11B must migrate the KVK renderer family (`kvk/rendering/`) to the shared helper while
  preserving KVK stats, targets, rankings, and history output contracts.
- Phase 11C must migrate `inventory/report_image_renderer.py` text primitives to the shared helper
  while preserving report layout, filenames, dimensions, and existing report/export behavior.

### Phase 12 — Preferences Hub Expansion

Expand `/me preferences` only after the persistence and product model are clear.

Likely deliverables:

- preference inventory across inventory, stats, exports, account behavior, local time, and
  notification-like settings
- SQL/JSON persistence validation for each candidate preference
- service-backed mutations only where privacy, restart safety, and legacy compatibility are
  preserved
- player-facing copy that avoids "coming soon" controls
- tests for every new preference write path

This phase should not add preferences that cannot be saved safely.

### Phase 13 — Legacy Redirects, Briefing, and Cleanup

After the new `/me` journeys are validated and player communication is complete, redirect or remove
remaining legacy paths only with operator approval. Phase 9 keeps export legacy commands live, so
any export-specific redirect/removal still needs a later communication/no-feedback rollout.

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
- Card-based subpages and guided Manage flows for accounts, reminders, preferences, inventory, and
  exports.
- Safe private launch buttons for inventory and exports while modern KVK outputs remain in their
  existing command paths.
- First-pass preferences hub for inventory visibility, followed by later approved preference
  expansion where persistence exists.
- Delivered export launchpad, Phase 9 dashboard Inventory/Exports handoffs, and preferred
  `/me exports` option windows.
- Delivered Inventory summary card and `/me inventory` alignment using the prepared
  `assets/me/cards/me inventory.png` card background, latest approved inventory data, and the
  existing `/myinventory` report/export journey.
- Shared visual-card renderer/helper consolidation for the `/me` visual-card model and adjacent
  KVK, PreKvK, and inventory renderers after the player self-service card surfaces are stable.
- Refresh behavior that prevents visible dashboard/subpage cards from showing stale state after
  account, reminder, or preference mutations.
- Legacy redirects and player briefing after validation.
- Command inventory, canonical command reference, docs, smoke tests, usage tracking updates.
- Architecture review of commands, views, services, repositories/DAL, caches, and persisted state.

## 12. Out of Scope for the First Build

- Full redesign of `/my_stats`.
- Full redesign of legacy inventory report cards, inventory import OCR/review, or inventory export
  outputs beyond the approved `/me` Inventory summary card.
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
- Do not launch public KVK outputs from `/me`; keep public/channel-gated KVK journeys in their
  existing command paths.
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
- full legacy inventory report visual redesign beyond the `/me` Inventory summary card
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
- Legacy export command redirect or removal for `/my_stats_export` and `/export_inventory`; this is
  remains after Phase 9 and still requires operator approval plus player communication before any
  redirect or removal.
- Export schema and format redesign; treat this as a separate export-output programme unless a
  later task explicitly narrows one compatible file-format improvement into this programme.

## 18. Suggested Next Action

Start Phase 11:

```text
Shared Visual-Card Renderer Consolidation
```

Use the prepared Phase 11 task pack to audit and consolidate stable card-rendering primitives
across the `/me` visual-card model and adjacent KVK, PreKvK, and inventory renderers. Keep the
first pass audit/scope-led and migrate one renderer at a time. Preferences expansion and legacy
export redirect/removal remain later programme phases, and export schema/format redesign remains a
separate export-output programme unless explicitly narrowed later. Do not redirect or remove
`/my_stats_export` or `/export_inventory` without explicit operator approval, player
communication, and a no-feedback monitoring window.
