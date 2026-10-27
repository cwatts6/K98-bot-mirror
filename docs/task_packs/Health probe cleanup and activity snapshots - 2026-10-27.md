# Health probe cleanup and activity snapshot completion

## Approved scope and cause

Report 55 linked an unstarted account ticket to a health probe. Admission was refused
while an export owned the account. Cleanup then exhausted its one-second coordination
allowance and left the durable pending ticket without automatic reconciliation. This
establishes the cleanup defect, not the SQL session holding the contested lock. Report
56 verifies the operator-withdrawn ticket resolved. No completed import/export is replayed.

The activity workbook is a top-ten-alliance snapshot. Its population differs from the
kingdom scan, so the previous comparison against every governor with a nonblank alliance
in the latest KingdomScanData4 scan was not a valid import completion requirement.
Snapshot 574 records 855 supplied and observed rows and zero missing/invalid metrics;
its 87 missing expected governors were a separate, superseded roster comparison.

## Architecture and lifecycle

Services own purpose and recovery; DAL owns transactional non-entry checks. Health purpose
is explicitly persisted as actor system:health_probe:v1 before admission. The request
remains the existing immutable read_configuration envelope, so authority read recovery
and provider evidence contracts do not change. Untyped historical reads and business
imports are never automatically reclassified as disposable probes.

| Boundary | Behavior and proof |
| --- | --- |
| Before request commit | Failed transaction creates no durable work; unknown acknowledgement is retained, never replayed on assumption. |
| Request committed, caller interrupted | Existing queue discovery finds explicit health purpose after restart. |
| Admission refused | Bounded five-second cleanup policy, capped attempts and elapsed time; only attributed timeout with acknowledged rollback and close retries. |
| Cleanup still busy | Report waiting; exact ticket stays discoverable for the next recovery cycle. No age-based release. |
| Recovery cancellation | Existing RecoveryAction intent, exact evidence token and transaction-time account lock. Requires initial pending/version1/fence0, no owner, spool, job, generation, membership, held resource, SQL receipt or execution stream. |
| Cleanup committed, reply lost | Receipt reconciliation proves withdrawal without repeating a write. |
| Recovery wins admission race | Fence stops late claim; caller reports deferred when exact health withdrawal is verified. |
| Admission wins race | Non-entry check refuses cleanup and retains the actual execution owner's resources. |
| Provider read/closure fails | Existing authority-backed configuration recovery applies; new cleanup cannot release admitted work. |
| Normal probe succeeds | One original provider operation and ordinary closure; no cancellation or replay. |
| Ordinary configuration/import ticket | Existing guided recovery; new automatic action is absent. |

SQL being unavailable cannot be made equivalent to completed cleanup. The guarantee is
that a new abandoned health request has durable recovery intent and is revisited when SQL
is available, while admitted or uncertain execution remains protected.

## Activity semantics and SQL alignment

Completion is based on the supplied file: expected count is parsed source rows, observed
count is valid rows written, and missing expected count is supplied rows lacking required
valid metrics. Existing parsing rejects invalid/duplicate governor IDs. Missing or invalid
Building/Tech values still prevent COMPLETE; explicit zero remains valid. The existing
usp_SetAllianceActivitySnapshotCompletion independently checks observed count against stored
rows in the same transaction. No schema, procedure, permission or activation change is needed.
Absent governors remain absent, never zero-filled. Leadership review can use COMPLETE
snapshots under its existing per-governor evidence rules.

The SQL companion provides a preview-first historical metadata reconciliation through
snapshot 574. It requires SOURCE_VALIDATED, an original source hash, no missing/invalid
metrics and agreement of recorded source, observed and actual stored counts. Older assumed
zero or genuinely partial snapshots are excluded. Its preview/apply results preserve the
old roster counts for the operator change record. No business rows or daily totals change.

## Refactor and security decisions

Reuse retry_coordination, transaction rollback evidence, QueueAdmissionDAL non-entry
checks/fencing, RecoveryService durable actions and the existing SQL completion procedure.
No new command/view logic or embedded command SQL. Remove the obsolete cross-report query.
No new deferred optimisation item: MGE confirmation and prior monitor cadence work remain
separate existing acceptance items. Changes security review required for each repository;
Deep and whole-codebase scans are not selected. Tests are not a substitute for that review.

## Validation and operator acceptance

Cover positive/negative purpose, all execution-evidence blockers, bounded retries, exhausted
cleanup, process restart, lost acknowledgement, claim/withdraw races, normal provider path,
ordinary import protection, 855-row activity completion and invalid/missing source metrics.
Use disposable local SQL engine tests for fencing/receipt reconciliation and historical
metadata preview/apply/repeat. Validate the full bot suite, architecture/deferred/security
routing, command registration, imports and complete protected-updater transition.

Deploy the reviewed private-main target with the matching updater package. Run graceful
restart only when the updater requests it. No SQL schema migration is required. Historical
activity repair is a separate operator SQL step after bot deployment: preview first, save
the result, then apply in the intended database and save both original and verified outputs.

After deployment: observe an ordinary health cycle and one during normal export activity;
expect admitted success or deferred waiting, no new stranded health queue ticket, and eventual
withdrawal after contention clears. Keep exact receipts if SQL remains unavailable. One future
ordinary activity upload should show source count = stored count and COMPLETE when all supplied
metrics are valid. Do not reupload existing files just to change their historical label.
