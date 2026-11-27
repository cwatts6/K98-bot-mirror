# H10 — remaining named-task settings proposal

PREPARED, NOT APPROVED OR EXECUTED. This is local preparation following H09 reconciliation. Prior approvals do not authorize this capture.

## Purpose and exact targets

H04 retained seven named task definitions with partial schedules. H07 covered four; H10 fills the missing schedule/execution settings for the other three. Source/retained evidence is the H04 receipt, not guesses based on task names. H09 resolved two script hashes; it did not resolve these task settings or restart arguments.

On MINI_AMD only, three exact Get-ScheduledTask reads in this order:

| Task path | Name | Expected trigger class | H04 context, not refreshed fact |
|---|---|---|---|
| `\` | K98 SQL Nightly Schema Export | MSFT_TaskDailyTrigger | Ready, cwatt/Highest, powershell.exe, working directory C:\K98-bot-SQL-Server |
| `\` | K98 SQL Schema Export | MSFT_TaskDailyTrigger | Disabled, cwatt/Highest, powershell.exe, working directory C:\Scripts |
| `\Restart\` | RUN_Bot | MSFT_TaskLogonTrigger | Disabled, cwatt/Highest, venv Python, Bot working directory |

Each had one action and one trigger. This operation does not execute schema export, connect to SQL, run Bot, or enable anything. Disabled task state is distinct from enabled trigger state. Names do not prove scope or effects; action arguments remain withheld and unbound.

## Exact command and observer

Command text: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/H10.txt`, 2526 bytes.

SHA256: `c20a11bbbf4fa0898db593cb8524f4fcf3f3256580d7cbc39bb1dcae403b78e2`.

Chris Watts is operator/reviewer/abort owner, using existing MINI_AMD\cwatt and retained tool `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`, SHA256 `60c9b29843624dd8af6b6a7b26147753be6aeef65098b9a503cc50850afe410f`. No elevation or alternate identity. The tool hash remains historical.

The command adapts the retained H07 metadata-only procedure to these three targets, adds task State and checks each expected trigger class. It emits only named settings: enabled/demand-start/catch-up/time limit, battery/idle/network/wake conditions, restart policy and multiple-instance policy; idle settings; trigger boundaries/time limit/delay/random delay/day/week intervals and masks; repetition settings. No action arguments, XML, credentials, subscription data or generic object dump is emitted. Unsupported/null fields remain uninterpreted; no default is inferred. State is a snapshot, not execution history or complete writer exclusion.

## Budgets, effects, stops and evidence

- One attempt, three exact definitions, one action/trigger per task, 20-second operator cutoff, 32 KiB UTF-8 success output. No enumeration, recursion, remote session, retries or other targets.
- Effects: local Task Scheduler/CIM metadata reads, CPU/memory and possible audit activity. No task control, file/ACL write, script invocation, SQL/provider/Discord request, backup/restore, import/export, Bot deployment/restart or activation.
- Stop on wrong host, missing/denied task, target/action/trigger-count drift, unexpected trigger class, exception or time/output limit. Interrupt at 20 seconds and retain partial output/error without retry. A state/settings difference is captured for review, not permission to correct it. Synchronous reads have no guaranteed hard cancellation or internal memory bound; do not start another copy while blocked.
- Output includes H10, host, start/end UTC, elapsed milliseconds and Completed, followed by the three task records. Completion is not independent exit-code/native identity proof. Preserve receipt time separately from reported execution times.
- After exact approval, record a new 20-minute UTC execution window with Chris as operator/reviewer/abort owner. Expired or earlier operation windows do not carry over. Preserve output/error as new `received-H10-<receiptUTC>.txt`, hash, compare scope/window/budgets to this proposal, reconcile against H04 and seal additively. Never overwrite originals or prior seals.

## Validation and boundary

Local PowerShell parse: zero errors. Static review confirms three literal task names, per-target class/shape checks and allowlisted settings only. H07's earlier execution does not prove H10 will succeed. No H10 live read was performed. Application tests and architecture/deferred/test-selection validators are skipped for additive documentation/inert command preparation with no runtime/configuration changes or PR. Security routing remains a documented preparation-only skip; pending S11 code reviews are separate. No standard/deep scan or remediation.

This completes preparation for missing settings among the seven already sampled tasks, not a complete task/service/manual-tool/SQL Agent writer inventory. Action bindings for these tasks, withheld restart arguments, native identity, protected-path/key custody, provider/SQL/storage observations remain unresolved. All seven typed G4 proofs and actual restore remain incomplete. Preserve the shared-account/admin-owned startup model, isolated hotfix, fresh output link/equivalent reports, and pending/recovered work. Memory cause stays deferred, withdrawn collector stays withdrawn, empty KVK/view-rehydration remain separate, and rollout/G5 remain unapproved.
