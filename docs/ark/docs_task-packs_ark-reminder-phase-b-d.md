# Ark Reminder System — Phase B+D: R3 Retime & Remove R9/R13

> **Task pack version:** 1.0  
> **Date:** 2026-03-26  
> **Prerequisite:** Phase A deployed and tested.

---

## Scope

Three changes, all in `ark/ark_scheduler.py` and `ark/reminder_types.py`:

1. **Phase B** — Replace the `final_day` reminder with a proper "registration closing
   soon" reminder that fires 1 hour before `SignupCloseUtc`, sends `@everyone`, and
   includes a jump link to the current registration message.
2. **Phase D** — Remove `REMINDER_24H` from both the channel and DM dispatch windows.
   Remove `REMINDER_24H` from the DM opt-out check path (it will remain as an unused
   constant for now — do not delete the SQL column or the constant).

No SQL schema changes. No new files except the test file.

---

## Background

- The existing `final_day` reminder fires when `close_dt.date() == now.date()` which
  can collide with the 20:00 UTC daily repost on the same day, creating two messages
  in quick succession.
- The replacement fires at `close_dt - 1h` which is a clean, unambiguous time.
- `@everyone` is needed because unsigned players may have missed all previous posts.
- A jump link to the registration message makes it easy to sign up directly from the
  reminder.
- `REMINDER_24H` (channel) overlaps with the Saturday daily repost of the registration
  message and is redundant. The 24h DM is similarly removed.

---

## Task B1 — Add `REMINDER_REGISTRATION_CLOSE_1H` constant

### File to modify
`ark/reminder_types.py`

### Change

Add one new constant. Keep all existing constants unchanged.

```python
REMINDER_REGISTRATION_CLOSE_1H = "registration_close_1h"
```

Add it to the file in a logical grouping — below the existing `REMINDER_DAILY` and
`REMINDER_FINAL_DAY` constants since it is also a registration-channel type.

Do NOT add it to `ALL_DM_REMINDER_TYPES` — this is a channel reminder, not a DM type.

---

## Task B2 — Add `announce` parameter to `_send_channel_reminder`

### File to modify
`ark/ark_scheduler.py`

### Change

`_send_channel_reminder` currently sends with no `allowed_mentions`:

```python
await channel.send(content=text, embed=embed)
```

Add an `announce: bool = False` parameter and pass `allowed_mentions` conditionally:

```python
async def _send_channel_reminder(
    *,
    client,
    state: ArkSchedulerState,
    match: dict[str, Any],
    reminder_type: str,
    channel_id: int,
    text: str,
    scheduled_for: datetime,
    dedupe_key: str | None = None,
    announce: bool = False,          # ← new parameter
) -> bool:
    ...
    await channel.send(
        content=text,
        embed=embed,
        allowed_mentions=discord.AllowedMentions(everyone=True) if announce else discord.AllowedMentions.none(),
    )
```

All existing call sites pass `announce=False` by default — no other changes needed at
call sites except the new R3 call (Task B3).

---

## Task B3 — Replace `final_day` block with `registration_close_1h` block

### File to modify
`ark/ark_scheduler.py`

### Remove

The entire `final_day` block inside `_run_match_reminder_dispatch` — the block that
checks `close_dt.date() == now.date()` and calls `_send_channel_reminder` with
`reminder_type="final_day"`.

### Replace with

A new block that fires at `close_dt - 1 hour`, uses `@everyone`, and includes a
Discord message jump URL in the embed.

```python
from ark.reminder_types import REMINDER_REGISTRATION_CLOSE_1H  # add to imports

# Registration closing soon — fires 1h before SignupCloseUtc with @everyone
if close_dt and now < close_dt:
    close_1h_sched = ensure_aware_utc(close_dt - timedelta(hours=1))
    if now >= close_1h_sched and (now - close_1h_sched) <= REMINDER_GRACE:
        from ark.reminder_state import make_channel_key  # already imported
        close_1h_key = make_channel_key(
            int(match["MatchId"]),
            int(reg_channel_id),
            REMINDER_REGISTRATION_CLOSE_1H,
        )
        if state.reminder_state.should_send_with_grace(
            key=close_1h_key,
            scheduled_for=close_1h_sched,
            now=now,
            grace=REMINDER_GRACE,
        ):
            # Build jump URL if registration message ref is available
            reg_msg_link: str | None = None
            reg_cid = int(match.get("RegistrationChannelId") or 0)
            reg_mid = int(match.get("RegistrationMessageId") or 0)
            if reg_cid and reg_mid:
                reg_channel_obj = client.get_channel(reg_cid)
                guild_id = getattr(
                    getattr(reg_channel_obj, "guild", None), "id", None
                )
                if guild_id:
                    reg_msg_link = (
                        f"https://discord.com/channels/{guild_id}/{reg_cid}/{reg_mid}"
                    )

            link_line = f"\n👉 {reg_msg_link}" if reg_msg_link else ""
            text = (
                f"⚠️ **Ark signups close in 1 hour — {match.get('Alliance', '')}!**"
                f"{link_line}"
            )
            sent = await _send_channel_reminder(
                client=client,
                state=state,
                match=match,
                reminder_type=REMINDER_REGISTRATION_CLOSE_1H,
                channel_id=int(reg_channel_id),
                text=text,
                scheduled_for=close_1h_sched,
                dedupe_key=close_1h_key,
                announce=True,
            )
            if sent:
                logger.info(
                    "[ARK_REGISTRATION] close_1h_reminder_sent match_id=%s channel_id=%s",
                    int(match["MatchId"]),
                    int(reg_channel_id),
                )
```

### Import additions required

Ensure `REMINDER_REGISTRATION_CLOSE_1H` is imported at the top of `ark_scheduler.py`
alongside the other `REMINDER_*` constants:

```python
from ark.reminder_types import (
    REMINDER_1H,
    REMINDER_4H,
    REMINDER_24H,           # keep for now — used in windows list until Phase D
    REMINDER_CHECKIN_12H,
    REMINDER_DAILY,
    REMINDER_REGISTRATION_CLOSE_1H,   # ← add
    REMINDER_START,
)
```

Also ensure `REMINDER_FINAL_DAY` is **removed** from the import list if it was
previously imported. Check `ark/reminder_types.py` — `REMINDER_FINAL_DAY` constant
should remain in the file (do not delete it) but it no longer needs to be imported
in `ark_scheduler.py`.

---

## Task D1 — Remove REMINDER_24H from dispatch windows

### File to modify
`ark/ark_scheduler.py`

### Change

In `_run_match_reminder_dispatch`, find the `windows` list:

```python
windows = [
    (REMINDER_24H, timedelta(hours=24)),
    (REMINDER_4H, timedelta(hours=4)),
    (REMINDER_1H, timedelta(hours=1)),
    (REMINDER_START, timedelta(hours=0)),
]
```

Remove the `REMINDER_24H` entry:

```python
windows = [
    (REMINDER_4H, timedelta(hours=4)),
    (REMINDER_1H, timedelta(hours=1)),
    (REMINDER_START, timedelta(hours=0)),
]
```

This removes both the channel reminder and the DM reminder for 24h, since both are
driven by the same `windows` loop.

### What to leave unchanged

- `REMINDER_24H` constant in `ark/reminder_types.py` — leave it.
- `OptOut24h` column in `ArkReminderPrefs` — leave it (no SQL change).
- `is_dm_allowed` in `ark/reminder_prefs.py` — leave it.
- Any existing `24h` keys already stored in `ark_reminder_state.json` — they become
  harmless orphans and will never match a new send attempt.

### Add deprecation comment

Above the `REMINDER_24H` constant in `ark/reminder_types.py`, add:

```python
# REMINDER_24H: retained for state-key compatibility but no longer dispatched.
# The 24h channel reminder was removed (overlaps with daily registration repost).
# The 24h DM was removed at the same time.
REMINDER_24H = "24h"
```

---

## Tests to add

**File:** `tests/test_ark_reminder_phase_bd.py`

1. **`test_close_1h_reminder_fires_in_window`** — mock a match with `SignupCloseUtc`
   set to `now + 45min`. Assert the `registration_close_1h` key is passed to
   `should_send_with_grace` and `_send_channel_reminder` is called with
   `announce=True`.

2. **`test_close_1h_reminder_does_not_fire_before_window`** — same match but `now`
   is 2 hours before close. Assert `_send_channel_reminder` is NOT called.

3. **`test_close_1h_reminder_does_not_fire_after_close`** — `now` is 10 minutes after
   `close_dt`. Assert not called.

4. **`test_close_1h_includes_jump_link_when_ref_available`** — mock a match with
   `RegistrationChannelId` and `RegistrationMessageId` set. Mock
   `client.get_channel()` to return a channel object with `guild.id = 12345`. Assert
   the `text` passed to `channel.send` contains
   `"https://discord.com/channels/12345/"`.

5. **`test_close_1h_omits_link_when_no_ref`** — same but `RegistrationMessageId` is
   `None`. Assert no URL in text.

6. **`test_24h_window_not_in_dispatch`** — assert `REMINDER_24H` does not appear in the
   `windows` list in `_run_match_reminder_dispatch` (import the function and inspect
   its local `windows` list, or test that no DM/channel send is attempted at T-24h).

 all mock match dicts must use proper Python types
 from datetime import UTC, datetime, date, timedelta

# Correct — use datetime objects, not strings
match = {
    "MatchId": 1,
    "Alliance": "k98A",
    "ArkWeekendDate": date(2026, 3, 28),           # datetime.date, not a string
    "MatchDay": "Sat",
    "MatchTimeUtc": datetime(2026, 3, 28, 11, 0, tzinfo=UTC).time(),
    "SignupCloseUtc": datetime(2026, 3, 28, 9, 0, tzinfo=UTC),  # datetime, not string
    "RegistrationStartsAtUtc": datetime(2026, 3, 24, 12, 0, tzinfo=UTC),
    "RegistrationChannelId": 111,
    "RegistrationMessageId": 222,
    "ConfirmationChannelId": 333,
}

---

## Acceptance criteria

- [ ] `registration_close_1h` fires at `SignupCloseUtc - 1h` ± 15 min grace.
- [ ] It sends `@everyone` via `allowed_mentions=discord.AllowedMentions(everyone=True)`.
- [ ] It includes a jump URL when `RegistrationChannelId` + `RegistrationMessageId` are
  present on the match row.
- [ ] It is deduped via `make_channel_key` with `REMINDER_REGISTRATION_CLOSE_1H` type.
- [ ] `REMINDER_24H` no longer appears in the `windows` list.
- [ ] No 24h channel or DM reminder is sent.
- [ ] `final_day` block is fully removed.
- [ ] `REMINDER_FINAL_DAY` constant remains in `reminder_types.py` but is not imported
  in `ark_scheduler.py`.
- [ ] `REMINDER_24H` constant remains in `reminder_types.py` with deprecation comment.
- [ ] All six tests pass.
- [ ] `black`, `ruff`, `pyright`, `pytest` all pass.

---

## Files changed

| File | Change type |
|------|-------------|
| `ark/reminder_types.py` | Modify — add `REMINDER_REGISTRATION_CLOSE_1H`; add deprecation comment to `REMINDER_24H` |
| `ark/ark_scheduler.py` | Modify — replace `final_day` block, add `announce` param, remove `REMINDER_24H` from `windows` |
| `tests/test_ark_reminder_phase_bd.py` | New — six tests |

---

## Do NOT change

- `ark/reminder_state.py`
- `ark/reminder_prefs.py`
- Any SQL schema
- Any other module

Note: _send_channel_reminder is currently synchronous. 
Phase C will make it async. 
The call added in this task already uses await _send_channel_reminder(...) — this is intentional and forward-compatible. 
Do not remove the await.
