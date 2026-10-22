# P0 coordinated completion

## Scope review — 22 October 2026

Implementation, validation, Changes reviews, coordinated PR preparation and updater
packaging are authorised. Do not merge, deploy, change activation flags or perform
production recovery. Deliver one bot mirror/private PR pair and the necessary SQL
PR, with a single ordered release handoff. Internal commits are not separate releases.

Baseline: mirror `f9bdaa9d4d35cabc9785b79341410fb9b6f620d1`, private
`a6c48f77724072c46acb62f4ef5665194dddbf07`, SQL
`716c74ebbced800de8243892a7bce6a5ebac380c`. The SQL primary checkout has
pre-existing changes; work from the isolated committed SQL baseline instead.

Report 18 includes 17,551 resolved incidents, no accepted repair awaiting
verification, and a healthy monitor. The two recently open captures were explicitly
closed as export skipped, not delivered. That is operational closeout, not proof
that all failure families are implemented or accepted.

## Reconciled obligations

| Family | Existing implementation/evidence | Remaining coordinated work |
|---|---|---|
| F01 | Replacement, publication readback and physical absence/damage recovery exist; the 715-second/132-request production check is accepted. | Reconcile the end-to-end failure matrix, especially repeated repair failure, retained-input identity and independent final delivery verification. |
| F02 | Exact-byte working-copy/backup recovery and fresh replacement proposal/read recovery exist. | Independently qualified succession for lost containment/active-registration history; explicit ownership/configuration conflict handling. Never invent a lost receipt or release foreign/live ownership. |
| F03 | Atomic report/configuration, capture/queue recovery, refused admission and configuration export-intent continuation exist. | Durable stage receipts and guided remaining-stage decisions after partial UPDATE_ALL2/configuration, cache/maintenance and failures before request creation. Historical partial results need a separately confirmed successor/disposition, not replay. |
| F04 | The deployed policy already enables rollover actions. Older task-pack statements saying otherwise are historical. | Complete callback, authority-journal, temporary-SQL and worker qualification, including blocker navigation and repeated interruption. |
| F05 | Evidence-bound admin actions, independent monitoring, reports and protected updater exist. | Final cross-family matrix, exact-source validation/review and coordinated package. Record production acceptance separately. |

## Architecture and persistence direction

Keep Discord commands/views as interaction routing. Services own continuation and
successor decisions; DAL/SQL own scope, locks, compare-and-swap and durable stage
receipts. Reuse the existing preparation, execution, action and immutable capture
contracts. New SQL contracts belong in the SQL repository with explicit migration,
permission and updater-profile integration.

Every resumable stage needs an identified input/configuration, dispatch identity,
live-execution exclusion, durable outcome and bounded next action. A committed
import is immutable. A completion observation, missing acknowledgement, elapsed
deadline, phase audit row or released reservation is not a stage receipt. Unknown
historical work must remain distinguishable from newly verified successor work.

A successor must independently verify its current inputs and outputs while retaining
the original unknown result and excluding its possible writers. Evidence recovery
must not widen authority, substitute arbitrary paths/files, or silently reconstruct
active registration from untrusted assertions.

## Validation and release contract

- Maintain an explicit obligation-to-code/test/evidence matrix. Do not mark an item
  complete solely because a test file exists or the current incident count is zero.
- Exercise permission, stale/concurrent confirmation, restart, lost dispatch/commit/
  queue replies, changed registration, foreign/live writers, partial failure and
  failure during repair through real service and admin paths.
- Validate changed SQL against the committed source, use disposable local SQL
  fixtures, and qualify migration apply/reapply and protected updater interruption.
- Run architecture, deferred-item, security-routing, selected/full tests, import
  smoke, command registration and log-isolation checks. Preserve unrelated failures
  and original failed-run evidence rather than rewriting results.
- Security review is **Changes**, Deep off, for final bot mirror, SQL and private
  promotion targets. Resolve accepted findings and code review comments before
  declaring merge readiness.
- Package exact final source/SQL transitions, predecessor checks, deployment order,
  resume/rollback constraints and operator instructions. Merge/deployment remain
  separate operator decisions.

## Preserved boundaries

Do not repeat the accepted publication check or the verified 415-row KVK16 cache
build (29 September source). Larger timing investigation remains deferred. No P0
gap moves into P1. Keep the full P1 programme next, including the still-unconfirmed
tracked-view restoration. Natural production admission/provider acceptance is a
post-deployment gate and must not be manufactured during implementation.

## Implemented coordinated scope

F03 now registers each pipeline run and seven stage operation identities before
execution. Stage observations distinguish producer completion, caches, maintenance
and export admission. An admitted export links its real job; admission does not
claim delivery. Recovery executes only the first unfinished eligible stage after a
separate confirmation. Unknown stages remain unknown until an explicit disposition
or separately verified successor; normal dispatch cannot consume a recovery intent.

UPDATE_ALL2 saves continuation inputs in its import transaction. Reporting commits
three stage receipts with their business writes. Continuation validates unchanged
input, configuration and actual SQL worker guards, then skips committed stages.
Historical runs are never backfilled. Legacy partial non-atomic configuration has
an exact unknown-outcome disposition and a separately confirmed fresh SQL-only
configuration successor. An absent original export intent cannot authorize export.

F02 adds independent containment and registration attestations when original private
history is unavailable. These are new sealed witnesses, not reconstructed original
receipts. They verify current permanent isolation or surviving sealed dependency
history, retain original uncertainty, and neither release foreign ownership nor
claim provider delivery. If the independent prerequisites are also lost, the exact
missing evidence is identified for collection; arbitrary SQL state/admin assertions
cannot replace it. An unattributed global SQL blocker has a separate disposition
only after actual writer locks, all durable producer/stream checks and exact ownerless
compare-and-swap prove it is safe. Prepared/running detached imports still block it.

The UI retains return links after verified evidence repair or disposition so the
original unfinished operation stays reachable. No new commands or activation flags
are introduced. The SQL migration adds six tables and changes four procedures.

## F01-F05 qualification matrix

| Obligation | Implementation and executable qualification | Acceptance boundary |
|---|---|---|
| F01 uncertain write, physical absence/damage, retained input and repeated repair failure | Existing replacement/publication services; `test_export_replacement_release_sql.py`, `test_publication_recovery_release_sql.py` exercise actual admin callbacks, retained inputs, stale/denied confirmation, lost admission, failed successor and independent delivery verification. | Google and native transport are simulated locally. Keep the accepted 715s/132-request result; do not repeat it. |
| F02 exact backup, lost containment/activation history and ownership conflicts | `export_evidence_recovery`, containment/registration attestation services and DALs, pool-retirement verification, `unowned_sql_hold_*`; new attestation/hold SQL suites plus `test_export_evidence_recovery_sql.py`, `test_rollover_evidence_loss_sql.py`, pool/rollover suites. | New witnesses never prove old outcomes. All-copy loss without independent prerequisites stays explicitly unknown with specific collection guidance. Foreign/live/unresolved work cannot be cleared. |
| F03 partial import/report/configuration and pre-request pipeline | `stats_report_continuation_*`, `processing_pipeline_receipt*`, `processing_pipeline_recovery`, `unreceipted_producer_recovery`, `legacy_configuration_continuation`; corresponding SQL/async suites and configuration continuation suites. | Counted fixture calculations validate transaction boundaries; the independent SQL token-equivalence validator checks preserved business blocks and unchanged nested calculators. No committed import replay or production failure injection. |
| F04 interrupted rollover and return navigation | Existing real rollover worker, proof service and authority journals; `test_rollover_replacement_guided_sql.py` covers pending/verified private, clear and setup phases, second replacement failure and lost settlement; evidence-loss and replacement suites cover missing journals/configuration and exact release. | Actual callbacks, SQL and worker logic; simulated provider/transport. Natural eligible production rollover remains post-deployment acceptance. |
| F05 permissions, concurrency, restart, lost replies, live writers, complete diagnostics | Real RecoveryService and callbacks in guided suites, new `p0_attestation_ui_harness`, source/SQL contracts, architecture/deferred/routing gates, broad private tests and protected updater rehearsal. | Implementation readiness, package qualification, deployed source and natural provider outcomes are separate evidence. Healthy monitoring alone closes none of these dimensions. |

## SQL and release evidence

The SQL candidate is `db18f23730521a41a215b744957cd61002eedf8d` over
`716c74ebbced800de8243892a7bce6a5ebac380c`. Its recovery reporting entry point
requires a non-NULL preparation ID. The legacy nullable `UPDATE_ALL2` call uses
an internal same-owner reporting core, with direct EXECUTE denied to `public`.
Restricted-user regression cases cover omitted/NULL IDs, dynamic and nested calls,
core invocation and legitimate static legacy/recovery chains. The existing trusted
application ALTER capabilities are outside this entry-point boundary. Final exact
Changes review evidence is recorded in the release handoff.

Historical SQL whitespace is retained intentionally
where it forms an authenticated preimage; it is not normalized to satisfy a cosmetic
diff check.

The disposable migration rehearsal passes live-writer refusal, precommit rollback,
apply/reapply, disabled-check refusal and changed-procedure refusal. A separately
installed literal-source reference is compared with the real protected adapter's
result across 460 application objects, effective permissions and three startup
contracts. This is no production migration or populated business-data benchmark.

The updater uses finite profile `20261022_002_p0_completion_release`, one child
migration, eleven pinned images, the deployed private predecessor and exact runtime
source pairs. It drains before SQL, then installs matching source/seed and verifies
one successor. A bot-only rollback after schema change is unsupported because the
previous whole-application contract rejects the new schema. Preserve receipts and
use the same release continuation or a reviewed compatible correction.

Final bot/private Changes reviews, exact-head CI, all review-comment closeout and
final package checks must pass before merge readiness is reported. The release
handoff records their exact heads, results, checksums and fixed operator commands.
No merge or deployment is performed by this work. Full private validation uses the
isolated private checkout; the scrubbed mirror intentionally lacks authority source.
