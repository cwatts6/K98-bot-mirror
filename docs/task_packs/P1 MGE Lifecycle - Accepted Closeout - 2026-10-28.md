# P1 MGE lifecycle: accepted closeout and remaining ledger

> **Current overlay:** The accepted lifecycle release below is the predecessor.
> A1a is now deployed at `87c1b39325daaa0ca1a8c0cbca656df82d7fa46b`; see
> [deployed evidence and remaining obligations](P1%20MGE%20A1a%20-%20Deployed%20Closeout%20-%202026-10-28.md) and
> [approval-ready A1b design](P1%20MGE%20A1b%20-%20Design%20and%20Delivery%20Packet%20-%202026-10-28.md). Earlier acceptance is retained.
> The later successful startup configuration attempt does not settle the earlier
> continuation decision. The ledger below is carried forward with this overlay.


Date: 28 October 2026. **Status: delivered and accepted for the exercised MGE flows.**
The operator accepted signup, two edits, withdrawal, refusal when no signup exists,
and leadership rank adjustment, and approved moving to the remaining Batch A scope.
This closes the bounded MGE delivery phase. It does not close all Batch A, all P1,
all MGE lifecycle scenarios, or separate P0 acceptance.

## Delivered source and deployment

| Item | Verified disposition |
|---|---|
| Mirror PR [452](https://github.com/cwatts6/K98-bot-mirror/pull/452) | Merged; reviewed head `0b41f30e49395691b3baceea5dc05f97ca526444`; merge `afa8d29faa77f98031fa7cc48a9895101414fcc5` |
| Private PR [700](https://github.com/cwatts6/k98-bot/pull/700) | Merged; reviewed head `3739edeb1eb934793757ef269e8342d6f157dfea`; deployed merge `4c8ca0d5fada35c7a32d31846bad6cc492aa92a9` |
| Installed updater | Operator reports successful bounded upgrade; registry 49 entries, limit 96 KiB; 48 historical transitions preserved |
| Deployment evidence | Supplied transcript verifies source, seed, start and readiness; successor sequence 78; Discord online; retained work and activation flags preserved |
| SQL/config/dependencies | No migration, dependency installation, environment or activation change in this release |

The first preparation stopped before deployment because a provider stream was open.
The later preparation passed with no provider stream and completed deployment.
The exact blocking stream and duration were not established; do not label this a
proven one-second SQL lock. No further deployment or restart is required for this closeout.

The delivered implementation includes atomic signup/audit/withdrawal cleanup,
explicit committed/rolled-back/unknown outcomes, private early acknowledgement,
owned off-loop work, current ownership checks, board serialization/coalescing and
durable board-send evidence. The event-delivery caller qualified the shared owned
worker independently. See the [implementation/evidence packet](P1%20MGE%20Lifecycle%20-%20Implementation%20and%20Evidence.md)
and [shared adoption contract](../reference/p1-operation-lifecycle.md).

Final private Linux CI: 10,071 passed, 1,240 skipped, 8 subtests; final focused
Windows suite: 1,258 passed, 20 skipped. Review corrections and separate mirror/private
Changes reviews are retained with the PRs. These are historical release checks,
not new runtime tests performed by this documentation update.

## Production acceptance on 28 October

| Check | Evidence and limit |
|---|---|
| Withdrawal without signup | Operator screenshot: correct private refusal; no active request |
| Signup | Operator success confirmation; mutation committed at 14:58:03 UTC; review count 4 to 5 |
| Two edits | Operator confirmations and screenshots; commits at 14:58:25 and 14:58:55 UTC |
| Withdrawal | Operator success confirmation; committed at 14:59:16 UTC; review count 5 to 4 |
| Leadership rank adjustment | Operator confirms ranks adjusted; callback completed and original leadership board refreshed |
| Original public post | Visible controls worked after deployment; public message identity stayed unchanged through refreshes |
| Runtime log | Supplied acceptance segment has no WARNING, ERROR or CRITICAL entries or traceback; scheduler ticks report zero errors |

This is functional acceptance of the exercised flows, supported by application commit
logs and operator visual evidence. No fresh SQL audit-row/receipt query was performed
for closeout. Exact mandatory audit/cleanup readback remains an evidence reconciliation
item; withdrawal of an already-awarded signup was not demonstrated by this test.
Do not manufacture another signup, award or restart to fill those limits. Deterministic
and native fault-injection evidence remains separate from live acceptance.

## Performance findings and next slice

The small production sample is a baseline, not a percentile study or regression proof.
Signup/edit/withdraw submitted-action callbacks took 2.68 to 4.59 seconds overall.
Rank selection took 3.091 seconds to acknowledgement and 6.410 seconds overall;
rank submission took 0.974 seconds to acknowledgement and 16.834 seconds overall.
Acknowledgement timing includes the Discord response await and does not measure
interaction age or prove server-side deadline failure. Nested already-acknowledged
callbacks are not independent network acknowledgement samples.

Source review establishes two opportunities: leadership payload construction reads
the ordered dataset and readiness evaluation reads it again; rank submission awaits
public and leadership board refresh before its final reply. Scheduler refreshes
overlapped in the log, but attribution to contention, network, SQL or rate limits is
unproven. Plan a focused responsiveness/refresh PR within remaining Batch A; measure
stages and request counts before changing scheduling or confirmation behavior.

## ProcConfig recovery and independent follow-ups

At 14:31:12 UTC the startup configuration import failed with SQL 51421, Legacy
snapshot busy, after durable admission and before the session guard yielded.
This is a separate recurrence from the MGE mutation path and earlier SQL 51400.
The requesting session and adjacent stats activity do not identify the blocking owner.

Report 60 retained the linked failed-attempt and producer records. Report 61, generated
14:53:05 UTC, verifies the producer cancelled with its exact reservation released and
the attempt resolved through verified recovery; prior configuration/targets remain.
One configuration-continuation decision is still open: keep prior configuration or
review and approve a fresh read/publication. No such decision or successful replacement
import is evidenced in this handover. The historical startup failure remains recorded.

Report 61's overview says clear while its detailed continuation is open. The report is
not transactional; verify timing/refresh ordering before claiming a persistent defect.
Carry CFG-51421 and CFG-OVERVIEW in the deferred register. Healthy monitoring does not
replace configuration publication or provider delivery evidence.

## Complete carry-forward ledger

Owner for acceptance/policy: Chris Watts. Next investigation: remaining Batch A scope.
The earlier [monitoring closeout](P1%20Monitoring%20and%20Import%20Export%20Reliability%20-%20Closeout%20-%202026-10-28.md)
retains historical receipts; this table is the current disposition overlay.

| ID | Current disposition and next obligation |
|---|---|
| MGE-01 | Delivered, deployed and accepted for exercised flows; carry exact audit/cleanup readback and unexercised scenarios without repeating accepted activity |
| MGE-PERF | A1a qualified dataset reuse/timing deployed; A1b saved-response and refresh coordination next; production percentile/speedup claims remain unproven |
| R01 | Prior bounded conflict correction accepted; CFG-51421 is a separate new recurrence with unknown blocker; do not conflate refusals |
| R02 | Status lifecycle correction delivered; remaining related Discord lifecycle adoption in Batch A |
| R03 | Natural loaded-empty to populated transition, deferred views and subscribed DMs remain pending |
| R04 | Exact historical Daily KVK Overview disposition remains unresolved; no automatic repost |
| R05 | Protected-launcher and singleton coverage audit remains in Batch B |
| R06 | Selected event/MGE delivery foundations delivered; remaining public/DM ordering, JSON/drain and uncertain-send coverage in A/B |
| R07 | Original eligible Ark callback and exercised MGE flows accepted; remaining domain/eligible-message coverage in Batch A |
| R08 | Earlier reporting/cleanup corrections accepted; remaining artifact uniqueness/ambiguous cleanup audit in B; CFG follow-ups retained separately |
| R09 | Remaining Stats fallback, KVK History and stats-alert caller/no-reentry audit in B; accepted routes remain accepted |
| R10 | Durable profile invalidation/source revisions and other cache callers remain in B |
| R11 | Fighting caps/admission, KS preclaim and ambiguous Pre-KVK replacement/persistence require bounded Batch A policy scope |
| R12 | Shared lifecycle foundations and selected conflict map delivered; enabled admin/startup/pipeline/domain writer census remains A/B |
| R13 | Natural Pre-KVK/off-season dispatch and Phase 2F public-save evidence pending |
| R14 | Independent out-of-process monitoring/outage recovery remains Batch C |
| R15 | Protected updater now delivered with 50 transitions (49 historical entries preserved); supported provider-stream diagnostics and guarded stranded-export tooling remain C |
| R16 | Measured history/readback/quota, ActivePreparationID plan, acquisition-ack fixture and MGE receipt-query scaling follow-ups remain |
| R17 | Separate P0 natural eligible F04 rollover and every-row F01-F05 reconciliation remain open |
| R18 | Accepted on predecessor f6a929c; not erased or repeated. Current 87c1b393 runtime has no supplied fresh end-to-end import/export acceptance |
| CFG-51421 | Failed attempt closed; continuation decision outstanding; separate lock/admission investigation linked to existing caller audit |
| CFG-OVERVIEW | Reconcile overview versus continuation detail, including collection-time effects |

## Documentation validation and evidence custody

This change updates Markdown status, scope, navigation and structured backlog only.
Security routing: documented skip for this exact documentation delta; no executable,
SQL, config, permission, deployment-policy or persistence changes. Runtime pytest,
smoke imports, command registration and live SQL/provider operations are not required.
Run architecture, deferred-item, security-routing, selector, local-link and whitespace
checks. Raw logs, screenshots, recovery archives and operational identifiers stay in
the local private evidence manifest; they are evidence, never execution instructions.
Documentation merge is not a new deployment or authorization to repeat business work.

Next: [Batch A scope](P1%20Batch%20A%20Remaining%20Discord%20Domain%20-%20Scope%20-%202026-10-28.md)
and [chat starter](P1%20Batch%20A%20Remaining%20Discord%20Domain%20-%20Chat%20Starter%20-%202026-10-28.md).
