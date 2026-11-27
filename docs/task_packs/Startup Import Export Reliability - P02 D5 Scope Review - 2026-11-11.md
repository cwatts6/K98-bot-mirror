# P02 D5 scope review and first bounded slice

Review date: 11 November 2026. Status: scope packet prepared; implementation and
native execution await scope confirmation. This is a review of the combined
solution, not D5 acceptance, deployment readiness or a new authorization to run
business work. The existing D1-D4 and P01 decisions remain in force.

The proposed D5a-f scope is retained with one ordering change: bring the bounded
Personal Stats cancellation/drain investigation forward within D5a, before
expensive native correctness and cost work. Keep broader lifecycle qualification
in D5d. Prepare the cost comparison design during D5a; execute it in D5e only
after correctness, ownership and fixture prerequisites pass.

The [complete reconciliation appendix](Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Obligation%20Reconciliation%20-%202026-11-11.md)
retains every F01-F32, C01-C16, all 73 action pairs, the four empty kinds,
A01-A14 and D01-D06. It supplements the active registers; it does not replace
them with a shorter checklist. The original coverage ledger's 371 paths and
separate final sweep's 322 additional dispositions remain historical scoped
evidence, not whole-module approval or a new P05 sweep.

## Fresh baseline and evidence custody

| Item | Verified result and limit |
| --- | --- |
| Bot checkout | Initially clean `main` at `52e6307df77472a12921fbc3a3998e397d512d9b`. Another process changed it during review to clean `main` at `e7443e37212ca91e20d531b3684cc369d0fe1505`, the scrubbed mirror refresh from private `bd9f4c6d`. Git tree comparison found no changed paths between these two Bot revisions. No checkout switch/reset was performed by this review. |
| Private source | Fresh remote `main` read returned `bd9f4c6dde5a5d8107c2cf62cf3c4cf162ac01cd`. Every common tracked file matches the current Bot checkout by Git blob identity; exactly 31 private-only files and no mirror-only files. Private `ef8aee34..bd9f4c6d` changes Markdown only. |
| SQL checkout | Clean `main` at `b924cedd53e29dd88c0e9e7b66208b4fdc1e53ba`; fresh remote tip matches. No SQL-root AGENTS.md or SECURITY.md was found. Bot instructions and authoritative SQL definitions govern this cross-repository review. |
| SQL payload | `ba5c6acbefba0eb89cb18842a7f6c6811096759b` to current SQL HEAD changes documentation only. Keep migration `20261111_001_p02_d4_combined`, profile `p02_d4_v1`, 30 objects, four ledgers, six kinds and eight initial rows. No payload repinning to a documentation commit. |
| Installed state | Last accepted Bot `97abcce1b2a9e71b3959eff74525c57930a703e6` and Phase 1 SQL `a202a51440f17233800b49801bd31c3ead2a9227` are retained evidence. This review makes no fresh production observation and does not establish installation of D2/D3/D4. |
| Fresh static census | 41 SQL roots; 1,765 tracked Bot Python files and 811 SQL files. Bot inventory matches the retained D4 final census. No added/removed referenced paths. Forty-five SQL reference-file raw hashes differ from that older receipt; each matches its older hash after LF/CRLF representation comparison. Committed SQL source is unchanged. This explains census transport differences; it does not relax release byte authentication. |
| Sequence/wrapper | Lexical schema census still reports `KS4_UNO_SEQ` and `usp_start_rok_tracker_log_backup` as missing. Their qualification definitions exist under SQL `qualification/p02_d4`; installed/dependency evidence, not creation of guessed schema objects, owns this boundary. |
| Action census | AST-only comparison against `services/recovery_release_policy.py` confirms 73 pairs, 52 action names, 22 kinds, four empty kinds, zero missing/extra/duplicate rows. Every listed implementation path exists. This does not prove each runtime predicate or authorize actions. |
| Publication | PR740/741 and mirror/SQL publication receipts are retained from the handoff and local final-review receipt. Fresh remote branch identities agree. The GitHub connector was unavailable; this review did not independently refetch every hosted check/comment. The secondary review remains incomplete, not an additional pass. |

Private review evidence is under `.codex_artifacts/p025`. Original private logs
remain at `.codex_artifacts/p024` and were read without modification:

| Original log | Bytes | SHA256 |
| --- | ---: | --- |
| `d4-private-quality-final-failed.log` | 31619 | `528deff3b5bd983c148572a971c924336ca8ed58fc4a4cbd8c2e6f28a13b8ec3` |
| `d4-private-quality-final-ci.log` | 123343 | `65bbc5ce6b48b088fb0b7643a0325e06d066888ca30aa5bbdd516efb11d4bfa1` |

No raw logs, principal inventories, backup-job identifiers or player rows belong
in public publication. The archive manifest remains active; no archive is moved
or rewritten by this review.

## Caller and physical ownership matrix

| Family / owners | Current source boundary | D5 proof still required |
| --- | --- | --- |
| Startup and shutdown / C01/C10 | `bot_instance._close_teardown_admission` closes first-use Personal Stats admission; `_perform_graceful_teardown` rejects false drain. `DL_bot.py` withholds process release while Stats jobs remain. Existing owned-work helpers shield/drain entered work. | Unstarted owner cancellation, concurrent drains, native completion/settlement, exceptional process exit; no successful release receipt while capacity remains owned. Preserve accepted P01 startup behavior. |
| Player ordinary/guided/startup/continuation / C02/C05/C15 | `player_stats_cache`, `core/export_sql_connection`, `services/player_report_continuation`; actual statement cap is 15 seconds with existing row-lock policy. Separate producer, capture, cache and physical cleanup. | Real final-composition workload under unchanged limits; slow connect/guard/statement/commit/close facts separately; no factory fallback or replay after uncertainty. |
| Configuration startup/admin/typed/pipeline/recovery / C03/C07 | `proc_config_import`, `services/configuration_producer`, configuration recovery DALs, `sp_TARGETS_MASTER -> CREATE_DELTA_TABLES`. Provider input precedes atomic SQL publication. | Both overlap orders, typed return and exact attempted input, lost commit/capture ACK and cleanup; original committed result survives upkeep/log faults. |
| Imports, capture, reports and compatibility / C04/C05/C11 | `processing_pipeline`, import outcome/capture DAL, `legacy_export_snapshot_service`, `new_source_import_dal`; UPDATE_ALL2 and S11 report stages retain receipts. | Full 14-output/detail-state/numeric/queued-byte proof; retained borrower/raw/cursor resources; ordinary/direct/legacy compatibility and unfinished-stage boundaries. |
| Recovery snapshots / C05/C07/C16 | `core/recovery_sql_snapshot` owns a dedicated transaction, three-second statements, zero row-lock wait and shared `K98:maintenance-schema:v1`; mutation-time fencing stays separate. | Reader-first and maintenance-first; stale tuples, disabled SNAPSHOT, permissions, rollback/isolation/cursor/close failure. Raw-history SQL 3961 remains separate. |
| Authority observation versus mutation / C06/C07 | `scripts/run_export_authority.py:serve` authenticates before dispatch. `ObservationProgress` permits one active and one waiting exact read selector, retains transport/SQL uncertainty and drains the physical thread. Configuration reconciliation stays serial. | Saturation without mutation starvation; unauthorized/extra-field selectors; both trust-model branches; lost reply/handle-close/worker-start failure and shutdown. Never infer all `inspect` actions are passive. |
| Actual holder evidence / C05/C11/C16 | `legacy_snapshot_admission`, `export_contention`, `sql_lock_holder_diagnostics`. Logical reservation, session lock and observer result are distinct. | Known holders in both arrival orders with connection birth identity, resource/mode and original return; denied/racing evidence explicitly unavailable. Historical CFG-51421 holder remains unknown. |
| Shared file lock / C13 | `core/file_lock` via `file_utils.acquire_lock`; ordinary/guided player cache, startup verifier, Ark team/state, tracked-view wrapper. Cleanup retains an uncertain owner and releases only its physical object. | Body FileExistsError, cancellation, Windows/POSIX replacement and foreign sentinel, first failure plus cleanup failure, partial two-file Ark save, next-writer exclusion and restart. |
| Personal reads/render / C10/C15 | `StatsRuntime.submit` submits render work before owner-task scheduling; native Future callback owns settlement. `drain` awaits native futures, then checks jobs and shuts executor down. | Failed CI scheduling case and equivalent dataset/SQL/error paths; two render slots, eight SQL slots, 32 observers unchanged. False drain can stop shutdown; no cause or early-capacity-release defect is yet established. |
| Passive health/history/notifications / C08/C09/C12/C14 | P01 passive status and calendar/upload outcome adoption retained; Recheck, accepted actions, group/batch/outcome workers have distinct active effects. | D5 non-interference/adoption regressions only. P03 owns original-intent settlement; P04 owns history/projection/capacity/classification; natural acceptance stays with existing registers. |

## Six maintenance boundaries, reviewed together

`services/maintenance_dal.py` owns the dedicated connection through response
consumption and acknowledged session cleanup. `usp_RunMaintenance` takes, in order,
post-import owner, legacy snapshot, delta publication, player publication and
maintenance-schema guards; all acquisitions are zero-wait. Child failure retains
the original error; the DAL must prove cleanup before returning a pooled handle.
Logical absence or an orphaned running row means unknown outcome, not replay.

| Kind | Producer / actual child | Preserved invariant and D5 acceptance |
| --- | --- | --- |
| import | `UPDATE_ALL2` / `IMPORT_STAGING_PROC_CORE`; `usp_MaintenanceImport` | Exact scan/history/import receipt and archive integrity commit with due intent. Exercise conditional real KS4 index work and sampled stats; managed-reader exclusion in both orders. |
| configuration | `sp_TARGETS_MASTER -> CREATE_DELTA_TABLES`; `usp_MaintenanceConfiguration` | Atomic output and row/large-batch counters; preserve 168-hour/row eligibility and actual delta-index work. Optional logging failure cannot undo business or upkeep evidence. |
| player_report | `SP_Stats_for_Upload`; `usp_MaintenancePlayerReport` | Consistent report/capture/provenance and transactional due generation. Actual STATS_FOR_UPLOAD FULLSCAN follows publication; every maintenance kind respects player-publication exclusion. |
| kvk_output | `sp_ExcelOutput_ByKVK`; `usp_MaintenanceKvkOutput` | Required shape/unique indexes/views remain business work. Verify KVK number, object ID/create time/header revision; one target per invocation, partial progress and replaced targets never become aggregate completion. |
| final_stats | `usp_S11CompleteStatsReportsCore`; `usp_MaintenanceFinalStats` | Stage-specific dashboard/summary intent and exact success receipts; preserve essential pre-admission checkpoint. Real stats/completion checkpoint separately owned. |
| post_import | explicit Python worker/DAL -> `usp_update_stats`; `usp_MaintenancePostImport` | Actual sp_updatestats and all-kind response, dedicated physical owner, no uncertain retry. Direct child calls without exact guards refuse before work. |

Backup demand is separate from these child-success flags. `MaintenanceBackupClaim`
uses committed summary demand even if high log use defers statistics. The same
maintenance session retains its claim through one dispatch and exact ACK. Requested
is not completed (`backup_completed=None`). Hidden/denied metadata, failed/unknown
ACK, pre-existing historical queue rows and alternate configured factories stay
explicit tests. No real backup/provider dispatch is in this scope approval.

Existing native component suites exercise actual children, with synthetic data
and documented fault substitutions. Final-report continuation models large
calculations; backup dispatch is simulated. Those are useful component proofs,
not final-scale whole-flow or provider acceptance.

## Evidence gaps and missed/new issues

| ID / classification | Evidence and consequence | Owner / prerequisite / acceptance proof |
| --- | --- | --- |
| Q01 retained failure; sharpened lifecycle hypothesis | CI 42998021332 attempt 1 at `8b6879bf` failed final `runtime.drain()` at test line 63: 1 failure, 13,248 passes, 1,458 skips, 19 warnings, eight subtests. Test and entire Personal Stats tree are unchanged from private baseline. Four focused cases, one same-head full retry and PR741's later 13,249-pass run do not close it. Source has a separate Future-completion callback and immediate final jobs check; a done Future with settlement still queued is a candidate ordering to investigate, not an established cause. | D5 lifecycle owner; bounded offline schedule harness first. Explain/reproduce native completion versus callback settlement and shutdown result. If not explained, retain explicit D5 qualification gap. No assertion/timeout weakening. |
| Q02 current environment gate | Fresh development host read: non-elevated `cwatt`, PowerShell 7.6.9, 8.16 GiB free memory, 1,344.29 GiB free C: disk; K98DEV and VM management services running. Hyper-V inspection denied by host permissions; no PSSession visible in this newly created shell. This says nothing about sessions in other PowerShell processes. VM/network/guest/database state remains unverified. | D5a environment owner + operator; exact retained VM identity and network isolation, current elevated Windows PowerShell 5.1 session, guest/process/SQL/resources/retained input receipts before any native proposal. No service start, UAC change or guessed session. Re-sample memory: the single sample has little margin above the floor. |
| Q03 retained-data feasibility gate | Phase 1 acceptance records exactly 21 inputs consumed, completed captures and database returned READ_ONLY/RESTRICTED_USER. Historical scripts contain exact prior session/run bindings and reset/restore paths. Their existence is not authority to reuse them for D5. Five new balanced pairs cannot be assumed executable from this state. | D5a/SQL/performance owner; first inventory and authenticate retained data and receipt state. Prepare an exact non-replay candidate qualification strategy; if it needs new inputs/reset/restore/settings changes, present that separate concrete decision. Do not substitute small synthetic costs for final-scale acceptance. |
| Q04 inherited opt-in test failure | `test_stats_report_continuation_sql.py` expects only exception_types/observed_utc to change, while `recovery_health.failure_detail` fingerprints exception type evidence. D3 records this assertion failure separately. It is not the render failure or proved D3 regression. | P04 diagnostic/history owner with D5 test coordinator; pin intended fingerprint/revision contract and classify before including the test as an unconditional green gate. Keep assertion and failure intact; no opportunistic fix under D5a. |
| Q05 newly explicit negative-control gap | SQL `usp_update_stats` selects all six fixed kinds. Bot `validate_receipts` rejects duplicates/invalid rows but requires only post_import; its fixture intentionally returns one row. `maintenance_service` can therefore assess completeness from a subset. This is a source-confirmed validation coverage gap; no ordinary intact-SQL truncation or production incident is proved. | D5b Bot/SQL receipt owner; challenge each omitted kind and missing final_stats backup demand, duplicate/foreign rows and malformed claimed generation against the authenticated six-kind contract. Decide complete-set versus an explicitly scoped response contract before any correction. Reject false completeness while preserving physical cleanup and original error. |
| Q06 retained isolation failure | Private `ddl-snapshot-rebuild.json` records rawError 3961 with rawAfter null; metadata remained readable. Managed recovery readers now share a schema exclusion guard; arbitrary history readers and ad-hoc DDL do not thereby become qualified. | D5b/c SQL owner; classify every actual reader's guard/isolation and both arrival orders. Preserve historical failure; qualify supported paths, leave arbitrary unguarded reader/DDL combinations outside the supported claim. |
| Q07 source/custody drift handling | Shared checkout changed during review; Git trees proved identical. Older census SQL hashes differ only by line endings. Unchecked ref movement or hash normalization could otherwise misattribute qualification. | D5a/f release reviewer; seal Git identities plus exact artifact hashes, recheck before edits/runs/publication. Keep source equivalence separate from actual-host custody and fixed payload authentication. No reset, historical hash rewrite or extra registry entry solely for this review. |

Q01/Q04/Q06 remain independent failed evidence. No evidence joins them to SQL
51400/51421 or proves a common root cause. Other unrelated refactors retain their
existing owners: broad importer extraction, wider numeric conversion, snapshot
decode/rebuild optimization, Stats UI/SDK acknowledgement, unrelated MGE/Ark
performance and standalone pre-KVK/weekly physical-close debt. No new broad
framework, scheduler, outbox, index programme or grant is proposed.

## Revised D5 slice order and dependency gates

| Slice | Entry and concrete exit |
| --- | --- |
| D5a reconciliation | This packet and full register; source/caller/evidence reconciliation; first bounded offline Q01 investigation; read-only target/fixture readiness. Exit with exact case/input/state/identity and operation/stop/cleanup matrix. Missing native prerequisites stay explicit. |
| D5b correctness and actual children | Approved exact isolated target and operation packet. Compare all 14 exports, 42 detailed output/state tables where applicable, underlying oracle and original queued bytes against accepted Phase 1 semantics. Actual six children and Q05 response controls; no business rerun to obtain a nicer receipt. |
| D5c observation and competing owners | Correctness holds. Both arrival orders for relevant global/account/season/schema/delta/player/file boundaries; actual known holder evidence, alternate factories/rights, saturation, serial mutation, disabled isolation and stale tuples. |
| D5d full lifecycle/fault/restart | Q01 result folded into broader caller coverage. Lost grant/commit/dispatch ACK, rollback/reset/cursor/guard/close uncertainty, process death, restart with retained generations and physical resources. Unknown outcomes stay owned, no fallback/replay. |
| D5e measured costs | D5a design fixes comparable OFF/ON work and actual maintenance exposure. Execute only after prior correctness/lifecycle gates and exact data authorization. Warmup then five balanced pairs at minimum, alternating first arm; final-stage and overall medians plus sampled resources and denominators. |
| D5f integration closeout | Every appendix row links to final candidate evidence or an explicit unresolved gate. Reconcile original failures, whole source/profile/updater tuple and archive/changed-path manifest. Prepare D6 readiness; do not silently waive a gap to call D5 complete. |

D5b preserves exact bigint/decimal/NULL/negative/overflow/halfway semantics and
latest names across historical reports. Retain raw serialized queued payload
bytes/digests, not reserialization equality. Reuse the Phase 1 independent oracle:
its final exports had 49,468 rows/827,683 cells; detailed source checks covered
19,920 endpoint, 432 aggregate and 117,696 combined-summary cells. These are
historical counts, not new D5 targets or passes. Compare dates against each actual
report execution clock. Keep existing unspecified equal-score ordinal policy;
a stable secondary key would be a separate behavior decision, not a prerequisite
for the first offline slice or an excuse for broad tolerance.

OFF/ON must differ only by the reviewed observation/diagnostic condition on the
same candidate and comparable admitted work. Measure maintenance separately and
within total eventual cost; do not obtain a pass by moving expensive work outside
the timed interval or warming one arm more than the other. Record due generations,
actual child entry, observer count, successes/refusals, manual actions, false
incidents, convergence and cleanup. Frozen numeric gates remain:

- RCSI off; host free memory **before VM startup** and each relevant disk
  reserve at least 8 GiB. The original Phase 1 implementation document explicitly
  excludes an additional 8 GiB post-start host reservation. Do not impose an
  8 GiB free-memory threshold inside the 8 GiB guest. See the D5a.2 memory-gate
  correction; the earlier wording is preserved in its private receipt.
- Optional statistics require sampled log below 70%; version store below 512 MiB.
- Three-second observation statements, zero row-lock wait; held metadata case
  bounded to 30 seconds. Other existing operation-specific budgets remain.
- After warmup and at least five balanced pairs: overall median ON <= OFF * 1.20
  + 1000 ms; each report-stage median ON <= OFF * 1.20 + 250 ms.
- The 1800-second rehearsal cap is not a Bot timeout increase. A failed resource
  or cost gate stops progression and retains the run; no limit increase or repeated
  runs to obtain green. No new input copy/reset/restore or backup-schedule change.

## Exact first bounded slice proposed for confirmation

**D5a.1: offline cancellation/drain investigation.** Development checkout only;
no SQL connection, VM execution, provider, Discord client or production operation.
Pin current Bot tree and Python/dependency versions before running. Use inert
render/read functions, real bounded threads, controlled asyncio scheduling and
test-owned temporary files. Keep runtime behavior and all current assertions,
timeouts and capacity limits unchanged while investigating.

Proposed test work belongs beside
`tests/test_personal_stats_render_submission.py`,
`tests/test_personal_stats_shutdown.py` and
`tests/test_personal_stats_owned_reads.py`. Reuse `StatsRuntime`, `drain_awaitable`
and `drain_thread`; do not introduce a replacement lifecycle framework.

| Cases | Deliberately controlled schedule / required observation |
| --- | --- |
| 1-4 | Cancel both owner tasks before first scheduling; first/second native completion in both orders, with normal versus deliberately queued settlement. Third render must refuse until physical settlement. |
| 5 | Both native futures already completed while their settlement callbacks are still queued. Record whether drain returns before the jobs ledger settles. A synthetic hold establishes mechanism only; correlate with a normal-loop event trace before claiming CI cause. |
| 6-7 | Two concurrent drains, each entering first in turn; same physical jobs joined, consistent results after settlement, executor shutdown accounted for separately. |
| 8 | One native render raises while the other remains active; original exception retained and remaining job drained. |
| 9 | Repeated cancellation of an entered drain; cancellation does not release native slots or permit a new runtime while work remains. |
| 10 | Owner-task allocation failure after executor acceptance; submitted work and callback stay owned. |
| 11 | Executor submission rejection before acceptance; only the unsubmitted reservation is released. |
| 12 | Executor shutdown failure/uncertainty after physical work completes; no claimed successful shutdown or hidden first failure. |

One bounded pass through these twelve schedules, then one invocation of the
three existing focused modules. No stress loop, blind full-suite retry or rerun
to obtain green. Keep existing 4/5-second native fixture release guards and
12-second subprocess watchdogs where those fixtures use them; new cases must
fit within those bounds. Maximum two rendering workers; observer and SQL limits
unchanged. Proposed aggregate wall-clock cap: five minutes, a test-run stop
boundary only, never a new application deadline.

Record only finite test events: submit, thread enter/return, owner cancel,
Future state, callback queued/entered, jobs count, drain enter/return and executor
shutdown enter/return, with case/process/loop identity. Cap new diagnostic output
at 1 MiB for the slice. Do not add production instrumentation. On first failed
safety assertion, stop dependent cases, retain the trace and classify it before
changing any code. Independent missing prerequisite cases may be reported as
not run; never count them as passes.

Cleanup: each case releases only its own barrier in finally, joins its actual
workers and drains settlement before closing its loop. No clearing runtime.jobs,
private hold registries or locks to force success. If cleanup cannot be proved,
retain the owned child/process evidence and stop; a watchdog termination is a
failed test, not a successful physical drain. Test output stays outside operational
logs. Before/after hash checks verify the two original CI logs remain unchanged.

Exit is either a demonstrated cause/mechanism with a focused correction proposal
and equivalent-caller test matrix, or an explicitly unresolved Q01 with the next
specific evidence needed. A runtime fix is not preselected or authorized by the
investigation proposal. SQL/native work remains behind its exact target gate.

## Architecture, validation and remaining decisions

Commands/views remain thin. Services own orchestration/outcome semantics; DALs and
authoritative SQL own transaction/receipt contracts. Physical custody remains in
the existing SQL/file/owned-work helpers. No SQL schema, runtime, test, config,
permission, timeout, release registry or helper behavior changes in this review.
The new Markdown packet is the only proposed tracked delta; original registers
remain intact. Relevant guidance read includes core standards, local SQL,
startup/shutdown, singleton, Windows custody, scope/test/SQL/security routing and
current D2-D5/programme references.

For this Markdown-only packet: run architecture, deferred-item, security-routing,
test selection, introduced-link/register completeness and whitespace checks.
Runtime pytest, imports/registration, native tests and a new security scan are
skipped because no executable or operational behavior changes. Future executable
Bot and SQL deltas require separate exact Changes targets, Deep off, or a precise
documented skip; prior scans do not cover a later correction.

Review validation: architecture validation passed (zero Python files applicable),
deferred-item validation passed for both new documents, and security-routing
validation passed with zero errors/warnings. The test selector ran successfully;
its generic recommendations were smoke imports, command registration and four
release/schema/permission regression modules. Those executable checks are skipped
for this scope-only Markdown addition: no release manifest, command, schema,
permission or executable file changes. Full pre-commit/pytest is likewise not a
meaningful gate for this review packet; document hygiene and source/register/link
checks cover the actual delta. No original failed evidence is waived by this skip.

Only the following decisions are needed now:

1. Confirm the retained full D5 scope and revised order, including D5a.1's bounded
   offline investigation before native qualification.
2. Permit that test-only investigation under the stated limits. No runtime fix,
   native SQL operation or production operation is implied.

Later concrete decisions: establish a usable elevated Windows PowerShell 5.1
read-only session for the exact retained isolated VM, then approve only the
specific target/operation packet justified by its inventory. A new copy/reset/
restore or larger allowance is not being requested here. Keep rank policy
unchanged unless separately chosen. Q05 may require a focused response-contract
correction after negative controls, not a blanket D5 rewrite.

D6 remains separate: fresh actual-host source/updater/seed/process identity and
rights; every changed path and ancestor including archives; exact combined
transition, drain, SQL receipt, source/seed/start/readiness. After SQL commits,
continue forward from the same verified receipt only. P03 actual blockers plus
essential P04 corrections precede first normal import/export. D7/P05 own whole-flow,
provider and natural acceptance. No production installation, restart, dispatch,
retained-work recovery or normal import/export occurred in this review.
