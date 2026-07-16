# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5G Account Data Export Consolidation

Status: active prepared implementation starter. Product decisions are approved; implementation must
begin with audit/scope and use the normal stop gates. One-pass execution is not approved.

## Copy/Paste Starter

```text
Codex, begin Player Self-Service Command Centre v2 Phase 5G: Account Data Export Consolidation.

Approval state:
- GovernorOS v2 Phases 1-5F are complete and operator accepted
- Phase 5F removed /me inventory, /myinventory, /inventory_preferences, /export_inventory, the
  Export Inventory button/option window, combined/all-governor Inventory export, public Inventory
  posting, and combined All viewing
- Inventory exports now remain only on the selected-governor RSS, Speedups, and Materials report pages
- do not reopen or duplicate central Inventory export
- the accepted Account Centre and Account Summary visual outputs must remain
- the canonical personal download route is /me accounts -> Account Summary -> Download data
- remove /me exports in Phase 5G
- remove /my_stats_export in Phase 5G; do not retain a redirect-only command
- retain /my_stats unchanged in Phase 5G and hand its redesign/migration to Phase 6
- all personal data downloads are all-linked/user-level; no Change Governor and no selected-governor
  Stats export in Phase 5G
- Full workbook is the default output
- Full workbook starts with ACCOUNT_SUMMARY, then README, ALL_DAILY, then per-governor sheets
- Current account snapshot CSV preserves the accepted 29-column Account Summary contract
- Raw stats history CSV preserves one row per governor per source date
- history choices are 30, 60, 90, 180, and 360 days; default 90
- one exact inclusive N-day window must be used everywhere, anchored to latest source date with
  start = latest - (days - 1)
- filter before reporting row counts
- correct every identified issue: unfiltered ALL_DAILY, 91-day 90-day output, fetched-vs-written row
  count, partial INDEX, fixed 180-day Forts rule, Stats CSV formula safety, duplicate Excel/Google
  Sheets choices, ambiguous freshness, and legacy footer/copy
- Google Sheets is workbook compatibility, not a separate generated format or live Sheet
- no SQL change or deployment is approved
- no new backdrop is required
- runtime implementation is approved subject to audit, architecture, plan, validation, review, and
  promotion gates
- one-pass execution is not approved

Current command target:
- top-level commands: 39 -> 38
- /me grouped subcommands: 8 -> 7
- /inventory grouped subcommands: remains 2

Target /me group:
/me dashboard
/me accounts
/me reminders
/me preferences
/me resources
/me speedups
/me materials

Removed in Phase 5G:
/me exports
/my_stats_export

Retained unchanged in Phase 5G:
/my_stats
/inventory import
/inventory audit
selected-governor RSS/Speedups/Materials report-page exports

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5G Account Data Export Consolidation.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5F Inventory Surface Consolidation and Legacy Retirement.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card.md
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Follow the conditional reading order in docs/reference/README.md for command retirement, Discord
components, file/spreadsheet generation, SQL-backed data access, testing, security routing, PR review,
and promotion.

Validate the SQL contract read-only against:
C:\K98-bot-SQL-Server

At minimum inspect dbo.vDaily_PlayerExport and search for downstream dependencies on current CSV
headers, workbook filenames, INDEX/ALL_DAILY sheet names, date-window behavior, and exports. No SQL
schema/table/view/procedure/index/data/permission change or deployment is approved. If a SQL change
appears necessary, stop and request a separate approval rather than expanding Phase 5G.

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
- bot repository: provisional diff-focused Changes review against the final intended base..head or
  staged working-tree patch
- execute $codex-security:security-diff-scan only after the final diff exists
- verify Scan type: Changes and Deep: Off
- focus on account-linkage revalidation, private response boundaries, component forgery/expiry,
  formula injection, path/filename/sheet safety, date/governor over-export, telemetry, and cleanup
- SQL repository: documented skip if work remains read-only and the SQL repo has no diff
- do not start a standard or deep codebase audit without a separate explicit operator request

Mandatory workflow:
1. Audit and scope review, then stop for approval.
2. Record the provisional security-routing decision and exact target; do not start a scan.
3. Architecture and SQL-contract validation plus exact file manifest, then stop for approval.
4. Implementation plan, command-resync order, output migration, test matrix, and rollback, then stop
   for approval.
5. Implement only after approval.
6. Run focused/output/full validation, command registration, architecture/deferred/security-routing,
   smoke imports, log-noise, pre-commit, K98 PR review, and final Changes review.
7. Create/review the mirror PR and complete operator Discord smoke.
8. Run promotion check, promote the exact accepted patch, deploy/restart, resync application commands,
   and verify production only after acceptance.

First response: audit only. Do not code.

Audit and report with repository evidence:

A. Current command surface
- exact /me exports registration, decorators, version, callback, PAGE_EXPORTS route, tests, docs, and
  command cache expectations
- exact /my_stats_export registration, decorators, version, redirect helper, unused format/days
  options, tests, docs, and command cache expectations
- exact /my_stats registration/decorators/channel gate/view/service paths to preserve unchanged
- exact current and target command counts
- every validator/canonical table/test/smoke document that must change
- command resync procedure required after deployment

B. Current Exports page and navigation
- every PAGE_EXPORTS import and caller
- every Exports button/custom_id/callback in governor dashboard, Accounts, Reminders, Preferences,
  Account Summary, child views, fallbacks, and tests
- build_exports_embed and generic renderer/page-card branch
- ExportStatus and generic summary reads
- assets/me/cards/me exports.png references
- ui/views/player_self_service_export_views.py callers
- exact direct orphan candidates and shared helpers that must remain

C. Account Summary canonical host
- immutable AccountsPortfolioPayload lifecycle and active authorisation boundary
- Account Summary Overview/Combat/Economy/page/timeout controls
- current Download CSV callback and 29-column accounts_export contract
- formula-safety behavior
- safe child-window pattern that preserves the parent report
- registry re-resolution/revalidation helper to use at Download execution
- current scan and Inventory freshness semantics

D. Stats export service/DAL/builders
- services/stats_export_service.py callers, models, temp-file lifecycle, telemetry, row metadata, and
  format handling
- stats/dal/stats_export_dal.py query, exact columns, sorting, and SQL view contract
- stats_exporter.py README/INDEX/ALL_DAILY/per-account tabs, KPI periods, Forts, sparklines, charts,
  daily tables, sheet names, links, engines, and date filtering
- stats_exporter_csv.py columns, date filtering, text handling, ordering, NaN/Inf behavior, and callers
- all downstream consumers of current filenames, headers, sheet names, or full-history behavior

E. Confirm every identified output defect
- ALL_DAILY currently receives unfiltered history
- inclusive cutoff currently produces days+1 calendar dates
- follow-up row_count currently represents fetched rows, not written rows
- INDEX is a partial snapshot compared with Account Summary
- Forts summary has a hidden fixed 180-day period
- Stats CSV lacks Account Summary's formula-leading text safety
- Excel and GoogleSheets call the same workbook builder and generate .xlsx
- follow-up lacks exact written start/end and separate freshness
- legacy footer/copy still advertises /my_stats_export or /me exports
- cleanup ownership across all success/failure paths

F. Output compatibility audit
- active external/manual consumers of INDEX, ALL_DAILY, per-account sheet names, filenames, and CSV
  headers
- whether replacing INDEX with ACCOUNT_SUMMARY is safe; if an active dependency is proven, stop and
  present a migration option rather than silently keeping duplicate summaries
- whether XlsxWriter and openpyxl paths meet one output contract
- exact window helper and filtering point
- exact safe-text helper design without corrupting numeric negatives

G. Documentation state
- every active statement that advertises /me exports or /my_stats_export
- every statement that says Phase 5G scope is undecided
- every statement that defines Phase 6 as dashboard Export Stats action
- every canonical /me list and command count
- historical archived files that remain accurate records and should not be rewritten

Stop after providing:
1. audit findings;
2. exact Review / Modify / Create / Delete manifest;
3. current and target command counts;
4. architecture recommendation;
5. exact output-contract recommendation and any compatibility escalation;
6. SQL read-only findings;
7. test-selection proposal;
8. security-routing proposal;
9. deployment/resync and rollback boundary;
10. explicit approval checkpoint.

Locked canonical journey:
/me accounts
-> Account Summary
-> Download data

Locked Download data choices:
1. Full workbook (.xlsx) - default
   - Account Summary + selected stats history
   - Excel / Google Sheets compatible
   - days selector 30/60/90/180/360, default 90
2. Current account snapshot (.csv)
   - exact current 29-column Account Summary
   - one row per linked governor
   - days not applicable
3. Raw stats history (.csv)
   - existing raw stats columns
   - one row per governor per source date
   - days selector 30/60/90/180/360, default 90

Locked workbook order:
1. ACCOUNT_SUMMARY
2. README
3. ALL_DAILY
4. per-governor sheets

Locked history filter:
latest_date = max(valid AsOfDate in authorised dataset)
start_date = latest_date - (requested_days - 1 days)
include start_date <= AsOfDate <= latest_date

Locked metadata:
- actual rows written, never prefilter fetched rows
- exact written history start and end dates
- authorised distinct governor count
- current snapshot row count where applicable
- stats freshness
- Inventory freshness/coverage where applicable
- generated full UTC timestamp

Locked privacy/scope:
- private/ephemeral only
- author-gated options and download
- active registry re-resolution at Download execution
- one immutable authorised export context
- all-linked user-level scope
- deduplicate history Governor IDs without hiding Account Summary duplicate-data state
- no Change Governor
- no dashboard Export Stats action

Locked Google Sheets wording:
- no separate Google Sheets output option
- one Full workbook (.xlsx) option labelled Excel / Google Sheets compatible
- upload-to-Drive instructions may be provided
- no live Sheet creation or sharing

Locked removal boundary:
- remove /me exports registration
- remove /my_stats_export registration
- remove all Exports navigation/buttons/custom IDs/copy
- remove PAGE_EXPORTS and direct Exports-only code/assets/tests after zero-caller proof
- remove obsolete ExportStatus/generic summary work only after caller proof
- update validator, canonical command docs, task indexes, README, briefing, programme and deferred docs
- resync commands after deployment

Locked preservation boundary:
- preserve /my_stats unchanged for Phase 6
- preserve accepted /me accounts and Account Summary cards and management
- preserve 29-column current snapshot contract
- preserve raw Stats column contract unless audit proves a defect and escalates it
- preserve selected-governor RSS/Speedups/Materials reports and their report-page exports
- preserve /inventory import and /inventory audit
- preserve registry authority, ownership/claim, VIP, profile, reminder, and Inventory calculation rules
- no SQL change
- no broad generic renderer framework
- no cross-domain export redesign

Expected architecture:
- Account Summary view owns only the Download data entry action
- a dedicated private Account Data options view owns component state
- a typed Account Data export service owns revalidation, output-kind/days validation, exact window,
  builder coordination, metadata, telemetry, and cleanup
- Accounts owns current snapshot mapping
- Stats DAL owns daily history reads
- pure shared helpers own exact window and spreadsheet-safe text only where contracts are identical
- commands and views contain no SQL or dataframe/workbook business logic

Required focused tests:
- command registration/removal and unchanged /my_stats
- no Exports navigation/custom IDs
- author/foreign/expired/stale option interactions
- account unlink/relink between open and Download
- all three output kinds
- exact 30/60/90/180/360 boundaries
- current snapshot 29-column golden contract
- raw history header/order/filter/safety contract
- workbook sheet order, values, links, filters, Forts period, charts, long/duplicate names, sparse data,
  and no repair warnings
- actual metadata and separate freshness
- temp/stream cleanup on every path
- Account Summary visual regression
- Inventory report-page export regression
- /my_stats regression
- command validators, architecture, deferred, security routing, smoke imports, pre-commit, full pytest,
  and log-noise

Phase 6 handoff after Phase 5G:
- Interactive Personal Stats Experience and /my_stats Migration
- separately decide canonical /me stats path, channel/private behavior, account selector and ALL mode,
  current time slices, presentation, performance, communication, final /my_stats removal, command
  resync, smoke, and rollback
- do not move personal downloads out of Account Summary
```
