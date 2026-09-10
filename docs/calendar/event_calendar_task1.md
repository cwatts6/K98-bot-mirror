# TASK 1 — Create SQL Schema for Event Calendar ✅ COMPLETED

## Objective
Create SQL tables required to store calendar rules, overrides, generated instances, and sync history.

## Implemented
Created idempotent SQL schema in:

- `sql/calendar_schema.sql`

Created SQL verification script in:

- `sql/tests/verify_calendar_schema.sql`

Added bot-side Task-1 scaffolding + tests:

- `event_calendar/cache_contract.py`
- `event_calendar/service.py`
- `tests/test_calendar_cache_contract.py`
- `tests/test_calendar_service.py`
- `tests/test_calendar_schema_contract.py`

---

## SQL Tables Created

- `dbo.EventRecurringRules`
- `dbo.EventOneOffEvents`
- `dbo.EventOverrides`
- `dbo.EventInstances`
- `dbo.EventSyncLog`

All with:
- stable PKs
- audit timestamps (`CreatedUTC`, `ModifiedUTC` where applicable)
- idempotent creation guards (`IF OBJECT_ID(...) IS NULL`)

---

## PK Strategy Implemented

- Natural source IDs (sheet-owned):
  - `EventRecurringRules.RuleID` (`NVARCHAR(128)`)
  - `EventOneOffEvents.EventID` (`NVARCHAR(128)`)
  - `EventOverrides.OverrideID` (`NVARCHAR(128)`)

- Surrogate generated IDs:
  - `EventInstances.InstanceID` (`BIGINT IDENTITY`)
  - `EventSyncLog.SyncID` (`BIGINT IDENTITY`)

---

## Datetime / Hash Standards Implemented

- Datetime precision: `DATETIME2(0)`
- Hash fields:
  - `SourceRowHash VARBINARY(32)`
  - `EffectiveHash VARBINARY(32)`

---

## Required Indexes Implemented

- `IX_EventInstances_StartUTC`
- `IX_EventInstances_EventType`
- `IX_EventInstances_SourceID`

(guarded with `sys.indexes` checks)

---

## Acceptance Criteria Status

- [x] Tables created successfully  
- [x] PK constraints applied  
- [x] Indexes created  
- [x] Idempotent schema script  
- [x] Added verification script for local rerun checks  
- [x] Added initial Python scaffolding and pytest coverage for Task 2 readiness

TASK 1 — Create SQL Schema for Event Calendar
Objective

Create SQL tables required to store calendar rules, overrides, generated instances, and sync history.

Instructions

Create SQL tables in the ROK_TRACKER database:

dbo.EventRecurringRules
dbo.EventOneOffEvents
dbo.EventOverrides
dbo.EventInstances
dbo.EventSyncLog

Include audit timestamps and stable primary keys.

Add appropriate indexes for lookup performance.

Suggested SQL File
sql/calendar_schema.sql

Required Table Definitions
EventRecurringRules
RuleID (PK)
IsActive
Emoji
Title
EventType
Variant
RecurrenceType
IntervalDays
FirstStartUTC
DurationDays
RepeatUntilUTC
MaxOccurrences
AllDay
Importance
Description
LinkURL
ChannelID
SignupURL
Tags
SortOrder
NotesInternal
CreatedUTC
ModifiedUTC
SourceRowHash
EventOneOffEvents
EventID (PK)
IsActive
Emoji
Title
EventType
Variant
StartUTC
EndUTC
AllDay
Importance
Description
LinkURL
ChannelID
SignupURL
Tags
SortOrder
NotesInternal
CreatedUTC
ModifiedUTC
SourceRowHash
EventOverrides
OverrideID (PK)
IsActive
TargetKind
TargetID
TargetOccurrenceStartUTC
ActionType
NewStartUTC
NewEndUTC
NewTitle
NewVariant
NewEmoji
NewImportance
NewDescription
NewLinkURL
NewChannelID
NewSignupURL
NewTags
NotesInternal
CreatedUTC
ModifiedUTC
SourceRowHash
EventInstances

Generated events.

InstanceID (PK)
SourceKind
SourceID
StartUTC
EndUTC
AllDay
Emoji
Title
EventType
Variant
Importance
Description
LinkURL
ChannelID
SignupURL
Tags
SortOrder
IsCancelled
GeneratedUTC
EffectiveHash

Indexes required:

IX_EventInstances_StartUTC
IX_EventInstances_EventType
IX_EventInstances_SourceID
EventSyncLog
SyncID (PK)
SyncStartedUTC
SyncCompletedUTC
SourceName
Status
RowsReadRecurring
RowsReadOneOff
RowsReadOverrides
RowsUpsertedRecurring
RowsUpsertedOneOff
RowsUpsertedOverrides
InstancesGenerated
ErrorMessage
Acceptance Criteria

Tables created successfully

PK constraints applied

indexes created

idempotent schema script
