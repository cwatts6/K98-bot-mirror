# P02 D5b report readiness — 2026-11-11

Maintenance qualification is complete with its failures preserved. Reports remain
outstanding; this packet is read-only preparation within the approved native D5b
scope, not another maintenance attempt or a report pass.

## Reopened console and evidence boundary

After the console-host hang, automatic Windows PowerShell launch returned
0xc0000142. The operator manually reopened Windows PowerShell and verified host
9SX2VF4, Desktop edition 5.1.26100.9711, elevated True. The connection-only setup
verified the exact running VM, four CPUs, fixed 8 GiB RAM, zero adapters and host
disk reserve, then created `D5bReports`, InstanceId
`67caa9aa-5bb2-466c-991d-26ab8e1a2fc6`, Opened/Available. Its console variable is
`$global:D5bReportSession`. The old session identity is retired, not reconstructed.

Successful maintenance receipt
`d5b-continuation-result-715c675f474c4d2aae0517dbfacf4f10.json`, SHA-256
`dbfc23fb7687ed4cd5952a1d9fd31ac4e5b6382710fdeb96bf5348cf8ac7601b`,
and its separate adjudication remain authoritative. The one targeted retry is
consumed; never run the old recovery/continuation scripts again. Original failure
receipts, first-error history, source database and inputs remain unchanged.
The native allowance remaining is 1513 seconds; 21 inputs remain consumed.

## Reviewed readiness operation

- Source `scripts/collect_p02_d5b_report_readiness.ps1`, SHA-256
  `3d469d126ac293e5ba5c6c8acb66909f3334e666b33ae511d0c53a84237e7d1a`.
- Manifest `.codex_artifacts/p025/d5b-report-readiness-manifest.json`, SHA-256
  `260db241f2d13bf22f9bb05e5ba63654340d76f64c4e060ef15b95a5b5364bdb`.
- Inert test `tests/validate_p02_d5b_report_readiness.ps1`, SHA-256
  `c9c36d0ca22bf524c64970d0ad9295b109b1f30b13fcdabc20bb671128753b65`.

The new collector pins the new session and successful continuation receipt, exact
copy identity/files/settings, Q volume and original source protection. It reads
the six completed claims, ownership, full permission fingerprint, nine summary
checkpoints, source row/scan aggregates and the eleven report definitions with
execution flags/signature counts. Thirty candidate structural fingerprints are
recorded for comparison with the installed candidate. Foreign copy sessions stop
the remaining checks; changed maintenance completion also stops them.

For each of the retained 42 detailed-state SELECTs and 14 export SELECTs, the
collector asks SQL Server to describe the result shape. It does not execute those
SELECTs or a producer. Only the last two historical database qualifiers are bound
to the disposable copy. The description batch writes local table variables only.
See Microsoft's [result-set description function](https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-objects/sys-dm-exec-describe-first-result-set-transact-sql?view=sql-server-ver17)
for its returned metadata and error fields. Missing/ambiguous/error metadata cannot
be treated as an accepted report contract during adjudication.

Success path: 27 client commands including closure, within the unchanged 48-command,
512-row per-command, 2048-total-row, 1 MiB receipt and 300-second outer envelope.
Metadata commands remain three seconds with zero lock wait; disk/version-store
reserves and VM allocation/isolation remain unchanged. The host writes a new
exclusive intent/receipt and deducts elapsed native time conservatively. No grant,
ownership change, installation, input read/replay, report or maintenance run occurs.

## Validation and next boundary

Actual Windows PowerShell 5.1 inert tests passed parsing, query budgets/disposal,
deadlines/cancellation, visibility tri-state, copy identity, conservative budget,
exact new-session binding, observation inventory, and metadata-only description
checks. Routing and whitespace checks passed. Broader Python tests and PR-only
architecture/deferred/test-selection gates are skipped for this standalone PS
observer; no Python or production code changed.

Independent review found no blocker. Changes scan
`a7330dde-7571-4d75-a82c-5953055f4aa6` completed with zero findings, Deep off, all
16 source files accounted for and prior 15 source hashes unchanged. Snapshot
`07fc1ba4da021497651168755f919baa310e4ddd585bec4dae3cbf6bbf1d7a36`;
findings SHA-256 `718bc635b467af9bee86320f136ba254e2120b154b10746a36cb67f368a2fa59`;
coverage SHA-256 `c89135cbca185fed0eab7719e1e1e8e678b49e391846220e640b199fa3dca33b`.

Adjudicate this native receipt before report execution. The remaining report
packet must bind the actual definitions/shapes, controlled report clock/cursor
stimuli on the disposable copy, original independent numeric/latest-name oracle,
all 42 states/14 exports and immutable queued bytes. Preserve the accepted
tied-zero-rank policy and all original operation-specific capture/time limits.
No historical runner may be imported or rerun wholesale; no consumed import or
completed maintenance may be replayed. Report rollback, physical connection
closure and original/candidate preservation need explicit evidence. Full D5b
closeout remains contingent on those checks.
