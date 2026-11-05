> **Archived 5 November 2026.** Delivered P01.1 implementation evidence. Its original release holds are historical; see [P01.1 closeout](Startup%20Import%20Export%20Reliability%20-%20P01.1%20Closeout%20-%202026-11-03.md).

# Startup reliability P01.1 — implementation and qualification

## Scope and status

Implements the approved first P01 slice, F08/F32: preserve startup results and
make shared timing/diagnostic failures independent of business execution.
Mirror base: `031af6e1c66d209f33c1db867ced44662189fef9`; its tree matches the
previously deployed private `b6ec4a0eeabd3d32d8fd98726ab8a6af5e6b829b`.
The implementation branch is `codex/p01-startup-outcomes`; final runtime source is
`80b05dfc257f70ca6bf4957b8cd62cdaaa975dac`. Implementation and local qualification
are complete. Promotion, installed-host qualification and deployment remain separate.

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
Overflow, coalescing, eviction, lost diagnostic contexts and sink failures remain
visible. Failed UUID allocation or full context capacity cannot prevent business
entry. Prior counters are separate from live counters, so loading a projection cannot
overwrite new losses; totals saturate within the restart reader contract. There is no
additional rotated stream in this slice; the bounded projection provides the
restart copy without duplicating records in the unbounded general log queue.

The recovery report reads a bounded in-memory summary (under 16 KiB), including
first failure, latest result/state and omitted-operation counts. It does not read
disk or run reconciliation while rendering. Optional observations are omitted with
an explicit marker if they would prevent the first otherwise-fitting incident from
fitting the attachment budget. Prior process references and original
observation times remain visible after restart; they are not current liveness proof.

The sink batches queued observations for up to one second before publishing. This
wait occurs only on the writer thread, without holding the queue or business locks.
Memory summaries and disk observations can lag by that interval plus entered I/O.
Closing interrupts the batching delay. This avoids rewriting the growing projection
on each producer wake and reduces Python-runtime and disk contention.

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

Final qualification is bound to the source revisions below; overlapping batches
are not added together as a unique test total.

| Gate | Result and limit |
|---|---|
| Frozen full suite at `f364440` | **11,047 passed, 1,113 skipped, 8 subtests passed**, one Google Python-version advisory; 1,257.78 seconds. Operational-log isolation passed. |
| Final runtime `80b05df` | **217 focused tests passed**, including the subsequent counter and batching changes; operational-log isolation passed. The full suite predates these narrow sink follow-ups. |
| Shared callers | 33 direct imports across 28 source files: startup, coalesced/owned work, private interactions, MGE review/roster/board/publication/recovery/scheduling and views, event delivery, export snapshot and recovery health. Existing caller suites plus dedicated injected-failure tests were used. |
| Deterministic gates | Architecture boundaries, deferred-item validation, explicit-path test selection, security-routing validation, command registration, import smoke, Ruff, Black/whitespace/merge-marker/size checks and committed-range secret scan pass. |
| Configured type check | Zero errors and 28 dependency-resolution warnings. This is the repository's configured limited scope, not whole-repository type coverage. |
| Updater | Exact Git predecessor/successor classification has no blockers and requires the updater upgrade. All 13 successor hashes match actual Git blobs; predecessor hashes and historical transitions are retained. Generated installer/upgrade parse under Windows PowerShell 5.1. Built, not installed. |
| SQL/live operations | No new SQL query, schema, procedure, grant or config contract. Source contracts were checked against the SQL repository during design. Native SQL contention and installed-process/custody acceptance are not claimed by this slice. |

Three complete **Changes** reviews cover the implementation and its final follow-ups;
Deep scan was off, no candidates/findings remain:

| Scan | Immutable range | Source items |
|---|---|---|
| `5f89dbd3-6a6d-4df1-b700-f7349204fb23` | `031af6e..7fb6317` | 15/15 |
| `33412e62-2619-47ff-ba3a-8cbd9d30b1f1` | `7fb6317..f364440` | 5/5 |
| `3c4c96b1-9151-4cee-8ca3-a67cce135721` | `f364440..80b05df` | 2/2 |

The supplied source-backed threat model was preserved across follow-ups. These reviews
do not attest live ACLs, installed updater identity, actual SQL holder or deployment
readiness. The final documentation-only receipt adds no executable behavior and has
a documented Changes-scan skip; no Codebase or Deep scan is a routine gate.

Tests cover late completion; result identity; mandatory receipt refusal; repeated
cancellation and physical drain; cancellation during verification; original exception
identity; clock/emitter/UUID/projection failures; saturation/reserved capacity; stalled
sink ownership; corrupt/oversized/unwritable persistence; restart first-failure and
result retention; early counter losses during restore; bounded passive reporting and
attachment budgets; known local holder attribution; actual startup wrapper selection;
shared MGE/interaction/delivery callers; and exact updater peers. A deterministic
60-second batching-delay test proves close interrupts the delay and flushes accepted
observations once; it does not wait out that delay.

Final local Windows/Python 3.11.9 cost qualification uses **200 matched alternating
sink-off/sink-on pairs after six warmups**, with identical owned 20 ms threads and
context in both arms. Median elapsed was 21.2259/21.2659 ms (**0.19% overhead**);
p95 was 22.6959/22.4164 ms (-1.23%, ordinary sampling variation). Added p95 heartbeat
delay was **0.21 ms**. Enqueue p95/p99 were **0.0022/0.0079 ms**. Both arms invoked
business work exactly 206 times including warmups and retained the original result.
The normal workload had zero dropped observations and zero sink failures; a separate
2,000-offer overload deliberately dropped 1,104 observations. Projection size was
583,104 bytes; final close/drain took 18.34 ms.

The sustained pre-batching check exceeded the provisional cost targets as the
projection grew (12.92% median/30.15% p95 at 200 pairs). That evidence is retained;
it motivated the bounded writer batching above. Two post-batching 200-pair checks
met the provisional local targets. These measurements isolate sink cost; they do
not measure all instrumentation against old code, every caller workload or production
SLOs. Absolute Windows heartbeat delay was about 14 ms in both arms. Broader native
observer/producer cost and contention qualification remains with P02/P05.

F08/F32 closure is limited to these implemented boundaries. P01.2 issuer launch
diagnostics, P01.3 health presentation, P01.4 upload/audit, P01.5 calendar and P01.6
personal-read capacity remain separate approved-design slices. SQL holder/native
contention qualification and F09 remain P02; continuation convergence stays P03.

## PR review follow-up before deployment

The late review of mirror #480/private #721 identified two small diagnostic
improvements within P01.1. Restored events must contain reference, stage, state and
timestamp before any retained record is mutated; malformed optional history can no
longer poison subsequent publication. Private callback timing now records interrupted
for errors and cancellation while preserving the exception and child-drain contract.
The exact P01.1 updater successor hashes are refreshed for these two runtime files.
This updates the uninstalled candidate; earlier updater packages are superseded.

Focused qualification: 79 tests passed, including four incomplete-history restore
cases and callback error/cancellation disposition; operational logs remained unchanged.
The traceback review suggestion was rejected with executable evidence: tb_next moves
toward the original raise site. The proposed concurrent initialization race is excluded
by the sole synchronous caller after the locked, one-time startup claim. Neither
requires a runtime change. Final private CI and deployment receipts remain separate.
