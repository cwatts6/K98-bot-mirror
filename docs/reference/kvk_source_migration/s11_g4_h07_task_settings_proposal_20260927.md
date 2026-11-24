# H07 — four-task schedule/settings capture proposal

Status: PREPARED, NOT APPROVED OR EXECUTED. The request to continue authorized local preparation. It did not authorize this new live observation. H06 is reconciled by the dated H06 addendum; its old proposed status in earlier sealed records is historical.

## Purpose and source basis

H04 already recorded seven exact tasks, their action executables, principal/run level, state, trigger type and partial schedules. Do not repeat broad task enumeration. H06 bound the reported startup-wrapper hash to isolated hotfix source. Local tracked PowerShell/XML searches found no definitions under the four task names below; that is not proof of absence on the production host. The reviewed wrapper source is not a complete scheduled-task definition.

This operation fills the missing schedule and execution-setting fields for four known operational tasks. It does not identify unknown action arguments, authenticate a running process, or prove no other writer exists. The two SQL schema-export tasks and disabled RUN_Bot remain outside this batch. No predecessor or withdrawn collector is invoked.

## Exact operation

On MINI_AMD only, Chris Watts runs the reviewed command once as the existing `MINI_AMD\cwatt` observer, using the previously pinned Windows PowerShell executable:

`C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`

Retained SHA256: `60c9b29843624dd8af6b6a7b26147753be6aeef65098b9a503cc50850afe410f`. This is a historical tool pin, not a new integrity observation. No alternate host, elevation or authentication is authorized.

Command text: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/H07.txt` (2,511 bytes).

SHA256: `acdc0ab6614d668115286dc570ea5a6c48d82d131d622d1fd9fa5ad7f7e6ad04`.

Exactly four `Get-ScheduledTask` reads, in order:

| Task path | Task name |
|---|---|
| `\` | `StartDLBotAfterSQL` |
| `\Restart\` | `Graceful DL_Bot Shutdown` |
| `\Restart\` | `Restart daily` |
| `\` | `DLBotLogRotate` |

The command is an inert text attachment for review/copy, not a deployed runner. It emits allowlisted settings: enabled/demand-start/catch-up, time limit, battery/idle/network conditions, wake, restart and instance policy; idle duration/wait/stop/restart; trigger enabled/start/end/time limit/delay/random delay/day interval/day bitmask/week interval; repetition interval/duration/stop-at-end. Unsupported fields may be null: null does not establish a default or an absent constraint. It emits no action arguments, task XML, subscriptions, credential material or generic object dump. Values are raw Task Scheduler values; interpret bitmasks and timestamps only during reconciliation.

## Effects, budgets and stops

- Effects: local Task Scheduler/CIM metadata reads, CPU/memory and possible audit activity. No remote session, SQL/provider/Discord request, task control, file write on the Bot host, script invocation, restart or permission change.
- Budget: one attempt, four explicit definitions, one action and one trigger each (as retained), 20 seconds total operator cutoff, 32 KiB UTF-8 success output. No recursive traversal, wildcard inventory or retry. No database, business data or script contents are read by the command.
- Stop on wrong host, missing/denied task, target or shape drift, unexpected trigger class, exception, time or output limit. Preserve any error/partial result without rerunning. The stopwatch checks occur between synchronous reads; they are not a hard cancellation guarantee. At 20 seconds, interrupt locally and stop; do not start another copy if a read remains blocked. Cancellation does not prove underlying work has finished.
- Success output includes operation/host, start/end UTC, elapsed milliseconds and `Completed`. This is the command's completion marker, not independent evidence of exit status or a verified execution envelope. Record any console error separately. The 32 KiB cap applies to the emitted success payload, not unbounded internal CIM response size; no claim of a hard memory bound is made.

## Approval and evidence

Approval must cover H07 and the exact hash above, Chris as operator/reviewer/abort owner, and a new 20-minute UTC execution window recorded when approval is received. Old windows have expired. Do not execute outside that window; no standing or later-operation permission follows.

Preserve the pasted JSON verbatim as a new dated `received-H07-<receiptUTC>.txt` in the existing capture evidence directory; retain errors if any. Record receipt time separately from the reported execution times, SHA256 the receipt, and reconcile only the selected settings against H04. No task is changed on a mismatch. Seal the new receipt/reconciliation additively without rewriting original files or seals.

## Validation and remaining gates

Local PowerShell parser: zero syntax errors; no live command execution. Static review confirms four exact task reads and allowlisted metadata output. Runtime tests and architecture/deferred/test-selection validators are skipped for this additive document and inert command proposal: no application implementation is changed and no PR is being prepared. Security routing: documented skip limited to local documentation/preparation artifacts; this is not approval of future execution, nor a review of pending S11 code. No standard/deep scan is requested or launched.

Remaining action/script effects require retained/source evidence first, then separately reviewed nonsecret fields or exact script targets. Do not dump arguments to discover them. Native identity, protected-path/key custody, provider, SQL and storage observations remain separately gated. All seven typed G4 proofs and actual restore remain incomplete. Preserve the single-account model, admin-owned startup/review, fresh generated output link and equivalent reports. Rollout/G5 and memory-cause investigation remain outside scope.
