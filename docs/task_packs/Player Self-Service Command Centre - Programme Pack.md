# Player Self-Service Command Centre — Programme Pack

## 1. Programme Header

- Programme name: `Player Self-Service Command Centre`
- Date: `2026-06-22`
- Owner/context: K98 Bot player self-service redesign following completion of the KVK Player Experience Redesign programme
- Programme type: Product UX / Discord command architecture / visual output redesign / player workflow consolidation / deferred optimisation programme
- One-pass approved: No
- Headline: **Every player now has a personal command centre.**

## Current Programme Status

Status as of 2026-06-22:

- Phase 1 audit and design is complete and archived as a historical execution record.
- Phase 2 `/me` command shell and navigation foundation is delivered in mirror PR #164 and
  production PR #472, smoke tested successfully, and awaiting manual merge/promotion.
- The delivered `/me` surface is intentionally read-only: dashboard, accounts, reminders,
  preferences, exports, navigation buttons, dashboard Quick Launch guidance, and legacy command
  preservation are in place.
- Next active implementation phase: Phase 3 Modern Account Centre.

Phase 2 manual smoke evidence:

- `/me dashboard` responds privately and shows the expected dashboard sections and controls.
- Quick Launch works and shows guidance for KVK stats, KVK targets, KVK history, KVK rankings,
  inventory, and exports.
- `/me exports` opens the exports page with page navigation only; the dashboard Quick Launch menu
  remains dashboard-only by design.
- Existing legacy commands still work.

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

Status: delivered, smoke tested, and awaiting manual merge/promotion.

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

Status: next active phase.

Replace fragmented account behaviours with one account centre journey.

Target consolidation:

```text
/register_governor
/modify_registration
/my_registrations
/mygovernorid
```

Likely deliverables:

- account summary view
- register / modify / remove flows
- Governor ID lookup integrated into account flow
- duplicate ownership handling
- slot management
- main/default account behaviour proposal or implementation if approved
- admin support implications documented

Phase 3 should build on the delivered `/me accounts` read-only shell rather than replacing it.
Legacy account commands must remain live until redirects are separately approved.

### Phase 4 — Modern Reminder Centre

Replace fragmented reminder behaviours with one reminder centre journey.

Target consolidation:

```text
/subscribe
/modify_subscription
/unsubscribe
```

Likely deliverables:

- current subscription summary
- event type selector
- reminder time selector
- unsubscribe flow
- DM availability/troubleshooting guidance
- sent/scheduled reminder status where safe
- duplicate reminder and restart-safety considerations

### Phase 5 — Visual `/me dashboard` Card and First-Pass Preferences

Build the premium dashboard card and extend the lightweight preferences hub once the data contract
and navigation have been proven.

Likely deliverables:

- Pillow-generated `/me dashboard` card
- identity header
- account setup status
- reminder setup status
- preference status chips
- quick launch controls
- inventory visibility preference management if approved
- output privacy preference proposal or implementation if supported

Phase 2 already surfaces inventory visibility status in `/me preferences`. Phase 5 should avoid
repeating that work and focus on generated-card quality plus any approved preference mutation.

### Phase 6 — Exports Launchpad and Player Output Links

Extend the delivered `/me exports` launchpad without redesigning all export logic.

Likely deliverables:

- `/me exports`
- stats export route
- inventory export route
- personal output guidance
- format explanations
- privacy and file-delivery warnings

Phase 2 already delivered first-pass export guidance. Phase 6 should only add direct export
actions if existing service-backed authorization, private file delivery, and Discord interaction
safety are preserved.

### Phase 7 — Legacy Redirects, Briefing, and Cleanup

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
```

Final removal should remain a separate cleanup step after a no-feedback window.

## 11. In Scope for the Programme

- New `/me` command group.
- New visual `/me dashboard` card.
- New account centre replacing separate registration/review/modify/lookup journeys.
- New reminder centre replacing separate subscribe/modify/unsubscribe journeys.
- Launch links/buttons/selects into the modern `/kvk` commands.
- First-pass preferences hub for inventory visibility and personal output defaults.
- First-pass export launchpad.
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
- preferences and exports have a first-pass guided home
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
- public calendar/KVK calendar redesign
- Ark/MGE self-service redesign
- full website implementation
- live web dashboard
- personalised recommendations
- predictive setup or performance guidance
- cross-feature notification inbox
- player achievement/badges profile
- account ownership dispute tooling

## 18. Suggested Next Action

Start Phase 3:

```text
Codex Task Pack - Player Self-Service Command Centre Phase 3 Modern Account Centre.md
```

Phase 3 should turn the delivered read-only `/me accounts` shell into a service-backed account
centre for lookup, registration, modification, removal, and account review while preserving all
legacy account commands until redirects are separately approved.
