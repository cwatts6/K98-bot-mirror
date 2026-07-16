# Codex Task Pack - Player Self-Service Command Centre v2 Phase 5F Inventory Surface Consolidation and Legacy Retirement

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 5F Inventory Surface Consolidation and Legacy Retirement`
- Date: `2026-07-16`
- Owner/context: Follow-on from completed, operator-accepted, merged, and deployed GovernorOS v2 Phase 5E Preferences. This task supersedes the previously proposed Phase 5F Premium Inventory Summary Card.
- Task type: `feature retirement | Discord command cleanup | Inventory UX consolidation | Preferences simplification | dead-code removal`
- One-pass approved: `No`
- Product decision approved: `Yes`
- Runtime implementation approved: `Yes, subject to the normal audit, architecture, and implementation-plan stop gates`
- Status: `implemented locally; validation, review, and mirror PR handoff in progress`
- New runtime backdrop: `none`
- Existing Preferences backdrop retained: `assets/me/cards/me_preferences.png`
- Asset approved for deletion after reference audit: `assets/me/cards/me inventory.png`
- Deployment shape: `one coordinated bot release; do not deploy a dead Inventory-visibility setting or a temporary half-retired command surface`

The operator has explicitly approved the retirement of `/me inventory`, `/myinventory`, and
`/inventory_preferences`. Public Inventory report posting is no longer required, and the legacy
combined `All` viewing route is not required by players. The definitive Inventory experience is the
selected-governor dashboard plus the private premium Resources, Speedups, and Materials reports.

This task must begin with repository inspection and exact dependency confirmation. Do not reopen the
retirement decision unless current repository evidence proves that a retained production capability
has no replacement or that the proposed removal would affect an unrelated supported workflow.

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5F Inventory Surface Consolidation and Legacy Retirement.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5E Premium Preferences Summary Card.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5B Premium Inventory Report Backdrops and Visual Alignment.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5A Direct Inventory Reports and Governor Context.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Then follow the conditional reading order in `docs/reference/README.md` for Discord command changes,
views/components, rendering and file handling, SQL-backed preferences, tests, security routing, and
promotion.

For SQL-facing validation, inspect the authoritative SQL repository:

```text
C:\K98-bot-SQL-Server
```

At minimum, verify `dbo.InventoryReportPreference` and search for every SQL-side dependency before
claiming that its Python callers are the final runtime consumers. No SQL deployment or destructive
SQL cleanup is approved in Phase 5F.

## 3. Objective

Make GovernorOS the single coherent Inventory experience by removing the redundant all-linked
Inventory summary and the legacy `/myinventory` route, while preserving the accepted private premium
selected-governor reports, imports, audits, calculations, ranges, exports, filenames, and Google
Sheets behavior.

At the same time, remove the now-obsolete Inventory visibility setting from Personal Settings and
simplify that page to regional profile and local-time context only. Delete code and assets that become
genuinely orphaned as a direct result, but do not turn the task into a broad Inventory or generic-view
refactor.

## 4. Background And Confirmed Evidence

### 4.1 Product evidence

Operator-supplied production usage evidence after the Phase 5A replacement routes were available:

```text
UserId              UserDisplay       Uses   LastSeenUtc
559076207627468807  Chrislos (1198)   2      2026-07-15 15:36:31.378
```

The only `/myinventory` user was the operator. The operator has confirmed:

- public Inventory report posting is not required;
- the combined `All` report viewing option is not required by players;
- `/myinventory` can be removed rather than redirected;
- `/inventory_preferences` is no longer required and can be removed;
- the old all-linked `/me inventory` summary should not receive a new premium card;
- the simpler selected-governor dashboard and direct premium report journey is the intended final UX.

### 4.2 Current deployed code surface confirmed before task-pack creation

The deployed Phase 5E tree still contains all three retiring entry points:

```text
commands/me_cmds.py
- /me inventory -> PAGE_INVENTORY

commands/inventory_cmds.py
- /myinventory
- /inventory_preferences redirect
- /inventory import and /inventory audit, which must remain
```

The old summary path remains:

```text
/me inventory
-> ui/views/player_self_service_views.py PAGE_INVENTORY
-> player_self_service/service.py all-linked InventoryStatus
-> player_self_service/page_cards.py Inventory branch
-> assets/me/cards/me inventory.png
-> Open Report
-> ui/views/inventory_report_views.py legacy selector
```

The legacy detailed-report path remains separate from the modern GovernorOS report controller:

```text
/myinventory
-> Inventory visibility read/default prompt
-> governor/output selector, including All
-> visibility-controlled public or ephemeral report posting
-> legacy range/export controller in ui/views/inventory_report_views.py
```

The modern path that must remain is:

```text
/me dashboard -> RSS | Speedups | Materials
/me resources | /me speedups | /me materials
-> ui/views/player_self_service_inventory_report_views.py
-> selected-governor access resolution/recheck
-> existing premium 1400x980 renderer
-> report tabs, 1M/3M/6M/12M, private exports, Dashboard return, Change Governor
```

Phase 5E currently makes Inventory visibility a required Preferences dependency:

```text
player_self_service/preferences_summary.py
- loads Inventory visibility with the regional profile
- produces PRIVATE/PUBLIC state and consequence copy
- treats a visibility-read failure as page-unavailable

player_self_service/preferences_renderer.py
- renders the PRIVATE/PUBLIC badge
- renders PRIVACY & SHARING

ui/views/player_self_service_preference_views.py
- Manage settings -> Privacy & sharing
- state-aware visibility confirmation and save

player_self_service/preference_service.py
- visibility revalidation and mutation
```

The old generic Player Self-Service summary also eagerly loads Inventory visibility, profile/VIP, and
all-linked Inventory data before producing Reminders or Exports. Phase 5F must audit and remove only
the summary fields/loaders that have no remaining live caller after the retiring routes are removed.

### 4.3 Command-governance baseline

Before Phase 5F:

```text
top-level commands: 42
/me grouped subcommands: 9
/inventory grouped subcommands: 2
```

Approved Phase 5F result:

```text
top-level commands: 40
/me grouped subcommands: 8
/inventory grouped subcommands: 2
```

The top-level reduction is `/myinventory` plus `/inventory_preferences`. Removing `/me inventory`
changes only the grouped `/me` count. `/inventory import`, `/inventory audit`, `/export_inventory`,
and the top-level `/inventory` group are not removed by this task.

### 4.4 Documentation-state mismatch to resolve

At the audit snapshot used to prepare this pack, the programme and task-pack index described Phase 5E
as archived, while the mirror repository still exposed the Phase 5E pack and starter under the active
`docs/task_packs/` path. The implementation branch must verify the local checkout and move those two
completed records into `docs/task_packs/archive/` if they are still active. Do not create duplicate
archive copies when the local checkout has already completed the move.

## 5. Approved Product Outcome

### 5.1 Final player Inventory model

```text
/me dashboard
  -> latest approved RSS, Speedups, and Materials for the selected governor
  -> RSS | Speedups | Materials buttons

/me resources
/me speedups
/me materials
  -> direct private premium selected-governor reports
  -> report tabs, ranges, private exports, Dashboard return, Change Governor

/me exports
  -> private Inventory export options, including All export scope

/inventory import
  -> screenshot import

/inventory audit
  -> admin import audit
```

Retired:

```text
/me inventory
/myinventory
/inventory_preferences
public Inventory report posting
combined All report viewing route
Inventory visibility preference in Personal Settings
```

### 5.2 Privacy model

After Phase 5F:

- every player-facing detailed Inventory report is private/ephemeral;
- report exports remain private;
- no player setting can make a direct report public;
- no public message is posted as part of Inventory viewing;
- no replacement Share/Public action is introduced;
- any future sharing workflow requires a new evidence-backed product decision and task pack.

### 5.3 Personal Settings model

`/me preferences` remains the private **Personal Settings** centre for:

- saved timezone;
- saved location/country;
- preferred-language metadata;
- derived local-time or UTC-reference context;
- three-field profile coverage;
- one deterministic regional-profile Settings Insight.

It no longer owns or displays Inventory visibility.

Approved header state:

```text
LOCAL
```

when a usable saved timezone produces the local-time reference, otherwise:

```text
UTC
```

for the honest UTC fallback. These labels describe the displayed time-reference mode; they are not a
new saved preference and do not change Reminder Centre UTC scheduling.

Approved main action:

```text
Manage settings
```

The action should open the Regional Profile field-selection journey directly. Do not retain an
otherwise-empty intermediate menu with a removed Privacy & sharing choice unless repository evidence
shows that direct entry would break an established lifecycle contract.

### 5.4 Preferences visual reflow

Reuse the accepted, fully opaque `1702x924` backdrop:

```text
assets/me/cards/me_preferences.png
```

Do not create or require a new backdrop.

Remove:

- PRIVATE/PUBLIC badge and color semantics;
- PRIVACY & SHARING heading/panel/copy;
- Inventory visibility consequence text;
- privacy-specific confirmation language;
- privacy-specific Settings Insight priority;
- `Update your regional profile and Inventory privacy.` copy.

Retain:

- invoking-user avatar and safe fallback;
- duplicate-safe Kingdom 1198 identity;
- local-time/UTC hero;
- regional profile rows;
- profile coverage;
- deterministic Settings Insight;
- stable `me_preferences_<discord_user_id>.png` filename;
- same-payload fallback;
- standalone private attachment;
- graceful timeout and complete stream cleanup.

The regional profile may expand across the body space reclaimed from Privacy & Sharing. Do not invent
a new metric or duplicate the same three values merely to fill the background. Exact line placement
must be checked at native, Discord desktop, and mobile scales before final acceptance.

## 6. Scope

### In Scope

- remove `/me inventory` command registration and all active navigation to the retired page;
- remove `/myinventory` command registration and its legacy report-selection journey;
- remove `/inventory_preferences` command registration and redirect;
- update command-registration approved baselines and grouped counts;
- remove `PAGE_INVENTORY`, Inventory summary fallback/card routing, Open Report, and related component
  IDs/copy;
- remove `assets/me/cards/me inventory.png` after proving no runtime or test reference remains;
- delete `ui/views/inventory_report_views.py` when the final import/reference audit confirms the file
  is exclusively owned by the retiring legacy journey;
- remove the Inventory visibility enum, read/write service wrappers, DAL methods, preference mutation
  service, and tests when no supported caller remains;
- detach Personal Settings from `dbo.InventoryReportPreference` and simplify its typed payload,
  renderer, fallback, Manage journey, insight rules, and tests;
- remove all-linked Inventory summary models/helpers/loaders from `player_self_service/service.py`
  when no supported caller remains;
- stop unrelated `/me` pages from eagerly reading obsolete visibility or all-linked Inventory summary
  data where the dependency is removed by this task;
- remove only newly orphaned generic page-card branches and helpers required by the retiring page;
- preserve the Preferences backdrop and reflow the existing card without a new asset;
- preserve direct reports, dashboard highlights, imports, audits, private exports, and existing report
  rendering/calculation contracts;
- update programme, task-pack indexes, canonical command reference, player/operator briefing,
  README-DEV, deferred items, tests, and smoke instructions;
- move completed Phase 5E task-pack records into the archive if the local checkout has not already done
  so;
- perform the required command resync/cache validation after deployment so removed guild commands do
  not remain visible.

### Out Of Scope

- deleting or changing `dbo.InventoryReportPreference` in SQL;
- migrating, rewriting, or backfilling existing visibility rows;
- adding a new privacy/sharing setting;
- adding a public Share Report action;
- changing `/inventory import`, upload-first imports, correction/review flows, materials continuation,
  or `/inventory audit`;
- changing Inventory calculations, source SQL, report payloads, trend logic, VIP calculations, report
  dimensions, stable report filenames, or premium report backdrops;
- changing direct-report tabs, ranges, Change Governor, >25 paging, access rechecks, no-data guidance,
  Dashboard return, or private export behavior;
- removing `InventoryReportView.ALL` where it remains required for private Inventory exports;
- removing `build_latest_inventory_snapshot()` or current-RSS helpers used by the governor dashboard or
  Accounts portfolio;
- changing Inventory export schemas, date windows, formats, filenames, or Google Sheets behavior;
- removing `/export_inventory` in this phase;
- changing `/my_stats`, `/my_stats_export`, `/mykvkcrystaltech`, `/stats player`, `/player_profile`, or
  `/kvk history`;
- broad consolidation of all Player Self-Service renderers/views before Phase 5G Exports is complete;
- dropping other historical assets or archived documentation merely because they mention retired
  commands;
- SQL schema, view, index, procedure, permission, or deployment changes.

## 7. Source Deferred Items

This task promotes the Inventory-specific portion of the following active deferred themes:

### Deferred Optimisation
- Area: `commands/me_cmds.py`, `ui/views/player_self_service_views.py`, `player_self_service/governor_dashboard_*`, `/me dashboard`, player self-service v2 docs/tests
- Type: architecture
- Description: The roadmap previously expected a premium Inventory summary. Product evidence now shows that the summary and legacy command surface are redundant; Phase 5F is promoted as consolidation and retirement instead.
- Suggested Fix: Execute this task pack as the active Phase 5F slice, preserving the modern direct-report and dashboard contracts.
- Impact: high
- Risk: medium
- Dependencies: Phase 5E deployed; usage evidence and operator approval recorded.

### Deferred Optimisation
- Area: `ui/views/player_self_service_views.py`, `player_self_service/page_cards.py`, `player_self_service/dashboard_card.py`, remaining generic `/me` page delivery
- Type: consistency
- Description: Inventory is no longer waiting for premium summary alignment. Its old summary path is approved for removal; Exports remains the only planned generic summary-page migration.
- Suggested Fix: Remove the Inventory-specific generic path now and keep the broader generic-renderer consolidation deferred until Phase 5G is accepted.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5F product decision; Phase 5G remains separate.

### Deferred Optimisation
- Area: legacy player self-service command registrations and Inventory preference/report views
- Type: cleanup
- Description: `/myinventory` and `/inventory_preferences` were previously retained for migration guidance or compatibility. Usage evidence and explicit operator approval now promote their final removal into Phase 5F.
- Suggested Fix: Remove only the approved Inventory registrations and directly orphaned code in this task; keep unrelated legacy cleanup deferred.
- Impact: medium
- Risk: low
- Dependencies: operator evidence and approval recorded in this pack.

## 8. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | `use` | Required to confirm the exact retiring command/view/service/DAL/asset/test boundary and prevent over-deletion of shared modern Inventory code. |
| `k98-discord-command-feature` | `use` | The task removes slash commands, buttons, views, selectors, interaction callbacks, response-visibility behavior, and command-cache entries. |
| `k98-sql-validation` | `use` | Validate that `dbo.InventoryReportPreference` has no SQL-side behavior or external bot consumer that changes the safe Python-removal boundary. No SQL write/change is approved. |
| `k98-test-selection` | `use` | Required before validation because the task spans command governance, Preferences, Inventory reports, exports, dashboard highlights, and import regression boundaries. |
| `k98-deferred-optimisation-capture` | `use` | Capture only genuinely out-of-scope non-security findings, particularly the later SQL table retirement and post-5G generic-renderer consolidation. |
| `k98-pr-review` | `use` | Required before handoff to verify no supported report/import/export path was removed and command/docs baselines agree. |
| `k98-promotion-check` | `use` | Required before production PR/promotion, command resync, and bot deployment. |
| `k98-security-review-routing` | `use` | Route a bot-repository Changes review because the diff changes Discord interactions, public/private behavior, command registration, SQL-backed preference reads/writes, and file/view lifecycle. SQL repo receives a documented skip because Phase 5F makes no SQL diff. |

### Security Review Decision

| Repository | Decision | Target | Expected setup / execution | Evidence |
|---|---|---|---|---|
| `K98-bot-mirror` | `Changes review` | Final Phase 5F branch or working-tree diff against the intended mirror `main` base | `Changes + Deep Off` using `$codex-security:security-diff-scan` | Pending final diff; verify command removal, private-only report behavior, authorization preservation, stale/foreign interaction handling, and no newly unsafe fallback or file lifecycle. |
| `K98-bot-SQL-Server` | `documented skip` | Read-only validation of `dbo.InventoryReportPreference` and dependency search; no SQL files changed | `Not applicable` | Record exact SQL files/searches inspected and that no schema, data, permission, procedure, migration, or deployment behavior changed. |

Do not start a standard or deep codebase audit without a separate explicit operator request.

## 9. Mandatory Workflow

1. Audit and scope review, then stop for approval.
2. Record the provisional `k98-security-review-routing` decision and exact Git target; do not start a
   scan during the audit response.
3. Architecture validation and exact file manifest, then stop for approval.
4. Implementation plan, including command-cache/deployment ordering, then stop for approval.
5. Implement only after approval.
6. Run focused/full validation, visual QA, command registration, SQL read-only contract checks, and
   K98 PR review.
7. Execute the bot Changes security review against the final diff with Deep off.
8. Create/review the mirror PR and complete operator Discord smoke.
9. Run promotion check, promote the same patch to production, resync commands, deploy, and verify the
   retired commands are absent.

Do not deploy separate partial workstreams that leave either:

- a Personal Settings privacy control with no supported report behavior; or
- a publicly posting legacy report path after the privacy control has been removed.

## 10. Audit Requirements

The first implementation response must report, with repository evidence:

### 10.1 Command and registration map

- exact registration and decorators for `/me inventory`, `/myinventory`, and
  `/inventory_preferences`;
- exact current top-level/grouped command counts and every hard-coded baseline/test/doc affected;
- command-cache/resync behavior required to remove guild commands after code deployment;
- confirmation that `/inventory import`, `/inventory audit`, and `/export_inventory` remain intact.

### 10.2 Legacy route ownership

- every import and caller of `ui/views/inventory_report_views.py`;
- whether the file can be deleted in full;
- every class/helper/test owned solely by `/myinventory` or `/me inventory` Open Report;
- every player-facing string that still directs users to a retiring command.

### 10.3 Modern report preservation

- exact `/me resources`, `/me speedups`, `/me materials`, and dashboard-button path;
- selected-governor access resolution and recheck;
- report type/range/Change Governor preservation;
- private export behavior;
- `InventoryReportView.ALL` export consumers;
- dashboard and Accounts current Inventory snapshot consumers;
- report renderer/backdrop/filename consumers.

### 10.4 Inventory visibility dependency map

- every Python reference to `InventoryReportVisibility`;
- every read/write/default/confirmation path in service and DAL layers;
- every test and doc asserting Only Me/Public behavior;
- exact SQL object definition and SQL-side dependency search;
- confirmation that no supported runtime consumer remains after the three approved commands and
  Preferences privacy UI are removed.

### 10.5 Preferences simplification map

- exact current Preferences summary, renderer, fallback, and child-view fields tied to visibility;
- exact current profile-only behavior that must remain;
- whether `ManageSettingsView` and `player_self_service/preference_service.py` become fully orphaned;
- exact safe route for `Manage settings` to open Regional Profile directly;
- exact LOCAL/UTC state derivation from the existing `TimeReferenceSummary`;
- card geometry and visual sample plan using the existing backdrop.

### 10.6 Generic summary and performance boundary

- exact live callers of `PlayerSelfServiceSummary.preferences` and `.inventory`;
- exact eager data reads performed by `build_player_self_service_summary` for Reminders, Exports,
  Accounts host refresh, and any fallback path;
- fields/loaders/helpers that can be removed without redesigning Reminders or Exports;
- pre-existing generic renderer branches that are unrelated to Phase 5F and should remain deferred;
- measurable test or call-count evidence that obsolete Inventory/visibility reads are gone.

### 10.7 Assets and documentation

- every reference to `me inventory.png` and whether the asset can be deleted safely;
- active versus archive location of Phase 5E task-pack records;
- canonical/current docs requiring updates;
- historical archived records that should remain unchanged as accurate history.

### 10.8 Stop condition

Do not code during the first audit response. Stop after:

1. audit findings;
2. exact review/modify/delete/create manifest;
3. architecture recommendation;
4. identified risks and rollback boundary;
5. test-selection proposal;
6. approval checkpoint.

## 11. Architecture Targets And Likely Files

The audit decides the final manifest. The following is the evidence-based starting point.

### Review

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `commands/me_cmds.py`
- `commands/inventory_cmds.py`
- `commands/command_inventory.py`
- `scripts/validate_command_registration.py`
- `ui/views/player_self_service_views.py`
- `ui/views/inventory_report_views.py`
- `ui/views/player_self_service_inventory_report_views.py`
- `ui/views/player_self_service_preference_views.py`
- `ui/views/player_self_service_export_views.py`
- `ui/views/player_self_service_governor_dashboard_views.py`
- `player_self_service/service.py`
- `player_self_service/page_cards.py`
- `player_self_service/dashboard_card.py`
- `player_self_service/preferences_summary.py`
- `player_self_service/preferences_renderer.py`
- `player_self_service/preference_service.py`
- `player_self_service/governor_dashboard_service.py`
- `inventory/models.py`
- `inventory/reporting_service.py`
- `inventory/dal/inventory_reporting_dal.py`
- `inventory/report_image_renderer.py`
- `inventory/export_service.py`
- `assets/me/cards/me inventory.png`
- `assets/me/cards/me_preferences.png`
- command, Preferences, Inventory, export, dashboard, and Player Self-Service tests
- active canonical/player/operator docs
- SQL repo `sql_schema/dbo.InventoryReportPreference.Table.sql` and repository-wide dependency search

### Likely Modify

- `commands/me_cmds.py`
- `commands/inventory_cmds.py`
- `scripts/validate_command_registration.py`
- `ui/views/player_self_service_views.py`
- `ui/views/player_self_service_preference_views.py`
- `player_self_service/preferences_summary.py`
- `player_self_service/preferences_renderer.py`
- `player_self_service/service.py`
- `player_self_service/page_cards.py`
- `inventory/models.py`
- `inventory/reporting_service.py`
- `inventory/dal/inventory_reporting_dal.py`
- focused test modules identified by audit
- `README-DEV.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/README.md`
- `docs/task_packs/archive/README.md`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`

### Likely Delete

- `ui/views/inventory_report_views.py`
- `player_self_service/preference_service.py`, only if no supported caller remains
- `assets/me/cards/me inventory.png`
- tests dedicated solely to the retired legacy controller, summary page, and visibility mutation

### Likely Move

- completed Phase 5E task pack and chat starter from `docs/task_packs/` to
  `docs/task_packs/archive/`, only if still active in the implementation checkout

### Create

- no new runtime module or asset is expected;
- create only tests/helpers when the audit proves they are needed for a clean existing-layer boundary.

## 12. Implementation Requirements

### 12.1 Workstream A - Command and navigation retirement

- remove the `/me inventory` grouped command and `PAGE_INVENTORY` import;
- remove `/myinventory` and `/inventory_preferences` registrations;
- remove every active `Inventory` navigation button from the generic Player Self-Service view;
- remove the `Open Report` button, callback, context adapter, and visibility prompt handoff;
- remove expired/error/help copy that instructs users to rerun retired commands;
- keep commands and views thin;
- update the approved top-level baseline and grouped-count expectations;
- ensure usage tracking and command versioning remain correct for all retained commands;
- explicitly resync application commands after deployment.

### 12.2 Workstream B - Legacy report-controller deletion

- prove `ui/views/inventory_report_views.py` has no retained runtime caller;
- remove the legacy governor/output selector, public/private dispatch, first-use preference prompt,
  old range/export controller, and `All` viewing option;
- delete dedicated tests rather than weakening them into meaningless coverage;
- do not remove the modern selected-governor report controller;
- do not remove shared renderer/export services used by modern reports or `/me exports`.

### 12.3 Workstream C - Personal Settings simplification

- make `PreferencesSummaryPayload` profile/time-reference focused;
- remove `InventoryVisibilitySummary`, consequence constants, visibility loader, visibility warnings,
  and visibility-required availability failure;
- derive the card state from existing time-reference mode as `LOCAL` or `UTC`;
- remove the Privacy & Sharing panel and fallback field;
- remove public/private insight priority and produce one profile-only deterministic sentence;
- keep profile coverage exactly out of three;
- keep unknown/unavailable saved profile values honest and internal keys hidden;
- make `Manage settings` open the Regional Profile journey directly where safe;
- remove privacy child views, confirmation, mutation locks used only for visibility, and related copy;
- preserve field catalogs, pagination, atomic per-field save/clear, stale/superseded handling, Back to
  Preferences, avatar, attachment replacement, and timeout behavior;
- reuse `assets/me/cards/me_preferences.png` and stable filename.

Recommended Settings Insight priority:

1. saved profile metadata is unavailable and needs review;
2. no usable timezone, so local-time context cannot be shown;
3. timezone is ready but one or both optional regional details are unset;
4. all three regional profile values are available.

### 12.4 Workstream D - Summary and data-read cleanup

- remove `InventoryCategoryStatus`, `InventoryStatus`, all-linked summary builders, upload-guidance
  summary copy, and snapshot loader wiring when no supported caller remains;
- remove generic visibility/profile/VIP summary fields and loaders only where the audit proves they
  are not used by a retained page or child refresh;
- stop Reminders and Exports from paying for obsolete Inventory/visibility reads;
- preserve account resolution used by Exports availability and retained page navigation;
- preserve reminder projection and scheduler-parity behavior unchanged;
- do not redesign the Exports summary or complete the Phase 5G renderer in this task;
- use call-count/fake-loader tests to prove removed readers are not invoked.

### 12.5 Workstream E - Visibility persistence detachment

When no supported caller remains:

- remove `InventoryReportVisibility` from the bot model;
- remove visibility read/write/default/resolve service APIs;
- remove visibility DAL queries and MERGE logic;
- remove the Preferences mutation service if fully orphaned;
- remove related tests and documentation;
- leave `dbo.InventoryReportPreference` and existing rows unchanged for rollback;
- add a structured deferred SQL cleanup item rather than dropping the table now.

### 12.6 Workstream F - Asset and generic-renderer cleanup

- delete `me inventory.png` only after static/runtime/test references are zero;
- remove only Inventory-specific branches from `player_self_service/page_cards.py`;
- do not use Phase 5F to delete the remaining generic Exports renderer or to build a broad framework;
- keep historical archived task packs/assets where they are accurate execution records and not runtime
  inputs.

### 12.7 Workstream G - Documentation and deployment

Update current truth in:

- programme pack;
- task-pack indexes;
- canonical command reference and counts;
- player/operator briefing;
- README-DEV;
- deferred optimisations;
- command smoke instructions;
- any current non-archived help copy.

Deployment order:

1. validate final bot diff and command inventory;
2. merge/promote the same patch;
3. deploy/restart the bot;
4. run the approved command resync/cache validation;
5. verify `/me inventory`, `/myinventory`, and `/inventory_preferences` are absent from Discord;
6. smoke `/me dashboard`, all three direct reports, `/me preferences`, `/me exports`, `/inventory
   import`, and `/inventory audit`;
7. retain SQL table/data untouched.

### 12.8 Command Surface Governance

- [ ] Record top-level command count `42 -> 40`.
- [ ] Record `/me` grouped subcommand count `9 -> 8`.
- [ ] Confirm `/inventory` remains at two subcommands.
- [ ] Remove `myinventory` and `inventory_preferences` from
  `APPROVED_TOP_LEVEL_COMMANDS`.
- [ ] Update canonical command tables and grouped summary.
- [ ] Update relevant player/operator docs and smoke references.
- [ ] Preserve decorators and versions for retained commands.
- [ ] Run `scripts/validate_command_registration.py`.
- [ ] Run `tests/test_validate_command_registration.py`.
- [ ] Run `tests/test_command_inventory.py`.
- [ ] Run `tests/test_command_registration_smoke.py`.
- [ ] Run focused `/me` and Inventory command registration tests.
- [ ] Perform and verify command resync after deployment.

## 13. Refactor Decisions

| Issue | Decision | Reason |
|---|---|---|
| Premium `/me inventory` card | `remove` | Dashboard highlights and direct premium reports are the canonical route; another summary adds no player value. |
| `/myinventory` | `remove` | Operator-only usage, no need for public posting, and no need for combined All viewing. |
| `/inventory_preferences` | `remove` | Its only meaningful preference is retired. |
| Public Inventory posting | `remove` | Explicit operator decision; all canonical report/export routes remain private. |
| Legacy `ui/views/inventory_report_views.py` | `remove if audit confirms exclusive ownership` | Modern GovernorOS reports use a separate controller. |
| Inventory visibility Python model/service/DAL | `remove if no caller remains` | Avoid a dead setting and dead SQL reads/writes. |
| `dbo.InventoryReportPreference` | `defer SQL retirement` | Preserve rollback and avoid an unnecessary destructive SQL deployment. |
| Preferences backdrop | `keep and reflow` | The accepted asset remains suitable; no replacement asset is needed. |
| All-linked Inventory summary service | `remove` | It exists for the retired page and causes unnecessary reads. |
| `InventoryReportView.ALL` | `keep where exports use it` | All export scope remains supported even though All viewing is retired. |
| Modern selected-governor report controller | `keep unchanged` | It is the definitive report UX. |
| Broad Player Self-Service renderer/view consolidation | `defer` | Wait until Phase 5G Exports has an accepted replacement. |
| Import orchestration refactor | `defer` | Separate active deferred item; unrelated to report-surface retirement. |

Any suspected security issue must follow `k98-security-review-routing`; do not record it as ordinary
optimisation debt.

## 14. Testing Requirements

Use `k98-test-selection` and the repository selector before finalizing exact commands.

### 14.1 Command and static-removal coverage

- `/me` registers exactly eight approved subcommands without Inventory;
- top-level baseline excludes `myinventory` and `inventory_preferences`;
- `/inventory import` and `/inventory audit` remain registered;
- no active command/view/copy references retired paths;
- command inventory reports the approved 40/8/2 result;
- command-cache/resync smoke confirms removed commands disappear.

### 14.2 Preferences coverage

- LOCAL state with a valid timezone, including DST and non-whole-hour offsets;
- UTC state with unset or unavailable timezone;
- complete, partial, unset, and unavailable profile values;
- profile-only insight priority;
- renderer/fallback contain no privacy or Inventory visibility content;
- Manage settings opens regional field selection directly;
- field save, clear, pagination, superseded, foreign, concurrent, cancel/back, and timeout behavior;
- avatar and no-avatar fallback;
- long/Unicode display names and labels;
- same-payload fallback, edit/send failure, attachment replacement, and complete stream cleanup;
- native, Discord desktop, and mobile visual samples.

### 14.3 Inventory preservation coverage

- dashboard RSS, Speedups, and Materials highlights remain correct;
- dashboard buttons open the correct selected-governor report;
- direct `/me resources`, `/me speedups`, and `/me materials` no/one/multiple/>25 journeys;
- report tabs, 1M/3M/6M/12M, Change Governor, Dashboard return, no-data guidance, private exports,
  attachment lifecycle, and timeout remain unchanged;
- report images preserve dimensions, filenames, data, icons, dates, and backdrops;
- Accounts current RSS and Inventory As Of remain correct;
- `/me exports` Inventory export supports Resources/Speedups/Materials/All, governor scope, windows,
  Excel/CSV/Sheets, and private delivery;
- `/inventory import`, upload-first import, materials continuation, correction/review, cancellation,
  approval, audit, and admin debug regressions remain green.

### 14.4 Data-access and performance coverage

- Preferences does not read `InventoryReportPreference`;
- Reminders and Exports do not invoke removed visibility or all-linked summary loaders;
- modern dashboard/report/Accounts loaders still call required Inventory readers;
- no new direct SQL exists in commands or views;
- SQL dependency search is recorded with no SQL diff.

### 14.5 Suggested validation commands

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
```

Focused tests should include the audit-confirmed equivalents of:

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests\test_me_cmds.py `
  tests\test_player_self_service_views.py `
  tests\test_player_self_service_service.py `
  tests\test_player_self_service_preferences_summary.py `
  tests\test_player_self_service_preferences_renderer.py `
  tests\test_player_self_service_preference_views.py `
  tests\test_me_inventory_report_views.py `
  tests\test_inventory_reporting_service.py `
  tests\test_governor_dashboard_discord_views.py `
  tests\test_governor_dashboard_service.py `
  tests\test_inventory_report_image_renderer.py `
  tests\test_inventory_export_service.py `
  tests\test_player_self_service_export_views.py `
  tests\test_validate_command_registration.py `
  tests\test_command_inventory.py `
  tests\test_command_registration_smoke.py
```

Delete obsolete test modules from the command only after their production code is deleted. Add the
actual selected Inventory import regression set identified by `scripts/select_tests.py`.

For the final runtime diff also run:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Run `git diff --check`, import smoke, native-size image inspection, Discord desktop/mobile previews,
and the final bot Changes security review.

## 15. Acceptance Criteria

- [ ] The exact repository dependency map has been audited and approved before coding.
- [ ] `/me inventory` is no longer registered or reachable through active navigation.
- [ ] `/myinventory` is no longer registered.
- [ ] `/inventory_preferences` is no longer registered.
- [ ] Top-level command count is 40 and `/me` grouped count is 8.
- [ ] Removed commands disappear from the Discord command cache after resync.
- [ ] Public Inventory report posting no longer exists.
- [ ] Combined All viewing no longer exists.
- [ ] Private All Inventory export remains available where currently supported.
- [ ] Dashboard Inventory highlights and all three direct report journeys remain unchanged.
- [ ] Imports, audits, report calculations, ranges, filenames, backdrops, exports, and Google Sheets
  behavior remain unchanged.
- [ ] Personal Settings contains no Inventory visibility state, panel, mutation, consequence copy, or
  dead privacy control.
- [ ] Personal Settings uses honest LOCAL/UTC presentation and retains all regional profile behavior.
- [ ] The existing Preferences backdrop, avatar, fallback, attachment, cleanup, and timeout contracts
  remain accepted.
- [ ] The legacy Inventory summary asset and directly orphaned code/tests are removed.
- [ ] `dbo.InventoryReportPreference` is not read or written by the retained runtime.
- [ ] `dbo.InventoryReportPreference` and its rows remain unchanged in SQL for rollback.
- [ ] No required dashboard, Accounts, direct-report, or export Inventory helper is over-deleted.
- [ ] No new direct SQL exists in commands or views.
- [ ] Current docs, command references, task indexes, and deferred items match the delivered state.
- [ ] Completed Phase 5E task records are archived if they were still active.
- [ ] Focused tests, full pytest, pre-commit, validators, log-noise analysis, and visual QA pass.
- [ ] Bot Changes security review is completed against the intended final diff with Deep off.
- [ ] Mirror PR review, operator Discord smoke, promotion check, production promotion, deployment, and
  command resync complete successfully.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. Audit Evidence And Final Scope
3. File Manifest
4. New Files
5. Modified Files
6. Deleted Files And Assets
7. Moved/Archived Files
8. SQL Validation And No-Change Statement
9. Helpers Reused And Preserved
10. Refactor Findings
11. Command Surface Before/After
12. Test And Visual Evidence
13. Security Review Decision And Evidence
14. Deployment And Command-Resync Steps
15. Rollback Plan
16. Deferred Optimisations

Rollback must be code-first: restore the removed bot routes and Preferences visibility dependency,
resync commands, and redeploy the prior accepted build. The untouched SQL table/rows provide a clean
rollback data boundary.

## 17. PR Summary Template

```md
## Summary

- retire `/me inventory`, `/myinventory`, and `/inventory_preferences`
- make the selected-governor dashboard and private premium Inventory reports the definitive viewing journey
- simplify Personal Settings to regional profile and LOCAL/UTC context
- remove directly orphaned visibility, legacy-controller, summary, test, and asset code

## Changes

- reduce top-level command count from 42 to 40 and `/me` subcommands from 9 to 8
- remove public Inventory report posting and combined All viewing
- preserve private All Inventory exports, imports, audits, calculations, ranges, filenames, report backdrops, Dashboard highlights, and modern report controls
- leave `dbo.InventoryReportPreference` untouched for rollback and defer SQL retirement

## Tests

- Exact focused command, Preferences, Inventory, export, dashboard, and import test commands to be recorded from the completed implementation.
- `python scripts/validate_architecture_boundaries.py`
- `python scripts/validate_deferred_items.py`
- `python scripts/select_tests.py`
- `python scripts/validate_codex_security_routing.py`
- `python scripts/validate_command_registration.py`
- `python scripts/smoke_imports.py`
- `python -m pre_commit run -a`
- `python -m pytest -q tests`
- `python scripts/analyse_pytest_log_noise.py`

## Security Review

- Decision: `Changes review`
- Repository / target: final Phase 5F mirror branch against the intended `main` base; record the exact commit range before scanning.
- Expected setup / execution: `Changes + Deep Off`
- Evidence: pending final Changes review; record the completed scan result and any finding disposition before PR handoff.
- SQL repository: `documented skip; read-only contract/dependency validation only, no SQL diff`

## Deferred Optimisations

- retain `dbo.InventoryReportPreference` for a later evidence-led SQL retirement slice
- retain broad generic Player Self-Service renderer/view consolidation until Phase 5G is complete

## Risk / Rollback

- primary risk is accidental removal of shared modern Inventory report/export/dashboard helpers
- rollback restores the prior bot patch and command registrations, resyncs commands, and reuses the untouched SQL preference rows
```
