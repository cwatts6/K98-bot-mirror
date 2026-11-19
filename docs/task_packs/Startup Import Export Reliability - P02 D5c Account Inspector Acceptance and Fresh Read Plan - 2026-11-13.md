# P02 D5c account inspector acceptance and fresh-read plan

## Accepted account-lock result

Receipt `d5c-stats-account-owner-result-047df896007b45c0bd26ae9eedacf334.json`
has SHA256 `1a5ace0bbdd03f523346d0db200cd1825b5a6bb9f6ffd55e1b5b8c149510e578`.
It is accepted: the actual Stats inspector observed global availability one,
then exact account availability zero, raised `ImportExecutionActive` and closed
its reader. The holder remained exclusive until its owned rollback and closure.
The process exited normally and independent session-absence checks passed.

Both preservation observations agree on all eleven fixture rows, original
failure history, completed maintenance, permissions, ownership, candidate
definitions and statistics. Removed accounts remain absent. The original
database remains protected. Forty-eight operations and 109 returned rows were
recorded, without errors or forced termination.

Host elapsed time 1.6155187 seconds is charged as two seconds. The acceptance
record is `d5c-stats-account-owner-acceptance.json`. There are 1,355 native seconds
remaining, including the protected 1,000-second later-phase reserve, and 50
Windows-test seconds. Eleven of 64 synthetic rows and all 21 retained inputs
remain consumed. Neither accepted owner-first attempt may repeat.

## Next distinct observation

Run the full unchanged `StatsImportOutcomeDAL.inspect` once on a fresh managed
connection, after the accepted global and account holders have closed. The
exact same labelled pending preparation is read. No exclusive holder is created
and no action is invoked. All three actual availability hints must equal one:
global, account and the exact preparation's import guard.

The resulting snapshot must contain every approved preparation value, no
execution receipt, no resource reservation, `captured=False`, and action `hold`
with the exact missing-execution explanation. Free locks never establish a
successful or safely abandoned historical execution. This packet does not
promote missing evidence into a recovery action.

The returned evidence token is checked against the captured raw token document.
The raw document is retained before driver representations are normalized for
cross-process comparisons. UUID spelling is normalized through UUID parsing;
32-byte hashes become lowercase hex; naive datetime2 values use ISO timestamps
at millisecond precision. Other types and every value must match the pinned
proposal exactly. No production normalization or inspector behavior is changed.

The real snapshot profile must acknowledge rollback, isolation restoration and
physical closure. Unknown cleanup fails the packet. The process must exit
normally and the independent observer must find no matching work or actor
sessions. Presence of any other copy session fails both preservation gates.

## Bounds and preservation

The packet reserves 43 client operations: 21 metadata, six outer control and
cancellation operations, and 16 reader operations (eight SQL calls, five rows).
The original 48-operation cap is unchanged. Planned rows are 110 under the same
2,048-row cap. The manifest is 130,713 bytes under 131,072; the 1 MiB receipt,
fixed VM, 60-second packet, 20-second actor watchdog, source expansion limits,
disk/log/version-store reserves and one-attempt intent remain unchanged.

No new input or fixture row, data/permission/isolation change, import, report,
maintenance, backup, provider request or recovery mutation is included. All
original receipt and source pins remain intact. The SQL schema and production
modules are unchanged. The two accepted holder receipts are lineage prerequisites.

## Offline checks and review

Ten isolated Python tests passed using the full bundled actual inspector and
inert connections. They cover the honest hold, each busy guard, wrong scope,
changed row, UUID representation, cleanup uncertainty, native failure causes,
source pins, forbidden exclusive-lock/write SQL and strict normalization types.
236 PowerShell 5.1 checks passed for parsing, remoting, exact pins, snapshot/token
evidence, false results, custody, preservation and all numeric gates.

Initial source preparation exceeded the manifest cap by 32 bytes and stopped
before writing an execution manifest. The unused holder-only constants were
removed from this fresh-reader test actor; no limit was raised. The initial
actor is retained as `d5c-stats-fresh-pre-size-correction.py`. No native attempt
occurred. Neither the prior scripts nor the application runtime were edited.

Route security review to Changes on the immutable seven-file packet, Deep off.
Independent review must complete before console handoff. Run repository
validators and explicit test selection. Broad application imports, command
registration, full pytest and release tests remain outside this isolated
qualification pass; it makes no runtime or deployment change.

This is the fresh-after-release full Stats case only. Other inspector routes
and reader-first ordering, remaining C04/C05/C06/C09 work, D5d physical failure
coverage, D5e and D5f remain open. D5a/D5b remain accepted. D6 production
deployment remains separate and unauthorized.
