# S02R5 — remaining public negative-ID GRANT tuples

PREPARED, NOT APPROVED OR EXECUTED. Exact command: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S02R5.sql.txt`.

SHA256: `7adf4b12c7f85444bf166f444292addceeaad9b1aa2635efa83104a9c76509a6`.

## Target, evidence and scope

Existing SSMS connection to MINI_AMD / ROK_TRACKER, accepted SQL ORIGINAL_LOGIN MicrosoftAccount\cwattsconsulting@outlook.com. Chris Watts is operator/reviewer/abort owner. Windows/UI MINI_AMD\cwatt remains separately retained. H14 observed SSMS executable SHA256 `935b24379389e8260ac0d02d5e77402b005fce12c72b0ed2894a4138a6864fb7` is historical, not refreshed here.

S02R1 retained 127 distinct public/GRANT/SELECT/OBJECT_OR_COLUMN tuples with negative major IDs and minor_id=0, plus two database grants. Its 129-row sentinel left detail incomplete. S02R3 later counted 217 negative-ID GRANT entries, giving an expected residual of 90 if those observations remain compatible. S02R4 captured the separate eight public DENYs. Reuse all these receipts; do not rerun their inventories.

Read sys.database_permissions joined to sys.database_principals, filtered to public, class=1, state=G, major_id<0. Exclude only the exact retained major IDs when permission_name=SELECT and minor_id=0. The 127-ID VALUES list is derived from the sealed S02R1 receipt, not an assumed numeric range. Other permissions/columns on the same IDs are not excluded. Output the same six fields as S02R1: grantee, state_desc, permission_name, class_desc, major_id, minor_id. Grantor ID is an ordering tie-breaker only; grantor provenance was not captured and is not claimed complete.

Retained input SHA256: `dc406548b4d8489eb13685755d2af5bbbde56425ac562cdefdc719656464a821` for `received-S02R1-20260927T205324Z.txt`. No module text, object data, keys/SIDs, object-name resolution or procedure execution. Negative IDs alone do not establish default/system/safe permissions. Mapping or effective-access questions remain separate.

This fills missing tuple detail using historical exclusions; it cannot prove excluded rows still exist or that permission categories have not changed. Even an expected 90-row result is not a fresh atomic 217-row inventory or change-detection proof. Duplicate displayed tuples or an unexpected count require reconciliation. No inferred grantor-level completeness.

## Guards, budgets and effects

Retain the exact S02R4 prefix: isolated transaction-state/count/implicit checks; accepted target/login; VIEW DEFINITION and database CONTROL gates; NOCOUNT ON, LOCK_TIMEOUT 1000 and DEADLOCK_PRIORITY LOW; identity/UTC/visibility row. CONTROL is an observer visibility requirement, not future application privilege.

Three result sets: one identity row; zero to 97 residual permission rows; one completion row. Ninety is the expected count; anything else stops for reconciliation. Ninety-seven is the sentinel for a 96-row detail budget. One attempt, one batch, maximum 64 KiB output, ten-second current-tab timeout, fifteen-second operator cutoff, one-second lock timeout and MAXDOP1 on the detail query. TOP caps output, not catalog scan/CPU/I/O/memory. The constant exclusion list is in-memory query input; no table is created or written.

Effects: metadata reads/locking/audit/resource use, scalar assignments, retained session SET effects and editor/history/autorecovery. No persistent SQL data/schema/permission change, impersonation, provisioning, application execution, import/export, backup/restore, task/Agent control, provider/Discord call, deployment/restart or Git publication.

## Execution and stops after exact approval

Requires a fresh twenty-minute UTC approval window. Same existing session only; no new connection requested, five-second connect timeout unestablished and invisible automatic reconnect cannot be excluded. Stop on changed/disconnected target, reconnect/auth/certificate prompts or unrelated editor work. No settings/TLS/client changes or new connection.

Replace only previous capture text in the existing unsaved editor with the complete query. Verify final marker `S02R5 remaining public negative-ID grants completed`; execute the full batch, not a selected fragment. Confirm ten-second timeout remains. Start timing before Execute; cancel at fifteen seconds and report if still running. Cancellation is not proof of server quiescence.

Stop on guards/errors, unexpected identity/visibility, count other than 90, sentinel, duplicate tuples, unexpected fields, truncation, output over 64 KiB, incomplete completion or time cap. No retries, paging, cap increase, broader query, kill, reconnect, grant/revoke or COMMIT/ROLLBACK/state repair. Preserve all three result sets, empty headers, errors and timing; receipt and execution times are distinct. No later operation inherits approval.

## Local validation and remaining proof

Verified retained receipt seal and all referenced files before deriving exclusions; exactly 127 unique negative IDs with the required SELECT/zero-column tuple. Static checks verify unchanged guard prefix, literal category filter, 127 exact exclusions, remaining-row cap and no old inventory. Standard catalog fields and query shape are retained from prior captures; no application schema assumption or SQL source execution.

Documentation/inert-query preparation retains security-routing skip; no runtime or permission implementation, PR or deployment. Runtime/predecessor tests and pre-PR validators are inapplicable, no security discovery. Preserve all prior evidence and pending/recovered work.

All seven typed G4 proofs and actual restore remain incomplete. Rollout/G5 remain unapproved. Preserve isolated hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues. This capture is neither a permission test nor a reason to modify existing rights.
