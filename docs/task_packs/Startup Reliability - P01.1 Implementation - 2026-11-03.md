# Startup reliability P01.1 — implementation and qualification

## Scope and status

Implements the approved first P01 slice, F08/F32: preserve startup results and
make shared timing/diagnostic failures independent of business execution.
Mirror base: `031af6e1c66d209f33c1db867ced44662189fef9`; its tree matches the
previously deployed private `b6ec4a0eeabd3d32d8fd98726ab8a6af5e6b829b`.
The implementation branch is `codex/p01-startup-outcomes`.

Recovery/deployment dependency assessment is pre-work **within P01.1**, before
any bot stop. The exact updater transition is part of this implementation.
F09/SQL 51421 contention diagnosis and correction remain P02. This change does
not repair or replay the failed pipeline, close its incidents, discard captures,
or establish whole-flow import/export acceptance.

## Result and ownership contract

- ProcConfig startup retains the original `(ok, report)` object. Its 180-second
  observation deadline no longer cancels it. An offload exception cannot select
  a fallback execution after entry.
- Startup reports distinguish observer deadline/cancellation, physical settlement,
  the returned result, and verification. A failed readback retains the original
  result and reports verification unavailable. An explicit false configuration
  result or unrecorded terminal attempt remains failed verification.
- `AttemptJournal` begin, phase and terminal writes remain required. No diagnostic
  wrapper surrounds those writes. The diagnostic reference is not an attempt,
  operation, SQL session, fence or release receipt.
- Owned thread work still runs once and drains through repeated cancellation.
  Its safe result facts survive cancellation of its observer. Raw return values,
  arbitrary report fields, exception messages and credentials are not persisted.
- Shared MGE board/roster owners and private interactions use safe clock/emission
  helpers. Local holder attribution observes the existing lock; it does not change
  lock order or grant ownership. SQL holder attribution remains unavailable/P02.
- Process-local context propagates through owned tasks and `asyncio.to_thread`.
  The legacy process payload remains unchanged: its returned attempt identity is
  retained, but the process-local diagnostic reference does not cross that hop.

## Optional diagnostic storage

Only the bot initializes the sink, after its first-ready gate. Watchdog and
maintenance logging setup cannot start another writer to the same projection.
Storage is `LOG_DIR/operation_observations/observations.json`, with a fixed
exclusive-create temporary sibling and atomic replacement. Links/reparse paths,
oversized files and malformed records are refused. This is an optional diagnostic
copy; it supplies no replay, repair, admission or completion authority.

Producers offer allowlisted primitives without waiting for a queue/registry lock
or doing filesystem, network, SQL or general-logger I/O. Limits are 256 active
diagnostic scopes, 1,024 queued envelopes with 128 reserved for material outcomes,
8 KiB per envelope, 32 transitions and 32 KiB per operation, 512 projections and
16 MiB per file. First failure and latest result have separate retention slots.
Completed, failure-free scopes expire after 30 days or capacity eviction;
unresolved first failures are retained until capacity refuses new observations.
Overflow, coalescing, eviction and sink failures remain visible. There is no
additional rotated stream in this slice; the bounded projection provides the
restart copy without duplicating records in the unbounded general log queue.

The recovery report reads a bounded in-memory summary (under 16 KiB), including
first failure, latest result/state and omitted-operation counts. It does not read
disk or run reconciliation while rendering. Prior process references and original
observation times remain visible after restart; they are not current liveness proof.

Business owners drain before sink closure. Accepted observations are drained and
entered I/O is joined. The logging atexit hook also closes/joins the sink; the
thread's daemon flag permits Python to reach that hook. A stuck native filesystem
call can delay shutdown and must not be reported as a completed drain. Forced
process termination can lose optional observations. It cannot weaken the required
domain or deployment receipts.

## Deployment dependencies and sequencing

1. Complete local review and Changes security review. Promote by the existing
   patch-based mirror-to-private workflow; deploy only private main.
2. Install the reviewed updater package before source deployment. The new
   `p011_startup_outcomes_v1` registry entry pins all 13 runtime members to their
   exact predecessor/successor hashes. Unknown peers, missing members and changed
   predecessor bytes are refused. Registry limits increase only to 57 entries and
   128 KiB. Existing transition entries and historical source assertions remain
   intact. No SQL migration or application grant/config change is introduced.
3. Before stopping the bot, obtain fresh installed updater/policy/source identity,
   process pair/incarnation, session, resource and stream evidence. Historical
   deployment receipts are comparison material, not a current readiness verdict.
4. Inspect the retained failed pipeline and configuration attempt/read preparation
   using existing supported recovery inspection. Preserve committed statistics
   and player captures, original input and original pipeline identity. Do not
   reupload, replay committed stages or infer success from released reservations.
5. Evaluate the **actual installed** startup/deployment contract over all registered
   resources. Retained quarantine is allowed only under its exact predecessor
   termination, owner/fence, stream containment/closure and session predicates.
   Incident count alone is not a deployment gate. Readiness cannot be inferred
   from a historical report, absent export job, diagnostic result or local test.
6. If the gate refuses, prepare the smallest supported recovery action and its
   exact current evidence for operator approval before any stop. A configuration
   closeout does not itself prove the original pipeline can resume: its recorded
   child/read association can still prevent continuation. Do not force-clear or
   make an unsupported association repair. Such a prerequisite remains attached
   to P01.1 release preparation; moving F09's root-cause fix into P01 is unnecessary.
7. Only after these checks and deployment authorization: use the protected updater
   to stop/drain, install the exact private source/policy, start once and verify
   the existing durable readiness receipts. Observe natural startup results and
   diagnostics. Optional evidence loss is not failed business work or permission
   to retry a provider mutation.

Rollback also uses the protected source/policy contract and current retained-work
checks. Older application code may ignore the optional diagnostic file. Required
configuration/domain receipt formats are unchanged. No deployment, restart,
provider request, SQL mutation or recovery action was performed for this package.

## Qualification record

Initial focused qualification: 119 passed. Updater/negative-boundary subset:
141 passed. Architecture boundaries, command registration and import smoke pass;
smoke uses the repository's test environment with dotenv disabled, never production
credentials. Final review and full-suite results are recorded below when complete.

Local Windows/Python 3.11.9 measurement used 30 matched, alternating pairs after six
warmups, with real owned 20 ms threads and a disk diagnostic sink. Median overhead
was 1.57%; p95 overhead 4.35%; enqueue p95 0.0104 ms and p99 0.0194 ms. The deliberate
2,000-offer burst dropped 1,104 observations, with zero sink failures. Added p95
heartbeat delay was 0.12 ms. Absolute heartbeat delay was about 14 ms in both arms
(Windows scheduling); these are synthetic local measurements, not production SLOs.

Tests cover late completion; result identity; mandatory receipt refusal; repeated
cancellation and physical drain; cancellation during verification; original exception
identity; clock/emitter/projection failures; saturation/reserved capacity; stalled
sink ownership; corrupt/oversized/unwritable persistence; restart first-failure and
result retention; bounded passive reporting; known local holder attribution; actual
startup wrapper selection; shared MGE/interaction callers; and exact updater peers.

F08/F32 closure is limited to these implemented boundaries. P01.2 issuer launch
diagnostics, P01.3 health presentation, P01.4 upload/audit, P01.5 calendar and P01.6
personal-read capacity remain separate approved-design slices. SQL holder/native
contention qualification and F09 remain P02; continuation convergence stays P03.
