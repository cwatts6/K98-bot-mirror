# Codex Task Pack — KVK Source Migration S2B SQL Publication State

## Current prerequisite handoff — 2026-09-10

S2A is accepted and merged: SQL PR #78 at `845a25fe66b1d2365fb38720390b4dadf50baa67`,
mirror PR #264 at `9fc0255dbaa0cbcb80c63c563657dad90bd5bcec`. Final review fixes passed
401 static assertions and 96 disposable rejection cases with twelve-table rollback. Read the
[S2A delivery](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S2A%20SQL%20Observation%20Facts.md)
and [local SQL development reference](../reference/local_sql_development.md).

Observed local clean-main anchors before this documentation refresh: bot
`58fc307935fdf1cfecdde839670ce5439f11baac` (tree matches accepted mirror merge), SQL
`845a25fe66b1d2365fb38720390b4dadf50baa67`. Reverify at execution; preserve newer work.
The older planning anchors below are historical, not checkout targets.

**S2B G3 remains pending.** Local instance `9SX2VF4\K98DEV` is available for future development;
its service is Manual and was stopped at the 2026-09-10 check. Existing
`K98_S2A_Disposable_20260909` is retained S2A evidence, not automatic S2B authorization.
Proposed separate target: `9SX2VF4\K98DEV` / `K98_S2B_Disposable_20260910` (not created).
The operator must explicitly authorize that exact target and S2B before creation/execution.
Then install accepted S2A prerequisites into the fresh target before testing the S2B migration;
do not reopen predecessor implementation or execute predecessor task packs automatically.
Recheck the S2B migration date/sequence before authoring; keep the approved file/test manifest
unless an explicitly explained date/sequence correction is required. No production execution.

## 1. Task Header

- Prepared 2026-09-09; owner Chris Watts; Phase 2B specification.
- G2 architecture approved, including authorized EndScanID corrections. **S2B G3 pending.**
- One-pass implementation approved: **No**. Execute only after explicit approval of this slice.
- Proposed isolated branch `codex/kvk-source-s2b`; not created during planning.
- Type: SQL implementation.

## 2. Required Reading

Read current AGENTS.md, README-DEV.md, docs/reference/README.md and its required core references,
the canonical task template, root/applicable SECURITY.md and relevant skills. Then read the
[approved contract](../reference/kvk_source_migration/phase_2_contract_and_architecture.md),
[implementation plan](../reference/kvk_source_migration/phase_2_implementation_plan.md),
[70 scenarios](../reference/kvk_source_migration/phase_2_acceptance_scenarios.md), latest programme/
register updates and this pack. User decisions override historical missing-B0/G2-pending wording.
For SQL-facing work read authoritative SQL instructions, sql_schema/README.md, migrations/README.md,
SQL_DATA_MIGRATION_GUARDRAILS and exact relevant snapshots. No inferred schema from Python alone.

## 3. Objective

Persist configuration versions, endpoint requests, immutable publications, disabled source routing and delivery receipts.

## 4. Background

Planning anchors: bot main `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; SQL main
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`. Recheck branches/HEADs/remotes/status at execution,
preserve existing work and record actual start/end hashes. Local definitions are not deployed proof.
No pull/reset/checkout to make a working copy match historical evidence. Use an authorized isolated
branch/worktree where needed. Phase-1 C01-C65 anchor dependencies; G2 fixes source semantics.

## 5. Scope

Predecessors: S2A accepted and S2B G3; explicit disposable SQL target for FK/state checks.

Only the section 11 manifest and requirements below. No generic refactor, WS1 reliability repair,
daily SCANORDER change, legacy backfill or independent stats/targets/history/profile migration.
No private workbook/player-row fixtures. No provider-formula or unavailable later-fight request.
This pack alone never authorizes pull/reset/merge/push/PR, live SQL, real imports/exports, Discord
actions, restarts, deployment or activation. Code validation uses mocks or explicit disposable SQL.
S6 additionally stops at G4 before any live action. No automatic next slice.

## 6. Source Deferred Items

Not derived from deferred work. Known legacy export grouping/summation and ProcConfig WS1 debt
remain separate. Capture only newly evidenced unrelated non-security debt in canonical format.

## 7. Codex Skills To Use

Architecture-scope, test-selection, security-review-routing and final PR-review apply. SQL-validation
applies to SQL-facing contracts. Discord-command-feature applies to S4A/S5A/S5B interaction work.
Promotion-check applies only when S6 reaches separately authorized G4 review. Deferred-capture and
spreadsheet inspection are conditional; no subagents required.

### Security Review Decision

Current pack authoring: bot docs-only skip; SQL no-change skip. Future execution: Bot no-change skip; SQL Changes review for this exact migration/snapshot/validator diff, Deep off.
Use k98-security-review-routing first; record exact immutable base/head or task-only authored patch,
Scan type Changes and Deep off. Never scan/stage unrelated dirty files or combine bot/SQL histories.
No routine standard/deep audit. Retain scan coverage/results privately; no public finding details.

## 8. Mandatory Workflow

1. Confirm explicit S2B approval and predecessor evidence; otherwise scope/review and stop.
2. Capture worktrees and exact manifest; recheck drift and source/SQL contracts before edits.
3. Implement only the approved boundary with assigned tests; preserve unrelated work.
4. Run checks, review exact diff/security target and report actual outcomes/limitations.
5. Stop at delivery; no automatic next task, G4 action or self-approval.

## 9. Focused Audit Requirements

Inspect section 11 read paths for helper semantics, layering, period/identity/availability and
regression contracts. Static source continuity does not prove current live rows/jobs or external
readers. Operator-attested SQL/config parity remains separately labelled. No credential discovery
or RDP required for this planning/implementation boundary. Evidence condition: Disposable SQL required for constraints. Active production config/jobs remain later readiness evidence.

## 10. Architecture Targets

kvk/models and kvk/schemas own pure types; kvk/services business rules; kvk/dal parameterized SQL,
transactions and mapping; commands/routes/views thin adapters. New SQL only in the SQL repository.
Follow the implementation-plan interfaces/lock order and approved source/field dictionary.
No second domain implementation in DL_bot.py or gsheet_module.py; no duplicated SQL calculation.

## 11. Exact File Manifest

All paths below are relative to **C:/K98-bot-SQL-Server**.
New files are proposed, not present yet; predecessor-created modifications require accepted delivery.
No wildcard authorizes extra files. Append implementation evidence to this pack after execution;
do not rewrite unrelated indexes. Migration date/sequence is the sole controlled allocation exception
in implementation-plan section 4; final name must be recorded before authoring and never renamed after merge.

### Read only

- `sql_schema/KVK.KVK_Windows.Table.sql`
- `sql_schema/KVK.KVK_DKPWeights.Table.sql`
- `sql_schema/KVK.KVK_CampMap.Table.sql`
- `sql_schema/dbo.ProcConfig.Table.sql`
- `migrations/README.md`

### Create

- `migrations/20260909_002_kvk_source_publication_state.sql`
- `sql_schema/KVK.SourceConfigVersion.Table.sql`
- `sql_schema/KVK.SourceWindowConfig.Table.sql`
- `sql_schema/KVK.SourceCampConfig.Table.sql`
- `sql_schema/KVK.SourceWeightConfig.Table.sql`
- `sql_schema/KVK.SourcePeriod.Table.sql`
- `sql_schema/KVK.SourceScanBinding.Table.sql`
- `sql_schema/KVK.SourceConfigRequest.Table.sql`
- `sql_schema/KVK.SourcePublication.Table.sql`
- `sql_schema/KVK.SourcePlayerResult.Table.sql`
- `sql_schema/KVK.SourceSelection.Table.sql`
- `sql_schema/KVK.SourceRouting.Table.sql`
- `sql_schema/KVK.SourceAction.Table.sql`
- `sql_schema/KVK.SourceDelivery.Table.sql`
- `deploy/Test-KvkSourcePublicationContracts.ps1`
- `validation/kvk_source/publication_constraints.sql`

### Modify

- `sql_schema/KVK.SourceAggregateReport.Table.sql`

## 12. Implementation Requirements

Create exactly thirteen S2B tables in plan section 4. Modify only S2A SourceAggregateReport snapshot to add same-source/KVK period FK after validation, without orphan deletion/backfill. Mirror Windows/Map structures in new config tables; existing sheets/tables unchanged.
SourceSelection has same-scope publication FK and monotonic version; SourceRouting.Enabled defaults false. Completeness/hash/counts require S3B transaction validation, not status flag alone. Request idempotency includes base config so 13-to-14-to-13 is a new action. Old versions remain immutable.
Nullable result metrics carry statuses; DKP decimal(38,6), weight decimal(38,12) plus source round-trip strings. Aggregate values remain immutable report references. Actions retain provenance and SourceDelivery stores owner/fence/pending/uncertain/confirmed receipts.
Static validator and rollback-only disposable SQL cover source/period FKs, duplicate generations, disabled defaults, absent-end retention, exact numeric ranges and retained history. No new procedures, grants or activation. Runtime CAS/concurrency remains S3B/S4B responsibility.

All slices retain B0 eligibility/attribution, exact endpoints, total-deaths player DKP and supplied
aggregate authority. Interim 11−10 then 12−10; EndScanID=13 gives 13−10; authorized update to 14
is itself correction authority for 14−10 without a second command. Pending desired endpoint cannot
label an older result current/final. It does not authorize weight/map/roster/source-content changes.
Daily namespaces remain separate; aggregate uploads/re-exports do not allocate a new player scan.

### Command Surface Governance

No command count change. Preserve permission/visibility/version/usage identity. Run or justify skipping actual command inventory/registration based on touched surfaces.

## 13. Refactor Decisions

Only new-source extraction and adapters in this manifest. Retain legacy behavior while preventing
its null-to-zero, upload-time, growing-roster and aggregate-recalculation rules leaking into new
source. No generic exporter/ProcConfig cleanup. Inspect helper semantics before reuse; expanding
the manifest requires bounded review, not opportunistic refactoring.

## 14. Testing Requirements

Scenario ownership: Storage foundations T29/T31/T43/T45/T47-T54/T65/T69-T70.

- Run new deploy/Test-KvkSourcePublicationContracts.ps1 and explicit-repo Validate-SqlRepo.ps1 after reviewing log effects.
- Run listed synthetic constraint SQL only in an authorized disposable database; static pass is not transaction proof.

For bot code run architecture/deferred/security-routing validators and test selector with exact
paths, applicable pre-commit on task files, focused tests and justified broader checks. S4/S5
shared integrations require full pytest and scripts/analyse_pytest_log_noise.py. S1/S3A may
justify focused-only. No historical suite result is a fresh pass. Safe smoke/registration uses
test environment; SQL tests never use default production targets. Static regex checks do not
prove transactions/concurrency. Report blocked integration separately; never substitute live SQL.

## 15. Acceptance Criteria

- [ ] Explicit slice approval and prerequisites; exact manifest and preservation verified.
- [ ] Assigned scenarios pass with actual evidence, including applicable failure/restart/permission cases.
- [ ] Legacy and independent sources preserved; no wrong period, zero fallback or precision loss.
- [ ] Exact per-repo security targets reviewed or precise skip justified.
- [ ] Remaining integration/live limits explicit; no automatic next slice or live action.

## 16. Required Delivery Output

Use canonical eleven parts: Summary; File Manifest; New Files; Modified Files; SQL Changes;
Helpers Reused; Refactor Findings; Test Plan with outcomes; Security Review Decision and Evidence;
Deployment Steps (none unless separately approved); Deferred Optimisations.

Rollback: Retain new tables disabled; never drop foundation data or alter legacy config. Later source-aware selection rollback requires validated service.

## 17. Proposed PR Summary

Describe concrete behavior, exact manifest, actual tests/security target, dependencies and rollback
limits. Keep private player rows/credentials/findings out of Git. No PR creation authorized by
preparation. End with slice status and next required gate.

**Prepared only. S2B G3 pending; no implementation executed.**

### S2B G3 and pre-edit evidence — 2026-09-10

Chris Watts explicitly approved S2B only, including local server `9SX2VF4\K98DEV` and
fresh `K98_S2B_Disposable_20260910`, compatibility 160, `Latin1_General_CI_AS`, accepted
S2A prerequisite installation and synthetic validation. This supersedes historical G3-pending
wording for S2B only. Stop after implementation/validation for review; no PR or later slice.

Pre-edit verification: bot main `58fc307935fdf1cfecdde839670ce5439f11baac` and SQL main
`845a25fe66b1d2365fb38720390b4dadf50baa67` match their remote main hashes. GitHub confirms
SQL #78 and mirror #264 merged at 07:27:22 and 07:27:43 UTC respectively; bot HEAD and
mirror merge `9fc0255dbaa0cbcb80c63c563657dad90bd5bcec` share tree
`4b8a9ea85f0a6d325c60dd2c83ea54786a3a3322`. S2A final evidence is 401 static assertions,
96 disposable rejections and twelve-table rollback, with the separate final five-file Changes
review supplementing its original fifteen-file review. These are accepted historical outcomes.
SQL was clean; bot had twelve modified documents plus untracked `local_sql_development.md`.
Initial preservation hashes cover 2,261 files. Existing documentation updates must accompany a
later authorized PR; no staging or PR is authorized now.

The local service is already running; no start/restart required. Readback verifies local engine
16.0.1200.5, retained S2A database at the required collation/compatibility, S2B database absent.
Controlled migration allocation before authoring: replace the proposed section 11 create path
`migrations/20260909_002_kvk_source_publication_state.sql` with
`migrations/20260910_001_kvk_source_publication_state.sql`. Actual date is 2026-09-10 and no
migration occupies that date/sequence. Every other SQL manifest path is unchanged.

Scope: thirteen additive state tables, one SourceAggregateReport period FK, static validator
and rollback-only fixture. No new procedure, grant, legacy modification or activation. Preserve
B0, exact UTC endpoints, semantic deduplication, interim 11-10 then 12-10, final 13-10 and
normal authorized endpoint correction to 14-10; aggregate and daily namespaces stay separate.
S3B/S4B retain immutable-write, completeness, CAS, transition and delivery-concurrency duties.
Security routing: exact task-only SQL patch from the recorded SQL HEAD, Changes, Deep off;
bot appendix is a separate documentation-only skip. Static and disposable SQL checks are
required; no runtime Python change warrants pytest, command registration or startup execution.

### S2B implementation delivery — 2026-09-10

#### 1. Summary

S2B storage implementation and authorized local constraint validation are delivered for operator
review. Thirteen additive tables persist configuration, desired endpoint requests, publication
generations, nullable player results, source selection/routing and delivery evidence. Routing
defaults disabled. S2A history, legacy SQL, bot runtime and all existing documentation work are
preserved. No successor slice or operational activation is approved by this delivery.

Both repositories are on `codex/kvk-source-s2b`, created from the verified current main HEADs.
No commits were created: bot start/end HEAD is `58fc307935fdf1cfecdde839670ce5439f11baac`;
SQL start/end HEAD is `845a25fe66b1d2365fb38720390b4dadf50baa67`. Remotes are unchanged.

#### 2. File Manifest

Exactly seventeen SQL paths, relative to `C:/K98-bot-SQL-Server`:

| Change | Exact path |
|---|---|
| Create | `migrations/20260910_001_kvk_source_publication_state.sql` |
| Create | `sql_schema/KVK.SourceConfigVersion.Table.sql` |
| Create | `sql_schema/KVK.SourceWindowConfig.Table.sql` |
| Create | `sql_schema/KVK.SourceCampConfig.Table.sql` |
| Create | `sql_schema/KVK.SourceWeightConfig.Table.sql` |
| Create | `sql_schema/KVK.SourcePeriod.Table.sql` |
| Create | `sql_schema/KVK.SourceScanBinding.Table.sql` |
| Create | `sql_schema/KVK.SourceConfigRequest.Table.sql` |
| Create | `sql_schema/KVK.SourcePublication.Table.sql` |
| Create | `sql_schema/KVK.SourcePlayerResult.Table.sql` |
| Create | `sql_schema/KVK.SourceSelection.Table.sql` |
| Create | `sql_schema/KVK.SourceRouting.Table.sql` |
| Create | `sql_schema/KVK.SourceAction.Table.sql` |
| Create | `sql_schema/KVK.SourceDelivery.Table.sql` |
| Create | `deploy/Test-KvkSourcePublicationContracts.ps1` |
| Create | `validation/kvk_source/publication_constraints.sql` |
| Modify | `sql_schema/KVK.SourceAggregateReport.Table.sql` |

Bot task-authored change: append-only evidence in this exact pack,
`docs/task_packs/Codex Task Pack - KVK Source Migration S2B SQL Publication State.md`.
The controlled migration date allocation above is the only manifest-name change.

#### 3. New Files

Sixteen SQL files listed above: one migration, thirteen snapshots, one offline PowerShell
validator and one guarded synthetic SQL fixture. No new bot files. Temporary authoring scripts,
guarded local SQL wrappers, transcripts, preservation hashes and security artifacts remain
outside Git. They contain synthetic evidence only.

#### 4. Modified Files

The aggregate snapshot retains its original table and selected-revision FK; the only added
executable statement is a trusted same-source/KVK/PeriodKey/PeriodKind FK to SourcePeriod.
This pack retains its complete pre-task byte prefix and appends authorization/delivery evidence.

Preservation verification covered 2,261 initial files: only these two approved existing paths
changed; the other 2,259 are byte-identical. Exactly sixteen new SQL paths exist and both staging
areas are empty. The twelve pre-existing modified bot documents and untracked
`docs/reference/local_sql_development.md` are preserved. Per operator instruction, those document
updates must be included when PR creation is separately authorized; no PR is created now.

#### 5. SQL Changes

The migration is one explicit transaction, joining an existing caller transaction without
committing it. Missing S2A prerequisites, occupied S2B names or untrusted constraints fail closed.
Because new SourcePeriod starts empty, existing aggregate families cannot already have matching
periods: the migration locks and rejects that condition before DDL rather than inventing periods,
deleting or backfilling data. Reference snapshots are not deployment entry points.

Scoped FKs bind configurations to rosters, windows to periods/configurations, bindings to the
separate player scan registry, publications to exact input/config references, results to eligible
roster members and configured camps, selections/actions/receipts to same-period publications,
and applied requests to the desired configuration. Config request uniqueness includes the base
configuration, allowing a distinct 13-to-14-to-13 action. Desired scan slots may remain absent.

Player numeric columns are nullable and have explicit case-sensitive field statuses; ranks carry
bounded cohorts. `power` and `troops_power` store signed endpoint deltas, `starting_power` is B0
power, and counter columns retain their S1 field names. DKP is `decimal(38,6)`; coefficients are
`decimal(38,12)` with separate source round-trip strings. Aggregate values are retained by
revision reference, never recalculated or copied into a second aggregate authority.

Storage checks do not establish a working publication service. S3B must validate exact
revision-to-scan and aggregate-to-period correspondence, B0 attribution, approved component
digests, normalized camp-key/name uniqueness and complete mapping scope, coefficient source
string agreement, representability before SQL conversion, row-set counts/digests, immutable
historical writes, monotonic updates and CAS under the approved lock order. S4B must implement
destination serialization, fence checks and uncertain-receipt reconciliation. Positive versions
and a `complete` flag alone are not proof of these later transaction/semantic invariants.

#### 6. Helpers Reused

Reused accepted S2A types, scoped-key conventions, BIN2 status checks, snapshot/migration
comparison and savepoint-rejection/rollback testing patterns. Used the existing explicit-repo
`deploy/Validate-SqlRepo.ps1`; its known effect is a local `logs/validation.jsonl` append.
No bot helper or legacy calculation/import path was changed or duplicated.

#### 7. Refactor Findings

New SQL remains in its owning repository; commands, views, DAL, services, startup and caches are
unchanged. No new direct SQL in interaction modules, generic exporter cleanup or ProcConfig/WS1
repair. S3B/S4B obligations above are planned slice boundaries, not completed S2B runtime claims.
No newly evidenced unrelated refactor item was established.

#### 8. Test Plan with Actual Outcomes

| Check | Actual outcome |
|---|---|
| Local target identity | `9SX2VF4\K98DEV`, SQL 16.0.1200.5; service already running, no start/restart |
| Create authorized S2B database | Passed; `K98_S2B_Disposable_20260910`, compatibility 160, `Latin1_General_CI_AS` |
| Install accepted S2A prerequisites | Passed; KVK schema and unchanged accepted S2A migration, no predecessor pack execution |
| Apply S2B migration | Passed, SQLCMD exit 0 |
| `deploy/Test-KvkSourcePublicationContracts.ps1 -RepoPath C:/K98-bot-SQL-Server` | Passed, 259 static assertions |
| `validation/kvk_source/publication_constraints.sql` | Passed, 131 expected rejections and 25-table rollback |
| Independent S2B catalog/row readback | 25 tables, 47 FKs, 165 CHECKs; all enabled/trusted, every table empty; zero user procedures/triggers |
| Separate S2A evidence readback | Unchanged 12 empty tables, 18 trusted FKs, 89 trusted CHECKs |
| `deploy/Validate-SqlRepo.ps1 -RepoPath C:/K98-bot-SQL-Server` | Passed, 0 errors, 15 existing migration warnings |
| Bot architecture/deferred/security-routing validators | Passed; no Python changes, no routing errors/warnings |
| Test selector with this exact pack path | Passed; suggested smoke/registration deliberately skipped as no bot runtime changed |
| Applicable document hooks | EOF, merge-conflict, large-file and final mixed-line-ending checks passed; trailing-whitespace hook selected no files |
| Source hygiene and secrets | Both Git diff checks passed; Gitleaks scanned the exact authored SQL bundle, no leaks |
| Preservation | Passed, 2,261 initial hashes checked; original pack prefix intact; seventeen SQL hashes match reviewed sources |

Positive storage cases retain interim endpoint generations 11-10 and 12-10, final 13-10, a pending
desired 14 while retaining the old publication/configuration, and replacement 14-10 with endpoint
request provenance. They retain the old publications and unchanged aggregate revision, allow
return-to-13 under a new base config, and record a rollback selection with increased version.
They also store negative power, valid zero DKP at zero B0 power, an unavailable power ratio,
fixed-point extrema, and claimed/uncertain/confirmed delivery evidence. These are synthetic
storage assignments, not execution of the future calculation/config import/publication workers.

Rejections cover source/season violations, unknown/mismatched FKs, duplicate versions/generations,
wrong selection periods, invalid endpoints/ranges, absent completion metadata, activation without
approval metadata, invalid receipt/fence state, later-only player IDs, wrong camp references,
metric null/status mismatches, status casing, invalid rank/cohorts and numeric overflow.

The initial fixture attempts rolled back after an overly specific constraint-order expectation:
SQL Server reported a dependent request FK before the expected window FK. The fixture now accepts
the appropriate integrity-error class for that multi-constraint mutation and reports unexpected
constraint names on specific cases; final 131-case execution passed. A temporary readback query
initially used reserved alias RowCount, then passed with a quoted alias. Neither required DDL fixes.
The document hook normalized only appended mixed line endings; original bytes remain intact.
Sandbox credential/cache restrictions were resolved through approved scoped elevated calls.

Python pytest, smoke imports, command inventory/registration, Python lint/type checks and pytest
log-noise runs are skipped: no Python, command, dependency, consumer, scheduler or startup code
changed. The SQL validator/fixture are the assigned tests. Full scenarios T29/T31/T43/T45/T47-T54/
T65/T69-T70 remain split: their storage foundations were exercised here; permission checks,
multi-connection CAS/crash recovery, immutable-write policy, complete row-set validation and
actual calculations/serving remain later-slice tests. No production coexistence, data, jobs,
real imports/exports, external delivery, bot restart or activation is claimed.

Local transcripts and seventeen-file hash manifest:
`C:/Users/cwatt/AppData/Local/Temp/k98-s2b-20260910` (`s2b-migration-result.txt`,
`s2b-constraints-result.txt`, `s2b-postcheck-result.txt`, `s2a-preservation-readback-result.txt`,
`final-sql-manifest.json`). Empty successful migration output is supported by exit 0 and the
independent catalog readback. Both evidence databases are retained.

#### 9. Security Review Decision and Evidence

SQL: Changes, Deep off, exact seventeen-file working-tree patch from
`845a25fe66b1d2365fb38720390b4dadf50baa67`. Scan `ec192690-194e-4a54-9eb6-b42f25f0d2c9`
sealed complete at 08:02:20 UTC, **17/17 files reviewed, zero findings, zero deferred candidates**.
Snapshot identity:
`codex-security-snapshot/v1:sha256:aace7f57fd81f40f30a527dda1a7cd06c2faa655948d9454751168fe5bd0d92d`.
Preflight passed 3/3 checks. Daybreak advisory: granted, Daybreak Blue. The scan used the
skill-required preflight and independent architecture/review workers within this task; no new
user-facing task or broader scan was created. No candidate required validation/attack-path work.

Private sealed report and canonical artifacts:
`C:/Users/cwatt/AppData/Local/Temp/codex-security-scans-R6uB4n/K98-bot-SQL-Server/845a25fe66b1d2365fb38720390b4dadf50baa67_20260910T075519Z_h6rrt2mr/report.md`.
Measured security goal usage: 125,364 tokens, 360 seconds. The workbench separately counts repeated
cached input in its rollout usage; that is a different measurement from the goal counter.

Bot: precise documentation-only skip for this appendix at bot HEAD
`58fc307935fdf1cfecdde839670ce5439f11baac`; no runtime, config, input, permission, dependency,
data access or persistence code changed. Existing user documentation was excluded from the SQL
security target. No unresolved finding details or private player data were added to Git.

#### 10. Deployment Steps

Only the explicitly authorized local disposable creation, prerequisite and S2B execution occurred.
No production target was connected, and no production deployment is authorized. Future reviewed
order is accepted S2A then S2B before any new-source writer; preserve tables/history and disabled
routing for rollback. The migration refuses existing unmatched report families; any reconciliation
requires separate review. No pull, reset, merge, push, PR, real import/export, Discord action,
restart, deployment or activation occurred. Source remains inactive.

#### 11. Deferred Optimisations

No new unrelated deferred optimisation identified. Existing WS1 and legacy export grouping/
summation work remain separate. The later semantic/transaction checks listed above are explicit
programme obligations, not silently accepted risks or permission to execute successor packs.

**S2B delivered for review. Stop here for operator review; no self-approval or automatic next slice.**

### Operator-authorized PR handoff — 2026-09-10

After reviewing the S2B delivery and summary, the operator requested creation of all required
PRs, ready for review, including existing untracked documentation updates. This authorizes
separate commits, origin pushes and PRs to SQL and the bot mirror only. It supersedes the
pre-review no-push/no-PR boundary above; production promotion, merge, activation and successor
execution remain unauthorized.

The mirror handoff includes exactly thirteen Markdown files: the existing S2A closeout and
status/index updates, S2B pack/starter and previously untracked local SQL development reference.
Current status notes now reflect completed S2B validation and PR review; prior dated evidence
is retained. Security routing is a documentation-only skip for this entire thirteen-file
mirror diff: no executable SQL, Python, permissions, dependency, configuration or runtime
persistence change. The separate seventeen-file SQL patch matches the completed Changes review (Deep off)
recorded above except for removal of extra EOF blank lines in nine schema files. Each final
SQL file was compared to its reviewed source after trimming only terminal CR/LF bytes;
all matched. The 259 static assertions passed again and staged diff hygiene passed.

Final mirror handoff checks passed across all thirteen files: architecture, deferred items,
security routing, exact-path test selector, applicable pre-commit hooks and staged Gitleaks.
Runtime-only hooks selected no files; the previously documented runtime-test skip still applies.
