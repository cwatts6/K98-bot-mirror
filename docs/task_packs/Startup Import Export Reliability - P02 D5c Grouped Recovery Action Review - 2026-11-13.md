# P02 D5c grouped recovery-action review

## Scope and current position

The six-case inspector batch is accepted: 25/25 inspector schedules complete.
The accepted factory matrix closes C09. D5c remains 9/12 families, with C04
(season/weights), C05 (queue/pool/holds) and C06 (effectful recovery) open.
The operator has approved continuing D5, batching where possible; this is not
production deployment authority or permission to relax numeric limits silently.

The next offline packet is `scripts/run_p02_d5c_action_orchestration.py`, with
`tests/test_p02_d5c_action_orchestration.py` and the frozen manifest under
`.codex_artifacts/p025/d5c-action-orchestration/packet.json`. It contains 42
distinct schedules: 7 execution-boundary controls, 8 Refresh/reconciliation,
7 dispatch/claim, 10 group-completion, 4 historical-approval acknowledgement,
and 6 automatic outcome-selection checks. One pass, first failure stops,
300 seconds, 1 MiB combined diagnostics, no native operations or new inputs.

## Source findings and proof boundaries

`RecoveryService.refresh` is effectful: it reconciles previously accepted actions
under the operation guard, preserves their original failure record, and only
then enters observation for a fresh inspection. A disabled fresh action must not
erase an already accepted action. Busy callers must not race that reconciliation.
The new matrix exercises those original bodies, including actual local guard,
observation context, failure projection and release-policy code.

`RecoveryService._dispatch` persists the claim before dispatch. Lost claim replies
and existing claims cannot authorize a second dispatch. A thrown dispatch marks
the durable result unknown. `_execute` releases its local guard before refreshing
the saved result. The matrix checks those transitions with inert stores/adapters;
it does not pretend a mock dispatch proves the adapter's final SQL guard.

Evidence and historical batches close only when the exact approved count has
terminal outcomes. Unknown, missing or excess outcomes cannot be called complete.
Historical approval first looks up the exact prior approval and performs the same
lookup after a lost reply. The approval cases deliberately isolate membership
verification and DAL persistence; those final guards remain separate obligations.

The automatic import-outcome selector can settle only a proven release_failure;
partial/unknown/failed observations retain the hold. No import or report replay
is needed to exercise this selector offline. This is not the complete scheduled
outcome worker or native settlement qualification.

## Remaining C06 binding

The original 73 policy-pair common-admission result stays accepted. It does not
prove every downstream adapter. Review must follow these production compositions:

| Family | Actual entry and downstream continuation |
|---|---|
| Stats/all-KVK/player/config capture | ImportRecoveryAdapter -> AllKvkCaptureRecoveryAdapter -> PlayerReportRecoveryAdapter -> ConfigurationProducerRecovery inheritance; settle, queue, run, abandon and cancel DALs |
| Configuration continuations | ConfigurationContinuation, inherited ConfigurationReadContinuation and LegacyConfigurationContinuation; serialized snapshot, exact marker, final record/reserve checks |
| Player/report/pipeline/refusal | PlayerReportContinuation, StatsReportContinuation, ProcessingPipelineRecovery, ProducerRefusalRecovery; exact continuation identity and original intent |
| Queue/hold/legacy | QueueAdmissionRecovery, UnownedSqlHoldRecovery, UnreceiptedProducerRecovery; final withdrawal/hold/retain guards |
| Export | ReplacementRecoveryAdapter wrapping ExportRecoveryAdapter; failed-export authority path, replacement authority context, delivery admission and inherited retry/proof paths |
| Rollover | RolloverReplacementAdapter wrapping RolloverRecoveryAdapter; replacement context and exact queued operation |
| Evidence/config read | EvidenceRecoveryAdapter and ConfigReadRecoveryAdapter; actual authority selectors and final receipt-bound mutation |

Generic Recheck means `RecoveryService.review -> refresh`; it is a behavior label,
not a separate `GenericRecheck` class. The scheduled `observe_recovery` path also
prioritizes accepted evidence/historical actions before discovery. Its deduplication
and automatic-action routing remain to be bound to this matrix. Actual final DAL
and authority guards, inherited paths, group membership/approval and complete
outcome-worker routing must be adjudicated before C06 closes. Source references
alone are not passed tests, and no family count advances for this preparation.

## Next grouped native preparation

Combine C04 and C05 against one relationship-complete labelled fixture on the
existing disposable database. Prepare all fixture identities/rows and both
arrival-order schedules before a handoff. Reuse accepted configuration and
restricted-reader evidence. Missing/denied metadata cases must use existing
approved seams or an explicit account/permission exception, never inferred rights.

Existing native pytest fixtures are assertion references only: they create a
database, omit foreign keys and delete whole tables. They must not be executed
on retained data. Validate the new fixture against the authoritative SQL source
and captured catalog, preserve foreign keys, and update only exact labelled rows.
No fixture count or command is approved by this design note before the complete
row proposal and executable gates have passed review.

The intended handoff is one fixture setup followed by one fail-fast grouped
consistency packet, with separate case receipts and cleanup gates. This is a
batching target, not a promise that two commands close all of D5c. Any measured
operation/source/row/time excess will produce one exact extension request before
native execution. The earlier six-case inspector exceptions do not transfer.

## Validation and security routing

Test-only files; no runtime, SQL source, permissions, deployment or retained-data
change. Reuse the accepted no-site runner with explicit standard-library preload,
create-only intent/result, bounded output, pinned source/evidence and blocked
network/native/process/thread/file effects. Preserve all prior failures.

Run a Changes review on a frozen narrow Git range, Deep off, before the single
offline pass. Include runner, tests, manifest, preparer and this plan. No broader
codebase scan. The test selector would recommend full pytest for a test-file
change; that is intentionally not run because conftest/application startup and
native fixtures exceed this bounded qualification. Broad smoke imports and
command registration are likewise excluded. No PR/promotion is being handed off;
architecture/deferred/security-routing validators remain later release gates.
No production refactor is introduced and no new optimisation debt is accepted.

Balances remain 1,305 native seconds, including a protected 1,000-second reserve;
305 seconds available to D5c; 50 Windows-test seconds; 11/64 synthetic rows; 21
inputs consumed and zero new. All exhausted retry allowances remain exhausted.
