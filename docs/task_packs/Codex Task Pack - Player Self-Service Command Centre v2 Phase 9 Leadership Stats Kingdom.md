# Codex Task Pack - Player Self-Service Command Centre v2 Phase 9 Leadership `/stats kingdom`

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 9 Leadership /stats kingdom`
- Date: `2026-07-19`
- Owner/context: `KD98 / Kingdom 1198 leadership analytics follow-on from Phase 8 /stats player`
- Task type: `leadership feature | grouped command | SQL aggregation | visual renderer | privacy/security | documentation`
- One-pass approved: `no`
- Product direction approved: `yes`
- Detailed audit/design approved: `yes`
- Runtime implementation approved: `Phase 8 acceptance prerequisite is satisfied; runtime remains blocked on the audit, SQL design, architecture, implementation-plan, visual, performance, security, and operator scheduling gates in this pack`
- Status: `proposed; programme scope agreed, detailed refinement may occur when Phase 9 becomes active`
- New command: `/stats kingdom`
- New top-level command: `none`
- Command target after deployment: `36 top-level; grouped 100 -> 101; /me remains 8; /stats 1 -> 2; /inventory remains 2`
- Command resync required: `yes`
- SQL deployment approved: `additive bounded kingdom reporting contracts only, through separately reviewed SQL PRs deployed before the bot patch`

## 2. Product Decision

Add one private leadership kingdom-review subcommand:

```text
/stats kingdom
```

It belongs beside `/stats player` under the same dedicated leadership permission and audit family.

It does not belong under `/me`.

The first release has exactly two main pages:

```text
Kingdom Overview
KVK Summary
```

A private Definitions/Method action explains formula and source semantics.

No public output, export, arbitrary kingdom selector, or website endpoint is added in Phase 9.

## 3. Locked Decisions

### Permission

Reuse the dedicated Phase 8 gate:

Leadership role IDs:

- Leadership channel.
- Child threads of the Leadership channel.

Admin:

- Leadership channel and child threads.
- Notify channel and child threads.

Never:

- role-name-only authorization;
- Ark Setup;
- DMs;
- any other channel.

Every interaction rechecks authorization.

### Kingdom Overview metrics

- Total Power.
- Total Kill Points.
- Total Deads.
- Total Healed.
- Total T4+T5 Kills.
- Total Kingdom Acclaim = `SUM(HighestAcclaim)` for the dynamic roster at the selected monthly snapshot.
- Active Governors = distinct Governor IDs in the authoritative complete scan.

Add context:

- Average Power per Active Governor.
- Net Active-Governor Change over 12 months.

Use `Governors`, not deduplicated human `Players`.

### Twelve-month chart

- Dynamic roster for each month.
- Monthly point = final authoritative complete scan in that calendar month.
- Current month uses latest complete scan and is labelled month to date.
- One chart with metric selector, not all scales overlaid.
- Missing months remain missing.
- Do not interpolate.

Selectable chart metrics:

```text
Power
Kill Points
Deads
Healed
T4+T5 Kills
Total Kingdom Acclaim
Active Governors
Average Power per Active Governor
```

### KVK Summary

- Last four completed/finalized KVKs.
- Completion uses the existing KVK reporting/state resolver.
- KVK type/name = `KVK_NAME`.
- Four equal blocks, newest first.

Each block:

- KVK number.
- KVK name.
- final data timestamp/state.
- Kill Points.
- T4+T5 Kills.
- Deads.
- Healed.
- KVK Acclaim = `SUM(Acclaim)` from one authoritative final row per Governor ID.
- Participants = distinct Governor IDs with final-event `Acclaim > 0`.
- Acclaim per Participant = `SUM(Acclaim) / Participants`.
- KP Loss = `SUM(Healed) * 20`.
- Tanking Score = `SUM(Kill Points) / (SUM(KP Loss) + SUM(Deads)) * 100`.
- Higher Tanking Score is better.

Do not average individual Tanking Scores.

### Participant definition

```text
COUNT(DISTINCT GovernorID)
WHERE final completed-KVK Acclaim > 0
```

- Governor count, not human-player count.
- Count once.
- Missing Acclaim makes participant metrics unavailable.
- Genuine zero means nonparticipant.
- Do not sum overlapping window rows.

## 4. Required Reading

Read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- engineering, execution, testing, skills/refactor, and deferred-framework references;
- active GovernorOS programme pack;
- this task pack;
- completed Phase 7 and Phase 8 packs;
- archived KVK reporting, KVK history, KVK rankings, KVK schema modernisation, and Phase 6 Stats packs;
- canonical command reference;
- deferred optimisations;
- player/operator briefing.

Validate SQL against:

```text
C:\K98-bot-SQL-Server
```

## 5. Objective

Give authorized leadership one private, source-transparent view of:

- current kingdom scale;
- twelve-month kingdom movement;
- roster expansion/contraction context;
- the last four completed KVK outcomes;
- kingdom fighting efficiency;
- breadth of KVK participation through Acclaim;
- source freshness and missing-history limitations.

The result should support strategic review without requiring spreadsheets, public KVK cards, or manual
aggregation.

## 6. Current State To Audit

Map:

- Phase 8 dedicated permission, audit, renderer, lifecycle, and Definitions patterns;
- `/stats` command registration and command-count tests;
- latest complete kingdom scan contract;
- `KingdomScanData4` scan/day/month history;
- existing 12-month or dashboard aggregate objects;
- KVK completion resolver;
- `KVK.KVK_Kingdom_Windowed`;
- `KVK.KVK_Player_Windowed`;
- KVK final/full reporting views;
- `v_EXCEL_FOR_KVK_All` and final Acclaim;
- `KVK_Details.KVK_NAME`;
- existing all-kingdom reporting DAL/service;
- source freshness;
- current indexes/plans;
- current KVK aggregate duplication risks across named windows.

The audit must identify one authoritative source per displayed metric.

## 7. Command Shape

```text
/stats kingdom
```

No options in the first release.

The command resolves the configured home kingdom from the existing authoritative constant/config.

Do not expose arbitrary kingdom input.

Private successful output opens Kingdom Overview.

## 8. Output Contract

### Accepted Phase 7/8 visual inheritance

Use the operator-accepted GovernorOS core visual language as the proportional starting point while
remaining a neutral leadership Kingdom product:

- `1702x924` standalone private card baseline, shared `core/visual_contract.py` colours,
  typography, state, panel, compact-number, UTC-date, and bounded placement primitives where
  consumers are identical;
- a top-right state pill with horizontally and vertically centred text, with source/page context
  aligned beneath it;
- row 0 owns Kingdom Overview and KVK Summary page navigation; the chart metric selector and
  Definitions/Method start below it and stay within Discord component-row limits;
- blue navigation/selection/neutral `UTC`, green current/success, amber stale/partial/review, red
  unavailable/failure/no data, and muted disabled/expired;
- truthful source freshness separate from generated UTC, compact unit-correct metrics, genuine
  zero preservation, and the accepted missing-value vocabulary;
- same-authorized-payload fallback, latest-transition-wins suppression, safe attachment
  replacement, preserve-and-disable timeout, and deterministic file/stream cleanup.

Do not force the Kingdom Overview chart or four-KVK summary into `/me` geometry. Do not add a
governor dropdown, player picker, `All Linked`, or arbitrary kingdom selector.

Primary pages:

```text
Kingdom Overview
KVK Summary
```

Controls:

- Overview.
- KVK Summary.
- Definitions/Method.
- chart metric selector on Overview.
- no player lookup;
- no governor selector;
- no export;
- no public share.

Successful output:

- private standalone leadership card;
- same-authorized-payload fallback;
- no second data fetch for fallback;
- in-place attachment replacement;
- bounded timeout;
- latest valid transition wins;
- files/streams closed;
- no player Discord avatar.

Proposed timeout copy:

```text
Kingdom review controls expired. Run /stats kingdom to refresh.
```

## 9. Page 1 - Kingdom Overview Header

Show:

- `Kingdom 1198` or configured kingdom label;
- latest complete scan timestamp/date;
- source state;
- `CURRENT`, `STALE`, `PARTIAL`, or `NO DATA`;
- current month-to-date label where relevant;
- generated UTC separately.

Freshness:

- current when latest authoritative scan <= 48 hours;
- stale when older;
- partial when monthly series/current totals have material source gaps;
- no data when no valid scan exists.

## 10. Current Headline Metrics

Tiles:

```text
Total Power
Total Kill Points
Total Deads
Total Healed
Total T4+T5 Kills
Total Kingdom Acclaim
Active Governors
Average Power / Active Governor
```

Each primary tile shows:

- latest value;
- net change over 12 months where a comparable point exists;
- latest complete scan date;
- compact number;
- missing/partial state.

### Total Kingdom Acclaim

Definition:

```text
SUM(HighestAcclaim)
for Governor IDs present in the dynamic roster at the monthly snapshot
```

Helper text:

```text
Combined current-roster Highest Acclaim
```

This is not Acclaim earned during the month.

### Active Governors

Definition:

```text
COUNT(DISTINCT GovernorID)
in the authoritative monthly complete scan
```

Do not deduplicate linked accounts into one human player.

### Average Power

```text
SUM(Power) / Active Governors
```

Unavailable for zero/missing denominator.

## 11. Monthly Dynamic-Roster Series

For each of 12 calendar months:

1. locate the final authoritative complete `SCANORDER` in the month;
2. select one final row per Governor ID in that scan;
3. aggregate the approved metric;
4. record scan timestamp, governor count, and source state.

Current month:

- latest complete scan;
- label `MTD`;
- do not imply complete month.

Missing month:

- no point;
- no zero;
- no interpolation.

Dynamic roster is intentional: each month represents the kingdom as it existed then.

## 12. Chart Contract

One large chart with selector.

Do not overlay incompatible scales.

For selected metric show:

- 12 monthly points;
- month labels;
- value labels or accessible text summary;
- first/latest/net change;
- min/max month;
- missing months;
- current MTD marker;
- source scan date for each point in fallback/Definitions.

Chart accessibility:

- labels and markers;
- no colour-only meaning;
- text summary;
- long-value compact formatting;
- original/desktop/mobile review;
- one-point and missing-series handling.

## 13. Net Active-Governor Change

Show:

```text
latest active governors - earliest comparable monthly active governors
```

Helper:

```text
+18 governors over 12 months
```

Do not interpret as migration, retention, or unique human-player growth without further evidence.

## 14. Page 2 - Last Four Completed KVKs

Resolve the latest four KVKs classified as ended/finalized by the shared KVK state/reporting contract.

Do not use:

- latest started KVK;
- end date alone;
- active KVK;
- incomplete final output;
- overlapping named windows summed together.

Four equal blocks, newest first.

Block title:

```text
KVK 15
KVK_NAME
```

Block data:

```text
Kill Points
T4+T5 Kills
Deads
Healed
KVK Acclaim
Participants
Acclaim / Participant
KP Loss
Tanking Score
```

Optional helper only if space/readability allows:

- final data timestamp;
- source complete/partial badge.

## 15. Final-Event Row Contract

Use exactly one authoritative final full-event row per Governor ID/KVK.

The audit must prove which object supplies:

- Governor ID;
- final `Acclaim`;
- Kill Points;
- T4;
- T5;
- Deads;
- Healed;
- final scan/output timestamp.

Do not sum:

- Pass 4/6/7/8 rows plus Full;
- duplicate view/table versions;
- multiple named windows representing overlapping ranges;
- current/final snapshots together.

If final-event uniqueness cannot be proved, the block is partial/unavailable.

## 16. KVK Acclaim And Participants

### KVK Acclaim

```text
SUM(final Acclaim)
```

### Participants

```text
COUNT(DISTINCT GovernorID)
WHERE final Acclaim > 0
```

### Acclaim per Participant

```text
SUM(final Acclaim) / Participants
```

Rules:

- positive participants only;
- zero participants -> `N/A`;
- missing Acclaim -> unavailable;
- each Governor ID once;
- show participant count as governors;
- no Discord registry dependency.

## 17. Kingdom KP Loss And Tanking Score

```text
Kingdom KP Loss = SUM(Healed Troops) * 20

Kingdom Tanking Score =
    SUM(Kill Points)
    --------------------------------
    Kingdom KP Loss + SUM(Deads)
    * 100
```

- ratio of sums;
- higher is better;
- non-positive denominator -> `N/A`;
- same shared Python/SQL parity fixtures as Phase 8;
- no average of individual scores;
- no old playstyle labels.

## 18. Source Coverage And Missing Data

Overview:

- latest scan freshness;
- month count available out of 12;
- earliest/latest point;
- missing month list.

KVK Summary:

- completed/final KVKs available out of four;
- missing metric state per KVK;
- final data timestamp;
- no missing-as-zero.

If fewer than four completed KVKs exist, show available blocks and honest missing slots.

## 19. Definitions/Method Panel

Explain:

- dynamic roster;
- final complete monthly scan;
- current month MTD;
- Active Governors;
- Total Kingdom Acclaim `SUM(HighestAcclaim)`;
- KVK Acclaim `SUM(Acclaim)`;
- Participants `Acclaim > 0`;
- Acclaim per Participant;
- KP Loss;
- Tanking Score ratio of sums;
- KVK completion source;
- freshness and missing months.

No second data query.

## 20. SQL Design

Prefer one bounded procedure or a small cohesive contract family.

Potential:

```text
dbo.usp_GetLeadershipKingdomReview
```

Inputs:

```text
@Kingdom
@Months = 12
@KvkCount = 4
@NowUtc optional
```

Return compact result sets:

- latest header/current totals;
- 12 monthly series rows;
- last four KVK aggregate rows;
- source coverage/history metadata.

Requirements:

- static parameterized T-SQL;
- bounded 12 months/four KVKs;
- one final scan per month;
- one final row per Governor ID/KVK;
- no dynamic SQL;
- no direct SQL in command/view;
- no large raw all-kingdom row transfer when SQL can aggregate;
- index changes only after plans/logical reads/timings/concurrency.

## 21. Architecture

Suggested package:

```text
leadership_kingdom/
    models.py
    service.py
    dal.py
    renderer.py
    views.py
```

Reuse from Phase 8:

- dedicated permission gate;
- leadership audit service;
- standalone delivery;
- fallback;
- state pill/visual language;
- timeout;
- transition safety;
- Definitions control;
- shared combat metrics.

Do not couple player-review payloads to kingdom-review payloads.

## 22. Audit

Use the dedicated leadership audit family.

Actions:

```text
kingdom_open
kingdom_page_change
kingdom_metric_change
kingdom_definitions
```

Store:

- actor ID;
- authorization basis/role ID;
- guild/channel;
- action/outcome;
- correlation ID;
- formula/payload version if useful.

Do not store:

- full kingdom metric values;
- rendered card;
- player names;
- raw SQL errors.

Identified retention remains 90 days.

## 23. Performance

Provisional targets:

- initial p95 <= 6 seconds;
- page transition using payload <= 3 seconds;
- metric selector using payload <= 2 seconds;
- one bounded SQL load;
- one render at a time per transition;
- latest valid transition wins.

Measure:

- cold/warm 12-month series;
- full monthly dynamic rosters;
- four completed KVKs;
- concurrent leadership requests;
- plan stability;
- logical reads;
- memory grants;
- image render time.

Do not add a materialized monthly table unless evidence proves the on-demand contract is unsuitable and
a refresh/staleness/rollback design is approved.

## 24. Visual Direction

Use the Phase 8 leadership product family, not `/me` identity styling.

Requirements:

- private leadership title;
- clear Kingdom identity;
- source state/freshness;
- large current totals;
- one readable chart;
- four balanced KVK blocks;
- consistent semantic colours;
- mobile readability;
- neutral KD98/kingdom mark;
- no Discord avatar;
- no crowding to fit unnecessary metrics.

The visual workshop may adjust geometry but not the locked data definitions without approval.

## 25. Command Governance

Before Phase 9:

```text
36 top-level
100 grouped
8 /me
1 /stats: player
2 /inventory
```

After Phase 9:

```text
36 top-level
101 grouped
8 /me
2 /stats: player, kingdom
2 /inventory
```

Update command inventory/validator/tests/docs and resync after deployment.

No new approved top-level command entry is required because `/stats` already exists.

## 26. Testing

### Permission

- same matrix as Phase 8;
- every page/selector recheck;
- role revoked;
- foreign/forged/late interactions;
- private only.

### Monthly series

- each calendar month;
- current MTD;
- dynamic roster;
- governor joins/leaves;
- duplicate scan rows;
- final scan choice;
- missing month;
- zero values;
- no interpolation;
- totals/average/active count;
- HighestAcclaim sum semantics.

### KVK

- existing completion resolver;
- four ended;
- fewer than four;
- active KVK excluded;
- final row uniqueness;
- KVK_NAME;
- SUM(Acclaim);
- participants Acclaim > 0;
- acclaim/participant zero/missing;
- ratio-of-sums Tanking;
- no overlapping windows;
- missing metrics.

### Rendering/lifecycle

- both pages;
- every chart metric;
- long/large values;
- no data/partial/stale;
- fallback parity;
- dimensions/opacity;
- original/desktop/mobile;
- timeout;
- attachment cleanup;
- transition race.

### Compatibility

- `/stats player` unchanged;
- Phase 8 permission/audit helpers;
- KVK reporting;
- canonical Tanking parity;
- command counts;
- no `/me` change.

## 27. Security Review

Mandatory bot and SQL Changes reviews with Deep off.

Focus:

- permission reuse correctness;
- private delivery;
- SQL aggregation bounds;
- dynamic roster correctness;
- final-row duplication;
- resource exhaustion;
- audit minimization;
- interaction forgery;
- attachment cleanup;
- formula parity.

No standard/deep codebase scan without explicit request.

## 28. Deployment

1. Confirm the archived Phase 8 acceptance baseline and do not absorb the active Phase 8.1 scope.
2. Audit/approve Phase 9.
3. Develop SQL contract.
4. Deploy/verify SQL.
5. Deploy bot.
6. Restart.
7. Resync commands.
8. Validate command cache/versions.
9. Smoke both pages and every chart metric.
10. Observe and promote.

## 29. Rollback

1. remove `/stats kingdom` bot patch;
2. deploy/restart;
3. resync;
4. verify `/stats player` remains;
5. leave additive SQL objects in place unless separately rolled back;
6. smoke Phase 8 and KVK reporting.

## 30. Documentation

Update:

- programme pack;
- task-pack README;
- canonical command reference;
- briefing;
- deferred optimisations;
- command counts;
- Definitions copy;
- operator smoke;
- task pack/starter archive after acceptance.

## 31. Workflow And Gates

1. Audit/scope only, stop.
2. Present source-of-truth matrix, monthly/KVK uniqueness proof, SQL contract, visual wireframe,
   file manifest, performance plan, security targets, command count, stop.
3. Present implementation/test/deploy/resync/smoke/rollback plan, stop.
4. Implement SQL after approval.
5. Implement bot after approval.
6. Validate focused/full/visual/architecture/deferred/registration/import/pre-commit/log-noise.
7. Run separate SQL and bot Changes reviews with Deep off.
8. Complete PR review.
9. Deploy SQL then bot, resync, smoke, observe, promote.

## 32. Acceptance Criteria

- [ ] `/stats kingdom` exists privately under `/stats`.
- [ ] Permission/channel/audit contracts match Phase 8.
- [ ] No `/me` or top-level command is added.
- [ ] Kingdom Overview shows the locked current metrics.
- [ ] Total Kingdom Acclaim uses dynamic-roster `SUM(HighestAcclaim)`.
- [ ] Active Governors is a Governor ID count.
- [ ] Average Power and net active-governor change are correct.
- [ ] Twelve-month chart uses each month's dynamic roster and final complete scan.
- [ ] Current month is labelled MTD.
- [ ] Missing months are not zero/interpolated.
- [ ] One selector controls the chart metric.
- [ ] Last four KVKs use the existing completion/finalization contract.
- [ ] KVK type is `KVK_NAME`.
- [ ] KVK Acclaim uses one final `SUM(Acclaim)`.
- [ ] Participants are distinct governors with Acclaim > 0.
- [ ] Acclaim per Participant is included.
- [ ] KP Loss and ratio-of-sums Tanking Score use the canonical formula.
- [ ] No overlapping KVK windows are summed.
- [ ] Source freshness/coverage is honest.
- [ ] Definitions panel explains all material semantics.
- [ ] SQL plans/performance and security reviews are accepted.
- [ ] Command surface is `36 top-level / 101 grouped / 8 me / 2 stats / 2 inventory`.
- [ ] Resync and operator smoke pass.
