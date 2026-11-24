# S01R2 — explicitly accept observed SQL observer for the metadata probe

PREPARED, NOT APPROVED OR EXECUTED. S00ID returned MINI_AMD (case-insensitive), ROK_TRACKER and original login `MicrosoftAccount\cwattsconsulting@outlook.com`. This proposal requires accepting that exact SQL observer for this metadata-only batch. It does not equate that name to Windows SID/label MINI_AMD\cwatt or select it as the future restricted application principal.

Exact SQL: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S01R2.sql.txt`.

SHA256: `3790ae24940c24b2ebf0831e183ec92caed77e41cf8198579eea14e88dccd052`.

Compared with sealed S01R1, only the expected lowercase ORIGINAL_LOGIN literal and final completion label change. Server/database, transaction/implicit-transaction and VIEW DEFINITION guards, eleven exact objects, definition size/hash handling, MAXDOP1 and metadata fields are unchanged. No guard is removed. Local text comparison verifies this limited delta. Prior failure and diagnostic remain sealed as history.

## Exact operator envelope

Chris Watts remains operator/reviewer/abort owner. Use the same existing SSMS query connection on MINI_AMD, ROK_TRACKER, Windows Authentication as operator-confirmed, with SQL ORIGINAL_LOGIN now explicitly expected to be `MicrosoftAccount\cwattsconsulting@outlook.com`. UI/Windows observer labels remain separately retained. No account creation, login change, impersonation or credential entry.

SSMS executable path is `C:\Program Files\Microsoft SQL Server Management Studio 22\Release\Common7\IDE\SSMS.exe`, H14 observed SHA256 `935b24379389e8260ac0d02d5e77402b005fce12c72b0ed2894a4138a6864fb7`. UI release 22.10.1, resource build 22.10.12210.168. Current query execution timeout must still be 10 seconds as reported by the operator. Stop on a different setting; no adjustment is included.

One attempt, one batch, existing connection only, zero new connections requested; no verified five-second connect timeout or guarantee against invisible SSMS automatic reconnect. Stop on disconnect/reconnect/login/certificate prompts without interaction. No TLS/security-setting changes or alternate SQLCMD route. Start timing before Execute, 10-second query timeout and 15-second operator cutoff; request Cancel then stop without retry. Cancellation is not server-quiescence proof; report still-running state, no kill/reconnect.

Replace only the existing supplied diagnostic/query text in the unsaved editor with the exact new batch. Stop if other work or changed target is present; do not save over a file or create a new query connection. Expected results: one identity/UTC/visibility row, eleven object rows, one completion/UTC row, <=32 KiB. Eligible module definition hash input <=1 MiB each; catalog CPU/I/O/memory is not hard-bounded. No definition text is emitted; null table module fields are expected and not table-absence proof.

Effects: metadata SELECTs and audit/CPU/locking activity; session NOCOUNT ON, LOCK_TIMEOUT 1000 and DEADLOCK_PRIORITY LOW remain afterward; editor text and normal client history/autorecovery. No data/schema/permission writes, application procedure, provisioning, deployment, imports/exports, task/Agent control, provider/Discord calls, backup/restore or Git publication. A missing object is an observation, not permission to install it.

Stop on guard/error/identity/transaction/visibility failure, reconnect prompt, time/output cap, missing/extra/truncated results or definition anomaly. Preserve all output/errors, including missing objects, without repeating predecessors or broadening the query. Source implementation remains distinct from installation proof and admin observation from restricted effective capability.

## Approval and validation

Approve S01R2/hash, the exact observed SQL observer, the stated existing-connection limits and session-setting effects for a fresh 20-minute UTC window. Earlier approvals do not carry over. Preserve all result sets/errors and operator timing if available in a new dated receipt; separate receipt time, reconcile and seal additively. No automatic subsequent query or installation.

Local validation: exact two-field text delta versus S01R1; same eleven authoritative SQL-source object names. No live SQL validation performed. Documentation/inert-proposal security-routing skip; no application/configuration/permission change or PR. All seven typed G4 proofs and actual restore remain incomplete. Preserve same-account/admin-owned operation, isolated hotfix, pending/recovered evidence, deferred memory cause, withdrawn collector and separate KVK/view issues; rollout/G5 remain unapproved.
