# Bot Operational Reliability Workstream 1 — ProcConfig Import Reliability and Truthful Completion Reporting

Formerly Discord Embed Payload Safety Phase 2L. Canonical owner:
[Bot Operational Reliability programme](Bot%20Operational%20Reliability%20-%20Programme%20Pack.md). Read the completed
[design and exact manifests](Bot%20Operational%20Reliability%20Workstream%201%20-%20Design%20and%20Manifests.md) before further work.
The programme boundary/documentation is approved; runtime/test/SQL implementation is not.
WS1 is the first designed workstream, not a decision to execute ahead of other programmes.
The completed [backlog assessment](Backlog%20Priority%20Assessment%20-%202026-09-09.md) records
the operator's order: KVK Source Migration first, private inventory second, WS1 third. Bring any
proved KVK prerequisite exception back for approval. Runtime implementation remains unapproved.

## Task header and authority

- Date: 2026-09-09
- Owner: Chris Watts
- Type: bug fix / coherent reliability batch
- Status: audit/design and portfolio assessment complete; priority selected as third; runtime/design approval pending
- One-pass runtime implementation approved: no
- Resume: read the completed design and manifests; revalidate drift without repeating the audit; stop for implementation approval
- Current closeout changes are documentation only. Do not implement this phase in the Phase 2K PRs.

## Objective

Deliver a reliable ProcConfig import result from SQL execution through every caller: handle pending
results and connection cleanup correctly, preserve known committed work, and stop false success
in worker exit codes, reports, telemetry, command responses and pipeline summaries. Fix both the
underlying resource-lifecycle failure and the end-to-end outcome contract in one bounded delivery.

Completion means the complete participating path is corrected and tested; a local nextset call or
one changed log line is insufficient. Unknown completion must stay unknown rather than trigger
another execution or be advertised as rolled back.

## Entry verification and prior acceptance

Final Phase 2K closeout, 2026-09-09: mirror #262 merged at 12:06:38 UTC and production
#569 at 12:07:06 UTC. Verified mirror main: `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`;
production main: `1e72949dc69f1a1e5a529dbf1951039fe0ba74a6`. Operator supplied the same
production bot HEAD and empty `git status --short`. Associated restart invoked 12:08:56.672,
ready 12:09:10.755, full startup complete 12:09:15.539, new child PID 4800. This closes the
final deployment evidence gap; candidate smoke/test revisions below remain historical evidence.

Recheck the current source/deployment baseline when implementation is selected; do not reopen
accepted candidate smoke merely because documentation now records the merged revision.

Phase 2K was delivered and smoke accepted on production candidate
`36208765bf7200fa6855f3892e6b32d43b23bccf`, mirror `2d892cefcfdfa0a8263efe69997bf292503b23aa`.
Documentation closeout heads follow; they were not the original smoke revision.
Read the archived Phase 2K pack/starter and updated original embed payload audit. Natural fighting
KVK16 scan1122 had an acknowledged receipt and confirmed claim; KS independently skipped.
Isolated Pre-KVK sent/committed, status retained the receipt, and repeat edited the same message.
Registration stayed 36 primary / 100 grouped / 24 ops. Full promoted suite: 3514 passed, 2 skipped.

Natural Pre-KVK (~two months away), off-season production observations and Phase 2F natural
public-save evidence remain separate follow-ups, not blockers to the accepted Phase 2K smoke.
Do not reopen Phase 2J removal, change H/I sessions/defaults, or couple import success to Discord
message receipt. Preserve Phase 2K receipt/claim semantics.

## Required reading and skills

Read AGENTS.md, README-DEV.md, docs/reference/README.md and all indexed core engineering,
execution, testing, skills/refactor and deferred-framework documents. Then:
- Archived Phase 2K pack and original Discord Embed Payload Safety Audit Findings.
- Active and resolved deferred registers.
- docs/reference/REVIEW_HELPERS.md for shared worker/result helpers.
- Promotion Guide.md and runbook_diagnostics.md for delivery/evidence.
- Root/applicable SECURITY.md as policy context.
- SQL source of truth at C:\K98-bot-SQL-Server; record its branch/SHA/status.

| Skill | Decision |
|---|---|
| k98-architecture-scope | Use for caller map, layers, contracts, manifests and approval packet |
| k98-sql-validation | Use before implementation; validate complete called-procedure/result contract |
| k98-test-selection | Use selector plus the failure/commit matrix below |
| k98-deferred-optimisation-capture | Use for unrelated debt; never substitute for vulnerability triage |
| k98-discord-command-feature | Use if existing admin command response/interaction behavior changes; no new commands |
| k98-pr-review | Use for complete final diff and test/security gates |
| k98-promotion-check | Use for separate mirror/production history and rollback/deployment |
| k98-security-review-routing | Use; future runtime delta requires Changes review, Deep off |

## Observed evidence and source seeds

Repeated production HY000 connection-busy failures: 2026-09-08 09:20:17,
2026-09-09 07:14:26 and 2026-09-09 11:46:51. A successful intervening import does not close
an intermittent failure. The latest error occurs at proc_config_import.py:1086 restoring
`conn.autocommit = previous_autocommit` after sp_TARGETS_MASTER. The worker then logs
"proc_config_import completed successfully", and the pipeline reports ProcImport=True.

Preliminary source inspection (revalidate at entry):
- run_proc_config_import returns `(False, report)` on its critical-failure path.
- maintenance_worker.py::do_proc_import logs success and returns zero after any non-raising result.
  A false result tuple is therefore not presently honored by this wrapper.
- dbo.sp_TARGETS_MASTER declares @KVK, @ForceRepublish and @RepublishReason and rejects ambient
  transactions. Its authoritative definition is sql_schema/dbo.sp_TARGETS_MASTER.StoredProcedure.sql.
  Do not solve the driver error by putting this call inside the import transaction.
- Exact result-set/cursor chain and partial-commit behavior still require SQL-aware audit.
  This pack does not claim the root cause is fully proved or the live SQL definition verified.

## Scope and audit requirements

Trace every direct, injected, synchronous, async, subprocess and fallback caller of ProcConfig,
including admin invocation, startup, pipeline preflight/normal branches and maintenance/callable
workers. Produce a caller matrix with input shape, execution owner, submission boundary, native
return, exception handling, exit code, stdout/result envelope, report consumption and public status.

Trace import preflight, transactional and nontransactional modes, dry-run, each commit/rollback,
post-import target refresh, cursor/result-set consumption, autocommit restoration, cursor/connection
close, report/manifest/last-report writes and telemetry. Include errors raised during nextset/fetch
and cleanup, PRINT/row-count/no-row/multiple result sets and nested called procedures. Establish
what execute returning proves and what remains pending.

Inventory which downstream steps run after failure, partial commit or unknown completion:
exports, cache/target refresh, summaries, stats publication and retry suggestions. Preserve existing
continuation by default, but explicitly approve any required policy change; never silently convert
truthful failure into an automatic import replay or change Phase 2K admission.

## Proposed outcome contract — finalize in design

| Condition | Required meaning |
|---|---|
| All required stages confirmed | Successful import; success worker exit and pipeline status |
| Pre-execution/preflight failure | Failed/not started; no side effects claimed |
| Transaction rolled back with evidence | Failure with rollback confirmed for that transaction only |
| Earlier tables committed, later stage fails | Partial completion with explicit committed stages |
| Target refresh entered, acknowledgment uncertain | Unknown target completion; retain known import commit |
| Cleanup fails after confirmed work | Preserve committed work and record cleanup failure separately |
| Report/manifest write fails | Separate artifact failure from SQL completion; define required vs optional artifact policy |
| Timeout/cancellation/worker loss after entry | Unknown where not evidenced; no second execution or automatic retry |

Define exact type/schema, valid values, compatibility and stage-to-overall mapping before coding.
Legacy Boolean callers must not treat a nonempty tuple/dict/string as success. Define whether a
confirmed commit plus cleanup failure is overall failure/partial and which exit code is used.
Require consistent worker JSON/status, exit code, report.success, telemetry and pipeline summary;
transport exit zero alone cannot override an explicit failed domain result. Reject malformed or
contradictory envelopes conservatively. Preserve original exception and cleanup errors independently.
Reports must not claim that a post-commit failure undid committed SQL work.

## Architecture and helper reuse

Keep commands thin; service owns orchestration/outcome mapping, DAL owns SQL execution/resource
lifetime. Audit legacy root-module extraction triggers without undertaking a whole-module rewrite.
Reuse established result/worker parsing, run_step, run_blocking_in_thread, run_maintenance_step,
callable-worker and import-report helpers when compatible. Inspect file_utils.py, process_utils.py,
maintenance_worker.py, scripts/callable_worker.py, sheet_importer.py and database connection helpers
before adding a helper. Assess whether report shapes already express required stages.

Keep backend selection distinct from execution outcome: fallback is allowed only when the selected
backend is unavailable before submission, not after work may have entered. No duplicate execution
on False returns, exceptions, timeout, cancellation or serialization failure.
No global monkeypatch, durable retry queue, recovery protocol or new reservation layer.

## Manifests required at design approval

The following is an audit inventory, not authorization to modify every file:
- proc_config_import.py, maintenance_worker.py, file_utils.py, process_utils.py
- processing_pipeline.py, admin_helpers.py, commands/admin_cmds.py
- scripts/callable_worker.py and actual startup/import callers found by search
- sheet_importer.py and actual connection/result helpers
- tests/test_proc_config_import.py, test_proc_config_import_phase2.py,
  test_proc_config_import_offload.py, test_worker_module.py, test_run_step.py,
  test_process_utils.py, test_processing_pipeline*.py, test_integration_end_to_end_fake_worker.py
- README-DEV.md, runbook_diagnostics.md, deferred registers and this pack/starter

Return exact modify/create/delete/review-only manifests for runtime, tests, docs and SQL separately.
Justify any new service/DAL/helper path and map each changed caller to tests.

SQL review inventory: authoritative dbo.sp_TARGETS_MASTER, dbo.ProcConfig and every nested
procedure/result-producing statement reached in the affected path, plus import table/staging
contracts actually touched. Inspect exact SQL parameter, transaction, PRINT/SELECT/RETURN,
error and output contracts. Record missing definitions rather than infer them from Python.
SQL change manifest starts EMPTY. If SQL change is necessary, propose a separately gated SQL
diff/PR with source-of-truth validation, migration order and rollback. No live SQL/calendar/config
mutation, force republish or manual side-effecting procedure invocation during audit.

## Focused test and risk matrix

- Faithful cursor fake reproduces HY000 if mode changes while results remain; regression fails
  against the old implementation. Test no rows, multiple sets, row counts, error on later nextset,
  execute failure and close failure; do not mask errors with a permissive fake.
- Transaction ordering: import commit precedes autonomous target call; no ambient target transaction;
  rollback before commit, partial commits, known committed work after cleanup failure.
- Target refresh incremental/full selection and existing SQL parameters unchanged.
- Worker false tuple, true tuple, raised error, malformed result, contradictory report/status,
  sync/async callable and JSON serialization; assert exit code and absence of false success.
- Direct/offload/subprocess/fallback equivalence; one execution maximum after entry, cancellation,
  timeout, backend unavailable before entry and late completion. Test at real wrapper boundaries.
- Report/manifest/last-report on every terminal path, stale report protection, optional telemetry
  failure and missing/unwritable artifact paths; no secrets/raw row contents in errors.
- Pipeline preflight and normal branches propagate domain failure, partial/unknown status and
  preserve approved downstream behavior. Include subprocess-to-pipeline integration with fake SQL.
- Existing admin permission/defer/response contract if touched; no command count/default changes.
- Preserve Phase 2K delivery outcomes, claims and upload-route workflow-vs-message distinction.

Run selector, focused tests, architecture/deferred/security-routing validators, smoke imports,
command registration, applicable pre-commit hooks and full pytest/log-noise before promotion.
Separate operational logs from pytest evidence. Fix related failures only; document unrelated ones.
Do not invent passing SQL integration evidence: fake-driver tests and live SQL validation are distinct.

## Security routing

Current pack/closeout: documented skip, Markdown-only, no runtime/config/permission/data-access/
deployment-script change. Future bot runtime diff: Changes review with Deep off, exact base/head
or frozen patch recorded after design. SQL repository: no changed files yet; if approved SQL changes
exist, require its own Changes-only target/review. Use security-diff-scan, never a standard/deep
repository scan as a routine gate. Route captured vulnerabilities to security triage/fix workflows.
Retain final artifacts/findings disposition and assess any post-scan delta explicitly.

## Refactor decisions and exclusions

Audit findings must be classified safe / fix-now-after-approval / defer / not-runtime. Fix the
accepted result-lifecycle and false-success family completely, including shared affected callers.
Capture unrelated Stats/KVK History executors, lifecycle/view rehydration, DM/JSON, fighting durable
ownership, KS claim timing and Pre-KVK ambiguous-edit policy separately. No new commands,
payload redesign, H/I changes, broad SQL modernization, connection-string/MARS toggle workaround,
calendar/state swaps, forced duplicates, automatic retries or data repair.

### Deferred Optimisation
- Area: ProcConfig import, target-refresh result lifecycle, maintenance worker and pipeline
- Type: consistency
- Description: Repeated busy-result cleanup failure is followed by success status despite a failed domain return.
- Suggested Fix: WS1 must jointly correct SQL resource lifetime and end-to-end outcome propagation, preserving partial commits and single execution.
- Impact: medium
- Risk: medium
- Dependencies: SQL-aware architecture approval and deterministic wrapper/transaction tests; implementation not yet approved.

Batch prioritization (planning estimate): Impact 4 + Frequency 4 + Risk Reduction 4 - Effort 3 = 9,
a good coherent batch. These scores rank reliability work only, not security severity.

## Smoke, rollout, rollback and definition of done

After design/implementation/review, promote mirror file delta through the production workflow.
Use approved staging/isolated SQL validation for failure cases; do not inject live SQL failures.
Observe the next legitimate successful import: retain deployed SHA/restart, correlated worker
result/exit, domain report, commit/target status, manifest identity and pipeline summary. No false
success may follow a failed result. Existing production failure evidence plus deterministic negative
tests covers failure reporting without rerunning side effects to manufacture smoke.
Do not count one clean import alone as proof of intermittent-failure remediation.

Define bounded rollback before delivery: revert the WS1 bot delta, preserving Phase 2K and all
state/reports. Reverting Python cannot undo already committed SQL data or target publication.
No replay, quota repair, manual rollback or state deletion. If SQL changes are approved, specify
compatibility and its independent rollback/deployment order.

Delivery checklist:
- Complete caller/SQL/result/resource/side-effect map, classifications and approved exact manifests.
- Correct failure reproduced by meaningful test; complete outcome chain and single-entry proven.
- SQL contract verified; no unresolved schema guesses or unapproved mutations.
- All applicable gates and final Changes reviews satisfied; no unresolved accepted findings.
- Mirror and production PRs include outcome examples, evidence, migration/rollback and limitations.
- Operator smoke accepted; final merges/main/deployed SHA/clean checkout/restart verified separately.
- Update original audit, runbook, active/resolved deferred items and archive completed pack/starter.
- Retain natural seasonal/Phase 2F observations independently; never silently close them.
