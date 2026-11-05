# S02R4 — public object/column DENY detail capture

PREPARED, NOT APPROVED OR EXECUTED. Exact command: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S02R4.sql.txt`.

SHA256: `18a97dc287264b7a8c4a1519b62004765c24b23ec4ef2cfd8e4c0043ec38ec24`.

## Target and missing fact

MINI_AMD / ROK_TRACKER, accepted SQL ORIGINAL_LOGIN MicrosoftAccount\cwattsconsulting@outlook.com, existing SSMS session only. Chris Watts is operator/reviewer/abort owner. Windows/UI MINI_AMD\cwatt remains separately recorded. Retained H14 SSMS executable SHA256 `935b24379389e8260ac0d02d5e77402b005fce12c72b0ed2894a4138a6864fb7`; not a new runtime binding.

S02R3 counted eight public OBJECT_OR_COLUMN DENY entries, all in the other/nonnegative-ID bucket. Their exact permission names and installed targets remain unknown. S02R4 reads only sys.database_permissions entries where joined principal name is public, class=1 and state=D. LEFT JOIN sys.objects, sys.schemas and sys.columns resolves names without dropping an unresolved permission row. Output grantee, state/permission/class names, major/minor IDs, schema/object/type/column names and two resolution flags. A minor_id of zero denotes no column-specific lookup; column_name NULL with column_resolved=1 is expected for that case. No column values, module bodies, keys/SIDs, object data or procedure execution.

Source review found public DENYs in authoritative migration `C:\K98-bot-SQL-Server\migrations\20260924_001_export_execution_evidence.sql`. Its source clauses cannot identify these installed entries: S01R3 observed those S11 objects absent. Do not infer an S11 conflict, apply a migration or remove DENYs based on a count. This capture supplies catalog facts only; no effective-access claim or remediation authority follows.

Reuse prior principal/membership, explicit SHEETS_USER grants, two procedure/schema mappings and public counts. Do not repeat those inventories. The 217 negative-ID public grants remain only partly detailed; S02R4 neither enumerates nor clears that remaining gap. Public DATABASE grants are outside this query.

## Guards, output and budgets

The exact S02R3 guard/identity prefix is retained: isolated XACT_STATE/count/implicit checks; accepted target/login; VIEW DEFINITION and database CONTROL gates; NOCOUNT ON, LOCK_TIMEOUT 1000 and DEADLOCK_PRIORITY LOW; identity/UTC/visibility output. CONTROL is observer visibility, not future application privilege.

Three result sets: one identity row; zero to 17 DENY detail rows; one completion row. Expected retained count is eight; any count other than eight requires stop/reconciliation without retry because the prior count cannot silently be assumed current. Seventeen is also the sentinel for the sixteen-row maximum detail budget. Missing object/schema or required column mapping (either resolution flag zero) requires stop, preserving rows; no broader lookup is authorized.

One attempt, one batch, maximum 32 KiB output, ten-second current-tab query timeout, fifteen-second operator cutoff, one-second lock timeout, MAXDOP1 on the detail query. TOP limits output, not all catalog scan/CPU/I/O/memory. Separate statements and previous receipts are not a transactional snapshot. Output timing is not a full execution stopwatch.

Effects: catalog reads/locking/audit/resource use, scalar assignments, persistent session SET effects and editor/history/autorecovery. No persistent SQL data/schema/permission changes, impersonation, provisioning, application execution, backup/restore, import/export, task/Agent control, provider/Discord calls, restart/deployment or Git publication.

## Execution and stops after exact approval

Fresh twenty-minute UTC window required. Same existing SSMS connection only; no new connection requested, five-second connect timeout unestablished, invisible automatic reconnect cannot be excluded. Stop on disconnected/changed target, reconnect/auth/certificate prompt or unrelated editor work. Do not create a connection or alter settings/TLS/client.

Replace only previous capture text in the existing unsaved editor with the complete exact batch. Verify final marker `S02R4 public DENY details completed`; execute all text, not a selected fragment. Confirm the existing ten-second timeout. Start operator timing before Execute; cancel at fifteen seconds and report if still running. Cancellation does not prove server quiescence.

Stop on guard/query errors, identity/visibility mismatch, count drift, sentinel, unresolved mappings, output over 32 KiB, truncation, unexpected/missing results, missing completion or time limit. No retries, paging, cap changes, grant/revoke, kill, reconnect, COMMIT/ROLLBACK or state repair. Retain all three result sets including empty headers, errors and timing. Receipt timestamp is separate from execution time. No subsequent operation inherits approval.

## Validation and retained scope

Local static review checks unchanged prefix, literal public/class/state filter, bounded output and LEFT JOIN resolution preserving misses; only catalog SQL, no dynamic query or runtime mutation. Live validation remains pending approval. Documentation/inert-capture preparation retains the security-routing skip; runtime/predecessor tests and pre-PR validators are inapplicable, no PR or security discovery.

All seven typed G4 proofs and actual restore remain incomplete; rollout/G5 remain unapproved. Preserve pending/recovered work, isolated hotfix, approved single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues.
