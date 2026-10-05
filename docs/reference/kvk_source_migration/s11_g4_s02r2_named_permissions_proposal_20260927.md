# S02R2 — bounded SHEETS_USER explicit-permission capture

PREPARED, NOT APPROVED OR EXECUTED. This is a newly scoped operation after S02R1 reached its permission sentinel, not authority to retry that batch.

## Exact operation and purpose

Command: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S02R2.sql.txt`.

SHA256: `95a5eecd8326bdaf9b85535d8a05f2f68f50b1dbafdad785d16265ab503c1de8`.

Target MINI_AMD / ROK_TRACKER; accepted SQL ORIGINAL_LOGIN MicrosoftAccount\cwattsconsulting@outlook.com. Chris Watts remains operator/reviewer/abort owner. Same existing SSMS session only; observed executable SHA256 `935b24379389e8260ac0d02d5e77402b005fce12c72b0ed2894a4138a6864fb7`. Windows/UI MINI_AMD\cwatt remains separately recorded.

Read only sys.database_permissions joined to sys.database_principals with literal grantee SHEETS_USER. Return name, state_desc, permission_name, class_desc, major_id and minor_id. Order by class/object/column/permission/state/grantor ID; grantor ID is a tie-breaker only, not output. No credential/SID bytes, module definitions, object-name lookup, application data or permission testing under another identity.

S02R1 already retained one named principal, eight role edges including SHEETS_USER/db_owner, and absence of three S11 roles with full reported visibility. Do not repeat these inventories or S01R3 object absence capture. S02R1's 129 permission rows were all public, so no SHEETS_USER explicit-permission result was established. Public permissions remain INCOMPLETE and outside this operation: no claim that their retained prefix is exhaustive or irrelevant. A separately scoped public proposal is needed before any such observation. No effective-permission closure follows from this capture.

## Guards, budgets and effects

Preserve the exact S02R1 prefix: isolated XACT_STATE, transaction count and implicit flag capture; reject nonzero/null; accepted target/login; database VIEW DEFINITION and CONTROL guards; NOCOUNT ON, LOCK_TIMEOUT 1000 and DEADLOCK_PRIORITY LOW; identity/UTC/visibility result. CONTROL is an observer visibility requirement, not approved application privilege. Guard failure does not authorize a grant or transaction repair.

Three result sets: one identity/visibility row; zero to 65 SHEETS_USER permission rows; one UTC/completion row. Permission budget is 64 rows plus sentinel: 65 means INCOMPLETE and stops further work. Do not infer no effective rights from zero explicit entries, or principal persistence from an empty join. Previously observed role rights, ownership, server privileges, signatures, DENYs and public inheritance remain separate from explicit grants.

One attempt, one batch, maximum 64 KiB supplied output, current-tab query timeout ten seconds and operator cutoff fifteen seconds. Lock timeout one second, MAXDOP1 for the permission SELECT. TOP caps output, not all catalog CPU/I/O/memory. Start operator timing before Execute. No new connection requested; five-second connection timeout unestablished and invisible client automatic reconnect cannot be excluded.

Effects are catalog reads, audit/resource/locking activity, scalar assignments, retained session SET changes and SSMS editor/history/autorecovery. No persistent SQL data/schema/permission writes, application procedure execution, provisioning, backup/restore, import/export, provider/Discord calls, Agent/task control, restart/deployment or Git publication.

## Operator execution and stop conditions

Only after exact approval, within a fresh twenty-minute UTC window: replace old capture text in the same existing unsaved SSMS editor, leaving unrelated work untouched. Stop if unrelated work or a changed/disconnected target is present. Verify final marker is `S02R2 named permission metadata batch completed`; do not execute old S01R3/S02R1 text or only a highlighted fragment. Confirm ten-second timeout remains; changing settings or creating a connection is not included.

Stop on guard/query errors, unexpected identity/visibility, 65 permission rows, output above 64 KiB, truncation, unexpected/missing result sets or disconnect/reconnect/auth/certificate prompts. Cancel at fifteen seconds; report if still running. Cancellation is not server-quiescence proof. No retry, pagination, cap increase, kill, reconnect, COMMIT/ROLLBACK, TLS change, grant/revoke or alternate client. Preserve all result sets including empty headers, errors and timing; receipt time stays separate from execution time.

## Local validation and outstanding proof

Static review: unchanged approved guard prefix; one literal named-principal filter; no principal/role/object inventory repeat; deterministic order and sentinel; no dynamic SQL or mutation. Catalog fields are retained from S02R1. SQL migration source reviewed locally for the previously absent role contracts; no source execution or installation. Runtime SQL validation remains pending exact approval.

Security-routing decision remains documentation/inert-observation preparation skip: no runtime code, permissions or deployment changed, no PR. Runtime tests, predecessor suites and pre-PR validators are not warranted for this preparation. No security discovery launched.

All seven typed G4 proofs and actual restore remain incomplete. No rollout/G5 authority follows. Preserve pending/recovered work, isolated production hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues. S02R2 approval carries over to no later operation.
