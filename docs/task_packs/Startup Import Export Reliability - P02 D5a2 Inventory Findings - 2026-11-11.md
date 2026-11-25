# P02 D5a.2 bounded inventory findings — 2026-11-11

Outcome: **inventory incomplete — stopped at the host access gate**.
The operator approved the bounded read-only
[D5a.2 plan](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a%20Readiness%20and%20Retained%20Data%20Plan%20-%202026-11-11.md).
One initial access observation was made; no automatic retry or larger-budget
attempt followed the failed gate.

## Observed result

At `2026-11-11T12:57:26.0461495Z`, the chosen execution channel reported:

| Gate | Required | Observed |
| --- | --- | --- |
| Host | `9SX2VF4` | Matched |
| PowerShell | Windows PowerShell 5.1, Desktop | 7.6.9, Core |
| Effective identity/access | Authorized elevated host context | `9SX2VF4\CodexSandboxOffline`, not elevated |

The tool request explicitly selected
`C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`; the observed
version/edition did not satisfy that request. The observed process context is
authoritative for this attempt. This does not prove that Windows PowerShell 5.1,
an elevated console, or a suitable authenticated session is absent elsewhere on
the host. Other processes/sessions were not enumerated. This was a failed
environment prerequisite, not an automatic approval-review rejection.

The read-only command queried only the current Windows identity, elevation,
host name, process ID and PowerShell version/edition. Its exact text, tool
result, limits and observations are preserved in:
`.codex_artifacts/p025/d5a2-inventory-20261111T125726Z/host-access-receipt.json`.
The reported command wall time was 0.163 seconds; the receipt is below 1 MiB.
No full SQL/VM collector was implemented or executed after this first gate
failed. No claim is made that an unbuilt collector passed review or validation.

## What remains unverified

| Planned stage | Disposition |
| --- | --- |
| Host/guest free memory and disk | Not sampled; historical values are not promoted to current evidence. |
| Exact VM identity, Running state, zero network adapters | Not inspected. No VM command executed. |
| Unique current authenticated PowerShell Direct session | Not inspected. No guessed session ID or new credential/session operation. |
| Guest identity and active producer checks | Not reached. |
| Retained 21-input file custody | Not reached; no input file was read or changed. Prior local capture hashes remain historical evidence. |
| SQL identity/settings/contracts/receipts/ledgers/resources | Not reached; zero connections and zero SQL statements. |
| SQL connection cleanup | Not applicable to this attempt: no SQL connection was created. |

## Case-to-state feasibility and next prerequisite

| Obligation | Available evidence | Current prerequisite/gap |
| --- | --- | --- |
| D5a readiness | Local retained-file audit and this failed access observation | A usable elevated Windows PowerShell 5.1 Desktop channel on the exact host, then the remaining approved gates. |
| D5b 42 detailed states, 14 exports, immutable bytes, six maintenance children | Intact historical baseline captures | Current target state is unverified; last accepted state was completed/read-only. No authorized mutable pre-state or fresh input allowance is established. |
| D5c both-order concurrency and permission/factory cases | Prior bounded component observations only | Exact combined candidate, accessible isolated target and separately authorized controlled workload. |
| D5d native fault/cancel/restart ownership | Approved local D5a.1 drain evidence | Native target readiness and case-specific authorization remain outstanding. |
| D5e warmup plus five balanced OFF/ON pairs | Historical Phase 1 timing evidence only | Comparable authorized pre-states; the historical reset/restore harness remains outside current limits. |
| D5f/D6 integration and release | Full obligation register retained | No new acceptance or release credit from this incomplete inventory. |

Next prerequisite: make an authorized elevated Windows PowerShell 5.1 Desktop
execution channel available on `9SX2VF4`, with exactly one Opened/Available
PowerShell Direct session bound to VM ID
`2ac1b401-7076-4965-af71-de36ee0f9f9c` (`K98-MGE-Qualification-20261029`).
The approved plan requires operator-created authentication if that session does
not exist; credentials must not be posted in the chat or evidence. Do not change
rights, start/resume the VM, add a network adapter, alter settings or reset data
to satisfy the prerequisite. A host access check is not permission to enter an
unverified guest.

Once the execution context is available and continuation is requested, retain
this failed receipt separately and prepare/static-check the narrow collector
and its exact query/path allowlists before the next attempt. Bind its bytes and
limits in a new receipt, make its own Changes/Deep-off security-review decision,
and execute only the previously approved read-only inventory. A successful
inventory still returns findings before installation, replay or rehearsal.

## Preserved boundaries and validation

The 21-input allowance remains consumed, with zero additional consumption.
No SQL connection, VM operation, guest command, input access, installation,
replay, rehearsal, copy/reset/restore, permission change, process/service change,
schedule change or production/provider action occurred. All original failure
evidence and the D5a.1 correction remain preserved. Full D5 scope and the
resource, timeout, row/output and cost limits in the approved plan are unchanged.

This turn adds this findings document and private generated evidence only.
Security routing: documented skip for that exact documentation/evidence delta;
no executable collector, runtime, SQL, configuration, permission or deployment
patch was introduced. The direct host observation is recorded in full and has
no SQL/VM/credential action. The prior drain security review is not reused as
collector coverage. A future collector must receive its own decision before use.

Validation covers document links/whitespace, receipt size/structure, current
candidate/original-evidence custody and architecture/deferred/security-routing
gates. Test selection is run for this document. Runtime pytest, imports,
registration and native validation are skipped: no behavior changed, and the
required native execution context failed its first gate.
