# Canonical Command Reference

Last updated: 2026-07-13

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
primary=42 grouped_subcommands_detected=101 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=42
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
| `/me` | 9 |
| `/mge` | 6 |
| `/ops` | 25 |
| `/prekvk` | 2 |
| `/registry` | 7 |
| `/stats` | 1 |
| `/subscriptions` | 3 |
| `/vote_admin` | 12 |

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
register_governor, registry, stats, subscribe, subscriptions, unsubscribe, vote_admin
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
| Calendar | `/calendar_reminder_config` | `commands/calendar_cmds.py` | Flat | Public command-level access | Ephemeral redirect | Standard | Deprecated redirect to `/me reminders`; remove only after no-feedback window | Phase 13 approved redirect slice keeps the command registered but replaces the old calendar-specific panel with private guidance to `/me reminders`. |
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
| Inventory | `/myinventory` | `commands/inventory_cmds.py` | Flat | Public command-level access | Ephemeral prompt; report visibility follows user preference | Standard | Preserve; `/me inventory` opens summary first, then equivalent selector/report journey | Player inventory report. Phase 10 preserves this journey behind the `/me inventory` Open Report action without changing output visibility, range controls, or report export buttons. |
| Inventory | `/inventory_preferences` | `commands/inventory_cmds.py` | Flat | Public command-level access | Ephemeral redirect | Standard | Deprecated redirect to `/me preferences`; remove only after no-feedback window | Phase 13 approved redirect slice keeps the command registered but replaces the old preference prompt entry point with private guidance to `/me preferences`. |
| Inventory | `/export_inventory` | `commands/inventory_cmds.py` | Flat | Public command-level access | Ephemeral redirect | Standard | Deprecated redirect to `/me exports`; remove only after no-feedback window | Phase 13 explicit operator approval redirects the legacy export entry point while preserving export schemas/services behind `/me exports`. Old options remain accepted for compatibility but are ignored by the redirect handler. |
| Inventory | `/inventory audit` | `commands/inventory_cmds.py` | Grouped | Admin-only decorator | Ephemeral | Standard | Preserve | Inventory import audit. |
| Location | `/location import` | `commands/location_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Imports location data. |
| Location | `/location player` | `commands/location_cmds.py` | Grouped | Admin or leadership in allowed channels | User-selectable | Standard | Preserve | Leadership player-location lookup. |
| MGE | `/mge leadership_board` | `commands/mge_cmds.py` | Grouped | Decorator-gated leadership/admin path | Ephemeral | Standard | Preserve | Leadership board controls. |
| MGE | `/mge import_results` | `commands/mge_cmds.py` | Grouped | Decorator-gated admin path | Ephemeral | Standard | Preserve | Manual MGE results import. |
| MGE | `/mge refresh_cache` | `commands/mge_cmds.py` | Grouped | Decorator-gated admin path | Ephemeral | Standard | Preserve | Refreshes MGE caches. |
| MGE | `/mge refresh_award_reminders` | `commands/mge_cmds.py` | Grouped | Decorator-gated admin path | Ephemeral | Standard | Preserve | Refreshes MGE award reminders. |
| MGE | `/mge commanders` | `commands/mge_cmds.py` | Grouped | Decorator-gated admin path | Ephemeral | Standard | Preserve | MGE commander controls. |
| MGE | `/mge admin_completion` | `commands/mge_cmds.py` | Grouped | Decorator-gated admin path | Ephemeral | Standard | Preserve | Admin completion controls. |
| Player Self-Service | `/me dashboard` | `commands/me_cmds.py` | Grouped | Public command-level access; selected governor must be actively linked to the invoking Discord user | Ephemeral | Standard (`v1.03`) | Preserve; GovernorOS v2 Phase 5A direct Inventory integration | Private governor-first command centre. No linked governor shows setup guidance, one opens directly, and multiple use an author-gated governor-only selector before payload fetch. The selected-governor standalone card is 1180x760 and adds latest approved RSS, Speedups, and legendary-equivalent Materials totals for that governor only. Selected dashboards expose Accounts, Reminders, Preferences, Exports, direct RSS/Materials/Speedups actions, and Change Governor where applicable. The approved private embed remains the same-payload fallback. |
| Player Self-Service | `/me accounts` | `commands/me_cmds.py` | Grouped | Public command-level access | Ephemeral | Standard | Preserve; Phase 6 generated card and guided Manage flow smoke tested | Private account centre for account review, Governor ID lookup, registration, replacement, and removal with confirmation through one guided Manage journey. |
| Player Self-Service | `/me reminders` | `commands/me_cmds.py` | Grouped | Public command-level access | Ephemeral | Standard | Preserve; Phase 7 unified KVK and calendar reminder centre delivered | Private reminder centre for KVK event reminder review/autosave/remove-all plus calendar reminder status and service-backed calendar reminder configuration. Phase 13 redirects `/subscribe`, `/modify_subscription`, `/unsubscribe`, and `/calendar_reminder_config` here. |
| Player Self-Service | `/me preferences` | `commands/me_cmds.py` | Grouped | Public command-level access | Ephemeral | Standard | Preserve; Phase 12B adds SQL-backed Discord-user profile preferences | Private preference status with service-backed inventory visibility controls, access to the existing Governor VIP update flow, and Manage Profile dropdown controls for Discord-user-level timezone, location country, and preferred language. Location country is stored as a two-letter code and displayed with a derived readable country name; the private manager child window is replaced after profile updates. |
| Player Self-Service | `/me inventory` | `commands/me_cmds.py` | Grouped | Public command-level access | Ephemeral | Standard | Preserve; Phase 10 inventory summary card delivered and smoke tested | Private Inventory summary card using latest approved resources, speedups, and materials data for the player's registered governors, with no-data upload guidance and an Open Report handoff to the preserved `/myinventory` journey. |
| Player Self-Service | `/me resources` | `commands/me_cmds.py` | Grouped | Public command-level access; selected governor must be actively linked to the invoking Discord user | Ephemeral | Standard (`v1.00`) | GovernorOS v2 Phase 5A complete; operator smoke passed | Private selected-governor Resources report using the existing 1400x980 Inventory renderer, honest native no-data output, 1M/3M/6M/12M ranges, private exports, report tabs, Dashboard navigation, and paged Change Governor controls. |
| Player Self-Service | `/me materials` | `commands/me_cmds.py` | Grouped | Public command-level access; selected governor must be actively linked to the invoking Discord user | Ephemeral | Standard (`v1.00`) | GovernorOS v2 Phase 5A complete; operator smoke passed | Private selected-governor Materials report using the same renderer, no-data, privacy, range, export, Dashboard, and Change Governor interaction contract. |
| Player Self-Service | `/me speedups` | `commands/me_cmds.py` | Grouped | Public command-level access; selected governor must be actively linked to the invoking Discord user | Ephemeral | Standard (`v1.00`) | GovernorOS v2 Phase 5A complete; operator smoke passed | Private selected-governor Speedups report using the same renderer, no-data, privacy, range, export, Dashboard, and Change Governor interaction contract. |
| Player Self-Service | `/me exports` | `commands/me_cmds.py` | Grouped | Public command-level access | Ephemeral | Standard | Preserve; Phase 9 preferred export route with option windows | Private personal export centre with `Export Stats` and `Export Inventory` child option windows. Stats supports Excel, CSV, and Google Sheets formats plus day-window selection. Inventory supports format, view, registered-governor scope, and day-window selection. Phase 13 redirects legacy `/my_stats_export` and `/export_inventory` here while preserving export schemas/services. |
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
| Player/KVK | `/mygovernorid` | `commands/telemetry_cmds.py` | Flat | Public command-level access | Ephemeral redirect | Standard | Deprecated redirect to `/me accounts`; remove only after no-feedback window | Phase 13 approved redirect slice keeps the command registered but sends private guidance to `/me accounts`, where lookup and account linking now live. |
| Player/KVK | `/player_profile` | `commands/telemetry_cmds.py` | Flat | Admin or leadership in allowed channels | Ephemeral | Standard | Preserve; out of Phase 13 player self-service redirect scope | Leadership profile lookup, not a player self-service path. Review only in a future leadership/profile workflow task. |
| Player/KVK | `/mykvkcrystaltech` | `commands/telemetry_cmds.py` | Flat | CrystalTech channel decorator with admin override | User-selectable; defaults private | Standard | Preserve after Phase 13 audit | Player CrystalTech progress has channel and visibility rules not replaced by `/me`; keep out of legacy self-service redirect cleanup. |
| PreKvK | `/prekvk report` | `commands/prekvk_cmds.py` | Grouped | Public command-level access | Ephemeral redirect | Standard | Deprecated redirect to `/kvk rankings type:prekvk` in the KVK stats channel; remove after no-feedback window | Retained temporarily so old invocations receive migration guidance. |
| PreKvK Admin | `/prekvk import_history` | `commands/prekvk_admin_cmds.py` | Grouped helper-attached | Admin notify-channel decorator | Ephemeral | Standard | Preserve | PreKvK history import. |
| Registry | `/register_governor` | `commands/registry_cmds.py` | Flat | Public command-level access | Ephemeral redirect | Standard | Deprecated redirect to `/me accounts`; remove only after no-feedback window | Phase 13 approved redirect slice keeps the command registered but replaces the old registration view path with private guidance to `/me accounts`. |
| Registry | `/modify_registration` | `commands/registry_cmds.py` | Flat | Public command-level access | Ephemeral redirect | Standard | Deprecated redirect to `/me accounts`; remove only after no-feedback window | Phase 13 approved redirect slice keeps the command registered but replaces the old modify/remove view path with private guidance to `/me accounts`. |
| Registry | `/registry remove` | `commands/registry_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Removes registration by Discord user/slot. |
| Registry | `/registry remove_by_id` | `commands/registry_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Removes registration by Governor ID. |
| Registry | `/my_registrations` | `commands/registry_cmds.py` | Flat | Public command-level access | Ephemeral redirect | Standard | Deprecated redirect to `/me accounts`; remove only after no-feedback window | Phase 13 approved redirect slice keeps the command registered but replaces the old account list/action view path with private guidance to `/me accounts`. |
| Registry | `/registry admin_register` | `commands/registry_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Admin registration flow. |
| Registry | `/registry audit` | `commands/registry_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Registry audit. |
| Registry | `/registry bulk_export` | `commands/registry_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Registry bulk export. |
| Registry | `/registry bulk_import_dryrun` | `commands/registry_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Registry import preview. |
| Registry | `/registry bulk_import` | `commands/registry_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Registry import apply. |
| Stats/KVK | `/kvk_admin test_export` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve; moved from `/kvk test_export` in Phase 2A | KVK export test. |
| Stats/KVK | `/mykvkstats` | `commands/stats_cmds.py` | Flat | KVK stats channel decorator with admin override | Ephemeral redirect | Standard | Deprecated redirect to `/kvk stats`; remove after no-feedback window | Retained temporarily so old invocations receive migration guidance. |
| Stats/KVK | `/kvk_admin refresh_stats_cache` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve; moved from `/kvk refresh_stats_cache` in Phase 2A | Refreshes stats cache. |
| Stats/KVK | `/my_stats` | `commands/stats_cmds.py` | Flat | KVK stats channel decorator | User-selectable | Standard | Preserve; include in Player Self-Service v2 programme | Personal stats report remains channel-gated and is not replaced by `/me exports` or `/me dashboard`; modernisation is deferred to the v2 programme pack. |
| Stats/KVK | `/my_stats_export` | `commands/stats_cmds.py` | Flat | Public command-level access | Ephemeral redirect | Standard | Deprecated redirect to `/me exports`; remove only after no-feedback window | Phase 13 explicit operator approval redirects the legacy export entry point while preserving export schemas/services behind `/me exports`. Old options remain accepted for compatibility but are ignored by the redirect handler. |
| Stats/KVK | `/stats player` | `commands/stats_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral | Standard | Preserve; include in Player Self-Service v2 scoping review | Leadership player stats lookup remains live; alignment with the full stats/profile modernisation belongs in the v2 programme pack. |
| Stats/KVK | `/mykvkhistory` | `commands/stats_cmds.py` | Flat | KVK stats channel decorator with admin override | Ephemeral redirect | Standard | Deprecated redirect to `/kvk history`; remove after no-feedback window | Retained temporarily so old invocations receive migration guidance. |
| Stats/KVK | `/kvk_rankings` | `commands/stats_cmds.py` | Flat | KVK stats channel decorator with admin override | Public redirect | Standard | Deprecated redirect to `/kvk rankings type:kvk`; remove after no-feedback window | Retained temporarily so old invocations receive migration guidance. |
| Stats/KVK | `/kvk_admin export_all` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve; moved from `/kvk export_all` in Phase 2A | KVK Google Sheets export. |
| Stats/KVK | `/kvk_admin recompute` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve; moved from `/kvk recompute` in Phase 2A | Recompute KVK outputs. |
| Stats/KVK | `/kvk_admin list_scans` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve; moved from `/kvk list_scans` in Phase 2A | Recent scan diagnostics. |
| Stats/KVK | `/kvk_admin test_embed` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve; moved from `/kvk test_embed` in Phase 2A | KVK embed test. |
| Stats/KVK | `/kvk_admin window_preview` | `commands/stats_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve; moved from `/kvk window_preview` in Phase 2A | KVK window preview. |
| Subscriptions | `/subscribe` | `commands/subscriptions_cmds.py` | Flat | Public command-level access | Ephemeral redirect | Standard | Deprecated redirect to `/me reminders`; remove only after no-feedback window | Phase 13 approved redirect slice keeps the command registered but replaces the old subscription view path with private guidance to `/me reminders`. |
| Subscriptions | `/modify_subscription` | `commands/subscriptions_cmds.py` | Flat | Public command-level access | Ephemeral redirect | Standard | Deprecated redirect to `/me reminders`; remove only after no-feedback window | Phase 13 approved redirect slice keeps the command registered but replaces the old edit view path with private guidance to `/me reminders`. |
| Subscriptions | `/unsubscribe` | `commands/subscriptions_cmds.py` | Flat | Public command-level access | Ephemeral redirect | Standard | Deprecated redirect to `/me reminders`; remove only after no-feedback window | Phase 13 approved redirect slice keeps the command registered but replaces the old direct unsubscribe cleanup path with private guidance to `/me reminders`, where remove-all/unsubscribe is confirmed. |
| Subscriptions | `/subscriptions list` | `commands/subscriptions_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Subscriber list. |
| Subscriptions | `/subscriptions migrate_dryrun` | `commands/subscriptions_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Subscription migration preview. |
| Subscriptions | `/subscriptions migrate_apply` | `commands/subscriptions_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Subscription migration apply. |
| Telemetry | `/ping` | `commands/telemetry_cmds.py` | Flat | Public command-level access | Public | Standard | Preserve flat health/debug path | Basic bot response test. |
| Voting Admin | `/vote_admin create` | `commands/vote_admin_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral command response; public vote post side effect | Standard | Phase 6 single-question MultiSelect | Creates a SQL-backed live vote post with individual option fields, guided duration choices, reminders, controlled launch mention behaviour, `result_visibility` selection for public live or hidden-until-close results, and optional `vote_mode` plus min/max selection controls. `OneChoice` remains the default with up to six public option buttons; `MultiSelect` uses a public opener button and private selection panel. Dedicated group approved because there is no `/admin` group and `/ops` is operational rather than voting workflow ownership. |
| Voting Admin | `/vote_admin update` | `commands/vote_admin_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral guided update panel | Standard | Phase 2 guided voting framework | Selects a vote by autocomplete and opens an explicit edit-target menu for safe open-vote fields: title, description, close time, unsent reminders, and future mention settings. |
| Voting Admin | `/vote_admin close` | `commands/vote_admin_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral command response; public close announcement side effect | Standard | Phase 2 guided voting framework | Selects a vote by autocomplete, closes it early, disables buttons, refreshes the final card, and sends a controlled close announcement with winner, tie, or no-vote summary. |
| Voting Admin | `/vote_admin status` | `commands/vote_admin_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral | Standard | Phase 5 hidden-until-close results | Selects a vote by autocomplete and shows vote state, result visibility, private admin totals, reminder delivery state, and original message link. |
| Voting Admin | `/vote_admin dashboard` | `commands/vote_admin_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral private dashboard view | Standard | Phase 13 Private Dashboard UI | Opens a private aggregate vote/survey dashboard over the Phase 11 dashboard-safe reporting contract, with filters, pagination, refresh, message links, HiddenUntilClose private admin aggregate visibility, and no Discord identity, per-user rows, raw text/detail answers, or unsubmitted drafts. |
| Voting Admin | `/vote_admin engagement` | `commands/vote_admin_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral private export controls and private CSV file | Standard | Phase 20 Per-User Engagement Export | Opens private select-driven engagement controls for window and audience, then exports a CSV with all eligible Discord users sorted highest engagement first. Includes spreadsheet-safe Discord user ID, display name, role names, eligible opportunities, vote/survey participation split, total participation, missed count, engagement rate, and last participation date. Raw text/detail answers, per-answer detail, public output, graph output, workbook output, governor-linked reporting, and SQL-native combined reporting remain out of scope. |
| Voting Admin | `/vote_admin export` | `commands/vote_admin_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral command response and private CSV file | Standard | Phase 4 voter-level audit export | Selects a closed vote by autocomplete and privately exports either totals-only CSV results or voter-level audit rows via the `mode` option. Voter audit includes spreadsheet-safe Discord user ID text, resolved Discord name, selected option, original option, vote timestamps, and change flag; governor identity remains deferred. |
| Voting Admin | `/vote_admin survey_create` | `commands/vote_admin_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral guided builder; public survey post side effect | Standard | Phase 7 first survey slice | Opens a private admin builder for 2-5 required choice-only survey questions, then publishes a SQL-backed survey with a persistent public Answer survey button, close/reminder controls, response-change setting, and public-live or hidden-until-close result visibility. |
| Voting Admin | `/vote_admin survey_update` | `commands/vote_admin_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral guided update panel | Standard | Phase 16 survey authoring and update controls | Selects an open survey by autocomplete and opens an explicit edit-target menu for safe open-survey fields: title, description, close time, unsent reminders, future mention settings, option icons, response-change setting, and result visibility. Option icons, response-change setting, and result visibility are blocked after submitted responses exist; question/option semantics remain locked after publish. |
| Voting Admin | `/vote_admin survey_close` | `commands/vote_admin_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral command response; public close announcement side effect | Standard | Phase 7 first survey slice | Selects an open survey by autocomplete, closes it early, disables the answer button, refreshes the final card, and sends a controlled close announcement. |
| Voting Admin | `/vote_admin survey_status` | `commands/vote_admin_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral | Standard | Phase 7 first survey slice | Selects a survey by autocomplete and shows survey state, result visibility, private admin live totals, reminder delivery state, and original message link. |
| Voting Admin | `/vote_admin survey_export` | `commands/vote_admin_cmds.py` | Grouped | Admin or leadership decorator | Ephemeral command response and private CSV file(s) | Standard | Phase 10 Survey Export v2 first runtime slice | Selects one closed survey by autocomplete and privately exports totals, response-detail, or report-bundle CSV output via the `mode` option. Response-detail and report-bundle detail output include spreadsheet-safe Discord user ID text and resolved Discord name for admin/leadership-only reporting. Aggregate report-bundle files exclude raw text/detail answers and per-user rows; the response-detail file remains the private raw/detail profile. |

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
  `dashboard`, `accounts`, `reminders`, `preferences`, and `exports`. Phase 10 later added
  `inventory` as a sixth private subcommand after the Inventory summary-card scope was approved.
  Phase 3 turned
  `/me accounts` into the modern account centre for lookup, registration, replacement, and removal
  with confirmation and was smoke tested successfully on 2026-06-22. Phase 4 turned
  `/me reminders` into the modern reminder centre for setup review, subscribe/update, and
  unsubscribe confirmation while preserving legacy reminder commands. Phase 4 was smoke tested
  successfully after the reminder event-category normalization fix. Phase 5 added the private
  generated `/me dashboard` visual card with embed fallback and service-backed inventory
  visibility controls in `/me preferences`. Phase 6 added generated cards for Accounts,
  Reminders, Preferences, and Exports; simplified Accounts and Reminders around one guided
  `Manage` journey each; added reminder autosave; added Governor VIP access in Preferences; and
  preserved `/me exports` as private guidance without dashboard Quick Launch. Phase 7 aligned
  `/me dashboard` to the full-bleed Phase 6 card style and unified `/me reminders` so it shows
  and manages KVK event reminders plus calendar reminder preferences through service-backed
  persistence. Phase 8 turns `/me exports` into a private launchpad for validated default stats
  and inventory export actions while preserving current export schemas, private delivery, and
  dashboard-only Quick Launch. Phase 9 removes KVK command targets from the
  dashboard launch surface, adds safe private dashboard Inventory and Exports handoffs, and makes
  `/me exports` the preferred export route with Stats and Inventory option windows. Phase 13 later
  redirects `/my_stats_export` and `/export_inventory` to `/me exports` while keeping export
  schemas and services unchanged. Phase 10 added a matching `/me inventory`
  generated card using latest approved inventory data, kept `/myinventory` as the detailed report
  journey, and was smoke tested successfully in production PR #480. Phase 12B adds SQL-backed
  Discord-user-level timezone, location country, and preferred language profile preferences to
  `/me preferences` while preserving Inventory visibility, Inventory VIP, and the current
  session-based local-time toggle. Manage Profile uses guided dropdowns and replaces the private
  manager child window after updates.
- GovernorOS v2 Phase 5A completed private `/me resources`, `/me materials`, and `/me speedups`
  selected-governor reports while preserving `/me inventory` and `/myinventory`. It keeps the
  top-level count at 42, increases `/me` from 6 to 9 subcommands, makes the multiple-governor
  dashboard entry selector governor-only, and adds selected-governor Inventory totals plus direct
  report actions to the 1180x760 dashboard. Operator smoke passed populated, honest no-data, and
  report-preserving governor-switch journeys on 2026-07-13. Phase 5B is a renderer-presentation
  follow-on and does not change this command surface or interaction contract.
- Player Self-Service Command Centre Phase 13 started legacy redirect planning with audit/scope
  only. The operator-provided SQL extract and dated JSONL files showed nonzero broad usage for
  every audited legacy and related personal path, recent direct usage for several legacy paths, and
  `/me` usage concentrated in the smoke-test/operator window. After reviewing the classifications,
  the operator approved lightweight private redirects for account, reminder, calendar reminder,
  inventory preference, and export legacy entry points. Production PR #486 delivered the redirects
  and operator smoke on 2026-06-27 confirmed all approved redirects are correct. `/myinventory`,
  `/my_stats`, `/mykvkcrystaltech`, `/player_profile`, and `/stats player` remain live; final
  command-registration removal requires player briefing, usage monitoring, operator approval, and
  a no-feedback monitoring window.
- Redirected legacy player self-service paths remain registered in parallel while the `/me`
  workflow rolls out.
- Public calendar and KVK calendar paths remain flat pending a dedicated UX redesign.
- `/ping` remains flat for simple health/debug discoverability.
- Discord Voting Post Framework Phase 17 audited the expanded `/vote_admin` group after
  `/vote_admin survey_update` delivery and explicitly retained the existing command shape. No
  `/vote_admin` renames, aliases, nested groups, new top-level commands, launch/help panels,
  command-registration baseline changes, permission changes, autocomplete changes, usage-tracking
  changes, export/report/dashboard changes, or public-rendering changes were approved. Leadership
  is comfortable with the current naming convention, and the small operator set does not need a
  runtime help surface.
- Discord Voting Post Framework Phase 20 split leadership engagement reporting out of
  `/vote_admin dashboard` into `/vote_admin engagement` after operator approval. The dashboard is
  now focused on individual vote/survey item inspection again, while engagement owns select-driven
  private CSV export controls. Operator smoke testing confirmed the CSV data, controls, and role
  filters on 2026-07-08. This is a grouped `/vote_admin` addition, not a new top-level command or
  `/vote_admin` rename.

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
