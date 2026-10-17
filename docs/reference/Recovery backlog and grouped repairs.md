# Recovery backlog and grouped repairs

## Scope and acceptance

This change addresses a recovery backlog of 17,431 recorded incidents. The supplied
400-record sample contained 362 missing replicas with verified originals, 34
verified repairs and four separate stats incidents. Recorded totals include resolved
work. Evidence-copy repair does not establish SQL write success or release a queue.

Acceptance requires:

- One admin confirmation durably approves the exact reviewed evidence-copy group.
  Changed membership requires a new review. Each item retains its own original
  evidence hash, actor, action receipt and independent verification.
- Accepted repairs progress in bounded batches without another admin interaction,
  survive restart, and do not starve behind untouched historical incidents. Failed
  checks rotate fairly; changed evidence is not repaired under stale approval.
- The centre displays operational incidents and group progress before individual
  evidence files. Unknown writes remain separately identified and protected.
- Notifications update one persisted overview, coalesce changes over five minutes,
  and do not repost unchanged incidents every minute. Old individual messages retain
  their working review buttons; historical alerts are not deleted.
- One ZIP includes a complete summary and every recorded incident through a cutoff,
  with diagnoses, required repairs, pending verification and blocker links. It uses
  bounded compressed and uncompressed storage and fails explicitly if incomplete.
- A never-admitted pending queue entry has a guided cancellation. Its initial state,
  immutable request hash, absence of streams, execution receipts, membership,
  reservations and captured output are checked under the account lock. Cancellation
  durably fences the old worker. Already-admitted/uncertain work links to its domain
  recovery and cannot use this cancellation.
  Typed producers always use their domain cancellation/continuation workflow,
  including requests which have not acquired admission yet.

## Admin workflow

Open **Recovery centre** from the status card or overview. Operational incidents and
repair groups appear first. **Browse individual incidents** retains detailed access.

Choose **Repair evidence group**, read the count and checks, then **Confirm grouped
repair**. Approval applies only to the reviewed set. There is no need to leave the
message open. Individual repair receipts are saved atomically before any filesystem
change; the monitor processes up to 50 accepted items per cycle. A lost confirmation
response can be investigated through the group in the centre. Do not submit another
group to retry an already-accepted action.

The group shows verified, pending and changed/not-applied counts. Completed with
exceptions means the batch finished evaluating its approvals, not that every original
incident was resolved. Unavailable verification stays pending and retries. The report
retains the individual outcomes and the original business recovery remains separate.

Choose **Download complete report** for `K98-recovery-complete-report.zip`:

- `summary.json`: complete counts by source, state and outcome, repair availability,
  linked recovery dependencies and monitor health.
- `incidents.jsonl`: one JSON record per incident, including resolved records and
  group progress. Raw request bodies, action inputs and credentials are excluded.

**Download recovery report** retains the existing detailed part workflow if an archive
exceeds the channel attachment limit or collection bound. Neither report applies a repair.

For **Account queue admission**, review the offered action. **Cancel unstarted queue
entry** cancels only a proven initial pending request. **Review execution and ownership**
opens the appropriate recovery when admission already happened. Successful cancellation
removes that ticket from eligibility; subsequent admission still checks every other owner.

## Replica investigation

Both the installed predecessor and merged source call `retain_replica` before returning
a new private-evidence receipt. Replica-creation failure prevents that receipt being
returned for SQL registration. The existing regression suite tests this boundary.
The sample alone therefore does not establish ongoing replica loss or its cause.

Replica file metadata is collected separately by the read-only support diagnostic,
without changing the installed private-evidence authority or its protected source
pins. Modification times are investigation hints, never trusted creation/execution
proof or repair tokens. Compare them with deployment timing and newly observed
incidents to distinguish legacy single-copy files from subsequent loss. Neither
individual nor grouped copy restoration is automatic: the service permits automatic
release only for previously approved verified read-only configuration recovery.

## Architecture, validation and rollout

The existing `RecoveryIncident` and `RecoveryAction` contracts hold group progress and
per-item approvals. The group ID is retained in each action's reason for audit correlation.
There is no new SQL schema or migration. Queries were checked against SQL source
`b663308aabe049319e1ce32a50d1bcfd810f9d8f`, including the initial preparation state and
ownership constraints. Services own approval and reporting; the views only route admin
interactions, defer responses and render results. Existing authorization, draining,
redaction, incident receipts and protected evidence restoration are reused.

Validation includes a 17,431-incident one-download test; wrong-admin/guild/channel
denials; SQL-backed group persistence, stale/duplicate approval and scope checks;
queue admission races, late workers and lost acknowledgements; existing evidence,
notification and recovery tests; and full private-checkout validation. The scrubbed
mirror omits authority modules needed by some SQL tests, so those run in the private
validation checkout with disposable local SQL objects only.

Merge reviewed mirror and private PRs, then use the installed coordinated updater on
MINI_AMD. Before a new deployment, finish the prior updater's retained readiness
verification. The supplied status verifies source, seed and start but leaves readiness
`intent_outcome_unconfirmed`; preserve receipts and follow same-release verification.
No production cancellation, replica repair or final deployment acceptance is established
by local tests. The exact reported blocker requires its current diagnostic evidence.

All remaining P0b recovery work stays in scope. This backlog change does not claim
completion of historical unknown-write, partial-output or missing-all-copy recovery.
