# Guided recovery delivery

Approved 2026-10-15. This is active delivery scope, not deferred optimisation.
The programme remains incomplete until every workstream and acceptance gate below is satisfied.

## Required packages

| Package | Priority | Status | Acceptance |
| --- | --- | --- | --- |
| Durable incidents and guided actions; SQL import settlement vertical | P0 | Implementing | Proactive discovery, persistent alert entry, fresh authorised preview/confirm, durable action identity, postcondition verification; restart/concurrency tests |
| Contested access and abandoned read ownership | P0 | Required | Proven-safe automatic release, exact-owner fencing, incident buttons, eligible work resumes |
| Unknown spreadsheet writes, exports and rollover | P0 | Required | Mutation-specific reconciliation, verified completion/continuation or guided containment, no blind replay or unsafe unlock |
| Committed import checkpoint/capture and partial processing | P0 | Required | Resume remaining stages without replaying committed import; explicit partial-result choice |
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
