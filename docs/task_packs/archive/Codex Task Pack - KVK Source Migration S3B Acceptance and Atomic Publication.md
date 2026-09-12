# Codex Task Pack — KVK Source Migration S3B Acceptance and Atomic Publication

> Archived 2026-09-10: S3B complete, operator smoke accepted and merged (#267/#574).
> Historical instructions below are not a new execution authorization. S4A is the next
> separately gated slice; see the current S4A pack/starter in the parent folder.

## Current entry handoff — 2026-09-10

Start S3B in a new chat with its matching starter only when granting S3B G3. S1/S2A/S2B/S3A
are accepted and merged; S3A mirror #266 and private bot #573 merge evidence and operator smoke
are in the [archived S3A pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S3A%20Player%20Window%20Calculations.md).
Verified local mirror main `9d08b3bf9e7cac6c95db1c4a120c8bf0aad7475f`; SQL main
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Both local pulls are complete; the bot machine
has not been updated or restarted. Recheck actual branches/HEADs/remotes/status and preserve
all pending documentation, including untracked Markdown. Historical planning anchors below
are not reset targets. S3B can be developed locally without deploying S3A to the bot machine.

S3B G3 and its disposable integration target remain unapproved by this preparation. The reusable
instance is `9SX2VF4\K98DEV` (alias `localhost\K98DEV`), but the operator must explicitly name
and authorize the S3B database and prerequisite installation/test operations before connection.
See [local SQL development](../../reference/local_sql_development.md). Preserve retained S2A/S2B
state. No default production connection, silent evidence-database reuse or automatic service start.
Actual two-connection transaction/concurrency evidence is required for acceptance; mocks alone
cannot close it. If target authorization is missing, keep integration pending and request it.

### Required carried-forward documentation in the later S3B PR

The operator explicitly requires this S3A closeout and archive work to accompany the S3B PR
when PR creation is separately authorized. This is approved carried-forward work, not unrelated
dirt to discard. At entry inventory tracked edits/deletions and untracked Markdown. Preserve
all thirteen documentation entries below (fifteen paths counting both sides of the two renames).
Include the complete manifest, both source deletions and archive destinations, repaired links,
and S3B implementation evidence in that PR. Do not omit untracked archive files or blanket-stage
unrelated work. Reconcile the final staged manifest, link checks and preservation evidence.
This documentation allowance supplements section 11; it changes no S3B runtime/SQL boundary
and does not authorize a push/PR, deployment, activation or successor pack by itself.

- Update: `README-DEV.md`.
- Update: `docs/reference/README.md`.
- Update: `docs/reference/local_sql_development.md`.
- Update: `docs/reference/kvk_source_migration/decision_and_evidence_register.md`.
- Update: `docs/reference/kvk_source_migration/phase_2_implementation_plan.md`.
- Update: `docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md`.
- Update: `docs/task_packs/KVK Source Migration - Programme Pack.md`.
- Update: `docs/task_packs/README.md`.
- Update: `docs/task_packs/archive/README.md`.
- Update: `docs/task_packs/Codex Task Pack - KVK Source Migration S3B Acceptance and Atomic Publication.md`.
- Update: `docs/task_packs/Codex Chat Starter - KVK Source Migration S3B Acceptance and Atomic Publication.md`.
- Archive move: `docs/task_packs/Codex Task Pack - KVK Source Migration S3A Player Window Calculations.md` → `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S3A Player Window Calculations.md`.
- Archive move: `docs/task_packs/Codex Chat Starter - KVK Source Migration S3A Player Window Calculations.md` → `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S3A Player Window Calculations.md`.

## 1. Task Header

- Prepared 2026-09-09; owner Chris Watts; Phase 2B specification.
- G2 architecture approved, including authorized EndScanID corrections. **S3B G3 pending.**
- One-pass implementation approved: **No**. Execute only after explicit approval of this slice.
- Proposed isolated branch `codex/kvk-source-s3b`; not created during planning.
- Type: bot implementation.

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

Accept immutable inputs idempotently and select coherent publications with durable config requests and CAS fencing; no runtime route or live import.

## 4. Background

Planning anchors: bot main `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; SQL main
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`. Recheck branches/HEADs/remotes/status at execution,
preserve existing work and record actual start/end hashes. Local definitions are not deployed proof.
No pull/reset/checkout to make a working copy match historical evidence. Use an authorized isolated
branch/worktree where needed. Phase-1 C01-C65 anchor dependencies; G2 fixes source semantics.

## 5. Scope

Predecessors: S1/S2A/S2B/S3A accepted; S3B G3; disposable SQL integration target.

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

1. Confirm explicit S3B approval and predecessor evidence; otherwise scope/review and stop.
2. Capture worktrees and exact manifest; recheck drift and source/SQL contracts before edits.
3. Implement only the approved boundary with assigned tests; preserve unrelated work.
4. Run checks, review exact diff/security target and report actual outcomes/limitations.
5. Stop at delivery; no automatic next task, G4 action or self-approval.

## 9. Focused Audit Requirements

Inspect section 11 read paths for helper semantics, layering, period/identity/availability and
regression contracts. Static source continuity does not prove current live rows/jobs or external
readers. Operator-attested SQL/config parity remains separately labelled. No credential discovery
or RDP required for this planning/implementation boundary. Evidence condition: Disposable SQL required for transaction/concurrency acceptance; unavailable integration remains pending, never production substitute.

## 10. Architecture Targets

kvk/models and kvk/schemas own pure types; kvk/services business rules; kvk/dal parameterized SQL,
transactions and mapping; commands/routes/views thin adapters. New SQL only in the SQL repository.
Follow the implementation-plan interfaces/lock order and approved source/field dictionary.
No second domain implementation in DL_bot.py or gsheet_module.py; no duplicated SQL calculation.

## 11. Exact File Manifest

All paths below are relative to **C:/discord_file_downloader**.
New files are proposed, not present yet; predecessor-created modifications require accepted delivery.
No wildcard authorizes extra files. Append implementation evidence to this pack after execution;
preserve/include the explicitly authorized carried-forward documentation manifest above; do not rewrite unrelated indexes. Migration date/sequence is the sole controlled allocation exception
in implementation-plan section 4; final name must be recorded before authoring and never renamed after merge.

### Read only

- `file_utils.py`
- `kvk/dal/kvk_all_import_dal.py`
- `kvk/target_cache_repository.py`
- `services/kvk_all_import_audit_service.py`

### Create

- `kvk/dal/new_source_import_dal.py`
- `kvk/dal/new_source_publication_dal.py`
- `kvk/dal/new_source_config_dal.py`
- `kvk/dal/new_source_reporting_dal.py`
- `kvk/services/new_source_artifact_store.py`
- `kvk/services/new_source_publication_service.py`
- `kvk/services/new_source_config_service.py`
- `tests/test_kvk_source_import_dal.py`
- `tests/test_kvk_source_publication.py`
- `tests/test_kvk_source_config_service.py`
- `tests/test_kvk_source_artifact_store.py`
- `tests/test_kvk_source_sql_integration.py`

### Modify

- No existing runtime files. Include the exact carried-forward documentation manifest above and append S3B delivery evidence to this pack.

## 12. Implementation Requirements

Implement plan section 5 operations and lock order. DAL owns parameterized SQL/transactions; services own revision/roster policy and pure S3A calculations. get_conn_with_retries is connection acquisition only, never uncertain-write replay. Inject connection/artifact roots; no default live integration connection.
Write bounded content-addressed originals before SQL reference with generated contained path, flush/hash/atomic replacement. Retain safe orphan evidence. SQL uniqueness/locks govern replay; ImportAudit best-effort context cannot determine admission. Same semantic re-export returns prior accepted identity, no scan or delivery intent allocation.
Aggregate acceptance commits both tabs. Live-as-of/final correction rules apply; candidate building is invisible until complete. CAS pointer transaction validates exact config/inputs/counts/hash, swaps selection and appends action/outbox. Read desired config/routing/pointer once then immutable facts; no false current final when desired end is pending.
Expose snapshot_endpoint_request on caller cursor with no commit/rollback; base-version idempotency/provenance persists. End-only changes keep approved weights/map/roster. Source-content and aggregate-final corrections require separate expected-version actions.
Opt-in disposable SQL tests use two actual connections for concurrent allocation/replay/CAS, before-commit rollback, after-facts/before-publication crash and uncertain commit readback. Never simulate these solely with mocks or run against default production DB. No route/startup worker, real export, Discord or activation in this slice.

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

Scenario ownership: T01/T04/T07/T41-T54/T65/T68-T70. Separately run tests/test_kvk_source_sql_integration.py only with explicit disposable target; mock suite is not integration proof.

- `python -m pytest -q tests/test_kvk_source_import_dal.py tests/test_kvk_source_publication.py tests/test_kvk_source_config_service.py tests/test_kvk_source_artifact_store.py tests/test_kvk_all_import_dal.py`

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

Rollback: Retain accepted facts/candidates, routing disabled. Read durable outcome before any retry; do not delete originals/history on uncertain commit.

## 17. Proposed PR Summary

Describe concrete behavior, exact manifest, actual tests/security target, dependencies and rollback
limits. Keep private player rows/credentials/findings out of Git. No PR creation authorized by
preparation. Include the full carried-forward documentation manifest, both sides of archive renames and repaired links. End with slice status and next required gate.

**Prepared only. S3B G3 pending; no implementation executed.**


## Documentation handoff validation — 2026-09-10

Documentation preparation only; S3B G3 and its explicitly named disposable SQL target remain
pending. Current merge/local/no-bot-update evidence is in the entry handoff and archived S3A pack.
Exact closeout: thirteen Markdown entries, fifteen paths including both sides of two archive moves.
Architecture validator passed (zero Python changed), deferred validator passed (thirteen Markdown),
security-routing validator passed (zero errors/warnings), and exact test selection completed.
All 120 relative links in changed documents resolved; archived security scan identities retained.
Runtime pytest, broad smoke imports and command-registration reruns are skipped for these solely
Markdown changes; operator S3A smoke and previous runtime results are retained as dated evidence.
Security: precise documentation-only skip for the exact manifest above; SQL remains unchanged.
No runtime/config/SQL/helper/refactor/deferred change, new implementation branch, commit/push/PR,
SQL connection, service start, bot-machine update, restart or activation. Preserve the pending
tracked edits, old-path deletions and untracked archive Markdown for the separately authorized PR.

Exact thirteen-file documentation pre-commit hooks passed; applicable checks required no rewrites.

## S3B G3 prerequisite verification — 2026-09-10

### 1. Summary

The operator approved S3B G3 in this task and subsequently authorized creation of an S3B
database on `9SX2VF4\K98DEV`. Earlier G3-pending wording is historical. Implementation
is **blocked at the SQL contract check**, not delivered or accepted: the accepted S3A
event-time endpoint behavior conflicts with two accepted S2B CHECK constraints. No runtime
file has been authored and no successor or predecessor implementation pack was executed.

Fresh connected GitHub readback confirms mirror #266 merged at 11:28:48 UTC as
`3154997fa2dfc124da75ee35dca79463c3196a43`; private bot #573 merged at 11:29:18 UTC as
`140fc89765b1d6ec8418ac6f6d039e575419c29e`. Archived final evidence was inspected,
including final separate Changes reviews and the operator's historical 77-test smoke.

### 2. File Manifest

Bot remains on `main`, HEAD `9d08b3bf9e7cac6c95db1c4a120c8bf0aad7475f`, with
`origin` = `https://github.com/cwatts6/K98-bot-mirror.git` and `production` =
`https://github.com/cwatts6/K98-bot.git`. SQL remains clean on `main`, HEAD
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`, origin
`https://github.com/cwatts6/K98-bot-SQL-Server.git`. Both worktree inventories were read.
No branch, staging, commit, pull, reset, merge, push or PR operation occurred.

All thirteen carried-forward documentation entries (fifteen paths) listed at this pack's
entry remain required. Both old-path deletions and both untracked archive destinations
are preserved. This execution changes only this pack by appending evidence; its earlier
contents and all other pending documents remain preserved. The thirteen-entry manifest
must still accompany any separately authorized S3B PR.

### 3. New Files

None. All twelve proposed runtime/test files in section 11 remain uncreated.

### 4. Modified Files

Only this task pack receives the present evidence appendix. Other dirty files are the
operator-authorized carried-forward work and have not been rewritten by this execution.

### 5. SQL Changes

SQL repository changes: none. The authorized fresh database is
`K98_S3B_Disposable_20260910` on verified `9SX2VF4\K98DEV`, engine `16.0.1200.5`,
compatibility 160 and collation `Latin1_General_CI_AS`. Created the prerequisite KVK
schema and installed the unchanged accepted migrations
`20260909_001_kvk_source_observation_facts.sql` and
`20260910_001_kvk_source_publication_state.sql` in that database only. Readback:
25 source tables, zero disabled/untrusted CHECKs and zero source rows. Retain this database.
Retained S2A/S2B databases were listed for target verification; neither was written or rebuilt.

The service was already running with startup type Automatic; this differs from the dated
Manual reference. No service configuration, start or restart was performed. Initial sandbox
authentication failed; elevated Windows authentication succeeded. SQLCMD rejected a forward-
slash input path before execution; the Windows-path retry installed S2A successfully.

**Blocking contract:** `KVK.SourceWindowConfig.CK_SourceWindowConfig_Bounds` requires
`EndScanID >= StartScanID`. `KVK.SourceConfigRequest.CK_SourceConfigRequest_Endpoints`
requires the same numeric order for both old and new endpoints. The merged migration contains
these checks at lines 168 and 248, and both reference snapshots agree. The approved architecture
and accepted S3A instead use event UTC, explicitly supporting a lower-ID end with later UTC.
S3B cannot persist those supported configurations/requests under the installed constraints.

Proposed bounded amendment, **not authorized or authored**: a new forward migration removing
only numeric endpoint ordering from these two source CHECKs, retaining positive/null ID rules;
update the two matching snapshots and add regression coverage to the SQL publication validator
and synthetic constraint fixture. Keep UTC ordering enforced and tested in S3A/S3B. Do not
alter legacy Windows, renumber scans, disable trusted constraints or rewrite merged migrations.
Candidate new migration name is `20260910_002_kvk_source_endpoint_identity_bounds.sql`;
recheck allocation before authoring. Proposed SQL manifest:

- Create `migrations/20260910_002_kvk_source_endpoint_identity_bounds.sql`.
- Modify `sql_schema/KVK.SourceWindowConfig.Table.sql`.
- Modify `sql_schema/KVK.SourceConfigRequest.Table.sql`.
- Modify `deploy/Test-KvkSourcePublicationContracts.ps1`.
- Modify `validation/kvk_source/publication_constraints.sql`.

This requires an explicit amendment to S3B's current bot-only boundary and a separate SQL
Changes review, Deep off. Existing S3B G3 and disposable-target authorization remain valid.

### 6. Helpers Reused

Existing S3A resolver tests were executed unchanged. No runtime helper added or modified.

### 7. Refactor Findings

The prerequisite endpoint constraint mismatch above blocks compatibility; it is not an
optional refactor or an accepted limitation. No generic WS1, exporter or daily namespace work.

### 8. Test Plan with Outcomes

Fresh command: `.venv/Scripts/python.exe -m pytest -q
tests/test_kvk_source_window_resolver.py -k lower` — **4 passed, 21 deselected**.
This verifies existing final/replacement lower-ID support and equal/earlier UTC rejection.
On the authorized S3B database, read the exact two installed CHECK definitions from
`sys.check_constraints` and evaluated them against synthetic VALUES: start/end 10/9 and
old 10/13 to new 10/9 were both **rejected**. This was evaluation of installed predicates,
not a full DAL insert/concurrency test; no source rows were inserted.

S3B unit tests, actual two-connection concurrency/CAS/uncertain-commit tests, full pytest,
runtime smoke and registration remain unexecuted. No S3B runtime exists; predecessor tests
and SQL predicate checks cannot establish S3B acceptance. Documentation validation results
are recorded below after execution.

### 9. Security Review Decision and Evidence

Current execution: precise bot Markdown-only skip for this evidence appendix and preserved
thirteen-entry carried-forward manifest; no runtime/configuration/permission/data-access
code changed. SQL repository: separate no-change skip at the HEAD above. No scan launched.
The planned S3B Changes review against its exact authored bot patch, Deep off, remains
required after implementation. Any approved SQL amendment needs its own immutable target
and separate Changes review. No standard/deep scan, new task, private data or credentials.

### 10. Deployment Steps

None. Only the authorized disposable database prerequisites were installed. No production
SQL, bot-machine update, real imports/exports, Discord action, restart, deployment or activation.
Stop for the bounded SQL contract amendment decision before implementing incompatible DAL.

### 11. Deferred Optimisations

No new unrelated deferred optimisation. The blocking prerequisite is retained above as a
required compatibility decision, not deferred technical debt or self-approved scope expansion.

#### Final prerequisite-pass checks

Architecture validator passed (zero Python changed); deferred validator passed (thirteen
Markdown documents); security-routing validator passed (zero errors/warnings); exact task-pack
test selection and `git diff --check` passed. All 120 relative links across the carried-forward
documents resolve. Applicable task-pack pre-commit hooks passed, including secret detection;
the first sandbox attempt could not write its cache, and the elevated retry passed.
The selector's broad smoke/registration recommendations are skipped for this documentation-only
execution with no runtime changes. This is not S3B implementation acceptance.

SHA-256 preservation check: the fourteen other paths are unchanged from entry, including both
absent old paths and both untracked archive files. The original S3B pack prefix remains byte-for-
byte intact. Both repository HEADs/branches and the SQL clean status remain unchanged.
No files were staged. Await an explicit SQL scope amendment; do not silently waive the accepted
S3A endpoint cases or alter the SQL schema under the current bot-only manifest.

## Operator correction and resumed S3B implementation — 2026-09-10

The operator clarified: **EndScanID must be greater than StartScanID; new player scans are
imported in calendar order, oldest first, with IDs allocated 1, 2, 3, ... and strictly
increasing scan-start UTC.** This supersedes lower-ID/later-UTC acceptance for the S3B write
boundary. The earlier prerequisite blocker and proposed five-file SQL amendment above are
withdrawn. Do not create that migration or relax S2B constraints. Existing baseline/no-fight
equal-endpoint semantics remain separate. Replays and accepted content corrections retain
their scan ID; aggregate reports never allocate player or daily scan IDs.

Source verification: `KVK.sp_KVK_AllPlayers_Ingest` allocates `MAX(ScanID)+1` under its
transaction/range locks; `dbo.IMPORT_STAGING_PROC_CORE` takes the maximum across kingdom
scan/receipt registries and allocates the next SCANORDER. Those statements establish
sequential allocation, not by themselves enforcement of chronological UTC admission. S3B
adds explicit increasing-UTC admission. Neither legacy importer nor SQL source was changed.

Resumed on local branch `codex/kvk-source-s3b` from the recorded bot HEAD, retaining all
pending work. The exact twelve new Python files in section 11 are now authored and under
validation; the historical prerequisite-pass statement that none existed no longer describes
the current working tree. Existing S3A runtime/tests remain unchanged; S3B validates its
stricter admission/config/selection boundary. No deployment or activation is involved.

Intermediate validation: 15 exact focused tests passed; 6 explicit S3B disposable SQL tests
passed, including two real concurrent connections for admission and CAS, caller transaction
rollback, uncertain commit readback, candidate invisibility, aggregate final/late-live behavior,
and actual 11-10, 12-10, 13-10, 14-10 progression. Broader S1/S3A/S3B regression/log hygiene:
255 passed with production operational logs unchanged. Architecture/deferred/security-routing
validators and exact-path test selection passed. All twelve-file hooks passed, including
Pyright and secret detection; registration remains 36/100 without drift. These are intermediate
results; final review, complete scenario coverage accounting and security results remain pending.

Synthetic SQL rows are isolated by generated test seasons in the authorized S3B database and
retained there. Later test runs use separately retained private temporary artifact roots rather
than pytest's rotating temporary directories. Initial fixture runs used pytest temporary roots;
those earlier rows are test evidence only and must not be mistaken for durable production
artifact-retention validation. Both retained S2A/S2B databases remain untouched.

Security started for the immutable twelve-file task-only working patch at
`C:/discord_file_downloader/.codex_scan_stage/s3b`, base
`9d08b3bf9e7cac6c95db1c4a120c8bf0aad7475f`: scan
`55a9e4fc-2f9c-4940-8053-479ea19bb5f3`, Changes, Deep off; snapshot
`codex-security-snapshot/v1:sha256:29e8c1ffd3a5b04a6b1429ca21b7252d0e2116881fbb9f30aaa3770df80863e5`.
Only that new review directory was appended to local `.git/info/exclude`. No staging, commit,
push or PR occurred. SQL still has a separate no-change skip; security is not yet complete.

## Operator scenarios and endpoint amendment review — 2026-09-10

The latest operator requirement supersedes the preceding strict-combat-ID wording: both
configured endpoints may change; a supplied EndScanID must be **greater than or equal to**
StartScanID. A blank/future end permits the latest accepted interim scan. Equal endpoints
represent a fight that never happened, with zero fight scores for every eligible B0 member.
Distinct scans still require increasing UTC; identical endpoints necessarily share their UTC.

1. **Summary:** Scenarios 1–3 now have explicit disposable SQL tests and pass. Scenario 4
   and authorized start-endpoint changes need the bounded predecessor-file amendment below;
   they are not implemented or accepted. Do not waive these requirements.
2. **File manifest:** Existing twelve S3B files and thirteen carried-forward documentation
   entries remain preserved. Bot branch `codex/kvk-source-s3b`, HEAD
   `9d08b3bf9e7cac6c95db1c4a120c8bf0aad7475f`; SQL clean main at
   `44afa315dd6cbfe9fec101f2a39a62e534f5b583`. No staging/commit/push/PR.
3. **New files:** No additional files this scenario-review pass.
4. **Modified files:** Added three cases within `tests/test_kvk_source_sql_integration.py`;
   appended this evidence. The proposed extra runtime modifications, not yet made, are
   `kvk/models/new_source_reporting.py`, `kvk/services/new_source_window_resolver.py`, and
   `kvk/services/new_source_calculation.py`. The first needs start-change provenance and
   equal-endpoint invariants; the second needs authorized start/end transitions and equal
   fight endpoints; the third needs explicit no-fight zero scores for the frozen eligible
   cohort, including members absent from the identical scan. Preserve ordinary missing-data
   semantics, B0 attribution, aggregate authority and daily namespaces.
5. **SQL changes:** None. Existing SourceWindowConfig/SourceConfigRequest checks already
   permit equality and store both old/new starts. Tests use only the previously authorized
   `K98_S3B_Disposable_20260910` on `9SX2VF4\K98DEV`; retained S2A/S2B remain untouched.
6. **Helpers reused:** S3A resolver/calculator, S3B injected transaction/config/publication
   operations and existing synthetic workbook fixtures. No legacy importer edits.
7. **Refactor findings:** This is a contract amendment, not unrelated cleanup. Section 11
   currently forbids editing existing runtime files; the three-file extension is pending
   operator review. No duplicate workaround implementation was introduced.
8. **Test plan/outcomes:** Fresh full opt-in S3B integration run: **17 passed**. Scenario 1
   selects 11−10 with desired end 15 absent; scenario 2 selects 11−10 with blank end;
   scenario 3 retains 14−10 on scan-15 arrival alone, then selects 15−10 after the authorized
   endpoint request, with synthetic DKP changing 400 to 500. Read-only synthetic probes show
   both S3B and S3A reject equal endpoints in a fight. Existing separate no-fight calculation
   gives zero for present eligible members but `missing_start` for an absent B0 member.
   These probes expose gaps; they are not scenario-4 acceptance. Add start-change, equality,
   below-start rejection and complete eligible-cohort zero-score tests with the amendment.
9. **Security review:** Still incomplete. Frozen scan
   `55a9e4fc-2f9c-4940-8053-479ea19bb5f3` failed canonical completion with
   “The latest saved scan draft is incomplete; continue the scan before completing it.”
   Its earlier snapshot does not cover subsequent hardening or these tests. Retain the same
   scan and evidence; do not report completion/no findings. Final exact Changes coverage,
   Deep off, remains required after the endpoint amendment. SQL separate no-change skip.
10. **Deployment steps:** None. No production connection, import/export, Discord action,
    restart, deployment or activation. Stop for bounded manifest review.
11. **Deferred optimisations:** None newly identified. Endpoint behavior gaps are required
    acceptance work, not deferred debt or implicit acceptance exceptions.

## S3B implementation delivery — final endpoint amendment, 2026-09-10

### 1. Summary

The operator explicitly approved adding the three S3A runtime files identified above.
This is the current S3B boundary; the historical pending/strict-greater/blocked entries above
remain as dated evidence, not current instructions. Both starts and ends can change through
an authorized, versioned endpoint request. A configured end must be at least the start;
blank/future ends use an explicit interim. Equal endpoints mark no-fight player scoring:
all frozen B0-eligible members receive zero supported fight-score deltas, even if absent from
the identical scan. Absolute power/profile availability and unsupported metrics are not
fabricated, and raw coverage counts remain truthful. Distinct scans retain increasing UTC.

Admission, immutable facts, candidate completion, publication CAS, action/outbox insertion,
caller-owned endpoint requests and coherent private reads are implemented without runtime
activation. End/start updates preserve roster, map, weights and unaffected source revisions;
the request itself authorizes the replacement. Source-content corrections remain separate.

### 2. File Manifest

Bot branch `codex/kvk-source-s3b`, unchanged base/HEAD
`9d08b3bf9e7cac6c95db1c4a120c8bf0aad7475f`. Remotes remain mirror `origin`
(`cwatts6/K98-bot-mirror`) and private `production` (`cwatts6/K98-bot`). SQL remains clean
`main`, HEAD `44afa315dd6cbfe9fec101f2a39a62e534f5b583`, origin
`cwatts6/K98-bot-SQL-Server`. Nothing is staged or committed; no network Git mutation or PR.
The exact runtime/test patch is twelve created files plus three explicitly authorized edits.

All thirteen carried-forward documentation entries in the entry manifest remain required
for the later separately authorized PR, including both deleted old paths, both untracked
archive destinations, repaired links and this delivery. SHA-256 verification preserved all
fourteen other paths and the original byte prefix of this pack. No blanket staging or discard.

### 3. New Files

- `kvk/dal/new_source_import_dal.py`: transactional observation/aggregate admission and replay.
- `kvk/dal/new_source_publication_dal.py`: completed candidates, input guards, CAS/action/outbox.
- `kvk/dal/new_source_config_dal.py`: caller-owned durable start/end requests.
- `kvk/dal/new_source_reporting_dal.py`: single-generation private read envelope.
- `kvk/services/new_source_artifact_store.py`: bounded private content-addressed originals.
- `kvk/services/new_source_publication_service.py`: S3A calculation and publication orchestration.
- `kvk/services/new_source_config_service.py`: authorized request boundary and endpoint order.
- `tests/test_kvk_source_import_dal.py`.
- `tests/test_kvk_source_publication.py`.
- `tests/test_kvk_source_config_service.py`.
- `tests/test_kvk_source_artifact_store.py`.
- `tests/test_kvk_source_sql_integration.py`.

### 4. Modified Files

- `kvk/models/new_source_reporting.py`: endpoint-pair provenance and equal-endpoint invariants.
- `kvk/services/new_source_window_resolver.py`: authorized start/end changes and no-fight slots.
- `kvk/services/new_source_calculation.py`: explicit zero fight scores across the eligible B0 cohort.
- This pack: appended evidence. All other carried-forward documentation remains unchanged.

### 5. SQL Changes

No SQL source/migration changes. Existing accepted S2A/S2B objects already support the
endpoint pair and equality. Only the previously authorized
`K98_S3B_Disposable_20260910` on `9SX2VF4\K98DEV` was used for setup and synthetic tests.
The initial prerequisite schema installation is recorded above. Later test seasons and
private temporary artifact roots are retained; S2A/S2B retained databases were not rebuilt
or written. No production data or connection fallback.

### 6. Helpers Reused and Legacy Importer Comparison

Reused S1 parser/metadata/digest types, S3A exact resolver/calculator/DTOs, fixed decimal
validation and the compatible healed-times-20 helper. DAL owns SQL; connections and private
artifact roots are injected. No automatic uncertain-write retry or ImportAudit admission gate.

Read-only source comparison found:

- `KVK.sp_KVK_Recompute_Windows` lines 103–119 substitutes maximum ScanID for a blank or
  future end; an existing configured end remains exact. Starts absent or above the maximum
  are skipped. Its later endpoint joins recalculate using both currently configured bounds.
- `KVK.sp_KVK_Get_Exports` lines 38–43 exposes the same effective-end cap.
- `KVK.sp_KVK_AllPlayers_Ingest` lines 69–85 checks season/timestamp/file-hash duplicates
  and allocates `MAX(ScanID)+1`. It does not itself enforce calendar-order admission or
  semantic ZIP re-export deduplication; S3B explicitly enforces both.
- `kvk/dal/kvk_all_import_dal.py` lines 485–491 commits facts before a separately committed
  recompute. S3B tests therefore cover accepted facts surviving failed candidate builds,
  and uncertain pointer commits with durable action/outbox readback.
- The transactional `proc_config_import.py` window write at lines 878–890 commits at 927;
  no direct window-recompute call was found in that module. Changing configuration without
  another player upload is therefore a distinct recovery/trigger case, not something to
  assume the legacy upload callback covers. The S3B scenario-3 test processes its durable
  endpoint request against already accepted scans without a second upload. Wiring the
  configuration-import hook/worker remains the separately authorized later slice.
- Legacy recompute full-outer-joins endpoint members, uses missing-value fallbacks and
  current weights. These behaviors are not copied into S3B: B0 eligibility/attribution,
  frozen weights, missing-data states, Decimal precision and supplied aggregate authority
  remain the approved contracts. Only explicit equal-endpoint no-fight scores become zero.
- With only the start imported, legacy capping can temporarily calculate start-minus-start.
  S3B retains `missing_end` while a blank/future configured end awaits a distinct scan;
  it does not declare a cancelled fight unless the configured endpoints are explicitly equal.

These are source-code observations, not claims about deployed SQL or live data. Legacy
importer, recompute, exports, daily SCANORDER and bot-machine behavior remain untouched.

### 7. Refactor Findings

The three-file amendment resolves the accepted model's end-only/equal-fight restrictions
without duplicating the calculator. No generic exporter, WS1 or ProcConfig refactor. Existing
historical lower-ID pure S3A tests remain compatibility tests; the S3B write boundary rejects
an end below start and admits new scans chronologically. They do not override current policy.

### 8. Test Plan with Actual Outcomes and Limits

- **22 real disposable SQL tests passed**, plus **3 publication unit tests** in the same
  focused run (25 total). Includes all four operator scenarios; start earlier/later, end
  shorter/blank/equal, future start, 11−10/12−10/13−10/14−10, exact 14−10→15−10, durable
  pending requests and rollback/replay, two-connection allocation/CAS/config races, coherent
  reads, aggregate both-tab rollback/finality/correction, stale mixed-stream rejection,
  candidate crash recovery and before/after commit acknowledgement failures.
- Broader source/legacy regression through `scripts/analyse_pytest_log_noise.py`:
  **256 passed**, production operational logs unchanged. An initial command used incorrect
  schema-test filenames and collected no tests; corrected explicit paths produced this pass.
- Architecture: 15 Python files passed. Deferred/security-routing validators passed with
  zero routing errors/warnings. Exact-path selector completed. Fifteen-file hooks passed,
  including Ruff, Black and Pyright after formatting/unused-import fixes.
- Import-only smoke passed with its built-in no-login/no-startup/no-file-logging guards.
  Registration: 36 primary commands, 100 grouped subcommands, no drift.
- Staged-only secret hook was supplemented by a separate redacted filesystem scan of the
  exact fifteen files (including untracked files): **no leaks found**.
- Initial full-suite sandbox run: **3,762 passed, 24 skipped, 2 failed**. The failures were
  `test_prekvk_dispatch_diagnostics.py::test_real_send_edit_readonly_status_and_restart`
  and `test_stats_alerts_guard.py::test_migration_and_distinct_claims_do_not_lose_rows`;
  Windows temporary-file replacement failed outside the changed S3B paths. Both passed
  in an isolated elevated rerun, with operational logs unchanged and no unrelated fixes.
  The wrapper exits before its log comparison on a failing suite, so the failed run is not
  itself a log-hygiene pass. The elevated full rerun completed: **3,764 passed, 24 skipped**
  in 166.45 seconds, with production operational logs unchanged. The 22 opt-in SQL cases
  are skipped without target environment variables in this full run and passed separately
  against the expressly authorized target; no default SQL connection was used.

Scenario accounting: T01/T04/T07/T41–T44/T46–T53/T65/T68–T70 have applicable admission,
config, publication or SQL evidence above. T45 roster-impact UI/onboarding and T54 interaction
refresh/actor rechecking remain later consumer/interaction integration work; S3B checks the
frozen roster and expected selection and exposes no interaction surface. Delivery workers,
external sends/cache invalidation, real workbooks, production throughput and bot-machine
restart/deployment are not exercised or authorized. This is local implementation evidence,
not live acceptance or authorization for later packs.

### 9. Security Review Decision and Evidence

SQL: separate no-change skip at its recorded clean HEAD. Bot: required **Changes**, **Deep
off**, final exact fifteen-file immutable working patch at
`C:/discord_file_downloader/.codex_scan_stage/s3b-final`, base
`9d08b3bf9e7cac6c95db1c4a120c8bf0aad7475f`, scan
`8e276080-b141-4469-b0b3-320f38355fc0`, snapshot SHA-256
`163c101a17baa9da88dd972d1fb5bae1b4b72e134d1ec3b5b774738cbb014c49`.
Completed at `2026-09-10T12:52:39Z`; canonical readback confirms **complete coverage,
15/15 reviewed surfaces, zero findings, zero deferred items and zero open questions**.
SHA-256 comparison verified every final working file still matches this frozen target.
Scan usage measurement was unavailable (`scan_thread_unavailable`). Private report directory:
`C:/Users/cwatt/AppData/Local/Temp/codex-security-scans-D9VbP8/s3b-final/9d08b3bf9e7cac6c95db1c4a120c8bf0aad7475f_20260910T124632Z_tr1xswzx`.
Retained canonical `report.md`, `coverage.json`, `findings.json`, `scan-manifest.json` and
`exports/results.sarif`; do not commit private scan artifacts.

The earlier twelve-file scan was recovered in a subsequent continuation and sealed, but its
canonical coverage remained partial because it retained an obsolete pending checkpoint.
It cannot establish the final gate; it and its private artifacts remain preserved. No standard
or deep scan, public finding details, credentials or private player fixtures entered Git.
Local detached review worktrees and exact local excludes are review artifacts, not PRs.

### 10. Deployment Steps

None. Routing remains unwired. No pull/reset/merge/push/PR, bot-machine update, production SQL,
real import/export, Discord action, restart, deployment or activation. Retain originals,
accepted facts and candidates. Read durable actions after uncertain commits; rollback uses
an increasing selection version and retained immutable facts. Stop for operator review.

### 11. Deferred Optimisations

No new unrelated deferred item. Known legacy recompute/fallback behavior is comparison
evidence, not scope to repair here. Later consumer/delivery/roster integration boundaries
remain owned by their separate packs, which were not executed.

### Final review checkpoint

The final fifteen-file Changes review and runtime checks above are complete. No blocking
finding was identified within the implemented local S3B boundary. Operator acceptance is
not self-granted: T45/T54 interaction/onboarding aspects and later consumer/delivery/live
validation remain explicitly unclosed as described above. Review this delivery before
authorizing any next gate; no successor pack was started.

Final preservation: all fifteen carried-forward paths (thirteen entries) retain their entry
state, except this pack's appended evidence; its original byte prefix remains preserved.
Both archive source deletions and untracked destinations remain present. All **120 relative
links resolve**. Final Markdown hooks, architecture/deferred/security-routing checks and
`git diff --check` passed. Final bot/SQL HEADs and remotes are the recorded values, SQL is
clean, and staging remains empty. Only the authorized twelve new files, three amended S3A
files and the carried-forward documentation appear in the working-tree handoff.

## PR review response — mirror #267 / private #574, 2026-09-10

The operator authorized assessment, fixes, replies and appropriate thread resolution on both
PRs. Five inline comments identify four distinct issues (action replay appears in both repos).
All four were accepted after inspecting the changed code and authoritative SQL definitions.

- **Rollback delivery reconciliation:** existing non-pending destination rows become
  `uncertain`, retaining receipts, owners/claim history and attempt counts while incrementing
  their fence and clearing confirmation. This queues reconciliation without discarding an
  ambiguous external outcome or resetting a fence to zero. The accepted CHECK permits only
  fence-zero initial `pending` rows, so a blind pending reset was deliberately avoided.
  Exact action replay returns before this transition and cannot repeatedly increment fences.
- **Equal-endpoint aggregate rejection:** the service and report model both use
  `is_no_fight` to reject aggregate objects. A cancelled fight may publish no aggregate
  while earlier accepted aggregate history remains immutable and retained.
- **Complete action replay identity:** the action compares request ID, reason, routing
  version and a canonical destination set, in addition to its prior identity fields. The
  destination scope is persisted in immutable action provenance; reordering/duplicates are
  equivalent, changed delivery intent is a conflict rather than apparent success.
- **Accepted observation period scope:** endpoint associations must be included in the
  accepted revision's persisted `MetadataJson.scope.period_keys`; a caller-supplied
  `ObservationInput.period_keys` cannot broaden it. The B0 roster input is independent,
  but B0 used as an actual start endpoint is checked like every other endpoint.

Exact follow-up manifest: `kvk/dal/new_source_publication_dal.py`,
`kvk/models/new_source_reporting.py`, `kvk/services/new_source_publication_service.py`,
`tests/test_kvk_source_publication.py`, `tests/test_kvk_source_sql_integration.py`, plus
this evidence appendix. No SQL schema/migration or unrelated file changes. Mirror fix base
`1364fa161cccec7295f78ec2f783b5f84ae7b1a1`; private fix base
`ea8ccdde752080e2d260b14cf364be0b04fcd07c`. Apply the identical file delta on each history.

Fresh focused validation: **32 disposable SQL tests plus 4 publication unit tests passed**.
Regressions cover all three destination kinds and four existing delivery states, stale worker
fences, once-only rollback replay, changed action inputs, both start/end scope forgery,
model/service aggregate rejection and retained aggregate history after cancellation. Five-file
hooks (including Ruff/Black/Pyright), architecture, deferred and routing validators passed.
Affected source/legacy regression and log-hygiene suite: **257 passed**, operational logs
unchanged. Smoke imports and registration (36/100, no drift) passed. The fresh elevated full
suite stopped producing progress around 19% and was interrupted after several minutes;
it is **not a new full-suite pass**, and the wrapper did not complete its log comparison.
The earlier 3,764-test full pass remains dated pre-fix evidence. No unrelated code was changed
to address the stalled run. The final narrow Changes review is appended after completion;
the prior security result is not claimed to cover this new patch. No external deliveries
were executed.

The general reviewer concern about missing SQL context is addressed by local verification
against clean SQL HEAD `44afa315dd6cbfe9fec101f2a39a62e534f5b583` and the expressly
authorized disposable database tests. This evidence does not replace human code review or
authorize production SQL, merges, deployment, activation or subsequent packs.

Mirror follow-up security: Changes, Deep off, scan
`308e7130-8e09-45fc-9765-c4c9673fc21f`, base/head
`1364fa161cccec7295f78ec2f783b5f84ae7b1a1`, frozen five-file patch digest
`f87292989c3a05addbd5f1d010d5c36dcfb822333ceff5c6c44f1019bc33b18c`.
Canonical completion/readback: **5/5 files, zero findings, deferred items or open questions**.
Root source bytes match the frozen reviewed target. Canonical report, coverage, findings,
manifest and SARIF remain in the private temporary security artifact directory, outside Git.

Separate private-history follow-up security: Changes, Deep off, scan
`97196427-2c4a-40e5-acbd-3f3c3f71c6e9`, base/head
`ea8ccdde752080e2d260b14cf364be0b04fcd07c`, at isolated target
`.codex_scan_stage/s3b-review-fixes-private`. The same five-file content digest above was
independently reviewed against this private history. Canonical completion/readback at
13:44:21 UTC: **5/5 files, zero findings, deferred items or open questions**. Private artifacts
remain outside Git. These narrow scans cover the review-fix delta; the initial full S3B
mirror review and its original private patch-equivalence evidence remain historical records.
All thirteen carried-forward entries (fifteen physical paths), including both archive renames
and the original S3B byte prefix, were reverified as preserved before publishing these fixes.


## S3B merged closeout and S4A handoff — 2026-09-10

**S3B is complete, operator smoke accepted and merged.** Mirror
[PR #267](https://github.com/cwatts6/K98-bot-mirror/pull/267) merged at 13:59:47 UTC as
`e915f9727f9492fe4ecc02b5c0d9f3c6e443be13`; private bot
[PR #574](https://github.com/cwatts6/k98-bot/pull/574) merged at 14:01:14 UTC as
`a8ad9f1d81cfb7884a9cdcc0b067c4346a204488` on 2026-09-10.
Operator post-merge smoke on mirror main `e915f972`: import smoke passed, registration
36/100 without drift or duplicates, **36 tests passed in 9.11s** (4 publication + 32 SQL).
Current synchronized local mirror main is `02385a0edc0ec83f77241e02648eabb3b7640ea6`;
local production/main is `a8ad9f1d81cfb7884a9cdcc0b067c4346a204488`; SQL main remains
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Both repos were clean at closeout entry.
S3B pack/starter are archived. **Next: S4A Shared Reports and Cards in a new chat, with
separate S4A G3 approval.** Preserve pending S3B closeout docs and both archive moves
for the eventual separately authorized S4A PR; its pack contains the complete manifest.
S3B's latest full-suite rerun stalled around 19% and remains incomplete; the accepted smoke
does not replace it. The earlier 3,764-pass full result is pre-review-fix evidence.

The operator confirms local pulls completed and no changes were pulled to the bot machine.
No bot-machine restart, production SQL deployment or source activation is evidenced or performed.
S4A local development does not require a bot-machine deployment. New routing remains disabled.

The accepted S3B boundary includes immutable acceptance, atomic publication and four review fixes:
rollback delivery reconciliation with increasing fences; aggregate rejection for equal-endpoint
no-fight windows; complete immutable action replay scope; accepted revision period-scope checks.
All five inline threads were replied to and resolved before merge. The two separate final
five-file Changes reviews, Deep off, completed with zero findings/deferred/open questions:
mirror `308e7130-8e09-45fc-9765-c4c9673fc21f`, private
`97196427-2c4a-40e5-acbd-3f3c3f71c6e9`. Earlier implementation/security evidence is retained.

Preserve the operator-approved endpoint amendment: either StartScanID or EndScanID may change;
a supplied end must be >= start. Distinct imported scans advance both ScanID and UTC scan start,
oldest first; semantic re-exports allocate no new scan. Blank/future end uses the latest eligible
interim; an available end pins the final, and an authorized endpoint update permits replacement
without a separate correction command. Equal endpoints produce zero supported fight scores for
every frozen B0-eligible member, including absent scan members, with aggregates not applicable.
Ordinary missing-data states remain explicit. Aggregate reports and daily SCANORDER stay separate.

The authorized S3B test target was `9SX2VF4\K98DEV` /
`K98_S3B_Disposable_20260910`, including prerequisite schema and synthetic two-connection tests.
Retain this database and the separate S2A/S2B evidence databases; no reuse/rebuild for S4A is
implicitly authorized. S4A uses mocks by default; any SQL integration must first have an explicitly
authorized disposable target and operations. No connection or setup was performed in this closeout.

The supplied transcript shows 36 passed in 9.11s on merged mirror main `e915f972`, import smoke
success and registration 36/100 without drift/duplicates. Its raw attachment stays outside Git.
The current synchronized main contains identical KVK source and these test files to private merge
`a8ad9f1d`. Historical 257 affected regressions passed with logs unchanged. The operator smoke
did not run the log-noise wrapper, so it is not new log-hygiene or full-suite evidence.
The interrupted post-review full suite remains an explicit S4A validation follow-up; investigate
its cause and run the required full suite/log-noise gate without silently expanding runtime scope.

S3B pack and historical starter are archived, with links repaired and delivery history retained.
The S4A pack/starter require all pending closeout documentation, including untracked archive
destinations and both source deletions, in the eventual separately authorized S4A PR.
These edits stay uncommitted for that handoff. No new chat or S4A implementation is started here.
Documentation-only security skip: exact closeout/status/links/archive manifest, no runtime,
configuration, permission, data-access or deployment effect. SQL repository: separate no-change skip.
Runtime pytest/smoke/registration reruns are skipped for this Markdown-only closeout.
