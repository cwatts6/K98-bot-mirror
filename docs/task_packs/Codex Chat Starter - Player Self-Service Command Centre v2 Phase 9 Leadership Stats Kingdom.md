# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 9 Leadership `/stats kingdom`

Status: initiation starter for proposed Phase 9. Start only after Phase 8 is accepted and archived. Use
with the matching Phase 9 task pack. One-pass execution is not approved.

## Copy/Paste Starter

```text
Codex, begin Player Self-Service Command Centre v2 Phase 9: Leadership /stats kingdom.

Approval state:
- Phase 8 /stats player must be complete and accepted first
- add private grouped /stats kingdom
- add no new top-level command
- change no /me command
- first release has two pages: Kingdom Overview and KVK Summary
- use the Phase 8 dedicated role-ID/channel gate, audit family, private delivery, fallback, timeout,
  Definitions, transition, and cleanup contracts
- one-pass execution is not approved
- first response must be audit/scope only; do not code

Command baseline before Phase 9:
- 36 top-level
- 100 grouped
- 8 /me
- 1 /stats: player
- 2 /inventory

Approved target:
- 36 top-level
- 101 grouped
- 8 /me
- 2 /stats: player, kingdom
- 2 /inventory
- command resync required

Permission:
Leadership role IDs:
- Leadership channel and child threads

Admin:
- Leadership channel and child threads
- Notify channel and child threads

Never:
- role-name-only authority
- Ark Setup
- DMs
- any other channel

Command:
- /stats kingdom
- no options in first release
- configured home kingdom only
- no arbitrary kingdom selector
- private only
- no export/share

Pages:
1. Kingdom Overview
2. KVK Summary
Controls:
- page buttons
- one chart metric selector on Overview
- Definitions/Method
- no player/governor picker

Overview current metrics:
- Total Power
- Total Kill Points
- Total Deads
- Total Healed
- Total T4+T5 Kills
- Total Kingdom Acclaim = SUM(HighestAcclaim) for the dynamic roster at the selected monthly snapshot
- Active Governors = distinct Governor IDs in the authoritative complete scan
- Average Power per Active Governor
- Net Active-Governor Change over 12 months

Use Governors, not deduplicated human Players.

Total Kingdom Acclaim helper:
- Combined current-roster Highest Acclaim
- do not describe it as Acclaim earned in the month

Twelve-month series:
- dynamic roster for each month
- monthly point = final authoritative complete SCANORDER in that calendar month
- one final row per Governor ID in that scan
- current month uses latest complete scan and is labelled MTD
- missing months remain missing
- no interpolation
- one large chart with selector; do not overlay incompatible scales

Chart metrics:
- Power
- Kill Points
- Deads
- Healed
- T4+T5 Kills
- Total Kingdom Acclaim
- Active Governors
- Average Power per Active Governor

Chart fallback/Definitions:
- first/latest/net change
- min/max month
- missing months
- MTD
- source scan date per point
- accessible labels/markers, no colour-only meaning

KVK Summary:
- latest four completed/finalized KVKs
- reuse existing kvk_state/reporting completion contract
- do not use end date alone
- exclude active/started/unfinalized KVK
- four equal blocks, newest first
- KVK type/name = KVK_NAME

Each KVK block:
- KVK number
- KVK_NAME
- final data timestamp/state
- Kill Points
- T4+T5 Kills
- Deads
- Healed
- KVK Acclaim = SUM(Acclaim) from one authoritative final row per Governor ID
- Participants = COUNT DISTINCT GovernorID where final Acclaim > 0
- Acclaim per Participant = SUM(Acclaim) / Participants
- KP Loss = SUM(Healed) * 20
- Tanking Score = SUM(Kill Points) / (KP Loss + SUM(Deads)) * 100
- higher Tanking Score is better
- never average individual Tanking Scores

Participant rules:
- governor count, not human-player count
- one final row per Governor ID/KVK
- count each once
- zero Acclaim = nonparticipant
- missing Acclaim = participant metrics unavailable
- do not sum overlapping Pass and Full windows

Final-row audit:
- prove authoritative source for GovernorID, Acclaim, KP, T4, T5, Deads, Healed, final timestamp
- do not sum Pass 4/6/7/8 + Full
- do not sum multiple overlapping named windows
- if uniqueness/finalization cannot be proved, mark partial/unavailable

Freshness/state:
- current latest complete scan <=48h
- stale when older
- partial for material monthly/KVK gaps
- no data when no valid scan
- source/generated time separate

Definitions panel:
- dynamic roster
- monthly final scan
- MTD
- Active Governors
- SUM(HighestAcclaim) Overview
- SUM(Acclaim) KVK
- Participants Acclaim > 0
- Acclaim/Participant
- KP Loss
- ratio-of-sums Tanking
- KVK completion
- freshness/missing months
- no second query

SQL:
- prefer one bounded dbo.usp_GetLeadershipKingdomReview or approved cohesive contract
- inputs home kingdom, 12 months, four KVKs, optional deterministic NowUtc
- compact result sets: header/current totals, 12 monthly rows, four KVK rows, source metadata
- static parameterized SQL
- one final scan/month
- one final row/governor/KVK
- no direct SQL in command/view
- no raw all-kingdom transfer when SQL can aggregate
- indexes/materialization only after plans/reads/timings/concurrency

Architecture:
- leadership_kingdom typed models/service/DAL/renderer/views or approved equivalent
- reuse Phase 8 permission, audit, combat metrics, delivery, fallback, state, timeout, transition,
  Definitions
- do not couple player and kingdom payloads
- no Discord avatar
- neutral KD98/Kingdom identity
- private standalone card

Audit:
- kingdom_open, kingdom_page_change, kingdom_metric_change, kingdom_definitions
- actor/authorization/guild/channel/action/outcome/correlation only
- identified retention 90 days
- no full metric values, rendered files, player names, or raw SQL errors

Performance:
- one bounded SQL load
- initial p95 target <=6s
- payload page transition <=3s
- metric selector <=2s
- measure cold/warm 12-month dynamic roster, four KVKs, concurrency, plans, logical reads, memory grants
- no materialized monthly table without evidence and explicit refresh/staleness/rollback design

Visual:
- Phase 8 leadership family, not /me identity
- large current totals
- one readable chart
- four balanced KVK blocks
- source state/freshness
- mobile readability
- no unnecessary metrics crowded into the card
- same-payload fallback

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- engineering/execution/testing/skills/deferred references
- active GovernorOS programme pack
- matching Phase 9 task pack
- accepted Phase 7 and Phase 8 packs
- KVK reporting/history/rankings/schema-modernisation packs
- briefing, canonical reference, deferred optimisations
- authoritative SQL repo C:\K98-bot-SQL-Server

Security:
- separate SQL and bot Changes scans, Deep off
- focus permission reuse, private delivery, SQL bounds, dynamic roster, final-row duplication,
  resource exhaustion, audit minimization, interaction forgery, attachment cleanup, formula parity
- no standard/deep codebase scan unless requested

Mandatory workflow:
1. Audit/scope only, stop.
2. Present source matrix, monthly final-scan proof, KVK final-row uniqueness, SQL contract, architecture,
   wireframes, command count, performance, security, tests, deploy/resync/smoke/rollback, stop.
3. Present implementation plan, stop.
4. Implement SQL after approval.
5. Implement bot after approval.
6. Validate focused/full/visual/architecture/deferred/registration/import/pre-commit/log-noise.
7. Run SQL and bot Changes reviews with Deep off.
8. PR review.
9. Deploy SQL then bot, restart, resync, smoke, observe, promote.

First response: audit only. Do not code.

Audit report must include:
A. exact /stats group registration and 36/100/8/1/2 -> 36/101/8/2/2 target
B. dedicated Phase 8 permission/audit/helper reuse map
C. authoritative latest complete scan and monthly final-scan algorithm
D. source and history availability for 12 monthly dynamic-roster points
E. exact metric source/aggregation/null/duplicate semantics
F. HighestAcclaim Overview naming and SUM semantics
G. Active Governor and Average Power rules
H. existing KVK completion resolver reuse
I. one-final-row-per-Governor/KVK proof
J. SUM(Acclaim), Participants Acclaim > 0, and Acclaim/Participant rules
K. ratio-of-sums KP Loss/Tanking parity
L. SQL result sets/plans/index evidence
M. two-page visual/control/fallback/lifecycle proposal
N. missing/stale/partial/no-data behaviour
O. tests/security/deploy/resync/smoke/rollback
P. explicit stop for operator approval
```
