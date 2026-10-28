# P1 operation lifecycle contract

> **Approved local A1b implementation:** The revised scope is implemented locally and undergoing final validation. See the [implementation and evidence record](../task_packs/P1%20MGE%20A1b%20-%20Implementation%20and%20Validation%20-%202026-10-28.md). Publication, merge and deployment remain separate. Earlier scope-only approval wording below is historical.

> **Current status - 28 October 2026, A1a deployed:** Mirror PR 454 and private
> PR 702 are merged; private `87c1b39325daaa0ca1a8c0cbca656df82d7fa46b` is deployed
> and Discord online. Signup/edit/withdraw are verified on this runtime. A1a qualified
> datasets and timing are delivered; the A1b design packet is prepared for approval.
> Rank confirmation still waits for board refresh. Report 62 queue closure, the older
> configuration decision and separate Discord lag remain follow-ups. Exact audit/cleanup,
> unexercised cases, fresh import/export, natural acceptance and P0 remain explicit.
> See [deployed closeout](../task_packs/P1%20MGE%20A1a%20-%20Deployed%20Closeout%20-%202026-10-28.md) and [A1b design packet](../task_packs/P1%20MGE%20A1b%20-%20Design%20and%20Delivery%20Packet%20-%202026-10-28.md).
> Earlier dated status and next-action text is historical where superseded.
> This documentation update requires no deployment, restart, SQL apply or repeat import.

MGE is the first integrated consumer. This contract also supports the remaining
Discord/domain, execution/persistence and operational P1 families. It does not
close their individual implementation or acceptance obligations.

## Separate evidence dimensions

| Dimension | Evidence / ownership |
|---|---|
| Admission | Current actor/roles, exact target, current domain policy, one acknowledged interaction |
| Execution | One owned worker; cancellation retains ownership until the worker settles |
| Mutation | `not_entered`, `committed`, `rolled_back`, or `unknown`; determined by persistence evidence |
| Presentation | Reply, DM and board refresh have independent outcomes; their failure cannot undo a confirmed commit |
| Recovery | Exact durable receipt and target identity; absence, elapsed time or a successful monitor do not authorize replay |

`core/owned_work.py` extracts the existing drain primitive. The legacy export
entry point remains compatible. Event delivery and MGE exercise the same primitive
with cancellation, repeated cancellation, context propagation and exceptions.
It neither retries work nor supplies database idempotency. A stuck underlying
driver remains outstanding work; cancellation is not proof it stopped.

`private_operation` acknowledges a private thinking response, retains the callback
through cancellation and rejects overlapping same-view actions. Final service and
DAL checks remain authoritative. View memory is only a UI guard. Modal openers
that need IO prepare data first and offer a fresh, owner-bound Open form button;
already prepared modal openers retain their immediate initial-response path.

## Persistence and conflicts

For each adopted caller, record: action/identity; admission owner; competing
writers; lock order; transaction boundary; required audit; commit evidence;
unknown-outcome disposition; response owner; refresh owner; shutdown/restart path.

MGE signup/create/edit/withdraw use event-first locking and one transaction for
the signup, required signup audit and withdrawal award deletion/audit. Identity
includes event, governor and signup. Edit forms compare their original snapshot
under the lock. Event mode, publish/completion status, close time and variant are
checked again at the final boundary. Roster insertion participates in the same
event-first order and rejects inactive/mismatched signups.

The existing signup audit JSON stores an operation ID, request fingerprint and
previous signup snapshot. A matching committed audit positively reconciles that
operation; reuse with different input is rejected. A connection failure before
entry is different from lost commit acknowledgement. A successful rollback after
a commit exception does not downgrade `unknown` to `rolled_back`.

The audit receipt is not an attempt ledger. An absent audit does not prove that
an earlier request never entered or authorize automatic replay. Existing legacy
records do not acquire new evidence retroactively.

## Refresh and message identity

`CoalescedWork` applies only to replaceable refresh work. Same-key requests before
execution share a pass; a request arriving during a pass requires another pass.
Event-scoped serialization covers scheduler and direct board syncs. Every pass
rereads authoritative state. Refresh failures are observed, and shutdown drains
owned work before closing the client. This coordination is process-local.

MGE board creation reuses the existing event-delivery journal. Durable entry
precedes Discord send. An acknowledged message whose SQL ID save failed can be
recovered by its exact recorded channel/message ID. Entered/unknown sends remain
held across restart. Missing known messages require explicit disposition; they
are not automatically replaced. This is evidence retention, not a retry queue.

Do not generalize a refresh key across operations with different notification,
target or publication semantics. Do not use refresh coalescing for business writes.

## Adoption and verification checklist

1. Map one real second caller and show both matching and differing contracts.
2. Preserve current permissions and policy; avoid copying MGE-specific SQL or locks.
3. Test acknowledgement failure, non-entry, commit/reply separation, cancellation,
   repeated clicks, stale state, competing writers and restart evidence separately.
4. Retain deterministic gates/events for concurrency tests; avoid sleep-based races.
5. Measure acknowledgement latency, loop responsiveness, operation duration,
   refresh pass/read/edit counts and outstanding ownership. Label simulated IO.
6. Qualify native locking, query plans and provider latency separately; do not
   extrapolate fixture timing to production.
7. Record exact source, validation, remaining uncertainty and operator acceptance.

For WS1/WS2 this supplies outcome and worker contracts; for WS3/WS4 it supplies
owned refresh and durable delivery evidence; for WS5/WS6 it supplies a writer-map
template and final-admission pattern. Each domain still needs its own authority,
policy and persistence review. External monitoring remains separate.

## Concrete remaining-scope adoption

| Stable ledger item | Foundation to carry forward | Still required in that area |
|---|---|---|
| R02 / R07 Discord and domain callbacks | `private_operation`, prepared forms, commit/reply separation and real callback tests | Trace each response owner and preserve domain eligibility; no claim that historical 10015/10062 has one cause |
| R06 remaining public/DM persistence | `drain_awaitable` / `drain_thread`, existing delivery journal, exact-ID recovery tests | Inventory child tasks, storage boundaries and destination identity; preserve natural acceptance |
| R08 / R09 legacy execution paths | Explicit mutation outcomes, fault-injection matrix, no-reentry evidence | Map the actual legacy wrapper and resources before adoption; keep accepted coordinated routes closed |
| R10 cache callers | Owned refresh, dirty-during-run test, source revision template | Durable invalidation/revision design remains unimplemented |
| R11 domain policy / persistence | Final-admission and writer-conflict checklist | Agree policy before changing fighting caps, preclaim or legacy replacement |
| R12 writer census | MGE writer map and two-caller cancellation evidence | Enumerate every enabled writer and prove participation in the chosen owner/lock |
| R15 / R16 delivery and performance | Exact source evidence, repeatable benchmark, explicit uncertainty | Protected updater release admission and actual SQL/provider measurements |

`mge/mge_roster_execution.py` owns the whole legacy roster service operation per
event across both roster UIs. This prevents newly off-loop read/modify/write calls
from racing; other events can progress independently. Every async roster mutation
adapter must participate. It is neither a cross-process lock nor a substitute for
atomic database writes. The signup writer supplies its own SQL transaction; legacy
roster audit grouping retains the separately captured adoption work.

R03/R04/R13 natural and historical disposition, R05 process singleton, R14 external
monitoring, P0 R17 and closed R18 keep their existing status. No ledger item is
closed merely because a shared helper is available.

See [MGE implementation and evidence](../task_packs/P1%20MGE%20Lifecycle%20-%20Implementation%20and%20Evidence.md).

## A1a qualified datasets and measurement framework

The [A1b design packet](../task_packs/P1%20MGE%20A1b%20-%20Design%20and%20Delivery%20Packet%20-%202026-10-28.md)
proposes strict public/identity/award reads, truthful legacy partial-result handling,
reply-independent owned refresh and existing-message restart reconciliation.
The final framework review also requires publication/refresh identity ownership:
an older refresh must not overwrite a newer or intentionally cleared board pointer.
Conditional ID writes and lifecycle-qualified journal recovery are proposed;
separate coalescing keys alone do not establish this invariant.
These are proposed additions, not delivered behavior. The present calendar window
does not guarantee recovery of every persisted board, and a legacy roster Boolean
does not supply the signup transaction's durable outcome contract.

The deployed A1a implementation distinguishes successful `loaded_empty` and `loaded`
leadership preparations from `unavailable` reads and `incomplete` preparation.
The adopted strict DAL callers propagate read failure; legacy callers retain their
existing list contract. A failed preparation is never a valid empty roster.
Leadership board refresh retains its existing message and identity on failure;
fresh publication readiness blocks before publication. Private leadership actions
report that data could not be verified. Successful empty-data policy is unchanged.

Preparation is not read-only: existing automatic placement can insert awards. Its
reentrant event thread owner is shared with `run_roster_mutation`, including both
roster UIs. Lock order is async roster owner (where applicable), then thread owner,
then existing DAL transactions. Board owner precedes thread owner on board refresh;
no thread owner is held across Discord IO or an await. Keep all synchronous callers
off the event loop. This does not serialize signup SQL writers or other processes.
An unconfirmed insert or failed readback stops the preparation without replay;
previous writes are not represented as rolled back. Cross-writer atomicity remains R12.

One prepared snapshot supplies both leadership rendering and displayed readiness.
It is never cached across actions or reused as publication authority. Publication
still reloads at its own boundary; whole-publication atomicity is not established.
Public signup rendering is outside this strict-dataset adoption and retains its
legacy failed-read contract; qualify it before any A1b refresh-policy change.

`core/operation_timing.py` adds random local correlation references. Context flows
through owned tasks and workers. Stages record interaction age, acknowledgement,
worker queue/execution, roster owner wait, dataset/DAL reads, board ownership and
Discord fetch/edit, private response and complete callback. Times are **inclusive**:
they may overlap and must not be summed. `completed` means the timed call returned,
not that a domain write committed or delivery succeeded. Nested acknowledgements
are `already_acknowledged`, never another network-ack sample. Acknowledgement
failure remains non-entry. No token, payload, connection string or exception text
is added to these structured timing records. Existing logs retain their contracts.

### Required adoption record for each follow-on slice

| Field | Required evidence |
|---|---|
| Target / authority | Exact actor, domain identity, current eligibility and final admission owner |
| Data | Valid empty/populated, unavailable and incomplete states; reader and hidden writer census |
| Execution | Real entrypoints, competing writers, lock order, child draining and restart limits |
| Mutation | Confirmed commit/rollback, non-entry and unknown outcomes kept distinct; exact reconciliation receipt |
| Presentation | Response, DM and each public destination independently settled; message IDs retained |
| Failure tests | Failed ack/read, partial write/readback, stale state, repeated click/cancel, overlapping caller, failed reply/refresh after commit |
| Measurement | Source/fixture hashes, same harness and workload, repetitions, counts, p50/p95 and loop delay; simulated IO explicitly labelled |
| Closure | Local tests/review, release readiness, deployment, runtime readiness and natural acceptance separately recorded |

Demonstrate one real second caller before changing shared helpers. Signup and rank
callbacks exercise A1a timing; both roster UIs, board preparation and publication
exercise the owner contract. Do not adopt MGE's event key, placement policy or
notification semantics automatically in Ark, voting or calendar.

See [A1a implementation and validation](../task_packs/P1%20MGE%20A1a%20-%20Implementation%20and%20Validation%20-%202026-10-28.md)
for the concrete caller matrix, repeatable measurements and remaining gates.
