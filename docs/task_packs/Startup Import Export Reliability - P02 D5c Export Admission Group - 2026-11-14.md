# P02 D5c export retry and skip consuming guards

Status: prepared for exact Changes review and one bounded offline execution under existing approval.

The preceding 147 adapter-boundary checks passed and left the final-route count at 45/73. This group follows two routes through their original consuming implementation: `export_job/retry_unstarted` and `export_job/skip_unstarted`. No production code changes are proposed.

## Selected checks and boundaries

151 checks comprise 144 behavioral cases and seven runner controls. Retry covers scan-data, all-KVK and new-source consumers; skip covers both legacy consumers. Cases cover valid requests, stale approvals, missing/foreign records, live version/state changes, prior attempts/streams, bounded audit fields, invalid identity, refusal of the account lock, lost final CAS, modeled commit acknowledgement loss, duplicate execution and reconciliation. Additional cases cover retired/skipped history, immutable failure history, source-season eligibility, destination membership/hash, storage identity, reservation ownership/fence, held preparation/output, preserving another owner's reservation and rollback after earlier modeled resource writes.

The original adapter, `ExportCoordinationDAL` retry/skip bodies, `_account`, `_job`, `_mutex`, `_cas`, canonical row mapping, identity and new-source season guard execute unchanged. The retry decorator is an identity function to prevent retry scheduling. SQL transport and transaction lifecycle are explicit in-memory models. Their SQL allowlist asserts exact statements, arguments and locks; the final consuming decisions remain original code. A refusal of the modeled lock checks propagation only, not SQL error classification. The new-source registered-publication call is an explicit identity-checked seam; this group does not qualify its broader publication-registration validation.

Native SQL constraints/locks, transaction durability, real connection custody, physical commit uncertainty and subsequent worker execution remain excluded. Some malformed ownership or membership fixtures are defensive states, not claims about native-reachable states. `reconcile-known` repeats the accepted receipt assertion explicitly; scenario counts are not independent branch-coverage percentages.

## SQL source validation

Read and pin the authoritative definitions in `C:/K98-bot-SQL-Server/sql_schema`: `dbo.ExportJob`, `dbo.ExportJobResource`, `dbo.ExportResource`, `dbo.ExportAttempt`, `dbo.ExportExecutionStream`, and `KVK.SeasonSource`. Confirmed relevant identifiers, binary hash shapes, nullable ownership fields, state/consumer constraints, version columns, provenance bound and source lifecycle. No SQL migration or schema edit is involved. Missing SQL objects must stop preparation; no guessed schema or native query is allowed.

## Review and execution

Freeze test, runner, preparer, packet and this plan as an isolated five-file Changes range. Deep is off; review every file, including inventory-filtered tests/docs. Require independent static review and completed scan before behavior execution. Preserve ordinary Git HEAD/index. The runner is an identity-only copy of the accepted guarded runner; original hash pins are verified, new loader dependencies are pinned recursively, and receipts use exclusive creation. Failure stops the batch and preserves its intent/result; any correction uses a new packet identity under existing approval.

Emulated test selection would recommend full pytest plus startup/registration smoke checks because a test file changes. Those broad startup paths and PR-wide validators are not appropriate to this isolated packet; use AST compilation, source/SQL pin checks, exact diff review, the bounded behavioral pass and post-pass adjudication. No PR/promotion is requested.

## Acceptance and preserved limits

A full pass qualifies these two routes at **original consuming-code plus modeled SQL** scope: 47/73 accepted and 26 remaining. It does not close a native D5c family. Native C04/C05/C06 and D5d/e/f remain open, and deployment remains separate. Do not promote boundary-only results for the other 26 routes.

All evidence is preserved. The offline ceiling remains 300 seconds and 1 MiB combined receipt bytes. Native allowance remains 1,260 seconds with a 1,000-second later-stage reserve; Windows allocation remains 50 seconds. Inputs remain 21 consumed and zero new; synthetic rows remain 11/64. No VM, SQL, provider, account, permission, installation or business operation is performed. No extension or user PowerShell step is needed.
