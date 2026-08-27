# Ark Reminder System — Phase E: Team Publish Player Mention Message

> **Task pack version:** 1.1 — amended post Phase C
> **Date:** 2026-03-26
> **Prerequisite:** Phase A deployed. Phase C deployed.

---

## Scope

When teams are published via `publish_reviewed_teams` → `publish_ark_teams`, send a
single plain-text Discord message to the confirmation channel that `@` mentions every
player assigned to a team. This is a **first-time publish only** notification — it
does not re-fire on re-publish (when the admin re-runs publish to update the 3 embeds).

No SQL schema changes. No new files except the test file.

---

## Background

Currently `publish_ark_teams` sends 3 embed messages (header, team 1, team 2) and
returns. Players have no notification. Admins must separately inform participants.

The mention message is a **fourth message** sent after the 3 embeds — plain content
text, not an embed, so Discord delivers the pings to each player.

---

## ← AMENDED: ArkTeamStateStore note

`ArkTeamStateStore` was removed from `ark/ark_scheduler.py` in Phase C but it is
**still present and actively used in `ark/team_publish.py`**. Do not remove it from
`team_publish.py`. This task does not touch the scheduler. Do not apply Phase C's
import cleanup to `team_publish.py`.

---

## Task E1 — Add first-publish detection to `publish_ark_teams`

### File to modify
`ark/team_publish.py`

### Logic

The function sets `assignment.published_at_utc` inside its body. Before setting it,
check if it was already set — this distinguishes first publish from re-publish:

```python
is_first_publish = assignment.published_at_utc is None
```

This check must happen **before** the line that assigns `published_at_utc`.

---

## Task E2 — Build and send the mention message

### File to modify
`ark/team_publish.py`

### After the 3 embed sends, add:

```python
if is_first_publish:
    all_assigned_ids = (
        set(assignment.team1_player_ids) | set(assignment.team2_player_ids)
    )
    mention_parts: list[str] = []
    no_discord_names: list[str] = []

    for gid in sorted(all_assigned_ids):
        row = rows_by_gid.get(gid)
        if not row:
            continue
        uid = row.get("DiscordUserId")
        if uid:
            mention_parts.append(f"<@{int(uid)}>")
        else:
            name = str(row.get("GovernorNameSnapshot") or f"Governor {gid}")
            no_discord_names.append(name)

    if mention_parts or no_discord_names:
        alliance = str(match.get("Alliance") or "")
        content_lines = [f"🏆 **Ark teams have been published — {alliance}!**"]
        if mention_parts:
            content_lines.append(" ".join(mention_parts))
        if no_discord_names:
            content_lines.append(
                f"*(No Discord link: {', '.join(no_discord_names)})*"
            )
        await channel.send(
            content="\n".join(content_lines),
            allowed_mentions=discord.AllowedMentions(users=True),
        )
        logger.info(
            "[ARK_TEAM_PUBLISH] mention_message_sent match_id=%s pinged=%s no_discord=%s",
            match_id,
            len(mention_parts),
            len(no_discord_names),
        )
```

### Safeguards

- If `mention_parts` and `no_discord_names` are both empty (no players found in
  `rows_by_gid`), skip the send silently and log a warning.
- Wrap the entire mention-message block in `try/except Exception` — a failure here
  must not cause `publish_ark_teams` to return `False`. Log the exception and
  continue.
- `discord.AllowedMentions(users=True)` ensures only the explicitly listed user
  mentions are resolved. `everyone=False` and `roles=False` by default.

### Message length guard

Discord message content is capped at 2000 characters. If `" ".join(mention_parts)`
would exceed ~1800 chars, split into multiple messages:

```python
MENTION_CHUNK_LIMIT = 1800

chunks: list[str] = []
current = ""
for mention in mention_parts:
    if len(current) + len(mention) + 1 > MENTION_CHUNK_LIMIT:
        chunks.append(current.strip())
        current = mention
    else:
        current = (current + " " + mention).strip()
if current:
    chunks.append(current)

# Send header on first chunk only
for i, chunk in enumerate(chunks):
    prefix = f"🏆 **Ark teams published — {alliance}!**\n" if i == 0 else ""
    await channel.send(
        content=prefix + chunk,
        allowed_mentions=discord.AllowedMentions(users=True),
    )
```

This handles rosters larger than ~90 players before hitting the limit.

---

## Tests to add

**File:** `tests/test_ark_team_publish_mention.py`

### Mock type note

`GovernorId` values in mock roster rows should be `int` or castable to `int`.
`DiscordUserId` should be `int` or `None`.

### Test list

1. **`test_mention_message_sent_on_first_publish`** — mock `assignment.published_at_utc
   = None`. Call `publish_ark_teams` with mocked channel and roster. Assert
   `channel.send` was called a 4th time (after 3 embed sends) with content containing
   `<@` mention strings.

2. **`test_mention_message_not_sent_on_republish`** — mock `assignment.published_at_utc
   = "2026-01-01T12:00:00Z"`. Assert `channel.send` called exactly 3 times (embeds
   only, no mention message).

3. **`test_mention_message_uses_name_fallback_for_no_discord`** — roster row has
   `DiscordUserId=None`. Assert content contains governor name string, not a
   `<@...>` mention.

4. **`test_mention_message_skipped_when_no_players_in_map`** — `rows_by_gid` is empty.
   Assert warning logged and only 3 sends (no mention message, no error raised).

5. **`test_mention_message_chunked_for_large_roster`** — mock 100 players all with
   Discord IDs. Assert `channel.send` is called more than 4 times (chunking
   occurred) and no individual content string exceeds 2000 chars.

---

## Acceptance criteria

- [ ] On first publish, a 4th message is sent after the 3 team embeds.
- [ ] The message content `@` mentions every player in `team1_player_ids` +
  `team2_player_ids` who has a `DiscordUserId`.
- [ ] Players without a Discord link are listed by name in a parenthetical, not silently
  dropped.
- [ ] On re-publish (admin updates teams), no mention message is sent.
- [ ] A failure to send the mention message does not cause `publish_ark_teams` to
  return `False`.
- [ ] Content is chunked if needed; no message exceeds 2000 chars.
- [ ] `ArkTeamStateStore` remains imported and used in `ark/team_publish.py` — not removed. ← AMENDED
- [ ] All 5 tests pass.
- [ ] `black`, `ruff`, `pyright`, `pytest` all pass.

---

## Files changed

| File | Change type |
|------|-------------|
| `ark/team_publish.py` | Modify — first-publish detection + mention message |
| `tests/test_ark_team_publish_mention.py` | New — 5 tests |

---

## Do NOT change

- `ark/confirm_publish_service.py` — no changes
- `ark/ark_scheduler.py` — no changes
- `ark/team_state.py` — no changes
- `tests/test_ark_reminder_phase_bd.py` — do not modify
- `tests/test_ark_reminder_phase_c.py` — do not modify
- Any SQL schema
