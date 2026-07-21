# Codex Task Pack - Player Self-Service Command Centre v2 Phase 8 Leadership `/stats player` Modernisation, Canonical Combat Metric Alignment and `/player_profile` Retirement

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 8 Leadership /stats player Modernisation, Canonical Combat Metric Alignment and /player_profile Retirement`
- Date: `2026-07-19`
- Owner/context: `KD98 / Kingdom 1198 leadership analytics follow-on after GovernorOS v2 Phase 7 /me closeout`
- Task type: `leadership feature | command modernisation | command retirement | SQL contract | visual renderer | privacy/security | combat-metric correction`
- One-pass approved: `no`
- Product decision approved: `yes`
- Audit/design approved: `yes`
- Runtime implementation approved: `complete`
- Status: `complete, production smoke tested and operator accepted on 2026-07-21; archived execution record`
- Canonical command: `/stats player`
- Removed command: `/player_profile`
- New `/me` command: `none`
- Command target after deployment: `37 -> 36 top-level; grouped remains 100; /me remains 8; /stats remains 1; /inventory remains 2`
- Command resync required: `yes`
- SQL deployment approved: `additive foundations and bounded leadership contracts only, through separately reviewed SQL PRs deployed before the dependent bot patch`

## 2. Product Decision

Phase 8 creates one definitive leadership player-review journey.

```text
/stats player
```

It does not create `/me inspect`.

`/me` remains the invoking player's linked-governor self-service family. Leadership review of an
arbitrary Governor ID belongs under `/stats`.

The existing `/player_profile` command is removed in the same accepted bot release. It is not kept
as a redirect, alias, compatibility path, public posting route, or second leadership location.

The successful end state is:

```text
Leadership/admin runs /stats player
-> exact Governor ID or normalized/fuzzy name lookup
-> private ambiguity selection when required
-> one private leadership review session
-> Overview / Kingdom Activity / KVK Performance / Player Record
-> Change Player or open an active linked governor
```

## 3. Locked Scope Decisions

### Command and target

- Modernise the existing `/stats player`.
- Preserve its grouped ownership under `/stats`.
- Keep `governor_id` and `name` as optional command options.
- Reject requests that provide both.
- Require one of them.
- Selected Governor ID is the performance scope.
- Do not aggregate all governors linked to the same Discord user into one Activity Index or rank.
- Active linked governors are context and navigation only.
- Remove `/player_profile` with no redirect after zero-caller proof.

### Periods

```text
30 days
90 days - default
180 days
360 days
```

- Exact inclusive windows anchored to the latest authoritative complete kingdom scan date.
- Compare with the immediately preceding equal-length window.
- A 360-day comparison may require up to 720 days of history.
- Keep a valid current 360-day result when the preceding 360 days are unavailable.
- Mark comparison unavailable.
- Never silently shorten or substitute either period.

### Scan Presence

- Every `KingdomScanData4.SCANORDER` is an authoritative complete kingdom scan.
- Presence denominator is all complete scans in the selected period.
- Label the metric `Scan Presence`.
- Also show scanned-day context.
- Presence remains outside the Activity Index.

### Rank cohort

- Governors present in the latest complete kingdom scan.
- Stale governors show their metrics but no current-kingdom rank.
- Ranks are per Governor ID, not deduplicated human player.
- Explicit zero is rankable where the source contract proves zero.
- Missing/untracked values are excluded from that metric's denominator.

### Activity Index v1

Weights:

```text
Forts Total       30%
Helps             22%
Tech Donations    18%
RSS Gathered      14%
Building Minutes  10%
Power Change       6%
```

- Prototype these weights, then replay production distributions before final acceptance.
- Missing component means Activity Index unavailable.
- Do not renormalise.
- Show every component score.
- Show `Activity Index v1` and Activity Rank.
- Do not add qualitative score bands in the first release.

### Data semantics

- Exclude negative monotonic-counter resets/corrections from contribution totals and warn.
- Negative Power Change remains valid and signed.
- Rally Daily contains only governors who recorded fort activity.
- Add a durable Rally Daily completion/header contract.
- Completed Rally date plus absent governor row means zero.
- No completed Rally report means missing.
- Alliance Activity snapshots cover every alliance represented in the latest complete kingdom scan
  and contain every member with explicit zero Building/Tech values.
- Missing expected Alliance Activity row is an integrity/coverage failure, not zero.
- Unallied governors may lack Alliance Activity coverage; Building/Tech and Activity Index are then
  unavailable.

### Freshness

- Latest authoritative kingdom scan no more than 48 hours old is current.
- Location has independent freshness.
- Show `CURRENT`, `STALE`, `PARTIAL`, or `NO DATA`.

### Location and shield

- Show latest `X:Y`.
- Show separate location-updated UTC timestamp.
- If `ShieldEndsAtUtc` is not null, show reported active/expired wording.
- Never put location/shield values in telemetry, audit details, filenames, or logs.

### Player Record

- Show active linked governor names and IDs.
- Exclude Discord user ID, Discord display name, and account slot/type.
- Show aliases grouped by Governor ID with First observed and Last observed.
- Add `GovernorNameHistory.LastSeen`.
- Maintain observation count internally.
- Show consecutive scan-derived alliance episodes.

### Canonical Tanking Score

Canonical formula everywhere:

```text
KP Loss = Healed Troops * 20

Tanking Score =
    Kill Points
    -------------------
    KP Loss + Deads
    * 100
```

- Higher is better.
- Invalid/zero denominator is `N/A`.
- Adopt across Account Summary, `/stats player`, future `/stats kingdom`, `/kvk stats`,
  `/kvk history` cards/summary/trends/CSV/ranks, and `/kvk rankings`.
- Rename `Lowest Tanking Score` to `Highest Tanking Score`.
- Sort Tanking Score descending.
- Remove old playstyle labels until new-formula production replay supports replacement bands.

### Heals ranking

Lower is better only among engaged participants:

```text
Kill Points > 0
AND at least one of:
- T4+T5 Kills > 0
- Deads > 0
- Healed > 0
```

### KVK targets

- `>=100%` means met.
- Exempt governors are omitted from eligible denominator.
- Show exemptions separately.
- Missing target data is not a failure.
- Missing KVK row is not zero.

### Permissions

Leadership role IDs:

- Leadership channel.
- Threads beneath the Leadership channel.

Admin user:

- Leadership channel and child threads.
- Notify channel and child threads.

Never:

- Ark Setup solely because it is in a generic allowed-channel collection.
- Role-name-only authorization.
- DMs.
- Any other guild channel.

Every interaction rechecks permission and channel.

### Audit

- Dedicated leadership review audit storage.
- Identified records retained 90 days.
- Longer-lived aggregates must be de-identified.
- No typed lookup text, names, metric values, location, shield, card contents, or raw SQL errors.

## 4. Required Reading

Read:

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
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 7 Visual Consistency Content Audit and Programme Closeout.md`
- archived Phase 6, Phase 5C, Phase 4, and KVK history/rankings task packs
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Validate all SQL assumptions against:

```text
C:\K98-bot-SQL-Server
```

## 5. Objective

Provide leadership with a private, decision-oriented review of one governor's current identity,
kingdom contribution, KVK performance, consistency, linked-governor context, aliases, alliance
history, and data confidence.

The review must answer:

- Is this governor current and identifiable?
- How much have they contributed to the kingdom over a meaningful period?
- How do they rank against the current kingdom?
- Are they consistently present in authoritative scans?
- Does recent contribution improve or decline against the preceding period?
- How did they perform in the latest completed KVK and the previous three?
- Are the visible conclusions based on complete data?
- What evidence-based leadership follow-up may be useful?

It must not expose Discord-user private settings or turn one opaque score into a disciplinary
judgement.

## 6. Confirmed Current State To Audit

At minimum map:

- current `/stats player` registration, decorators, channel behaviour, options, default period,
  fuzzy matching, multi-match `ALL` aggregation defect, views, charts, timeout, telemetry, and tests;
- current `/player_profile` registration, lookup, public/channel posting side effects, profile cache,
  renderer, views, buttons, fallbacks, tests, and every remaining caller;
- Phase 6 personal Stats models/service/DAL/renderer/view stack;
- Governor dashboard inspect-safe context and payload foundation;
- modern KVK history payload, renderer, ranks, CSV, and state;
- KVK stats and ranking Tanking Score consumers;
- Account Summary canonical KP Loss/Tanking implementation;
- registry reverse lookup;
- PlayerLocation and shield source;
- GovernorNameHistory;
- Alliance Activity snapshot header/rows;
- Rally Daily staging/current/import/audit flow;
- current KVK completion resolver in `kvk_state.py`;
- KVK final/full reporting rows;
- command-count validator and canonical docs.

The audit must produce a zero-caller deletion map before removing any profile-specific module.

## 7. Command Shape And Lookup

Command shape:

```text
/stats player governor_id:<optional> name:<optional>
```

Rules:

1. Neither supplied -> private validation error.
2. Both supplied -> private validation error.
3. Governor ID -> exact positive integer lookup.
4. Name -> normalize, exact-match first, fuzzy second.
5. One exact/fuzzy result -> open it.
6. More than one result -> private ambiguity selector.
7. No result -> private not-found response.
8. Never aggregate multiple fuzzy results.
9. Never treat ambiguity as `ALL`.

Normalization:

- Unicode-aware trim;
- collapse repeated whitespace;
- casefold;
- preserve genuine display spelling;
- bounded input length;
- parameterized SQL only;
- safe selector labels.

Ambiguity selector may show:

- governor name;
- Governor ID;
- current alliance;
- last scan date.

It must not show Discord identity or account slot.

`Change Player` uses the same dedicated lookup path and preserves selected period/page where safe.

## 8. Permission Contract

Create a dedicated gate rather than reusing the generic broad allowed-channel decorator.

Authorization inputs:

```text
fixed admin user ID
configured leadership role IDs
guild ID
channel ID or parent channel ID
```

Role names are not authority.

Check at:

- command entry;
- ambiguity selection;
- page switch;
- period switch;
- KVK-history/Definitions child action;
- linked-governor navigation;
- Change Player;
- refresh;
- fallback delivery.

If permission is revoked during a session, the next interaction fails closed privately and does not
reuse cached authorization.

## 9. Output And Navigation

### Accepted Phase 7 inheritance

Start from the operator-accepted Phase 7 core summary language, not from the legacy leadership
renderer. This is visual/interaction inheritance, not `/me` product ownership:

- proportional `1702x924` standalone-card baseline with neutral KD98/governor identity and no
  Discord avatar;
- shared `core/visual_contract.py` colours, typography hierarchy, panel edge/fill, compact-number,
  UTC-date, state, and bounded placement primitives where the consumers are identical;
- bright labels and values, restrained muted support copy, readable mobile scaling, and no
  colour-only meaning;
- one top-right state pill whose text is genuinely centred horizontally and vertically using
  font-bearing-aware placement; source/mode/period support aligns beneath it;
- row 0 is the four-page leadership navigation family. Period, Change Player,
  Definitions/Method, and any approved refresh control start on later rows and remain within
  Discord component limits;
- blue marks navigation/selection/neutral information, including `UTC`; green means current or
  success, amber means stale/partial/review, red means unavailable/failure/no data, and muted means
  disabled/expired;
- keep truthful source freshness separate from the generated UTC footer, and retain `—`, `Not
  recorded`, `NO DATA`, `UNAVAILABLE`, genuine zero, signed deltas, percentages, K/M/B, days,
  minutes, donations, RSS, KP Loss, and Tanking Score semantics;
- same-authorized-payload fallback, latest-transition-wins suppression, safe attachment
  replacement, preserve-and-disable timeout, and file/stream cleanup are mandatory.

Do not force the four leadership pages into the Preferences grid or any other `/me` page geometry.
Use the shared visual family while designing each page around its approved leadership evidence.

Primary private pages:

```text
Overview
Kingdom Activity
KVK Performance
Player Record
```

Controls:

- four page buttons;
- 30/90/180/360-day selector;
- Change Player;
- Definitions/Method;
- optional refresh only if the audit proves it is needed;
- no public share/export in Phase 8.

Successful output:

- standalone private generated card;
- leadership-specific renderer/payload;
- neutral KD98/governor identity, not Discord avatar;
- same-authorized-payload text/embed fallback;
- no second fetch for fallback;
- in-place attachment replacement;
- preserve current page/period when changing a linked governor where practical;
- bounded timeout that preserves the last report and disables controls.

Do not reuse the self-view linked-governor picker or All Linked option.

The Change Player and linked-governor controls must nevertheless retain the accepted selection
safety properties: exact Governor ID or opaque server-held token, duplicate-name-safe labels,
paging where more than 25 choices are possible, clear selected Governor ID, current selection
blue/disabled, page/period preservation, latest-transition-wins handling, and permission plus
target-access revalidation before every data read. They must never expose Discord identity,
account slot/type, or an `All Linked` choice.

## 10. Header Contract

Show:

- Governor name;
- Governor ID;
- current alliance;
- current Power;
- City Hall;
- last governor scan UTC;
- selected period and exact inclusive dates;
- number of valid source observations;
- data-confidence state;
- latest `X:Y`;
- separate location-updated UTC;
- shield line when `ShieldEndsAtUtc` is non-null.

Shield wording:

```text
Reported active until 18 Jul 2026, 16:30 UTC
Reported expired at 18 Jul 2026, 09:15 UTC
```

Omit when null.

Do not imply real-time shield confirmation.

## 11. Data-Confidence State

Precedence:

### `NO DATA`

No governor scan observation exists in the selected window.

### `STALE`

- Latest kingdom scan is more than 48 hours old; or
- source is current but governor is absent from the latest complete scan.

Show historical values when available. Withhold current-kingdom ranks.

### `PARTIAL`

Governor is current but one or more required sources cannot support a reliable total, comparison,
rank, KVK result, or Activity Index.

### `CURRENT`

- latest complete scan is no more than 48 hours old;
- governor is present;
- required source contracts are usable.

If both stale and partial:

```text
Primary badge: STALE
Secondary warning: Partial activity coverage
```

Location staleness does not change the kingdom-data badge.

## 12. Separate Presence And Coverage

Display two concepts.

### Scan Presence

```text
distinct complete SCANORDER values containing Governor ID
------------------------------------------------------------
all complete SCANORDER values in selected period
* 100
```

Also show:

```text
Present on X of Y scanned days
```

### Data coverage

Show source-specific coverage, for example:

```text
Stats scans 94/100
Alliance Activity 13/13 snapshots
Rally Daily 86/90 completed report dates
```

Presence answers whether the governor appeared. Coverage answers whether source systems support the
calculation.

Do not combine them into one score.

## 13. Period And Comparison Contract

Anchor:

```text
latest authoritative complete kingdom scan date
```

Current window:

```text
start = anchor - days + 1
end   = anchor
```

Previous window:

```text
previous_end   = start - 1
previous_start = previous_end - days + 1
```

Required source read depth:

```text
30  -> 60 days
90  -> 180 days
180 -> 360 days
360 -> 720 days
```

Comparison requires:

- both exact windows;
- valid source semantics in both;
- no excluded reset affecting the metric;
- comparable source definitions;
- valid alliance context where relevant.

Otherwise:

```text
Previous-period comparison unavailable
```

Do not display `0%` or `no change`.

## 14. History-Depth Audit

Produce a matrix:

| Source | Earliest | Latest | Gaps | 30+previous | 90+previous | 180+previous | 360+previous |
|---|---:|---:|---|---|---|---|---|
| Kingdom scans | | | | | | | |
| Alliance Activity | | | | | | | |
| Rally Daily completion | | | | | | | |
| Governor aliases | | | | | | | |
| Player locations | | | | | | | |
| Final KVK history | | | | N/A | N/A | N/A | N/A |

Distinguish:

- calendar dates;
- scan observations;
- snapshot dates;
- completed Rally report dates;
- genuine gaps;
- reset-excluded values;
- inferred/backfilled history;
- provable final KVK rows.

## 15. Kingdom Activity Metrics

Order:

1. Forts Total.
2. Helps.
3. Tech Donations.
4. RSS Gathered.
5. Building Minutes.
6. Power Change.

Each metric shows:

- period total;
- average per valid reporting day;
- previous equal-period change;
- current-kingdom rank;
- top-percentile position;
- valid cohort count;
- source coverage.

Example:

```text
FORTS TOTAL
182 | 2.1/reporting day | +18% vs previous period
#24 of 318 current governors | Top 8%
```

If coverage differs materially, compare valid reporting-day rates and label it as a rate comparison.

## 16. Rank Rules

Metric rank:

- competition ranking;
- ties share rank and gaps remain;
- descending for activity contribution;
- denominator is current governors with valid values;
- valid zero remains included;
- missing/untracked excluded;
- stale target receives no rank;
- show `#x of N`.

Activity Index component percentile:

1. rank higher value as better;
2. use average rank for ties;
3. convert:

```text
Component Score =
    (N - Average Rank)
    ------------------
    (N - 1)
    * 100
```

- best = 100;
- worst = 0;
- all tied = 50;
- N < 2 -> unavailable.

## 17. Activity Index v1

Formula:

```text
Forts percentile          * 0.30
Helps percentile          * 0.22
Tech Donations percentile * 0.18
RSS Gathered percentile   * 0.14
Building percentile       * 0.10
Power Change percentile   * 0.06
```

Display:

```text
Activity Index v1  74/100
Activity Rank      #38 of 284 fully covered governors
```

Requirements:

- all six components present;
- no renormalisation;
- visible component scores;
- formula version in payload and telemetry;
- no hidden clamping except the percentile range;
- no `Excellent/Poor/Inactive` bands;
- production replay before final weights are accepted.

Replay report:

- distribution by period;
- median/quartiles;
- fully covered count;
- unavailable count by cause;
- weight sensitivity;
- new-arrival impact;
- negative Power impact;
- top/bottom outliers;
- comparison stability.

Any weight change after replay requires explicit operator approval and a version decision.

## 18. New Arrivals And Low Tenure

If first observed after window start:

```text
NEW TO PERIOD
First observed 42 days into this 90-day window
```

Rules:

- show genuine totals and Presence;
- show valid ranks where comparable;
- do not extrapolate;
- Activity Index unavailable if required components are incomplete;
- suppress adverse prompts caused only by short tenure;
- suggest a shorter period only as a neutral option.

## 19. Source Reset Rules

Monotonic counters:

- RSS Gathered;
- Helps;
- Kill Points;
- kills;
- deads;
- healed;
- other audited cumulative fields.

Negative deltas:

- exclude from contribution totals;
- record a data warning;
- do not convert to zero silently;
- do not use in comparison/rank/index.

Power Change:

- signed negative is valid;
- include in total, comparison, rank, and component percentile.

Alliance Activity retains its week-boundary/reset contract.

Rally Daily is direct per-date activity, not a cumulative delta.

## 20. Rally Daily Completion Foundation

Add:

```text
dbo.RallyDailySnapshotHeader
```

Recommended columns:

```text
AsOfDate                date          primary key
CompletedAtUtc          datetime2(0)  not null
SourceRowCount          int           not null
DistinctGovernorCount   int           not null
Revision                int           not null
CompletionSource        nvarchar(24)  not null
ImportBatchId           bigint        null
```

CompletionSource:

```text
live_import
audit_backfill
inferred_backfill
```

A completed zero-row report is valid.

### Import correction

Replace current merge-only behaviour with transactional date replacement:

1. validate staging for `@AsOfDate`;
2. reject duplicate Governor IDs;
3. validate non-negative Rally values;
4. begin transaction with `XACT_ABORT ON`;
5. delete current rows for the date;
6. insert all staging rows;
7. rebuild dependent Rally export;
8. rebuild/snapshot dependent player-fort output;
9. upsert header as final success step;
10. commit.

Verify downstream procedures are safe in the transaction boundary.

Do not materialize zero rows for every governor. Infer zero in the review query only when the header
proves completion.

### Historical backfill

Priority:

1. durable successful import audit;
2. other authoritative completion record;
3. existing Rally date as explicitly inferred fallback.

Unprovable dates remain missing.

## 21. Alliance Activity Contract

Confirmed:

- every snapshot covers every alliance in the latest complete kingdom scan;
- every member is present;
- explicit zero Building/Tech values exist.

Therefore:

- explicit zero is genuine;
- missing expected row is partial/integrity failure;
- full current allied-governor rank is valid;
- unallied governor may have unavailable components/index;
- no `tracked alliances only` label is required.

## 22. Deterministic Leadership Prompts

Maximum two:

- one strength/stable point;
- one attention/question point.

Prompts must cite visible evidence.

Examples:

```text
Strong fort contribution: top 10% of the current kingdom over 90 days.

RSS gathering is in the bottom quartile. Review gathering routines or whether resource support is
needed.
```

```text
No Tech Donations were recorded with complete Alliance Activity coverage. Confirm the governor
understands kingdom donation expectations.
```

Suppress when:

- coverage partial;
- governor stale;
- new to period;
- previous period unavailable;
- source definition changed;
- alliance context makes comparison unreliable;
- cohort too small.

Do not claim motivation, intent, resource need, inactivity, or misconduct from the metrics alone.

## 23. Latest Completed KVK

Reuse the existing `kvk_state.py` completion/state resolver.

Do not create an end-date-only alternative.

Historical resolver:

1. load candidate KVK detail rows;
2. apply the existing pure state resolver to each;
3. require normal final reporting output;
4. choose highest ended KVK;
5. exclude started/active/unfinalized KVK.

Show:

- KVK number;
- `KVK_NAME`;
- KVK rank;
- T4+T5 kills;
- kill target percent;
- Kill Points;
- deads;
- dead target percent;
- healed;
- KP Loss;
- Tanking Score;
- Acclaim;
- individual completed-KVK best Acclaim;
- latest Acclaim as percent of best;
- DKP;
- DKP target percent;
- Pre-KVK points/rank where available;
- Honor points/rank where available;
- final data timestamp;
- source coverage/finalization state.

## 24. Canonical Combat Metrics

Create one pure Discord-free module, for example:

```text
kvk/combat_metrics.py
```

Functions:

```text
calculate_kp_loss(healed_troops)
calculate_tanking_score(kill_points, healed_troops, deads)
is_engaged_kvk_participant(kill_points, t4_t5_kills, deads, healed_troops)
```

Canonical formula:

```text
kp_loss = healed * 20
denominator = kp_loss + deads
score = kill_points / denominator * 100
```

Return unavailable for invalid/missing inputs or non-positive denominator.

Update every consumer:

- Account Summary retains its current correct result;
- `/kvk stats`;
- KVK stats card payload and renderer;
- `/kvk history` rows, Summary, Trends, CSV/export;
- history overall-rank SQL;
- `/kvk rankings`;
- Phase 8 leadership payload/card;
- Phase 9 kingdom payload/card;
- tests, docs, fallbacks, labels.

Specific changes:

- `Lowest Tanking Score` -> `Highest Tanking Score`;
- descending best/rank/trend direction;
- remove old lower-is-better semantics;
- remove current old-formula playstyle labels;
- show `Higher is better` until new bands are evidence-approved.

Python and SQL expressions require parity fixtures.

## 25. Heals And Engagement

Engaged participant:

```text
Kill Points > 0
AND (T4+T5 Kills > 0 OR Deads > 0 OR Healed > 0)
```

Healed ranking:

- engaged only;
- ascending;
- valid zero heals may rank best only when engagement is proven;
- do not label historical maximum heals as best efficiency.

Tanking Score ranking:

- engaged only;
- positive denominator;
- descending.

## 26. Last Three Completed KVKs

Show:

- valid rows `x of 3`;
- kill targets met;
- dead targets met;
- DKP targets met;
- exemptions;
- latest versus previous;
- latest versus previous-two average;
- rank direction;
- Kill Points direction;
- Tanking Score direction;
- Acclaim effort direction;
- missing rows as missing.

Example:

```text
Kill target: 2/2 eligible met | 1 exempt
Dead target: 3/3
DKP target: 2/3
```

Never convert missing target or missing row to failure/zero.

## 27. Player Record

### Active linked governors

Resolve active registry owner from selected Governor ID, then return active governors under that
owner.

Show:

- current governor name;
- Governor ID.

Exclude:

- Discord user ID;
- Discord name;
- account slot/type;
- reminders/preferences;
- inventory visibility;
- language/timezone;
- exports;
- removed/superseded historical registrations.

If unlinked:

```text
No active linked-governor group is recorded.
```

Linked governors may be opened in the same authorized leadership session.

### Alias history

Extend `GovernorNameHistory`:

```text
LastSeen      datetime2(0) not null
SeenScanCount int          not null
```

Backfill from `KingdomScanData4` using normalized name:

- `MIN(ScanDate)` FirstSeen;
- `MAX(ScanDate)` LastSeen;
- `COUNT(DISTINCT SCANORDER)` SeenScanCount.

Ongoing idempotent post-scan upsert:

- insert new alias;
- retain earliest FirstSeen;
- advance LastSeen;
- advance/recompute observation count;
- no case-only/whitespace-only duplicate.

Recommended index:

```text
(GovernorID, LastSeen DESC)
INCLUDE (GovernorName, FirstSeen, SeenScanCount)
```

UI:

```text
Name | First observed | Last observed
```

### Alliance history

Derive consecutive episodes from authoritative complete scans:

- latest final row per Governor ID/SCANORDER;
- trim/casefold alliance;
- collapse consecutive identical values;
- preserve leave-and-return;
- blank while present -> `Unallied`;
- missing scan is not `Unallied`;
- show observation count;
- current episode first;
- initial latest five with paging if required.

## 28. Definitions/Method Panel

Private ephemeral text panel from payload/constants; no second data query.

Explain:

- selected and previous dates;
- Scan Presence formula;
- source coverage;
- Activity Index v1 weights and percentile method;
- rank cohort;
- reset exclusions;
- Tanking Score;
- engaged participant;
- KVK completion source;
- target/exemption handling;
- linked-governor privacy boundary.

## 29. SQL Design

Prefer dedicated bounded stored procedures and compact result sets rather than sending all-kingdom
daily rows to Python.

Potential contract family:

```text
dbo.usp_GetLeadershipPlayerReview
dbo.usp_GetLeadershipPlayerIdentityHistory
dbo.usp_PurgeLeadershipPlayerReviewAudit
```

Exact names require SQL architecture approval.

Player review procedure inputs:

```text
@GovernorID
@PeriodDays in (30,90,180,360)
@NowUtc optional for deterministic tests
```

Return compact typed sets for:

- header/current identity/location;
- current and previous activity values/coverage;
- metric ranks/percentiles/cohort counts;
- Presence;
- latest completed KVK;
- last three completed KVKs;
- linked governors;
- aliases;
- alliance episodes;
- source history bounds/gaps;
- formula/version metadata where useful.

Requirements:

- static parameterized T-SQL;
- bounded 720-day history;
- set-based current cohort;
- no dynamic SQL;
- no direct SQL in commands/views;
- no over-read of Discord relationship fields;
- additive migrations;
- indexes only after actual plans/logical reads/timings/concurrency prove need.

## 30. Dedicated Leadership Audit

Recommended table:

```text
dbo.LeadershipPlayerReviewAudit
```

Fields:

```text
AuditID
ExecutedAtUtc
ActorDiscordID
TargetGovernorID nullable until resolution
GuildID
ChannelID
AuthorizationBasis
AuthorizationRoleID nullable
Action
Outcome
ErrorCode nullable
RequestCorrelationID
ExpiresAtUtc
```

Actions:

```text
open
ambiguity_select
page_change
period_change
linked_governor_change
change_player
definitions
refresh
```

Do not store:

- typed name query;
- governor name;
- alliance;
- Discord display name;
- account slots;
- metrics;
- location;
- shield;
- card/attachment;
- free-text SQL/Python errors.

Purge identified rows at 90 days.

De-identified longer aggregates may retain only date/action/outcome/counts.

General `BotCommandUsage` may continue recording qualified usage, but is not the detailed inspect
audit source.

## 31. Architecture Direction

Suggested package:

```text
leadership_player/
    models.py
    service.py
    dal.py
    renderer.py
    views.py
    insights.py
```

Or an operator-approved equivalent under an existing stats/leadership package.

Principles:

- typed immutable payload;
- commands/views thin;
- SQL in DAL only;
- pure calculations in domain helpers;
- KVK history/combat services reused, not copied;
- self-view payload and selector not reused where privacy semantics differ;
- renderer has no SQL/Discord/network I/O;
- fallback from same payload;
- explicit correlation ID and audit service;
- bounded caches keyed by authorized target/period/formula version;
- permission checked before cache access and again before sensitive transitions.

## 32. Performance Targets

Provisional audit targets:

- initial private result p95 <= 6 seconds;
- page-only transition p95 <= 3 seconds;
- period/target transition p95 <= 5 seconds;
- render <= 3 seconds;
- bounded SQL timeout;
- no N+1 reads;
- one set-based activity/rank load;
- one bounded KVK history load;
- one identity-history load;
- safe concurrent-session limits;
- latest valid transition wins.

Measure:

- 30/90/180/360;
- current/stale/unlinked;
- long alias/alliance history;
- full current kingdom cohort;
- 720-day comparison;
- concurrent leadership requests;
- cold/warm plans;
- logical reads and memory grants.

## 33. Interaction And Lifecycle

- private only;
- no public fallback;
- author and permission gate before mutation;
- stale work cannot replace newer state;
- preserve page/period across valid target changes where practical;
- handled failures restore usable controls;
- timeout preserves report and disables controls;
- late/foreign/forged components rejected;
- files/streams closed on success/failure/cancel/timeout/stale suppression;
- no raw exceptions;
- no value leakage in logs.

Proposed expiry copy:

```text
Leadership review controls expired. Run /stats player to refresh.
```

## 34. `/player_profile` Retirement

Before deletion:

- map registration and command inventory;
- map profile lookup service callers;
- map profile cache callers;
- map player profile renderer callers;
- map location view callers;
- map tests/docs/telemetry;
- prove which modules are command-specific versus shared.

Remove:

- top-level registration;
- command callback;
- command-specific public posting flow;
- command-specific renderer/view/buttons only when zero-caller;
- command-specific tests/docs;
- approved top-level baseline entry;
- smoke references.

Retain shared profile/location helpers still used elsewhere.

No redirect.

## 35. Command Governance

Current:

```text
37 top-level
100 grouped
8 /me
1 /stats
2 /inventory
```

After Phase 8:

```text
36 top-level
100 grouped
8 /me
1 /stats: player
2 /inventory
```

Update:

- `scripts/validate_command_registration.py`;
- command inventory tests;
- canonical command reference;
- programme pack;
- briefing;
- task-pack index;
- deprecated/retired command docs;
- smoke checklist.

Resync after deployment.

## 36. Testing

Required categories:

### Permission/security

- admin Leadership channel;
- admin Notify channel;
- admin denied elsewhere;
- leadership role ID Leadership channel/thread;
- leadership denied Notify;
- matching role name without ID denied;
- Ark Setup denied;
- DM denied;
- role revoked mid-session;
- foreign user;
- forged target/component;
- audit minimization.

### Lookup

- exact ID;
- invalid ID;
- exact normalized name;
- case/space normalization;
- one fuzzy result;
- multiple fuzzy results;
- duplicate labels;
- no result;
- both options supplied;
- bounded malicious/Unicode input;
- no multi-match aggregation.

### Activity/data

- each period;
- exact dates;
- previous dates;
- 720-day unavailable comparison;
- Presence scans and scanned days;
- current/stale/partial/no data;
- Rally explicit zero versus missing;
- Alliance explicit zero;
- unallied;
- resets;
- negative Power;
- ranks/ties/percentiles;
- Activity Index missing component;
- new arrival;
- prompts suppressed/produced correctly.

### KVK

- shared completion resolver;
- current KVK excluded;
- latest completed selected;
- missing final output;
- all metrics;
- target met/exempt/missing;
- last-three missing rows;
- Acclaim personal best;
- engaged participant;
- lower Heals;
- canonical Tanking formula;
- higher-is-better ranks/trends.

### Identity history

- linked/unlinked;
- active governors only;
- no Discord metadata;
- LastSeen backfill/upsert;
- case/space aliases;
- one-scan alias;
- alliance episodes;
- leave/return;
- blank alliance versus missing scan;
- paging.

### Rendering/lifecycle

- all pages;
- long/Unicode;
- maximum values;
- no-data;
- fallback parity;
- dimensions/opacity;
- mobile/desktop;
- attachment cleanup;
- timeout;
- latest transition wins.

### Compatibility

- `/kvk stats`;
- `/kvk history` cards/summary/trends/CSV;
- `/kvk rankings`;
- Account Summary;
- current KVK reporting;
- `/stats player` replacement;
- `/player_profile` absent;
- command counts.

## 37. Formula Parity

Create shared fixtures covering:

- missing inputs;
- zero denominator;
- deads-only;
- heals-only;
- mixed denominator;
- large values;
- decimal precision;
- aggregate kingdom values.

Prove identical outputs across:

- Python helper;
- SQL expression;
- Account Summary;
- KVK stats;
- KVK history;
- history CSV;
- KVK rankings;
- Phase 8;
- Phase 9.

## 38. Security Review

A dedicated final Codex Security Changes review with Deep off is mandatory.

Focus:

- arbitrary Governor ID access;
- stable role-ID authorization;
- channel/thread scoping;
- mid-session permission revocation;
- fuzzy lookup input and ambiguity controls;
- linked-governor relationship metadata;
- location/shield confidentiality;
- audit/telemetry minimization and retention;
- SQL parameterization and bounded reads;
- 720-day resource use;
- cache authorization;
- attachment/fallback privacy;
- command retirement;
- global metric correction consistency.

SQL diff receives its own Changes review.

Do not use a standard/deep codebase scan unless explicitly requested.

## 39. Deployment Order

1. Complete audit/design, implementation, correction validation, and separate bot/SQL Changes reviews.
2. Deploy SQL migrations `20260719_001` through `20260719_007` in order.
3. For every historically finalized KVK required by the latest-three experience, execute
   `dbo.usp_BackfillKvkFinalReportCompletion` with an explicit audited KVK number, final scan order,
   final-data UTC timestamp, and `AUDIT_BACKFILL`; use `INFERRED_BACKFILL` only when the approved
   evidence ladder reaches the explicit-inference step. The Python `kvk_state.py` resolver remains
   the ended/finalized authority; never infer completion from an end date alone.
4. Execute the initial `dbo.usp_PurgeLeadershipPlayerReviewAudit`, then verify the write-bound purge
   invoked by every `dbo.usp_RecordLeadershipPlayerReviewAudit` call preserves only 90 days of
   identified rows and retains only de-identified daily aggregates beyond that window.
5. Before bot rollout, verify the latest three ended/finalized KVKs have valid
   `dbo.KVKFinalReportHeader` rows and that finalized output row/target/exemption semantics are intact.
6. Verify deployed execute grants, procedures, static parameterization, history bounds, source
   completion headers, representative plans/logical reads/timings, lock behavior, and concurrent
   name-history/audit writes. Add indexes only when that production evidence justifies them.
7. Deploy coordinated bot patch:
   - new `/stats player`;
   - canonical Tanking corrections;
   - `/player_profile` removal.
8. Restart.
9. Resync to `36 top-level / 100 grouped / 8 me / 1 stats / 2 inventory` and prove
   `/player_profile` is absent with no redirect or alias.
10. Validate command cache and versions.
11. Complete operator Discord smoke.
12. Observe and promote the exact accepted patch.

## 40. Rollback

Rollback order:

1. restore prior bot patch and `/player_profile`;
2. restore previous KVK Tanking behaviour only as part of the complete bot rollback;
3. deploy/restart;
4. resync;
5. smoke `/stats player`, `/player_profile`, KVK stats/history/rankings, Account Summary;
6. leave additive SQL tables/columns/data in place unless a separately validated rollback is required;
7. rollback dependent SQL procedure/migration only after bot rollback.

Backfilled alias/header/audit data is not destructively removed by default.

## 41. Documentation

Update:

- active programme pack;
- task-pack README;
- canonical command reference;
- deferred optimisations;
- player/operator briefing;
- KVK command docs for Tanking semantics;
- formula definitions;
- permission matrix;
- command-count validator;
- smoke guide;
- task pack/starter archive after completion.

## 42. Workflow And Gates

1. Audit/scope only, then stop.
2. SQL source/history/permission/command/caller/formula audit, then stop.
3. Present architecture, result-set contracts, schema migrations, visual wireframes, permissions,
   file manifest, security targets, performance plan, and exact command changes, then stop.
4. Present implementation/test/deploy/resync/smoke/rollback plan, then stop.
5. Implement SQL only after SQL approval.
6. Implement bot only after bot-plan approval.
7. Run focused/full/visual/architecture/deferred/registration/import/pre-commit/log-noise validation.
8. Run separate SQL and bot Changes reviews with Deep off.
9. Complete PR review.
10. Deploy SQL then bot, resync, smoke, observe, and promote.

## 43. Acceptance Criteria

- [x] `/stats player` is the only leadership player-review command.
- [x] `/player_profile` is removed with no redirect.
- [x] Dedicated role-ID/channel gate matches the locked matrix.
- [x] Output is always private.
- [x] Lookup never aggregates ambiguous matches.
- [x] Selected governor only is the performance scope.
- [x] 30/90/180/360 periods and exact preceding windows work.
- [x] 360-day current result survives unavailable preceding history.
- [x] History-depth matrix is recorded.
- [x] CURRENT/STALE/PARTIAL/NO DATA and 48-hour rule are correct.
- [x] Scan Presence and source coverage are separate.
- [x] Rally completion header and date-replacement semantics are delivered.
- [x] Alliance Activity explicit-zero semantics are preserved.
- [x] Activity metrics, ranks, percentiles, Index v1, new-arrival rules, reset rules, and prompts are
      transparent and tested.
- [x] Latest completed KVK reuses the existing resolver.
- [x] Canonical Tanking Score is identical everywhere and higher is better.
- [x] Old KVK playstyle labels are removed/deferred.
- [x] Heals rank uses engaged participants and lower-is-better.
- [x] Last-three target/exemption/missing rules are correct.
- [x] Linked governors expose names/IDs only.
- [x] Alias LastSeen/observation and alliance episodes work.
- [x] Location/shield are private and independently timestamped.
- [x] Dedicated audit retains identity 90 days and stores no unnecessary values.
- [x] No Discord private settings leak.
- [x] Performance evidence is explicitly carried into Phase 8.1 rather than hidden or treated as complete.
- [x] Security reviews close with no unresolved finding.
- [x] Command surface is `36 / 100 / 8 / 1 / 2` as documented.
- [x] Resync and operator smoke pass.

## 44. Closeout

Phase 8 completed on 2026-07-21 after SQL-first migration deployment, command resync, bot restart,
data-source and historic-completion correction, global combat-metric parity validation, private
interaction smoke, all-page/all-period data smoke, crash correction and operator acceptance.

Mirror PR #230 and production PR #537 carry the accepted bot change. The deployed SQL migration
series and its merged follow-up PR #53 carry the accepted source-completion, leadership-contract,
history and audit corrections. The accepted command surface is:

```text
36 top-level / 100 grouped / 8 /me / 1 /stats / 2 /inventory
```

The remaining visual hierarchy, Last Active signal, record formatting and measured load/query
performance work is not a Phase 8 defect backlog. It is deliberately scoped in the separately
approval-gated Phase 8.1 task pack.
