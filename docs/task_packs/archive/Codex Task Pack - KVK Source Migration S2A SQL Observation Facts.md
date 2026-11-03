# Codex Task Pack — KVK Source Migration S2A SQL Observation Facts

**Archived completed slice — 2026-09-10.** S2A/S2B are accepted and merged.
All earlier approval requests, pending states and next-S2 instructions below are dated history.
Next is the active S3A pack with separate G3 approval; do not execute this archived starter/pack.

## Current status — S2A complete, accepted and merged

SQL PR #78 and mirror PR #264 merged on 2026-09-10. The final review fixes passed 401 static
assertions and 96 disposable SQL rejection cases with twelve-table rollback. S2B has since
completed implementation and local validation and is authorized for separate PR review;
production SQL deployment and source activation remain separate.
See the [local SQL development reference](../../reference/local_sql_development.md) for K98DEV
setup and per-slice disposable-target authorization. Earlier preparation/delivery entries below
are dated history and do not supersede this closeout.

## Historical execution handoff after S1 smoke - 2026-09-09

**Prepared for S2A approval only; G3 pending.** S1 typed schemas/digest are accepted and the
operator's bot-machine smoke passed 200 tests; restart/startup succeeded. Read the
[archived S1 delivery](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S1%20Offline%20Source%20Validation.md).
The operator will merge PRs #263/#570 and perform final verification before the next handoff.
At S2A execution, verify the actual accepted/merged predecessor revision and both repository
branches, HEADs, remotes and status; do not reuse the historical main hashes as current proof.
SQL is currently clean at `fc0e94ebd2e0a98286069c8a8b71365dd5178657`; no S2A migration exists.
The proposed date/sequence must be checked and allocated under the existing plan rule before edits.

The section 11 manifest remains exactly twelve tables, one migration, one static validator and
one disposable constraint-test script. Preserve section 12 invariants and section 14 tests.
S2B publication/configuration tables, DAL/intake, runtime activation and real imports are excluded.
Read current SQL instructions if present (no root AGENTS.md was present at preparation),
`sql_schema/README.md`, `migrations/README.md` and `docs/SQL_DATA_MIGRATION_GUARDRAILS.md`.
Offline schema authoring/static validation may proceed after explicit S2A G3; executing migration
or constraint SQL requires an explicitly named, authorized disposable SQL Server database.
If unavailable, report integration validation pending; do not use production or discover credentials.
No disposable target is supplied or authorized by this preparation. SQL integration acceptance
must retain actual FK/unique/check/rollback evidence, not substitute text checks for execution.

Security at execution: separate SQL Changes target for exact migration/snapshots/validators,
Deep off; bot no-code-change skip except any approved evidence appendix. Stop for review after
S2A; S2B needs its own G3. No automatic successor, PR, deployment, restart or activation.

## 1. Task Header

- Prepared 2026-09-09; owner Chris Watts; Phase 2B specification.
- G2 architecture approved, including authorized EndScanID corrections. **S2A G3 pending.**
- One-pass implementation approved: **No**. Execute only after explicit approval of this slice.
- Proposed isolated branch `codex/kvk-source-s2a`; not created during planning.
- Type: SQL implementation.

## 2. Required Reading

Read current AGENTS.md, README-DEV.md, docs/reference/README.md and its required core references,
the canonical task template, root/applicable SECURITY.md and relevant skills. Then read the
[approved contract](../../reference/kvk_source_migration/phase_2_contract_and_architecture.md),
[implementation plan](../../reference/kvk_source_migration/phase_2_implementation_plan.md),
[70 scenarios](../../reference/kvk_source_migration/phase_2_acceptance_scenarios.md), latest programme/
register updates and this pack. User decisions override historical missing-B0/G2-pending wording.
For SQL-facing work read authoritative SQL instructions, sql_schema/README.md, migrations/README.md,
SQL_DATA_MIGRATION_GUARDRAILS and exact relevant snapshots. No inferred schema from Python alone.

## 3. Objective

Add isolated immutable source/roster/report storage and database-enforced uniqueness; no actual import, route or publication.

## 4. Background

Planning anchors: bot main `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; SQL main
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`. Recheck branches/HEADs/remotes/status at execution,
preserve existing work and record actual start/end hashes. Local definitions are not deployed proof.
No pull/reset/checkout to make a working copy match historical evidence. Use an authorized isolated
branch/worktree where needed. Phase-1 C01-C65 anchor dependencies; G2 fixes source semantics.

## 5. Scope

Predecessors: S1 typed schema/digest accepted; S2A G3; explicit disposable SQL target before integration acceptance.

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

1. Confirm explicit S2A approval and predecessor evidence; otherwise scope/review and stop.
2. Capture worktrees and exact manifest; recheck drift and source/SQL contracts before edits.
3. Implement only the approved boundary with assigned tests; preserve unrelated work.
4. Run checks, review exact diff/security target and report actual outcomes/limitations.
5. Stop at delivery; no automatic next task, G4 action or self-approval.

## 9. Focused Audit Requirements

Inspect section 11 read paths for helper semantics, layering, period/identity/availability and
regression contracts. Static source continuity does not prove current live rows/jobs or external
readers. Operator-attested SQL/config parity remains separately labelled. No credential discovery
or RDP required for this planning/implementation boundary. Evidence condition: Disposable SQL required for real constraint tests. No production substitute or credential discovery.

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

- `sql_schema/KVK.KVK_Scan.Table.sql`
- `sql_schema/KVK.KVK_AllPlayers_Raw.Table.sql`
- `sql_schema/KVK.KVK_Player_Baseline.Table.sql`
- `sql_schema/KVK.KVK_CampMap.Table.sql`
- `deploy/Test-KvkTargetPublicationContract.ps1`
- `deploy/Validate-SqlRepo.ps1`
- `migrations/README.md`

### Create

- `migrations/20260909_001_kvk_source_observation_facts.sql`
- `sql_schema/KVK.SourceArtifact.Table.sql`
- `sql_schema/KVK.SourceImportAttempt.Table.sql`
- `sql_schema/KVK.SourceObservation.Table.sql`
- `sql_schema/KVK.SourceObservationRevision.Table.sql`
- `sql_schema/KVK.SourcePlayerSnapshot.Table.sql`
- `sql_schema/KVK.SourceLogicalScan.Table.sql`
- `sql_schema/KVK.SourceRoster.Table.sql`
- `sql_schema/KVK.SourceRosterMember.Table.sql`
- `sql_schema/KVK.SourceAggregateReport.Table.sql`
- `sql_schema/KVK.SourceAggregateRevision.Table.sql`
- `sql_schema/KVK.SourceKingdomReportRow.Table.sql`
- `sql_schema/KVK.SourceCampReportRow.Table.sql`
- `deploy/Test-KvkSourceObservationContracts.ps1`
- `validation/kvk_source/observation_constraints.sql`

### Modify

- None.

## 12. Implementation Requirements

Create exactly the twelve S2A tables in plan section 4 and matching migration/snapshots. Existing objects untouched. Enforce cross-source/KVK and same-observation revision FKs; add circular selected-revision links after table creation with nullable pointer only during a controlled transaction. Positive IDs/ranges/unique keys mandatory.
SourceLogicalScan supports locked per-source/KVK allocation in later DAL, unique observation binding; no trigger/default allocation for alias or aggregate insert. Aggregate rows store eight dedicated Decimal/raw/unit column groups, no FLOAT or DKP calculation. Scope/map checks are service-owned with persisted provenance, not a universal 36-kingdom constraint.
Add static validator patterned on existing read-only text checks and synthetic constraint SQL inside an explicit rollback transaction, guarded to a disposable test database and requiring authorized execution. Cover duplicate keys, mismatched source/season, circular revision mismatch, numeric limits and transaction rollback. Static checks do not prove runtime locks.
Period FK arrives in S2B; foundation cannot activate. No new procedures/UDTs/triggers/permission grants, legacy recompute edits or ProcConfig rows. Migration date/sequence follows the controlled rule in plan section 4; record final path before authoring.

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

Scenario ownership: T13/T17/T46/T50; database identity foundations for T01-T08/T68.

- Run new deploy/Test-KvkSourceObservationContracts.ps1 for static contract checks.
- Run deploy/Validate-SqlRepo.ps1 with explicit RepoPath after reviewing its log writes.
- Run listed synthetic constraint SQL only against an explicitly authorized disposable database; retain rollback evidence.

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

Rollback: Manual: retain additive objects with source disabled. No DROP script or accepted-evidence deletion. Disposable transaction rolls back only its synthetic rows.

## 17. Proposed PR Summary

Describe concrete behavior, exact manifest, actual tests/security target, dependencies and rollback
limits. Keep private player rows/credentials/findings out of Git. No PR creation authorized by
preparation. End with slice status and next required gate.

**Prepared only. S2A G3 pending; no implementation executed.**


## S2A G3 implementation delivery - 2026-09-09

The operator explicitly approved **S2A only** and requested implementation/static validation,
then a stop for review. At that initial authoring checkpoint no disposable target was supplied,
so integration was pending then. The later authorized disposable SQL validation and operator
acceptance receipts below supersede that limit: S2A integration evidence is now included and
accepted. S2B and every successor retain their separate approval gates.

### 1. Summary

Authored the isolated twelve-table observation/artifact/roster/aggregate foundation, its migration,
static validator and synthetic rollback fixture. No existing SQL object, bot runtime, importer,
configuration, publication state, command or daily namespace changes. B0 membership/attribution,
exact source endpoints and semantic re-export identity remain separate from aggregate authority.
Interim 11-10 then 12-10; final 13-10; authorized EndScanID=14 itself permits replacement 14-10
in the later configuration/publication implementation. S2A neither performs those calculations
nor requires an extra correction command. SQL authoring is delivered for review, not activated.

S1 prerequisite verified through the connected GitHub reader: mirror #263 merged at
2026-09-09 18:36:00 UTC, merge `e427e27904d4e20e75cab40bac23776c83dc2e29`; production #570
merged at 18:36:48 UTC, merge `abfc3845e9f8b78d70f88bada5a76c454ff32cb8`. The ten S1
source/test Git blobs match both merge trees and the current local bot tree. Local archived S1
receipt and merged PR metadata retain operator acceptance and **200 passed, 1 warning in 5.39s**,
restart/startup success, no machine Git HEAD, and the separate tracked-view timeout limitation.
These historical tests/restart are not S2A SQL execution or new deployment evidence. GitHub CLI
reads returned HTTP 401; the connected GitHub reader supplied the successful verification.

### 2. File Manifest

SQL base/start HEAD: `fc0e94ebd2e0a98286069c8a8b71365dd5178657`, clean `main` at
`C:/K98-bot-SQL-Server`. Its origin remains `https://github.com/cwatts6/K98-bot-SQL-Server.git`.
Implementation is in the same SQL history on `codex/kvk-source-s2a`, isolated worktree
`C:/discord_file_downloader/.sql-worktrees/kvk-source-s2a`, same HEAD. The original checkout
and every pre-existing worktree remain preserved. New files are unstaged and uncommitted.

Bot base/start HEAD: `d3a5c5565d9eb5e8cf5994e3044307db66d7fecb`, clean `main`. Evidence branch
`codex/kvk-source-s2a` retains that HEAD. Origin remains `https://github.com/cwatts6/K98-bot-mirror.git`;
production remains `https://github.com/cwatts6/K98-bot.git`. Only this appendix modifies the bot tree.
No pull, reset, merge, push or PR; no production checkout/history mutation.

The exact section 11 manifest is unchanged: twelve snapshots plus one migration and two validators.
The creation date was verified as 2026-09-09 and no migration occupied that day's sequence.
**Final migration path recorded before authoring:**
`migrations/20260909_001_kvk_source_observation_facts.sql`. No allocation exception was needed.

### 3. New Files

All fifteen paths below are relative to the SQL worktree above:

- `migrations/20260909_001_kvk_source_observation_facts.sql`
- `sql_schema/KVK.SourceArtifact.Table.sql`
- `sql_schema/KVK.SourceImportAttempt.Table.sql`
- `sql_schema/KVK.SourceObservation.Table.sql`
- `sql_schema/KVK.SourceObservationRevision.Table.sql`
- `sql_schema/KVK.SourcePlayerSnapshot.Table.sql`
- `sql_schema/KVK.SourceLogicalScan.Table.sql`
- `sql_schema/KVK.SourceRoster.Table.sql`
- `sql_schema/KVK.SourceRosterMember.Table.sql`
- `sql_schema/KVK.SourceAggregateReport.Table.sql`
- `sql_schema/KVK.SourceAggregateRevision.Table.sql`
- `sql_schema/KVK.SourceKingdomReportRow.Table.sql`
- `sql_schema/KVK.SourceCampReportRow.Table.sql`
- `deploy/Test-KvkSourceObservationContracts.ps1`
- `validation/kvk_source/observation_constraints.sql`

### 4. Modified Files

Only this S2A pack's append-only delivery evidence. No existing SQL file, index document,
predecessor, architecture, plan, acceptance-scenario or Python file was modified. Private scan
artifacts and temporary validator-mutation fixtures are outside Git. The existing repository
validator writes only its ignored `logs/validation.jsonl` in the isolated SQL worktree.

### 5. SQL Changes

Exactly twelve new tables under KVK. Composite source/season keys enforce revision, roster,
scan and aggregate references; selected revisions include the parent observation/report ID.
Circular selected-pointer and import-attempt outcome links are added after all tables exist.
Equivalent re-export attempts can point at an existing revision with their own original artifact.
Player semantic uniqueness includes observation/schema/digest version; aggregate finalization
may reuse unchanged content as a separate state event. LogicalScanID remains positive int,
unique per source/season and observation, with no identity, default, trigger or aggregate allocator.

Player counters have 31 dedicated nullable bigint columns with one-to-one snake_case S1 header
mapping and explicit JSON field-state checks; valid zero differs from unavailable NULL. Names,
Alliance and Civilization are nullable text; bounded private raw JSON retains source evidence.
Frozen roster references the exact B0 revision and scope/member digests; absent B0 power does
not remove eligibility. Kingdom/camp rows each retain eight nonnegative decimal(38,6) values,
eight raw tokens, eight positive displayed units, precision kinds and raw cell provenance.
Row mapping digests reference the same immutable aggregate revision. No DKP calculation,
player rollup, camp sum or universal 36-kingdom constraint is introduced.

The migration checks existing KVK schema, SQL JSON compatibility >=130, explicit
Latin1_General_100_BIN2 availability and absent destination names. Collision/repeat execution
fails closed for migration-history/drift review. It owns a transaction only if none exists,
propagates errors and verifies all twelve tables and trusted/enabled constraints. Rollback
retains additive objects with source disabled; no DROP or evidence deletion is supplied.

Limits: actual compilation, FK/check/unique enforcement and rollback have not run on SQL Server.
Typed SQL conversions can round before CHECK evaluation; later DAL must bind S1-validated
integers/Decimals exactly and test driver precision. NULL selected pointers, immutable accepted
writes, scope/map completeness, row counts/digests, monotonic revisions/selection and allocation
locks require later transactional service/DAL enforcement. S2B alone adds the period FK and
publication/configuration state. These are explicit contract boundaries, not S2A runtime claims.

### 6. Helpers Reused

The static validator follows `Test-KvkTargetPublicationContract.ps1`'s read-only text/assertion
pattern; no connection/deployment helper is invoked by it. Existing `Validate-SqlRepo.ps1` and
its inspected JSON-log helper are used unchanged with explicit RepoPath. Existing SQL snapshots
and JSON conventions were checked. No Python business helper, legacy numeric coercion, upload-time
default or reporting calculation is reused; no shared helper extraction is needed for this slice.

### 7. Refactor Findings

No command/view SQL, duplicated business calculation or runtime-state refactor was introduced.
Existing legacy summation and ProcConfig WS1 debt remain outside the exact manifest. No newly
proved unrelated debt was identified. K98 PR-review checks retain a review hold on integration
acceptance: static assertions cannot establish SQL runtime correctness or deployment readiness.

### 8. Test Plan with Actual Outcomes

- `deploy/Test-KvkSourceObservationContracts.ps1 -RepoPath C:/discord_file_downloader/.sql-worktrees/kvk-source-s2a`:
  **passed, 393 assertions** across all twelve snapshots, migration and rollback fixture.
- Six temporary offline mutations: **all correctly rejected** (snapshot mismatch, allocator
  default, missing composite FK columns, FLOAT substitution, removed source allowlist, removed
  disposable server guard). Delivered source remained unchanged.
- `deploy/Validate-SqlRepo.ps1 -RepoPath C:/discord_file_downloader/.sql-worktrees/kvk-source-s2a`:
  **succeeded, zero errors, 15 warnings**, all warnings refer to pre-existing migrations.
  Log source reviewed before execution; ignored isolated-worktree validation log only.
- `validation/kvk_source/observation_constraints.sql`: **authored, NOT executed**. Contains 91
  expected-rejection cases plus valid graph, bigint/decimal boundary, genuine-zero/unavailable,
  re-export alias, same-content aggregate finalization, half-aggregate rollback and all-twelve-table
  rollback checks. Error expectations distinguish constraint violations from arbitrary failures.
- SQL integration remains **pending**: explicitly authorized exact disposable server/database,
  compilation, actual constraint/error behavior and rollback receipts. Fixture refuses ambient
  transactions; requires three explicit session-context authorizations, exact server/database
  equality and a `K98_S2A_Disposable_` database name. It has no connection target or USE statement.
  Concurrent T50 allocation/acceptance and T68 registry behavior remain later DAL integration tests.
- T13/T17 identity and duplicate-row foundations, T46 rollback and T50 uniqueness are represented;
  SQL execution is not counted as passed. T01-T08/T68 have storage identity foundations only.
  Parser cases retain historical accepted S1 coverage; S2A did not rerun or execute S1 as a pack.
- Bot focused/full pytest, log-noise suite, smoke imports and command inventory/registration checks
  are intentionally skipped: no bot source/test, command, runtime wiring, startup, scheduler,
  cache or operational logging changed. SQL tests do not substitute for those future gates.

### 9. Security Review Decision and Evidence

SQL: **Changes**, Deep **off**, exact fifteen-file working-tree target at
`fc0e94ebd2e0a98286069c8a8b71365dd5178657` in the isolated SQL worktree. Scan
`030f5b97-1524-44bf-b5aa-9b3ea79a2ec8`; snapshot digest
`codex-security-snapshot/v1:sha256:4f0e343990a5c40f2ae133d6dcb64c41895cafce36a56995901cc373b322e2e8`.
Final scan outcome is recorded in the validation closeout below. Preflight passed all three
checks without config edits; TAC advisory returned `granted`, `tac1`. A helper invocation with
a session-cap flag failed because protocol version was unknown; the supported retry preserved
verified native ownership without guessing a version and passed. Required skill review workers
are internal to this task; no new user-facing task was created.

Bot: separate **documentation-only skip** for this appendix against
`d3a5c5565d9eb5e8cf5994e3044307db66d7fecb`: no runtime, config, dependency, permission,
input, data-access or persistence behavior change. Original SQL main checkout: separate no-diff
skip; the authored SQL patch is reviewed in its own history/worktree. No production bot patch.
No standard/deep scan, combined-history target, private player rows or credentials in Git.

### 10. Deployment Steps

**None performed or authorized.** Review S2A, then supply a named authorized disposable target
before migration/constraint execution and integration acceptance. No production SQL, imports,
exports, Discord actions, restart, deployment or activation. Retain additive objects and evidence
with source disabled for rollback. Stop here; S2B needs its own approval and is not executed.

### 11. Deferred Optimisations

None newly established. Preserve existing unrelated work and known legacy/WS1 items separately.
Integration evidence is an open acceptance gate, not a deferred optimisation or an assumed pass.

### Validation closeout — 2026-09-09

The SQL Changes review is sealed complete at 19:05:32 UTC: **15/15 files covered,
zero findings, zero deferred candidates**, Deep off. The exact snapshot above is unchanged.
Private scan artifacts are outside Git at
`C:/Users/cwatt/AppData/Local/Temp/codex-security-scans-mvEYrZ/kvk-source-s2a/fc0e94ebd2e0a98286069c8a8b71365dd5178657_20260909T185852Z_uvwbtkvl`
(`report.md`, `scan-manifest.json`, `findings.json`, `coverage.json`, and
`exports/results.sarif`). Measured scan rollout accounting: 4,533,706 total tokens,
including 4,380,416 cached input tokens; three internal review threads. The skill-created
scan goal completed with 113,056 tokens used; no user token budget was requested.

Static evidence: **393 assertions passed**; six deliberately corrupted temporary copies
were rejected. Repository SQL validation passed with **0 errors / 15 pre-existing migration
warnings**. The 91 expected-rejection SQL cases are authored only, **not executed**.
No SQL compilation, migration execution, constraint execution or integration acceptance is
claimed. A named, explicitly authorized disposable SQL server/database remains required.

Hook scope: Python lint, formatting, typing and runtime tests are skipped because the bot
change is documentation only and the SQL patch adds no Python. The configured LF rewrite
hook is replaced with read-only consistent line endings (SQL CRLF; document LF), whitespace, EOF, conflict-marker and size
checks to preserve the original task-pack bytes. No YAML changed. The staged-only secrets
hook cannot cover unstaged SQL additions; the cached Gitleaks executable is used instead
against temporary exact copies of the fifteen SQL files and this delivery document. No hook
installation, staging or repository-wide auto-fix is needed. Final hygiene, secrets and
preservation outcomes are recorded below after those checks.

**Stopped for S2A review. Integration validation pending. S2B remains unapproved and untouched.**

Final closeout: all sixteen files passed read-only hygiene; Gitleaks reported no leaks.
Preservation hashes confirm all 713 original SQL files unchanged and exactly this pack changed
among 1,532 bot files; its original byte prefix is intact. All fifteen SQL hashes match the
sealed review manifest. The initial hygiene assertion expected CRLF for the document too;
the appendix was normalized to the original document LF and the check passed.

### Authorized disposable SQL validation — 2026-09-09 21:08 UTC

This dated execution receipt supersedes the earlier offline-only/pending statements for the
S2A migration and constraint fixture. The operator explicitly authorized creation and S2A
migration/constraint testing of `9SX2VF4\K98DEV` / `K98_S2A_Disposable_20260909`, then requested
execution. No production SQL target was connected to or changed.

Local environment: SQL Server 2022 Developer x64, build `16.0.1200.5` (matching the
operator-reported production build), server collation `SQL_Latin1_General_CP1_CI_AS`, Windows
authentication, and max server memory 8192 MB configured/active. Database collation is
`Latin1_General_CI_AS`, compatibility 160. SQL service startup remains Manual. SSMS was installed
separately; the operator completed KB5122771 installation and the requested local PC restart.
The update's valid Microsoft signature and published SHA-256 were verified before installation.

Execution and outcomes:

- Reverified bot/SQL branches, HEADs and remotes against the baseline above. All fifteen SQL
  SHA-256 hashes still match the sealed Changes review; no SQL source edits were required.
- Re-ran the exact static validator: **393 assertions passed**.
- Created the empty authorized disposable database and its prerequisite `KVK` schema owned by
  `dbo`; no legacy tables, production data, jobs, bot configuration or successor packs imported.
- Used Windows-authenticated SQLCMD with explicit local shared-memory connection and guards
  for exact server/database, engine version, database collation and compatibility. The sandbox
  initially could not authenticate; the authorized elevated local execution succeeded.
- Applied unchanged `20260909_001_kvk_source_observation_facts.sql`: **exit 0**, all twelve
  tables created; the migration's own transaction and postchecks completed successfully.
- Ran unchanged `observation_constraints.sql` with the three explicit authorization session
  context values: **exit 0; 91 expected rejections passed; 12-table rollback verified**.
  The fixture also exercised valid synthetic rows, exact numeric boundaries, semantic aliases,
  same-content aggregate finalization and partial aggregate rollback.
- Independent postcheck: **12 tables, 18 foreign keys and 89 CHECK constraints; zero disabled
  or untrusted constraints; zero rows in every table; zero user procedures or triggers**.
- Execution transcripts and guarded local wrappers are outside Git at
  `C:/Users/cwatt/AppData/Local/Temp/s2a-integration-20260909` (`migration-result.txt`,
  `constraints-result.txt`, `post-check-result.txt`). Migration transcript is empty on success;
  its exit status and independent catalog checks establish the outcome.

The disposable database is retained with the twelve empty tables for inspection. S2A's authored
migration and SQL constraint/rollback integration checks now **pass on the authorized local
SQL Server target**. This does not establish whole-production-schema coexistence, production
rollout, real imports, future driver Decimal admission, concurrent DAL locking, immutable-write
policy, commit-time completeness, startup/restart behavior or S2B publication behavior. The
future-layer obligations already recorded above remain separate; no broader acceptance is claimed.

Security routing: reuse the sealed 15-file SQL Changes review (Deep off), because every reviewed
SQL source hash is unchanged. Bot changes remain solely this evidence appendix, a documentation-only
skip; original SQL main remains a separate no-diff skip. No new scan, staging, commit, pull, reset,
merge, push, PR, production action, deployment, activation or successor implementation occurred.
Runtime Python tests remain skipped: no bot runtime or Python code changed. Stop for operator
review of this new S2A execution evidence; S2B still requires its own approval.

### Operator acceptance and PR handoff — 2026-09-09 21:11 UTC

**S2A accepted by Chris Watts**, including the unchanged implementation and successful authorized
disposable SQL migration, 91 expected rejections and twelve-table rollback verification. The
operator said "approved, whats next?" and then explicitly authorized recording approval,
preparing the changes, creating the PRs and marking them ready for review. This supersedes
historical G3-pending, offline-only and integration-pending status for S2A in this document.

The handoff consists of two separate PRs: the exact fifteen-file implementation in
`cwatts6/K98-bot-SQL-Server`, and this evidence-only task-pack appendix in
`cwatts6/K98-bot-mirror`, both from `codex/kvk-source-s2a` into `main`. Local commits and branch
pushes needed for these PRs are authorized by that request. The production bot remote is not
part of this handoff; no merge, deployment, source activation or S2B implementation is authorized.

Final review: no blocking issue identified within the approved S2A boundary. The previously
sealed SQL Changes review covers the unchanged fifteen source files; the bot appendix has a
separate documentation-only security skip. The local SQL execution results above remain the
integration evidence; production-schema coexistence and future DAL/publication obligations
remain outside this acceptance. The SQL checkout at `C:/K98-bot-SQL-Server` stays unchanged.

Handoff validation: architecture, deferred-item and security-routing validators passed; the
test selector was run for the exact document. Runtime pytest, import smoke, command registration,
Python lint/format/type checks and log-noise tests are skipped because no bot runtime, command
surface, Python or dependency files changed. SQL static validation and the actual SQL harness
supply the relevant implementation checks. No new deferred optimisation item was established.

### PR review follow-up — 2026-09-09

The operator authorized checking, actioning, replying to and resolving PR comments. SQL PR #78
identified two valid gaps: case-insensitive JSON field-status comparisons and corrected player
revisions without a predecessor. Both are fixed in the original migration and matching snapshots:
`FieldStatusJson` explicitly uses `Latin1_General_100_BIN2`; corrected observation revisions
require non-null `SupersedesRevisionID`, with existing same-parent FK and self-link rejection intact.
The exact fifteen-file SQL manifest is unchanged; only five existing files changed in this follow-up.

Regression evidence: the new casing case failed against the prior disposable schema (the invalid
case was accepted). Rebuilt exactly the twelve verified-empty tables inside a guarded transaction
on the already authorized disposable database, using the revised migration. All **96 expected
rejections passed**, including four casing cases and missing correction lineage. Canonical status
values and a valid same-observation correction predecessor passed. Twelve-table rollback and
independent zero-row checks passed; all 18 foreign keys and 89 CHECK constraints remain trusted
and enabled. Static validator: **401 assertions passed**. SQL repository validator: 0 errors,
15 existing warnings. No production database or successor behavior was changed.

Bot PR #264 identified historical pending language and stale canonical status pages. The initial
pending paragraph is now explicitly historical; current status says S1 merged and S2A accepted,
with PR review still open and S2B requiring separate G3. This explicitly requested documentation
follow-up expands the original appendix-only handoff to ten documentation files: README-DEV,
reference/task-pack/archive indexes, programme pack, decision register, implementation plan,
Phase 2B evidence log, historical S2A starter and this delivery. Historical evidence is retained.

Fresh SQL security routing: Changes, Deep off, exact five-file working-tree delta from
`b4175db954f984ed62254fc40c067fdaf63f4c85`; scan `ca8c1c81-64f5-44e8-a2a6-cba908e386bd`, snapshot
`codex-security-snapshot/v1:sha256:74075e7bae0da60d972ff25fb78ce11c87998592e13ce00a78d7bd2d487701cc`.
Sealed complete, **5/5 files, zero findings, zero deferred candidates**. This supplements the
prior complete fifteen-file baseline review; it does not reuse that baseline as proof of changed
SQL. Preflight passed all three checks, TAC granted tac1, prior canonical threat model retained.
Scan goal usage: 43,156 tokens, 140 seconds. Private report artifacts remain under
`C:/Users/cwatt/AppData/Local/Temp/codex-security-scans-xwpop1/kvk-source-s2a/b4175db954f984ed62254fc40c067fdaf63f4c85_20260909T214535Z_7_sby_9k`.
Bot follow-up is a separate documentation-only security skip: status/evidence only, no runtime,
permissions, config or SQL execution code. Architecture/deferred/security-routing checks passed;
test selector run. Runtime Python tests/import smoke/registration checks remain inapplicable.

### Merged S2A closeout and S2B handoff — 2026-09-10

Verified GitHub SQL PR #78 merged at 07:27:22 UTC as
`845a25fe66b1d2365fb38720390b4dadf50baa67`; mirror PR #264 merged at 07:27:43 UTC as
`9fc0255dbaa0cbcb80c63c563657dad90bd5bcec`. Local SQL main is at the SQL merge. Local bot mirror
main was clean at `58fc307935fdf1cfecdde839670ce5439f11baac`; its mirror commit records source
`566c564b` and its tree has no difference from the accepted mirror merge. These are observed
handoff anchors, not instructions to reset a later checkout. The operator reports production
has not received the runtime deployment/update or restart; no independent production execution
is claimed here.

The canonical status/index surfaces and S2B pack/starter now point past S2A. The reusable local
SQL reference records instance configuration, Manual startup, existing S2A evidence and separate
future-slice database authorization. S2B remains unimplemented and G3 pending. No new chat,
SQL execution, production promotion/deployment, restart or successor work occurred in this
read-only repository verification and documentation refresh.
