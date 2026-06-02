# Codex Task Pack - Command Platform Phase 5A Admin Leadership Operator Domain Grouping

## 1. Task Header

- Task name: Command Platform Phase 5A - Admin Leadership Operator Domain Grouping
- Date: 2026-06-01
- Owner/context: Command Platform Audit & Optimisation Programme
- Task type: deferred optimisation batch / command-surface migration
- One-pass approved: no
- Status: implemented in this Phase 5A branch

## 2. Required Reading

Before implementation, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/task_packs/Codex Task Pack - Command Platform Audit & Optimisation Programme.md`
- `docs/task_packs/Codex Task Pack - Command Platform Phase 5 Public Domain Grouping Design.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Also review:

- `commands/registry_cmds.py`
- `commands/stats_cmds.py`
- `commands/inventory_cmds.py`
- `commands/admin_cmds.py`
- `commands/events_cmds.py`
- `commands/subscriptions_cmds.py`
- `commands/activity_cmds.py`
- `commands/location_cmds.py`
- `commands/command_inventory.py`
- `core/command_lifecycle.py`
- `scripts/validate_command_registration.py`
- command registration, inventory, lifecycle, and validator tests
- domain command tests for registry, stats/KVK, inventory, calendar admin, events, subscriptions,
  CrystalTech, honor, location, and activity
- docs and smoke references that mention any moved flat command path

## 3. Objective

Implement the approved Phase 5A command-surface migration by grouping admin, leadership, and
operator-heavy flat commands under stable domain or operator groups while preserving behavior.

This phase should:

- move only the approved Phase 5A admin/leadership/operator command paths
- preserve command handlers, decorators, permissions, options, autocomplete, descriptions,
  versions, usage tracking, response visibility, service calls, and command-cache semantics
- keep player self-service commands flat
- keep generic public calendar/KVK calendar commands flat
- reduce the top-level command count without redesigning public/player workflows
- update tests, command-platform docs, and smoke references for moved paths
- run Codex Security before PR handoff because Discord command paths and permission-sensitive
  interaction surfaces are changing

## 4. Background

Phase 4 was completed in PR 134 (`codex/command-platform-phase-4-ark-grouping`), smoke tested
successfully, merged, and pushed to production. It grouped all 14 Ark commands under `/ark`.

Phase 5 was completed in PR 135 (`codex/command-platform-phase-5a-design-docs`), merged, and
pushed to production in production PR 444. It approved Phase 5A as the next implementation slice
for admin/leadership/operator grouping only, and deferred player self-service plus public
calendar/KVK calendar redesign outside this command-count programme.

Current validator baseline after Phase 4 and Phase 5 design:

```text
primary=62 grouped_subcommands_detected=43 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=62
```

Current grouped command summary:

| Group | Statically detected subcommands |
|---|---:|
| `/ark` | 14 |
| `/ops` | 21 |
| `/mge` | 6 |
| `/prekvk` | 2 |

Phase 5A implementation baseline:

```text
primary=39 grouped_subcommands_detected=76 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=39
```

Grouped command summary:

| Group | Expected subcommands |
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

Recalculate during implementation if any target path changes after scope review.

## 5. Scope

### In Scope

Create or extend grouped command surfaces for these approved moves:

#### Registry Admin

- `/remove_registration` -> `/registry remove`
- `/remove_registration_by_id` -> `/registry remove_by_id`
- `/admin_register_governor` -> `/registry admin_register`
- `/registration_audit` -> `/registry audit`
- `/bulk_export_registrations` -> `/registry bulk_export`
- `/bulk_import_registrations_dryrun` -> `/registry bulk_import_dryrun`
- `/bulk_import_registrations` -> `/registry bulk_import`

#### KVK / Stats Admin And Leadership

- `/test_kvk_export` -> `/kvk test_export`
- `/refresh_stats_cache` -> `/kvk refresh_stats_cache`
- `/kvk_export_all` -> `/kvk export_all`
- `/kvk_recompute` -> `/kvk recompute`
- `/kvk_list_scans` -> `/kvk list_scans`
- `/test_kvk_embed` -> `/kvk test_embed`
- `/kvk_window_preview` -> `/kvk window_preview`
- `/player_stats` -> `/stats player`

`/player_stats` is included because it is gated by `is_admin_or_leadership()`.

#### Inventory Admin / Operator

- `/import_inventory` -> `/inventory import`
- `/inventory_import_audit` -> `/inventory audit`

#### Calendar Admin / Operator

- `/calendar_refresh` -> `/ops calendar_refresh`
- `/calendar_generate` -> `/ops calendar_generate`
- `/calendar_publish_cache` -> `/ops calendar_publish_cache`
- `/calendar_status` -> `/ops calendar_status`

Do not create a `/calendar` group in Phase 5A. The flat public `/calendar` command remains in
place until the deferred public calendar/KVK calendar redesign.

#### Events Admin / Operator

- `/refresh_events` -> `/events refresh`
- `/refresh_kvk_overview` -> `/events refresh_kvk_overview`

#### Subscriptions Admin / Operator

- `/list_subscribers` -> `/subscriptions list`
- `/migrate_subscriptions_dryrun` -> `/subscriptions migrate_dryrun`
- `/migrate_subscriptions_apply` -> `/subscriptions migrate_apply`

#### CrystalTech Admin / Operator

- `/crystaltech_validate` -> `/crystaltech validate`
- `/crystaltech_reload` -> `/crystaltech reload`
- `/crystaltech_admin_reset` -> `/crystaltech admin_reset`

#### Honor Admin / Operator

- `/honor_purge_last` -> `/honor purge_last`

Do not move `/honor_rankings` in Phase 5A.

#### Location Admin / Leadership / Operator

- `/import_locations` -> `/location import`
- `/player_location` -> `/location player`

`/player_location` is included because it is gated by admin/leadership access in allowed channels.

#### Activity Leadership / Operator

- `/activity_top` -> `/activity top`

### Also In Scope

- command registration, inventory, cache/version, lifecycle, and validator test updates
- focused domain tests for moved command registration and preserved behavior
- docs and smoke-reference updates for moved paths
- command-platform audit, command-surface audit, and task-pack updates
- Codex Security review before PR handoff

### Out Of Scope

- Player self-service workflow redesign:
  - `/register_governor`
  - `/modify_registration`
  - `/my_registrations`
  - `/mygovernorid`
  - `/mykvkstats`
  - `/my_stats`
  - `/my_stats_export`
  - `/mykvkhistory`
  - `/mykvktargets`
  - `/mykvkcrystaltech`
  - `/myinventory`
  - `/inventory_preferences`
  - `/export_inventory`
  - `/subscribe`
  - `/modify_subscription`
  - `/unsubscribe`
  - `/calendar_reminder_config`
- Generic public calendar/KVK calendar redesign:
  - `/calendar`
  - `/calendar_next_event`
  - `/next_kvk_fight`
  - `/next_kvk_event`
- `/honor_rankings`
- `/player_profile`
- `/ping`
- SQL schema changes
- permission-decorator behavior changes
- command option/autocomplete/description/version changes unless required only to preserve grouped
  registration
- handler/service/DAL/view behavior refactors beyond the minimum needed to attach handlers to
  command groups
- aliases or transition shims unless explicitly approved
- production promotion or deployment

## 6. Mandatory Workflow

1. Review/scope Phase 5A and stop for approval.
2. Map every moved command handler, decorator, option, autocomplete, version, usage tracking, and
   response visibility.
3. Confirm target group names and the calendar admin `/ops calendar_*` correction.
4. Present implementation plan and stop for approval unless one-pass implementation is explicitly
   approved in the new chat.
5. Implement approved Phase 5A grouping only.
6. Update focused tests and docs.
7. Run validation.
8. Run Codex Security review before PR handoff.
9. Open a ready-for-review PR against `K98-bot-mirror`.

## 7. Acceptance Criteria

- [ ] Only approved Phase 5A command paths are moved.
- [ ] Player self-service commands remain flat.
- [ ] Generic public calendar/KVK calendar commands remain flat.
- [ ] `/calendar` remains a flat public command.
- [ ] Calendar admin commands move under `/ops calendar_*`, not `/calendar ...`.
- [ ] `/player_location` and `/player_stats` are included as admin/leadership lookup commands.
- [ ] `/honor_rankings`, `/player_profile`, and `/ping` remain unchanged.
- [ ] Command decorators, permissions, options, autocomplete, descriptions, versions, usage
      tracking, response visibility, service calls, and handler behavior are preserved.
- [ ] Command inventory, lifecycle, cache/version, and validator tests understand the new grouped
      paths.
- [ ] `scripts/validate_command_registration.py` reports the expected Phase 5A baseline or any
      variance is explained.
- [ ] Docs and smoke references reflect moved paths.
- [ ] Codex Security review is run before PR handoff.

## 8. Suggested Validation

Minimum validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_registration_smoke.py tests\test_command_inventory.py tests\test_command_lifecycle.py
```

Focused domain coverage to review and run as applicable:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_registry_cmds.py tests\test_registry_command_service.py tests\test_registry_service.py tests\test_registry_views_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_stats_cmds.py tests\test_kvk_admin_service.py tests\test_kvk_export_service.py tests\test_kvk_all_recompute_sql_contract.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_command_registration.py tests\test_inventory_audit_service.py tests\test_inventory_upload_flow.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_admin_calendar_commands_task3.py tests\test_calendar_publish_cache.py tests\test_calendar_status_embed_task4.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_events_views.py tests\test_subscription_views.py tests\test_activity_cmds.py tests\test_location_views_smoke.py tests\test_location_import_service.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_crystaltech_service.py tests\test_honor_rankings_view.py
```

Before PR handoff, run or justify skipping:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security is required because Phase 5A changes Discord command paths and
permissions-sensitive interaction entry points.

## 9. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. SQL Changes
4. Helpers Reused
5. Refactor Findings
6. Test Plan And Results
7. AI Review Gates
8. Deployment / Rollback Notes
9. Deferred Optimisations
