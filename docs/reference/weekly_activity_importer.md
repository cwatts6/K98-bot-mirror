# Weekly Activity Importer

Purpose: document the weekly alliance activity Excel import path.

## Main Files

- `DL_bot.py` delegates uploads in `ACTIVITY_UPLOAD_CHANNEL_ID` through
  `upload_routes/weekly_activity_route.py`.
- `upload_routes/weekly_activity_route.py` owns Discord route matching, SQL preflight,
  generic durable import audit wiring, duplicate/success/error embeds, notify-channel fallback,
  ingest offload dispatch, and best-effort log-backup scheduling.
- `weekly_activity_importer.py` parses and writes activity snapshots.
- SQL schema lives in `C:\K98-bot-SQL-Server`.

## Expected Workbook

The upload is the weekly alliance activity export, commonly named:

```text
1198_alliance_activity.xlsx
```

Required logical columns are matched tolerantly for whitespace, non-breaking spaces, and case:

- `GovernorID`
- `Name`
- `Alliance`
- `Power`
- `Kill Points`
- `Help Times`
- `Rss Trading`
- `Building`
- `Tech Donation`

## Deduplication

Files are deduplicated by:

- `WeekStartUtc`
- `SourceFileSha1`

`SourceFileSha1` is stored as `VARBINARY(20)` in SQL.

Duplicate uploads do not create a new `dbo.AllianceActivitySnapshotHeader` row. Generic audit
records therefore keep duplicate outcomes uncorrelated to an external weekly activity snapshot.

## SQL Writes

The importer writes:

1. `dbo.AllianceActivitySnapshotHeader`
2. `dbo.AllianceActivitySnapshotRow`
3. `dbo.AllianceActivityDelta`
4. `dbo.AllianceActivityDaily`

Validate these objects against the SQL repo before changing importer behaviour.

## Generic Import Audit

The upload route creates best-effort generic audit rows through the shared import audit service
and SQL-owned writer procedures.

- `ImportKind`: `weekly_activity`
- `SourceType`: `discord_upload_xlsx`
- Phases: `weekly_activity_xlsx_parse`, `weekly_activity_sql_ingest`,
  `weekly_activity_post_import_backup`
- Accepted imports correlate to `dbo.AllianceActivitySnapshotHeader` with
  `ExternalBatchId = <SnapshotId>`.
- Duplicate and failed outcomes remain uncorrelated when no snapshot row exists.

The route performs a direct thread pre-parse to capture source row counts for audit without going
through the maintenance offload wrapper. The importer remains the owner of the SQL transaction and
reparses the workbook for the actual database ingest.

## Daily Rebuild Behaviour

- Rebuilds daily deltas for the whole week from cumulative snapshot rows.
- Consolidates multiple snapshots per day by taking the maximum cumulative totals for that day.
- Carries missing days forward.
- Clamps within-week cumulative decreases to avoid negative daily deltas.
- Replaces the week's `AllianceActivityDaily` rows in a single transaction.

## Implementation Notes

- Missing/blank names are stored as SQL `NULL`.
- Thousands separators are removed before numeric conversion.
- Timestamp handling is UTC-oriented; SQL compatibility currently uses naive UTC values in this importer.
- Transactions roll back on exceptions.
- Blocking import work is offloaded by the upload handler.

## Tests

- Focused route coverage lives in `tests/test_weekly_activity_upload_route.py`.
- Weekly activity audit helper coverage lives in
  `tests/test_weekly_activity_import_audit_service.py`.
- Shared durable audit wrapper coverage lives in `tests/test_import_audit_service.py` and
  `tests/test_import_audit_dal.py`.

## Delivery Notes

- Phase 5B extracted weekly activity routing into `upload_routes/weekly_activity_route.py`.
- Alliance weekly upload was smoke tested successfully on 2026-05-26 after PR 114 was merged and
  pushed to production.
- Task C Slice 6 adopted generic durable audit for weekly activity uploads in mirror PR #187 and
  production PR #495. Production smoke testing on 2026-06-29 confirmed two accepted imports with
  `RowsInSource=816`, `RowsStaged=816`, `RowsWritten=816`, `RowsSkipped=0`, correlation to
  `dbo.AllianceActivitySnapshotHeader` snapshot ids `440` and `441`, and completed parse, SQL
  ingest, and backup phases. The duplicate smoke confirmed `Status=duplicate`,
  `RowsInSource=816`, `RowsSkipped=816`, no external correlation, and completed parse plus
  duplicate ingest phases.
