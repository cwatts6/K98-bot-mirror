# Codex Task Pack - KVK Player Experience Redesign Phase 4B History Audit and Optioneering

## 1. Task Header

- Task name: `KVK Player Experience Redesign - Phase 4B History Audit and Optioneering`
- Date: `2026-06-06`
- Owner/context: `K98 Bot KVK Player Experience Redesign programme after Phase 4A targets rollout`
- Task type: `feature discovery / UX audit / architecture scope / Discord interaction design / staged implementation plan`
- One-pass approved: `no`
- Status: `Phase 4Bi and Phase 4Bii delivered, merged, and pushed to production; Phase 4Biii remains outstanding`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by
`docs/reference/README.md`. Do not add every reference document by default.

Also read:

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/task_packs/KVK Player Experience Redesign - Phase 1 Audit and Design Report.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3 Modern mykvkstats Visual Card.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3B Stats Card Polish and Secondary Cards.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3C Overall Rank and Card Polish.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 4 Modern Targets and Full History.md`
- `docs/reference/canonical_command_reference.md` if command descriptions or command-surface notes change

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

`C:\K98-bot-SQL-Server`

## 3. Objective

Audit and redesign the full KVK history player journey, then implement it in controlled
sub-phases.

The approved direction is:

- `/kvk stats` should be the live current-KVK performance journey.
- `/kvk history` should become the modern past-performance and trend-analysis journey.
- `/mykvkhistory` should retain the legacy chart/table/CSV output during player validation so the
  modern no-graph journey can be compared safely against the existing graph journey.

The final solution should help players understand historical KVK performance clearly, using modern
cards for the common player questions and CSV export for deeper data review. Do not force graph
output into the modern `/kvk history` path unless player validation proves it is still needed.

## 4. Background

Phase 4A completed the modern `/kvk targets` journey in PR #145 and promoted it to production.
History was deliberately deferred because the existing output is a different kind of experience:

- A chart embed with dual-axis metric plotting.
- A generated chart image.
- A separate data/table image.
- Account selection.
- Metric buttons such as `Kills vs %`, `Deads vs %`, `DKP vs %`, and `Custom...`.
- CSV export.
- Last 3 / Last 6 / Last 10 table-range controls.

The user-provided current-output screenshot and the completed audit should be used as design input.
The current output is graph-first, but the approved product direction is to test whether players
prefer a clearer card-based past-performance journey without graphs.

The compact History card attached to `/kvk stats` is already modernised, but Phase 4B should move
that historical context into `/kvk history`. After Phase 4B, `/kvk stats` should keep only current
KVK-focused cards: `Main Card` and `More Stats`.

## 4A. Phase 4B Audit Decision Update

Audit and optioneering have completed. The approved approach is a staged modern history redesign:

- Make `/kvk history` the modern card-based history journey.
- Keep `/mykvkhistory` on the existing chart/table/CSV output for side-by-side player testing.
- Do not add `/kvk history_chart` initially; the legacy `/mykvkhistory` path already preserves the
  graph journey during validation.
- Retain explicit `governor_id` lookup on `/kvk history` so admin/leadership can inspect other
  players.
- Use the same player account picker pattern as `/kvk stats` and `/kvk targets` where practical.
- Keep CSV export and expand it where useful so Last 6, Last 10, Last 12, and full history needs are
  serviced by export data rather than by overloading the default card.
- Define `last 3 KVKs` as the current started KVK plus the previous two started KVKs. For example,
  if KVK 15 has started, last 3 is KVK 13, KVK 14, and KVK 15. If KVK 15 has not started, last 3 is
  KVK 12, KVK 13, and KVK 14.
- Treat missing metrics as missing, not zero, especially for Acclaim and healed troops because
  those values only exist for recent KVKs.
- Honor and PreKVK were excluded from the original row-by-row history design, but Phase 4Bii
  intentionally added them as Summary-card personal-best records where data exists. Do not add
  row-by-row Honor/PreKVK trend output in Phase 4Biii unless explicitly approved.
- Show Acclaim as a raw KVK metric for now. Do not show `Acclaim vs Target%` until a real
  per-KVK acclaim target contract exists.

New background assets added for Phase 4B cards:

| Asset | Intended Use |
|---|---|
| `assets/kvk/cards/history_card1.PNG` | Main `/kvk history` Last 3 KVK performance card. |
| `assets/kvk/cards/history_card2.PNG` | Moved history-summary card formerly attached to `/kvk stats`. |
| `assets/kvk/cards/history_card3.PNG` | History Trends card. |

## 4A.1 Phase 4Bi Delivery Update - 2026-06-17

Phase 4Bi is complete. It was delivered in mirror PR #148 on branch
`codex/phase-4bi-history-foundation`, smoke tested successfully, merged, and pushed to production.

Delivered scope:

- Added renderer-independent history payload models and service shaping.
- Added the expanded, null-preserving modern history data/export contract.
- Validated the SQL-facing history contract against `dbo.v_EXCEL_FOR_KVK_Started`, backed by
  `dbo.v_EXCEL_FOR_KVK_All` and `dbo.KVK_Details`.
- Preserved SQL access in `kvk/dal/kvk_history_dal.py` and service layers only.
- Selected Last 3 KVKs from started-KVK logic.
- Preserved missing/null distinction for modern payload rows, including Acclaim.
- Prepared `/kvk history` for shared single-governor picker flow while retaining explicit
  `governor_id` lookup.
- Kept `/mykvkhistory` on the legacy chart/table/CSV journey for player comparison.
- Preserved and expanded CSV export with the modern history column set.
- Included the Phase 4B task-pack/archive updates and the three history card assets.
- Addressed code-review hardening for exact BIGINT-safe integer parsing and no-account picker
  ephemeral consistency.
- Addressed smoke-test feedback by trimming SQL-padded governor names in history display/export
  paths.

Validated smoke-test result:

- `/kvk history` with registered accounts works as before.
- `/kvk history governor_id:<id>` now displays trimmed governor names in the legend and data table.
- `/mykvkhistory` remains unchanged and works as expected.
- `/kvk history` CSV export succeeds and emits trimmed governor names.
- Channel and permission behaviour tested successfully.
- No runtime log errors observed during smoke testing.

Validation evidence from PR #148:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_history_service.py tests\test_kvk_cmds.py tests\test_kvk_history_offload_and_utils.py tests\test_validate_command_registration.py
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
git diff --check
```

Known unrelated validation note:

- `tests/test_ui_imports.py` has an existing unrelated failure because the test stubs `utils`
  without `parse_last_refresh_utc`, causing `build_KVKrankings_embed.py` import failure. This is
  outside the history Phase 4Bi delivery surface.

Phase 4Bii is delivered, merged, and pushed to production.

## 4A.2 Phase 4Bii Implementation Update - 2026-06-17

Phase 4Bii has been delivered, merged, and pushed to production.

Delivered scope:

- Added a dedicated modern history renderer for `KvkHistoryPayload`.
- Built the main `/kvk history` Last 3 KVK card using `history_card1.PNG`.
- Updated Last 3 ordering to descending/newest-started first and changed the title to
  `Last 3 KVKs`.
- Matched the card-native text-on-background style used by the other KVK cards, removing the
  unnecessary boxed row treatment.
- Added healed values to Last 3 rows where collected.
- Kept historically uncollected or missing acclaim/healed values blank instead of rendering
  misleading zeroes.
- Added a visual kills-trend indicator alongside the trend label.
- Added and redesigned the moved history Summary card using `history_card2.PNG`.
- Summary now uses a 3x4 record layout:
  - Row 1: Highest Rank, Autarchs, KVK Played, Highest Acclaim.
  - Row 2: Most Kills, Most KillPoints, Most Deads, Most Heals.
  - Row 3: Most DKP, Lowest Tanking Score, Most Pre-KVK, Most Honor.
- Summary values include the KVK achieved in. Rankable records also include overall rank across
  all players and every KVK where available: Acclaim, KillPoints, Deads, Heals, DKP, Tanking
  Score, Pre-KVK, Honor, and Kills.
- Highest Rank, Autarchs, and KVK Played intentionally do not show overall rank.
- Lowest Tanking Score is displayed as a percent and is calculated as
  `(HealedTroopsDelta * 20) / KillPointsDelta`, skipping rows where `KillPointsDelta` is missing
  or zero and skipping rows where `HealedTroopsDelta` is missing or zero.
- Added modern `/kvk history` controls for `History`, `Summary`, and `Export CSV`.
- Preserved CSV export using the Phase 4Bi expanded, null-preserving export contract.
- Rewired `/kvk history` to the modern card journey for registered-account and explicit
  `governor_id` flows.
- Kept `/mykvkhistory` on the legacy chart/table/CSV journey.
- Removed the `History` button from `/kvk stats`, leaving `Main Card` and `More Stats`.
- Removed the now-dead stats-side history renderer to avoid two competing history-card sources.
- Hardened history posting and view behaviour:
  - avoided coupling history posting to private stats-card helpers;
  - captured followup messages where supported so controls can disable on timeout;
  - used interaction/original-response editing for ephemeral Summary/History switching;
  - handled missing/deleted host messages with a user-visible notice;
  - covered CSV export success and failure paths.
- Updated command-surface documentation for `/kvk history` and `/mykvkhistory`.
- Generated visual samples under `.codex_artifacts/` for registered-account and explicit lookup
  Last 3/Summary paths.

Validation evidence from Phase 4Bii:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_history_renderer.py tests\test_kvk_history_card_views.py tests\test_kvk_cmds.py tests\test_kvk_stats_card_views.py tests\test_kvk_stats_card_renderer.py tests\test_kvk_history_service.py
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
```

Codex Security diff scan completed with no reportable findings:

`C:\Users\cwatt\AppData\Local\Temp\codex-security-scans\discord_file_downloader\109ee068_20260617T095053\report.md`

Phase 4Biii is the remaining Phase 4B implementation scope.

## 4B. Approved Sub-Phase Plan

### Phase 4Bi - History Payload, Data Contract, Picker, Export, And Test Foundation

Status: complete. Delivered in mirror PR #148, smoke tested, merged, and pushed to production.

Build the renderer-independent history payload/service boundary before visual redesign.

Required outcomes:

- Add or refine history service/model code that returns Discord-free, renderer-independent payloads.
- Preserve SQL access in DAL/service layers only.
- Validate and document the history SQL contract against `C:\K98-bot-SQL-Server`.
- Expand bot-side data shape to support rank, kills, kill target percent, deads, dead target
  percent, DKP, DKP target percent, Acclaim, history summary values, and trend inputs.
- Preserve missing/null distinction for metrics, especially Acclaim.
- Select last 3 KVKs using started-KVK logic.
- Keep `/mykvkhistory` legacy.
- Prepare `/kvk history` to use the same account picker style as `/kvk stats` and `/kvk targets`,
  while retaining explicit `governor_id` lookup.
- Preserve and expand CSV export so deeper history ranges are available outside the card view.
- Add missing service, DAL, view, picker, export, and command tests.
- No final card redesign is required in 4Bi unless it is needed as a small proof-of-wiring.

### Phase 4Bii - Modern `/kvk history` Last 3 Card And Stats History Move

Status: complete. Delivered, merged, and pushed to production.

Switch `/kvk history` to the modern card journey while keeping `/mykvkhistory` legacy.

Required outcomes:

- Implement the main `/kvk history` Last 3 KVK card using `history_card1.PNG`.
- Main card title should show `GovernorName` and Governor ID as a smaller/subtitle treatment, with
  Discord avatar/emoji identity treatment where available.
- Title right side should show average kills, average kill target percent, and a trend indicator
  for the same last 3 KVKs.
- Each row represents one KVK and shows:
  - KVK number
  - rank
  - kills and kill target percent
  - deads and dead target percent
  - healed troops where collected
  - DKP and DKP target percent
  - Acclaim, shown blank where unavailable or historically uncollected
- Move and redesign the existing compact `/kvk stats` History card into `/kvk history`, using
  `history_card2.PNG`.
- Summary card records are Highest Rank, Autarchs, KVK Played, Highest Acclaim, Most Kills, Most
  KillPoints, Most Deads, Most Heals, Most DKP, Lowest Tanking Score, Most Pre-KVK, and Most Honor.
- Summary rankable records show overall rank across all players/every KVK plus the KVK achieved
  in, where available.
- Lowest Tanking Score is `(HealedTroopsDelta * 20) / KillPointsDelta` displayed as a percent,
  excluding missing/zero kill points and missing/zero healed troops.
- Remove the `History` button from `/kvk stats`, leaving `Main Card` and `More Stats`.
- Preserve fallback behaviour and player-test safety.

### Phase 4Biii - Trends Card, Switching, And Final Polish

Add the remaining trend-analysis layer and final polish to the already-delivered modern history
journey.

Required outcomes:

- Implement the History Trends card using `history_card3.PNG`.
- Add the `Trends` button to the existing modern `/kvk history` card view without regressing
  `History`, `Summary`, or `Export CSV`.
- Trends should build on the delivered metrics rather than duplicating the Last 3 or Summary card.
  Consider rank, kills, kill target percent, deads, dead target percent, healed troops where
  collected, DKP, DKP target percent, Acclaim where collected, KillPointsDelta, and tanking score
  where calculable.
- Trend logic must treat missing values as missing rather than zero. In particular, historical
  acclaim and healed-troop zeroes should stay blank/missing unless confirmed as true data.
- Tanking trend logic must use the delivered formula and exclusions:
  `(HealedTroopsDelta * 20) / KillPointsDelta`, displayed as a percent, skipping missing/zero
  kill points and missing/zero healed troops.
- Do not rebuild the delivered Summary record/rank model unless a defect is found.
- Preserve final switch/button behavior between History, Summary, Trends, and Export.
- Generate visual samples for single-account and lookup flows.
- Decide after player testing whether graph output remains only in `/mykvkhistory` or needs a
  modern advanced path later.

## 5. Scope

### In Scope

- Audit `/kvk history` and `/mykvkhistory` end to end.
- Audit the current chart, table image, CSV export, account picker, metric buttons, custom picker,
  and range buttons.
- Validate the current history data contract and SQL source objects.
- Identify which metrics are available, reliable, readable, and useful.
- Implement the approved staged modern `/kvk history` model after Phase 4Bi scope confirmation.
- Preserve existing command paths during design and rollout.
- Preserve `/mykvkhistory` as the legacy graph/table/CSV path during player validation.
- Preserve and expand CSV export.
- Preserve explicit Governor ID lookup on `/kvk history`.
- Introduce account-picker parity with `/kvk stats` and `/kvk targets` where practical.
- Move the compact `/kvk stats` History card into `/kvk history`.
- Keep `/kvk stats` focused on current KVK output after the move.
- Preserve the Phase 4Bii Summary record model, including Highest Rank, Autarchs, KVK Played,
  Highest Acclaim, Most Kills, Most KillPoints, Most Deads, Most Heals, Most DKP, Lowest Tanking
  Score, Most Pre-KVK, and Most Honor.
- Use the three new history background assets under `assets/kvk/cards/`.
- Identify test coverage and visual/manual validation needed for the chosen option.

### Out of Scope

- No immediate implementation beyond the approved sub-phase being executed.
- No removal or deprecation of `/mykvkhistory`.
- No removal of CSV export without explicit approval.
- No new `/kvk history_chart` command in Phase 4B.
- No new top-level command or command group.
- No broad `/kvk rankings` redesign; that remains Phase 5.
- No changes to KVK import, recompute, export, Google Sheets tab names, or cache refresh semantics
  unless a defect is found and separately approved.
- No website implementation.
- No direct SQL in command modules, Discord views, or renderers.
- No predictive "on track" modelling.
- No row-by-row Honor or PreKVK history/trends in Phase 4B unless explicitly approved. Phase 4Bii
  already includes Most Pre-KVK and Most Honor as Summary-card personal-best records.
- No `Acclaim vs Target%` display until acclaim targets exist in an approved SQL/data contract.

## 6. Source Deferred Items

This task is a planned programme phase, not a standalone deferred optimisation batch.

If audit finds out-of-scope debt, capture it in `docs/reference/deferred_optimisations.md` using:

```md
### Deferred Optimisation
- Area:
- Type: performance | architecture | cleanup | refactor | consistency
- Description:
- Suggested Fix:
- Impact: low | medium | high
- Risk: low | medium | high
- Dependencies:
```

Likely audit candidates:

```md
### Deferred Optimisation
- Area: ui/views/kvk_history_view.py / kvk_history_utils.py
- Type: architecture
- Description: The current full-history flow may mix Discord view interaction state, chart/table generation, pandas dataframe shaping, and output composition more tightly than the Phase 3/4A renderer-independent pattern.
- Suggested Fix: Audit whether a history payload/service boundary should be introduced before any visual redesign, keeping the view responsible only for interaction flow.
- Impact: medium
- Risk: medium
- Dependencies: Phase 4B audit and approved output option
```

## 7. Codex Skills To Use

### Skill Decisions

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation; first stage is audit/scope only. |
| `k98-discord-command-feature` | use | History is a Discord command/view journey with buttons, selects, generated images, and CSV export. |
| `k98-sql-validation` | use | History data is SQL-backed through `dbo.v_EXCEL_FOR_KVK_Started` and related KVK metadata. |
| `k98-test-selection` | use | Required before validation to select history, command, view, renderer, and export tests. |
| `k98-deferred-optimisation-capture` | use if needed | Required if audit finds out-of-scope debt in history utilities, views, services, or DAL. |
| `k98-pr-review` | use | Required before PR handoff after implementation. |
| `k98-promotion-check` | use | Required before production promotion or bot-machine deployment. |
| `codex-security:security-scan` | use for implementation | Required if implementation touches Discord interactions, SQL/data access, file export, or user-controlled input. Skip is acceptable for audit/docs-only output with stated reason. |

## 8. Mandatory Workflow

Phase 4B audit and option approval are complete. Phase 4Bi and 4Bii are delivered. Continue with
the remaining sub-phase:

1. Start Phase 4Biii in a new chat from this task pack.
2. Re-read the required repo guidance and this updated Phase 4B pack.
3. Validate SQL/data contracts against `C:\K98-bot-SQL-Server`.
4. Treat Phase 4Bi and Phase 4Bii as complete and use their payload, export, Last 3, Summary,
   view-switching, and missing-value foundations.
5. Implement only Phase 4Biii scope unless the operator explicitly expands scope.
6. Do not rebuild the delivered Last 3 card, Summary record model, CSV export, or `/kvk stats`
   History removal unless a defect is found.
7. Keep `/mykvkhistory` as the legacy graph/table/CSV path.
8. Add or update focused tests in every implementation sub-phase.
9. Generate visual/manual review samples for all card changes.
10. Run focused validation and selected broader validation.
11. Run or document the Codex Security review gate for implementation PRs.

Do not implement multiple sub-phases in one PR unless the operator explicitly approves that scope.

## 9. Audit Requirements

Review and document:

- `/kvk history` command path in `commands/kvk_cmds.py`.
- `/mykvkhistory` command path in `commands/stats_cmds.py`.
- `ui/views/kvk_history_view.py` interaction state, account select, metric buttons, custom picker,
  CSV export, and table-range controls.
- `services/kvk_history_service.py` account ordering, governor ID normalization, dataframe shaping,
  and missing-KVK backfill.
- `kvk/dal/kvk_history_dal.py` SQL contract and current embedded queries.
- `kvk_history_utils.py` chart, table, CSV, and metric helper ownership.
- `embed_kvk_history.py` chart embed copy and legend/axis description.
- Existing tests for history service, offload/utils, view behaviour, command registration, and
  `/kvk` command routing.
- Current generated chart readability on desktop and mobile.
- Current generated table readability for Last 3, Last 6, Last 10, and likely full-history lengths.
- Empty history, missing governor, multi-account, and overlay behaviours.
- Whether chart/table generation should remain matplotlib/table-image based, move to a card
  wrapper, or be split into summary card plus detail outputs.
- Whether the current right-axis `% of target` design is the clearest comparator for every metric.
- Whether history should include or exclude Acclaim, overall rank, honor, PreKVK, pass-window, or
  personal-best metrics in Phase 4B.

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | `/kvk history` becomes modern; `/mykvkhistory` remains legacy chart/table/CSV. No new command group. |
| Service/payload | Add renderer-independent history payload/service boundaries in Phase 4Bi. |
| DAL | Keep SQL/data access in `kvk/dal/` or service-owned data access; no SQL in commands/views/renderers. |
| View | Modern `/kvk history` view owns controls and interaction flow only; legacy view remains available for `/mykvkhistory`. |
| Chart/table rendering | Keep legacy chart/table for `/mykvkhistory`; modern `/kvk history` should not depend on chart output. |
| Export | Preserve and expand CSV export; test generated filename/content behaviour. |
| Assets | Use `history_card1.PNG`, `history_card2.PNG`, and `history_card3.PNG` under `assets/kvk/cards/`. |
| Tests | Focused tests under `tests/` for service, view, output shape, export, and selected rendering. |
| Docs | Update programme/task-pack docs after delivery. |

## 11. Likely Files

### Review

- `commands/kvk_cmds.py`
- `commands/stats_cmds.py`
- `services/kvk_history_service.py`
- `kvk/dal/kvk_history_dal.py`
- `kvk_history_utils.py`
- `embed_kvk_history.py`
- `ui/views/kvk_history_view.py`
- `ui/views/kvk_stats_card_views.py`
- `kvk/rendering/kvk_stats_card_renderer.py`
- `assets/kvk/cards/history_card1.PNG`
- `assets/kvk/cards/history_card2.PNG`
- `assets/kvk/cards/history_card3.PNG`
- `tests/test_kvk_history_service.py`
- `tests/test_kvk_history_offload_and_utils.py`
- `tests/test_kvk_cmds.py`
- `tests/test_kvk_stats_card_views.py`
- `tests/test_validate_command_registration.py`
- SQL repo objects for `dbo.v_EXCEL_FOR_KVK_Started`, `dbo.KVK_Details`, and history source tables/views

### Modify

For Phase 4Biii, likely candidates are:

- `services/kvk_history_service.py`
- `kvk/dal/kvk_history_dal.py` only if the delivered data contract is missing a required trend
  field
- `commands/kvk_history_card_posting.py` or equivalent if needed
- `kvk/rendering/kvk_history_renderer.py`
- `kvk/models/kvk_history_payload.py`
- `ui/views/kvk_history_card_views.py`
- focused history renderer, service, card-view, and command tests
- programme/task-pack docs

### Create

Phase 4Bi/4Bii already created the main modern history modules. In Phase 4Biii, create only
missing trend-specific tests or helper/model types if the existing modules cannot express the
trend payload cleanly:

- `tests/test_kvk_history_renderer.py`
- `tests/test_kvk_history_payload.py` if payload types change
- `tests/test_kvk_history_card_views.py`
- `tests/test_kvk_history_service.py`

## 12. Optioneering Requirements

Produce at least these options before implementation:

### Option A - Polish Existing Journey

Keep the current chart embed, chart image, data image, account selector, metric buttons, custom
picker, and CSV export. Improve labels, spacing, copy, empty states, and reliability without a new
card layer.

Best when:

- The graph remains the primary value.
- Current controls are broadly useful.
- Risk should stay low.

Trade-offs:

- Less visual alignment with stats/targets.
- Existing chart/table image limitations remain.

### Option B - Hybrid Summary Card Plus Existing Detail Flow - Approved Direction

Approved with a modification: `/kvk history` becomes the modern card-based journey and
`/mykvkhistory` preserves the existing chart/table/CSV detail flow during player validation.
CSV export remains the deeper data path for longer ranges. The existing graph is not moved into a
new `/kvk history_chart` command in Phase 4B.

Best when:

- The card is useful for quick understanding.
- The legacy graph/table remains available for comparison through `/mykvkhistory`.
- Visual alignment matters but data density is too high for one card.

Trade-offs:

- More moving parts and more tests.
- Needs careful rollout communication so players understand `/kvk history` is the modern path and
  `/mykvkhistory` is the legacy graph path during testing.

### Option C - Modern Chart/Table Wrapper

Keep matplotlib/table generation, but wrap the chart and data table in a cleaner Phase 3-style
layout with consistent header, governor identity, legend, footer, and controls. This may be a
single generated image or two coordinated images.

Best when:

- The current chart is valuable but visually disconnected.
- The chart can remain readable after applying the card language.

Trade-offs:

- Risk of making the graph smaller or less readable.
- Needs visual validation across long names, long histories, and mobile Discord.

### Option D - Data-First Interactive History Browser

Move away from a graph-first presentation and provide a paginated/table-first Discord view with
metric toggles, personal-best callouts, and CSV export. Use cards only for optional summaries.

Best when:

- The graph is hard to read on mobile.
- Players mostly need exact KVK-by-KVK values.

Trade-offs:

- Less visually striking.
- May not satisfy users who like trend graphs.

### Option E - Defer Visual Redesign, Improve Data Contract First

If audit finds that the data contract is ambiguous or missing key metrics, defer output redesign
and first build a history payload/data-contract pack.

Best when:

- Metric semantics are unclear.
- Acclaim/rank/honor/PreKVK inclusion needs SQL or product decisions.

Trade-offs:

- No immediate UX improvement.
- Avoids reworking the output twice.

## 13. Data And Metric Questions To Answer

Answer before implementation:

- Which metrics should Phase 4B display by default? Delivered baseline: rank, kills, kill target
  percent, deads, dead target percent, healed troops where collected, DKP, DKP target percent,
  Acclaim where collected, KillPointsDelta, AutarchTimes, PreKVK points, Honor points, and
  tanking score where calculable.
- Should the default remain `T4&T5 Kills` vs `% of Kill target`? No for modern `/kvk history`;
  graph defaults remain only in legacy `/mykvkhistory`.
- Should deads and DKP each continue to pair with their own `% of target` right axis? Only in
  legacy chart output; modern card rows show metric plus percent directly.
- Should Acclaim appear in full history now, later, or never? Yes as raw Acclaim where available;
  show blank/missing where unavailable or historically uncollected.
- Should KVK rank or overall rank history be included? Include KVK rank in last-3 rows and trend
  card. Do not invent a new overall-rank source for history without SQL validation.
- Should Honor and PreKVK history remain outside this command? They are included as Summary-card
  personal-best records after Phase 4Bii. Do not add row-by-row Honor or PreKVK trends in Phase
  4Biii unless explicitly approved.
- Should pass-window kills/deads remain custom-only or become selectable presets? Exclude from
  modern cards; preserve in legacy/export if already available.
- Should multiple selected governors remain capped at three overlays? Modern card is single
  selected governor by default. Legacy `/mykvkhistory` can preserve overlay behaviour.
- What is the right empty-state for KVKs with no row versus zero-filled started KVKs? The new
  payload must distinguish missing row, missing metric, and true zero. For Acclaim and
  HealedTroopsDelta, historical zeroes are treated as missing/uncollected unless confirmed as true
  zero data.
- How should Lowest Tanking Score be calculated? Delivered answer:
  `(HealedTroopsDelta * 20) / KillPointsDelta`, displayed as a percent, lower is better, excluding
  rows where `KillPointsDelta` or `HealedTroopsDelta` is missing or zero.
- Which labels need renaming to avoid confusion between highest-ever, last-KVK, target percent, and
  current-KVK stats? Move historical labels from `/kvk stats` to `/kvk history`; keep `/kvk stats`
  current-focused.

## 14. Implementation Requirements

Once an option is approved:

- Keep commands and views thin.
- Put data shaping and comparison rules in service/model code.
- Keep SQL/data access in DAL/service layers.
- Keep renderers free of SQL and Discord objects.
- Preserve `/mykvkhistory` legacy chart/table/CSV output.
- Modernise `/kvk history` using card output and richer CSV export.
- Preserve fallback behaviour if card/export generation fails.
- Keep card output readable on Discord mobile.
- Add or update focused tests for every changed behaviour.
- Generate visual samples for at least one registered-account path and one explicit Governor ID
  lookup path.

### 14.1 Approved `/kvk history` Card Model

Modern `/kvk history` should expose these cards:

1. `History` / Last 3 KVK performance card using `history_card1.PNG`.
2. `Summary` card using `history_card2.PNG`, moving the existing compact History content away from
   `/kvk stats`.
3. `Trends` card using `history_card3.PNG`.

Implementation may choose exact button labels, but labels should make the distinction clear:
`History`, `Summary`, `Trends`, and `Export CSV` are the preferred starting point. Phase 4Bii
delivered `History`, `Summary`, and `Export CSV`; Phase 4Biii should add `Trends`.

### 14.2 Main History Card Design

The main card should show the current selected governor's last 3 started KVKs.

Header:

- Governor name.
- Governor ID as smaller subtitle/subscript-style text.
- Discord avatar/emoji identity treatment where available.
- Right-hand summary block with average kills, average kill target percent, and trend indicator
  across the same last 3 KVKs.

Rows:

- One row per KVK.
- Show KVK number, rank, kills plus kill target percent, deads plus dead target percent, healed
  troops where collected, DKP plus DKP target percent, and Acclaim.
- Show Acclaim and healed troops as blank/missing when unavailable or historically uncollected. Do
  not display zero unless the SQL row is confirmed to contain a true zero.

### 14.3 Summary Card Design

Phase 4Bii moved and redesigned the current `/kvk stats` History card content into
`/kvk history`. Preserve this delivered model unless a defect is found.

- Row 1: Highest Rank, Autarchs, KVK Played, Highest Acclaim.
- Row 2: Most Kills, Most KillPoints, Most Deads, Most Heals.
- Row 3: Most DKP, Lowest Tanking Score, Most Pre-KVK, Most Honor.
- Each record shows the value and the KVK achieved in.
- Acclaim, KillPoints, Deads, Heals, DKP, Tanking Score, Pre-KVK, Honor, and Kills also show
  overall rank across all players/every KVK where available.
- Highest Rank, Autarchs, and KVK Played do not show overall rank.
- Lowest Tanking Score is `(HealedTroopsDelta * 20) / KillPointsDelta`, displayed as a percent,
  lower is better, excluding rows where kill points or healed troops are missing or zero.

Do not duplicate this content on `/kvk stats` after the move.

### 14.4 Trends Card Design

The Trends card should include:

- rank
- kills
- kill target percent
- deads
- dead target percent
- healed troops where collected
- DKP
- DKP target percent
- Acclaim where collected
- KillPointsDelta where it adds useful signal
- tanking score where calculable

For each metric:

- show trend direction and enough context to explain the direction
- avoid duplicating the Last 3 rows or Summary personal-best grid
- treat missing values as missing, not zero
- use the delivered tanking-score formula and exclusions
- avoid predictive "on track" wording

## 15. Command Surface Governance

- [ ] No new top-level command.
- [ ] No new grouped subcommand unless separately approved.
- [ ] Preserve `/kvk history` and `/mykvkhistory` registrations.
- [ ] Preserve decorators, permissions, response visibility, options, usage tracking, and command
  cache behaviour unless explicitly approved.
- [ ] Run or justify skipping `scripts/validate_command_registration.py`.
- [ ] Update `docs/reference/canonical_command_reference.md` only if command descriptions or visible
  behaviour notes change.

## 16. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| Full history may be too dense for a single stats-card-style image | split into History, Summary, and Trends cards | Readability matters more than forcing all history into one image. |
| History view may own too much output composition | fix in Phase 4Bi | Renderer-independent payload/service boundary is approved. |
| CSV export remains useful | preserve and expand | CSV services longer ranges and detailed data instead of keeping Last 6/10/12 in the default card. |
| Legacy `/mykvkhistory` still lives | not applicable | Parallel rollout is intentional. |
| Modern `/kvk history_chart` split | do not create in Phase 4B | Legacy `/mykvkhistory` preserves graph testing without new command-surface weight. |
| Acclaim target percentage | defer | Acclaim targets do not exist yet. |
| Honor and PreKVK history | summary-only | Phase 4Bii includes Most Honor and Most Pre-KVK as Summary-card personal-best records; row-by-row history/trends remain out of scope unless explicitly approved. |
| `/kvk stats` History button | move to `/kvk history` in Phase 4Bii | Stats should be current KVK; history should own past performance. |
| `/kvk rankings` polish | defer | Phase 5 owns rankings. |

Add further rows based on actual findings. Deferred items must use the structured format from
`docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 17. Testing Requirements

Cover or justify:

- `/kvk history` happy path.
- `/mykvkhistory` legacy happy path remains unchanged.
- registered-account and explicit Governor ID paths.
- empty history / missing governor path.
- same account picker style as `/kvk stats` and `/kvk targets` where implemented.
- single-governor modern card output.
- legacy chart/table output remains covered for `/mykvkhistory`.
- legacy metric preset buttons, custom metric picker, and Last 3 / Last 6 / Last 10 range buttons
  remain covered where legacy code is retained.
- CSV export content and filename.
- expanded CSV export includes deeper history data where approved.
- fallback behaviour when card/export generation fails.
- command registration unchanged.
- renderer/payload output shape if a new payload or renderer is added.
- `/kvk stats` no longer shows the History button after the move.
- Acclaim missing/null handling.
- HealedTroopsDelta missing/null/zero-as-uncollected handling.
- last 3 started-KVK selection.
- Summary personal-best value, KVK-achieved, and overall-rank display for rankable records.
- Lowest Tanking Score calculation displays as a percent and excludes missing/zero kill points and
  missing/zero healed troops.
- Trend calculation excludes missing values and does not backfill historical Acclaim or healed
  troop gaps with zero.
- Trends button switches successfully from History and Summary, and History/Summary can be
  restored after visiting Trends.

Suggested focused tests after audit:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_history_service.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_history_offload_and_utils.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_cmds.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_history_renderer.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_history_card_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py
```

Suggested validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
```

Run full tests before promotion if practical:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

For docs-only audit/optioneering output, runtime pytest may be skipped with a documented reason.

## 18. Acceptance Criteria

Audit/optioneering acceptance:

- [x] Current `/kvk history` and `/mykvkhistory` behaviours are mapped.
- [x] Current data contract and SQL source objects are validated or ambiguities are documented.
- [x] Current screenshot/output is used as design input.
- [x] At least four viable output options are compared with trade-offs.
- [x] A recommended staged solution is proposed and approved.
- [x] Implementation plan is separated into Phase 4Bi, 4Bii, and 4Biii.
- [x] No implementation occurred before approval.

Phase 4Bi implementation acceptance:

- [x] Renderer-independent history payload/model foundation is delivered.
- [x] Modern history SQL/export contract is DAL/service-owned.
- [x] Last 3 started-KVK selection is implemented.
- [x] Missing/null metric distinction is preserved for modern payload rows.
- [x] `/kvk history` is prepared for shared account picker flow and explicit lookup.
- [x] `/mykvkhistory` remains legacy.
- [x] CSV export is preserved and expanded.
- [x] Focused tests and validation passed.
- [x] Smoke-test feedback for SQL-padded governor names is fixed.
- [x] PR #148 was merged and pushed to production.

Phase 4Bii implementation acceptance:

- [x] Approved output model is implemented without removing legacy commands.
- [x] `/kvk history` uses the modern card model.
- [x] Last 3 card is newest-started first, uses the `Last 3 KVKs` title, and includes healed
  troops where collected.
- [x] Missing/uncollected Acclaim and healed values stay blank instead of rendering misleading
  zeroes.
- [x] Summary card uses the delivered 12-record model with KVK-achieved context.
- [x] Rankable Summary records include overall rank across all players/every KVK where available.
- [x] Lowest Tanking Score uses the delivered percent formula and skips missing/zero kill points
  and missing/zero healed troops.
- [x] `/mykvkhistory` retains the old chart/table/CSV journey during player testing.
- [x] Existing useful export behaviour remains or is deliberately replaced with richer export data.
- [x] Output is readable on Discord mobile.
- [x] Commands/views remain thin.
- [x] No new direct SQL exists in command, view, or renderer modules.
- [x] Focused tests pass.
- [x] Visual/manual review samples are generated where output changes.
- [x] Codex Security review is run or explicitly skipped based on risk triggers.
- [x] Programme/task-pack docs are updated after delivery.

Phase 4Biii implementation acceptance, outstanding:

- [ ] Trends card is implemented using `history_card3.PNG`.
- [ ] Trends button is added without regressing History, Summary, or Export CSV.
- [ ] Trend metrics build on the delivered Last 3/Summary data rather than duplicating those cards.
- [ ] Trend logic preserves missing/uncollected Acclaim and healed values as missing.
- [ ] Tanking trend logic uses the delivered percent formula and exclusions.
- [ ] `/mykvkhistory` remains legacy graph/table/CSV.
- [ ] Focused service, renderer, view, command, and validation tests pass.
- [ ] Visual/manual review samples are generated for registered-account and explicit lookup flows.
- [ ] Codex Security review is run or explicitly skipped based on risk triggers.

## 19. Required Delivery Output

For the audit/optioneering stage:

1. Summary
2. Current Behaviour Map
3. Data Contract Findings
4. UX Findings From Existing Screenshot/Output
5. Architecture Findings
6. Option Matrix
7. Recommended Option
8. Implementation Plan
9. Test Strategy
10. Risks / Open Questions
11. Deferred Optimisations

For the implementation stage, use:

1. Summary
2. File Manifest
3. SQL Changes
4. Command Surface Changes
5. User-Visible Behaviour Changes
6. Data Contract / Payload Summary
7. Renderer / Output Summary
8. Refactor Findings
9. Test Plan and Results
10. Visual Review Evidence
11. AI Review Gates
12. Deployment Steps
13. Rollback Plan
14. Deferred Optimisations

## 20. PR Summary Template

```md
## Summary

- Audited and/or modernised the full `/kvk history` journey according to the approved Phase 4B scope.

## Changes

- <audit docs or implementation changes>

## SQL Changes

- None, or list companion SQL PR and deployment order.

## Tests

- <focused pytest/validators/manual visual checks>

## AI Review Gates

- Codex Security: <run | skipped, with reason>

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Risk: full history is a high-traffic player output with chart/table/export interaction complexity.
- Rollback: preserve or restore the existing chart/table/CSV output while keeping legacy commands live.
```

## 21. Historical Codex Chat Starter - Phase 4Bii

Superseded. Phase 4Bii is delivered, merged, and pushed to production. Use the Phase 4Biii starter
below for the next implementation chat.

## 22. Codex Chat Starter - Phase 4Biii

```text
Codex, start Phase 4Biii of the KVK Player Experience Redesign: History Trends Card And Final
Polish.

Phase 4A targets is complete, merged, and promoted to production. Phase 4B audit and
optioneering are complete. Phase 4Bi is complete, smoke tested, merged in mirror PR #148, and
pushed to production. Phase 4Bii is complete, merged, and pushed to production.

The delivered product model is:

- /kvk stats = current KVK performance only, with Main Card and More Stats.
- /kvk history = modern card journey for past-performance review.
- /mykvkhistory = legacy graph/table/CSV journey retained during player testing.
- No /kvk history_chart command in Phase 4B.
- CSV export remains the deeper/full-history data path.

Read:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/KVK Player Experience Redesign - Programme Pack.md
- docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 4B History Audit and Optioneering.md

Delivered Phase 4Bi/4Bii baseline:

- Renderer-independent history payload/service/DAL/export foundation exists.
- /kvk history uses the modern Last 3 KVK card with history_card1.PNG.
- Last 3 is newest-started first and titled Last 3 KVKs.
- Last 3 rows show KVK, rank, kills, deads, healed where collected, DKP, and acclaim where
  collected.
- Missing or historically uncollected Acclaim and healed values stay blank, not zero.
- /kvk history Summary uses history_card2.PNG and a 12-record layout:
  Row 1: Highest Rank, Autarchs, KVK Played, Highest Acclaim.
  Row 2: Most Kills, Most KillPoints, Most Deads, Most Heals.
  Row 3: Most DKP, Lowest Tanking Score, Most Pre-KVK, Most Honor.
- Summary values include the KVK achieved in.
- Rankable Summary records include overall rank across all players/every KVK where available:
  Acclaim, Kills, KillPoints, Deads, Heals, DKP, Tanking Score, Pre-KVK, and Honor.
- Highest Rank, Autarchs, and KVK Played do not show overall rank.
- Lowest Tanking Score is (HealedTroopsDelta * 20) / KillPointsDelta, displayed as a percent,
  lower is better, skipping rows where KillPointsDelta is missing/zero and rows where
  HealedTroopsDelta is missing/zero.
- /kvk history currently has History, Summary, and Export CSV controls.
- /kvk stats no longer has a History button.
- /mykvkhistory remains legacy and unchanged.

Phase 4Biii scope only:

- Implement the Trends card using assets/kvk/cards/history_card3.PNG.
- Add a Trends button to the existing /kvk history card view.
- Preserve History, Summary, and Export CSV behaviour.
- Do not rebuild the delivered Last 3 or Summary cards unless a defect is found.
- Trends should build on delivered metrics without duplicating Last 3 rows or the Summary
  personal-best grid.
- Consider rank, kills, kill target percent, deads, dead target percent, healed troops where
  collected, DKP, DKP target percent, Acclaim where collected, KillPointsDelta, and tanking score
  where calculable.
- Treat missing values as missing, not zero. Keep historical Acclaim/healed zeroes blank unless
  confirmed as true data.
- Use the delivered tanking-score formula and exclusions.
- Avoid predictive "on track" wording.
- Keep graph/table output only in /mykvkhistory.
- Generate visual samples for registered-account and explicit governor_id lookup paths.
- Add focused service, renderer, view, command, and missing-value/tanking-score tests.

Likely files:
- commands/kvk_cmds.py
- commands/kvk_history_card_posting.py
- services/kvk_history_service.py
- kvk/dal/kvk_history_dal.py only if the existing contract lacks a required trend field
- kvk/models/kvk_history_payload.py
- kvk/rendering/kvk_history_renderer.py
- ui/views/kvk_history_card_views.py
- tests/test_kvk_history_service.py
- tests/test_kvk_history_renderer.py
- tests/test_kvk_history_card_views.py
- tests/test_kvk_cmds.py

Validation to plan:
- focused KVK history tests
- scripts/validate_architecture_boundaries.py
- scripts/validate_deferred_items.py
- scripts/select_tests.py
- scripts/smoke_imports.py
- scripts/validate_command_registration.py
- pre-commit
- full pytest before PR handoff if practical
- Codex Security review because this touches Discord interactions, SQL-backed data, file/image
  output, and export-adjacent history code
```
