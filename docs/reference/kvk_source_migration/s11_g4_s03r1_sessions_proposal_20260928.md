# S03R1 — bounded SQL user-session candidates

PREPARED, NOT APPROVED OR EXECUTED. Exact query `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S03R1.sql.txt`; SHA256 `11fa3b923b4bf8b3dcd1b65baee1caf3e1a83e61c07b3a90da6581060842a3b0`.

## Target and purpose

Same existing SSMS connection to MINI_AMD / ROK_TRACKER, accepted SQL ORIGINAL_LOGIN MicrosoftAccount\cwattsconsulting@outlook.com. Chris Watts remains operator/reviewer/abort owner. Windows/UI MINI_AMD\cwatt is separate. H14 executable SHA256 `935b24379389e8260ac0d02d5e77402b005fce12c72b0ed2894a4138a6864fb7` is retained historical evidence.

This extracts only the session query from held historical S03: sys.dm_exec_sessions WHERE is_user_process=1, TOP65, ordered by session_id. Instance-wide user sessions are the explicit target, not just ROK_TRACKER; the observer's current database is guarded as context. Output session_id, login_name, host_name, host_process_id, program_name, login_time and status. No SQL text, input buffers, query plans, network addresses, credentials, requests/locks or Agent commands. The observer's own session may appear.

Purpose: identify possible SQL writer clients for later targeted reconciliation. Sleeping sessions are not necessarily harmless or drained; missing sessions do not exclude future/task/manual/provider writers. Client-supplied host/program/PID labels are not native authenticated Bot identity. SQL login_time has no timezone annotation here and must not be relabelled UTC or FILETIME. This query neither filters proven writers nor proves writer absence.

## Visibility, budgets and effects

Retain the exact S02R5 prefix: isolated transaction-state/count/implicit guards, accepted target/login, VIEW DEFINITION and database CONTROL gates, session SETs and identity/UTC/visibility row. Add IS_SRVROLEMEMBER(sysadmin)=1 before the session SELECT, stopping otherwise. This intentionally strict observer gate avoids accepting a partial instance-session view; it does not ask to grant sysadmin, select it for the application, or change an account. If it fails, the identity row may already be returned; preserve it and the error, stop without workaround.

Three result sets on success: one identity row; zero to 65 sessions; one completion row. Sixty-five is the sentinel for the 64-session budget. One attempt, one batch, at most 64 KiB output, ten-second current-tab timeout, fifteen-second operator cutoff, one-second lock timeout, MAXDOP1 on session query. TOP bounds output, not all resource use. Session state can change during capture; no consistent multi-statement snapshot claimed.

Effects: DMV/catalog reads, audit/resource/locking activity, scalar assignments, NOCOUNT ON/LOCK_TIMEOUT1000/DEADLOCK_PRIORITY LOW persisting in the observer session, editor/history/autorecovery. No persistent SQL data/schema/permissions change, impersonation, KILL, session termination, application procedure, provisioning, backup/restore, import/export, Agent/task control, provider/Discord call, deployment/restart or Git publication.

## Execution and stop envelope

Fresh twenty-minute UTC exact approval required. Same existing session only; no new connections requested, five-second connect timeout unestablished and invisible automatic reconnect cannot be excluded. Stop if that session is unavailable, target differs, unrelated editor work exists or reconnect/auth/certificate prompt appears. No new connection/settings/TLS/client route.

Replace old capture text with this complete query in the existing unsaved editor. Verify final marker `S03R1 user session metadata completed`, confirm existing ten-second timeout, execute the whole batch once (not a selected fragment). Start timing before Execute; cancel at fifteen seconds and report if still running. Cancellation does not prove server quiescence.

Stop on any guard/query error, identity/visibility mismatch, 65 sessions, unexpected/truncated results, output beyond 64 KiB, missing completion or time limit. Preserve all three sets/empty headers and errors/timing. No retry, pagination, cap increase, grants, KILL, reconnect, COMMIT/ROLLBACK or state repair. No downstream inspection/control of observed sessions is approved.

## Validation and retained scope

Local static checks compare the session SELECT to retained S03 and the prefix to S02R5; added observer gate reviewed, no Agent queries or raw command/session SQL reads included. No application schema assumption or live validation. Security-routing skip remains documentation/inert metadata proposal only; no runtime code/permission/deployment change, no PR, runtime/predecessor tests or security discovery.

All seven typed G4 proofs and actual restore remain incomplete; rollout/G5 unapproved. Preserve prior evidence/pending files, isolated hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues. This approval carries to no other operation.
