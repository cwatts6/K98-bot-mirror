# Weekly Activity Importer

Purpose: document the weekly alliance activity Excel import path.

## Main Files

- `DL_bot.py` handles uploads in `ACTIVITY_UPLOAD_CHANNEL_ID`.
- `weekly_activity_importer.py` parses and writes activity snapshots.
- SQL schema lives in `C:\K98-bot-SQL-Server`.
- Tests: `tests/test_weekly_activity_importer.py`.

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

## SQL Writes

The importer writes:

1. `dbo.AllianceActivitySnapshotHeader`
2. `dbo.AllianceActivitySnapshotRow`
3. `dbo.AllianceActivityDelta`
4. `dbo.AllianceActivityDaily`

Validate these objects against the SQL repo before changing importer behaviour.

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

```powershell
python -m pytest -q tests/test_weekly_activity_importer.py
```
