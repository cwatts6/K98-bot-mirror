# D5c grouped final settlement safeguards

Scope: offline qualification of stats_import/release_failure,
stats_import/supersede_partial and unreceipted_producer/retain_unknown. Existing
approval covers preparation, narrow Changes review and the bounded pass. No
production code, input, native SQL or VM operation is included.

Original service classes, StatsImportOutcomeDAL, UnreceiptedProducerDAL and the
legacy capture-session owner execute against an inert SQL transport. Original
snapshot, scope, action, token, row mapping, identity, digest, bounded JSON,
mutex and compare-and-set bodies remain intact. The legacy path also uses the
original session acquisition/release and custody bodies. A deterministic fake
database validates exact arguments, records update attempts and models rollback;
it cannot establish SQL Server atomicity or real physical lock exclusion.

Each of the two stats routes has 39 scenarios. The legacy route has 43, followed
by the aggregate ledger's seven runner safety controls: 128 cases in one pass.
Cases cover valid settlement, changed versions/fences/owners, foreign scope,
missing or conflicting receipts/resources, active producers, lost update races,
bounded reasons, known/current/stale reconciliation and malformed legacy markers.
No original import or provider operation can dispatch. Original error fields,
input identity and unknown-outcome meaning must remain unchanged. Structural
refusal cases use a newly matching token so the final guard is reached.

Applicability: stats settlement relies on its exact SQL execution receipt rather
than the legacy request hash. Legacy disposition verifies request identity and
rejects stronger typed checkpoints. Stats reconciliation intentionally accepts an
equivalent existing settlement, including an automatic observer's disposition;
it does not require the same actor. Legacy reconciliation requires its exact
action/token marker. These distinct contracts are asserted without weakening them.
The missing/invalid tuple tests are offline defensive cases; no foreign key or
constraint is disabled to create them in SQL.

The SQL source-of-truth definitions for ExportPreparation, ExportResource,
StatsImportExecution and ExportExecutionStream were inspected and are pinned.
No schema/procedure/config migration or runtime refactor is proposed. Reuse the
reviewed offline runner; create new packet/intent/result paths and preserve all
prior source/evidence hashes, including the previous 93-case acceptance.

Limits remain 300 seconds and 1 MiB combined intent/result, first-failure stop,
one frozen pass with no automatic replay. Any corrected run uses a new packet
under the existing explicit additional-pass approval, retaining original failure.
Balances stay 1,305 native seconds including the 1,000-second reserve, 50 Windows
seconds, 11/64 synthetic rows and 21 consumed inputs. No extension is needed.

Security routing: Changes review of this test file, runner, preparer, packet and
plan only, with Deep off. Supporting original code is inspected for accurate
guard coverage. Compile the entire pinned dependency closure under the execution
read/import guards before review and the qualifying pass. Original Python helper
definitions execute; module startup and application imports remain excluded.

The selected tests replace the selector's broad pytest recommendation for this
bounded qualification, since application startup and unrelated workloads are
outside this group. Full pytest, smoke imports and PR-wide validators remain
deferred to an actual PR handoff. Review and tests are separate gates. No
production helper duplication, runtime change or deferred optimisation is added.

Acceptance requires exact case ordering/outcomes, preserved hashes, seven expected
boundary refusals, no extra tasks/threads, inert transaction restoration and exact
cursor/session-close accounting. Physical cleanup, native races, commit loss and
crash custody remain separate. This group can accept only its three named final
routes, not the other 66 routes or C04/C05/C06 as complete.
