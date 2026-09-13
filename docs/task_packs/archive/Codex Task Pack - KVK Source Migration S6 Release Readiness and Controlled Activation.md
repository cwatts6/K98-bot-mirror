# Codex Task Pack — KVK Source Migration S6 Release Readiness and Controlled Activation

> **Archived 2026-09-12: S6 evidence delivery is merged and operator accepted.**
> This pack is retained history, not executable instructions. Public routing and
> residual release gates remain open; no activation is claimed.
> Next: [S7 planning](../Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md). Exact closeout: [handoff](../../reference/kvk_source_migration/post_s6_handoff_log.md).

> **2026-09-12 PR #272 routing review correction:** Public runtime routing is an
> OPEN implementation prerequisite. The current code does not consume
> SourceRouting.Enabled to switch ordinary readers to V2. The routing-row update
> below is only a conditional design and must not run until a separately approved,
> reviewed, deployed and accepted public routing consumer exists. Synthetic
> rehearsal acceptance does not close this gap or establish activation readiness.


> **2026-09-12 mirror PR authorization:** Chris Watts explicitly approved committing,
> pushing and opening the complete documentation-only draft PR in K98-bot-mirror.
> This supersedes the preceding pending-PR-permission statements. No merge,
> production promotion or activation is authorized. Rehearsal evidence is accepted;
> unresolved operational gates and all retained uncertain outputs remain preserved.


> **2026-09-12 operator acceptance update:** Chris Watts replied "approved please
> proceed" to the completed rehearsal report. The measured rehearsal outcomes are
> accepted. Outstanding scheduling, capacity/retention and uncertain-publication
> dispositions remain explicit release gates; this is not evidence of their
> resolution. The next proposed external step is the complete S6 documentation
> mirror PR. Its exact commit/push/PR permission is being clarified against the
> earlier explicit prohibition. Production operations remain unexecuted.


> **2026-09-12 S6 authenticated rehearsal update:** The operator restored the ignored
> local credential and approved the 5,806-player × ten-period synthetic benchmark,
> confirming both other importers would remain idle. Actual Google write/readback
> and local K98DEV rehearsal evidence now supersedes the earlier credential blocker.
> S6-OPS01, S6-PERF01 and S6-CAP01 remain OPEN for operator acceptance and the exact
> unresolved operational gates recorded in the latest appendix of both release
> documents and the S6 pack. No production activation or G5 acceptance is claimed.


> **2026-09-12 S6 output-provisioning update:** Separate S6 output creation was
> approved and completed: one private index and eight private slots, owner and
> service-account Editor metadata verified. Operator expectation is 2–3 exports/day,
> with no fixed maximum duration. Code review found no common lock across S6,
> all-KVK export and scan-data import. Runtime Google rehearsal is currently blocked
> by the missing configured local service-account key; no provider interruption or
> representative-load pass is claimed. All three S6 gates remain OPEN. See the latest
> provisioning appendix in the two release documents and S6 pack.


> **2026-09-12 S6 rehearsal update:** Chris Watts subsequently approved a local
> K98DEV database and beginning rehearsal. Synthetic local SQL/process checks passed
> in `K98_S6_Disposable_20260912`; no production activation occurred.
> S6-OPS01, S6-PERF01 and S6-CAP01 remain OPEN pending provider evidence and operator
> acceptance. Earlier G3-only/no-rehearsal statements below describe the retained
> preparation checkpoint, not the subsequent local rehearsal. See the dated
> rehearsal appendix in both S6 release documents for exact outcomes and gaps.


> Current 2026-09-12: explicit S6 G3 approved documentation/evidence preparation only.
> Prepared release evidence; stop at G4, with OPS01/PERF01/CAP01 open and G5 operator-owned.
> Historical prepared/pending wording below is retained as the original template, not current status.
> See [canonical S6 delivery](../../reference/kvk_source_migration/release_evidence_log.md).


## 1. Task Header

- Prepared 2026-09-09; handover refreshed 2026-09-12 after S5B merge; owner Chris Watts.
- G2 architecture approved, including authorized EndScanID corrections. **S6 G3 pending.**
- One-pass implementation approved: **No**. Execute only after explicit approval of this slice.
- Proposed isolated branch `codex/kvk-source-s6`; not created during planning.
- Type: release evidence preparation.

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

Prepare an evidence-backed activation and rollback packet, then stop for G4 operational approval.

## 4. Background

Historical planning anchors (superseded for execution by the S5B closeout below): bot main `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; SQL main
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`. Recheck branches/HEADs/remotes/status at execution,
preserve existing work and record actual start/end hashes. Local definitions are not deployed proof.
No pull/reset/checkout to make a working copy match historical evidence. Use an authorized isolated
branch/worktree where needed. Phase-1 C01-C65 anchor dependencies; G2 fixes source semantics.

## 5. Scope

Predecessors: All preceding slices accepted; explicit S6 G3 authorizes evidence preparation only; separate G4 approval required for live actions.

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

Current pack authoring: bot docs-only skip; SQL no-change skip. Future execution: Bot docs-only skip for readiness evidence; SQL no-change skip. Re-evaluate any operational or implementation delta separately.
Use k98-security-review-routing first; record exact immutable base/head or task-only authored patch,
Scan type Changes and Deep off. Never scan/stage unrelated dirty files or combine bot/SQL histories.
No routine standard/deep audit. Retain scan coverage/results privately; no public finding details.

## 8. Mandatory Workflow

1. Confirm explicit S6 approval and predecessor evidence; otherwise scope/review and stop.
2. Capture worktrees and exact manifest; recheck drift and source/SQL contracts before edits.
3. Implement only the approved boundary with assigned tests; preserve unrelated work.
4. Run checks, review exact diff/security target and report actual outcomes/limitations.
5. Stop at delivery; no automatic next task, G4 action or self-approval.

## 9. Focused Audit Requirements

Inspect section 11 read paths for helper semantics, layering, period/identity/availability and
regression contracts. Static source continuity does not prove current live rows/jobs or external
readers. Operator-attested SQL/config parity remains separately labelled. No credential discovery
or RDP required for this planning/implementation boundary. Evidence condition: Live rows/jobs, deployment state, permissions and recovery proof are mandatory before G4 activation, not prerequisites for S1.

## 10. Architecture Targets

kvk/models and kvk/schemas own pure types; kvk/services business rules; kvk/dal parameterized SQL,
transactions and mapping; commands/routes/views thin adapters. New SQL only in the SQL repository.
Follow the implementation-plan interfaces/lock order and approved source/field dictionary.
No second domain implementation in DL_bot.py or gsheet_module.py; no duplicated SQL calculation.

## 11. Exact File Manifest

All paths below are relative to **C:/discord_file_downloader**.
New files are proposed, not present yet; predecessor-created modifications require accepted delivery.
No wildcard authorizes extra files. Append implementation evidence to this pack after execution;
include the specifically listed closeout indexes; do not rewrite unrelated indexes. Migration date/sequence is the sole controlled allocation exception
in implementation-plan section 4; final name must be recorded before authoring and never renamed after merge.

### Read only

- `docs/reference/Promotion Guide.md`
- `docs/reference/runbook_devops.md`
- `docs/reference/ENV_REFERENCE.md`
- `docs/reference/runbook_startup.md`
- `docs/reference/runbook_shutdown.md`

### Create

- `docs/reference/kvk_source_migration/release_readiness_and_rollback.md`
- `docs/reference/kvk_source_migration/release_evidence_log.md`

### Modify / preserve closeout documentation

- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/kvk_source_migration/decision_and_evidence_register.md`
- `docs/reference/kvk_source_migration/phase_2_implementation_plan.md`
- `docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md`
- `docs/reference/local_sql_development.md`
- `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S6 Release Readiness and Controlled Activation.md`
- `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S6 Release Readiness and Controlled Activation.md`
- `docs/task_packs/KVK Source Migration - Programme Pack.md`
- `docs/task_packs/README.md`
- `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S5B Endpoint Config and Recovery Integration.md`
- `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S4B Versioned Exports and Delivery.md`
- `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S5B Endpoint Config and Recovery Integration.md`
- `docs/task_packs/archive/README.md`

### Archive move sources (carry deletion side into PR)

- `docs/task_packs/Codex Chat Starter - KVK Source Migration S5B Endpoint Config and Recovery Integration.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S5B Endpoint Config and Recovery Integration.md`

These are two moves into the archive paths above, not deletion of historical evidence.
The closeout carry-forward is exactly 14 documents / 16 Git paths; S6 adds its two Create paths.
No other file is authorized by this manifest.

## 12. Implementation Requirements

Record actual accepted commits, schema/config capabilities, B0 mappings, jobs/editors, permissions, backups and external consumers. Label operator attestation separately from independently queried evidence. Use only authorized read-only access; do not discover credentials or invent connection targets.

Prepare concrete target-specific steps: SQL deployment with routing off, bot deployment with flags off, isolated private shadow validation, export/version checks, backup/reconciliation and explicit activation. These are proposed steps, not authorization to run them. No activation helper currently exists; prepare the precise transaction preview with expected routing/selection versions and capability checks for G4. Any required new helper code needs a separately approved bounded implementation manifest.

This slice edits documentation only. Do not run production smoke tests, migrate, import, export, send Discord messages, restart or deploy. Stop at G4. G5 acceptance is also operator-owned. Do not wait for a later fight or final overall report to prepare readiness.

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

Scenario ownership: G4 evidence for T17, T35–T43, T46–T59, T61–T62, T64–T70.

- Validate document links, exact manifests and cited source/commit evidence. Operational smoke tests remain proposed until separate G4 approval; report unavailable live evidence explicitly.

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
- [ ] Complete closeout carry-forward manifest included in the eventual S6 PR, with both archive move sides and repaired links verified in Files changed.

## 16. Required Delivery Output

Use canonical eleven parts: Summary; File Manifest; New Files; Modified Files; SQL Changes;
Helpers Reused; Refactor Findings; Test Plan with outcomes; Security Review Decision and Evidence;
Deployment Steps (none unless separately approved); Deferred Optimisations.

Rollback: Readiness edits are reversible documentation. Operational rollback must identify exact routing/config versions and compatible legacy evidence; do not promise a valid legacy fallback without verification.

## 17. Proposed PR Summary

Describe concrete behavior, exact manifest, actual tests/security target, dependencies and rollback
limits. Keep private player rows/credentials/findings out of Git. No PR creation authorized by
preparation. End with slice status and next required gate.

**Prepared only. S6 G3 pending; no implementation executed.**


## Required S4B operational evidence handoff - 2026-09-11

Read the [named follow-up register](../../reference/kvk_source_migration/phase_2_implementation_plan.md#s4b-follow-ups). Carry **S6-OPS01, S6-PERF01 and S6-CAP01** as explicit open activation gates into both planned release documents. Owner: S6 readiness author for the plan/evidence, Chris Watts for operational approval and acceptance.

- [ ] S6-OPS01: prepare exact disposable targets and process-interruption points for private writes, Viewer grants and current-pointer updates. Require durable phase/fence/receipt, external readback, quarantine/uncertainty handling and no duplicate publication after restart.
- [ ] S6-PERF01: agree acceptable duration/cadence and shared request budget before measuring representative multipart synthetic uploads and complete readbacks. Record player/period volumes, actual API counts, bytes/cells, elapsed time and quota/retry outcomes; account for other service-account consumers without running production operations.
- [ ] S6-CAP01: size current/staging, final/reference retention and private-recovery quarantine, verify exact provisioned owner/Editor/canShare/audience configuration, and rehearse insufficient slots/bounded receipt exhaustion with safe fail-closed handling. Nine initial files is not a lifetime cap. Any new code/schema helper needs separate bounded approval.
- [ ] Include evidence paths, exact revisions/targets, actual outcomes and operator acceptance or an explicit unresolved blocker for every ID. Do not mark activation ready while any gate lacks its required evidence.

S6 remains documentation-only through G3. Prepare concrete reviewable rehearsal steps and stop for separate G4/exact-operation authorization before execution. This handoff grants no live SQL, file write, message, restart, deployment or activation permission and does not run the future pack.


## S5B accepted closeout and S6 entry - 2026-09-12

S5B is complete, accepted, successfully smoke tested and merged (#271/#578). Read the
[archived S5B delivery](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S5B%20Endpoint%20Config%20and%20Recovery%20Integration.md).
Local mirror main/origin main is 85f303f6bd82bdc9a5cfc2d713da5480e1fa694a, synchronized from
production merge c7e063f02ebe8287a584d0054ea14f91a0c0ecc6 and containing review fix e5bbd8f7.
SQL main is 44afa315dd6cbfe9fec101f2a39a62e534f5b583. These are entry anchors, not instructions
to reset or overwrite work; recheck both repos and their remotes, branches, HEADs and status.
The operator confirms local pulls complete and **no bot-machine pull**. Smoke acceptance is
operator-reported with recorded local synthetic integration/import evidence; no fresh post-merge
or bot-machine smoke is claimed. All preceding slices stay accepted; S5B-REC01 is closed.
Retain the exact tested revisions, scan targets and disposable databases; do not rerun predecessors.

Start S6 in a new chat only after explicit S6 G3. That permits documentation/evidence preparation
only, not rehearsal execution. Carry S6-OPS01, S6-PERF01 and S6-CAP01 into both proposed release
documents as open gates until separately authorized evidence is measured and accepted. G4/exact
operations and G5 acceptance remain operator-owned. No live SQL, bot-machine update, restart,
real import/export, Discord action, deployment or activation is authorized by this handover.

Preserve every pending closeout documentation change, including untracked archive files and both
rename sides, from the pack's exact carry-forward manifest. Include these changes alongside S6's
new readiness documents in the eventual separately authorized S6 PR; do not omit them as pre-existing
work. Verify the final PR Files changed list contains the complete manifest (or prove specific paths
were already merged), repaired links and the updated evidence. Carry approved documentation through
later separately authorized production promotion as well. No PR is created by this handover.


## Closeout validation decision - 2026-09-12

This handover updates Markdown status, archive links and the exact S6 documentation PR manifest only.
No runtime, configuration, dependency, permission, SQL, deployment or persistence behavior changes.
Security routing: bot documentation-only skip; SQL no-change skip. No new scan is warranted.
Validate local links, archive moves, matching status blocks and the exact manifest; run architecture,
deferred-items, security-routing and test-selection validators plus applicable Markdown hooks.
Runtime pytest, SQL integration and smoke/registration reruns are skipped for this documentation-only
patch; prior S5B outcomes remain explicitly historical. No additional optimisation item was found.


Closeout checks completed: architecture (0 Python paths), deferred-items (14 Markdown documents),
security-routing (0 errors/warnings) and test selector passed. Applicable documentation pre-commit
hooks passed. All local Markdown link paths in the changed documents resolve; the nine current
status blocks are identical; section 11 matches all 16 pending Git paths exactly. Both S5B archive
sources are absent and their destinations retain the historical records. No runtime/SQL/test file
changed. Documentation remains local and uncommitted for S6 carry-forward; no PR or new chat created.


## S6 G3 evidence preparation delivery - 2026-09-12

This dated record supersedes the historical G3-pending/prepared-only text above.
**Evidence preparation delivered; stopped at G4. Activation is not ready; G5 is operator-owned.**
The [canonical S6 evidence log](../../reference/kvk_source_migration/release_evidence_log.md)
contains the complete exact manifest, historical test/security identities, actual validation and gaps.
The [release readiness and rollback packet](../../reference/kvk_source_migration/release_readiness_and_rollback.md)
contains proposed operations only, with unbound live values and explicit stop conditions.

### 1. Summary

Explicit S6 G3 and all preceding acceptance evidence were confirmed before edits. S5B-REC01 remains
closed. S6-OPS01, S6-PERF01 and S6-CAP01 are OPEN in both release documents; no measurement or
operational acceptance is invented. The approved B0, exact endpoints, UTC scan start, semantic
re-export deduplication, 11−10 / 12−10 / 13−10 / authorized 14−10 and namespace contracts remain.

### 2. File Manifest

Exactly section 11: 16 carried Git paths plus two Create paths = 18 paths / 16 extant documents.
Preserve both S5B archive move sides in the eventual separately authorized PR. Local manifest equality
is verified; remote PR Files changed verification remains pending because no PR was created.
Both repos remain on main at entry HEADs: bot 85f303f6bd82bdc9a5cfc2d713da5480e1fa694a;
SQL 44afa315dd6cbfe9fec101f2a39a62e534f5b583. Local production/main is
c7e063f02ebe8287a584d0054ea14f91a0c0ecc6. Remotes/worktrees/status were checked without fetch.

### 3. New Files

Only docs/reference/kvk_source_migration/release_readiness_and_rollback.md and
 docs/reference/kvk_source_migration/release_evidence_log.md from the Create manifest.

### 4. Modified Files

Nine exact closeout/index paths gain current S6 status/navigation; S6 starter gains a dated notice;
this pack gains notice/delivery. All original document bytes remain retained. The three carried
archive documents remain byte-identical to S6 entry and both deleted archive sources stay absent.

### 5. SQL Changes

None. Authoritative routing/selection/publication/request/delivery/action shapes and both accepted
migration hashes were checked locally. SQL clean; no SQL connection, validator, migration or query.
Current live rows/jobs/schema, permissions, mappings and backup/restore evidence remain unverified.

### 6. Helpers Reused

No helper created/changed. Existing DAL lock_scope/locked_period/desired_config contracts inform
the non-executable activation transaction preview. No activation helper is asserted to exist.

### 7. Refactor Findings

No new in-scope runtime/refactor defect established. Legacy export/ProcConfig WS1 debt remains
separate; no opportunistic cleanup. Missing operational capabilities remain release gates.

### 8. Test Plan with Outcomes

Architecture passed (0 Python paths), deferred-items passed (16 Markdown documents), security-routing
passed (0 errors/warnings), exact 18-path selector passed, git diff --check passed. Links, fragments,
manifest and original-byte preservation passed; final counts follow below. Direct installed Markdown
hook checks passed except the deliberately retained pre-existing README trailing whitespace.
Pre-commit launcher/cache/stall limitations and the restored fixer change are recorded in the canonical
log; no full hook-suite pass claimed. Runtime pytest/imports/registration/SQL tests are skipped for
this documentation-only scope; no historical S5B result is relabelled as fresh evidence.

### 9. Security Review Decision and Evidence

Bot documentation-only skip: exact 18-path working-tree patch against
85f303f6bd82bdc9a5cfc2d713da5480e1fa694a, including all carried documentation. No executable/config/
permission/dependency/data-access/deployment/persistence change. Separate SQL no-change skip:
44afa315dd6cbfe9fec101f2a39a62e534f5b583 to itself, clean. No new scan. Later required reviews must
use Changes, exact separate repo targets, Deep off. Historical scan manifests/results stay retained.

### 10. Deployment Steps

None. Proposed SQL-first/flags-off/private-shadow/export/reconciliation/activation and rollback
steps are documented only. G4 must bind exact targets, versions, capabilities, audit/backup proof
and permitted operations. G5 stays operator-owned. No live action, Git publication or new task.

### 11. Deferred Optimisations

None new. OPS01/PERF01/CAP01 are mandatory open acceptance gates, not deferred debt. Documentation
is reviewable now; no activation, complete operational scenario pass or PR verification is claimed.

Final local check: all 174 local Markdown links and 13 fragments resolve; exact 18-path manifest,
14 original documents preserved, three unchanged archive documents, both absent move sources and
nine identical S6 status blocks verified. G4 operational scenarios and PR Files changed remain pending.

## 2026-09-12 authorized local rehearsal — partial evidence, gates OPEN

Chris Watts approved "local database on K98DEV server" and "approval to begin
rehearsal" after the retained G3 preparation checkpoint. This authorizes the local
synthetic work recorded here; it is not production activation or G5 acceptance.
No predecessor pack was executed. No real player import/export, Discord action,
bot-machine update/restart, Git publication, deployment or activation was performed.

### Exact execution and retained evidence

- Local server identity: `9SX2VF4\K98DEV`, SQL Server `16.0.1200.5`; shared-memory
  connection `lpc:localhost\K98DEV`, Windows authentication.
- New, previously absent database: `K98_S6_Disposable_20260912`, collation
  `Latin1_General_CI_AS`, compatibility 160. Retained predecessor databases were
  not modified. Installed accepted migrations `20260909_001_kvk_source_observation_facts.sql`
  (SHA-256 `4b19c8e54a7555e796c06124640efd27b6838c8360d352bd55265d04bdc1614c`)
  and `20260910_001_kvk_source_publication_state.sql`
  (`2985551c7cac6ba158a38c436389aa13b44fe36235ccf6768b684037cce77fbc`).
  Synthetic KVK_Windows fixture matches authoritative columns, primary key, default
  and checks; legacy secondary indexes were not installed. There are 26 KVK tables;
  setup reported zero disabled/untrusted constraints. This is not a full production schema.
- Bot main/origin-main `85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`;
  SQL main/origin-main `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
  Remotes retain the section-1 entry mapping; no fetch, pull or ref mutation.
- Temporary S6 harness uses existing synthetic helper functions and current DAL/services;
  it does not invoke predecessor test suites. Only owned hidden child processes exit.
  No production bot process is started or killed. All database connections assert the
  exact server and database. Evidence directory (outside Git):
  `C:/Users/cwatt/AppData/Local/Temp/k98-s6-rehearsal-x8tpc14d`.
- `setup.py` completed once. Initial sandbox Windows-authentication connection failed;
  the same target succeeded with approved elevated execution. No authentication or
  TLS-verification bypass was added to resolve that failure.
- `local_rehearsal.py` completed once, exit 0, from
  `2026-09-12T14:42:16.747885Z` to `2026-09-12T14:42:27.478053Z`.
  Exact outcomes, UTC timestamps, publication/period IDs and versions are retained in
  `local-results.json`; child process IDs and committed/checkpoint evidence are in
  `before_commit-exit.json`, `after_commit-exit.json`, `private_started-exit.json`
  and `publication_pending-exit.json`. Preserve this directory and database; no cleanup
  or blind replay is authorized. Entry documentation backups are in `entry.json`.

### Actual results and limits

| Check | Actual result | Limit / scenario allocation |
|---|---|---|
| Synthetic endpoints in seasons 139295168 and 65250356 | Both advanced live 11−10, live 12−10, final 13−10 | Partial T68–T70; two synthetic governors, not representative population |
| Duplicate observation 13 | Existing ScanID 13 returned; recovery allocated no publication | Semantic duplicate path checked; not a full ZIP/format variation matrix |
| Owned process exit before transaction commit | Fresh connection observed zero config requests and zero Windows rows; prior publication retained | Partial T46–T51; no SQL server restart |
| Owned process exit after commit/lost acknowledgement | One durable request and Windows row; fresh process recovered pending live 13−10, then corrected_final 14−10 after scan 14 arrived | EndScanID update itself supplied authority; no separate correction command; second recovery no-op |
| Exit after private_started checkpoint | Normal retry blocked; explicit local recovery changed owner and fence 1→2; two old synthetic slot IDs quarantined | S6-OPS01 partial only: no Google request was in flight |
| Exit after publication_pending checkpoint | Normal retry and private recovery both blocked | S6-OPS01 partial only: no grant or pointer mutation performed |
| Receipt boundary | Exactly 1024 UTF-16 units accepted; 1025 rejected | S6-CAP01 partial only: direct serializer contract, not actual multipart/provider exhaustion |
| Isolation | Routing enabled rows = 0; aggregate state remained not_received | No inferred aggregate report, daily SCANORDER operation or real data import |

### Workbook inventory and outstanding operator inputs

B0, F1S, F1M and F1E source workbooks are present in Downloads and their SHA-256
hashes match the accepted evidence. The A1 aggregate example is also present under
the private evidence directory and matches
`563e7a67948dbcde211764e30645a1188d06d7e39335e5793335a23f6ea9d2e3`.
Presence/hash verification did not import their contents or approve their endpoint
mapping. A1 remains a format/example artifact unless separately bound. No required
recorded source workbook is missing from this inventory; it does not establish a
future production input set. Private workbooks and credentials remain outside Git.

Read-only Google metadata checks found all five registered S4B workbooks accessible:
index `1xwF92PbxgXD0InA-ekuEPkN8MA5pgd1navpMyxEe6_Y`, quarantined slots
`1lD6o6uOKUg1e0H0cAz2guFOkFG0sXDntjt9wz_oDC3I` and
`1_Jb6hkBreXTR256MEYgFAraKDjytcQtCjEPe26qABFg`, retained recovery slots
`1bcqUkN3fySc34BsEDo_nflU3hfHJLqe5pBM6med9VS4` and
`1H9kXpIl0Vg5zv1CoLghp680j0Q90mD3fE_IpIIPG-7M`.
Existing service-account Editor access and owner's canShare were verified. Index
and recovery slots have link Viewer access; quarantined slots remain private.
These are retained evidence, not disposable S6 destinations; none was mutated.
No dedicated S6 workbook set was found in the metadata search. Approval to provision
a separate index/eight blank slots with exact rehearsal sharing, or operator-supplied
dedicated IDs, remains pending. A proposed eight-slot set is not yet a proven retention budget.

| Gate | Status after local rehearsal | Still required before acceptance |
|---|---|---|
| S6-OPS01 | OPEN; local process/SQL recovery evidence added | Dedicated Google targets and authorized sharing; measured interruption during private writes, Viewer grants and index pointer; actual external readback, fences/receipts, quarantine and reconciliation |
| S6-PERF01 | OPEN; no representative load measurement | Operator export cadence, maximum duration and other service-account consumers; agreed shared budget; actual representative multipart bytes/cells/API calls/readbacks/timing/429/503 outcomes |
| S6-CAP01 | OPEN; receipt boundary and existing ACL metadata checked | Dedicated owner/Editor/canShare/audience proof, measured active/staging/final/reference/quarantine retention, insufficient-slot and receipt-exhaustion behavior at actual provider scale |

G4 authorization remains bounded to approved rehearsal operations. G5 acceptance
and production activation remain operator-owned; none of these gates is accepted
by this local pass. Earlier unexecuted scenario rows retain their historical G3
meaning; only the partial evidence explicitly allocated above is new.

### Security, delivery and rollback disposition

Tracked changes remain the exact documentation carry-forward manifest, including
both archive rename sides. Temporary synthetic harnesses and results stay outside
Git; no production implementation, config, schema source or test file changed.
Bot security target remains the exact 18-path Markdown working-tree delta against
`85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`: documented inert-evidence skip.
SQL target remains separately `44afa315dd6cbfe9fec101f2a39a62e534f5b583` to itself,
empty delta: no-change skip. Runtime rehearsal evidence does not constitute a new
security scan. Any required later review must use Changes at exact separate repo
targets, Deep off. No standard/deep scan or automatic new task was launched.

No new deferred item was identified. Promotion verdict remains **Do not promote**:
provider evidence, acceptance, exact production operations and rollback authority
are unresolved. Retain local artifacts and disabled routing; do not delete/reuse
quarantined or retained workbooks. Canonical delivery remains sections 1–11 plus
this dated supplement. Eventual separately authorized PR and production promotion
must include the complete carry-forward manifest or prove individual paths merged.

### Local evidence SHA-256 manifest

| File | SHA-256 |
|---|---|
| `setup.py` | `56004b38572af3e4922ceecee5125f3bb133c3569a3b4da8581fb3c94a29644a` |
| `local_rehearsal.py` | `5982c3bd0c81b2e57edab75f003c12cee08c9b149f267cda9e5641a91d9c5acb` |
| `local-results.json` | `1be09acac6cdf679377a3994c7db4adb3e09a32bed5e601141022fdf355ba7ba` |
| `before_commit-exit.json` | `bbe1bf6084afcaa981b9d7cd458aaaeb84518a0a3da24589dfc7aef7a249978a` |
| `after_commit-exit.json` | `71d0faed122a7d540afe68c96cca510d2b57e3929ca46dc85333a5c1e5e9a783` |
| `private_started-exit.json` | `f1d94f5a4283832604d15d3e44e420aef2c836dca462751e3ad029afeb65fa3c` |
| `publication_pending-exit.json` | `a8faeaad3a71229522a17fd31db2962a386078cef6a26714800687d5e0beff66` |

### Rehearsal documentation validation

Fresh architecture validation passed (0 Python paths); deferred validation passed
(16 Markdown documents); security-routing validation passed (0 errors/warnings);
`git diff --check` passed. Exact-path test selection passed for all 18 manifest
paths; generic smoke-import/command-registration recommendations are skipped for
this documentation delta. No predecessor suite or full runtime suite was rerun.
The separately executed S6 synthetic process/SQL harness outcome is recorded above.

Manifest/preservation and link checks passed: exactly 18 Git paths, 16 extant
documents, all original rehearsal-entry bytes retained, three carried archived
documents unchanged, both archive source deletions preserved, 174 local links and
13 fragments resolved. Bot index remains empty; SQL repo remains clean; branches,
HEADs, origin/main refs and remotes remain at entry. Read-only local refs do not
prove remote freshness. Detailed validation and exact-path selection are retained
as `documentation-validation.json` and `selected-tests.txt` in the local evidence
directory. Earlier pre-commit orchestration limitations remain; no new blanket
pre-commit or security-scan pass is claimed. No private rows or credentials were
added to Git. Required eventual PR Files changed verification remains pending.

## 2026-09-12 S6 output provisioning and shared-consumer review

### Authority and operator performance expectations

Chris Watts approved S6 outputs and asked Codex to create them. The earlier question
specified a separate index/eight blank slots, the existing service-account Editor,
and Viewer sharing only for verified synthetic publication rehearsal. Creation and
Editor grants are now complete. No public Viewer grant, synthetic Google export or
pointer publication has yet been executed in S6. Retained S4B workbooks were untouched.

Operator expectation: **two or three exports per day; no fixed maximum duration**,
with runtime to be measured and made efficient where authorized. This removes the
unanswered cadence/duration question; do not invent a duration pass threshold.
Expected other service-account consumers are the all-KVK importer and scan-data
importer. The operator believed controls may prevent overlap and requested a check.
No account-wide quota isolation or runtime exclusivity is attested by that belief.
Performance acceptance should report actual elapsed time, size, calls, readbacks,
throttling and remaining headroom, then retain the operator's G5 decision.

### Created output manifest and verification

Nine unique native Google spreadsheets were imported from one verified blank local
XLSX into the new private My Drive `ChatGPT` folder
`1DMOF77hmxhY8PVS5R99E7kXFm3OKzU1k`. All title prefixes are
`K98 S6 rehearsal 2026-09-12`. The index and slots have distinct IDs from all retained
S4B/protected workbooks. No production config was changed to register these IDs.

| Role | Exact Google spreadsheet ID |
|---|---|
| index | `19jOzLAnEildMoxEQNqLsnkcB8tPo0w9Kym5_cbLof_g` |
| slot01 | `1oMIBoMqDp5od5hwEoAqlsvs8kK7svCsYcd0VEHb8Oxw` |
| slot02 | `1eWty-3Zr4RGfpA4eqpSTiVSNYZwrzUiXbG0kQ7yybMU` |
| slot03 | `1LeoZ5bySHbGTAyNUGNiKyUiG9zqn56eRvD-CTQvH7RI` |
| slot04 | `1i3o7DxQnsECQnFJ9bzI_mx6BBXb8-zvkVRU7pxQYWQ8` |
| slot05 | `1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg` |
| slot06 | `1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0` |
| slot07 | `1zMc_m7I70jr1s-GDBq035mGh0orXBAl3v2VJ-KZeY9k` |
| slot08 | `10GwOQWI5TgC2StB7axq3zZrMyjlQgj-PX_i6Ku3d2Lw` |

Connected-owner Drive metadata verified owner Chris Watts and exactly one additional
permission: the existing service-account Editor. There are no anyone/domain/group
permissions. Owner canShare is true for all nine. This is not yet evidence that the
runtime service-account credential can authenticate or that its canShare is true.
Native Sheets metadata verified one `Sheet1` per file, 1000 rows by 26 columns.
Bounded formula-mode readback of `Sheet1!A1:Z1000` returned no cells for every file.
They are intentionally blank operational slots, not finished reader-facing reports.
Native metadata retained hidden gridlines; no populated view exists for visual QA.
Default workbook timezone is America/Los_Angeles; no date values/formulas were
written. This timezone does not assign or alter UTC scan-start evidence; any later
timestamp handling must preserve the approved explicit UTC contract.

The local artifact builder exported and rendered the empty XLSX, then its process
returned exit 1 despite reporting completion. This is not recorded as a clean
builder process pass. Independent saved-XLSX inspection found only Sheet1 and no
populated cells; all nine native conversions and blank readbacks succeeded.

### Shared-consumer controls — static findings at exact accepted bot HEAD

| Code evidence | Finding and implication |
|---|---|
| `bot_helpers.py:280–339`; `services/fallback_upload_staging_service.py:79–101` | Monitored scan uploads share a process-local processing_lock across downstream processing. This protects that queue's participants. |
| `dl_bot.py:635–658` | All-KVK upload is a separate route before the fallback queue, returning without enqueueing there. |
| `upload_routes/kvk_all_route.py:535–548`; `kvk_all_importer.py:134–151` | All-KVK auto-export is scheduled as its own task and offloaded to a thread. The scan processing_lock is not acquired here. |
| `file_utils.py:1355–1400` | Thread offload runs the callable via asyncio.to_thread; its telemetry registry is not a global export queue. |
| `kvk/dal/new_source_delivery_dal.py:220–249` | S6 SQL session lock is keyed by destination kind/ID. It serializes participants for that destination, not all Google consumers. |
| `kvk/services/new_source_export_service.py:23–35,665–688` | S6 service-account pacing is 2.1 seconds between calls within a process. Other processes and legacy gsheet callers do not share that process memory. GET 429/503 retry behavior does not serialize mutations across consumers. |

Conclusion: **the current code does not establish a common lock/queue across all
three consumers**. Two or three exports/day does not preclude simultaneous bursts.
This is a concrete S6-PERF01 release gap, not a request to rewrite the importers or
run them concurrently. No live importer, bot-machine or credential consumer was
started to test contention. Runtime deployed versions/settings remain unverified.
Use separately verified scheduling/exclusivity or an explicitly approved shared
control change before claiming account-wide serialization; no implementation change
is included in this evidence-only delivery.

### Runtime preflight blocker and open acceptance gates

`sdk_preflight.py` ran once at `2026-09-12T14:59:38.149140Z` and failed before any
Google API call with FileNotFoundError. Read-only configuration resolution confirmed
the current GOOGLE_CREDENTIALS_FILE target is
`C:/discord_file_downloader/statsupdate-0d8b70356ef2.json`, which is absent; the default
credentials.json path is also absent. The existing trust bundle is present and TLS
verification remains enabled. No key was printed, created, copied or put in Git.
The operator was asked for the existing local key path or restoration at the configured
path; only a filesystem path/confirmation is needed, not key contents in chat.

Connected-owner Google Drive access was used for authorized provisioning and
readback; it must not substitute for the missing runtime service-account identity
in OPS01/PERF01/CAP01 measurements. No automatic retry of the failed preflight,
provider mutation or predecessor execution occurred. Preserve its failed result.

| Gate | Current status | Remaining exact evidence |
|---|---|---|
| S6-OPS01 | OPEN; local process evidence retained, dedicated outputs now bound | Restore local runtime credential; actual private-write/grant/pointer interruption and fresh-process external readback/reconciliation |
| S6-PERF01 | OPEN; 2–3/day, no hard duration cap recorded; shared-lock gap evidenced | Authenticated representative multipart measurement with actual calls/readbacks/bytes/timing/retries; shared-consumer budget or verified exclusivity; operator acceptance |
| S6-CAP01 | OPEN; nine private files provisioned; owner/Editor/blank readback passed | Runtime service-account canShare and synthetic Viewer publication proof; actual capacity/retention/insufficient-slot/receipt exhaustion; operator acceptance |

No G5 acceptance or production activation is granted. Database remains
`K98_S6_Disposable_20260912` with routing disabled from the retained local result;
this provisioning step did not write SQL. No pull/reset/merge/push/PR, production
SQL, real data import/export, Discord action, restart, deployment or activation.
All existing documentation, untracked archives and both rename sides remain in
the exact S6 carry-forward manifest. Canonical delivery is sections 1–11 plus the
dated supplements; previous pending-output/cadence statements are historical.

### Retained evidence manifest

Evidence directory remains `C:/Users/cwatt/AppData/Local/Temp/k98-s6-rehearsal-x8tpc14d`.

| File | SHA-256 |
|---|---|
| `s6-output-ids.json` | `b567d50aac28788ed83dcace812169edf77f4c2edcfbc0b6b8b330d61ac4dd5e` |
| `s6-output-metadata.json` | `dfac47c6338ddab0205972ad4f93c1441c5dec98a96955183529f8842e686a58` |
| `s6-output-blank-readback.json` | `6a3db33da630e95a6657500e3f2ddd13ad5fe1502344aaadbba51b2a3afc0054` |
| `sdk_preflight.py` | `1398e0d0f0c2981c8f05fb460819edbac40a5c4c9c9ced3450528c65234c3d8b` |
| `sdk-preflight-results.json` | `e95b26f5867247350f07ef6c2ff2afa25d70befc45033bdb99d1ca6b1a91b5e3` |

## 2026-09-12 authenticated S6 rehearsal and representative benchmark

### Authority, isolation and immutable revisions

The operator restored the configured local credential and explicitly approved
**5,806 synthetic players across ten periods**, confirming that the all-KVK and
scan-data importers would remain idle. This is operator-attested isolation during
this benchmark, not independent monitoring or a proven common concurrency lock.
Earlier approval covers the local K98DEV rehearsal and dedicated S6 outputs.
No real source-player workbook was imported or exported. Existing S4B files and
accepted predecessor evidence remain untouched; no predecessor was rerun.

Bot main/origin main remains `85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`,
with local production/main anchor `c7e063f02ebe8287a584d0054ea14f91a0c0ecc6`.
Bot origin is `https://github.com/cwatts6/K98-bot-mirror.git`; production is
`https://github.com/cwatts6/K98-bot.git`. SQL main/origin main remains
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`, origin
`https://github.com/cwatts6/K98-bot-SQL-Server.git`, with no SQL Git changes.
There are no runtime-source or tracked-test edits. Temporary rehearsal harnesses
and exact result artifacts are retained outside Git in the evidence directory below.

The only database written is retained disposable `K98_S6_Disposable_20260912`
on verified `9SX2VF4\K98DEV`, reached using `lpc:localhost\K98DEV` and Windows
authentication. Completed checks assert zero enabled SourceRouting rows. No
production SQL, bot-machine update, restart, real import/export, Discord operation,
deployment, activation, pull/reset/merge/push/PR or commit occurred.

The configured service-account key was restored locally and remains Git-ignored;
its contents are absent from Git and evidence. The restored runtime preflight
authenticated successfully and checked all nine original S6 files private/blank,
service-account Editor and canShare. The earlier missing-key failure remains
retained rather than rewritten. TLS verification used the existing trust bundle.

### Actual operations, recovery and limits of interruption evidence

The small operational scenarios deliberately use an **11,223-cell test ceiling**
to force two real Google files from 2,286 logical cells. This is a temporary harness
override; the accepted production 9,000,000-cell limit is unchanged. These scenarios
are operational proofs, not representative performance measurements.

* A child process exited after submitting a private data-write body, before reading
  its response. A fresh process observed the durable private_started claim and
  blocked blind retry. Explicit private recovery used fresh original slots 03–04,
  changed owner/fence 1→2, quarantined slots 01–02, fully verified and published.
  An independent audit found the quarantined grids/values unchanged. Confirmed
  repeat returned the same receipt with zero Google calls.
* Receipt-capacity exhaustion was rejected before SQL claim or provider calls using
  sixteen synthetic, unallocated 128-character IDs. No fake ID was accessed. Actual
  retained-slot exhaustion refused original slots 03–04 with setup_required after
  four GETs and no provider mutation. This proves fail-closed behavior, not an
  accepted long-term retention budget.
* The original pointer send-boundary interruption did **not** advance the index.
  Its planned confirmation assertion failed: fresh external readback correctly
  left the claim unresolved at publication_pending. Original slots 05–06 are
  verified public Viewer files, but the original index still references the prior
  confirmed generation in slots 03–04. Blind retry and private reclaim were blocked.
  This uncertainty is preserved; no forced pointer write or receipt repair occurred.
* A separate small scenario on the benchmark destination exits **after Google
  returns pointer success but before SQL confirmation**. Fresh-process reconciliation
  confirms the exact pointer/key/fence/directory evidence; a repeat makes zero
  Google calls. This proves loss of the application's acknowledgment, not an
  in-flight network cut that happened to succeed remotely.
* A separate Viewer-grant interruption submits the first grant, holds the response
  unread for one second, and exits. Fresh external ACL/pointer readback records the
  actual resulting permissions. Its publication_pending claim remains unresolved;
  blind retry and private reclaim remain blocked. No permission replay or repair
  is attempted. See the retained readback JSON for exact observed ACLs.

Intentional exit markers requested codes 88/89; the shell runner reported exit 1
for those interrupted processes. They are recorded as deliberate interruptions,
not clean process passes or observed runner exit codes 88/89. The original pointer
readback assertion failure is retained distinctly from the safe blocked outcome.

### Representative performance measured with normal settings

The accepted SQL publication path supplied 5,806 synthetic B0-eligible players and
ten fight-period publications, across two synthetic kingdoms/camps. All ten selected
publications contain 5,806 player results. This is a representative row/period load,
not the real B0 workbook's 36-kingdom distribution or a mixed aggregate-report case.
Independent aggregate/overall reports remain honestly not_received. No fight sum
was presented as an authoritative aggregate. Daily SCANORDER remains separate.

The run used the unchanged **9,000,000 cells per part**, **500 rows per data write**,
and **2.1-second service-account pacing**, followed by full provider value readback
before Viewer publication and index confirmation. There were 17,831,186 logical
data cells and 17,831,355 physical cells including repeated headers and directory,
split across two output files. These are measured/planned generation counts, not
an assertion that all cells contain nonempty values.

| Measurement | Actual result |
|---|---|
| Run UTC | `2026-09-12T15:27:06.420046+00:00` to `2026-09-12T16:07:01.192365+00:00` |
| Generation loading | 92.281 seconds |
| Export including full readback and publication | 2248.609 seconds (37.48 minutes) |
| Export API calls (excludes initial preflight) | 991 |
| Encoded request-body bytes | 219796508 |
| Decoded response JSON bytes | 202250907 |
| HTTP error status counts | `{}` |
| Durable outcome | confirmed, export_complete; repeat identical receipt with zero Google calls |

Response JSON bytes are decoded application measurements, not compressed wire
traffic. Elapsed time includes the actual default pacing and provider/network time.
The operator specified two or three exports daily with no fixed maximum duration;
no invented timing threshold or claim of optimal performance is applied.

| Actual export method | Calls |
|---|---|
| `drive.files.get` | 110 |
| `drive.files.update` | 5 |
| `drive.permissions.create` | 3 |
| `sheets.spreadsheets.batchUpdate` | 2 |
| `sheets.spreadsheets.get` | 16 |
| `sheets.spreadsheets.values.batchGet` | 368 |
| `sheets.spreadsheets.values.get` | 9 |
| `sheets.spreadsheets.values.update` | 478 |

### Dedicated benchmark output manifest and retained state

These additional seven synthetic files were created under the existing S6 output
and benchmark approvals. Initial runtime preflight verified private blank files,
Editor access and canShare. Full benchmark files 01–02 are retained unchanged by
the subsequent small operational checks. Slots 03–04 hold the independently
confirmed small acknowledgment-loss generation. Slots 05–06 hold the later
grant-interruption generation with unresolved publication. The benchmark index
therefore points to the confirmed small generation after those checks; use the
large generation's retained receipt directory URL to inspect the benchmark.

| Role | Exact Google spreadsheet ID |
|---|---|
| index | `1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY` |
| slot01 | `1_idQ1VTjlkY7AuTehXde783k7OZfwqm4GjvBOb9nkZU` |
| slot02 | `1CkgvVGNN-UUBfM0rCVxmHoDbWK_5nfDU7R63j2EYP6g` |
| slot03 | `1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU` |
| slot04 | `1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU` |
| slot05 | `1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ` |
| slot06 | `1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk` |

Large-generation receipt (exact): `{"delivery_state": "confirmed", "diagnostic": null, "export_complete": true, "receipt": "{\"export_key\":\"eca93ecc70fe04cb836a483fafb65fa17cd0a990730d4ca77e5d55667557b9ea\",\"publication_id\":\"390dd712-10c4-5cc3-befd-7dbb067e300c\",\"selection_version\":1,\"export_complete\":true,\"remote_id\":\"https://docs.google.com/spreadsheets/d/1_idQ1VTjlkY7AuTehXde783k7OZfwqm4GjvBOb9nkZU/edit#gid=2036238961\",\"phase\":\"published\",\"audience\":\"public_viewer\",\"attempt_slots\":[\"1_idQ1VTjlkY7AuTehXde783k7OZfwqm4GjvBOb9nkZU\",\"1CkgvVGNN-UUBfM0rCVxmHoDbWK_5nfDU7R63j2EYP6g\",\"1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU\",\"1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU\",\"1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ\",\"1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk\"]}", "setup_required": null, "sql_selected": true}`

### Acceptance gates and rollback boundary

| Gate | Status and evidence | Remaining operator-owned decision |
|---|---|---|
| S6-OPS01 | OPEN: real private-write interruption/recovery/quarantine, successful-pointer acknowledgment-loss reconciliation and grant uncertainty readback recorded | Accept precise measured evidence; decide exact handling of retained publication_pending claims. Do not blind-retry, reclaim or erase them. |
| S6-PERF01 | OPEN: approved 5,806 × ten-period normal-budget full-readback measurement completed under operator-attested importer idleness | Accept measured duration/cadence and representative-profile limits; establish verified scheduling/exclusivity or separately approved shared control. Static review found no common lock across all three consumers. |
| S6-CAP01 | OPEN: real multipart publication/ACL checks, retained-slot refusal and receipt-size fail-closed checks recorded | Accept retention horizon, correction/quarantine allowance and provisioned-slot budget; unresolved files remain occupied evidence, not reusable capacity. |

The original final/interim contracts remain: B0 eligibility, exact endpoint IDs,
UTC scan start, semantic re-export deduplication, interim 11−10 then 12−10, final
13−10 and authorized EndScanID 14 permitting replacement 14−10 without another
correction command. Accepted preceding slices and S5B-REC01 remain closed. No
G5 acceptance is inferred from rehearsal execution. Live G4 exact operations and
G5 acceptance remain operator-owned; production activation is not authorized.

Rollback readiness here means preserving disabled routing, original files and
receipts, all uncertain/quarantined outputs, and the isolated disposable database.
No destructive cleanup, live rollback or activation action was executed.

### Canonical validation, carry-forward and exact evidence manifest

This appendix supplements canonical delivery sections 1–11 and earlier dated
evidence; prior blockers and failures are historical records, not current claims.
The exact eighteen Git paths remain the required delivery manifest: sixteen
existing Markdown files plus both deleted rename sources, with an empty index.
All pre-existing closeout work and untracked archives must accompany the eventual
separately authorized S6 PR; no Files changed verification against a PR is possible
because no PR exists. The three carried archived delivery/starter documents remain
byte-for-byte unchanged. Final local path/link/hash verification is recorded in
documentation-validation.json after this update.

Tracked-source tests are not rerun for this Markdown-only update. Architecture,
deferred-item, security-routing, test-selection and whitespace checks are recorded
separately. Earlier pre-commit environment/cache limitations and historical README
trailing spaces remain qualified; no blanket pre-commit or gitleaks pass is claimed.
Security routing remains the documented documentation-only skip: exact Bot
working-tree eighteen-path delta against 85f303f6, separate SQL empty delta against
44afa315. No new Changes review is claimed for temporary harnesses. Any separately
required review must use Changes at separate exact repo targets, Deep off; no
standard/deep scan or automatic task was started.

Evidence directory: `C:/Users/cwatt/AppData/Local/Temp/k98-s6-rehearsal-x8tpc14d`.
Artifacts below are local evidence, not committed data. Retain them for operator
acceptance; temporary storage is not a durable external archive.

| Result artifact | Actual status | Wall seconds | API calls | SHA-256 |
|---|---|---|---|---|
| `sdk-preflight-results.json` | failed | None | 0 | `e95b26f5867247350f07ef6c2ff2afa25d70befc45033bdb99d1ca6b1a91b5e3` |
| `sdk-preflight-restored-results.json` | passed | 62.692 | 27 | `056f413efcf9779f6e7fb814b8d9a246ad6f59fce99a9baadd4166b3f2fc3cc7` |
| `provider-private_interrupt.json` | process_exit_after_request_body_sent | 67.452 | 33 | `d0f79b7bbe3507a919a4c6bf281fb5270f2e8d7d260e6e7cd322aa595581e0db` |
| `provider-private_readback.json` | passed | 40.762 | 20 | `87794272a267676f4d1e384cf05a36ddcb9870659c2a2416bf66d8cd1226a158` |
| `provider-private_recover.json` | passed | 181.493 | 87 | `2fbe2c65f0c547b9ba86db0d90dcd755a57badb8b2ba5bd9301027941fc182e3` |
| `provider-quarantine_audit.json` | passed | 36.483 | 18 | `2bb7c23be548ce38fea1277d8c45a4cf0518c9987c10a0f1b8bbe2afe0f46aa0` |
| `provider-confirmed_repeat.json` | passed | 0.202 | 0 | `414442b4f63d187d9bba88690dfce4a247bc0e5981f368a5b76db2e612680a30` |
| `provider-receipt_capacity.json` | passed | 0.173 | 0 | `7d57b9e391a4f742c26016c0186c067cee3709c2e7ee65069304063060a0ef3b` |
| `provider-insufficient_slots.json` | passed | 7.137 | 4 | `27a05211d2113d071246b48a1ba0bfa2814dbdd95b1a18c7bc36d8cd04bc2179` |
| `provider-pointer_interrupt.json` | process_exit_after_request_body_sent | 189.391 | 84 | `bd2b272bbcce4912786307d608479d1bb8030918e117fe94d959a046c3d41952` |
| `provider-pointer_readback.json` | failed | None | 26 | `be2df5ccfdc28ed4d0d1dbbc8c5dfef7e96041bebd98c55b3d3d03c8b3a69757` |
| `benchmark-plan.json` | prepared | 384.769 | 0 | `80f063bc02c9e81c1f94ada693144899df105458f28461ab8cf8e39127182c37` |
| `benchmark-results.json` | passed | 2394.772 | 1012 | `3587bbafc0bc145744c79ff03cb51e119915ad373ec3dd428385051880615e7b` |
| `benchmark-ops/provider-pointer_interrupt.json` | process_exit_after_google_success_before_sql_confirmation | 175.194 | 84 | `cd4564f160011a516b373048ad6d13ec2756ef1431e1a3ab15bac09367b79833` |
| `benchmark-ops/provider-pointer_readback.json` | passed | 72.031 | 35 | `4584425b6995f81788a2f2ca4947d3033f9683e1ffcd0f5c5b73e3f6a1de6752` |
| `benchmark-ops/provider-pointer_repeat.json` | passed | 0.118 | 0 | `c0519e4c8b4bde982a35e9dd34993a0d9d6919da38cfeeff6e7bee878499e393` |
| `benchmark-ops/provider-grant_interrupt.json` | process_exit_after_request_body_sent | 167.528 | 80 | `be447d3ce3eef8740c402957b948ebb72cced27b2a8d1dbbab863de6834bb82c` |
| `benchmark-ops/provider-grant_readback.json` | passed | 50.941 | 25 | `adabc4e3d5b404e5bc4ef755e66e2c783b581e301c680f75bd507763b4bfe553` |

### Exact interruption readback identities


`provider-pointer_readback.json`:

```json
{
  "index": "19jOzLAnEildMoxEQNqLsnkcB8tPo0w9Kym5_cbLof_g",
  "key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
  "slots": [
    "1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg",
    "1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0"
  ],
  "claim_before": {
    "state": "claimed",
    "fence": 4,
    "owner": "bca05d8c-2fa1-43b2-a036-9905e45150f0",
    "receipt": {
      "export_key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "publication_id": "e19c89ac-7977-5f28-ae4c-031807cd1728",
      "selection_version": 5,
      "quarantined_slots": [
        "1eWty-3Zr4RGfpA4eqpSTiVSNYZwrzUiXbG0kQ7yybMU",
        "1oMIBoMqDp5od5hwEoAqlsvs8kK7svCsYcd0VEHb8Oxw"
      ],
      "phase": "publication_pending",
      "export_complete": true,
      "attempt_slots": [
        "1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg",
        "1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0"
      ],
      "audience": "public_viewer"
    }
  },
  "reconcile": {
    "state": "claimed",
    "fence": 4,
    "owner": "bca05d8c-2fa1-43b2-a036-9905e45150f0",
    "receipt": {
      "export_key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "publication_id": "e19c89ac-7977-5f28-ae4c-031807cd1728",
      "selection_version": 5,
      "quarantined_slots": [
        "1eWty-3Zr4RGfpA4eqpSTiVSNYZwrzUiXbG0kQ7yybMU",
        "1oMIBoMqDp5od5hwEoAqlsvs8kK7svCsYcd0VEHb8Oxw"
      ],
      "phase": "publication_pending",
      "export_complete": true,
      "attempt_slots": [
        "1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg",
        "1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0"
      ],
      "audience": "public_viewer"
    }
  },
  "index_values": [
    [
      "78792a5a9782b69ca430cc3a5deeecf5a8e8ff7090dd547cbe533d229c589d56",
      "2",
      "https://docs.google.com/spreadsheets/d/1LeoZ5bySHbGTAyNUGNiKyUiG9zqn56eRvD-CTQvH7RI/edit#gid=1761925453"
    ]
  ],
  "blind_retry_blocked": true,
  "private_reclaim_blocked": true,
  "observed_permissions": [
    {
      "id": "19jOzLAnEildMoxEQNqLsnkcB8tPo0w9Kym5_cbLof_g",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    }
  ]
}
```

`benchmark-ops/provider-pointer_readback.json`:

```json
{
  "index": "1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY",
  "key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
  "slots": [
    "1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU",
    "1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU"
  ],
  "claim_before": {
    "state": "claimed",
    "fence": 2,
    "owner": "11e75cb1-3ec1-4371-bcab-73d5898ed90b",
    "receipt": {
      "export_key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "publication_id": "e19c89ac-7977-5f28-ae4c-031807cd1728",
      "selection_version": 5,
      "phase": "publication_pending",
      "export_complete": true,
      "attempt_slots": [
        "1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU",
        "1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU"
      ],
      "audience": "public_viewer"
    }
  },
  "reconcile": {
    "state": "confirmed",
    "fence": 2,
    "owner": "11e75cb1-3ec1-4371-bcab-73d5898ed90b",
    "receipt": {
      "export_key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "publication_id": "e19c89ac-7977-5f28-ae4c-031807cd1728",
      "selection_version": 5,
      "export_complete": true,
      "remote_id": "https://docs.google.com/spreadsheets/d/1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU/edit#gid=1773447482",
      "phase": "published",
      "attempt_slots": [
        "1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU",
        "1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU"
      ],
      "audience": "public_viewer"
    }
  },
  "index_values": [
    [
      "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "2",
      "https://docs.google.com/spreadsheets/d/1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU/edit#gid=1773447482"
    ]
  ],
  "blind_retry_blocked": true,
  "private_reclaim_blocked": true,
  "observed_permissions": [
    {
      "id": "1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    }
  ]
}
```

`benchmark-ops/provider-grant_readback.json`:

```json
{
  "index": "1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY",
  "key": "c19df611173a42517f45c61fdc76693d1f363187b1ea83bc3677de3966b7d85c",
  "slots": [
    "1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ",
    "1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk"
  ],
  "claim_before": {
    "state": "claimed",
    "fence": 3,
    "owner": "487a17d9-c64d-4116-9274-143ddffbabb1",
    "receipt": {
      "export_key": "c19df611173a42517f45c61fdc76693d1f363187b1ea83bc3677de3966b7d85c",
      "publication_id": "54a2480a-26fb-5bad-a3f5-9321525a731c",
      "selection_version": 1,
      "phase": "publication_pending",
      "export_complete": true,
      "attempt_slots": [
        "1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ",
        "1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk"
      ],
      "audience": "public_viewer"
    }
  },
  "reconcile": {
    "state": "claimed",
    "fence": 3,
    "owner": "487a17d9-c64d-4116-9274-143ddffbabb1",
    "receipt": {
      "export_key": "c19df611173a42517f45c61fdc76693d1f363187b1ea83bc3677de3966b7d85c",
      "publication_id": "54a2480a-26fb-5bad-a3f5-9321525a731c",
      "selection_version": 1,
      "phase": "publication_pending",
      "export_complete": true,
      "attempt_slots": [
        "1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ",
        "1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk"
      ],
      "audience": "public_viewer"
    }
  },
  "index_values": [
    [
      "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "2",
      "https://docs.google.com/spreadsheets/d/1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU/edit#gid=1773447482"
    ]
  ],
  "blind_retry_blocked": true,
  "private_reclaim_blocked": true,
  "observed_permissions": [
    {
      "id": "1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk",
      "permissions": [
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    }
  ]
}
```

| Additional exact artifact | SHA-256 |
|---|---|
| `local_rehearsal.py` | `5982c3bd0c81b2e57edab75f003c12cee08c9b149f267cda9e5641a91d9c5acb` |
| `local-results.json` | `1be09acac6cdf679377a3994c7db4adb3e09a32bed5e601141022fdf355ba7ba` |
| `provider_ops.py` | `024042a7326dd52a20e029300cdcd67da2e5d3b8e038a1c940c1f02742f78fb4` |
| `provider_followups.py` | `3e0ebe1ff201ee86e0a500d503261cff60c857395d2d30e15336b744d75e65eb` |
| `provider-plan.json` | `0d9beb3c2d8468493aaa440f5dfdbd6602462557f32185e50c61bf011df0e05d` |
| `benchmark_setup.py` | `7e3c752531519e1c00bd753694f029bb2497d71fad29296e0e3397071b50f161` |
| `benchmark_run.py` | `ebe84bad8a1dd3cdf35ad4b1ece6dde27af2b549d151324d8204d286fc1d7502` |
| `benchmark_operational_followups.py` | `2c1c4af4334699b99603a33368556f21a2643f1ef7c0de6b529a6bfd99d8f885` |
| `benchmark-output-ids.json` | `b7d62f7be4937a7478ba0ce57e0e6ec0e5bb09f55d8b3fc7df91732e5aa80483` |
| `benchmark-output-metadata.json` | `f2f49b7b1c90a7eb56487ba88ee071a2796c7f6afbdccf43253c12bdd080efbe` |
| `benchmark-request-estimate.json` | `bee223dd1ca04c7f9d5c90a57d6db5eed07fbe2e7e727348f327bf800ae24c9d` |
| `runtime-summary.json` | `ca3866531e21cf29ee47d377b8fea667cc2657b635c30fcc26205846da161222` |

### Final authenticated-rehearsal documentation validation

After recording the actual runtime outcomes, architecture validation passed
(0 changed Python files), deferred-item validation passed (16 Markdown files),
security-routing validation passed (0 errors/warnings), and git diff --check passed.
Exact-path test selection passed; its generic smoke-import and command-registration
recommendations are skipped because runtime source/registration are unchanged and
no PR is being handed off. No predecessor tests or production smoke were rerun.
The complete 18-path manifest, empty Git index, all original evidence-entry bytes,
three unchanged carried archive documents and both rename deletions were verified.
All 174 local links and 13 fragments resolved. Bot/SQL main and origin/main remain
at the entry anchors; remotes were rechecked, SQL status is clean, and bot changes
are exactly the preserved documentation manifest. Local production/main is still
c7e063f02ebe8287a584d0054ea14f91a0c0ecc6. No remote fetch was performed.

All required source workbooks are present according to the retained read-only
inventory; the restored credential now authenticates. No additional workbook or
credential creation is required for this completed rehearsal. S6-OPS01, S6-PERF01
and S6-CAP01 remain OPEN with the precise acceptance gaps above. No production G4
action, G5 acceptance, PR or activation is claimed.

## 2026-09-12 operator approval of completed rehearsal evidence

Chris Watts approved proceeding after the completed rehearsal report. Record this
as acceptance of the measured synthetic results, including the 37m 29s full export
and verification, successful private recovery and pointer acknowledgment-loss
reconciliation, and safe blocking of the two uncertain publications. Earlier
statements awaiting acceptance of those measured results are historical.

This approval supplies no new scheduling window, shared-consumer control, retention
horizon, correction/quarantine allowance or exact recovery operation for uncertain
publications. Those facts must not be invented or marked implemented. S6-OPS01,
S6-PERF01 and S6-CAP01 therefore retain their open operational components, with
the measured rehearsal evidence now operator accepted. Full release G5 acceptance
and production G4 execution are not inferred.

The concrete next proposed action is a documentation-only mirror branch
`codex/kvk-source-migration-s6-release-evidence`, exact eighteen-path commit and
push to `origin` (`cwatts6/K98-bot-mirror`), and a draft PR into `main` titled
"Document KVK S6 rehearsal evidence and release gates". Include all pending
closeout documentation, both S5B rename sides and untracked archive files. After
creation, verify the PR Files changed against the complete manifest; do not merge
or promote. This is a prepared proposal, not a claim that a branch/commit/PR exists.
The earlier explicit no-push/no-PR restriction makes clarification of this exact
external step necessary; rehearsal acceptance alone does not identify it.

Validation at approval entry reconfirmed both repository HEADs/remotes/status,
all eighteen Git paths, empty index, clean SQL tree, preserved original document
bytes, 174 local links and 13 fragments. This update changes documentation only;
the existing runtime-test and separate-repository security skip decisions remain
applicable. No SQL, Google, Discord, Git publication or production action is part
of this approval record. Preserve all disposable databases and retained outputs.

## PR 272 review correction — missing public routing consumer

Review comment 3996906362 is valid. At reviewed bot commit
`758d6be163026f0299c05c3ad0bf2c4517c55932`, routing-row access in
`kvk/dal/new_source_config_dal.py:13–28` and
`kvk/dal/new_source_admin_dal.py:494–498` provides locking/onboarding, not public
read dispatch. `stats_alerts/embeds/kvk.py:154–185` selects V2 only with explicit
diagnostic source_selection; ordinary requests retain the legacy path.

A successful SourceRouting.Enabled update alone cannot activate public V2 readers.
The readiness sequence and transaction preconditions now explicitly stop until a
separately approved, reviewed, deployed and accepted routing consumer covers all
intended public readers. Require ordinary-request enable/disable behavior, pinned
routing/selection versions, unavailable/stale/capability handling, cache/restart
behavior and rollback tests bound to the deployed consumer revision. This is an
implementation gap, not merely missing deployment evidence or an activation helper.
No runtime implementation is included or authorized by this documentation correction.
S6-OPS01/PERF01/CAP01 and all retained uncertainty remain as previously recorded;
this additional prerequisite cannot be discharged by their synthetic measurements.

Copilot reviewed 16/16 files and generated no inline comments, but requested final
human review of the large evidence record. That requirement remains: operator
rehearsal acceptance is recorded, while independent remote reviewers cannot verify
local disposable databases, runtime JSON artifacts or every historical claim from
the PR alone. Hashes identify retained artifacts; they do not substitute for access
and inspection. No independent review or full release acceptance is invented.

Validation for this correction: Markdown-only; no runtime tests or predecessor
rehearsals rerun. Recheck local links, the complete 18-path PR manifest, staged
whitespace, architecture/deferred/security-routing and staged secrets. Security
routing remains documentation-only skip for the exact Bot review-fix diff; SQL
remains unchanged at 44afa315dd6cbfe9fec101f2a39a62e534f5b583. No activation,
merge, production promotion, SQL execution or Google operation is performed.
