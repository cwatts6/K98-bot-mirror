# Codex Task Pack — KVK Source Migration S5A Private Intake and Admin Controls

## 1. Task Header

- Prepared 2026-09-09; owner Chris Watts; Phase 2B specification.
- G2 architecture approved, including authorized EndScanID corrections. **S5A G3 pending.**
- One-pass implementation approved: **No**. Execute only after explicit approval of this slice.
- Proposed isolated branch `codex/kvk-source-s5a`; not created during planning.
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

Add disabled private intake and owner-bound administrative controls for the new source.

## 4. Background

Planning anchors: bot main `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; SQL main
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`. Recheck branches/HEADs/remotes/status at execution,
preserve existing work and record actual start/end hashes. Local definitions are not deployed proof.
No pull/reset/checkout to make a working copy match historical evidence. Use an authorized isolated
branch/worktree where needed. Phase-1 C01-C65 anchor dependencies; G2 fixes source semantics.

## 5. Scope

Predecessors: S1, S3B, S4A and S4B accepted; explicit S5A G3.

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

1. Confirm explicit S5A approval and predecessor evidence; otherwise scope/review and stop.
2. Capture worktrees and exact manifest; recheck drift and source/SQL contracts before edits.
3. Implement only the approved boundary with assigned tests; preserve unrelated work.
4. Run checks, review exact diff/security target and report actual outcomes/limitations.
5. Stop at delivery; no automatic next task, G4 action or self-approval.

## 9. Focused Audit Requirements

Inspect section 11 read paths for helper semantics, layering, period/identity/availability and
regression contracts. Static source continuity does not prove current live rows/jobs or external
readers. Operator-attested SQL/config parity remains separately labelled. No credential discovery
or RDP required for this planning/implementation boundary. Evidence condition: Real channel/role configuration must be verified before enabling, not before mocked implementation.

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

- `upload_routes/common.py`
- `upload_routes/kvk_all_route.py`
- `core/interaction_safety.py`
- `decoraters.py`
- `services/kvk_all_import_audit_service.py`
- `scripts/validate_command_registration.py`

### Create

- `upload_routes/kvk_source_route.py`
- `kvk/services/new_source_admin_service.py`
- `ui/views/kvk_source_import_view.py`
- `tests/test_kvk_source_upload_route.py`
- `tests/test_kvk_source_admin.py`
- `tests/test_kvk_source_import_view.py`

### Modify

- `DL_bot.py`
- `bot_config.py`
- `commands/stats_cmds.py`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/ENV_REFERENCE.md`
- `tests/test_kvk_all_upload_route.py`
- `tests/test_kvk_admin_service.py`

## 12. Implementation Requirements

Route a distinct configured channel before legacy/fallback routing; reject channel collisions and never let a recognized malformed source file fall through. One workbook per confirmation. Enforce guild and role checks in handlers and callbacks; channel ACL alone is insufficient. Bind short-lived confirmation controls to their owner and persist receipts for explicit resume.

Add grouped `/kvk_admin source` actions status, resume, accept, finalize, correct and configure, with no activation action. Preserve existing decorators and grouped command inventory. Finalization, source-content correction and config approval require authorized controls and an audit reason.

Add KVK_SOURCE_INTAKE_ENABLED=false and KVK_SOURCE_RECOVERY_ENABLED=false, channel ID 0, empty role IDs and unset private artifact root. Do not configure real roles/channels or enable flags. Disabled behavior must preserve the legacy route without requiring new SQL objects.

All slices retain B0 eligibility/attribution, exact endpoints, total-deaths player DKP and supplied
aggregate authority. Interim 11−10 then 12−10; EndScanID=13 gives 13−10; authorized update to 14
is itself correction authority for 14−10 without a second command. Pending desired endpoint cannot
label an older result current/final. It does not authorize weight/map/roster/source-content changes.
Daily namespaces remain separate; aggregate uploads/re-exports do not allocate a new player scan.

### Command Surface Governance

Add one grouped /kvk_admin source subcommand with action options; zero top-level additions. Update canonical grouped inventory, preserve decorators/visibility and test real options. No APPROVED_TOP_LEVEL_COMMANDS change for this grouped addition.

## 13. Refactor Decisions

Only new-source extraction and adapters in this manifest. Retain legacy behavior while preventing
its null-to-zero, upload-time, growing-roster and aggregate-recalculation rules leaking into new
source. No generic exporter/ProcConfig cleanup. Inspect helper semantics before reuse; expanding
the manifest requires bounded review, not opportunistic refactoring.

## 14. Testing Requirements

Scenario ownership: T01, T09–T19, T41–T45, T54, T64; permission, owner, timeout, duplicate and disabled-route regressions.

- `python -m pytest -q tests/test_kvk_source_upload_route.py tests/test_kvk_source_admin.py tests/test_kvk_source_import_view.py tests/test_kvk_all_upload_route.py tests/test_kvk_admin_service.py tests/test_validate_command_registration.py tests/test_command_inventory.py tests/test_command_registration_smoke.py`

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

Rollback: Disable intake; retain persisted receipts, facts and publications. Preserve legacy channel behavior.

## 17. Proposed PR Summary

Describe concrete behavior, exact manifest, actual tests/security target, dependencies and rollback
limits. Keep private player rows/credentials/findings out of Git. No PR creation authorized by
preparation. End with slice status and next required gate.

**Prepared only. S5A G3 pending; no implementation executed.**


## S4B closeout prerequisite and documentation carry-forward - 2026-09-11

S4B is accepted, successfully synthetic-smoke tested and merged through mirror #269 and private #576.
Local main is synchronized at `64f6b058c224e749ece334d66cdf0efc81bd983d`; production/main is
`63fcb392385fd2ccad78801cbd4f8bd70f426cc3`; SQL main is `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
No changes have been pulled to the bot machine, per operator. S1/S3B/S4A/S4B prerequisites are accepted.
S5A is ready for a new-chat scope/implementation handoff with explicit S5A G3; this docs request does
not supply that approval. Fresh execution must recheck refs, dirty files and authoritative contracts.
Use the [archived S4B evidence](archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S4B%20Versioned%20Exports%20and%20Delivery.md).
Final review fixes passed 150 focused tests and 3,940 full-suite tests with 34 skipped in each checkout,
operational logs unchanged. Historical successful real-SDK synthetic smoke is retained separately;
no post-merge live smoke or deployment is claimed. S5B-REC01 and S6-OPS01/PERF01/CAP01 remain open.

### Required documentation manifest for the eventual S5A PR

This is an explicitly authorized documentation-only addition to section 11; it does not expand its
runtime/test boundary. Include every path below when an S5A PR is separately authorized, including
untracked Markdown, both deleted source paths and both archive destinations. Preserve full evidence,
repaired links and prior archive history. Do not drop these changes when creating a branch/worktree.
The runtime section's instruction not to rewrite unrelated indexes does not exclude these named
closeout changes. Recheck the exact diff before staging; do not stage unrelated files. The S5A PR
summary must state S4B accepted/merged, local pulls complete, bot-machine untouched, routing disabled,
and retain the named S5B/S6 gates. Production promotion must carry the same documentation delta.

- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/kvk_source_migration/decision_and_evidence_register.md`
- `docs/reference/kvk_source_migration/phase_2_implementation_plan.md`
- `docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md`
- `docs/reference/local_sql_development.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S4B Versioned Exports and Delivery.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S5A Private Intake and Admin Controls.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S4B Versioned Exports and Delivery.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S5A Private Intake and Admin Controls.md`
- `docs/task_packs/KVK Source Migration - Programme Pack.md`
- `docs/task_packs/README.md`
- `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S4B Versioned Exports and Delivery.md`
- `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S4B Versioned Exports and Delivery.md`
- `docs/task_packs/archive/README.md`

Documentation validation: runtime pytest/import/registration reruns and new Security scans are skipped
for this exact Markdown status/link/archive change, which has no executable/config/permission/SQL effect.
SQL has a separate no-change skip. Run architecture/deferred/security-routing validators, test selector,
Git whitespace and local link/archive checks. Prior runtime tests and security reviews remain historical.
No new files outside the two archive destinations; no runtime helpers or SQL changes; no new deferred debt.

Closeout validation completed: architecture (zero Python files), deferred-document (13 Markdown records), and security-routing checks passed; selector reviewed. Its baseline imports/registration recommendations are explicitly skipped for this documentation-only change. Local Markdown links and both archive moves verified; Git whitespace checks passed. All closeout changes remain uncommitted for the S5A handoff; no push/PR, bot-machine action or later-slice execution performed.


## S5A G3 pre-edit contract review - 2026-09-11

### 1. Summary

The operator explicitly approved S5A G3 in the current task. Historical G3-pending text above
is superseded by that approval. S1/S3B/S4A/S4B acceptance is confirmed by the operator and the
current handoff records; S4B's archived final evidence was read, including successful real-SDK/
disposable-SQL private recovery, public Viewer publication, fresh-client deduplication and
retired-slot reuse. Those historical results are not new S5A validation.

Pre-edit review found a concrete mismatch between the mandatory durable intake/configuration
requirements and section 11's exact file manifest. Runtime implementation has not started.
This is a requested manifest amendment, not a request to reapprove G3 or reopen a predecessor.

### 2. File Manifest

This turn appends only to this task pack. All 15 pending documentation paths in the carry-forward
manifest above remain present in their original tracked/untracked/deleted states. Existing worktrees
and retained databases are untouched. No index, branch or commit mutation was performed.

Verified bot: main / HEAD and origin/main `64f6b058c224e749ece334d66cdf0efc81bd983d`;
production/main `63fcb392385fd2ccad78801cbd4f8bd70f426cc3`.
Remotes: origin `https://github.com/cwatts6/K98-bot-mirror.git`, production
`https://github.com/cwatts6/K98-bot.git`.
Verified SQL: main / HEAD and origin/main `44afa315dd6cbfe9fec101f2a39a62e534f5b583`, clean;
origin `https://github.com/cwatts6/K98-bot-SQL-Server.git`.
These are local Git observations without fetch/pull or fresh remote-service verification.

### 3. New Files

No new repository file. Proposed sole runtime-manifest addition, awaiting approval:
`kvk/dal/new_source_admin_dal.py`.

### 4. Modified Files

Only this evidence appendix was authored. No runtime/config/test modification and no command
registration change. All earlier bytes of this pack and all other pending closeout files are retained.

### 5. SQL Changes

None. Static authoritative snapshots confirm SourceImportAttempt already allows received/validated
states, nullable revision references and bounded JSON provenance. SourceRoster, SourceConfigVersion,
SourcePeriod and SourceAction have the existing version/provenance constraints. No new schema is
proposed. SQL AGENTS.md is absent; sql_schema/README.md, migrations/README.md and
SQL_DATA_MIGRATION_GUARDRAILS.md were read. No SQL connection or deployment command was run.

### 6. Helpers Reused

No code authored. Inspected reuse candidates: SourceImportDAL, Admission, ArtifactStore,
PublicationService, snapshot_endpoint_request, canonical serialization and transaction/lock helpers.
Existing import acceptance, calculation, publication, export and delivery behavior remains unchanged.

### 7. Refactor Findings and Concrete Amendment

This is an in-scope implementation dependency, not unrelated optimisation or a security finding:

- `kvk/dal/new_source_import_dal.py:208` reads outcomes by the complete replay key, with no
  receipt-ID lookup or draft creation API. `_attempt` at line 241 inserts only accepted/duplicate
  outcomes. `_replay` at line 216 rejects a receipt without an accepted revision at lines 236-238.
  Thus it cannot directly persist and then resume a not-yet-accepted metadata confirmation.
- `kvk/dal/new_source_config_dal.py:47` copies an existing approved configuration for an endpoint
  request; a missing base is rejected. No runtime roster/period/initial-config writer was found in
  kvk, services or upload_routes. Existing integration fixtures create those records with test SQL.
- `kvk/dal/new_source_publication_dal.py:452` provides selection/finalize/correct/endpoint-update/
  rollback, not initial configuration onboarding. A SQL enum alone is not a callable onboarding API.

Section 11 says "No wildcard authorizes extra files" and section 13 says "expanding the manifest
requires bounded review". Adding SQL execution to the allowed admin service or views would violate
section 10's DAL ownership. In-memory or ad-hoc JSON confirmations would not satisfy SQL-backed
receipt/resume requirements. A mock-only protocol without a concrete persistence adapter would not
be a complete S5A implementation.

Proposed amendment: add only `kvk/dal/new_source_admin_dal.py` to section 11 Create. It would own
parameterized draft-receipt persistence and actor/guild/source-scoped reload, immutable approved
roster/period/config onboarding and the reads needed to compose existing accepted-input/publication
APIs. Use existing schema, transaction/lock order, artifact validation and idempotent acceptance;
retain uncertain outcomes for reconciliation. Domain authorization/metadata policy stays in the
already-approved admin service. Use the already-listed `tests/test_kvk_source_admin.py` for fake
connection/repository contract and negative tests. No additional test path or SQL change is requested.
Any further proven manifest need must be reviewed explicitly before authoring it.

The eventual implementation must retain either-endpoint updates, EndScanID >= StartScanID,
equal-endpoint B0 zeros/aggregate not-applicable, ordinary missingness, 11-10 then 12-10 interim,
13-10 final and authorized 14-10 replacement without another correction command. Semantic
re-exports, aggregate reports and daily SCANORDER retain their separate identities. S5B's config
hook/background recovery and all S6 operations remain outside this proposal.

### 8. Test Plan with Actual Outcomes

No S5A behavioral tests were run: no implementation exists yet. Focused/full pytest, log-noise,
imports, registration and runtime pre-commit checks are skipped for this documentation-only preflight;
no historical test count is represented as a new pass. Section 14 remains the required implementation
validation plan after the manifest issue is resolved. Documentation checks are recorded below.

### 9. Security Review Decision and Evidence

Bot: documented skip for this appendix only, which records scope/evidence and changes no executable,
permission, configuration, input, SQL or persistence behavior. No implementation patch exists to scan.
SQL: separate no-change skip at `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
Future implementation still requires a task-only Changes review, Deep off, at its actual immutable
bot target. Preserve pending S4B documentation without including it as unrelated runtime scan input.
No scan was started and no S5A security pass is claimed.

### 10. Deployment Steps

None. No pull/reset/merge/push/PR, production SQL, real import/export, Discord action, restart,
deployment, activation or bot-machine action. No private player data or credentials read or added.
Routing remains disabled. No automatic predecessor, successor, subagent or new task execution.

### 11. Deferred Optimisations and Review Gate

No new deferred optimisation. This manifest dependency remains part of S5A, not a deferred substitute
for required functionality. S5B-REC01 and S6-OPS01/PERF01/CAP01 remain open under their named gates.
Next required decision: approve the single-file DAL manifest amendment above. S5A G3 remains
approved; S5A implementation and acceptance remain incomplete.

Documentation validation: architecture passed (0 Python files); deferred validation passed
(13 Markdown files); security-routing passed (0 errors/0 warnings); exact-pack selector reviewed;
Git whitespace passed. Selector baseline import/registration recommendations are skipped for this
nonexecutable appendix. Preservation check passed for all 15 pending path states: the other 14
paths are byte-identical or remain deleted, and this pack retains its complete original byte prefix.
All 129 relative file links across the pending documents resolve; both archive move sides remain
intact; index is empty; SQL remains clean. No runtime tests, runtime review or security scan is
claimed. Pre-commit was not run: this preflight is not PR packaging, and automatic Markdown
normalization must not rewrite the preserved closeout bytes. Start/end repository HEADs are unchanged.


## S5A G3 implementation delivery - 2026-09-11

### 1. Summary

S5A private intake and owner-bound controls are implemented locally for review, with the explicit
G3 approval and subsequently approved single-file DAL amendment. Historical pending/preflight-only
statements above remain preserved as history. **Acceptance is not complete; do not merge or enable.**
Two command-inventory assertions, the canonical security coverage discrepancy, and the scenario
limitations below remain explicit review gaps. No predecessor or later pack was executed.

Default-off intake consumes recognized attachments before legacy routing, checks fresh guild
membership/roles, retains private originals and durable receipts, and offers one grouped
`/kvk_admin source` command with status/resume/accept/finalize/correct/configure. Source acceptance
and configuration approval do not claim publication or delivery. Frozen B0, map/weights, UTC
identity, semantic deduplication and exact endpoints reuse the accepted source contracts.

### 2. File Manifest

Bot remains on main at `64f6b058c224e749ece334d66cdf0efc81bd983d` (also origin/main);
production/main remains `63fcb392385fd2ccad78801cbd4f8bd70f426cc3`.
SQL remains main at `44afa315dd6cbfe9fec101f2a39a62e534f5b583` (also origin/main), clean.
These start/end refs and the previously recorded remotes were rechecked locally without fetching.
The main checkout index remains empty; no feature branch, commit, push or PR was made.

Exactly seven new implementation/test files, seven modified implementation/test/reference files,
and this append-only delivery record are authored. The existing 15-path documentation carry-forward
manifest above remains mandatory for any separately authorized S5A PR, including both archive
rename sides and untracked Markdown. Other pending files remain byte-identical or deleted as
originally recorded; this pack preserves its original byte prefix.

An isolated detached review worktree at `.codex_scan_stage/s5a` contains only the 14 execution
files below over the bot HEAD. It excludes pending S4B documents and this evidence appendix.
The first attempted review worktree `.codex_scan_stage/s5a-private-controls` failed during
materialization because of a Windows path-length limit; its residual state was retained, not
reset or deleted. The successful shorter worktree used per-command long-path support.
All earlier worktrees and retained databases were preserved.

### 3. New Files

- `kvk/dal/new_source_admin_dal.py` - approved manifest addition: owner/guild/source-scoped
  durable draft receipts, optimistic versions, atomic accepted outcome, initial configuration
  onboarding and endpoint requests using existing authoritative tables.
- `kvk/services/new_source_admin_service.py` - authorization, explicit UTC metadata, real
  parser/artifact validation, review/expiry/digest binding, admin actions and bounded summaries.
- `upload_routes/kvk_source_route.py` - disabled distinct private route; one bounded XLSX,
  no malformed-file fallthrough, fresh membership before and after attachment download.
- `ui/views/kvk_source_import_view.py` - owner-bound five-minute views/modals, fresh membership,
  ephemeral review pages, durable resume and retained expected revision/version.
- `tests/test_kvk_source_admin.py` - synthetic service/fake-repository and parameterized
  DAL/transaction tests; no live SQL or private player fixtures.
- `tests/test_kvk_source_upload_route.py` - disabled/malformed/permission/collision/offload tests.
- `tests/test_kvk_source_import_view.py` - owner/guild/channel/timeout/revision-resume/modal tests.

### 4. Modified Files

- `DL_bot.py` - four added lines import/call the route before legacy handlers.
- `bot_config.py` - intake/recovery false, channel 0, empty role IDs, artifact root unset.
- `commands/stats_cmds.py` - one grouped source subcommand with six real action choices,
  receipt UUID and optional expected source revision/version; existing decorators retained.
- `docs/reference/canonical_command_reference.md` - 36 top-level/101 grouped commands,
  eight kvk_admin children, private-control usage and explicit inactive/publication boundary.
- `docs/reference/ENV_REFERENCE.md` - exact default settings and pre-enable ACL requirements.
- `tests/test_kvk_admin_service.py` - real Pycord command-option/invocation checks for all six actions.
- `tests/test_kvk_all_upload_route.py` - route-order regression.
- This task pack - append-only delivery evidence; original scope and S4B closeout bytes preserved.

The run-only manifest includes `tests/test_validate_command_registration.py` and
`tests/test_command_registration_smoke.py`, but the edit manifest does not. Both still assert
100 grouped commands. Their two proposed count-only changes to 101 remain unmade pending the
bounded manifest clarification requested during implementation. Section 11 states
"No wildcard authorizes extra files"; section 13 requires bounded review for expansion.

### 5. SQL Changes

No SQL-repository file changes, migration, schema deployment, SQL connection, real import/export
or database cleanup. The new Python DAL uses existing SourceImportAttempt/Artifact/Observation/
Revision/LogicalScan/Roster/RosterMember/ConfigVersion/WindowConfig/CampConfig/WeightConfig/
ScanBinding/Period/Routing/Selection/Publication/ConfigRequest definitions and existing helpers.
Authoritative snapshots and connection contracts were inspected in the separate SQL repository.

Draft receipts have a separate s5a_draft action key; accepted S3B attempts remain immutable.
The outer transaction owns both acceptance and receipt outcome; borrowed importer commit/rollback
methods do not terminate it. Errors roll back the outer transaction, while uncertain commit
requires durable readback. Season locks precede state checks. No tests here prove SQL Server
locking/concurrency or actual deployed schema/permission parity.

### 6. Helpers Reused

Existing SourceImportDAL, Admission, ArtifactStore, source filename/metadata validators, real
player/aggregate parsers, FrozenWeights, canonical serialization, parameterized row mapping,
transaction/season-lock helpers, snapshot_endpoint_request, safe_defer, send_ephemeral and
existing version/safety/usage decorators. No duplicated DKP, aggregate summation, daily SCANORDER,
exporter or publication implementation was introduced.

Distinct player scans retain the accepted DAL's increasing ScanID/UTC check; semantic re-exports
reuse acceptance identities. Aggregate acceptance never allocates a player scan. Either endpoint
may change; a supplied end below start is rejected. Equal-endpoint configuration is accepted,
aggregate acceptance is rejected as not applicable, and accepted pure reporting tests retain zero
supported fight scores for every B0 member. Ordinary missing values remain explicit.

### 7. Refactor Findings

The pre-edit durable-receipt/initial-onboarding DAL gap was implemented in the specifically approved
new DAL file. Business rules remain in the service; commands/routes/views contain no SQL.
Review fixed expired configuration re-preparation, expected revision preservation on resume,
and accidental map/weight/coverage replacement during new-period onboarding.

Existing roster replacement is rejected, not silently implemented as growth. Full T45 explicit
roster-version correction and impact-preview workflow is **not delivered** by these controls.
This is a disclosed acceptance gap, not a newly accepted deferred optimisation or an implicit
authorization for another pack. No general reliability, exporter or ProcConfig refactor.

### 8. Test Plan with Actual Outcomes

All runs used `.venv/Scripts/python.exe`, synthetic fixtures and mocks. No disposable/live SQL
opt-in target or operations were authorized; the SQL integration tests remained skipped.

| Check | Actual outcome |
|---|---|
| Exact section 14 eight-file pytest command, final files | 144 passed, 2 failed in 6.16s |
| New/modified source-control behavioral suites (five files) | 109 passed in 3.82s |
| Full pytest through log-noise wrapper, final files | 4,015 passed, 34 skipped, 2 failed in 148.29s |
| Log-noise wrapper, only the two known count assertions deselected | 4,015 passed, 34 skipped, 2 deselected in 147.46s; operational logs unchanged |
| Architecture validator, exact seven runtime Python paths | Passed |
| Deferred-document validator | Passed, 15 Markdown files |
| Codex Security routing validator | Passed, zero errors/warnings |
| Exact 14-path test selector | Reviewed; focused tests, UI imports, full suite, smoke/registration recommendations covered |
| Task-file pre-commit | Passed applicable EOF/conflict/line-ending/size/Ruff/Black/Pyright/logging/registration hooks |
| Direct task-file Gitleaks stdin scan, redacted | Passed; about 267,051 bytes, no leaks |
| Import smoke in test mode | Passed |
| Command-registration validator | Passed: 36 top-level, 101 grouped, kvk_admin eight; no duplicate/drift |
| Git whitespace and empty main index | Passed |

The two failures are exactly the 100-versus-101 assertions named above; do not call full/focused
pytest green. The full wrapper exits before its log comparison on pytest failure, so the separate
deselected run is the actual log-hygiene evidence. Pre-commit initially hit the sandbox's read-only
cache, then succeeded with reviewed cache access. Its staged Gitleaks hook saw an empty main index;
the additional direct scan above provides actual task-file secret-check coverage. No private
workbook bytes, credentials, operational-log contents or vulnerability details were added to Git.

Scenario evidence is bounded:

- T01/T09-T19: fresh synthetic S5A admission/UTC/dedup/malformed-input tests plus accepted parser
  regressions in the fresh full run. No real workbook ingestion is claimed.
- T41-T44: owner/admin, expected revision, live/final source-acceptance controls and accepted DAL/
  reporting regressions are exercised. A complete command-to-selected-publication transition,
  external intent and cross-publication correction workflow are not demonstrated by these mocks.
- T45: frozen-roster/no-growth rejection verified; explicit roster-correction version/impact preview
  remains an implementation/acceptance gap.
- T54/T64: stale receipt/config/revision, role loss, wrong guild/channel/owner and expiry/resume
  negative cases pass. A real restarted Discord process and SQL concurrency are not proven.
- Interim 11-10/12-10, final 13-10, authorized 14-10 replacement, equal-endpoint zeros and explicit
  missingness retain accepted calculation/publication contracts and fresh regression coverage.
  S5A records approved endpoint requests without another correction command; it does not execute
  S5B processing or label an older publication current/final.

### 9. Security Review Decision and Evidence

Bot: Changes review, Deep off, exact detached task-only target
`C:/discord_file_downloader/.codex_scan_stage/s5a`.
Base/head `64f6b058c224e749ece334d66cdf0efc81bd983d`;
snapshot `codex-security-snapshot/v1:sha256:5e4babe37c631377e2f0680fd08b67984d84e80144a20bbf1e672d77dc3d2c0a`.
Scan `7878ed68-a1f2-4d95-afb5-96cd86fa605c` completed and sealed at
2026-09-11T21:52:39.117388Z with **zero findings**. Daybreak status granted, program Daybreak Blue.
No token-usage measurement was returned.

Important canonical evidence gap: the sealed coverage is **partial**. The final semantic draft
recorded completed reviews for all seven runtime files (plus five tests/two docs) and an empty
deferred list, but the workbench retained the earlier dal-review "in progress" checkpoint when
merging coverage. The independent DAL review did finish and its no-candidate evidence appears in
the same final surfaces. This discrepancy is preserved and disclosed; no sealed artifact was
altered and no second scan/completion or broader audit was launched. **The security gate is not
represented as an unqualified complete-coverage pass.** Review requires resolving this discrepancy.

The security workflow used its required dedicated capability-preflight worker, independent
architecture review and bounded DAL discovery worker within this task; no new user-facing task
was created. All discovery candidates were recorded once (empty); candidate validation/attack-path
phases were not applicable. Private canonical artifacts remain outside Git in the tool-owned scan
directory. Source/SQL targets were never combined.

SQL: separate no-change skip at `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
This appendix has a docs-only scan skip; it adds no executable/configuration behavior. Actual ACLs,
live SQL target/permissions/concurrency and later publication/recovery integration remain unverified.

### 10. Deployment Steps

None authorized or performed. No pull/reset/merge/push/PR, production SQL, real imports/exports,
Discord actions, bot-machine access, restarts, deployment or activation. Intake/recovery defaults
remain false; source routing is not enabled. No files or databases were deleted.
Future rollback remains disable intake and retain receipts/originals/facts/publications while
preserving legacy routing; this delivery performs no rollback or operational action.

### 11. Deferred Optimisations and Review Gate

No new unrelated optimisation item. Existing S5B-REC01 and S6-OPS01/PERF01/CAP01 remain open and
are not closed by mocked S5A evidence. Do not execute their packs automatically.

**Review verdict: Do not merge yet.** Review the two count-only manifest updates, the explicit
scenario/roster-correction gaps and canonical partial-security-coverage discrepancy. G3 approval
does not self-approve acceptance, PR creation or activation. Implementation is retained locally
as a reviewable S5A draft; the full carry-forward manifest and archived S4B evidence remain intact.

Final delivery verification: all 14 execution files match the sealed scan snapshot byte-for-byte;
all 129 relative links resolve; original closeout bytes and archive sides remain preserved;
deferred/security-routing/whitespace checks pass. Main index remains empty and SQL remains clean.

## Canonical S5A gap-closure delivery - 2026-09-11

This appendix supersedes the earlier incomplete delivery verdict for the revised local patch.
Earlier evidence and failed outcomes remain historical; none were rewritten.

### 1. Summary

Operator-authorized S5A gap closure implemented: the two command-count tests now expect 101,
every high-level command is checked against the 25-child limit, explicit B0 roster correction
has a reviewed diff/retention plan and appends a new version, and real publication-service
composition is exercised with fake persistence and empty destinations. The exact revised
patch has a sealed complete-coverage Changes review with zero findings. Stop for S5A review.

### 2. Scope and Repository Evidence

S1, S3B, S4A and S4B acceptance and explicit S5A G3 remain the prerequisites recorded above.
Current instructions, core references, approved architecture including EndScanID, Phase 2B
plan, pack and archived S4B evidence informed this work. No other pack was executed.

Bot remains main at `64f6b058c224e749ece334d66cdf0efc81bd983d`, matching local origin/main;
production/main remains `63fcb392385fd2ccad78801cbd4f8bd70f426cc3`.
Remotes remain origin `https://github.com/cwatts6/K98-bot-mirror.git` and production
`https://github.com/cwatts6/K98-bot.git`. Main index is empty; pending work is unstaged/untracked.
SQL remains clean on main at `44afa315dd6cbfe9fec101f2a39a62e534f5b583`, matching local
origin/main, with origin `https://github.com/cwatts6/K98-bot-SQL-Server.git`.
These are local observations; no fetch or pull was performed.

The full exact 15-path documentation carry-forward manifest at lines 209-223 remains mandatory
alongside the execution manifest below for any separately authorized S5A PR. Preserve both S4B
archive rename sides, untracked Markdown, repaired relative links and all delivery evidence.
The original pack byte prefix and other pending closeout documents are preserved. Existing
review worktrees and retained databases are untouched. No review-target directory belongs in a PR.

### 3. New Files

- `kvk/dal/new_source_admin_dal.py`
- `kvk/services/new_source_admin_service.py`
- `upload_routes/kvk_source_route.py`
- `ui/views/kvk_source_import_view.py`
- `tests/test_kvk_source_admin.py`
- `tests/test_kvk_source_upload_route.py`
- `tests/test_kvk_source_import_view.py`

The DAL addition retains its explicit manifest approval. Roster correction requires a selected
revision of the same original B0 observation, records added/removed/changed member provenance,
checks the current selection guard under the season lock and inserts a new roster/version.
It does not rewrite existing configurations, memberships or historical publications.

### 4. Modified Files

- `DL_bot.py`
- `bot_config.py`
- `commands/stats_cmds.py`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/ENV_REFERENCE.md`
- `tests/test_kvk_admin_service.py`
- `tests/test_kvk_all_upload_route.py`
- `tests/test_validate_command_registration.py` - newly authorized count/limit assertion edit.
- `tests/test_command_registration_smoke.py` - newly authorized count/limit assertion edit.

These nine modified files plus seven new files are the exact 16-file execution/security manifest.
This task pack receives append-only evidence separately. The existing source subcommand gains
the boolean `roster_correction` option for configure; no additional command child is introduced.
Each affected selected publication must be listed once as `UUID | retain` before confirmation.
Ordinary configure still cannot replace B0. Later adoption of a corrected roster by existing
publications requires its own reviewed correction; no historical adoption is performed here.

### 5. SQL Changes

None in the SQL repository. Python queries were checked against authoritative existing definitions.
Fake cursors verify bound parameters and append-only roster writes; transaction tests exercise
rollback/uncertain-commit paths. No SQL target, connection, schema deployment or database deletion
was performed. Live SQL locking, concurrency and actual permission parity are not proven.

### 6. Helpers Reused

The prior delivery's import, artifact, metadata, parser, transaction, interaction and endpoint-request
helpers remain reused. New composition tests use the real PublicationService and calculation
models with a fake DAL. B0 eligibility, exact endpoints, explicit UTC scan start and semantic
re-export identity remain intact. Distinct scans increase ScanID and UTC; ordinary missingness
remains explicit. Aggregate reports and daily SCANORDER remain separate.

### 7. Refactor Findings

The earlier missing T45 workflow is now implemented within configure: explicit same-B0 correction,
diff preview, complete publication-retention plan, durable confirmation and a new roster version.
No general refactor or unrelated optimisation was introduced. Historical selections remain pinned.

### 8. Test Plan with Actual Outcomes

All tests used synthetic fixtures, mocks and fake destinations. Final revised-file outcomes:

| Check | Actual outcome |
|---|---|
| Exact section 14 eight-file pytest command | 162 passed in 5.53s |
| Full pytest through log-noise wrapper | 4,033 passed, 34 skipped in 142.61s; operational logs unchanged |
| Architecture validator, seven runtime paths | Passed |
| Deferred-document validator | Passed, 15 Markdown files |
| Security-routing validator | Passed, zero errors/warnings |
| Exact 16-path test selector | Reviewed; focused/full/UI/import recommendations covered |
| Exact task-file pre-commit | All applicable hooks passed after formatting, including Ruff/Black/Pyright/registration |
| Direct redacted Gitleaks stdin scan of 16 files | 323,208 bytes; no leaks |
| Test-mode import smoke | Passed |
| Command registration | 36 top-level, 101 grouped, kvk_admin 8; largest group ops 24; every group <=25 |
| Main index / SQL working tree / whitespace | Empty / clean / passed |

T45 tests cover role loss, stale/expired review, missing or rewriting publication plans, later-B0
substitution, unselected revisions, new kingdom rejection and append-only version/member writes.
Pycord invocation verifies the boolean option and private response. Resume retains the roster mode.

Mocked publication composition now takes an S5A-accepted final aggregate through the real
PublicationService, checks final calculation/selection arguments and uses no external destinations.
It exercises interim 11-10 then 12-10, final 13-10, and an S5A-approved EndScanID 14 request leading
to replacement 14-10 through endpoint_update without a separate correction command. Equal endpoints
retain zero supported fight scores for all B0 members and aggregates not applicable in regression
coverage. This is component composition, not an executed S5B worker or live command-to-SQL workflow.
The 34 skips remain skips; no disposable SQL target was authorized.

### 9. Security Review Decision and Evidence

Bot Changes review, Deep off, exact detached target `C:/discord_file_downloader/.codex/s5a-review2`;
base/head `64f6b058c224e749ece334d66cdf0efc81bd983d`;
snapshot `codex-security-snapshot/v1:sha256:59ba5c46ba55925335d78c5ad63c2fc8356c963253ac6a41a46a2fecdf3a9489`.
Scan `541665eb-2d37-4e14-8ce9-038329bf9653` sealed at 2026-09-11T22:18:44.627158Z.
Readback confirms **complete coverage, zero findings, empty deferred candidates** for this patch.
All seven runtime files and nine supporting test/reference files were reviewed. Required capability
preflight, independent architecture and bounded DAL discovery completed; Daybreak Blue access was
granted. No measured token usage was returned. No standard/deep scan or new user-facing task.

The earlier partial scan remains unchanged historical evidence. This fresh review covers the revised
16-file patch and resolves its coverage gap; sealed artifacts were not repaired or rewritten.
SQL has a separate no-change skip at `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
This evidence appendix has a docs-only skip. Private canonical artifacts stay outside Git.
Actual channel/filesystem ACLs, live SQL permissions/concurrency and S5B integration remain unverified.

### 10. Deployment Steps

None performed or authorized. Intake/recovery remain default false and routing disabled. No
pull/reset/merge/push/PR, production SQL, real imports/exports, Discord actions, bot-machine changes,
restart, deployment or activation. Retained databases and prior work are preserved.

### 11. Deferred Optimisations and Review Gate

No new unrelated deferred item. S5B-REC01 and S6-OPS01/PERF01/CAP01 remain open; they do not block
this mocked S5A review and were not executed. The previously identified S5A implementation/test
and security-evidence gaps are closed within the authorized mocked boundary described above.
**Ready for operator S5A review; acceptance, PR creation and activation are not self-approved.**

Final readback: all 16 execution files match the sealed target byte-for-byte; all 15 closeout paths
and the original pack prefix are preserved; all 129 relative links resolve. Deferred/routing and
whitespace checks pass. Both HEADs/remotes are unchanged, the main index is empty and SQL is clean.

## Operator acceptance and PR authorization - 2026-09-12

The operator reviewed and accepted S5A, then explicitly authorized creating the mirror PR and
marking it ready for review. This supersedes the pending operator-review gate above. The PR carries
the exact 16 execution files and all 15 documentation paths, including both S4B archive rename sides.
Runtime/test bytes remain identical to the sealed Changes target; existing passing validation and
security evidence apply. This acceptance/authorization note changes documentation only.
Production promotion, merge, deployment, activation and later packs remain separately gated.
