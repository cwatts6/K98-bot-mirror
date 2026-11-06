# Codex Task Pack - Player Self-Service Command Centre v2 Phase 7 `/me` Visual Consistency, Content Audit and Programme Closeout

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 7 /me Visual Consistency, Content Audit and Programme Closeout`
- Date: `2026-07-19`
- Owner/context: `KD98 / Kingdom 1198 GovernorOS v2 follow-on from completed and operator-accepted Phase 6 Interactive Period Performance`
- Task type: `visual consistency | content audit | narrow renderer refactor | documentation | programme closeout`
- One-pass approved: `no`
- Product decision approved: `yes`
- Audit/design approved: `yes`
- Runtime implementation approved: `completed after the audit, visual-contract, implementation-plan, review, security, and operator gates in this pack`
- Status: `complete; final Discord smoke and operator visual acceptance passed on 2026-07-19`
- Reference surface: `/me stats`
- Command target: `no command registration change`
- SQL deployment approved: `no`
- Application-command resync required: `no`

## 2. Locked Programme Decisions

### 2.1 KVK history placement decision

The former proposed Phase 7 `/me history` implementation is closed with no build.

```text
/kvk history remains the canonical KVK-history command.
/me history will not be registered.
No redirect, alias, dashboard History action, or implicit handoff is added.
```

This decision must be recorded in the active programme pack, command reference, briefing, and task-pack
index. It is a product-placement decision, not an incomplete implementation.

### 2.2 Phase 7 purpose

Phase 7 is the final `/me` product-quality pass before the programme moves into the separate leadership
`/stats` family.

The accepted `/me stats` card is the visual and interaction reference because it is the newest
operator-accepted GovernorOS card and already carries the latest decisions for:

- typography hierarchy;
- state-pill placement and treatment;
- source-versus-generated freshness;
- compact numbers and signed deltas;
- blue primary navigation;
- same-payload fallback;
- deterministic rendering;
- transition safety;
- preserve-and-disable timeout;
- accessibility and mobile readability.

Phase 7 must improve consistency without reopening product ownership or adding new features.

## 3. Required Reading

Read and follow:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- this task pack
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 6 Interactive Period Performance and Legacy Command Retirement.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5D Premium Reminders Summary Card.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5E Premium Preferences Summary Card.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5B Premium Inventory Report Backdrops and Visual Alignment.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Inspect every retained runtime backdrop and renderer before proposing changes.

## 4. Objective

Deliver one coherent GovernorOS visual language across every retained `/me` card and same-payload
fallback while preserving each page's accepted purpose, data, dimensions, controls, privacy,
permissions, calculations, filenames, and lifecycle.

The result should feel intentionally designed as one product rather than a sequence of independently
completed cards.

This is not a redesign programme. It is a measured consistency and content-correctness pass.

## 5. Current Command Baseline

Phase 6 is complete and operator accepted.

```text
top-level commands: 37
grouped subcommands: 100
/me subcommands: 8
/inventory subcommands: 2
```

Canonical `/me` group:

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me resources
/me speedups
/me materials
/me stats
```

Phase 7 must leave these counts and paths unchanged.

## 6. Surfaces In Scope

### Core 1702x924 summary family

- `/me stats`
  - Overview
  - Activity
  - Combat
- `/me accounts`
- Account Summary
  - Overview
  - Combat
  - Economy
- `/me reminders`
- `/me preferences`

### Selected-governor dashboard

- `/me dashboard`
- Existing 1180x760 card
- Existing fallback
- Existing selected-governor navigation and Change Governor controls

### Selected-governor Inventory report family

- `/me resources`
- `/me speedups`
- `/me materials`
- Existing 1400x980 report-specific backdrops
- Existing tabs, ranges, exports, charts, no-data output, Dashboard return, and Change Governor controls

### Shared presentation and lifecycle

- same-authorized-payload fallbacks;
- page navigation labels;
- status/state pills;
- date/freshness wording;
- timeout wording;
- missing-value formatting;
- attachment replacement and cleanup;
- original, desktop, and mobile visual presentation.

## 7. Explicit Non-Goals

Phase 7 must not:

- add, remove, rename, redirect, or regroup a command;
- add `/me history`;
- add a History dashboard action;
- change `/kvk history`;
- add leadership inspection to `/me`;
- change any SQL object, DAL contract, query, cache, persistence, data source, metric, rank, formula,
  export, or account-resolution rule;
- change personal privacy or output visibility;
- change Dashboard, Accounts, Reminders, Preferences, Stats, or Inventory ownership;
- change governor-selection semantics;
- change the accepted timeout or stale/foreign-interaction rules except to fix a proven inconsistency;
- resize every card to one common canvas;
- replace report-specific Inventory accents with a generic palette;
- merge all renderers into one framework;
- perform a broad view or attachment-lifecycle refactor without directly proven, identical contracts;
- change public KVK or leadership command behaviour;
- introduce new player copy that changes product meaning.

A genuine typo, mislabeled unit, inaccessible contrast issue, clipped field, inconsistent missing-value
label, or stale historical copy may be corrected. Any change that alters data meaning or workflow
must be escalated and approved separately.

## 8. `/me stats` Reference Contract

The accepted Stats renderer is the default visual reference.

Reference colour tokens:

```text
TEXT       = (248, 251, 255, 255)
MUTED      = (190, 210, 235, 255)
BLUE       = (91, 190, 255, 255)
GOLD       = (255, 206, 92, 255)
GREEN      = (76, 225, 148, 255)
AMBER      = (255, 196, 78, 255)
RED        = (255, 132, 132, 255)
SHADOW     = (0, 0, 0, 190)
PANEL      = (3, 11, 27, 220)
PANEL EDGE = (91, 190, 255, 180), width 2
```

Reference geometry and hierarchy:

- circular invoking-user avatar in the top-left identity region where the page is Discord-user scoped;
- strong uppercase product title;
- prominent identity/scope line;
- right-aligned contextual mode/period text;
- right-hand state pill;
- large metric values;
- concise muted helper text;
- consistent panel border weight and radius;
- source freshness separated from generated time;
- blue current/primary navigation;
- complete text equivalents for charts and state.

The exact Stats absolute coordinates are not automatically copied to different canvas sizes. The
hierarchy, alignment logic, spacing rhythm, state semantics, and proportional placement are the
reference.

## 9. Visual Family Rules

### 9.1 Core summary cards

The 1702x924 summary cards should align closely on:

- outer margins;
- header baseline;
- avatar diameter and top-left safe zone;
- title and identity scale;
- state-pill top/right alignment;
- panel edge colour, width, and radius;
- metric label/value/helper hierarchy;
- section-heading colour and case;
- footer baseline;
- data-refresh and generated-time wording;
- navigation order and visual state.

Page-specific backdrops and information layouts remain.

### 9.2 Governor dashboard

Preserve the accepted 1180x760 canvas and selected-governor emphasis.

Align proportionally on:

- typeface and text-fitting behaviour;
- core GovernorOS text, muted, blue, gold, state, and panel semantics;
- label/value hierarchy;
- missing-value presentation;
- date and freshness formatting;
- border weight and radius;
- blue primary navigation.

Do not remove the larger governor avatar, selected-governor identity treatment, account type/VIP
self-view content, or Dashboard-specific action composition.

### 9.3 Inventory reports

Preserve:

- 1400x980 output;
- the three report-specific backdrops;
- item icons;
- chart layouts;
- Resources, Speedups, and Materials accent colours;
- 1M/3M/6M/12M ranges;
- report tabs;
- private exports;
- genuine upload dates;
- no-data guidance;
- Change Governor.

Align only common GovernorOS elements such as base typography, header identity, non-domain text
colours, border weight, date/number formatting, freshness wording, missing values, timeout copy, and
navigation.

## 10. Typography Contract

Use `core.visual_text` for glyph-safe font loading, fitting, width measurement, and embedded-colour
handling.

Audit and standardise the relative scale for:

1. product title;
2. primary identity;
3. scope or page context;
4. state pill;
5. section heading;
6. metric label;
7. metric value;
8. helper/supporting text;
9. chart labels;
10. footer.

Requirements:

- no renderer-local font-file discovery;
- no inconsistent bold measurement;
- no silent clipping;
- long Latin, CJK, combining-character, and emoji-containing names remain readable;
- no tiny helper text used to compensate for avoidable layout drift;
- no colour-only meaning;
- the same semantic level should not vary materially in size or weight between comparable cards.

## 11. State-Pill Contract

Standard visual treatment:

- dark translucent fill;
- semantic coloured outline;
- semantic or light text;
- rounded capsule;
- same relative top-right position within each card family;
- readable state text in addition to colour.

Semantic colours:

```text
GREEN  = ready, current, active, successful
BLUE   = neutral informational mode or selection
AMBER  = review, partial, stale, incomplete
RED    = no data, unavailable, failed
MUTED  = off, disabled, expired
```

Examples:

- Stats `READY` -> green
- Stats `PARTIAL` -> amber
- Preferences `LOCAL` -> green
- Preferences `UTC` -> blue, not warning amber
- Reminders `OFF` -> muted
- No-data/unavailable -> red
- Dashboard neutral context must not look like an error

The phase must audit whether each current state word has the correct semantic colour before changing
only its appearance.

## 12. Panel, Alignment and Spacing Contract

Audit:

- outer gutters;
- vertical section rhythm;
- panel corner radii;
- panel opacity;
- panel edge opacity and width;
- title and metric baselines;
- left/right alignment;
- card-to-card state-pill placement;
- consistent spacing between labels, values, and helpers;
- footer and navigation safe zones;
- chart legend alignment;
- long-content overflow treatment.

Do not add boxes where a page's approved backdrop intentionally provides the structure. Use the
Stats contract as the default and document deliberate exceptions.

## 13. Content Consistency Audit

### 13.1 Missing values

Use:

```text
—              missing individual value
Not recorded   source has never recorded the value and explanation matters
NO DATA        whole-card or whole-source healthy empty state
UNAVAILABLE    dependency/request failure
```

Remove inconsistent `N/A`, `None`, blank strings, and false zero values where they mean missing.

A genuine numeric zero must remain `0`.

### 13.2 Dates and freshness

Default UTC display:

```text
18 Jul 2026, 14:05 UTC
```

Keep separate:

- data refreshed;
- Stats source refreshed;
- Inventory uploaded;
- location updated;
- generated.

Do not replace source freshness with generation time.

### 13.3 Numbers and units

Audit:

- K/M/B suffix casing;
- decimal precision;
- signed deltas;
- percentages;
- days;
- minutes;
- Tech Donations as donations, not minutes;
- RSS labels;
- KP Loss;
- Tanking Score;
- singular/plural copy;
- current snapshot versus period change.

Do not change calculations in this phase.

### 13.4 Identity

- Discord-user/all-linked cards may show the invoking Discord identity.
- Selected-governor cards prioritise governor name and Governor ID.
- Preserve the existing duplicate-safe Kingdom suffix handling.
- Preserve self-view-only account slot/type and VIP where already approved.
- Do not add Discord identity to future leadership patterns.
- Do not show a player's Discord avatar on leadership cards.

### 13.5 Navigation and timeout copy

Standardise labels where they mean the same action:

```text
Dashboard
Back
Manage
Change Governor
Overview
Activity
Combat
Economy
Cancel
```

Primary/current navigation is blue. Secondary alternatives remain secondary. Destructive actions keep
explicit danger treatment.

Standard expiry pattern:

```text
Report controls expired. Run <canonical command> to refresh.
```

The last report remains visible and controls are disabled.

## 14. Narrow Shared Visual Contract

A small module may be introduced, for example:

```text
player_self_service/visual_contract.py
```

It may own:

- core colour tokens;
- typography scale;
- standard state semantic colours;
- panel tokens;
- date formatting;
- compact-number formatting;
- missing-value constants;
- bounded shared primitives for a header, pill, or panel only where contracts are identical.

It must not become:

- a universal renderer;
- a generic page/grid engine;
- a payload framework;
- a cross-domain data model;
- a broad view base class;
- a reason to force Dashboard or Inventory into Stats geometry.

Every extraction requires at least two proven identical consumers and focused tests.

## 15. Architecture And File Audit

At minimum inspect:

```text
player_self_service/stats_renderer.py
player_self_service/accounts_renderer.py
player_self_service/reminders_renderer.py
player_self_service/preferences_renderer.py
player_self_service/governor_dashboard_renderer.py
inventory/report_image_renderer.py
player_self_service/page_cards.py
ui/views/player_self_service_views.py
ui/views/player_self_service_governor_dashboard_views.py
ui/views/player_self_service_stats_views.py
ui/views/player_self_service_account_summary_views.py
ui/views/player_self_service_reminder_views.py
ui/views/player_self_service_preference_views.py
ui/views/player_self_service_inventory_report_views.py
core/visual_text.py
assets/me/cards/
assets/Inventory/cards/
```

Map:

- every renderer-local colour;
- every font size and fallback;
- every state-pill implementation;
- every panel primitive;
- every date/number formatter;
- every missing-value string;
- every card dimension;
- every stable filename;
- every fallback;
- every timeout and attachment transition;
- every current visual test and sample generator.

The audit must identify intentional product differences separately from accidental drift.

## 16. Visual Review Matrix

Create before-and-after contact sheets covering every retained card/page.

For each card/page render:

- fully populated;
- sparse/partial;
- honest no-data;
- long Latin name;
- CJK/Unicode name;
- emoji-containing name;
- avatar present;
- avatar absent/fallback;
- maximum realistic values;
- zero values;
- long supporting text;
- every state-pill variant.

Inspect at:

- original resolution;
- Discord desktop-style scaling;
- Discord mobile-style scaling.

The contact sheet must make header baselines, pill positions, panel edges, typography, avatar
treatment, and footer alignment easy to compare.

## 17. Functional Preservation

Phase 7 must prove no regression to:

- private/ephemeral delivery;
- access revalidation;
- selected Dashboard governor;
- All Linked Stats scope;
- account management;
- reminder management and scheduler parity;
- Regional Profile;
- Inventory report ranges/tabs/exports;
- chart values;
- filenames;
- fallback payload parity;
- stale/foreign interaction rejection;
- latest-transition-wins behaviour;
- preserve-and-disable timeout;
- file and stream cleanup.

## 18. Testing

Required focused tests include:

- approved output dimensions;
- opaque output;
- shared token use;
- state semantic mapping;
- date/number/missing-value formatters;
- long-name and Unicode fitting;
- deterministic image output;
- stable filenames;
- no clipped known bounding boxes;
- fallback content parity;
- attachment replacement;
- stream closure;
- timeout disabling controls while preserving the last card;
- no command-registration change;
- no SQL/DAL/service payload drift.

Avoid brittle whole-image equality as the only test. Prefer structural, geometry, token, text-fit, and
approved visual-snapshot tests.

Run the relevant focused suites, then:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
```

Run pytest log-noise analysis where required by repository instructions.

## 19. Security Routing

Phase 7 is presentation-focused but still processes user-controlled text, avatars, images, file
streams, and Discord interactions.

Provisional routing:

- bot repository final target: `Changes`, `Deep: Off`;
- focus on unbounded image/text input, attachment cleanup, stale interaction replacement, avatar
  handling, and any new shared primitive;
- SQL repository: documented skip because no SQL diff is approved;
- documentation-only preparation commit: documented skip if it contains no runtime/config/dependency
  change.

Do not start a standard or deep repository scan without explicit operator approval.

## 20. Workflow And Approval Gates

1. **Audit only.** Produce the full surface/token/typography/geometry/content/lifecycle inventory and
   deliberate-exception list. Stop for operator approval.
2. **Visual contract proposal.** Present the exact shared tokens, state semantics, reference scales,
   per-family geometry, file manifest, and before-contact sheet. Stop.
3. **Implementation plan.** Present file-by-file changes, tests, sample matrix, security target,
   rollback, and smoke. Stop.
4. Implement only after approval.
5. Run focused, visual, full, architecture, deferred, registration, import-smoke, pre-commit,
   log-noise, and security-routing validation.
6. Run the final Changes review with Deep off.
7. Complete PR review and operator original/desktop/mobile contact-sheet review.
8. Deploy without command resync.
9. Complete Discord smoke for each retained `/me` surface.
10. Record acceptance and close the `/me` programme presentation phase.

## 21. Operator Discord Smoke

At minimum verify:

- all eight `/me` commands;
- Dashboard no/one/multiple governor paths;
- Dashboard Change Governor;
- Accounts and all Account Summary pages;
- Reminders populated/no-upcoming/unavailable and Manage return;
- Preferences LOCAL/UTC and Manage return;
- Stats Overview/Activity/Combat, every period family, governor switching, All Linked, and timeout;
- Resources/Speedups/Materials populated/no-data, ranges, tabs, exports, Dashboard return, and Change
  Governor;
- fallback path for representative summary, Dashboard, Stats, and Inventory pages;
- desktop and mobile readability;
- no value, date, unit, state, or control changed incorrectly.

## 22. Rollback

Rollback is bot-code/assets/tests/docs only.

- restore the previous renderers and assets;
- redeploy/restart normally;
- no command resync;
- no SQL rollback;
- smoke the restored `/me` cards;
- do not roll back Phase 6 data/command behaviour.

## 23. Acceptance Criteria

- [x] The former `/me history` proposal is recorded as closed with no build.
- [x] All retained `/me` surfaces are inventoried.
- [x] Intentional visual differences are documented.
- [x] `/me stats` is the accepted default style reference.
- [x] Comparable summary cards align in typography, colour, spacing, borders, state pills, freshness,
      and navigation.
- [x] Dashboard and Inventory retain their approved dimensions and specialist layouts.
- [x] Missing values, dates, units, numbers, state semantics, and timeout wording are consistent.
- [x] No command, SQL, metric, permission, privacy, data, export, or workflow contract changes.
- [x] Same-payload fallbacks remain accessible and value-parity tested.
- [x] All image/file/stream lifecycle contracts remain safe.
- [x] Contact-sheet visual review passes at original, desktop, and mobile scales.
- [x] Focused/full/repository/security validation passes.
- [x] Operator Discord smoke passes.
- [x] Command counts remain `37 / 100 / 8 / 2`.
- [x] Phase 7 is archived after acceptance and Phase 8 becomes the next active task pack.

## 24. Delivery And Closeout Record

Status: `complete and operator accepted on 2026-07-19`.

Delivered without changing commands, SQL, DAL contracts, payload data, metrics, formulas, ranks,
permissions, privacy, exports, account resolution, or product ownership:

- aligned the retained `/me` visual family to the accepted Stats colour, type, panel, state,
  number/date, freshness, fallback, accessibility, transition, timeout, and cleanup language;
- introduced the bounded shared `core/visual_contract.py` primitives only where at least two
  renderers had identical consumers; no universal renderer, grid, payload, or view framework was
  created;
- kept Dashboard at `1180x760`, the core summary family at `1702x924`, and Inventory reports at
  `1400x980` with their report-specific backdrops, charts, icons, ranges, exports, and category
  accents;
- vertically centred state-pill text using font-bearing-aware placement across the family;
- completed row-0 cross-navigation: Accounts, Reminders, Preferences, and Stats are available on
  each applicable core page, while Stats page/mode controls begin on the next row;
- retained author gating, opaque duplicate-safe governor tokens, current-registry revalidation,
  selected-governor preservation, same-payload fallbacks, latest-transition-wins suppression,
  preserve-and-disable timeout, and deterministic attachment/file cleanup;
- left-aligned the Accounts hero metric headings while preserving right-aligned coverage/support
  copy;
- rebuilt Preferences into the accepted premium summary format: three regional-profile cards, a
  local-time panel, a settings-insight panel, and a Manage strip, with `LOCAL`/neutral-blue `UTC`
  semantics unchanged;
- preserved `/kvk history` as the only KVK-history route and added neither `/me history` nor a
  Dashboard History action.

Validation evidence:

- focused Phase 7 tests: `120 passed`;
- deterministic visual sample matrix: `143 renders passed`;
- full suite: `2701 passed, 2 skipped`;
- architecture, deferred-item, test-selection, security-routing, command-registration,
  pre-commit/pyright, and production-promotion validation passed;
- Codex Security Changes scan `7d78f323-bc7c-412c-b187-642ffe716289`: five of five discovery
  receipts complete, zero reportable findings;
- final Discord smoke accepted all retained surfaces, row-0 navigation, governor switching,
  fallback/lifecycle behaviour, and the revised Preferences and Accounts presentation.

Command-count proof remained unchanged throughout delivery:

```text
top-level commands: 37
grouped subcommands: 100
/me subcommands: 8
/inventory subcommands: 2
```

No application-command resync or SQL deployment was required. Mirror PR #229 and production PR
#536 contain the accepted Phase 7 delivery. Phase 8 is now the next active, separately gated slice.
