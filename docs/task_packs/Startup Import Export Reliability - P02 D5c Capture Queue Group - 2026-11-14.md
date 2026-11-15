# D5c capture-to-queue safeguard group

Existing approval covers this grouped preparation, review, one bounded offline
pass and related test-only corrections. Current countdown: 24/73 final-action
routes accepted, 49 remaining; 25/25 inspector checks and 9/12 D5c families closed.

## Scope

Target four `queue_capture` routes: stats import, all-KVK, player report and
configuration producer. The 181 checks comprise 174 behavior cases and seven
runner controls. Capture resumption remains separate: it adopts and updates
saved capture state and needs its own final-boundary tests.

Load original service/adapter bodies, the immutable snapshot serializer/parser,
the actual retained-file length/hash validator, runtime verification/enqueue,
JobSpec validation and the coordinator's final transaction/admission/CAS logic.
The file path transport supplies labelled bytes from memory; SQL transport models
exact parameter bindings, transaction rollback, resource registration and job
linkage. Retry scheduling is disabled. No actual database or filesystem spool is
accessed. Constructor installation checks, real lock scheduling, producer work,
provider dispatch and physical connection cleanup are not established here.

Across all four routes check valid admission, stale tokens/versions/scope,
generation/request mismatch, closed or pending capture, pipeline ownership,
missing/corrupt/noncanonical retained bytes, wrong payload identity/registration,
invalid destinations and output hashes. Inject changes after runtime verification
at the final queue transaction: account, storage, consumer, season, spool identity,
state, disposition and competing job. A version-only change is intentionally
accepted when immutable inputs still match: the final CAS uses the newly read
version. Test lost CAS rollback, resource-kind and destination collisions, exact
replay versus foreign replay and current/known/stale acknowledgement reconciliation.
Both no-export producer dispositions must refuse queue admission.

Assertions require one ready job, exact retained bytes, immutable input digest,
destination bindings, original enqueue ticket and one preparation linkage, or
complete transaction rollback. Earlier execution evidence and snapshot ownership
remain unchanged. No application cancellation or business work is dispatched.
The canonical native retained owner is never accessed, cleared or renamed.

## Review and limits

Security decision: Changes review, Deep off, exact isolated five-file snapshot
(test, runner, preparer, packet and this plan); ordinary HEAD/index untouched.
Independent review covers actual authority versus transport seams, SQL bindings,
fail-closed cases, review pins, startup and effect isolation before execution.
Authoritative ExportPreparation/Job/Resource/JobResource SQL definitions and
existing SQL pins are checked. No runtime or SQL repository files change.

Use the bounded runner with isolated/no-site/no-bytecode Python, not broad pytest
startup. PR-wide architecture/deferred/routing validators and broad smoke tests
are deferred to PR readiness; this local qualification adds no runtime helper or
new architecture boundary. No unrelated deferred optimisation is introduced.

300 seconds, 1 MiB combined intent/result, first failure stops, no automatic replay.
Every correction retains the previous packet and receipts. Existing balances are
1260 native seconds (1000 protected for later D5), 50 Windows-test seconds,
21 consumed inputs and 11/64 synthetic database rows. This offline group consumes
zero native time, new inputs or database rows. No extension is needed.

Acceptance is scoped to original queue admission logic with inert transports;
it does not establish capture resumption, native concurrency, native business
effects or provider publication. Update the countdown only after review and
receipt adjudication; C04, C05 and remaining C06 work remain open.
