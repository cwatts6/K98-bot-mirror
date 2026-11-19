# P02 D5e readiness acceptance and bounded cost extension

## Receipt accepted

`d5e-grouped-readiness-result-dc38f3d9df604427a4852a4fd5f9f7c0.json` matches SHA-256
`be2c91bfb87b792e770ff3176802e9df5f92fb97aecb399a0744cd41143a17f2`.
All seven readiness groups passed. Both error lists are empty; exact collector
births closed and final disposal was acknowledged. Accepted database identities,
all 27 retained file observations, D5d fixture rows and source preservation match.
The SQL compiler described `[RowCount]` and `[backup]` as bigint; the actual count
SELECT returned 6 and 1. No native behavioural case or cost arm was replayed.

Seven actual maintenance/dispatcher definitions were compared to their owning
SQL-repository procedure files. Only the declared leading DDL header and transport
line endings/final batch terminator were accounted for; full remaining bodies
matched. Raw receipt and source files remain retained. This comparison is distinct
from blindly trusting an observed catalog body.

The host adjudication is retained in
`.codex_artifacts/p025/d5e-readiness-acceptance-20261115.json`.
Elapsed host time 0.5092877 seconds is charged as **one native second**.

| Scope | Completed | Expected |
| --- | ---: | ---: |
| Accepted D5d behavioural cases | 92 | 92 |
| Accepted D5d final accounting | 1 | 1 |
| Accepted D5e readiness checks | 7 | 7 |
| **Accepted fixed subtotal** | **100** | **100** |
| Proposed fresh cost arms, including two warmups | 0 | 12 |
| **Subtotal including proposed cost arms** | **100** | **112** |

Copy setup acceptance and offline preparation controls are tracked separately,
not added to the behavioural denominator. D5e cost acceptance and D5f closeout
remain open; the table does not invent a denominator for the whole programme.

## Remaining allowances and observed resources

Native allowance is **1,235 seconds**, Windows **49 seconds**. Synthetic row
attempts are **83/83 used**, zero available; the consumed 21-input allowance is
unchanged. The earlier one-database extension was consumed by the preserved D5d
database. There is no unused approval for this next copy.

Readiness observed Q: free 177,607,409,664 bytes (about 165.4 GiB), guest C: free
11,299,643,392 bytes, and host C: free 1,324,913,381,376 bytes. The D5b source has
18,239,979,520 data bytes and 68,719,476,736 log bytes, about 81.0 GiB allocated.
Log use is 2.60624313%; version store is zero. These observations are not future
capacity guarantees; the packet rechecks them before and during work.

## Exact extension requested

Authorize only:

1. **One fresh database**, `K98_P025_D5e_Cost_20261115`, copied once from the
   accepted `K98_P025_D5b_20261111` (ID 8, birth `2026-11-11 17:00:42.830`).
   This explicitly authorizes the retained-data copy, including inherited fixture
   rows, without treating it as a new imported input or new synthetic INSERT.
2. **One retained COPY_ONLY/CHECKSUM backup**, under the new
   `Q:\D5eCost-20261115` directory, capped at 32 GiB. Normal SQL backup-history
   metadata is permitted. No maintenance backup job is dispatched.
3. **Twelve additional test-created log-row attempts**, raising the synthetic
   ceiling **83 â†’ 95**, one actual `DeltaProcessingLog` insert for each fresh
   warmup/measured configuration child. Count failed attempts too. No extra
   manual fixture INSERT, new uploaded input or retry is included.
4. Qualification-only fresh demand generations and twelve fresh committed report/
   maintenance trials **inside the new cost copy only**, as described below.
   Accepted databases 7/8/9/10, original claims, receipts and consumed intents are
   preserved. Derived report rows produced by the actual report procedures are
   workload output, not twelve invented import completions.

No time, Windows, VM memory/CPU, disk-size, permission or production extension is
requested. Allocate **450 seconds maximum for setup** and **600 for the grouped
measurement packet** from the existing 1,235. At both maxima, **185 seconds remain
for D5f**. This explicitly allocates part of the protected later-D5 reserve to D5e;
it does not spend it on more D5d work. Charge actual rounded-up elapsed time only
when closure is proven; otherwise retain the full applicable reservation.

The Q: maximum envelope is 32 GiB backup + 32 GiB target data + 80 GiB target log
+ 2 GiB evidence + 8 GiB free reserve = **154 GiB**. It fits the observed free
space without expanding the existing 256 GiB qualification VHD. Recheck the full
envelope before setup; monitor the file caps and 8 GiB floors during work.

## Reviewed setup operation, pending extension approval

`scripts/copy_p02_d5e_cost_database.ps1` derives from the preserved reviewed D5b
copy harness, with a new fixed one-shot intent and exact source/target identities.
Its `ApprovedCostCopy` switch must remain absent until the extension is approved.
Preparation never supplies that switch or executes the operational script.

In one grouped setup packet it verifies the borrowed PS5.1 session, VM, VHD,
volume, source identity/files and all retained preimages; refuses existing target
paths/database or another retained-database session; creates the owned directory;
takes and verifies the copy-only backup with its explicit MOVE map; restores the
new database without REPLACE; caps only new data/log growth; verifies source
preservation, new ledger/data provenance and all seven child definitions; captures
cross-database dependency metadata; and proves owned SQL session closure.

The new paths are `Q:\D5eCost-20261115\source-copyonly.bak`,
`Q:\D5eCost-20261115\K98_P025_D5e_Cost_20261115.mdf` and the corresponding
`K98_P025_D5e_Cost_20261115_log.ldf`. No source path is a destination. The packet
executes zero cost arms and creates zero additional synthetic rows.

Bounds: 450 host seconds, 380 guest admission seconds, at most 300 seconds per
copy statement, three-second metadata commands, zero lock wait, 220 commands,
2,048 returned metadata rows and 1 MiB receipt. Exact asynchronous command/task/
connection ownership survives uncertain cancellation. An unjoined remote job is
retained, not blindly stopped/deleted. No automatic retry, DROP, reset, overwrite,
permission fallback, production restart or service stop is allowed.

The setup receipt must supply the new database's actual birth, owner, module and
dependency bindings before the measurement runner can be sealed. Source-only
readiness cannot supply a database identity that does not yet exist. Therefore
the measurement runner is not represented as executable or reviewed at this stage.

## Grouped cost workload prepared

The create-only plan `.codex_artifacts/p025/d5e-cost-plan-20261115.json` fixes twelve
unique request IDs, expected due generations, equal OFF/ON warmup and five measured
pairs in alternating order: OFF/ON, ON/OFF, OFF/ON, ON/OFF, OFF/ON. Each arm is
bounded to 45 seconds; 60 seconds of the 600-second measurement envelope cover
shared checks and cleanup. A failed/missing arm is retained and stops progression.

Use the same retained 486,842 source rows, max scan 1245, 415 latest-scan rows,
candidate and output comparison policy in both conditions. The report stimulus
rewinds the nine **cost-copy-only** summary cursors from 1245 to 1244, then invokes
the actual names and summary procedures and commits their report work. Rollback-
only work is not substituted for committed cost or eventual maintenance.

Fresh demand uses the existing coalesced ledger rows in the new copy. Configuration
receives fourteen explicitly synthetic pending requests of 415 rows per arm:
5,810 pending rows minus the 415-row last batch gives 5,395, above the actual
5,000-row upkeep threshold. This forces real configuration upkeep in every arm
without inventing historical imports or altering its procedure. Other five kinds
receive one fresh demand each. The actual six maintenance children run under
fresh claims. Initial post_import generation 2 and its historical first error
15247 are retained; new generations start at 3. The original completed claim is
never retried. Each arm should produce exactly one new configuration log row.

Before measurement, freeze the actual observation/diagnostic condition and source
bindings, all six child-entry proofs, physical maintenance branch comparability,
raw report output equality, date/tie handling, per-stage/overall timers, observer
counts, refusals, false incidents and closure. Both arms keep RCSI off and all
safety/ownership checks. Do not use a synthetic observer proxy to claim product
cost, silently skip upkeep, or warm only one arm. Dependency mismatches or unequal
physical work are blockers, not permission to tune the threshold or rerun.

After warmup, overall median ON must be <= OFF * 1.20 + 1,000 ms; each report-stage
median ON must be <= OFF * 1.20 + 250 ms. Include actual maintenance, observers and
physical cleanup in eventual total time. D5f and D6 remain separate gates.

## Preparation evidence

Setup preparation passed 51 PowerShell 5.1 controls, 13 cleanup-fault controls and three additional async
fault/cancellation/settlement scenarios against the exact helper bodies, with no
SQL/VM operation. The cost-plan contract passed 16 checks including duplicate IDs,
consumed generations, unequal warmup, row/space/time overruns, insufficient upkeep
demand, missing arms and loosened thresholds. These controls are not cost passes.
An initial static no-worker assertion also matched the harmless catalog name;
it was narrowed to actual EXEC invocation and rerun. Historical test evidence is
preserved. Final source hashes, validation and Changes review are recorded in the
setup handoff. No new deferred optimisation item or application change is introduced.

Initial Changes review of `65f4ac92` found no reportable attacker-path finding,
but two concrete correctness blockers: separate timing clocks and unguarded
cleanup/stop exceptions. That revision is retained and is not executable handoff
evidence. The correction shares the parent's elapsed clock, passes both remaining
duration and UTC deadline to the guest, reserves command cleanup time, retains
exact SQL objects on disposal failure, and publishes host custody before attempting
stop. The full reservation remains charged when any cleanup is uncertain. Final
review covers that correction; the initial review is not treated as approval.
