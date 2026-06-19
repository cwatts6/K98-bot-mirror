# Codex Task Pack - KVK Player Experience Redesign Phase 5 Unified Rankings Visual/UX Polish

## 1. Task Header

- Task name: `KVK Player Experience Redesign - Phase 5 Unified Rankings Visual/UX Polish`
- Date: `2026-06-18`
- Owner/context: `K98 Bot KVK Player Experience Redesign programme after Phase 4 completion`
- Task type: `feature / UX redesign / Discord interaction polish / renderer-service-DAL cleanup / staged implementation plan`
- One-pass approved: `no`
- Status: `Phase 5A, Phase 5B, Phase 5C, and Phase 5D complete; Phase 5E ready for next-chat delivery`

## Phase 5A Completion Note

Phase 5A is complete. It was delivered in mirror PR #152, promoted through production PR #461,
pushed to production, and smoke tested successfully.

Delivered Phase 5A scope:

- Added `/kvk rankings type:records` under the existing `/kvk rankings` command surface.
- Preserved the no-new-top-level-command rule and kept legacy ranking commands live.
- Added the KD98 Hall of Fame first release as Top 10 all-time single-KVK performances.
- Supported Hall of Fame metrics: Kills, KillPoints, Deads, DKP, Healed, Acclaim, Honor, and
  PreKvK where source data produces qualifying values.
- Kept records Top 10 only; no Top 25, Top 50, or Top 100 record controls were added.
- Allowed repeated appearances by the same governor because records are single-KVK performances,
  not unique-player lifetime standings.
- Added `kvk.models.kvk_rankings`, `kvk.services.kvk_rankings_service`,
  `kvk.dal.kvk_rankings_dal`, `kvk.rendering.kvk_rankings_embed`, and
  `ui.views.kvk_rankings_views` as the first shared rankings hub foundation.
- Added Hall of Fame error/fallback handling and view timeout hardening.
- Updated canonical command docs for the visible `records` type choice.
- Removed Top 100 from primary KVK/Honor player controls while preserving internal/deeper support
  where existing paths still need it.

## Phase 5B Completion Note

Phase 5B is complete. It was delivered in mirror PR #153, promoted through production PR #462,
pushed to production, and smoke tested successfully.

Delivered Phase 5B scope:

- Built the unified current-ranking browser foundation for `/kvk rankings type:kvk`, `honor`, and
  `prekvk`.
- Added shared current-ranking payload/service shaping for KVK cache rows, latest Honor scan rows,
  and PreKvK report payloads.
- Added `CurrentRankingsBrowserView` with mode selector, mode-specific metric selector, and Top
  10/25/50 controls.
- Kept Top 100 out of the primary player controls.
- Converted `/kvk rankings type:prekvk` to the unified public embed browser.
- Preserved legacy `/prekvk report` as the image-based PreKvK report flow.
- Preserved legacy `/kvk_rankings` and `/honor_rankings` during rollout.
- Preserved `/kvk rankings type:records` exactly as the Phase 5A Hall of Fame Top 10 records mode.
- Re-applied the stricter Honor no-admin-override channel policy inside browser mode switching.
- Smoke-polished the unified KVK table renderer to avoid duplicate sorted metric columns and to
  reuse the legacy fixed-width one-line row budget.
- Clarified KVK footer counts as `Showing: N of total filtered rows`; PreKvK uses `Showing: Top N`
  where only an already-limited report payload is available.
- Captured remaining My Rank/export and legacy-ranking consolidation work as structured deferred
  optimisations.
- Validated SQL/cache assumptions against `C:\K98-bot-SQL-Server`.
- Ran focused tests, full tests, standard validators, pre-commit, and Codex Security. Production
  smoke testing passed.

## Phase 5C Completion Note

Phase 5C is complete. It was delivered in mirror PR #154, promoted through production PR #463,
pushed to production, and smoke tested successfully.

Delivered Phase 5C scope:

- Added a Pillow-rendered Top 10 visual spotlight card for `/kvk rankings type:kvk`.
- Limited the first visual-card slice to current KVK Top 10 rankings to preserve the Phase 5B
  unified browser foundation.
- Preserved embed fallback for render/send failures.
- Kept Top 25 and Top 50 on the compact unified embed browser.
- Kept Top 100 out of the primary player controls.
- Kept Power available for Top 25/50 compact analysis, but removed Power from the Top 10 card
  metric set because the card is intended to spotlight performance, not the "kills ordered by
  power" diagnostic view.
- Defaulted current KVK rankings to Kills.
- Added Top 10 card metrics for Kills, % Kill Target, Deads, DKP, Acclaim, and Tanking Score.
- Implemented Tanking Score with the same current/history semantics: lower is better, and rows
  must have positive KillPoints and positive healed troops.
- Added KVK ranking card assets under `assets/kvk/cards/` and aligned the card styling with the
  delivered `/kvk stats` visual language.
- Polished the card through production smoke feedback: removed dense dividers and low-value header
  text, removed player-irrelevant source wording, right-aligned the footer, improved top-three rank
  emphasis, changed low-contrast DKP/Tanking colours, and selected metric-specific supporting
  values.
- Preserved `/kvk rankings type:records` exactly as the Phase 5A Hall of Fame Top 10 embed mode.
- Preserved legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report`.
- Preserved the image-based legacy `/prekvk report`.
- Added focused renderer/service/view/command coverage plus visual sample generation and
  inspection.

## Phase 5D Completion Note

Phase 5D is complete. It was delivered in mirror PR #155, promoted through production PR #464,
pushed to production, and smoke tested successfully.

Delivered Phase 5D scope:

- Added a Pillow-rendered Top 10 Hall of Fame visual card for `/kvk rankings type:records`.
- Supported all existing Hall of Fame records metrics: Kills, KillPoints, Deads, DKP, Healed,
  Acclaim, Honor, and PreKvK where source data produces qualifying values.
- Used the existing Hall of Fame ranking payload/service/DAL rows rather than recalculating
  source-of-truth record semantics in the renderer.
- Added metric-specific qualifying record totals from the Hall of Fame DAL so cards can show
  `Top 10 from N records` for the selected metric.
- Kept records Top 10 only; no Hall of Fame Top 25, Top 50, or Top 100 controls were added.
- Preserved repeated-governor record appearances because records remain single-KVK performances,
  not unique-player lifetime standings.
- Preserved missing/uncollected historical metric exclusion and did not rank missing values as
  zero.
- Preserved embed fallback for records card render/send failures.
- Preserved the Phase 5C current KVK Top 10 card, Phase 5B unified browser, Top 25/50 compact
  browser output, Top 100 exclusion, legacy ranking commands, and image-based legacy
  `/prekvk report`.
- Polished the card through smoke-test feedback: removed developer-note footer wording, replaced
  duplicate header copy with metric-specific record totals, cached the darkening overlay, fixed
  symmetric shading, and centered the top-three podium text.
- Generated and inspected local visual samples, ran focused tests, standard validators,
  pre-commit, full pytest during PR handoff, and Codex Security with no reportable findings.

Next Phase 5 sub-phase:

- Phase 5E should add Honor and PreKvK Top 10 visual card layers using the shared ranking payloads.
- Preserve the delivered current KVK Top 10 card, records Top 10 card, and Phase 5B unified
  browser behaviour.
- Keep Top 25 and Top 50 on the compact browser unless a later approved visual sub-phase expands
  them.
- Keep Top 100 out of primary player controls.
- Preserve Honor's no-admin-override KVK stats channel gate.
- Preserve legacy commands during rollout.
- Preserve image-based legacy `/prekvk report`.
- Keep My Rank/export and legacy-ranking consolidation in the Phase 5 delivery plan after the
  visual-card slices, now starting in Phase 5F unless later scope changes are approved.
- Continue to capture all deferred optimisations that remain part of "rankings done right" so they
  can be delivered in later Phase 5 sub-phases rather than lost.

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
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 4B History Audit and Optioneering.md`
- `docs/reference/canonical_command_reference.md` if command descriptions, command references, or visible command behaviour change

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

```text
C:\K98-bot-SQL-Server
```

Do not infer ranking source contracts from Python-only usage where SQL definitions exist.

## 3. Objective

Modernise `/kvk rankings` into a unified, high-traffic ranking browser covering KVK, Honor,
PreKvK, and all-time KVK performance records without treating the output as a plain data dump.

The redesigned ranking journey should make the popular Top 10, Top 25, and Top 50 current-ranking
views fast, readable, attractive, and useful every day during KVK. Top 100 should not remain a
primary player button unless audit evidence proves meaningful usage; deeper data should move to
export or an advanced path.

Add a new Hall of Fame / all-time records concept to celebrate the greatest single-KVK performances
across all collected KVKs, such as Top 10 kills, KillPoints, deads, DKP, healed, acclaim, honor,
and PreKvK records. This should be treated as a historical performance-record journey, not as a
current-KVK leaderboard.

The output should align visually and architecturally with the delivered modern `/kvk stats`,
`/kvk targets`, and `/kvk history` journeys, while preserving legacy commands during rollout.

## 4. Background

The programme vision is to make the KVK player commands feel like a coherent product rather than a
set of legacy data-dump embeds. Phase 3 delivered modern `/kvk stats`; Phase 4A delivered modern
`/kvk targets`; Phase 4B delivered modern `/kvk history`. Phase 5 is now the remaining core player
journey: rankings.

The delivered `/kvk rankings` scaffold now supports ranking types `kvk`, `honor`, `prekvk`, and
`records`. Phase 5B unified the current ranking browser:

- KVK, Honor, and PreKvK current rankings use `kvk.services.kvk_rankings_service`,
  `kvk.rendering.kvk_rankings_embed`, and
  `ui/views/kvk_rankings_views.py::CurrentRankingsBrowserView`.
- KVK current rankings are shaped from the stats cache with the existing `STATUS = INCLUDED` and
  `Starting Power >= 40M` filters.
- Honor current rankings are shaped from the latest Honor scan and preserve the stricter
  no-admin-override channel gate.
- PreKvK current rankings wrap `prekvk.report_service` for unified browser output under
  `/kvk rankings type:prekvk`.
- Hall of Fame records use `kvk.services.kvk_rankings_service`,
  `kvk.dal.kvk_rankings_dal`, `kvk.rendering.kvk_rankings_embed`, and
  `ui/views/kvk_rankings_views.py::HallOfFameRecordsView`.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` paths remain live. Legacy
  `/prekvk report` remains image-based.

Current player observation:

- Top 10, Top 25, and Top 50 are used frequently.
- Top 100 appears unused or low-value for normal Discord use.
- Rankings are popular because they are social, competitive, and checked repeatedly; the design must support repeated daily use without becoming noisy.
- Phase 5A acted on the strong product opportunity to add an all-time `Hall of Fame` / records mode showing the greatest single-KVK performances ever recorded for the kingdom. Later Phase 5 work should now protect and polish that journey while unifying the current ranking browser.

The key product challenge is that rankings are essentially tables, but players do not experience
them as tables. They use them to answer social and competitive questions:

- Who is leading?
- Who is just outside the top group?
- Where do I sit?
- Who is catching up?
- Which metric matters right now?
- How does Honor or PreKvK compare with the main KVK leaderboard?

## 5. Product Direction And Design Recommendation

### 5.1 Recommended end-state

Build a modern **Ranking Hub** rather than a bigger table.

The first screen should be a clean public browser with:

- ranking mode selector: `KVK`, `Honor`, `PreKvK`
- metric selector appropriate to the selected mode
- size controls: `Top 10`, `Top 25`, `Top 50`
- optional `My Rank` / `Find Me` action for registered users
- optional `Export` / `Full List` action for deeper data, not a primary `Top 100` button

### 5.2 Display model

Use a two-layer display model:

1. **Top 10 Spotlight Card**
   - Generated image card, matching the modern KVK visual language.
   - Designed for the channel: visually shareable, clear, and competitive.
   - Shows podium/top 3 prominently, then ranks 4-10 as compact challengers.
   - Includes selected mode, metric, KVK context, filters, and last refresh.

2. **Top 25 / Top 50 Compact Browser**
   - Keep embed/table output initially, but make it cleaner and unified.
   - Use a payload/service contract so it can later render as image if needed.
   - Prioritise readability and interaction reliability over over-styled dense image tables.

Top 100 should be removed from the primary player controls in Phase 5 unless audit data proves it is
used. If full-depth access is still needed, provide it as:

- CSV export;
- admin/operator-only diagnostic path;
- or a clearly labelled `Full List` advanced action.

### 5.3 Smart feature: `My Rank` / `Find Me`

Add a `My Rank` experience if feasible from the existing registry and ranking data.

For a registered user, this should show:

- their selected governor account;
- their current rank for the active ranking mode and metric;
- the row above and below them where available;
- their gap to next rank or top 10/25/50 where meaningful;
- a private response by default to avoid spam or embarrassment.

This is likely more valuable than Top 100 because players who are outside the displayed range care
about their position, not about reading 100 rows.

### 5.4 Ranking mode strategy

Supported modes should remain under the existing `/kvk rankings` subcommand unless audit proves a
need to split:

| Mode | Initial metrics | Notes |
|---|---|---|
| `KVK` | Overall, Power, KillPoints/KP, Kills, `% Kill Target`, Deads, DKP, possibly Acclaim | Validate available fields and naming. Consider whether default should be `Overall` or `Kills/KP`, not `Power`. |
| `Honor` | Honor Points | Later optional: rank by daily gain or stage if SQL supports it. |
| `PreKvK` | Overall, Stage 1, Stage 2, Stage 3 | Reuse existing report payload/renderer where possible. |

Do not add pass-window rankings, Top Movers, trend deltas, or comparison charts unless the audit
finds reliable current data contracts and the operator approves expansion.

### 5.5 UI principle

The ranking browser should feel fast and stable. It should not overload the player with every
possible metric at once.

Preferred control layout:

- Row 0: ranking type selector, metric selector.
- Row 1: `Top 10`, `Top 25`, `Top 50`, `My Rank`, `Export` if implemented.
- Row 2: pagination only when needed.

Avoid too many buttons. Avoid duplicate controls between ranking types. Avoid a permanent Top 100
button in the public player journey.


### 5.6 New feature recommendation: KD98 Hall of Fame / all-time records

Add a dedicated all-time performance-record mode as part of Phase 5, subject to SQL/data-contract
audit.

This should answer a different player question from current rankings:

```text
What are the greatest KVK performances our kingdom has ever seen?
```

Recommended user-facing concept:

```text
KD98 Hall of Fame
Top 10 All-Time KVK Performances
```

Initial record categories to audit and, where validated, support:

- Kills / T4+T5 Kills
- KillPoints / KP
- Deads
- DKP
- Healed troops
- Acclaim / contribution where collected
- Honor points
- PreKvK points

These should be **single-KVK performance records**, not lifetime totals. The same governor may
appear multiple times if they produced multiple record-setting KVKs. That is acceptable and should
be treated as part of the excitement: it shows legendary repeated performances rather than forcing a
unique-player-only leaderboard.

Each row should show at minimum:

- rank
- governor name
- Governor ID where useful or as fallback
- record value
- KVK number
- KVK name/mode where available
- optional kingdom/camp/context where reliable

Do not mix current KVK rankings and all-time records in the same dataset or card. They should be
separate modes with clear titles and labels.

### 5.7 Command placement recommendation for records

Preferred first implementation: keep records inside the existing `/kvk rankings` journey by adding
a new ranking type choice after audit approval:

```text
/kvk rankings type:records
```

Acceptable label alternatives for the visible choice are:

- `records`
- `hall_of_fame`
- `all_time`

The task should audit which label is clearest in Discord's slash-command UI. The output title can
use the friendlier wording `Hall of Fame` even if the command choice is `records`.

Do **not** create a new top-level command in Phase 5. A future `/kvk records` or `/kvk halloffame`
subcommand can be considered only after usage validates that records deserves promotion to its own
journey.

## 6. Scope

### In Scope

- Audit current `/kvk rankings` implementation end to end.
- Audit legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` paths where still active.
- Audit existing ranking usage logs if available, especially Top 10/25/50/100 and ranking type usage.
- Confirm whether Top 100 is unused enough to remove from primary controls.
- Preserve the delivered `records` ranking type under `/kvk rankings` for all-time single-KVK performance records.
- Preserve all-time record missing/null semantics for historically unavailable fields such as acclaim and healed troops.
- Design a unified ranking payload/model that can support KVK, Honor, PreKvK, and all-time record rows.
- Build or propose a service boundary for ranking data shaping and filtering.
- Keep command/view code thin and avoid direct SQL in commands/views/renderers.
- Preserve existing `/kvk rankings type` command surface unless a new visible option is explicitly approved.
- Preserve legacy commands during rollout.
- Modernise the KVK ranking browser controls and output shape.
- Modernise Honor ranking controls and output shape so it feels part of the same browser.
- Integrate PreKvK ranking/report controls into the same UX model where practical without regressing the existing image renderer.
- Preserve Hall of Fame / all-time Top 10 records; add visual cards only in the later card phase unless Phase 5B explicitly expands scope.
- Add `My Rank` / local-position experience if feasible within existing registry and data contracts.
- Add or improve CSV/export/full-list behaviour if Top 100 is removed from primary controls.
- Add focused tests for ranking service/payload, view interactions, command routing, filtering, sorting, pagination, and fallback behaviour.
- Generate visual samples for Top 10 card output if image output is implemented.
- Update programme/task-pack docs and command reference if visible command behaviour changes.

### Out of Scope

- No removal of legacy `/kvk_rankings`, `/honor_rankings`, or `/prekvk report` commands in Phase 5.
- No new top-level command or command group.
- No website implementation.
- No prediction, “on track”, or motivational coaching based on ranking movement unless separately approved.
- No pass-window ranking expansion unless data contracts are validated and scope is explicitly approved.
- No Top Movers / rank movement feature unless previous-snapshot data is already reliable and approved for Phase 5.
- No lifetime-total Hall of Fame records unless explicitly approved; the recommended records model is single-KVK performances.
- No unique-governor-only deduplication for all-time records unless audit proves players prefer it; repeated legendary performances by the same player are acceptable.
- No SQL changes unless the audit proves they are necessary and a companion SQL PR is planned.
- No broad redesign of `/kvk stats`, `/kvk targets`, or `/kvk history` beyond optional navigation links to rankings.
- No change to KVK import/recompute/export semantics unless a defect is found and separately approved.

## 7. Source Deferred Items

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

Likely candidates:

```md
### Deferred Optimisation
- Area: build_KVKrankings_embed.py / ui.views.stats_views.KVKRankingView
- Type: architecture
- Description: KVK ranking formatting, filtering, safe field extraction, sorting, pagination, and Discord output are tightly coupled around a fixed-width embed table.
- Suggested Fix: Introduce a renderer-independent ranking payload/service boundary, then let embed and image renderers consume the same payload.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5 rankings audit and approved output design.
```

```md
### Deferred Optimisation
- Area: honor_rankings_view.py
- Type: consistency
- Description: Honor rankings have their own independent Top-N buttons and embed builder, including Top 100, rather than sharing the unified ranking browser control model.
- Suggested Fix: Migrate Honor rankings to the shared ranking payload/view model while preserving the legacy command path.
- Impact: medium
- Risk: low
- Dependencies: Phase 5 shared ranking browser.
```

## 8. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation to map command, view, service, DAL, renderer, cache, export, and legacy-command impact. |
| `k98-discord-command-feature` | use | Required because this task changes slash command output, views, buttons, selects, pagination, embeds/images, and interaction callbacks. |
| `k98-sql-validation` | use | Required because KVK, Honor, and PreKvK rankings are SQL/cache-backed and may depend on stored procedures/views/export tables. |
| `k98-test-selection` | use | Required before validation to select ranking, command, view, renderer, export, and regression tests. |
| `k98-deferred-optimisation-capture` | use if needed | Required if audit finds out-of-scope debt in ranking builders, views, caches, SQL contracts, or legacy commands. |
| `k98-pr-review` | use | Required before PR handoff. |
| `k98-promotion-check` | use | Required before production promotion or bot-machine deployment. |
| `codex-security:security-scan` | use for implementation | Required because Discord interactions, SQL/cache-backed data, user-controlled selections, generated files, and exports may be touched. |

## 9. Mandatory Workflow

Default workflow:

1. Audit current ranking commands, views, data sources, and usage evidence, then stop for approval.
2. Produce a current behaviour map and UX findings.
3. Validate ranking data contracts against `C:\K98-bot-SQL-Server` and current cache/service modules.
4. Produce an option matrix and recommended staged implementation plan.
5. Stop for operator approval before implementation.
6. Implement only the approved sub-phase.
7. Add/update focused tests and generate visual samples where output changes.
8. Run focused validation plus standard validators.
9. Run or document Codex Security review.
10. Prepare PR and promotion notes.

Proceed in one pass only if the operator explicitly approves one-pass implementation.

## 10. Audit Requirements

Review and document:

- `/kvk rankings` command path in `commands/kvk_cmds.py`.
- Legacy `/kvk_rankings` command path if still active.
- Legacy `/honor_rankings` command path if still active.
- Legacy `/prekvk report` path and whether it is the same journey as `/kvk rankings type:prekvk`.
- `build_KVKrankings_embed.py` formatting, sanitisation, field mapping, filtering, sorting, pagination, and footer behaviour.
- `ui/views/stats_views.py::KVKRankingView` metric selector, Top-N buttons, Top 100 pagination, response editing, timeout, and failure handling.
- `honor_rankings_view.py::HonorRankingView` independent button model, Top 100 support, data refresh, and response fallback behaviour.
- `ui/views/prekvk_report_views.py::PreKvkReportView` sort selector, limit buttons, author guard, rendering path, and channel posting behaviour.
- `prekvk.report_service`, `prekvk.models`, and `prekvk.report_image_renderer` where available in the repo.
- `stats_alerts.honors.get_latest_honor_top` and underlying SQL/data source.
- `utils.load_stat_cache` and player stats cache contracts used by KVK rankings.
- Historical KVK data sources suitable for all-time records, likely including the same SQL-backed history contracts validated during Phase 4B and any KVK all-player/all-KVK views.
- Any current SQL views/procedures used for KVK, Honor, PreKvK, or all-time performance records.
- Existing tests for KVK rankings, Honor rankings, PreKvK reports, command routing, command registration, and UI imports.
- Usage logs for ranking type, Top-N selection, pagination, and Top 100 if usage tracking has enough data.
- Channel restrictions, admin override differences, visibility differences, and requester guards.
- Current behaviour on empty data, stale cache, cache load failure, SQL failure, and renderer failure.
- Readability on desktop and mobile for Top 10, 25, and 50.
- Whether current KVK default metric should remain `power` or shift to `overall`, `kills`, or `kp` based on player value.
- Whether `STATUS = INCLUDED` and `min_power = 40,000,000` should be visible in the footer/filter chip.
- Whether `Top 100` should be removed, hidden, converted to export, or retained as advanced/admin-only.
- Whether all-time records should use command choice `records`, `hall_of_fame`, or `all_time`.
- Which all-time record metrics are reliable enough for Phase 5, especially kills, KillPoints, deads, DKP, healed, acclaim, honor, and PreKvK.
- Whether historical missing/uncollected values are distinguishable from true zeroes for every proposed record metric.
- Whether all-time record rows should allow the same governor to appear multiple times. Starting recommendation: yes, because these are greatest performances, not unique-player standings.

## 11. Architecture Targets

| Concern | Target |
|---|---|
| Slash command | Preserve `/kvk rankings` with delivered `type:records`; do not add a new top-level records command. |
| Legacy commands | Preserve `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` during rollout. |
| Service/payload | Add or refine renderer-independent ranking payload/model code for current rankings and all-time records. |
| DAL/cache | Keep SQL/cache access in service/DAL/cache layers, not views/renderers. |
| Views | Shared ranking browser view owns interaction flow only. |
| Renderer | Top 10 card renderer can use Pillow; embed/table renderer consumes same payload. |
| Export | Full-list/deeper output should be CSV/export rather than primary Top 100 UI. |
| Records/Hall of Fame | Preserve the delivered records service/data contract for all-time single-KVK performances; keep records Top 10 only. |
| Assets | Use existing KVK card background provider or create ranking/records-specific assets under `assets/kvk/cards/` only if needed. |
| Tests | Focused tests under `tests/` for service, payload, sorting, filtering, pagination, command routing, renderer, and export. |
| Docs | Programme/task-pack docs and canonical command reference if visible behaviour changes. |

## 12. Likely Files

### Review

- `commands/kvk_cmds.py`
- `commands/stats_cmds.py` or equivalent legacy command modules for `/kvk_rankings` and `/honor_rankings`
- `build_KVKrankings_embed.py`
- `ui/views/stats_views.py`
- `honor_rankings_view.py`
- `ui/views/prekvk_report_views.py`
- `prekvk/report_service.py`
- `prekvk/models.py`
- `prekvk/report_image_renderer.py`
- `stats_alerts/honors.py`
- Phase 4B history service/DAL/model modules if reused for all-time record source contracts
- `utils.py` / cache-loading helpers
- `constants.py`
- existing ranking, honor, prekvk, command, and UI tests
- SQL repo objects backing current KVK rankings, Honor rankings, and PreKvK reports

### Modify

Exact files should be decided after audit. Likely candidates:

- `commands/kvk_cmds.py`
- `ui/views/kvk_rankings_view.py` or a new shared ranking view module
- `services/kvk_rankings_service.py` or a ranking subsystem service module
- `services/kvk_records_service.py` or a records submodule if all-time records are split from current rankings
- `kvk/models/kvk_rankings_payload.py` or equivalent model module
- `kvk/models/kvk_records_payload.py` or equivalent if records need a distinct payload
- `kvk/rendering/kvk_rankings_renderer.py` if Top 10 image output is approved
- `kvk/rendering/kvk_records_card_renderer.py` if Hall of Fame card output is approved
- `build_KVKrankings_embed.py` if retained as wrapper/fallback
- `honor_rankings_view.py` if migrated or wrapped into shared view
- `ui/views/prekvk_report_views.py` only where integration is required
- focused tests
- programme/task-pack docs after delivery
- `docs/reference/canonical_command_reference.md` if visible command behaviour changes

### Create

Potentially:

- `kvk/models/kvk_rankings_payload.py`
- `kvk/services/kvk_rankings_service.py`
- `kvk/dal/kvk_rankings_dal.py` only if current cache/service access is not sufficient
- `kvk/rendering/kvk_rankings_card_renderer.py`
- `kvk/rendering/kvk_records_card_renderer.py`
- `ui/views/kvk_rankings_browser_view.py`
- `tests/test_kvk_rankings_service.py`
- `tests/test_kvk_rankings_browser_view.py`
- `tests/test_kvk_rankings_renderer.py`
- `tests/test_kvk_records_service.py`
- `tests/test_kvk_records_renderer.py`
- `tests/test_kvk_rankings_cmds.py`

Use existing repository naming conventions if audit finds a better local pattern.

## 13. Optioneering Requirements

Produce at least these options before implementation:

### Option A - Polish Current Separate Outputs

Keep KVK, Honor, and PreKvK as separate current implementations but polish copy, labels, button
states, footer filters, and Top-N controls.

Best when:

- Delivery risk must be very low.
- There is not enough time to introduce a shared ranking payload.

Trade-offs:

- Does not fully deliver the unified product feel.
- Leaves duplicated interaction logic and uneven visual language.

### Option B - Unified Embed Browser First - Recommended Phase 5A Baseline

Introduce a shared ranking payload/service and shared browser controls, but keep the main output as
clean Discord embeds/tables for Top 25 and Top 50. Add clear mode/metric selectors and remove Top
100 from primary controls unless usage evidence says otherwise.

Best when:

- Stability and readability matter more than a full visual leap.
- The ranking data contract needs unification before advanced card rendering.

Trade-offs:

- Less visually impressive than the new stats/targets/history cards.
- Still partly table-based.

### Option C - Top 10 Spotlight Card Plus Embed Browser - Recommended End-State

Build Option B foundation, then add a generated Top 10 spotlight card for KVK/Honor/PreKvK modes.
Top 25/50 remain embed/table or compact image depending on readability.

Best when:

- Top 10 is the most shareable, repeated, social output.
- The new KVK visual language should be visible in rankings without making Top 50 unreadable.

Trade-offs:

- Requires visual review and renderer tests.
- More implementation surface than embed-only.

### Option D - Full Image Leaderboard

Render Top 10, 25, and 50 as generated images.

Best when:

- Visual polish is the top priority and the renderer can remain readable.

Trade-offs:

- Risk of unreadable dense output on mobile.
- More maintenance and fitting complexity.
- Less accessible/searchable than embeds and CSV.

### Option E - Data-First Export/CSV Model

Keep the public display limited to Top 10/25 and provide CSV export for everything else.

Best when:

- Top 50/100 are mainly admin/deep-analysis outputs.

Trade-offs:

- May reduce the popular public Top 50 behaviour.
- Less engaging for players.


### Option F - Hall of Fame / All-Time Records Mode - Delivered Phase 5A Foundation

Phase 5A added a `records` ranking mode showing Top 10 all-time single-KVK performances across
collected KVK history.

Best when:

- The goal is to add excitement and replay value, not just modernise current tables.
- Historical data is reliable enough to rank single-KVK performances across KVKs.
- Players would enjoy seeing all-time record holders and legendary repeated performances.

Trade-offs:

- Requires careful SQL/data-contract validation across all KVKs.
- Missing historical fields, especially acclaim and healed, must not be ranked as true zeroes.
- The same player may appear multiple times, which is desirable for performance records but should
  be clearly explained.
- May need a distinct card design language from current live rankings.

Follow-on recommendation:

- Keep it under `/kvk rankings type:records`.
- Preserve the first-release Top 10-only control model.
- Render Top 10 records as a visual card in the later card phase; do not build Top 25/50 all-time
  records unless player usage later proves demand and the operator approves it.

## 14. Approved Starting Recommendation For Codex To Test

The working recommendation is:

1. **Phase 5A: Audit, data contract, Hall of Fame foundation, and first control policy**
   - Complete. Delivered in mirror PR #152 and production PR #461, then smoke tested in production.
   - Added `/kvk rankings type:records` under the existing command surface.
   - Built the Top 10 KD98 Hall of Fame single-KVK records foundation.
   - Validated first-release records against the existing historical KVK source path.
   - Added shared ranking payload/model/service/DAL/rendering foundations for records.
   - Removed Top 100 from primary KVK/Honor player controls.

2. **Phase 5B: Unified current-ranking embed browser**
   - Complete. Delivered in mirror PR #153 and production PR #462, then smoke tested in
     production.
   - Added shared mode/metric/Top-N controls for current KVK, Honor, and PreKvK rankings.
   - Primary Top-N buttons are Top 10, Top 25, and Top 50.
   - Kept Top 100 out of primary controls.
   - Added consistent footer/filter/source/freshness information.
   - Preserved delivered Hall of Fame records mode and kept it Top 10 only.
   - Preserved legacy commands.
   - Captured My Rank/export and legacy-ranking consolidation as deferred Phase 5 work.
   - Hardened Honor browser mode switching so it cannot bypass the stricter channel gate.
   - Smoke-polished KVK table layout to keep Top 10 rows one line per row.

3. **Phase 5C: Current KVK Top 10 visual spotlight card**
   - Complete. Delivered in mirror PR #154 and production PR #463, then smoke tested and polished
     in production.
   - Added current KVK Top 10 visual ranking cards for Kills, % Kill Target, Deads, DKP, Acclaim,
     and Tanking Score.
   - Defaulted KVK rankings to Kills.
   - Kept Power for Top 25/50 compact browser analysis, but removed it from the Top 10 card metric
     set.
   - Preserved Top 25/50 compact browser output, embed fallback, Top 100 exclusion, records Top 10
     only, legacy commands, and image-based legacy `/prekvk report`.

4. **Phase 5D: Hall of Fame records Top 10 visual cards**
   - Complete. Delivered in mirror PR #155 and production PR #464, then smoke tested and polished
     in production.
   - Added Hall of Fame cards for all existing all-time single-KVK record categories.
   - Used the delivered records payload/DAL/service rows rather than recalculating records in the
     renderer.
   - Added metric-specific qualifying record counts for `Top 10 from N records` wording.
   - Kept records Top 10 only; no records Top 25, Top 50, or Top 100 controls were added.
   - Preserved current KVK Top 10 cards, compact browser output, embed fallback, legacy commands,
     repeated-governor appearances, missing historical metric exclusion, and image-based legacy
     `/prekvk report`.
   - Preserved Honor and PreKvK for the next visual-card slice rather than expanding 5D.

5. **Phase 5E: Honor and PreKvK Top 10 visual cards**
   - Next active sub-phase.
   - Audit Honor and PreKvK card value, freshness wording, support values, and visual hierarchy.
   - Add visual Top 10 cards for one or both modes using the shared ranking payloads.
   - Preserve Honor's no-admin-override KVK stats channel gate.
   - Preserve legacy `/prekvk report` as image-based unless a later approved phase explicitly
     changes it.
   - Keep Top 25 and Top 50 on the compact unified browser unless separately approved.

6. **Phase 5F: My Rank / Find Me and export polish**
   - Add private local-position view for registered governors.
   - Add full-list CSV/export if Top 100 is removed.
   - Add records export/detail output only if useful after the Top 10 card is validated.
   - Consider legacy redirect only after usage review and separate approval.

7. **Phase 5G+: Remaining rankings deferred optimisation closure**
   - Deliver any structured Phase 5 deferred optimisations that remain after 5B-5F.
   - Add extra sub-phases rather than leaving known rankings UX, architecture, export, or visual
     debt unresolved at the end of Phase 5.

Do not merge these sub-phases into one PR unless explicitly approved.

## 15. Ranking Payload Requirements

Create or refine a renderer-independent payload able to represent:

- mode: `kvk`, `honor`, `prekvk`, and optionally `records` / `hall_of_fame`
- KVK number and KVK name/mode where available
- selected metric and metric label
- selected limit: 10, 25, or 50
- page number and total pages where pagination is needed
- filters applied, such as `STATUS = INCLUDED` and minimum power
- generated/refreshed timestamp
- source state: fresh, stale, unavailable, partial, or empty
- rows with rank, governor ID, governor name, alliance/kingdom/camp if available, primary metric value, and supporting metrics
- record rows with record value, KVK number, KVK name/mode, and enough context to show that the row is a single-KVK historical performance
- top 3 / podium markers
- requester/account context for `My Rank` where applicable
- export availability and filename/context if implemented

The service should own:

- filtering rules;
- sort semantics;
- tie-breakers;
- missing-value handling;
- limit normalization;
- rank calculation;
- row slicing/pagination;
- source/freshness metadata;
- for all-time records, metric eligibility and null/missing-value exclusions across historical KVKs.

Renderers and views must not calculate source-of-truth ranking semantics.

## 16. Output Requirements

### 16.1 Unified browser

The browser should clearly show:

- current mode and metric;
- current Top-N selection;
- ranking rows;
- freshness/source information;
- filters applied;
- empty/failure state;
- controls that remain in sync after interactions.

### 16.2 KVK ranking output

Audit whether current default should remain `Power`. Strongly consider defaulting to a more KVK
meaningful metric if available, such as `Overall`, `Kills`, `KP`, or `DKP`.

The KVK mode should support at least:

- Power
- Kills / T4+T5 Kills
- `% Kill Target`
- Deads
- DKP

Audit and add only if reliable:

- KVK Overall
- KillPoints/KP
- Acclaim/contribution
- tanking score
- pass-window metrics

### 16.3 Honor ranking output

Honor should look like part of the same ranking browser, not a separate simple list.

Minimum output:

- rank
- governor name
- governor ID if name is missing or optional in footer/detail
- honor points
- KVK/source freshness where available

### 16.4 PreKvK ranking output

PreKvK currently has a richer image/report path. Do not regress it.

Minimum integration:

- keep Overall, Stage 1, Stage 2, Stage 3 sort options;
- align limit controls with Top 10/25/50 if supported by `PREKVK_REPORT_LIMITS`;
- align public/private response behaviour deliberately;
- preserve author guard where appropriate;
- keep image renderer if it remains better than embed.

### 16.5 Top 10 visual card

If image output is approved, Top 10 card should include:

- title: mode + metric + current KVK context;
- podium/top 3 visual emphasis;
- ranks 4-10 as clean rows;
- primary metric value;
- one or two supporting stats only;
- filters/freshness footer;
- no dense 7-column table on the card;
- embed fallback if rendering fails.

### 16.6 Top 25 and Top 50

Top 25 and Top 50 must remain readable on Discord mobile.

Do not force every metric into every row. For each ranking mode, choose:

- rank;
- governor name;
- primary metric;
- one or two useful supporting metrics;
- optional footer/context for the rest.

For deeper analysis, prefer CSV/export.

### 16.7 Top 100 decision

Top 100 should not be a primary visible button unless usage audit proves it is meaningfully used.

Preferred handling:

- remove from primary player controls;
- preserve legacy Top 100 where necessary during rollout;
- add `Export` or `Full List CSV` for all rows;
- document the Top 100 decision in the delivery notes.


### 16.8 Hall of Fame / all-time records output

If approved, records mode should be visually distinct from current KVK rankings.

Recommended default output:

```text
KD98 Hall of Fame
Top 10 All-Time Kills
```

Controls:

- metric selector: Kills, KP, Deads, DKP, Healed, Acclaim, Honor, PreKvK where validated;
- Top 10 only in the first release;
- optional export/detail after the card is validated;
- no Top 25/50/100 controls for records unless later approved.

Each record row should show:

- rank;
- governor name;
- record value;
- KVK number;
- KVK name/mode where available;
- optional Governor ID in detail/footer/fallback rather than cluttering the main card.

Design notes:

- Repeated player appearances are allowed and expected.
- Title/copy must make clear that these are all-time single-KVK performances, not current rankings
  and not lifetime totals.
- Missing historical metrics must be excluded from that metric's record ranking, not treated as
  zero.
- If a metric only exists from recent KVKs, include a footer/note such as `Metric collected from
  KVK X onward` if the source contract can identify that boundary.

## 17. Command Surface Governance

- [ ] State whether the task changes top-level command count, grouped subcommand count, or neither.
- [ ] No new top-level command.
- [ ] No new grouped subcommand unless separately approved.
- [ ] Preserve `/kvk rankings` registration.
- [ ] Preserve existing `/kvk rankings type` choices unless visible option changes are explicitly approved.
- [x] `records` is now a visible `/kvk rankings type` choice; command docs, registration tests, usage routing, and smoke-test references were updated in Phase 5A.
- [ ] Preserve legacy ranking commands during rollout.
- [ ] Preserve or explicitly update `@versioned()`, `@safe_command`, `@track_usage()`, channel guards, admin override differences, visibility behaviour, autocomplete/options, usage-log identity, and command-cache behaviour.
- [ ] If any command description or visible behaviour changes, update `docs/reference/canonical_command_reference.md`.
- [ ] Run or justify skipping `scripts/validate_command_registration.py`, `tests/test_validate_command_registration.py`, `tests/test_command_inventory.py`, and `tests/test_command_registration_smoke.py`.

## 18. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| KVK ranking builder mixes formatting, filtering, sorting, and Discord embed output | fix in Phase 5B where practical | Shared ranking payload is needed before a smart browser or card renderer. |
| Honor ranking has separate Top-N/button/output implementation | fix or wrap in Phase 5B | Ranking modes should feel unified. |
| PreKvK already has image renderer but independent flow | preserve and integrate carefully | Do not regress working output; align controls where practical. |
| Top 100 appears unused | likely remove from primary player UI | Replace with My Rank and/or export unless usage data contradicts. |
| All-time records are now exposed as `/kvk rankings type:records` | preserve in Phase 5B | Phase 5A delivered Top 10 Hall of Fame records; later visual/export polish can build on it without expanding first-release controls. |
| Ranking default metric is Power | audit | Power may not be the most meaningful KVK leaderboard default. |
| My Rank is absent | likely add if feasible | Better player value than a long Top 100 table. |
| Pass-window / movement / trend rankings | defer unless approved | Risk of data-contract expansion and confusing semantics. |
| Legacy commands remain live | not applicable | Parallel rollout is intentional. |

Add further rows based on actual findings. Deferred items must use the structured format from
`docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 19. Testing Requirements

Cover or justify:

- `/kvk rankings type:kvk` happy path.
- `/kvk rankings type:honor` happy path.
- `/kvk rankings type:prekvk` happy path.
- Legacy `/kvk_rankings` remains live where applicable.
- Legacy `/honor_rankings` remains live where applicable.
- Legacy `/prekvk report` remains live.
- KVK ranking metric selection.
- Honor ranking refresh.
- PreKvK sort selection.
- Top 10, 25, and 50 limit behaviour.
- Top 100 removal/hiding/export decision.
- `/kvk rankings type:records` or equivalent new choice if approved.
- All-time records metric selection.
- All-time records sorting across multiple KVKs.
- All-time records allow repeated governor appearances unless a different rule is approved.
- All-time records exclude missing/uncollected values rather than ranking them as zero.
- Pagination when visible.
- Button/select state sync.
- Author guard for private/requester-specific controls.
- Public vs private response behaviour.
- Empty cache/data behaviour.
- Stale cache/freshness footer behaviour.
- SQL/cache failure fallback.
- Renderer failure fallback if image output is added.
- CSV/export content if export is added.
- Hall of Fame card renderer fallback if records image output is added.
- `My Rank` registered-account, multi-account, no-account, not-ranked, and missing-governor paths if implemented.
- Filtering and tie-breaker correctness.
- Missing-value handling without misleading zeroes.
- Command registration unchanged.

Suggested focused tests after audit, adapt to actual files:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_cmds.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_service.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_browser_view.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_renderer.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_honor_rankings.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_prekvk_report_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py
```

Suggested standard validation:

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

Visual validation if image output changes:

- Generate Top 10 KVK ranking card sample.
- Generate Top 10 Hall of Fame / all-time records card sample for at least kills and one historically sparse metric such as acclaim or healed if validated.
- Generate Top 10 Honor ranking card sample.
- Generate Top 10 PreKvK ranking card sample if PreKvK image output is changed.
- Generate Top 25 and Top 50 browser samples.
- Inspect desktop and mobile-like readability.
- Confirm long names, missing names, high values, ties, and empty values do not clip or mislead.

## 20. Acceptance Criteria

Audit/optioneering acceptance:

- [x] Current KVK, Honor, and PreKvK ranking behaviours are mapped for the Phase 5B browser.
- [x] Current data contracts and SQL/cache source objects are validated or ambiguities documented
  for the Phase 5B browser.
- [ ] Current usage evidence for Top 10/25/50/100 is reviewed where available.
- [x] Top 100 recommendation is explicitly documented for current-ranking primary controls.
- [x] Hall of Fame / all-time records feasibility is audited against SQL/data contracts for the first release.
- [x] Records command placement is delivered as `/kvk rankings type:records`; no new top-level command.
- [ ] At least four viable output options are compared with trade-offs.
- [x] A recommended staged solution is proposed.
- [ ] No implementation occurs before approval unless explicitly approved.

Implementation acceptance:

- [x] `/kvk rankings` feels like one coherent browser across KVK, Honor, and PreKvK.
- [x] Top 10, Top 25, and Top 50 are fast, readable, and stable in the unified embed browser.
- [x] Top 100 is removed from primary player controls or retained with evidence-backed justification.
- [x] Hall of Fame / all-time records mode is implemented as the Phase 5A Top 10 foundation.
- [x] All-time records clearly show single-KVK performance context and do not imply lifetime totals.
- [x] Historical missing/uncollected record metrics are excluded or labelled safely.
- [x] `My Rank` / local-position flow is implemented or explicitly deferred with reason.
- [x] Legacy ranking commands remain live during rollout.
- [x] No new direct SQL exists in command, view, or renderer modules.
- [x] Data shaping/filtering/sorting lives in service/model/DAL layers.
- [x] Commands and views remain thin.
- [x] Fallback behaviour remains useful if data or rendering fails.
- [x] Output is readable on Discord mobile for the Phase 5B embed browser after smoke polish.
- [x] Focused tests pass.
- [x] Standard validators pass or skips are documented.
- [x] Visual review artifacts are generated when image output changes.
- [x] Codex Security review is run or explicitly skipped based on risk triggers.
- [x] Deferred optimisations are captured structurally.
- [x] Programme/task-pack docs are updated after delivery.

## 21. Required Delivery Output

For the audit/optioneering stage:

1. Summary
2. Current Behaviour Map
3. Data Contract Findings
4. Usage Findings, especially Top 10/25/50/100
5. UX Findings
6. Architecture Findings
7. Option Matrix
8. Recommended Option
9. Proposed Sub-Phase Plan
10. Top 100 Decision
11. Hall of Fame / All-Time Records Decision
12. My Rank Decision
13. Test Strategy
14. Risks / Open Questions
15. Deferred Optimisations

For implementation stages:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. SQL Validation Evidence
7. Command Surface Changes
8. User-Visible Behaviour Changes
9. Data Contract / Payload Summary
10. Renderer / Output Summary
11. Export / Top 100 Decision
12. Hall of Fame / All-Time Records Behaviour
13. My Rank Behaviour
14. Helpers Reused
15. Refactor Findings
16. Test Plan and Results
17. Visual Review Evidence
18. AI Review Gates
19. Deployment Steps
20. Rollback Plan
21. Deferred Optimisations

## 22. PR Summary Template

```md
## Summary

- Modernised the unified `/kvk rankings` browser according to the approved Phase 5 scope.
- Preserved legacy ranking command paths during rollout.
- Improved Top 10/25/50 ranking UX and documented the Top 100 decision.
- Added or scoped KD98 Hall of Fame / all-time single-KVK performance records where approved.

## Changes

- <ranking service/payload/view/renderer changes>
- <KVK/Honor/PreKvK/Records behaviour changes>
- <tests/docs updates>

## SQL Changes

- None, or list companion SQL PR and deployment order.

## Tests

- <focused pytest/validators/manual visual checks>

## Visual Review

- <generated sample paths and desktop/mobile readability notes, if image output changed>

## AI Review Gates

- Codex Security: <run | skipped, with reason>

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Risk: rankings are high-traffic public KVK outputs; regressions will be visible immediately.
- Risk: all-time records can mislead players if historical missing values are treated as real zeroes or if single-KVK records are confused with lifetime totals.
- Mitigation: shared payload tests, focused view tests, historical null-handling tests, visual review, legacy command preservation, and embed fallback.
- Rollback: revert `/kvk rankings` wiring to the current KVK/Honor/PreKvK handlers while leaving legacy commands live.
```

## 23. Codex Chat Starter

Historical starter for Phase 5A. Phase 5A, Phase 5B, Phase 5C, and Phase 5D are complete; use
`docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5E Honor and PreKvK Visual Ranking Cards.md`
for the next delivery chat.

```text
Codex, start Phase 5 of the KVK Player Experience Redesign: Unified /kvk rankings Visual/UX Polish.

Phase 4 is complete: /kvk stats, /kvk targets, and /kvk history are now modernised and promoted to production. Phase 5 now needs serious audit, UX design, and staged implementation planning for /kvk rankings, covering KVK rankings, Honor rankings, PreKvK rankings, and a proposed KD98 Hall of Fame / all-time records mode.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/KVK Player Experience Redesign - Programme Pack.md
- docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 4 Modern Targets and Full History.md
- docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 4B History Audit and Optioneering.md
- docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 5 Unified Rankings Visual UX Polish.md

Current context:
- /kvk rankings already exists as a scaffold with type choices: kvk, honor, prekvk.
- Current KVK rankings use build_KVKrankings_embed.py and ui/views/stats_views.py::KVKRankingView.
- Current Honor rankings use honor_rankings_view.py::HonorRankingView.
- Current PreKvK rankings use ui/views/prekvk_report_views.py::PreKvkReportView and prekvk.report_image_renderer.
- Players use Top 10, Top 25, and Top 50 heavily. Top 100 appears unused and should not remain a primary player button unless usage evidence proves otherwise.
- The goal is not just to make a prettier table. Build a smart ranking browser that answers who is leading, who is close, where the player ranks, and which leaderboard matters right now.
- Add a serious audit/design recommendation for a Hall of Fame / all-time records mode showing Top 10 single-KVK performances across all collected KVKs: kills, KillPoints, deads, DKP, healed, acclaim, honor, and PreKvK where validated.
- Records should be single-KVK performances, not lifetime totals. The same governor may appear multiple times if they hold multiple all-time performances.

Start with audit and optioneering only unless explicitly approved to implement:
1. Map current KVK/Honor/PreKvK ranking behaviours and source data contracts.
2. Validate SQL/cache sources against C:\K98-bot-SQL-Server where applicable.
3. Review usage logs for Top 10/25/50/100 if available.
4. Audit all-time records feasibility across historical KVK SQL/data sources, including missing/null handling for healed and acclaim.
5. Propose a unified Ranking Hub design with mode/metric selectors, Top 10/25/50 controls, Top 100/export decision, Hall of Fame records mode, and a possible My Rank / Find Me flow.
6. Recommend staged implementation, likely: 5A audit/foundation, 5B Hall of Fame records foundation, 5C unified current-ranking browser, 5D Top 10 visual cards, 5E Honor/PreKvK cards, 5F My Rank/export polish.
7. Stop for approval before implementation.

Do not remove legacy commands. Do not add a new top-level command. Do not put SQL in command/view/renderer modules. Do not create `/kvk records` in Phase 5 unless separately approved; prefer `/kvk rankings type:records` or equivalent if the records mode is approved. Capture out-of-scope findings as structured deferred optimisations.
```
