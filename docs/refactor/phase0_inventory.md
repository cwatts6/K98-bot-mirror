# Phase 0 — Command/UI/Persistence Inventory

## 1) Boot chain + command registration wiring (authoritative map)

```text
run_bot.py (watchdog parent)
  -> launches child process DL_bot.py
      -> imports bot instance from bot_instance.py
      -> Calls Commands.register_commands(bot)
      -> bot.start(...)

bot_instance.on_ready()
  -> loads event cache
  -> loads DM trackers (dm_sent + dm_scheduled)
  -> schedules rehydrate_live_event_views(...)
  -> schedules rehydrate_tracked_views(...)
```

Secondary command entrypoints that exist in repo:
- `cogs/commands.py` (`SummaryCommands` Cog, slash commands + `setup(bot)` add_cog).
- `subscribe.py` (`Subscribe` Cog using `app_commands.command` + `setup(bot)` add_cog).

> Notes:
> - Runtime wiring in `DL_bot.py` currently uses `Commands.register_commands(bot)` for the primary command surface.
> - Cog-based command modules are present and loadable, but not the main path in current startup flow.

---

## 2) Slash command inventory

### 2.1 Primary slash commands (`Commands.py` via `register_commands`)

| Command | Module | Domain | Permission/decorator profile | Typical output |
|---|---|---|---|---|
| `summary` | `Commands.py` | Ops reporting | `versioned`, `safe_command`, `track_usage` | Summary embed/message |
| `weeksummary` | `Commands.py` | Ops reporting | `versioned`, `safe_command`, `track_usage` | 7-day summary embed/message |
| `history` | `Commands.py` | Ops reporting | `versioned`, `safe_command`, `track_usage` | Paginated history view |
| `failures` | `Commands.py` | Ops reporting | `versioned`, `safe_command`, `track_usage` | Failure log view |
| `ping` | `Commands.py` | Health | `versioned`, `safe_command`, `track_usage` | Pong/status text |
| `run_sql_proc` | `Commands.py` | Admin/import | `is_admin_and_notify_channel` + safe/versioned/usage | Status embed/text |
| `run_gsheets_export` | `Commands.py` | Admin/export | `is_admin_and_notify_channel` + safe/versioned/usage | Export status |
| `test_kvk_export` | `Commands.py` | Admin/test | `is_admin_and_notify_channel` + safe/versioned/usage | Test output embed |
| `restart_bot` | `Commands.py` | Admin/runtime | `is_admin_and_notify_channel` + safe/versioned/usage | Confirm + restart signal |
| `force_restart` | `Commands.py` | Admin/runtime | `is_admin_and_notify_channel`, `ext_commands.has_permissions` + safe/versioned/usage | Forced restart flow |
| `resync_commands` | `Commands.py` | Admin/discord sync | `is_admin_and_notify_channel` + safe/versioned/usage | Sync status |
| `show_command_versions` | `Commands.py` | Admin/diagnostics | `is_admin_and_notify_channel` + safe/versioned/usage | Version report |
| `validate_command_cache` | `Commands.py` | Admin/diagnostics | `is_admin_and_notify_channel` + safe/versioned/usage | Validation report |
| `view_restart_log` | `Commands.py` | Admin/logs | `is_admin_and_notify_channel` + safe/versioned/usage | Restart log output |
| `import_proc_config` | `Commands.py` | Admin/config | `is_admin_and_notify_channel`, `ext_commands.has_permissions` + safe/versioned/usage | Import result |
| `dl_bot_status` | `Commands.py` | Admin/health | `is_admin_and_notify_channel` + safe/versioned/usage | Status embed |
| `logs` | `Commands.py` | Admin/logs | `is_admin_and_notify_channel` + safe/versioned/usage | Log tail view |
| `show_logs` | `Commands.py` | Admin/logs | `is_admin_and_notify_channel` + safe/versioned/usage | Log display |
| `last_errors` | `Commands.py` | Admin/logs | `is_admin_and_notify_channel` + safe/versioned/usage | Error excerpt |
| `crash_log` | `Commands.py` | Admin/logs | `is_admin_and_notify_channel` + safe/versioned/usage | Crash log excerpt |
| `test_embed` | `Commands.py` | Admin/test | `is_admin_and_notify_channel` + safe/versioned/usage | Test embed |
| `mykvktargets` | `Commands.py` | Player/KVK | `channel_only` + safe/versioned/usage | Target lookup embed + selection UI |
| `mygovernorid` | `Commands.py` | Player/registry | safe/versioned/usage | Governor/account info |
| `nextfight` | `Commands.py` | Event reminders | safe/versioned/usage | Fight embed + persistent toggle view |
| `nextevent` | `Commands.py` | Event reminders | safe/versioned/usage | Event embed + persistent toggle view |
| `refresh_events` | `Commands.py` | Admin/events | `is_admin_and_notify_channel` + safe/versioned/usage | Refresh status |
| `refresh_kvk_overview` | `Commands.py` | Admin/events | `is_admin_and_notify_channel` + safe/versioned/usage | Overview refresh status |
| `subscribe` | `Commands.py` | Player/subscriptions | safe/versioned/usage | Subscription view |
| `modify_subscription` | `Commands.py` | Player/subscriptions | safe/versioned/usage | Subscription edit view |
| `unsubscribe` | `Commands.py` | Player/subscriptions | safe/versioned/usage | Confirmation/status |
| `list_subscribers` | `Commands.py` | Admin/subscriptions | `is_admin_and_notify_channel` + safe/versioned/usage | Subscriber list |
| `register_governor` | `Commands.py` | Player/registry | safe/versioned/usage | Registration UI + persistence |
| `modify_registration` | `Commands.py` | Player/registry | safe/versioned/usage | Modification UI + persistence |
| `remove_registration` | `Commands.py` | Admin/registry | `is_admin_and_notify_channel` + safe/versioned/usage | Removal confirmation/result |
| `remove_registration_by_id` | `Commands.py` | Admin/registry | `is_admin_and_notify_channel` + safe/versioned/usage | Removal result |
| `mykvkstats` | `Commands.py` | Player/stats | `channel_only` + safe/versioned/usage | Stats embed + account picker UI |
| `refresh_stats_cache` | `Commands.py` | Admin/stats | `is_admin_and_notify_channel` + safe/versioned/usage | Cache refresh status |
| `player_profile` | `Commands.py` | Player/profile | safe/versioned/usage | Profile embed/view |
| `import_locations` | `Commands.py` | Admin/location | `is_admin_and_notify_channel` + safe/versioned/usage | Import status |
| `player_location` | `Commands.py` | Player/location | safe/versioned/usage | Location embed + refresh view |
| `my_registrations` | `Commands.py` | Player/registry | safe/versioned/usage | Registration list + action view |
| `admin_register_governor` | `Commands.py` | Admin/registry | `is_admin_and_notify_channel` + safe/versioned/usage | Admin registration flow |
| `registration_audit` | `Commands.py` | Admin/registry | `is_admin_and_notify_channel` + safe/versioned/usage | Audit output |
| `bulk_export_registrations` | `Commands.py` | Admin/registry | `is_admin_and_notify_channel` + safe/versioned/usage | File export/status |
| `bulk_import_registrations_dryrun` | `Commands.py` | Admin/registry | `is_admin_and_notify_channel` + safe/versioned/usage | Dry-run report |
| `bulk_import_registrations` | `Commands.py` | Admin/registry | `is_admin_and_notify_channel` + safe/versioned/usage | Import report + confirm UI |
| `usage` | `Commands.py` | Admin/telemetry | `is_admin_or_leadership` + safe/versioned/usage | Usage summary |
| `usage_detail` | `Commands.py` | Admin/telemetry | `is_admin_or_leadership` + safe/versioned/usage | Detailed usage report |
| `my_stats` | `Commands.py` | Player/stats | `channel_only` + safe/versioned/usage | Personal stats embed + paging UI |
| `my_stats_export` | `Commands.py` | Player/stats | safe/versioned/usage | Export/attachment |
| `player_stats` | `Commands.py` | Admin/analytics | `is_admin_or_leadership` + safe/versioned/usage | Player stats output |
| `migrate_subscriptions_dryrun` | `Commands.py` | Admin/migrations | `is_admin_and_notify_channel` + safe/versioned/usage | Dry-run migration report |
| `migrate_subscriptions_apply` | `Commands.py` | Admin/migrations | `is_admin_and_notify_channel` + safe/versioned/usage | Applied migration report |
| `mykvkhistory` | `Commands.py` | Player/KVK history | `channel_only` + safe/versioned/usage | KVK history embeds + select UI |
| `kvk_rankings` | `Commands.py` | Player/KVK rankings | `channel_only` + safe/versioned/usage | Ranking embed + pagination view |
| `kvk_export_all` | `Commands.py` | Admin/KVK export | `is_admin_and_notify_channel` + safe/versioned/usage | Export status/file |
| `kvk_recompute` | `Commands.py` | Admin/KVK compute | `is_admin_and_notify_channel` + safe/versioned/usage | Recompute status |
| `kvk_list_scans` | `Commands.py` | Admin/KVK diagnostics | `is_admin_and_notify_channel` + safe/versioned/usage | Scan list |
| `test_kvk_embed` | `Commands.py` | Admin/KVK test | `is_admin_and_notify_channel` + safe/versioned/usage | Test embed |
| `kvk_window_preview` | `Commands.py` | Admin/KVK preview | `is_admin_and_notify_channel` + safe/versioned/usage | Window preview output |
| `crystaltech_validate` | `Commands.py` | Admin/crystaltech | `is_admin_and_notify_channel` + safe/versioned/usage | Validation report |
| `crystaltech_reload` | `Commands.py` | Admin/crystaltech | `is_admin_and_notify_channel` + safe/versioned/usage | Reload status |
| `mykvkcrystaltech` | `Commands.py` | Player/crystaltech | `channel_only` + safe/versioned/usage | Progress embed + controls |
| `crystaltech_admin_reset` | `Commands.py` | Admin/crystaltech | `is_admin_and_notify_channel` + safe/versioned/usage | Reset confirmation/result |
| `honor_rankings` | `Commands.py` | Player/honor | `channel_only` + safe/versioned/usage | Honor ranking embed + pagination |
| `honor_purge_last` | `Commands.py` | Admin/honor | `is_admin_and_notify_channel` + safe/versioned/usage | Purge status |

### 2.2 Cog/app-command surfaces present in repo

| Command | Module | Registration style | Notes |
|---|---|---|---|
| `summary`, `weeksummary`, `history`, `failures`, `ping` | `cogs/commands.py` | `commands.slash_command` on `SummaryCommands` Cog + `setup(bot)` | Overlaps with Commands.py command names; secondary/legacy path. |
| `subscribe` | `subscribe.py` | `@app_commands.command` on Cog + `setup(bot)` | Additional subscription command implementation path. |

---

## 3) UI inventory (Views / Modals / Select)

Legend:
- **Ephemeral-only**: intended for transient interaction responses (timeout-bound, no startup rehydrate path).
- **Persisted/Rehydrated**: can survive restart via tracked message IDs + `bot.add_view`/rehydrate logic.

### 3.1 Persisted / rehydrated UI (must keep import path or compatibility shim)

| UI class | Type | Module | Used by commands/flow | Persistence contract | custom_id/prefix scheme |
|---|---|---|---|---|---|
| `LocalTimeToggleView` | View | `embed_utils.py` | `nextevent`, `nextfight`, live event embeds | persisted via `VIEW_TRACKING_FILE` and rehydrated by `rehydrate_tracked_views`; also re-bound by `rehydrate_live_event_views` | deterministic `{sanitized_prefix}_local_time_toggle` |
| `NextFightView` | View (subclass) | `Commands.py` | `/nextfight` | tracked entry written to view tracker; rehydrated using key/prefix | prefix defaults to `nextfight` |
| `NextEventView` | View (subclass) | `Commands.py` | `/nextevent` | tracked entry written to view tracker; rehydrated using key/prefix | prefix defaults to `nextevent` |

### 3.2 Ephemeral/transient UI classes

- **Commands/UI flows (`Commands.py`)**
  - `LogTailView`, `MyRegsActionView`, `GovNameModal`, `ModifyStartView`, `RegisterStartView`, `EnterGovernorIDModal`, `GovernorSelect`, `GovernorSelectView`, `_LocationSelect`, `LocationSelectView`, `OpenFullSizeView`, `ProfileLinksView`, `MyKVKStatsSelectView`, `RefreshLocationView`, `KVKRankingView`, `TargetLookupView`, `FuzzySelectView`, `PostLookupActions`, `ConfirmRestartView`, `DynamicEventSelect` (2 defs), `ReminderSelect` (2 defs), `SubscriptionView` (2 defs), `ConfirmImportView`.
- **Governor registry module (`governor_registry.py`)**
  - `RegisterGovernorView`, `ModifyGovernorView`, `KVKStatsView`, `ConfirmRemoveView`.
- **Other modules**
  - `SubscribeView` (`subscribe.py`), `AccountPickerView` and `_AccountSelect` (`account_picker.py`),
    `SetupView`/`StepSelect`/`ProgressView`/`ResetConfirmView` (`crystaltech_ui.py`),
    `SliceButtons` and `AccountSelect` (`embed_my_stats.py`),
    `HistoryView` and `FailuresView` (`embed_utils.py`),
    `HonorRankingView` (`honor_rankings_view.py`),
    `KVKHistoryView`, `AccountSelect`, `CustomMetricView`, `LeftMetricSelect`, `RightMetricSelect` (`kvk_history_view.py`),
    `_KVKTargetsView`/`_KVKTargetsSelect` (`kvk_ui.py`, and analogous local classes in `target_utils.py`),
    `HealthView` (`bot_instance.py`).

> UI import-path stability note:
> - Persistent classes (`LocalTimeToggleView`, `NextFightView`, `NextEventView`) are restart-critical and should not be moved/renamed without compatibility shims.
> - Transient classes can generally be refactored more freely if command callsites are updated.

---

## 4) Persistence/state contracts

## 4.1 `VIEW_TRACKING_FILE` (`data/view_tracker.json`)

- Root schema: `dict[str, entry]`, keyed by logical view key/prefix (e.g., `nextevent`, `nextfight`, or other tracked keys).
- Entry required fields:
  - `channel_id` (int-convertible)
  - `message_id` (int-convertible)
  - `events` (non-empty list; validated/normalized via `events_from_persisted`)
- Entry optional fields:
  - `created_at`
  - `prefix`
- Rehydration: `rehydrate_tracked_views(bot)` fetches channel/message, rebuilds `LocalTimeToggleView`, and `bot.add_view(..., message_id=...)`.

Sample record:

```json
{
  "nextevent": {
    "channel_id": 123456789012345678,
    "message_id": 223456789012345678,
    "prefix": "nextevent",
    "created_at": "2026-01-01T00:00:00Z",
    "events": [
      {
        "name": "Next Ruins",
        "type": "ruins",
        "start_time": "2026-01-02T18:00:00Z"
      }
    ]
  }
}
```

## 4.2 Embed tracking schema (`EMBED_TRACKING_FILE` / `data/live_event_embeds.json`)

- In-memory shape: `embed_tracker: dict[event_id, entry]`.
- Current entry shape: `{ "message_id": int, "prefix": str }`.
- Legacy-compatible entry shape still handled: plain integer message_id.
- Rehydration path: `rehydrate_live_event_views(bot, event_channel_id)`.

Sample record:

```json
{
  "ruins:next_ruins:2026-01-02T18:00:00+00:00": {
    "message_id": 323456789012345678,
    "prefix": "countdown_next_ruins"
  }
}
```

## 4.3 Subscription tracker schema (`SUBSCRIPTION_FILE` / `data/subscription_tracker.json`)

- Root schema: `dict[user_id_str, user_config]`.
- `user_config` keys:
  - `username: str`
  - `subscriptions: list[str]` (normalized to `VALID_TYPES`)
  - `reminder_times: list[str]` (normalized to `DEFAULT_REMINDER_TIMES`)
- Migration utilities exist for legacy aliases and dropped keys.

Sample record:

```json
{
  "123456789012345678": {
    "username": "ExampleUser",
    "subscriptions": ["fights", "ruins"],
    "reminder_times": ["1h", "24h"]
  }
}
```

## 4.4 Governor registry schema (`REGISTRY_FILE` / `data/governor_registry.json`)

- Root schema: `dict[discord_user_id_str, user_block]`.
- `user_block` keys:
  - `discord_name: str`
  - `accounts: dict[account_type, {"GovernorID": str, "GovernorName": str}]`
- `GovernorID` is normalized via `normalize_governor_id` on load and register/modify operations.

Sample record:

```json
{
  "123456789012345678": {
    "discord_name": "User#1234",
    "accounts": {
      "Main": {"GovernorID": "856126", "GovernorName": "MainGov"},
      "Alt 1": {"GovernorID": "856127", "GovernorName": "AltGov"}
    }
  }
}
```

## 4.5 Event cache persistence schema (`CACHE_FILE_PATH` / `data/event_cache.json`)

- Root payload written by `save_event_cache()`:
  - `last_refreshed: ISO8601 UTC string`
  - `events: list[event]`
- Event fields require parseable `start_time` and `end_time` (ISO string on disk; datetime in memory).
- Invalid event rows are skipped on load.

Sample record:

```json
{
  "last_refreshed": "2026-01-01T00:00:00+00:00",
  "events": [
    {
      "name": "Next Ruins",
      "type": "ruins",
      "start_time": "2026-01-02T18:00:00+00:00",
      "end_time": "2026-01-02T20:00:00+00:00"
    }
  ]
}
```

## 4.6 DM reminder trackers (sent + scheduled)

- `DM_SENT_TRACKER_FILE` (`data/dm_sent_tracker.json`)
  - shape: `{event_id: {user_id: [delta_seconds, ...]}}`
- `DM_SCHEDULED_TRACKER_FILE` (`data/dm_scheduled_tracker.json`)
  - on-disk shape: `{event_id: {user_id: [delta_seconds, ...]}}`
  - in-memory shape migrates to sets for scheduled deltas: `{event_id: {user_id: set(...)}}`
- Both loaders migrate legacy non-nested formats to current nested-per-user schema.

---

## 5) Dependency hotspots / circular-import risk notes

1. **`Commands.py` monolith imports many domains + inner UI classes + command defs**
   - High fan-in/fan-out module; command registration and UI definitions are tightly coupled.
2. **Cross-reference between `embed_utils` and `Commands` via command-callback helper path**
   - `embed_utils.TargetLookupView` calls into `Commands.mykvktargets`, increasing cycle risk if modules are split incorrectly.
3. **Persistent UI rehydration depends on stable symbol locations**
   - `rehydrate_views` imports `LocalTimeToggleView` from `embed_utils`; moving class without shim can break startup rebind.
4. **Dual command systems coexist (`register_commands` + Cog/app_commands files)**
   - Refactors must keep one authoritative registration path and avoid duplicate name collisions.
5. **Tracker schemas are shared across runtime + maintenance tools/tests**
   - `view_tracker`, `embed_tracker`, `subscription_tracker`, registry, and event cache each have migration/normalization logic that downstream code assumes.

---

## 6) Refactor slicing guardrails from this inventory

- No command renames until command registration is centralized and duplicate Cog-path intent is explicitly decided.
- Persistent/rehydrated UI classes must either keep import path and class name stable, or ship compatibility exports.
- Schema-affecting changes must include migrations for:
  - `VIEW_TRACKING_FILE`
  - `EMBED_TRACKING_FILE`
  - `SUBSCRIPTION_FILE`
  - `REGISTRY_FILE`
  - `CACHE_FILE_PATH`
  - DM tracker files (`DM_SENT_TRACKER_FILE`, `DM_SCHEDULED_TRACKER_FILE`)
