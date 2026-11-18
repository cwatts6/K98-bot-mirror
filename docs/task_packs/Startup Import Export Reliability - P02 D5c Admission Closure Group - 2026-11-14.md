# D5c admission closure group

Prepare, review and run one grouped bounded offline pass under existing operator approval. Start at 20/73 final recovery routes accepted, 53 remaining. Scope is `producer_refusal/cancel_saved_stage` and `producer_refusal/close_unstarted_admission`. Acceptance adds two routes only after all scenarios pass; it does not close D5c or authorize deployment.

Exercise the original service inspect/execute/reconcile bodies and full ProducerRefusalDAL snapshot, original-history validation, serialization, cancellation and closure methods. Load original input/filename validation, SQL row mapping, token serialization, mutex/CAS helpers, StatsImportOutcomeDAL idle/snapshot and active provider-stream gate. No application startup or external connection occurs. Reuse the accepted guarded runner and inert transaction model; the enabled runtime execution gate delegates directly to the original active-stream check. The registered-execution negative uses the final DAL directly under its real serialized scope because the service correctly delegates existing execution to a separate inspector instead of offering cancellation.

Cover exact saved cancellation, refusal checkpoints at versions 2/4/5 and a previous admission-closure marker; close original pending, preflight, sql_pending, writing and uncertain admission states. Test stale approvals, scope/hash/input mismatch, streams and execution, active/closed continuation history including 128 old attempts, lock refusals, missing/wrong resources, final CAS rollback and exact dispatcher context. Competing changes are injected after the final reviewed snapshot, before the mutation transaction. Reconciliation checks accepted and lost acknowledgements, stale decisions and foreign markers. Preserve original inputs, memberships, prior failure/closure history and unrelated owners. No business runner may execute.

The transport validates SQL text/bindings and models committed changes and rollback; it is not SQL Server scheduling, physical cleanup or permission proof. This group does not qualify resume/import work or dispatch it. No source input is opened, copied or consumed.

## Limits and preservation

One offline pass, 300 seconds, first failure stops, combined intent/result at most 1 MiB. Exclusive new receipt paths prevent automatic replay. Prior packets, receipts and every source pin remain unchanged. Native remaining 1,302 seconds with 1,000 protected for later stages; Windows-test 50 seconds; synthetic rows 11/64; inputs 21 consumed, zero new. No native operation, runtime correction, permission/setting change or limit extension. Existing retained canonical owner stays untouched.

## Review and validation

SQL contract checked read-only against `C:/K98-bot-SQL-Server`: ExportPreparation typed owner/fence/version/generation, ExportResource exact ownership and membership, execution/provider streams, and existing preparation/attempt relationships. Preserve all inherited SQL pins. Bot test-only files change; SQL repository does not.

Changes review, Deep off, exact five-file frozen diff from keep-prior review head `1b33bdb278daecf010cb2412d24a15248dcc3a60`: test, runner, preparer, packet and this plan. Parent and independent review must complete before execution. Pin all original source bodies and verify source/evidence hashes before and after execution. Preserve a failed attempt as-is and use a distinct corrected packet if required under the existing broad approval.

The test selector would recommend full pytest plus startup/command smoke checks for a test-file change. Those and broad architecture/deferred/security-routing gates remain deferred to overall handoff: this group changes no application layer, commands, dependencies or production behavior, and arbitrary startup is outside this bounded offline scope. The focused guarded batch, syntax checks, frozen diff whitespace and complete source review are the chosen validation. No refactor or new deferred optimization is introduced.

Final route countdown becomes 22/73 accepted, 51 remaining only on complete acceptance. Inspector25/25 stays accepted. Native C04/C05 and remaining final-action/native effects C06 remain open. No operator PowerShell command is needed for this offline group.
