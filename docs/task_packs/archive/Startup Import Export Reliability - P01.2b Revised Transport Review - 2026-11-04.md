# P01.2b revised transport review

Status: E75, 4 November 2026. Operator decision: close the proactive startup-observer/instrumentation proposal without deployment. Its theoretical coverage benefit does not justify the measured cost, complexity and risk. Preserve the bot and startup behavior; use existing evidence and simple best-effort collection. No replacement observer, shared-memory/native issuer helper or mandatory new exporter is queued. Future additions require a demonstrated incident/evidence gap and proportionate cost and safety justification. This is a scope decision, not delivery or passing qualification of P01.2b instrumentation. Earlier designs and E72-E74 results remain historical evidence.

## E75: operator decision - simplicity and startup safety take priority

The operator accepted E74's value/cost conclusion and explicitly rejected pursuing a theoretical requirement at additional cost or risk. Close proactive P01.2b startup instrumentation without deployment; do not treat it as waiting for optimisation or a different transport. The rejected pipe, external observer and shared-memory/native issuer helper are not active implementation tasks.

Use the already-delivered evidence collection and existing supported logs, receipts and reports. Capture or present additional available information on a best-effort basis where it helps an actual investigation. Missing early detail is an accepted coverage limitation, never proof of success or of no failure. Do not add startup dependencies, background workers, polling, retries, stream interception or stronger durability requirements solely to fill hypothetical gaps. Existing mandatory operational receipts and safety checks remain unchanged.

No standalone offline exporter is mandated or authorized for implementation by this decision. If an incident reveals a useful collection gap, first identify the precise question, existing evidence source and smallest safe on-demand improvement; justify its resource cost and failure behavior before adding infrastructure. No guarantee of complete evidence or zero resource cost is made.

The prior P01.2b feature-specific implementation manifest, B01-B09 delivery gates and theoretical early-coverage promises are historical conditional designs, not outstanding blockers for a feature the operator declined. This does not waive the established non-interference, custody, redaction or validation obligations for any future actual change. P01.1/P01.2a acceptance and the outstanding issue-driven P01.3-P01.6/P02-P05 and incident-recovery work retain their owners; no incidents are cleared and no business result is inferred.

Preserve E72-E74 and the private inert fixtures as rejected-design evidence; do not install or rerun them automatically. No runtime, SQL, task, policy, service, production or deployment change accompanies this decision. The documentation/archive carry-forward obligation survives cancellation of the instrumentation feature and belongs in the next appropriate authorized reliability PR/promotion; this creates no PR or publication authorization.

This update is documentation only. Validate links, current status, archive preservation and the documentation gates. Runtime tests, smoke imports, command registration and a Changes security scan are skipped because no runtime, imports, configuration, permissions, dependencies or executable fixtures changed. This decision adds no optimisation backlog item: the proposal is declined, not deferred for tuning.

## Historical E74: smaller external observer tested; integration stopped on cost

The user agreed to establish value with the smallest isolated prototype, keeping the issuer, imports and standard streams unchanged. This authorizes the private feasibility screen only. It holds back E73's mailbox, emitter and in-process native helper; it does not authorize installation, runtime integration or production changes. No additional operator evidence was needed.

The fixture launches one inert Python child through a fresh Windows PowerShell 5.1.26100.9711 wrapper. A prebuilt .NET observer inherits only an exact child handle with SYNCHRONIZE and PROCESS_QUERY_LIMITED_INFORMATION through an explicit handle list. It waits on native process exit, with no idle polling, and writes one bounded result. The wrapper synchronously loads the same prebuilt .NET assembly for native handle duplication and observer creation after the one child launch; that setup is included in timing. The held-back in-process helper refers to the issuer: this prototype still has native interop in the wrapper and does not prove wrapper setup immune to failure or stalls. A separate no-child path records the fixture's missing-interpreter refusal without changing exit 4. There is no SQL, provider, bot import, application state, automatic retry or diagnostic incident creation. The harness owns only its private process jobs and uses kill-on-close for fixture cleanup.

**Value demonstrated:** exact attempt/PID/creation/exit evidence, including immediate exit, plus a missing-interpreter phase. Healthy native exit records distinguish process termination from business success. **Value not demonstrated:** root cause/traceback, gate/bootstrap stage detail, resolution of the six historical incidents, offline/report usability or improved recovery decisions. Existing journal and pipeline evidence remains necessary. Observer or publication failure can leave no new evidence; absence must mean unavailable/unknown coverage.

Fourteen functional scenarios passed: baseline/candidate workload and immediate exit; denied terminate access; missing observer; observer crash and deliberate observer termination; failed publication path and delayed publication; baseline/candidate missing interpreter; baseline/candidate 1 MiB stderr. Intended child exit remained 37 (idle control 0), wrapper outcome remained 0 or missing-interpreter 4, and one workload entry was counted per launched-child case. The immediate baseline's already-exited process was not independently queried; the candidate's retained native handle observed exit 37. All 255 valid-run case jobs physically settled. Largest result was 267 bytes. The write-failure case is an existing directory at the target file path, not a simulation of every ACL or disk failure. The publication delay is two seconds, not a proof of arbitrary stuck-I/O cancellation.

**Cost decision: failed.** The first cold attachment added 3443.3 ms against the pre-registered maximum of 500 ms. The original recorded setup was 3443.7 ms; the same-run baseline instrumentation cost was subtracted. Do not discard this first-use result because later launches are warmer. The exact source of this delay has not been attributed. After this failure was identified, the already-running screen completed the idle sample and 120 alternating matched pairs to quantify cost, without integration or changing limits.

| Repeated-screen metric | Measured | Pre-set maximum | Result |
| --- | --- | --- | --- |
| added_setup_ms_p95 | 496.4365 | 50 | fail |
| added_setup_ms_p99 | 501.5679 | 100 | fail |
| added_setup_ms_max | 503.6472 | 500 | fail |
| added_spawn_return_ms_p95 | 3.9995 | 10 | pass |
| added_spawn_return_ms_p99 | 13.0367 | 25 | pass |
| work_ratio_median | 1.0082 | 1.02 | pass |
| work_p95_ratio | 0.9677 | 1.05 | pass |
| idle_cpu_seconds | 0.0000 | 0.125 | pass |
| idle_peak_working_set_mib | 14.0859 | 32 | pass |
| idle_private_bytes_mib | 12.1953 | 32 | pass |

Idle observation lasted 125.00 seconds; the observer was still waiting on the live idle child at the sample boundary. Idle CPU/memory success cannot override the cold failure. Fresh wrapper processes include per-process assembly loading, while the host filesystem/security/runtime caches can warm. This is an inert steady-work comparison: the harness releases workload after attachment so it can verify exact native identity and fault timing. It therefore does not qualify concurrent startup contention, real bot speed, loop lag or readiness. Start-Process return latency is not application readiness. A 120-pair screening sample does not prove a population p99 or zero regressions.

**Security and lifetime limits:** reduced inherited rights are not a token/process sandbox. A same-principal observer could seek additional handles; no claim of containment against arbitrary malicious or faulty observer behavior is made. The local trusted fixture accepts private paths and contains explicit fault modes; it is not a deployable protected helper. Actual elevated custody, same-SID restrictions, malformed handles/inputs, physical-owner admission/caps, scheduled-task/logoff/job semantics, updater zero-instance behavior, venv redirector chains and full installed package acceptance remain unqualified. A stuck writer must retain its admission slot; a timeout is not proof of worker exit.

Two earlier runs are invalid fixtures, preserved separately: the venv executable was a redirector and its child PID differed from the launched PID; after selecting the underlying interpreter, an exact job-process-count assumption incorrectly included Windows console hosts. The final fixture counts per-PID workload-entry files, verifies native identity where retained, and uses job active-process counts for physical settlement. These corrections do not relax outcome, cost or resource limits.

Private evidence: `p012b-external-observer-validation-20261104/plan.json`, source/build files, and `run-bede20d5-0478-4ca7-b3d5-13dd1fc9e7d9/receipt.json` plus `decision.json`, under the existing private artifact root. Hashes bind the plan, executable and executed sources; all earlier results remain. E72's pipe evidence remains untouched.

**Recommendation:** do not integrate this prototype or resume the more intrusive E73 helper. Prefer a revised offline-only collection scope using already-existing authoritative evidence if it supplies enough operator value. It would add no continuous observer or new startup emission, but cannot reconstruct early events that were never recorded; on-demand collection still has bounded resource costs. If exact early native-exit evidence remains indispensable, a separately reviewed smaller launch mechanism must first beat this cold-cost gate and satisfy the missing lifetime/security gates. No further implementation of either alternative is authorized by this result alone.

Validation scope: native inert experiments and documentation checks; no full bot, SQL, installed acceptance, P01.2a combined report test or product security certification. Security routing is a documented skip for the Git-backed prose-only change and private undeployed qualification fixtures, with the fixture code reviewed for process ownership, handle rights, bounded outputs and absence of production reachability. Any future integrated launch/helper/file-handling patch requires a Changes security review, Deep off, against its exact diff. Generic smoke imports/command registration and runtime pytest are skipped because application imports, registrations and runtime files are unchanged. No PR, merge or deployment is claimed.

## Retained E73 recommendation (superseded for implementation)

Everything below retains the earlier E73 proposal and review record. E74 above governs the current decision; these historical recommendations do not authorize implementing the mailbox or helper.


Keep the issuer's existing standard streams unchanged. Replace stderr interception with bounded, code-owned diagnostic records written to fixed-size shared memory. A separately owned observer reads those records and the exact retained process handle, then publishes the existing proposed safe online/offline projection. It has no role in application execution, restarts, settlement or release admission.

The proposed mailbox is memory backed by the Windows paging file, not a diagnostic file mapped into the issuer. Readers do not own capacity or acknowledge consumption. An absent, stopped or dead observer therefore does not close the producer's stream or prevent a producer from updating its own mapping. This removes the particular consumer dependency demonstrated by E72. It is a design argument requiring native qualification, not a claim that the replacement already passes.

**Approval must explicitly replace the earlier bounded-stderr requirement with bounded structured early-failure evidence.** P01.2b will not intercept arbitrary stderr, persist tracebacks, change Python's exception hook, redirect to NUL, change standard-stream buffering, or guarantee the full message from failures before trusted diagnostic initialization. Native attempt/process evidence and allowlisted gate/wrapper/issuer milestones remain required. This is a visible coverage trade-off, not an unchanged implementation detail.

No Windows service, global tracing session, recovery engine, SQL schema, provider call, alternative launcher or automatic observer restart is proposed.

## Evidence and alternatives reviewed

E72 proved that losing the sole pipe reader changed the inert Python child's exit from 37 to 120. Healthy-reader and no-capture controls preserved 37. Current issuer source imports standard modules, parses arguments, loads `run_export_authority.py` and completes `bootstrap` before trusted application imports. Moving application diagnostic imports before that boundary would change the trust contract. The supplied task has an elevated interactive principal, a logon trigger and termination settings; native task/job behavior still needs qualification.

| Option | Assessment |
| --- | --- |
| Another blocking pipe reader or larger pipe | Rejected. A spare unread endpoint can turn reader loss into a full-buffer wait; more capacity does not remove dependence on a reader. |
| Nonblocking/overlapped redirected stderr | Rejected as a drop-in replacement. Partial writes, unavailable capacity, disconnect errors and flush behavior still reach the ordinary Python stream. Cancellation of outstanding I/O is not proof of settlement. |
| Redirect stderr to a file | Rejected for this slice. Child writes then depend on storage, quotas and file errors; raw content may be persisted before redaction. File-backed mapping does not remove that dependency. |
| Wrapper around Python / replacement exception hook | Rejected here. It changes the entrypoint or error/exit handling and still cannot capture interpreter failures before that wrapper runs without another transport. |
| ETW structured events | Viable alternative, not selected. It provides OS event transport and drops events when buffers are unavailable, but requires provider/session custody, session lifetime, loss attribution and collection integration. An EventWrite success with no recording session is not retained evidence. It also needs explicit preservation of first-failure milestones when ordinary buffers wrap. |
| Fixed pagefile-backed mailbox plus process observer | Recommended. Small per-attempt ownership, no reader acknowledgement, explicit loss/overwrite, private custody and reusable safe report/export path. Costs include a native protocol/helper, optional initialization risk and a volatile-to-durable publication gap. |

The Win32 distinctions above are supported by Microsoft's [pipe wait-mode documentation](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-type-read-and-wait-modes), [EventWrite contract](https://learn.microsoft.com/en-us/windows/win32/api/evntprov/nf-evntprov-eventwrite), and [shared-memory lifetime documentation](https://learn.microsoft.com/en-us/windows/win32/memory/sharing-files-and-memory). Selecting the mailbox is this review's engineering recommendation.

## Revised launch and transport design

1. **Trusted gate and optional setup.** Preserve every original principal, custody, source, policy and executable check. After the diagnostic helper itself is authenticated, prepare the bounded memory objects and optional observer. Failure of a diagnostic-only component disables that channel; it never skips a mandatory launch check or turns an otherwise permitted start into an extra launch. Earlier failures before trusted capture exists remain explicit coverage gaps. No synchronous diagnostic disk write is added to a business thread.
2. **Separate producer ownership.** Use two unnamed pagefile-backed mappings per attempt: one for the single-threaded gate/wrapper, one for the issuer. The gate initializes fixed headers before handoff. Each producer owns only its writable mapping. The observer receives read-only mapping handles; its own process observations and publisher state remain separate. Unnamed objects avoid caller-chosen names and object-name collisions. Only the exact trusted participants receive handles through a restricted inheritance/duplication list; role descendants must receive none.
3. **One issuer launch.** Preserve the current command, flags, working directory, environment policy and standard-stream behavior. Retain the original process handle at creation; duplicate only query/synchronize rights to the observer. No terminate, suspend, job-assignment or application-command interface is exposed to the observer. An unknown creation/handoff result never triggers a second start. A diagnostic handle failure after creation records incomplete coverage without altering the child.
4. **Post-bootstrap Python detail.** Initialize the issuer emitter only after the existing protected `bootstrap` succeeds. Keep the invocation and its trust roots unchanged. Record fixed stage start/result/failure codes around imports, policy parsing, token/mutex/history checks, SQL installation/reconciliation, publication and drain boundaries as available after that initialization. Observe existing exceptions/returns and preserve their original control flow, including SystemExit/cancellation. Do not evaluate exception strings, locals or traceback source text. The emitter has no business-success authority.
5. **Write without reader participation.** A producer writes an at-most-1-KiB fixed record, publishes its sequence using a qualified native atomic protocol, and returns. It never waits for a reader, a receipt, free queue space, an export or a disk write. Each mapping has one writer; unexpected concurrent/reentrant emission is refused rather than queued or spin-waited. Preserve the first failure and key milestones in reserved slots; overwrite only ordinary recent-event slots and count it. Saturation never grows storage or changes the business result.
6. **Independent observation/publication.** The observer reads consistent snapshots with a bounded number of attempts; a torn/busy record is unavailable, never a fabricated event. It observes creation/exit through the retained handle even if the interpreter never emits an event. A separate bounded publisher writes protected safe generations. Publisher stall cannot block the producer or native process observer. Entered I/O remains physically owned and accounted for; no timeout is called settlement.
7. **Settlement without a dependency on diagnostics.** Producer mappings live until their own handles/views close; observer loss cannot invalidate another process's mapping. No producer joins the observer, flushes its diagnostic channel at exit, restarts it, or waits for persistence. On normal issuer exit the observer takes a final bounded snapshot and records native exit if it still holds the handle. On observer loss, its last durable state remains incomplete. On process/OS loss before publication, unsaved memory can be lost.

Microsoft documents that [mapping objects remain while participants retain handles](https://learn.microsoft.com/en-us/windows/win32/memory/sharing-files-and-memory) and that a [retained process object supports termination observation](https://learn.microsoft.com/en-us/windows/win32/procthread/terminating-a-process). Neither mechanism makes optional evidence durable.

## What non-interference means, and what remains a gate

The guarantee to qualify is **no new dependency on diagnostic reader/publisher progress, no new standard-stream failure, no duplicate launch and unchanged original result/control flow under diagnostic component failure**. It is not a claim of zero overhead or immunity to machine-wide failure. Page faults, OS scheduling and initialization can take time; a shared mapping is not a hard-real-time primitive.

Optional initialization is a specific unresolved implementation gate, not exempt from the contract. Loading a helper, creating/mapping handles, validating its custody or initializing a Python module can fail or stall. Establish the exact pre-initialization/disable path before integration; do not hide a blocking import or file operation behind a nominal timeout or detached worker. If the chosen implementation introduces an unbounded diagnostic dependency at initialization, it fails feasibility and returns for review. Mandatory existing source/custody checks remain mandatory.

Use a fixed native protocol with correct alignment and release/acquire publication; a Python byte copy, checksum or volatile declaration alone is not proof of atomic cross-process publication. Reader validation must not write to a read-only view. There must be no unbounded CAS retry loop, cross-process mutex, reader-owned cursor or reused handle accepted on number alone. Microsoft's [interlocked access documentation](https://learn.microsoft.com/en-us/windows/win32/sync/interlocked-variable-access) describes atomic operations and ordering across shared memory; the exact native implementation still needs review and tests.

A malformed record or diagnostic failure yields an enum/counter or no-op, preserving the original application exception/return. Do not catch and suppress business failures. Existing stderr problems can still occur through the unchanged environment; the claim is that P01.2b adds no observer dependency to that stream.

## Coverage and trade-offs

All retained rows distinguish expected binding, observed identity, asserted producer stage, native exit, publication quality and unavailable reason. A stage-start record proves entry, not completion. An unobserved completion does not establish failure at that stage.

| Failure or boundary | Evidence retained when the relevant channel/publisher is available | Explicit limitation |
| --- | --- | --- |
| Task cannot invoke PowerShell, gate cannot parse, or helper admission cannot run | Existing task/OS evidence if separately supplied; no claimed P01.2b producer record | Cannot guarantee a self-record from code that never executed |
| Missing Python; gate policy/hash/custody refusal; wrapper readiness failure | Attempt, known actor/source binding, exact allowlisted gate/wrapper stage and original exit/reason | No arbitrary exception text; capture unavailable if trusted diagnostic setup itself did not succeed |
| Windows refuses process creation | Attempt, spawn-entered/native error, wrapper result, no successful process-creation observation | Missing result or lost handoff is unknown, not permission to retry |
| Interpreter/DLL initialization failure, top-level syntax/standard-import failure, argument parsing or protected bootstrap failure | Bound launch identity, actual creation/exit when observed, last gate stage, issuer events unavailable | No promise of Python exception type, failing line or traceback; exit alone does not identify the cause |
| Failure after trusted emitter initialization but before any journal | Specific code-owned issuer phase, first failure type/code, counters, native exit if observed | Unrecognized exception types become a fixed fallback; no secrets, raw messages or stack locals |
| Abrupt issuer death | Last consistent milestones and actual native exit if the observer survives | No fabricated final event; last stage may have completed without its event being retained |
| Publisher slow, disk full or safe-generation replacement interrupted | Memory milestones and counters may remain available to the live observer; previous valid durable generation survives | Acknowledgement/persistence is not required for business progress; final unsaved detail may be lost |
| Observer dies before/after spawn | Existing durable prefix remains; producer continues without it | Later issuer exit may be unobserved. No automatic restart, backfill or recovery action |
| Machine/power loss | Previously committed safe generations | No guarantee for the last unpublished memory interval; no manufactured crash-time exit code |
| Journal appears before/after native exit observation | Exact PID/creation/policy/publication correlation; preserved first failure and independent journal facts | Journal validation does not establish provider delivery or erase prior diagnostic failure |

An always-complete durable trace under collector/storage/power failure would require a different reliability contract, such as blocking on persistence or an additional retained capture authority. Neither is smuggled into this optional diagnostic slice. Useful early evidence is preserved; arbitrary pre-initialization stderr detail and guaranteed final-event durability are intentionally not promised.

## Proposed bounds and persistence semantics

These replace the original pipe/classifier bounds; unchanged online/offline/session retention limits still apply.

| Resource | Bound / behavior |
| --- | --- |
| Shared memory | Two 64-KiB mappings per attempt; at most four admitted observers/attempt mappings, 512 KiB total shared allocation. Admission must account for existing physical owners, including stuck publishers; refuse additional capture when full. |
| Per-mapping layout | 4-KiB immutable header; 32 x 1-KiB recent slots; eight x 2-KiB reserved milestone slots; 4-KiB counters; 8-KiB reserved/versioned space. Header includes schema, attempt, producer role and expected bindings. |
| Event and milestone | Fixed integer/enum fields plus bounded identifiers/digests. Event <=1 KiB; existing 8-KiB envelope is only an outer projection cap. First-failure slot is never replaced by later success. Counts saturate visibly. |
| Producer work | One bounded emission attempt, no retries or dynamic queue allocation; no read acknowledgement, filesystem/network/SQL work or required notification signal in the hot path. |
| Observer polling | At most 10 polls/second while active; at most two bounded consistency attempts per slot per poll. No polling callback in the issuer. Native exit wait stays independent from publishing. |
| Publisher | Coalesce <=1 ordinary write/second with reserved milestone opportunities and existing bounded queue. Stalled I/O remains owned. No fresh publisher for the same attempt to bypass a stuck one. |
| Exit tail | Target observer settlement <=5 seconds after issuer exit, with incomplete persistence reported honestly. No EOF or pipe-drain requirement and no child kill policy. |
| Safe retained attempt | Existing 32-KiB projection cap, 128-attempt history and 30-day completed retention. Replace stderr text with structured event/coverage summary. |
| Existing delivery caps | Preserve 512-KiB online early component, 4-KiB ordinary summary, 8-MiB attachment, 17-MiB pending session, frozen retry semantics and total 64-MiB diagnostics namespace limits from the original packet. |

The first gate entry may exist only in memory until publication. Exports must separately show observation time, snapshot time, durable publication time and coverage/loss; an old file must never appear to describe the current attempt. If setup failed before any record exists, label absence as unknown coverage rather than counting a nonexistent successful attempt.

## Custody, schema and delivery changes

- Create mapping security descriptors at creation. SYSTEM/Administrators only for private objects; do not grant the ordinary application SID private mapping access merely because the elevated user shares that SID. Restrict handles by role, use non-executable views, and prove no mapping/nonce/handle reaches application children. See [mapping access rights](https://learn.microsoft.com/en-us/windows/win32/memory/file-mapping-security-and-access-rights).
- The bot still reads only a complete, protected safe projection. Offline export still operates without Python or Discord and cannot choose arbitrary privileged paths. No raw stderr is acquired or newly stored by P01.2b.
- Treat mappings as optional volatile diagnostics, never restart/replay state. Publisher files retain the original admin-only/private versus application-read-only/safe split. Existing mandatory incarnation/deployment/SQL receipts remain authoritative.
- Proposed new schema fields: `transport=pagefile_mailbox_v1`, `stderr_capture=not_performed`, `issuer_detail_start=after_trusted_bootstrap`, emitter availability, retained/overwritten/refused/inconsistent counts, native-observer availability and publication quality. Existing deployed V1/V2 schemas remain unchanged; these unreleased launch schemas can be finalized together.
- Preserve the original installation/package inventory discipline and all 61 updater transitions. Record exact revised helper bytes, architecture, schema and compile provenance in the installed manifest. Do not dynamically compile or download a native helper on production startup.

## Revised proposed files and build boundary

Keep the original gate/wrapper/issuer, online/offline consumers, updater/package/transition and test manifest, with these explicit changes:

| File / area | Revised responsibility |
| --- | --- |
| `scripts/K98-StartupEvidence.ps1` and `scripts/K98-StartupEvidenceNative.cs` | Optional setup, mapping handles, process observation and publisher ownership. Remove pipe reader, stderr classifier and EOF lifecycle. |
| New `core/startup_launch_events.py` | Trusted post-bootstrap Python emitter adapter. Fixed stages/enums only; no logging-system import or business-state mutation. |
| Proposed new `scripts/native/K98StartupMailbox.cpp` / `.h`, `scripts/build_k98_startup_mailbox.ps1` | Small shared native ABI for fixed record emission and consistent snapshot reads, with bounded validation and explicit atomic ordering. Build-only MSVC/Windows SDK dependency; no new production compiler. Exact ABI/build feasibility is an initial gate. |
| Protected generated native helper | Install under the immutable diagnostic tool package, outside the application source-only tree. Independently pin/hash and review it; never weaken `bootstrap`'s source-only inventory to admit arbitrary native application modules. No packaged binary is produced by this review. |
| Native/Python tests | Replace pipe-success expectations with unchanged-stream, mailbox-lifetime, torn-record, saturation, emitter-init, missing-helper and native-exit cases. Preserve E72 as rejected-design evidence, not a passing regression. |

The native ABI is proposed to avoid pretending ordinary Python buffer copies are a complete synchronization protocol. Its loader and initialization risk are material: they must be tested first, and helper authentication must not create an unbounded diagnostic dependency in the issuer. The helper must have a trivial DLL entry/detach path with no disk/network work, thread joins, waits or shutdown publication. Incorrect pointer/size/ABI handling could itself affect the issuer; bounds, architecture, lifetime and fault handling are acceptance requirements, not assumed properties of native code. If a smaller implementation using already reviewed native primitives can prove the same protocol, document the exact manifest change before choosing it; no silent new loader or pre-bootstrap import is allowed.

No SQL implementation is proposed. The existing targeted recovery data is sufficient for this design; it does not replace action-time recovery/ownership checks. No additional production collection is requested now.

## Qualification and decision before resuming

The next authorized implementation phase should begin with a replacement feasibility harness, not report integration. It must prove:

1. **B01/B02, D01-D05:** current launcher semantics and one creation; native PID/FILETIME/exit for immediate exit and pre-emitter failure. Inject missing interpreter, invalid custody/policy, top-level syntax/import and bootstrap failures. Assert the coverage table's distinctions instead of demanding a nonexistent traceback.
2. **B03/A14:** repeat healthy/absent/terminated/paused-observer controls with unchanged standard streams, including during emission, first failure and final exit. Full/overwritten slots, failed publisher, disk stall and malformed data must not alter original result. The child must not need a reader to proceed.
3. **Initialization feasibility:** absent/wrong-hash helper, map/handle allocation failure, import/load failure and stalled optional setup must not create a new unbounded dependency, fallback start or swallowed business exception. Measure setup separately; stop again if this cannot be proved with the proposed trust/build boundary.
4. **B04/B06:** producer death mid-slot, repeated updates, reader races and sequence overflow; observer read-only enforcement, wrong identity/handle/header, same-SID unelevated access, inheritance leaks, task termination/logoff and exact old/new installed packages. Test real Desktop PowerShell 5.1, not only parsing.
5. **B05/B07:** offline restart/continuation/retry, missing/torn/stale projection and incomplete publication; ordinary/ZIP quality agreement; unchanged P01.2a Q01-Q12/R1-R6, eight startup references and physical collection ownership.
6. **B08/B09:** retain the two actual 125-second combined report cases; add sustained structured-event saturation while ordinary stderr remains on its baseline route. Preserve matched-launch, RSS, CPU, loop-lag and report-cost gates; complete exact Changes reviews and later authorized installed acceptance.

Initial targets remain added setup/handoff p95 <=250 ms, p99 <=500 ms; a two-second optional observation budget is not permission to abandon active setup I/O or assume a worker exited. Retain >=100 matched launches and the existing report/resource thresholds. No finite timing samples prove immunity to all OS stalls; the structural dependency review and fault tests are both required.

**Recommendation for approval:** accept the mailbox/native-observer direction and the explicit replacement of arbitrary stderr capture with structured early-failure evidence, then resume isolated feasibility first. This review does not authorize implementing that revision; the E72 stop remains until the user approves it. No deployment or production change is requested.

## Historical E73 review validation boundary

This is a documentation/design change. Source and Win32 contracts were inspected; no replacement code, binary, native experiment or application test was run. Documentation links/hygiene, architecture/deferred/security-routing validators and explicit-path test selection apply. Runtime pytest/import/registration and Changes security scan are skipped for this prose-only revision; an implemented privileged helper/loader/IPC diff requires a Bot Changes review, Deep off, followed by separate private promotion review. The complete documentation carry-forward set now contains 26 paths, including this review.
