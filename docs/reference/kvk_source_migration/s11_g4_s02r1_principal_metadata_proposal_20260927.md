# S02R1 — current database principal/role catalog capture

PREPARED, NOT APPROVED OR EXECUTED. S01R3 proved point-in-time absence of eleven exact S11 objects with reported VIEW DEFINITION=1. Do not query their shapes or repeat object inventories. This separate catalog operation resolves current named-principal/role/explicit-permission facts only.

Exact SQL: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S02R1.sql.txt`.

SHA256: `e538b8e7eb4f4f3502e93332cc31e808ba47d5d0e528cdcd3b9cbba803fd864c`.

## Targets and source basis

Use MINI_AMD / ROK_TRACKER, accepted SQL ORIGINAL_LOGIN MicrosoftAccount\cwattsconsulting@outlook.com; retain Windows/UI MINI_AMD\cwatt separately. Chris Watts is operator/reviewer/abort owner. Existing SSMS connection only, H14 observed executable SHA256 935b24379389e8260ac0d02d5e77402b005fce12c72b0ed2894a4138a6864fb7; operator-reported current query timeout ten seconds.

Read sys.database_principals for exactly SHEETS_USER, ExportExecutionAuthority, ExportExecutionReader and ExportLegacyEntryReader. Read up to 65 database-role membership edges across this database (64-row budget plus sentinel). Read up to 129 explicit database permission entries (128 plus sentinel) for those four names plus public. Output name/type/default schema, role/member names, and permission state/name/class/major_id/minor_id; no SID bytes, credentials, module text or application data.

Role names and contracts are grounded in authoritative local SQL migrations `20260924_001_export_execution_evidence.sql` and `20260924_002_export_legacy_module_permissions.sql`. Catalog SQL is retained S02 with guarded identity/visibility and a completion row; no migration executes. Missing roles remain an installation observation, not absent source or permission to provision them.

The isolated state-capture sequence from successful S01R3 is preserved: separate XACT_STATE/count/implicit flag assignments, reject nonzero/null. Identity and VIEW DEFINITION guards remain. An additional database CONTROL check ensures this admin-observer capture is not silently accepted through a restricted metadata view; if it fails, stop without granting anything. Identity output includes observed VIEW DEFINITION and database CONTROL. This observer requirement does not select or approve privileged rights for the future application identity.

## Result sets and limits

Five result sets, in order:

1. Identity/UTC and two visibility flags: one row.
2. Named principal rows: zero to four; absent rows require visibility context, not guesses.
3. Database role/member edges: zero to 65; 65 means incomplete and stops further work without pagination/retry.
4. Filtered explicit permissions: zero to 129; 129 means incomplete and stops further work without pagination/retry.
5. Completion UTC/status: one row.

One attempt, one batch, <=64 KiB output, ten-second client timeout, fifteen-second operator cutoff. Module/data reads are excluded. Catalog query CPU/I/O/memory are not hard-bounded by row limits. Role/permission inventories use MAXDOP1, session lock timeout one second and low deadlock priority. Empty fixed-role permissions are not proof of no effective rights: fixed-role capabilities, transitive membership, ownership, server roles, signatures/certificates, DENY interactions and effective application capability remain separate gaps. This is neither a full permission closure nor a permission test under the future application principal.

## Execution, effects and stop conditions

Replace only supplied capture SQL in the same existing unsaved editor; stop if other work/changed target is present. Do not save over a file or open a new query connection. Confirm this tab's ten-second timeout remains set; no settings adjustment included. Zero new connections requested; five-second connect timeout unestablished and invisible SSMS automatic reconnect cannot be excluded. Stop on disconnect/reconnect/auth/certificate prompts; no interaction, TLS weakening or alternate SQLCMD route.

Start timing before Execute. Cancel at fifteen seconds and report still-running state; cancellation is not proof server work ended. No retry, kill, reconnect, COMMIT/ROLLBACK or state remediation. Stop on guard/query errors, identity/visibility mismatch, sentinel saturation, truncated/oversized/unexpected results or incomplete completion. Preserve all output/errors and empty result-set headers. Do not expand targets or grant/revoke/alter permissions.

Effects: metadata SELECT/audit/CPU/locking and local scalar assignments; session NOCOUNT ON, LOCK_TIMEOUT 1000 and DEADLOCK_PRIORITY LOW remain afterward (same approved effects as S01R3); editor text/history/autorecovery. No data/schema/permission writes, application procedure, install/provisioning, import/export, backup/restore, Agent/task control, provider/Discord call, deployment or Git publication.

## Approval and validation

Approve S02R1/exact hash and this existing-session observer/visibility envelope for a fresh twenty-minute UTC window. S01R3 approval does not carry over. Preserve five result sets/errors, timing if available and receipt timestamp separately; hash/reconcile/seal additively. No subsequent operation implied.

Local static review verifies retained S02 catalog targets/caps, isolated guards and source role names. No live SQL validation. Documentation/inert-query preparation security-routing skip, no application/configuration/permission change or PR; runtime/pre-PR validators skipped. All seven typed G4 proofs and actual restore remain incomplete. Preserve isolated hotfix, single-account/admin-owned operation, pending/recovered files, deferred memory cause, withdrawn collector and separate KVK/view issues. Rollout/G5 remain unapproved.
