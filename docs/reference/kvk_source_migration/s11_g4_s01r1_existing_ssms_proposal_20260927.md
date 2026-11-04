# S01R1 — exact metadata probe using the existing SSMS connection

PREPARED, NOT APPROVED OR EXECUTED. The operator reports changing execution timeout from 15 to 10 seconds and asks to proceed. This records that supplied setting and prepares the revised exact query/envelope; it does not silently convert the old connection-timeout requirement into approval. Original U01/U01R1 failed/stopped records remain untouched; no UI retry was performed.

## Client, observer and target

Use only the already-connected SSMS query editor on MINI_AMD, database ROK_TRACKER, Windows Authentication as MINI_AMD\cwatt. Chris Watts is operator/reviewer/abort owner and runs the SQL manually. SSMS About reported 22.10.1; H14 resource version is 22.10.12210.168. Observed executable:

`C:\Program Files\Microsoft SQL Server Management Studio 22\Release\Common7\IDE\SSMS.exe`

H14 observed SHA256: `935b24379389e8260ac0d02d5e77402b005fce12c72b0ed2894a4138a6864fb7`. This is an observed pin, not independent vendor authenticity or full runtime closure. Current query execution timeout=10 seconds is operator-reported, not independently reobserved. Before executing, Chris must confirm the active query tab retains that value; do not assume a global default applies to this tab. A mismatch stops this operation; no settings adjustment is included.

## Explicit connection-envelope revision for approval

The original subpacket proposed a new connection with a 5-second connect timeout. S01R1 instead requests **zero new connections**, one batch on the existing authenticated query connection, 10-second query timeout and a 15-second operator overall execution cutoff. Five-second connection timeout is not claimed verified or satisfied. If disconnected, a reconnect/login/certificate prompt appears, or the connection changes, stop without executing/reconnecting. Do not change encryption/trust/certificate settings or use the historical failed SQLCMD route. Any SSMS internal automatic reconnection not exposed by the UI cannot be excluded by this procedure; approval must accept that limited existing-session observation rather than claim a proved no-reconnect mechanism. If that limitation is unacceptable, keep SQL held for another exact client procedure.

## Exact query and effects

Query text: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S01R1.sql.txt`.

SHA256: `0aab337e0626985f7325d680ce3a3df9aef85c0559be9af46cbb2fed21205b9a`.

This retains original S01's eleven exact source objects and definition-hash query, adding guards before metadata capture: server MINI_AMD, database ROK_TRACKER, original login MINI_AMD\cwatt, no current/implicit transaction, and database VIEW DEFINITION. Unexpected identity, transaction state or visibility raises an error and stops. No USE, impersonation, application procedure, application table read, import/export or migration is executed.

The batch sets NOCOUNT ON, LOCK_TIMEOUT 1000 and DEADLOCK_PRIORITY LOW for this session; these session settings remain changed afterward and are explicitly part of the proposed effect. They are not data/schema/permission changes. It returns identity/UTC/visibility, then eleven object rows with name/type/presence, definition byte length and SHA256 of <=1 MiB module definitions in SQL UTF-16 byte domain, then completion UTC/status. Table definition fields are normally null because sys.sql_modules applies to modules; this is not proof a table is missing. Definition text is not emitted. Missing/invisible/encrypted/oversized definitions remain unresolved; no dynamic expansion or rerun.

Source targets were checked against the authoritative local SQL schema filenames. This is a limited presence/definition observation, not full column/index/UDT/signature/grant or restricted-application capability proof. Admin observer permissions do not establish application permissions. Installed hashes must later be compared in the same byte domain; no direct raw UTF-8 source-hash comparison.

## Budget, execution and stops

- One attempt, one batch in the existing query tab; no GO repetition, automatic retry or concurrent copy. Start timing immediately before Execute. 10-second reported client timeout; 15-second operator cutoff; request Cancel at cutoff and stop without retry. Cancellation does not prove the server ended work. If still running, report that state for a separate decision; do not kill the session or close/reconnect to hide it.
- Three result sets: one identity row, exactly eleven object rows, one completion row; <=32 KiB supplied text output. Definition hashing eligibility <=1 MiB per module; catalog evaluation has no certified hard memory/I/O bound. The eleven-row query uses MAXDOP 1; lock timeout is one second. No physical backup/media/database inspection outside the named catalogs.
- Stop on errors, unexpected identity/visibility/transaction guard, missing/extra/truncated result sets, output/time cap, reconnect/certificate prompt or definition anomaly. Preserve all returned rows/errors, including missing objects; do not install anything or recapture predecessors. Lack of completion row is incomplete, not success.
- Effects: metadata query execution and audit/CPU/locking activity, the three stated session-option changes, query text entered in the existing editor and possible normal SSMS local history/autorecovery. No Bot/SQL deployment, data/schema writes, provisioning, provider/Discord calls, BACKUP/RESTORE/VERIFYONLY/CHECKDB, Agent/task control or Git publication.
- Paste this exact batch once only after approval in the already-observed blank query editor. Do not create a new query connection. Existing nonblank editor content, changed target or unknown settings stop for review. Do not save over a file. Assistant will not enter or execute SQL during this preparation.

## Approval and evidence

Approve S01R1, its exact hash, the existing-connection envelope revision/limitations, and the stated session settings for a new 20-minute UTC window. H14/timeout-update approval alone does not authorize this revised SQL batch. Preserve all three result sets and errors as a new dated receipt, execution start/end and observed elapsed if available, alongside the server UTC fields. Separate receipt time from execution. Hash and reconcile additively; never rewrite prior evidence.

Local validation: eleven object names resolve to authoritative SQL source files; guards/output/scope manually reviewed. No live SQL syntax/runtime validation or application tests were run. Documentation/inert-query preparation security-routing skip; this does not substitute for implementation review. Runtime/pre-PR validators skipped because no application/SQL deployment change or PR occurs. All seven typed G4 proofs and actual restore remain incomplete. Missing installation/runtime evidence does not imply missing source. Preserve single-account/admin-owned model, isolated hotfix, deferred memory investigation, withdrawn collector and separate KVK/view issues; later rollout/G5 remain unapproved.
