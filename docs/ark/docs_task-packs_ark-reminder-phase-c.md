# Ark Reminder System — Phase C: Team Names in Reminder Embeds

> **Task pack version:** 1.1 — amended post Phase B+D
> **Date:** 2026-03-26
> **Prerequisite:** Phase A and Phase B+D deployed and tested.

---

## Scope

Replace the current count-based "Team Summary" in channel and DM reminder embeds with
player name lists sourced from SQL. The screenshot provided shows the current output:

> Team 1: **9** / Team 2: **8** / Unassigned: **0**

The target output (if teams are finalised) is:
> **Team 1:** Chrislos, BlazieP, …
> **Team 2:** PlayerA, PlayerB, …

No counts. No governor IDs. No Discord `@` mentions. Names only.

If teams are not yet finalised (no `IsFinal=1` rows), the team section is omitted
entirely — do not show draft team names to participants in reminders.

---

## Background

`_build_team_summary_lines` currently reads from `ArkTeamStateStore` (JSON file).
This is fragile — if the bot restarts or the JSON is cleared the field silently
disappears. The SQL table `dbo.ArkMatchTeams` is the authoritative source. The roster
(`get_roster`) already provides `GovernorNameSnapshot` keyed by `GovernorId`.

---

## ← AMENDED: Critical constraint from Phase B+D

`_send_channel_reminder` was updated in Phase B+D. When converting it to `async` in
this task, the following must be preserved exactly:

- The `announce: bool = False` parameter must remain on the function signature.
- The `AllowedMentions` logic inside the function body must remain unchanged:
  ```python
  allowed_mentions=discord.AllowedMentions(everyone=True) if announce else discord.AllowedMentions.none()
  ```
- The `close_1h` call site in `_run_match_reminder_dispatch` passes `announce=True`
  — this must continue to work after the async conversion.
- Do not remove, rename, or reorder the `announce` parameter.

---

## ← AMENDED: Test fixture typing rule

All mock match dicts in tests must use proper Python types — not ISO strings.
`resolve_ark_match_datetime` and `ensure_aware_utc` will raise `TypeError` on strings.

```python
from datetime import UTC, date, datetime

match = {
    "MatchId": 1,
    "Alliance": "k98A",
    "ArkWeekendDate": date(2026, 3, 28),                          # datetime.date
    "MatchDay": "Sat",
    "MatchTimeUtc": datetime(2026, 3, 28, 11, 0, tzinfo=UTC).time(),  # datetime.time
    "SignupCloseUtc": datetime(2026, 3, 28, 9, 0, tzinfo=UTC),    # datetime (aware)
    "RegistrationStartsAtUtc": datetime(2026, 3, 24, 12, 0, tzinfo=UTC),
    "RegistrationChannelId": 111,
    "RegistrationMessageId": 222,
    "ConfirmationChannelId": 333,
}
```

---

## Task C1 — New async helper `_build_team_name_fields`

### File to modify
`ark/ark_scheduler.py`

### Implement

```python
async def _build_team_name_fields(
    match_id: int,
    roster: list[dict[str, Any]] | None = None,
) -> tuple[str, str] | None:
    """
    Return (team1_names_str, team2_names_str) from finalised SQL team rows,
    or None if no finalised teams exist.

    Names are comma-separated GovernorNameSnapshot values.
    Only IsFinal=1 rows are used — draft rows are not shown in reminders.
    If roster is not provided, it is fetched from SQL.
    """
```

Implementation steps:

1. Call `list_match_team_rows(match_id=match_id, draft_only=False)`.
2. Filter to rows where `IsFinal == 1`. If none, return `None`.
3. If `roster` is `None`, call `await get_roster(match_id)`.
4. Build a `governor_id → GovernorNameSnapshot` map from the roster:
   ```python
   name_map = {
       int(r["GovernorId"]): str(r.get("GovernorNameSnapshot") or "Unknown")
       for r in roster
       if r.get("GovernorId") is not None
   }
   ```
5. Separate final rows into team 1 and team 2 by `TeamNumber`, in order.
6. Build name strings:
   ```python
   t1_names = ", ".join(name_map.get(int(r["GovernorId"]), "Unknown") for r in team1_rows)
   t2_names = ", ".join(name_map.get(int(r["GovernorId"]), "Unknown") for r in team2_rows)
   ```
7. Truncate each string to 950 characters with `…` if exceeded (Discord embed field
   limit is 1024; leaving margin for the field label).
8. Return `(t1_names, t2_names)`.

Wrap in `try/except Exception` and log a warning on failure, returning `None`.

### Imports required

`list_match_team_rows` and `get_roster` are already imported in `ark_scheduler.py`.

---

## Task C2 — Update `_build_channel_reminder_embed`

### File to modify
`ark/ark_scheduler.py`

### Current signature
```python
def _build_channel_reminder_embed(
    *,
    match: dict[str, Any],
    reminder_type: str,
    text: str,
) -> discord.Embed:
```

### New signature
```python
async def _build_channel_reminder_embed(
    *,
    match: dict[str, Any],
    reminder_type: str,
    text: str,
    roster: list[dict[str, Any]] | None = None,
) -> discord.Embed:
```

### Change body

Replace the `_build_team_summary_lines` call with `_build_team_name_fields`:

```python
team_fields = await _build_team_name_fields(int(match["MatchId"]), roster=roster)
if team_fields:
    t1_names, t2_names = team_fields
    embed.add_field(name="Team 1", value=t1_names or "—", inline=False)
    embed.add_field(name="Team 2", value=t2_names or "—", inline=False)
```

Remove the old `summary = _build_team_summary_lines(...)` call entirely.

### Update call site

`_build_channel_reminder_embed` is called inside `_send_channel_reminder`.
`_send_channel_reminder` must now be `async` (it calls an `async` embed builder).

### ← AMENDED: Updated `_send_channel_reminder` signature

When making `_send_channel_reminder` async, the full signature must be:

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
    announce: bool = False,      # ← PRESERVE from Phase B+D — do not remove
) -> bool:
```

The body must preserve:
```python
await channel.send(
    content=text,
    embed=embed,
    allowed_mentions=discord.AllowedMentions(everyone=True) if announce else discord.AllowedMentions.none(),
)
```

All existing call sites already use `await _send_channel_reminder(...)` — no changes
needed at call sites.

---

## Task C3 — Update `_build_dm_reminder_embed`

### File to modify
`ark/ark_scheduler.py`

### Same change pattern as C2

```python
async def _build_dm_reminder_embed(
    *,
    match: dict[str, Any],
    reminder_type: str,
    include_checkin_line: bool = False,
    roster: list[dict[str, Any]] | None = None,
) -> discord.Embed:
```

Replace `_build_team_summary_lines` with `_build_team_name_fields`. Same field
structure as C2.

### Update call site

`_build_dm_reminder_embed` is called inside `_dispatch_dm_reminders_for_match`.
That function already calls `get_roster` at the top:

```python
roster = await get_roster(int(match["MatchId"]))
```

Pass this roster through to `_build_dm_reminder_embed` as `roster=roster` to avoid
a second SQL fetch.

---

## Task C4 — Remove `_build_team_summary_lines`

### File to modify
`ark/ark_scheduler.py`

The synchronous `_build_team_summary_lines` function (which reads from
`ArkTeamStateStore` JSON) is now fully replaced. Delete it.

Also remove the `from ark.team_state import ArkTeamStateStore` import **if and only
if** `ArkTeamStateStore` is not used anywhere else in `ark_scheduler.py`. Check
before removing.

---

## Tests to add

**File:** `tests/test_ark_reminder_phase_c.py`

### Fixture typing rule

All mock match dicts must use Python native types — see the amended fixture note at
the top of this task pack.

### Test list

1. **`test_build_team_name_fields_returns_names_from_final_rows`** — mock
   `list_match_team_rows` to return two `IsFinal=1` rows (one per team). Mock
   `get_roster` to return matching names. Assert returned tuple contains correct
   comma-separated names.

2. **`test_build_team_name_fields_returns_none_when_no_final_rows`** — mock
   `list_match_team_rows` to return only `IsDraft=1` rows. Assert `None` is returned.

3. **`test_build_team_name_fields_returns_none_when_no_rows`** — mock empty return.
   Assert `None`.

4. **`test_build_team_name_fields_truncates_long_names`** — mock 30 players all with
   long names. Assert neither string exceeds 950 chars and ends with `…`.

5. **`test_channel_embed_includes_team_fields_when_teams_published`** — call
   `_build_channel_reminder_embed` with a mocked match that has final team rows.
   Assert embed has fields named "Team 1" and "Team 2".

6. **`test_channel_embed_omits_team_fields_when_no_final_teams`** — same but no final
   rows. Assert no "Team 1" or "Team 2" fields in embed.

7. **`test_dm_embed_includes_team_fields`** — same pattern for DM embed, passing a
   roster directly.

### ← AMENDED: Phase B+D regression check

After implementing Phase C, run the Phase B+D test file to confirm no regressions:

```bash
pytest tests/test_ark_reminder_phase_bd.py -v
```

All 6 tests must continue to pass. If any fail, the `announce` parameter or
`AllowedMentions` logic has been accidentally removed — restore it before marking
Phase C complete.

---

## Acceptance criteria

- [ ] Channel reminder embeds show "Team 1: Name, Name, …" and "Team 2: …" when
  final team rows exist in SQL.
- [ ] DM reminder embeds show the same team name format.
- [ ] Neither embed shows team info when only draft rows exist.
- [ ] No counts, no governor IDs, no Discord `@` mentions in team fields.
- [ ] `_build_team_summary_lines` is deleted.
- [ ] `ArkTeamStateStore` import removed from `ark_scheduler.py` if unused.
- [ ] `_send_channel_reminder` is `async` and retains `announce: bool = False` param.
- [ ] `_build_channel_reminder_embed` is `async` and retains `roster` param.
- [ ] `AllowedMentions` logic inside `_send_channel_reminder` is unchanged from Phase B+D.
- [ ] Roster is passed through from `_dispatch_dm_reminders_for_match` — no extra
  SQL fetch per DM.
- [ ] All 7 new tests pass.
- [ ] `tests/test_ark_reminder_phase_bd.py` — all 6 tests still pass. ← AMENDED
- [ ] `black`, `ruff`, `pyright`, `pytest` all pass.

---

## Files changed

| File | Change type |
|------|-------------|
| `ark/ark_scheduler.py` | Modify — new async helper, updated embed builders, remove old helper |
| `tests/test_ark_reminder_phase_c.py` | New — 7 tests |

---

## Do NOT change

- `ark/team_state.py` — leave untouched
- `ark/team_publish.py` — leave untouched
- `ark/reminder_types.py` — no changes
- `tests/test_ark_reminder_phase_bd.py` — do not modify this file ← AMENDED
- Any SQL schema
