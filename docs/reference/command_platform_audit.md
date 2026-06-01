# Command Platform Audit

Last updated: 2026-06-01

## Programme Status

Phase 1, Permission Decorator Standardisation, was completed in PR 131
(`codex/command-platform-phase-1-permission-decorators`), smoke tested successfully, merged, and
pushed to production. The PR standardised active command permission gates onto decorators without
changing command paths, command grouping, or command registration count.

Phase 2, Validator And Inventory Tooling Enhancement, was completed in PR 132
(`codex/command-platform-phase-2-validator-inventory`), smoke tested successfully, merged, and
pushed to production. The PR retired unused disabled secondary command declarations, made
`/prekvk import_history` visible to static grouped-subcommand reporting, and preserved all active
command paths and the active top-level command count.

Phase 3, Low-Risk Ops Consolidation And Startup Audit Log Alignment, was completed in PR 133
(`codex/command-platform-phase-3-ops-startup-audit`), smoke tested successfully, merged, and pushed
to production. The PR grouped the approved operational/reporting commands under `/ops`, aligned
startup command-audit logging with the authoritative command inventory, and confirmed
`/ops validate_command_cache` remained green after restart.

Phase 4, Ark Command Grouping, was completed in PR 134
(`codex/command-platform-phase-4-ark-grouping`), smoke tested successfully, merged, and pushed to
production. The PR grouped all 14 Ark commands under `/ark`, including public
`/ark reminder_prefs` and `/ark report_players`, preserved existing permissions/options/versions
and Ark modal/view flows, added a post-merge Discord briefing note, and confirmed
`/ops validate_command_cache` remained green after restart.

## Audit Baseline

Static command registration validation after Phase 4 implementation reports:

```text
primary=62 grouped_subcommands_detected=43 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=62
```

Grouped command summary:

| Group | Statically detected subcommands |
|---|---:|
| `/ark` | 14 |
| `/ops` | 21 |
| `/mge` | 6 |
| `/prekvk` | 2 |

The primary command surface has a 38-command buffer below Discord's 100 top-level application
command limit. The validator warns at 90+ and fails above 100.

Usage levels below are based only on local JSONL usage files under `data/command_usage_*.jsonl`
available during the audit. SQL-backed production history may contain broader usage evidence.
Observed local usage only showed Ark reminder preferences activity, with 439 events under the
previous `/ark_reminder_prefs` path. All other
commands are marked `none observed` pending SQL usage review.

## Audit Decisions

- Inline permission checks are non-compliant for command-platform standardisation. Commands marked
  `inline check` must be moved to standard decorators before or during any command-path migration.
- Existing grouped command paths should be preserved unless a later phase explicitly approves a
  second migration.
- Public/player command moves require operator approval and user-facing communication.
- Disabled secondary command surfaces must be retired or classified separately by the validator.
  Phase 2 retired the unused `cogs/commands.py` and root `subscribe.py` legacy declarations after
  confirming they are not loaded by startup.

## Command Inventory

| Category | Current path | Owner module | Permission model | Usage | Registration | Proposed path / disposition |
|---|---|---|---|---:|---|---|
| Activity | `/activity_top` | `commands/activity_cmds.py` | decorator | none observed | top-level | Phase 5A `/activity top` |
| Ark | `/ark create_match` | `commands/ark_cmds.py` | decorator | none observed | grouped | Preserve |
| Ark | `/ark force_announce` | `commands/ark_cmds.py` | decorator | none observed | grouped | Preserve |
| Ark | `/ark amend_match` | `commands/ark_cmds.py` | decorator | none observed | grouped | Preserve |
| Ark | `/ark cancel_match` | `commands/ark_cmds.py` | decorator | none observed | grouped | Preserve |
| Ark | `/ark reminder_prefs` | `commands/ark_cmds.py` | public | high local JSONL | grouped | Preserve |
| Ark | `/ark set_preference` | `commands/ark_cmds.py` | decorator | none observed | grouped | Preserve |
| Ark | `/ark clear_preference` | `commands/ark_cmds.py` | decorator | none observed | grouped | Preserve |
| Ark | `/ark ban_add` | `commands/ark_cmds.py` | decorator | none observed | grouped | Preserve |
| Ark | `/ark ban_revoke` | `commands/ark_cmds.py` | decorator | none observed | grouped | Preserve |
| Ark | `/ark ban_list` | `commands/ark_cmds.py` | decorator | none observed | grouped | Preserve |
| Ark | `/ark set_result` | `commands/ark_cmds.py` | decorator | none observed | grouped | Preserve |
| Ark | `/ark report_players` | `commands/ark_cmds.py` | public | none observed | grouped | Preserve |
| Ark | `/ark generate_draft` | `commands/ark_cmds.py` | decorator | none observed | grouped | Preserve |
| Ark | `/ark create_team` | `commands/ark_cmds.py` | decorator | none observed | grouped | Preserve |
| Calendar | `/calendar` | `commands/calendar_cmds.py` | public | none observed | top-level | Defer calendar/KVK calendar UX redesign |
| Calendar | `/calendar_next_event` | `commands/calendar_cmds.py` | public | none observed | top-level | Defer calendar/KVK calendar UX redesign |
| Calendar | `/calendar_reminder_config` | `commands/calendar_cmds.py` | public | none observed | top-level | Defer player self-service workflow redesign |
| Calendar Ops | `/calendar_refresh` | `commands/admin_cmds.py` | decorator | none observed | top-level | Phase 5A `/calendar refresh` |
| Calendar Ops | `/calendar_generate` | `commands/admin_cmds.py` | decorator | none observed | top-level | Phase 5A `/calendar generate` |
| Calendar Ops | `/calendar_publish_cache` | `commands/admin_cmds.py` | decorator | none observed | top-level | Phase 5A `/calendar publish_cache` |
| Calendar Ops | `/calendar_status` | `commands/admin_cmds.py` | decorator | none observed | top-level | Phase 5A `/calendar status` |
| CrystalTech Ops | `/crystaltech_validate` | `commands/admin_cmds.py` | decorator | none observed | top-level | Phase 5A `/crystaltech validate` |
| CrystalTech Ops | `/crystaltech_reload` | `commands/admin_cmds.py` | decorator | none observed | top-level | Phase 5A `/crystaltech reload` |
| CrystalTech Ops | `/crystaltech_admin_reset` | `commands/admin_cmds.py` | decorator | none observed | top-level | Phase 5A `/crystaltech admin_reset` |
| Events | `/next_kvk_fight` | `commands/events_cmds.py` | public | none observed | top-level | Defer calendar/KVK calendar UX redesign |
| Events | `/next_kvk_event` | `commands/events_cmds.py` | public | none observed | top-level | Defer calendar/KVK calendar UX redesign |
| Events | `/refresh_events` | `commands/events_cmds.py` | decorator | none observed | top-level | Phase 5A `/events refresh` |
| Events | `/refresh_kvk_overview` | `commands/events_cmds.py` | decorator | none observed | top-level | Phase 5A `/events refresh_kvk_overview` |
| Honor/KVK | `/honor_rankings` | `commands/stats_cmds.py` | decorator | none observed | top-level | Defer; public/channel-limited ranking UX |
| Honor/KVK | `/honor_purge_last` | `commands/stats_cmds.py` | decorator | none observed | top-level | Phase 5A `/honor purge_last` |
| Inventory | `/import_inventory` | `commands/inventory_cmds.py` | decorator | none observed | top-level | Phase 5A `/inventory import` |
| Inventory | `/myinventory` | `commands/inventory_cmds.py` | public | none observed | top-level | Defer player self-service workflow redesign |
| Inventory | `/inventory_preferences` | `commands/inventory_cmds.py` | public | none observed | top-level | Defer player self-service workflow redesign |
| Inventory | `/export_inventory` | `commands/inventory_cmds.py` | service authorization context | none observed | top-level | Defer player self-service workflow redesign |
| Inventory | `/inventory_import_audit` | `commands/inventory_cmds.py` | decorator | none observed | top-level | Phase 5A `/inventory audit` |
| Location | `/import_locations` | `commands/location_cmds.py` | decorator | none observed | top-level | Phase 5A `/location import` |
| Location | `/player_location` | `commands/location_cmds.py` | admin/leadership allowed channels | none observed | top-level | Phase 5A `/location player` |
| MGE | `/mge leadership_board` | `commands/mge_cmds.py` | decorator | none observed | grouped | Preserve |
| MGE | `/mge import_results` | `commands/mge_cmds.py` | decorator | none observed | grouped | Preserve |
| MGE | `/mge refresh_cache` | `commands/mge_cmds.py` | decorator | none observed | grouped | Preserve |
| MGE | `/mge refresh_award_reminders` | `commands/mge_cmds.py` | decorator | none observed | grouped | Preserve |
| MGE | `/mge commanders` | `commands/mge_cmds.py` | decorator | none observed | grouped | Preserve |
| MGE | `/mge admin_completion` | `commands/mge_cmds.py` | decorator | none observed | grouped | Preserve |
| Ops | `/ops run_sql_proc` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Ops | `/ops run_gsheets_export` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Ops | `/ops graceful_restart` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Ops | `/ops force_restart` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Ops | `/ops resync_commands` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Ops | `/ops show_command_versions` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Ops | `/ops validate_command_cache` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Ops | `/ops view_restart_log` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Ops | `/ops import_proc_config` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Ops | `/ops dl_bot_status` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Ops | `/ops logs` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Ops | `/ops show_logs` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Ops | `/ops last_errors` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Ops | `/ops crash_log` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Player/KVK | `/mykvktargets` | `commands/telemetry_cmds.py` | decorator | none observed | top-level | Defer player self-service workflow redesign |
| Player/KVK | `/mygovernorid` | `commands/telemetry_cmds.py` | public | none observed | top-level | Defer player self-service workflow redesign |
| Player/KVK | `/player_profile` | `commands/telemetry_cmds.py` | decorator | none observed | top-level | Defer profile workflow review |
| Player/KVK | `/mykvkcrystaltech` | `commands/telemetry_cmds.py` | decorator | none observed | top-level | Defer player self-service workflow redesign |
| PreKvK | `/prekvk report` | `commands/prekvk_cmds.py` | public | none observed | grouped | Preserve |
| PreKvK Admin | `/prekvk import_history` | `commands/prekvk_admin_cmds.py` | decorator | none observed | grouped by helper | Preserve; improve static validator detection |
| Processing Reports | `/ops summary` | `commands/admin_cmds.py` | public | none observed | grouped | Preserve |
| Processing Reports | `/ops weeksummary` | `commands/admin_cmds.py` | public | none observed | grouped | Preserve |
| Processing Reports | `/ops history` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Processing Reports | `/ops failures` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Registry | `/register_governor` | `commands/registry_cmds.py` | public | none observed | top-level | Defer player self-service workflow redesign |
| Registry | `/modify_registration` | `commands/registry_cmds.py` | public | none observed | top-level | Defer player self-service workflow redesign |
| Registry | `/remove_registration` | `commands/registry_cmds.py` | decorator | none observed | top-level | Phase 5A `/registry remove` |
| Registry | `/remove_registration_by_id` | `commands/registry_cmds.py` | decorator | none observed | top-level | Phase 5A `/registry remove_by_id` |
| Registry | `/my_registrations` | `commands/registry_cmds.py` | public | none observed | top-level | Defer player self-service workflow redesign |
| Registry | `/admin_register_governor` | `commands/registry_cmds.py` | decorator | none observed | top-level | Phase 5A `/registry admin_register` |
| Registry | `/registration_audit` | `commands/registry_cmds.py` | decorator | none observed | top-level | Phase 5A `/registry audit` |
| Registry | `/bulk_export_registrations` | `commands/registry_cmds.py` | decorator | none observed | top-level | Phase 5A `/registry bulk_export` |
| Registry | `/bulk_import_registrations_dryrun` | `commands/registry_cmds.py` | decorator | none observed | top-level | Phase 5A `/registry bulk_import_dryrun` |
| Registry | `/bulk_import_registrations` | `commands/registry_cmds.py` | decorator | none observed | top-level | Phase 5A `/registry bulk_import` |
| Stats Ops | `/ops test_embed` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Stats/KVK | `/test_kvk_export` | `commands/stats_cmds.py` | decorator | none observed | top-level | Phase 5A `/kvk test_export` |
| Stats/KVK | `/mykvkstats` | `commands/stats_cmds.py` | decorator | none observed | top-level | Defer player self-service workflow redesign |
| Stats/KVK | `/refresh_stats_cache` | `commands/stats_cmds.py` | decorator | none observed | top-level | Phase 5A `/kvk refresh_stats_cache` |
| Stats/KVK | `/my_stats` | `commands/stats_cmds.py` | decorator | none observed | top-level | Defer player self-service workflow redesign |
| Stats/KVK | `/my_stats_export` | `commands/stats_cmds.py` | public | none observed | top-level | Defer player self-service workflow redesign |
| Stats/KVK | `/player_stats` | `commands/stats_cmds.py` | admin/leadership | none observed | top-level | Phase 5A `/stats player` |
| Stats/KVK | `/mykvkhistory` | `commands/stats_cmds.py` | decorator | none observed | top-level | Defer player self-service workflow redesign |
| Stats/KVK | `/kvk_rankings` | `commands/stats_cmds.py` | decorator | none observed | top-level | Defer; public/channel-limited ranking UX |
| Stats/KVK | `/kvk_export_all` | `commands/stats_cmds.py` | decorator | none observed | top-level | Phase 5A `/kvk export_all` |
| Stats/KVK | `/kvk_recompute` | `commands/stats_cmds.py` | decorator | none observed | top-level | Phase 5A `/kvk recompute` |
| Stats/KVK | `/kvk_list_scans` | `commands/stats_cmds.py` | decorator | none observed | top-level | Phase 5A `/kvk list_scans` |
| Stats/KVK | `/test_kvk_embed` | `commands/stats_cmds.py` | decorator | none observed | top-level | Phase 5A `/kvk test_embed` |
| Stats/KVK | `/kvk_window_preview` | `commands/stats_cmds.py` | decorator | none observed | top-level | Phase 5A `/kvk window_preview` |
| Subscriptions | `/subscribe` | `commands/subscriptions_cmds.py` | public | none observed | top-level | Defer player self-service workflow redesign |
| Subscriptions | `/modify_subscription` | `commands/subscriptions_cmds.py` | public | none observed | top-level | Defer player self-service workflow redesign |
| Subscriptions | `/unsubscribe` | `commands/subscriptions_cmds.py` | public | none observed | top-level | Defer player self-service workflow redesign |
| Subscriptions | `/list_subscribers` | `commands/subscriptions_cmds.py` | decorator | none observed | top-level | Phase 5A `/subscriptions list` |
| Subscriptions | `/migrate_subscriptions_dryrun` | `commands/subscriptions_cmds.py` | decorator | none observed | top-level | Phase 5A `/subscriptions migrate_dryrun` |
| Subscriptions | `/migrate_subscriptions_apply` | `commands/subscriptions_cmds.py` | decorator | none observed | top-level | Phase 5A `/subscriptions migrate_apply` |
| Telemetry | `/ping` | `commands/telemetry_cmds.py` | public | none observed | top-level | Keep flat or move to `/ops ping` |
| Usage Analytics | `/ops usage` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |
| Usage Analytics | `/ops usage_detail` | `commands/admin_cmds.py` | decorator | none observed | grouped | Preserve |

## Domain Review Summary

| Domain | Strengths | Weaknesses / risks | Improvement opportunity |
|---|---|---|---|
| Ark | Strong service/DAL/test ecosystem and consistent leadership decorators on most admin paths. Phase 4 grouped all Ark commands under `/ark`. | Create/amend/cancel command bodies still contain substantial orchestration that should move into services later. | Follow up with an Ark command orchestration extraction batch. |
| Ops | Core operational tools are grouped and command lifecycle reuse is strong. Phase 3 moved approved reporting, usage, and test ops paths under `/ops`. | Calendar, CrystalTech, registry admin, KVK admin, location, activity, and subscription admin commands remain flat. | Execute approved Phase 5A admin/leadership/operator domain grouping. |
| MGE | Already grouped; permission decorators mostly consistent. | `/mge admin_completion` uses an inline admin check. | Standardise decorator and preserve current grouped path. |
| Public KVK/Stats | Rich test coverage and recent service/DAL cleanup around KVK admin commands. | Personal player paths are flat and likely high-traffic; some current commands may reflect development slices rather than ideal user journeys. | Move only admin/leadership KVK/stat commands in Phase 5A; defer personal player workflow redesign. |
| Registry | Strong service/cache tests and command service extraction. | Public self-service paths are discoverability-sensitive and may be better redesigned around a coherent Governor ID/account workflow. | Group admin registry commands in Phase 5A; defer public account workflow redesign. |
| Inventory | Service-oriented implementation and focused inventory tests. Phase 1 standardised command access checks onto decorators. | Inventory export still passes admin context to the service for self-service/admin override semantics; personal commands are high-discoverability. | Move import/audit only in Phase 5A; defer personal inventory workflow redesign. |
| Calendar / Events | Calendar command layer is thin and docs are extensive. | Public calendar/KVK calendar commands have inconsistent naming, visibility, scope, and button behavior. | Move admin refresh/status commands in Phase 5A; defer public calendar/KVK calendar UX redesign. |
| Subscriptions | Public flow is simple and tested via views. | Public subscription commands are player self-service paths that need communication and may benefit from flow redesign. | Move admin list/migration commands in Phase 5A; defer subscription self-service redesign. |
| Secondary cogs | Phase 2 retired unused disabled legacy declarations. | No active secondary command surface remains. | Keep validator tolerant of missing retired paths and focused on active startup-sync risks. |

## Technical Debt Register

### Phase 1 Completed Item
- Area: `commands/admin_cmds.py`, `commands/inventory_cmds.py`, `commands/location_cmds.py`, `commands/mge_cmds.py`, `commands/stats_cmds.py`, `commands/telemetry_cmds.py`, `decoraters.py`
- Type: consistency
- Description: Phase 1 moved active command access control for the reviewed inline admin/channel/leadership checks onto standard decorators and removed redundant inline admin gates from already-decorated commands.
- Resolution: Added reusable decorator support for admin-only, admin-or-leadership in allowed channels, and missing-config channel denial. Preserved command paths, command count, service handoff behavior, and denial visibility. `/export_inventory` remains service-authorized because it is self-service with admin override context rather than a command-denial gate.
- Validation: Command registration remained `primary=82 grouped_subcommands_detected=21 secondary_cogs=5 secondary_subscribe=1 total_unique=82`; full pytest, pre-commit, log-noise validation, and Codex Security diff review passed.

### Phase 4 Completed Item
- Area: `commands/ark_cmds.py`, `docs/ark/`, Ark command tests
- Type: architecture
- Description: Phase 4 grouped all Ark commands under `/ark`, including public reminder
  preferences and player report commands, while preserving existing behavior, permissions, command
  options, versions, usage tracking, response visibility, modal/view flows, and command-cache
  semantics.
- Resolution: Delivered in PR 134
  (`codex/command-platform-phase-4-ark-grouping`), smoke tested successfully, merged, and pushed to
  production.
- Validation: Production smoke confirmed `/ops validate_command_cache` green and the active
  baseline at
  `primary=62 grouped_subcommands_detected=43 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=62`.

### Phase 2 Completed Item
- Area: `scripts/validate_command_registration.py`, `cogs/commands.py`, `subscribe.py`
- Type: cleanup
- Description: Phase 2 retired unused disabled secondary command declarations and updated
  validator reporting so duplicates are classified as active startup-sync risks versus disabled
  legacy declarations when retained in test fixtures.
- Resolution: Removed the legacy `cogs/commands.py` and root `subscribe.py` files after confirming
  startup uses `Commands.register_commands(bot)` as the authoritative path and does not load these
  cogs. The validator now reports no retained disabled legacy command surfaces. PR 132 was smoke
  tested with a graceful restart and `/ops validate_command_cache`, merged, and pushed to
  production.

### Deferred Optimisation
- Area: `commands/`, command documentation
- Type: consistency
- Description: Permission model and command-path documentation are not consistently discoverable across domains.
- Suggested Fix: Promote this inventory into a canonical command reference with path, owner, permissions, usage, migration status, and operator-facing notes.
- Impact: high
- Risk: low
- Dependencies: Complete SQL-backed usage review or explicitly accept local JSONL-only usage evidence.

## Phased Roadmap

### Phase 1 - Permission Decorator Standardisation

Status: complete. Delivered in PR 131, smoke tested successfully, merged, and pushed to production.

Goal: remove inline permission checks from command handlers and move command access control onto
standard decorators.

Scope:

- `commands/admin_cmds.py`: `/history`, `/failures`
- `commands/inventory_cmds.py`: `/import_inventory`, `/export_inventory`,
  `/inventory_import_audit`
- `commands/location_cmds.py`: `/player_location`
- `commands/mge_cmds.py`: `/mge admin_completion`
- `commands/stats_cmds.py`: redundant inline admin gate in `/test_kvk_export`
- `commands/telemetry_cmds.py`: `/player_profile`
- Redundant inline admin gates in already-decorated `/ops run_sql_proc`,
  `/ops run_gsheets_export`, and `/ops dl_bot_status`

Implementation notes:

- Prefer existing decorators: `is_admin_and_notify_channel`, `is_admin_or_leadership_only`,
  `is_admin_or_leadership`, and `channel_only`.
- Add a new standard decorator only if an existing rule cannot represent the current behavior,
  especially for self-service commands with admin override or channel-specific public access.
- Preserve current ephemeral/public responses.
- Do not group or rename commands in this phase.

Validation:

- Focused permission tests for every command whose inline check is removed.
- Existing command registration smoke tests.
- `python scripts/validate_command_registration.py`
- `python scripts/smoke_imports.py`
- Codex Security review required before PR because this phase touches permission boundaries and
  Discord interactions.

Delivered validation:

- Command registration remained
  `primary=82 grouped_subcommands_detected=21 secondary_cogs=5 secondary_subscribe=1 total_unique=82`.
- Focused command permission decorator tests passed.
- Full pytest, pre-commit, smoke imports, architecture validation, deferred-item validation,
  command registration validation, pytest log-noise analysis, and Codex Security diff review
  passed before merge.
- Production smoke testing completed successfully after merge/promotion.

### Phase 2 - Validator And Inventory Tooling Enhancement

Status: complete. Delivered in PR 132, smoke tested successfully, merged, and pushed to production.

Goal: improve command-platform reporting before large migrations.

Scope:

- `scripts/validate_command_registration.py`
- `commands/command_inventory.py`
- tests around command inventory, grouped command flattening, warning thresholds, and duplicate
  classification

Implementation notes:

- Distinguish active authoritative command paths from disabled secondary cogs.
- Retire confirmed-unused disabled secondary declarations.
- Detect helper-attached grouped subcommands such as `/prekvk import_history`.
- Report command owner module, group/subcommand path, duplicate source, and near-limit risk.
- Keep the existing hard fail above 100 top-level commands and warning at 90+.

Validation:

- `tests/test_validate_command_registration.py`
- `tests/test_command_inventory.py`
- `tests/test_command_lifecycle.py`
- `tests/test_command_registration_smoke.py`
- `python scripts/validate_command_registration.py`

Delivered validation:

- Command registration now reports
  `primary=82 grouped_subcommands_detected=22 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=82`.
- Focused validator, inventory, lifecycle, and registration smoke tests passed.
- Full pytest, pre-commit, smoke imports, architecture validation, deferred-item validation,
  command registration validation, and pytest log-noise analysis passed before merge.
- Production smoke testing completed via graceful restart and `/ops validate_command_cache`.

### Phase 3 - Low-Risk Ops Consolidation And Startup Audit Log Alignment

Status: complete. Delivered in PR 133, smoke tested successfully, merged, and pushed to production.

Goal: recover command headroom with low public-UX risk after permissions are standardised.

Delivered scope:

- Moved `/summary`, `/weeksummary`, `/history`, `/failures` under `/ops`.
- Moved `/usage` and `/usage_detail` under `/ops`.
- Moved `/test_embed` under `/ops`.
- Kept `/ping` flat for health/debug discoverability.
- Fixed stale `DL_bot.py` startup command audit logging so startup smoke logs do not show
  `primary=0 ... total_unique=0` when the authoritative validator reports the real active command
  inventory.

Implementation notes:

- Preserve existing command behavior, output, and usage tracking.
- Update docs that mention the old paths.
- Public visibility of `/summary` and `/weeksummary` was explicitly approved for grouping and
  preserved at `/ops summary` and `/ops weeksummary`.
- Complete startup audit log alignment before or alongside command grouping so Phase 3 smoke logs
  can be trusted.

Validation:

- Command registration smoke tests.
- Focused tests for migrated handlers.
- Command cache/version tests where grouped names affect signatures.
- Startup log smoke for corrected command audit summary or explicit removal of stale counts.
- Expected validator baseline after Phase 3:
  `primary=75 grouped_subcommands_detected=29 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=75`.

Delivered validation:

- Startup smoke confirmed the authoritative command-audit line reports
  `primary=75 grouped_subcommands_detected=29 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=75`.
- Startup smoke no longer showed the stale `primary=0 ... total_unique=0` summary.
- `/ops validate_command_cache` reported all commands correctly versioned and cached.
- Manual smoke confirmed the moved commands executed correctly after production promotion.

### Phase 4 - Ark Command Grouping

Status: complete. Delivered in PR 134, smoke tested successfully, merged, and pushed to
production.

Goal: group Ark commands under `/ark`, recovering the largest remaining top-level block.

Delivered scope:

- Leadership/admin paths: `create_match`, `force_announce`, `amend_match`, `cancel_match`,
  `set_preference`, `clear_preference`, `ban_add`, `ban_revoke`, `ban_list`, `set_result`,
  `generate_draft`, `create_team`
- Public paths: `reminder_prefs`, `report_players`

Implementation notes:

- Public Ark path migration was approved because Ark is fortnightly and the public commands were
  not currently in active use; a post-merge Discord briefing note was added at
  `docs/ark/ark_command_grouping_discord_briefing.md`.
- Preserved `is_admin_or_leadership_only`, `channel_only`, autocomplete/options, modal/view flows,
  and interaction response behavior.
- Updated Ark docs and smoke-test runbooks that referenced flat paths.
- Follow up separately on extracting substantial create/amend/cancel orchestration out of
  `commands/ark_cmds.py` into Ark services.

Delivered validation:

- Ark command tests, including reminder prefs and force announce.
- Ark registration, draft, ban, cancel, and result focused tests where touched.
- Command registration validation and smoke imports.
- Full pytest, pre-commit, architecture validation, deferred-item validation, command registration
  validation, pytest log-noise analysis, and Codex Security diff review passed before merge.
- Production smoke confirmed `/ops validate_command_cache` green after restart.

### Phase 5 - Public Domain Grouping Design / Phase 5A Admin Grouping

Status: design approved for Phase 5A only. See
`docs/task_packs/Codex Task Pack - Command Platform Phase 5 Public Domain Grouping Design.md`.

Goal: implement only the approved admin/leadership/operator grouping slice and defer player
self-service plus public calendar/KVK calendar redesign out of this command-count programme.

Approved Phase 5A scope:

- `/registry`: remove, remove_by_id, admin_register, audit, bulk_export, bulk_import_dryrun,
  bulk_import
- `/kvk`: test_export, refresh_stats_cache, export_all, recompute, list_scans, test_embed,
  window_preview
- `/stats`: player
- `/inventory`: import, audit
- `/calendar`: refresh, generate, publish_cache, status
- `/events`: refresh, refresh_kvk_overview
- `/subscriptions`: list, migrate_dryrun, migrate_apply
- `/crystaltech`: validate, reload, admin_reset
- `/honor`: purge_last
- `/location`: import, player
- `/activity`: top

Implementation notes:

- Preserve behavior, permissions, options, autocomplete, versions, usage tracking, response
  visibility, command-cache behavior, and handler bodies.
- `/player_location` and `/player_stats` are included because they are admin/leadership lookup
  commands, not player self-service commands.
- Leave player self-service commands flat in Phase 5A; capture them as a separate workflow
  redesign deferred optimisation.
- Leave generic public calendar/KVK calendar commands flat in Phase 5A; capture them as a
  separate calendar UX redesign deferred optimisation.

Validation:

- Domain-focused command tests.
- Permission boundary tests for admin/public split.
- Docs update review for every renamed path.

### Phase 6 - Canonical Command Documentation

Goal: make command ownership, permissions, and path status discoverable.

Scope:

- Promote this audit into a maintained command reference.
- Update stale Ark, calendar, inventory, registry, and KVK docs after approved path changes.
- Add guidance for new commands: group-first design, permission decorator choice, test minimums,
  and command-count impact.

Validation:

- Documentation review.
- `python scripts/validate_deferred_items.py`
- `python scripts/select_tests.py`

### Phase 7 - Future Governance And CI Guardrails

Goal: prevent command-limit drift after the programme ends.

Scope:

- CI enforcement around validator output.
- Optional richer command inventory artifact from validation.
- Command design checklist for task packs.
- Near-limit risk reporting and domain owner summaries.

Validation:

- Validator tests.
- CI/pre-commit integration checks where applicable.

## Recommended Execution Order

1. Phase 1: Permission Decorator Standardisation.
2. Phase 2: Validator And Inventory Tooling Enhancement.
3. Phase 3: Low-Risk Ops Consolidation And Startup Audit Log Alignment.
4. Phase 4: Ark Command Grouping.
5. Phase 5A: Admin/Leadership/Operator Domain Grouping.
6. Phase 6: Canonical Command Documentation.
7. Phase 7: Future Governance And CI Guardrails.

The next implementation PR should be Phase 5A only. Player self-service workflow redesign and
public calendar/KVK calendar redesign are deferred into separate optimisation tasks rather than
continued as simple command grouping inside this programme.
