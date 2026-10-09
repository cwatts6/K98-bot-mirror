# S11 contention and recovery: first implementation slice

## Scope and evidence

User authorized the phase on 2026-10-08, including implementation, reviewed PRs and
production promotion, with no automatic merge. Step 1 was source/evidence review.
Baseline mirror main: `6e4a0042df5054dee20c90ca514d2e456cfd62ca`.
Production baseline is operator-evidenced private main `8bf2faf5`; ordinary graceful
restart passed. Intake/recovery remain false. This work does not settle the held
`c9831a9d-3031-4954-9da9-79815406ec0b` preparation or replay a producer.

The retained 11:14:29.719 UTC event proves error 51400, `Export admission busy`.
The previous `_mutex` mapped every negative application-lock return to that error.
The event contains no SQL session/client/stack actions. Timeout, cancellation,
deadlock, competing holder and execution boundary therefore remain unattributed.
Repeated reads of that historical XML cannot provide those missing fields.

Microsoft documents return codes 0/1 as success, -1 as timeout, -2 as cancellation,
-3 as deadlock victim and -999 as validation/other call failure:
[sp_getapplock](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-getapplock-transact-sql).
Only -1 is eligible for the new bounded retry. A generic SQLSTATE or 51400 is not.

Native isolated reproduction on local K98DEV established:

- The old wrapper raises identical 51400 before synthetic execution and after a
  committed synthetic row but before checkpointing. One row remains committed in
  the latter case; the error alone cannot authorize replay.
- Confirmed rollback leaves no synthetic row.
- A barrier-controlled incompatible application lock succeeds after release
  (observed 92 ms in the initial bounded-wait experiment).
- The actual old preparation transition statement produces 11502 for `@P2` in
  `sp_describe_undeclared_parameters`. Explicit `nvarchar(max)` casting fixes
  description. This is a reproducible source defect, not attribution of the four
  historical uncorrelated events or proof of their execution outcome.

The new isolated database is `S11_Contention_Disposable_20261008_d39a2afb` on
`9SX2VF4\K98DEV`. It contains synthetic evidence only and is retained. No production
read, producer, import, provider call, migration, old recovery or restart ran.
Raw evidence and the initial reproducer are in the local S11 artifact directory.

## SQL and source trace

Authoritative definitions were read from `C:\K98-bot-SQL-Server`, including
`ExportPreparation`, `ExportPreparationResource`, `SP_Stats_for_Upload` and
`UPDATE_ALL2`. `GenerationJson` is `nvarchar(max)`; the cast does not alter stored
state or introduce a migration. Existing owner/fence/version predicates remain.

`verify_producer_cursor` authorizes on its own coordination transaction.
`_authorize` acquires account first, then claim resources and row locks. The
session guard uses a different, session-owned legacy-output lock. The producer
uses another connection. One bot can therefore contend with its own concurrent
health/configuration/producer tasks; no particular historical holder is proven.

The stats procedure supports an ambient transaction; the Python caller currently
commits before recording its preparation checkpoint. UPDATE_ALL2 owns multiple
phases and also checkpoints separately. KVK ingest/recompute can append the
checkpoint on their existing producer cursor. These contracts are not equivalent:
an external-cursor checkpoint acknowledgement is pending the caller's commit.
This slice does not silently convert any producer transaction contract.

## Architecture and behavior

- DAL emits an attributed refusal containing original application-lock result,
  SQL session, transaction state/count and hashed resource identity. It preserves
  the driver exception as the cause. Logs omit driver prose and parameter data.
- `services/export_contention.py` owns classification, rollback/release proof and
  bounded coordination retry. Existing transaction code supplies commit-unknown
  semantics. A successful rollback **and** connection close must occur before
  retry eligibility. A cleanup failure or unknown commit is never retried.
- Dedicated authorization, transition, uncertainty persistence, capture and
  unstarted withdrawal transactions may retry a timeout. They never invoke a
  producer/provider. External producer transactions are explicitly excluded.
- Retry starts share one monotonic one-second budget (the existing dedicated
  connection's lock budget), at most eight attempts, with 25 ms doubling delays
  capped at 250 ms. No SQL lock timeout is widened. Existing SQL connection/query
  timeouts still bound in-flight I/O; the retry budget does not interrupt I/O.
- Admission uses its existing 60-second outer wait and the same durable ticket;
  it has no nested retry loop. Non-waiting health admission makes one attempt.
  Refusal detail is rate-limited to attempts 1, 31 and 61, plus wait/result summaries.
- Writer diagnostics distinguish authorization, producer entry/return, local
  commit request/acknowledgement, durable checkpoint and snapshot capture. A log
  is never accepted as durable commit proof. The stats caller has the explicit
  producer/commit instrumentation; broader producer diagnostics remain follow-up.
- Only the audited stats caller opts into explicit before-side-effects evidence.
  An exhausted first authorization timeout can close that live guard and mark
  its exact writing claim unavailable through existing guarded transition/CAS.
  Previously authorized work, other errors and historical claims remain held.
- The original writer/completion exception survives failed uncertainty or close
  cleanup. Secondary failures receive separate sanitized diagnostics.

Commands remain unchanged. No new SQL schema, permissions, configuration, provider
behavior or activation flags are introduced. Existing diagnostic UUID/counter
validation and transaction ownership helpers are reused. No suitable existing
helper provided attributed lock classification plus confirmed-release retry.

## Validation and review

Risk-based tests cover timeout recovery/exhaustion, cancellation/deadlock exclusion,
rollback/close failure, commit acknowledgement loss, external transactions, health
probe behavior, producer non-execution, explicit pre-execution release, prior
authorization, log redaction and original-error preservation. Native tests use
two connections/barriers and the actual parameterized transition statement.

The native test requires both `K98_CONTENTION_SQL=LOCAL_SYNTHETIC_ONLY` and the
exact isolated `K98_CONTENTION_DATABASE`; ordinary CI skips it. It never creates
or runs a real producer. Synthetic commit receipts are retained, not cleared.

Security routing: **Changes**, Deep off, bot baseline `6e4a0042` to this slice's
final review head. SQL repository has no delta: separate no-change skip. The
review must cover classification, bounded replay, ownership and log redaction.
Full pytest/log-noise, architecture/deferred/test-selector/routing, smoke imports,
registration and lint are required before production promotion. Final results
and exact scan/PR identities will be recorded in the handover.

## Remaining phase work and deployment

This first PR is not full automatic-recovery or go-live acceptance. Remaining:
durable receipt-based restart reconciliation/recapture; additional producer
boundary coverage; native cancellation/lock-order and real contract tests;
purpose-specific fresh held-operation evidence and business reconciliation;
controlled import/provider acceptance and later KVK16 checkpoints.

Absent durable outcome proof, the existing uncertain operation stays held. The
new live pre-execution evidence is deliberately not reconstructed after restart.
No replay based on elapsed time, missing process, missing generation or empty
spool metadata is allowed. Broader recovery must not rerun a proven committed
producer and requires its own reviewed slice.

Promote the validated mirror delta using the patch-based private PR workflow.
No merge is automatic. This slice needs no SQL migration or configuration change.
After operator merges, prepare the exact source/seed/readiness packet and use
`Deploy-K98Release.ps1` with `/ops graceful_restart`. Its first real release must
succeed before generic-runner live acceptance is claimed. Do not reuse successful
initial cutover, migration or recovery scripts.
