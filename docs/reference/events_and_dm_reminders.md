# Events And DM Reminders

Purpose: describe the current reminder systems and where to look when changing reminder,
subscription, or event-calendar behaviour.

## Read-only next-alert projection

`/me reminders` uses the same narrow pure eligibility functions as live KVK and Calendar dispatch.
The request path bulk-loads KVK upcoming-cache health/occurrences, the saved user configuration, and
one sent/scheduled tracker snapshot; it separately bulk-loads Calendar runtime-cache health/
occurrences, raw per-event preferences, and sent-key state. The pure functions accept an injected
timezone-aware UTC clock and already-loaded inputs. They create no task, timer, DM, acknowledgement,
cache refresh, network call, or persistence write.

The cross-system selector excludes sent alerts, retains genuine future KVK alerts represented by a
scheduled or rehydrated task marker, applies the KVK 48-hour horizon and late/immediate behavior,
applies Calendar all/specific preferences and grace/sent-key behavior, and never returns a past
display timestamp. It chooses the earliest future candidate with a deterministic KVK-first tie-break.
Healthy empty inputs and unavailable inputs remain distinct.

On 2026-07-15 the operator authorised a narrow correction discovered during the Phase 5D.1 parity
audit: KVK `now` maps to `timedelta(0)` and was previously skipped by a truthiness check. Live KVK
dispatch and read-only projection now treat it as the existing saved at-start option. The correction
uses the existing scheduling horizon, delayed task registry, sent/scheduled markers, rehydration,
retry, cleanup, and duplicate-send rules; it does not change Calendar or add a lead time.

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

## Active Public-Reminder Tracker Persistence

`event_scheduler.save_active_reminders()` writes the unchanged `REMINDER_TRACKING_FILE`
(`DATA_DIR/active_reminders.json`) using `file_utils.atomic_json_write`, with `ensure_ascii=True`,
`sort_keys=True`, and `default=None`. UTF-8 text, two-space indentation, recursive key order,
Unicode escaping, no appended newline, numeric Discord IDs, and event fallback datetime semantics
remain compatible with the previous direct writer. Invalid values still fail the save; they are
not silently converted to strings. Existing shared-writer callers retain their previous defaults.

Each invocation writes its own same-directory temp, flushes/fsyncs/closes it, then replaces the
tracker. WinError 32 receives the existing bounded retries; other errors, including WinError 5,
reach the existing non-raising `[REMINDER_CACHE] Failed to save:` warning. The last committed file
survives unsuccessful replacement. Handled failures clean up that invocation's temp best-effort;
a hard process exit can leave an ignored `.atomic.*.tmp`. Do not restore from or automatically
delete such files: verify process ownership before any manual operational cleanup.

All public saves currently execute synchronously on the bot loop after their existing mapping
mutation. The DM tracker offloads/lock are separate. Unique temps prevent temp-name collisions,
not cross-process lost updates. Singleton metadata checks reduce normal overlap but do not provide
exclusive process acquisition. Public send/delete/expiry task ownership remains separate deferred
work; Phase 2F changes neither that lifecycle nor the Discord-to-disk failure window.

Startup loads public reminders before event-cache load/refresh, starts the readiness-gated event
scheduler bundle, then performs orphan cleanup. Legacy periodic cleanup starts later. Rehydration
edits the stored message with the existing view and hashed custom ID; refresh only edits its embed.
Do not move these steps as part of persistence changes.

Candidate smoke is natural only: restart with a valid tracker, observe the same message/view,
then the next normal publication/replacement/expiry and valid JSON without save/load warnings.
An embed-only refresh does not save the tracker. Do not force mentions, delete live messages,
corrupt production state, or inject failures. Rollback is a bot commit revert/redeploy; prior code
reads candidate JSON without migration. Atomic replacement does not guarantee universal power-loss
durability or a transaction with Discord.

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


## Pre-KVK reservation operations - Phase 2G

Fresh production Pre-KVK/off-season admission uses `<STATS_ALERT_LOG>.dispatch.json` version 1
and an OS-backed `.dispatch.lck` lock. The CSV remains the successful-send/ping log; message state
retains its JSON shape. Test bypasses and same-day edits retain existing behavior. Active conflicts
block fresh sends across midnight/restart. Only proven pre-invocation non-delivery releases;
entered-send exceptions are uncertain because Discord client retries can obscure acceptance.
Accepted receipts replay state/CSV projections without another send. No exactly-once claim is made.

Preserve journal/logs for recovery. The local `ReservationStore.reconcile_receipt` API requires
positive token/channel/bot-author/payload/message/time verification. History-search absence or TTL
never permits retry. Unknown ownership remains blocked. Never unlink `.lck` files with live writers.
Stop all writers for rollout/rollback and back up CSV, message state and journal together. Old code
ignores the journal: reconcile accepted/uncertain attempts and retain consistent legacy projections
before downgrade; keep dispatch stopped if outcomes remain unknown. Mixed versions and independent
filesystems are excluded. Retention, singleton repair, public child supervision and DM redesign
remain separate. See archived Phase 2G pack sections 15–17 and its delivery closure for the protocol,
validated boundaries and carried-forward live smoke. The active Phase 2H pack owns isolated
Pre-KVK dispatch diagnostics; natural production calendar routing remains a separate observation.
