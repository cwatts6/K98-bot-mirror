# Events And DM Reminders

Purpose: describe the current reminder systems and where to look when changing reminder,
subscription, or event-calendar behaviour.

## Current Systems

Two reminder/event systems coexist:

| Area | Current role | Main files |
|------|--------------|------------|
| Legacy subscription reminders | User subscription commands and KVK event reminder trackers | `commands/subscriptions_cmds.py`, `subscription_tracker.py`, `event_scheduler.py`, `reminder_task_registry.py` |
| Event calendar reminders | Calendar-backed event cache, runtime cache, reminder prefs/state, pinned embed, scheduler | `event_calendar/`, `commands/calendar_cmds.py`, `commands/admin_cmds.py` |

Prefer the `event_calendar/` subsystem for new calendar/reminder work. Treat
`event_scheduler.py` as legacy unless the task explicitly touches subscription reminders.

## Legacy Subscription Reminder State

Important persisted files are defined in `constants.py`:

- `SUBSCRIPTION_FILE`
- `DM_SCHEDULED_TRACKER_FILE`
- `DM_SENT_TRACKER_FILE`
- `FAILED_DM_LOG`
- `REMINDER_TRACKING_FILE`

The legacy flow:

1. User manages reminders through `/subscribe`, `/modify_subscription`, or `/unsubscribe`.
2. `subscription_tracker.py` validates and persists subscription config.
3. `event_scheduler.py` schedules, sends, records, and rehydrates DM reminders.
4. `reminder_task_registry.py` tracks reminder tasks so they can be cancelled or cleaned up.

When changing this path, verify:

- JSON load/save is atomic or failure-safe.
- Duplicate DMs are prevented through sent/scheduled trackers.
- Restart rehydration does not resend stale reminders unexpectedly.
- Unsubscribe removes pending scheduled work.

Relevant tests include:

- `tests/test_subscription_views.py`
- `tests/test_event_scheduler_tracker_locking.py`
- `tests/test_rehydrate_views.py`
- `tests/test_rehydrate_sanitize_and_fileio.py`

## Event Calendar Reminder State

The newer calendar system lives under `event_calendar/`:

- `event_calendar/service.py` orchestrates sync, generation, and cache publish.
- `event_calendar/cache_contract.py` defines the cache payload.
- `event_calendar/cache_publisher.py` writes the runtime cache.
- `event_calendar/runtime_cache.py` reads the cache for commands/views.
- `event_calendar/reminders.py` dispatches reminders.
- `event_calendar/reminder_prefs.py` and `reminder_prefs_store.py` manage user preferences.
- `event_calendar/reminder_state.py` tracks reminder delivery state.
- `event_calendar/scheduler.py` runs scheduled calendar work.

Important persisted files include:

- `EVENT_CALENDAR_CACHE_FILE_PATH`
- `event_calendar_reminder_state.json`
- `event_calendar_reminder_prefs.json`

Relevant tests include:

- `tests/test_calendar_cache_contract.py`
- `tests/test_calendar_runtime_cache.py`
- `tests/test_calendar_reminders.py`
- `tests/test_calendar_reminders_dispatch.py`
- `tests/test_calendar_reminder_prefs.py`
- `tests/test_calendar_scheduler.py`
- `tests/test_calendar_service.py`

## Operational Checks

For reminder issues:

1. Confirm the bot has one active process only.
2. Check `logs/log.txt`, `logs/error_log.txt`, and `logs/telemetry_log.jsonl`.
3. Inspect the relevant persisted state file under `DATA_DIR`.
4. Confirm all reminder timestamps are UTC.
5. Confirm the scheduler has not been disabled for smoke/import validation.
6. Run focused tests for the touched reminder subsystem.

## Change Rules

- Keep Discord interaction code in command/view layers.
- Keep reminder rules and persistence in services/state modules.
- Preserve restart safety.
- Add regression coverage for duplicate-send, unsubscribe/cancel, stale-state, and preference changes.
