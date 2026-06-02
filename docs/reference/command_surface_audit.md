# Command Surface Audit

Last updated: 2026-06-01

## Post-Audit Programme Updates

Command Platform Phase 1, Permission Decorator Standardisation, was completed in PR 131
(`codex/command-platform-phase-1-permission-decorators`), smoke tested successfully, merged, and
pushed to production. Phase 1 did not rename, retire, regroup, or change the count of any slash
commands. It standardised active command permission gates onto decorators and kept the registration
baseline unchanged.

Command Platform Phase 2, Validator And Inventory Tooling Enhancement, was completed in PR 132
(`codex/command-platform-phase-2-validator-inventory`), smoke tested successfully, merged, and
pushed to production. Phase 2 retired unused disabled secondary command declarations and made
helper-attached `/prekvk import_history` visible in static grouped-subcommand reporting.

Command Platform Phase 3, Low-Risk Ops Consolidation And Startup Audit Log Alignment, was completed
in PR 133 (`codex/command-platform-phase-3-ops-startup-audit`), smoke tested successfully, merged,
and pushed to production. Phase 3 moved the approved low-risk operational/reporting commands under
`/ops`, fixed the stale startup command-audit summary, and confirmed command-cache validation
remained green after restart.

Command Platform Phase 4, Ark Command Grouping, was completed in PR 134
(`codex/command-platform-phase-4-ark-grouping`), smoke tested successfully, merged, and pushed to
production. Phase 4 moved all 14 Ark commands under `/ark`, including public reminder preferences
and player report commands, while preserving Ark permissions, command options, versions, usage
tracking, response visibility, modal/view flows, and command-cache behavior.

Command Platform Phase 5, Public Domain Grouping Design, was completed in PR 135
(`codex/command-platform-phase-5a-design-docs`), merged, and pushed to production in production PR
444. Phase 5 approved Phase 5A as the next implementation slice for admin/leadership/operator
domain grouping only, and deferred player self-service plus public calendar/KVK calendar redesign
outside this command-count programme.

Command Platform Phase 5A, Admin/Leadership/Operator Domain Grouping, grouped the approved admin,
leadership, and operator paths by domain while preserving player self-service commands and generic
public calendar/KVK calendar commands.

Current baseline after Phase 5A implementation:

```text
primary=39 grouped_subcommands_detected=76 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=39
```

The next command-platform phases are canonical command documentation and future governance/CI
guardrails. Player self-service and generic public calendar/KVK calendar redesign remain deferred
outside this command-count programme.

## Current Registration Summary

`scripts/validate_command_registration.py` reports:

```text
primary=39 grouped_subcommands_detected=76 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=39
```

Grouped command summary:

| Group | Statically detected subcommands |
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

The primary command surface now has a 61-command buffer below Discord's 100 top-level
application-command limit. The validator warns at 90+ and fails above 100.

## Batch 1 Renamed Command Paths

### Operational Admin Commands

| Old path | New path |
|---|---|
| `/run_sql_proc` | `/ops run_sql_proc` |
| `/run_gsheets_export` | `/ops run_gsheets_export` |
| `/restart_bot` | retired in favour of `/ops graceful_restart` |
| n/a | `/ops graceful_restart` |
| `/force_restart` | `/ops force_restart` |
| `/resync_commands` | `/ops resync_commands` |
| `/show_command_versions` | `/ops show_command_versions` |
| `/validate_command_cache` | `/ops validate_command_cache` |
| `/view_restart_log` | `/ops view_restart_log` |
| `/import_proc_config` | `/ops import_proc_config` |
| `/dl_bot_status` | `/ops dl_bot_status` |
| `/logs` | `/ops logs` |
| `/show_logs` | `/ops show_logs` |
| `/last_errors` | `/ops last_errors` |
| `/crash_log` | `/ops crash_log` |
| `/summary` | `/ops summary` |
| `/weeksummary` | `/ops weeksummary` |
| `/history` | `/ops history` |
| `/failures` | `/ops failures` |
| `/usage` | `/ops usage` |
| `/usage_detail` | `/ops usage_detail` |
| `/test_embed` | `/ops test_embed` |

Permission decorators were preserved during Batch 1. Phase 1 later removed redundant inline admin
checks from already-decorated `/ops run_sql_proc`, `/ops run_gsheets_export`, and
`/ops dl_bot_status` without changing these command paths.

### MGE Commands

| Old path | New path |
|---|---|
| `/mge_leadership_board` | `/mge leadership_board` |
| `/mge_import_results` | `/mge import_results` |
| `/mge_refresh_cache` | `/mge refresh_cache` |
| `/mge_refresh_award_reminders` | `/mge refresh_award_reminders` |
| `/mge_commanders` | `/mge commanders` |
| `/mge_admin_completion` | `/mge admin_completion` |

Permission decorators and MGE leadership channel checks were preserved during Batch 1. Phase 1
later moved `/mge admin_completion` access control onto the standard decorator layer without
changing the grouped command path.

### Ark Commands

| Old path | New path |
|---|---|
| `/ark_create_match` | `/ark create_match` |
| `/ark_force_announce` | `/ark force_announce` |
| `/ark_amend_match` | `/ark amend_match` |
| `/ark_cancel_match` | `/ark cancel_match` |
| `/ark_reminder_prefs` | `/ark reminder_prefs` |
| `/ark_set_preference` | `/ark set_preference` |
| `/ark_clear_preference` | `/ark clear_preference` |
| `/ark_ban_add` | `/ark ban_add` |
| `/ark_ban_revoke` | `/ark ban_revoke` |
| `/ark_ban_list` | `/ark ban_list` |
| `/ark_set_result` | `/ark set_result` |
| `/ark_report_players` | `/ark report_players` |
| `/ark_generate_draft` | `/ark generate_draft` |
| `/create_ark_team` | `/ark create_team` |

Phase 4 preserved existing Ark permissions, public/private response visibility, command versions,
usage tracking, options, and modal/view flows while moving all Ark commands into the `/ark` group.

## Deferred Follow-Up Batches

Phase 5A completed the approved admin/leadership/operator domain grouping across registry admin,
KVK/stat admin, inventory import/audit, calendar/event admin refresh/status paths, subscriptions
admin, CrystalTech admin, honor purge, location admin/leadership, and activity leadership
commands.

Remaining command-surface batches are staged in `docs/reference/deferred_optimisations.md` and the
command-platform programme docs. Recommended order:

1. Canonical command documentation after Phase 5A path changes.
2. Future governance and CI guardrails.

The previously considered player self-service grouping is deferred because commands such as
`/register_governor`, `/modify_registration`, `/my_registrations`, `/mygovernorid`,
`/mykvkstats`, `/my_stats`, `/myinventory`, and `/subscribe` likely need workflow redesign rather
than simple path grouping. The public calendar/KVK calendar commands are also deferred because
`/calendar`, `/calendar_next_event`, `/next_kvk_fight`, and `/next_kvk_event` have inconsistent
visibility, naming, scope, and button behavior that should be redesigned together.

Phase 5A implementation note: calendar admin/operator commands moved under existing
`/ops calendar_*` paths, not `/calendar ...`, because `/calendar` remains a flat public command
until the deferred public calendar/KVK calendar redesign.

Phase 2 retired the unused disabled secondary command declarations in `cogs/commands.py` and
root `subscribe.py`, leaving `commands/` as the only command registration surface and removing the
previous informational duplicate warnings for `/summary`, `/weeksummary`, `/history`,
`/failures`, `/ping`, and `/subscribe`.

Phase 3 corrected the stale `DL_bot.py` startup audit count so restart smoke logs use the same
authoritative command inventory semantics as the validator instead of reporting
`primary=0 ... total_unique=0` from the legacy `Commands.py` shim.
