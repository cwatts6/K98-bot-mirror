# Phase 2 — Ark DAL + Cache Plan

This document defines required data access operations (DAL) and the cache / JSON persistence plan for Ark of Osiris.

## DAL Principles

- Use the existing DB helpers from `stats_alerts/db.py` (sync + async wrappers).
- All state mutations write to SQL first, then any in-memory caches/Discord messages.
- Every state-changing operation should call `insert_audit_log(...)`.
- Match creation must validate **alliance channel IDs** are configured in `ArkAlliances`. If either channel ID is missing, reject the action and tell the user.

## Status
✅ Largely implemented (Phase 2)
- Core ArkMatches/ArkSignups DAL functions implemented.
- Audit logging in place for match + signup actions.
- `ark_message_state.json` used for registration message refs.

⚠️ Pending (future phases)
- Bans DAL (Phase 8)
- Reminder prefs DAL (Phase 7)
- Results tracking DAL (Phase 9)
- `ark_reminder_state.json` usage (Phase 7)

## Task 2A — Required DAL Operations

> **Note:** These are *stubs/specs* only. SQL implementation comes in Phase 3+.

### ArkAlliances

- `list_alliances(active_only: bool = True) -> list[dict]`
  - Returns `{Alliance, RegistrationChannelId, ConfirmationChannelId, IsActive}`.
- `get_alliance(alliance: str) -> dict | None`
  - Returns alliance row for validation.

### ArkMatches

- `create_match(...) -> int`
  - Args: `alliance, ark_weekend_date, match_day, match_time_utc, signup_close_utc, notes, actor_discord_id`
  - Returns `MatchId`.
  - Must enforce `(Alliance, ArkWeekendDate)` uniqueness.
- `amend_match(...) -> bool`
  - Update day/time/notes (alliance change only if no signups).
- `cancel_match(match_id: int, actor_discord_id: int) -> bool`
  - Set status `Cancelled`.
- `get_match(match_id: int) -> dict | None`
- `list_open_matches(alliance: str | None = None) -> list[dict]`
  - Status in `Scheduled` or `Locked`.

### ArkSignups

- `get_roster(match_id: int) -> list[dict]`
- `add_signup(...) -> int`
  - Args: `match_id, governor_id, governor_name, discord_user_id, slot_type, source, actor_discord_id`
  - Returns `SignupId`.
- `remove_signup(...) -> bool`
  - Args: `match_id, governor_id, status, actor_discord_id`
- `switch_signup_governor(...) -> bool`
  - Switch a governor within the same user.
- `move_signup_slot(...) -> bool`
  - Promote/demote between Player/Sub.
- `mark_checked_in(...) -> bool`
- `mark_emergency_withdraw(...) -> bool`
  - Set status to `Withdrawn`, trigger promotion.
- `find_active_signup_for_weekend(governor_id: int, ark_weekend_date: date, exclude_match_id: int | None = None) -> dict | None`
  - Prevent duplicate signups across alliances for the same Ark weekend.

### ArkBans

- `add_ban(...) -> int`
- `revoke_ban(ban_id: int, actor_discord_id: int) -> bool`
- `list_bans(active_only: bool = True) -> list[dict]`
- `get_active_ban_for(...) -> dict | None`
  - Resolve by `discord_user_id` and/or `governor_id` + `ark_weekend_date`.

### ArkReminderPrefs

- `get_reminder_prefs(discord_user_id: int) -> dict | None`
- `upsert_reminder_prefs(...) -> bool`

### ArkResults

- `set_match_result(...) -> bool`
  - Sets Win/Loss + notes, moves status to `Completed`.

### ArkAuditLog

- `insert_audit_log(...) -> int`

---

## Task 2B — Cache + JSON State Plan

### JSON State Files

**1) `ark_message_state.json`**
```json
{
  "matches": {
    "12345": {
      "registration": {"channel_id": 1095, "message_id": 9001},
      "confirmation": {"channel_id": 1096, "message_id": 9002}
    }
  }
}
```

**2) `ark_reminder_state.json`**
```json
{
  "reminders": {
    "12345|111111111111111111|24h": "2026-03-07T08:00:00Z",
    "12345|111111111111111111|4h": "2026-03-07T20:00:00Z"
  }
}
```

### In-Memory Caches

- `ark_open_match_cache`: `dict[str, list[Match]]` keyed by `Alliance`
- `ark_roster_cache`: `dict[int, Roster]` keyed by `MatchId`
- `governor_cache`: reuse existing governor/registry cache(s)

### Restart Resilience Plan

On startup:

1. Load **open/locked upcoming matches** from SQL.
2. Rehydrate reminder jobs:
   - Use SQL for canonical schedule.
   - Use `ark_reminder_state.json` to avoid duplicates.
3. Reconcile Discord message IDs:
   - If missing, re-post embed and update JSON.
4. Ensure only **one** scheduled task per match/reminder type.

---

## Enforcement Notes

- If `ArkAlliances.RegistrationChannelId` or `ConfirmationChannelId` is NULL for an alliance, **match creation must be blocked** and the user told how to fix it.
- JSON state is **auxiliary**, SQL is canonical.
