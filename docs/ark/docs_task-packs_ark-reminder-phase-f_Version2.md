# Ark Reminder System — Phase F: Cancel Notification DM

> **Task pack version:** 1.1 — amended post Phase E
> **Date:** 2026-03-26
> **Prerequisite:** Phase A deployed.

---

## Scope

When an Ark match is cancelled by an admin, send a DM to every currently active
signed-up player informing them of the cancellation. Best-effort, per-user
deduplication via `ArkReminderState`, no opt-out. No SQL schema changes.

---

## Background

`cancel_match` in `ark/dal/ark_dal.py` updates the match status. It is called from a
command handler. The command handler must:

1. Load the roster **before** calling `cancel_match`.
2. After cancellation succeeds, dispatch DMs to all active roster members.

The cancel DM is one-time and informational. Players cannot opt out.

---

## ← AMENDED: Deduplication approach — ArkReminderState, not SQL

Unlike Phase E's mention message (which uses in-memory `published_at_utc` state and
has no restart-safe dedup guard), Phase F's cancel DM **is** deduplication-guarded
via `ArkReminderState` key tracking. This is intentional — cancel DMs must survive
bot restarts without double-sending.

Do not add a SQL flag for Phase F deduplication. The `ArkReminderState` JSON store
with per-user keys is the correct mechanism here and is consistent with the pattern
established in Phase A.

---

## ← AMENDED: Test patch path convention

Follow the convention established across Phases B/C/D/E:

- Patch symbols in `ark/reminders.py` as: `patch("ark.reminders.<symbol>")`
- Patch DAL functions as: `patch("ark.reminders.ArkReminderState")` or via the
  module they are imported into
- Do not patch at the source module path if the import is local to `ark.reminders`

---

## Task F0 — Fix `cancel_match_reminders` to use `ArkReminderState`

### File to modify
`ark/reminders.py`

### Problem (confirmed from Phase A audit)

`cancel_match_reminders` currently uses `ArkJsonState` to clear reminder state.
`ArkJsonState.reminders` is a **different dict** from `ArkReminderState.reminders`.
Clearing `ArkJsonState.reminders` does not clear the keys that
`_run_match_reminder_dispatch` uses to check `state.reminder_state.was_sent(key)`.
This means after a cancel, time-relative reminder keys in `ArkReminderState` are
never cleared, so reminders can still fire for a cancelled match.

### Fix — convert to synchronous, use `ArkReminderState`

```python
from ark.reminder_state import ArkReminderState

def cancel_match_reminders(match_id: int) -> bool:
    """
    Remove reminder state for a match so reminders don't re-send after cancel.

    Returns True if any reminder entries were removed.
    Uses ArkReminderState (the scheduler's authoritative reminder store).
    Synchronous — ArkReminderState.load() and .save() are synchronous.
    """
    state = ArkReminderState.load()
    prefix = f"{match_id}|"
    before = len(state.reminders)
    state.reminders = {
        key: val for key, val in state.reminders.items()
        if not key.startswith(prefix)
    }
    changed = len(state.reminders) != before
    if changed:
        state.save()
        logger.info("[ARK_REMINDERS] Cleared reminder state for match_id=%s", match_id)
    return changed
```

### ← AMENDED: Call site search required

`cancel_match_reminders` is currently `async def` and may be `await`-ed at call
sites. Before finalising, search the entire codebase for all call sites:

```
grep -r "cancel_match_reminders" --include="*.py"
```

For every call site found:
- If it uses `await cancel_match_reminders(...)` — remove the `await` (it is now sync)
- If it imports `cancel_match_reminders` from `ark.reminders` — no import change needed
- Log each call site found and confirm it compiles after the `await` removal

### Import changes in `ark/reminders.py`

- Remove: `from ark.state.ark_state import ArkJsonState`
  (only if `ArkJsonState` is not used elsewhere in the file after this change)
- Add: `from ark.reminder_state import ArkReminderState`
  (may already be present from Phase A's `reschedule_match_reminders` — check before
  adding a duplicate import)

---

## Task F1 — New function `dispatch_cancel_dms`

### File to modify
`ark/reminders.py`

### Add new imports required

```python
from typing import Any
import discord
```

`ArkReminderState` will already be imported after Task F0.

### Implementation

```python
async def dispatch_cancel_dms(
    *,
    client,
    match_id: int,
    match: dict[str, Any],
    roster: list[dict[str, Any]],
) -> dict[str, int]:
    """
    Send a cancellation DM to every active signed-up player for a match.

    Deduplication is per-user via ArkReminderState keys — safe across bot restarts.
    No opt-out: cancellation DMs are always sent.

    Returns counters: {"attempted": n, "sent": n, "skipped_dedupe": n, "failed": n}
    """
    counters: dict[str, int] = {
        "attempted": 0,
        "sent": 0,
        "skipped_dedupe": 0,
        "failed": 0,
    }

    reminder_state = ArkReminderState.load()
    alliance = str(match.get("Alliance") or "Unknown")

    for row in roster:
        if (row.get("Status") or "").lower() != "active":
            continue
        uid = row.get("DiscordUserId")
        if not uid:
            continue

        user_id = int(uid)
        dkey = f"{match_id}|{user_id}|cancelled"

        if reminder_state.was_sent(dkey):
            counters["skipped_dedupe"] += 1
            continue

        counters["attempted"] += 1

        embed = discord.Embed(
            title="❌ Ark Match Cancelled",
            description=f"The **{alliance}** Ark match has been cancelled.",
            color=discord.Color.red(),
        )
        governor_name = str(row.get("GovernorNameSnapshot") or "")
        if governor_name:
            embed.add_field(name="Your Governor", value=governor_name, inline=False)

        try:
            user = await client.fetch_user(user_id)
            await user.send(embed=embed)
            reminder_state.mark_sent(dkey)
            counters["sent"] += 1
            logger.info(
                "[ARK_CANCEL_DM] sent match_id=%s user_id=%s governor=%s",
                match_id,
                user_id,
                governor_name,
            )
        except discord.Forbidden:
            logger.info(
                "[ARK_CANCEL_DM] dm_blocked match_id=%s user_id=%s",
                match_id,
                user_id,
            )
            # Mark as sent to prevent retry spam — user has DMs disabled
            reminder_state.mark_sent(dkey)
            counters["failed"] += 1
        except Exception:
            logger.exception(
                "[ARK_CANCEL_DM] failed match_id=%s user_id=%s",
                match_id,
                user_id,
            )
            counters["failed"] += 1
            # Do NOT mark as sent on unexpected failure — allow retry

    reminder_state.save()

    logger.info(
        "[ARK_CANCEL_DM] dispatch_complete match_id=%s attempted=%s sent=%s "
        "skipped=%s failed=%s",
        match_id,
        counters["attempted"],
        counters["sent"],
        counters["skipped_dedupe"],
        counters["failed"],
    )
    return counters
```

---

## Task F2 — Call `dispatch_cancel_dms` from the cancel command handler

### File to locate

**Search first** — do not assume the file path:

```
grep -r "cancel_match" commands/ --include="*.py" -l
grep -r "cancel_match" ark/ --include="*.py" -l
```

The cancel match slash command will call `cancel_match` from `ark.dal.ark_dal`.
Locate the command handler file before making any changes.

### Required sequence in the command handler

```python
# 1. Load roster and match BEFORE cancelling
roster = await get_roster(match_id)
match = await get_match(match_id)
if not match:
    # ... handle not found
    return

# 2. Cancel
ok = await cancel_match(match_id=match_id, actor_discord_id=actor_discord_id)
if not ok:
    # ... error response
    return

# 3. Dispatch cancel DMs — best-effort, must not block or fail the command
from ark.reminders import dispatch_cancel_dms
try:
    await dispatch_cancel_dms(
        client=ctx.bot,       # or interaction.client depending on command style
        match_id=match_id,
        match=match,
        roster=roster,
    )
except Exception:
    logger.exception("[ARK_CMD] cancel_dm_dispatch_failed match_id=%s", match_id)
```

The DM dispatch must not block the command response. If the roster is large this
could take a few seconds — confirm the command uses `safe_defer` before the DM
loop if not already deferred.

---

## Tests to add

**File:** `tests/test_ark_cancel_dm.py`

### Patch path convention

Follow Phase E convention — patch at the module where the symbol is used:

```python
patch("ark.reminders.ArkReminderState")
patch("ark.reminders.discord")   # if needed for Forbidden
```

### Test list

1. **`test_cancel_dm_sent_to_active_players`** — roster with two active players with
   Discord IDs. Assert `user.send` called twice with embeds containing
   "Cancelled".

2. **`test_cancel_dm_skips_inactive_players`** — one active, one inactive. Assert
   `user.send` called once.

3. **`test_cancel_dm_skips_players_without_discord_id`** — player with
   `DiscordUserId=None`. Assert not attempted.

4. **`test_cancel_dm_deduplication`** — pre-populate `ArkReminderState.reminders`
   with one player's cancel key already marked sent. Assert only the other player
   is attempted.

5. **`test_cancel_dm_forbidden_is_marked_sent`** — mock `user.send` to raise
   `discord.Forbidden`. Assert key is marked sent (no retry), counter shows
   `failed=1`.

6. **`test_cancel_dm_unexpected_exception_not_marked_sent`** — mock `user.send` to
   raise generic `Exception`. Assert key is NOT marked sent (retry allowed), counter
   shows `failed=1`.

7. **`test_cancel_match_reminders_uses_reminder_state`** — call
   `cancel_match_reminders` with a pre-populated `ArkReminderState` (not
   `ArkJsonState`). Assert keys are cleared from `ArkReminderState.reminders`.
   Assert function is synchronous (not a coroutine).

---

## Acceptance criteria

- [ ] `cancel_match_reminders` is now a regular (synchronous) function using
  `ArkReminderState`.
- [ ] All `await cancel_match_reminders(...)` call sites have had `await` removed.
- [ ] `ArkJsonState` import removed from `ark/reminders.py` (if no longer used).
- [ ] `dispatch_cancel_dms` sends a DM embed to every active player with a Discord ID.
- [ ] Players without `DiscordUserId` are silently skipped (logged at DEBUG).
- [ ] `discord.Forbidden` is handled gracefully — marked sent, not retried.
- [ ] Unexpected exceptions are logged but do not halt the loop; key is NOT marked
  sent.
- [ ] Deduplication prevents double-DM across bot restarts.
- [ ] The cancel command handler loads roster before calling `cancel_match`.
- [ ] DM dispatch failure does not cause the cancel command to return an error.
- [ ] All 7 tests pass.
- [ ] `black`, `ruff`, `pyright`, `pytest` all pass.

---

## Files changed

| File | Change type |
|------|-------------|
| `ark/reminders.py` | Modify — fix `cancel_match_reminders` (F0) + add `dispatch_cancel_dms` (F1) |
| `commands/ark_cmds.py` (or equivalent, confirm via search) | Modify — call `dispatch_cancel_dms` post-cancel (F2) |
| `tests/test_ark_cancel_dm.py` | New — 7 tests |

---

## Do NOT change

- `ark/dal/ark_dal.py` — `cancel_match` itself unchanged
- `ark/team_publish.py` — no changes
- `ark/ark_scheduler.py` — no changes
- `tests/test_ark_reminder_phase_bd.py` — do not modify
- `tests/test_ark_reminder_phase_c.py` — do not modify
- `tests/test_ark_team_publish_mention.py` — do not modify
- Any SQL schema
