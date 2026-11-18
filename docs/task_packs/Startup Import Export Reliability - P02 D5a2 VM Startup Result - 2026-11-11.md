# P02 D5a.2 VM startup result — 2026-11-11

Status: **exact VM running and isolated; inventory stopped by host memory floor**.

The operator explained that the VM had been off because it was not needed for
the last two phases, and explicitly requested starting it. That authorizes this
start; it does not waive the [approved inventory limits](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a%20Readiness%20and%20Retained%20Data%20Plan%20-%202026-11-11.md)
or authorize installation, replay or rehearsal. The
[previous session setup result](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a2%20Session%20Setup%20Result%20-%202026-11-11.md)
and its receipt remain separate and unchanged.

The agent's preliminary exact-ID lookup received an operating-system Hyper-V
permission denial. It changed no VM state; this was not an automatic approval
review rejection. The operator then ran the guarded start command in the
already verified elevated Windows PowerShell 5.1 console. It checked the host
resource floor, exact ID/name and zero adapters before allowing a start from
Off; it did not change VM configuration or retry a failed start.

## Operator-reported result

| Observation | Value | Disposition |
| --- | --- | --- |
| VM ID | `2ac1b401-7076-4965-af71-de36ee0f9f9c` | Expected target |
| Name | `K98-MGE-Qualification-20261029` | Matched |
| State | `Running` | Start objective achieved |
| Network adapters | `0` | Isolation matched at observation |
| Host free memory after start | **4.271 GiB** | Below unchanged 8 GiB minimum; stop |
| Host C: free disk after start | **1,343.658 GiB** | Above unchanged 8 GiB minimum |

The rounded memory reading is approximately 3.729 GiB below the required floor.
Do not reduce the floor or change VM memory settings to make the result pass.
No automatic stop/restart, process termination or settings change followed.

The private derived receipt is
`.codex_artifacts/p025/d5a2-vm-start-20261111T131136Z/operator-result.json`.
These values came from operator-pasted output, not an independently captured
full inventory. The actual guest services/tasks started by boot were not
observed; do not claim that boot had no guest-side effects.

## Remaining boundary

No guest command, SQL connection, input inspection, installation, replay or
rehearsal was issued by this startup procedure. The consumed 21-input allowance
remains consumed; no additional input use is authorized. Guest identity,
resources, active producers, installed SQL/contracts/ledgers and retained input
custody remain unverified. Opening an elevated operator console has not attached
the agent's execution channel to it.

The next prerequisite is sufficient host free memory while this VM remains
running. The operator may decide which unrelated host applications can be
closed after saving work; the agent has not closed anything or selected a
process to terminate. After that external condition changes and continuation
is requested, take a fresh bounded resource observation. Only a passing result
permits continuation of the previously approved read-only setup/inventory.
Do not automatically retry, start a workload, reset data or enlarge the allowance.

## Validation

This result adds documentation and private generated evidence only. Security
routing is a documented skip for that exact delta: no runtime, SQL,
configuration, permission or deployment implementation was changed. The VM
start was an explicitly authorized operator action, not a new executable patch.
No full inventory collector is claimed to have been implemented or reviewed.

Validate document links/whitespace, evidence structure and size, prior failure
receipts and source/test hashes; run architecture/deferred/security-routing and
explicit-path test selection. Runtime tests/imports/registration and native
qualification are skipped because no application behavior changed and the
host memory gate failed.
