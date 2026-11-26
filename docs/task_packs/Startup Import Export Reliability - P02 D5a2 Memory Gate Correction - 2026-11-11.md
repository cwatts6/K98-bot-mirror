# P02 D5a.2 memory-gate correction — 2026-11-11

**The assistant's post-start memory stop was based on an incorrectly expanded
requirement. It is withdrawn; the original limits remain unchanged.**

The original
[Phase 1 implementation record](archive/Startup%20Import%20Export%20Reliability%20-%20P02%20Phase%201%20Implementation%20-%202026-11-07.md)
defines, at line 160, at least 8 GiB free host memory **before starting the VM**.
Lines 172–175 expressly state that this is not an additional 8 GiB reservation
after startup and retain the 4-CPU / 8-GiB / zero-network-adapter VM. The guest
requirement at line 161 is 8 GiB free **disk**, not free memory. The later
remaining-work handover calls the host memory condition an existing prerequisite;
the later abbreviated D5 wording did not explicitly change its timing.

The assistant incorrectly converted that inherited prerequisite into an 8 GiB
post-start host gate and also added an impossible 8 GiB free-memory gate inside
an 8 GiB guest. Those additions did not preserve the original constraints. The
readiness plan and local scope-review wording are corrected to their source;
this is not a request to lower an approved resource limit.

## Actual evidence and disposition

- Before the authorized VM start, the guarded operator command checked host
  free memory and disk against 8 GiB and reached the start without throwing.
  The earlier operator-reported pre-start memory sample was 11.493 GiB. The
  exact pre-start sample used by the start command was not printed; do not
  relabel 11.493 GiB as that command's own measurement.
- The operator then reported the exact VM Running with zero network adapters.
  Post-start host free memory was 4.271 GiB. That observation remains valid;
  its interpretation as an 8 GiB floor failure was wrong.
- A direct host CIM observation at 13:15:59 UTC reported 31.568 GiB usable
  memory and 5.708 GiB free. It is an observation, not a failed post-start gate.
- The operator's exact-VM lookup reported fixed memory, 8 GiB assigned/startup
  and 1.6 GiB demand. The 0.5 GiB minimum and 1,024 GiB maximum do not mean
  dynamic memory is enabled or that the maximum is currently allocated.
- The known host SQL service was running, with 0.057 GiB working set and
  3.183 GiB private committed memory. These are different measures; no claim
  is made that stopping it would release 3.183 GiB of physical RAM. No SQL
  connection or service change occurred. A bounded read of twelve largest
  process working sets does not completely account for host/kernel memory.

The user need not close more applications or alter VM memory to satisfy the
invented conditions. The memory-only stop is removed. Remaining identity,
isolation, disk, active-producer, SQL-state, input-custody and cleanup checks
are still required under the already approved read-only packet. No installation,
replay, rehearsal, reset/restore, new input or larger allowance is authorized.
The 21-input allowance remains consumed.

## Custody and validation

All original failed access/setup/startup receipts and their historical findings
documents remain unchanged. They are evidence of what was observed and decided
at that time; this correction supersedes only the erroneous memory disposition.
The pre-correction readiness and scope-review documents are preserved byte for
byte as `original-plan-1.md` and `original-plan-2.md` under
`.codex_artifacts/p025/d5a2-memory-gate-correction/`, with SHA-256 values in
`correction-receipt.json`. Do not overwrite those originals or recast any failed
test/SQL 3961 evidence as passing.

This is a documentation/evidence correction only. Security routing: documented
skip for that delta; no runtime, SQL, permission, configuration or collector
implementation changed. Validate links, whitespace, original receipt/candidate
hash custody, architecture/deferred/security routing and explicit-path test
selection. Runtime tests and native SQL are not part of this correction.
