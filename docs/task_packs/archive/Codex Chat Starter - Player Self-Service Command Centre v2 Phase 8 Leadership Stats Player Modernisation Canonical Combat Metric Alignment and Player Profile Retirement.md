# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 8 Leadership `/stats player` Modernisation, Canonical Combat Metric Alignment and `/player_profile` Retirement

Status: archived closeout starter. Phase 8 was production smoke tested and operator accepted on
2026-07-21. Do not use this starter for new work; use the active Phase 8.1 starter for the approved
visual hierarchy, Presence/Last Active and performance refinement.

## Copy/Paste Starter

```text
Codex, begin Player Self-Service Command Centre v2 Phase 8: Leadership /stats player Modernisation,
Canonical Combat Metric Alignment, and /player_profile Retirement.

Approval state:
- Phase 7 /me closeout is complete, smoke tested, operator accepted, and archived on 2026-07-19
- /stats player is the one approved leadership player-review command
- do not create /me inspect
- remove /player_profile in the same accepted release
- no /player_profile redirect, alias, or second leadership location
- selected Governor ID is the performance scope
- linked governors are context/navigation only
- default period is 90 days
- supported periods are 30/90/180/360 days
- private output only
- one-pass execution is not approved
- first response must be audit/scope only; do not code

Current command baseline before Phase 8:
- 37 top-level
- 100 grouped
- 8 /me
- 1 /stats: player
- 2 /inventory

Approved target after Phase 8:
- 36 top-level
- 100 grouped
- 8 /me
- 1 /stats: player
- 2 /inventory
- /player_profile absent

Dedicated permission matrix:
Leadership role IDs:
- Leadership channel
- Leadership child threads

Admin:
- Leadership channel and child threads
- Notify channel and child threads

Never:
- Ark Setup solely through a generic allowed-channel set
- role-name-only authority
- DMs
- any other channel

Recheck permission/channel on command entry and every interaction.

Command shape:
- /stats player governor_id:<optional> name:<optional>
- reject neither and both
- ID exact only
- name Unicode trim/collapse/casefold
- exact normalized match first
- fuzzy match second
- one match opens
- multiple matches use a private author/permission-gated selector
- never aggregate ambiguous matches
- selector may show name, Governor ID, current alliance, last scan
- never show Discord identity/account slot

Pages:
1. Overview
2. Kingdom Activity
3. KVK Performance
4. Player Record
Controls:
- 30/90/180/360 selector
- Change Player
- Definitions/Method
- no public share/export

Header:
- governor name/ID
- current alliance
- current Power
- City Hall
- last governor scan
- selected period and exact dates
- valid source observations
- CURRENT/STALE/PARTIAL/NO DATA
- latest X:Y
- separate location-updated UTC
- ShieldEndsAtUtc when non-null with Reported active/expired wording
- no Discord avatar; use neutral KD98/governor identity

Freshness:
- current scan <=48 hours
- stale if source >48h or governor absent from latest complete scan
- partial if current governor but required source incomplete
- no data if no governor scan in selected period
- stale wins as primary badge over partial
- location freshness is separate

Scan Presence:
- every KingdomScanData4.SCANORDER is authoritative complete
- distinct scans containing Governor ID / all scans in selected window
- also show scanned-day presence
- keep Presence outside Activity Index

Coverage:
- show Stats scans, Alliance Activity snapshots, Rally completed report dates separately
- do not merge Presence and coverage

Exact periods:
- current start = anchor - days + 1
- previous end = current start - 1
- previous start = previous end - days + 1
- 30 -> 60 read days
- 90 -> 180
- 180 -> 360
- 360 -> 720
- keep current 360 when previous unavailable
- mark comparison unavailable
- never shorten silently

History-depth audit:
- earliest/latest/gaps for Kingdom scans, Alliance Activity, Rally completion, aliases, locations,
  final KVK history
- distinguish scans, dates, snapshots, report completion, resets, inferred/backfilled history

Activity metrics in order:
1. Forts Total
2. Helps
3. Tech Donations
4. RSS Gathered
5. Building Minutes
6. Power Change

Each shows:
- total
- average per valid reporting day
- previous equal-period change
- current-kingdom #x of N
- top percentile
- source coverage

Rank cohort:
- governors in latest complete kingdom scan
- stale target has no rank
- competition rank for displayed metrics
- valid zeros included
- missing excluded

Activity Index v1 weights:
- Forts 30%
- Helps 22%
- Tech 18%
- RSS 14%
- Building 10%
- Power 6%
- component scores use average-rank percentile:
  (N - Average Rank) / (N - 1) * 100
- all tied = 50
- N < 2 unavailable
- missing component -> whole index unavailable
- do not renormalise
- show all components and Activity Rank
- no Excellent/Poor/Inactive bands
- replay production distributions before final weight acceptance

Source rules:
- exclude negative monotonic-counter resets and warn
- negative Power Change remains signed/valid
- Alliance Activity covers every current alliance/member with explicit zero Building/Tech
- missing expected Alliance row is partial, not zero
- unallied may have unavailable Building/Tech/index
- Rally Daily contains only active governors
- add dbo.RallyDailySnapshotHeader
- completed report + missing governor row = zero
- no completed report = missing
- change Rally import from merge-only to transactional date replacement
- header written only after dependent rebuild/snapshot succeeds
- historical completion backfill: audit proof first, then other authority, then explicitly inferred date
- do not materialize zero rows for every governor

New arrivals:
- show NEW TO PERIOD and first observed offset
- do not extrapolate
- suppress adverse prompts caused only by short tenure

Leadership prompts:
- maximum two
- one strength/stable, one attention/question
- cite visible rank/trend/coverage evidence
- suppress for stale, partial, new arrival, non-comparable period, small cohort
- do not infer motive, resource need, misconduct, or inactivity

KVK completion:
- reuse existing kvk_state.py resolver and final reporting output
- do not create end-date-only logic
- latest ended/finalized KVK only
- current/started/unfinalized excluded

Latest KVK fields:
- KVK number and KVK_NAME
- KVK rank
- T4+T5 kills and target %
- Kill Points
- deads and target %
- healed
- KP Loss
- Tanking Score
- Acclaim, personal completed-KVK best, % of best
- DKP and target %
- Pre-KVK points/rank
- Honor points/rank
- final data time/state

Last three:
- valid x/3
- kill/dead/DKP targets met
- exemptions separate
- >=100% met
- missing target is not failure
- missing row is not zero
- latest vs previous and previous-two average
- rank/KP/Tanking/Acclaim-effort trends

Canonical Tanking Score everywhere:
- KP Loss = Healed * 20
- Tanking Score = Kill Points / (KP Loss + Deads) * 100
- higher is better
- invalid/non-positive denominator = unavailable
- create one pure kvk/combat_metrics.py or approved equivalent
- update Account Summary parity, /kvk stats, /kvk history cards/summary/trends/CSV/ranks,
/kvk rankings, Phase 8, and future Phase 9
- Lowest Tanking Score -> Highest Tanking Score
- sort/rank/trend descending
- remove old playstyle labels until production replay supports new bands
- Python/SQL parity fixtures are mandatory

Engaged participant for lower-heals and Tanking ranks:
- Kill Points > 0
- and kills > 0 or deads > 0 or healed > 0
- Healed rank ascending among engaged
- Tanking rank descending among engaged with valid denominator

Player Record:
- active linked governor names/IDs only
- no Discord ID/name/account slot/type
- no reminders/timezone/language/inventory/export metadata
- unlinked message is honest
- linked governors can open in same session
- aliases grouped by Governor ID
- add GovernorNameHistory.LastSeen and SeenScanCount
- backfill MIN/MAX ScanDate and COUNT DISTINCT SCANORDER
- idempotent post-scan upsert
- first/last observed labels
- alliance episodes from consecutive complete scans
- blank while present = Unallied
- missing scan is not Unallied
- preserve leave-and-return
- page if needed

Audit:
- dedicated LeadershipPlayerReviewAudit
- actor ID, target ID, guild/channel, authorization basis/role ID, action/outcome/error code,
  correlation ID, expiry
- actions: open, ambiguity_select, page_change, period_change, linked_governor_change, change_player,
  definitions, refresh
- identified retention 90 days
- longer aggregates de-identified
- never store typed lookup, names, metrics, alliance, location, shield, cards, or raw SQL/Python errors

SQL:
- dedicated bounded leadership review contract
- up to 720 days
- compact result sets, set-based current-cohort ranks
- GovernorNameHistory migration/backfill/upsert
- RallyDailySnapshotHeader and corrected importer
- leadership audit and purge
- static parameterized SQL
- no SQL in commands/views
- indexes only after plans/reads/timings/concurrency

Architecture:
- thin command/view
- typed immutable leadership payload
- leadership-specific renderer
- reuse KVK services/calculations, do not copy
- do not reuse self-view picker/All Linked
- same-payload fallback
- latest transition wins
- bounded cache after authorization
- neutral leadership identity, no Discord avatar

Locked Phase 7 visual/navigation handoff:
- start from the accepted 1702x924 core summary visual family and shared core/visual_contract.py
  tokens/primitives; do not reuse legacy leadership visuals or create a universal renderer
- retain neutral KD98/governor identity with no Discord avatar and do not force /me page geometry
- row 0 contains Overview, Kingdom Activity, KVK Performance, Player Record; period, Change Player,
  Definitions/Method, and any approved refresh control begin below it
- state-pill text is centred middle, not baseline-bottom; keep the pill top right with aligned
  page/period/freshness support beneath it
- blue is neutral/selection/navigation including UTC; green current/success; amber
  stale/partial/review; red unavailable/failure/no data; muted disabled/expired
- keep source freshness and Generated separate; preserve genuine zero and the accepted — / Not
  recorded / NO DATA / UNAVAILABLE, K/M/B, signed delta, percentage, day/minute, RSS, donation,
  KP Loss, and Tanking Score language
- Change Player/linked-governor controls use exact IDs or opaque tokens, are duplicate-name safe,
  page where needed, disable the current choice in blue, preserve page/period, and revalidate
  permission/target before every read; no All Linked or Discord account metadata
- same-payload fallback, latest-transition-wins, attachment replacement, preserve-and-disable
  timeout, and file/stream cleanup are mandatory

/player_profile retirement:
- prove every caller
- remove top-level registration/callback/public posting flow
- remove command-specific renderer/view/tests only when zero-caller
- retain shared lookup/location/cache helpers still used
- update approved command baseline
- no redirect

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- engineering/execution/testing/skills/deferred references
- active GovernorOS programme pack
- matching Phase 8 task pack
- archived accepted Phase 7 task pack and closeout record
- archived Phase 6/5C/KVK history/KVK rankings packs
- briefing, canonical reference, deferred optimisations
- authoritative SQL repo C:\K98-bot-SQL-Server

Security:
- separate SQL and bot Changes scans, Deep off
- focus on arbitrary ID access, role/channel revalidation, lookup input, relationship metadata,
  location/shield, audit minimization/retention, SQL bounds, cache authorization, attachment privacy,
  command retirement, and global metric parity
- do not start a standard/deep codebase scan unless requested

Mandatory workflow:
1. Audit/scope only, stop.
2. Present command/caller/permission/source/history/formula audit and security routing, stop.
3. Present SQL schema/result sets, architecture, visual wireframes, file manifest, performance plan,
   tests, deployment/resync/smoke/rollback, stop.
4. Implement SQL after approval.
5. Implement bot after approval.
6. Validate focused/full/visual/architecture/deferred/registration/import/pre-commit/log-noise.
7. Run SQL and bot Changes reviews with Deep off.
8. PR review.
9. Deploy SQL then bot, restart, resync, smoke, observe, promote.

First response: audit only. Do not code.

Audit report must include:
A. exact current /stats player behaviour and ambiguity aggregation defect
B. exact /player_profile registration, posting, modules, tests, and caller deletion map
C. exact dedicated permission implementation proposal versus generic decorators
D. all data sources, earliest/latest/gaps, and 720-day feasibility
E. Rally completion/import audit and migration option
F. Alliance explicit-zero proof
G. Activity/rank/index SQL and percentile proposal
H. new-arrival/reset/comparison rules
I. existing KVK completion resolver reuse
J. every current Tanking/Healed consumer and exact global correction manifest
K. KVK final-row/target/exemption semantics
L. linked-governor/alias/alliance/location/shield privacy contract
M. audit schema/retention
N. renderer/pages/controls/fallback/lifecycle wireframe
O. performance/plan/concurrency budget
P. exact command count and resync plan
Q. tests/security/deploy/rollback
R. explicit stop for operator approval
```
