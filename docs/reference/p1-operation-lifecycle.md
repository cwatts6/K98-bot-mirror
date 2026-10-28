# P1 operation lifecycle contract

> **Current status - 28 October 2026, MGE closeout:** The bounded MGE phase is
> delivered and accepted for exercised signup/edit/withdrawal and leadership flows
> on private `4c8ca0d5fada35c7a32d31846bad6cc492aa92a9`. Next: remaining Batch A
> Discord/domain scope, starting with measured MGE responsiveness/refresh work.
> ProcConfig cancellation is verified; its continuation choice and separate reliability
> follow-ups remain open. Exact audit/cleanup readback and unexercised MGE cases remain
> explicit. Full P1, natural acceptance and P0 rollover are not closed.
> See [accepted closeout and complete ledger](../task_packs/P1%20MGE%20Lifecycle%20-%20Accepted%20Closeout%20-%202026-10-28.md),
> [next scope](../task_packs/P1%20Batch%20A%20Remaining%20Discord%20Domain%20-%20Scope%20-%202026-10-28.md) and [chat starter](../task_packs/P1%20Batch%20A%20Remaining%20Discord%20Domain%20-%20Chat%20Starter%20-%202026-10-28.md).
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
