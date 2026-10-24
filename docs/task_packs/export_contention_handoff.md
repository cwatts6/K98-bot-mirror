# Export checkpoint contention and pipeline capture handoff

The failed normal export stopped because its authority could not acquire the SQL
account application lock at the next request's `prepared` checkpoint. Captured
diagnostics attribute SQLSTATE 42000 / error 51700 to that checkpoint after 108
completed request observations in the same stream. The request had not reached
the provider dispatch step. Closure then met the same refusal; failure recording
also lost immediate account-lock admission with error 51400. The observations do
not identify the competing SQL session, establish full delivery, or prove that
the provider child terminated. Partial earlier writes remain possible.

The authoritative request procedure uses `sp_getapplock` with timeout zero.
Local SQL reproduction produced the same refusal while another synthetic
transaction held the account lock. This establishes the failure mechanism;
attribution to a particular monitoring task would require additional evidence.

## Corrective scope

- Authority stream/request checkpoints wait at most one second for the same
  account lock using Session ownership on their fresh dedicated connection.
  The unchanged procedure acquires its Transaction lock on that same session,
  rechecks ownership and versions, and commits its own short transaction. All
  result sets and the explicit outer-lock release must acknowledge before return.
  No SQL checkpoint, provider request or unknown commit is replayed.
- The worker's account boundary uses the same bounded wait before taking any
  row/resource locks, including authorization and failure recording. Existing
  durable claims, fences and release conditions are unchanged.
- The pipeline deliberately submits its last capture for a consumer. Recovery
  previously inspected earlier import/report captures independently, offering
  another queue action despite the final capture's existing job. The new read-only
  lineage query follows exact producer operation, pipeline, configuration capture,
  queue receipt, spool identity, account, storage and destinations. Intermediate
  capture cards link to that job and retain all original records. A verified
  handoff resolves only the queue question, never spreadsheet delivery. An
  unconfirmed pipeline remains open; stale independent queue/skip actions refuse.

## Architecture and SQL

Changes stay in service/DAL layers and the exact updater transition registry.
No Discord command, import/report producer, credential, output URL, permission or
SQL schema/procedure changes are included. Existing mutex and transaction helpers
are reused. SQL names, constraints and case-sensitive UUID comparisons are checked
against the authoritative SQL repository. No migration is required. The new files
must be included in the protected source inventory; ordinary uncoordinated source
replacement is insufficient.

## Validation and review

Focused tests cover short contention, permanent contention, ownership checks,
missing replies, commit acknowledgement loss, session-lock release, exact queue
lineage, pending pipelines, changed scope/spool and stale recovery actions.
Restricted-login SQL fixtures exercise the real role/account-lock prologue and
case-sensitive lineage query in disposable local databases. They do not constitute
production replay, full provider acceptance or proof of historical termination.

Required gates: formatting/lint, architecture, deferred-items, test selection,
security routing, focused regression tests, import/registration smoke, isolated
updater qualification and protected rehearsal. Both Git histories require exact
Changes security review, Deep off, plus ordinary PR review. SQL has no changed
diff to review. Public artifacts exclude operational identifiers and raw evidence.

## Production boundary and outstanding work

Preserve both committed scans, the earlier scan's three reporting receipts, the
later retained SQL output, all reservations/receipts and all eleven existing URLs.
Do not rerun imports/reports, blindly requeue captures, replace URLs, clear claims,
merge, deploy or restart as part of this correction. Existing uncertain execution
must be reconciled from durable evidence separately from source readiness. The
updater must stop if its normal drain/evidence checks cannot be satisfied.

P0 F01-F05 and functional production acceptance remain open. Full P1 follows,
including empty-event readiness and tracked-view restoration. The already verified
715-second/132-request timing check is not repeated. No broader optimization is
included in this correction.
