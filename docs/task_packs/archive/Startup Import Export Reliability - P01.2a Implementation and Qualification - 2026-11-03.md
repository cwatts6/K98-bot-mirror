# P01.2a implementation and local qualification

> **Current programme checkpoint - 4 November 2026 (E68/E69):** P01.2a is deployed and accepted for its declared reporting/evidence scope at private `67c4e12a8ecf0c25280770860480ac65a6826602`.
> Read the [P01.2a closeout](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Closeout%20-%202026-11-04.md) for delivered corrections, evidence limits, learnings and remaining owners; [P01.2b handover](Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Handover%20and%20Scope%20-%202026-11-04.md) is the next review/design task.
> Earlier dated statuses, holds and next-action instructions in this document are retained history and are superseded for current scheduling. P01.3-P01.6/P02-P05 and exact incident recovery remain open; no replay of accepted work.

**Current E64:** mirror [#482](https://github.com/cwatts6/K98-bot-mirror/pull/482) and private [#722](https://github.com/cwatts6/k98-bot/pull/722) are merged. Private target `07bc9d6ebd5964f9bf660822f03a932a2472d966` is prepared for operator deployment, with final review, CI and the packet recorded in the [review/merge receipt](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Review%20and%20Merge%20-%202026-11-03.md). No production deployment, restart or recovery action was performed. Earlier scope, authorization and failed-run receipts below are historical.

Date: 3 November 2026. Owner: Codex. Decision: E59 approved implementation and local
qualification of the [design packet](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Design%20and%20Qualification%20-%202026-11-03.md).
The local candidate is implemented, but **Q12 producer-cost acceptance failed**.
It is not release-qualified. This is not a production acceptance receipt.
PR, merge, promotion, deployment, restart and provider/recovery actions remain outside
this approval. P01.1 acceptance and P01.2b/P02-P05 ownership remain unchanged.

## Candidate and preservation

- Mirror worktree: `C:/discord_file_downloader/.codex_artifacts/p1-mge-mirror-review`.
- Branch: `codex/p012a-evidence-bundle`; base `ecaaf2dcfa10b48cea1a088aa7465ab20bd0eb4b`.
  Its runtime source matched the previously reviewed mirror base `607f6a81`.
- Private deployed-source baseline: `0247371d90ec88d4c0639e9200164f4256086037`, read-only.
- SQL source: `C:/K98-bot-SQL-Server`, `7e91989f619deb46836194c7e705b0a9eb2ebe11`, read-only.
- Private receipts/scripts/logs: implementation evidence (private evidence: `.codex_artifacts/startup-import-export-review-20261102/p012a-implementation-20261103`).
  Source inventories retain SHA-256 hashes; source files are uncommitted. The root
  programme checkout's unrelated documentation/navigation changes are preserved.

## Implemented behavior

The existing complete-report action builds an incident-first ZIP containing
`summary.json`, `incidents.jsonl`, `operations.jsonl`, `startup.json`,
`diagnostic-health.json` and `manifest.json`. Missing or bounded sources are labeled
independently. Collection reads saved observations; it does not run recovery,
provider probes, completion checkers, imports, exports or runtime installation.

Physical children have identities separate from their parent. Their returned
booleans remain values, while explicit feature checkers supply feature outcomes.
Eight milestone slots preserve entry, physical entry, deadline, cancellation,
failure, parent return, verification and terminal observations. First failure is
retained. New pure projections cover configuration, player-cache/main-versus-last-KVK,
profile/name persistence, and tracked-view restoration outcomes.

The optional sink writes V2 and original-reader-compatible V1 files independently.
Its health distinguishes memory, attempted publication, successful publication,
restored observations and prior acknowledgements. Corrupt originals are preserved
without overwriting an occupied invalid-file slot. Restore does not replay counters.

One nonblocking process-wide lease covers report build and UI delivery. Runtime
registration uses existing ownership and refuses report admission without waiting
during reconfiguration. Cancellation drains entered physical work. Current
admin/guild/channel checks occur before reads, at continuation lookup and before
ephemeral delivery; attachments disable mentions and close their buffers.

The normal cap is 8 MiB, with supported smaller budgets down to 64 KiB. Incident
reads use 10-row pages plus lookahead; the existing DAL default remains 100. A failed
or overflowing incident scan discards its ZIP prefix and restarts explicit incident
continuation from the original cursor/cutoff, without an automatic rescan. Frozen
diagnostic continuations are actor/channel/guild/store/process bound, single use,
expire after 600 seconds and retain at most two 17 MiB sessions. Initial and later
parts share a generation and hash chain; fragments include the full component hash.
Minimum summaries remain in the initial ZIP. Oversized incidents give required-byte
guidance and leave the cursor unchanged.

The 30-second collection deadline is cooperative. It cannot terminate native SQL,
filesystem or Discord transport calls. A failed continuation send requires a new
collection because the token was consumed when the part was built. Neither limit
is presented as successful delivery or completed drain.

## Changed layers

| Layer | Files in mirror worktree |
|---|---|
| Shared optional observations | `core/operation_evidence.py`, `core/owned_work.py`, `core/startup_diagnostics.py` |
| Typed interpretation and sink | `services/startup_outcome_projection.py`, `services/operation_diagnostics.py` |
| Report construction | `services/recovery_evidence_bundle.py`, `services/recovery_complete_report.py`, `services/recovery_report.py` |
| Service, ownership and SQL read | `services/recovery_service.py`, `services/recovery_runtime.py`, `services/export_runtime_composition.py`, `services/recovery_dal.py` |
| Existing Discord callbacks | `ui/views/recovery_view.py`, `ui/views/recovery_backlog_view.py` |
| Regression coverage | `tests/conftest.py`, `tests/test_recovery_backlog.py`, `tests/test_recovery_report.py`, `tests/test_recovery_report_sql.py`, new `tests/test_recovery_evidence_bundle.py`, new `tests/test_startup_outcome_projection.py` |

No SQL schema, grants, ProcConfig, staging, required receipts, command identifiers,
protected launcher, provider protocol or release registry was changed.

## Local qualification

Use the worktree-local interpreter, `PYTHON_DOTENV_DISABLED=1`, synthetic test
configuration and operational-log isolation. No operational log reads were used as
test evidence. Each result below states its scope; skipped tests remain unexecuted.

| Check | Evidence/result |
|---|---|
| Focused final behavior | 760 tests passed; operational logs unchanged (`focused-final.log`). Covers ownership, startup, diagnostics, report, recovery, cache and composition callers. |
| Additional shared callers | 205 tests passed; operational logs unchanged (`shared-callers-final.log`). Configuration, event restoration/delivery, graceful shutdown, MGE refresh/publication/finalisation, interaction safety and redaction. |
| Final report/privacy regressions | 140 passed (`report-final.log`); includes digest-only memoization, identifier equivalence, required-size and delivery-cancellation checks. |
| Native SQL | 7 report tests passed using existing localhost K98DEV session-local tables created from authoritative definitions. All states, scope, SQL GUID ordering, timestamp precision, cutoff, action joins and 10+1 paging were exercised. Initial sandbox SSPI refusal was followed by an approved identical unsandboxed local-fixture invocation. No installed schema or production data change. |
| Native query cost | Authoritative temporary table/index definitions, 18,000 incidents and 1,800 actions: default 100-row pages took 1.39304 s over 180 pages; bundle 10-row pages took 11.44923 s over 1,800 pages. Ten-row page p95 was 9.6822 ms, p99 12.3465 ms. Actual SQL GUID membership matched, data checksum/revisions were unchanged, and a separate local observer found zero transactions after physical fixture close (`native-report-cost.json`). This reuses one local fixture connection with 5 s login/15 s statement/1 s lock limits; installed application/reader factories, network, retries and production plans remain unqualified. Two earlier harness expectations were invalid because the fixture deliberately makes per-page close a no-op; their logs are retained, not reported as DAL failures or cleanup proof. |
| Original V1 compatibility | Exact baseline reader loaded new V1 output; original writer added a downgrade interval; upgraded sink preserved legacy and V2 evidence. `original-v1-compatibility.json` retains original reader hash `61678d5433af061b469b6e2cf8351deb8ac78b92edb516ba74210f86b8d20f33`. |
| Production-sized bounds | `bounds-qualification.json`: 512 roots with all eight milestones and 16 children each; 23,351 bytes per exercised row; V2 11,956,657 bytes and V1 2,415,288 bytes. All 512 rows reconstructed through 64 KiB continuation and restored. Two maximum sessions retained 35,651,584 bytes. Additional peak RSS 104,288,256 bytes, below 256 MiB. This fixture does not claim every possible 32 KiB row shape. |
| Capacity loss | Actual 1,024 queue capacity: 896 ordinary +128 reserved critical; two refused offers, one critical. Actual 256 context capacity: one visible lost context, all slots released. Root refusal preserved failures and counted loss. |
| Publication failure isolation | Four actual-file write/flush fault cases passed, independently for V1/V2 (`publication-faults.json`). Prior file/hash/acknowledgement remained, temporary file was removed, other format published, two current memory roots survived, and raw fault text was absent from health. Replace failure and corrupt-file retention also have pytest coverage. |
| Saturated producer qualification | A barrier-stalled writer accepted exactly 1,024 of 2,200 events, counted 1,176 critical drops, and preserved all 400 business calls/returns. With all 256 context slots held, 400 scope attempts produced 400 explicit losses, zero events, and preserved all 400 calls/returns. Both scenarios used 200 matched worker pairs; timing under concurrent test/report load is retained separately from isolated normal acceptance. |
| Producer cost — failed gate | Final 200-pair check after the long qualification processes finished: median 13.65085 ->13.98195 ms (**+2.42549%, limit 2%**); p95 15.6509 ->16.0995 ms (+2.86629%, limit 5%); p99 17.0088 ->33.2246 ms (**+95.33771%, limit 10%**). All 400 calls/returns preserved; zero drops. Enqueue p95 0.0311 ms/p99 0.0477 ms and heartbeat deltas +0.1915/+0.6161 ms pass. `producer-cost-final-normal.json` and `producer-final-gates.json` are authoritative; the earlier passing run and concurrent-load run are retained but do not override this result. The harness compares the old/new observation/worker helpers with the same current sink, so it does not prove a complete old-versus-new sink cost bound. No claim of Q12 completion. |
| Report cost — passed | 200 alternating paired runs, identical 18,000-incident/64-operation fixture: candidate p50 3.72141 s, p95 **4.38244 s**, p99 **4.51823 s**, maximum 4.60322 s; limits p95<=5/p99<=10. Original builder/redactor baseline p50 7.53488 s, p95 8.87234 s, p99 9.30904 s. Extra peak RSS **4,698,112 bytes**, below 128 MiB. Final source and fixture hashes are in `report-cost.json`. Earlier failed/invalid partial runs are retained and excluded from acceptance; one baseline-sharing error was corrected by loading both original modules. Earlier final-run pairs overlapped broad pytest, later pairs did not; no samples were filtered. |
| Whole Windows suite | First run: 11,042 passed, 1,114 skipped, 8 subtests passed, 41 failed; loaded code before final correctness fixes. Broad rerun: 11,066 passed, 1,114 skipped, 8 subtests passed, 31 failed in 1,114.18 seconds (`full-final.log`, `full-suite-disposition.json`). All 31 failures are authenticated updater source-inventory assertions. No report failures remained. The rerun predates only the later redaction optimization, required-size message and three regressions, covered by the final 140-test batch. This is not a green whole-suite or updater-readiness claim. |
| Validators and lint | Architecture: 20 Python paths; deferred: no mirror Markdown delta; security-routing: zero errors/warnings; explicit-path test selector completed. Ruff and sequential Black apply configured rules. Configured Pyright: zero errors, 28 dependency-resolution warnings. Black's process-pool wrapper stalled locally; sequential calls to the same formatter/checker completed, without changing its rules. Selected-file Gitleaks: no leaks in 20 frozen files. Hash, whitespace, EOF, conflict-marker and size checks passed (`hygiene-final.json`); the cached large-file hook's Git attribute lookup could not operate on the outside-worktree snapshot, so its size check was performed directly. |
| Imports and registration | Synthetic-config smoke passed. Registration: 36 primary commands, 102 grouped subcommands, no drift. 21 command-registration tests passed. Standalone UI-import fixture failure was reproduced on the unchanged private baseline; see deferred capture below. |

The full-suite log guard exits on pytest failure before comparing log snapshots;
do not claim full-run log hygiene from that failure. The passing focused/shared
guarded runs explicitly prove their own unchanged operational logs.

## Security review

`k98-security-review-routing` required Changes review for diagnostics persistence,
SQL paging, authorization and Discord attachment/session handling. Deep remained
off; no Codebase scan was used. Bot history only; SQL has no diff.

First frozen candidate: scan `767a9288-9a80-4353-ab1b-0f3ab91c52ad`, digest
`5cfa4ae7fcfc6f2eea67b4f93f0abe9f77b86a9a60bad55c6a5050e9e0b5ae46`;
all 14 runtime and six test files covered, zero security candidates. Six ordinary
correctness issues were corrected and regression-tested: sink-health depth,
initial continuation linkage, minimum summary retention, persistence vocabulary,
restore-capacity accounting and child initialization attribution.

Second frozen candidate: completed scan `5cf9f142-f35a-4773-ae61-48552f25398f`, digest
`2cb7bf2e10de4498b49f7067ea9a67bb6ca701c6870f502613598ca1a8a1b76f`;
all 14 runtime and six test files covered, zero candidates. Unchanged-file review
was carried forward only with independently compared SHA-256 evidence. This scan
predates the final performance/required-size changes and is superseded below.

Final candidate: completed scan `6b457f0f-35ca-41cd-80b1-7b980efd2538`, digest
`f2661253d533d2e66f30993587c325a9b8a8b278f6f4338c331b8cc2df58f73d`;
all 14 runtime and six test files covered, zero candidates/findings. Final source
hashes were rechecked against `final-source-manifest.json`; the cache, identifier
fast path, required-size guidance and new tests were independently reviewed.
Canonical report: `C:/Users/cwatt/.codex/state/plugins/codex-security/scans/p1-mge-mirror-review/ecaaf2dcfa10b48cea1a088aa7465ab20bd0eb4b_20261103T191440Z_39q12m5z/report.md`.

The first review's usage tool reported 13,260,374 aggregate tokens across five
participating chats (13,211,408 input, including 12,921,088 cached; 48,966 output,
including 16,896 reasoning). These are tool-reported aggregate session counters,
not an estimate of incremental scan cost. Final completion returned no separate
usage measurement; no number is inferred for it.

Security closure does not prove production permissions, native timing, complete
functional qualification or deployment acceptance. Managed canonical scan reports
and source inventories are retained privately; no findings were suppressed into debt.

## Remaining acceptance and next boundary

The implementation preserves the design budgets. Qualification reports failed
gates instead of raising limits. Q01-Q10 have controlled regression evidence above;
the design table remains authoritative for unexercised permutations. Q11 establishes
local SQL behavior, not installed application/reader profile latency. Q12 report
latency/memory passed, but producer median and p99 overhead failed. Production natural
restore/download acceptance remains after a separately authorized deployment.

The authenticated updater source inventories still describe the deployed P01.1
bytes. Their failure against this source candidate does not authorize bypassing or
rewriting them. The later release package must select and qualify its complete
source transition and predecessor path, with exact final candidate hashes, review
and private-history equivalence. No routine updater-eligibility claim is made here.

Current decision: **hold P01.2a release readiness**. The approved design explicitly
requires a narrower implementation or a revised decision when measured cost limits
fail; it does not permit silently increasing them. The next focused correction must
identify and reduce producer/sink median and tail cost while retaining every typed
outcome, milestone, receipt boundary and owned drain. The existing measurements do
not establish the cause of the tail increase. Requalify against the unchanged limits
and obtain an exact Changes review for any new patch. This remains unfinished P01.2a
acceptance, not unrelated deferred debt and not permission to ship only the ZIP path.

## Deferred capture

Decision: defer the existing standalone import fixture issue; it reproduces on the
unchanged private baseline and is unrelated to this runtime change.

### Deferred Optimisation
- Area: `tests/test_ui_imports.py` dependency stubs.
- Type: consistency
- Description: The standalone UI-import test's stub omits `PLAYER_STATS_LAST_CACHE`, so imports fail on both this candidate and unchanged private `0247371d90ec88d4c0639e9200164f4256086037`. Synthetic full smoke succeeds; this is not proof that the standalone fixture is healthy.
- Suggested Fix: Reconcile the fixture's exported constants with the current import contract and verify isolated and suite-order execution in a separate test-maintenance change.
- Impact: low
- Risk: low
- Dependencies: Preserve standalone reproduction and baseline revision; do not weaken production import requirements to satisfy a stub.
