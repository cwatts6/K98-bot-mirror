# Codex Task Pack - Player Self-Service Command Centre v2 Phase 5G Account Data Export Consolidation

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 5G Account Data Export Consolidation`
- Date: `2026-07-16`
- Owner/context: `KD98 / Kingdom 1198 GovernorOS v2 follow-on from completed and operator-accepted Phase 5F Inventory Surface Consolidation and Legacy Retirement`
- Task type: `feature | refactor | command retirement | export-contract correction | documentation`
- One-pass approved: `no`
- Product decision approved: `yes`
- Runtime implementation approved: `yes, subject to the normal audit, architecture, implementation-plan, validation, and promotion gates`
- Status: `active task pack prepared; implementation not started`
- New runtime backdrop: `none`
- SQL deployment approved: `no`
- Command target: `39 -> 38 top-level commands; /me 8 -> 7 grouped subcommands; /inventory remains 2`

### Locked product decision

Phase 5G removes `/me exports` and `/my_stats_export` rather than retaining redirect-only or duplicate
entry points. The canonical player journey becomes:

```text
/me accounts
-> Account Summary
-> Download data
```

The accepted Account Centre and Account Summary visual outputs remain the primary current-account
experience. `Download data` provides one private, author-gated choice of:

```text
Full workbook (.xlsx)       -> current Account Summary + selected stats-history window
Current snapshot (.csv)     -> exact current Account Summary rows only
Raw stats history (.csv)    -> one row per linked governor per source date
```

The data scope is always the invoking Discord user's complete currently authorised linked-governor
portfolio. Phase 5G has no selected-governor export mode, no `Change Governor`, and no dashboard
`Export Stats` action.

`/my_stats` remains unchanged in Phase 5G. Its interactive player-stats redesign and command migration
become Phase 6.

## 2. Required Reading

Before implementation, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- this task pack
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5F Inventory Surface Consolidation and Legacy Retirement.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Then follow the conditional reading order in `docs/reference/README.md` for command retirement,
Discord views/components, spreadsheet and temporary-file handling, SQL-backed export contracts,
testing, security routing, PR review, and promotion.

Validate the authoritative SQL source read-only against:

```text
C:\K98-bot-SQL-Server
```

At minimum inspect `dbo.vDaily_PlayerExport` and search for consumers that depend on current CSV
headers, filenames, workbook sheet names, or date-window behavior. No SQL schema, table, view,
procedure, index, data, permission, or deployment change is approved.

## 3. Objective

Make Account Summary the single obvious home for personal account-data downloads. Preserve the
well-received `/me accounts` and Account Summary visual experience, replace its narrow `Download CSV`
action with `Download data`, and provide current snapshot, raw history, and a curated full workbook
through one private option window.

At the same time, remove the now-redundant `/me exports` and `/my_stats_export` command routes and
correct the known Stats export defects so the selected history window, row counts, worksheet content,
freshness, safety, and format labels are truthful and consistent.

## 4. Background And Confirmed Current State

### 4.1 Phase 5F final Inventory state

Phase 5F is complete and operator accepted. Current repository and smoke evidence confirms:

- `/me inventory`, `/myinventory`, `/inventory_preferences`, and `/export_inventory` are removed;
- the `Export Inventory` control and combined/all-governor Inventory export are removed;
- `/me exports` is Stats-only;
- Inventory exports remain only on selected-governor Resources, Speedups, and Materials report pages;
- `/inventory import` and `/inventory audit` remain;
- `dbo.InventoryReportPreference` remains dormant and unchanged.

Phase 5G must not reopen or duplicate the removed central Inventory export.

### 4.2 Current command and UI surface

Current `main` confirms:

```text
commands/me_cmds.py
- /me exports remains registered
- it opens PAGE_EXPORTS through the generic Player Self-Service page controller

commands/stats_cmds.py
- /my_stats remains the live interactive stats command
- /my_stats_export remains registered as a deprecated redirect to /me exports
- its format and days slash options are accepted but discarded

scripts/validate_command_registration.py
- my_stats_export remains in APPROVED_TOP_LEVEL_COMMANDS
```

Current views still expose `Exports` navigation from the governor dashboard and the Player
Self-Service pages. Account Summary currently exposes `Download CSV` and builds only the current
29-column snapshot.

The approved Phase 5G result is removal, not another redirect:

```text
remove /me exports
remove /my_stats_export
retain /my_stats unchanged for Phase 6
replace Account Summary Download CSV with Download data
```

### 4.3 Snapshot versus history

The current Account Summary CSV is a current portfolio snapshot with one row per linked governor.
Its 29-column contract is:

```text
Slot
Role
Registered Name
Current Governor Name
Governor ID
Civilisation
City Hall
VIP
Power
Troop Power
Kill Points
T4 Kills
T5 Kills
T4+T5 Kills
Deads
Healed Troops
KP Loss
Tanking Score
Highest Acclaim
Helps
RSS Gathered
RSS Assistance
RSS Total
Conduct
Location X
Location Y
Data State
Last Governor Scan
Inventory As Of
```

The Stats export is longitudinal: one row per governor per source date with daily values and deltas
from `dbo.vDaily_PlayerExport`. These are related datasets, not interchangeable table grains.

### 4.4 Confirmed output defects to correct

The operator sample and code audit identified all of the following:

1. `ALL_DAILY` writes complete fetched history before filtering, so a 90-day workbook can contain years.
2. Current cutoff subtracts `days`, so inclusive 90-day tables can contain 91 calendar dates.
3. Follow-up `row_count` reports fetched rows rather than actual rows written.
4. Workbook `INDEX` is a partial latest snapshot and duplicates the richer Account Summary.
5. `FortsTotal` on the index uses a hidden fixed 180-day period regardless of selected window.
6. Stats CSV does not apply the formula-leading text protection used by Account Summary CSV.
7. `Excel` and `Google Sheets` are separate choices even though both create the same `.xlsx` bytes.
8. Follow-up metadata lacks exact written start/end dates and separate Stats/Inventory freshness.
9. Snapshot, historical, and generated timestamps can be collapsed into ambiguous update wording.
10. Cleanup must remain complete through the new route and every success/failure/cancel/timeout path.

Every item is in Phase 5G scope.

## 5. Approved Product And Output Contract

### 5.1 Canonical visible journey

```text
/me accounts
-> Account Summary
-> Download data
```

Rules:

- Account Centre and Account Summary visual fields remain unchanged.
- `Download data` is enabled only when the authorised Account Summary payload has rows.
- No `Exports` navigation button remains anywhere in GovernorOS.
- No `Change Governor` appears in the download journey.
- Cancel/timeout guidance points back to `/me accounts -> Account Summary -> Download data`.

### 5.2 Output A: Full workbook - default

Player-facing label:

```text
Full workbook (.xlsx)
Account Summary plus stats history
Excel / Google Sheets compatible
```

Default history window: `90 days`.

Approved worksheet order:

```text
1. ACCOUNT_SUMMARY
2. README
3. ALL_DAILY
4. <one account worksheet per linked governor>
```

Contract:

- `ACCOUNT_SUMMARY` is first and contains the complete current Account Summary data, filters, frozen
  header, useful formats, and links to per-governor worksheets.
- It replaces the partial `INDEX` sheet unless audit proves an active dependency requiring explicit
  migration approval.
- `README` explains snapshot versus history data, selected window, sheet order, missing values,
  freshness, and Google Sheets import compatibility.
- `ALL_DAILY` and every account history table/chart are filtered to one exact selected window.
- Per-governor KPIs, comparisons, sparklines, charts, and daily rows remain useful but must label
  current, selected-window, and lifetime values honestly.

### 5.3 Output B: Current account snapshot

Player-facing label:

```text
Current account snapshot (.csv)
One row per linked governor
```

Contract:

- Preserve the current 29 headers, order, exact values, formula safety, and UTF-8 compatibility.
- Preserve the current filename unless audit proves a compatibility reason to change it:
  `me_account_summary_<discord_user_id>_<UTC timestamp>.csv`.
- History days do not affect this output.
- No history SQL read is performed for snapshot-only output.

### 5.4 Output C: Raw stats history

Player-facing label:

```text
Raw stats history (.csv)
One row per governor per source date
```

History choices:

```text
30 | 60 | 90 | 180 | 360 days
```

Contract:

- Preserve the existing raw Stats headers/order unless audit proves a field defect.
- Apply the exact selected window.
- Extend spreadsheet formula safety to user-controlled text such as Governor and Alliance names.
- Preserve typed numbers, integral Governor IDs, ISO-style dates, null handling, and stable sort.
- Preserve `stats_<safe_display_name>_<UTC timestamp>.csv` unless compatibility evidence says otherwise.

### 5.5 Exact history-window semantics

Use one tested helper for workbook and raw CSV:

```text
latest_date = maximum valid AsOfDate in the authorised fetched dataset
start_date = latest_date - (requested_days - 1 calendar days)
include rows where start_date <= AsOfDate <= latest_date
```

Rules:

- A 90-day request spans exactly 90 inclusive calendar dates.
- Source gaps can produce fewer represented dates; never invent rows.
- Filter before final row counts and metadata.
- Use the same boundary for `ALL_DAILY`, account tables, charts, Forts period sums, and raw CSV.
- Validate days against the approved set at the service boundary.

### 5.6 Forts and period metrics

- Remove the hidden fixed 180-day Forts rule from other requested periods.
- Selected-period Forts summaries use the selected window.
- Lifetime/cumulative fields remain lifetime only when labelled explicitly.
- Never place selected-window sums, current snapshots, and lifetime values under one ambiguous label.

### 5.7 Google Sheets wording

Do not present Google Sheets as a separate generated format while it produces the same workbook.
Use one option:

```text
Full workbook (.xlsx) - Excel / Google Sheets compatible
```

Instructions may explain Drive upload. Phase 5G does not create or share a live Google Sheet.

### 5.8 Follow-up metadata

Successful output must report only truthful applicable fields, including:

- output kind;
- authorised distinct governor count;
- current snapshot rows where applicable;
- actual history rows written where applicable;
- exact history start/end and requested days;
- Stats freshness;
- Inventory freshness/coverage where applicable;
- full generated UTC timestamp.

Remove every footer or instruction saying `/my_stats_export` remains available.

### 5.9 Privacy and revalidation

- Every output is private/ephemeral.
- Re-resolve the active account registry at Download execution.
- Build one immutable authorised context and use the same distinct Governor IDs for that request.
- Duplicate IDs remain visible as Account Summary data-quality state but must not duplicate history
  queries or portfolio totals.
- Reject foreign, stale, expired, superseded, and forged interactions.
- Validate output kind, days, paths, filenames, and worksheet names at service boundaries.

## 6. Scope

### In Scope

- Remove `/me exports` and `/my_stats_export` registrations.
- Reduce command baselines to 38 top-level and 7 `/me` subcommands.
- Remove all Exports navigation, custom IDs, callbacks, page branches, fallback copy, and retry copy.
- Replace Account Summary `Download CSV` with `Download data`.
- Add one private Account Data options view for Full workbook, Current snapshot, Raw history, Days,
  Download, and Cancel.
- Add a typed Account Data export service/model boundary.
- Reuse Account Summary payload/export for current snapshot.
- Reuse and correct Stats DAL/export builders for history.
- Add `ACCOUNT_SUMMARY` first and replace partial `INDEX`, subject to dependency escalation.
- Correct date windows, counts, Forts, formula safety, freshness, labels, instructions, telemetry,
  filenames where approved, and cleanup.
- Remove directly orphaned Exports-only code/assets/tests after zero-caller proof.
- Update command governance, programme, deferred, README, briefing, task indexes, tests, and smoke docs.
- Validate `dbo.vDaily_PlayerExport` read-only.
- Produce deterministic output-shape/golden-contract evidence.

### Out of Scope

- `/my_stats` runtime redesign, migration, removal, redirect, or visual change.
- Creating `/me stats` in Phase 5G.
- A dashboard Export Stats action or selected-governor Stats export.
- Changes to Resources/Speedups/Materials report-page exports.
- Central or all-governor Inventory export.
- SQL changes or deployment.
- Live Google Sheets API creation/upload.
- ZIP bundles as the primary journey.
- New account/profile/inventory metrics.
- Registry authority, slots, ownership, claim, or Account Management changes.
- Broad cross-domain export redesign.
- Broad generic renderer/view consolidation beyond direct zero-caller cleanup.
- Removal of any other legacy command.

## 7. Source Deferred Items

### Deferred Optimisation
- Area: `commands/stats_cmds.py`, `commands/me_cmds.py`, Player Self-Service docs/tests
- Type: cleanup
- Description: `/my_stats_export` is redirect-only with discarded options and `/me exports` is a one-action page duplicating the new Account Summary download purpose.
- Suggested Fix: Remove both in Phase 5G, move downloads to Account Summary, update command governance, and resync commands.
- Impact: high
- Risk: medium
- Dependencies: Phase 5F accepted; operator approval recorded here.

### Deferred Optimisation
- Area: Stats export service/builders and Account Summary export
- Type: consistency
- Description: filtering, counts, summary sheet, Forts period, safety, freshness, and format labels are inconsistent or misleading.
- Suggested Fix: Apply this pack's exact output contract with focused and golden-file tests.
- Impact: high
- Risk: medium
- Dependencies: current SQL view contract; no SQL change.

### Deferred Optimisation
- Area: generic Player Self-Service Exports page/card lifecycle
- Type: architecture
- Description: Exports is the final supported caller of older generic page-card behavior.
- Suggested Fix: Remove direct zero-caller artifacts in Phase 5G; keep broader consolidation separate.
- Impact: medium
- Risk: medium
- Dependencies: command/page removal and focused lifecycle proof.

## 8. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | `use` | Multi-layer command, view, service, DAL, exporter, file, docs, and deletion scope. |
| `k98-discord-command-feature` | `use` | Removes commands/navigation and adds a private component workflow. |
| `k98-sql-validation` | `use` | Read-only view/column/date/dependency validation; no SQL diff. |
| `k98-test-selection` | `use` | Command, privacy, date, file-shape, cleanup, and regression risk. |
| `k98-deferred-optimisation-capture` | `use` | Capture unrelated export, generic-view, or `/my_stats` debt. |
| `k98-pr-review` | `use` | Required before mirror handoff. |
| `k98-promotion-check` | `use later` | After PR validation and operator smoke. |
| `k98-security-review-routing` | `use` | Bot Changes review, Deep Off; SQL documented skip if unchanged. |

### Security Review Decision

| Repository | Decision | Target | Expected setup / execution | Evidence |
|---|---|---|---|---|
| `K98 bot mirror` | `Changes review` | Final Phase 5G base..head or staged patch | `Changes + Deep Off` | Pending final diff; record exact target, snapshot, coverage, and result. |
| `K98 SQL Server` | `documented skip` | Read-only inspection of `dbo.vDaily_PlayerExport` and dependencies | `Not applicable` | Expected because no SQL diff or runtime SQL change is approved. Re-route if scope changes. |

Bot review focus:

- IDOR/account-linkage revalidation;
- private response boundaries;
- forged/stale/expired components;
- formula injection;
- path/filename/worksheet safety;
- date/governor over-export;
- duplicate Governor IDs;
- cleanup and exception handling;
- telemetry avoiding private row values.

Do not start a standard or deep codebase audit without a separate explicit operator request.

## 9. Mandatory Workflow

1. Audit and scope review, then stop for approval.
2. Record provisional security routing and exact intended target; do not start the scan.
3. Validate architecture, SQL contract, output compatibility, and exact manifest, then stop.
4. Present implementation plan, resync order, output migration, tests, and rollback, then stop.
5. Implement only after approval.
6. Run focused, output-shape, full, command, architecture, deferred, log-noise, and import validation.
7. Execute final bot Changes review with Deep Off and record SQL skip evidence.
8. Complete K98 PR review and mirror PR.
9. Complete operator Discord smoke.
10. Run promotion check, promote exact accepted patch, deploy/restart, resync commands, and verify.

One-pass execution is not approved.

## 10. Audit Requirements

### Command surface

Confirm exact registrations, decorators, versions, tests, docs, caches, and before/after counts for:

- `/me exports`;
- `/my_stats_export` and its discarded options;
- `/my_stats`, which must remain unchanged;
- current `39 / 8 / 2` and target `38 / 7 / 2`;
- every validator/canonical table/smoke reference;
- command resync and rollback resync.

### Navigation and page surface

Map every Exports button/import/custom ID from:

- governor dashboard;
- Accounts, Reminders, Preferences;
- Account Summary and child views;
- fallbacks and tests.

Classify `PAGE_EXPORTS`, `build_exports_embed`, generic renderer/card branches, `ExportStatus`, the
Exports asset, the Stats-only export view, and tests as delete/modify/retain with caller evidence.

### Account Summary host

Confirm:

- immutable authorised payload lifecycle;
- current sections, pagination, timeout, and parent-message ownership;
- current Download CSV callback and exact 29-column mapping;
- safe child-window pattern;
- active registry revalidation helper;
- current Stats and Inventory freshness semantics.

### Stats export service/DAL/builders

Map:

- registry resolution and distinct IDs;
- `stats_export_dal` query and order;
- source date/null handling;
- temporary files and telemetry;
- service result metadata;
- CSV/workbook builders and every caller;
- non-Player-Self-Service consumers;
- downstream dependencies on filenames, headers, sheet names, or full history.

### Workbook audit

Document current and target behavior for README, INDEX, ALL_DAILY, account tabs, KPI periods,
MTD/last-month comparisons, Forts, sparklines, charts, daily tables, sheet names, links, sparse data,
and XlsxWriter/openpyxl behavior. If fallback engines cannot meet one full-workbook contract, fail
clearly or make them equivalent rather than silently degrading output.

### Spreadsheet safety

Audit every user-controlled text field in CSV/XLSX, including registered/current names, alliance,
role/slot where external, civilisation/VIP labels, filenames, and worksheet names. Protect text
formula prefixes without corrupting typed negative numeric values.

### Documentation

Find every active statement that advertises either removed command, says Phase 5G is undecided,
defines Phase 6 as dashboard Export Stats, lists Exports in `/me`, reports the old target counts, or
retries through `/me exports`. Preserve accurate historical archive records.

## 11. Architecture Targets

| Concern | Target |
|---|---|
| Commands | Remove registrations; no replacement command in Phase 5G. |
| Views | Account Summary owns the entry button; a dedicated Account Data option view owns interaction state only. |
| Service | Typed Account Data service owns revalidation, output validation, exact window, builder coordination, metadata, telemetry, and cleanup. |
| Snapshot | Reuse `AccountsPortfolioPayload` and `accounts_export.py`. |
| History | Reuse Stats DAL and corrected exporters. |
| Helpers | Narrow exact-window, safe-text, safe filename/sheet, and cleanup helpers only where contracts match. |
| SQL | Read-only validation; no SQL in command/view code and no SQL diff. |
| Tests | Command, view, service, window, file-shape, safety, cleanup, and regression suites. |

Recommended concepts:

```text
AccountDataExportKind
- FULL_WORKBOOK
- CURRENT_SNAPSHOT_CSV
- RAW_HISTORY_CSV

AccountDataExportRequest
- discord_user_id
- display_name
- output_kind
- history_days when applicable
- entry_point = account_summary

AccountDataExportContext
- authorised AccountsPortfolioPayload
- distinct authorised governor_ids
- generated_at_utc

AccountDataExportFile
- owned path/bytes and temp directory
- filename and output kind
- governor_count
- snapshot/history row counts
- requested days and exact dates
- Stats and Inventory freshness
- instructions and telemetry
```

Views must not assemble dataframes, calculate windows, choose SQL columns, or build workbooks.

## 12. Likely Files

### Review

- `commands/me_cmds.py`
- `commands/stats_cmds.py`
- `scripts/validate_command_registration.py`
- `ui/views/player_self_service_views.py`
- `ui/views/player_self_service_governor_dashboard_views.py`
- `ui/views/player_self_service_account_summary_views.py`
- `ui/views/player_self_service_export_views.py`
- `player_self_service/accounts_models.py`
- `player_self_service/accounts_service.py`
- `player_self_service/accounts_export.py`
- `player_self_service/service.py`
- `player_self_service/page_cards.py`
- `services/stats_export_service.py`
- `stats/dal/stats_export_dal.py`
- `stats_exporter.py`
- `stats_exporter_csv.py`
- relevant tests and active docs
- SQL repository source for `dbo.vDaily_PlayerExport`

### Modify - expected

- command and validator files above;
- dashboard/generic/Account Summary views;
- Account snapshot and Stats export service/builders;
- canonical command reference and platform audit;
- programme, deferred, README, briefing, task indexes, tests, and smoke docs.

### Create - recommended, subject to architecture approval

- `player_self_service/account_data_export_models.py`
- `player_self_service/account_data_export_service.py`
- `ui/views/player_self_service_account_data_export_views.py`
- focused service/view tests.

### Delete - only after zero-caller proof

- `ui/views/player_self_service_export_views.py`;
- Exports-only generic card/asset/tests;
- redirect-only `/my_stats_export` tests;
- obsolete Exports status/summary code.

Do not delete shared modules because their names look old; prove retained callers first.

## 13. Implementation Requirements

- Keep commands and views thin.
- Re-resolve active linked accounts at Download execution and build one immutable context.
- Reuse Accounts snapshot mapping; keep raw history SQL in the Stats DAL.
- Put exact window calculation in one tested pure helper.
- Filter before row counts and metadata.
- Use a validated output-kind enum, not free-form format strings.
- Disable/mark days not applicable for snapshot output.
- Use injected UTC time in service tests and filenames.
- Extend formula safety to historical text while keeping numeric values typed.
- Keep filenames/sheets safe and handle truncated-name collisions.
- Ensure hyperlinks target final unique sheet names.
- Close every workbook, stream, Discord file, temp file, and directory on every path.
- Do not log row content, coordinates, names, or exported values.
- Remove command registrations and navigation in the same deployable patch.
- Update expiry/retry copy to the canonical Account Summary route.
- Capture unrelated debt as deferred; keep security findings in the security workflow.

### Command Surface Governance

- [ ] Record `39 -> 38` top-level, `/me 8 -> 7`, `/inventory 2 -> 2`.
- [ ] Remove `my_stats_export` from `APPROVED_TOP_LEVEL_COMMANDS`.
- [ ] Remove `/me exports` from grouped expectations and canonical tables.
- [ ] Preserve `/my_stats` decorators, version, channel gate, telemetry, and behavior.
- [ ] Preserve `/inventory import` and `/inventory audit`.
- [ ] Update cache/resync and smoke instructions.
- [ ] Run command registration, inventory, and smoke tests.

## 14. Refactor Decisions

| Issue | Decision | Reason |
|---|---|---|
| Duplicate download homes | `fix now` | Locked canonical Accounts journey. |
| Redirect-only `/my_stats_export` | `fix now` | No permanent redirect-only commands. |
| Date filtering and row metadata | `fix now` | User-visible correctness. |
| Partial INDEX | `fix now` | Account Summary is the accepted current portfolio contract. |
| Fixed 180-day Forts | `fix now` | Hidden semantic mismatch. |
| Fake separate Google Sheets format | `fix now` | Misleading format contract. |
| Stats CSV formula safety | `fix now` | Output safety and consistency. |
| Exports-only generic artifacts | `fix now after proof` | Direct orphan created by route removal. |
| Broader generic consolidation | `defer` | Not required for approved outcome. |
| `/my_stats` redesign | `defer to Phase 6` | Separate product and migration decisions. |
| Cross-domain export redesign | `defer` | Distinct owners/contracts. |
| Live Google Sheets API | `defer` | Requires auth, ownership, sharing, and retention design. |

## 15. Testing Requirements

### Command/navigation

- removed commands no longer register;
- `/my_stats` remains unchanged;
- `/me` exact seven subcommands and `/inventory` exact two;
- no Exports button/custom ID remains;
- removed commands disappear after resync.

### Download data view

- author can open from every Account Summary section/page;
- foreign/expired/stale/superseded interactions denied;
- Full workbook default and 90 days default;
- snapshot makes Days not applicable;
- Cancel sends no file;
- no rows/setup guidance;
- registry unavailable/no Stats/builder failures private and truthful;
- unlink/relink between opening and Download cannot over-export.

### Exact windows

For 30/60/90/180/360 verify latest included, start = latest - days + 1, prior date excluded, workbook
and CSV match, gaps do not invent rows, invalid days rejected, and date normalisation is timezone-safe.

### Snapshot CSV

- exact 29 headers/order/values;
- formula safety and UTF-8 behavior;
- stable filename;
- no history query.

### Raw history CSV

- stable headers/order;
- exact filter/count/sort;
- formula-safe text without changing negative numbers;
- integral IDs and safe null/NaN/Inf handling;
- safe filename and telemetry.

### Full workbook

- ACCOUNT_SUMMARY, README, ALL_DAILY, then account sheets;
- INDEX removed unless approved compatibility escalation;
- snapshot values match snapshot CSV;
- links/sheet names safe and unique;
- every history table and chart uses exact window;
- Forts uses selected period;
- sparse/one-point/no-data behavior truthful;
- supported engine opens without repair warnings;
- same workbook for Excel/Google Sheets compatibility.

### Follow-up/cleanup

- actual rows and exact dates;
- separate Stats and Inventory freshness;
- exact generated UTC;
- no legacy footer;
- every success/failure/send/cancel/cancellation path cleans owned resources exactly once;
- telemetry failure does not fail a successful download.

### Regression

- Account Centre and Account Summary visuals unchanged;
- Manage Accounts/Update VIP unchanged;
- dashboard and direct Inventory reports unchanged;
- report-page Inventory exports unchanged;
- Reminders/Preferences unchanged apart from Exports nav removal;
- `/my_stats` slices/selectors/charts/channel gate/telemetry unchanged;
- no SQL write.

Suggested gates:

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

Generate and inspect representative one/five/many-account, duplicate-ID, long/Unicode/formula-name,
sparse, 30-day, 360-day, snapshot-only, no-data, and registry-failure outputs.

## 16. Acceptance Criteria

- [ ] `/me exports` and `/my_stats_export` are removed, not redirected.
- [ ] `/my_stats` is unchanged and handed to Phase 6.
- [ ] Counts are 38 top-level, 7 `/me`, 2 `/inventory`.
- [ ] No Exports navigation/control remains.
- [ ] `/me accounts -> Account Summary -> Download data` is the only central download journey.
- [ ] Accepted Accounts/Account Summary visual output is unchanged.
- [ ] Full workbook default; current snapshot and raw history remain separate grains.
- [ ] Account Summary is first workbook sheet.
- [ ] Exact N-day filter is used everywhere.
- [ ] Actual written counts/dates and separate freshness are reported.
- [ ] Forts uses selected period.
- [ ] Formula safety covers CSV/XLSX text.
- [ ] Google Sheets is compatibility wording, not a separate file.
- [ ] Active account revalidation occurs at Download.
- [ ] No new SQL or direct SQL in commands/views.
- [ ] All temporary resources clean up on every path.
- [ ] Direct orphans are removed only after caller proof.
- [ ] Focused/full/golden/command/pre-commit/log/architecture/deferred/security-routing gates pass.
- [ ] SQL read-only evidence, final Changes review, K98 PR review, and operator smoke are recorded.
- [ ] Commands are resynced after deployment.

## 17. Deployment And Rollback

### Deployment

1. Promote the exact accepted bot patch.
2. Deploy/restart normally.
3. Resync application commands so both removed routes disappear.
4. Verify counts and exact `/me` list.
5. Smoke all three Account Summary outputs.
6. Smoke `/my_stats` unchanged.
7. Smoke all three Inventory report-page exports unchanged.
8. Monitor export errors, cleanup warnings, and player feedback.

No SQL deployment is part of Phase 5G.

### Rollback

Rollback restores the prior accepted Phase 5F bot patch and registrations together, resyncs commands,
and verifies the old Stats-only `/me exports` path. It must not restore any central Inventory export
removed in Phase 5F. Generated downloads require no data migration or rollback transformation.

## 18. Required Delivery Output

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. Deleted Files And Zero-Caller Evidence
6. SQL Validation / SQL Changes
7. Helpers Reused
8. Output Contract Changes
9. Refactor Findings
10. Tests And Results
11. Security Decision And Evidence
12. Command Counts And Resync
13. Deployment
14. Rollback
15. Deferred Optimisations

## 19. PR Summary Template

```md
## Summary

- make `/me accounts -> Account Summary -> Download data` canonical
- remove `/me exports` and `/my_stats_export`
- add snapshot CSV, raw history CSV, and Account-Summary-first full workbook
- correct date windows, counts, Forts, safety, freshness, and Sheets labelling
- leave `/my_stats` for Phase 6 and preserve Inventory report-page exports

## Tests

- <focused commands/views/services/exporters>
- <golden/output-shape validation>
- <full suite, pre-commit, and repository validators>

## SQL Changes

- None; `dbo.vDaily_PlayerExport` and dependencies validated read-only.

## Security Review

- Decision: `Changes review`
- Repository / target: `<bot base..head>`
- Expected setup / execution: `Changes + Deep Off`
- Evidence: `<scan, snapshot, coverage, result>`
- SQL repository: `documented skip` because no SQL diff exists

## Risk / Rollback

- Main risks are over-export, workbook compatibility regression, and incomplete route removal.
  Rollback restores the prior bot patch and resyncs commands while retaining Phase 5F Inventory
  retirements.
```

## 20. Phase 6 Handoff

After Phase 5G acceptance, Phase 6 becomes:

```text
Interactive Personal Stats Experience And /my_stats Migration
```

Phase 6 separately decides the future `/me stats` path, channel/private behavior, ALL/account selector,
Yesterday/WTD/last-week/MTD/last-month/3M/6M semantics, presentation, performance, communication, final
`/my_stats` removal rather than a permanent redirect, resync, smoke, and rollback. Personal downloads
remain owned by Account Summary.
