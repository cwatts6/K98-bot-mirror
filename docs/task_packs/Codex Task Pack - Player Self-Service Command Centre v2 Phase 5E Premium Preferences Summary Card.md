# Codex Task Pack - Player Self-Service Command Centre v2 Phase 5E Premium Preferences Summary Card

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 5E Premium Preferences Summary Card`
- Date: `2026-07-15`
- Owner/context: Follow-on from completed and operator-accepted GovernorOS v2 Phases 5D Reminders and 5D.1 Authoritative Next Scheduled Alert Projection.
- Task type: `feature | premium Preferences renderer | Discord interaction simplification | narrow settings-ownership migration`
- One-pass approved: `No`
- Product/content/visual contract approved: `Yes`
- Runtime implementation approved: `Yes, subject to the normal repository audit, architecture, and implementation-plan stop gates`
- Status: `next active GovernorOS implementation slice`
- Approved runtime backdrop: `assets/me/cards/me_preferences.png`
- Required output: `1702 x 924` standalone private PNG
- Stable filename: `me_preferences_<discord_user_id>.png`

The product and visual workshop is complete. Do not reopen the core information architecture, add
new settings, or restore VIP to Preferences unless repository evidence proves the locked contract is
unsafe or impossible. Start with repository inspection and architecture confirmation, report any
material mismatch, and stop at the required approval gates before coding.

## 2. Required Reading

Read first:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5E Premium Preferences Summary Card.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5D Premium Reminders Summary Card.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5D.1 Authoritative Next Scheduled Alert Projection.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card.md`
- the archived/current task for `GovernorOS Preferences Centre "The Governor's Accord" Backdrop V1`, where present
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- the GovernorOS Visual Design Bible where present

Then follow the conditional reading order in `docs/reference/README.md` for Discord views,
rendering/file handling, SQL-backed preferences, testing, and deployment.

Validate every touched SQL-backed persistence or field contract against:

```text
C:\K98-bot-SQL-Server
```

This task does not approve a SQL deployment. SQL validation is required because Inventory
visibility, user profile metadata, and VIP are existing persisted contracts whose ownership and UI
entry points are being changed.

## 3. Objective

Deliver a premium private `/me preferences` experience that feels like a purposeful Personal
Settings Centre rather than a catch-all setup page. It must make the player's saved regional context,
current local-time reference, and Inventory privacy understandable in seconds.

At the same time, simplify the action surface to one `Manage settings` entry and move governor-
specific VIP editing to the existing Accounts management journey, while preserving the underlying
profile, visibility, VIP, authorization, persistence, and legacy-command contracts.

## 4. Background And Current-State Audit

The current page is known to expose:

- Inventory visibility as public or private;
- a VIP summary for linked governors;
- saved timezone, location, and language;
- a direct `Set Public` or `Set Private` action;
- `Update VIP`;
- `Manage Profile`;
- a native profile child window with timezone, country/location, language, and clear controls.

The likely current owner chain is:

```text
/me preferences
-> commands/me_cmds.py
-> ui/views/player_self_service_views.py
-> player_self_service/service.py builds the current Discord-user summary
-> player_self_service/page_cards.py renders the current 1702x924 Preferences card
-> concise private embed is the fallback

Set Public / Set Private
-> existing Inventory visibility service/persistence
-> host Preferences refresh

Update VIP
-> existing linked-governor and VIP selection child view
-> existing GovernorInventoryProfile service/persistence
-> host Preferences refresh

Manage Profile
-> existing private profile child view
-> saved timezone/location/language service and catalogs
-> per-field save/clear behavior
-> host Preferences refresh or Back transition
```

This map is intentionally a starting hypothesis. The first implementation step must confirm the
actual modules, data sources, mutation ownership, fallback path, timeout behavior, host refresh,
and tests. Do not move code based only on this document's likely filenames.

## 5. Approved Product Ownership

### 5.1 Preferences owns user-level settings

`/me preferences` remains private, Discord-user scoped, and independent of a selected governor. Its
approved responsibility is:

- saved timezone;
- saved location/country;
- preferred language metadata;
- Inventory privacy and sharing;
- derived local-time context from the saved timezone;
- future cross-GovernorOS defaults only when separately approved and genuinely user-level.

It must not become the home for account data, report controls, reminder configuration, export
options, or unrelated fields merely because they do not yet have another page.

### 5.2 Accounts owns governor-specific VIP

VIP is linked-governor account data. Phase 5E therefore approves the following narrow migration:

- remove the VIP list from the Preferences card and fallback;
- remove `Update VIP` from the Preferences main view and Manage Settings journey;
- add `Update VIP` as a task inside the existing `Manage Accounts` child journey;
- reuse the current governor-to-VIP selection, validation, save, and persistence path rather than
  implementing a second editor;
- continue showing VIP read-only where already approved in Accounts/Account Summary and Inventory;
- keep the account-management host page all-linked/user scoped with no `Change Governor` control.

This is a UI ownership migration, not a VIP data-model redesign.

### 5.3 Preferences remains the single Inventory-visibility editor

The Inventory visibility setting remains here under `Privacy & Sharing` because it is a user-level
privacy decision. Other pages may show the current state read-only, but they must not become a
second mutation owner during this phase.

## 6. Scope

### In Scope

- a typed, read-only Preferences summary payload or cohesive extension of the existing summary;
- deterministic local-time and UTC-offset derivation from the saved timezone and one injected UTC
  `generated_at` value;
- friendly timezone, country, and language presentation using current authoritative catalogs;
- profile-detail coverage for timezone, location, and preferred language;
- a deterministic one-sentence Settings Insight;
- a dedicated premium `1702x924` Preferences render using
  `assets/me/cards/me_preferences.png`;
- best-effort invoking-user Discord avatar with the accepted GovernorOS safe fallback;
- standalone private attachment delivery with same-authorized-payload fallback;
- one main `Manage settings` action and a simplified private settings child journey;
- deliberate confirmation for Inventory visibility changes;
- removal of VIP content/actions from Preferences;
- narrow re-hosting of the existing Update VIP journey inside `Manage Accounts`;
- current access recheck for every governor-specific VIP save;
- timeout, stale/foreign/forged/concurrent handling, attachment replacement, and stream cleanup;
- focused/full tests, visual samples, Codex Security review, PR review, mirror smoke, and production
  promotion gates;
- programme, briefing, canonical reference, task-pack index, and deferred-item documentation updates.

### Out Of Scope

- a new preference or profile field;
- a preferred/default governor setting;
- a 12/24-hour display preference;
- a local-versus-UTC application-wide display toggle;
- automatic timezone or location detection;
- inferring timezone from location, language, Discord locale, IP address, or device data;
- full interface localization or translation;
- changing the Reminder Centre's UTC schedule policy;
- per-governor Inventory visibility;
- privacy audit history or sharing telemetry;
- a new VIP source, validation rule, default, range, or business definition;
- account registry, ownership, claim, slot, lookup, replace, or remove redesign;
- SQL schema/table/view/index/stored-procedure changes;
- new persistence or a migration of saved values;
- Inventory report, import, range, export, filename, or Google Sheets changes;
- command additions, renames, redirects, or removals;
- a broad summary-card renderer/view framework;
- changes to Phase 5D reminders, Phase 5F Inventory summary, Phase 5G Exports summary, History, or
  Inspect.

## 7. Locked Visual And Delivery Contract

### 7.1 Runtime asset

Use only:

```text
assets/me/cards/me_preferences.png
```

Requirements:

- exact size `1702 x 924`;
- fully opaque production asset; RGBA storage is acceptable only when every alpha value is `255`;
- no runtime use of a 2x master;
- missing, corrupt, transparent, or wrong-sized assets must fail safely into the same-payload private
  fallback rather than a blank or stretched card;
- never stretch or silently crop the approved asset.

### 7.2 Successful output

- standalone private attachment, not an embed-wrapped image;
- stable filename `me_preferences_<discord_user_id>.png`;
- generated off the event loop;
- no second service/data fetch when rendering or delivery fails;
- deliberate clearing/replacement of prior attachments when moving between parent and child views;
- every image, byte buffer, and Discord file stream closed on success, fallback, edit/send failure,
  timeout, cancellation, stale suppression, and concurrent navigation.

### 7.3 Identity treatment

- use the invoking Discord user's bounded circular avatar in the accepted Accounts/Reminders style;
- use a safe local fallback when avatar retrieval, validation, decoding, or timeout fails;
- fit long and Unicode display names;
- do not derive the page identity from a selected governor;
- avoid duplicating the Kingdom suffix when a display name already ends in an equivalent `(1198)`
  presentation.

### 7.4 Composition map

The renderer should respect the approved backdrop geometry:

```text
Full canvas:                       x 0-1702,    y 0-924
Header and identity:               x 92-1610,  y 48-202
Local-time / UTC-reference hero:   x 92-1610,  y 214-390
Architectural transition:          x 0-1702,   y 396-416
Regional Profile:                  x 92-1000,  y 426-650
Privacy & Sharing:                 x 1020-1610,y 426-650
Inter-column gap:                  x 1000-1020,y 426-650
Settings Insight:                  x 92-1610,  y 664-752
Manage explanation:                x 92-1610,  y 766-848
Footer:                            x 92-1610,  y 858-920
```

Pillow may draw restrained GovernorOS panels and separators. The background itself contains no fake
UI. Do not place important text over the extreme architectural lanes.

## 8. Approved Main-Card Information Hierarchy

### 8.1 Header

Preferred visual title:

```text
PERSONAL SETTINGS
```

The slash command and navigation label remain `/me preferences` and `Preferences`.

Header content:

```text
PERSONAL SETTINGS                                      PRIVATE
Chrislos (1198)                         3 of 3 profile details set
```

The upper-right privacy state is exactly one of:

- `PRIVATE`;
- `PUBLIC`.

Recommended color treatment:

- `PRIVATE`: restrained green/teal positive treatment;
- `PUBLIC`: warm amber/gold attention treatment;
- do not present `PUBLIC` as an error or use alarm red.

Supporting completeness copy:

- `3 of 3 profile details set`;
- `2 of 3 profile details set`;
- `1 of 3 profile details set`;
- `No profile details set`.

Do not invent `READY`, `REVIEW`, or `SETUP` for this page. Optional profile fields are descriptive,
not a pass/fail account state.

### 8.2 Local-time hero

Valid saved-timezone example:

```text
LOCAL TIME REFERENCE
17:29
Europe/London • UTC+1
United Kingdom • English (UK)
```

No usable timezone example:

```text
UTC REFERENCE
16:29 UTC
Set a timezone to add local-time context.
```

Rules:

- compute the displayed time once from the payload's injected aware UTC `generated_at`;
- use a consistent 24-hour `HH:mm` presentation; do not infer a 12-hour preference;
- derive the current UTC offset from the saved timezone at `generated_at`, including daylight-saving
  changes and non-whole-hour offsets;
- use an unambiguous offset label such as `UTC`, `UTC+1`, `UTC-3`, `UTC+5:30`;
- reuse an existing timezone helper/catalog when authoritative;
- otherwise use a proven local IANA-timezone implementation available in the repository/runtime;
- perform no network call and add no external time service;
- do not infer timezone from location or language;
- if the saved timezone is absent or cannot be resolved, show the UTC-reference variant and surface
  a reviewable warning without exposing an unsafe raw key;
- the card is a snapshot, not a ticking clock; no job, timer, or automatic refresh is created;
- this hero does not change Reminder Centre schedule display or reminder dispatch semantics.

### 8.3 Regional Profile

Approved rows:

```text
REGIONAL PROFILE
Timezone: Europe/London
Location: United Kingdom (GB)
Preferred language: English (UK) • en-GB
```

Unset values use `Not set`.

Rules:

- reuse current authoritative timezone, country, and language catalogs and ordering;
- keep stored codes/keys unchanged;
- show player-facing labels and codes where useful;
- raw unknown keys remain internal;
- an unavailable legacy value is not silently treated as valid or as `Not set`;
- `Preferred language` is metadata only unless the application is already localized; do not promise
  that the whole interface will change language;
- profile completeness counts the three recognized, usable saved values: timezone, location, and
  preferred language;
- location and language remain optional; incomplete coverage is neutral unless a saved value is
  invalid/unavailable.

### 8.4 Privacy & Sharing

Approved structure:

```text
PRIVACY & SHARING
Inventory visibility: PRIVATE
<one- or two-line explanation of the exact current visibility consequence>
```

or:

```text
PRIVACY & SHARING
Inventory visibility: PUBLIC
<one- or two-line explanation of the exact current visibility consequence>
```

Before finalizing wording, trace the authoritative visibility service and every affected report path.
The copy must not imply that private direct `/me resources`, `/me materials`, or `/me speedups`
reports become public; Phase 5A explicitly keeps those paths private. Suitable wording should make
clear that the preference controls only the supported existing Inventory visibility surface.

Never claim that a report is public, private, discoverable, or shared more broadly than the actual
runtime contract.

### 8.5 Settings Insight

Render exactly one deterministic sentence, normally no more than two clauses.

Priority order:

1. unavailable or invalid saved profile metadata that needs review;
2. no usable timezone, because local-time context cannot be shown;
3. Inventory is public, so the sharing state deserves deliberate awareness;
4. one or more optional regional profile values are not set;
5. complete regional profile with private Inventory as the neutral-positive state.

Approved example family:

```text
A saved profile value is no longer available; review your regional profile in Manage settings.
Set a timezone to add local-time context; your inventory remains private.
Your inventory is public; review sharing when you no longer need supported reports to be public.
Two of three profile details are set; the remaining field can be added at any time.
Your regional profile is complete; local time is 17:29 and inventory remains private.
```

Do not:

- infer that location and timezone should match;
- warn because a player travels, lives abroad, or chooses another timezone;
- infer nationality, language fluency, preferred event time, or risk;
- use cross-player popularity or recommendations;
- repeat every card value in prose;
- invent a recommendation to fill space.

### 8.6 Action explanation and footer

Action copy:

```text
Manage settings
Update your regional profile and inventory privacy.
```

Footer pattern:

```text
Local time is a refresh-time reference • Reminder schedules remain in UTC
Refreshed 15 Jul 2026 14:49 UTC
```

Use the accepted split-footer pattern where it reads best: explanatory context on the left and a
full UTC refreshed date-time on the right. The same injected `generated_at` must drive both the
local-time hero and footer.

## 9. Recommended Typed Summary Contract

Create a cohesive Preferences-specific payload if the existing shared summary cannot express the
approved rules cleanly. Do not make commands or views assemble the card.

Recommended concepts:

```text
PreferencesSummaryPayload
- Discord-user identity
- generated_at_utc
- privacy: InventoryVisibilitySummary
- regional_profile: RegionalProfileSummary
- time_reference: TimeReferenceSummary
- profile_details_set
- profile_details_total = 3
- profile_supporting_text
- deterministic Settings Insight
- warnings / unavailable saved values

InventoryVisibilitySummary
- is_public
- state_label: PRIVATE | PUBLIC
- player-facing consequence text derived from the authoritative visibility contract

RegionalProfileSummary
- timezone: PreferenceValueSummary
- location: PreferenceValueSummary
- preferred_language: PreferenceValueSummary

PreferenceValueSummary
- is_set
- is_available
- stored_key/code retained internally
- player-facing label
- optional player-facing code

TimeReferenceSummary
- LOCAL | UTC_FALLBACK
- display_time
- timezone_label when usable
- utc_offset_label when usable
- optional location/language context
- source/supporting line
```

Payload rules:

- use one aware UTC clock value per request;
- keep formatting and insight logic deterministic and unit-testable;
- no writes occur while building the summary;
- no N+1 governor reads are introduced merely because the old Preferences payload contained VIP;
- do not fetch VIP for the Preferences card unless a still-shared internal payload requires it for
  another page and removing that read would create unsafe broad refactoring;
- service failures degrade honestly; missing is not zero, false, or private by assumption.

## 10. Main Discord Component Contract

The accepted main-page rows are:

```text
Row 1: Accounts | Reminders | Preferences (active/disabled)
Row 2: Dashboard | Exports
Row 3: Manage settings
```

Rules:

- use blue-primary styling for the first-row global navigation;
- use the existing secondary style for `Dashboard` and `Exports`;
- use one clear success-style `Manage settings` action;
- remove the deprecated/irrelevant Inventory navigation button from this page, matching accepted
  Accounts and Reminders navigation;
- remove direct `Set Public`/`Set Private`, `Update VIP`, and `Manage Profile` buttons from the main
  Preferences view;
- use real Discord components only; paint no buttons into the PNG;
- the active `Preferences` button remains disabled;
- optional selected-governor context is retained only so `Dashboard` can return to the same validated
  governor.

## 11. Manage Settings Child Journey

`Manage settings` replaces the existing private host content in place. It must not open duplicate
private follow-up windows for repeated clicks.

### 11.1 Child layout

The preferred compact child flow is one native settings window:

```text
MANAGE SETTINGS
Regional profile
- Timezone select/update flow
- Location select/update flow
- Preferred language select/update flow

Privacy & sharing
- state-aware Change Inventory Visibility action

Back to Preferences
```

Use the existing field catalogs, pagination, save/autosave, validation, and persistence semantics.
Do not introduce a cross-field transaction unless the current code already owns one.

### 11.2 Clear / Not set behavior

Remove the permanent row of three separate `Clear Timezone`, `Clear Country`, and `Clear Language`
buttons from the top-level child window.

Preferred behavior:

- expose `Not set` or `Clear` deliberately inside the relevant field's existing update flow;
- if a select already reaches Discord's 25-option limit, use a contextual field-specific clear step
  rather than dropping a real option or adding three persistent host buttons;
- preserve the exact stored-null/clear semantics and confirmation requirements already in use;
- after a successful update/clear, refresh the same child state so the saved value is visible;
- `Back to Preferences` regenerates the parent summary from current authorized state and replaces
  child attachments/components cleanly.

### 11.3 Inventory visibility change

The privacy action must be state aware:

- when private, offer a clear action to make the supported Inventory visibility public;
- when public, offer a clear action to make it private;
- show the current state and exact consequence before mutation;
- require explicit confirmation for both directions;
- re-read or revalidate current state at confirmation time to reject stale/concurrent changes;
- use the existing visibility service and persistence contract;
- cancellation returns to Manage Settings without mutation;
- success returns to a refreshed Preferences parent card or another operator-approved clear success
  state that immediately reflects the new privacy pill;
- no public message is posted merely because the visibility preference changed.

### 11.4 Child timeout and interaction safety

- author-gated;
- reject foreign, stale, forged, superseded, and concurrent interactions;
- preserve the last valid private content on timeout;
- visibly disable every remaining child control;
- provide a concise rerun/back instruction where the current architecture supports it;
- do not refetch or rerender merely to mark timeout;
- close any attachment or image stream owned by a child-to-parent refresh.

## 12. VIP Migration Into Manage Accounts

### 12.1 Placement

Add `Update VIP` at the existing task-selection level inside `Manage Accounts`, alongside the current
lookup/register/replace/remove account-management tasks. Do not add a second green button to the
Accounts main card solely for VIP.

### 12.2 Behavior to reuse

Re-host the current Update VIP child journey with the smallest safe refactor:

```text
Manage Accounts
-> Update VIP
-> explicit linked-governor selection/resolution
-> explicit VIP-level selection
-> Save VIP
-> current access and state recheck
-> existing persistence service
-> clear success/error result
-> return/refresh Accounts management host
```

Rules:

- retained Dashboard governor context must never silently choose the governor;
- one linked governor may be offered/preselected only if that is already the current journey's
  behavior; do not bypass explicit identity display and access validation;
- multiple and more-than-25 linked governors use the accepted paged selector/resolver contract where
  required;
- zero linked governors receive concise register-account guidance and no write;
- recheck current registry linkage/authorization immediately before save;
- preserve the existing VIP range, labels, null/not-set behavior, write contract, logging, and error
  handling;
- do not change Account Summary, Inventory calculations, or SQL definitions merely because the
  editor moved;
- successful save should be visible when the player returns to an Accounts surface that already
  displays VIP, without requiring a stale cached payload.

### 12.3 Removal from Preferences

Tests and review must prove that Preferences no longer:

- displays per-governor VIP values;
- fetches them solely for rendering;
- exposes an Update VIP component;
- carries a governor selector for VIP;
- implies VIP is a Discord-user-level preference.

## 13. Governor Context And Privacy Rules

| Surface | Scope | Governor behavior |
|---|---|---|
| Preferences summary | Discord user | No Change Governor; no governor filter |
| Manage Settings | Discord user | No governor picker |
| Inventory visibility | Discord user | Existing user-level mutation contract |
| Accounts summary | All linked governors / Discord user | No Change Governor |
| Manage Accounts -> Update VIP | Governor-specific child | Explicit governor resolution and access recheck |
| Dashboard | Selected governor | Return context only when navigating to Preferences |

Additional rules:

- direct `/me preferences` entry carries no implicit governor;
- navigation from a selected Dashboard may retain the selected ID only for a validated Dashboard
  return;
- no selected governor may alter profile, privacy, local-time, or completeness content;
- every Preferences output remains private even when Inventory visibility is `PUBLIC`;
- user-level settings must not leak into future leadership `/me inspect` output.

## 14. Architecture Targets

| Concern | Target |
|---|---|
| Slash command entry | existing `commands/me_cmds.py` path; thin dispatch only |
| Parent/child Discord views | existing `ui/views/` Player Self-Service ownership, split only when a narrow module removes real complexity |
| Preferences summary assembly | `player_self_service` service/model layer |
| Local-time and label derivation | pure/service helpers with injected clock; reuse current catalogs |
| Inventory visibility mutation | existing authoritative Inventory profile/visibility service |
| VIP mutation | existing authoritative Inventory profile service, re-hosted under Accounts management |
| Data access | existing repository/DAL/service contracts; no direct SQL in commands/views |
| Rendering | dedicated or page-specific renderer ownership; no broad framework |
| Documentation | `docs/` programme/task/canonical/briefing/deferred surfaces |
| Tests | focused `tests/` modules plus full repository gates |

Commands and views must not own timezone conversion, profile-completeness rules, privacy consequence
copy, insight priority, SQL, or VIP business logic.

## 15. Likely Files

### Review

- `commands/me_cmds.py`
- `ui/views/player_self_service_views.py`
- every current Preferences/Profile child-view module discovered from that path
- every current Accounts Manage child-view module discovered from that path
- `player_self_service/service.py`
- `player_self_service/page_cards.py`
- any existing page-specific renderer/model modules used by Accounts and Reminders
- `inventory/profile_service.py`
- the existing Inventory visibility repository/service path
- the existing GovernorInventoryProfile VIP repository/service path
- current timezone, country, and language catalog/helper modules
- current attachment/edit/timeout helper modules
- `tests/test_me_cmds.py`
- `tests/test_player_self_service_views.py`
- `tests/test_player_self_service_service.py`
- `tests/test_player_self_service_page_cards.py`
- focused Inventory profile/visibility tests
- focused Accounts management tests
- command registration and smoke tests

### Modify

Only files proven necessary by the audit, expected to include:

- Preferences summary model/service/renderer ownership;
- Player Self-Service parent navigation/action composition;
- the current profile/settings child view;
- the current Accounts Manage task selector;
- the existing VIP child route/import location where required;
- focused tests and programme/reference docs.

### Create

Create a dedicated `preferences` model/renderer/helper module only when repository inspection proves
that extending the shared `page_cards.py` or service would make ownership materially worse. Do not
create a speculative framework or duplicate existing avatar/panel/text-fitting primitives.

## 16. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | `use` | Required before implementation because the slice crosses parent views, settings services, rendering, and a narrow Accounts child migration. |
| `k98-discord-command-feature` | `use` | Buttons, selects, confirmations, child replacement, timeout, author gating, and page navigation change. |
| `k98-sql-validation` | `use` | Validate existing profile, visibility, and GovernorInventoryProfile contracts; no SQL deployment is approved. |
| `k98-test-selection` | `use` | Required to combine focused profile/visibility/VIP/view/render tests with broader regressions. |
| `k98-deferred-optimisation-capture` | `use` | Capture out-of-scope shared-renderer, catalog, or legacy-flow debt without widening 5E. |
| `k98-pr-review` | `use` | Required before mirror PR handoff. |
| `k98-promotion-check` | `use later` | Required before production PR/merge/deployment after operator smoke. |
| `codex-security:security-scan` | `use` | Privacy mutation, author-gated Discord interactions, governor access, persisted profile values, asset/file handling, and attachment lifecycle are in scope. |

## 17. Mandatory Workflow

1. **Repository audit / scope review** — map the exact current Preferences, profile, visibility, VIP,
   Accounts Manage, renderer/fallback, attachment, and timeout flows; then stop for approval.
2. **Architecture validation** — propose exact files/layers, helper reuse, SQL-contract validation,
   and refactor boundaries; then stop for approval.
3. **Implementation plan** — map work into code/test/doc steps and list any deviations from this
   locked contract; then stop for approval.
4. **Implementation** after approval.
5. **Focused and full validation**, visual samples, security review, and PR review.
6. **Mirror PR and operator Discord smoke**.
7. **Production promotion check**, production PR, deployment, and final smoke only after acceptance.

The audit may refine filenames and implementation mechanics. It may not silently change the product
ownership, content hierarchy, action model, or approved backdrop.

## 18. Audit Requirements And Escalation Gates

The initial audit must report:

- exact current command/view/service/repository/renderer/fallback chain;
- exact persistence owner for timezone, location, language, Inventory visibility, and VIP;
- authoritative catalogs and friendly-label helpers;
- existing clear/save/autosave semantics;
- existing visibility consequence across `/me` direct reports, `/myinventory`, exports, and any
  public report paths;
- current Update VIP governor resolution, access checks, option limits, save semantics, and host
  refresh;
- current Accounts Manage task-selection component budget;
- current avatar/background/attachment lifecycle and timeout behavior;
- current tests and gaps;
- exact likely file manifest;
- whether the approved backdrop exists, is `1702x924`, and is fully opaque.

Stop and ask the operator before implementation if:

- the backdrop is absent, corrupt, non-opaque, or not exactly `1702x924`;
- the saved timezone contract cannot produce authoritative local time without a new dependency or
  persistence change;
- the current Inventory visibility behavior cannot be explained accurately in player-facing copy;
- moving Update VIP requires changing registry authority, VIP meaning, SQL schema, or account
  lifecycle rules;
- adding Update VIP to Manage Accounts exceeds Discord component limits without a material workflow
  redesign;
- current profile clear semantics would be changed by the proposed child simplification;
- a broad shared renderer/view framework appears necessary;
- an out-of-scope defect must be fixed to deliver safely.

Do not silently omit the local-time hero, retain VIP in Preferences, expose a direct public toggle,
or substitute a new setting to work around a blocker.

## 19. Initial Refactor Decisions

| Issue | Decision | Reason |
|---|---|---|
| VIP list/editor on Preferences | `fix now` | Governor-specific data has a clear Accounts owner and currently dominates a user-level page. |
| Three unrelated main actions | `fix now` | One Manage Settings action creates a coherent low-frequency settings surface. |
| Local-time derivation in renderer/view | `do not allow` | Deterministic conversion belongs in a pure/service layer with an injected clock. |
| Three permanent Clear buttons | `fix now within approved child flow` | Keep clear semantics but move them into the relevant field flow. |
| Broad summary-card framework extraction | `defer` | Phase 5E remains page-specific; extract only helpers already proven across accepted pages. |
| Preferred governor or time-format setting | `defer` | No approved cross-module behavior or user-value evidence yet. |
| Full localization | `defer` | Preferred language remains profile metadata under the current contract. |
| SQL/profile schema redesign | `not applicable` | Existing persisted values and meanings are retained. |

Any newly discovered deferred item must use the structured format in
`docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 20. Command Surface Governance

- No new top-level command.
- No new `/me` grouped subcommand.
- `/me preferences`, `/me accounts`, and all legacy redirects retain their names and registration.
- Preserve `@versioned()`, `@safe_command`, `@track_usage()`, permission decorators, private response
  behavior, command-cache behavior, and usage-log identities.
- Increment only existing command/page version metadata required by repository policy; do not treat
  a version increment as a new command.
- Update canonical documentation to state that VIP editing now lives under `Manage Accounts` while
  `/me preferences` owns regional profile and Inventory privacy.
- Run:

```powershell
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_command_inventory.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_command_registration_smoke.py
```

Use actual repository-supported commands/paths when names differ.

## 21. Testing Requirements

### 21.1 Summary service and deterministic formatting

Cover:

- all three profile values set;
- each one-field and two-field partial combination;
- all values unset;
- valid IANA timezone in standard time;
- valid timezone during daylight saving;
- positive, negative, whole-hour, half-hour, and quarter-hour UTC offsets where supported;
- UTC timezone;
- local date differing from UTC date;
- missing timezone;
- unavailable/invalid saved timezone;
- known and unknown country/language codes;
- profile-completeness rules;
- exact insight priority and one-sentence output;
- single injected `generated_at` driving hero and footer;
- no location/timezone mismatch inference;
- service failure and honest unavailable behavior.

### 21.2 Renderer and fallback

Cover:

- exact `1702x924` output;
- stable filename;
- strict background size/opacity validation;
- private and public pills;
- local-time and UTC-reference heroes;
- complete, partial, unset, and unavailable profile states;
- long/Unicode display name;
- long timezone, country, and language labels;
- two-line privacy consequence;
- maximum intended insight length;
- avatar success and fallback;
- duplicate-safe Kingdom identity;
- same-payload embed fallback;
- render failure, file creation failure, send/edit failure;
- deliberate attachment clearing and complete stream closure.

### 21.3 Parent view and navigation

Cover:

- direct `/me preferences` entry;
- navigation from a selected Dashboard and validated return;
- no, one, multiple, and more-than-25 linked governors do not alter Preferences content;
- no `Change Governor` on Preferences;
- active Preferences navigation disabled;
- no Inventory navigation button;
- one `Manage settings` action only;
- no direct Set Public/Private, Update VIP, or Manage Profile main buttons;
- author, foreign, stale, forged, superseded, concurrent, timeout, and cancellation paths;
- parent/child attachment replacement and cleanup.

### 21.4 Manage Settings

Cover:

- existing timezone/location/language save behavior;
- field-specific clear/Not set behavior;
- Discord 25-option/pagination behavior;
- child replacement rather than duplicate windows;
- current values reflected after save/clear;
- Back to Preferences refresh;
- privacy state-aware action;
- confirmation and cancellation in both directions;
- stale-state revalidation;
- mutation failure without misleading success;
- no public message emitted by the setting change;
- timeout disables controls and preserves the last valid private content.

### 21.5 VIP migration and Accounts regression

Cover:

- no VIP values or controls on Preferences card/fallback/Manage Settings;
- Update VIP appears inside Manage Accounts at the approved task level;
- zero linked governors receive guidance and no write;
- one, multiple, and more-than-25 governor selection paths;
- retained Dashboard governor is never silently selected;
- current linkage/access is rechecked before save;
- current VIP labels/range/not-set/save semantics remain unchanged;
- stale/foreign/forged/concurrent save rejection;
- successful save appears on the appropriate refreshed Accounts surface;
- existing find/register/replace/remove/confirm/cancel/ownership/claim/slot flows are unchanged;
- Account Summary and Inventory VIP calculations remain compatible.

### 21.6 Repository gates

At minimum run or justify the exact repository equivalents of:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
```

Add focused tests selected from the actual touched modules. Record test counts and skips accurately.

## 22. Visual Validation Matrix

Generate clean review samples at original size, normal Discord desktop width, and mobile preview for
at least:

1. Private Inventory; all profile details set; valid daylight-saving timezone.
2. Public Inventory; all profile details set.
3. Private Inventory; timezone unset; UTC-reference hero.
4. Private Inventory; only one profile detail set.
5. All profile details unset.
6. Invalid/unavailable saved timezone or catalog value.
7. Long/Unicode display name and long labels.
8. Maximum intended Settings Insight and two-line privacy consequence.
9. Avatar unavailable fallback.
10. Same-payload fallback embed.

Review the complete Discord message with external navigation and `Manage settings` beneath the
attachment. The local-time hero must dominate without making the card look like a clock room; the
profile/privacy columns must remain balanced; the footer must remain readable; no heavy emergency
darkening should be necessary.

## 23. Manual Discord Smoke

After automated validation and mirror deployment:

1. Direct `/me preferences` opens privately as a standalone premium card.
2. Avatar, duplicate-safe display name, privacy pill, profile coverage, local time/UTC offset, and
   full refreshed timestamp are correct.
3. A timezone crossing DST displays the correct current offset from the same refresh time.
4. Timezone unset produces UTC-reference copy without failure.
5. Public and private consequence copy matches actual supported Inventory behavior.
6. No VIP values, Update VIP button, direct visibility toggle, or Change Governor appears.
7. Navigation rows are Accounts/Reminders/Preferences, Dashboard/Exports, then Manage settings.
8. Manage Settings opens in place; profile save and field-specific clear behavior work; Back refreshes
   the parent.
9. Public/private confirmation, cancel, stale revalidation, and reflected host refresh work.
10. Manage Accounts exposes Update VIP; explicit governor and VIP selection save correctly; existing
    account tasks remain intact.
11. Selected-Dashboard return is preserved without filtering Preferences or preselecting VIP.
12. Timeout preserves the current private report, disables controls, and rejects later interactions.
13. Renderer/avatar/delivery failure uses the same-payload private fallback.
14. Desktop and mobile previews remain readable and premium.

Do not promote until operator smoke and visual acceptance pass.

## 24. Acceptance Criteria

- [ ] Repository audit maps the exact Preferences, profile, visibility, VIP, Accounts Manage,
      renderer/fallback, attachment, and timeout flows.
- [ ] Architecture and implementation plan are approved before coding.
- [ ] `/me preferences` is a private Discord-user Personal Settings page with no Change Governor.
- [ ] Successful output is a standalone `1702x924` PNG using
      `assets/me/cards/me_preferences.png` and stable filename.
- [ ] Invoking-user avatar, long-name fitting, duplicate-safe identity, and safe fallback work.
- [ ] Header shows `PRIVATE` or `PUBLIC` plus honest three-field profile coverage.
- [ ] Local-time hero uses one injected UTC clock, saved timezone semantics, DST-aware offset, and
      honest UTC fallback without live ticking or network calls.
- [ ] Regional Profile shows genuine friendly timezone/location/language values and honest unset or
      unavailable states.
- [ ] Privacy copy matches the exact existing Inventory visibility contract and does not imply that
      private direct `/me` reports become public.
- [ ] Exactly one deterministic Settings Insight follows the approved priority.
- [ ] Main controls are the approved navigation rows plus one `Manage settings` action.
- [ ] Manage Settings preserves existing save/clear persistence semantics, moves clear actions into
      field-specific flows, and confirms visibility changes.
- [ ] VIP values and editing are removed from Preferences.
- [ ] Existing Update VIP behavior is re-hosted inside Manage Accounts with explicit governor
      resolution and access recheck.
- [ ] Existing account management, profile persistence, visibility, VIP, report, export, Google
      Sheets, command, and legacy redirect contracts remain compatible.
- [ ] Same-payload fallback, off-loop rendering, attachment replacement, timeout preservation, and
      complete stream cleanup are tested.
- [ ] Focused/full validation, SQL contract validation, visual matrix, Codex Security review, PR
      review, operator smoke, and promotion checks are recorded.
- [ ] No new direct SQL exists in commands or views.
- [ ] No SQL deployment or data migration is required.
- [ ] Deferred findings are captured structurally without widening Phase 5E.
- [ ] Programme, briefing, canonical reference, task-pack/starter indexes, and next-phase handoff are
      updated.

## 25. Required Delivery Output

Provide:

1. Summary.
2. File Manifest.
3. New Files.
4. Modified Files.
5. SQL Changes and validation evidence.
6. Helpers Reused.
7. Product-contract confirmation and any approved deviations.
8. Refactor Findings.
9. Focused/full Test Plan and results.
10. Visual sample manifest.
11. Codex Security and K98 PR-review results.
12. Mirror deployment and operator smoke result.
13. Production promotion/deployment steps.
14. Rollback plan.
15. Deferred Optimisations.
16. Phase 5F handoff status.

## 26. Deployment And Rollback

Expected deployment shape:

- bot-code and documentation change only;
- approved production-size backdrop is already present at
  `assets/me/cards/me_preferences.png`;
- no SQL script, schema deployment, data migration, scheduler restart protocol, or external service
  change;
- normal mirror PR, review, mirror deployment, operator smoke, production PR, promotion check, bot
  deployment, and final smoke.

Rollback:

- revert the Phase 5E code/document changes;
- restore the previous Preferences renderer/action composition and Update VIP entry point if needed;
- the new backdrop may remain dormant without affecting persistence;
- no data rollback should be required because stored profile, visibility, and VIP contracts are
  unchanged.

## 27. PR Summary Template

```md
## Summary

- Rebuilt `/me preferences` as the premium GovernorOS Personal Settings card using the approved
  1702x924 Governor's Accord backdrop.
- Added deterministic saved-timezone local-time context, regional-profile coverage, exact Inventory
  privacy explanation, and one Settings Insight.
- Replaced the three main settings actions with one Manage Settings journey.
- Moved the existing governor-specific Update VIP editor into Manage Accounts without changing VIP
  persistence or account-management rules.

## Changes

- <typed Preferences summary and renderer>
- <parent/child view and attachment lifecycle changes>
- <Manage Settings profile/privacy controls>
- <Manage Accounts Update VIP re-host>
- <tests and docs>

## Tests

- <focused commands and counts>
- <full suite>
- <visual matrix>
- <operator smoke>

## AI Review Gates

- Codex Security: <scan id/result>
- K98 PR review: <result>
- Promotion check: <result or pending>

## SQL

- No SQL deployment. Existing profile, visibility, and GovernorInventoryProfile contracts validated
  against `C:\K98-bot-SQL-Server`.

## Deferred Optimisations

- None, or structured items only.

## Risk / Rollback

- Main risk is privacy-copy or interaction regression; rollback is a code-only reversion because no
  persisted contract or schema changed.
```

## 28. Remaining Phase 5 Handoff

After Phase 5E is operator accepted and archived, prepare separately:

- Phase 5F: Premium Inventory Summary Card;
- Phase 5G: Premium Exports Summary Card.

Neither phase inherits permission to change the profile, visibility, VIP, Accounts management, or
local-time contracts delivered here.
