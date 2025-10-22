# weekly_activity_importer

This module ingests the weekly alliance activity Excel export (1198_alliance_activity.xlsx),
stores snapshot header/rows, computes snapshot deltas vs the *previous* snapshot for the same week,
and rebuilds daily deltas for the week from cumulative snapshot rows.

## Expected Excel columns (tolerant matching)
The importer looks for the following logical columns (matching is tolerant to whitespace,
non-breaking spaces and case differences). Required logical names:

- GovernorID
- Name
- Alliance
- Power
- Kill Points
- Help Times
- Rss Trading
- Building
- Tech Donation

If an exact header name is not present, the importer performs case/whitespace-insensitive matching to find a suitable column.

## Deduplication
Files are deduplicated by (WeekStartUtc, SourceFileSha1) where `SourceFileSha1` is the SHA-1 of the uploaded file bytes (VARBINARY(20) in SQL). If a duplicate is detected, ingest_weekly_activity_excel returns (0, 0).

## What the importer writes
1. dbo.AllianceActivitySnapshotHeader
   - metadata about the upload (SnapshotTsUtc, WeekStartUtc, SourceFileSha1, Row_Count, etc).

2. dbo.AllianceActivitySnapshotRow
   - per-governor cumulative totals for the snapshot (including BuildingTotal and TechDonationTotal).

3. dbo.AllianceActivityDelta
   - per-governor delta between this snapshot and the previous snapshot for the same week.
   - Note: zero-delta rows are intentionally retained for auditing/history.

4. dbo.AllianceActivityDaily (rebuilt)
   - The importer recomputes daily deltas for the whole week from cumulative snapshot rows and replaces
     the week's rows in dbo.AllianceActivityDaily in a single transaction.

## Daily rebuild behaviour
- For each governor over the week (Monday..Sunday):
  - The importer consolidates multiple snapshots per day by taking the maximum cumulative totals for that day.
  - Missing days carry forward the previous day's cumulative (or 0 on Monday).
  - If cumulative values decrease within the week (e.g., counter reset or data cleanup), decreases are clamped to the previous value (monotonic non-decreasing), and resulting daily deltas for that day become 0.
- The week is replaced in the AllianceActivityDaily table in a single delete + insert operation.

## Notes / Implementation details
- GovernorName and AllianceTag: missing/blank names are stored as SQL NULL (Python None) rather than the literal `"nan"`.
- Number parsing: thousands separators (commas) are removed before numeric conversion.
- Timezones: the importer expects timestamps in UTC and normalizes/compares WeekStartUtc using naive UTC datetimes for SQL compatibility.
- Transaction safety: the importer explicitly rolls back the DB transaction on exceptions and logs the error.

## Testing
Unit tests are provided under `tests/test_weekly_activity_importer.py`. They cover parsing, trimming, thousands-separator handling, the drop of invalid GovernorID rows, and the weekly rebuilder logic using a mocked DB cursor.
