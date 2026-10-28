# P1 MGE lifecycle: implementation and evidence

Date: 28 October 2026. Status: local implementation under validation; not deployed.

The operator approved the expanded MGE scope, reusable P1 foundations, a second
caller compatibility check and measured optimisation. The accepted monitoring/
import/export phase and R18 remain closed. No production operation, restart,
SQL installation or acceptance replay is part of this work.

## Baseline and implementation slices

Mirror baseline: `50c5e1a4a60a0438dca788298047f7d6dfb66e39` (includes the accepted
28 October closeout). Branch: `codex/p1-mge-lifecycle`. SQL definitions reviewed in
the separate authoritative SQL checkout; no SQL repository changes or migration.

| Slice | Changes | Reusable contribution |
|---|---|---|
| Persistence | Atomic signup/audit/withdraw cleanup, exact identities, current event checks, edit snapshot, operation receipt, explicit commit/rollback/unknown | Outcome vocabulary and writer/conflict template |
| Interaction | Early private acknowledgement, owned off-loop execution, current roles and form owner, repeat guard, commit separate from reply/DM/refresh, safe prepared-modal handoff | Compatible interaction helper and shared cancellation primitive |
| Presentation | Event-scoped board serialization, coalesced refresh requests, off-loop scheduler/board reads, durable board-send evidence, exact-ID recovery | Reusable refresh coordinator and failure scenarios |

Mutation persistence is deliberately MGE-specific. The global legacy SQL wrapper
is unchanged. No new domain policy, schema, global lock, retry framework or
automatic recovery command is introduced.

## Conflict and ownership map

| Writer / consumer | Authority and ordering | Remaining boundary |
|---|---|---|
| Signup create/edit/withdraw | Event lock -> exact signup -> awards where needed; required writes/audits in one transaction | Registry linkage is validated through the existing service; no registry policy rewrite |
| Open-mode switch | Existing event-first transaction, then award/signup deletion and audits | Historical receipts remain history |
| Publish/unpublish | Existing event-first DAL locks order with signup admission | Provider publication protocol remains its own service contract |
| Complete/reopen | Event-row update conflicts with held event lock | Existing completion semantics retained |
| Roster insertion | Event -> active exact signup -> award insert | Other roster operations retain existing outcome contracts |
| Board scheduler/manual sync | Event-scoped serialized read/render/edit | Process lock is not cross-process ownership |
| Background refresh callback | Coalesced owned request; dirty-during-run guarantees another pass | Authoritative state reread after restart; no persisted refresh queue |
| Board creation | Existing durable delivery journal before send, receipt before SQL ID save | Unknown send held; missing known message requires disposition |

## Second caller evidence

`services/event_delivery_service.py` now imports the extracted worker directly.
The old `services/legacy_export_snapshot_service.py:drain_thread` remains a
compatible wrapper for existing consumers. MGE SQL writes and event-journal writes
both prove that cancellation does not release the caller while the worker lives.
Context propagation and exception behaviour are tested through the compatibility
entry point. The event caller retains its own journal, admission and locks;
MGE retains its own SQL transaction and business policy.

MGE additionally consumes the existing durable delivery journal for board creation.
Restart fixtures verify exact-ID recovery after acknowledgement and refusal to
resend after a lost send acknowledgement or failed receipt write.

## Measurement method and initial results

`scripts/benchmark_mge_lifecycle.py` executes the real callback and board sync
with deterministic simulated SQL/service/Discord delays. No live database or
Discord call occurs. Raw measurements and source hashes are retained locally in
`.codex_artifacts/mge-*.json`; these are development evidence, not runtime receipts.

Initial 20-sample callback fixture, 50 ms blocking service:

| Metric | Before | After |
|---|---:|---:|
| Median acknowledgement | 50.35 ms | 0.007 ms |
| Median total callback | 50.37 ms | 51.12 ms |
| Median maximum event-loop lag | 49.46 ms | 15.38 ms |
| Mutation / reply / refresh requests per submission | 1 / 1 / 1 | 1 / 1 / 1 |

The improvement is responsiveness and ownership, not faster business SQL. Windows
timer scheduling remains visible in the lag measurement. Instrumented application
logs record callback acknowledgement/total duration and mutation outcome/duration.

Same-turn burst of 20 board-refresh requests, 50 ms simulated IO per pass:

| Metric | Before | After |
|---|---:|---:|
| Event reads / roster reads / Discord edits / ID writes | 20 / 20 / 20 / 20 | 1 / 1 / 1 / 1 |
| Fixture elapsed time | 560.02 ms | 81.25 ms |

The baseline excludes its old fixed 0.5-second dispatch delay. This is a burst
fixture, not a claim that all refresh traffic reduces by 95%. A separate test
injects another burst during execution and requires two passes with the latest
revision displayed. Source hashes distinguish uncommitted after-code from baseline.

Native SQL execution/plan measurements are not established by these fixtures.
The event audit lookup uses the existing EventId index and JSON receipt filtering;
no unmeasured index or SQL speedup claim is made. Before native execution, prepare
and approve a distinct disposable target under the local SQL development contract;
retained S11 databases and production are excluded.

## Validation

- Initial focused lifecycle/transaction/second-caller suite: 79 passed.
- Expanded MGE, interaction and legacy-worker suite: 457 passed, one dependency warning.
- Architecture, import smoke (isolated test configuration), command registration
  and security-routing gates passed during implementation.
- Full-suite/log-isolation and final Changes review results are recorded below
  when complete. The current document does not assert those gates have passed.

Fault injection covers required write/audit failure, confirmed rollback, rollback
failure, lost commit acknowledgement, exact receipt reconciliation, identity
mismatch, inactive/stale signup, locked event, unknown acknowledgement, current
form owner, repeated clicks, worker cancellation, reply failure, refresh ordering
and restart after uncertain board delivery. These are offline tests; native SQL
locking, live callbacks and operator visual acceptance remain distinct.

Security target: Changes review of this branch against the pinned mirror baseline,
Deep off. No repository-wide audit is selected. SQL source remains unchanged.

## Operator evidence and acceptance

For a new normal MGE signup/edit/withdraw, retain the operation reference, exact
event/governor/signup, response outcome and refreshed original board. Verify the
signup and mandatory audit/cleanup together. The service exposes the exact
read-only `read_operation_receipt(event_id, actor_discord_id, operation_id)` lookup.
Its absence or read failure is not retry authorization. Do not rerun the reported
historical attempt merely to obtain acceptance.

For board delivery uncertainty, retain the existing journal entry and destination.
An acknowledged channel/message ID supports exact recovery; `entered` does not.
Do not delete the journal, repost automatically, or classify elapsed time as failure.

Source review, local tests, native qualification, mirror PR, promotion, deployment
and operator acceptance remain separate. R03/R04/R13 natural/historical obligations,
R05/R08-R12 residual audits/policy, R14-R16 operations/performance and separate P0
R17 remain on the [stable ledger](P1%20Monitoring%20and%20Import%20Export%20Reliability%20-%20Closeout%20-%202026-10-28.md).

See the [shared adoption contract](../reference/p1-operation-lifecycle.md).
