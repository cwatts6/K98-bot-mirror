# P02 D5e measured launch refusal and grouped continuation

## Receipt and reconciliation

The saved receipt `d5e-measured-cost-result-ccb9d8302acc4f9180f58b48e732ea91.json`
matches SHA256 `6a8aba7515f5c6b341ea2165c1ca0fb0638ec3c15fe36691396cf91908f9e4d3`.
The error is `Exact actor launch contract`, thrown by the retained D5d C# helper
because its working-directory guard admits only `Q:\D5dContinuation-20261115`.
The measured wrapper supplied `Q:\D5eMeasured-20261115`. This guard executes
before CreateProcessW. No process launch record, actor output, measured arm or
row attempt exists in the receipt. The owned empty job and all SQL observers
closed; elapsed time 0.5586983 seconds charges one native second.

This was a packet preparation defect: the earlier review followed job ownership
and cleanup but missed the inherited launcher's exact directory contract. The
new tests compile the actual C# source under Windows PowerShell 5.1, reproduce
the old refusal, and pass the exact new wrapper command through the same guard
that the new Start method invokes before native creation. A syntax-only or
text-presence test is not sufficient evidence for a reused launch contract.

| Accounting | Completed / expected or remaining |
| --- | --- |
| Fixed accepted checks | 100 / 100 |
| Binding checks | 3 / 8 |
| Cost arms | 0 / 12 |
| Native acceptance total | **103 / 120** |
| Setup, separately tracked | 1 / 1 |
| New offline continuation controls | **47 / 47** (4 Python, 43 PowerShell) |
| Native time remaining | **986 seconds** |
| Windows fault time remaining | **49 seconds** |
| Synthetic row attempts | **83 / 95 used; 12 remain** |
| New database / backup allowances | **0 / 0 remain** |

The previous 35/35 preparation controls remain preserved as historical evidence;
they did not cover this launcher contract and are not new native passes. The
earlier 21-input allowance remains consumed. No accepted work was replayed.

## Scope and continuation

The continuation has a new host intent, receipt prefix and private guest folder,
`Q:\D5eMeasuredContinuation-20261115`. The prior intent, receipt, payload, actor,
private directory and all accepted evidence remain untouched. Before launch it
requires exactly the old packet.json and actor.py with their original hashes;
any extra entry, including a started-arm directory, stops continuation. It also
checks the previous exact application and collector SQL births are absent.

The dedicated C# types D5eCostContinuationActor and D5eCostContinuationJob retain
the earlier exact executable, suspended creation, no inherited handles, no
visible window, job assignment, token/birth/membership checks, bounded waits,
exact-handle termination and physical closure behavior. Only the dedicated
type names and exact new working directory change. A side-effect-free guard
is shared by Start and the offline control. Empty commands are rejected. Existing
loaded continuation types are refused, so a stale assembly cannot be reused.
The original D5d helper is neither weakened nor overwritten.

The Python measured actor remains byte-for-byte unchanged. Payload differences
are restricted to the reconciled native balance, new directory, prior-unentered
proof and additional preservation pins. All twelve request IDs, five balanced
measured pairs, warmups, fresh demand generations, 57 output bindings, clock/tie
policy, real diagnostics, physical branch checks and cost thresholds are frozen
from the reviewed measured packet. Five binding groups and twelve arms remain
grouped in one operator invocation. Starting these unentered arms is not replay
of accepted or entered work; the guard must prove that distinction first.

The reservation stays **600 native seconds, zero Windows seconds and at most
12 row attempts**. At maximum planned consumption **386 native seconds** remain,
above the retained 185-second D5f minimum. No database, backup, input, storage or
time extension is needed. Unknown ownership/output retains the original full
reservation and conservative row accounting. There is no automatic retry.

Review also identified two inherited failure-path gaps before handoff. Empty-job
close now stores its exact handle in guest custody before attempting close and
clears custody only on success. Row accounting separately reports observed and
reserved attempts: all twelve remain reserved whenever actor closure is unknown,
even if a partial guest receipt exists. Verified closure alone allows the
unstarted row allowance to remain available. Fault-injection controls cover both
conditions without closing native handles or running an actor.

## Validation and review

Tests exercise real C# compilation and both directory contracts, exact command
construction using the actual caller's AST-derived directory and executable,
wrong executable/path/hash/application/command length refusal,
stale-helper refusal, prior file identity and entered-work rejection, old SQL
owner refusal, create-only receipts, receipt-hash adjudication, payload equality
and all prior handoff pins. No child process, SQL connection or VM workload is
created by these controls. Native CreateProcessW success in the guest is still
operator evidence, not an offline claim.

Changes stay in operational tooling, tests and this addendum. All SQL objects,
candidate modules, application callers and deployment state are unchanged and
remain pinned to the authoritative sources. No unrelated refactor is included;
new wrapper/type names are necessary to preserve immutable accepted evidence.
Required architecture, deferred-item and security-routing validators and test
selection run. Full application pytest, imports and Discord registration are
skipped because no application runtime or command registration changed. The
security review is Changes for the exact continuation-only immutable range,
with Deep off. The final handoff record supplies hashes and review outcome.
