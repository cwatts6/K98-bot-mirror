# P0 reporting session correction

## Scope and cause

The first normal acceptance import after the coordinated P0 release committed
its input, then failed with SQL 51961 in `usp_S11ValidateStatsReportStage` at the
session-guard check. The admitted writer held the snapshot application lock on
its guard connection, but `run_sql_procedure` opened a separate producer
connection. The exact-import lock was therefore on a different session. Existing
recovery tests acquired both locks together and missed this natural-entry path.

The log wrapper also swallowed `fetchall` and `nextset` exceptions, reported
success, and left the durable-completion check to report a missing receipt.
The six-column result was the committed Phase A summary, not completed reporting.

## Architecture and persistence

- `stats_import_outcome_service.execution_connection` owns the narrow import
  connection decision. Coordinated imports borrow their active `scan_data`
  writer's autocommit connection; they do not enter its connection context,
  commit, roll back, close it or release its guard. The outer writer retains
  custody until capture/failure settlement. The original timeout is restored.
  If restoration itself fails while an execution/cancellation error propagates,
  preserve the original error and attach a secondary restoration note. A standalone
  restoration failure after success still propagates.
- Other producer connection behavior remains unchanged. Missing admission,
  closed/wrong owners, runtime mismatch and ambient transactions are refused.
- The log wrapper skips description-less rowcounts but propagates driver errors
  unchanged. It requires the named final eight-column SUCCESS result and never
  treats a Phase A or audit row as completed reporting.
- SQL source validation uses `C:\K98-bot-SQL-Server` at `81dbf8c`, including
  `usp_S11RunStatsImport`, `UPDATE_ALL2`, `usp_S11ValidateStatsReportStage`,
  `usp_S11CompleteStatsReportsCore` and both durable receipt tables. No SQL
  definition, permission, migration, deployment descriptor or receipt changes.

Insufficient error handling and missing natural-entry regression coverage are
fixed in this scope. No command/view changes, new SQL helper abstractions or
unrelated refactors are needed. Existing deferred performance work and full P1
remain next; all F01-F05 production acceptance obligations remain open as before.

## Validation and security decision

Use targeted import, timeout/cancellation, immutable-input, capture, pipeline,
reporting-continuation and result-stream regressions; run repository validators,
lint and the full suite before private promotion. The local SQL regression
reproduces the old split-session refusal against the actual validator, then
executes the corrected borrower with real locks and durable stage checkpoints.
Large business calculations use counted transactional probes; this is not a
production import/export test. Existing SQL interruption/retry, changed-input,
ownership and missing-guard refusals remain required.

Changes security reviews are required separately for the final mirror and private
base/head ranges, with Deep off. SQL has no diff and needs no new security scan.
Tests do not replace those reviews. Conditional references: diagnostics runbook,
Promotion Guide and S11 deployment/restart contract. Implementation and packaging
are authorized; merge, deployment and production recovery are operator-owned.

## Deployment and acceptance

Prepare a source-only corrective release through the protected updater, verifying
compatibility with the already installed r7 tool. Retain the existing SQL release
descriptor and committed migration evidence. Do not reinstall SQL or weaken its
guard. Package qualification must distinguish synthetic host bindings from live
readiness and production observations.

After operator merge/deployment, inspect the retained scan's **Unfinished scan
reports** incident and use its guided **Finish remaining reports** action only
when the current evidence checks pass. This runs reporting-only continuation,
skipping committed stages. Then inspect the linked import/capture and unfinished
pipeline incidents for their next guided actions. Do not re-upload the committed
file, run UPDATE_ALL2 again, supersede the partial outcome merely to clear it, or
release the linked SQL blocker independently. Confirm downstream receipts,
admission and provider delivery before accepting functional health.

The accepted historical 715-second / 132-request publication and 415-row startup
cache check must not be repeated for this correction. Tracked-view restoration
remains unconfirmed P1.
