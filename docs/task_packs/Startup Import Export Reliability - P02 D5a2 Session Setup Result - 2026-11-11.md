# P02 D5a.2 session setup result — 2026-11-11

Status: **elevated host console available; stopped at VM identity/state gate**.
This follows the operator's request to make the elevated console available.
The [approved inventory plan](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a%20Readiness%20and%20Retained%20Data%20Plan%20-%202026-11-11.md)
and all its limits remain unchanged. The
[earlier access failure](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a2%20Inventory%20Findings%20-%202026-11-11.md)
and original machine-captured receipt remain intact as a separate attempt.

## Observations and provenance

An explicit launch of the installed Windows PowerShell executable with RunAs
requested an elevated interactive console. The operator handled the local
Windows interaction and pasted the following read-only verification results:

- Host: `9SX2VF4`.
- Version: `5.1.26100.9711`; edition: `Desktop`; elevated: `True`.
- Host free memory: **11.493 GiB**; C: free disk: **1,343.698 GiB**.

Both host resource readings exceed the unchanged 8 GiB floor. These are
operator-reported observations, not an independently machine-captured inventory.
Opening this console does not attach the agent execution channel to it.

The next operator-executed check requested only VM ID
`2ac1b401-7076-4965-af71-de36ee0f9f9c` and required name
`K98-MGE-Qualification-20261029` and state `Running`. It returned the guard error:

> VM identity/state failed. Stop; do not start or change it.

The actual VM name and state were not printed. The output cannot distinguish a
name mismatch from a state mismatch; do not infer that the VM is off, renamed
or otherwise changed. The command stopped before adapter inspection, session
enumeration, the local credential prompt, or New-PSSession. No guest session
was created by this setup command; no guest, SQL or retained-input work ran.

Private derived receipt:
`.codex_artifacts/p025/d5a2-session-setup-20261111T130445Z/operator-result.json`.
It explicitly distinguishes reported observations, known command flow and
unobserved state. No credentials were submitted in the chat or written to it.

## Next bounded decision

Keep the elevated console open. Do not repeat the connection script or change
the VM to make the gate pass. The next proposed diagnostic, not yet executed,
is one read-only lookup of the same exact VM ID, returning only Id, Name and
State. Acknowledge this follow-up before running it because the approved
inventory stopped on an identity/state mismatch:

```powershell
Get-VM -Id '2ac1b401-7076-4965-af71-de36ee0f9f9c' -ErrorAction Stop |
    Select-Object Id, Name, State | Format-List
```

That result would distinguish the failed condition. It would not authorize a
VM start/resume, rename, adapter change, alternate target, rights change or
settings change. Return its result before any further setup/native work.

The consumed 21-input allowance remains consumed, with no extra input, copy,
reset or restore. All D5 obligations, time/row/output/resource limits, original
failure evidence and the D5a.1 correction remain preserved. Native readiness,
guest resources, isolation, installed SQL/contracts/ledgers and input custody
remain unverified. No installation, replay or rehearsal is authorized here.

## Review validation

This adds documentation and a private derived result only; there is no runtime,
SQL, configuration, permission or deployment patch. Security routing is a
documented skip for this exact documentation/evidence delta. The host setup
commands and operator authentication instructions are preserved in the chat;
no full collector is claimed to have been implemented, reviewed or executed.
Future collector implementation still needs its own review decision.

Run document architecture/deferred/security-routing checks, explicit-path test
selection, link/whitespace validation and prior receipt/candidate custody checks.
Executable regression tests and native qualification are skipped because this
delta changes no application behavior and the VM gate failed.
