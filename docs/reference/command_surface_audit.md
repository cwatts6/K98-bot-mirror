# Command Surface Audit

Last updated: 2026-06-01

## Post-Audit Programme Updates

Command Platform Phase 1, Permission Decorator Standardisation, was completed in PR 131
(`codex/command-platform-phase-1-permission-decorators`), smoke tested successfully, merged, and
pushed to production. Phase 1 did not rename, retire, regroup, or change the count of any slash
commands. It standardised active command permission gates onto decorators and kept the registration
baseline unchanged:

```text
primary=82 grouped_subcommands_detected=22 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=82
```

The next programme slice is Phase 2, Validator And Inventory Tooling Enhancement. It should improve
registration reporting and disabled-secondary classification before further grouping migrations.

## Current Registration Summary

`scripts/validate_command_registration.py` reports:

```text
primary=82 grouped_subcommands_detected=22 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=82
```

Grouped command summary:

| Group | Statically detected subcommands |
|---|---:|
| `/ops` | 14 |
| `/mge` | 6 |
| `/prekvk` | 2 |

The primary command surface now has an 18-command buffer below Discord's 100 top-level
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

## Deferred Follow-Up Batches

Next command-surface batches are staged in `docs/reference/deferred_optimisations.md` and the
command-platform programme docs. Recommended order:

1. Validator and command inventory tooling enhancement.
2. Low-risk Ops consolidation, after validator reporting is clearer.
3. Ark grouping under `/ark`, with operator communication for public paths.
4. Public/player domain grouping across KVK, registry, inventory, calendar, and subscriptions.

Phase 2 retired the unused disabled secondary command declarations in `cogs/commands.py` and
root `subscribe.py`, leaving `commands/` as the only command registration surface and removing the
previous informational duplicate warnings for `/summary`, `/weeksummary`, `/history`,
`/failures`, `/ping`, and `/subscribe`.
