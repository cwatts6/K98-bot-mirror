# H11 — two source-grounded task action comparisons

PREPARED, NOT APPROVED OR EXECUTED. This is local preparation after H10. New live observation requires exact approval and a fresh window.

## Evidence and purpose

H04/H10 identify the enabled nightly schema-export task and disabled RUN_Bot. Local SQL source `deploy/Install-NightlySchemaExportTask.ps1` constructs an exact candidate action from defaults: powershell.exe, the nightly wrapper path, SQL/Bot repository paths, MINI_AMD and ROK_TRACKER. The installer was read, never invoked. Local installer/wrapper bytes match SQL HEAD `4cd1554dc3d063e323f22350c88df1444cd0ed4b` after line-ending normalization. Exact hashes and retained copies are in `h11-source-pins.json`, `Install-NightlySchemaExportTask.ps1.local-source.txt` and `Invoke-NightlyProdSchemaExport.ps1.local-source.txt` in the capture evidence directory.

The wrapper source imports helpers and may source Bot development-environment scripts; it logs, fetches/prunes Git refs, switches/pulls main, invokes schema snapshot export, calls retention/postprocessing, and may send Discord failure alerts. Even NoGitCommitPush is not a metadata-only mode: initial fetch/pull and export preparation remain. This is a partial source effects map, not deployed-byte or actual-run proof. No wrapper, installer, dependency, export or cleanup was executed.

Older SQL audit/task-pack descriptions are historical, not current installed-action proof. They do not replace H10's current supplied settings. RUN_Bot candidate entrypoints are the known run_bot.py and DL_bot.py paths from retained Bot source; neither is inferred as its actual argument until a match is supplied. The operator-confirmed normal startup task remains StartDLBotAfterSQL.

## Exact operation

Command: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/H11.txt`, 3052 bytes.

SHA256: `f44061566d61feb4b981b6f38284ec364c4eff4b6e2ab475c8bc071fc3566e92`.

On MINI_AMD, exactly two Get-ScheduledTask reads:

1. `\K98 SQL Nightly Schema Export`: validate powershell.exe and working directory `C:\K98-bot-SQL-Server`. Compare arguments case-sensitively against the exact installer-default string retained in the command. This includes only fixed known paths, MINI_AMD and ROK_TRACKER. Different whitespace, case, flags, targets or credentials do not match.
2. `\Restart\RUN_Bot`: validate the retained venv Python executable and Bot working directory. Compare arguments case-sensitively against eight explicit forms: quoted/unquoted relative/absolute run_bot.py or DL_bot.py, with no extra flags or arguments.

Chris Watts is operator/reviewer/abort owner under existing MINI_AMD\cwatt. Retained Windows PowerShell path: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`; SHA256 `60c9b29843624dd8af6b6a7b26147753be6aeef65098b9a503cc50850afe410f`. No elevation or alternate identity. Tool pin is historical.

Only whole-string allowlist matches are emitted. Otherwise ArgumentsAllowlistMatched=false and AllowlistedArguments=null; no raw arguments, secret bytes, argument hashes, task XML or generic dump leave the observer. Output also includes task State, validated executable/directory, operation/host, start/end UTC, elapsed milliseconds and completion marker. Match establishes only reported task metadata equality; it does not bind deployed wrapper bytes, dependency versions, credentials, provider/SQL permissions, native process identity or actual effects. Nonmatch is a normal unresolved result, not a task defect.

## Effects, budgets, stops and receipt

- Local Task Scheduler/CIM metadata reads, CPU/memory and possible audit activity only. Arguments enter observer memory for filtering. No SQL/provider/Discord request, installer/wrapper invocation, task control, import/export, file/ACL change, deployment/restart or Git operation on production.
- One attempt, two named definitions, one Exec action each, 4096 argument characters per definition, 20-second operator cutoff, 16 KiB success output. No recursion, broad task search, retries or target discovery. Synchronous reads have no hard cancellation/internal memory guarantee.
- Stop on wrong host, missing/denied task, target/action count/type drift, executable/directory drift, length/error/time/output cap. Interrupt at 20 seconds, preserve partial output/error, do not retry or start another copy while blocked. Unknown arguments stay withheld. Do not widen matching or print raw arguments in response to nonmatch.
- Approve H11 and its exact hash with a new 20-minute UTC window recorded on approval. Old approvals/windows do not carry over. Preserve supplied output/error as `received-H11-<receiptUTC>.txt`, distinguish execution from receipt time, hash, reconcile and seal additively. Completion is not an independently observed OS exit code.

## Remaining facts and validation

The disabled older `K98 SQL Schema Export` script path and withheld Restart daily switches remain unknown. A separate question asks only for already-known nonsecret facts, explicitly without live inspection or credentials/comments. No answer is assumed and no dependent observation is prepared from guesses. These gaps do not prevent this two-task proposal.

Local PowerShell parser: zero errors. Static comparison confirms exact literal allowlists and read-only task queries; candidate SQL source was read and pinned without evaluation. No live test/import performed. Security routing is a documentation/inert-proposal skip with bounded allowlisted output, not a review of pending S11 runtime changes or permission for execution. Application tests and pre-PR validators are skipped because no application/configuration change or PR is made.

All seven typed G4 proofs and actual restore remain incomplete. Complete writer exclusion, native identity, ACL/key custody, provider/SQL/storage observations remain open. Preserve pending/recovered work, same-account/admin-owned operation, isolated production hotfix and fresh output/equivalent reports. Memory-cause investigation stays deferred; withdrawn collector stays withdrawn; empty KVK and view-rehydration stay separate. No rollout/G5, provisioning, restore or Git publication follows.
