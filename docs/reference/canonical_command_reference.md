# Canonical Command Reference

Last updated: 2026-07-18

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
primary=37 grouped_subcommands_detected=100 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=37
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
| `/me` | 8 |
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

The Phase 8 implementation baseline contains 36 top-level commands and 100 grouped subcommands.
`/me` contains eight grouped subcommands, `/stats` contains one, and `/inventory` contains two.

```text
activity, ark, calendar, calendar_next_event, calendar_reminder_config, crystaltech, events,
honor, honor_rankings, inventory, kvk, kvk_admin, kvk_rankings, location, me, mge,
modify_registration, modify_subscription, my_registrations, mygovernorid,
mykvkcrystaltech, mykvkhistory, mykvkstats,
mykvktargets, next_kvk_event, next_kvk_fight, ops, ping, prekvk,
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
| Inventory | `/inventory audit` | `commands/inventory_cmds.py` | Grouped | Admin-only decorator | Ephemeral | Standard | Preserve | Inventory import audit. |
| Location | `/location import` | `commands/location_cmds.py` | Grouped | Admin notify-channel decorator | Ephemeral | Standard | Preserve | Imports location data. |
| Location | `/location player` | `commands/location_cmds.py` | Grouped | Admin or leadership in allowed channels | User-selectable | Standard | Preserve | Leadership player-location lookup. |
| MGE | `/mge leadership_board` | `commands/mge_cmds.py` | Grouped | Decorator-gated leadership/admin path | Ephemeral | Standard | Preserve | Leadership board controls. |
| MGE | `/mge import_results` | `commands/mge_cmds.py` | Grouped | Decorator-gated admin path | Ephemeral | Standard | Preserve | Manual MGE results import. |
| MGE | `/mge refresh_cache` | `commands/mge_cmds.py` | Grouped | Decorator-gated admin path | Ephemeral | Standard | Preserve | Refreshes MGE caches. |
| MGE | `/mge refresh_award_reminders` | `commands/mge_cmds.py` | Grouped | Decorator-gated admin path | Ephemeral | Standard | Preserve | Refreshes MGE award reminders. |
| MGE | `/mge commanders` | `commands/mge_cmds.py` | Grouped | Decorator-gated admin path | Ephemeral | Standard | Preserve | MGE commander controls. |
| MGE | `/mge admin_completion` | `commands/mge_cmds.py` | Grouped | Decorator-gated admin path | Ephemeral | Standard | Preserve | Admin completion controls. |
| Player Self-Service | `/me dashboard` | `commands/me_cmds.py` | Grouped | Public command-level access; selected governor must be actively linked to the invoking Discord user | Ephemeral | Standard (`v1.03`) | Preserve; GovernorOS v2 Phase 6 Stats handoff implemented | Private governor-first command centre. No linked governor shows setup guidance, one opens directly, and multiple use an author-gated governor-only selector before payload fetch. The selected-governor standalone card is 1180x760 and adds latest approved RSS, Speedups, and legendary-equivalent Materials totals for that governor only. Row 0 exposes Accounts, Reminders, Preferences, and Stats; Stats reuses the validated selected Governor ID and the personal Stats service revalidates current linkage before its data read. Direct RSS/Speedups/Materials and Change Governor remain where applicable. The approved private embed remains the same-payload fallback. |
| Player Self-Service | `/me accounts` | `commands/me_cmds.py` | Grouped | Public command-level access | Ephemeral | Standard | GovernorOS v2 Phase 5G Account Data host; operator accepted 2026-07-17 | Private Discord-user/all-linked-governor portfolio card with author avatar, Main/role ordering, accepted Account Summary visuals and guided account management. Account Summary owns the author-gated `Download data` child journey: a default Account-Summary-first Excel/Google Sheets-compatible workbook, exact 29-column current snapshot CSV, or raw Stats history CSV. Download execution re-resolves active registry authority, applies one exact inclusive 30/60/90/180/360-day window where applicable, and reports actual written rows/date bounds plus separate freshness. It does not show Change Governor; selected governor context is retained only for validated Dashboard return. |
| Player Self-Service | `/me reminders` | `commands/me_cmds.py` | Grouped | Public command-level access | Ephemeral | Standard (`v1.01`) | Phase 5D.1 complete and operator accepted 2026-07-15 | Private Discord-user-level premium reminder centre with invoking-user avatar/safe fallback, duplicate-safe Kingdom identity, earned ACTIVE/REVIEW/OFF state, and an authoritative scheduler-parity hero: earliest future KVK/Calendar alert, healthy `NO UPCOMING ALERT`, or request-level `SCHEDULE UNAVAILABLE`. Friendly labels and absolute UTC times never expose raw occurrence keys or imply delivery success; the event start date-time is visually prominent in bold gold. The existing 1702x924 card, stable filename, same-payload fallback, Manage journey, KVK autosave/remove-all/confirmation DM, Calendar Settings, privacy, navigation, timeout, attachment cleanup, and return-only Dashboard context remain unchanged. Phase 13 redirects `/subscribe`, `/modify_subscription`, `/unsubscribe`, and `/calendar_reminder_config` here; the three existing next-event commands remain registered and unchanged. Projection bulk-loads each source/config/tracker once, uses one injected UTC clock including the default KVK snapshot, and performs no tasks, DMs, acknowledgements, refreshes, network calls, or writes. The operator authorised the narrow KVK zero-duration correction so saved `now` is genuinely at-start eligible through the existing scheduling/tracker/rehydration/retry machinery. No Calendar, persistence, event-source/type, lead-time, cadence, SQL, command-registration, or DM-content contract changed. |
| Player Self-Service | `/me preferences` | `commands/me_cmds.py` | Grouped | Public command-level access | Ephemeral | Standard (`v1.02`) | Preserve; GovernorOS v2 Phase 5F profile-only consolidation | Private Discord-user-level Personal Settings centre for saved timezone, location country, preferred-language metadata, and derived DST-aware local-time context. The successful result is an avatar-enabled standalone 1702x924 attachment using `assets/me/cards/me_preferences.png`, with a same-authorised-payload fallback and graceful timeout. The header is `LOCAL` when the saved timezone is usable and `UTC` otherwise; this is derived display state, not a saved preference. Manage settings opens Regional Profile directly. Regional fields retain existing catalogs, paging, validation/null semantics, atomic field-specific save/clear, superseded/concurrent safety, Back navigation, timeout, fallback, attachment replacement, and cleanup. There is no Inventory visibility, Privacy & Sharing journey, VIP content/action, or Change Governor. Governor-specific VIP editing remains owned by Manage Accounts -> Update VIP. No SQL object/schema/deployment change. |
| Player Self-Service | `/me stats` | `commands/me_cmds.py` | Grouped | Public command-level access; every scope/period load revalidates active registry linkage | Ephemeral only | Standard (`v1.00`) | GovernorOS v2 Phase 6 complete; operator smoke accepted 2026-07-18 | Private-anywhere Period Performance for the selected Dashboard governor, otherwise Main, otherwise the first valid canonical slot; All Linked is explicit. Overview, Activity, and Combat share the approved opaque 1702x924 avatar-enabled card and same-payload accessible fallback. Seven exact Stats-anchor periods include Last 90/180 Days, signed corrections, truthful source/account-day coverage, READY/PARTIAL/NO DATA/UNAVAILABLE, integrated RSS/Fort and Combat trends, opaque duplicate-name-safe governor tokens, 24-governor pages plus All Linked, latest-transition-wins handling, bounded authorized cache reuse, and a 180-second preserve-and-disable timeout. The accepted presentation uses the Reminders-aligned right-hand pill/header stack, compact totals and averages, consistent chart date axes, latest anchor-date `KingdomScanData4.ScanDate` as `Data last refreshed`, and a separate generated-time footer. No Ark, ranks, targets, badges, download, or export action is present. |
| Player Self-Service | `/me resources` | `commands/me_cmds.py` | Grouped | Public command-level access; selected governor must be actively linked to the invoking Discord user | Ephemeral | Standard (`v1.00`) | GovernorOS v2 Phase 5B complete; operator smoke passed 2026-07-13 | Private selected-governor Resources report using the report-specific premium 1400x980 Inventory backdrop, honest native no-data output, 1M/3M/6M/12M ranges, private exports, report tabs, Dashboard navigation, and paged Change Governor controls. |
| Player Self-Service | `/me materials` | `commands/me_cmds.py` | Grouped | Public command-level access; selected governor must be actively linked to the invoking Discord user | Ephemeral | Standard (`v1.00`) | GovernorOS v2 Phase 5B complete; operator smoke passed 2026-07-13 | Private selected-governor Materials report using the report-specific premium 1400x980 Inventory backdrop with unchanged no-data, privacy, range, export, Dashboard, and Change Governor interaction contract. |
| Player Self-Service | `/me speedups` | `commands/me_cmds.py` | Grouped | Public command-level access; selected governor must be actively linked to the invoking Discord user | Ephemeral | Standard (`v1.00`) | GovernorOS v2 Phase 5B complete; operator smoke passed 2026-07-13 | Private selected-governor Speedups report using the report-specific premium 1400x980 Inventory backdrop with unchanged no-data, privacy, range, export, Dashboard, and Change Governor interaction contract. |
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
| Player/KVK | `/kvk history` | `commands/kvk_cmds.py` | Grouped | KVK stats channel decorator with admin override | Private picker/error handling where needed; selected/default single-account history posts public; preserves `governor_id` lookup | Standard | Canonical player KVK history command; `/me history` explicitly rejected | Player KVK History, Summary, Trends, and CSV export journey. The 2026-07-18 placement decision keeps this as the one KVK-history entry point; no `/me history`, alias, redirect, or Dashboard History action is planned. |
| Player/KVK | `/kvk rankings` | `commands/kvk_cmds.py` | Grouped | KVK stats channel decorator with admin override for all ranking types | Public unified browser for KVK, Honor, PreKvK, and records; private My Rank follow-ups for registered users | Standard | Canonical player ranking browser | Required `type` option supports `kvk`, `honor`, `prekvk`, and `records`; current KVK, Honor, PreKvK, and Hall of Fame records Top 10 render visual cards with embed fallback, records remain Top 10 only, current Top 25/50 remain compact browser output, and current KVK/Honor/PreKvK include a private My Rank button without adding Top 100 to primary controls. |
| Player/KVK | `/mykvktargets` | `commands/telemetry_cmds.py` | Flat | KVK target channel decorator with admin override | Ephemeral redirect | Standard | Deprecated redirect to `/kvk targets`; remove after no-feedback window | Retained temporarily so old invocations receive migration guidance. |
| Player/KVK | `/mygovernorid` | `commands/telemetry_cmds.py` | Flat | Public command-level access | Ephemeral redirect | Standard | Deprecated redirect to `/me accounts`; remove only after no-feedback window | Phase 13 approved redirect slice keeps the command registered but sends private guidance to `/me accounts`, where lookup and account linking now live. |
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
| Stats/KVK | `/stats player` | `commands/stats_cmds.py` | Grouped | Dedicated stable leadership-role-ID/channel check; admin additionally allowed in Leadership and Notify channel/threads; revalidated before every cache, state or data access | Private/ephemeral only | Standard | Canonical leadership player route; Phase 8 complete and accepted; Phase 8.1 implementation in validation | One selected-governor review with 30/90/180/360-day kingdom contribution, ranks, primary Scan Presence ratio/percentage, bounded Last Active evidence, Activity Index v1, latest-three finalized-KVK performance, linked-governor context/navigation, complete grouped/paged aliases and alliances, Overview-only location/shield, dedicated 90-day identified audit retention, and no `/me inspect`, public share, or export. |
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

## Approved Command Roadmap And Completed No-Command Closeout

The current command table and validator baseline above remain authoritative until each phase is
deployed and commands are resynced.

### Phase 7

- Completed and operator accepted on 2026-07-19 in mirror PR #229 and production PR #536.
- No command change or resync occurred.
- `/me` remains eight subcommands.
- `/me history` will not be implemented.
- `/kvk history` remains canonical.
- Runtime remains `37 top-level / 100 grouped / 8 me / 2 inventory`.
- The accepted `/me` visual contract includes centred top-right state pills, complete
  Accounts/Reminders/Preferences/Stats row-0 navigation, page-local controls below row 0,
  compact/unit-correct content, source/generated separation, same-payload fallbacks,
  latest-transition-wins, preserve-and-disable timeout, and cleanup.
- Dashboard remains `1180x760`, core summaries `1702x924`, and Inventory `1400x980` with its
  report-specific visual/data/export structure.

### Phase 8

- Complete, deployed, resynced, production smoke tested and operator accepted on 2026-07-21.
- Modernised existing `/stats player` as the only leadership player-review route.
- Do not create `/me inspect`.
- Remove top-level `/player_profile` with no redirect.
- Accepted resynced surface: `36 top-level / 100 grouped / 8 me / 1 stats / 2 inventory`.
- Dedicated stable-role-ID/channel gate:
  - leadership role IDs in Leadership channel/threads;
  - admin in Leadership and Notify channel/threads;
  - no role-name-only, Ark Setup, DM, or other-channel authorization.

### Phase 8.1

- Refine the accepted `/stats player` visual hierarchy, Presence/Last Active signal, KVK/record
  readability and measured performance.
- No command, option or permission change; no resync expected.
- Preserve `36 / 100 / 8 / 1 / 2`.
- The approved SQL addition is the bounded Last Active procedure. Any table/index or further SQL
  optimisation remains actual-plan/read/timing evidence- and separately approval-gated.

### Phase 9

- Add grouped `/stats kingdom`.
- No new top-level command and no `/me` change.
- Target after resync: `36 top-level / 101 grouped / 8 me / 2 stats / 2 inventory`.
- Private two-page Kingdom Overview and completed-KVK Summary.
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
  report-preserving governor-switch journeys on 2026-07-13. Phase 5B completed its shared
  1400x980 premium renderer refresh without changing this command surface or interaction contract;
  the presentation includes restored item icons, the invoking-player avatar with safe fallback,
  fitted typography, up to six evenly spaced genuine upload dates, and density-aware markers for
  every plotted upload. Operator Discord smoke and final visual acceptance passed on 2026-07-13.
  Phase 5C Accounts completed and passed operator smoke/premium visual acceptance on 2026-07-14;
  it is a user/all-linked-governor summary page and therefore keeps Dashboard return context
  without exposing Change Governor. Phase 5D Reminders completed and passed operator smoke on
  2026-07-15 with a
  standalone 1702x924 card with invoking-user avatar and safe fallback, earned ACTIVE/REVIEW/OFF
  state, approved coverage hero,
  friendly KVK/Calendar summaries, deterministic insight, and unchanged Manage/scheduler behavior.
  It retains the same user-level/no-Change-Governor rule and explicitly closes host-refresh
  attachment streams. Codex Security scan `8fcf96f6-44e0-4d87-8521-7de721444ef7` found no Phase 5D
  security issue. Final operator smoke accepted Manage refresh/reflected updates, graceful timeout,
  avatar, duplicate-safe suffix, navigation, alignment, and dated-footer presentation. Phase 5D.1
  is implemented and locally validated with shared pure KVK/Calendar eligibility, one bulk-loaded
  cross-system projection, deterministic absolute-UTC selection, healthy-empty/unavailable
  distinction, and unchanged `/calendar_next_event`, `/next_kvk_event`, and `/next_kvk_fight`
  registrations. The operator authorised the discovered KVK `now` zero-duration correction so the
  saved At start choice is genuinely live-eligible. Final operator Discord smoke passed on
  2026-07-15, including authoritative NEXT presentation and the bold-gold event-start emphasis;
  the completed Phase 5D.1 task pack and starter are archived.
- GovernorOS v2 Phase 5F supersedes the proposed Premium Inventory Summary Card and Phase 5E's
  Inventory-privacy ownership. It retires `/me inventory`, `/myinventory`, and
  `/inventory_preferences`, and `/export_inventory` as one bot release, reducing the top-level command count from 42 to 39
  and `/me` from 9 to 8 subcommands while `/inventory` remains at 2. Public Inventory posting and
  combined `All` viewing and export routes are removed. The three selected-governor report pages retain
  their private Excel/CSV/Google Sheets exports; `/me exports` is Stats-only.
  The selected-governor dashboard and `/me resources`, `/me speedups`, and `/me materials` remain
  the definitive report UX. Personal Settings is profile-only with derived `LOCAL`/`UTC` context.
  The bot no longer reads or writes Inventory visibility; `dbo.InventoryReportPreference` remains
  untouched for rollback and there is no Phase 5F SQL deployment.
- GovernorOS v2 Phase 5G supersedes the Phase 5F Stats-only export-centre checkpoint. The accepted
  implementation removes `/me exports` and `/my_stats_export`, leaving 38 top-level commands, seven `/me`
  subcommands, and two `/inventory` subcommands. `/me accounts -> Account Summary -> Download data`
  is the single private all-linked personal-data journey. `/my_stats` remains unchanged for Phase 6,
  and selected-governor Resources, Speedups, and Materials retain their report-page exports. Final
  command resync and operator Discord smoke passed on 2026-07-17.
- GovernorOS v2 Phase 6 completed final production Discord smoke and was operator accepted on
  2026-07-18. The maintained current target is 37 top-level, 100 grouped, eight `/me`, and two
  `/inventory` commands. Private-anywhere `/me stats` owns personal Period Performance; top-level
  `/my_stats` is removed without a redirect. `/stats player`, `/player_profile`, `/mykvkcrystaltech`,
  `/kvk history`, Inventory import/audit, selected-governor Inventory report-page exports, and Account
  Summary Download data remain at the current runtime baseline. The approved follow-on roadmap closes
  `/me history`, makes Phase 7 a no-command `/me` visual/content closeout, assigns `/stats player` and
  `/player_profile` consolidation to Phase 8, and adds `/stats kingdom` in Phase 9. SQL PRs #43/#44
  deployed the additive `dbo.usp_GetPersonalStatsDaily` contract before the bot; its header exposes
  latest anchor-date source refresh independently from report generation time.
- GovernorOS v2 Phase 8 completed production smoke and was operator accepted on 2026-07-21. The
  maintained current target is 36 top-level, 100 grouped, eight `/me`, one `/stats`, and two
  `/inventory` commands. `/stats player` is the only private leadership player-review route;
  `/player_profile` is removed without redirect. Mirror PR #230 and production PR #537 carry the
  bot result after SQL-first deployment. Phase 8.1 is a no-command-change visual hierarchy,
  Presence/Last Active, record-readability and evidence-led performance refinement; no resync is
  expected and SQL changes are not pre-approved.
- Player Self-Service Command Centre Phase 13 started legacy redirect planning with audit/scope
  only. The operator-provided SQL extract and dated JSONL files showed nonzero broad usage for
  every audited legacy and related personal path, recent direct usage for several legacy paths, and
  `/me` usage concentrated in the smoke-test/operator window. After reviewing the classifications,
  the operator approved lightweight private redirects for account, reminder, calendar reminder,
  inventory preference, and export legacy entry points. Production PR #486 delivered the redirects
  and operator smoke on 2026-06-27 confirmed all approved redirects were correct. Phase 5F later
  approved retirement of `/myinventory` and `/inventory_preferences`. That historical baseline was
  later superseded: Phase 6 removed `/my_stats` and Phase 8 removed `/player_profile`, both without
  redirects. `/mykvkcrystaltech` and `/stats player` remain live; any other final registration
  removal still requires route-specific briefing, usage evidence and operator approval.
- Remaining redirected legacy player self-service paths stay registered in parallel while their
  `/me` replacements roll out; Phase 5F's two approved Inventory removals are excluded.
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
