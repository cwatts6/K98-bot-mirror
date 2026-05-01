# Phase 7 — Reminder System + User Preferences

## Overview
Phase 7 adds end-to-end Ark reminder delivery with dedupe/restart safety and per-user DM preferences.

Implemented scope:
- Pre-close reminders in registration channel:
  - Daily reminder (20:00 UTC)
  - Final-day reminder (stronger nudge)
- Match-start reminder windows:
  - 24h / 4h / 1h / start
- Check-in reminder:
  - T-12h DM reminder
- `/ark_reminder_prefs` command + UI toggles
- SQL-backed per-user preference persistence
- JSON reminder dedupe/state persistence with restart grace window
- Scheduler logging + failure handling

---

## Status
✅ Implemented and validated in local test suite  
✅ SQL migration applied successfully  
✅ Pre-commit and targeted Ark tests passing

---

## What Was Added

### 1) SQL
- `ArkReminderPrefs` table created/updated with:
  - `DiscordUserId` PK
  - `OptOutAll`
  - `OptOut24h`
  - `OptOut4h`
  - `OptOut1h`
  - `OptOutStart`
  - `OptOutCheckIn12h`
  - `CreatedAtUtc`, `UpdatedAtUtc`
- Index on `OptOutAll`

### 2) Reminder State
- `ark/reminder_state.py`
  - Persisted reminder send ledger
  - Grace-window dedupe (`15m`)
  - Key helpers for DM/channel/daily channel dedupe keys
- Default path aligned with `DATA_DIR/ark_reminder_state.json`

### 3) Scheduler Integration
- `ark/ark_scheduler.py`
  - Added reminder dispatch flow in lifecycle loop
  - Per-match async lock to avoid race duplicates
  - Pre-close registration reminders
  - Confirmation-channel start-window reminders
  - DM reminders with user preference gating
  - DM failure logging with match/type/user context
  - Guarded jump-link generation (no guild_id=0 links)
  - Daily dedupe key includes UTC date so daily reminders can repeat each day pre-close

### 4) Preferences
- `ui/views/ark_reminder_prefs_view.py`
  - Toggle buttons for each preference
  - User guard (only requester can edit)
  - Added `__all__ = ["ArkReminderPrefsView"]`
- `commands/ark_cmds.py`
  - `/ark_reminder_prefs` command
  - Default-seed behavior for first-time users
- DAL additions for `get_reminder_prefs` and `upsert_reminder_prefs`

---

## Reminder Behavior Summary

### Registration channel (pre-close)
- Daily at 20:00 UTC while match is pre-close and not locked/cancelled/completed
- Final-day reminder on signup-close date
- Includes signup jump link when available (and can be required)

### Confirmation/planning channel
- 24h / 4h / 1h / start reminders

### DM reminders
- 24h / 4h / 1h / start + check-in T-12h
- Respect per-user preferences
- Logged failures; dispatch continues for other users

### Dedupe / restart
- Sent reminder keys are persisted in JSON state
- Grace window avoids replay storms and allows controlled catch-up after restart

---

## Tests Added / Updated
- reminder state tests (dedupe + keys + persistence)
- reminder prefs tests
- reminder prefs view tests
- scheduler reminder routing/dedupe/status-gating tests
- scheduler compatibility tests (lock/check-in behavior)

---

## Known Follow-ups (Phase 8 candidates)
1. Optional bulk prefs fetch in DAL (single query per dispatch batch)
2. Optional stronger observability counters/metrics export
3. Optional admin reminder diagnostics command (preview next due reminders)
4. Optional reminder templates/config from SQL (`ArkConfig`) instead of constants
5. Optional cleanup utility for stale reminder keys

---

## Operational Notes
- If legacy root-level `ark_reminder_state.json` exists, migrate to `DATA_DIR`.
- Ensure scheduler starts only once at bot startup.
- For smoke testing, use accelerated SQL windows then restore defaults afterward.

---

## Completion Check
- [x] SQL migration applied
- [x] Bot code merged locally
- [x] Tests passing
- [x] Pre-commit clean
- [x] Ready to open PR and start Phase 8 planning
