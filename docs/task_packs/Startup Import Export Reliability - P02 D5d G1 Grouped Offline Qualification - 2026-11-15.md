# P02 D5d G1 grouped offline qualification

15 November 2026. Existing operator approval covers preparation, tests, review and
bounded offline execution. Native work remains an operator-console handoff after
complete packet review. D5a/b/c stay accepted; D5c has zero remaining checks.

## Frozen scope before execution

Four work groups remain: G1 offline custody; G2 native cancellation/physical release;
G3 maintenance/transaction uncertainty; G4 restart/lost acknowledgement. This is
not a native-case denominator. G1 has **47 behavioral cases**, separately from
**11 runner controls**. The exact expanded identifiers and preserved source hashes
are in the create-new G1 packet. No whole test module runs.

| Selection | Cases | Inherited obligation and observable pass condition |
| --- | ---: | --- |
| Threaded SQL setup | 4 | Pending close gates admission without locking observers; late setup cannot escape an uncertain hold; concurrent success/failure keeps each exact handle. These were explicitly excluded from the accepted 38-case packet. |
| Observation dispatch and request handles | 14 | Interrupted launch retains its worker; lost reply never replays; failures preserve original errors and close transferred handles; deadlines retain capacity; pending requests dispatch only after original cleanup; each owned handle is attempted and unconfirmed IO prevents close. |
| Checkpoint lifecycle and receipt binding | 13 | Rollback/close/commit uncertainty cannot authorize retry; ordinary producer transactions do not inherit metadata retries; completed receipt fields must match before CAS; externally owned cursor is neither reopened nor retried. |
| Nested custody | 16 | Exact connection identity, player/capture inner failure fencing, writer guard entry/exit, retained child resources, unknown commit as primary failure and raw inner holds survive outer cleanup. |

Accepted 42 drain checks and 38 custody checks (31 behavioral, seven controls)
are carried unchanged. D5c scheduling, route/admission and factory evidence is
reused: this group does not repeat the 73 routes, 25 inspectors or 18 final native
checks. Some primitives also appeared in broader D5c schedules; G1 qualifies the
distinct failure injection/cleanup ordering, not another route or family pass.
Synthetic birth/restart selections from `test_export_child_restart.py` stay with
G4's physical restart work; none is silently counted as G1 or native acceptance.

## Architecture and boundaries

The new runner reuses `Runner`, source-body selection, import refusal, audit hooks,
bounded output and create-new receipt writing from the accepted custody runner.
It permits only the selected observation-worker and thread-pool targets, at most
two concurrent workers and 32 starts. Per-case completion requires no live owned
threads. Test-owned failed handles remain strongly referenced to process exit.
Only synthetic module registries are reset between independent cases.

No production source, original tests or SQL definitions change. Actual service,
DAL, transaction, custody, writer and checkpoint bodies are loaded without module
startup or broad autouse fixtures. Original assertions are retained. The original
writer fixture uses an inert path/store constructor; it does not establish real
file durability. Diagnostic transport is inert. SQL connections, statements and
commit effects are doubles; native physical closure remains G2-G4.

The unsafe shared-clock fixture is not changed or called. A test-owned facade is
injected only into the selected contention module; the real watchdog clock is
captured independently. No new production helper or monitoring framework exists.

Source validation checked authoritative `dbo.StatsImportExecution` receipt fields
and state/ownership semantics in the SQL repository. Labelled partial rows cover
consumed fields only and are not valid insertion fixtures or new SQL rows.

## Bounds, preservation and review

Each preparation/qualification process has a 300-second watchdog and 1 MiB receipt
ceiling, with captured output capped at 16 KiB. No network, real driver, provider,
VM, native child, credential loading or writes outside its fresh intent/result
files are allowed. Case failure or unexpected boundary attempt stops the batch.
Missing final receipt is uncertainty, never a pass or permission to repeat.

The handover checkpoint's six evidence pins, five tracked-source pins and both
repository HEADs matched. Accepted drain candidate hashes are retained. Existing
receipts, source and the ordinary index are pinned; the retained VHDX is excluded
from content hashing and remains outside all write permissions of the runner.

Preparation history is preserved. The first manifest-generation command selected
the retained VHDX for a read-only hash by mistake and was interrupted; it produced
no packet or intent. An early runner launch consequently refused the absent packet
before any test. The second manifest selection is limited to source and bounded
text evidence. No qualification case, native time, input or row was consumed.

Security decision: **Changes review**, Deep off, exact new G1 executable delta
and directly supporting code. Unchanged accepted source must not be rescanned as
a new codebase audit. SQL has no delta and receives a documented no-change skip.
Preparation controls validate startup, original fixture construction, imports,
clock isolation, refused effects and receipt serialization before qualification.
Final review must account for both new Python files before execution.

Full pytest, application import smoke and command registration are intentionally
not run: no production registration/import behavior changes, and broad startup
would exceed the selected offline boundary and replay accepted evidence. Run
architecture, deferred-item, test-selector and security-routing gates; retain
lint and exact guarded runner results. No deferred optimisation is introduced.

## Allowances and remaining path

No native allocation is consumed by G1. Balances remain 1,248 native seconds,
including 1,000 reserved for later D5; 50 Windows-test seconds; 21 consumed inputs;
67 consumed synthetic SQL rows. Preparatory local Python controls are offline
qualification, not Windows-native tests. Any extension must be concrete and
recorded before use. G2-G4 and D5e/f need a joint native allocation before handoff.

The last operator session cannot be inspected from this process. A future reviewed
native packet must validate its availability, exact VM/database identities and
prior fixture state before dispatch. No reconnection is requested speculatively.
D6 deployment remains separate. P03 actual blockers and essential P04 corrections
still precede first normal import/export; offline success is not installation or
live provider acceptance.
