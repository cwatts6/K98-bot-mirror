# H08 — bounded action-binding proposal

PREPARED, NOT APPROVED OR EXECUTED. Continuing local preparation does not authorize this new live capture. H07's receipt is reconciled separately; original seals remain unchanged.

## Source first

Local Git objects at production hotfix `bd980c0f497faf2048eaf1fb6b79600662911763` contain two candidate scripts. Retained verbatim Git blobs and LF/CRLF hashes are in `.codex_artifacts/s11-g4-capture-preparation-20260926/`, files `graceful_shutdown.py.hotfix-source.txt`, `rotate-logs.ps1.hotfix-source.txt` and `h08-source-pins.json`. These are candidates, not proven task bindings or deployed file hashes.

| Candidate | Git bytes / SHA256 | Source effects if invoked; no invocation now |
|---|---|---|
| graceful_shutdown.py | 13495 / `be79f5a3e2300cbddc221f8754d2fd654598308e70b5eb8f19de7d7511c305bc` | Loads Bot configuration, writes exit/marker/shutdown metadata and logs, attempts a Discord notification before process termination, waits two seconds, finds DL_bot.py command-line matches using psutil, calls terminate/wait then kill on timeout, may remove the marker, may prompt interactively. Default per-process wait is 15 seconds with environment override. This does not prove cooperative queue drain on Windows or a hard total deadline. |
| rotate-logs.ps1 | 2222 / `677d4060c69a0f6604dbc91811da1ec73db83c1e723994759e33bc4d884bcda1` | Defaults to wrapper log and last 1000 lines; may create log directory, writes a temporary file under TEMP, attempts replacement by move, copy and overwrite fallbacks with cleanup. Arguments can override log path/retention. No deployed-byte or runtime-effect claim. |

The source ordering and possible waits reinforce H07's limit: the one-minute configured shutdown/restart separation does not establish completed drain. Preserve this as a rollout planning constraint, not a new incident investigation or authorization to fix/invoke anything.

## Exact proposed observation

Command: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/H08.txt`, 3511 bytes.

SHA256: `5a59516a1e6ee912ebfe08bd983bbb26dfa30759937d7069840ed3a51083b4d1`.

Target MINI_AMD; observer `MINI_AMD\cwatt`; Chris Watts remains operator, reviewer and abort owner. Use the retained Windows PowerShell pin at `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`, SHA256 `60c9b29843624dd8af6b6a7b26147753be6aeef65098b9a503cc50850afe410f`. No elevation or alternate identity requested. This pin is historical, not a new hash observation.

Exactly three named Get-ScheduledTask reads:

1. `\Restart\Graceful DL_Bot Shutdown`: require the H04 venv executable and Bot working directory. Accept only candidate graceful_shutdown.py as absolute path or relative filename (quoted or unquoted), optionally preceded by -u.
2. `\Restart\Restart daily`: require H04 executable `Shutdown` and empty working directory. Accept only whitespace-separated /r, /f and /t followed by 1–10 decimal digits. This is a capture allowlist, not validation that combinations are meaningful or safe to execute.
3. `\DLBotLogRotate`: require H04 executable powershell.exe and empty working directory. Accept only the absolute candidate rotate-logs.ps1 path with selected -NoProfile/-NonInteractive/-ExecutionPolicy Bypass options, optional numeric -KeepLines and optional -LogFile restricted to the known wrapper-log path.

Only fully matched argument strings are emitted. Full patterns are in the hashed command, anchored at both ends with a 100 ms regex timeout. Unmatched strings produce ArgumentsAllowlistMatched=false and a null argument field; they are not printed, hashed, evaluated, followed or executed. This is a deliberately incomplete allowlist. Withheld arguments remain an unknown effect; do not rerun with a broader pattern or paste raw secrets. Duplicate options or invalid numeric semantics are retained for review, not interpreted as approved actions. The capture does not read either candidate script on the host. Deployed-byte binding would be a separate later exact file observation.

## Effects, budgets, evidence and stops

- Local Task Scheduler/CIM metadata reads, CPU/memory and possible audit activity only. No SQL/provider/Discord call, task start/stop/change, file write on the Bot host, script invocation, restart or permission change. Argument strings enter local process memory for filtering; output is allowlisted.
- One attempt, three definitions, one Exec action each, 20-second operator cutoff, 4096-character argument cap per definition, 16 KiB UTF-8 success payload. No wildcard inventory, recursion or retry. Synchronous CIM internals do not have a certified hard memory bound or hard cancellation deadline.
- Stop on wrong host, missing/denied task, target/action-count/type drift, executable/working-directory drift, regex/error/length/time/output limit. Interrupt at 20 seconds, retain error/partial result, no retry or additional copy while blocked. Cancellation is not proof all underlying work ended. An allowlist nonmatch completes as withheld metadata; review that receipt before proposing any further capture.
- Output includes exact task names, validated executable/directory, matched flag, only allowlisted arguments, host, start/end UTC, elapsed milliseconds and completion marker. The marker is not independent exit-status or native identity proof. Preserve output/error in new `received-H08-<receiptUTC>.txt`, record execution versus receipt times, hash and reconcile additively. Do not rewrite existing seals.
- Approval must name H08 and its exact hash and establish a fresh 20-minute UTC window when approved. H07 approval does not carry over. No live run follows this proposal automatically.

## Validation and unchanged boundaries

Local parser reports zero errors; twelve synthetic allowlist cases pass, including known-path acceptance and rejection of extra arguments, alternate log destinations, encoded commands and command separators. No ScheduledTasks read or candidate invocation occurred in those checks. Review covers only local preparation; no installed/runtime claim.

Security routing: documentation/inert capture-proposal skip, with explicit full-string output allowlists and synthetic negative checks. No application/configuration/permission changes or PR; architecture/deferred/test-selection validators and runtime tests are skipped on that basis. Pending S11 implementation and its historical scans remain separate. No new standard/deep scan or remediation was initiated.

All seven typed G4 proofs and actual restore remain incomplete. Other task/service/manual-tool/SQL Agent effects, native identity, protected paths/key custody, provider/SQL/storage observations remain open. Preserve the single-account/admin-owned model, fresh output link and equivalent reports. Memory-cause investigation stays deferred; withdrawn collector remains untouched; empty KVK and view-rehydration remain separate. No rollout, G5, provisioning, publication or deployment authorization is implied.
