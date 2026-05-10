# TASK 2 — Build Google Sheets → SQL Sync Module ✅ COMPLETED

## Objective
Load Google Sheets data into SQL source tables with validation, normalization, hash-based change detection, and graceful failure handling.

## Implemented

### Module
- `event_calendar/sheets_sync.py`

### Core functions
- `fetch_sheet_csv()`
- `parse_recurring_rules()`
- `parse_oneoff_events()`
- `parse_overrides()`
- `upsert_sql_rows()`
- `sync_sheets_to_sql()`

### Service integration
- `event_calendar/service.py` now calls `sync_sheets_to_sql()` and stores status/last result.

### Admin controls (wired)
- `/calendar_refresh`
- `/calendar_status`

### Config
- `constants.py`:
  - `EVENT_CALENDAR_SHEET_ID = os.getenv("EVENT_CALENDAR_SHEET_ID", "").strip() or None`

### Test coverage
- `tests/test_sheets_sync_parsers.py`
- `tests/test_sheets_sync_flow.py`
- `tests/test_calendar_service.py` (updated for live sync path)

### SQL smoke scripts
- `sql/tests/verify_calendar_sync_smoke.sql`
- `sql/tests/verify_calendar_source_counts.sql`

---

## Validation/Normalization rules implemented

- Booleans normalized from common truthy/falsey text forms.
- Datetimes normalized to UTC and truncated to `datetime2(0)` precision.
- Tags normalized to comma-separated canonical string (trimmed + deduped).
- Whitespace trimmed; empty strings normalized to NULL where appropriate.
- Required columns validated per tab.
- Required field and basic logical checks applied (e.g. `end > start`).

---

## Hash-based upsert behavior

- Row hash computed from canonical normalized row payload using SHA-256.
- Hash stored in `SourceRowHash` (`VARBINARY(32)`).
- Existing row updated only when hash changes.
- Unchanged rows skipped.

---

## Failure behavior implemented

On fetch/parse/validation failure:
- SQL source tables remain unchanged.
- Failure status written to `EventSyncLog`.
- Structured failure result returned from service/sync.
- Telemetry event emitted with error details.

---

## Acceptance criteria status

- [x] Rows loaded into SQL source tables
- [x] Schema/row validation enforced
- [x] Hash comparison prevents unnecessary updates
- [x] Sync log populated (success/failure)
- [x] Admin refresh/status controls available
