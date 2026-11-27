# P02 observer mutation coverage reconciliation

20 November 2026. Local source review in progress; no new runtime acceptance.
This supplements the observer design and traceability. It does not alter the
68 requirement records, 73 policy pairs, D7 status or downstream owners.

## Authenticated source boundary

All 594 records in deploy/p02_observer_application_sources.json are resolved:
591 match the current SQL worktree with the existing LF source convention;
three retain exact historical Git bytes:

| Source | Exact historical commit |
| --- | --- |
| dbo.ExportReplacementDelivery | 2dd649bfb5c8b71597dffb8b0f25d53c10cb510f |
| dbo.KingdomScanData4 | d2ad697727349452a31269a3b938a440f7011f25 |
| dbo.usp_GetPersonalStatsDaily | f9e0cf8375fb40ce8b39c6484c5f1c2eb948a990 |

No expected hash was replaced by an observed hash. The three historical records
remain unchanged predecessor obligations. The inventory contains 124 procedures,
51 views, eight inline functions, one scalar function, 408 tables and two table
types. Four new protocol triggers are reviewed separately from those 594 records.

ScriptDom parsed all 188 module/trigger sources. For 92 exported files, intact
export preparation and intact module definition were parsed as separate batches;
the original source bytes and definition line numbers were retained. All 124
procedure definitions are represented. The first parser pass and its null-tree
failure are preserved; the corrected pass has no parse errors. The resulting
280 source sections and 6,352 fragments are a review worklist, not acceptance
counts or proof that dynamic SQL has been fully classified.

Evidence: .codex_artifacts/p02-observer-proof-20261119/continuation-20261120/
source-sink-reconciliation-01. Resolved source hashes, historical bytes, parser
projections, actual static write targets and dynamic dispatches are retained there.

## Lifecycle sinks traced from statements

The admitted lifecycle query reads KVKFinalReportHeader, MaintenanceKvkWork and
the kvk_output row of MaintenanceWork. The authenticated procedure definitions
contain these 13 direct write statements:

| Writer | Statements | Invalidation and continuous owner |
| --- | ---: | --- |
| usp_MaintenanceDue | 1 | Maintenance table trigger covers relevant kvk_output demand; caller transaction is preserved. |
| usp_MaintenanceKvkDue | 2 | KVK-work trigger; publication requires an existing transaction and schema ownership. Its aggregate demand goes through usp_MaintenanceDue. |
| usp_MaintenanceKvkOutput | 3 | KVK-work trigger covers running, completed and failed states. Normal dispatch inherits the maintenance worker's session mutation marker. |
| usp_RecordKvkFinalReportCompletion | 2 | Header trigger covers insert/update, including direct/backfill calls. Its owned or borrowed transaction remains the physical boundary. |
| usp_RunMaintenance | 5 | Session mutation marker starts before early unknown-state repair and remains through children and outcome/failure recording. Normal completion releases it; failure requires actual caller cleanup. |

The three table invalidators cover INSERT/UPDATE/DELETE at statement scope.
MaintenanceConfigurationWork is not read by this lifecycle query; configuration
demand also updates MaintenanceWork, while relevant configuration metadata DDL
uses the database invalidator. Ordinary business/audit DML is not a reason to
add unrelated table triggers.

No parsed static TRUNCATE or BULK statement targets these three lifecycle tables.
There are 24 static TRUNCATE candidates elsewhere, including temporary and
ordinary business tables. Dynamic target construction still requires review;
this result is not a general assertion that bulk/DDL bypass is impossible.
The explicit lifecycle ALTER denials, fresh permission checks and retained native
bulk/TRUNCATE refusals remain necessary.

## Entrypoints, dynamic execution and limits

The worklist identifies 35 runtime dynamic-SQL dispatches in 17 procedures after
excluding export declaration stubs. No variable procedure-name dispatch was
found in the parsed procedure definitions. Dynamic SQL fragments and ordinary
data literals must be distinguished by their actual execution path; keyword
counts alone are not closure evidence.

Normal sp_TARGETS_MASTER publication begins its transaction before the enrolled
sp_ExcelOutput_ByKVK child, then retains the same transaction through later
sp_Prep_ExcelOutputTable and view publication. The direct child is not independently
granted EXECUTE by the reviewed application grant inventory. This closes that
source-defined normal call edge; arbitrary trusted/manual use is not inferred.

The report validator enrolls before its legacy NULL-preparation return and
retains transaction ownership for the actual report body. Maintenance enrolls
before early repair, dispatches all six children under its real business guards,
and retains the marker on failure until physical cleanup is acknowledged.

The database DDL trigger invalidates supported catalogue changes. Temporary
tables are distinct from the admitted database catalogue. A direct multi-statement
privileged/manual operation must use the mutation protocol for its full lifetime
or occur during a drained migration; individually committed DDL statements do
not establish continuous ownership between statements.

## Remaining closure conditions

- Qualify the source-classified dynamic paths below in the remaining native cases;
  source-defined ownership does not establish simultaneous engine progress.
- Reconcile actual native DDL event, permission/signature and disable/re-enable
  cases with this source inventory; an event-group declaration is not proof of
  every relevant event.
- Complete both arrival orders for all five real roles with actual simultaneous
  SQL-engine activity, useful business completion, immutable capture and the next
  independent consumer. Preserve original publications 539/540.
- Complete the agreed balanced workload cost cases and full three-contract/
  release transition. The authenticated source census does not substitute for
  those outcomes or final separate Bot/SQL Changes reviews.

## Dynamic dispatch source disposition

All 35 sites are classified below. The reviewed grant inventories directly grant
EXECUTE to SP_Stats_for_Upload and sp_TARGETS_MASTER; none of the other 15 has
an independent direct grant in those inventories. The 279 activation roots are
source-selection roots, not a list of runtime-authorised entries. Incoming call
edges and effective permissions must remain distinct.

| Procedure | Sites | Effect | Source ownership and limit |
| --- | ---: | --- | --- |
| dbo.CREATE_DASH2 | 1 | Ordinary data INSERT into EXCEL_FOR_DASHBOARD; dynamic columns are selected from existing metadata. | Report-core child; no direct reviewed EXECUTE grant. No lifecycle-table target. |
| dbo.IMPORT_STAGING_PROC_CORE | 1 | BULK INSERT into fixed IMPORT_STAGING_CSV_RAW from the digest-bound claimed path. | Owned or borrowed import transaction; target cannot select a lifecycle table. Existing source/file custody retained. |
| dbo.SP_Stats_for_Upload | 2 | Source validation SELECT and INSERT into a temporary candidate table from integer-selected EXCEL_FOR_KVK output. | Direct grant retained; owned/borrowed transaction and publication guard. No dynamic persistent DDL or lifecycle target; player_report due is outside the KVK lifecycle query. |
| dbo.TARGETS_NEW | 1 | Create/truncate/insert fixed numeric KVK target/output/export table families. | No direct reviewed grant or incoming pinned call edge. Privileged/manual multi-statement use requires enrollment/drain; source presence is not installed use. |
| dbo.sp_Create_Excel_For_Kvk_Indexes | 4 | Drop/create two named indexes on a parsed and quoted table. | No direct reviewed grant or incoming pinned call edge. Individual DDL invalidates; manual multi-statement use requires continuous enrollment/drain. |
| dbo.sp_ExcelOutput_ByKVK | 1 | Canonical numeric EXCEL_FOR_KVK output replacement inside the publication transaction. | Explicit mutation marker before relevant writes; master, loop and report-core callers inherit transaction ownership. |
| dbo.sp_Maintain_PlayerKVKHistory | 1 | MERGE ordinary PlayerKVKHistory data from a numeric KVK output. | Backfill child; no direct reviewed grant. No metadata/lifecycle write. |
| dbo.sp_Prep_ExcelExportTable | 3 | Create/truncate/insert numeric EXCEL_EXPORT_KVK_TARGETS table; identifiers quoted. | Master transaction; DDL invalidator owns first relevant DDL through commit. No lifecycle target. |
| dbo.sp_Prep_ExcelOutputTable | 3 | Drop/recreate/insert numeric EXCEL_OUTPUT_KVK_TARGETS table; identifiers quoted. | Normal master path follows enrolled publisher in the same transaction. Direct privileged/manual use requires enrollment/drain. |
| dbo.sp_Prep_TargetTable | 3 | Create/truncate/insert numeric TARGETS table; identifiers quoted. | Master transaction; first relevant DDL enrolls even when this child precedes the publisher. No lifecycle target. |
| dbo.sp_Rebuild_ExcelForDashboard | 1 | Drop/recreate fixed EXCEL_FOR_DASHBOARD using numeric KVK source tables. | Report-core transaction and validator marker; direct privileged/manual multi-statement use requires enrollment/drain. |
| dbo.sp_Rebuild_v_PlayerKVK_Last3 | 1 | Single CREATE OR ALTER VIEW of the fixed player-KVK view. | DDL invalidator covers the statement; no direct reviewed grant or incoming pinned call edge. |
| dbo.sp_Refresh_View_EXCEL_FOR_KVK_All | 4 | Two fixed view definitions, with empty/nonempty branches and quoted numeric output names. | Normal publisher transaction already marked; direct privileged/manual multi-statement use requires enrollment/drain. |
| dbo.sp_TARGETS_MASTER | 3 | Target count SELECT, publication-row INSERT and fixed target-report view replacement. | Direct reviewed grant; per-KVK transaction begins before children and commits after view publication. First DDL or enrolled publisher retains marker through commit. |
| dbo.usp_MaintenanceConfiguration | 1 | Index rebuild/reorganise on fixed reviewed delta-table inventory. | Actual worker session marker spans maintenance, state updates and failure recording; no direct reviewed grant. |
| dbo.usp_MaintenanceImport | 2 | Index rebuild/reorganise on fixed KingdomScanData4. | Actual worker session marker; index name comes from metadata. No new identifier policy is inferred from this census. |
| dbo.usp_MaintenanceKvkOutput | 3 | Two missing-index CREATEs and FULLSCAN statistics on exact claim-bound numeric output. | Actual worker session marker, existing five business guards and exact object/header claim; lifecycle updates additionally use table invalidator. |

This completes the source-level classification of the extracted dynamic dispatches.
Native event/bypass coverage, installed-use evidence for legacy/manual paths and
Q03/Q04/Q07 progress/cost acceptance remain open. No production pin, permission or
business calculation was changed as part of this review.
