# SSMS binding preparation — H13 and U01

PREPARED, NOT APPROVED OR EXECUTED. The operator selected SSMS 22.10.1 with Windows Authentication as MINI_AMD\cwatt; the prior authorized RDP observation confirmed visible version/server/database/principal. Continue local preparation only. No SQL query or settings change is proposed here.

## H13 — exact named-process path observation

Command: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/H13.txt`, 1305 bytes.

SHA256: `211b5454cd7dd7ce8fb57a8780dd122438bb31aca1343e949448f82c106b9b77`.

Target MINI_AMD, exactly one local Win32_Process CIM query filtered to Name = 'Ssms.exe', selecting only Name, ProcessId and ExecutablePath. Take at most two records as a sentinel; require exactly one nonblank path. Multiple/zero results stop rather than selecting a process. No command line, environment, memory, tokens, file contents or SQL are read; no discovered path is subsequently opened or hashed. The next file-hash read must be independently specified against the accepted exact path.

Chris Watts is operator/reviewer/abort owner as existing MINI_AMD\cwatt, using retained Windows PowerShell `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`, SHA256 `60c9b29843624dd8af6b6a7b26147753be6aeef65098b9a503cc50850afe410f`. No elevation or alternate identity. The pin is historical.

Budget: one attempt, one named-process CIM query, 5-second CIM operation timeout, 10-second operator cutoff, two-record sentinel with exactly one accepted, 8 KiB success JSON. The CIM timeout and outer stopwatch do not guarantee hard cancellation/provider memory bounds. Stop on wrong host, zero/multiple processes, missing path, errors or time/output cap; interrupt, retain error/partial output, no retry. No process start/stop, file write, SQL/provider/Discord connection or deployment effect. CPU/CIM/audit activity may occur. Emit operation/host/start/end UTC/elapsed/completion and the three fields; receipt time is separate. A PID/path snapshot does not establish native identity or bind that process to the displayed UI with a retained handle.

## U01 — read current query execution timeout

Exact bounded UI procedure: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/U01.txt`.

SHA256: `0aea5d4f7c2633734c13845d73b63d214470c478d0336ea4cf0495df0f76ea89`.

Target only the existing mini_amd RDP window, SSMS 22.10.1 and existing blank query tab displaying MINI_AMD / ROK_TRACKER / MINI_AMD\cwatt. The assistant uses Computer Use for observed-control navigation; Chris remains reviewer/abort owner. Require fresh UI state, not stale window coordinates. At most six input actions and four screenshots, one attempt, 60-second operator cutoff. Dismiss the existing About dialog if necessary, open the current editor's Query Options / Execution-General page, read Execution time-out without editing, then Cancel. Stop on target/identity/query-content change, ambiguity, missing control, unexpected dialog/reconnect request, error or caps. If a cap prevents Cancel, report the dialog left open without further action. No SQL execution, typing commands, metadata refresh, authentication/security-setting interaction or connection change. Only UI navigation/screenshots; existing application background activity is not certified absent.

The [Microsoft Query Execution documentation](https://learn.microsoft.com/en-us/ssms/menu-help/options-query-execution) identifies Query Options from the editor context menu and defines zero execution timeout as unlimited. [Microsoft's timeout troubleshooting documentation](https://learn.microsoft.com/troubleshoot/sql/database-engine/performance/troubleshoot-query-timeouts) distinguishes query cancellation from connection timeout. These support preparation, not a claim about the installed setting. UI observation is not proof of enforced total runtime or completed server cancellation.

Record only version/target/timeout/outcome in at most 8 KiB local notes; screenshots remain in tool history. Do not record unrelated editor data. No private bytes are requested. Do not use the prohibited terminal UI or authentication-dialog automation. No automatic retry or alternate workflow if navigation differs.

## Approval, evidence and later decision

H13 and U01 are independent and may be approved together for a fresh exact 20-minute UTC window. Approval must cover both IDs/hashes explicitly; neither authorizes the future executable hash, changing settings or S01 SQL. H13 is operator-run PowerShell, U01 assistant UI navigation. Preserve a separate dated receipt and reconciliation for each, recording execution/observation versus receipt time and sealing additively. Unexpected/missing facts stay unresolved; no blanket approval follows.

After path evidence, prepare a single named SSMS file metadata/hash read with an explicit byte budget. After timeout evidence, specify any required per-query timeout adjustment as a separate approved setting change; do not quietly alter a global default. Existing selected-client approval does not authorize a new connection or TLS/certificate bypass. The original 5-second connect / 10-second command / 15-second overall SQL envelope remains held until a concrete enforceable procedure or exact revised operator decision is documented. An already-open session alone does not establish those bounds. Never retry the historical failed SQLCMD route automatically.

Validation: H13 PowerShell parser has zero errors; static review confirms one exact process-name filter and no follow-on file access. U01 is a reviewed, capped UI procedure, not a script to execute. Documentation/inert-preparation security-routing skip; no application/runtime/configuration changes, PR, runtime test or new scan. Original evidence remains preserved. All seven typed G4 proofs and actual restore remain incomplete; same-account/admin-owned operation, isolated hotfix and deferred memory/withdrawn collector boundaries remain unchanged.
