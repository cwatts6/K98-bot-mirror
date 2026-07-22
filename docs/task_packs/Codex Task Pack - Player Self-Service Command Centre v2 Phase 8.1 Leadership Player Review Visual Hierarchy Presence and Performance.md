# Codex Task Pack - Player Self-Service Command Centre v2 Phase 8.1 Leadership Player Review Visual Hierarchy, Presence and Performance

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 8.1 Leadership Player Review Visual Hierarchy, Presence and Performance`
- Date: `2026-07-21`
- Owner/context: `KD98 / Kingdom 1198 follow-up after accepted Phase 8 leadership /stats player delivery`
- Task type: `leadership UX refinement | derived activity signal | renderer/layout | SQL and bot performance audit | optional evidence-led optimisation`
- One-pass approved: `no`
- Product scope approved: `yes`
- Runtime implementation approved: `yes; operator approved the audited bot scope and additive Last Active procedure on 2026-07-21`
- Status: `implementation complete; validation, representative production measurement, review and deployment pending`
- Canonical command: `/stats player`
- Command change: `none`
- Command baseline and target: `36 top-level / 100 grouped / 8 /me / 1 /stats / 2 /inventory`
- Command resync expected: `no; revalidate and resync only if the audit proves a registration change`
- SQL deployment: `approved additive dbo.usp_GetLeadershipPlayerLastActive only; no table or index change`
- Background asset: `assets/stats/cards/stats_player.png`

## 2. Required Reading

Read the current versions before any implementation:

1. `AGENTS.md`
2. `README-DEV.md`
3. `docs/reference/README.md`
4. `docs/reference/K98 Bot - Project Engineering Standards.md`
5. `docs/reference/K98 Bot - Coding Execution Guidelines.md`
6. `docs/reference/K98 Bot - Testing Standards.md`
7. `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
8. `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
9. `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
10. this task pack and its matching chat starter
11. archived Phase 8 task pack and closeout record
12. archived accepted Phase 7 task pack for the inherited visual/lifecycle contract
13. Phase 9 `/stats kingdom` task pack only to prevent overlap
14. `docs/player_self_service_command_centre_briefing.md`
15. `docs/reference/canonical_command_reference.md`
16. `docs/reference/deferred_optimisations.md`
17. relevant root and nested `SECURITY.md` files
18. authoritative SQL repository `C:\K98-bot-SQL-Server`

Use additional references only when the task audit proves they apply.

## 3. Objective

Refine the accepted private `/stats player` experience so each page has a clearer purpose, make
presence, recent activity, location and shield context useful at a glance, improve KVK and Player
Record readability, and measure then reduce avoidable first-load and period-change latency without
weakening the Phase 8 data, authorization, privacy, lifecycle, or coverage contracts.

Phase 8.1 is a refinement of the accepted Phase 8 product. It is not a replacement leadership
command, a metric redesign, a public sharing feature, or permission to create speculative SQL
tables or indexes.

## 4. Background

Phase 8 is complete after successful SQL-first deployment, bot restart/resync, production smoke,
data-source correction, KVK final-history backfill, crash correction, and operator acceptance on
2026-07-21. It delivered the one approved private leadership player-review command, retired
`/player_profile`, aligned canonical combat metrics globally, and established the bounded
leadership SQL, audit, lookup, history, source-completion, renderer and interaction contracts.

Production smoke proved the data is now available and materially correct, but also showed that:

- Overview duplicates three metrics already owned by Kingdom Activity;
- Presence, location and shield context are too visually quiet for the decisions Overview should
  support;
- Kingdom Activity and KVK Performance can use the space released by removing repeated location
  context;
- three completed KVK rows are difficult to compare in the current full-width stack;
- Player Record repeats Governor IDs and limits readable identity/alliance history presentation;
- cold first load and especially 360-day period changes need measured performance analysis.

## 5. Scope

### In Scope

#### Overview purpose and hierarchy

- Remove the Overview cards for Forts Total, Helps and Tech Donations. These remain unchanged and
  fully available on Kingdom Activity.
- Keep Activity Index v1 on Overview with its existing six-component formula, coverage, ranking,
  missing-value and reset semantics.
- Promote Presence to a primary Overview element adjacent to Activity Index.
- Present Presence as both an exact scan ratio and a percentage, for example:

```text
Presence
185 / 191 scans
97%
```

- Add `Last Active Date` and a separate active/inactive classification using the exact contract in
  section 12.
- Make latest X:Y, location-updated UTC and shield status materially larger and easier to scan.
- Keep location freshness separate from governor/source freshness.
- Keep the common governor header, period, dates, valid source observations and primary
  CURRENT/STALE/PARTIAL/NO DATA badge.
- Retain leadership prompts only if they still fit honestly after the new hierarchy. Do not make
  prompts more prominent than Presence, Activity, location or shield.

#### Kingdom Activity layout

- Keep the common governor header and all six accepted activity metrics, values, averages,
  comparisons, ranks, percentiles, coverage and reset warnings unchanged.
- Remove the repeated latest X:Y/location/shield strip from this page.
- Use the released vertical space to enlarge the six metric panels and their key typography.
- Preserve genuine zero, missing, partial coverage, reset-exclusion and unavailable distinctions.

#### KVK Performance layout

- Remove the repeated latest X:Y/location/shield strip.
- Continue to show exactly the latest three eligible completed/finalized KVKs and `valid x/3`.
- Replace the vertical full-width stack with three side-by-side KVK cards on the `1702x924`
  proportional baseline.
- Each populated card must retain, with readable hierarchy:
  - KVK number, `KVK_NAME`, and KVK rank;
  - T4+T5 kills and target percentage;
  - Kill Points;
  - Deads and target percentage;
  - Healed and engaged-cohort Healed rank;
  - KP Loss;
  - Tanking Score and engaged-cohort Tanking rank;
  - Acclaim, personal completed-KVK best context and percentage of best;
  - DKP and target percentage;
  - Pre-KVK points/rank;
  - Honor points/rank;
  - exemptions and honest missing-value treatment where applicable.
- Remove final data date/time/state from the visible KVK cards.
- Remove visible `MET` / `NOT MET` words. Preserve the numeric target percentages and the
  underlying target, exemption, missing and eligibility semantics.
- Preserve higher-is-better canonical Tanking Score and lower-is-better Healed ranking semantics.
- Keep latest-versus-previous and previous-two-average context only when it remains readable and
  is not contradicted by missing/exempt data.
- Render honest NO DATA/UNAVAILABLE states for fewer than three valid KVKs; never repeat or invent
  a KVK to fill a column.

#### Player Record readability

- Rename `Alliance Episodes` to `Alliances`.
- Group Aliases by Governor ID with one visible Governor ID heading rather than repeating it on
  every alias row.
- Show each alias on a readable row using the accepted content pattern:

```text
Governor ID 35711701
TroIl       1st 16 May 24   last 21 Jul 26   577 scans
JohnPaulV   1st 15 Oct 25   last 25 Oct 25    37 scans
```

- Apply the same grouped structure to Alliances: one Governor ID heading followed by alliance,
  first observed, last observed and scan-count rows.
- Preserve all alias rows returned by the bounded identity-history contract. Do not impose a silent
  five-row renderer limit.
- Page deterministically when the full Alias/Alliance content does not fit.
- Preserve leave-and-return alliance episodes, blank-while-present `Unallied`, and the rule that a
  missing governor scan is not an Unallied observation.
- Preserve active linked-governor navigation and its privacy contract.

#### Performance assessment and evidence-led improvement

- Measure cold and warm first load plus 30/90/180/360 period transitions before changing the data
  architecture.
- Attribute latency across authorization/lookup, SQL calls, result mapping, KVK resolution,
  payload construction, rendering/PNG encoding, attachment replacement, cache and inflight work.
- Capture actual SQL execution plans, `STATISTICS IO`, `STATISTICS TIME`, row counts, result-set
  sizes, duration and concurrency behavior for the authoritative leadership procedures.
- Test representative governors: recent and long-tenure, sparse and dense activity, one and three
  finalized KVKs, and high alias/alliance history.
- Compare cold cache, warm cache and bounded concurrent leadership reads.
- Assess page-specific lazy loading, result-set splitting, cache granularity, query changes,
  pre-aggregation and supporting SQL objects as candidates—not preselected solutions.
- Propose the smallest evidenced change. Any new maintained table must define refresh ownership,
  transactionality, staleness, repair/backfill, monitoring, deployment order and rollback.
- Any index must be justified by actual plan/read/timing evidence and concurrency impact.
- Record an operator-approved performance budget after the baseline. Do not claim success solely
  because Discord was deferred in time.

#### Documentation and rollout

- Update the renderer contract, method/definitions copy, smoke guide, task-pack index, programme
  pack, briefing and deferred register.
- Run focused and full validation in proportion to the final change.
- Run bot Changes security review with Deep off.
- Run a separate SQL Changes review with Deep off only if an approved SQL diff exists.
- Deploy SQL before bot only when the approved solution contains SQL changes.

### Out of Scope

- A new command, subcommand, alias, redirect, public share or export.
- Restoring `/player_profile`, creating `/me inspect`, or changing `/stats kingdom` Phase 9.
- Changing the dedicated Phase 8 leadership permission matrix or making output public.
- Changing Activity Index weights, ranking equations, KVK formulas, target definitions or the
  accepted historic completion/backfill evidence.
- Treating a missing scan, missing source row or unavailable metric as zero.
- Using Discord identity, account slot/type, reminders, timezone, language, Inventory or export
  metadata in Player Record.
- A universal renderer/view/payload framework.
- A speculative covering index, materialized snapshot or pre-aggregation table without measured
  evidence and a separately approved SQL contract.
- Live destructive or load testing without explicit operator approval.

## 6. Source Deferred Items

### Deferred Optimisation
- Area: `leadership_player_review` SQL/DAL/service/cache/render path and SQL repository leadership procedures
- Type: performance
- Description: Phase 8 functional smoke succeeded, but cold first load and 360-day transitions are visibly slow. No accepted stage-by-stage timing, actual-plan, logical-read, result-size, cache or concurrency evidence yet identifies the dominant cost.
- Suggested Fix: Phase 8.1 owns a measurement-first investigation and the smallest evidence-led bot and/or SQL refinement. Do not assume a new table or index is required.
- Impact: high
- Risk: medium
- Dependencies: accepted Phase 8 production data, representative Governor IDs, production-safe measurement window, SQL owner approval for plans/reads, and separate SQL review if SQL changes result.

The existing broad renderer-framework deferred item remains deferred. Phase 8.1 is an approved
leadership-specific layout refinement, not evidence for a universal framework.

## 7. Codex Skills To Use

- `k98-architecture-scope` for the initial source, layer, SQL, permission, lifecycle, performance and
  approval-gate audit.
- `k98-sql-validation` before any SQL-facing design or implementation.
- `k98-discord-command-feature` for the private renderer/view/control implementation and specialist
  review.
- `k98-test-selection` for focused/full/visual/performance validation selection.
- `k98-deferred-optimisation-capture` for residual work that remains genuinely out of scope.
- `k98-security-review-routing` before any security workflow.
- `codex-security:security-diff-scan` for the approved bot diff and separately for an approved SQL
  diff, both with Deep off.
- `k98-pr-review` after implementation and validation.
- `k98-promotion-check` before mirror-to-production promotion/deployment.

### Skill Decisions

- Do not use `k98-promotion-check` during audit/design.
- Do not use a standard or deep repository security scan as a routine gate.
- Do not treat test selection, security review or PR review as substitutes for one another.

### Security Review Decision

Bot Changes review is mandatory because the slice touches private arbitrary-Governor-ID output,
location/shield presentation, SQL-backed data, bounded caching and Discord interactions. Deep is
off. Focus on authorization revalidation, target substitution, cache authorization, attachment
privacy, location/shield leakage, pagination tokens, stale interaction races, SQL bounds and error
minimization.

If the SQL repository is unchanged, record a precise SQL-review skip. If SQL changes are approved,
run a separate SQL Changes review with Deep off focused on static parameterization, bounded dates,
execution rights, result minimization, retained audit privacy, refresh/backfill safety and denial of
unbounded reads.

## 8. Mandatory Workflow

1. Audit/scope only, then stop.
2. Present current payload/query/render timing, Last Active source semantics, exact wireframes,
   SQL-impact decision, file manifest, performance experiment and security routing, then stop.
3. If SQL change is recommended, present schema/result sets, plans/read evidence, refresh/backfill,
   deployment and rollback design, then stop for separate approval.
4. Implement only the approved bot and optional SQL scope.
5. Validate focused calculations, DAL/service, renderer/golden, view/lifecycle, registration and
   performance evidence.
6. Run architecture, deferred, selected-test, formatting/type, import, registration, pre-commit and
   log-noise gates as applicable.
7. Run bot Changes security review with Deep off and SQL Changes review only when SQL changed.
8. Complete PR review and address review comments.
9. Deploy SQL first only when required; deploy bot, restart, smoke every page/period, observe and
   promote the exact accepted patch.

No one-pass execution is approved.

## 9. Audit Requirements

The first response must be audit/scope only and must report:

A. current page payload fields, renderer regions, controls and page-specific duplication;
B. exact source and ordering for Presence and each Last Active candidate metric;
C. how consecutive observations are paired without converting absence into zero;
D. reset, duplicate, null, partial, new-arrival and source-completion handling;
E. whether Last Active can be calculated correctly within the existing 720-day bound;
F. exact UTC TODAY/inactive threshold semantics;
G. current Alias and Alliance result-set limits, service mapping, renderer limits and pagination;
H. current latest-three finalized-KVK selection and every field retained/removed visually;
I. cold/warm timing breakdown for representative 30/90/180/360 requests;
J. SQL procedure actual plans, logical reads, elapsed/CPU time, rows and result sizes;
K. cache keys, TTL, inflight deduplication and page/period transition behavior;
L. permission and target revalidation at command entry and every interaction;
M. privacy impact of enlarging location/shield information;
N. proposed renderer wireframes including long Unicode and no-data states;
O. exact bot and optional SQL file manifests;
P. focused/full/visual/performance test selection;
Q. security routing, deployment, smoke and rollback;
R. explicit stop for operator approval.

## 10. Architecture Targets

- Keep command and view adapters thin.
- Preserve the immutable typed `LeadershipPlayerReviewPayload` boundary or an approved compatible
  evolution; do not pass raw SQL rows into rendering.
- Keep Last Active calculation in a pure domain/service helper with SQL/Python parity fixtures if
  SQL contributes the derived date.
- Keep leadership-specific rendering separate from self-view renderers.
- Reuse Phase 8 KVK services and canonical combat helpers; do not copy formulas.
- Keep common header/location/panel primitives bounded to proven identical behavior.
- Prefer page-specific data retrieval only if it materially reduces measured latency and preserves
  same-payload fallback for the page being rendered.
- Preserve latest-transition-wins, attachment replacement, authorization-before-cache/read,
  preserve-and-disable timeout and file/stream cleanup.
- Keep SQL static, parameterized, bounded to at most 720 days and outside commands/views.

## 11. Likely Files

### Review

- `leadership_player_review/commands.py`
- `leadership_player_review/view.py`
- `leadership_player_review/service.py`
- `leadership_player_review/dal.py`
- `leadership_player_review/models.py`
- `leadership_player_review/renderer.py`
- `leadership_player_review/record_paging.py`
- `leadership_player_review/permissions.py`
- `kvk/`, `kvk_state.py`, and canonical combat metric helpers
- Phase 8 leadership tests and visual fixtures
- SQL repository leadership procedures, tables, migrations and plan evidence

### Modify

- Only files proven by the audit and approved manifest.
- Expected bot changes are leadership models/service/DAL only where required for Last Active or
  pagination, leadership renderer/view, tests and documentation.
- SQL files are modified only after an approved evidence-led SQL design.

### Create

- Pure Last Active calculation helper/fixtures if no existing domain module is appropriate.
- Performance evidence artifacts or reproducible bounded harness as approved.
- SQL migration/schema files only when an approved SQL change is required.

## 12. Implementation Requirements

### Last Active Date contract

The accepted Phase 8.1 definition is:

```text
Last Active Date = latest authoritative complete KingdomScanData4 ScanDate, within the available
bounded 720-day history, on which at least one eligible activity value increased relative to the
immediately previous complete kingdom scan in which that Governor ID was present.
```

Eligible values:

1. Power
2. Healed
3. RSS Gathered
4. RSS Assisted
5. Helps
6. Tech Donations
7. Building Minutes
8. Fort rallies completed

Rules:

- Use UTC calendar dates.
- Order complete kingdom scans deterministically by scan order/date and compare only with the prior
  complete scan in which the governor is present.
- A missing governor scan is missing evidence. It is not an implicit zero and does not create a
  positive change when the governor returns.
- For Alliance Activity, evaluate the valid accepted source value available at each compared scan
  cutoff. The governor row must be present under the Phase 8 historic/fix-forward completion
  contract; missing source evidence does not create a delta.
- For Rally, evaluate completed report evidence available at each compared scan cutoff. A completed
  report with no governor row is an explicit zero for that report date, while a report without
  completion evidence is missing. A positive interval is attributed to the later kingdom ScanDate,
  not silently relabelled as a report date.
- Positive change means strictly greater than the prior eligible value.
- Zero change does not count.
- Negative monotonic-counter change is a reset and does not count.
- Positive Power change counts; negative Power change does not establish activity for this signal.
- Do not extrapolate or synthesize activity across absent observations.
- When several metrics change on one date, return that date once.
- Bound the search to 720 days. If no qualifying positive change is observed, display `Not
  recorded`; do not infer inactivity from unavailable evidence.
- If Last Active Date is more than 30 UTC calendar days before current UTC TODAY, classify
  `INACTIVE`. Exactly 30 calendar days old remains `ACTIVE`.
- ACTIVE/INACTIVE is separate from and subordinate to CURRENT/STALE/PARTIAL/NO DATA. It must not
  replace or recolor the primary data-state badge.
- Show Last Active source coverage or method access through Definitions/Method.

### Presence contract

- Presence remains distinct governors scans / all complete kingdom scans in the selected window.
- Show the exact numerator/denominator and one-decimal percentage unless the accepted visual
  contract selects whole percentage consistently.
- Preserve scanned-day presence in Definitions/Method or a secondary line.
- Presence remains outside Activity Index v1.
- Missing scans and source coverage are not merged into Presence.

### Visual hierarchy

- Retain `assets/stats/cards/stats_player.png`, neutral KD98/governor identity and no Discord avatar.
- Keep row 0 page navigation and controls below it.
- Keep the state-pill text vertically centered at top right.
- Blue remains neutral/selection/navigation/UTC; green current/success; amber stale/partial/review;
  red unavailable/failure/no data; muted disabled/expired.
- Footer label is `Data refreshed`, consistent with accepted `/me` pages; Generated is right aligned.
- Keep source/data refreshed and Generated separate.
- Meet established contrast and font-size requirements and validate at desktop and Discord-scaled
  presentation.

### Command Surface Governance

- No new registrations or options.
- `/stats player` remains the only leadership player-review command.
- `/player_profile` remains absent with no redirect.
- Counts remain `36 / 100 / 8 / 1 / 2`.
- No resync is expected. If a registration diff appears, stop and obtain approval.

### Permission and privacy

- Preserve the dedicated stable-role-ID/channel matrix from Phase 8.
- Recheck authorization and target at command entry and every interaction before data/cache access.
- Output remains private.
- Location/shield enlargement does not authorize wider delivery, storage or audit capture.
- Audit never stores metrics, names, alliance, location, shield, cards or raw SQL/Python errors.

## 13. Refactor Decisions

- Approved: small pure Last Active helper, renderer-local layout helpers, bounded record pagination
  improvement, and measured DAL/service/cache changes.
- Conditional: page-specific query/result contracts, pre-aggregation, indexes or maintained tables
  only after evidence and separate approval.
- Rejected: universal renderer/grid, self-view picker reuse, All Linked scope, broad KVK rewrite,
  command restructuring or unrelated cleanup.
- If a candidate refactor is useful but not required for acceptance, capture it using the deferred
  optimisation format and keep it out of the Phase 8.1 diff.

## 14. Testing Requirements

### Focused calculation tests

- one test for a positive change in each of the eight eligible Last Active metrics;
- unchanged, null, negative and monotonic-reset cases;
- missing governor between observations and return without false delta;
- completed Rally absence as zero and incomplete Rally report as missing;
- Alliance historic accepted rows and fix-forward explicit zero/missing behavior;
- duplicate timestamps/scan orders and deterministic ordering;
- no prior observation, new arrival and no qualifying change;
- exactly 30 versus 31 UTC calendar days;
- 720-day bound and no-data output.

### Data/service tests

- Presence numerator/denominator/percentage and scanned-day distinction;
- all Alias and Alliance rows preserved and deterministically paged;
- latest three finalized KVKs, one/two/three/no valid KVKs;
- retained target/exemption/missing semantics after removal of MET text;
- unchanged Activity Index and canonical combat outputs;
- authorization-before-cache/read and period/page preservation.

### Renderer and interaction tests

- deterministic images for all four pages and every primary state;
- long Unicode governor/alliance/alias text, max values and missing values;
- Overview hierarchy with Activity, Presence, Last Active and enlarged location/shield;
- enlarged six-tile Activity page without location strip;
- three-column KVK layout plus one/two/no-data variants;
- grouped Alias/Alliance record pages and pagination;
- Data refreshed left, Generated right;
- fallback parity, latest-transition-wins, replacement, timeout disable and cleanup.

### Performance validation

- reproducible cold/warm 30/90/180/360 timing matrix;
- stage-level bot timings with bounded labels and no private values;
- actual SQL plans, IO/time, rows and result sizes for representative cases;
- cache hit/miss/inflight behavior;
- bounded concurrency without a live load test unless explicitly approved;
- before/after comparison against an operator-approved budget.

### Repository gates

- focused pytest selected from the diff;
- full pytest unless explicitly justified;
- deterministic visual validation;
- `python scripts/validate_architecture_boundaries.py`;
- `python scripts/validate_deferred_items.py`;
- `python scripts/select_tests.py`;
- `python scripts/validate_codex_security_routing.py`;
- command registration validation;
- smoke imports, formatting/type checks, pre-commit and log-noise checks as applicable;
- SQL repository validation when SQL changed;
- bot Changes security review and conditional SQL Changes review, Deep off.

## 15. Acceptance Criteria

- [ ] Phase 8 data, formula, ranking, coverage and privacy behavior is preserved.
- [ ] Overview no longer duplicates Forts, Helps or Tech Donations.
- [ ] Presence shows an exact ratio and percentage as a primary Overview metric.
- [ ] Last Active matches all eight source rules without treating absence as zero.
- [ ] More-than-30-day UTC inactivity classification is correct and separate from freshness state.
- [ ] Location, location freshness and shield are larger on Overview and absent from Activity/KVK.
- [ ] Kingdom Activity retains all six metrics and materially improves readability.
- [ ] KVK shows the latest three eligible finalized KVKs in readable side-by-side cards.
- [ ] KVK cards remove final timestamp/state and MET/NOT MET copy without losing percentages,
      exemptions or honest missing semantics.
- [ ] Player Record uses `Alliances`, grouped Governor ID structure and complete paginated history.
- [ ] Data refreshed is left aligned and Generated is right aligned on every page.
- [ ] Cold/warm and period-change performance evidence identifies dominant costs.
- [ ] Any optimisation is the smallest evidenced change and meets the approved budget.
- [ ] No speculative SQL table/index is introduced.
- [ ] Dedicated authorization is rechecked on every interaction and output remains private.
- [ ] Same-payload fallback, transition, attachment, timeout and cleanup contracts pass.
- [ ] Command surface remains `36 / 100 / 8 / 1 / 2`; no resync is required.
- [ ] Focused/full/visual/performance/repository/security validation closes cleanly.
- [ ] Operator smoke and visual acceptance pass before promotion.

## 16. Required Delivery Output

The implementation handoff must include:

- exact delivered visual and data-contract changes;
- Last Active source/parity evidence and threshold examples;
- before/after performance table by period and cold/warm state;
- SQL plans/read/timing summary and whether SQL changed;
- exact bot and optional SQL file manifests;
- focused/full/visual/repository/security test evidence;
- command-count and no-resync verification;
- deployment order, smoke results, observation and rollback state;
- residual deferred items only where they remain genuinely outside scope;
- explicit operator acceptance before Phase 8.1 archive.

### Implementation evidence, 2026-07-21

- Bot instrumentation records authorization/lookup, connection, SQL fetch, mapping, KVK, payload,
  render, attachment and cache/inflight stages without logging governor identity, location or
  shield values.
- `scripts/measure_leadership_player_review.py` provides an explicit read-only, sequential
  30/90/180/360 cold/warm application harness. It labels representative cases without writing
  Governor IDs to the result artifact.
- SQL adds only `dbo.usp_GetLeadershipPlayerLastActive`, its migration/rollback and a read-only
  measurement harness. The procedure returns one compact row and preserves the eight approved
  source, complete-scan, missing, reset and UTC-threshold rules.
- `deploy/Measure-Phase81LeadershipPerformance.sql` captures actual-plan-compatible IO/time,
  result rows, existing index definitions and usage, statistics age/sampling, operational
  lock/latch counters and missing-index hints. Hints are advisory and cannot approve an index.
- No table, index, materialized snapshot or pre-aggregation object is introduced. Representative
  production actual plans and cold/warm read evidence remain a deployment-window evidence gate,
  not a reason to speculate locally.
- Proposed acceptance budget: warm application-cache period/page transition p95 <= 1.0 s;
  warm SQL-backed period transition p95 <= 2.5 s; cold first load p95 <= 5.0 s; render plus PNG
  encode p95 <= 750 ms; attachment replacement p95 <= 1.5 s. No representative case may exceed
  the existing interaction timeout, regress logical reads by more than 10% without an explained
  correctness trade-off, or expose private values in performance artifacts. The operator must
  accept or revise this budget after the baseline is collected.

## 17. PR Summary Template

## Summary

Refine accepted `/stats player` page hierarchy, add authoritative Presence/Last Active emphasis,
improve KVK and record readability, and apply only measured performance improvements.

## Changes

- Overview Presence, Last Active and location/shield hierarchy
- larger Activity layout without repeated location strip
- three-column latest-three KVK presentation
- grouped, complete Alias/Alliance Player Record presentation
- evidence-led bot/SQL performance refinement, if approved
- updated documentation and deterministic tests

## Tests

- focused Last Active/data/service/view/renderer tests
- deterministic visual matrix
- cold/warm 30/90/180/360 performance evidence
- full pytest and repository validation gates
- SQL validation when applicable

## Security Review

- Bot Changes review: required, Deep off
- SQL Changes review: required only if SQL changed, Deep off
- Standard/deep codebase scan: not requested

## Deferred Optimisations

- List only evidence-backed residual work not required for this slice.

## Risk / Rollback

- Primary risks: incorrect inactivity inference, hidden missing data, layout truncation, private
  location exposure, cache authorization errors and SQL regression.
- Roll back bot first. Roll back SQL only after the bot no longer depends on it. Preserve additive
  evidence/data unless a separately validated destructive rollback is required.
