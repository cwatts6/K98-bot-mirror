# Phase 6 — Signup Close + Confirmation Embed + Check-in + Emergency

## Overview
Phase 6 completes the match lifecycle after signup close:
- Match lock at `signup_close_utc`
- Confirmation embed posting
- Check-in activation at T-12h
- Emergency withdraw flow (confirmation embed only)

All state changes write to SQL first, then update Discord embeds.

---

## Status
✅ Implemented (Phase 6)
- Scheduler posts confirmation embed at close.
- Registration embed shows “Signups Closed” and disables buttons.
- Confirmation message IDs stored in SQL + `ark_message_state.json`.
- Check-in button hidden until T-12h; then enabled.
- Emergency withdraw triggers auto-promotion and logs updates.

---

## Task 6A — Signup Close Job + Confirmation Embed

### Behavior
At `signup_close_utc`:
1. Set match `Status = Locked`
2. Edit registration embed to “Signups Closed��
3. Post confirmation embed to `ArkAlliances.ConfirmationChannelId`
4. Persist confirmation message IDs in:
   - SQL (`ArkMatches.ConfirmationChannelId`, `ArkMatches.ConfirmationMessageId`)
   - JSON (`ark_message_state.json`)
5. Write `match_lock` audit log

### Acceptance Criteria
✅ Triggered automatically  
✅ Embed posted and stored  
✅ Survives restart via JSON/SQL

---

## Task 6B — Check-in System (T-12h)

### Behavior
- Check-in button is **hidden** until T-12h
- At T-12h:
  - Confirmation embed updated with check-in button
  - Checked-in roster displayed
- Clicking check-in:
  - Sets `CheckedIn = 1`
  - Sets `CheckedInAtUtc`
  - Writes `check_in` audit log

### Acceptance Criteria
✅ Check-in cannot be performed early  
✅ Checked-in roster displayed on confirmation embed  
✅ Audit log written

---

## Task 6C — Emergency Withdraw (Confirmation Embed Only)

### Behavior
- Button appears only on confirmation embed
- Click:
  - Marks signup status `Withdrawn`
  - Triggers auto-promotion of earliest sub
  - Updates confirmation embed with “Updates” field
  - Writes `emergency_withdraw` audit log

### Acceptance Criteria
✅ Requires confirmation embed  
✅ Auto-promotion occurs  
✅ Updates field tracks emergency action  

---

## Notes / Implementation Details

- Scheduler: `ark/ark_scheduler.py`
- Confirmation flow: `ark/confirmation_flow.py`
- Embed updates: `ark/embeds.py`
- View: `ArkConfirmationView` in `ui/views/ark_views.py`
- Message refs: `ark_message_state.json`
- SQL fields: `ArkMatches.ConfirmationChannelId`, `ArkMatches.ConfirmationMessageId`

---

## Tests Added
- Check-in flow (single + multi governor selection)
- Emergency withdraw flow (promotion + updates field)
- Confirmation embed snapshot for Updates field
- Scheduler behavior:
  - T-12h activation
  - Locked matches not re-locked

## SQL Reset (restore defaults after smoke testing)

Use this after accelerated testing to restore **ArkConfig** defaults:

sql
UPDATE dbo.ArkConfig
SET
    AnchorWeekendDate = '2026-03-07',
    FrequencyWeekends = 2,
    AllowedDaysJson = N'["Saturday","Sunday"]',
    AllowedTimeSlotsJson = N'[
      {"day":"Saturday","times":["11:00","13:00","14:00","15:00","20:00"]},
      {"day":"Sunday","times":["04:00","12:00","14:00","20:00"]}
    ]',
    SignupCloseDay = 'Friday',
    SignupCloseTimeUtc = '23:00:00',
    PlayersCap = 30,
    SubsCap = 15,
    CheckInActivationOffsetHours = 12,
    ReminderIntervalsHoursJson = N'[24,4,1,0]',
    ReminderDailyNudgeEnabled = 1,
    UpdatedAtUtc = SYSUTCDATETIME();

## SQL Cleanup (parameterized)
remove test matches:
DECLARE @MatchId bigint = 7; -- set match id to clean

DELETE FROM dbo.ArkAuditLog WHERE MatchId = @MatchId;
DELETE FROM dbo.ArkSignups WHERE MatchId = @MatchId;
DELETE FROM dbo.ArkMatches WHERE MatchId = @MatchId;

/* =========================================
   Ark Match Reset + Reseed Script (with signups)
   ========================================= */

DECLARE @MatchId bigint = 7;  -- << set match id to reset
DECLARE @Alliance nchar(255) = N'Hlks'; -- << set alliance
DECLARE @ArkWeekendDate date = '2026-02-28'; -- << set test weekend date
DECLARE @MatchDay char(3) = 'Sat'; -- Sat or Sun
DECLARE @MatchTimeUtc time(0) = '11:35'; -- << set test time
DECLARE @SignupCloseUtc datetime2(0) = DATEADD(minute, -1, SYSUTCDATETIME()); -- force close

-- Sample seeded signups
DECLARE @PlayerGovernorId bigint = 2441482;
DECLARE @PlayerName nvarchar(64) = N'Chrislos';
DECLARE @PlayerDiscordId bigint = 559076207627468807; -- replace with real user id

DECLARE @SubGovernorId bigint = 2510418;
DECLARE @SubName nvarchar(64) = N'Scrooge M';
DECLARE @SubDiscordId bigint = 559076207627468807; -- replace with real user id

-- 1) Remove dependent rows
DELETE FROM dbo.ArkAuditLog WHERE MatchId = @MatchId;
DELETE FROM dbo.ArkSignups WHERE MatchId = @MatchId;

-- 2) Remove the match itself
DELETE FROM dbo.ArkMatches WHERE MatchId = @MatchId;

-- 3) Recreate a clean match with same MatchId
SET IDENTITY_INSERT dbo.ArkMatches ON;

INSERT INTO dbo.ArkMatches
    (MatchId, Alliance, ArkWeekendDate, MatchDay, MatchTimeUtc, SignupCloseUtc, Status, Notes, CreatedAtUtc, UpdatedAtUtc,
     ConfirmationChannelId, ConfirmationMessageId)
VALUES
    (@MatchId, @Alliance, @ArkWeekendDate, @MatchDay, @MatchTimeUtc, @SignupCloseUtc, 'Scheduled', NULL,
     SYSUTCDATETIME(), SYSUTCDATETIME(), NULL, NULL);

SET IDENTITY_INSERT dbo.ArkMatches OFF;

-- 4) Seed signups
INSERT INTO dbo.ArkSignups
    (MatchId, GovernorId, GovernorNameSnapshot, DiscordUserId, SlotType, Status,
     CheckedIn, CheckedInAtUtc, Source, CreatedAtUtc, UpdatedAtUtc)
VALUES
    (@MatchId, @PlayerGovernorId, @PlayerName, @PlayerDiscordId, 'Player', 'Active',
     0, NULL, 'Admin', SYSUTCDATETIME(), SYSUTCDATETIME()),

    (@MatchId, @SubGovernorId, @SubName, @SubDiscordId, 'Sub', 'Active',
     0, NULL, 'Admin', DATEADD(second, 1, SYSUTCDATETIME()), DATEADD(second, 1, SYSUTCDATETIME()));

-- 5) Optional: lock immediately (if you want confirmation embed to post right away)
-- UPDATE dbo.ArkMatches
-- SET Status = 'Locked', UpdatedAtUtc = SYSUTCDATETIME()
-- WHERE MatchId = @MatchId;

SELECT * FROM dbo.ArkMatches WHERE MatchId = @MatchId;
SELECT * FROM dbo.ArkSignups WHERE MatchId = @MatchId ORDER BY CreatedAtUtc ASC;
