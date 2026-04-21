# Usage Telemetry — Audit & Design Note

**Date:** 2026-04-21  
**Scope:** `usage_tracker.py`, `decoraters.py`, `bot_instance.py`, `commands/admin_cmds.py`, `commands/telemetry_cmds.py`, `constants.py`

---

## 1. Current Event Sources (Producers)

| Source | File / Function | Event shape | Writes to | Awaited? | Failure impact |
|--------|----------------|-------------|-----------|----------|----------------|
| Slash command | `decoraters.py / @track_usage` | Full schema | JSONL + SQL queue | Fire-and-forget (`asyncio.create_task`) | None (caught) |
| Admin/channel deny | `decoraters.py / is_admin_and_notify_channel._log_denied` | Slim event, `success=False` | JSONL + SQL queue | Awaited (inside decorator) | None (caught) |
| Button/select | `bot_instance.py / _log_interaction_usage` | Slim event, `app_context=button/select` | JSONL + SQL queue | Fire-and-forget | None (caught) |
| Autocomplete | `bot_instance.py / _log_interaction_usage` | Slim event, `app_context=autocomplete` | JSONL + SQL queue | Fire-and-forget | None (caught) |
| Metric event | `usage_tracker.py / usage_event` | `command_name=metric:<name>`, `app_context=metric` | Metrics JSONL + SQL queue | Fire-and-forget | None (caught) |
| Alert event | `usage_tracker.py / _emit_alert` | `command_name=metric_alert:<name>`, `app_context=internal` | Alerts JSONL + SQL queue | Fire-and-forget | None (caught) |

---

## 2. Persistence Targets

| Target | Owner | Intent | Rotation/Pruning | Notes |
|--------|-------|--------|-----------------|-------|
| `dbo.BotCommandUsage` (SQL) | `usage_tracker.AsyncUsageTracker._flush` | Primary audit store | None (managed by DBA / SQL Server) | All event types including internal |
| `data/command_usage_YYYYMMDD.jsonl` | `usage_tracker._jsonl_path_utc` | Fallback / debug audit | **Now pruned** (default 30 days) | Written for every event |
| `data/metrics_YYYYMMDD.jsonl` | `usage_tracker._metrics_jsonl_path_utc` | Metric event log | **Now pruned** (default 30 days) | Metric events only |
| `data/alerts_YYYYMMDD.jsonl` | `usage_tracker._alerts_jsonl_path_utc` | Alert event log | **Now pruned** (default 30 days) | Alert events only |

---

## 3. Lifecycle Issues Found & Fixed

### Issue 1 — Dual singleton (FIXED)
`decoraters.py` maintained its own `_tracker: AsyncUsageTracker | None` separate from the
global `_GLOBAL_TRACKER` in `usage_tracker.py`. This meant slash commands used a different tracker
instance than metric/alert pseudo-events, producing two parallel SQL flush workers.

**Fix:** `decoraters.py / usage_tracker()` now delegates to `_ensure_global_tracker()` from
`usage_tracker.py`. All producers share the single global instance.

### Issue 2 — Import-time start (FIXED)
The old `usage_tracker()` factory in `decoraters.py` called `_tracker.start()` immediately,
which could fire before the event loop was ready (e.g., during collection/import phase).

**Fix:** Construction is now lightweight; `.start()` is called explicitly from `on_ready` in
`bot_instance.py`. Duplicate `start()` calls are idempotent and logged at DEBUG.

### Issue 3 — Auto-start in `_ensure_global_tracker` (FIXED)
`usage_tracker._ensure_global_tracker()` auto-started the tracker if a loop was detected.
This was removed to keep lifecycle ownership clearly in `bot_instance.py`.

### Issue 4 — No JSONL retention (FIXED)
Daily JSONL files accumulated without limit. Three families now have configurable retention
(default 30 days each). Pruning runs once at startup after the tracker is started.

---

## 4. Proposed Ownership Model

```
constants.py          – retention constants (USAGE_JSONL_RETENTION_DAYS etc.)
usage_tracker.py      – AsyncUsageTracker, prune_usage_jsonl, is_user_facing_event,
                        start_usage_tracker, stop_usage_tracker, usage_event
decoraters.py         – @track_usage decorator, usage_tracker() shim → global tracker
bot_instance.py       – explicit start (on_ready) + stop (shutdown) + prune at startup
commands/admin_cmds.py – /usage, /usage_detail reporting commands
commands/telemetry_cmds.py – shared SQL helpers (_ctx_filter_sql, _fetch_rows,
                              _user_facing_filter_sql)
```

---

## 5. Retention Policy

| Env var | Default | Applies to |
|---------|---------|-----------|
| `USAGE_JSONL_RETENTION_DAYS` | 30 | `command_usage_YYYYMMDD.jsonl` |
| `USAGE_METRICS_JSONL_RETENTION_DAYS` | 30 | `metrics_YYYYMMDD.jsonl` |
| `USAGE_ALERTS_JSONL_RETENTION_DAYS` | 30 | `alerts_YYYYMMDD.jsonl` |

Setting a value to `0` disables pruning for that family (files kept forever).

Pruning rules:
- Only the three known JSONL families are touched; no other files are affected.
- Current-day files are **never** deleted.
- Malformed filenames (cannot parse date) are skipped and logged.
- Dry-run mode available: `prune_usage_jsonl(data_dir, dry_run=True)`.
- Pruning runs once at bot startup, after the tracker is started.

---

## 6. Internal Pseudo-Events & Reporting

Internal pseudo-events (`metric:<name>` and `metric_alert:<name>`) are written to SQL alongside
user-facing events. They have:
- `command_name` prefixed with `metric:` or `metric_alert:`
- `app_context` of `metric` or `internal`
- `user_id = NULL`

### What `/usage` and `/usage_detail` now include/exclude

| `context_filter` value | Includes internal events? | Notes |
|------------------------|--------------------------|-------|
| `slash` (default) | ❌ No | `appcontext='slash'` filter naturally excludes them |
| `component` | ❌ No | |
| `autocomplete` | ❌ No | |
| `all` | ❌ No by default | SQL filter excludes `metric:*` and `metric_alert:*` names |
| `internal` (**new**) | ✅ Only internals | Shows only `metric:*` and `metric_alert:*` events |

The `is_user_facing_event(event: dict) -> bool` helper is available in `usage_tracker.py` for
Python-side filtering.

---

## 7. Shutdown Guarantee

`bot_instance.py / _graceful_teardown()` calls `await usage_tracker().stop()` which:
1. Sets the `_stop` event to signal the worker loop to exit.
2. Awaits the worker task (which drains all remaining queue items).
3. Logs the number of extra items drained.

This ensures no queued events are lost on clean shutdown.

---

## 8. Follow-up Recommendations

1. **Schedule pruning periodically** (e.g., daily) in addition to startup pruning, if JSONL volume
   is high and restarts are infrequent.
2. **Archive instead of delete**: Modify `prune_usage_jsonl` to move old files to a `.archive/`
   subdirectory rather than deleting, if long-term audit is required.
3. **SQL-side pruning**: Implement a stored procedure or maintenance job to prune
   `dbo.BotCommandUsage` rows older than a configurable threshold.
4. **Metric event SQL opt-out**: If metric pseudo-events cause noise in SQL reporting, consider
   skipping SQL flush for `app_context in ('metric', 'internal')` via a config flag.
5. **Command cache for autocomplete**: The `/usage_detail` autocomplete reads live
   `bot.application_commands`; this is robust but could cache results briefly if latency is a concern.
