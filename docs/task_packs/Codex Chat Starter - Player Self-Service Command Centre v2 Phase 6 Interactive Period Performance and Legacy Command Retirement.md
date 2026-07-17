# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 6 Interactive Period Performance and `/my_stats` Retirement

Status: active Phase 6 implementation starter. Use with the matching active task pack. Phase 5G is
complete and archived. The product, command, visual, metric, period, privacy, All Linked, and legacy-
retirement decisions below are approved; one-pass execution is not approved.

## Copy/Paste Starter

```text
Codex, begin Player Self-Service Command Centre v2 Phase 6: Interactive Period Performance and
/my_stats Retirement.

Approval state:
- GovernorOS v2 Phase 5 is complete and operator accepted through Phase 5G
- mirror PR #227 and production PR #534 contain the accepted Phase 5G Account Data Export Consolidation
- the post-Phase-5G command baseline is 38 top-level, 99 grouped, 7 /me, and 2 /inventory
- Account Summary is the only central personal-data download home:
  /me accounts -> Account Summary -> Download data
- do not reopen /me exports, /my_stats_export, workbook, CSV, Google Sheets, Inventory export, or
  Account Summary ownership
- Phase 6 canonical command is /me stats
- add /me stats under the existing /me group
- add a Stats/Period Performance action from the selected-governor Dashboard
- remove top-level /my_stats in the same Phase 6 deployment
- do not retain /my_stats as a redirect, alias, compatibility route, or observation route
- /me stats is always private/ephemeral and is usable from any guild channel or thread
- do not apply the current KVK player-stats channel gate to /me stats
- preserve /stats player registration, permission, visibility, and proven legacy dependencies for the
  later /stats player versus /me inspect decision
- runtime implementation is approved subject to audit, architecture, plan, validation, final Changes
  review, operator smoke, and promotion gates
- one-pass execution is not approved

Approved command target:
- top-level commands: 38 -> 37
- grouped subcommands: 99 -> 100
- /me grouped subcommands: 7 -> 8
- /inventory grouped subcommands: remains 2

Target /me group after Phase 6:
/me dashboard
/me accounts
/me reminders
/me preferences
/me resources
/me speedups
/me materials
/me stats

Removed in Phase 6:
/my_stats

Retained outside Phase 6:
/stats player
/player_profile
/mykvkcrystaltech
/kvk history
/inventory import
/inventory audit
selected-governor RSS/Speedups/Materials report-page exports
Account Summary Download data and all Phase 5G output contracts

Approved visual contract:
- runtime backdrop: assets/me/cards/me_stats.png
- production output: private standalone 1702x924 PNG
- stable filename direction: me_stats_<discord_user_id>.png
- one shared backdrop across Overview, Activity, and Combat
- invoking player's bounded circular Discord avatar at top left on every successful mode
- safe local GovernorOS/KD98 avatar fallback
- header contains scope/identity, mode, period, exact dates, Stats anchor, coverage, state, and full UTC
- fallback is built from the same already-authorized payload and performs no second data fetch
- no separate successful chart embeds; RSS and Fort charts are integrated into Activity

Approved modes:
1. Overview
2. Activity
3. Combat

Approved default state:
- mode: Overview
- period: This Week
- scope: selected Dashboard governor, otherwise Main, otherwise first valid canonical slot
- All Linked is explicit and is never the default
- one linked governor opens directly without a redundant selector

Approved periods, all source-date anchored and inclusive:
- Yesterday = anchor - 1 day only
- This Week = Monday through anchor
- Last Week = previous Monday through Sunday
- This Month = first of anchor month through anchor
- Last Month = complete previous calendar month
- Last 90 Days = anchor - 89 days through anchor
- Last 180 Days = anchor - 179 days through anchor
- replace current Last 3M and Last 6M labels/meanings for the personal route
- do not reuse the current month-boundary last_3m/last_6m SQL meanings under the new labels
- Yesterday never silently means previous available scan
- exact dates must be displayed on every card and fallback

Approved Growth metrics:
- Power change, with period-end Power as secondary context
- Troop Power change, with period-end Troop Power as secondary context

Approved Activity/Participation metrics:
- RSS gathered
- RSS assisted
- Helps
- Build activity
- Tech donations
- Forts total
- Forts launched
- Forts joined
- RSS Gathered, RSS Assisted, and Helps use consistent total plus Average per reporting day treatment
- other daily activity metrics may use the same average where source-correct/readable
- negative source corrections remain signed and are never clamped to zero

Approved Combat metrics:
- Kill Points gained
- T4 kills gained
- T5 kills gained
- T4+T5 combined period gain
- Deads gained
- Healed Troops gained

Explicitly removed from /me stats:
- Ark Played
- Ark Won
- Ark average kills/deads/heals
- Ranged Points
- Highest Acclaim
- Autarch values
- Olympia
- achievements/badges/rankings/targets
- every download/export action

Approved selector and All Linked contract:
- use Governor ID or a server-held opaque token as component identity, never governor name
- support duplicate governor names
- support Main + 5 Alts + 20 Farms plus explicit All Linked through safe paging/picker behavior
- re-resolve active registry linkage before every period/scope data fetch
- reject removed, transferred, forged, foreign, expired, and superseded interactions
- preserve mode and period when changing governor/scope
- never silently fall back from an invalid governor to All Linked
- deduplicate Governor IDs before SQL reads and All Linked aggregation
- retain a visible duplicate-ID review warning
- All Linked is period activity, not another Account Summary
- aggregate additive metrics only
- do not sum ratios, ranks, highest values, or per-account averages
- recompute daily series and averages after aggregation
- show reporting-governor and account-day coverage
- do not treat missing rows as zero without authoritative source proof

Approved state/coverage contract:
- READY = healthy required reads and complete required Stats coverage
- PARTIAL = usable data with incomplete date/governor/account-day/source coverage
- NO DATA = healthy read with no usable rows for the exact selected scope/window
- UNAVAILABLE = registry/SQL/required request dependency failed
- access removal/transfer is an explicit access-changed interaction result, not NO DATA
- selected-governor coverage = distinct reporting dates / expected inclusive dates
- All Linked coverage includes reporting governors and distinct governor-date account-days
- audit null/absent Alliance Activity and Fort semantics before retaining any missing-as-zero behavior
- player-facing errors must not expose Python exception types or raw SQL

Approved chart/accessibility contract:
- Activity contains RSS daily and Fort daily trends
- use exact selected dates and values
- support signed axes for negative corrections
- one-point Yesterday uses a marker/bar or text summary, not a fake trend
- no valid points means no chart
- provide text equivalents: total, average per reporting day where applicable, peak date/value, coverage
- do not depend on colour alone; include signs, labels, and readable markers/legends
- validate original 1702x924, Discord desktop, and mobile previews

Approved interaction/lifecycle contract:
- private/ephemeral only; no public fallback or expiry notice
- author checks occur before mutating visible state
- latest valid transition wins; stale work cannot replace newer content
- mode-only changes reuse the immutable authorized payload where possible
- period/scope changes revalidate current registry and perform one set-based load
- restore usable controls after handled failures
- 180-second inactivity baseline
- timeout preserves the last report, disables all controls, and says:
  Report controls expired. Run /me stats to refresh.
- do not delete the report or send a second expiry card
- render off the event loop with explicit bounds
- close every chart/image/file/stream on success, failure, timeout, navigation, cancellation, and stale suppression

Approved performance/telemetry direction:
- prefer one consistent set-based payload rather than sequential summary/trend/freshness reads
- validate single, multi, 26-account, 90-day, and 180-day performance
- use a bounded TTL/LRU cache; authorization before cache reuse
- safely deduplicate identical inflight loads
- separate data, render, and delivery timings
- provisional targets for audit: initial p95 <=5s, transition p95 <=4s, data timeout around 8-10s,
  render timeout around 3-4s
- telemetry includes entry route, mode, period, scope type, coverage counts, result state, timings,
  fallback reason, timeout, access changed, and stale suppression
- do not routinely log governor/account names or report values in Phase 6 interaction telemetry

Approved SQL boundary:
- validate C:\K98-bot-SQL-Server read-only
- inspect dbo.vDaily_PlayerExport, dbo.usp_GetPlayerStatsWindows,
  dbo.fn_StatsWindowDeltas_GovCsv, dbo.IntList, and underlying Stats/Alliance Activity/Fort sources
- no SQL schema/object/index/data/permission/deployment change is pre-approved
- do not modify shared last_3m/last_6m semantics in place without explicit approval
- if exact correctness/performance genuinely requires a SQL diff, stop with one narrow additive
  option, deployment order, security target, tests, and rollback

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/reference/K98 Bot - Project Engineering Standards.md
- docs/reference/K98 Bot - Coding Execution Guidelines.md
- docs/reference/K98 Bot - Testing Standards.md
- docs/reference/K98 Bot - Skills & Refactor Triggers.md
- docs/reference/K98 Bot - Deferred Optimisation Framework.md
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 6 Interactive Period Performance and Legacy Command Retirement.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5G Account Data Export Consolidation.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 4 Premium Governor Dashboard Renderer.md
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Inspect assets/me/cards/me_stats.png before architecture approval. Confirm exact 1702x924 production
size, opacity, safe zones, and suitability for Overview/Activity/Combat. Do not create another backdrop.

Follow docs/reference/README.md for conditional command, helper, telemetry, testing, security, PR-review,
and promotion references.

Use these skills:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review
- k98-promotion-check only at the later promotion gate
- k98-security-review-routing

Security routing:
- bot repository: provisional final diff-focused Changes review against the intended Phase 6 base..head
  or staged working-tree patch
- execute $codex-security:security-diff-scan only after the final diff exists
- verify Scan type: Changes and Deep: Off
- focus on registry revalidation, private visibility, component forgery/expiry/concurrency, SQL over-read,
  avatar/network input, telemetry minimisation, performance/resource exhaustion, attachments, cleanup,
  and atomic command retirement
- SQL repository: documented skip when validation remains read-only and the SQL repo has no diff
- if a SQL diff is separately approved, stop and record a separate SQL Changes target/review
- do not start a standard or deep codebase audit without an explicit operator request

Mandatory workflow:
1. Audit and scope review, then stop for approval.
2. Record the provisional security-routing decision and targets; do not start a scan.
3. Architecture and read-only SQL-contract validation, exact file manifest, visual geometry, component
   rows, and selector/paging proposal, then stop for approval.
4. Implementation plan covering data shape, periods, metrics, coverage, aggregation, renderer, charts,
   interactions, performance, tests, communication, deploy/resync, smoke, rollback, and docs, then stop.
5. Implement only after approval.
6. Run focused/visual/full/architecture/deferred/security-routing/registration/import/pre-commit/log-noise validation.
7. Run final bot Changes review with Deep off and confirm the SQL skip/outcome.
8. Complete K98 PR review and mirror PR handoff.
9. Announce removal, deploy/restart, resync commands, and complete operator Discord smoke after acceptance.
10. Run promotion check and promote the exact accepted patch.

First response: audit only. Do not code.

Audit and report with repository evidence:

A. Current command and migration surface
- exact /my_stats registration, decorators, channel/thread/admin behavior, version, usage identity,
  private response, tests, docs, and command-cache expectations
- exact current 38/99/7/2 baseline and 37/100/8/2 target
- exact /me group insertion point and standard decorators for /me stats
- exact selected-governor Dashboard action rows/context and component capacity
- every active /my_stats, Last 3M/6M, channel-gate, old-chart, timeout, and rerun reference
- latest descriptive usage evidence and stats-channel communication audience
- exact application-command resync steps

B. Legacy personal/leadership shared stack
- map commands/stats_cmds.py, embed_my_stats.py, stats_service.py, stats_helpers.py,
  constants.STATS_VIEW_TIMEOUT, tests/test_embed_my_stats.py, and tests/test_stats_service.py
- classify personal-only, leadership-only, and shared callers
- prove /stats player dependencies that must remain
- identify zero-callers only after /my_stats removal
- document direct SQL/business logic not to copy
- capture leadership defects/cleanup for later Inspect review rather than expanding Phase 6

C. Governor context, avatar, and Dashboard patterns
- no/one/multiple/>25 linked governor behavior
- canonical slots, duplicate names, duplicate IDs, selected Dashboard context, Main-first fallback
- access-revalidation and latest-transition-wins helpers
- accepted paged governor selector/picker patterns
- invoking-user avatar limits/fallback
- attachment replacement, timeout, fallback, and stream cleanup patterns

D. SQL/data and performance proof
- exact vDaily_PlayerExport columns/types/null/date grain/source joins/index implications
- exact global Stats anchor semantics
- current stored-procedure/function period and aggregation semantics
- why current last_3m/last_6m cannot back Last 90/180 unchanged
- cumulative versus delta versus daily-count semantics for every approved metric
- negative correction behavior
- null/absence behavior for Alliance Activity and Forts
- one-call/minimal-call set-based options for up to 26 accounts x 180 days
- representative rows/logical reads/timing/concurrency
- no-SQL bot-DAL recommendation or explicit narrow SQL escalation

E. Exact period, coverage, and All Linked proof
- deterministic boundaries across week/month/year/leap-day edges
- exact 90/180 counts
- missing Yesterday
- selected reporting days
- All Linked reporting governors/account-days
- duplicate-ID dedupe
- additive metric proof and recomputed averages/daily series
- no ratios/highest/averages summed
- no missing-as-zero without source proof

F. Visual, renderer, charts, fallback, and accessibility
- validate me_stats.png dimensions/opacity/safe zones
- Overview/Activity/Combat geometry and exact external component-row options
- top-left circular Discord avatar and fallback
- long/Unicode and large signed values
- integrated RSS/Fort charts including negative, one-point, and no-point behavior
- accessible text equivalents and no colour-only meaning
- same-payload fallback and no-second-fetch proof
- file/stream lifecycle and original/desktop/mobile visual matrix

G. Interaction, privacy, timeout, cache, and telemetry
- private-anywhere command with no channel decorator/public fallback
- author check before state mutation
- current-linkage revalidation before fetch
- forged/foreign/expired/removed/transferred interaction rejection
- >25 selection plus All Linked
- mode/period/scope preservation
- latest-request-wins and control recovery after failure
- 180-second preserve-and-disable timeout
- bounded cache and authorization-before-cache
- data/render/delivery telemetry and content minimisation

H. Documentation, deployment, observation, and rollback
- exact validator/canonical/README/briefing/deferred/task-index/programme/smoke updates
- stats-channel announcement before removal
- atomic deploy/restart/resync order
- production verification and observation metrics
- rollback restore/redeploy/resync/smoke
- historical archive records to leave unchanged

Stop after providing:
1. audit findings;
2. exact Review / Modify / Create / Delete manifest;
3. confirmed current and target command counts;
4. /stats player preservation and legacy zero-caller boundary;
5. SQL read-only findings and no-SQL/escalation recommendation;
6. typed architecture recommendation;
7. exact component row and >25 paging recommendation;
8. period/metric/coverage/All Linked/state recommendation;
9. renderer/chart/fallback/accessibility recommendation;
10. measured performance/cache/telemetry recommendation;
11. test-selection proposal;
12. security-routing proposal;
13. communication/deploy/resync/smoke/rollback boundary;
14. explicit approval checkpoint.

Do not code in the first response.

Expected architecture direction, subject to the audit/architecture stop:
- commands/me_cmds.py owns only the thin /me stats registration
- commands/stats_cmds.py loses the personal /my_stats registration but preserves /stats player
- ui/views/player_self_service_stats_views.py owns author-gated state, components, paging, transitions,
  attachment/fallback delivery, and timeout only
- player_self_service/stats_models.py owns Discord-free typed period/scope/state/coverage/metric payloads
- player_self_service/stats_service.py owns registry revalidation, exact windows, aggregation, coverage,
  state, cache coordination, and payload assembly
- stats/dal/personal_stats_dal.py owns set-based read-only SQL
- player_self_service/stats_renderer.py owns deterministic 1702x924 Pillow/card/chart rendering
- the Dashboard reuses validated selected-governor context
- legacy embed_my_stats.py/root stats_service.py remain where /stats player still calls them
- commands/views contain no SQL or dataframe/chart business logic

Required focused coverage includes:
- command counts/removal/resync and preserved /stats player
- no/one/multiple/26-slot/duplicate-name/duplicate-ID/All Linked
- active-linkage change and forged/foreign/expired/stale transitions
- all seven exact periods and edge dates
- every approved metric positive/zero/negative/null
- selected and All Linked totals/averages/coverage
- READY/PARTIAL/NO DATA/UNAVAILABLE/access changed
- Overview/Activity/Combat, avatar/fallback, charts, mobile, same-payload fallback
- timeout, cache, performance, telemetry, attachment/stream cleanup
- unchanged Phase 5G downloads and Inventory report-page exports
- no Ark and no download/export action in /me stats

Do not implement until I approve the audit, architecture, and implementation plan.
```
