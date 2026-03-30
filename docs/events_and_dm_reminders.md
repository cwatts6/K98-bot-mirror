# Events & DM Reminders (expanded)

This document expands the earlier overview with exact JSON examples, direct line-numbered references to the implementation (where available), and a suggested runtime checklist for local testing and debugging.

Primary source files
- event_scheduler.py — scheduler, trackers, DM delivery and rehydration logic  
  Permalink: https://github.com/cwatts6/K98-bot-mirror/blob/main/event_scheduler.py
- subscribe.py — user-facing subscribe command and interactive view  
  Permalink: https://github.com/cwatts6/K98-bot-mirror/blob/main/subscribe.py
- subscription_tracker.py — subscription persistence, validation and migration  
  Permalink: https://github.com/cwatts6/K98-bot-mirror/blob/main/subscription_tracker.py

Note: line-numbered references below point to functions and blocks in the two files where exact line numbers were available. For the subscription persistence module, the key function names and example JSON shapes are provided — open subscription_tracker.py if you want exact line numbers.

---

## Exact JSON examples (representative)

Use these examples as templates for the real files the bot reads/writes. The shapes match the code's save/load logic.

1) Subscription file (SUBSCRIPTION_FILE)
- Shape: top-level object where keys are user IDs (strings) and values are objects with username, subscriptions, reminder_times and optional metadata.
Example:
```json
{
  "123456789012345678": {
    "username": "alice#1234",
    "subscriptions": ["ruins", "altars"],
    "reminder_times": ["1h", "15m"],
    "created_at": "2025-10-20T12:00:00Z"
  },
  "987654321098765432": {
    "username": "bob#4321",
    "subscriptions": ["all"],
    "reminder_times": ["1h", "0m"],
    "created_at": "2025-10-20T13:25:00Z"
  }
}
```

2) dm_scheduled_tracker (DM_SCHEDULED_TRACKER_FILE)
- Shape: mapping event_id -> mapping user_id -> list (persisted as list, runtime uses set)
- event_id format: `<type>:<ISO8601 start_time>` (e.g. `ruins:2025-10-20T15:00:00+00:00`)
Example:
```json
{
  "ruins:2025-10-20T15:00:00+00:00": {
    "123456789012345678": [3600, 900],   // T-1h (3600s) and T-15m (900s)
    "987654321098765432": [3600, 0]      // T-1h and immediate T-0
  },
  "altars:2025-10-21T18:30:00+00:00": {
    "123456789012345678": [3600]
  }
}
```
Runtime note: when loaded, inner lists are converted to sets for fast membership checks (see save/load methods).

3) dm_sent_tracker (DM_SENT_TRACKER_FILE)
- Shape: mapping event_id -> mapping user_id -> list of delta_seconds already sent
Example:
```json
{
  "ruins:2025-10-20T15:00:00+00:00": {
    "123456789012345678": [3600],
    "987654321098765432": [3600, 0]
  }
}
```

4) failed DM log (FAILED_DM_LOG)
- Shape: array of failure objects (append-only)
Example:
```json
[
  {
    "user_id": "555666777888999000",
    "event_name": "Test Ruins",
    "event_time": "2025-10-20T15:00:00+00:00",
    "delta_seconds": 0,
    "reason": "DMs disabled",
    "timestamp": "2025-10-20T15:00:05Z"
  },
  {
    "user_id": "123456789012345678",
    "event_name": "Altars",
    "event_time": "2025-10-21T18:30:00+00:00",
    "delta_seconds": 3600,
    "reason": "HTTPError: 500 Server Error",
    "timestamp": "2025-10-20T14:10:00Z"
  }
]
```

5) reminder tracking file (REMINDER_TRACKING_FILE)
- Shape: mapping event_id -> metadata about the channel/message and optionally event snapshot.
Example:
```json
{
  "ruins:2025-10-20T15:00:00+00:00": {
    "channel_id": 999888777666555444,
    "message_id": 123456789012345678,
    "event": {
      "name": "Test Ruins",
      "type": "ruins",
      "start_time": "2025-10-20T15:00:00+00:00",
      "end_time": "2025-10-20T15:00:30+00:00",
      "zone": "Test Zone"
    }
  }
}
```
Runtime note: save_active_reminders writes live message id/channel id and attempts to include an event snapshot when available.

---

## Line-numbered references (quick navigation)

The numbers refer to the lines in the repository files at the current `main` commit shown in the code listing.

event_scheduler.py
- load_dm_sent_tracker — lines 157–185  
  Loads DM sent tracker and migrates old shapes to a per-user nested dict.
- save_dm_sent_tracker — lines 188–206  
  Atomic write to DM_SENT_TRACKER_FILE (writes a temp file then moves).
- save_dm_scheduled_tracker — lines 208–225  
  Serializes the scheduled tracker (sets -> lists) and writes atomically.
- load_dm_scheduled_tracker — lines 228–255  
  Loads scheduled tracker and converts inner lists to sets.
- log_failed_dm — lines 258–286  
  Appends structured failure objects to FAILED_DM_LOG (array).
- save_active_reminders — lines 380–410  
  Persists active reminder messages (channel/message) and attempts to attach event snapshot.
- load_active_reminders — lines 429–507  
  Reads reminder tracking file, re-fetches messages, reattaches view, restores active_reminders.
- rehydrate_dm_scheduled_tasks — lines 625–826  
  Recreates delayed and immediate DM tasks from persisted dm_scheduled_tracker. Important behavior:
  - prunes stale markers
  - for seconds_until > 0 -> creates delayed_user_dm tasks and registers them
  - for seconds_until within grace window -> sends immediate DM
  - removes markers for invalid users/events
- delayed_user_dm — lines 828–861  
  Sleeps until scheduled send then calls send_user_reminder and removes the scheduled marker.
- send_user_reminder — lines 862–932  
  Composes the DM embed, sends to the user, updates dm_sent_tracker and dm_scheduled_tracker. Handles discord.Forbidden and other exceptions by logging into failed DM log and tracker counters.
- schedule_event_reminders (main scheduling loop) — lines 934–1112  
  Primary loop:
  - loads trackers (lines 935–936)
  - rehydrates (lines 940–943)
  - iterates events, for each event and each subscriber schedules or immediately sends DMs using register_user_task/delayed_user_dm/send_user_reminder
  - persists dm_scheduled_tracker after scheduling (line ~1062–1063)
  - sleeps and loops (end of loop lines 1106–1111)
- cleanup_dm_scheduled_tracker & cleanup_dm_sent_tracker — lines 288–324 and 326–362  
  Prune stale events and empty user buckets; save after pruning.

subscribe.py
- constants import and defaults — lines 8–13
- SubscribeView class — lines 22–156  
  - view construction, Selects for event-types and times (lines 33–59)
  - helper `_apply_state` (line 87–91)
  - on_save handler — lines 105–156 (calls set_user_config and sends the welcome DM)
- Subscribe cog & command — lines 159–180  
  - load_subscriptions() in cog init (line 162)
  - `/subscribe` command entrypoint lines 164–179
- setup function — lines 182–184

subscription_tracker.py (key functions — open file for exact line numbers)
- load_subscriptions() — loads SUBSCRIPTION_FILE into memory
- save_subscriptions() — writes the subscription JSON (atomic write)
- get_user_config(user_id) — returns config for a user (or None)
- set_user_config(user_id, username_repr, selected_types, selected_times) — validate + persist
- migration & validation utilities: `_validated_types`, `_validated_times` and migration helpers

---

## Typical JSON lifecycle and how files are mutated

1. User runs `/subscribe` (subscribe.py lines 164–179). The interaction opens `SubscribeView` (22–86). On Save (105–156), `set_user_config` is invoked which writes into SUBSCRIPTION_FILE.
2. Scheduler starts (schedule_event_reminders lines 934–1112):
   - load_dm_sent_tracker (157–185)
   - load_dm_scheduled_tracker (228–255)
   - rehydrate persisted scheduled DMs (625–826) on startup (unless in test_mode)
3. When scheduler decides to schedule a per-user DM it:
   - adds delta_seconds to dm_scheduled_tracker runtime sets (lines ~1028–1032, 1062).
   - calls save_dm_scheduled_tracker (208–225) to persist the marker to disk (lists written).
4. When a DM is actually sent:
   - send_user_reminder (862–932) will append delta_seconds to dm_sent_tracker per user and save_dm_sent_tracker (188–206).
   - dm_scheduled_tracker entry for that user/delta is removed and save_dm_scheduled_tracker is called (930–931).
5. Rehydrate flow on restart (625–826) will recreate tasks or send immediate DMs for markers within the grace window, and prune invalid/stale markers.

---

## Suggested runtime checklist (local / dev)

Preparation
- Confirm Python environment and install requirements (discord client lib; check repo requirements if present).
- Ensure config/constants are set: confirm SUBSCRIPTION_FILE, DM_SCHEDULED_TRACKER_FILE, DM_SENT_TRACKER_FILE, FAILED_DM_LOG and REMINDER_TRACKING_FILE point to a writable directory for the running bot.
- Run the bot locally in a dev/test server where you can receive DMs (create a test bot invite).

Quick sanity checks (before running scheduler)
- File permissions: ensure the bot process can read/write the files used by the trackers.
  - Example:
    - ls -l path/to/SUBSCRIPTION_FILE path/to/DM_SCHEDULED_TRACKER_FILE
- Inspect current persisted files to understand state:
  - cat SUBSCRIPTION_FILE
  - cat DM_SCHEDULED_TRACKER_FILE
  - cat DM_SENT_TRACKER_FILE
  - cat FAILED_DM_LOG

Smoke tests once bot is running
1. Subscribe a test user
   - Run `/subscribe` (in a test guild) and pick types and times (subscribe.py lines 164–179; view save code 105–156).
   - After Save, confirm SUBSCRIPTION_FILE contains the test user entry.
   - Confirm the bot attempted to DM the user (welcome DM) — if DMs are blocked, subscribe view edits text to warn (subscribe.py lines 147–152).
2. Trigger a test reminder
   - Start the scheduler in test mode (schedule_event_reminders test_mode True). The function uses a short test event when test_mode is True and schedules sends using TEST_REMINDER_WINDOWS (see schedule_event_reminders lines 945–956).
   - Observe: bot will send channel reminder (send_reminder_at) and DM flows (send_user_reminder).
3. Simulate an immediate user DM
   - Use `send_user_reminder(user, test_event, delta)` from an interactive session (or create a small test harness) to see the exact embed and whether the send succeeds.
4. Inspect trackers after sends
   - Confirm DM_SENT_TRACKER_FILE includes the delta_seconds (save path created by save_dm_sent_tracker lines 188–206).
   - Confirm DM_SCHEDULED_TRACKER_FILE removed scheduled markers for completed sends (save_dm_scheduled_tracker lines 208–225).
   - Check FAILED_DM_LOG for any failure entries (log_failed_dm lines 258–286).

Targeted debugging recipes
- If no DMs are delivered but scheduler logs indicate scheduled sends:
  - Look at FAILED_DM_LOG for errors and reasons (log_failed_dm).
  - Confirm DM_SENT_TRACKER_FILE didn't get updated (would indicate send didn't complete or save failed).
  - Manually call send_user_reminder for a test user to reproduce the error and capture exception trace.
- If duplicate DMs occur:
  - Ensure only one scheduler process is running (multiple processes will schedule the same sends).
  - Verify dm_sent_tracker has the delta recorded (prevents duplicates) — if it's not saved (check save_dm_sent_tracker logs lines 200–204), check file writes/permissions.
- If scheduled markers persist after a successful send:
  - Confirm dm_scheduled_tracker removal logic is executed in send_user_reminder final block (line 930–931).
  - Check atomic save: temp file rename should succeed (save functions use temp + shutil.move; lines ~200–223).
- If rehydration sends unexpected immediate DMs after restart:
  - Inspect rehydrate grace threshold (`REHYDRATE_STALE_GRACE_SECONDS` around line 69) and the rehydrate logic (625–826). The grace window permits immediate sends for slightly-late markers.

Developer tips & common places to inspect (file/line quick map)
- event_scheduler.py:
  - Tracker load/save and migration: 157–206 (dm_sent), 208–255 (dm_scheduled)
  - Rehydration: 625–826
  - Send DM path: 828–932 (delayed_user_dm & send_user_reminder)
  - Main scheduling loop: 934–1112
  - Reminder message persistence: 380–410 (save_active_reminders) and 429–507 (load_active_reminders)
- subscribe.py:
  - View building & save handler: 22–156 (SubscribeView), save metamethod 105–156
  - `/subscribe` app command: 164–179
- subscription_tracker.py (persistence & validation)
  - Functions: load_subscriptions, save_subscriptions, get_user_config, set_user_config, migration, and validation helpers. Use those to inspect exact field names and allowed types.

---

## Troubleshooting checklist (concise)

1. Confirm bot can write to all persistence paths.
2. Confirm SUBSCRIPTION_FILE contains expected user entries after `/subscribe`. If not, inspect subscribe.py logs (see try/except when calling set_user_config lines 120–129).
3. Confirm `dm_scheduled_tracker` markers are created when the scheduler sees an event within scheduling window (schedule_event_reminders lines ~1018–1065).
4. Confirm `dm_sent_tracker` is updated after a send (send_user_reminder lines 906–911).
5. Inspect FAILED_DM_LOG for Forbidden / network errors (log_failed_dm lines 258–286).
6. If restarting: ensure rehydration behaves as expected (rehydrate_dm_scheduled_tasks lines 625–826).
7. If duplicates: ensure only one scheduler loop runs and `dm_sent_tracker` persisting is not failing.

---

If you would like, I can add this file into a branch and prepare a PR with the markdown content placed at `docs/events_and_dm_reminders.md`. The file above is ready to be committed as-is.
