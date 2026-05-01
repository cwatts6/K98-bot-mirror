# Ark Reminder System — Phase G+H: Check-in Announcement, SQL Dedup, Code Review Fixes & Housekeeping

> **Task pack version:** 1.0
> **Date:** 2026-03-27
> **Prerequisite:** Phases A, B+D, C, E, F all deployed and tested.

---

## Scope

This task pack combines:

- **G** — Add a one-time check-in open announcement to the confirmation channel
- **H-SQL** — Add `MentionMessageSent` flag to `dbo.ArkMatches` to make the Phase E
  team-publish mention message restart-safe
- **H-CR** — Fix all code review findings from the post-Phase-F review
- **H-cleanup** — Minor housekeeping (dead constants, log consistency)

SQL schema changes are required in `cwatts6/K98-bot-SQL-Server`.
Python changes are in `cwatts6/K98-bot-mirror`.
Deploy SQL first, then Python.

---

## Part 1 — SQL schema change (K98-bot-SQL-Server)

### File to create
`sql_schema/dbo.ArkMatches.Table.sql` — ADD COLUMN migration

### Change

Add one nullable `bit` column to `dbo.ArkMatches`:

```sql
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID(N'[dbo].[ArkMatches]')
      AND name = N'MentionMessageSent'
)
BEGIN
    ALTER TABLE [dbo].[ArkMatches]
    ADD [MentionMessageSent] [bit] NOT NULL
        CONSTRAINT [DF_ArkMatches_MentionMessageSent] DEFAULT (0);
END
```

This column tracks whether the first-publish `@` mention message has been sent for a
match. `0` = not sent (default), `1` = sent. Setting it in SQL makes the dedup
restart-safe — if the bot restarts between team publish and mention send, the flag
prevents a double mention.

---

## Part 2 — DAL update (ark/dal/ark_dal.py)

### Add two new DAL functions

**2a — `get_mention_message_sent`**

```python
async def get_mention_message_sent(match_id: int) -> bool:
    sql = """
        SELECT MentionMessageSent
        FROM dbo.ArkMatches
        WHERE MatchId = ?;
    """
    row = await run_one_async(sql, (int(match_id),))
    return bool((row or {}).get("MentionMessageSent") or 0)
```

**2b — `mark_mention_message_sent`**

```python
async def mark_mention_message_sent(match_id: int) -> bool:
    sql = """
        UPDATE dbo.ArkMatches
        SET MentionMessageSent = 1,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.MatchId
        WHERE MatchId = ?
          AND MentionMessageSent = 0;
    """
    row = await run_one_async(sql, (int(match_id),))
    return int((row or {}).get("MatchId") or 0) > 0
```

The `WHERE MentionMessageSent = 0` guard makes `mark_mention_message_sent` an
idempotent compare-and-set — a second call for the same match returns `False` without
writing.

---

## Part 3 — team_publish.py update (H-SQL)

### File to modify
`ark/team_publish.py`

### Replace in-memory `is_first_publish` check with SQL flag

**Current (Phase E):**
```python
is_first_publish = assignment.published_at_utc is None
```

**New:**

```python
from ark.dal.ark_dal import (
    ...,
    get_mention_message_sent,
    mark_mention_message_sent,
)

# After loading match and before the embed sends:
is_first_publish = not (await get_mention_message_sent(int(match_id)))
```

After the mention message is successfully sent, mark it in SQL:

```python
# Inside the mention message send block, after channel.send(...) succeeds:
await mark_mention_message_sent(int(match_id))
```

If `mark_mention_message_sent` returns `False` (already marked by a concurrent
process), log at `DEBUG` and continue — the message was already sent.

The `try/except` wrapper on the mention block is unchanged — a failure in
`mark_mention_message_sent` should be logged but must not propagate as an error from
`publish_ark_teams`.

### Remove the `assignment.published_at_utc is None` check

The in-memory check is no longer needed and should be deleted. The SQL flag is the
sole authority.

---

## Part 4 — Code review fixes (H-CR)

### CR1 — `cancel_match_reminders` preserves cancelled dedupe keys

**File:** `ark/reminders.py`

`cancel_match_reminders` currently wipes all keys with the `"{match_id}|"` prefix,
including `"{match_id}|{user_id}|cancelled"` keys. This breaks restart-safe dedup
for cancel DMs.

**Fix:** Preserve keys whose third segment is `"cancelled"`:

```python
def cancel_match_reminders(match_id: int) -> bool:
    state = ArkReminderState.load()
    prefix = f"{match_id}|"

    def _should_keep(key: str) -> bool:
        if not key.startswith(prefix):
            return True
        parts = key.split("|")
        # Preserve per-user cancellation DM dedupe keys
        return len(parts) >= 3 and parts[2] == "cancelled"

    before = len(state.reminders)
    state.reminders = {k: v for k, v in state.reminders.items() if _should_keep(k)}
    changed = len(state.reminders) != before
    if changed:
        state.save()
        logger.info("[ARK_REMINDERS] Cleared reminder state for match_id=%s", match_id)
    return changed
```

---

### CR2 — `dispatch_cancel_dms` saves state after each successful send

**File:** `ark/reminders.py`

Currently `reminder_state.save()` is called once at the end of the loop. A crash
mid-loop means already-sent users get a second DM on retry.

**Fix:** Call `reminder_state.save()` immediately after each `mark_sent` call:

```python
# After mark_sent in the success path:
reminder_state.mark_sent(dkey)
reminder_state.save()   # ← save after each successful send
counters["sent"] += 1

# After mark_sent in the Forbidden path:
reminder_state.mark_sent(dkey)
reminder_state.save()   # ← save after each terminal failure
counters["failed"] += 1
```

Remove the `reminder_state.save()` call at the end of the loop — it is no longer
needed (every terminal state is already persisted inline).

Performance note: for typical Ark rosters (10–30 players) the extra file writes are
negligible. The `atomic_write_json` helper already handles atomicity.

---

### CR3 — `@everyone` token in registration_close_1h message content

**File:** `ark/ark_scheduler.py`

`AllowedMentions(everyone=True)` grants permission for `@everyone` to resolve, but
Discord requires the literal `@everyone` token in the message content for the ping
to fire.

**Fix:** Prepend `@everyone` to the text:

```python
text = (
    f"@everyone ⚠️ **Ark signups close in 1 hour — {match.get('Alliance', '')}!**"
    f"{link_line}"
)
```

---

### CR4 — Scheduler reloads `ArkReminderState` from disk each poll tick

**File:** `ark/ark_scheduler.py` — `schedule_ark_lifecycle`

`reschedule_match_reminders` writes cleared keys to disk. The running scheduler holds
`ArkSchedulerState.reminder_state` loaded once at startup. The on-disk clear is never
picked up until restart.

**Fix:** Reload `ArkReminderState` from disk at the top of each poll tick, replacing
the stale in-memory instance:

```python
async def schedule_ark_lifecycle(client, poll_interval_seconds: int = 300) -> None:
    state = ArkSchedulerState()

    while True:
        try:
            # Reload reminder state from disk each tick so that external clears
            # (e.g. reschedule_match_reminders) take effect within one poll interval.
            state.reminder_state = ArkReminderState.load()

            config = await get_config()
            ...
```

This is one line added at the top of the `while True` body. The existing
`ArkSchedulerState.reminder_state` field initialiser (`field(default_factory=ArkReminderState.load)`)
remains — it handles the initial load.

`ArkReminderState` is already imported in `ark_scheduler.py` — no new import needed.

---

### CR5 — Cancel DM dispatch moved to background task

**File:** `commands/ark_cmds.py`

The cancel flow currently awaits `dispatch_cancel_dms` before sending the interaction
response, risking Discord's 3-second interaction timeout on larger rosters.

**Fix:** Fire the DM dispatch as a background task after the interaction is
acknowledged:

```python
import asyncio

# ... (cancel logic, confirmation embed update) ...

# Acknowledge the interaction first
await interaction.response.edit_message(...)   # or followup — whatever the existing pattern is

# Then dispatch DMs in the background — must not block the response
asyncio.create_task(
    _dispatch_cancel_dms_background(
        client=interaction.client,
        match_id=sel.match_id,
        match=match,
        roster=roster,
    )
)
```

Add a module-level private coroutine to keep the command handler thin:

```python
async def _dispatch_cancel_dms_background(
    *, client, match_id: int, match: dict, roster: list
) -> None:
    try:
        await dispatch_cancel_dms(
            client=client,
            match_id=match_id,
            match=match,
            roster=roster,
        )
    except Exception:
        logger.exception("[ARK_CMD] cancel_dm_dispatch_failed match_id=%s", match_id)
```

The interaction response must be sent **before** `asyncio.create_task` — confirm the
existing flow already defers or edits the message before this point.

---

### CR6 — Content length guard covers full composed message

**File:** `ark/team_publish.py`

The chunk loop enforces `MENTION_CHUNK_LIMIT` (1800 chars) on the mention string
only. The header (`🏆 **Ark teams published...**\n`) and no-Discord suffix can push
individual messages over Discord's 2000-char cap.

**Fix:** Enforce the limit against the fully composed content string:

```python
MENTION_CHUNK_LIMIT = 1800
DISCORD_MESSAGE_LIMIT = 2000

# After building mention_parts and no_discord_names:
alliance = str(match.get("Alliance") or "")
header = f"🏆 **Ark teams have been published — {alliance}!**\n"
no_discord_suffix = (
    f"\n*(No Discord link: {', '.join(no_discord_names)})*"
    if no_discord_names
    else ""
)
# Truncate no_discord_suffix if needed to guarantee the final message fits
max_suffix_len = DISCORD_MESSAGE_LIMIT - len(header) - len(" ".join(mention_parts[:1])) - 10
if len(no_discord_suffix) > max_suffix_len:
    no_discord_suffix = no_discord_suffix[:max_suffix_len - 1] + "…"

# Chunk only the mention string; header goes on first chunk only
chunks: list[str] = []
current = ""
for mention in mention_parts:
    candidate = (current + " " + mention).strip()
    full_candidate = header + candidate + no_discord_suffix
    if current and len(full_candidate) > DISCORD_MESSAGE_LIMIT:
        chunks.append(current.strip())
        current = mention
    else:
        current = candidate
if current:
    chunks.append(current.strip())

for i, chunk in enumerate(chunks):
    prefix = header if i == 0 else ""
    suffix = no_discord_suffix if i == len(chunks) - 1 else ""
    content = prefix + chunk + suffix
    await channel.send(
        content=content,
        allowed_mentions=discord.AllowedMentions(users=True),
    )
```

---

### CR7 — Docstring correction in `publish_ark_teams`

**File:** `ark/team_publish.py`

Update the docstring as suggested by the reviewer:

```python
"""
...
Returns True if all required data is present and the embed messages are sent
without error. Returns False if required data is missing (for example, if the
assignment, match, roster, or target channel cannot be resolved).

A failure in the mention message does not cause this function to return False.

Discord API failures during the embed sends or edits (for example, from
``channel.send``, ``fetch_message``, or ``edit``) are not caught by this
function and will propagate as exceptions (such as ``discord.HTTPException``,
``discord.Forbidden``, or ``discord.NotFound``).
"""
```

---

### CR8 — `ensure_aware_utc` computed once in registration guard

**File:** `ark/ark_scheduler.py`

```python
if starts_at:
    starts_at_utc = ensure_aware_utc(starts_at)
    if starts_at_utc > now:
        logger.info(
            "[ARK_SCHED] reminder_dispatch_skip match_id=%s reason=registration_not_open "
            "registration_starts_at_utc=%s",
            match_id,
            starts_at_utc.isoformat(),
        )
        return
```

---

### CR9 — `get_user` before `fetch_user` in `dispatch_cancel_dms`

**File:** `ark/reminders.py`

```python
user = client.get_user(user_id)
if user is None:
    user = await client.fetch_user(user_id)
```

---

---

## Part 5 — Phase G: Check-in open announcement

### File to modify
`ark/ark_scheduler.py`

### What to add

When a locked match transitions into the check-in window (i.e. `now >= checkin_at`
for the first time), send a one-time message to the confirmation channel informing
players that check-in is open.

**State key:** Use `make_channel_key` with a new constant:

```python
# ark/reminder_types.py — add:
REMINDER_CHECKIN_OPEN = "checkin_open"
```

**In `_run_match_reminder_dispatch`**, inside the `status == "locked"` section, after
the existing `checkin_sched` DM dispatch block:

```python
# Check-in open channel announcement — fires once when check-in window opens
if conf_channel_id and now >= checkin_sched:
    checkin_open_key = make_channel_key(
        int(match["MatchId"]),
        int(conf_channel_id),
        REMINDER_CHECKIN_OPEN,
    )
    if not state.reminder_state.was_sent(checkin_open_key):
        await _send_channel_reminder(
            client=client,
            state=state,
            match=match,
            reminder_type=REMINDER_CHECKIN_OPEN,
            channel_id=int(conf_channel_id),
            text=f"🔔 **Check-in is now open — {match.get('Alliance', '')}!** Use the button on the match post to check in.",
            scheduled_for=checkin_sched,
            dedupe_key=checkin_open_key,
        )
```

This does not use `should_send_with_grace` (no 15-min window needed — it fires at any
point after `checkin_sched` if not yet sent, not just in a narrow grace window). The
`was_sent` check is the sole gate.

**No `@everyone`** — this goes to the confirmation channel where only signed-up
players are the intended audience.

---

## Part 6 — Housekeeping (H-cleanup)

### H1 — `REMINDER_FINAL_DAY` deprecation comment

**File:** `ark/reminder_types.py`

Add a comment above `REMINDER_FINAL_DAY`:

```python
# REMINDER_FINAL_DAY: superseded by REMINDER_REGISTRATION_CLOSE_1H in Phase B.
# Retained for state-key compatibility only. Not dispatched.
REMINDER_FINAL_DAY = "final_day"
```

### H2 — Warning log when locked match has no team rows near match time

**File:** `ark/ark_scheduler.py`

In `_run_match_reminder_dispatch`, in the section that dispatches the `4h` channel
reminder (`REMINDER_4H`), add a diagnostic log if no final team rows exist for a
locked match:

```python
if rtype == REMINDER_4H and conf_channel_id:
    team_rows = await list_match_team_rows(match_id, draft_only=False)
    final_rows = [r for r in team_rows if int(r.get("IsFinal") or 0) == 1]
    if not final_rows:
        logger.warning(
            "[ARK_SCHED] no_final_teams_at_4h_reminder match_id=%s",
            match_id,
        )
```

`list_match_team_rows` is already imported. This is diagnostics only — it does not
block reminder dispatch.

---

## Part 7 — Test fixes (H-CR test corrections)

### File to modify: `tests/test_ark_reminder_phase_bd.py`

**CR10 — Assert `@everyone` in content**

In `test_close_1h_reminder_fires_in_window` (and any related test that checks the
close_1h send), add an assertion that the content string contains `"@everyone"`:

```python
call_kwargs = channel.send.call_args.kwargs
assert "@everyone" in (call_kwargs.get("content") or ""), \
    "Expected @everyone token in message content"
```

### File to modify: `tests/test_ark_reminder_reschedule.py`

**CR11 — `test_guard_allows_open_registration` proves bypass**

Replace the current implementation with a sentinel pattern:

```python
@pytest.mark.asyncio
async def test_guard_allows_open_registration(monkeypatch):
    """Guard does NOT fire when RegistrationStartsAtUtc is in the past."""
    from ark.ark_scheduler import _run_match_reminder_dispatch, ArkSchedulerState

    now = datetime(2026, 3, 28, 12, 0, tzinfo=UTC)
    monkeypatch.setattr("ark.ark_scheduler._utcnow", lambda: now)

    state = ArkSchedulerState()
    mock_client = MagicMock()

    match = {
        "MatchId": 1,
        "Alliance": "k98A",
        "Status": "Scheduled",
        "ArkWeekendDate": date(2026, 3, 28),
        "MatchDay": "Sat",
        "MatchTimeUtc": datetime(2026, 3, 28, 15, 0, tzinfo=UTC).time(),
        "SignupCloseUtc": datetime(2026, 3, 28, 14, 0, tzinfo=UTC),
        "RegistrationStartsAtUtc": datetime(2026, 3, 24, 12, 0, tzinfo=UTC),  # past
    }

    with patch(
        "ark.ark_scheduler.resolve_ark_match_datetime",
        side_effect=RuntimeError("sentinel — proves guard did not return early"),
    ):
        with pytest.raises(RuntimeError, match="sentinel"):
            await _run_match_reminder_dispatch(mock_client, state, match)
```

**CR12 — Replace `Path("/dev/null")` with `tmp_path`**

Update `_make_state` to accept a `tmp_path` fixture parameter or use a
`pytest.fixture` that provides a temp file path. Change all usages in the test file:

```python
@pytest.fixture
def reminder_state_path(tmp_path):
    return tmp_path / "ark_reminder_state_test.json"

def _make_state(reminders: dict[str, str], path: Path) -> ArkReminderState:
    """Build an in-memory ArkReminderState backed by a temp file."""
    return ArkReminderState(path=path, reminders=dict(reminders))
```

Update each test that calls `_make_state` to receive `reminder_state_path` as a
fixture and pass it through. Also patch `state.save` where the test should not write
to disk, or let it write to the temp path (both are acceptable).

---

## Tests to add

**File:** `tests/test_ark_reminder_phase_gh.py`

1. **`test_checkin_open_announcement_fires_once`** — mock a locked match with
   `now >= checkin_at`. Assert `_send_channel_reminder` is called with
   `reminder_type=REMINDER_CHECKIN_OPEN`. Call again — assert not called a second
   time (deduped by `was_sent`).

2. **`test_checkin_open_announcement_not_fired_before_checkin_window`** — `now` is
   13h before match start (before `checkin_at`). Assert not called.

3. **`test_cancel_match_reminders_preserves_cancelled_keys`** — populate reminders
   with a mix of `24h`, `4h`, `start`, and `cancelled` keys for match_id=1. Call
   `cancel_match_reminders(1)`. Assert all non-cancelled keys are removed. Assert
   all `cancelled` keys are preserved.

4. **`test_dispatch_cancel_dms_saves_after_each_send`** — mock two active players.
   Mock `state.save` to track call count. Assert `save` is called once per
   successful send (2 times total), not once at the end.

5. **`test_mention_message_not_resent_after_sql_flag_set`** — mock
   `get_mention_message_sent` to return `True`. Assert `channel.send` is called
   exactly 3 times (embeds only, no mention message) even when
   `assignment.published_at_utc is None`.

6. **`test_mention_message_sets_sql_flag_on_first_publish`** — mock
   `get_mention_message_sent` to return `False`. Assert `mark_mention_message_sent`
   is called after the mention send.

---

## Deployment order

1. **SQL first** — run the `dbo.ArkMatches` ALTER TABLE in `K98-bot-SQL-Server`
2. **Python** — deploy `K98-bot-mirror` changes
3. Validate locally: `pytest`, `black`, `ruff`, `pyright`

---

## Acceptance criteria

- [ ] `MentionMessageSent` column added to `dbo.ArkMatches` (SQL repo)
- [ ] `get_mention_message_sent` and `mark_mention_message_sent` added to DAL
- [ ] `publish_ark_teams` uses SQL flag instead of in-memory check
- [ ] `cancel_match_reminders` preserves `cancelled` dedupe keys (CR1)
- [ ] `dispatch_cancel_dms` saves after each send/Forbidden (CR2)
- [ ] `@everyone` token present in `registration_close_1h` content (CR3)
- [ ] `schedule_ark_lifecycle` reloads `ArkReminderState` each tick (CR4)
- [ ] Cancel DM dispatch is a background task in `ark_cmds.py` (CR5)
- [ ] Full message length enforced in team publish chunking (CR6)
- [ ] `publish_ark_teams` docstring updated (CR7)
- [ ] `ensure_aware_utc` computed once in registration guard (CR8)
- [ ] `get_user` before `fetch_user` in cancel DM dispatch (CR9)
- [ ] `@everyone` asserted in content in `test_ark_reminder_phase_bd.py` (CR10)
- [ ] `test_guard_allows_open_registration` uses sentinel pattern (CR11)
- [ ] `Path("/dev/null")` replaced with `tmp_path` (CR12)
- [ ] `REMINDER_CHECKIN_OPEN` constant added; check-in announcement fires once (G)
- [ ] `REMINDER_FINAL_DAY` deprecation comment added (H1)
- [ ] 4h-reminder team row warning log added (H2)
- [ ] All new tests pass
- [ ] `tests/test_ark_reminder_phase_bd.py` — all 6 still pass
- [ ] `tests/test_ark_reminder_phase_c.py` — all 7 still pass
- [ ] `black`, `ruff`, `pyright`, `pytest` all pass

---

## Files changed

| File | Repo | Change type |
|------|------|-------------|
| `sql_schema/dbo.ArkMatches.Table.sql` | SQL Server | Modify — add `MentionMessageSent` column |
| `ark/dal/ark_dal.py` | mirror | Modify — add 2 DAL functions |
| `ark/team_publish.py` | mirror | Modify — SQL flag dedup, docstring, chunking fix |
| `ark/reminders.py` | mirror | Modify — CR1, CR2, CR4-reload prep, CR9 |
| `ark/ark_scheduler.py` | mirror | Modify — CR3, CR4, CR8, G (checkin announcement), H2 |
| `ark/reminder_types.py` | mirror | Modify — add `REMINDER_CHECKIN_OPEN`, H1 comment |
| `commands/ark_cmds.py` | mirror | Modify — CR5 background task |
| `tests/test_ark_reminder_phase_gh.py` | mirror | New — 6 tests |
| `tests/test_ark_reminder_phase_bd.py` | mirror | Modify — CR10 assertion |
| `tests/test_ark_reminder_reschedule.py` | mirror | Modify — CR11, CR12 |

---

## Do NOT change

- `ark/team_state.py`
- `ark/confirmation_flow.py`
- `ark/registration_flow.py`
- `tests/test_ark_reminder_phase_c.py`
- `tests/test_ark_team_publish_mention.py`
- `tests/test_ark_cancel_dm.py`
