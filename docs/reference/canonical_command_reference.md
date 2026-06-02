# Canonical Command Reference

Last updated: 2026-06-02

This is the maintained command reference for the K98 bot after Command Platform Phase 5A. Use
this document for current command paths, ownership, permissions, visibility, and command-surface
governance. Historical migration notes remain in `command_platform_audit.md` and
`command_surface_audit.md`.

## Source Of Truth

The runtime source of truth is the active `commands/` package registered through
`commands/register_all()`. Static command-count validation is provided by
`scripts/validate_command_registration.py`, which uses `commands/command_inventory.py`.

Current validator baseline:

```text
primary=39 grouped_subcommands_detected=76 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=39
```

Grouped command summary:

| Group | Subcommands |
|---|---:|
| `/activity` | 1 |
| `/ark` | 14 |
| `/crystaltech` | 3 |
| `/events` | 2 |
| `/honor` | 1 |
| `/inventory` | 2 |
| `/kvk` | 7 |
| `/location` | 2 |
| `/mge` | 6 |
| `/ops` | 25 |
| `/prekvk` | 2 |
| `/registry` | 7 |
| `/stats` | 1 |
| `/subscriptions` | 3 |

## Command Surface Rules

- New admin, leadership, operator, diagnostic, and domain-maintenance commands should be designed
  group-first unless an approved task explicitly keeps them flat.
- Preserve player self-service and public calendar/KVK calendar commands as flat paths until a
  dedicated workflow redesign is approved.
- All active commands are expected to use `@versioned()`, `@safe_command`, and `@track_usage()`
  unless a task explicitly documents a local exception.
- Grouped usage tracking should record the qualified command path, for example `stats player` or
  `inventory import`.
- Any command path change must update this file, relevant operator docs, command-registration
  validation expectations, and smoke references.
- Keep `scripts/validate_command_registration.py` green. The current warning threshold is 90
  top-level commands and the hard limit is Discord's 100 top-level application-command ceiling.

## Canonical Command Table

Legend:

- `Grouped` means the current path is a subcommand under a top-level group.
- `Flat` means the command remains a top-level application command.
- `Standard` version/usage means `@versioned()`, `@safe_command`, and `@track_usage()` are expected.
- `Public` permission means there is no command-level admin/leadership decorator; channel, service,
  or view-level checks may still apply.

| Domain | Current path | Owner module | Status | Permission model | Response visibility | Version/usage | Migration/disposition | Operator notes |
|---|---|---|---|---|---|---|---|---|
| Activity | `/activity top` | `commands/activity_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral | Standard | Preserve | Leadership activity report. |
| Ark | `/ark create_match` | `commands/ark_cmds.py` | Grouped | Admin or leadership plus Ark setup channel | Ephemeral | Standard | Preserve | Ark setup workflow. |
| Ark | `/ark force_announce` | `commands/ark_cmds.py` | Grouped | Admin or leadership plus Ark setup channel | Ephemeral command response; public announcement side effect | Standard | Preserve | Reposts active Ark registration. |
| Ark | `/ark amend_match` | `commands/ark_cmds.py` | Grouped | Admin or leadership plus Ark setup channel | Ephemeral | Standard | Preserve | Ark match amendment workflow. |
| Ark | `/ark cancel_match` | `commands/ark_cmds.py` | Grouped | Admin or leadership plus Ark setup channel | Ephemeral | Standard | Preserve | Cancels Ark match and related reminders/DMs. |
| Ark | `/ark reminder_prefs` | `commands/ark_cmds.py` | Grouped | Public command-level access | Ephemeral | Standard | Preserve | Player reminder settings. |
| Ark | `/ark set_preference` | `commands/ark_cmds.py` | Grouped | Admin or leadership plus Ark setup channel | Ephemeral | Standard | Preserve | Sets player team preference. |
| Ark | `/ark clear_preference` | `commands/ark_cmds.py` | Grouped | Admin or leadership plus Ark setup channel | Ephemeral | Standard | Preserve | Clears player team preference. |
| Ark | `/ark ban_add` | `commands/ark_cmds.py` | Grouped | Admin or leadership plus Ark setup channel | Ephemeral | Standard | Preserve | Adds Ark signup ban. |
| Ark | `/ark ban_revoke` | `commands/ark_cmds.py` | Grouped | Admin or leadership plus Ark setup channel | Ephemeral | Standard | Preserve | Revokes Ark signup ban. |
| Ark | `/ark ban_list` | `commands/ark_cmds.py` | Grouped | Admin or leadership plus Ark setup channel | Ephemeral | Standard | Preserve | Lists active Ark bans. |
| Ark | `/ark set_result` | `commands/ark_cmds.py` | Grouped | Admin or leadership plus Ark setup channel | Ephemeral | Standard | Preserve | Records Ark result. |
| Ark | `/ark report_players` | `commands/ark_cmds.py` | Grouped | Public command-level access | Public | Standard | Preserve | Player report. |
| Ark | `/ark generate_draft` | `commands/ark_cmds.py` | Grouped | Admin or leadership plus Ark setup channel | Ephemeral | Standard | Preserve | Generates draft Ark teams. |
| Ark | `/ark create_team` | `commands/ark_cmds.py` | Grouped | Admin or leadership plus Ark setup channel | Ephemeral | Standard | Preserve | Creates Ark team record. |
| Calendar | `/calendar` | `commands/calendar_cmds.py` | Flat | Public command-level access | Ephemeral | Standard | Defer public calendar redesign | Calendar overview remains flat. |
| Calendar | `/calendar_next_event` | `commands/calendar_cmds.py` | Flat | Public command-level access | Ephemeral | Standard | Defer public calendar redesign | Next generic calendar event. |
| Calendar | `/calendar_reminder_config` | `commands/calendar_cmds.py` | Flat | Public command-level access | Ephemeral | Standard | Defer player self-service redesign | Player reminder configuration. |
| Calendar Ops | `/ops calendar_refresh` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Runs full calendar refresh pipeline. |
| Calendar Ops | `/ops calendar_generate` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Generates calendar cache/source data. |
| Calendar Ops | `/ops calendar_publish_cache` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Publishes calendar runtime cache. |
| Calendar Ops | `/ops calendar_status` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Calendar diagnostics. |
| CrystalTech Ops | `/crystaltech validate` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Validates CrystalTech config. |
| CrystalTech Ops | `/crystaltech reload` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Reloads CrystalTech config/cache. |
| CrystalTech Ops | `/crystaltech admin_reset` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Resets CrystalTech state. |
| Events | `/next_kvk_fight` | `commands/events_cmds.py` | Flat | Public command-level access | Public | Standard | Defer public calendar/KVK calendar redesign | Public KVK fight view. |
| Events | `/next_kvk_event` | `commands/events_cmds.py` | Flat | Public command-level access | Public | Standard | Defer public calendar/KVK calendar redesign | Public KVK event view. |
| Events | `/events refresh` | `commands/events_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Refreshes event cache/countdowns. |
| Events | `/events refresh_kvk_overview` | `commands/events_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Refreshes daily KVK overview. |
| Honor/KVK | `/honor_rankings` | `commands/stats_cmds.py` | Flat | KVK stats channel decorator | Public | Standard | Defer public ranking UX | Public/channel-limited ranking output. |
| Honor/KVK | `/honor purge_last` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Purges latest honor scan. |
| Inventory | `/inventory import` | `commands/inventory_cmds.py` | Grouped | Inventory upload channel decorator with admin override | Ephemeral | Standard | Preserve | Imports resources, speedups, or materials screenshots. |
| Inventory | `/myinventory` | `commands/inventory_cmds.py` | Flat | Public command-level access | Ephemeral prompt; report visibility follows user preference | Standard | Defer player self-service redesign | Player inventory report. |
| Inventory | `/inventory_preferences` | `commands/inventory_cmds.py` | Flat | Public command-level access | Ephemeral | Standard | Defer player self-service redesign | Report visibility preference. |
| Inventory | `/export_inventory` | `commands/inventory_cmds.py` | Flat | Service authorization with admin override context | Ephemeral | Standard | Defer player self-service redesign | Exports approved inventory records. |
| Inventory | `/inventory audit` | `commands/inventory_cmds.py` | Grouped | Admin-only decorator | Ephemeral | Standard | Preserve | Inventory import audit. |
| Location | `/location import` | `commands/location_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Imports location data. |
| Location | `/location player` | `commands/location_cmds.py` | Grouped | Admin or leadership in allowed channels | User-selectable | Standard | Preserve | Leadership player-location lookup. |
| MGE | `/mge leadership_board` | `commands/mge_cmds.py` | Grouped | Decorator-gated leadership/admin path | Ephemeral | Standard | Preserve | Leadership board controls. |
| MGE | `/mge import_results` | `commands/mge_cmds.py` | Grouped | Decorator-gated admin path | Ephemeral | Standard | Preserve | Manual MGE results import. |
| MGE | `/mge refresh_cache` | `commands/mge_cmds.py` | Grouped | Decorator-gated admin path | Ephemeral | Standard | Preserve | Refreshes MGE caches. |
| MGE | `/mge refresh_award_reminders` | `commands/mge_cmds.py` | Grouped | Decorator-gated admin path | Ephemeral | Standard | Preserve | Refreshes MGE award reminders. |
| MGE | `/mge commanders` | `commands/mge_cmds.py` | Grouped | Decorator-gated admin path | Ephemeral | Standard | Preserve | MGE commander controls. |
| MGE | `/mge admin_completion` | `commands/mge_cmds.py` | Grouped | Decorator-gated admin path | Ephemeral | Standard | Preserve | Admin completion controls. |
| Ops | `/ops summary` | `commands/admin_cmds.py` | Grouped | Public command-level access | Public | Standard | Preserve | Daily file-processing summary. |
| Ops | `/ops weeksummary` | `commands/admin_cmds.py` | Grouped | Public command-level access | Public | Standard | Preserve | Seven-day file-processing summary. |
| Ops | `/ops history` | `commands/admin_cmds.py` | Grouped | Admin-only decorator | Public | Standard | Preserve | Processed-file history. |
| Ops | `/ops failures` | `commands/admin_cmds.py` | Grouped | Admin-only decorator | Public | Standard | Preserve | Failed-file history. |
| Ops | `/ops run_sql_proc` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Runs configured SQL procedure. |
| Ops | `/ops run_gsheets_export` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Runs Google Sheets export. |
| Ops | `/ops graceful_restart` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Preferred cooperative restart. |
| Ops | `/ops force_restart` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator plus permission checks | Ephemeral | Standard | Preserve | Break-glass restart. |
| Ops | `/ops resync_commands` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Manual command sync/cache update. |
| Ops | `/ops show_command_versions` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Version report. |
| Ops | `/ops validate_command_cache` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Command-cache validation. |
| Ops | `/ops view_restart_log` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Restart log output. |
| Ops | `/ops import_proc_config` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator plus permission checks | Ephemeral | Standard | Preserve | ProcConfig import. |
| Ops | `/ops dl_bot_status` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Bot status. |
| Ops | `/ops logs` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Log tail controls. |
| Ops | `/ops show_logs` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Log display. |
| Ops | `/ops last_errors` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Recent errors. |
| Ops | `/ops crash_log` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Crash log excerpt. |
| Ops | `/ops test_embed` | `commands/admin_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Test embed dispatch. |
| Ops | `/ops usage` | `commands/admin_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral | Standard | Preserve | Usage analytics summary. |
| Ops | `/ops usage_detail` | `commands/admin_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral | Standard | Preserve | Usage analytics detail. |
| Player/KVK | `/mykvktargets` | `commands/telemetry_cmds.py` | Flat | KVK target channel decorator with admin override | User-selectable | Standard | Defer player self-service redesign | Player target lookup. |
| Player/KVK | `/mygovernorid` | `commands/telemetry_cmds.py` | Flat | Public command-level access | Ephemeral | Standard | Defer player self-service redesign | Governor ID lookup. |
| Player/KVK | `/player_profile` | `commands/telemetry_cmds.py` | Flat | Admin or leadership in allowed channels | Ephemeral | Standard | Defer profile workflow review | Leadership profile lookup. |
| Player/KVK | `/mykvkcrystaltech` | `commands/telemetry_cmds.py` | Flat | CrystalTech channel decorator with admin override | User-selectable; defaults private | Standard | Defer player self-service redesign | Player CrystalTech progress. |
| PreKvK | `/prekvk report` | `commands/prekvk_cmds.py` | Grouped | Public command-level access | Ephemeral | Standard | Preserve | Public read-only PreKvK report. |
| PreKvK Admin | `/prekvk import_history` | `commands/prekvk_admin_cmds.py` | Grouped helper-attached | Admin notify-channel decorator | Ephemeral | Standard | Preserve | PreKvK history import. |
| Registry | `/register_governor` | `commands/registry_cmds.py` | Flat | Public command-level access | Ephemeral | Standard | Defer player self-service redesign | Player account registration. |
| Registry | `/modify_registration` | `commands/registry_cmds.py` | Flat | Public command-level access | Ephemeral | Standard | Defer player self-service redesign | Player registration modification. |
| Registry | `/registry remove` | `commands/registry_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Removes registration by Discord user/slot. |
| Registry | `/registry remove_by_id` | `commands/registry_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Removes registration by Governor ID. |
| Registry | `/my_registrations` | `commands/registry_cmds.py` | Flat | Public command-level access | Ephemeral | Standard | Defer player self-service redesign | Player registration list/actions. |
| Registry | `/registry admin_register` | `commands/registry_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Admin registration flow. |
| Registry | `/registry audit` | `commands/registry_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Registry audit. |
| Registry | `/registry bulk_export` | `commands/registry_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Registry bulk export. |
| Registry | `/registry bulk_import_dryrun` | `commands/registry_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Registry import preview. |
| Registry | `/registry bulk_import` | `commands/registry_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Registry import apply. |
| Stats/KVK | `/kvk test_export` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | KVK export test. |
| Stats/KVK | `/mykvkstats` | `commands/stats_cmds.py` | Flat | KVK stats channel decorator with admin override | Ephemeral | Standard | Defer player self-service redesign | Personal KVK stats. |
| Stats/KVK | `/kvk refresh_stats_cache` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Refreshes stats cache. |
| Stats/KVK | `/my_stats` | `commands/stats_cmds.py` | Flat | KVK stats channel decorator | User-selectable | Standard | Defer player self-service redesign | Personal stats report. |
| Stats/KVK | `/my_stats_export` | `commands/stats_cmds.py` | Flat | Public command-level access | Ephemeral | Standard | Defer player self-service redesign | Personal stats export. |
| Stats/KVK | `/stats player` | `commands/stats_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral | Standard | Preserve | Leadership player stats lookup. |
| Stats/KVK | `/mykvkhistory` | `commands/stats_cmds.py` | Flat | KVK stats channel decorator with admin override | User-selectable | Standard | Defer player self-service redesign | Personal KVK history. |
| Stats/KVK | `/kvk_rankings` | `commands/stats_cmds.py` | Flat | KVK stats channel decorator | Public | Standard | Defer public ranking UX | KVK rankings. |
| Stats/KVK | `/kvk export_all` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | KVK Google Sheets export. |
| Stats/KVK | `/kvk recompute` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Recompute KVK outputs. |
| Stats/KVK | `/kvk list_scans` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Recent scan diagnostics. |
| Stats/KVK | `/kvk test_embed` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | KVK embed test. |
| Stats/KVK | `/kvk window_preview` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | KVK window preview. |
| Subscriptions | `/subscribe` | `commands/subscriptions_cmds.py` | Flat | Public command-level access | Ephemeral | Standard | Defer player self-service redesign | Player subscription signup. |
| Subscriptions | `/modify_subscription` | `commands/subscriptions_cmds.py` | Flat | Public command-level access | Ephemeral | Standard | Defer player self-service redesign | Player subscription edit. |
| Subscriptions | `/unsubscribe` | `commands/subscriptions_cmds.py` | Flat | Public command-level access | Ephemeral | Standard | Defer player self-service redesign | Player unsubscribe. |
| Subscriptions | `/subscriptions list` | `commands/subscriptions_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Subscriber list. |
| Subscriptions | `/subscriptions migrate_dryrun` | `commands/subscriptions_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Subscription migration preview. |
| Subscriptions | `/subscriptions migrate_apply` | `commands/subscriptions_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Subscription migration apply. |
| Telemetry | `/ping` | `commands/telemetry_cmds.py` | Flat | Public command-level access | Public | Standard | Preserve flat health/debug path | Basic bot response test. |

## Migration And Disposition Notes

- Phase 3 grouped low-risk ops/reporting commands under `/ops`.
- Phase 4 grouped all Ark commands under `/ark`.
- Phase 5A grouped approved admin, leadership, and operator paths under `/activity`,
  `/crystaltech`, `/events`, `/honor`, `/inventory`, `/kvk`, `/location`, `/ops`, `/registry`,
  `/stats`, and `/subscriptions`.
- Player self-service paths remain flat pending a dedicated workflow redesign.
- Public calendar and KVK calendar paths remain flat pending a dedicated UX redesign.
- `/ping` remains flat for simple health/debug discoverability.

## Validation Expectations

For command documentation or command-surface changes, run or justify skipping:

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_inventory.py tests\test_command_registration_smoke.py
.\.venv\Scripts\python.exe -m pre_commit run -a
```

For runtime command changes, also run focused command, permission, interaction, and lifecycle tests
for the affected domain. Run or justify skipping Codex Security review when command runtime,
permission, interaction, SQL/data access, file handling, config, network, user-input, or
restart-sensitive persistence behavior changes.
