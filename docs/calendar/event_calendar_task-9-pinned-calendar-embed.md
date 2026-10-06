# Task 9 — Pinned Calendar Embed (Final Implementation)

## Status
✅ Completed and smoke-tested locally on **2026-03-09**. Tracker atomic-persistence hardening was
production deployed and operator smoke accepted on **2026-09-01** through mirror PR #250 and
production PR #557.

## Implemented Scope

### 1) Pinned 30-day calendar embed
- Added persistent pinned calendar orchestration in:
  - `event_calendar/pinned_embed.py`
- Implemented:
  - `update_calendar_embed(channel_id: int, *, force_refresh: bool = False) -> dict`
- Behavior:
  - Renders from **JSON runtime cache only**
  - 30-day window
  - Groups events by date
  - Includes emoji + title + variant, start/end + links/channel mentions
  - Enforces embed safety limits (field/value/overall truncation strategy)
  - Reuses tracked message ID and edits in place
  - Pins message when needed and keeps pinned
  - Graceful fallback preserves last-known-good message on failures

### 2) Pinned local-time toggle + rehydration
- Reused existing local-time UX pattern via `LocalTimeToggleView` bridge in:
  - `ui/views/calendar.py` (`CalendarLocalTimeToggleView`)
- Added pinned view rehydration:
  - `rehydrate_pinned_calendar_view(bot)` in `event_calendar/pinned_embed.py`
- Rehydration resilience:
  - Handles deleted/missing channel/message
  - Clears invalid tracker state safely
  - Does not crash startup
- Tracker persistence:
  - Retains `data/calendar_pinned_tracker.json` and its existing dictionary shape
  - Writes through `file_utils.atomic_write_json()` with parent creation, flush/`fsync`, atomic
    replacement, transient Windows sharing-violation retries, and failed-temp cleanup
  - Preserves the prior valid tracker when replacement fails while retaining the existing logged,
    non-raising caller boundary

### 3) Local-time toggle for user commands
- `/calendar` and `/calendar_next_event` now include local-time button
- `/calendar` uses unified view class:
  - pagination + local-time in one view object (fixes callback/view mismatch)
- Command-response rehydration not required (timeout allowed)

### 4) Daily automation + sequencing
- Added daily pinned refresh orchestration in `bot_instance.py`:
  - startup immediate run (`startup_pinned_refresh`)
  - daily cadence run (`scheduler_pinned_daily`)
- Sequence is enforced:
  1. pipeline refresh (sync → generate → publish)
  2. pinned embed update
- If pipeline fails:
  - pinned message is preserved
  - telemetry/log emitted clearly
- Lock compatibility:
  - uses `get_operation_lock("calendar_refresh")`

### 5) Task 8 follow-up fixes included
- `_cache_footer()` no longer depends on missing `pipeline_run_id` in cache payload  
  (uses `generated_utc`, `horizon_days`, `source`)
- Pagination `on_timeout()` disables buttons and edits message
- Button label consistency aligned
- KVK tracker-key compatibility maintained for renamed commands
- Timeout classifier test corrected to include `asyncio.TimeoutError`
- `/calendar` day-window fixed from `356` to `365`
- Docs aligned with shipped behavior

## Architecture updates
- `commands/calendar_cmds.py` reduced to command entrypoints/wiring
- `ui/views/calendar.py` holds calendar view/render helpers
- `event_calendar/runtime_cache.py` remains data/query layer
- `event_calendar/pinned_embed.py` handles pinned lifecycle

## Behavior Notes
- `/calendar` and `/calendar_next_event` are now configured as **ephemeral** responses.
- Pinned calendar update is robust to transient sheet/pipeline failures; stale content is preserved by design.

## Validation completed

### Pytest
- Calendar-related pytest suites passed locally, including:
  - `tests/test_calendar_pinned_embed.py`
  - `tests/test_calendar_views.py`
  - `tests/test_calendar_commands.py`
  - `tests/test_calendar_scheduler.py`
  - `tests/test_calendar_service.py`

### Manual Discord smoke
- Pinned embed created, pinned, and edited in-place (message reused)
- Pinned local-time button works before and after restart
- `/calendar_next_event` local-time button works
- `/calendar` pagination + local-time works (fixed unified view issue)
- Daily sequencing and failure-preserve behavior verified in logs

### Atomic persistence follow-up — 2026-09-01
- Focused tracker coverage passed `11` tests, calendar coverage passed `114`, lifecycle coverage
  passed `25`, shared atomic-helper retry coverage passed `2`, and the full suite passed with
  `3027 passed, 2 skipped`.
- Changes-only security review `43628893-300e-44ae-970d-e406bb39ac11` ran with Deep off, complete
  coverage, and zero findings.
- Production restart completed pinned-calendar rehydration and edited the existing message in
  place with `status=edited` and `events=25`; channel/message identity remained unchanged,
  `updated_at_utc` advanced, tracker JSON remained valid, no duplicate or stale temporary file
  remained, and the next daily refresh scheduled normally.
- No SQL, config, dependency, command, permission, reminder, scheduler, cache, embed, button, or
  user-facing output change was required.

---

## Known operational notes
- Discord 429 warnings may appear for unrelated high-frequency message edits (e.g., health card updates).  
  This does not affect calendar correctness; optional retry/backoff hardening can be added separately.
