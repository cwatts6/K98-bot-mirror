# Player Self-Service Command Centre - Phase 1 Audit and Design Report

Status: completed Phase 1 report. The active programme pack now tracks delivered Phase 2 status
and Phase 3 next work; this report remains the historical audit/design source.

## 1. Executive Summary

Phase 1 recommends introducing a new player-owned `/me` command group as the personal
self-service home for account identity, reminder setup, preferences, exports, and quick links to
existing player outputs.

Recommended model:

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me exports
```

The design should ship in parallel with the current flat commands. No legacy command should be
removed in the first implementation phase. The first implementation should create the shell,
navigation, status summaries, safe service/view boundaries, and a polished private dashboard embed
MVP that feels like the first version of a real product rather than a plain command index. Account
mutation, reminder mutation, the generated PNG dashboard card, exports polish, and legacy redirects
should remain separate phases.

Why `/me` is worth a new top-level group: no existing group can own this surface without making the
product model confusing. `/registry`, `/subscriptions`, `/inventory`, `/stats`, and `/kvk` are
domain groups. `/me` is a player portal that coordinates across domains.

Command governance impact: adding `/me` changes the top-level command count from 40 to 41 and adds
5 grouped subcommands. This requires operator approval, an
`APPROVED_TOP_LEVEL_COMMANDS` update, this command reference update, smoke references, and command
registration validation before implementation.

No runtime code or SQL changes were made during this audit.

## 2. Current Command Surface Map

| Current command | Owner | Current role | Visibility and permissions | Recommended disposition |
| --- | --- | --- | --- | --- |
| `/register_governor` | `commands/registry_cmds.py` | Register one account slot by Governor ID | Public command-level access, ephemeral | Keep live; surface through `/me accounts`; later redirect only after validation |
| `/modify_registration` | `commands/registry_cmds.py` | Modify or remove one account slot | Public command-level access, ephemeral | Keep live; fold into `/me accounts`; later redirect |
| `/my_registrations` | `commands/registry_cmds.py` | Account review plus action buttons | Public command-level access, ephemeral | Main seed for `/me accounts`; keep live during rollout |
| `/mygovernorid` | `commands/telemetry_cmds.py` | Governor ID lookup by name | Public command-level access, ephemeral | Integrate into `/me accounts`; keep live initially |
| `/subscribe` | `commands/subscriptions_cmds.py` | Start KVK event DM reminders | Public command-level access, ephemeral | Replace with `/me reminders` journey after Phase 2 |
| `/modify_subscription` | `commands/subscriptions_cmds.py` | Change reminder types/times or unsubscribe | Public command-level access, ephemeral | Replace with `/me reminders`; keep live initially |
| `/unsubscribe` | `commands/subscriptions_cmds.py` | Remove KVK event reminder config | Public command-level access, ephemeral | Replace with `/me reminders`; keep live initially |
| `/calendar_reminder_config` | `commands/calendar_cmds.py` | Calendar reminder preference panel | Public command-level access, ephemeral | Audit as related reminder preference surface; do not fold into Phase 2 mutation |
| `/inventory_preferences` | `commands/inventory_cmds.py` | Set inventory report visibility | Public command-level access, ephemeral | Surface in `/me preferences`; keep command initially |
| `/myinventory` | `commands/inventory_cmds.py` | Latest personal inventory report | Public command-level access, private prompt, report visibility follows preference | Link from dashboard and `/me exports`; no redesign in first build |
| `/export_inventory` | `commands/inventory_cmds.py` | Export approved inventory records | Service authorization with admin override context, ephemeral | Link from `/me exports`; do not rewrite export logic |
| `/my_stats` | `commands/stats_cmds.py` | Legacy personal stats report | KVK stats channel, user-selectable output controls | Link only; no redesign in first build |
| `/my_stats_export` | `commands/stats_cmds.py` | Personal stats export | Public command-level access, ephemeral file | Link from `/me exports`; service/DAL already exists |
| `/mykvkcrystaltech` | `commands/telemetry_cmds.py` | Personal CrystalTech output | CrystalTech channel with admin override; defaults private | Quick link, not redesigned |
| `/player_profile` | `commands/telemetry_cmds.py` | Leadership player profile lookup | Admin/leadership in allowed channels, ephemeral | Not player self-service; keep outside `/me` |
| `/kvk stats` | `commands/kvk_cmds.py` | Modern KVK stats | KVK stats channel with admin override | Quick launch only |
| `/kvk targets` | `commands/kvk_cmds.py` | Modern KVK targets | KVK target channel with admin override | Quick launch only |
| `/kvk history` | `commands/kvk_cmds.py` | Modern KVK history | KVK stats channel with admin override | Quick launch only |
| `/kvk rankings` | `commands/kvk_cmds.py` | Modern KVK rankings | KVK stats channel with admin override | Quick launch only |

The command registration validator currently reports:

```text
primary=40 grouped_subcommands_detected=80 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=40
```

## 3. Current User Journey Audit

### New Player Setup

Current flow requires the player to discover at least two commands: `/mygovernorid` to find an ID
and `/register_governor` to register it. If they later need to review or correct the setup, they
must remember `/my_registrations` and `/modify_registration`.

Problem: the journey is functionally complete but command-name heavy.

Target: `/me dashboard` shows "no accounts", then `/me accounts` offers "Find Governor ID" and
"Register account" without requiring prior command knowledge.

### Existing Player Review

Current flow is split between `/my_registrations`, `/modify_registration`, `/myinventory`,
`/my_stats`, KVK commands, and subscriptions.

Problem: the player can inspect pieces, but there is no single status page that answers whether
their account, reminders, and preferences are ready.

Target: `/me dashboard` shows account count, main account status, reminder status, inventory
visibility status, and quick launch options.

### Account Change

Current flow is strong at the persistence layer. Registry writes go through service/DAL and SQL
stored procedure contracts. The command and registry views still own journey branching, duplicate
pre-checks, and some validation.

Target: account-change orchestration should move behind a player self-service account service.
Views should route interactions and render confirmations only.

### Reminder Change

Current KVK reminder flow is concentrated in `commands/subscriptions_cmds.py` and
`ui/views/subscription_views.py`. It uses JSON-backed subscription state, scheduler tasks, scheduled
DM tracker state, sent DM tracker state, and DM failure handling.

Problem: the command body owns much of the normalization, confirmation, DM messaging, unsubscribe
cleanup, and tracker coordination. This is too much to copy into `/me reminders`.

Target: `/me reminders` should be implemented with a thin command, a reminder-centre service, and
interaction views that call service operations.

### Preferences And Exports

Inventory report visibility is already modeled as a persisted SQL preference. Personal stats and
inventory exports already use service/DAL boundaries. These should be linked and guided rather
than rewritten early.

Target: `/me preferences` starts with existing inventory visibility. `/me exports` starts as a
guided launchpad for existing export flows.

## 4. Current Architecture and Persistence Map

### Account/Registry

- Commands: `commands/registry_cmds.py`, `commands/telemetry_cmds.py`
- Views/modals: `ui/views/registry_views.py`
- Account summary service: `services/governor_account_service.py`
- Registry service: `registry/registry_service.py`
- Registry DAL: `registry/dal/registry_dal.py`
- Compatibility facade: `registry/governor_registry.py`
- Lookup helper: `target_utils.py`
- SQL objects validated: `dbo.DiscordGovernorRegistry`,
  `dbo.sp_Registry_Insert`, `dbo.sp_Registry_SoftDelete`,
  `dbo.sp_Registry_GetByDiscordID`, `dbo.sp_Registry_GetByGovernorID`,
  `dbo.sp_Registry_GetAllActive`, `dbo.sp_Registry_UpsertFromImport`,
  `dbo.vw_All_Governors_Clean`, and `dbo.v_Active_Players`.

### KVK And Stats Outputs

- Commands: `commands/kvk_cmds.py`, `commands/stats_cmds.py`
- Modern output services/views: KVK service/view modules plus existing stats services
- Personal stats export service: `services/stats_export_service.py`
- Personal stats export DAL: `stats/dal/stats_export_dal.py`
- SQL object validated: `dbo.vDaily_PlayerExport`

### Inventory

- Commands: `commands/inventory_cmds.py`
- Views: `ui/views/inventory_report_views.py`
- Services: `inventory/reporting_service.py`, `inventory/export_service.py`
- DAL: `inventory/dal/inventory_reporting_dal.py`,
  `inventory/dal/inventory_export_dal.py`, `inventory/dal/inventory_profile_dal.py`
- SQL objects validated: `dbo.InventoryReportPreference`,
  `dbo.GovernorInventoryProfile`, `dbo.InventoryImportBatch`,
  `dbo.GovernorResourceInventory`, `dbo.GovernorSpeedupInventory`, and
  `dbo.GovernorMaterialInventory`.

### Reminders

- KVK reminder commands: `commands/subscriptions_cmds.py`
- KVK reminder view: `ui/views/subscription_views.py`
- KVK reminder store: `subscription_tracker.py`
- Scheduler and trackers: `event_scheduler.py`, `dm_tracker_utils.py`,
  `reminder_task_registry.py`
- Calendar reminder command: `commands/calendar_cmds.py`
- Calendar reminder view/store: `ui/views/reminder_config.py`,
  `event_calendar/reminder_prefs_store.py`
- Current persistence: JSON files plus in-memory task registry and scheduler tracker recovery.
  `subscription_tracker.py` uses an atomic temp-file replace; calendar reminder prefs use
  `atomic_write_json`.

### Usage And Command Governance

- Validator: `scripts/validate_command_registration.py`
- Inventory parser: `commands/command_inventory.py`
- SQL usage object validated: `dbo.BotCommandUsage`
- Current command reference: `docs/reference/canonical_command_reference.md`

## 5. Usage and Discoverability Review

Live SQL-backed usage was not queried in this audit. The SQL repo contains `dbo.BotCommandUsage`
with command/user/time indexes, so a later operator review can compare actual usage before legacy
redirect/removal phases.

Even without live counts, the command surface shows obvious discoverability cost:

- Account setup is split across lookup, register, review, modify, and remove paths.
- KVK reminder setup is split across subscribe, modify, and unsubscribe paths.
- Inventory visibility is separate from inventory report and inventory export.
- Modern `/kvk` outputs have a coherent home, but broader personal setup does not.

Phase 2 should include usage tracking for `/me dashboard`, `/me accounts`, `/me reminders`,
`/me preferences`, and `/me exports` so rollout evidence exists before any legacy redirects.

## 6. Pain Points and Opportunity Assessment

Primary pain points:

- Too many player-facing flat commands for one personal setup journey.
- Command names expose implementation history instead of player questions.
- Reminder flows mix command, service, scheduler, tracker, and DM concerns.
- Account views already form a mini account centre, but the entry point is still
  `/my_registrations`.
- Several current prompts point to old names such as `/register_governor`, `/mygovernorid`,
  `/modify_subscription`, or `/unsubscribe`.
- The dashboard concept needs status data from multiple subsystems, so misleading "complete" or
  "healthy" labels are a real risk.

Main opportunity:

- Build `/me` as the stable personal home while leaving domain commands available.
- Reuse proven services and existing views where safe, but do not copy command bodies forward.
- Add a clean place for future personal settings without expanding `/kvk`, `/registry`,
  `/subscriptions`, or `/inventory` beyond their domain meaning.

## 7. Target `/me` Command Model Options

### Option A - New `/me` Group

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me exports
```

Pros:

- Best player mental model.
- Short and memorable.
- Clearly cross-domain.
- Leaves `/kvk` focused on KVK outputs and `/registry`/`/subscriptions` focused on domain/admin
  surfaces.

Cons:

- Adds one top-level command group.
- Requires command-governance approval and documentation updates.

### Option B - Use `/registry` And `/subscriptions`

Pros:

- No new top-level group.
- Keeps account/reminder logic in existing domains.

Cons:

- Does not solve the "one personal home" goal.
- Preferences, exports, inventory, and KVK links do not naturally belong under registry or
  subscriptions.

### Option C - Use `/player`

Pros:

- Also player-oriented.
- Could theoretically include profile outputs later.

Cons:

- `player_profile` is already a leadership/admin concept.
- `/player` sounds like lookup/profile rather than personal self-service.
- Higher risk of mixing admin/leadership and player-owned flows.

## 8. Recommended `/me` Command Model

Use Option A.

Recommended semantics:

- `/me dashboard`: personal setup status and quick launch.
- `/me accounts`: account centre, review/register/modify/remove/find Governor ID.
- `/me reminders`: reminder centre, current setup and update entry points.
- `/me preferences`: personal defaults and privacy, starting with inventory visibility.
- `/me exports`: guided launchpad for stats and inventory exports.

Operator approval is required before adding `/me`.

Implementation naming:

- Command module: `commands/me_cmds.py`
- Service package: `player_self_service/` or `services/player_self_service_service.py`
- Views: `ui/views/player_self_service_views.py`
- Tests: `tests/test_me_cmds.py`, `tests/test_player_self_service_service.py`,
  `tests/test_player_self_service_views.py`

### Phase 2 Product Quality Bar

Phase 2 must be treated as the first player-visible product foundation, not just a command shell.

Even while read-only, `/me dashboard` should feel like a premium private player home:

- status-first, not command-first
- understandable within five seconds
- no wall of text
- no more than three visible dashboard sections
- every section shows current state plus the next useful action
- legacy command names are avoided in primary copy unless needed for transition safety
- controls feel like navigation inside one product, not links to unrelated command fragments
- unknown or failed data sources are shown honestly as `unknown` or `not available`, never guessed
- no dead buttons whose only outcome is "coming soon"

Phase 2 should leave players thinking: "this is where I manage myself", even before account and
reminder mutation are folded into `/me`.

## 9. Dashboard Information Architecture

Dashboard sections should be capped at three:

1. Accounts
2. Reminders
3. Preferences and Quick Links

Suggested status rows:

| Status | Source | Display rule |
| --- | --- | --- |
| Registered accounts | `governor_account_service.get_account_summary_for_user` | Show count and main slot if present |
| Main/default account | Registry `Main` slot | Show "Main set" only if the source is present |
| KVK reminders | `subscription_tracker.get_user_config` | Show subscribed/not subscribed plus concise type/time summary |
| Calendar reminders | `event_calendar.reminder_prefs_store.get_user_prefs` | Show only if included in current phase wording |
| Inventory visibility | `inventory.reporting_service.get_visibility_preference_or_none` | Show private/public/not set |
| Quick launch | Static command links/buttons/select labels | Do not duplicate full output |

Dashboard should not show every account slot, every event type, and every export setting at once.

### Required Phase 2 Dashboard MVP Shape

The Phase 2 dashboard should use a polished embed or embed-plus-view layout with a predictable
status-led structure.

Suggested first release shape:

```text
/me dashboard

Header:
K98 Personal Command Centre
Private setup dashboard for <player>

Accounts:
- Main: set / not set
- Linked: 0 / 1 / multiple
- Next action: Register / Review / Manage

Reminders:
- KVK reminders: on / off / unknown
- Times: concise summary such as 24h, 4h, 1h
- Next action: Set up / Manage

Preferences:
- Inventory visibility: private / public / not set / unknown
- Exports: available through private export tools
- Next action: Review preferences

Controls:
Accounts | Reminders | Preferences
Quick Launch select: KVK stats, KVK targets, KVK history, KVK rankings, Inventory, Exports
```

This MVP should not list every command. It should present player status and the next sensible step
for each area.

## 10. Account Centre Journey Design

`/me accounts` should open a private account centre with:

- account summary by slot
- "Register account"
- "Modify account"
- "Remove account"
- "Find Governor ID"
- "Back to dashboard"

Phase 2 should show summary and useful next-action guidance only. It should not fill the account
centre with dead "coming soon" buttons. Mutation can come in Phase 3.

Phase 3 success gate: do not implement `/me accounts` write actions until account centre service
ownership is complete.

Phase 3 should consolidate:

- `/register_governor`
- `/modify_registration`
- `/my_registrations`
- `/mygovernorid`

Service ownership:

- account centre service loads summaries, free slots, registered slots, Governor ID lookup results,
  duplicate/claim status, and confirmation payloads.
- views own select/menu/modal routing only.
- registry service/DAL continue to own writes and SQL contracts.

## 11. Reminder Centre Journey Design

`/me reminders` should open a private reminder centre with:

- subscribed/not subscribed status
- selected event types
- selected reminder times
- DM warning/help state where safe
- "Subscribe or update"
- "Unsubscribe"
- "Back to dashboard"

Phase 2 should show status and useful next-action guidance only. Avoid placeholder controls that
do nothing except say "coming soon". Phase 4 should extract reminder mutation into a service before
any `/me reminders` write path is added.

Phase 4 success gate: do not implement `/me reminders` write actions until reminder centre service
ownership is complete.

Service ownership:

- reminder centre service reads and normalizes subscription config.
- later mutation service owns validation, type normalization, reminder time normalization, tracker
  cleanup, task cancellation, DM confirmation, and scheduler coordination.
- views own selectors and confirmation routing.

## 12. Preferences and Exports First-Pass Design

`/me preferences` first pass:

- inventory report visibility
- future output privacy defaults only where supported by real storage
- optional preferred account/main-account explanation, but no new storage unless separately
  approved

`/me exports` first pass:

- personal stats export route
- inventory export route
- guidance on file visibility and format
- no rewrite of export generation

Existing services are good enough to launch from:

- `services/stats_export_service.py`
- `inventory/export_service.py`
- `inventory/reporting_service.py`

## 13. Visual Direction and Wireframe Notes

The future visual card should be a generated PNG aligned with the modern KVK suite but visually
quieter because this is setup/status, not competition performance.

Phase 2 should not wait for the generated PNG before creating a premium feel. It should establish a
polished embed MVP first, then the generated card can replace or enhance that stable layout once
account and reminder status contracts have been proven.

Recommended first card:

```text
1180 x 640
Header: player display name, K98 identity, data freshness
Left: account status and main account
Middle: reminder status and next action
Right: preferences and quick launch summary
Footer: private setup note and "Use /me accounts / reminders / preferences"
```

Wireframe:

```text
+----------------------------------------------------------------+
| K98 Personal Command Centre                         Updated ... |
| Player Name                                                     |
|----------------------------------------------------------------|
| Accounts                  Reminders              Preferences    |
| Main: Gov Name            KVK: Enabled           Inventory: ... |
| Accounts: 3 linked        Times: 24h, 1h         Exports: ready |
| Action: Review            Action: Manage         Action: Edit   |
|----------------------------------------------------------------|
| Quick launch: KVK stats | targets | history | rankings | export |
+----------------------------------------------------------------+
```

The card should be introduced only after the data contract is stable enough to avoid misleading
status.

## 14. Interaction Model and Anti-Busy Rules

Rules:

- Dashboard has at most 3 visible sections.
- Dashboard starts with at most 3 primary buttons: Accounts, Reminders, Preferences.
- Quick launch uses one select menu or compact secondary buttons, not a wall of buttons.
- Use modals only for focused text input such as Governor ID or Governor name.
- Account/reminder mutation confirmations must be private.
- Dashboard and all setup flows should default ephemeral.
- Public quick launches must follow the target command's existing channel and visibility rules.
- Every subview has a "Back to dashboard" route.
- Timeouts disable controls and leave a short private retry path.
- Destructive actions such as remove account or unsubscribe require confirmation.
- Legacy command users receive redirect/help messaging only after a later approved phase.
- Where mutation is not implemented yet, prefer useful status and clear next-action guidance over
  disabled or dead "coming soon" controls.
- The dashboard must not read like a command index; command names can appear in transition/help
  copy, but the primary UI should describe player-owned actions and states.

Initial button/select budget:

| Surface | Buttons | Selects | Modals |
| --- | ---: | ---: | ---: |
| `/me dashboard` | 3 primary, up to 1 secondary | 1 quick-launch select | 0 |
| `/me accounts` | 4 actions plus back | 1 account/slot select | Governor ID/name input |
| `/me reminders` | 3 actions plus back | event type and time selects | 0 |
| `/me preferences` | 2 actions plus back | preference select where needed | 0 |
| `/me exports` | 2 export actions plus back | format/view selects where needed | 0 |

## 15. Legacy Migration and Deprecation Plan

1. Build `/me` in parallel.
2. Keep every legacy command live.
3. Add player/operator docs and a briefing note.
4. Watch usage and player feedback.
5. Convert selected legacy commands to redirect/help responses only after operator approval.
6. Wait through an agreed no-feedback window.
7. Remove legacy registrations only in a separate cleanup phase.

Initial keep-live list:

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

Legacy command removal is explicitly out of scope until rollout evidence exists.

## 16. Architecture Target State

Target ownership:

| Concern | Target |
| --- | --- |
| Commands | `commands/me_cmds.py`, thin and decorated |
| Dashboard/account/reminder orchestration | `player_self_service` service layer |
| Registry writes | existing `registry/registry_service.py` and `registry/dal/registry_dal.py` |
| Reminder reads/writes | new reminder centre service wrapping existing stores before mutation is exposed |
| Inventory preferences/exports | existing inventory services/DAL |
| Stats exports | existing stats export service/DAL |
| Views/modals | `ui/views/player_self_service_views.py` |
| Visual rendering | later `player_self_service/rendering/` or approved shared card package |
| SQL | SQL repo only, later if approved |
| Docs | command reference, task packs, player briefing |

Do not put direct SQL in `commands/me_cmds.py` or new views.

## 17. SQL/Data Dependency Notes

Validated SQL source objects exist for:

- registry persistence and uniqueness: `dbo.DiscordGovernorRegistry` plus registry stored
  procedures and indexes
- Governor lookup: `dbo.vw_All_Governors_Clean`
- active player audit support: `dbo.v_Active_Players`
- personal stats export: `dbo.vDaily_PlayerExport`
- inventory reporting/preferences/export: inventory tables listed in section 4
- command usage review: `dbo.BotCommandUsage`

No SQL schema change is recommended for Phase 2.

Potential later SQL question:

- KVK subscriptions are file-backed today. A SQL-backed subscription store may be useful later,
  but should not be folded into `/me` shell work. Treat it as a separate design task if current
  JSON/tracker behavior proves insufficient.

## 18. Testing and Validation Strategy

Phase 1 documentation validation:

- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py "docs/task_packs/Player Self-Service Command Centre - Phase 1 Audit and Design Report.md" "docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 2 Command Shell and Navigation Foundation.md"`
- After docs are written: run architecture/deferred/test-selector validators where practical.

Phase 2 implementation tests should include:

- command registration validation
- command inventory tests
- `/me` command smoke tests
- decorator/usage tracking expectations for grouped paths
- dashboard service no-account/single-account/multi-account status tests
- reminder summary tests for subscribed, unsubscribed, invalid/empty config
- preference summary tests for unset/private/public inventory visibility
- view ownership, timeout, back-navigation, and stale interaction tests
- no mutation tests proving Phase 2 does not register, remove, subscribe, unsubscribe, or export
  directly from the dashboard shell

Player journey acceptance checks:

- New player with no accounts can run `/me dashboard` and understand how to get started without
  already knowing `/mygovernorid` or `/register_governor`.
- Existing player with one account can immediately see their main account and setup status.
- Existing player with multiple accounts can see that multiple accounts are linked without being
  shown a dense full-slot matrix on the dashboard.
- Subscribed player can see what KVK reminders they have enabled without opening
  `/modify_subscription`.
- Unsubscribed player can understand how to set reminders without being shown a dense
  configuration screen.
- Player never sees full account details, full reminder details, and export forms on the same
  screen.
- Unknown source states are visible and honest, not hidden behind false "ready" language.

Recommended focused commands for Phase 2:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_inventory.py tests\test_command_registration_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_views.py
```

Broaden to full pytest before promotion because `/me` crosses multiple player-facing subsystems.

## 19. Risks and Rollback/Containment

| Risk | Containment |
| --- | --- |
| New top-level group not approved | Stop before implementation or choose a lower-quality grouped alternative |
| Dashboard becomes too busy | Enforce section/button/select budgets |
| Misleading status | Show "unknown" or "not available" instead of guessed completion |
| Reminder restart behavior regresses | Do not mutate reminders in Phase 2; test restart/tracker behavior in Phase 4 |
| Legacy command confusion | Keep old commands live; use briefing before redirects |
| Privacy regression | Default setup views to ephemeral; quick launches respect existing command rules |
| Cross-domain service creep | Keep command shell service read-only in Phase 2 |

Rollback for Phase 2 is simple if kept shell-only: remove `/me` registration, remove docs entries,
and leave all legacy commands unchanged.

## 20. Proposed Implementation Phases

1. Phase 2 - `/me` command shell and polished dashboard embed foundation.
2. Phase 3 - Modern account centre.
3. Phase 4 - Modern reminder centre.
4. Phase 4B - Visual `/me dashboard` generated card once account/reminder status contracts are
   stable.
5. Phase 5 - First-pass preferences and exports launchpad.
6. Phase 6 - Legacy redirects, briefing, and final cleanup after approval.

## 21. Recommended Next Task Pack

Use:

```text
docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 2 Command Shell and Navigation Foundation.md
```

Phase 2 should add the `/me` group only after operator approval. It should create the shell,
read-only summary service, polished private dashboard embed, basic views, tests, command reference
updates, and briefing draft. It should not change account registrations, subscription configs,
inventory preference writes, export generation, SQL schema, or legacy command behavior.

## 22. Deferred Optimisations

### Deferred Optimisation
- Area: `commands/subscriptions_cmds.py`, `ui/views/subscription_views.py`, `subscription_tracker.py`, `event_scheduler.py`, `dm_tracker_utils.py`, `reminder_task_registry.py`
- Type: architecture
- Description: Player KVK reminder mutation is currently concentrated in command callbacks and view closures that own validation, event-type normalization, reminder-time normalization, DM confirmation, unsubscribe cleanup, task cancellation, and scheduled/sent tracker updates. Copying this into `/me reminders` would preserve mixed command/view/service responsibilities and increase restart-safety risk.
- Suggested Fix: Before `/me reminders` performs writes, create a reminder centre service that owns subscription validation, mutation, tracker cleanup, task cancellation, DM confirmation outcomes, and scheduler coordination. Keep views limited to interaction routing and user-readable confirmations.
- Impact: high
- Risk: medium
- Dependencies: Phase 2 shell is complete; focused subscription view, tracker, scheduler, and restart-safety tests are selected.

### Deferred Optimisation
- Area: `ui/views/registry_views.py`, `commands/registry_cmds.py`, `target_utils.py`
- Type: refactor
- Description: The account journey has strong registry service/DAL persistence, but current commands and views still own Governor ID lookup branching, duplicate/claim checks, slot-selection flow, and confirmation payload shaping. The same Governor ID lookup journey appears across `/mygovernorid`, registry modals, and account action views.
- Suggested Fix: For Phase 3, introduce an account centre service that prepares account summaries, slot options, Governor ID lookup results, claim-check outcomes, and confirmation models. Leave registry views to route selects/modals and call the service.
- Impact: medium
- Risk: medium
- Dependencies: Phase 2 shell is complete; preserve registry stored procedure contracts and existing registry tests.

### Deferred Optimisation
- Area: `commands/calendar_cmds.py`, `ui/views/reminder_config.py`, `event_calendar/reminder_prefs_store.py`, `commands/subscriptions_cmds.py`
- Type: architecture
- Description: KVK event reminders and calendar reminder preferences are separate player-facing reminder surfaces with different storage and terminology. Folding both into `/me reminders` without a shared product model could confuse players or imply one setting controls the other.
- Suggested Fix: Keep Phase 2 `/me reminders` read-only and explicit about which reminder family is shown. Later, decide whether `/me reminders` presents KVK reminders only, calendar reminders only, or a two-tab/two-section reminder centre with clear labels and separate persistence boundaries.
- Impact: medium
- Risk: medium
- Dependencies: Operator decision on reminder terminology and player communication.

## 23. Delivery Notes

- Runtime code changed: no.
- SQL changed: no.
- Helpers reused: no runtime helper changes; audit identified existing account, registry, stats
  export, inventory, interaction safety, and command validation helpers for future reuse.
- Restart behavior changed: no.
- Codex Security review: skipped for Phase 1 because this is documentation/design only. Future
  implementation phases touch Discord interactions, permissions, user input, SQL/data access, file
  exports, and restart-sensitive reminder persistence, so Codex Security should be considered
  before PR handoff.
