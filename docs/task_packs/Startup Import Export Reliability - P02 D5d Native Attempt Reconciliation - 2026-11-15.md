# D5d native attempt reconciliation and grouped read-only continuation

The approved grouped packet stopped before admitting its first behavioral case.
The saved receipt `d5d-grouped-result-54e952ab1ce24ce1bb05fd5375552255.json` has the
operator-reported SHA-256
`6501040b7c79953d81a0db6bca9419bcba1321c3ad9996c3dade64fbd09eb40e`.
The original packet, runner, intent, approval and preparation receipt remain
unchanged. No old intent is removed and no failed packet is rerun.

## Authoritative outcome and limits

The guest reported `Exact contained actor absent`. In the pinned runner this
occurs after assigning the first child handle to its owned job, when the active
process count is not one, and before publishing `assigned.gate`. The actor cannot
load its native driver or begin the case before that gate. Root cause of early
child exit or the observed job count is not yet established; its retained stderr,
stdout and guest result must be read before preparing a continuation.

Database `K98_P025_D5d_Fault_20261115` was created as ID 10, birth
`2026-11-15 10:31:04.697`. Its birth was recorded after all fixed SQL setup batches
returned successfully. Those authoritative setup batches attempt eight seed rows:
six MaintenanceWork, one MaintenanceConfigurationWork and one MaintenanceBackupWork.
MaintenanceKvkWork and both marker tables begin empty. Thus 75 rows are accounted
as attempted (67 prior plus eight setup), with eight of the approved 83 still
reserved for unfinished effects/transaction cases. Do not reset or recreate these
seeds. Actual retained values/counts remain to be checked independently before use.

Host elapsed time was 1.5584001 seconds; the packet charged its ceiling, two
seconds, leaving a recorded 1,246 seconds. Guest elapsed was 0.8013184 seconds.
Windows subgroup time was zero, leaving 50 seconds. The protected later-phase
reserve remains 1,000 seconds; inputs remain 21 consumed and zero new.

The original observer closure check returned true. The receipt's `closed=false`
also reflects the case error, rather than establishing an active owner. Conversely,
that observer flag does not establish post-failure preservation or every custody
boundary. Poststate `preserved=false`, missing final fixture counts and absent
per-case cleanup evidence prevent native acceptance. The recorded time debit is
carried forward while the grouped read-only check resolves outstanding poststate
and ownership evidence. No claim of healthy whole-flow operation is made.

## Running test totals

| Behavioral tranche | Expected | Accepted | Pending |
| --- | ---: | ---: | ---: |
| G1 | 47 | 47 | 0 |
| G2 native | 11 | 0 | 11 |
| G3 native | 9 | 0 | 9 |
| G4 native | 4 | 0 | 4 |
| G4 original offline restart variants | 21 | 0 | 21 |
| **Total** | **92** | **47** | **45** |

There is one failed native packet attempt, zero completed native cases and no
accepted test replay. Preparation counts remain separate: original 12 Python
groups and 45 PowerShell controls; the new diagnostic has 22 passing offline
PowerShell controls initially, increased to 26 after the closure-refusal correction.
Diagnostic observations are not added to the behavioral
denominator. The 21 original restart variants remain pending and are not silently
treated as covered by the native named-job case or by preparation controls.

## Next grouped packet

`scripts/observe_p02_d5d_grouped_failure.ps1` is a one-shot read-only collector.
It reads six exact retained files, including the first child's stderr/stdout and
assignment gate; records Python owners without terminating anything; checks old
SQL observer births and application identities; reads the six new fixture tables;
and compares all 63 pinned original preservation queries. It uses the same exact
borrowed session, VM/volume and database identities. The retained original and
disposable databases are not changed. It records its own observers and verifies
their closure independently, with the final collector close acknowledgement
identified separately.

The new intent and host receipt have distinct names. The old runner is loaded
only as pinned text to extract the already reviewed Canon/Same comparison bodies;
its execution body is never invoked. Fixed preservation query text comes only
from the hash-pinned original manifest. No DDL, fixture write, actor launch,
privilege change, process termination, cleanup deletion or database recreation is
included. No extra database, rows or input allowance is needed.

Reserve up to 15 native seconds within the recorded 1,246-second balance, leaving
1,231 seconds if the whole reservation is charged; the 1,000-second later reserve
is protected. No Windows subgroup case runs. If the diagnostic cannot establish
closure, its job and full reservation remain for reconciliation, not retry.
Following its receipt, recompute the remaining allowance and prepare a continuation
only for verified unfinished stages, using the existing DB10 and seeds if valid.

## Review and validation

Scope is limited to the read-only diagnostic and its controls. No application or
authoritative SQL source changes. Required decision: Changes security review of
two new PowerShell files, Deep off, base `78f96e125b95e09ae2f8d2e4549cec086f2d3910`
to `f55a77000a7258322b4f0a629db600a6518b4b91`, scan
`d9ec5be1-dcd8-46a4-8332-c208c9880225` completed with no reportable vulnerability.
Its correctness review required avoiding an unnecessary SQL collector after a
pre-SQL refusal, and retaining closure unknown if any opened observer lacks its
exact birth. The corrected snapshot is `62c174ad5f5edb0a76e6f35d266797b105449424`,
reviewed separately from `f55a7700` in Changes scan
`10c9d9b9-9ab0-4692-ad19-5b29ee088d18`, completed with full two-file delta coverage,
zero reportable vulnerabilities and no remaining concrete handoff blocker.
Final diagnostic runner SHA-256:
`ea60028ac5281665d2f4e92e72513c9797366152fa760a8bb63761867197adec`.
Latest 26-control output is retained at
`.codex_artifacts/p025/d5d-diagnostic-controls-final.txt`.

Tool-reported aggregate review counters: initial diagnostic 1,999,954 total tokens
(1,982,208 cached input), final delta 1,461,783 (1,455,616 cached input). These
rollout counters are not incremental billing, additive estimates or native time.

Offline controls exercise exact hash refusal, bounded file reads, missing evidence,
one-shot receipt preservation, duration/row/operation limits, one-row shape,
parameter binding and reader/command cleanup on success and failure. They do not
connect to SQL or the VM. Broad pytest, registration/smoke and release gates are
not repeated for this collector-only change; earlier accepted schedules must not
replay. Architecture, deferred-item, security-routing and explicit-path selection
remain the documentation/tooling gates. No unrelated refactor or deferred item is
introduced.
