# Codex Chat Starter - Command Platform Phase 5A Admin Leadership Operator Domain Grouping

Use this starter to begin the next Command Platform Audit & Optimisation Programme implementation
phase.

Source programme documents:

- `docs/task_packs/Codex Task Pack - Command Platform Audit & Optimisation Programme.md`
- `docs/task_packs/Codex Task Pack - Command Platform Phase 5 Public Domain Grouping Design.md`
- `docs/task_packs/Codex Task Pack - Command Platform Phase 5A Admin Leadership Operator Domain Grouping.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Phase 5 design was completed in PR 135 (`codex/command-platform-phase-5a-design-docs`), merged,
and pushed to production in production PR 444. It approved Phase 5A only: admin, leadership, and
operator command grouping. It deferred player self-service workflow redesign and public
calendar/KVK calendar redesign outside the command-count programme.

Current validator baseline:

```text
primary=62 grouped_subcommands_detected=43 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=62
```

Expected Phase 5A baseline if the approved implementation scope is delivered as written:

```text
primary=39 grouped_subcommands_detected=76 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=39
```

## Copy/Paste Starter

Codex, begin Command Platform Phase 5A: Admin Leadership Operator Domain Grouping.

This follows the completed Phase 5 design PR:

- PR 135: `codex/command-platform-phase-5a-design-docs`
- Production PR 444: promoted to `K98-bot/main`
- Result: merged and pushed to production
- Current validator baseline:

```text
primary=62 grouped_subcommands_detected=43 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=62
```

The objective for this phase is to implement only the approved admin/leadership/operator grouping
slice. Do not move player self-service commands or generic public calendar/KVK calendar commands.

## 1. Task Header

- Task name: Command Platform Phase 5A - Admin Leadership Operator Domain Grouping
- Date: 2026-06-01
- Owner/context: Command Platform Audit & Optimisation Programme
- Task type: deferred optimisation batch / command-surface migration
- One-pass approved: no

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
- `docs/task_packs/Codex Task Pack - Command Platform Phase 5A Admin Leadership Operator Domain Grouping.md`
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
- relevant domain tests and docs/smoke references for moved paths

## 3. Objective

Move only the approved admin/leadership/operator command paths into grouped command surfaces while
preserving existing behavior, permissions, options, autocomplete, descriptions, versions, usage
tracking, response visibility, command-cache semantics, service calls, and handler bodies.

## 4. Approved Scope

Move these commands only:

- Registry:
  - `/remove_registration` -> `/registry remove`
  - `/remove_registration_by_id` -> `/registry remove_by_id`
  - `/admin_register_governor` -> `/registry admin_register`
  - `/registration_audit` -> `/registry audit`
  - `/bulk_export_registrations` -> `/registry bulk_export`
  - `/bulk_import_registrations_dryrun` -> `/registry bulk_import_dryrun`
  - `/bulk_import_registrations` -> `/registry bulk_import`
- KVK / stats:
  - `/test_kvk_export` -> `/kvk test_export`
  - `/refresh_stats_cache` -> `/kvk refresh_stats_cache`
  - `/kvk_export_all` -> `/kvk export_all`
  - `/kvk_recompute` -> `/kvk recompute`
  - `/kvk_list_scans` -> `/kvk list_scans`
  - `/test_kvk_embed` -> `/kvk test_embed`
  - `/kvk_window_preview` -> `/kvk window_preview`
  - `/player_stats` -> `/stats player`
- Inventory:
  - `/import_inventory` -> `/inventory import`
  - `/inventory_import_audit` -> `/inventory audit`
- Calendar admin/operator:
  - `/calendar_refresh` -> `/ops calendar_refresh`
  - `/calendar_generate` -> `/ops calendar_generate`
  - `/calendar_publish_cache` -> `/ops calendar_publish_cache`
  - `/calendar_status` -> `/ops calendar_status`
- Events:
  - `/refresh_events` -> `/events refresh`
  - `/refresh_kvk_overview` -> `/events refresh_kvk_overview`
- Subscriptions:
  - `/list_subscribers` -> `/subscriptions list`
  - `/migrate_subscriptions_dryrun` -> `/subscriptions migrate_dryrun`
  - `/migrate_subscriptions_apply` -> `/subscriptions migrate_apply`
- CrystalTech:
  - `/crystaltech_validate` -> `/crystaltech validate`
  - `/crystaltech_reload` -> `/crystaltech reload`
  - `/crystaltech_admin_reset` -> `/crystaltech admin_reset`
- Honor:
  - `/honor_purge_last` -> `/honor purge_last`
- Location:
  - `/import_locations` -> `/location import`
  - `/player_location` -> `/location player`
- Activity:
  - `/activity_top` -> `/activity top`

Important correction from the design handoff: do not create `/calendar ...` grouped commands in
Phase 5A. `/calendar` remains a flat public command, so calendar admin/operator commands should
move under existing `/ops calendar_*` paths.

## 5. Out Of Scope

Do not move:

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
- `/calendar`
- `/calendar_next_event`
- `/next_kvk_fight`
- `/next_kvk_event`
- `/honor_rankings`
- `/player_profile`
- `/ping`

Also out of scope:

- SQL schema changes
- permission behavior changes
- public/player workflow redesign
- public calendar/KVK calendar UX redesign
- aliases or transition shims unless explicitly approved
- production promotion or deployment

## 6. Mandatory Workflow

1. Review/scope Phase 5A and stop for approval.
2. Confirm every moved command's handler, decorator, option, autocomplete, version, usage tracking,
   and response visibility.
3. Confirm the `/ops calendar_*` calendar admin target paths.
4. Present implementation plan and stop for approval.
5. Implement only approved Phase 5A grouping.
6. Update focused tests and docs.
7. Run validation.
8. Run Codex Security review before PR handoff.
9. Open a ready-for-review PR against `K98-bot-mirror`.

Proceed in one pass only if explicitly approved in the new chat.

## 7. Suggested Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_registration_smoke.py tests\test_command_inventory.py tests\test_command_lifecycle.py
```

Run focused domain tests selected during scope review. Before PR handoff, run or justify skipping:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security is required because this phase changes Discord command paths and
permissions-sensitive interaction entry points.

## 8. Required Delivery Output

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
