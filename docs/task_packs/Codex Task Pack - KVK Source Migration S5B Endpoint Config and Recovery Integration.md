# Codex Task Pack — KVK Source Migration S5B Endpoint Config and Recovery Integration

## 1. Task Header

- Prepared 2026-09-09; owner Chris Watts; Phase 2B specification.
- G2 architecture approved, including authorized EndScanID corrections. **S5B G3 pending.**
- One-pass implementation approved: **No**. Execute only after explicit approval of this slice.
- Proposed isolated branch `codex/kvk-source-s5b`; not created during planning.
- Type: bot implementation.

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

Persist endpoint change intent in the existing config transaction and recover pending publication work safely.

## 4. Background

Planning anchors: bot main `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; SQL main
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`. Recheck branches/HEADs/remotes/status at execution,
preserve existing work and record actual start/end hashes. Local definitions are not deployed proof.
No pull/reset/checkout to make a working copy match historical evidence. Use an authorized isolated
branch/worktree where needed. Phase-1 C01-C65 anchor dependencies; G2 fixes source semantics.

## 5. Scope

Predecessors: S3B, S4B and S5A accepted; explicit S5B G3; disposable SQL for transaction-hook integration.

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

Current pack authoring: bot docs-only skip; SQL no-change skip. Future execution: Bot Changes review for this exact implementation diff, Deep off; SQL no-change skip. Prerequisite SQL slices have separate reviews.
Use k98-security-review-routing first; record exact immutable base/head or task-only authored patch,
Scan type Changes and Deep off. Never scan/stage unrelated dirty files or combine bot/SQL histories.
No routine standard/deep audit. Retain scan coverage/results privately; no public finding details.

## 8. Mandatory Workflow

1. Confirm explicit S5B approval and predecessor evidence; otherwise scope/review and stop.
2. Capture worktrees and exact manifest; recheck drift and source/SQL contracts before edits.
3. Implement only the approved boundary with assigned tests; preserve unrelated work.
4. Run checks, review exact diff/security target and report actual outcomes/limitations.
5. Stop at delivery; no automatic next task, G4 action or self-approval.

## 9. Focused Audit Requirements

Inspect section 11 read paths for helper semantics, layering, period/identity/availability and
regression contracts. Static source continuity does not prove current live rows/jobs or external
readers. Operator-attested SQL/config parity remains separately labelled. No credential discovery
or RDP required for this planning/implementation boundary. Evidence condition: Actual config editor paths/jobs and live rows remain G4 readiness evidence.

## 10. Architecture Targets

kvk/models and kvk/schemas own pure types; kvk/services business rules; kvk/dal parameterized SQL,
transactions and mapping; commands/routes/views thin adapters. New SQL only in the SQL repository.
Follow the implementation-plan interfaces/lock order and approved source/field dictionary.
No second domain implementation in DL_bot.py or gsheet_module.py; no duplicated SQL calculation.

## 11. Exact File Manifest

All paths below are relative to **C:/discord_file_downloader**.
New files are proposed, not present yet; predecessor-created modifications require accepted delivery.
No wildcard authorizes extra files. Append implementation evidence to this pack after execution;
do not rewrite unrelated indexes. Migration date/sequence is the sole controlled allocation exception
in implementation-plan section 4; final name must be recorded before authoring and never renamed after merge.

### Read only

- `processing_pipeline.py`
- `file_utils.py`
- `docs/task_packs/Bot Operational Reliability Workstream 1 - Design and Manifests.md`

### Create

- `kvk/services/new_source_recovery_service.py`
- `tests/test_kvk_source_config_hook.py`
- `tests/test_kvk_source_recovery.py`

### Modify

- `proc_config_import.py`
- `bot_instance.py`
- `bot_config.py`
- `upload_routes/kvk_source_route.py`
- `stats_alerts/interface.py`
- `tests/test_proc_config_import.py`
- `tests/test_proc_config_import_phase2.py`
- `tests/test_kvk_source_upload_route.py`

## 12. Implementation Requirements

Follow implementation-plan section 5 exactly. Insert SourceConfigRequest using the same cursor/connection before the existing transactional Windows import commit (planning anchor proc_config_import.py line 927). Never commit separately or rely on importer success after commit. Disabled mode must require no new SQL schema; enabled mode fails closed if schema is missing. Preserve unchanged sheet structures and nontransactional import behavior.

Record the actual config actor/provenance, including a system/import identity where no editor identity is available; never invent an editor. Endpoint-only updates retain approved weight/map/roster bindings. Idempotency includes base config so 13→14→13 is a distinct authorized sequence. Pending 14 must not expose 13 as current final.

Use a bounded off-event-loop recovery worker, register once, cancel cleanly and resume persisted requests after restart. Gate it with the default-off recovery flag. Do not repost public messages automatically. Preserve daily three-claim and independent KS4 lifecycle behavior in stats_alerts/interface.py. Do not repair generic ProcConfig/WS1 autocommit, targets or historical offloading debt. Prove commit-then-return-error recovery with disposable SQL and deterministic failures.

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

Scenario ownership: T48–T54, T59, T68–T70; transaction rollback, committed request followed by importer error, restart and pending endpoint.

- `python -m pytest -q tests/test_kvk_source_config_hook.py tests/test_kvk_source_recovery.py tests/test_proc_config_import.py tests/test_proc_config_import_phase2.py tests/test_kvk_source_upload_route.py tests/test_kvk_source_delivery.py`

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

Rollback: Disable intake/recovery and source routing through separately authorized controls; retain requests and historical publications. Do not delete accepted intent.

## 17. Proposed PR Summary

Describe concrete behavior, exact manifest, actual tests/security target, dependencies and rollback
limits. Keep private player rows/credentials/findings out of Git. No PR creation authorized by
preparation. End with slice status and next required gate.

**Prepared only. S5B G3 pending; no implementation executed.**


## Required S4B handoff checks - 2026-09-11

Read the [named follow-up register](../reference/kvk_source_migration/phase_2_implementation_plan.md#s4b-follow-ups) before S5B implementation. **S5B-REC01 is required for S5B acceptance**, not optional debt. S4B-MP01 supplies component-level synthetic multi-period coverage; it does not prove this worker/caller wiring.

- [ ] Prove default-off startup, one worker registration, bounded off-event-loop calls and clean cancellation.
- [ ] Prove a committed endpoint request survives importer return error and resumes after restart using disposable SQL.
- [ ] Compose the actual caller with S4B delivery: when either included period changes, pass that changed selection as anchor, recheck all selections, preserve the other period and deduplicate receipt reload. An unchanged confirmed anchor with a new combined key must fail closed.
- [ ] Preserve uncertain receipts and private quarantine; no TTL reclaim, blind send/edit replacement or automatic public repost. Daily three-claim ownership is unchanged.
- [ ] Record exact tests, SQL target/revision, runtime gates and remaining S6-OPS01/S6-PERF01/S6-CAP01 evidence. Do not claim deterministic restart tests are real in-flight Google interruption proof.

These clarify testing of the existing S5B integration boundary. They do not expand its runtime/SQL file manifest, authorize a later slice, or permit production/external operations. S5B G3 and predecessors remain separate prerequisites.


## S5A closeout prerequisite and documentation carry-forward - 2026-09-12

S5A is accepted, successfully smoke tested (operator reported) and merged in mirror #270 and private
bot #577. Local pulls are complete at mirror main `90aea74c93c6aad2c890d1783ff53f109cc7bf8a` and
production/main `dd69666a04daa47d6d596e694aff024a02417144`; SQL remains
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. No bot-machine pull or deployment occurred.
Read the [archived S5A delivery](archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S5A%20Private%20Intake%20and%20Admin%20Controls.md), including its smoke-evidence limits and final complete Changes review.
S3B/S4B/S5A are accepted prerequisites, not tasks to re-execute. This closeout is not S5B G3.

Start S5B in a new chat using its starter only with explicit S5B G3. First confirm fresh repo state,
existing helper/schema contracts and exact manifests. Mocked preparation can proceed within that
approval; before executing the required disposable-SQL tests obtain the exact target and permitted
operations. No default/production SQL fallback; report the integration gate open if not authorized.
No retained database deletion, real imports/exports, provider/Discord action, restart or activation.
Either endpoint may change through authorized configuration; supplied EndScanID >= StartScanID.
Equal endpoints mean zero supported fight scores for all B0 members, aggregates not applicable;
distinct player scans increase both ScanID and UTC. Preserve explicit ordinary missingness, semantic
re-export identity and separate daily SCANORDER. EndScanID authorization itself permits 14-10 after
13-10 without a second correction command. No command-count increase; every group stays <=25.

### Required documentation manifest for the eventual S5B PR

This is the explicitly authorized documentation-only addition to section 11. It does not expand
runtime/test/SQL scope. Include every path below alongside the approved S5B execution manifest
when its PR is separately authorized, including untracked Markdown and both deleted source paths
and archive destinations. Preserve complete historical evidence and repaired links. The instruction
not to rewrite unrelated indexes does not exclude these exact closeout files. No wildcard or bulk
staging is permitted; exclude local review worktrees such as `.codex_scan_stage/` and `.codex/`.
Production promotion, when separately authorized, must carry the same documentation delta.

- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/kvk_source_migration/decision_and_evidence_register.md`
- `docs/reference/kvk_source_migration/phase_2_implementation_plan.md`
- `docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md`
- `docs/reference/local_sql_development.md`
- `docs/task_packs/KVK Source Migration - Programme Pack.md`
- `docs/task_packs/README.md`
- `docs/task_packs/archive/README.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S5A Private Intake and Admin Controls.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S5A Private Intake and Admin Controls.md`
- `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S5A Private Intake and Admin Controls.md`
- `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S5A Private Intake and Admin Controls.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S5B Endpoint Config and Recovery Integration.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S5B Endpoint Config and Recovery Integration.md`

The PR summary must state S5A accepted/smoke-tested/merged with operator-attested smoke limits,
local pulls complete, bot-machine untouched, routing disabled and S5B-REC01/S6 gates explicitly open
until their actual evidence is accepted. Add S5B delivery outcomes, remaining gaps and exact separate
repo security targets; do not turn historical results into fresh passes.

Documentation validation: run architecture/deferred/security-routing validators, exact-path test
selection, whitespace and local link/archive checks. This closeout changes only Markdown status,
links and archive placement: runtime pytest/import and new Security scans have a documented skip;
SQL is a separate no-change skip. Future S5B code requires its own tests and Changes review, Deep off.


## S5B implementation delivery - 2026-09-12

This dated delivery supersedes the historical "G3 pending / prepared only" status above.
**Review verdict: do not merge yet.** Implementation and synthetic validation are ready for
review; S5B acceptance and S5B-REC01 remain open pending disposable SQL integration.
No predecessor or later pack was executed.

### 1. Summary

Explicit S5B G3 was provided in this task. S3B/S4B/S5A acceptance was confirmed from current
programme/plan/register and archived S5A evidence; operator smoke evidence remains operator
reported. The user separately approved these two bounded manifest amendments:

- Create `kvk/dal/new_source_recovery_dal.py` for Windows-to-period/base resolution, bounded
  durable discovery, schema checks and immutable publication-input loading.
- Modify `kvk/dal/new_source_publication_dal.py` solely to validate a contiguous same-period
  endpoint request chain from selected to desired config, retaining component/input/CAS checks.
  This handles two authorized imports before recovery, including 13 -> 14 -> 13.

The transactional Windows import records endpoint intent before its existing commit, using
the same cursor. Recovery is default-off, bounded, off the event loop, registered once and
resumes from SQL. Intake confirmation and normal stats processing supply wake hints.
Explicit Sheets registrations reuse S4B delivery; no automatic Discord publication is added.

### 2. File Manifest

Entry and delivery repo state was checked locally without fetching:

| Repository | Branch | Entry and delivery HEAD | Remotes / status |
|---|---|---|---|
| Bot | main | `90aea74c93c6aad2c890d1783ff53f109cc7bf8a` | origin = K98-bot-mirror; production = K98-bot; original docs plus exact S5B files remain uncommitted |
| SQL | main | `44afa315dd6cbfe9fec101f2a39a62e534f5b583` | origin = K98-bot-SQL-Server; clean, no changes |

Bot origin/main matches HEAD; local production/main remains
`dd69666a04daa47d6d596e694aff024a02417144`. SQL origin/main matches HEAD.
These are local ref observations, not remote freshness or deployed parity proof.
All pre-existing worktrees remain. The new detached review worktree
`.codex_scan_stage/s5b` contains only the ten authored Python files over the bot HEAD;
it is local evidence and is excluded from delivery/staging. No implementation branch,
commit, staged change, PR or promotion was created.

All fifteen original documentation status entries were SHA-256 checked unchanged before
this append. This pack retains its original bytes as a prefix; the other fourteen entries,
including both S5A archive moves, remain unchanged. Preserve the exact documentation
carry-forward manifest above in any separately authorized future PR.

### 3. New Files

- `kvk/services/new_source_recovery_service.py`: config hook adapter, typed publication
  orchestration, explicit export caller, wake hints and monitored worker.
- `kvk/dal/new_source_recovery_dal.py`: approved amendment; schema/transaction checks,
  period discovery, request-chain proof and immutable SQL input loading.
- `tests/test_kvk_source_config_hook.py`: synthetic hook/import tests and three opt-in
  disposable SQL cases.
- `tests/test_kvk_source_recovery.py`: typed reload, chain rejection, lifecycle, permission,
  exact endpoint sequence and composed S4B multi-period caller tests.

### 4. Modified Files

- `proc_config_import.py`: optional actor/provenance and precommit hook; nontransaction path retained.
- `bot_instance.py`: one monitored recovery registration in ready services.
- `bot_config.py`: interval (default 30 seconds, allowed 1-300), batch (default 8, allowed 1-32)
  and explicit export registrations (default empty JSON list, maximum eight).
- `upload_routes/kvk_source_route.py`: wake after durable intake confirmation.
- `stats_alerts/interface.py`: non-test wake hint; existing daily three-claim/KS4 flow retained.
- `kvk/dal/new_source_publication_dal.py`: approved bounded request-chain amendment.
- This task pack: append-only delivery evidence.

The approved existing test paths `tests/test_proc_config_import.py`,
`tests/test_proc_config_import_phase2.py` and `tests/test_kvk_source_upload_route.py`
needed no edits and were executed unchanged. Read-only processing/file/WS1 files were not changed.

### 5. SQL Changes

None. Queries were checked against the authoritative SQL repository at the HEAD above,
including Source config/window/period/roster/weight/camp definitions, accepted observation
and aggregate revisions, publication/selection/action/delivery, and KVK_Windows.
Existing S3B transactions and lock order are reused. No DDL, schema migration, database
connection or SQL execution was performed in this task.

The disposable target and permitted operations were requested but not supplied.
The three integration tests therefore skipped explicitly. Their opt-in fixture has no
default target, validates an explicitly named S5B disposable database and local K98DEV
server identity, uses synthetic data, and does not install schema or delete a database.
It requires separately prepared accepted schema plus KVK_Windows. No production fallback.

### 6. Helpers Reused

Existing `request_endpoint_update` / `snapshot_endpoint_request`, `locked_period`,
`desired_config`, transaction/season locks and canonical serialization are reused.
PublicationService owns calculation and immutable candidate construction; PublicationDAL
retains completeness/input checks and pointer/action/delivery CAS.
S4B `load_sheets_generation`, `deliver_export`, DeliveryRepository and registered
GoogleSheetsTransport retain whole-generation checks, RAW precision, destination fences,
uncertain receipts and private quarantine. TaskMonitor owns worker lifecycle.
Existing S4B synthetic multi-period test machinery is composed through the actual S5B caller.

### 7. Refactor Findings

The original manifest lacked the DAL owner required by sections 10-11; the approved DAL
amendment resolves that gap. The publication guard rejected a valid rapid request chain;
the second approved amendment resolves that bounded issue. No general ProcConfig/WS1,
legacy exporter, daily lifecycle or source-calculation refactor was included.
No new command or permission model was added.

### 8. Test Plan with Outcomes

Commands used `.venv/Scripts/python.exe`; the system interpreter lacked pytest.
Fresh results for this authored patch:

| Check | Actual outcome |
|---|---|
| Exact six-file pytest command in section 14 | 158 passed, 3 skipped, 12.02 seconds |
| Full suite through `scripts/analyse_pytest_log_noise.py` | 4,064 passed, 37 skipped, 183.65 seconds |
| Operational log isolation | Passed; production operational logs unchanged |
| Architecture boundaries, exact Python manifest | Passed, 10 Python files |
| Deferred item validator | Passed |
| Codex Security routing validator | Passed, zero errors/warnings |
| Exact-path test selector | Required focused plus full suite, smoke and registration; executed |
| Smoke imports | Passed |
| Command registration | Passed; 36 top-level, 101 grouped, kvk_admin 8, largest group 24; no drift/duplicates |
| Exact-file pre-commit | Applicable hooks passed, including formatting/lint/type checks |
| Direct pyright | Zero errors; five dependency-resolution warnings; pre-commit pyright passed |

The configured gitleaks pre-commit hook uses staged content; the index is empty, so that hook
result alone is not evidence of scanning untracked bodies. The Changes source review covered
the new files; fixtures are synthetic and no credential contents or private player rows were added.

T68-T70 synthetic caller coverage proves interim 11-10, then 12-10, final 13-10, honest
pending desired 14, then corrected final 14-10 without a separate correction command.
B0 eligibility, exact UTC inputs, typed Decimal/missingness and generation deduplication
use the accepted pure model. Aggregate authority stays independent of player scan allocation.
Lifecycle tests cover default-off/no factory access, one registration, thread offload,
wake/restart behavior and cancellation waiting for in-flight work. Permission rejection
does not trigger confirmation wake. Daily and independent-source regressions pass.

S5B-REC01 multi-period caller tests pass for either included period changing, retaining the
other selection, receipt reload/deduplication and the unchanged-anchor negative case.
Uncertain receipts are not automatically reclaimed; no private-slot replacement is attempted.

**Integration gap:** T48-T54/T70 transaction/concurrency behavior is not established by
mocked tests or the broad suite. Three disposable SQL tests exist for rollback, committed
intent followed by importer return error and fresh-instance recovery, and two authorized
imports before recovery. They remain unexecuted. Prior accepted SQL slice results are
dependencies, not a fresh S5B integration pass. No real in-flight Google interruption was tested.

### 9. Security Review Decision and Evidence

Bot review: **Changes, Deep off**, task-only uncommitted patch over base/head
`90aea74c93c6aad2c890d1783ff53f109cc7bf8a`, isolated target
`C:/discord_file_downloader/.codex_scan_stage/s5b`.
Completed and sealed scan `6033894b-0125-44ea-8bd4-10651fcd8d38`;
snapshot digest
`codex-security-snapshot/v1:sha256:a13668a623d83c785b9e4df0e16b90087004a51d6c99ba6b0a2254b2bdb238af`.
Completed readback confirms zero findings, complete static diff coverage: eight runtime
inventory files and both test files as supporting surfaces. All ten file hashes match the
reviewed patch. The threat-model workflow's independent architecture review also found
no concrete candidate. No standard/deep scan or automatic new task was launched.

Private canonical report is retained under the existing local scan bundle:
`%TEMP%/codex-security-scans-nRIFjb/s5b/90aea74c93c6aad2c890d1783ff53f109cc7bf8a_20260912T092558Z_w82ui57v/report.md`.
The tool reports 2,487,502 total tokens across two rollout threads
(2,344,448 cached input tokens); this is tool-reported rollout accounting, not a claimed
independent measurement of only security reasoning.

SQL review: separate no-change skip at
`C:/K98-bot-SQL-Server`, base/head `44afa315dd6cbfe9fec101f2a39a62e534f5b583`,
clean tracked/untracked/index state. No combined-history target.
The inherited docs and this delivery append have a documentation-only skip.
Static security completion does not close the SQL integration or runtime gates.

### 10. Deployment Steps

None executed or authorized. Recovery and intake defaults remain off; export registration
defaults empty. No pull/reset/merge/push/PR, production SQL, real import/export, Discord action,
restart, deployment, activation or database deletion occurred.
No S6 or predecessor pack was started.

Future separately approved setup must provide the exact disposable SQL target/operations
and accepted schema before the remaining tests can run. Live editor/path parity, real
provider interruption, capacity and capability evidence remain S6-OPS01/S6-PERF01/S6-CAP01
and G4 concerns, not completed S5B work. Runtime rollback remains separately authorized
disablement with accepted requests/history retained.

### 11. Deferred Optimisations

No new unrelated optimisation item was established. Existing WS1 and legacy export debt
remain separate. The missing SQL integration evidence is an acceptance gate, not deferred
optimisation. Stop for review with **S5B implementation delivered, acceptance pending**.


## S5B disposable SQL validation follow-up - 2026-09-12

The user approved integration execution and creation of a suitable database on local K98DEV.
This follow-up supersedes the earlier missing-target and unexecuted-integration status; the
original eleven-part delivery and its dated evidence remain intact. **S5B is ready for operator
review; the required disposable SQL test gap is closed. Operator acceptance is not self-granted.**

### Summary and SQL setup

Created and retained `9SX2VF4\K98DEV` / `K98_S5B_Disposable_20260912`, reached explicitly through
`lpc:localhost\K98DEV` with Windows authentication. Verified SQL Server `16.0.1200.5`, database
collation `Latin1_General_CI_AS` and compatibility `160`. The service was already running;
no service start or restart occurred. The name was verified absent before creation.
No retained predecessor database was reused, rebuilt or deleted.

Installed accepted schema prerequisites from SQL HEAD `44afa315dd6cbfe9fec101f2a39a62e534f5b583`:

- `20260909_001_kvk_source_observation_facts.sql`, SHA-256
  `4b19c8e54a7555e796c06124640efd27b6838c8360d352bd55265d04bdc1614c`.
- `20260910_001_kvk_source_publication_state.sql`, SHA-256
  `2985551c7cac6ba158a38c436389aa13b44fe36235ccf6768b684037cce77fbc`.

Added a local synthetic KVK_Windows prerequisite matching the authoritative column, primary-key,
default and CHECK contracts. Legacy secondary indexes are unnecessary for the synthetic insert
and were not installed. This is test setup, not a new SQL migration or snapshot deployment.
The database has 26 KVK tables and no disabled/untrusted foreign-key or CHECK constraints.
The setup script is retained outside Git at `%TEMP%/k98-s5b-setup.py`.
Installing accepted prerequisites did not execute a predecessor pack or its tests.

### Test outcomes and retained evidence

Ran the exact section-14 six-file pytest command with only these process-scoped settings:
`KVK_S5B_SQL_SERVER=localhost\K98DEV` and
`KVK_S5B_SQL_DATABASE=K98_S5B_Disposable_20260912`.
**161 passed, zero skipped, in 13.25 seconds.** No source or test changes were needed.

All three formerly skipped SQL cases passed:

1. A deterministic precommit failure rolls back both the synthetic Windows row and request.
2. A deterministic postcommit importer error preserves both; a new RecoveryService instance
   resumes the missing desired endpoint as live/pending, then selects corrected final after
   the desired observation arrives, and the next recovery is a no-op.
3. Two authorized endpoint updates before recovery (fixture 3 -> 4 -> 3, equivalent to
   13 -> 14 -> 13) select the final desired config through the contiguous request chain.
   Repeated recovery is a no-op.

Independent aggregate SQL readback: three periods, three requests, six historical publications,
three current selections and one Windows row. Current selections are two finals at fixture scan 3
and one corrected final at fixture scan 4. Two requests are applied; one earlier chain link retains
its historical pending state. The rapid-chain test verifies the latest desired config is current
and idempotent; that retained older link is not the active desired endpoint.
Enabled source-routing rows: zero. Invalid/disabled/untrusted constraints: zero.
All synthetic evidence is retained. No private player data or credential contents were read or added.

The prior full-suite/log-isolation result remains 4,064 passed / 37 skipped; it was not repeated
because code is unchanged and the previously missing SQL cases now passed in the focused run.
This follow-up does not claim new real-provider interruption, production configuration, capacity,
or live runtime evidence. Those S6/G4 gates remain unchanged. S5B-REC01 now has its required
synthetic caller/lifecycle and disposable SQL recovery evidence for operator review.

### Manifest, security and stop boundary

All ten Python files still match the hashes of completed Changes scan
`6033894b-0125-44ea-8bd4-10651fcd8d38` (Deep off, zero findings). Its historical unexecuted-SQL
limitation is supplemented by this dated evidence, not silently rewritten. No new code scan is
needed for unchanged code. Only this authorized pack append changes; no new repository files.
SQL repository remains clean at `44afa315dd6cbfe9fec101f2a39a62e534f5b583`, so its separate
no-change review decision remains valid. Bot HEAD remains
`90aea74c93c6aad2c890d1783ff53f109cc7bf8a`; prior work is preserved.

No PR, pull/reset/merge/push, production SQL, real import/export, Discord action, restart,
deployment, activation or later pack was performed. Stop for S5B review with the disposable
integration gap closed; retain the database and all historical evidence.

## PR #271 review response - 2026-09-12

The operator authorized action, review and replies for all three inline comments. This bounded
follow-up adds `commands/admin_cmds.py`, `tests/test_proc_config_import_offload.py` and
`docs/reference/ENV_REFERENCE.md` to the S5B modify manifest for these comments only.
No SQL/shared-helper/later-slice implementation is included; file_utils.py and maintenance_worker.py
remain unchanged.

- Hoisted pandas import out of the row loop, retaining the default-off early return.
- Manual imports pass the authenticated Discord actor, guild, interaction and trigger; startup
  imports record the system trigger. The process adapter carries one typed JSON payload and
  reconstructs keyword arguments because the existing worker dispatch is positional. Explicit
  thread mode uses the direct thread helper; the incompatible legacy process-handle fallback is
  not used. Nested worker results preserve importer failure, and unknown outcomes do not replay.
- Documented all three recovery variables, exact JSON keys/types/bounds, synthetic example,
  dedicated/protected workbook rules, audience and credentials, receipt-capacity limits and the
  conditional exact MAINT_SPEC_ALLOWLIST entry. Configuration is validated before SQL/credentials.
  Shared workbook IDs, protected IDs, malformed fields and unsupported keys fail closed.

Fresh final focused validation: 180 passed in 16.51 seconds, including all three approved disposable
SQL cases on retained K98_S5B_Disposable_20260912. Actual serialization/worker dispatch is tested
in-process with a synthetic importer; process result transport is mocked. Explicit thread and
asyncio fallbacks, actor/provenance, failed importer result and malformed export configuration
are covered. An initial full run exposed test-order leakage from a prior worker test's imported
fake normalizer; this new test now explicitly binds the real dependency and restricted allowlist.
The combined maintenance/offload regression passed 24 tests in 3.77 seconds. No shared test or
runtime helper was changed to hide the failure.

Architecture, deferred, security-routing, exact-path selector, smoke imports and registration
passed (36 top-level / 101 grouped; no drift/duplicates). Applicable pre-commit code checks passed;
formatting-only hook corrections are included. Final staged checks and full-suite result follow below.

Security: Changes, Deep off, final seven-file fix patch over
87ec2e825f670628284b30c2987256bd2277e845; completed/read-back scan
`a7fba7aa-53ea-4ddc-bc86-f9c7e9ac42e8`, digest
`codex-security-snapshot/v1:sha256:ec2985fdcfe7d4e14bda24b65ecbc60d8f8c96d6d5d50787ae94ba3cc1f7835c`.
Zero findings; four runtime files and supporting tests/docs reviewed. Independent architecture
review confirmed the helper-contract fixes. Tool-reported scan usage: 693,721 tokens (689,024
cached input), rollout accounting. Earlier scan b6ab46fa-4d44-48c1-9db5-b018962c0d55 retained the
initial helper-contract gaps and is not the final gate. The only post-scan changes are documentation
of the allowlist/evidence and test dependency isolation; no runtime/security-control changes.
Those exact documentation/test-harness changes were reviewed with a no-runtime-change scan skip.
The initial S5B review remains evidence for the preceding commit; this scan covers its fix delta.

SQL repository remains unchanged at 44afa315dd6cbfe9fec101f2a39a62e534f5b583: separate no-change skip.
Real configured allowlist, production/operator parity and provider/capacity evidence remain S6/G4.
No credentials, private player data, production SQL, real imports/exports, Discord operations,
merge, deployment, activation or later-pack execution. No new deferred optimisation item.

Final full-suite rerun: **4,080 passed, 37 skipped in 160.78 seconds**; operational logs unchanged.
The three S5B SQL cases passed separately in the 180-test focused run. One earlier full run
failed the now-isolated worker test; another paused near dashboard tests and was interrupted.
The final verbose run completed without failures; no unrelated dashboard code was changed.
Final staged pre-commit checks, including secret scanning and registration, passed.


## PR #271 second review response - 2026-09-12

Addressed the two further comments within the existing S5B manifest:

- Process-mode results above 900 serialized characters now use a bounded status envelope,
  preserving the authoritative success Boolean, explicit failure indication and a persisted-report
  path when it fits. The full importer report remains in the existing report/logging mechanism.
  This avoids the unchanged worker's default 1,000-character telemetry truncation. Two tests use
  the real worker result emitter with large success/failure reports and verify wrapper results.
  Configuring a worker cutoff below this envelope is outside the default guarantee; preserve the
  documented default or a larger cutoff. No automatic replay or shared-worker change was added.
- Applied same-config requests no longer supply actor/reason/RequestID to subsequent ordinary
  publications. These use system:kvk_source_recovery. Actual endpoint transitions and still-pending
  endpoint completion retain request context. A disposable SQL regression proves that a later live
  scan creates a system publish action with no request ID and leaves AppliedPublicationID unchanged.

Changed files: proc_config_import.py, kvk/services/new_source_recovery_service.py,
tests/test_proc_config_import_offload.py, tests/test_kvk_source_config_hook.py and this evidence append.
No new manifest path, SQL repository change, provider operation or later-slice work.

Focused seven-file suite on the approved retained local K98_S5B_Disposable_20260912 database:
**183 passed, zero skipped, in 14.63 seconds**, including four SQL integration cases.
Architecture/deferred/security-routing validators, test selector, smoke imports and command
registration passed (36 top-level / 101 grouped; no drift/duplicates). Applicable pre-commit
formatting/lint/type checks passed. Final staged secret check and suite outcomes follow below.

Changes review, Deep off: completed/read-back scan 5b415d65-f28b-4dc8-a043-87e206ff1a2d,
four-file task-only patch over 964893c5e20688ac826209af4f964838fd1f943e; snapshot digest
codex-security-snapshot/v1:sha256:f3fd00516c094a3a8c6a15e86ad9a22d193c1133106e11aa4a3eead75ca22e9f.
Two runtime inventory files plus both supporting test files reviewed, zero findings.
Independent architecture review found no blocker. Tool-reported rollout usage: 1,179,705 tokens,
including 1,137,152 cached input tokens. Evidence-only append has a documentation-only scan skip.
SQL remains clean at 44afa315dd6cbfe9fec101f2a39a62e534f5b583: separate no-change skip.
Retain prior scans and historical test evidence; this scan covers only the latest fix delta.

The combined full run stalled in the unrelated dashboard timeout test area with an asyncio
wait recorded by faulthandler. No dashboard code was changed. The entire dashboard test file
passed separately: 36 passed in 1.99 seconds, operational logs unchanged. The rest of the suite
is run separately to preserve complete test coverage; this is not a claim that the stalled
single-process invocation passed. No new unrelated refactor or optimisation was implemented.
No merge, production push/SQL, real import/export, Discord action, deployment or activation.

Final remaining-suite result: **4,046 passed, 38 skipped in 163.58 seconds**, operational logs
unchanged. With the 36 separately passed dashboard tests, all suite tests were covered across
two runs: **4,082 passed and 38 skipped**. The four S5B SQL cases passed separately in the
183-test focused run. Final staged pre-commit, including secret scanning, passed.


### Production PR 578 review follow-up - 2026-09-12

User authorized checking, fixing, responding to and resolving production PR 578 comments.
Entry branch prod/kvk-source-s5b was clean at ff0dba287aa25cced60518d39d2c3b9036111bfa;
PR head matched and base main was dd69666a04daa47d6d596e694aff024a02417144.
Origin remains K98-bot-mirror; production remains K98-bot. No pull/reset/merge performed.

Addressed all three review threads within S5B:

- Recovery restores numeric semantic values using the accepted player/aggregate schema,
  independently of Excel numeric/text storage. Numeric-looking Name/Alliance/Civilization
  remain strings; nulls, metric states, raw storage and aggregate displayed-unit evidence remain
  intact. Parser roundtrip regressions cover numeric/text player cells and abbreviated aggregates.
- New synthetic disposable SQL regression accepts text-stored counters, reloads each immutable
  revision and publishes recovery results. Persisted values, states and ranks match direct
  calculation; the expected T4/T5 kill points value is 200.
- All nine synced status files now lead with current S5B review status and explicitly label the
  retained S5A closeout as historical. Both PRs remain open; activation and later packs stay gated.
- Importer fallback comments now match its three-step docstring.

Exact changed manifest: kvk/dal/new_source_recovery_dal.py; proc_config_import.py;
tests/test_kvk_source_recovery.py; tests/test_kvk_source_config_hook.py; README-DEV.md;
docs/reference/README.md; docs/reference/local_sql_development.md;
docs/reference/kvk_source_migration/decision_and_evidence_register.md;
docs/reference/kvk_source_migration/phase_2_implementation_plan.md;
docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md;
docs/task_packs/README.md; docs/task_packs/KVK Source Migration - Programme Pack.md;
docs/task_packs/archive/README.md; and this canonical evidence append.
The nine status paths directly address the reviewer's requested synchronized documentation fix.

Actual validation: focused seven-file suite **186 passed, zero skipped, 12.36 seconds**, including
all five S5B SQL cases against retained local K98DEV / K98_S5B_Disposable_20260912.
The new test's initial fixture/assertion-shape errors were corrected before this passing run.
Full suite split around the previously documented unrelated dashboard timing-sensitive file:
**4,048 passed, 39 skipped in 191.33 seconds**, plus **36 dashboard tests passed in 1.80 seconds**;
total **4,084 passed, 39 skipped** across two runs. The five opt-in S5B SQL skips in the broad run
were exercised separately above; predecessor SQL cases remain opt-in and were not reopened.
Operational-log isolation passed. Architecture, deferred-items, security-routing, test selector,
smoke imports and command registration passed (36 top-level / 101 grouped, no drift/duplicates).
All nine current status blocks were verified identical. Formatting/lint/type hooks passed.

Security: Changes, Deep off, production fix delta only over ff0dba287aa25cced60518d39d2c3b9036111bfa.
Completed and read back scan cf5a25c1-f9c6-431b-a2c6-fa9dba1716a7; snapshot digest
codex-security-snapshot/v1:sha256:645aab4b987b8eaebf2c2a63a9a4e9cb2ef7150adcb77b1f6efea8f0fb01a27b.
Both runtime inventory files, both test files and nine status documents reviewed; zero findings,
no deferred candidates. Independent architecture review found no regression. Daybreak granted
(Daybreak Blue). Tool-reported rollout usage 1,485,812 tokens, including 1,390,592 cached inputs.
Canonical manifest/findings/coverage/report retained in the scan directory under local temporary
codex-security-scans-nRIFjb. This subsequent evidence-only append has a documentation-only scan skip.
SQL repo remains clean at 44afa315dd6cbfe9fec101f2a39a62e534f5b583: separate no-change review skip.

No production SQL, real import/export, Discord action, restart, deployment, activation or merge.
This follow-up targets production PR 578 only; mirror PR 271 has not been updated by this follow-up.
Mirror synchronization remains a handover item so a later mirror promotion does not lose this fix.
