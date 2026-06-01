# Command Platform Audit

Last updated: 2026-06-01

## Audit Baseline

Static command registration validation currently reports:

```text
primary=82 grouped_subcommands_detected=21 secondary_cogs=5 secondary_subscribe=1 total_unique=82
```

Grouped command summary:

| Group | Statically detected subcommands |
|---|---:|
| `/ops` | 14 |
| `/mge` | 6 |
| `/prekvk` | 1 |

The primary command surface has an 18-command buffer below Discord's 100 top-level application
command limit. The validator warns at 90+ and fails above 100.

Usage levels below are based only on local JSONL usage files under `data/command_usage_*.jsonl`
available during the audit. SQL-backed production history may contain broader usage evidence.
Observed local usage only showed `/ark_reminder_prefs` activity, with 439 events. All other
commands are marked `none observed` pending SQL usage review.

## Audit Decisions

- Inline permission checks are non-compliant for command-platform standardisation. Commands marked
  `inline check` must be moved to standard decorators before or during any command-path migration.
- Existing grouped command paths should be preserved unless a later phase explicitly approves a
  second migration.
- Public/player command moves require operator approval and user-facing communication.
- Disabled secondary command surfaces must be retired or classified separately by the validator.

## Command Inventory

| Category | Current path | Owner module | Permission model | Usage | Registration | Proposed path / disposition |
|---|---|---|---|---:|---|---|
| Activity | `/activity_top` | `commands/activity_cmds.py` | decorator | none observed | top-level | Candidate `/activity top` |
| Ark | `/ark_create_match` | `commands/ark_cmds.py` | decorator | none observed | top-level | Candidate `/ark create_match` |
| Ark | `/ark_force_announce` | `commands/ark_cmds.py` | decorator | none observed | top-level | Candidate `/ark force_announce` |
| Ark | `/ark_amend_match` | `commands/ark_cmds.py` | decorator | none observed | top-level | Candidate `/ark amend_match` |
| Ark | `/ark_cancel_match` | `commands/ark_cmds.py` | decorator | none observed | top-level | Candidate `/ark cancel_match` |
| Ark | `/ark_reminder_prefs` | `commands/ark_cmds.py` | public | high local JSONL | top-level | Candidate `/ark reminder_prefs`; public migration needs approval |
| Ark | `/ark_set_preference` | `commands/ark_cmds.py` | decorator | none observed | top-level | Candidate `/ark set_preference` |
| Ark | `/ark_clear_preference` | `commands/ark_cmds.py` | decorator | none observed | top-level | Candidate `/ark clear_preference` |
| Ark | `/ark_ban_add` | `commands/ark_cmds.py` | decorator | none observed | top-level | Candidate `/ark ban_add` |
| Ark | `/ark_ban_revoke` | `commands/ark_cmds.py` | decorator | none observed | top-level | Candidate `/ark ban_revoke` |
| Ark | `/ark_ban_list` | `commands/ark_cmds.py` | decorator | none observed | top-level | Candidate `/ark ban_list` |
| Ark | `/ark_set_result` | `commands/ark_cmds.py` | decorator | none observed | top-level | Candidate `/ark set_result` |
| Ark | `/ark_report_players` | `commands/ark_cmds.py` | public | none observed | top-level | Candidate `/ark report_players`; public migration needs approval |
| Ark | `/ark_generate_draft` | `commands/ark_cmds.py` | decorator | none observed | top-level | Candidate `/ark generate_draft` |
| Ark | `/create_ark_team` | `commands/ark_cmds.py` | decorator | none observed | top-level | Candidate `/ark create_team` |
| Calendar | `/calendar` | `commands/calendar_cmds.py` | public | none observed | top-level | Keep or candidate `/calendar browse` after UX approval |
| Calendar | `/calendar_next_event` | `commands/calendar_cmds.py` | public | none observed | top-level | Candidate `/calendar next_event` |
| Calendar | `/calendar_reminder_config` | `commands/calendar_cmds.py` | public | none observed | top-level | Candidate `/calendar reminder_config` |
| Calendar Ops | `/calendar_refresh` | `commands/admin_cmds.py` | decorator | none observed | top-level | Candidate `/calendar refresh` |
| Calendar Ops | `/calendar_generate` | `commands/admin_cmds.py` | decorator | none observed | top-level | Candidate `/calendar generate` |
| Calendar Ops | `/calendar_publish_cache` | `commands/admin_cmds.py` | decorator | none observed | top-level | Candidate `/calendar publish_cache` |
| Calendar Ops | `/calendar_status` | `commands/admin_cmds.py` | decorator | none observed | top-level | Candidate `/calendar status` |
| CrystalTech Ops | `/crystaltech_validate` | `commands/admin_cmds.py` | decorator | none observed | top-level | Candidate `/crystaltech validate` |
| CrystalTech Ops | `/crystaltech_reload` | `commands/admin_cmds.py` | decorator | none observed | top-level | Candidate `/crystaltech reload` |
| CrystalTech Ops | `/crystaltech_admin_reset` | `commands/admin_cmds.py` | decorator | none observed | top-level | Candidate `/crystaltech admin_reset` |
| Events | `/next_kvk_fight` | `commands/events_cmds.py` | public | none observed | top-level | Candidate `/events next_fight` |
| Events | `/next_kvk_event` | `commands/events_cmds.py` | public | none observed | top-level | Candidate `/events next_event` |
| Events | `/refresh_events` | `commands/events_cmds.py` | decorator | none observed | top-level | Candidate `/events refresh` |
| Events | `/refresh_kvk_overview` | `commands/events_cmds.py` | decorator | none observed | top-level | Candidate `/events refresh_kvk_overview` |
| Honor/KVK | `/honor_rankings` | `commands/stats_cmds.py` | decorator | none observed | top-level | Candidate `/honor rankings` |
| Honor/KVK | `/honor_purge_last` | `commands/stats_cmds.py` | decorator | none observed | top-level | Candidate `/honor purge_last` |
| Inventory | `/import_inventory` | `commands/inventory_cmds.py` | decorator | none observed | top-level | Candidate `/inventory import` |
| Inventory | `/myinventory` | `commands/inventory_cmds.py` | public | none observed | top-level | Candidate `/inventory report` |
| Inventory | `/inventory_preferences` | `commands/inventory_cmds.py` | public | none observed | top-level | Candidate `/inventory preferences` |
| Inventory | `/export_inventory` | `commands/inventory_cmds.py` | service authorization context | none observed | top-level | Candidate `/inventory export` |
| Inventory | `/inventory_import_audit` | `commands/inventory_cmds.py` | decorator | none observed | top-level | Candidate `/inventory audit` |
| Location | `/import_locations` | `commands/location_cmds.py` | decorator | none observed | top-level | Candidate `/location import` |
| Location | `/player_location` | `commands/location_cmds.py` | decorator | none observed | top-level | Candidate `/location player` |
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
| Player/KVK | `/mykvktargets` | `commands/telemetry_cmds.py` | decorator | none observed | top-level | Candidate `/kvk targets` |
| Player/KVK | `/mygovernorid` | `commands/telemetry_cmds.py` | public | none observed | top-level | Candidate `/registry lookup` or keep flat |
| Player/KVK | `/player_profile` | `commands/telemetry_cmds.py` | decorator | none observed | top-level | Candidate `/profile player` |
| Player/KVK | `/mykvkcrystaltech` | `commands/telemetry_cmds.py` | decorator | none observed | top-level | Candidate `/crystaltech progress` |
| PreKvK | `/prekvk report` | `commands/prekvk_cmds.py` | public | none observed | grouped | Preserve |
| PreKvK Admin | `/prekvk import_history` | `commands/prekvk_admin_cmds.py` | decorator | none observed | grouped by helper | Preserve; improve static validator detection |
| Processing Reports | `/summary` | `commands/admin_cmds.py` | public | none observed | top-level | Candidate `/ops summary`; confirm public/admin intent |
| Processing Reports | `/weeksummary` | `commands/admin_cmds.py` | public | none observed | top-level | Candidate `/ops weeksummary`; confirm public/admin intent |
| Processing Reports | `/history` | `commands/admin_cmds.py` | decorator | none observed | top-level | Candidate `/ops history` |
| Processing Reports | `/failures` | `commands/admin_cmds.py` | decorator | none observed | top-level | Candidate `/ops failures` |
| Registry | `/register_governor` | `commands/registry_cmds.py` | public | none observed | top-level | Candidate `/registry register` or keep flat |
| Registry | `/modify_registration` | `commands/registry_cmds.py` | public | none observed | top-level | Candidate `/registry modify` or keep flat |
| Registry | `/remove_registration` | `commands/registry_cmds.py` | decorator | none observed | top-level | Candidate `/registry remove` |
| Registry | `/remove_registration_by_id` | `commands/registry_cmds.py` | decorator | none observed | top-level | Candidate `/registry remove_by_id` |
| Registry | `/my_registrations` | `commands/registry_cmds.py` | public | none observed | top-level | Candidate `/registry mine` or keep flat |
| Registry | `/admin_register_governor` | `commands/registry_cmds.py` | decorator | none observed | top-level | Candidate `/registry admin_register` |
| Registry | `/registration_audit` | `commands/registry_cmds.py` | decorator | none observed | top-level | Candidate `/registry audit` |
| Registry | `/bulk_export_registrations` | `commands/registry_cmds.py` | decorator | none observed | top-level | Candidate `/registry bulk_export` |
| Registry | `/bulk_import_registrations_dryrun` | `commands/registry_cmds.py` | decorator | none observed | top-level | Candidate `/registry bulk_import_dryrun` |
| Registry | `/bulk_import_registrations` | `commands/registry_cmds.py` | decorator | none observed | top-level | Candidate `/registry bulk_import` |
| Stats Ops | `/test_embed` | `commands/admin_cmds.py` | decorator | none observed | top-level | Candidate `/ops test_embed` |
| Stats/KVK | `/test_kvk_export` | `commands/stats_cmds.py` | decorator | none observed | top-level | Candidate `/kvk test_export` |
| Stats/KVK | `/mykvkstats` | `commands/stats_cmds.py` | decorator | none observed | top-level | Candidate `/kvk stats` or keep flat |
| Stats/KVK | `/refresh_stats_cache` | `commands/stats_cmds.py` | decorator | none observed | top-level | Candidate `/kvk refresh_stats_cache` |
| Stats/KVK | `/my_stats` | `commands/stats_cmds.py` | decorator | none observed | top-level | Candidate `/stats mine` or keep flat |
| Stats/KVK | `/my_stats_export` | `commands/stats_cmds.py` | public | none observed | top-level | Candidate `/stats export` or keep flat |
| Stats/KVK | `/player_stats` | `commands/stats_cmds.py` | decorator | none observed | top-level | Candidate `/stats player` |
| Stats/KVK | `/mykvkhistory` | `commands/stats_cmds.py` | decorator | none observed | top-level | Candidate `/kvk history` or keep flat |
| Stats/KVK | `/kvk_rankings` | `commands/stats_cmds.py` | decorator | none observed | top-level | Candidate `/kvk rankings` |
| Stats/KVK | `/kvk_export_all` | `commands/stats_cmds.py` | decorator | none observed | top-level | Candidate `/kvk export_all` |
| Stats/KVK | `/kvk_recompute` | `commands/stats_cmds.py` | decorator | none observed | top-level | Candidate `/kvk recompute` |
| Stats/KVK | `/kvk_list_scans` | `commands/stats_cmds.py` | decorator | none observed | top-level | Candidate `/kvk list_scans` |
| Stats/KVK | `/test_kvk_embed` | `commands/stats_cmds.py` | decorator | none observed | top-level | Candidate `/kvk test_embed` |
| Stats/KVK | `/kvk_window_preview` | `commands/stats_cmds.py` | decorator | none observed | top-level | Candidate `/kvk window_preview` |
| Subscriptions | `/subscribe` | `commands/subscriptions_cmds.py` | public | none observed | top-level | Candidate `/subscriptions subscribe` or keep flat |
| Subscriptions | `/modify_subscription` | `commands/subscriptions_cmds.py` | public | none observed | top-level | Candidate `/subscriptions modify` or keep flat |
| Subscriptions | `/unsubscribe` | `commands/subscriptions_cmds.py` | public | none observed | top-level | Candidate `/subscriptions unsubscribe` or keep flat |
| Subscriptions | `/list_subscribers` | `commands/subscriptions_cmds.py` | decorator | none observed | top-level | Candidate `/subscriptions list` |
| Subscriptions | `/migrate_subscriptions_dryrun` | `commands/subscriptions_cmds.py` | decorator | none observed | top-level | Candidate `/subscriptions migrate_dryrun` |
| Subscriptions | `/migrate_subscriptions_apply` | `commands/subscriptions_cmds.py` | decorator | none observed | top-level | Candidate `/subscriptions migrate_apply` |
| Telemetry | `/ping` | `commands/telemetry_cmds.py` | public | none observed | top-level | Keep flat or move to `/ops ping` |
| Usage Analytics | `/usage` | `commands/admin_cmds.py` | decorator | none observed | top-level | Candidate `/ops usage` |
| Usage Analytics | `/usage_detail` | `commands/admin_cmds.py` | decorator | none observed | top-level | Candidate `/ops usage_detail` |

## Domain Review Summary

| Domain | Strengths | Weaknesses / risks | Improvement opportunity |
|---|---|---|---|
| Ark | Strong service/DAL/test ecosystem and consistent leadership decorators on most admin paths. | Largest flat top-level block; public paths require operator communication; docs reference flat names. | First high-value grouping phase after decorator audit. |
| Ops | Core operational tools already grouped and command lifecycle reuse is strong. Phase 1 standardised `/history`, `/failures`, and redundant already-decorated admin gates. | Processing report commands remain flat. | Move remaining report/usage/test ops commands under `/ops` after operator approval. |
| MGE | Already grouped; permission decorators mostly consistent. | `/mge admin_completion` uses an inline admin check. | Standardise decorator and preserve current grouped path. |
| Public KVK/Stats | Rich test coverage and recent service/DAL cleanup around KVK admin commands. | Many public player paths are flat and highly discoverable; moving them could confuse players. | Split admin KVK commands first; defer player path changes until approved UX rules exist. |
| Registry | Strong service/cache tests and command service extraction. | Public self-service paths are discoverability-sensitive; admin bulk operations remain flat. | Group admin registry commands first; decide public path policy separately. |
| Inventory | Service-oriented implementation and focused inventory tests. Phase 1 standardised command access checks onto decorators. | Inventory export still passes admin context to the service for self-service/admin override semantics. | Group under `/inventory` only after public-path UX approval. |
| Calendar / Events | Calendar command layer is thin and docs are extensive. | Calendar admin commands live in `admin_cmds.py` while public commands live in `calendar_cmds.py`; many docs reference flat paths. | Group calendar public/admin commands with careful docs update. |
| Subscriptions | Public flow is simple and tested via views. | Legacy `subscribe.py` still duplicates `/subscribe`; public path migration needs communication. | Retire or classify legacy cog first, then consider `/subscriptions` group. |
| Secondary cogs | Disabled by default, reducing active startup risk. | Validator duplicate output does not distinguish disabled code from active risk. | Enhance validator or retire legacy declarations. |

## Technical Debt Register

### Phase 1 Completed Item
- Area: `commands/admin_cmds.py`, `commands/inventory_cmds.py`, `commands/location_cmds.py`, `commands/mge_cmds.py`, `commands/stats_cmds.py`, `commands/telemetry_cmds.py`, `decoraters.py`
- Type: consistency
- Description: Phase 1 moved active command access control for the reviewed inline admin/channel/leadership checks onto standard decorators and removed redundant inline admin gates from already-decorated commands.
- Resolution: Added reusable decorator support for admin-only, admin-or-leadership in allowed channels, and missing-config channel denial. Preserved command paths, command count, service handoff behavior, and denial visibility. `/export_inventory` remains service-authorized because it is self-service with admin override context rather than a command-denial gate.
- Validation: Command registration remained `primary=82 grouped_subcommands_detected=21 secondary_cogs=5 secondary_subscribe=1 total_unique=82`; full pytest, pre-commit, log-noise validation, and Codex Security diff review passed.

### Deferred Optimisation
- Area: `commands/ark_cmds.py`, `docs/ark/`, Ark command tests
- Type: architecture
- Description: Ark remains a large flat command surface with stale flat-path documentation and public/operator workflows tied to current names.
- Suggested Fix: Design an approved `/ark` grouping migration with docs/tests/operator communication.
- Impact: high
- Risk: medium
- Dependencies: Operator approval for public Ark path changes.

### Deferred Optimisation
- Area: `scripts/validate_command_registration.py`, `cogs/commands.py`, `subscribe.py`
- Type: cleanup
- Description: Duplicate command warnings do not distinguish disabled legacy surfaces from active startup-sync risk.
- Suggested Fix: Add active/disabled classification or retire disabled declarations after confirmation.
- Impact: medium
- Risk: low
- Dependencies: Confirm secondary cogs are never production-loaded.

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

### Phase 2 - Validator And Inventory Tooling Enhancement

Goal: improve command-platform reporting before large migrations.

Scope:

- `scripts/validate_command_registration.py`
- `commands/command_inventory.py`
- tests around command inventory, grouped command flattening, warning thresholds, and duplicate
  classification

Implementation notes:

- Distinguish active authoritative command paths from disabled secondary cogs.
- Detect helper-attached grouped subcommands such as `/prekvk import_history`.
- Report command owner module, group/subcommand path, duplicate source, and near-limit risk.
- Keep the existing hard fail above 100 top-level commands and warning at 90+.

Validation:

- `tests/test_validate_command_registration.py`
- `tests/test_command_inventory.py`
- `tests/test_command_lifecycle.py`
- `tests/test_command_registration_smoke.py`
- `python scripts/validate_command_registration.py`

### Phase 3 - Low-Risk Ops Consolidation

Goal: recover command headroom with low public-UX risk after permissions are standardised.

Scope candidates:

- Move `/summary`, `/weeksummary`, `/history`, `/failures` under `/ops`.
- Move `/usage` and `/usage_detail` under `/ops`.
- Move `/test_embed` under `/ops` or retire if no longer useful.
- Consider `/ping` ownership: keep flat for health/debug discoverability or move to `/ops ping`.

Implementation notes:

- Preserve existing command behavior, output, and usage tracking.
- Update docs that mention the old paths.
- Treat public visibility of `/summary` and `/weeksummary` as an explicit operator decision.

Validation:

- Command registration smoke tests.
- Focused tests for migrated handlers.
- Command cache/version tests where grouped names affect signatures.

### Phase 4 - Ark Command Grouping

Goal: group Ark commands under `/ark`, recovering the largest remaining top-level block.

Scope candidates:

- Leadership/admin paths: `create_match`, `force_announce`, `amend_match`, `cancel_match`,
  `set_preference`, `clear_preference`, `ban_add`, `ban_revoke`, `ban_list`, `set_result`,
  `generate_draft`, `create_team`
- Public paths: `reminder_prefs`, `report_players`

Implementation notes:

- Public Ark path migration requires operator approval and communication timing.
- Preserve `is_admin_or_leadership_only`, `channel_only`, autocomplete/options, modal/view flows,
  and interaction response behavior.
- Update Ark docs and smoke-test runbooks that reference flat paths.

Validation:

- Ark command tests, including reminder prefs and force announce.
- Ark registration, draft, ban, cancel, and result focused tests where touched.
- Command registration validation and smoke imports.
- Codex Security review required due to permissions, public interactions, and restart-sensitive Ark
  flows.

### Phase 5 - Public Domain Grouping Design

Goal: decide the player-facing command policy before touching high-discoverability paths.

Scope candidates:

- `/registry`: registration, my registrations, admin registry operations
- `/kvk` and `/stats`: KVK rankings, personal stats, exports, admin KVK operations
- `/inventory`: import, report, preferences, export, audit
- `/calendar` and `/events`: calendar browsing, reminder config, next KVK events/fights,
  refresh operations
- `/subscriptions`: subscribe, modify, unsubscribe, list, migration commands
- `/crystaltech`, `/honor`, `/location`, `/activity`

Implementation notes:

- Split admin-heavy commands from player self-service commands where that reduces UX risk.
- Keep heavily used/self-service paths flat unless operators approve migration.
- Consider transition docs or announcement copy for public renames.

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
3. Phase 3: Low-Risk Ops Consolidation.
4. Phase 4: Ark Command Grouping.
5. Phase 5: Public Domain Grouping Design.
6. Phase 6: Canonical Command Documentation.
7. Phase 7: Future Governance And CI Guardrails.

The first implementation PR should be Phase 1 only. Grouping before decorator standardisation would
make permission preservation harder to verify and would mix behavior-risk cleanup with path
migration.
