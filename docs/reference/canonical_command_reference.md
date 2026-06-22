# Canonical Command Reference

Last updated: 2026-06-22

This is the maintained command reference for the K98 bot after the completed Command Platform
Audit & Optimisation Programme. Use
this document for current command paths, ownership, permissions, visibility, and command-surface
governance. Historical migration notes remain in `command_platform_audit.md` and
`command_surface_audit.md`.

## Source Of Truth

The runtime source of truth is the active `commands/` package registered through
`commands/register_all()`. Static command-count validation is provided by
`scripts/validate_command_registration.py`, which uses `commands/command_inventory.py`.

Current validator baseline:

```text
primary=41 grouped_subcommands_detected=85 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=41
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
| `/kvk` | 4 |
| `/kvk_admin` | 7 |
| `/location` | 2 |
| `/me` | 5 |
| `/mge` | 6 |
| `/ops` | 25 |
| `/prekvk` | 2 |
| `/registry` | 7 |
| `/stats` | 1 |
| `/subscriptions` | 3 |

## Command Surface Rules

- New admin, leadership, operator, diagnostic, and domain-maintenance commands should be designed
  group-first unless an approved task explicitly keeps them flat.
- New top-level slash commands are blocked by `scripts/validate_command_registration.py` unless
  the task explicitly approves the new flat path, updates the approved top-level baseline in that
  validator, updates this reference, and documents why a grouped command is not suitable.
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

## Approved Top-Level Baseline

The approved top-level command baseline is enforced by `APPROVED_TOP_LEVEL_COMMANDS` in
`scripts/validate_command_registration.py`. The current approved baseline is:

```text
activity, ark, calendar, calendar_next_event, calendar_reminder_config, crystaltech, events,
export_inventory, honor, honor_rankings, inventory, inventory_preferences, kvk, kvk_admin, kvk_rankings,
location, me, mge, modify_registration, modify_subscription, my_registrations, my_stats,
my_stats_export, mygovernorid, myinventory, mykvkcrystaltech, mykvkhistory, mykvkstats,
mykvktargets, next_kvk_event, next_kvk_fight, ops, ping, player_profile, prekvk,
register_governor, registry, stats, subscribe, subscriptions, unsubscribe
```

If a task proposes a new top-level command, it must:

- state why the command cannot be grouped under an existing domain group
- include operator approval for the flat path
- update `APPROVED_TOP_LEVEL_COMMANDS`
- update this canonical command table and grouped summary if applicable
- update operator/user docs and smoke references for the new path
- run command registration validation and focused command inventory tests

Grouped subcommands do not require changing the approved top-level baseline unless they create a
new group.

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
| Honor/KVK | `/honor_rankings` | `commands/stats_cmds.py` | Flat | KVK stats channel decorator | Public redirect | Standard | Deprecated redirect to `/kvk rankings type:honor`; remove after no-feedback window | Retained temporarily so old invocations receive migration guidance. |
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
| Player Self-Service | `/me dashboard` | `commands/me_cmds.py` | Grouped | Public command-level access | Ephemeral | Standard | Preserve; Phase 2 read-only shell | Private player command centre status dashboard. `/me` owns the cross-domain player portal because account, reminder, preference, export, inventory, and KVK launch guidance do not fit cleanly under one existing domain group. |
| Player Self-Service | `/me accounts` | `commands/me_cmds.py` | Grouped | Public command-level access | Ephemeral | Standard | Preserve; Phase 3 modern account centre | Private account centre for account review, Governor ID lookup, registration, replacement, and removal with confirmation. |
| Player Self-Service | `/me reminders` | `commands/me_cmds.py` | Grouped | Public command-level access | Ephemeral | Standard | Preserve; Phase 2 read-only shell | Private KVK reminder setup status and transition guidance. |
| Player Self-Service | `/me preferences` | `commands/me_cmds.py` | Grouped | Public command-level access | Ephemeral | Standard | Preserve; Phase 2 read-only shell | Private player preference status, starting with inventory visibility. |
| Player Self-Service | `/me exports` | `commands/me_cmds.py` | Grouped | Public command-level access | Ephemeral | Standard | Preserve; Phase 2 read-only shell | Private personal export launch guidance; no files are generated by the shell. |
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
| Player/KVK | `/kvk stats` | `commands/kvk_cmds.py` | Grouped | KVK stats channel decorator with admin override | Private selector; selected single-account stats post public | Standard | Canonical player KVK stats command | Player KVK stats journey. |
| Player/KVK | `/kvk targets` | `commands/kvk_cmds.py` | Grouped | KVK target channel decorator with admin override | User-selectable | Standard | Canonical player KVK targets command | Player KVK targets journey. |
| Player/KVK | `/kvk history` | `commands/kvk_cmds.py` | Grouped | KVK stats channel decorator with admin override | Private picker/error handling where needed; selected/default single-account history posts public; preserves `governor_id` lookup | Standard | Canonical player KVK history command | Player KVK History, Summary, Trends, and CSV export journey. |
| Player/KVK | `/kvk rankings` | `commands/kvk_cmds.py` | Grouped | KVK stats channel decorator with admin override for all ranking types | Public unified browser for KVK, Honor, PreKvK, and records; private My Rank follow-ups for registered users | Standard | Canonical player ranking browser | Required `type` option supports `kvk`, `honor`, `prekvk`, and `records`; current KVK, Honor, PreKvK, and Hall of Fame records Top 10 render visual cards with embed fallback, records remain Top 10 only, current Top 25/50 remain compact browser output, and current KVK/Honor/PreKvK include a private My Rank button without adding Top 100 to primary controls. |
| Player/KVK | `/mykvktargets` | `commands/telemetry_cmds.py` | Flat | KVK target channel decorator with admin override | Ephemeral redirect | Standard | Deprecated redirect to `/kvk targets`; remove after no-feedback window | Retained temporarily so old invocations receive migration guidance. |
| Player/KVK | `/mygovernorid` | `commands/telemetry_cmds.py` | Flat | Public command-level access | Ephemeral | Standard | Defer player self-service redesign | Governor ID lookup. |
| Player/KVK | `/player_profile` | `commands/telemetry_cmds.py` | Flat | Admin or leadership in allowed channels | Ephemeral | Standard | Defer profile workflow review | Leadership profile lookup. |
| Player/KVK | `/mykvkcrystaltech` | `commands/telemetry_cmds.py` | Flat | CrystalTech channel decorator with admin override | User-selectable; defaults private | Standard | Defer player self-service redesign | Player CrystalTech progress. |
| PreKvK | `/prekvk report` | `commands/prekvk_cmds.py` | Grouped | Public command-level access | Ephemeral redirect | Standard | Deprecated redirect to `/kvk rankings type:prekvk` in the KVK stats channel; remove after no-feedback window | Retained temporarily so old invocations receive migration guidance. |
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
| Stats/KVK | `/kvk_admin test_export` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve; moved from `/kvk test_export` in Phase 2A | KVK export test. |
| Stats/KVK | `/mykvkstats` | `commands/stats_cmds.py` | Flat | KVK stats channel decorator with admin override | Ephemeral redirect | Standard | Deprecated redirect to `/kvk stats`; remove after no-feedback window | Retained temporarily so old invocations receive migration guidance. |
| Stats/KVK | `/kvk_admin refresh_stats_cache` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve; moved from `/kvk refresh_stats_cache` in Phase 2A | Refreshes stats cache. |
| Stats/KVK | `/my_stats` | `commands/stats_cmds.py` | Flat | KVK stats channel decorator | User-selectable | Standard | Defer player self-service redesign | Personal stats report. |
| Stats/KVK | `/my_stats_export` | `commands/stats_cmds.py` | Flat | Public command-level access | Ephemeral | Standard | Defer player self-service redesign | Personal stats export. |
| Stats/KVK | `/stats player` | `commands/stats_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral | Standard | Preserve | Leadership player stats lookup. |
| Stats/KVK | `/mykvkhistory` | `commands/stats_cmds.py` | Flat | KVK stats channel decorator with admin override | Ephemeral redirect | Standard | Deprecated redirect to `/kvk history`; remove after no-feedback window | Retained temporarily so old invocations receive migration guidance. |
| Stats/KVK | `/kvk_rankings` | `commands/stats_cmds.py` | Flat | KVK stats channel decorator with admin override | Public redirect | Standard | Deprecated redirect to `/kvk rankings type:kvk`; remove after no-feedback window | Retained temporarily so old invocations receive migration guidance. |
| Stats/KVK | `/kvk_admin export_all` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve; moved from `/kvk export_all` in Phase 2A | KVK Google Sheets export. |
| Stats/KVK | `/kvk_admin recompute` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve; moved from `/kvk recompute` in Phase 2A | Recompute KVK outputs. |
| Stats/KVK | `/kvk_admin list_scans` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve; moved from `/kvk list_scans` in Phase 2A | Recent scan diagnostics. |
| Stats/KVK | `/kvk_admin test_embed` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve; moved from `/kvk test_embed` in Phase 2A | KVK embed test. |
| Stats/KVK | `/kvk_admin window_preview` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve; moved from `/kvk window_preview` in Phase 2A | KVK window preview. |
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
  `/crystaltech`, `/events`, `/honor`, `/inventory`, `/kvk` (renamed to `/kvk_admin` in Phase 2A), `/location`, `/ops`, `/registry`,
  `/stats`, and `/subscriptions`.
- KVK Player Experience Redesign Phase 2A moved KVK admin/operator commands from `/kvk` to
  `/kvk_admin`, leaving `/kvk` available for the player KVK scaffold.
- KVK Player Experience Redesign Phase 2B added the player `/kvk` group with `stats`, `targets`,
  `history`, and `rankings` subcommands in parallel with the legacy flat player commands.
- KVK Player Experience Redesign Phase 7 changed `/mykvkstats`, `/mykvktargets`,
  `/mykvkhistory`, `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` into temporary
  deprecated redirect/help responses. The old command paths remain registered only for migration
  guidance and should be removed after the agreed no-feedback window.
- Phase 7 follow-up channel consistency aligned `/kvk targets` to `KVK_TARGET_CHANNEL_ID` with
  admin override and `/kvk stats`, `/kvk history`, and all `/kvk rankings` types to
  `KVK_PLAYER_STATS_CHANNEL_ID` with admin override.
- Player Self-Service Command Centre Phase 2 added `/me` with five private subcommands:
  `dashboard`, `accounts`, `reminders`, `preferences`, and `exports`. Phase 3 turned
  `/me accounts` into the modern account centre for lookup, registration, replacement, and removal
  with confirmation. Existing legacy self-service commands remain registered in parallel.
- Legacy player self-service paths remain registered in parallel while the `/me` workflow rolls out.
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
