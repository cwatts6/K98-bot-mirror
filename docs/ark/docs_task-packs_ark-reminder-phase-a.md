# Ark Reminder System — Phase A: Critical Bug Fixes

> **Task pack version:** 1.0  
> **Date:** 2026-03-26  
> **Prerequisite reading:** Engineering Standards, Codex Execution Guidelines, Development Initiation Statement  
> **Companion analysis:** Ark Reminder Audit (produced prior to this task pack)

---

## Scope

Fix two confirmed bugs in the Ark reminder scheduler. No new features. No behaviour
changes beyond fixing the defects described. No SQL schema changes.

---

## Background

A full reminder audit was completed before this task. Two critical bugs were identified:

1. **Premature daily repost** — the registration embed is being reposted at 20:00 UTC
   for matches whose `RegistrationStartsAtUtc` is in the future. The repost runs against
   all `Scheduled` matches returned by `list_open_matches()`, which does not filter on
   registration start time. There is no guard inside `_run_match_reminder_dispatch`.

2. **`reschedule_match_reminders` is a no-op stub** — `ark/reminders.py` contains a
   function `reschedule_match_reminders` that only logs and returns. It is called from
   the match amend flow. This means that when a match time is changed, time-relative
   reminders (24h, 4h, 1h, start, checkin_12h) are never rescheduled. Already-sent
   state keys remain stale; not-yet-sent reminders fire at the wrong time.

---

## Task A1 — Add `RegistrationStartsAtUtc` guard in `_run_match_reminder_dispatch`

### File to modify
`ark/ark_scheduler.py`

### What to change

Inside `_run_match_reminder_dispatch`, immediately after the block that loads `status`
and exits early for `cancelled`/`completed`, add a guard:

```python
# Guard: do not run any reminder or repost logic until registration is open
starts_at = match.get("RegistrationStartsAtUtc")
if starts_at and ensure_aware_utc(starts_at) > now:
    logger.info(
        "[ARK_SCHED] reminder_dispatch_skip match_id=%s reason=registration_not_open "
        "registration_starts_at_utc=%s",
        match_id,
        ensure_aware_utc(starts_at).isoformat(),
    )
    return
```

### Exact placement

The guard must be inserted **after** `now = _utcnow()` is assigned and **before** the
`close_dt` block and the `if status != "locked"` daily repost block. `now` is already
computed at that point in the function.

### What this fixes

- Daily repost no longer fires for matches that have not opened registration yet.
- Final-day (registration closing) reminder no longer fires before registration opens
  (pathological edge case but also resolved by this guard).

### What this does NOT change

- Any match whose `RegistrationStartsAtUtc` has already passed behaves identically to
  before.
- Any match with a `NULL` `RegistrationStartsAtUtc` is not blocked (the guard is skipped
  if `starts_at` is falsy).

### Logging requirement

Log at `INFO` level with `match_id` and `registration_starts_at_utc` as shown above.
Use the `[ARK_SCHED]` prefix for consistency with surrounding code.

---

## Task A2 — Implement `reschedule_match_reminders`

### File to modify
`ark/reminders.py`

### Current state

```python
async def reschedule_match_reminders(
    *,
    match_id: int,
    match_datetime_utc: datetime,
    signup_close_utc: datetime,
) -> None:
    """
    Ark reminder reschedule hook (Phase 3B stub).
    ...
    """
    logger.info(
        "[ARK_REMINDERS] Reschedule requested for match_id=%s ...",
        match_id,
        ...
    )
```

### What to implement

Replace the stub body with logic that:

1. Loads `ArkReminderState` from its default path.
2. Identifies all state keys for this `match_id` that are time-relative reminder types.
   The types to clear are defined in `ark/reminder_types.py`:
   - `REMINDER_24H` (`"24h"`)
   - `REMINDER_4H` (`"4h"`)
   - `REMINDER_1H` (`"1h"`)
   - `REMINDER_START` (`"start"`)
   - `REMINDER_CHECKIN_12H` (`"checkin_12h"`)
3. Removes all matching keys from `state.reminders` (both channel keys and DM keys
   for this match).
4. Saves the state file if any keys were removed.
5. Logs the result.

### Key format reference

Keys are in one of two formats (from `ark/reminder_state.py`):
- DM key: `"{match_id}|{user_id}|{reminder_type}"`
- Channel key: `"{match_id}|channel:{channel_id}|{reminder_type}"`

Both start with `"{match_id}|"`. The time-relative types are the five constants above.
The daily repost key also starts with the match_id prefix but uses `REMINDER_DAILY`
and includes a date suffix — **do not clear it**, the daily repost is date-keyed and
will naturally re-evaluate.

### Filtering logic

```python
time_relative_types = {
    REMINDER_24H, REMINDER_4H, REMINDER_1H, REMINDER_START, REMINDER_CHECKIN_12H
}
prefix = f"{match_id}|"

def _is_time_relative_key(key: str) -> bool:
    if not key.startswith(prefix):
        return False
    # key format: "{match_id}|...|{reminder_type}" or "{match_id}|...|{type}|{date}"
    parts = key.split("|")
    # reminder_type is always the third segment (index 2) for both DM and channel keys
    return len(parts) >= 3 and parts[2] in time_relative_types
```

### Signature (do not change)

```python
async def reschedule_match_reminders(
    *,
    match_id: int,
    match_datetime_utc: datetime,
    signup_close_utc: datetime,
) -> None:
```

The function is called with keyword arguments from the amend flow. The
`match_datetime_utc` and `signup_close_utc` parameters are retained for future use
(when reminder scheduling becomes proactive). For now they are accepted but not used
beyond logging.

### Logging requirement

```
[ARK_REMINDERS] reschedule match_id={match_id} cleared_keys={n} new_match_dt={iso} new_close_dt={iso}
```

Log at `INFO`. If no keys were cleared, log at `DEBUG` to avoid noise.

---

## Tests to add

**File:** `tests/test_ark_reminder_reschedule.py`

Cover:

1. **`test_reschedule_clears_time_relative_keys`** — populate a mock
   `ArkReminderState.reminders` dict with a mix of DM keys, channel keys, and daily
   keys for match_id=1. Call `reschedule_match_reminders`. Assert that all
   time-relative keys for match 1 are removed and the daily key and other-match keys
   are untouched.

2. **`test_reschedule_no_keys_is_noop`** — call with an empty reminders dict. Assert no
   error and state is unchanged.

3. **`test_guard_blocks_future_registration`** — unit-test `_run_match_reminder_dispatch`
   (or the guard logic extracted into a testable helper) with a match where
   `RegistrationStartsAtUtc` is 24 hours in the future. Assert that the function
   returns early and does not attempt any channel or DM send.

4. **`test_guard_allows_open_registration`** — same as above but with
   `RegistrationStartsAtUtc` 1 hour in the past. Assert the function proceeds past
   the guard.

Tests must not require a live Discord client or SQL connection. Use mocks/fakes.

---

## Acceptance criteria

- [ ] `_run_match_reminder_dispatch` returns early without any send or repost if
  `RegistrationStartsAtUtc` is in the future.
- [ ] `reschedule_match_reminders` removes exactly the five time-relative reminder type
  keys (DM and channel) for the given match_id from `ark_reminder_state.json`.
- [ ] `reschedule_match_reminders` does NOT remove daily repost keys or keys for other
  match IDs.
- [ ] Both functions log at the required level with required fields.
- [ ] All four tests pass.
- [ ] `black`, `ruff`, `pyright`, `pytest` all pass.
- [ ] No changes to any other files outside `ark/ark_scheduler.py`, `ark/reminders.py`,
  and `tests/test_ark_reminder_reschedule.py`.

---

## Files changed

| File | Change type |
|------|-------------|
| `ark/ark_scheduler.py` | Modify — add guard in `_run_match_reminder_dispatch` |
| `ark/reminders.py` | Modify — implement `reschedule_match_reminders` |
| `tests/test_ark_reminder_reschedule.py` | New — four tests |

---

## Do NOT change

- `ark/reminder_state.py` — no changes needed
- `ark/reminder_types.py` — no changes needed
- Any SQL schema
- Any other Python module
- Existing test files
