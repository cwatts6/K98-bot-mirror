# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 8.1 Leadership Player Review Visual Hierarchy, Presence and Performance

Status: active initiation starter. Phase 8 was smoke tested, operator accepted and closed on
2026-07-21. Use with the matching Phase 8.1 task pack. One-pass execution is not approved.

## Copy/Paste Starter

```text
Codex, begin Player Self-Service Command Centre v2 Phase 8.1: Leadership Player Review Visual
Hierarchy, Presence and Performance.

Approval state:
- Phase 8 /stats player is complete, production smoke tested and operator accepted on 2026-07-21
- /stats player remains the only leadership player-review command
- /player_profile remains retired with no redirect
- no command registration or permission-model change is approved
- output remains private
- one-pass execution is not approved
- first response must be audit/scope only; do not code

Command baseline and target:
- 36 top-level
- 100 grouped
- 8 /me
- 1 /stats: player
- 2 /inventory
- no resync expected

Preserve Phase 8:
- dedicated stable-role-ID/channel permission matrix and per-interaction revalidation
- selected Governor ID performance scope; linked governors context/navigation only
- 30/90/180/360 periods, 90 default, up to 720 bounded read days
- CURRENT/STALE/PARTIAL/NO DATA and separate source/location freshness
- Scan Presence separate from source coverage and Activity Index
- all six Activity metrics, rank/percentile/coverage and reset semantics
- Activity Index v1 weights/formula
- latest three finalized KVKs and canonical combat metrics
- Player Record privacy and history semantics
- same-payload fallback, latest-transition-wins, attachment replacement, timeout disable and cleanup
- neutral KD98/governor identity; no Discord avatar or account metadata

Overview:
- remove Forts, Helps and Tech Donations cards because Kingdom Activity owns them
- make Activity Index and Presence primary adjacent elements
- Presence shows exact scans and percentage, e.g. 185/191 and 97%
- add Last Active Date
- make latest X:Y, location-updated UTC and shield status materially larger
- keep primary freshness state separate from ACTIVE/INACTIVE

Last Active Date:
- latest authoritative complete KingdomScanData4 ScanDate within bounded 720-day history where one
  eligible value positively changed relative to the immediately prior complete scan in which that
  Governor ID was present
- eligible: Power, Healed, RSS Gathered, RSS Assisted, Helps, Tech Donations, Building Minutes,
  Fort rallies completed
- compare values at complete scan cutoffs only; missing governor/source observations are not zero
- negative monotonic resets do not count
- completed Rally missing row is zero; no completed report is missing; positive interval activity
  is attributed to the later complete kingdom ScanDate
- use UTC calendar dates
- more than 30 days before UTC TODAY = INACTIVE; exactly 30 days remains ACTIVE
- no qualifying observed change = Not recorded, not inferred inactive
- ACTIVE/INACTIVE never replaces CURRENT/STALE/PARTIAL/NO DATA

Kingdom Activity:
- keep header and all existing data semantics
- remove repeated latest X:Y/location/shield strip
- enlarge six metric boxes and key text

KVK Performance:
- remove repeated latest X:Y/location/shield strip
- show latest three eligible finalized KVKs as three side-by-side cards
- retain KVK number/name/rank, T4+T5 and target %, KP, Deads and target %, Healed/rank, KP Loss,
  Tanking/rank, Acclaim/best context, DKP and %, Pre-KVK and Honor
- remove visible final date/time/state and MET/NOT MET words
- retain numeric percentages, exemptions and honest missing semantics
- never invent/repeat a KVK when fewer than three are valid

Player Record:
- rename Alliance Episodes to Alliances
- show one Governor ID heading, then readable Alias rows with first/last/scans
- use the same grouped structure for Alliances
- preserve every bounded result row; page when required, no silent five-row limit
- preserve leave/return and missing-scan-is-not-Unallied semantics

Footer:
- label source time Data refreshed consistently with accepted /me pages
- keep Data refreshed left aligned and Generated right aligned

Performance:
- measure before changing architecture
- capture cold/warm first load and 30/90/180/360 transitions
- attribute authorization/lookup, SQL, mapping, KVK, payload, render, attachment and cache time
- collect actual SQL plans, IO/time, rows and result sizes for representative governors
- assess page-specific loading, cache granularity, query refinement, pre-aggregation and supporting
  objects as candidates only
- no speculative table/index; any SQL change needs separate design approval, SQL PR, validation,
  Changes scan and SQL-first deployment
- no live load test without explicit approval

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md and required engineering/execution/testing/skills/deferred references
- active programme pack
- this Phase 8.1 pack
- archived Phase 8 and Phase 7 packs/closeout
- Phase 9 pack only to prevent overlap
- briefing, canonical command reference and deferred optimisations
- relevant SECURITY.md files
- authoritative SQL repo C:\K98-bot-SQL-Server

Skills:
- k98-architecture-scope
- k98-sql-validation for SQL-facing work
- k98-discord-command-feature for implementation/specialist review
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-security-review-routing
- codex-security:security-diff-scan for bot Changes and separately for SQL only if SQL changes
- k98-pr-review
- k98-promotion-check before promotion

Security:
- bot Changes scan required, Deep off
- SQL Changes scan required only if SQL changed, Deep off
- focus on arbitrary ID access, revalidation, cache authorization, location/shield privacy,
  pagination tokens, interaction races, SQL bounds and attachment privacy
- do not start a standard/deep codebase scan unless explicitly requested

Mandatory workflow:
1. Audit/scope only, stop.
2. Present Last Active source semantics, current timing/query/render audit, exact wireframes, SQL
   impact decision, file manifest, performance plan, tests, security routing, deploy/smoke/rollback,
   stop.
3. If SQL is recommended, present plans/reads evidence and exact schema/result/refresh/rollback
   contract, stop for separate approval.
4. Implement only approved bot and optional SQL scope.
5. Validate focused/full/visual/performance/architecture/deferred/registration/import/pre-commit/
   log-noise as applicable.
6. Run bot Changes review and conditional SQL Changes review with Deep off.
7. PR review, deploy SQL first only if required, deploy bot, restart, smoke, observe, promote.

First response: audit only. Do not code.

Audit report must include:
A. exact current payload/query/render/page duplication
B. Presence and each Last Active source and ordering
C. missing/reset/new-arrival/completion semantics
D. exact >30-day UTC threshold
E. Alias/Alliance limits and pagination path
F. latest-three finalized-KVK selection and retained/removed fields
G. cold/warm timing by 30/90/180/360 period and stage
H. SQL actual plans, reads, time, rows and result sizes
I. cache/inflight/transition behavior
J. permission/privacy revalidation
K. visual wireframes and long/no-data states
L. exact bot and optional SQL manifest
M. tests and performance acceptance budget proposal
N. security/deploy/smoke/rollback
O. explicit stop for operator approval
```
