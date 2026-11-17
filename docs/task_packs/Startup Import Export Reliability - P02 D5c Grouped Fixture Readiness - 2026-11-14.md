# D5c grouped read-only fixture readiness

Prepare one operator handoff for the shared-state and schema prerequisites of
C04/C05/C06. Existing approval covers this bounded read-only collection. It creates
no fixture, permission, isolation, VM, production or application-data change and
does not execute Python, a recovery action or a business workload.

The collector uses the existing elevated Windows PowerShell 5.1 console on
9SX2VF4 and its D5cResume PSSession (instance
0273a292-0961-4cda-bbce-15de9eaead0e). The exact isolated VM, MINI_AMD guest,
K98_P025_D5b_20261111 copy, integrated login, original read-only database, Q: volume,
resources and connection-birth cleanup gates remain pinned. No new authentication
or connection fallback is provided. A changed/missing session stops before SQL.

## One grouped collection

1. Recheck identity, resources, unchanged candidate/maintenance/backup/permission
   state, all eleven accepted fixture rows and absence of the removed test accounts.
2. Read the canonical sql_snapshot:legacy_outputs resource and its exact producer
   blockers, without changing the resource key or excluding foreign owners. Read
   the global active-stream count used by the original hold guard.
3. Read columns/defaults, outgoing foreign-key columns and check constraints for
   31 fixed tables supporting season/routing/weights and queue/pool/hold fixtures.
   Foreign references outside that set are named. Return disabled/untrusted status
   for adjudication. Historical column order is evidence, not an automatic mismatch.
4. Reread shared state and protected records; require stability. Dispose the work
   connection, then verify its recorded birth is absent with the cleanup observer.

These are separate bounded read-committed observations, not an atomic snapshot or
a proof of future quietness. A stable count does not prove stream membership was
unchanged; this count is planning evidence only. Native fixture admission still
requires exact identities/preimages and its own reviewed guards. Readiness is not
a successful overlap or effectful-recovery test. Existing canonical retained rows
must not be modified on the strength of this receipt alone.

## Bounds and preservation

There are 35 SQL statements plus six reserved controls (two opens, two closes and
two cancellations): 41 of 48 client operations. Maximum returned rows are 1,781 of
2,048, with no query exceeding 512. The scoped catalog caps are 384 KVK columns,
256 dbo columns, 512 foreign-key columns, 256 checks and 32 table records. Static
source has 277 and 110 respective columns. TOP(cap+1) is an overflow sentinel;
the reader throws on the extra row instead of accepting truncated evidence.

Query timeout remains three seconds. Work admission ends at 30 seconds; cleanup
admission at 42. Host cancellation starts at 45 seconds and joins for up to ten.
The full handoff has a 60-second ceiling; uncertain jobs/objects remain in custody,
and dependent work stops. No forced SQL-session termination, process kill, retry,
new VM session, table cleanup or setting adjustment is allowed.

The 89,626-byte manifest fits the existing 128 KiB ceiling. Receipt remains capped
at 1 MiB (guest payload at 900,000 bytes), with a separate small create-new intent.
No prior six-inspector batch size/operation extension is inherited. Balances before
execution: 1,305 native seconds including 1,000 protected later-stage seconds;
50 Windows-test seconds; eleven of 64 synthetic rows; 21 inputs consumed, zero new.
Charge the full reported host duration rounded up. No extension is needed here.

The generator validates the earlier collector and manifest hashes, the accepted
six-inspector batch and final child receipt, and imports the current preservation
query and expected values from that exact accepted chain. It pins 31 authoritative
SQL source files and all prior lineage. It removes unrelated Python/ODBC registry
enumeration from this collector. Existing SQL helpers, session-context checks,
deadline, cancellation and custody behavior are retained unchanged.

## Validation and review

The offline validator parses the complete PowerShell 5.1 collector, compares its
reused helpers and protected queries, rehashes lineage/schema pins, validates the
exact ledger, exercises actual comparison clauses with remoted-shaped evidence,
and rejects altered fixture/account/session counts and missing catalog tables.
It exercises the original row reader with an inert DataTableReader, including row
overflow/cancellation/disposal and operation exhaustion before command creation.
It invokes no collector, SQL, VM, application startup or external service.

Two validator-only failures are retained under
`d5c-grouped-readiness-offline-failure-1.json` and `-2.json`, with the exact failed
test files. The first correction removes exactly the outer AST braces; the second
prevents a ScriptMethod from enumerating its fake reader. Neither changed the
collector. The corrected offline pass completed 374 checks. These parser/fake
results do not claim native SQL or physical cleanup success.

Security routing is Changes, Deep off, covering the collector, validator,
preparer, execution manifest and this plan. Complete that independent review before
operator execution. No SQL repository edit is included. Source object names and
queried business columns were checked against C:\K98-bot-SQL-Server; sys catalog
queries do not infer application schema from Python usage.

The test selector would recommend broad pytest for changed tests plus startup
imports. Those are replaced here by the bounded offline validator; application
startup is outside this qualification packet. Full pytest, smoke imports and
PR-wide architecture/deferred/security-routing gates remain deferred to an actual
PR handoff. No runtime refactor, helper relocation or deferred optimization is
introduced. Reused code is intentionally preserved in this immutable qualification
packet so earlier scripts and evidence remain intact.

Only after reviewed native receipt adjudication may exact new fixture identities
and the complete setup/test sequence be finalized. Keep continuing the remaining
offline final-action groups independently. D5c remains open; this readiness step
closes no concurrency or effectful-action obligation by itself.
