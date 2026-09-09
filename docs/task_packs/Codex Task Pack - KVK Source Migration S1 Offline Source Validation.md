# Codex Task Pack — KVK Source Migration S1 Offline Source Validation

## 1. Task Header

- Prepared 2026-09-09; owner Chris Watts; Phase 2B specification.
- G2 architecture approved, including authorized EndScanID corrections. **S1 G3 pending.**
- One-pass implementation approved: **No**. Execute only after explicit approval of this slice.
- Proposed isolated branch `codex/kvk-source-s1`; not created during planning.
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

Create pure typed player/aggregate workbook validation, explicit UTC metadata and semantic re-export comparison. No SQL, runtime route or publication.

## 4. Background

Planning anchors: bot main `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; SQL main
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`. Recheck branches/HEADs/remotes/status at execution,
preserve existing work and record actual start/end hashes. Local definitions are not deployed proof.
No pull/reset/checkout to make a working copy match historical evidence. Use an authorized isolated
branch/worktree where needed. Phase-1 C01-C65 anchor dependencies; G2 fixes source semantics.

## 5. Scope

Predecessors: G2 approved; no live environment or predecessor implementation required.

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

1. Confirm explicit S1 approval and predecessor evidence; otherwise scope/review and stop.
2. Capture worktrees and exact manifest; recheck drift and source/SQL contracts before edits.
3. Implement only the approved boundary with assigned tests; preserve unrelated work.
4. Run checks, review exact diff/security target and report actual outcomes/limitations.
5. Stop at delivery; no automatic next task, G4 action or self-approval.

## 9. Focused Audit Requirements

Inspect section 11 read paths for helper semantics, layering, period/identity/availability and
regression contracts. Static source continuity does not prove current live rows/jobs or external
readers. Operator-attested SQL/config parity remains separately labelled. No credential discovery
or RDP required for this planning/implementation boundary. Evidence condition: None for offline implementation after S1 G3. Actual workbook reinspection optional and read-only; synthetic fixtures suffice.

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

- `kvk/schemas/kvk_all_schema.py`
- `kvk/services/kvk_all_import_service.py`
- `kvk/__init__.py`
- `kvk/models/__init__.py`
- `tests/test_kvk_all_import_service.py`
- `requirements.txt`

### Create

- `kvk/schemas/new_source_schema.py`
- `kvk/models/new_source_observation.py`
- `kvk/services/new_source_metadata.py`
- `kvk/services/new_source_parser.py`
- `kvk/services/new_source_digest.py`
- `tests/test_kvk_new_source_schema.py`
- `tests/test_kvk_new_source_metadata.py`
- `tests/test_kvk_new_source_parser.py`
- `tests/test_kvk_new_source_digest.py`
- `tests/kvk_source_fixtures.py`

### Modify

- None.

## 12. Implementation Requirements

Implement the five interfaces and exact ParseLimits in plan section 3. Schema/models own headers, enums, limits and immutable typed results; metadata module owns time/identity confirmation; parser owns bounded XLSX reads; digest owns canonical typed-value comparison.
Use pinned openpyxl and stdlib only. No dependency changes, eager package exports, application constants/Discord/SQL imports. Accept bounded bytes, never user paths. Formula/external links never execute. Do not reuse legacy _as_int because malformed/fractional input cannot silently become valid zero or identity.
Retain artifact hash, typed cells, schema, digest and field states. Both aggregate tabs validate as one result; raw token/precision survive. Duplicate identities/unknown schema reject; optional invalid player metrics become unavailable. Changed bytes with equal recognized typed cells are re-exports; changed cell type/value/precision is not equivalent.
Synthetic fixture helper creates in-memory XLSX only. Golden digest vector, reordered rows/sheets, ZIP metadata changes, formula cells, high IDs, Decimal limits and bounded ZIP negatives required. Never copy B0/P1/P2/A1/player CSVs into fixtures. S1 emits validated metadata only; DB scan allocation and calculation belong to later slices.

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

Scenario ownership: T01-T20; parsing boundaries of T63. T68 allocation is not implemented here.

- `python -m pytest -q tests/test_kvk_new_source_schema.py tests/test_kvk_new_source_metadata.py tests/test_kvk_new_source_parser.py tests/test_kvk_new_source_digest.py tests/test_kvk_all_schema.py tests/test_kvk_all_import_service.py`

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

Rollback: Revert isolated modules/tests before wiring; no data, database or external effect to undo.

## 17. Proposed PR Summary

Describe concrete behavior, exact manifest, actual tests/security target, dependencies and rollback
limits. Keep private player rows/credentials/findings out of Git. No PR creation authorized by
preparation. End with slice status and next required gate.

**Prepared only. S1 G3 pending; no implementation executed.**


## S1 G3 implementation delivery — 2026-09-09

The operator explicitly approved G3 for **S1 only** in the current task. This supersedes the
historical pending wording above. G2 approval, including EndScanID, was verified in the current
architecture/Phase 2B plan/register. No predecessor implementation or live environment was required.
Implementation is delivered for review. The final security artifact has a coverage-status gap;
this is not a clean merge-readiness or activation approval. No next slice starts automatically.

### 1. Summary

Implemented offline typed player/aggregate XLSX validation, explicit UTC metadata confirmation,
versioned semantic comparison and synthetic tests. No runtime caller, SQL, scan allocation,
roster mutation, publication, command, configuration or dependency change.

Source facts preserve observed identities/kingdoms and unavailable fields. Later services must
apply frozen B0 eligibility/attribution and exact endpoints: interim 11−10 then 12−10; final
13−10; authorized EndScanID=14 itself permits replacement 14−10 without another correction command.
These downstream calculations are not implemented or claimed tested by S1. Aggregate authority,
separate final overall and daily SCANORDER remain separate. Aggregate reports allocate no scan.

### 2. File Manifest

Exactly the ten new Python paths in section 11 plus this pack's append-only evidence block.
No runtime files outside that manifest changed. Required read paths remain byte-identical.

Bot start: main, HEAD `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`.
Bot end: `codex/kvk-source-s1`, same HEAD; source/tests remain untracked and unstaged for review.
Origin remains `https://github.com/cwatts6/K98-bot-mirror.git`; production remains
`https://github.com/cwatts6/K98-bot.git`. No commit, pull, reset, merge, push or PR.

SQL start/end: main, HEAD `fc0e94ebd2e0a98286069c8a8b71365dd5178657`, clean;
origin `https://github.com/cwatts6/K98-bot-SQL-Server.git`. Remotes were inspected, not contacted.
Existing bot documentation changes and untracked planning work were preserved. A pre-edit hash
inventory captured 1,522 existing Git-visible files; all were byte-identical before this append.
The pack's original byte prefix is separately retained by length/hash for final preservation check.
Ignored private source files were not opened or used as fixtures.

Two detached, ignored review worktrees retain the first and corrected task-only patches under
`.codex_scan_stage/kvk-source-s1-review` and `.codex_scan_stage/s1-final`. Both use the verified
bot HEAD. An initial long-path checkout failed and cleaned itself up; retry with command-local
`core.longpaths=true` succeeded. No persistent Git setting changed.

### 3. New Files

- `kvk/schemas/new_source_schema.py`: exact headers, enums, limits and typed rejection.
- `kvk/models/new_source_observation.py`: immutable metadata, cells, metrics, rows and results.
- `kvk/services/new_source_metadata.py`: strict basename UTC grammar, explicit overrides/scope,
  confirmation provenance and prior-evidence identity conflict checks.
- `kvk/services/new_source_parser.py`: bounded bytes/ZIP/XML/XLSX validation, exact numeric tokens,
  optional player availability and atomic both-tab aggregate validation.
- `kvk/services/new_source_digest.py`: length-prefixed typed canonical SHA-256 v1.
- `tests/kvk_source_fixtures.py`: entirely synthetic in-memory workbook generation.
- `tests/test_kvk_new_source_schema.py`
- `tests/test_kvk_new_source_metadata.py`
- `tests/test_kvk_new_source_parser.py`
- `tests/test_kvk_new_source_digest.py`

### 4. Modified Files

Only this task pack receives an appended delivery record. No existing Python, package initializer,
requirements, index, architecture, acceptance-scenario or unrelated task-pack content was edited.

### 5. SQL Changes

None. SQL has a separate no-change review disposition at the exact HEAD above. No SQL connection,
schema authoring, migration, deployment validator or disposable/live database operation occurred.
Local repository definitions are not deployed-state evidence.

### 6. Helpers Reused

Reused stdlib dataclasses/enums, Decimal, hashlib, zipfile/XML parsing and pinned openpyxl 3.1.5.
Inspected legacy schema/import helpers and the existing shared-helper inventory. Legacy integer
coercion, timestamp assumptions, label truncation and application-heavy imports do not satisfy
S1, so none were imported. Inert package initializers remain unchanged. No eager exports.

### 7. Refactor Findings

No direct SQL, Discord dependencies, public output, caches or persistence were introduced.
No independent legacy cleanup or WS1 repair was pulled into this task. One initial Changes-review
finding was fixed within the existing parser/test manifest; details remain in private scan evidence.

Ordinary formulas remain inert private typed evidence. Array/data-table formula descriptors,
non-XML binary package parts and novel tail annotations fail closed for schema review. The approved
aggregate tail shape is at most nine numeric E-column annotations after a blank separator. This is
an XML-only source schema, not a general-purpose Excel document importer.

### 8. Test Plan with Actual Outcomes

Execution used Python 3.11.9 with the repository's existing `.venv/Lib/site-packages` supplied
through PYTHONPATH: openpyxl 3.1.5, pytest 9.0.3, pandas 3.0.2. The latter two differ from the
requirements pins; no dependency installation or requirements changes occurred. The new runtime
uses no pandas. The default Python alone lacked openpyxl; `.venv/Scripts/python.exe` is absent.

Exact pack command, run on both delivered source and final review worktree:

```powershell
python -m pytest -q tests/test_kvk_new_source_schema.py tests/test_kvk_new_source_metadata.py tests/test_kvk_new_source_parser.py tests/test_kvk_new_source_digest.py tests/test_kvk_all_schema.py tests/test_kvk_all_import_service.py
```

Final outcome: **181 passed**, 3.86 seconds in the final review worktree. Earlier failures exposed
a Windows CRLF fixture serialization issue, the initial golden-vector placeholder and invalid
numeric XML handling; these were corrected and final tests rerun. No unrelated failure remains.
The in-scope security fix adds six alternate-part positive/negative cases.

- Architecture validator: passed, exactly ten Python paths.
- Deferred-item validator: passed for this pack; final appended block rechecked below.
- Security-routing validator: passed, zero errors/warnings; repository-wide read-only scope is
  intrinsic to that validator, and does not scan source vulnerabilities.
- Test selector: exit 0 with the exact ten Python paths; recommends full tests, smoke and registration.
- Focused pure import smoke: passed without constants, Discord, SQL, utils or pandas imports.
- Ruff: passed on all ten task paths.
- Applicable pre-commit: passed end-of-file, merge-conflict, line-ending, large-file, Ruff and
  logging-basicConfig checks. Nonapplicable hooks report skipped.
- Black CLI stalled and was interrupted, including its single-worker attempt. Sequential
  `black.format_str` with the repository's line length 100/Python 3.11 mode formatted and then
  verified all ten files; AST parse and final scan-copy byte equality also passed.
- Pyright hook skipped: configured repository-wide scripts/bot_config scope excludes S1 and does
  not accept task filenames. Staged-only Gitleaks hook skipped: no files were staged. New source
  and synthetic fixtures were inspected for private data/credentials; no such contents were added.
- Full pytest, log-noise full-suite runner, application-wide smoke and command registration are
  justified skips for this isolated S1 boundary: no shared-helper/runtime wiring, command, startup,
  scheduler, cache or persistence changes. Focused legacy regression and pure smoke passed.
- `git diff --check`: passed. New Python hygiene checked separately because the files are untracked.

Digest golden vector independently reproduced from the documented length-prefix encoding:
`bda549cea82699c69fae53e5ae25455572c6e0d1ceddb46627d490aa18b59395`.
A synthetic 5,806-row workbook (533,855 compressed bytes) parsed under default limits in 4.247
seconds; fixture generation took 1.433 seconds. This is not a full-maximum memory/throughput benchmark.
Lowered-limit negative tests exercise every ParseLimits field; default constants are asserted.

T01–T20 are covered at the **S1 parsing/metadata/digest boundary**, plus T63's inert-input portion.
Persistent alias acceptance/replay (T01/T02), correction/selection effects (T04/T07), evidence lookup
(T06/T08), historical migration behavior (T20), and export/Discord escaping (T63) require later
owners. S1 returns prepared facts only, not SQL acceptance or publication outcomes. T68 allocation
and T69/T70 endpoint/configuration behavior remain later-slice work. No live-input parity is claimed.

### 9. Security Review Decision and Evidence

Routing: bot **Changes**, exact task-only uncommitted patches, **Deep off**. SQL separate no-change
skip. No standard/deep repository scan, external finding disclosure or new Codex task.
Parent-only sequential review; no independent agent. Preflight ready with the documented
parent-only warning. TAC advisory status `granted`, grant `tac1`.

Initial scan `104c4527-a108-4556-8822-741332cc5928`: completed, one validated finding, complete
coverage; the original review worktree remains unchanged. The finding was remediated within S1.

Final scan `5dd053ad-ebf3-4f64-a1a9-5586c5c3a6f3`: completed, **zero findings**, ten reviewed
source/test surfaces. Exact base/head are both `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`;
authored working-tree snapshot is
`codex-security-snapshot/v1:sha256:76da2f063eae45a79dd4aa112077e66b8d59c886bb964a5c33e623290bc59890`.
The final reviewed worktree is byte-identical to all ten delivered Python files.

**Evidence gap:** sealed canonical `coverage.json` reports `partial` and retains the earlier
`final-evidence` checkpoint reason, despite the complete final draft and all ten reviewed surfaces.
The sealed artifact was not rewritten. This is an unresolved security-evidence gate; do not claim
fully complete canonical security coverage or merge readiness. There is no additional unresolved
code finding identified by this review. No replacement scan was launched solely to hide this gap.

Private canonical manifest/findings/coverage/report and fix evidence are retained beneath the scan
tool's temporary `codex-security-scans-FXJcWu` directory, with the exact scan IDs above. No private
finding detail or workbook/player-row evidence is copied into Git.

### 10. Deployment Steps

None authorized or performed. No real import/export, Discord action, restart, deployment,
activation, production SQL, pull/reset/merge/push or PR. Do not proceed to another pack.
Rollback before wiring is removal/reversion of the isolated new modules/tests after review; there
is no database or external effect to reverse. Resolve the canonical security-evidence gap and
review S1 before separately approving a successor slice. G4 remains separate.

### 11. Deferred Optimisations

No new unrelated non-security debt established. Existing legacy reporting/export and ProcConfig
WS1 items remain separate and unchanged. The security evidence gap is not deferred optimisation.

**S1 stop point:** implementation and focused validation delivered; review pending, with the
canonical security coverage-status gap explicitly open. No self-approval or automatic next task.

Final preservation follow-up: Git reported the two nested review worktrees as untracked
directories. Two exact entries were appended to local `.git/info/exclude`, preserving its
existing contents; no tracked ignore rule or Git config value changed. These retained review
artifacts are now excluded from accidental staging.

Final actual checks: preservation passed for all 1,522 captured files/original pack prefix;
exactly ten new authored Python files; final scan-copy byte equality passed; index empty;
SQL clean. Appended-pack deferred validation, architecture validation (ten Python files),
security-routing validation (zero errors/warnings) and git diff --check passed.


## S1 security evidence closure - 2026-09-09

The operator explicitly requested resolution of the security gap. This append supersedes the
open-gap status in the historical delivery above; it does not rewrite the original sealed scan
or record operator acceptance of S1.

Changes scan `411061cc-b75a-48f1-8c95-820d2dadb55b` completed and sealed at
`2026-09-09T16:36:36.676197Z`: **complete canonical coverage, zero findings, zero deferred items,
zero open questions**, all ten source/test surfaces accounted for. The completed canonical
manifest, findings and coverage were read back through the security tool after finalization.
The earlier partial scan remains retained unchanged for audit history.

Exact bot target: `C:/discord_file_downloader/.codex_scan_stage/s1-final`, task-only working tree,
Changes, Deep off. Base/head both `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; snapshot unchanged:
`codex-security-snapshot/v1:sha256:76da2f063eae45a79dd4aa112077e66b8d59c886bb964a5c33e623290bc59890`.
Fresh byte comparison verifies all ten reviewed files equal the delivered files. The generated
inventory contains five runtime files; all five synthetic test files were additionally read and
explicitly included in canonical coverage. Fresh parent-only review found no unresolved candidate.
Preflight ready with documented parent fallback; TAC status granted, level tac1. No delegation,
standard/deep scan or new task was used.

Private canonical artifacts remain under the scan tool's temporary directory:
`codex-security-scans-FXJcWu/s1-final/1a3a5de3d2e9f349c276725f6271ef19a7517c4f_20260909T163350Z_6hvct3v_/`.
Canonical coverage SHA256: `f38192ed029b19a035b138bb16b30eb5f2969d568396246591e1ac5fd4ee2a96`.
Canonical findings SHA256: `eadb19459e31005d18731a8d9b3152572226c2bb4bb2a722d3eca48b1ead1af1`.
Tool-reported scan usage: 836,637 total tokens (832,686 input including 782,848 cached;
3,951 output), from codex_rollout accounting. No private finding or player data is added here.

The exact six-file pytest command in section 14 was rerun against this immutable target:
**181 passed in 3.48 seconds**. This includes the six alternate-part preflight regression cases.
Runtime source and tests required no further edits. Prior lint/architecture/import-smoke evidence
still applies to identical bytes; the existing dependency-version and maximum-load limitations
remain explicit in section 8. They are not claimed as newly validated or live integration proof.

Bot remains `codex/kvk-source-s1`, original HEAD/remotes unchanged, index empty. SQL separately
reverified: clean main at `fc0e94ebd2e0a98286069c8a8b71365dd5178657`, original origin unchanged;
precise no-change security skip remains valid. All 1,522 captured pre-existing files and the
original pack prefix were verified preserved before this append.

### Remaining S1 completion gate

Implementation, assigned offline validation, legacy regression, exact-manifest preservation and
canonical Changes security evidence are delivered. **Operator review and acceptance of S1 remain.**
The acceptance review includes the documented XML-only schema/formula-descriptor restrictions and
test-environment limitations. No additional in-scope code defect or required unfinished S1 check
was identified in this follow-up. No acceptance, merge, promotion or activation is self-approved.

Persistent alias acceptance, scan allocation, B0 roster application, endpoint calculations,
SQL publication, public rendering and runtime intake are later-slice responsibilities, not an
unfinished S1 implementation. The approved EndScanID and separate aggregate/daily semantics remain
unchanged. No later pack, Git publication or live action was executed.


## S1 operator acceptance and PR authorization - 2026-09-09

The operator accepted S1 after the security evidence closure and explicitly requested PRs
marked ready for review. This authorizes committing and publishing the exact S1 delivery for
mirror and production review; the earlier no-push/no-PR restriction is superseded for this step.
No merge, deployment, activation or successor slice is authorized. SQL has no S1 delta.
Only the ten approved Python files and this canonical S1 pack belong in the PR delta.
Other planning documents and pre-existing working-tree edits remain outside these PRs.
The pack links to locally retained architecture/planning references that are not published by
this S1-only change. The complete implementation and validation boundary is recorded here.


## S1 PR review follow-up - 2026-09-09

The operator requested review comments be actioned, answered and resolved. Mirror PR #263
had one optional precision-evidence comment; production #570 had no inline findings.
Centralized the pinned openpyxl worksheet-path adapter, normalized one package-leading slash,
and reject absent/unresolvable worksheet evidence with SourceValidationError. Every preflighted
XML part now retains its token map, including empty maps. Numeric cells require their original
XML lexeme; the float-derived string fallback is removed. No dependency or schema version changes.
Nine synthetic regressions cover relative/absolute paths, missing loader attributes or paths,
lost token maps in player/aggregate parsing and legitimate text-only aggregate worksheets.
Exact six-file S1/legacy suite: 190 passed in 5.59 seconds. Existing digest golden vector passes.
Only the parser, its test file and this append change; original S1 and operational boundaries hold.
Separate Changes reviews of the follow-up commit ranges, Deep off, are recorded in PR replies.
The hosted Codex code-review summaries report failed jobs on both original PR heads; these are
not passing reviews. Copilot reviewed both PRs, and local Changes evidence remains separate.
