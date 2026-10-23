# Existing SSMS client confirmation — 2026-09-27

The operator selected installed SSMS 22.10.1, confirmed Windows Authentication as MINI_AMD\cwatt, and explicitly authorized visual confirmation through the already-open RDP session. This supersedes the SQL-client choice question in the after-H12 overlay. It does not approve a query or a new connection.

## UI observation

Using the Computer Use skill, the assistant found the unique returned Remote Desktop Connection window titled `mini_amd - Remote Desktop Connection`. It was minimized; it was restored. The first screenshot showed a PowerShell window obscuring an existing SSMS About dialog. No terminal input was sent. One click on the exposed About-dialog body brought that SSMS dialog forward.

The resulting screenshot shows:

- About SQL Server Management Studio: version 22.10.1.
- Object Explorer: MINI_AMD (SQL Server 16.0.1200.5 - mini_AMD\cwatt).
- Existing query tab/status: connected, MINI_AMD, MINI_AMD\cwatt, ROK_TRACKER, session label 74; blank query editor.

Screenshots remain in tool history; no standalone screenshot artifact or independent executable attestation is claimed. Version and displayed connection labels were visually observed. Windows Authentication mode is operator-confirmed, consistent with the visible Windows principal; no authentication dialog or SQL identity query was used to verify it. Session number 74 is a point-in-time UI label, not an authenticated process or durable connection binding.

The assistant did not execute SQL, open/refresh Object Explorer nodes, initiate/reconnect a session, change client settings, invoke terminal commands or scripts, or perform deployment/task control. The existing About dialog was left open. The application may maintain its pre-existing connection; no claim of zero background application activity is made.

## Remaining SQL capture binding

Chosen client: SSMS 22.10.1 on MINI_AMD. Existing observer: MINI_AMD\cwatt under operator-confirmed Windows Authentication. Target for the proposed S01 metadata block remains MINI_AMD / ROK_TRACKER.

Still missing: exact SSMS executable path/hash, secure connection configuration and reviewed timeout/cancellation procedure. Do not infer a standard installation path or approve the historical SQLCMD route. No certificate bypass or new credentials. The packet's 5-second connection / 10-second command / 15-second overall limits still need a concrete SSMS-compatible procedure; the existing connection alone does not prove them. Revise and seal the exact proposal before any query or settings change.

All seven typed G4 proofs and actual restore remain incomplete. This is a client-selection/UI receipt only, not SQL installation, restricted effective capability or rollout proof. Source/runtime distinctions, preserved evidence, isolated hotfix, single-account/admin-owned operation and all prior scope boundaries remain unchanged.
