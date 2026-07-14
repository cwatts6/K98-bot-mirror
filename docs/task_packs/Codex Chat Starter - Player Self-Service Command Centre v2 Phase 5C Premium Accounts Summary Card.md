# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card

Status: implementation complete on the mirror feature branch; automated validation is recorded in
the task pack/PR and operator Discord smoke remains the final acceptance gate. Retained as the exact
execution prompt.

## Copy/Paste Starter

```text
Codex, implement Player Self-Service Command Centre v2 Phase 5C: Premium Accounts Summary Card.

Approval state:
- implementation is approved within the task-pack contract
- the visual/product workshop is complete
- the production backdrop is already in the repo at `assets/me/cards/me_accounts.png`
- the asset is exactly 1702x924 and is approved for runtime use
- do not reopen backdrop selection, metric selection, or Account Summary scope unless repository
  evidence reveals a genuine blocker

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5B Premium Inventory Report Backdrops and Visual Alignment.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 4 Premium Governor Dashboard Renderer.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 6 Guided Management Cards and Workflow Simplification.md
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md
- the GovernorOS Visual Design Bible where present

Use these skills:
- k98-architecture-scope
- k98-discord-command-feature
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review
- codex-security:security-scan

First inspect the repository and report a concise implementation map:
- current `/me accounts` command/view/service/DAL/renderer flow
- current `AccountStatus`/summary payload and guided Manage refresh path
- authoritative registry slot/Main/name fields
- authoritative latest Kingdom 1198 scan fields and actual SQL column names
- canonical Inventory current-RSS calculation and whether it supports a bulk linked-governor read
- existing location, civilisation mapping, compact number, CSV, fallback, and attachment helpers
- exact files/tests you will change

After that inspection, proceed without another product approval checkpoint unless one of the task
pack's escalation gates is hit.

Locked main card:
- private/ephemeral, author-gated, all-linked-governor scope
- standalone 1702x924 attachment using `assets/me/cards/me_accounts.png`
- stable `me_accounts_<discord_user_id>.png` filename
- best-effort invoking-user Discord avatar at the upper left, with author validation and bounded read
- no Change Governor and no implicit selected-governor filter
- optional selected dashboard governor may be retained only as validated Dashboard-return context
- successful render uses a standalone attachment; concise fallback uses the same already-loaded
  authorized payload

Locked hierarchy:
ACCOUNT CENTRE                                      READY/REVIEW/SETUP
<Discord display name> (1198)                       <N> governors
MAIN GOVERNOR  <name> • <ID>

LATEST SNAPSHOTS
[ LINKED ] [ PORTFOLIO POWER ] [ T4+T5 KILLS ] [ RSS TOTAL ]

LINKED GOVERNORS
SLOT | GOVERNOR | ID | POWER | DATA

PORTFOLIO INSIGHT
<one deterministic observation, maximum two clauses>

Manage accounts
Find an ID, add, replace or remove a linked governor.

Refreshed <DD Mon YYYY HH:MM UTC>

Metric rules:
- Linked is the real linked count only; never show count against configured capacity
- Linked helper shows real Main/Alt/Farm role counts
- Portfolio Power sums the latest available Power for distinct linked Governor IDs
- T4+T5 Kills sums only latest cumulative T4 and T5 kills
- RSS Total sums current holdings using the exact canonical Inventory calculation
- RSS Gathered and RSS Assistance are lifetime values and are not the headline RSS metric
- missing values are not zero; show honest n/N reporting coverage and `—` where nothing reports
- do not double-count duplicate linked Governor IDs; duplicates produce REVIEW

Latest-scan rule:
- Kingdom 1198 is the only scan dataset
- `latest_scan_date = MAX(ScanDate)` across that dataset
- each governor uses its own `MAX(ScanDate)`
- CURRENT when equal; STALE when older; NO DATA when no usable row; UNRESOLVED when the linked record
  cannot be resolved safely
- READY when Main exists, IDs are unique/resolved, and all linked governors are CURRENT
- REVIEW for stale/missing/unresolved/duplicate entries
- SETUP for no linked governors or no Main
- Inventory coverage is separate from the governor DATA state

Roster rules:
- one full-width table, Main first then authoritative slot order
- latest scanned name, with registered-name fallback
- show up to 8 rows; with more than 8 show 7 rows plus `+ N more — open Account Summary`
- this is display pagination only, never an account registration limit

Portfolio Insight priority:
1. data/coverage issue
2. registered-name/current-name mismatch
3. current RSS concentration
4. power or T4+T5 composition
5. activity leader such as RSS Assistance or Helps
6. positive all-current fallback
Use genuine values, stable tie handling, no zero-denominator percentages, and no mixed-scope
kills-per-power ratio.

Main component rows:
- Row 0: Accounts (blue, disabled) | Reminders (blue) | Preferences (blue)
- Row 1: Dashboard | Exports
- Row 2: Manage Accounts | Account Summary

Manage Accounts:
- preserve the existing lookup/add/replace/remove/confirm/cancel/current-state revalidation,
  ownership/claim, slot, audit, and mutation wording contracts
- successful mutation refreshes the new portfolio payload/card
- do not redesign the guided workflow

Account Summary:
- new private read-only child action covering every linked governor
- use the same 1702x924 approved backdrop and standalone attachment delivery
- stable `me_account_summary_<discord_user_id>.png` attachment filename
- no Change Governor
- 8 governor rows per page; Main first then slot order; support hundreds of governors
- three visual sections:
  1. Overview: Slot, Governor, Civilisation, City Hall, VIP, Power, Troop Power,
     Location X:Y, Last Scan
  2. Combat & Participation: Slot, Governor, Kill Points, T4+T5 Kills, Deads, Healed Troops,
     Highest Acclaim, KP Loss, Tanking Score, Conduct
  3. Economy & Activity: Slot, Governor, RSS Gathered, RSS Assistance, RSS Total, Helps,
     Inventory As Of
- repeated compact portfolio header includes total Power, Troop Power, T4+T5 Kills, and RSS Total
- additive fields may use SUM; Highest Acclaim uses MAX; never aggregate IDs, names, coordinates, or dates
- section change resets to page 1

Account Summary controls:
- Row 0: Accounts (blue, disabled) | Reminders (blue) | Preferences (blue)
- Row 1: Dashboard | Exports
- Row 2: Overview | Combat | Economy
- Row 3: Previous | Next | Download CSV | Back to Accounts
- active/boundary controls disabled appropriately

Complete CSV:
- private follow-up; do not destroy the visual report state
- one row per linked registry entry
- exact non-compact values
- columns, in order:
  Slot, Role, Registered Name, Current Governor Name, Governor ID, Civilisation, City Hall, VIP,
  Power, Troop Power, Kill Points, T4 Kills, T5 Kills, T4+T5 Kills, Deads, Healed Troops,
  KP Loss, Tanking Score, Highest Acclaim, Helps, RSS Gathered, RSS Assistance, RSS Total, Conduct, Location X,
  Location Y, Data State, Last Governor Scan, Inventory As Of
- Helps appears once
- UTF-8, existing export conventions, CSV formula-injection protection, safe filename, and complete
  stream cleanup

Approved data scope:
- read-only service/DAL/payload expansion is part of Phase 5C
- use typed portfolio/row/summary models rather than renderer-owned dictionaries
- use set-based/bulk reads; no N+1 per governor; design for up to hundreds of linked accounts
- validate actual SQL sources against `C:\K98-bot-SQL-Server`
- reuse the canonical Inventory RSS calculation; do not duplicate or redefine it
- preserve nulls and exact values in models/CSV; formatting belongs in the renderer
- KP Loss is `Healed Troops * 20`; Tanking Score is
  `Kill Points / (KP Loss + Deads) * 100`, with no zero-denominator value
- no SQL schema/table/view/index change is approved
- no registry, slot, ownership, claim, lookup, or persistence redesign is approved

Delivery and safety:
- render off the event loop
- no second data fetch merely because rendering/edit/delivery fails
- same-payload fallback for main and current summary page
- deliberate attachment replacement on every transition
- graceful timeout preserves the current private report, disables controls, and gives a rerun instruction
- close all image/file/CSV streams on success and every failure/timeout/stale/cancel path
- keep coordinates and the complete report private
- protect CSV from formula injection and filenames from user-controlled path content
- run focused tests, repository gates, full pytest, visual samples, and Codex Security review

Do not do:
- no account-capacity denominator or arbitrary max
- no fifth headline metric
- no Change Governor
- no public Account Summary or coordinate disclosure
- no SQL schema/index/persistence change without a new approval gate
- no redesign of Manage
- no changes to Reminders, Preferences, Inventory summary, Exports summary, Dashboard, direct
  Inventory reports, Export Stats, History, Inspect, Last Login, Olympia, CrystalTech, website/API,
  public `/kvk`, existing export schemas, Inventory imports, or Google Sheets behavior
- no broad renderer/view framework
- no fake data, dummy rows, estimated totals, or invented insights

Escalate only when an approved field has no authoritative source, canonical RSS cannot be reused,
a schema/index change is genuinely required, the approved asset is missing/wrong-sized, component
limits make the locked controls impossible, or current registry semantics make Main/slot ordering
ambiguous. Do not silently omit or substitute requirements.

Implement the approved scope, add/update focused tests and documentation, render original/desktop/
mobile samples, run repository gates and security review, create/update the PR, and stop for operator
Discord smoke.
```
