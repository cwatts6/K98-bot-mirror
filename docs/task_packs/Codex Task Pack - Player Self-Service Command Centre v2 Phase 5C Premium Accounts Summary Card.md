# Codex Task Pack - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card`
- Date: `2026-07-14`
- Owner/context: Follow-on from completed and operator-accepted GovernorOS v2 Phase 5B.
- Task type: `data/service/DAL | premium Accounts renderer | private Account Summary report | Discord interaction`
- One-pass approved: `Yes - within the locked product, data, visual, interaction, and compatibility contract below`
- Implementation approved: `Yes`
- Status: `implemented and locally validated - operator Discord smoke pending`
- Approved runtime backdrop: `assets/me/cards/me_accounts.png`
- Approved production canvas: `1702 × 924 PNG`

The visual/product workshop is complete. Do not reopen backdrop selection, information hierarchy,
metric selection, or Account Summary scope unless repository evidence reveals a genuine blocker.

## 2. Required Reading

Read before implementation:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5B Premium Inventory Report Backdrops and Visual Alignment.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 4 Premium Governor Dashboard Renderer.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 6 Guided Management Cards and Workflow Simplification.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- the GovernorOS Visual Design Bible where present in the repository

Use:

- `k98-architecture-scope`
- `k98-discord-command-feature`
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review`
- `codex-security:security-scan` when available

## 3. Context And Approved Direction

GovernorOS v2 Phases 1-5B are complete. Phase 4 established the premium standalone generated-card,
blue-navigation, same-payload fallback, attachment cleanup, and selected-governor contracts. Phase
5B applied the accepted visual standard to Inventory reports and passed operator smoke/final visual
acceptance on 2026-07-13.

`/me accounts` already provides a private, author-gated, all-linked-governor summary and a guided
`Manage` journey. The existing page is useful but behaves mainly as a registration receipt. Phase
5C upgrades it into a concise linked-governor portfolio: it confirms the registry, shows combined
scale, exposes data health, provides one deterministic portfolio insight, and adds a private detailed
`Account Summary` report.

The operator has completed and approved the product workshop. The approved clean backdrop is now in
the local repository at:

```text
assets/me/cards/me_accounts.png
```

It is exactly `1702 × 924`. It replaces the legacy space-containing path
`assets/me/cards/me accounts.png` for the Phase 5C renderer. Runtime must load the production-size
asset only. No source master is required by the bot.

## 4. Objectives

Deliver both of the following in one Phase 5C implementation:

1. A premium standalone `/me accounts` portfolio card using the approved backdrop and the locked
   content hierarchy below.
2. A new private, read-only `Account Summary` child journey covering every linked governor through
   readable paginated visual sections plus a complete CSV export.

Preserve the existing account-management journey, privacy model, navigation, fallback behavior,
author gating, attachment lifecycle, and registry authority.

## 5. Page Semantics And Governor Rule

- `/me accounts` represents the invoking Discord user's complete linked-governor registry.
- It is a Discord-user/all-linked-governor page, not a selected-governor page.
- It must never be filtered by an optional dashboard governor.
- It remains private/ephemeral and author-gated.
- Do not add `Change Governor`, including for users with more than 25 linked governors.
- `dashboard_governor_id` may be carried only as valid return context so `Dashboard` can reopen the
  previously selected governor after a fresh access check.
- Direct `/me accounts` entry has no implicit governor filter. Returning to Dashboard uses the
  existing no/one/multiple-governor resolution journey.
- `Account Summary` is also all-linked-governor scoped and must not introduce a governor selector.
- There is no player-facing maximum linked-governor count. Never display `linked / capacity` and do
  not hardcode the configured database slot ceiling into product copy or rendering behavior.

## 6. Locked Main Accounts Card

### 6.1 Approved hierarchy

The populated card should follow this hierarchy:

```text
ACCOUNT CENTRE                                           READY
<Discord display name> (1198)                       <N> governors
MAIN GOVERNOR  <main governor name> • <governor ID>

LATEST SNAPSHOTS

LINKED              PORTFOLIO POWER      T4+T5 KILLS       RSS TOTAL
<N>                 <compact total>      <compact total>   <compact total>
<role breakdown>    <scope/coverage>     <scope/coverage>  <scope/coverage>

LINKED GOVERNORS
SLOT     GOVERNOR                 ID             POWER          DATA
...

PORTFOLIO INSIGHT
<one short deterministic observation, no more than two clauses>

Manage accounts
Find an ID, add, replace or remove a linked governor.

Refreshed <DD Mon YYYY HH:MM UTC>
```

Use singular/plural grammar correctly, for example `1 governor` and `5 governors`.

### 6.2 Header and identity

Render:

- `ACCOUNT CENTRE`;
- the earned state pill: `READY`, `REVIEW`, or `SETUP`;
- the invoking Discord display name and fixed Kingdom 1198 context;
- the linked-governor count at the upper right;
- `MAIN GOVERNOR  <name> • <ID>` when a Main exists;
- an honest setup/missing-Main message when it does not.

The operator smoke refinement adds the invoking Discord user's best-effort avatar at the upper
left. Avatar reads remain author-validated and timeout-bounded; a failed read leaves the clean
header intact. If the Discord display name already ends in `(1198)`, do not append the Kingdom
suffix a second time.

### 6.3 Latest snapshot metrics

Render exactly four cards:

1. `LINKED`
2. `PORTFOLIO POWER`
3. `T4+T5 KILLS`
4. `RSS TOTAL`

Definitions:

- **Linked**: count of linked registry rows/governors for the invoking Discord user. Do not show a
  denominator or configured maximum.
- **Portfolio Power**: sum of the latest available Power value for each distinct linked Governor ID.
- **T4+T5 Kills**: sum of the latest cumulative T4 and T5 kill values for each distinct linked
  Governor ID. The label must not imply all kill tiers.
- **RSS Total**: sum of each linked governor's current RSS holdings using the exact canonical
  Inventory calculation already used by GovernorOS Inventory. It is current stock, not lifetime RSS
  gathered or assistance.

Recommended helper lines:

- Linked: `1 Main • 2 Alts • 2 Farms`, calculated from the real slot roles.
- Portfolio Power: `Latest snapshot • 5/5 reporting`.
- T4+T5 Kills: `Lifetime • 5/5 reporting`.
- RSS Total: `Current holdings • 5/5 reporting`.

Do not silently coerce missing source values to zero. Sum genuine available values and show honest
coverage such as `4/5 reporting`. If no values report, render `—` rather than a fabricated zero.
A genuine reported zero remains `0`.

### 6.4 Linked-governor roster

Use one full-width, five-column roster:

```text
SLOT | GOVERNOR | ID | POWER | DATA
```

Ordering:

1. Main first;
2. remaining entries in the existing authoritative slot order;
3. do not sort the default view by power or name.

Name behavior:

- display the latest scanned Governor name when available;
- fall back to the registered account name when scan data is unavailable;
- retain both registered and scanned names in the service payload so name changes can be reported
  honestly and exported.

Visible-row policy:

- when there are eight or fewer linked governors, show up to eight roster rows;
- when there are more than eight, show the first seven rows and use the eighth row for
  `+ <N> more linked governors — open Account Summary`;
- this is a display limit only, never a registration limit;
- `Account Summary` must cover all linked governors, including hundreds of accounts.

Use compact player-facing number formatting for Power while retaining exact values in the payload
and CSV.

### 6.5 Portfolio Insight

Render one deterministic insight line, normally no more than two clauses. Data-health observations
always outrank performance observations.

Priority:

1. stale, missing, unresolved, duplicate, or partial-reporting warning;
2. registered-name versus latest-scanned-name mismatch;
3. current RSS concentration;
4. power or T4+T5 kill composition;
5. role/activity leader such as RSS Assistance or Helps;
6. positive all-current fallback.

Approved example:

```text
Main holds 46% of linked power; Scrooge M leads RSS assistance.
```

Other valid templates include:

```text
1 linked governor is behind the latest scan; totals use 4/5 current records.
Farm accounts hold 68% of current RSS; Scrooge M holds the largest balance.
Main contributes 71% of T4+T5 kills; BlaizeP leads the non-Main accounts.
Registered name differs from the latest scanned name for 1 governor.
All 5 linked governors are current; 4 have City Hall 25.
```

Rules:

- never derive a comparative insight from missing or stale values without saying coverage is partial;
- require a positive denominator before calculating a percentage;
- use stable tie handling (`joint lead` or authoritative slot order) and test it;
- round displayed percentages to whole numbers;
- do not use kills-per-power or other ratios that mix lifetime and current measures;
- omit a second clause when there is no genuinely useful second observation.

### 6.6 Action explanation and footer

Keep the image copy:

```text
Manage accounts
Find an ID, add, replace or remove a linked governor.
```

Render:

```text
Refreshed <DD Mon YYYY HH:MM UTC>
```

`Refreshed` means the UTC date and time at which the card was generated/refreshed. It must not be
presented as the governor scan date. Per-governor scan date-times remain available through DATA
state and Account Summary.

## 7. Approved Backdrop Geometry

The renderer must compose around the approved `1702 × 924` asset and preserve these content zones:

| Zone | Coordinates |
|---|---|
| Header and status | `x 92–1610`, `y 48–138` |
| Identity | `x 92–1610`, `y 140–244` |
| Four latest-snapshot cards | `x 92–1610`, `y 258–402` |
| Architectural transition | `y 400–432` |
| Linked-governor roster | `x 92–1610`, `y 426–708` |
| Portfolio Insight | `x 92–1610`, `y 712–780` |
| Action explanation | `x 92–1610`, `y 784–854` |
| Footer | `x 92–1610`, `y 860–920` |

Suggested metric slots:

```text
Card 1: x 92–455
Card 2: x 477–840
Card 3: x 862–1225
Card 4: x 1247–1610
```

Do not paint fake buttons into the image. All interactive controls remain real Discord components.

## 8. Latest-Scan And DATA-State Contract

Kingdom 1198 is the only governor scan dataset used for this feature. A single global latest scan is
therefore authoritative; do not partition freshness by kingdom or source.

Conceptually:

```text
latest_scan_date
    = MAX(ScanDate) across the Kingdom 1198 governor dataset

governor_last_scan_date
    = MAX(ScanDate) for the linked Governor ID
```

Per-row DATA state:

| State | Rule |
|---|---|
| `CURRENT` | Governor's latest `ScanDate` equals the global latest `ScanDate`. |
| `STALE` | Governor has scan data, but its latest `ScanDate` is older than the global latest. |
| `NO DATA` | A structurally valid linked Governor ID has no usable scan row. |
| `UNRESOLVED` | The linked registry record or Governor ID cannot be resolved safely. |

Top-level pill:

- `READY`: a Main exists, linked Governor IDs are unique/resolved, and every linked governor is
  `CURRENT` in the latest Kingdom 1198 scan.
- `REVIEW`: one or more entries is stale, missing, unresolved, duplicated, or otherwise requires
  attention.
- `SETUP`: no governors are linked or no Main is configured.

Supporting text:

- healthy: `<N> governors`;
- review: `<current>/<linked> current`;
- setup: concise setup state such as `No governors` or `Main required`.

Inventory snapshot coverage affects the RSS metric helper and summary economy fields, but it does
not redefine the Kingdom 1198 DATA state. Do not mark a governor scan `STALE` merely because its
Inventory snapshot is unavailable.

When duplicate linked Governor IDs exist, surface `REVIEW`, do not double-count them in portfolio
metrics, and preserve enough row-level detail for the operator to diagnose the registry issue.

## 9. Data And Service Contract

### 9.1 Approved scope expansion

Phase 5C is no longer presentation-only. Read-only service/DAL/payload expansion is explicitly
approved for the fields required by the main portfolio card and Account Summary.

No SQL schema, table, index, persistence, account-slot, ownership, claim, mutation, or registry-rule
change is approved or expected. Validate all SQL-facing field names and source objects against:

```text
C:\K98-bot-SQL-Server
```

If an approved field has no authoritative existing source, stop and report that field-specific
blocker. Do not invent, estimate, or silently drop it.

### 9.2 Recommended typed models

Prefer new cohesive service-level models rather than inflating a legacy renderer-specific object:

```text
AccountsPortfolioPayload
- viewer_discord_id
- display_name
- kingdom_id
- generated_at_utc
- latest_scan_date
- state: READY | REVIEW | SETUP
- state_supporting_text
- linked_count
- role_counts
- main_governor
- portfolio_power
- portfolio_power_coverage
- t4_t5_kills
- t4_t5_coverage
- rss_total
- rss_coverage
- roster_rows
- hidden_roster_count
- portfolio_insight
- missing_fields / warnings

LinkedGovernorPortfolioRow
- slot
- role
- slot_order
- registered_name
- governor_name
- governor_id
- civilization
- city_hall
- power
- troop_power
- kill_points
- t4_kills
- t5_kills
- t4_t5_kills
- deads
- healed_troops
- highest_acclaim
- helps
- rss_gathered
- rss_assistance
- rss_total
- conduct
- location_x
- location_y
- last_scan_date
- inventory_as_of
- data_state
- missing_fields

AccountSummaryPayload
- portfolio header/aggregate values
- all linked rows
- generated_at_utc
- exact export metadata
```

Names may follow repository conventions, but the responsibility split must remain equivalent.

### 9.3 Source direction

| UI/data field | Authoritative source direction |
|---|---|
| Slot, role, Main, registered name, linked count | Existing Discord-governor registry/service |
| Global latest scan | `MAX(ScanDate)` across the Kingdom 1198 governor scan dataset |
| Current governor name and last scan | Latest usable scan row for that Governor ID |
| Civilisation | Existing `Civilization` source/mapping; player-facing label may use `Civilisation` |
| Power, City Hall, Troop Power, Kill Points | Latest governor scan/profile source already used by GovernorOS |
| VIP | Existing `dbo.GovernorInventoryProfile.VipLevelCode/VipLevelLabel` profile source |
| T4 and T5 kills | Latest cumulative T4/T5 fields; sum only those two tiers |
| Deads, Healed Troops, Highest Acclaim, Helps | Latest authoritative governor scan/profile fields |
| RSS Gathered, RSS Assistance | Existing cumulative/lifetime governor fields |
| RSS Total | Exact canonical current-holdings calculation from Inventory |
| Conduct | SQL/source field `Conduct`; use existing player-facing formatter |
| Location | Current `PlayerLocation.X` and `PlayerLocation.Y` source already used by GovernorOS |
| Inventory As Of | Timestamp of the Inventory snapshot used for that governor |
| KP Loss | Calculated from exact Healed Troops as `Healed Troops * 20` |
| Tanking Score | Calculated as `Kill Points / (KP Loss + Deads) * 100`; null for missing/zero denominator |

Do not duplicate the Inventory RSS formula in a new renderer or view. Reuse/extract the canonical
Inventory calculation through an appropriate service boundary.

### 9.4 Query and assembly requirements

- Resolve all linked governors from the authoritative registry at request time.
- Use set-based/bulk reads. Do not issue one SQL query per linked governor.
- Design for portfolios ranging from zero to hundreds of accounts.
- Avoid assumptions tied to Discord's 25-option select limit; this journey uses rows/pagination, not
  a governor selector.
- Use the latest usable row per Governor ID and one global latest scan value.
- Keep exact numeric values in models and CSV; compact formatting belongs in rendering.
- Preserve nulls. Missing is not zero.
- Deduplicate metric aggregation by Governor ID while preserving duplicate registry rows as a
  `REVIEW` warning.
- Reuse current access, registry, Inventory, and visual-number-formatting services where possible.
- Keep commands and views thin; no direct SQL in Discord callbacks or renderers.

## 10. Account Summary Child Journey

### 10.1 Entry and purpose

Add a second Accounts page action:

```text
[ Manage Accounts ]  [ Account Summary ]
```

`Account Summary` is private, author-gated, read-only, and covers every governor currently linked to
the invoking Discord user. Disable it when no governors are linked. It must not alter account
registry state.

### 10.2 Presentation

Use the same approved `assets/me/cards/me_accounts.png` backdrop and `1702 × 924` canvas for the
visual summary pages. Deliver each successful page as a standalone private attachment.

The summary repeats a compact portfolio header:

```text
ACCOUNT SUMMARY                                      READY
<N> governors
<Power>    <Troop Power>    <T4+T5 Kills>    <RSS Total>
```

Then render one of three sections.

#### Overview

```text
Slot
Governor
Civilisation
City Hall
VIP
Power
Troop Power
Location (X:Y)
Last Scan
```

When registered and latest-scanned names differ, show the current Governor name as primary and the
registered name as a restrained secondary note, subject to fitted bounds.

#### Combat & Participation

```text
Slot
Governor
Kill Points
T4+T5 Kills
Deads
Healed Troops
Highest Acclaim
KP Loss
Tanking Score
Conduct
```

#### Economy & Activity

```text
Slot
Governor
RSS Gathered
RSS Assistance
RSS Total
Helps
Inventory As Of
```

Scope labels must remain honest:

- Kill Points, T4+T5 Kills, Deads, Healed, RSS Gathered, and RSS Assistance are cumulative/lifetime
  values where that is the actual source contract.
- RSS Total is current holdings.
- `Inventory As Of` identifies the Inventory snapshot used.
- `Last Scan` identifies the governor scan, not the card render time.
- `Last Scan` and `Refreshed` include both UTC date and time.
- Summary tables use compact player-facing values; exact values remain in the CSV.

### 10.3 Pagination

- Render at most eight governor rows per visual page.
- Main remains first, followed by authoritative slot order.
- Section changes reset to page 1.
- Previous/Next buttons page through all linked governors without a hard maximum.
- Show `Page X of Y` and the total governor count.
- Empty and partial pages remain honest; do not create dummy rows.
- For a 500-account portfolio, every linked row must remain reachable through pagination and the CSV.

### 10.4 Aggregate row/header rules

Use portfolio totals only for genuinely additive fields:

- `SUM`: Power, Troop Power, Kill Points, T4+T5 Kills, Deads, Healed Troops, Helps, RSS Gathered,
  RSS Assistance, and RSS Total.
- `MAX`: Highest Acclaim.
- `COUNT/GROUP` only when useful: Civilisations, City Hall levels, Conduct states.
- Never aggregate names, Governor IDs, coordinates, scan dates, or Inventory timestamps.
- Never replace a missing member value with zero merely to complete a total.

### 10.5 Complete CSV export

Provide a private `Download CSV` action from Account Summary. The CSV is the definitive complete
report and contains one row per linked registry entry with these columns in this order:

```text
Slot
Role
Registered Name
Current Governor Name
Governor ID
Civilisation
City Hall
VIP
Power
Troop Power
Kill Points
T4 Kills
T5 Kills
T4+T5 Kills
Deads
Healed Troops
KP Loss
Tanking Score
Highest Acclaim
Helps
RSS Gathered
RSS Assistance
RSS Total
Conduct
Location X
Location Y
Data State
Last Governor Scan
Inventory As Of
```

Requirements:

- no duplicate `Helps` column;
- exact, non-compact numeric values suitable for analysis;
- UTF-8 CSV using the repository's established export conventions;
- safe formula-injection handling for user-controlled text cells;
- stable, filesystem-safe filename following existing private export conventions, recommended:
  `account_summary_<discord_user_id>_<UTC timestamp>.csv`;
- send as a private follow-up so downloading does not destroy the visual summary state;
- close the file/stream on success and every failure path.

### 10.6 Summary controls

Retain global navigation and use real Discord controls. Recommended rows:

```text
Row 0: Accounts (blue, disabled) | Reminders (blue) | Preferences (blue)
Row 1: Dashboard | Exports
Row 2: Overview | Combat | Economy
Row 3: Previous | Next | Download CSV | Back to Accounts
```

Rules:

- active section is disabled;
- Previous/Next are disabled at boundaries;
- `Download CSV` is disabled with no linked rows;
- `Back to Accounts` returns to the host portfolio card;
- no `Change Governor` control appears anywhere in the journey;
- every callback rechecks author/view validity and safely suppresses stale or forged interactions.

## 11. Main Accounts Component Rows

The main card uses:

```text
Row 0: Accounts (blue, disabled) | Reminders (blue) | Preferences (blue)
Row 1: Dashboard | Exports
Row 2: Manage Accounts | Account Summary
```

`Manage Accounts` preserves the existing guided management journey. `Account Summary` opens the
new read-only report. Do not paint either button into the PNG.

## 12. Renderer And Delivery Contract

### 12.1 Main card

- Output: exactly `1702 × 924`.
- Runtime backdrop: `assets/me/cards/me_accounts.png`.
- Stable filename: `me_accounts_<discord_user_id>.png`.
- Successful output: standalone private attachment, not an embed-wrapped image.
- Fallback: concise private Accounts embed built from the same already-authorized portfolio payload.
- On timeout, preserve the existing private card/fallback, disable every control, and add a concise
  rerun instruction without refetching or rerendering.

### 12.2 Account Summary pages

- Output: exactly `1702 × 924`.
- Runtime backdrop: the same approved Accounts asset.
- Stable attachment filename: `me_account_summary_<discord_user_id>.png`.
- Successful output: standalone private attachment.
- Fallback: concise private embed/text representation of the current section/page from the same
  already-loaded summary payload. Do not attempt to place hundreds of rows in one fallback embed.
- On timeout, preserve the current private page, disable every control, and add a concise `/me
  accounts` rerun instruction without refetching or rerendering.

### 12.3 Shared renderer requirements

- Render off the event loop.
- Use deterministic Pillow output.
- Reuse `core.visual_text` and existing glyph/grapheme-safe fitting helpers where appropriate.
- Fit long Discord names, governor names, large totals, and `X:Y` values within fixed bounds.
- Use honest `—`, `NO DATA`, and partial-coverage treatments.
- Do not create a broad new visual-card framework or import renderer-private helpers across families.
- Replace prior attachments deliberately on every in-place transition.
- Do not refetch data merely because avatar loading, rendering, file creation, message edit, or
  delivery fails.
- Close every image/file/CSV stream on success, fallback, timeout, cancellation, stale suppression,
  navigation, and exception paths.

## 13. Existing Manage Journey - Preserve Exactly

`Manage Accounts` continues to provide the existing private guided journey for:

- Governor ID/name lookup;
- add/register;
- replace;
- remove;
- confirmation and cancellation;
- current-state revalidation immediately before mutation;
- ownership/claim and slot rules;
- audit behavior;
- mutation result wording;
- host Accounts-card refresh after a successful change.

Foreign, stale, forged, timed-out, cancelled, duplicate, and concurrent actions remain privately
denied or safely suppressed. Phase 5C may adapt the host refresh to the new standalone card and new
payload, but it must not redesign the guided workflow or mutate its business rules.

## 14. Architecture Direction

- Keep command callbacks thin.
- Keep linked-registry resolution, latest-scan assembly, aggregation, coverage, state derivation,
  insight selection, summary rows, and CSV data preparation in services/domain helpers.
- Keep SQL access in DAL/repository layers.
- Keep Discord routing, component state, author gating, timeout behavior, and message edits in views.
- Keep visual composition in the established page-card renderer or a narrow Accounts-specific
  renderer if that produces clearer boundaries.
- Reuse existing attachment cleanup, fallback, number formatting, Inventory RSS, and access helpers.
- Do not create a broad renderer/view framework as part of Phase 5C.
- Do not load the source asset through user-controlled paths.

## 15. SQL, Persistence, Privacy, And Security

Approved SQL-facing scope:

- read-only query/DAL expansion needed to obtain the approved latest governor fields in bulk;
- read-only reuse/bulk access for canonical current Inventory RSS totals;
- current `PlayerLocation` lookup in bulk where needed.

Not approved:

- schema/table/view/index changes without a new explicit checkpoint;
- writes outside the existing Manage workflow;
- account-slot, registry-authority, ownership, claim, lookup-matching, or persistence redesign;
- public delivery of the card, Account Summary, CSV, or coordinates.

Security requirements:

- all output remains private/ephemeral and author-gated;
- re-resolve the invoking user's current linked registry before loading Account Summary;
- never trust component-provided Governor IDs as authorization;
- protect CSV cells from formula injection;
- sanitize filenames and never derive local paths from user-controlled names;
- cap/validate rendered text and payload sizes for very large portfolios;
- do not log private coordinates, full CSV contents, or unnecessary account values;
- run Codex Security review because private multi-account data, coordinates, user-controlled names,
  SQL reads, attachments, CSV, and guided mutations are in scope.

## 16. Compatibility Contract

- `/me accounts` remains private and all-linked-governor scoped.
- Existing legacy redirects to `/me accounts` remain unchanged.
- Command registration and top-level command count remain unchanged.
- A version-only command metadata increment is permitted if repository conventions require it.
- Existing Accounts/Reminders/Preferences and Dashboard/Inventory/Exports navigation remains.
- No Change Governor on Accounts or Account Summary.
- The guided Manage journey remains behaviorally unchanged.
- The successful card moves from embed-wrapped image to standalone attachment.
- Same-payload fallback, attachment replacement, and stream cleanup remain mandatory.
- No change to other `/me` pages, direct Inventory reports, `/myinventory`, existing export schemas,
  Inventory imports, Google Sheets behavior, public `/kvk`, or leadership inspect.

## 17. Do Not Do In Phase 5C

- No configured account-capacity display or artificial governor maximum.
- No account slot, claim/ownership, lookup matching, mutation, confirmation, or registry redesign.
- No SQL schema, table, view, index, cache, scheduler, startup, or persistence change without a new
  approval gate.
- No Change Governor.
- No Reminders, Preferences, Inventory summary, Exports summary, Dashboard, direct Inventory report,
  Export Stats, History, Inspect, Last Login, Olympia, CrystalTech, website/API, or public `/kvk`
  change.
- No public Account Summary or coordinate disclosure.
- No fake data, dummy rows, invented totals, estimated RSS, fabricated insight, or decorative controls.
- No broad renderer/view framework.

## 18. Test Strategy

### 18.1 Data/service tests

Cover:

- zero, one, five, eight, nine, more-than-25, and 500 linked governors;
- Main first and authoritative slot ordering;
- no configured Main;
- duplicate linked Governor IDs;
- global `MAX(ScanDate)` across the single Kingdom 1198 dataset;
- CURRENT, STALE, NO DATA, and UNRESOLVED derivation;
- READY, REVIEW, and SETUP derivation and supporting text;
- latest row selection per Governor ID;
- distinct-ID aggregation without double counting duplicates;
- role breakdown singular/plural formatting;
- Portfolio Power, T4+T5 Kills, and canonical RSS Total calculations;
- missing values versus genuine zero and accurate reporting coverage;
- current RSS not confused with lifetime RSS Gathered/Assistance;
- deterministic insight priority, percentages, ties, zero denominators, and partial coverage;
- registered-name/current-name mismatch;
- set-based/bulk DAL behavior with no N+1 call pattern;
- DAL/Inventory-source failure degradation.

### 18.2 Renderer tests

Cover:

- exact `1702 × 924` dimensions;
- exact approved backdrop path;
- stable main and summary filenames;
- four and only four metric cards;
- full-width roster and seven-plus-overflow treatment;
- long/Unicode Discord and governor names;
- very large numbers;
- CURRENT/STALE/NO DATA/UNRESOLVED labels;
- best-effort invoking-user avatar, failed-read fallback, and duplicate `(1198)` suffix prevention;
- empty, partial, unavailable, and all-current samples;
- Account Summary Overview, Combat, and Economy samples;
- eight-row pagination pages;
- original-size, normal Discord desktop, and mobile previews.

### 18.3 View/interaction tests

Cover:

- standalone successful delivery and same-payload fallback;
- exact main component rows and button labels;
- Account Summary entry, tabs, boundary-disabled pagination, CSV, and Back to Accounts;
- graceful main/summary timeout preserving the report while disabling controls;
- no Change Governor for one, multiple, more-than-25, and 500 governors;
- direct `/me accounts` entry and selected-dashboard-to-Accounts-to-Dashboard return;
- unchanged Manage lookup/add/replace/remove/confirm/cancel/revalidation;
- successful mutation refresh using the new host payload/card;
- foreign, forged, stale, timed-out, cancelled, duplicate, and concurrent interactions;
- renderer/file/edit/delivery failure without a second data fetch;
- attachment replacement and stream cleanup across every transition;
- CSV formula-injection handling, private follow-up, filename, column order, Unicode, and cleanup;
- summary fallback limited to the current section/page rather than oversized output.

### 18.4 Regression and repository gates

Include existing page-card, player-self-service view, account service, Inventory service, UI import,
command registration, legacy redirect, and attachment cleanup regressions.

Run the repository-prescribed focused selection plus:

```powershell
.\.venv\Scripts\python.exe scripts/validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts/validate_deferred_items.py
.\.venv\Scripts\python.exe scripts/select_tests.py
.\.venv\Scripts\python.exe scripts/smoke_imports.py
.\.venv\Scripts\python.exe scripts/validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts/analyse_pytest_log_noise.py
```

## 19. Manual Discord Smoke

After automated validation:

1. Direct `/me accounts` opens privately as a standalone premium card with the approved backdrop.
2. Header, Main, governor count, four metrics, coverage, role breakdown, roster, insight, and footer
   match genuine data.
3. CURRENT/STALE/NO DATA/UNRESOLVED and READY/REVIEW/SETUP states are exercised.
4. Zero, one, five, more-than-eight, more-than-25, and a large synthetic portfolio remain readable
   and operational.
5. `Manage Accounts` lookup/add/replace/remove/cancel/confirm remains correct.
6. A successful mutation refreshes totals, states, roster, insight, and attachment without stale files.
7. `Account Summary` opens Overview, Combat, and Economy privately.
8. Summary pagination reaches every account, preserves section state, and handles boundaries.
9. CSV contains every linked row, exact approved columns, safe text, and genuine values.
10. Coordinates appear only in the private summary/CSV.
11. Dashboard return preserves valid selected context when entered from Dashboard; direct entry uses
    normal Dashboard governor resolution.
12. Change Governor is absent everywhere in Accounts and Account Summary.
13. Main and summary fallback, timeout, foreign, stale, concurrent, render failure, edit failure, and
    stream cleanup paths are safe.
14. Original-size, Discord desktop, and Discord mobile presentation are accepted.

## 20. Acceptance Criteria

- [x] Approved `assets/me/cards/me_accounts.png` is loaded at exactly `1702 × 924`.
- [x] Main Accounts output is a standalone private PNG with stable filename.
- [x] The approved header and `LATEST SNAPSHOTS` hierarchy is implemented.
- [x] Exactly four metrics are shown: Linked, Portfolio Power, T4+T5 Kills, and RSS Total.
- [x] No account-capacity denominator or arbitrary maximum is displayed.
- [x] RSS Total reuses the canonical current Inventory holdings calculation.
- [x] Latest-scan and DATA-state logic uses one global Kingdom 1198 `MAX(ScanDate)`.
- [x] READY/REVIEW/SETUP is earned from the approved registry/scan rules.
- [x] The full-width roster, overflow row, and deterministic Portfolio Insight are implemented.
- [x] `Manage Accounts` remains behaviorally unchanged and refreshes the new host card.
- [x] `Account Summary` provides private Overview, Combat, and Economy visual pages for all governors.
- [x] The complete private CSV contains the approved columns once each and exact values.
- [x] No Change Governor appears on Accounts or Account Summary.
- [x] Read-only DAL/service/payload expansion is set-based and validated against the SQL repository.
- [x] No SQL schema, persistence, registry-authority, ownership, or mutation redesign is introduced.
- [x] Same-payload fallbacks, attachment replacement, and all stream cleanup paths are tested.
- [ ] Focused/full validation, security review, visual samples, and operator Discord smoke are recorded.
- [x] Programme, briefing, canonical, task-pack, starter, and deferred documents reflect delivery.

## 20A. Implementation And Validation Evidence

- Branch: `codex/phase-5c-premium-accounts-summary` against the scrubbed mirror.
- SQL contract: Kingdom 1198 scan, location, civilisation, registry, and Inventory sources were
  checked against `C:\K98-bot-SQL-Server`; no schema, view, index, or persistence change was needed.
- Focused/selected validation: 189 tests passed. Full regression: 2,521 passed and 2 skipped.
- Repository gates: architecture boundaries, deferred-item structure, selected-test analysis, smoke
  imports, and command registration all passed; Ruff passed and Pyright reported no errors.
- Visual QA: main Accounts and all three Account Summary sections were rendered at original,
  Discord desktop, and Discord mobile sizes under the task's Codex visualization directory.
- Codex Security: repository-wide ranked review plus explicit Phase 5C privacy, authorization, SQL,
  CSV, filename, attachment, and stream-lifetime coverage was run. Any unrelated repository finding
  is recorded separately and is not silently folded into this feature scope.
- Remaining gate: operator Discord smoke against the mirror PR. Do not promote or deploy before it
  passes.

## 21. Remaining Decisions And Escalation Gates

There are no known blocking product or visual decisions.

Stop and ask the operator only if repository inspection proves one of the following:

- an approved field has no authoritative existing source;
- canonical Inventory RSS cannot be reused without changing its business definition;
- a SQL schema/view/index change is required rather than a read-only query/DAL expansion;
- the approved backdrop is absent, corrupted, or not exactly `1702 × 924`;
- Discord component limits or mobile validation make the locked interaction/layout impossible without
  changing the product contract;
- existing registry semantics make the approved Main/role/slot ordering ambiguous.

Do not silently omit a field, substitute a different metric, add a fifth headline card, introduce an
account-capacity denominator, or redesign Manage to work around a blocker.

## 22. Remaining Summary-Card Handoff

After Phase 5C completes, execute separately:

- Phase 5D: Premium Reminders Summary Card
- Phase 5E: Premium Preferences Summary Card
- Phase 5F: Premium Inventory Summary Card
- Phase 5G: Premium Exports Summary Card

Each page reuses the accepted standalone/fallback/navigation discipline but receives its own
page-specific content, asset, data, and action approval. None shows Change Governor.
