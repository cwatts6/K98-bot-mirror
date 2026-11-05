# P01.4 whole-solution design and delivery decision

> **Current E91, 5 November 2026:** The [complete local qualification receipt](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Complete%20Local%20Qualification%20-%202026-11-05.md) records the full original P01.4 design implemented and qualified locally, with both optional workers enabled in the unpublished candidate. Cost, physical-drain, diagnostic-priority, updater, regression and Changes-review gates passed. No CSV scope was deferred. Publication/deployment and natural-activity acceptance remain outstanding; earlier E88-E90 disabled/pending statements below are historical. Existing changes and archive moves are preserved.

**E90, 5 November 2026 — design review completed; proposed runtime changes are not implemented or qualified.** The operator approved reviewing the whole solution before deciding adoption and deployment sequence. Preserve the original F17/F30 acceptance scope. Both worker gates remain off. This supersedes E89's recommendation to adopt SQL now and defer file logging; it does not erase E88/E89 evidence. No publication, deployment, production/provider operation or new SQL connection occurred in this review.

Read with the [original design and acceptance contract](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Source%20Review%20and%20Design%20-%202026-11-05.md), [implementation receipt](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Local%20Implementation%20and%20Qualification%20-%202026-11-05.md), and [prior adoption decision](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Adoption%20Decision%20-%202026-11-05.md). Their dated approval-pending text is historical. This packet recommends the next implementation/qualification scope, not a release waiver.

## Scope summary and recommended decision

**Keep one complete P01.4 design: truthful outcomes and custody, two isolated optional I/O workers, one shared lifecycle contract, and bounded diagnostic reporting that cannot flood existing operation evidence.** Retain the existing file-thread approach as a candidate until valid measurements establish whether it needs replacement. Do not introduce a process, spool, new database queue or generic executor without evidence that the simpler design cannot meet the contract.

Default to one deployment after whole-solution qualification. If earlier value becomes necessary, split outcome/admission/custody corrections from the complete optional-worker foundation; do not split the current SQL worker from unresolved lifecycle/reporting work merely because its isolated tests passed. PR review slices and deployment count are separate decisions.

The scope can plausibly be completed with this architecture, but file physical-I/O qualification and combined cost remain unproved. Neither this review nor the new controls certify full P01.4 completion. A failed future gate means retain the evidence and revisit the affected mechanism; never weaken the limits or silently defer original scope.

| Original requirement | Existing evidence | Remaining work in the full design |
| --- | --- | --- |
| A: confirmed ingestion survives optional audit/refresh/notification failure; uncertainty remains uncertainty | Implemented; E89 focused regression matrix passed | Preserve results and rerun affected route/compatibility tests on final candidate |
| B: one selected-message admission, correct attachment selection, staged reader ownership and acknowledgement | Implemented and locally covered | Preserve cancellation/custody behaviour through integration; no restart/redelivery exactly-once promise |
| B: optional CSV cannot delay downloader/callback | Prototype disabled; duplicate write removed, remaining awaited append outside lock | Adopt only after startup, lifecycle, loss visibility, valid cost and native file failure/close qualification |
| C: optional audit SQL cannot delay the six selected entry paths | Isolated native SQL and route qualification in E89 | Preserve binding/no-replay contract; correct diagnostic pressure/lifecycle coupling; qualify revised and combined candidate |
| Whole application remains responsive with bounded memory and truthful physical drain | Individual evidence exists | Combined normal, saturated, faulted, restart/report and shutdown matrix; final updater/full-suite work |

## Findings that change the decision

### 1. The file failure is real evidence, but its causal interpretation was too strong

The retained E88 run measured added p95 timer lag of 15.2062 ms against the unchanged 5 ms allowance. It remains a failed qualification run. Its harness starts a 1 ms `asyncio.sleep` observer for each tiny operation. Baseline awaits aiofiles completion; the candidate returns after queue admission. Those arms have different event-loop wake-up patterns. Raw per-sample timings were not retained in E88, so its exact cause cannot be reconstructed conclusively.

New offline controls use the unchanged worker and the actual `append_csv_line` function extracted alone to avoid bot/config bootstrap. They write only private fixture CSVs, change no system timer settings, and use no SQL/network. Three blocks of 30 retained samples per arm, with rotating order, show:

| Original single-timer observation method | p95 range across three blocks, ms |
| --- | ---: |
| Do nothing | 14.494–14.991 |
| Offer to a worker that does no I/O | 15.132–16.102 |
| Offer to the unchanged file worker | 15.554–16.430 |
| Await the real aiofiles append helper | 0.007–0.202 |
| Await an executor completion that does no work | 0.000 |

An empty operation can appear much worse than awaited work. The evidence supports a wake-up/measurement confound, not a demonstrated 15 ms file-worker blocking cost. Zero-clamped timer samples also do not prove zero latency. Do not replace a functioning mechanism solely on that interpretation.

A second control uses the same external wake source for every arm and separately records source-wakeup lateness and event-loop delivery latency. Across two blocks, file-worker delivery p95 was 0.567–0.609 ms versus no-op 0.519–0.541 ms. Source-wakeup p95 was roughly 12–13 ms for ordinary arms. Deliberate 50 ms loop blocking produced delivery p95 44.166–46.955 ms; a deliberate CPU/GIL stall produced 17.685–17.691 ms delivery p95 and roughly 28.6–28.9 ms source lateness. Thus source lateness must also be retained; measuring callback delivery alone can miss CPU starvation of the observer.

These are causal controls, not a replacement acceptance benchmark: one-second observation windows, small CSVs, no actual downloader/business path and no combined SQL pressure. A first external-observer version failed to reliably detect its 25 ms CPU control; that receipt and source are retained, and no acceptance claim uses it. The default system Python initially lacked aiofiles; the installed project environment was used, without package changes. Final control writers settled 164 file and 182 no-I/O entries, zero failures/drops, and both stopped.

**Disposition:** file adoption stays held, but classify its mechanism as unqualified rather than proven intrinsically too costly. The SQL p95 timer-lag results used the related short-operation observer too: retain SQL's measured business timings/native drain evidence, but remeasure responsiveness in the final combined protocol. Do not describe the previous zero samples as universal zero lag.

### 2. SQL audit currently amplifies diagnostic overload

`ImportAuditWriter.action` projects every offered/rejected action; execution and settlement project further events. A full audit queue therefore emits repeated `failed` events. The existing diagnostic sink treats `failed`, `completed` and `settled` as critical; they can consume the reserved queue space. E89 pressure recorded 8,450 diagnostic drops, 8,192 critical. Static source explains a causal path; the receipt does not identify each dropped event as belonging to another business operation.

There is also retained-history coupling: current capacity/file-size eviction can remove a completed operation without distinguishing optional upload-audit records from other operation evidence. Fixing queue flooding alone would leave this path. Admission, processing cost, retained rows, report selection, restoration and file-size eviction must all respect priority.

**Disposition:** diagnostic isolation is required before either optional worker is adopted. Keep loss visible, but represent repeated loss as bounded state/counters rather than generating an event per loss. This is a directly related correction, not a reason to reopen the whole P01.2a/P01.3 programme.

### 3. Lifecycle is shared, and file startup/cleanup is not yet at SQL's standard

Both writers inherit `OptionalWriter`. Startup wires the file worker before SQL; file construction/start exceptions currently escape, unlike the SQL startup isolation. Teardown waits for file close before requesting SQL close. A stalled file join can therefore delay closing SQL admission. File `with open(...)` does not retain an explicit handle on an uncertain close as the SQL path now does. Current counters/projections also need consistent discard accounting and availability visibility.

**Disposition:** settle the shared lifecycle before release. Do not change required business ownership, singleton authority, source receipts or restart permission to solve optional I/O.

## Architecture direction and contracts

### Independent execution; shared policy

Retain exactly one SQL writer and one download-CSV writer, plus the already existing diagnostic sink. SQL and CSV do not share an execution queue, connection, default-executor job stream or business lock. SQL never runs on the diagnostic sink. A blocked SQL call cannot prevent the file worker from entering independent work, and vice versa. Ordinary disk/CPU contention is still possible and must be measured.

Reuse `services/optional_upload_transport.py` for bounded primitive admission and common lifecycle state. Keep SQL identity/connection rules in `optional_import_audit_worker.py` and `stats/dal/import_audit_dal.py`; CSV encoding/handle rules stay in `download_log_service.py`. A small proposed `services/optional_upload_lifecycle.py` coordinates these owners, replacing only the new root wiring. It is not a general scheduler. Reuse `core.owned_work` for cancellation-safe waiting and existing upload ownership registration for business settlement.

### Admission and outcomes

- Offers perform bounded primitive validation/serialization and nonwaiting admission only. No SQL, filesystem, hash of uploaded bytes, provider call, blocking mutex or arbitrary callback enters the offer path.
- Once adopted, unavailable/full/closed/error means an optional observation is refused. Never fall back to awaited SQL/CSV, spawn a replacement worker or replay the business action. Before adoption, the legacy path remains explicitly separate and source-gated.
- SQL local correlation remains distinct from an acknowledged SQL identity. No dependent write without exact binding; no retry, lookup/rebinding or replay after lost acknowledgement. Admission is not persistence acknowledgement. Current procedure result/status semantics remain unchanged.
- Preserve the detached five-column UTF-8 CSV shape, quoting and one-row source behaviour. Do not retain upload bytes/staged handles. Required Ready/fsync/hash/manifest/export receipts remain required and outside these optional queues.
- Preserve confirmed ingestion and exact export preparation authority. A diagnostic failure cannot turn a committed import into failure or authorize export/recovery.

### One lifecycle for both owners

Use explicit not-started/running/unavailable/closing/closed/cleanup-unconfirmed states with a single startup attempt per process. Both construction and thread-start failure are isolated from bot readiness, retain redacted error type, expose unavailable state, and prohibit automatic replacement or synchronous fallback. Repeated ready hooks cannot create another owner.

Split close into a nonblocking admission-close/discard request and physical settlement wait. After business admission closes and entered business readers finish, request closure of **both** optional queues before waiting on either. Discard only unentered optional work, with bounded per-kind/per-context accounting. An offer racing closure is either owned and accounted or rejected; no orphan or late SQL admission.

Join both owners through owned, cancellation-safe waits; an error in one must not skip requesting/observing the other's closure. These waits may use existing helper threads, but never create replacement I/O writers. Keep the diagnostic sink available while either owner can still report. Once both have physically settled or returned retained cleanup uncertainty, publish final partial/closed observations and close the diagnostic sink through its existing owned path. Aggregate uncertainty and refuse a successful overall drain receipt. If a native call never returns, retain its owner and continue to report draining; do not detach it or claim normal shutdown.

File writes need explicit handle custody across write/flush/close failures. A write error with confirmed close may record failure and allow later independent rows; it never replays the failed row. Unconfirmed close retains the handle, stops admission and prevents replacement/drain certification, matching SQL. Tests must prove original write failure and cleanup failure remain distinguishable. A bounded queue does not bound an arbitrary OS filesystem stall; the five-second native fixture gate is environmental evidence, not a universal deadline guarantee.

### Bounded reporting without flooding other evidence

Recommended implementation: a distinct, nonwaiting, coalescing upload-observation lane in the existing diagnostic sink. Do not send per-offer audit-failure events into its general queue. This lane carries only primitive observation state, not SQL/file work.

Give this lane its own admission lock; optional producers never hold the general queue lock. The sink takes a bounded lane snapshot, releases that lock, then validates/serializes it. No callback, nested lock acquisition or report work runs while either admission lock is held. Audit-write acknowledgement and worker settlement remain explicitly diagnostic facts, never business-commit or export-delivery evidence.

Proposed exact bounds: 64 correlation slots, each at most 4 KiB encoded, holding a first-failure observation and latest state/loss watermark; at most 256 KiB encoded mailbox retention. One slot represents aggregate file-worker state. Two fixed bounded worker summaries expose startup/closure state and saturating loss counters even when correlation slots are unavailable. This is an explicit extra mailbox budget to approve and measure, not a silent increase to existing queue/history limits. Python object/RSS retention must also pass sustained-cycle measurement.

Repeated updates coalesce by correlation; preserve first failure, latest state, monotonic sequence and cumulative loss. Replacing an intermediate observation increments an omission/coalescing count; a full lane records refused observations without generating another event. Final context removal cannot erase unpersisted first-failure/loss evidence: transfer the bounded summary to the lane or mark aggregate coverage partial. Aggregate counting under contention must never pretend to be exact if updates could be lost; use a tested bounded accounting design and explicit unknown/partial coverage where exactness is unavailable.

The existing sink thread drains the general queue first, then at most 16 dirty optional slots per existing one-second publish cycle, with bounded yields. Wake only for newly dirty state, not every rejection. If no further offers arrive, retained dirty slots must still progress; schedule another bounded cycle until drained. This is diagnostic publication, never a SQL retry. Final close processes at most the retained 64 slots and includes their final counters. Busy/stale/unavailable state is visible; reports never trigger probes or a flush.

Keep the general queue's existing 1,024 capacity and 128 critical reserve. Keep existing persisted limits: 512 operation records, 32 KiB per record, 16 MiB document including overhead, 30-day/capacity retention. Optional upload records may occupy at most 64 of those records and only otherwise available capacity. They may replace optional records, but may not evict a non-upload operation to enter. When an ordinary operation needs room, optional rows are evicted first. Apply the same priority to file-bound trimming, restore/merge, report previews and archive budget selection. Preserve omission/eviction provenance and first-failure meaning. Classify the lane/source through code-owned validated metadata, never arbitrary caller-selected priority.

Reuse existing bounded publication, redaction, restore and ordinary/complete-report paths. Add narrowly versioned optional fields with missing/legacy values explicitly unknown. No new unlimited history file or SQL spool. Complete archives must include the same frozen snapshot/counters, truthful partial coverage, and correct final member hashes/sizes. Existing higher-priority components must retain their place. Disk failure can still lose unpersisted diagnostic evidence, including counters; no lossless promise is made.

This design isolates queue and retention priority; it cannot promise zero shared CPU/disk cost. Combined tests must reject a change that protects admission but degrades business responsiveness or existing report completeness.

## Alternatives and decision boundaries

| Alternative | Assessment |
| --- | --- |
| Two bounded writers with the shared lifecycle and isolated reporting above | Recommended minimal coherent design; retains most existing code and qualification work |
| One SQL/CSV execution worker | Reject: a slow sink serializes the other; sharing policy does not require sharing execution |
| Put both onto general logging/default executor or spawn tasks per offer | Reject: does not establish bounded isolated capacity/physical ownership; general logging uses an unbounded SimpleQueue |
| Add CSV execution to the existing diagnostic sink | Not selected: stalled CSV would delay diagnostic persistence; would need a stronger coupling justification |
| Dedicated subprocesses | Reserve only if valid cost/native closure evidence defeats threads; introduces startup, IPC, Windows supervision, credentials/custody and still cannot infer SQL cancellation from process exit |
| Durable SQL/file spool or guaranteed audit delivery | Different requirement: adds persistence/replay/acknowledgement design. Not necessary for agreed optional diagnostics, and not silently introduced |

There is no claim that every OS stall can finish within a hard deadline, that optional audit is complete after a crash, or that this closes incident recovery/P02–P05. If guaranteed audit delivery or bounded forced shutdown becomes a requirement, return with a changed scope rather than weakening required business safety.

## Affected areas, SQL and refactor review

| Area | Planned disposition |
| --- | --- |
| Existing A routes/services, fallback queue/staging, `utils.py` and `bot_helpers.py` | Preserve outcome/custody fixes and public results; use actual callers in combined tests |
| `services/optional_upload_transport.py` | Common close-request/wait and lifecycle/accounting contract; retain bounded admission |
| `services/download_log_service.py` | Once-only isolated startup, explicit handle custody, bounded failure/loss observations |
| `services/optional_import_audit_worker.py` | Reuse SQL binding/DAL rules; replace event amplification with coalesced observations; reconcile close accounting |
| Proposed `services/optional_upload_lifecycle.py`, `bot_instance.py` | Small lifecycle coordinator and wiring; no global executor rewrite |
| `services/operation_diagnostics.py`, `services/recovery_report.py`, `services/recovery_evidence_bundle.py` | Separate optional lane/priority, bounded counters and backward-compatible report/restore validation where required |
| `core/operation_evidence.py` | Extend only if a validated observation schema requires it; no change to business receipt authority |
| Updater transition and tests | Add reviewed successor for final immutable candidate; preserve historical pins |

SQL source: `C:/K98-bot-SQL-Server`, unchanged head `7e91989f619deb46836194c7e705b0a9eb2ebe11`. The six ImportAudit table/procedure hashes still match the native qualification receipt. StartBatch returns `ImportAuditBatchId` plus `CorrelationId`; RecordPhase uses `SetBatchStatus` optionally and writes within its audit transaction. Keep `SetBatchStatus=None` for independent observation phases. No schema, ProcConfig, index, business table, permissions or migration change is proposed. Retain dedicated trusted connection, autocommit verification, two-second login/statement settings and retained unconfirmed-close ownership. No connection was opened for this review; this is source-contract validation, not fresh native qualification.

Refactor triggers: duplicate lifecycle/error policy and diagnostic amplification are fix-now within P01.4. Shared generic helper/global importer extraction stays outside scope under the existing deferred records. No new SQL in commands/views. Optional memory state is deliberately non-authoritative and not replayed on restart; critical business persistence is unchanged. Retain existing failed prototypes/evidence privately; remove superseded runtime branches only once replacement and caller compatibility are proved, not during this design review.

Conditional references used: helper review, startup/shutdown/singleton ownership, diagnostics, Windows ownership/access contract, core engineering/testing/refactor/deferred standards. K98 architecture-scope, SQL-validation, test-selection and security-routing govern the packet. No promotion workflow was executed.

## Qualification plan and stop conditions

1. Freeze the measurement protocol before testing candidates. Retain E88 failures and new controls. Use identical fixed observation windows, randomized/alternating baseline/candidate order, warmup, raw samples and sample counts, both source-wakeup and loop-delivery timings, no-op/empty-worker controls, plus known loop and CPU stalls. Calibrate detection before interpreting results. Report timer overshoot separately; do not change system timer resolution or add artificial wakeups only to the candidate. The common observer's overhead must be measured. If controls fail, results are inconclusive, never green.
2. Keep the original budgets: offer p95 <=1 ms/p99 <=5 ms; at least 30 paired actual-workload repetitions per important path; <=2% median/<=5% p95 added elapsed and <=5 ms p95 responsiveness increase; cold setup plus sustained pressure. Specify the comparable responsiveness metric before qualification, retaining legacy timer results alongside it. Use actual downloader/fallback composition and six upload entry paths with offline business/Discord boundaries. Small control timings are not production throughput claims.
3. Test all four configurations locally: neither worker, file only, SQL only, both. Observe required business receipts/output/counts, CSV shape/count, audit calls/bindings, thread/session counts, queue/payload/context high water, diagnostic omissions, existing evidence priority, RSS and post-close retention. Test simultaneous ingress and reports with a near-capacity historical diagnostic projection. Measure combined caps, not just individual peaks.
4. Use barriers for file blocked, SQL blocked, both blocked, full/closed/oversize offers, startup construction/thread failure, close refusal, producer cancellation and repeated shutdown cancellation. Prove all admissions close before any join, other owner drains despite one refusal, no replacement/retry/synchronous fallback, and required staged input survives until its reader stops. Injected failures and real filesystem/driver failures must be distinguished.
5. Native qualification remains on uniquely named disposable databases at `localhost\K98DEV`, exact fixture-owned sessions only. File fixtures use a private local directory, not operational logs. Exercise permission/sharing errors, write/flush/close custody, login/statement/contention/disconnect, and five-second measured failure-settlement envelope. Retain adverse receipts and exact cleanup outcomes. No provider requests or committed-upload replay.
6. Saturate optional observation updates while inserting known critical business events. Assert optional traffic alone cannot consume their general queue slots or evict their retained records. Verify first failure/latest state, monotonic counts, skipped slots/partial markers and fair bounded progress. Restart from valid/partial/malformed/missing history; never recreate live audit handles. Validate actual ordinary report and complete ZIP, higher-priority components, final hashes/sizes and frozen continuation.
7. After corrections, run focused route, fallback and lifecycle tests, configured type/lint, architecture/deferred/security-routing, smoke/registration, log hygiene, and the final full suite after the updater successor is prepared. Existing source-pin failures are a release blocker, not unrelated failures to suppress. Perform a new Changes review for the final runtime diff; prior E89 review does not cover the proposed changes.

Test inventory to retain/extend: `tests/test_optional_import_audit_worker.py` (currently includes file-writer cases), `tests/test_graceful_shutdown.py`, `tests/test_bot_helpers_fallback_worker.py`, `tests/test_fallback_queue_route.py`, `tests/test_fallback_upload_staging_service.py`, `tests/test_fallback_import_service.py`, `tests/test_utils_live_queue.py`, `tests/test_live_queue_persistence.py`, all six entry-path tests from the original design, and `tests/test_p012a_evidence_contract.py`, `tests/test_p012a_recoverable_reports.py`, `tests/test_p013_complete_archive.py`. Add focused file/lifecycle/priority tests where the new contracts need separate coverage. Preserve all existing updater-transition fixtures.

## Delivery sequence and approval recommendation

Implement locally in reviewable steps: (1) measurement harness and shared lifecycle; (2) coalesced/priority-safe diagnostics and both adapters; (3) native plus combined qualification and any evidence-driven file correction; (4) final updater successor, full suite and Changes review. Both adoption gates stay off until the complete selected candidate meets the applicable gates. A successful component test alone cannot enable it.

| Delivery choice | When justified | Remaining obligations |
| --- | --- | --- |
| One deployment of complete P01.4 | Default recommendation; no urgent early-release need supplied | Full local qualification first, then separately authorized publication/promotion and natural-activity acceptance |
| Two deployments: A plus admission/custody, then complete optional workers | Early correctness value is needed while worker qualification continues; extract first patch with no dormant worker/report/lifecycle coupling | Verify each exact candidate and updater successor; second is additive to agreed contracts; P01.4 stays open after first |
| SQL first, CSV later | Only after final shared lifecycle/reporting and combined design have already been validated, and a named operational learning objective justifies it | Extra compatibility/rollback/qualification work; not recommended now and no promise of zero rework |

No production learning is currently required to resolve the known design gaps. Natural activity later validates rollout; it must not substitute for controlled failure qualification. Two PRs can still form one deployment, while two deployments each need their own exact reviewed updater and acceptance evidence.

**Recommended next decision:** approve implementing and qualifying the complete design above, including the explicit bounded observation lane and priority changes, with the original P01.4 scope retained and one deployment as the default. Publication/deployment remain separately held. Do not amend acceptance or defer CSV logging at this point.

## Review evidence and validation disposition

Private evidence root: `C:/discord_file_downloader/.codex_artifacts/p014-whole-design-20261105/`. Retained: `before.json`, `after.json`, source and both versions of timer controls, raw `timer-controls-20261105T125955.json` (observer sensitivity limitation) and `timer-controls-20261105T130052.json` (corrected controls), environment failure and subsequent run outputs. Existing E88/E89 receipts remain untouched.

This review changes only the design/status Markdown in the mirror; private experiments do not change shipped code/tests/config. All existing candidate file hashes matched E89 before the review. Final checks verify every existing non-Markdown candidate hash is unchanged, root/private/SQL repositories retain their prior heads/status, all six SQL definitions match, both source gates remain false and document links resolve.

Security routing: documented skip for this documentation/private offline-control increment; no deployed runtime, configuration, dependency, permission, network, SQL or persistence contract changed. The control script imports only the isolated writer modules and extracts the CSV helper, accepts no user input, and writes fixed private fixtures. The proposed runtime changes will require Changes review, Deep off, for the exact Bot candidate; no separate SQL diff exists. No new scan is launched for prose or to rediscover prior findings.

Runtime pytest/type/smoke/registration and native SQL reruns are skipped for this review because application/test/SQL sources are unchanged; previous 467-pass evidence is historical, not a test of this proposal. Run documentation architecture/deferred/security-routing, explicit-path test selection, links, whitespace and preservation checks. Validation results are retained in `document-validation.json` and `validation-run.txt` beside the private controls. Full implementation/combined qualification and release readiness remain outstanding.

Completed review checks: architecture (zero runtime files in this increment), deferred format (11 Markdown files), explicit-path test selection, security routing (zero errors/warnings), whitespace and preservation passed. All 384 relative links in the affected documents resolve. Both worker gates are unchanged and disabled. No new security scan, runtime regression run or native SQL qualification is claimed for this documentation increment.
