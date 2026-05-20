# Command Surface Audit

Last updated: 2026-05-20

## Delivery Status

Batch 1 is complete, merged, promoted to production, and smoke tested on the bot machine.

Production restart evidence from 2026-05-20 confirmed:

- grouped command signatures are stable across restarts;
- no `SlashCommandGroup` `_callback` signature warnings remain for `/ops`, `/mge`, or `/prekvk`;
- the one-time command cache migration completed and the follow-up restart reported `commands_changed result: False`;
- startup skipped Discord command sync on the settled cache and continued through reminder/event cache rehydration.

## Current Registration Summary

`scripts/validate_command_registration.py` reports:

```text
primary=82 grouped_subcommands_detected=21 secondary_cogs=5 secondary_subscribe=1 total_unique=82
```

Grouped command summary:

| Group | Statically detected subcommands |
|---|---:|
| `/ops` | 14 |
| `/mge` | 6 |
| `/prekvk` | 1 statically detected, plus `/prekvk import_history` attached through the PreKvK admin helper |

The primary command surface now has an 18-command buffer below Discord's 100 top-level
application-command limit. The validator warns at 90+ and fails above 100.

Runtime command-cache and command-version checks flatten grouped commands before reading callback
versions, so moved commands are tracked as paths such as `/ops run_sql_proc`, `/mge refresh_cache`,
and `/prekvk report`.

## Batch 1 Renamed Command Paths

### Operational Admin Commands

| Old path | New path |
|---|---|
| `/run_sql_proc` | `/ops run_sql_proc` |
| `/run_gsheets_export` | `/ops run_gsheets_export` |
| `/restart_bot` | `/ops restart_bot` |
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

Permission decorators and inline admin checks were preserved.

### MGE Commands

| Old path | New path |
|---|---|
| `/mge_leadership_board` | `/mge leadership_board` |
| `/mge_import_results` | `/mge import_results` |
| `/mge_refresh_cache` | `/mge refresh_cache` |
| `/mge_refresh_award_reminders` | `/mge refresh_award_reminders` |
| `/mge_commanders` | `/mge commanders` |
| `/mge_admin_completion` | `/mge admin_completion` |

Permission decorators, MGE leadership channel checks, and admin completion interaction checks were
preserved.

## Deferred Follow-Up Batches

Next command-surface batches are staged in `docs/reference/deferred_optimisations.md`.
Recommended order:

1. Ark grouping under `/ark`, with operator communication for public paths.
2. Public/player domain grouping across KVK, registry, inventory, calendar, and subscriptions.
3. Secondary command surface retirement or clearer validator classification for disabled cogs.
