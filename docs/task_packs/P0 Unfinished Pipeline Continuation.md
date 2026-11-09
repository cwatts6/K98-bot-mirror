# P0 unfinished pipeline continuation

## Scope review and current evidence

Implementation is authorised after scope review. The verified starting source is
mirror `8b986c3c`, the snapshot of private `6c8f7bad` (PR #673). Deployment of that
private revision is operator-attested. No merge, deployment, production repair,
import replay or publication check is part of this development work.

The retained KVK16 publication result is confirmed at 715 seconds / 132 requests,
compared with 816.7 seconds / 170 requests. Saved timing evidence attributes
130.032 seconds to retained history, 403.546 to provider readback, 148.735 to sealed
history, 29.562 to sealed replay and 0.719 to final origin verification. Readback
includes 258.027 seconds of budget waiting. Detail intervals overlap and must not
be summed. Larger timing changes are captured in the deferred optimisation register.
Do not repeat this successful production check.

Startup KVK16 cache completion is verified by the operator: 415 rows, source scan
29 September. Tracked-view restoration remains unconfirmed in P1.

## Durable stage map

| Stage | Authoritative evidence | Continuation boundary |
| --- | --- | --- |
| Input preparation/archive | Exact immutable filename and `KS4_ImportFileClaim`/archive evidence | Missing files require collection and identity verification. Never substitute a different input or repeat a committed import. |
| Import / UPDATE_ALL2 Phase A | Exact `StatsImportExecution` preparation, owner/fence and scan receipt committed with import | `import_committed`, `partial` and `completed` preserve the import. Released reservations do not prove import or pipeline completion. |
| UPDATE_ALL2 reporting | Final `completed` receipt and counter; intermediate audit result rows are not durable stage receipts | Phase B can commit a prefix before the final transaction. Historical `partial` cannot authorise replay of all reports. Additional transactional stage receipts or a separately confirmed superseding report contract are required. |
| Player report SQL | Typed atomic producer request plus same-transaction generation checkpoint | Existing recovery captures a committed result; verified rollback requires a new explicit report decision. |
| Player/name/target caches | Exact cache payload/provenance and existing cache-continuation evidence where available | SQL completion or export admission does not certify cache freshness. Do not generalise the accepted startup result to other invocations. |
| Post-import maintenance | Existing outcome/telemetry only; no complete durable per-pipeline stage contract | A timeout can leave work running. No automatic replay or completion inference. Durable receipt work remains P0-F03. |
| Configuration read | Typed immutable read association, membership, stream absence and exact withdrawal evidence | Verified pre-read refusal can offer a new confirmed read. Generic historical reads or ambiguous ownership are not adopted. |
| Configuration publication | Typed atomic request and same-transaction configuration/target checkpoint | Resume capture for a committed result. Verified rollback permits a new confirmed publication. Historical partial configuration without this contract remains unproven. |
| Output capture | Immutable spool identity/hash/bytes, generation and exact ownership | Existing capture recovery verifies saved output without rerunning its producer. |
| Export admission/delivery | Preparation's unique job association; separate job/provider outcome | Queue admission is not delivery. Unknown writes retain their reconciliation workflow. |

Mutations retain account/storage scope, producer exclusion, owner/fence/version
checks and evidence-bound confirmation. Live work, changed configuration, missing
receipts or ownership, and released reservations alone cannot authorise continuation.

## First implementation: configuration continuation with export intent

Existing configuration continuation always saves SQL-only intent. The new
**Continue config for export** choice is offered only when the verified original
request explicitly records `pipeline_export_v1`, after rollback or pre-read refusal
independently verifies. SQL-only and keep-prior decisions remain available. Unknown
historical intent does not gain the new action.

The admin reviews all current sources/destinations and separately confirms. The
existing marker saves the intent before dispatch. The child uses that exact saved
registration and action identity. Restart/lost replies reconcile that child without
executing configuration again. Committed children hand off to existing capture/queue
recovery; failed attempts require a new confirmation. No scan import or UPDATE_ALL2
entry point is called.

This continues the configuration/output branch only. It does not close unknown
maintenance, cache, earlier reporting or provider-delivery stages, and does not
repair historical partial configuration.

## Architecture, SQL and validation

Decisions stay in services; DAL serialization, bounded JSON, CAS, original-request
hash and child-identity checks are reused. Capture collection is shared with the
synchronous guided continuation. No SQL/business logic is added to commands/views
and no command registration changes. No unrelated refactor is included.

SQL validation uses committed source `716c74e` from the authoritative SQL repository,
including `ExportPreparation`, `ExportResource`, `StatsImportExecution` and recovery
action contracts. The main SQL checkout at `d08306c` has pre-existing changes and
lacks later replacement objects; it is preserved. Temporary-table fixtures use
the complete committed snapshot, not inferred schemas.

No new SQL object, migration, receipt table or SQL transition is introduced here.
This reuses the existing marker's export-disposition field and already-supported
pipeline producer request. UPDATE_ALL2 stage-receipt work requires a separate SQL
diff, tests and Changes review.

Regression coverage includes eligibility, preserved SQL-only/legacy intent, real
temporary SQL transactions, production action policy, admin review pages,
permissions, changed configuration, live dispatch, blocked access, restart,
lost dispatch/commit/queue replies and repair failure. Provider transport and
business configuration calculation are simulated; no production acceptance follows.

Security target: **Changes**, mirror base `8b986c3c` to final candidate, Deep off.
SQL has no changed diff in this slice. Repository gates and exact updater
transition/package qualification remain separate from production acceptance.

## Required remaining programme

- F01: remaining absence/damage/replacement and repeated-repair-failure acceptance;
  retain the confirmed publication and measured timing result.
- F02: qualified successor handling when no exact backup survives,
  configuration/ownership conflicts and preserved unverifiable history.
- F03: historical partial configuration, partial UPDATE_ALL2 reporting, remaining
  durable pipeline stages and pre-request failures beyond the typed cases above.
- F04: final rollover matrix, callback/journal/SQL/worker qualification and natural
  eligible production verification.
- F05: final cross-family permissions, stale/concurrent actions, restart, lost
  replies, changed configuration, live writers, repair failure, packaging and
  separate natural production admission/provider outcomes.

No unfinished P0 obligation moves to P1. Full P1 remains next: Discord/domain
deliveries; files, archives, caches and queues outside this P0 pipeline;
independent outage/host recovery and the complete bot write inventory. Tracked
Discord view restoration remains an unconfirmed P1 observation.
