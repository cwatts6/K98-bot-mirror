# Codex Task Pack - Player Self-Service Command Centre v2 Phase 6 Interactive Period Performance and `/my_stats` Retirement

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 6 Interactive Period Performance and /my_stats Retirement`
- Date: `2026-07-17`
- Owner/context: `KD98 / Kingdom 1198 GovernorOS v2 follow-on from completed and operator-accepted Phase 5G Account Data Export Consolidation`
- Task type: `feature | refactor | command migration | command retirement | visual renderer | documentation`
- One-pass approved: `no`
- Product decision approved: `yes`
- Runtime implementation approved: `yes, subject to the normal audit, architecture, implementation-plan, validation, security-review, operator-smoke, and promotion gates`
- Status: `implementation in validation; final Changes reviews, operator smoke, and promotion pending`
- Approved runtime backdrop: `assets/me/cards/me_stats.png`
- Target successful output: `private standalone 1702x924 PNG plus same-authorized-payload fallback`
- SQL deployment approved: `yes; additive dbo.usp_GetPersonalStatsDaily only, with a separate SQL diff/review and SQL-before-bot deployment order; indexes remain measurement-gated`
- Command target: `38 -> 37 top-level commands; grouped subcommands 99 -> 100; /me 7 -> 8; /inventory remains 2`
- Command resync required: `yes, after the atomic Phase 6 deployment`

### Locked product decision

Phase 6 replaces the current interactive personal Stats route with:

```text
/me stats
```

The Phase 6 deployment adds `/me stats`, adds the selected-governor Dashboard Stats action, and
removes `/my_stats` in the same approved bot patch. `/my_stats` is not retained as a redirect,
alias, compatibility command, or observation-only route.

The new experience is a private **Period Performance** product. It analyses a selected linked
governor or the invoking player's explicit All Linked portfolio across exact source-date windows.
It does not own current-account downloads. The Phase 5G journey remains canonical and unchanged:

```text
/me accounts
-> Account Summary
-> Download data
```

Phase 6 creates no workbook, CSV, Google Sheet, export action, download button, or replacement
Exports page.

### Locked presentation decision

The one approved `assets/me/cards/me_stats.png` backdrop is reused across three in-place report
modes:

```text
Overview
Activity
Combat
```

Every generated card includes the invoking player's bounded circular Discord avatar at the top left,
with the accepted safe local GovernorOS/KD98 fallback. The card shows selected scope, governor
identity where applicable, friendly period, exact inclusive dates, authoritative Stats data anchor,
reporting coverage, state, view-specific metrics, and truthful freshness/generated time.

## 2. Required Reading

Before implementation, read the current repository instructions and indexed standards:

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
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5G Account Data Export Consolidation.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 4 Premium Governor Dashboard Renderer.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Inspect the approved runtime asset before architecture approval:

```text
assets/me/cards/me_stats.png
```

Validate that the production asset is exactly `1702x924`, fully opaque, readable under the planned
Overview/Activity/Combat overlays, and not accidentally replaced by a master/source image.

For security-review routing, read the active root and applicable nested `SECURITY.md` files and use
`k98-security-review-routing`. For telemetry/diagnostic changes, use the conditional diagnostics
reference. For helper extraction, use `docs/reference/REVIEW_HELPERS.md`. Use the Promotion Guide
only at the later promotion/deployment gate.

For SQL-facing work, validate the authoritative objects read-only against:

```text
C:\K98-bot-SQL-Server
```

At minimum inspect and search consumers of:

```text
dbo.vDaily_PlayerExport
dbo.usp_GetPlayerStatsWindows
dbo.fn_StatsWindowDeltas_GovCsv
dbo.IntList
```

Also inspect the underlying Kingdom 1198, Alliance Activity, and Fort/rally sources used by the
view. Do not infer null, zero, missing-day, source-date, or aggregation semantics solely from Python.
No SQL schema, table, view, function, procedure, index, data, permission, or deployment change is
pre-approved. If exact correctness or the required performance genuinely needs a SQL-repository
diff, stop and present the narrow additive option, deployment order, security target, and rollback
before implementation.

## 3. Objective

Deliver `/me stats` as the private premium GovernorOS Period Performance experience for one currently
linked governor or the player's explicit All Linked portfolio. Show exact period movement and daily
activity across Growth, Economy, Participation, and Combat using the approved `1702x924` card,
truthful coverage, integrated RSS/Forts trends, and a complete accessible fallback.

Remove `/my_stats` atomically, remove its channel gate and legacy personal ownership, resync the
application-command cache, and preserve Account Summary downloads plus the separate leadership
`/stats player` behavior.

## 4. Background And Confirmed Current State

### 4.1 Phase 5G accepted end state

Phase 5G is complete and operator accepted through mirror PR `#227` and production PR `#534`.
Application-command resync confirmed:

```text
top-level commands: 38
/me subcommands: 7
/inventory subcommands: 2
```

`/me accounts -> Account Summary -> Download data` now owns the Full workbook, Current snapshot CSV,
and Raw stats history CSV. `/me exports` and `/my_stats_export` are absent. The three selected-
governor Inventory report-page exports remain.

Phase 6 must not reopen any Phase 5G download, sheet, filename, workbook, CSV, Inventory-export, or
navigation decision.

### 4.2 Current personal Stats route

Post-Phase-5G `commands/stats_cmds.py` still registers top-level `/my_stats` with:

- the configured KVK player-stats channel gate and thread handling;
- admin bypass;
- private/ephemeral defer and output;
- active account-registry lookup;
- Main/first-account/ALL defaulting;
- default `This Week` (`wtd`) period;
- the shared `get_stats_payload`, `build_embeds`, and `SliceButtons` stack;
- one stats embed plus separate RSS and Fort chart attachments;
- a 14-minute legacy view timeout;
- performance and interaction telemetry.

The current UI mixes cumulative/end snapshots, period deltas, daily activity, lifetime Ark values,
and additive portfolio rows. It uses governor names as selector identity, cannot safely represent all
26 configured account slots plus ALL in one Discord select, does not re-resolve current linkage on
every transition, and does not provide the approved premium GovernorOS presentation or coverage
contract.

### 4.3 Leadership dependency boundary

`/stats player` currently shares the legacy `stats_service.py`, `embed_my_stats.py`, and
`SliceButtons` implementation. Phase 6 removes the personal `/my_stats` registration but does not
silently redesign, migrate, retire, or broadly clean the leadership route.

The audit must prove every remaining caller before deleting legacy helpers. Retain code and tests
still required by `/stats player`. Capture leadership-only defects or consolidation opportunities for
the later `/stats player` versus `/me inspect` decision unless Phase 6 directly causes a regression.

### 4.4 Approved visual input

The operator-approved runtime backdrop is already present locally:

```text
assets/me/cards/me_stats.png
```

It was designed as one shared GovernorOS Operations Observatory environment with:

- a quiet top-left avatar zone;
- persistent identity, state, period, date-anchor, and coverage zones;
- a flexible primary metric field;
- a chart-safe lower analysis region;
- a concise status/insight and footer region;
- GovernorOS obsidian, purple, bronze/gold, and restrained cyan-teal visual continuity.

Do not create a second backdrop, redesign the room, add generated UI to the asset, or change the
canvas without explicit visual escalation.

### 4.5 Approved product direction

Option B, full Period Performance, is selected. Phase 6 includes Growth, Economy/Participation, and
Combat. Ark of Osiris is removed completely because it is already owned by the governor Dashboard
and does not meaningfully vary with the selected period.

## 5. Scope

### In Scope

- Add private grouped `/me stats` under the existing `/me` command group.
- Add a Stats/Period Performance action from the selected-governor Dashboard while preserving the
  validated selected governor as the first-choice context.
- Remove top-level `/my_stats` in the same bot deployment; do not retain a redirect or alias.
- Remove the personal KVK stats-channel gate by making `/me stats` privately usable from any guild
  channel or thread.
- Build a new typed personal Period Performance model/service/DAL/renderer/view stack rather than
  repurposing the leadership-facing legacy stack.
- Use the approved `assets/me/cards/me_stats.png` background and invoking-user Discord avatar.
- Deliver Overview, Activity, and Combat modes inside one author-gated private experience.
- Support one linked governor, multiple linked governors, duplicate names, more than 25 linked
  choices, and explicit All Linked scope.
- Re-resolve current registry linkage before every data fetch and reject stale, removed, transferred,
  forged, foreign, expired, or superseded interactions.
- Implement the seven exact source-date windows and display their exact dates.
- Implement the approved Growth, Activity, Fort, and Combat metrics with signed corrections.
- Implement truthful reporting-day, governor, and account-day coverage.
- Integrate RSS and Fort trends into the Activity presentation with accessible text equivalents.
- Separate genuine no data, partial data, unavailable data, and access-changed states.
- Add latest-request-wins transition safety, bounded timeouts, safe fallback, attachment replacement,
  avatar/network limits, file/stream cleanup, cache discipline, and operational telemetry.
- Update command governance, canonical docs, player/operator briefing, task indexes, deferred items,
  smoke references, and the programme close-out record during implementation/acceptance.
- Communicate removal before deployment, resync commands after deployment, observe the new route,
  and retain a tested rollback path.

### Out of Scope

- Any personal workbook, CSV, Google Sheet, download button, export action, or Exports-page revival.
- Changes to Account Summary fields, Download data outputs, schemas, filenames, windows, or
  spreadsheet behavior.
- Ark of Osiris metrics or placeholders in `/me stats`.
- Ranged Points, Highest Acclaim, Autarch counts, Olympia, achievements, badges, rankings, targets,
  or cross-player comparison.
- Public Stats output or a user-selectable public/private option.
- Retaining `/my_stats` as a redirect, alias, observation route, or permanent compatibility command.
- Redesigning, renaming, removing, or broadly refactoring `/stats player`, `/player_profile`,
  `/mykvkcrystaltech`, `/kvk stats`, `/kvk history`, or `/me inspect`.
- Broad consolidation of Player Self-Service renderers, views, selector frameworks, or generic page
  lifecycle helpers beyond directly proven Phase 6 needs.
- SQL-repository changes or deployment without a separate explicit escalation and approval.
- Changes to registry ownership, linking, claiming, slot capacity, VIP, reminders, Preferences,
  Inventory calculations, report-page exports, or KVK command behavior.
- A persistent default-governor preference; existing Dashboard context and Main-first resolution are
  sufficient for this phase.

## 6. Approved Product, Period, And Data Contract

### 6.1 Canonical player journey

Direct entry:

```text
/me stats
-> resolve current linked governors privately
-> no governors: Accounts setup guidance
-> one governor: open Overview directly
-> multiple governors: selected Dashboard governor, otherwise Main, otherwise first valid slot
-> optional explicit All Linked selection
-> switch Overview / Activity / Combat and period in place
```

Dashboard entry:

```text
/me dashboard
-> selected governor
-> Stats
-> /me stats Period Performance with that governor selected
```

Every successful or fallback response remains private/ephemeral. The command has no channel-only
restriction and no public fallback message.

### 6.2 Default state

```text
mode: Overview
period: This Week
scope: selected Dashboard governor, else Main, else first valid linked governor
All Linked: available only when more than one distinct linked Governor ID exists; never the default
```

Mode changes must normally reuse the already-authorized period payload without another SQL read.
Period or scope changes may load a new payload after current registry revalidation.

### 6.3 Header and identity

Every generated card and same-payload fallback must show applicable values from this contract:

```text
PERIOD PERFORMANCE
invoking user's circular Discord avatar at top left
account slot and governor name
Governor ID
selected scope: one governor or All Linked
friendly mode: Overview | Activity | Combat
friendly period label
exact inclusive start and end dates
authoritative Stats data anchor
reporting-day coverage
governor and account-day coverage where applicable
READY | PARTIAL | NO DATA | UNAVAILABLE
full generated/refreshed UTC date-time
```

Do not display one Alliance value for All Linked as though the entire portfolio shares it. Long and
Unicode Discord/governor names must fit safely. The avatar is best-effort, bounded, time-limited, and
restricted to the invoking author; use the accepted safe local fallback without changing the payload.

### 6.4 Exact period semantics

All period boundaries use the same authoritative Stats source anchor, not wall-clock today and not a
user timezone. The audit must prove the source-date type and authoritative global anchor in the SQL
repo. The service returns exact start/end dates with the payload.

| Player label | Exact inclusive source-date behavior |
|---|---|
| Yesterday | `anchor - 1 day` through `anchor - 1 day` |
| This Week | Monday of the anchor week through anchor |
| Last Week | Previous Monday through previous Sunday |
| This Month | First day of the anchor month through anchor |
| Last Month | First through final day of the previous calendar month |
| Last 90 Days | `anchor - 89 days` through anchor |
| Last 180 Days | `anchor - 179 days` through anchor |

Rules:

- Replace current `Last 3M` and `Last 6M` player-facing options with `Last 90 Days` and
  `Last 180 Days`.
- Do not reuse the current SQL `last_3m`/`last_6m` month-boundary meanings under the new labels.
- A complete Last 90 Days window contains exactly 90 calendar dates; Last 180 Days contains 180.
- Source gaps produce incomplete coverage; never invent or forward-fill daily rows.
- Yesterday never silently means previous available scan. No row on the prior calendar date is an
  honest NO DATA or PARTIAL condition according to the typed state contract.
- The exact same boundaries govern headline movement, daily totals, averages, charts, selected-
  governor scope, and All Linked scope.

### 6.5 Selected-governor scope

For one selected governor:

- use Governor ID or a server-held opaque token as component identity, never governor name;
- show the canonical slot plus current display name;
- preserve period and mode when changing governor;
- show no redundant All Linked/individual duplicate when only one distinct Governor ID is linked;
- revalidate active linkage before every period/scope data load;
- never fall back from an invalid selected governor to All Linked silently.

### 6.6 All Linked scope

All Linked is a selected-period portfolio activity view, not another current Account Summary.
Deduplicate Governor IDs before data access and aggregation while retaining a visible review warning
when the registry contains duplicate IDs.

Only additive values may be aggregated:

```text
period-end Power and Troop Power, with reporting-governor coverage
Power and Troop Power change
RSS gathered
RSS assisted
Helps
Build activity
Tech donations
Forts total, launched, and joined
Kill Points gained
T4 kills gained
T5 kills gained
T4+T5 combined period gain
Deads gained
Healed Troops gained
```

Rules:

- Do not sum ratios, percentages, ranks, per-account averages, highest values, or labels.
- Recompute All Linked daily series and averages after aggregation.
- Averages use distinct valid reporting dates for the selected scope and are labelled
  `Average per reporting day`.
- Show reporting-governor and account-day coverage so partial portfolios cannot masquerade as
  complete totals.
- Do not treat missing governor/date/source rows as zero unless the SQL/source contract proves that
  absence means genuine zero activity.

### 6.7 Approved metrics

#### Growth

```text
Power change
Troop Power change
```

Selected-period signed change is the primary value. Period-end Power/Troop Power may be secondary
context, clearly labelled. Negative corrections or genuine decreases remain signed and visible.

#### Activity and participation

```text
RSS gathered
RSS assisted
Helps
Build activity
Tech donations
Forts total
Forts launched
Forts joined
```

RSS Gathered, RSS Assisted, and Helps use one consistent total-plus-average treatment. For multi-day
windows, show `Average per reporting day`; for a single reporting date, show the total without a
misleading average. Build activity, Tech donations, and Forts may use the same reporting-day average
where readable and source-correct.

Do not clamp negative source corrections to zero. Distinguish a genuine zero from no observation.

#### Combat

```text
Kill Points gained
T4 kills gained
T5 kills gained
T4+T5 combined period gain
Deads gained
Healed Troops gained
```

These are period movements, not cumulative totals. The audit must validate the canonical source for
combined T4+T5 period gain. Prefer deriving it from the same displayed T4 and T5 gains unless the SQL
contract proves the source combined delta is independently authoritative; any discrepancy must be
reported before implementation.

#### Removed

```text
Ark Played
Ark Won
Ark average kills/deads/heals
```

No Ark field, placeholder, collapsed section, or All Linked Ark calculation remains in the personal
Period Performance experience.

### 6.8 Reporting coverage and state

The typed payload must distinguish at least:

```text
READY
PARTIAL
NO_DATA
UNAVAILABLE
```

Baseline meanings:

- `READY`: required reads succeeded and the selected scope has complete required Stats coverage for
  the exact period; any optional subsource coverage is represented truthfully.
- `PARTIAL`: usable data exists, but required dates, governors, account-days, or metric-source
  coverage is incomplete.
- `NO_DATA`: reads succeeded but no usable rows exist for the selected scope and exact period.
- `UNAVAILABLE`: registry, SQL, or another required request-level dependency failed.

Access removal/transfer is an explicit interaction result and must not be mislabelled as NO DATA.
Player-facing errors do not expose Python exception types or raw SQL details.

Coverage contract:

- selected governor: distinct reporting dates / expected inclusive dates;
- All Linked: distinct reporting Governor IDs / expected distinct linked IDs;
- All Linked account-days: distinct valid governor-date rows / (`expected governors * expected days`);
- metric/source-specific coverage is shown where the underlying daily source can be absent
  independently of the main Stats row;
- the audit must validate whether null/absent Alliance Activity or Fort rows mean zero activity or
  missing source data before any `COALESCE` rule is retained.

### 6.9 Overview, Activity, and Combat modes

The exact Pillow geometry follows the approved backdrop and visual audit, but the information
ownership is locked:

#### Overview

Prioritise:

```text
Power change and period-end Power
Troop Power change and period-end Troop Power
RSS gathered
Kill Points gained
Forts
coverage/status report note
```

#### Activity

Show:

```text
RSS gathered
RSS assisted
Helps
Build activity
Tech donations
Forts total/launched/joined
RSS daily trend
Forts daily trend
peak date/value and coverage text equivalents
```

#### Combat

Show:

```text
Kill Points gained
T4 kills gained
T5 kills gained
T4+T5 combined
Deads gained
Healed Troops gained
signed correction/status note where applicable
```

The one shared backdrop must remain readable for all three modes. Do not create another generated
background or one image per mode.

### 6.10 Charts and accessible equivalents

RSS and Fort trends are retained only in Activity and integrated into the successful `1702x924`
card rather than sent as separate chart embeds.

Requirements:

- exact selected-period dates and values;
- signed axes where negative corrections exist;
- sensible tick density at desktop and mobile preview scale;
- one-point Yesterday treatment as a marker/bar or text summary, never a fake trend line;
- no chart when there are no valid points;
- text equivalents containing period total, average per reporting day where applicable, peak date,
  peak value, and coverage;
- no reliance on colour alone; use labels, signs, markers, and readable legends;
- chart/render failure falls back from the same payload without another data fetch.

## 7. Codex Skills To Use

Use these local Codex skills when they apply. The security-routing skill is mandatory and does not
itself launch a scan.

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | `use` | Required before implementation to confirm the new personal stack, legacy caller boundary, SQL/no-SQL decision, exact file manifest, and approval stops. |
| `k98-discord-command-feature` | `use` | Adds `/me stats`, removes `/my_stats`, changes Dashboard actions, and adds private views, selects/buttons, callbacks, timeout, and command resync. |
| `k98-sql-validation` | `use` | Period, delta, coverage, All Linked, null/zero, freshness, and performance semantics depend on SQL-backed sources. Validation is read-only unless separately escalated. |
| `k98-test-selection` | `use` | Required to combine the selector with risk-based command, DAL, service, renderer, interaction, regression, and visual coverage. |
| `k98-deferred-optimisation-capture` | `use` | Capture out-of-scope legacy `/stats player`, shared-stack, SQL-performance, or renderer consolidation work structurally. |
| `k98-pr-review` | `use` | Required before PR handoff to verify scope, architecture, SQL alignment, command counts, tests, lifecycle, and promotion readiness. |
| `k98-promotion-check` | `use at later gate` | Required only after mirror implementation, final validation, security evidence, and operator smoke are accepted. |
| `k98-security-review-routing` | `use` | Separate bot and additive-SQL final diff-focused Changes reviews, both Deep off. No codebase/deep scan. |

### Security Review Decision

| Repository | Decision | Target | Expected setup / execution | Evidence |
|---|---|---|---|---|
| `K98-bot-mirror` | `Changes review` | Final intended Phase 6 base..head or staged working-tree patch | `Changes + Deep Off` using `$codex-security:security-diff-scan` after the final diff exists | Pending; focus on registry revalidation, private visibility, component forgery/expiry/concurrency, SQL over-read, avatar/network input, telemetry minimisation, resource exhaustion, attachment cleanup, and command retirement. |
| `K98-bot-SQL-Server` | `Changes review required` | Final intended additive `dbo.usp_GetPersonalStatsDaily` schema/migration/rollback diff | `Changes / Deep Off` | Required because the operator approved the additive set-based contract after architecture review. Review SQL independently from the bot; any index remains outside this diff unless measurement separately approves it. |

Do not start a standard or deep codebase audit without an explicit operator request for that exact
audit. Existing captured security findings use the triage/remediation workflow rather than new
discovery.

## 8. Mandatory Workflow

1. Audit and scope review, then stop for approval.
2. Record the provisional security-routing decision and exact intended targets; do not start a scan.
3. Architecture and read-only SQL-contract validation, including the exact file manifest and visual
   layout/component-row proposal, then stop for approval.
4. Implementation plan covering data shape, periods, aggregation, selector/paging, rendering,
   performance, tests, communication, deployment/resync, smoke, rollback, and documentation, then
   stop for approval.
5. Implement only after approval.
6. Run focused, visual, full, architecture, deferred, security-routing, command-registration,
   import-smoke, pre-commit, and log-noise validation.
7. Execute the final bot Changes review with the intended base/head and `Deep: Off`; confirm the SQL
   documented skip or separately approved SQL outcome.
8. Complete K98 PR review and mirror PR handoff.
9. Deploy/restart and resync application commands only after the implementation and communication
   gates are accepted; complete operator Discord smoke.
10. Run promotion check and promote the exact accepted patch to production.

One-pass execution is not approved.

## 9. Audit Requirements

### A. Current command surface and usage evidence

Audit and report:

- exact `/my_stats` registration, version, description, decorators, channel/thread/admin behavior,
  defer/output visibility, usage identity, tests, docs, and command-cache expectations;
- exact post-Phase-5G command counts from the validator and canonical reference;
- exact `/me` group registration and insertion point for `/me stats`;
- every active Dashboard action row and selected-governor context path;
- every user/operator document and smoke reference that mentions `/my_stats`, Last 3M/6M, the old
  channel gate, separate chart embeds, or 14-minute timeout;
- the latest available `/my_stats` usage evidence and current stats-channel audience for communication
  planning; removal is already product-approved and the evidence is descriptive, not a new retention gate;
- exact resync/deployment steps required to remove the guild command.

### B. Legacy personal/leadership shared stack

Map all callers and behavior for:

```text
commands/stats_cmds.py
embed_my_stats.py
stats_service.py
stats_helpers.py
constants.STATS_VIEW_TIMEOUT
tests/test_embed_my_stats.py
tests/test_stats_service.py
```

Confirm:

- which functions/classes are personal-only, leadership-only, or shared;
- exact `/stats player` dependencies and regressions to preserve;
- direct SQL and business logic that must not be copied into the new command/view;
- current selector identity, option-limit, author/expiry, timeout, attachment, failure, and telemetry behavior;
- current chart generation and negative-axis behavior;
- direct zero-caller candidates after `/my_stats` removal;
- leadership defects or cleanup that must be deferred rather than silently folded into Phase 6.

### C. Governor context and Dashboard integration

Audit the accepted GovernorOS selector/context/navigation stack:

- no/one/multiple/>25 governor resolution;
- canonical slot ordering and duplicate-name/duplicate-ID behavior;
- selected Dashboard governor propagation;
- access re-resolution helpers and transition-generation/latest-wins patterns;
- invoking-user avatar retrieval limits and fallback helpers;
- Dashboard component row capacity after adding Stats;
- attachment replacement, fallback, timeout, stale/foreign interaction, and stream cleanup patterns
  to reuse rather than duplicate.

### D. SQL/data-source and metric semantics

Validate read-only against the SQL repo:

- exact `vDaily_PlayerExport` columns, types, nullability, date grain, deduplication, source joins,
  and indexes/underlying access paths;
- exact global Stats data-anchor semantics;
- current `usp_GetPlayerStatsWindows` window definitions and why `last_3m`/`last_6m` cannot back the
  new Last 90/180 labels unchanged;
- exact function behavior for first/last snapshots, period deltas, cumulative values, Forts, and
  missing rows;
- whether Power, Troop Power, KP, T4, T5, Deads, Healed, RSS, Helps, Building, Tech, and Fort values
  are daily deltas, cumulative snapshots, or daily counts;
- whether negative values represent valid corrections and must remain;
- whether null/absent Alliance Activity and Fort rows mean zero or missing data;
- one-call or minimal-call set-based DAL options for one governor and up to 26 configured slots over
  180 days;
- representative row counts, logical reads, execution time, and concurrency expectations;
- whether a bot-DAL query over existing objects is sufficient. If not, stop with a narrow additive
  SQL option; do not modify the shared procedure in place without approval.

### E. Period, coverage, and aggregation proof

For all seven periods, prove with deterministic injected anchors:

- exact start/end dates across Monday, month, year, and leap-day boundaries;
- exact 90/180 inclusive date counts;
- Yesterday missing-row behavior;
- selected-governor reporting-day calculation;
- All Linked reporting-governor and account-day calculation;
- deduplication of duplicate Governor IDs;
- additive aggregation for every approved metric;
- recomputation of portfolio averages and daily series;
- no sum of ratios/averages/highest values;
- no missing-as-zero assumption without source evidence;
- consistent scope/date boundaries between metrics, charts, coverage, and fallback.

### F. Visual, renderer, and accessibility audit

Inspect the `1702x924` asset and accepted GovernorOS renderers for:

- exact dimensions, RGB/opacity, safe zones, and runtime path;
- top-left circular invoking-user avatar with fallback;
- long/Unicode identity fitting;
- Overview, Activity, Combat geometry and external component layout;
- signed positive/negative/zero treatment without colour-only meaning;
- chart-label/tick density and one-point/no-data behavior;
- text-equivalent content for RSS and Fort charts;
- standalone attachment filename and delivery pattern;
- same-payload fallback completeness;
- render/file/send failure and cancellation cleanup;
- original, Discord desktop, and mobile preview requirements.

### G. Interaction, privacy, and concurrency audit

Prove the proposed view can:

- remain private in any guild channel/thread;
- reject foreign users before mutating visible state;
- re-resolve current linkage before every data fetch;
- reject removed/transferred/forged selections without falling back to ALL;
- support more than 25 linked choices plus All Linked safely;
- preserve selected scope, period, and mode across valid transitions;
- avoid a SQL read for mode-only changes;
- prevent stale or slower work from replacing a newer transition;
- restore usable controls after a failed transition;
- preserve the last report and visibly disable controls after 180 seconds of inactivity;
- emit no public expiry/failure message;
- release every file and underlying stream on success, failure, timeout, navigation, cancellation,
  and stale suppression.

### H. Performance, cache, and telemetry audit

Measure or model:

- current cold and warm `/my_stats` data, chart, and delivery timings;
- sequential query/chart costs and opportunities for one set-based payload;
- event-loop blocking risk;
- 180-day All Linked upper-bound row and render cost;
- bounded TTL/LRU cache design and invalidation/access-recheck order;
- explicit data and render timeouts;
- latest-request-wins cancellation/stale suppression;
- telemetry split into data, render, and delivery duration;
- entry route, scope type, period, mode, coverage, result state, fallback reason, timeout, and
  access-changed events;
- removal of routine governor/account names from Phase 6 telemetry.

Provisional performance targets to validate before locking the implementation plan:

```text
initial private report p95: <= 5 seconds
period/scope transition p95: <= 4 seconds
required data-read timeout: approximately 8-10 seconds
card/chart render timeout: approximately 3-4 seconds
```

If evidence requires different targets, stop with the measured baseline and recommended values.

### I. Documentation, communication, deployment, and rollback audit

Identify exact updates for:

- `README-DEV.md`;
- `docs/player_self_service_command_centre_briefing.md`;
- `docs/reference/canonical_command_reference.md`;
- `docs/reference/deferred_optimisations.md`;
- task-pack and archive indexes;
- this programme pack and implementation close-out;
- command validator and registration tests;
- stats-channel pre-deployment announcement and player guidance;
- mirror deployment/restart/resync, production promotion, and rollback resync.

Historical archived Phase 5G and earlier execution records remain accurate and are not rewritten.

### Audit stop output

Stop after providing:

1. evidence-backed current-state findings;
2. exact Review / Modify / Create / Delete manifest;
3. confirmed current and target command counts;
4. legacy `/stats player` preservation and zero-caller boundary;
5. SQL read-only findings and no-SQL versus escalation recommendation;
6. exact typed model/service/DAL architecture;
7. exact component-row and >25 paging proposal;
8. exact period, metric, coverage, All Linked, and state semantics;
9. renderer/fallback/accessibility proposal using `me_stats.png`;
10. measured performance/cache/telemetry proposal;
11. test-selection proposal;
12. security-routing proposal;
13. communication/deployment/resync/smoke/rollback boundary;
14. explicit approval checkpoint.

Do not code in the first response.

## 10. Architecture Targets

| Concern | Target |
|---|---|
| `/me stats` slash handler | Thin registration in `commands/me_cmds.py`; defer privately and hand off to the controller. |
| `/my_stats` retirement | Remove only the personal top-level registration and direct personal-only imports/copy after caller proof. |
| Dashboard action | Existing governor-dashboard view/controller; carry validated selected Governor ID into the Stats entry. |
| Discord view/state | New `ui/views/player_self_service_stats_views.py` or audit-approved equivalent. Own author gating, mode/period/scope component state, paging, transition generation, attachment replacement, fallback delivery, and timeout only. |
| Typed models | New `player_self_service/stats_models.py` or audit-approved equivalent. Own period/scope/state/coverage/metric/trend/payload contracts. |
| Business service | New `player_self_service/stats_service.py` or audit-approved equivalent. Own current registry revalidation, period resolution, aggregation, coverage, state, report-note selection, cache coordination, and payload assembly. |
| DAL | New `stats/dal/personal_stats_dal.py` or audit-approved equivalent. Own set-based read-only SQL and row mapping; no SQL in command/view/renderer. |
| Renderer | New `player_self_service/stats_renderer.py` or audit-approved equivalent. Own deterministic `1702x924` Pillow composition, integrated charts, fitting, fallback-ready formatting, and stable filename. |
| Avatar | Reuse the accepted bounded invoking-user avatar helper and safe local fallback where contracts match. |
| Shared helpers | Pure exact-period, coverage, formatting, or chart primitives only when contracts are genuinely shared and caller proof supports extraction. |
| Legacy leadership stack | Retain `embed_my_stats.py`/`stats_service.py` code still used by `/stats player`; no broad migration in Phase 6. |
| Telemetry | Existing usage tracker plus narrow structured Phase 6 performance/interaction events with minimised content. |
| Documentation | Current programme, canonical command reference, README/briefing, task indexes, deferred register, smoke and deployment records. |
| SQL schema | Additive `dbo.usp_GetPersonalStatsDaily` procedure, migration, and rollback are approved. Deploy SQL before bot; keep any index measurement-gated. |
| Tests | Focused command, DAL, service, renderer, view, lifecycle, performance-shape, command-governance, and visual suites. |

### Recommended typed concepts

```text
PersonalStatsMode
- OVERVIEW | ACTIVITY | COMBAT

PersonalStatsPeriod
- YESTERDAY | THIS_WEEK | LAST_WEEK | THIS_MONTH | LAST_MONTH | LAST_90_DAYS | LAST_180_DAYS

PersonalStatsScope
- GOVERNOR | ALL_LINKED
- selected Governor ID where applicable
- distinct authorised Governor IDs

StatsPeriodWindow
- period key and player label
- authoritative anchor date
- exact inclusive start/end dates
- expected calendar-day count

StatsCoverage
- expected/reporting days
- expected/reporting governors
- expected/reporting account-days
- source-specific coverage where required

PeriodMetric
- value
- optional period-end value
- signed correction/decrease state
- reporting coverage / missing state

PersonalStatsPayload
- invoking Discord user and generated time
- identity/avatar input
- scope and period window
- READY | PARTIAL | NO_DATA | UNAVAILABLE
- Growth, Activity/Forts, and Combat metrics
- RSS and Fort daily trends
- coverage, warnings, and concise report note
- freshness/data anchor
```

Models remain Discord-free and renderer-independent where practical.

## 11. Likely Files

The audit must replace this provisional list with an exact manifest.

### Review

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- `docs/player_self_service_command_centre_briefing.md`
- `commands/me_cmds.py`
- `commands/stats_cmds.py`
- `ui/views/player_self_service_governor_dashboard_views.py`
- `player_self_service/governor_dashboard_*`
- `services/governor_account_service.py`
- `registry/account_slots.py`
- `embed_my_stats.py`
- `stats_service.py`
- `stats_helpers.py`
- `file_utils.py`
- `decoraters.py`
- `usage_tracker.py`
- `constants.py`
- `assets/me/cards/me_stats.png`
- `scripts/validate_command_registration.py`
- `commands/command_inventory.py`
- current command-registration, dashboard, stats, renderer, interaction, and visual tests
- SQL repo objects listed in Required Reading

### Modify

- `commands/me_cmds.py`
- `commands/stats_cmds.py`
- `ui/views/player_self_service_governor_dashboard_views.py`
- `scripts/validate_command_registration.py`
- command-registration and command-inventory tests
- directly affected dashboard tests
- directly affected legacy stats tests after caller classification
- `README-DEV.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/README.md`
- `docs/task_packs/archive/README.md` at close-out only
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`

### Create

Provisional architecture; final names require audit approval:

- `player_self_service/stats_models.py`
- `player_self_service/stats_service.py`
- `player_self_service/stats_renderer.py`
- `stats/dal/personal_stats_dal.py`
- `ui/views/player_self_service_stats_views.py`
- focused Phase 6 command/DAL/service/renderer/view/visual tests

### Delete or narrow only after zero-caller proof

- the `/my_stats` command body and personal-only copy/imports in `commands/stats_cmds.py`;
- tests that assert the retired personal command or obsolete channel gate;
- personal-only legacy helpers with no `/stats player` or other caller.

Do not delete `embed_my_stats.py`, root `stats_service.py`, `SliceButtons`, chart helpers, constants, or
tests merely because `/my_stats` is removed. Retain every proven leadership caller until the later
Inspect review.

## 12. Implementation Requirements

### 12.1 Thin layers and authoritative context

- Keep `/me stats` and Dashboard callbacks thin.
- Move period, aggregation, coverage, state, cache, and report-note logic into the service.
- Move SQL into a dedicated DAL.
- Keep the renderer deterministic and free of SQL/registry reads.
- Resolve the invoking author and current registry before data access.
- Re-resolve current registry authority before every period/scope fetch and immediately before any
  transition that could expose a different governor.
- Mode-only changes reuse the current immutable authorized payload where possible.

### 12.2 Selector and component state

- One linked distinct governor opens directly without a redundant selector.
- Multiple governors default to selected Dashboard context, then Main, then first canonical slot.
- All Linked is explicit and never the initial default.
- Use Governor ID or an opaque server-held token, not governor name, as component identity.
- Support duplicate names and the full configured Main + 5 Alts + 20 Farms population.
- Provide safe >25 paging or a separately opened governor-picker pattern consistent with GovernorOS.
- Preserve selected mode and period across scope changes and selected scope/period across mode changes.
- Keep component layout within Discord's five-row and 25-component constraints.
- The architecture approval must lock the exact row layout; do not improvise during implementation.

### 12.3 Interaction safety and concurrency

- Perform author/expiry/access checks before mutating visible state.
- Acknowledge interactions promptly without allowing foreign users to disable controls.
- Disable or show loading state during valid work and restore usable controls after handled failure.
- Use one transition generation/reservation so the latest valid request wins.
- Suppress stale data/render/delivery completion without replacing newer content.
- Propagate cancellation correctly.
- Never post a channel-visible failure or expiry notice for this private report.

### 12.4 Data and SQL

- Use one consistent source anchor and exact period across every metric, trend, coverage value, and
  fallback field.
- Prefer one set-based request payload rather than the current sequential summary/trend/freshness
  reads.
- Do not reuse current `last_3m`/`last_6m` semantics for Last 90/180 Days.
- Preserve negative values and source corrections.
- Do not convert missing/null to zero without SQL/source proof.
- Bound and validate Governor IDs, period keys, date windows, row counts, and result shapes at the
  service/DAL boundary.
- Deduplicate authorized Governor IDs before the SQL read.
- Avoid N+1 reads and per-governor SQL loops.
- No SQL migration/deployment is included unless separately approved after the architecture stop.

### 12.5 Renderer and avatar

- Validate `assets/me/cards/me_stats.png` strictly at runtime or test time according to accepted
  renderer patterns: exact `1702x924`, fully opaque, production asset only.
- Render a standalone PNG with stable filename:

```text
me_stats_<discord_user_id>.png
```

- Use the invoking player's bounded circular Discord avatar at top left on Overview, Activity, and
  Combat, with the safe local fallback.
- Reuse avatar bytes across in-place transitions where safe; do not refetch for fallback.
- Render off the event loop with an explicit timeout.
- Support long/Unicode names and maximum compact values.
- Keep signed values readable without depending on red/green colour alone.
- Integrate charts into Activity; no separate chart embeds on the successful path.
- Close Pillow outputs, chart streams, `discord.File`, and underlying streams on every path.

### 12.6 Same-payload fallback

- Build a complete private embed/text fallback from the same already-authorized payload.
- Fallback contains identity/scope, exact period dates, state/coverage, all mode-relevant metrics,
  chart text equivalents, source anchor, and generated time.
- Render or attachment-delivery failure does not trigger a second SQL read or bypass access.
- Do not expose exception class names or raw SQL errors to players.
- A fallback delivery transition clears/replaces obsolete attachments deliberately.

### 12.7 Timeout

- New Phase 6 controls use a 180-second inactivity baseline, implemented through replacement/new-view
  state so successful transitions receive a fresh interaction window where appropriate.
- On timeout, preserve the last valid report, disable every control, reject later interactions, and
  show concise private rerun guidance:

```text
Report controls expired. Run /me stats to refresh.
```

- Do not delete the report, send a second expiry card, advertise a retired command, or post publicly.

### 12.8 Cache and performance

- Authorisation is checked before returning cached data.
- Cache keys include exact period/scope and distinct Governor IDs; stale registry membership cannot
  widen a cached response.
- Use a bounded TTL/LRU or equivalent structure with explicit eviction, not an unbounded dictionary.
- Deduplicate inflight identical reads safely.
- Separate data, render, and delivery timings.
- Mode-only rendering must not create avoidable DB work.
- Confirm representative single, multi, 26-account, 90-day, and 180-day costs before release.

### 12.9 Telemetry and logging

Record narrow structured events for:

```text
entry route: direct /me stats | Dashboard Stats
mode
period
scope type: governor | all_linked
linked/reporting governor counts
reporting/expected days and account-days
result state
data duration
render duration
delivery duration
fallback reason
timeout
access changed/stale transition suppression
```

Do not routinely log governor names, account names, chart values, or raw SQL/player data in Phase 6
interaction telemetry. Preserve standard qualified command usage identity `me stats`.

### 12.10 Command Surface Governance

- [ ] Confirm post-Phase-5G baseline: 38 top-level, 99 grouped, 7 `/me`, 2 `/inventory`.
- [ ] Add grouped `/me stats`; grouped total becomes 100 and `/me` becomes 8.
- [ ] Remove top-level `/my_stats`; top-level total becomes 37.
- [ ] Remove `my_stats` from `APPROVED_TOP_LEVEL_COMMANDS`.
- [ ] Do not add a new top-level command or command group.
- [ ] Add/retain `@versioned()`, `@safe_command`, and `@track_usage()` on `/me stats`.
- [ ] Do not apply the legacy KVK stats-channel decorator to `/me stats`.
- [ ] Preserve `/stats player` registration, permission decorator, visibility, and usage identity.
- [ ] Update the canonical command table, grouped summary, user/operator docs, smoke references, and
  expected command-cache state.
- [ ] Run command registration validation and the dedicated inventory/registration smoke tests.
- [ ] Resync application commands after atomic deployment and verify `/me stats` present and
  `/my_stats` absent.

### 12.11 Player communication, deployment, observation, and rollback

Before deployment:

- capture a final usage snapshot for context;
- announce the new `/me stats` route and scheduled `/my_stats` removal in the existing player-stats
  channel;
- update player/operator guidance and smoke instructions;
- confirm the accepted asset is present on the exact deployment branch.
- confirm the runtime SQL principal can execute `dbo.usp_GetPersonalStatsDaily` through the existing
  same-owner permission chain; do not grant broad table access as a workaround.

Atomic deployment:

```text
deploy and verify dbo.usp_GetPersonalStatsDaily
add /me stats
add Dashboard Stats action
remove /my_stats
update command validator/docs/tests
deploy/restart bot
resync application commands
/ops resync_commands
/ops validate_command_cache
/ops show_command_versions
```

`/ops resync_commands` is the authoritative guild sync/cache update. After it reports success,
`/ops validate_command_cache` must show the runtime cache matches registration and
`/ops show_command_versions` must show `/me stats` `v1.00`; verify `/my_stats` is absent and
`/stats player` remains before player smoke.

Post-deployment observation:

- direct and Dashboard entry use;
- selected governor versus All Linked;
- period and mode use;
- state/coverage outcomes;
- cold/warm latency;
- fallback rate and reason;
- timeouts, stale suppression, and access-change events;
- player feedback in the current stats channel.

Rollback:

1. revert the accepted Phase 6 bot patch;
2. restore `/my_stats` to the approved top-level inventory;
3. redeploy/restart;
4. resync application commands;
5. smoke the restored private channel-gated route and preserved `/stats player`;
6. after the bot is confirmed on the restored contract, run the approved SQL rollback to drop
   `dbo.usp_GetPersonalStatsDaily`, or leave the additive object only with explicit operator approval.

The SQL migration changes no table data. Its rollback drops only the new additive procedure after
the bot dependency has been removed.

## 13. Refactor Decisions

The audit must confirm or amend this table before implementation.

| Issue | Decision | Reason |
|---|---|---|
| Top-level `/my_stats` registration and old channel-gated personal journey | `fix now` | Explicitly approved for atomic retirement in Phase 6. |
| New private `/me stats` typed stack | `fix now` | Required to meet the approved product, access, data, rendering, and lifecycle contracts. |
| Current Last 3M/Last 6M period labels and month-boundary meanings | `fix now for personal route` | Replace with exact Last 90/180 Days; do not silently change leadership semantics. |
| Name-valued selector and >25 option risk | `fix now` | Governor ID/opaque identity and safe paging are required for the personal route. |
| Missing access revalidation and transition race in personal route | `fix now` | Privacy/integrity requirement. |
| Current sequential summary/trend/freshness and chart work | `fix now for new stack` | Required for performance, consistent anchor, coverage, and truthful state. |
| Legacy `embed_my_stats.py` and root `stats_service.py` used by `/stats player` | `retain` | Leadership scope is deferred to `/stats player` versus `/me inspect` review. |
| Existing `/stats player` behavior defects or presentation quality | `defer` | Do not mix leadership redesign into the player migration; capture structurally. |
| Broad shared GovernorOS selector/renderer/view consolidation | `defer` | Only extract proven identical contracts needed by Phase 6. |
| SQL view/procedure/function changes | `not pre-approved` | Validate read-only; stop for explicit SQL escalation if required. |
| Account Summary downloads and Stats export builders | `not applicable` | Phase 5G owns downloads; Phase 6 adds no downloadable data output. |
| Ark metrics in period performance | `remove now` | Duplicate Dashboard content and invalid/irrelevant period placement. |

Non-security out-of-scope findings use the structured deferred optimisation format. Suspected
security findings remain in the security workflow and are not downgraded into ordinary debt.

## 14. Testing Requirements

Use `k98-test-selection` and provide coverage or a precise skip reason for every category.

### 14.1 Command and migration

- `/me stats` is registered with private behavior and standard decorators.
- `/my_stats` is absent from source inventory and approved top-level baseline.
- `/stats player` remains registered with unchanged permission/visibility semantics.
- Exact `37 top-level / 100 grouped / 8 me / 2 inventory` final counts.
- Dashboard Stats action preserves selected Governor ID.
- No legacy channel gate is applied to `/me stats`.
- Command resync smoke confirms the old guild command is absent.

### 14.2 Registry, selector, and access

- no accounts;
- registry unavailable;
- one account/direct open/no redundant selector;
- multiple accounts/Main default;
- selected Dashboard governor default;
- Main missing/first canonical slot fallback;
- duplicate governor names;
- duplicate Governor IDs deduplicated with warning;
- full 26-slot registry plus explicit All Linked and safe paging;
- foreign interaction;
- expired interaction;
- forged Governor ID/token;
- governor unlinked, replaced, or transferred after open;
- All Linked membership changed after open;
- no silent fallback to All Linked;
- mode change reuses payload;
- period/scope change revalidates and fetches once;
- latest valid interaction wins and stale completion is suppressed.

### 14.3 Period boundaries

Use deterministic injected anchors covering:

- Monday and Sunday;
- month start/end;
- December/January rollover;
- leap year and 29 February;
- Yesterday exact prior date;
- Last Week previous Monday-Sunday;
- Last Month complete previous month;
- Last 90 exactly 90 inclusive dates;
- Last 180 exactly 180 inclusive dates;
- sparse source dates and missing Yesterday;
- all metrics/trends/coverage using the same boundaries.

### 14.4 Metrics and All Linked

For every approved metric:

- positive value;
- zero value;
- negative correction;
- null/missing source;
- selected governor;
- All Linked additive aggregation;
- reporting-governor and account-day coverage;
- duplicate-ID exclusion;
- no missing-as-zero without source proof;
- total and average-per-reporting-day parity;
- T4 + T5 combined-source/derived parity;
- no Ark fields;
- no export/download fields or controls.

### 14.5 State and fallback

- READY complete data;
- PARTIAL missing dates/governors/source coverage;
- NO DATA healthy empty exact window;
- UNAVAILABLE registry/data failure;
- access-changed interaction;
- player-facing copy contains no raw exception/SQL detail;
- same payload used for fallback;
- fallback contains all mode-relevant values and chart equivalents;
- image render failure;
- chart failure;
- attachment creation failure;
- send/edit failure;
- no second data fetch on fallback;
- no public fallback.

### 14.6 Renderer, chart, and accessibility

- strict `1702x924` output and backdrop validation;
- fully opaque PNG;
- stable `me_stats_<discord_user_id>.png` filename;
- avatar and safe fallback on all three modes;
- long/Unicode Discord and governor names;
- large positive/negative values;
- signs/labels present without colour-only meaning;
- Activity RSS/Fort two-chart layout;
- negative chart point and signed axis;
- one-point Yesterday treatment;
- no-point/no-chart treatment;
- controlled tick density;
- chart text equivalents;
- Overview/Activity/Combat original-size, Discord desktop, and mobile previews;
- selected governor, All Linked, PARTIAL, NO DATA, UNAVAILABLE, and avatar-fallback visual samples.

### 14.7 Lifecycle, cache, and performance

- every `discord.File` and underlying stream closes on success/failure/cancel/timeout/navigation/stale suppression;
- attachment replacement clears obsolete charts/cards;
- 180-second timeout preserves report and disables controls;
- late interaction rejection;
- no second expiry message and no channel-visible notice;
- bounded cache eviction and TTL behavior;
- authorization before cache reuse;
- inflight deduplication and exception consistency;
- representative 26-account/180-day row shape;
- data/render timeout behavior;
- telemetry events and content minimisation;
- no event-loop blocking regression.

### 14.8 Regression boundary

- Account Summary Download data and all three output kinds unchanged;
- Resources/Speedups/Materials report-page exports unchanged;
- `/inventory import` and `/inventory audit` unchanged;
- `/stats player` command registration and core rendering path retained;
- Dashboard, Accounts, Reminders, Preferences, Inventory reports, and navigation still function;
- no new direct SQL in command or view modules.

### 14.9 Baseline validation commands

At minimum consider and record results for:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Add focused commands selected from the final manifest for Stats command, DAL/service, renderer,
views, dashboard integration, registration governance, and Phase 5G download regressions.

Before PR handoff, complete the Security Review Decision table and retain the evidence. The routine
bot review uses the final Changes target with `Deep: Off`. The additive SQL repository uses its own
final Changes target with `Deep: Off`; neither review is a codebase/deep scan.

## 15. Acceptance Criteria

- [ ] Audit, architecture, and implementation plan were separately approved before coding.
- [ ] `/me stats` is registered under the existing `/me` group with standard decorators and private
  use from any guild channel/thread.
- [ ] `/my_stats` is removed, not redirected, and absent after command resync.
- [ ] Final command counts are 37 top-level, 100 grouped, 8 `/me`, and 2 `/inventory`.
- [ ] The selected-governor Dashboard exposes Stats and preserves validated governor context.
- [ ] No/one/multiple/26-slot and All Linked journeys behave as approved.
- [ ] Governor ID/opaque component identity replaces name-based authority.
- [ ] Current registry linkage is revalidated before every data fetch.
- [ ] Overview, Activity, and Combat use one approved `assets/me/cards/me_stats.png` backdrop.
- [ ] Every successful card uses the invoking player's circular Discord avatar at top left with safe
  fallback and is exactly `1702x924`.
- [ ] Header identity, exact period dates, data anchor, coverage, state, and generated UTC are truthful.
- [ ] Yesterday, This Week, Last Week, This Month, Last Month, Last 90 Days, and Last 180 Days match
  the exact approved inclusive source-date contracts.
- [ ] Last 90/180 do not reuse the current Last 3M/6M month semantics.
- [ ] Power/Troop movement, RSS, RSS Assistance, Helps, Build, Tech, Forts, KP, T4, T5, Deads, and
  Healed values are source-correct, signed, and coverage-aware.
- [ ] All Linked includes only approved additive metrics, deduplicates IDs, recomputes averages, and
  shows reporting/account-day coverage.
- [ ] Ark is completely absent from the personal Period Performance experience.
- [ ] No download/export action or Phase 5G output contract appears in `/me stats`.
- [ ] Activity integrates truthful RSS/Fort trends and complete accessible text equivalents.
- [ ] READY/PARTIAL/NO DATA/UNAVAILABLE and access-changed behavior are distinct and honest.
- [ ] Same-payload fallback performs no second data fetch and contains all key information.
- [ ] Latest interaction wins; stale/foreign/forged/expired transitions cannot replace valid content.
- [ ] Timeout preserves the last report, disables controls, remains private, and references only
  `/me stats`.
- [ ] Data, chart, avatar, attachment, and stream work is bounded, off-loop where required, and
  cleaned up on every path.
- [ ] Representative performance meets the approved measured budgets or an explicit operator-approved
  adjustment is documented.
- [ ] `/stats player` remains registered and its proven legacy dependencies are preserved for the
  later Inspect review.
- [ ] Account Summary downloads and Inventory report-page exports remain unchanged.
- [ ] Player communication, deployment/restart, command resync, observation, smoke, and rollback are
  documented and exercised.
- [ ] Focused, visual, full, architecture, command, deferred, security-routing, import, pre-commit,
  log-noise, and PR-review gates pass or have precise accepted exceptions.
- [ ] Final bot security review is Changes with Deep off and no unresolved Phase 6 finding.
- [ ] Additive SQL procedure/migration/rollback pass a separate SQL Changes review with Deep off.
- [ ] Non-security out-of-scope findings are captured structurally; security findings remain in the
  security workflow.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. Deleted/Narrowed Legacy Code With Caller Proof
6. SQL Validation / SQL Changes
7. Period, Metric, Coverage, And All Linked Contract
8. Renderer / Visual Samples / Accessibility
9. Helpers Reused
10. Refactor Findings
11. Test Results
12. Security Review Decision And Evidence
13. Player Communication
14. Deployment / Restart / Command Resync
15. Operator Discord Smoke
16. Rollback
17. Deferred Optimisations

## 17. PR Summary Template

```md
## Summary

- add private `/me stats` Period Performance with Overview, Activity, and Combat on the approved
  `1702x924` GovernorOS card
- support selected-governor and explicit coverage-aware All Linked scope across seven exact periods
- remove `/my_stats` rather than retaining a redirect, then resync the command surface
- preserve Account Summary downloads, Inventory report-page exports, and leadership `/stats player`

## Changes

- add typed personal Stats models, read-only DAL/service, renderer, author-gated view, charts, fallback,
  lifecycle, telemetry, and tests
- add the selected-Dashboard Stats action and invoking-user avatar presentation
- replace Last 3M/6M with exact Last 90/180 Days
- update command governance, documentation, communication, smoke, and rollback records

## Tests

- Focused Phase 6 command, DAL, service, renderer, view, and regression commands selected by `k98-test-selection`
- Approved original-size, Discord desktop, and mobile visual matrix
- `python scripts/validate_command_registration.py`
- `python scripts/validate_architecture_boundaries.py`
- `python scripts/validate_deferred_items.py`
- `python scripts/validate_codex_security_routing.py`
- `python scripts/smoke_imports.py`
- `python -m pytest -q tests`
- `python -m pre_commit run -a`

## Security Review

- Decision: `Changes review`
- Repository / target: `K98-bot-mirror` final intended base..head recorded in the PR
- Expected setup / execution: `Changes + Deep Off`
- Evidence: completed scan result and finding disposition recorded before PR handoff
- SQL repository: separate additive-procedure Changes review with `Deep: Off`

## Deployment / Command Resync

- announce the new route and old-command removal before deployment
- deploy/restart the exact accepted bot patch
- resync application commands
- verify `/me stats` present, `/my_stats` absent, `/stats player` retained, and counts `37 / 8 / 2`

## Deferred Optimisations

- None, or structured non-security items including the later `/stats player` versus `/me inspect`
  architecture decision.

## Risk / Rollback

- Primary risks are incorrect period/coverage math, over-aggregation, stale access, slow 180-day All
  Linked rendering, and accidental leadership-stack deletion. Rollback restores the accepted pre-
  Phase-6 bot patch and `/my_stats` registration, redeploys, resyncs commands, and re-smokes the
  restored route. After bot rollback, the SQL rollback drops only the additive procedure; no data
  rollback is required.
```
