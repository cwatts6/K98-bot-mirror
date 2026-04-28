# PR Summary — Ark Task 3: Auto-Creation from Calendar

## Overview
This PR completes **Task 3 — Ark auto-creation from calendar** for the Ark automation roadmap.

It extends the Ark lifecycle foundation delivered previously so that Ark calendar rows in
`dbo.EventInstances` can create first-class `ArkMatches` rows and immediately trigger the
standard registration lifecycle.

Core flow now delivered:

**`dbo.EventInstances` → Ark auto-create service → `dbo.ArkMatches` → `ArkRegistrationController.ensure_registration_message(...)`**

---

## Delivered in this PR

### 1) SQL-backed Ark calendar detection
Implemented Ark candidate querying from `dbo.EventInstances` with these guardrails:

- `EventType = 'ark'`
- `IsCancelled = 0`
- deterministic ordering by `StartUTC`, `InstanceID`
- scheduler-safe query window for upcoming/recently-relevant rows

This keeps SQL as the event source of truth and avoids JSON/runtime ownership for auto-create.

### 2) Ark title parsing and date derivation
Implemented parsing for titles in the expected format:

- `Ark <Alliance> <DayName> <HH:MM>`
- Example: `Ark k98A Saturday 20:00`

Extracted values:

- `Alliance`
- `MatchDay`
- `MatchTimeUtc`

Weekend date derivation uses **`EventInstances.EndUTC`** per production rule.

### 3) Missing Ark match creation
When a valid calendar row is found and no Ark match exists for the same:

- `Alliance`
- `ArkWeekendDate`

...the bot creates a new `ArkMatches` row.

Auto-created rows are still normal Ark matches; there is no parallel Ark subtype.

### 4) Calendar lineage persistence
This PR adds Ark match lineage fields so production support and later tasks can trace match origin:

- `CalendarInstanceId`
- `CreatedSource`

Current usage:

- auto-created matches use `CreatedSource = 'calendar_auto'`
- manual create path now stamps `CreatedSource = 'manual'`

### 5) Registration lifecycle integration
After SQL creation, the auto-create flow immediately invokes:

- `ArkRegistrationController.ensure_registration_message(...)`

This preserves the current Ark architecture:

- controller owns registration posting/reposting
- scheduler does not directly build/post registration embeds
- registration state remains SQL-backed on `ArkMatches`

### 6) Duplicate and cancel-safe behavior
Duplicate prevention uses the confirmed business rule:

- only one match per `(Alliance, ArkWeekendDate)`

Scheduler behavior on existing rows:

- existing scheduled/locked/completed match → skip
- existing cancelled match → skip
- cancelled rows are **not reopened automatically**

This preserves manual cancel priority.

### 7) Scheduler integration
Ark auto-create now runs from the existing Ark scheduler ownership path.

This means:

- no parallel Ark scheduler framework was introduced
- auto-create participates in the normal Ark lifecycle tick
- existing visibility refresh/reminder behavior remains in place

---

## Files added / modified

### New
- `ark/ark_auto_create_service.py`
- `sql_schema/dbo.ArkMatches.Alter.CalendarLineage.sql`
- `tests/test_ark_auto_create_service.py`
- `docs/ark/PR_SUMMARY_ARK_TASK3_AUTO_CREATE.md`
- `docs/ark/TASK PACK — Ark Auto-Creation from Calendar handover notes.md`

### Modified
- `ark/dal/ark_dal.py`
- `ark/ark_scheduler.py`
- `commands/ark_cmds.py`
- `ark/registration_messages.py`
- `tests/test_ark_scheduler.py`
- `tests/test_ark_cancel_match.py`

---

## Acceptance criteria status

- [x] Eligible Ark calendar rows detected from SQL
- [x] Cancelled calendar rows ignored
- [x] Title parsing implemented and validated
- [x] Missing Ark matches auto-created
- [x] Duplicate creation prevented across reruns/restarts
- [x] Multiple same-weekend events supported across different alliances
- [x] Auto-created matches immediately enter standard registration lifecycle
- [x] Manual cancel remains authoritative
- [x] Manual create remains available
- [x] Ark match lineage persisted in SQL

---

## Variance from original scope

### A) Added stronger lineage than the minimum required
The original scope asked for assessment of whether lineage fields were needed.

Final delivery includes lineage fields directly:

- `CalendarInstanceId`
- `CreatedSource`

This was added deliberately for production traceability and future-task support.

### B) SQL schema artifact remains local handoff-style in this repo
Engineering standards prefer SQL schema files in the SQL Server repo.

This delivery includes the schema artifact locally in `sql_schema/` so deployment work is explicit
and handoff-ready.

### C) Registration repost semantics were also normalized
While not the main Task 3 objective, follow-up review regression handling also aligned
`upsert_registration_message(...)` force-repost behavior with the shared expected logic.

---

## What remains before production closeout
If implementation review is accepted, the only meaningful remaining work for this task is:

1. **smoke test in the bot environment**
   - seed/confirm a real `EventInstances` Ark row
   - verify match row creation in `ArkMatches`
   - verify registration post appears in the configured registration channel
   - verify rerun does not duplicate the row
   - verify cancelled existing match is skipped

2. **SQL migration deployment sequencing**
   - apply `CalendarInstanceId` / `CreatedSource` schema update first
   - then deploy bot code

No additional subsystem redesign is pending for Task 3 itself.

---

## Recommended smoke test checklist

1. Insert or confirm a future `EventInstances` Ark row.
2. Run scheduler tick / start bot in environment with scheduler enabled.
3. Confirm exactly one `ArkMatches` row exists for `(Alliance, ArkWeekendDate)`.
4. Confirm `CalendarInstanceId` and `CreatedSource='calendar_auto'` are populated.
5. Confirm registration message was created through the normal lifecycle path.
6. Run scheduler again and confirm no duplicate row is created.
7. Cancel the match manually and run scheduler again.
8. Confirm the cancelled row is not reopened/recreated.

---

## Task 4 handoff headline
Task 4 and later Ark work should now assume:

- Ark matches may be manual or calendar-auto-created
- both use the same `ArkMatches` table
- both use the same registration lifecycle controller path
- cancel behavior is shared
- lineage is available in SQL for support/debug/reporting
