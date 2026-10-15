# Guided recovery delivery

Approved 2026-10-15. This is active delivery scope, not deferred optimisation.
The programme remains incomplete until every workstream and acceptance gate below is satisfied.

## Required packages

| Package | Priority | Status | Acceptance |
| --- | --- | --- | --- |
| Durable incidents and guided actions; SQL import settlement vertical | P0 | Draft Bot PR 331 / SQL PR 108 | Proactive discovery, persistent alert entry, fresh authorised preview/confirm, durable action identity, postcondition verification; restart/concurrency tests |
| Contested access and abandoned read ownership | P0 | Draft Bot PR 332 / SQL PR 109; incomplete-journal/closure paths still required | Proven-safe automatic release, exact-owner fencing, incident buttons, eligible work resumes |
| Unknown spreadsheet writes, exports and rollover | P0 | Guided verified-outcome slice implementing; unknown-mutation containment still required | Mutation-specific reconciliation, verified completion/continuation or guided containment, no blind replay or unsafe unlock |
| Committed import checkpoint/capture and partial processing | P0 | Draft Bot PR 333; all-KVK/missing-output paths still required | Resume remaining stages without replaying committed import; explicit partial-result choice |
| Discord deliveries and domain publication | P1 | Required | Existing-post reconciliation, guided missing-post repair, expired-reminder policy; Ark/MGE/voting/calendar coverage |
| Files, archives, caches and queues | P1 | Required | Identity-checked continuation, conflicting-file preservation, no duplicate timeout fallback |
| Monitor health, outage recovery and complete write inventory | P1 | Required | Independent outage detection, guided host recovery, every enabled write path classified and covered |
| Integrated acceptance and deployment verification | Release gate | Required | Admin begins with alert only; no IDs, commands or SQL needed; verified outcomes and resumed eligible work |

## Common contract

Persist the incident, evidence revision, action intent, execution outcome and audit history.
Permissions and current evidence must be checked on every action. A confirmation authorises
a decision; it cannot prove an old remote writer has stopped. Never release by timeout alone.
An uncertain repair must be reconciled through its original action identity, never replayed.
Acknowledgement, snooze and ownership release are not proof that business work completed.
Alerts must survive restarts, support deleted-message repair and retain unresolved incidents.

Target detection: within 60 seconds of observing uncertainty or an operation-specific stall
threshold while dependencies are healthy; no subsequent job is needed to discover failure.

## Required validation

Inject failure before dispatch, after remote success, after SQL commit and during recovery.
Exercise restart, simultaneous clicks/admins, stale evidence, revoked permissions, deleted
alerts, missing/corrupt receipts, partial output, external edits and live old writers.
Run focused tests, architecture/deferred/security-routing validators, test selection,
command registration and import smoke. Separate Bot and SQL Changes reviews, Deep off.
Validate actual SQL transactions on a disposable target before deployment acceptance.

## Delivery boundary

Implementation and focused mirror/SQL PRs are authorised. Production merge, SQL installation,
deployment and provider operations are not performed by this implementation task.
Preserve existing reader/updater work in the original checkout. New work uses isolated branches.
Any newly discovered recovery gap in these categories remains required programme work.

## Current evidence and remaining P0 work

The first slice is published as [Bot PR 331](https://github.com/cwatts6/K98-bot-mirror/pull/331)
and [SQL PR 108](https://github.com/cwatts6/K98-bot-SQL-Server/pull/108). Its clean full suite
passed 7,717 tests, with 113 skipped and one existing scrubbed-mirror failure for the absent
command-governance workflow. Production installation and integrated acceptance remain open.

The next slice provides authority-derived investigation and guided release for closed abandoned
configuration reads, including after authority restart. On 2026-10-15 the operator explicitly
approved automatic release when the authority verifies the complete private journal, read-only
requests, closed child and exact ownership. The monitor uses the same durable action intent and
verified settlement as the admin button. This approval does not cover unknown writes or
unverifiable history. Normal contention remains amber/deferred in health displays, and repeated
health checks share their retained operation rather than abandoning it at the UI timeout.

Still required in P0: incomplete journal/closure recovery, unknown provider-write reconciliation
or verified containment, export/rollover guidance, committed SQL checkpoint/capture continuation,
and proof that eligible queued work resumes. A held incident with only a recheck button does
not satisfy programme completion. These are required implementation packages, not optimisation.

The committed stats-import continuation adds a guided **Finish capture & queue export**
action. It requires the original completion receipt, original registered configuration,
exact retained reservation and both SQL session guards. Adoption increments preparation
and resource versions while preserving the import receipt. A durable action marker lets
the same repair continue after checkpoint, spool, capture-receipt or queue-acknowledgement
loss. Complete output hashes cannot be replaced. Resolution requires verified retained
bytes and idempotent queue admission; provider delivery remains a distinct incident.
Temporary-table engine tests cover those interruption points, active original sessions,
stale claims and changed output. All-KVK generation recovery and unverifiable or missing
output still require their guided workflows before the programme can be complete.

## Focused publication and export recovery checkpoint

The read slice is [Bot PR 332](https://github.com/cwatts6/K98-bot-mirror/pull/332)
and [SQL PR 109](https://github.com/cwatts6/K98-bot-SQL-Server/pull/109).
The committed scan-data capture slice is
[Bot PR 333](https://github.com/cwatts6/K98-bot-mirror/pull/333). Its full suite passed
7,799 tests, with 113 skipped and the same existing absent command-governance workflow
failure. Both final Changes reviews are sealed and read back; the draft-schema finalization
error was corrected on the original scan without replacing it.

The next focused export slice connects account/storage/registered-pool scoped discovery to
the existing recovery centre. It provides pre-attempt retry, authority-verified publication
settlement, verified interrupted-retirement continuation, completed-rollover settlement and
proven-damage rebuild. Each uses durable action identity, fresh registration and evidence,
existing exact-version SQL transitions and independent receipt verification. A queued repair
resolves repair admission only; its delivery remains separately monitored. Existing unknown
mutation proofs cannot be overridden by a button or admin assertion. No new persistent SQL
objects are introduced in this slice; authoritative schemas are used in temporary-table tests.

That export slice is now [Bot PR 334](https://github.com/cwatts6/K98-bot-mirror/pull/334).
Its exact Changes review covered all five changed source files with no findings and was
sealed/read back successfully. Its focused suite passed 197 tests; its full suite passed
7,816 tests with 113 skipped and the same baseline missing-workflow failure.

The closure slice, [Bot PR 335](https://github.com/cwatts6/K98-bot-mirror/pull/335), retains positive exact-child termination evidence and its immutable
closure receipt across local acknowledgement/storage failures. It re-reads the exact session,
child, account, frozen version and sealed journal before finishing closure. Configuration
discovery can finish an already interrupted owned read; registered proof requests can finish
only the matching job/rollover's interrupted locally owned children. Healthy streams are not
interrupted, old-session children are not adopted, and no provider request is replayed. Closed
streams still need the independent complete-journal and operation-specific settlement proofs.
Recovery after losing the entire authority process before durable closure, and incomplete
read-terminal journals, remain required P0 work in the subsequent focused slice.

The read-journal slice accepts only complete sealed historical probe prefixes consisting of
`prepared`, or `prepared` then `dispatch_intent`, as abandoned reads. All immutable request
identities, private payload/event bytes, sequence membership, closure and registration still
verify. The same prefixes remain forbidden as fresh provider observations or mutation proof.
An additive SQL migration makes the historical catalogue gate agree with the private verifier,
so a recovered failed read cannot poison the next independent reconciliation. Bot and SQL must
be deployed together with refreshed protected source/installation pins. Temporary SQL tests
execute the migration's actual predicate and procedure postimage; no persistent objects are
installed. Missing/corrupt private bytes and unproven old-session closure remain separately
required recovery paths, along with the unknown-write and P1 packages above.

Still required before P0 completion: legacy unknown writes, absent attempted-publication retry,
damaged-index/unknown-write containment and registration replacement, earlier rollover phases,
incomplete private journal/child closure recovery, all-KVK generation and missing/unverifiable
output. P1 and integrated alert-to-resolution acceptance also remain required. These entries
are implementation obligations, not deferred optimisation or claims of completed coverage.

## All-KVK capture and retained queue admission

The next focused slice resumes all-KVK capture only from the atomic completion checkpoint
written by KVK ingest/recompute or KVK recompute. It rechecks original configuration and season,
exclusive SQL producer exclusion, exact retained reservation, immutable completed output hashes
and the original recovery action. The shared capture implementation preserves checkpoints and
reconciles lost acknowledgements without rerunning SQL producers.

Both all-KVK and stats captures stranded before queue admission are independently discovered.
The recovery centre offers **Queue verified capture** with a confirmation checklist. Inspection
is read-only; only a durable confirmed action can admit that snapshot to the queue. Its
idempotent job link and retained bytes are verified before resolution. Stale confirmation,
foreign storage/account, changed output, active original producer and lost queue acknowledgement
are covered by focused tests and actual temporary SQL transactions.

Security routing: Changes review of this focused branch against `e4eacf39`, Deep off,
covering SQL fencing, storage/account scope, retained file verification, admin confirmation
and restart persistence. The authoritative ExportPreparation and ExportResource definitions
were checked in the SQL source repository; this slice introduces no persistent SQL objects.
Missing checkpoints, unverifiable output and all other remaining programme workflows above
remain required implementation work. This slice does not claim full recovery completion.

The capture/queue slice is [Bot PR 337](https://github.com/cwatts6/K98-bot-mirror/pull/337).
336 affected tests and 74 log-isolation tests passed, including temporary SQL fault cases;
the exact eight-source Changes review is sealed with no findings. Full-suite validation
continues separately and is recorded in the PR.

## Verified absent-publication retry

An attempted new-source export settled as absent keeps its original failed attempt and
quarantined parts. The recovery centre now offers **Retry verified absent export**:
admin confirmation requests a fresh authority probe, complete closed journal verification
with no dispatched mutation, current absence, original retained input and safe capacity.
Only then can one separate RepairID export be admitted. The original attempt is never reset.
Lost admission acknowledgements resolve from that exact repair receipt. Unknown writes
remain in the distinct containment/reconciliation scope; they cannot use this action.

The coordinated SQL change allows failed jobs to enter a read-only probe. Mutation admission
stays running-only. The migration pins the exact installed predecessor/postimage and retains
session, resource, ownership, membership and role checks. Bot source pins and updater
transitions change with it. The action preserves existing quarantine rather than inventing
a replacement history.

During this review, the stream-close SQL gate was found to reject unfinished read prefixes
before the private verifier can evaluate them. Completing that close gate with exact positive
child closure and read-only membership is the next required focused P0 correction. It is
distinct from missing/corrupt private evidence and lost-authority-process recovery, which
remain required. No recheck-only path is considered completed programme coverage.

## Read-prefix closure correction

The SQL close gate now permits a preserved nonterminal request only when the persisted
stream purpose is `probe`, its request kind is `read`, and its history contains `prepared`
with no events outside `prepared`/`dispatch_intent`. Missing events, mutation requests and
other purposes remain blocked. The unchanged exact session/account/child/version/sequence
CAS and authority-derived positive child termination still govern closure. The independent
private verifier then checks complete bytes and ordering before any configuration release.
No terminal event is fabricated, and an unfinished read cannot count as a fresh observation.

Migration `20261015_005_read_prefix_closure.sql` follows the failed-publication probe migration,
pins the whole predecessor/postimage, refuses unexpected signatures and preserves roles.
Coordinated Bot source pins must be deployed with it. Actual temporary SQL tests exercise the
close predicate, unchanged history, all closure CAS dimensions and installed module hash.
Separate Bot/SQL Changes reviews use the focused `guided-read-close` branches, Deep off.
No persistent SQL installation or provider operation is part of these tests.

This closes the read-prefix SQL/verifier mismatch only. Whole-authority process loss,
unverifiable evidence, unknown-write containment and the other required P0/P1 workflows
remain active programme obligations, with guided actions and verification required throughout.

## Failed-publication probe request admission

The follow-through review found that request prepare/dispatch still used the older job-state
allowlist after stream-open admitted a failed-job probe. Migration
`20261015_006_failed_probe_request_events.sql` aligns that read-only probe gate with stream-open.
Mutation admission remains running-only; probe preparation still rejects mutation requests.
Both gates retain exact owner, account, fence, version, epoch, nested action and membership
checks. The migration pins the actual manual-public-viewer predecessor, not an earlier
installation body, and refreshes the paired Bot source pins.

Temporary SQL tests now exercise both admission gates across the same state matrix and all
job-ownership dimensions, plus probe mutation rejection and exact compiled postimages.
Separate Changes reviews cover the focused Bot and SQL `guided-probe-events` branches.
This is required completion of the verified-absence button's probe path, not a new recovery
policy or permission to replay unknown writes. All remaining P0/P1 obligations stay active.

## Committed capture with unavailable output

Stats and all-KVK incidents now offer **Keep SQL; skip this export** alongside capture/queue
continuation. The confirmation states that committed SQL data is preserved and the spreadsheet
may remain out of date. The repair excludes active producers, checks the original completed
checkpoint and exact account/storage/owner/fence/version, refuses any queued job or associated
provider stream, and atomically marks only the unqueued preparation unavailable and releases
its exact SQL snapshot reservation. Original requests, execution receipts, generation hashes
and spool references remain intact. Resolution explicitly reports `export_skipped`.

A deterministic local output/format failure during a capture repair records a durable failure
checkpoint under the same producer guards. That fences the old action and exposes the next
guided decision rather than leaving it perpetually pending. SQL timeouts and unknown queue
commits are not classified as safe failure. A queued export cannot use this action.

Tests cover the full failed-capture to confirmed-skip flow, lost acknowledgement, later
unowned reservation, stale/foreign scope, active SQL work, provider evidence and retained
spool preservation for both consumers. The existing confirmation view displays KVK season.
This branch requires a Bot Changes review, Deep off; no SQL schema delta is needed because
the authoritative preparation, resource and execution contracts already represent this
state. Missing atomic checkpoints, queued corrupt exports and unknown provider writes retain
their separate required workflows; no programme completion or deferral is claimed.
