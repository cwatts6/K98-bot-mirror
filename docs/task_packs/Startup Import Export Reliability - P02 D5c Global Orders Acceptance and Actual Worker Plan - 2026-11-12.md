# P02 D5c global orders acceptance and actual worker plan - 2026-11-12

Status: global owner-first receipt accepted. The operator explicitly approved
the bounded actual-worker scope; first admission packet preparation is underway.
No new demand or worker invocation has run. D5c/d/e/f remain open. This document
is not an execution script or an assertion that the remaining runner is ready.

## Accepted result and remaining budget

Receipt `d5c-global-owner-first-result-f49ef04b1f224cca86b8b36126855568.json`
matches SHA256 `6D57F665DBB2E9876B9902EFDA12B36E4C8DAE67AF2A02A0CD3A39455ABFEC21`.
Independent local adjudication checked all 24 observations, pinned source hashes,
paired original protection/ownership/permissions/ledger/backup/session context,
resource gates and physical process/session cleanup. The global owner acquired
Exclusive before one managed reader entered SNAPSHOT with Shared schema ownership
and NoLock for the global resource. Fourteen reader acknowledgements ended in
rollback, isolation restoration and cursor/connection close. Owned release
returned 0/NoLock; PID 2160 joined normally with exit 0 and empty stderr. The
holder and reader births were distinct and both sessions were independently absent.

Actual wrapper counts: 24 statements/29 rows. Actual child: seven statements/six
rows. Reserved totals: 48 commands/41 rows. Full host elapsed 2.2047723 seconds
debits three, leaving **1,462 native seconds**, including 462 in the proposed
D5c allocation and the unchanged 1,000-second later-slice reserve. **21 inputs
remain consumed; zero new inputs.** The create-new acceptance record is
`.codex_artifacts/p025/d5c-global-owner-first-acceptance.json`.

Together with the preceding result this accepts both global guard/managed-reader
arrival orders. Full inspectors, account scope and actual maintenance overlap
are not proved by these two lock-only cases.

## Scope summary and affected areas

Next proposed addition: one labelled generation-2 `post_import` demand on the
existing disposable database, five bounded blocked-worker cases, and at most
one actual `post_import` child execution. Do not repeat D5b's six-child suite or
its consumed recovery retry. The copy is `K98_P025_D5b_20261111`, database ID 8,
creation time `2026-11-11 17:00:42.830`, on the existing isolated MINI_AMD VM.
The original database remains read-only/restricted and untouched.

All tooling stays in test scripts and private qualification artifacts. Reuse
the current managed reader and unchanged installed candidate procedures. No
Bot runtime, SQL repository, command/view, scheduler, ProcConfig, schema,
permission, ownership, VM resource or isolation changes are proposed. There is
no new generic lock framework, instrumentation or justified deferred refactor.

## Exact demand identity and compare-and-set

Label: `P02-D5c-post-import-generation-2`.
New request ID: `468fc60f-8424-4637-b576-99717c7ad062`.
There is exactly one admission attempt; finding that ID already present is an
uncertain/prior outcome to reconcile, never permission to advance again.

The prior full row is pinned by accepted remaining-readiness V2 receipt SHA256
`C822B1CA6CAEBA7AB16A6F1EAB55D46621AA0FF79A6BC1EAF24D9272AB2388DB`.
The latest accepted global-order receipt independently confirms its common
ledger fields. Before any write, re-read all 19 columns below and require exact
typed equality under a short transaction with UPDLOCK/HOLDLOCK and zero lock wait:

| Column | Exact expected value |
| --- | --- |
| Kind | post_import |
| DueGeneration | 1 |
| CompletedGeneration | 1 |
| KS4DueGeneration | 0 |
| KS4CompletedGeneration | 0 |
| DashboardDueGeneration | 0 |
| DashboardCompletedGeneration | 0 |
| SummaryDueGeneration | 0 |
| SummaryCompletedGeneration | 0 |
| ClaimedGeneration | 1 |
| ClaimID | 3e723a45-4471-424c-aacf-f0afeb85c748 |
| LastRequestID | 74abc842-4837-42c3-b330-65b2e1b0c300 |
| State | complete |
| DueUTC | 2026-11-11 17:55:17.791 |
| StartedUTC | 2026-11-11 19:26:05.426 |
| CompletedUTC | 2026-11-11 19:26:09.958 |
| FirstErrorNumber | 15247 |
| FirstErrorUTC | 2026-11-11 17:55:28.565 |
| LastErrorNumber | NULL |

Acquire the exact maintenance worker Session guard before that transaction.
Require no other pending/running work, unchanged five completed rows, unchanged
backup demand, ownership/permissions and candidate fingerprints. Persist and
flush create-new original-row, five-row, failure-lineage and request-intent
evidence before admission. Host and Q: copies must both be acknowledged before
the transaction may commit; a missing durable acknowledgement stops admission.

Within the transaction call unchanged `dbo.usp_MaintenanceDue` with
`@Kind='post_import'`, the exact new request ID and all three optional flags 0.
Require DueGeneration=2, CompletedGeneration=1, State=pending, the new
LastRequestID and DueUTC inside the captured SQL admission-time window. All
other columns must equal the original row, including ClaimID, StartedUTC,
CompletedUTC and both first-error fields. Check the five other rows and backup
demand unchanged before commit. Roll back only this owned transaction on a
confirmed failure; unknown commit/close stops all further work for adjudication.
Explicitly acknowledge release of the owned worker guard and physical closure.

The eventual new ClaimID is generated by the unchanged worker's NEWID(); do not
preassign or overwrite it. Capture its exact value with ClaimedGeneration=2,
require it differs from generation 1, and retain the old claim in the immutable
history receipt. The new request ID remains the durable generation label.

## Bounded execution sequence after scope approval

Prepare, test and review each hash-pinned packet before handing it to the same
authenticated operator console. Approval of this proposal is not permission to
run a draft or the historical fixtures. Adjudicate each receipt before proceeding.

1. Admit only the exact new demand above, then close all owned sessions. This
   packet runs no child. Keep generation 2 pending across subsequent reviewed
   checks; do not reset or recreate it if a check fails.
2. In fixed, separately recorded cases, hold each of the worker, global, delta
   and player Session guards, one at a time, then call the unchanged worker once
   for `post_import`. Require the pending row and old claim unchanged, no child
   entry, all worker-owned guards released, and closure. Test-owned holders are
   released only after the worker call finishes. These are four intentional
   no-child admission cases, not attempts to re-execute completed work.
3. Establish the real managed reader's Shared schema guard, then call the real
   worker once. Require the same pending row and no child entry, then acknowledge
   the reader's physical cleanup. This is the fifth blocked-worker case.
4. With no test holder present, launch the unchanged worker once. There may be
   at most one child entry for generation 2. Attempt one scheduled observation
   of its exact birth, request and owned guards while it runs; only if that
   observation establishes the phase may a fresh reader/contender test proceed.
   Reader entry during the actual schema holder must refuse with 51966 after
   clean rollback/close; fixed resource contenders must be refused by the exact
   observed worker. A missed scheduling window is **unexercised**, not a pass.
   No polling loop, artificial production pause, second demand or child rerun
   is authorized to obtain a preferred result.
5. Require completion of exactly generation 2/new claim, first error 15247 and
   original timestamp retained, five other completed rows/backup demand unchanged,
   expected statistics evidence and physical release/connection/process cleanup.
   A failure/unknown result is retained and stops dependent work without reset.

Exact fixed Session resources, in candidate acquisition order:

- `K98:post-import-stats:v1`
- `k98-legacy-output-snapshot`
- `K98:TargetPublication:DeltaPreprocessing`
- `K98:StatsForUpload:Publish`
- `K98:maintenance-schema:v1` (reader uses Shared/Transaction)

The source has no deterministic external pause after schema acquisition. Source
review therefore cannot promise that the single actual-child window will be
observed. Any unexercised worker-first row remains open; guard-only evidence must
not replace it. Counter evidence must retain cache identity and its preimage;
cache eviction/restart is not proof of zero executions. Use claim and physical
statistics evidence alongside counters, not counter totals alone.

## Limits, implementation gates and validation

Use at most five packets, each at most 60 seconds including cleanup: a worst-case
300-second allocation fits the 462-second proposed D5c balance. Debit actual
rounded-up host times, including refusals and failures, with no refund/reset.
Stop before a packet if its whole ceiling cannot fit the remaining allocation.
The original 1,800-second cap and later 1,000-second reserve remain unchanged.

Every packet must statically enumerate at most 48 client-command units, at most
512 rows per result/2,048 total, a one-MiB receipt, at most two actors plus one
observer, fixed disk/log/version-store reserves and 8-GiB/four-CPU/zero-NIC VM.
An overlapping .NET metadata connection counts toward that same three-session
ceiling. Use existing statement/work/cleanup bounds; do not lengthen a timeout
to make a failing workload pass. Packet preparation must prove these counts
before any console handoff. Split read-only metadata across the five packets
when needed; do not drop required pre/poststate or closure checks.

Validate the complete affected packet path: exact-row drift/null/timestamp and
duplicate-request refusal, rollback and lost-commit acknowledgement, no worker
call before durable admission, each refused guard, reader cleanup uncertainty,
one child limit, first-error retention, counter-cache ambiguity, scheduling miss,
all five other claims, backup non-dispatch and physical cleanup. Use isolated
fake-driver/offline PS5.1 checks; no native fixture bootstrap or app startup.
Preserve all failures before corrections. Source-only packet fixes do not qualify
native overlap; any demonstrated production defect needs its own correction plan.

Authoritative source read: `dbo.MaintenanceWork.Table.sql`,
`dbo.usp_MaintenanceDue.StoredProcedure.sql`,
`dbo.usp_RunMaintenance.StoredProcedure.sql` and
`dbo.usp_MaintenancePostImport.StoredProcedure.sql` under the SQL repository's
`sql_schema`. All columns/flags/guards/claim generation and owner-executed
statistics behavior above follow those definitions. Existing D5b .NET execution
and physical cleanup patterns are design inputs, not scripts to rerun.

Security routing for this acceptance/plan-only update: documented skip. No
executable, permission, configuration, SQL or runtime behavior changes. The
future SQL-access/process packet requires Changes review of its exact Bot delta,
Deep off; SQL source remains read-only and has no patch target. Architecture,
deferred/routing and explicit-path test-selection checks apply to these docs;
runtime tests are skipped because this turn changes evidence and planning only.
Checks completed: architecture (zero changed Python files), deferred validation
(two Markdown files), security routing (zero errors/warnings) and explicit-path
test selection. The selector's application smoke, command registration and
release/native test suggestions are skipped: no executable/application/release
change occurred and those suites exceed this source-only scope. Local introduced
links, whitespace and acceptance-artifact existence were also checked.
No promotion guide/deployment workflow applies. Diagnostic evidence boundaries
follow the diagnostics runbook; no new public message or health probe is added.

## Decision and remaining D5 scope

This needs a specific scope addition because the accepted D5c source plan
explicitly reserved new maintenance demand for approval and preserved the
completed D5b claims. The requested addition is one generation-2 demand, five
no-child worker admission calls and one possible actual child execution, with
the one scheduling observation described above. It grants no permission or
isolation exception and authorizes no import/report/backup/provider work.

Synthetic season/queue/action-time rows, restricted-user authentication and
SNAPSHOT-disabled native proof still require their own feasible concrete plans;
they are not included here. Windows pipe/file tests and D5d/e/f remain open.
Completing the above sequence alone does not complete D5c or authorize D6.
