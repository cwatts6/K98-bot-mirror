# D5c remaining grouped checks and source review

## Outcome and scope

The remaining D5c work is organized into four preparation groups below. This is
a source-reviewed specification and coverage inventory, **not an executable
qualification packet**. No test, SQL statement, VM operation or new input was
run for this preparation. Existing successful and failed results are preserved.

The current acceptance record remains 9/12 D5c families closed, 25/25 inspector
checks accepted, and 46/46 representative handler safeguard checks accepted.
The three open families are C04 season/weights, C05 queue/pool/holds and C06
effectful recovery. These four groups are not a promise of four console commands:
each executable batch must fit its reviewed command, source, time and row ledger.

Source inventory:
`.codex_artifacts/p025/d5c-remaining-groups-20261114.json`.
It records 73 unique action routes, their actual execute/reconcile source bindings,
52 current Bot source hashes and method locations, 50 verified authoritative SQL
source files, 28 worker/membership scenario IDs, 14 season negative/boundary
scenario IDs, and 17 proposed native schedules. It reverified all 627 preserved
V3 source/evidence pins and the accepted V3 receipt hash. Those are preparation
checks, not newly passed qualification tests.

## Group G1: final action and reconciliation safeguards

**Offline, original code with inert effects.** The 73 policy routes comprise 18
accepted representative baselines and 55 routes without that representative
coverage. Every route still needs its final-boundary disposition. Reuse the 18
accepted baselines; add only the missing deeper guard proofs. Do not rerun the
old 46-check packet or treat its service-level refusal as a final DAL proof.

For each named route, bind:

1. The original final authoritative reread, including inherited and delegated paths.
2. Changed reviewed token/version, fence or owner, as present in that contract.
3. Foreign account/storage/consumer scope and an active physical owner where relevant.
4. A valid-current-state control reaching the same inert effect boundary.
5. Accepted-action reconciliation, including unknown outcomes and original failure retention.

Applicability must be explained from source for every omitted dimension. A route
cannot pass because an outer `inspect` double refuses before the deeper guard.
Keep real canonicalization, `_wire`, identity and digest helpers; introduce inert
seams only at external I/O or the exact effect boundary. Use original inherited
methods and preserve class structure. Token and outcome assertions must match the
actual contract, not a generic error-message substring.

| Route cluster | Final boundary to include |
| --- | --- |
| Stats/all-KVK/player/configuration capture | Actual settlement/capture DAL and current producer identity; valid checkpoint/generation and cancellation paths |
| Configuration/player/report continuations | Locked snapshot/record/reservation and exact continuation or run identity |
| Pipeline and producer refusal | Continue beyond the earlier transaction-entry sentinel to the final locked state check |
| Queue/hold/unreceipted | Actual withdrawal, fixed-resource ownership and retain guards |
| Export and rollover | Replacement/retirement authority, inherited base adapter, registration context and delivery admission; a mocked authority reply does not prove its checks |
| Private evidence/configuration read | Actual authority-selected evidence and final receipt-bound mutation checks |

The manifest enumerates each route individually with source locations and hashes.
This is 73 route obligations, **not 73 newly executable tests**. The exact expanded
case count is frozen only after final-guard applicability and dependency closure
are reviewed. Group related original bodies into one offline handoff where the
300-second/1 MiB envelope permits. All provider, SQL, subprocess and native calls
remain blocked. No captured input or production recovery is executed.

## Group G2: whole worker and exact group membership

**One planned offline group of 28 behavioral scenarios**, plus the existing seven
runner safety controls in its future executable manifest. This extends the
accepted orchestration result; it does not repeat its dispatch/claim or group-count
cases under new labels.

The 14 worker scenarios cover accepted evidence/history priority, incident/source
deduplication, missing adapters, busy/failure preservation, scoped cursor state,
healthy and automatic routing, the existing history budget, clean-sweep evidence,
registration failure and persisted failed checks. Exercise the original
`observe_recovery` body with bounded in-memory pages and controlled time. Do not
run the existing 1,764-cycle workload or application startup.

The 14 membership scenarios cover empty/duplicate/foreign/oversized selection,
changed revision/token/configuration, pending decisions, a race at the locked
DAL reread, evidence count/member mismatch, busy group approval, a valid control,
and atomic rollback on an injected insert failure. Exercise original
`selected_members`, `verify_members`, `approve_selected` and `approve`, including
their SQL-selection behavior through an inert cursor. Do not replace membership
verification with a successful stub as the earlier orchestration test did.

Exact scenario IDs and expected outcomes are in G2 of the inventory. Inert
transaction behavior is evidence about application orchestration, not SQL Server
atomicity or physical restart proof. D5d still owns the latter fault schedules.

## Group G3: season, routing and weight consistency

Prepare the 14 offline negative/boundary scenarios using original validation
bodies: missing choice/member; foreign season/period/choice; publication/config
mismatch; content hash; stale season/weight; disabled/unsupported routing; denied
or missing metadata; and payload access only after metadata closure. A constraint-
invalid row must not be inserted by disabling a foreign key to create a test.
Where SQL itself prevents a malformed tuple, record that constraint and qualify
the defensive Python refusal offline. Reuse accepted generic isolation/rights
evidence without claiming that it exercises every season caller.

Six native schedules are specified: season, routing and weights in each arrival
order. Writer-first must return the old committed tuple while exact fixture
changes remain uncommitted, then roll back. Reader-first must prove the first
metadata read has occurred, acknowledge one exact fixture commit, retain the old
coherent view, then verify the new view on a fresh connection. A snapshot transaction
opened without a first read is not sufficient overlap evidence.

The actual methods are `SeasonSourceDAL.read`, `resolve_season_read` and
`ExportCoordinationDAL.check_intent_weights`. Keep all tuple members and actual
weight/hash validation. Retain final committed labelled versions; no reset/retry.
The source relationships include observation/revision, artifact, roster, period,
configuration/window/scan, update/publication, complete selection, routing and
export-intent provenance. Cyclic nullable creation pointers must be completed
before commit; they cannot be left as a fixture shortcut.

No exact new row proposal is ready yet. Count actual rows, including both versions
and all mandatory parents, against the **53 rows still available**. A SQL
`SourceArtifact` reference is metadata and must never be described as a new
verified/imported spreadsheet. Any need for actual new input conflicts with the
consumed 21-input allowance and stops preparation for that path.

## Group G4: queue, pool, hold tuples and native stale-state refusals

Eight native consistency schedules are specified: queue operator, pool operation,
recovery job and unowned hold, each in both arrival orders. Include the related
discovery/receipt methods in the frozen case ledger; do not infer all callers from
one root-method result. Relevant families are `ExportCoordinationDAL`,
`ExportRecoveryDAL`, `SourceOutputPoolDAL` and `UnownedSqlHoldDAL`.

Three representative native stale-state schedules target the actual final queue
withdrawal, pool confirmation and unowned-hold clear guards. These require
freshly reviewed synthetic identities and preimages. Existing configuration CAS
refusal remains accepted and is not repeated. A refused call passes only with
unchanged records, no durable action and physical cleanup confirmed.

**Specific source constraint:** `UnownedSqlHoldDAL.RESOURCE` is fixed to
`sql_snapshot:legacy_outputs`; it also counts active streams globally. A renamed
test resource or a new account filter would change what is being tested. The
current canonical resource state and global blockers have not been established
by this source-only pass. The next native readiness proposal must read them
without mutation. If the row already exists, leave it untouched under the present
retained-row boundary. A necessary exact exception must be presented with its
preimage and bounded restoration plan before use. Do not invent a second database,
clear retained streams, change constants or relax the guard to obtain a pass.

## Batching, limits and admission gates

No limit extension is requested or consumed by this preparation. Current balances:

| Limit | Current value |
| --- | --- |
| Native time remaining | 1,305 seconds |
| Protected later-phase reserve | 1,000 seconds |
| Available to D5c | 305 seconds |
| Windows-test allocation | 50 seconds |
| Synthetic rows | 11 used of 64; 53 available |
| Retained inputs | 21 consumed; zero new |
| Offline pass | 300 seconds; 1 MiB combined diagnostics |
| Native packet | 48 client commands; 512 rows/command; 2,048 rows overall; 1 MiB receipt |
| Concurrent SQL ownership | Two actors plus one cleanup observer |
| Observation / optional holder / hold | 3 seconds / 1 second / 30 seconds |

Preserve the existing VM, disk/memory reserves, version-store/log limits, application
timeouts and all exhausted retry allowances. Charge the full host duration rounded
up; restart or a new batch never replenishes it. The earlier six-inspector
288-operation/180-second and source-size extensions applied only to that named
packet. They cannot be inherited by these groups.

Before asking for a batch extension, finish the exact executable packet and show
its operation ledger, source sizes, output bounds and cumulative time allocation,
including preflight and cleanup. Propose only the measured shortfall. Do not call
several 48-command cases a single unrestricted handoff or split after a failure to
evade a cap. If the next ready group fits, proceed under existing approval without
asking again. This document does not reserve another native attempt.

Each executable group must have frozen case IDs, hashes and original preimages;
parser/dependency/serialization checks; a narrow Changes review with Deep off;
one create-only intent and separately attributable case outcomes; first-failure
stop; and no automatic retry. Cleanup uncertainty stops all dependent cases. The
native fixture setup and its dependent tests must be reviewed together before
setup, with the setup receipt adjudicated before tests begin.

## Review findings and validation decision

Source review confirmed three preparation risks and carried them as gates:

- Existing native pytest fixture setup removes FK clauses, deletes whole tables,
  and creates users or changes isolation. Reuse assertions only; never execute
  those fixtures against this retained copy.
- The shared unowned-hold key/global-stream query prevents an arbitrary isolated
  key from proving the original guard. Fresh read-only readiness is necessary.
- The representative handler pass stops before several final effect boundaries.
  G1 explicitly retains those obligations instead of treating all 73 paths as passed.

The source-only generator rehashed 627 preservation pins, 50 SQL source files and
52 Bot sources, and checked route cardinality/unique IDs. It imports no application
module and executes no selected function. The inventory is a planning artifact;
its size is not a proposed native manifest-size exception. It is not transferred
into the VM.

Security routing for this delivery: documented skip for the Markdown plan and
generated source inventory; no runtime, SQL, permissions, dependency or operational
behavior changed. The local metadata generator only reads pinned source/evidence
and creates this planning artifact. No independent executable-packet review is
claimed. Future runners, test harnesses and executable manifests require their
own frozen Changes review before qualification.

No runtime tests, smoke imports or native tests are run for this planning delivery.
Validate manifest counts/hashes, required links, whitespace and unchanged original
evidence. Architecture, deferred-item, security-routing and selector PR gates are
deferred to an actual PR; no PR or promotion is handed off here. No production
helper or refactor is introduced and no outstanding D5 obligation is moved into
optional debt. D5d, D5e, D5f and separately approved D6 deployment remain unchanged.

## Next preparation order

Finish the bounded G2 runner first because its original bodies and 28 scenarios
are fully enumerated without a new native fixture. Continue G1 final-route tracing
and G3/G4 exact row/command ledgers within the approved preparation scope.
Compile/check the whole selected dependency closure before consuming a pass,
including inherited empty suites and original serialization helpers. Bring back
the tested and reviewed executable packet, with any exact extension request.

This preserves the operator's preference for grouped handoffs while keeping a
candid countdown: **three D5c families remain open; this preparation closes none**.
