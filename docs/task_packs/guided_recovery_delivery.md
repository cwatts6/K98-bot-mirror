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
sealed/read back successfully. Its focused suite passed 197 tests; the full suite remains
in progress at this checkpoint.

The next closure slice retains positive exact-child termination evidence and its immutable
closure receipt across local acknowledgement/storage failures. It re-reads the exact session,
child, account, frozen version and sealed journal before finishing closure. Configuration
discovery can finish an already interrupted owned read; registered proof requests can finish
only the matching job/rollover's interrupted locally owned children. Healthy streams are not
interrupted, old-session children are not adopted, and no provider request is replayed. Closed
streams still need the independent complete-journal and operation-specific settlement proofs.
Recovery after losing the entire authority process before durable closure, and incomplete
read-terminal journals, remain required P0 work in the subsequent focused slice.

Still required before P0 completion: legacy unknown writes, absent attempted-publication retry,
damaged-index/unknown-write containment and registration replacement, earlier rollover phases,
incomplete private journal/child closure recovery, all-KVK generation and missing/unverifiable
output. P1 and integrated alert-to-resolution acceptance also remain required. These entries
are implementation obligations, not deferred optimisation or claims of completed coverage.
