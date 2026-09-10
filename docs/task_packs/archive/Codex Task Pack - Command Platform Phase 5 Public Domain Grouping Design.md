# Codex Task Pack - Command Platform Phase 5 Public Domain Grouping Design

> Status: complete. Delivered in PR 135 (`codex/command-platform-phase-5a-design-docs`), merged,
> pushed to production in production PR 444, and later archived after Command Platform Phase 7
> closed the programme.

## 1. Task Header

- Task name: Command Platform Phase 5 - Public Domain Grouping Design
- Date: 2026-06-01
- Owner/context: Command Platform Audit & Optimisation Programme
- Task type: deferred optimisation batch / command-surface design
- One-pass approved: no
- Status: complete; delivered in PR 135, merged, and pushed to production in production PR 444
  Phase 5A was later delivered in PR 136, smoke tested successfully, merged, and pushed to
  production on 2026-06-02.

## 2. Required Reading

Before implementation or documentation changes, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/task_packs/Codex Task Pack - Command Platform Audit & Optimisation Programme.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Also review:

- `commands/registry_cmds.py`
- `commands/stats_cmds.py`
- `commands/inventory_cmds.py`
- `commands/calendar_cmds.py`
- `commands/events_cmds.py`
- `commands/subscriptions_cmds.py`
- `commands/admin_cmds.py`
- `commands/telemetry_cmds.py`
- `commands/activity_cmds.py`
- `commands/location_cmds.py`
- `commands/command_inventory.py`
- `core/command_lifecycle.py`
- `scripts/validate_command_registration.py`
- command registration, inventory, lifecycle, and validator tests
- public/user-facing docs and smoke references for registry, KVK/stats, inventory, calendar,
  events, subscriptions, location, CrystalTech, honor, and activity commands

## 3. Objective

Design the next command grouping strategy and approve only the low-disruption
admin/leadership/operator implementation slice. Public/player self-service and generic public
calendar/KVK calendar commands are intentionally deferred for deeper workflow redesign.

This phase should:

- review remaining flat public/player and admin-heavy domain command paths
- approve Phase 5A for admin/leadership/operator grouping only
- distinguish high-discoverability public/player workflows that should not be moved by simple
  path grouping
- capture player self-service and generic calendar/KVK calendar redesign as deferred
  optimisations
- identify the safest next implementation slice after design approval
- keep the current Phase 4 command baseline unchanged
- update command-platform docs with the approved Phase 5 design and roadmap

## 4. Background

Phase 4 was completed in PR 134 (`codex/command-platform-phase-4-ark-grouping`), smoke tested
successfully, merged, and pushed to production. It grouped all 14 Ark commands under `/ark`,
including public `/ark reminder_prefs` and `/ark report_players`, and confirmed command-cache
validation remained green after restart.

Current validator baseline:

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

The top-level command surface now has a 38-command buffer below Discord's 100-command limit. Phase
5 is not urgent command-count emergency work; it is the policy/design phase for public and
player-facing domains where discoverability and operator communication matter more than raw count
reduction.

## 5. Approved Phase 5A Scope

Phase 5A is the only approved implementation slice from this design phase. It should group
admin/leadership/operator-heavy commands by domain while preserving behavior, permissions,
options, versions, usage tracking, autocomplete, response visibility, command-cache semantics,
and handler bodies.

Phase 5A completion note: PR 136 (`codex/command-platform-phase-5a-admin-grouping`) delivered the
approved implementation slice, passed smoke testing, merged, and was pushed to production. The
delivered baseline is
`primary=39 grouped_subcommands_detected=76 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=39`.
The next command-platform phase is Phase 6, Canonical Command Documentation.

Approved Phase 5A candidates:

- Registry admin:
  - `/remove_registration` -> `/registry remove`
  - `/remove_registration_by_id` -> `/registry remove_by_id`
  - `/admin_register_governor` -> `/registry admin_register`
  - `/registration_audit` -> `/registry audit`
  - `/bulk_export_registrations` -> `/registry bulk_export`
  - `/bulk_import_registrations_dryrun` -> `/registry bulk_import_dryrun`
  - `/bulk_import_registrations` -> `/registry bulk_import`
- KVK / stats admin and leadership:
  - `/test_kvk_export` -> `/kvk test_export`
  - `/refresh_stats_cache` -> `/kvk refresh_stats_cache`
  - `/player_stats` -> `/stats player`
  - `/kvk_export_all` -> `/kvk export_all`
  - `/kvk_recompute` -> `/kvk recompute`
  - `/kvk_list_scans` -> `/kvk list_scans`
  - `/test_kvk_embed` -> `/kvk test_embed`
  - `/kvk_window_preview` -> `/kvk window_preview`
- Inventory admin/operator:
  - `/import_inventory` -> `/inventory import`
  - `/inventory_import_audit` -> `/inventory audit`
- Calendar admin/operator:
  - `/calendar_refresh` -> `/ops calendar_refresh`
  - `/calendar_generate` -> `/ops calendar_generate`
  - `/calendar_publish_cache` -> `/ops calendar_publish_cache`
  - `/calendar_status` -> `/ops calendar_status`
- Events admin/operator:
  - `/refresh_events` -> `/events refresh`
  - `/refresh_kvk_overview` -> `/events refresh_kvk_overview`
- Subscriptions admin/operator:
  - `/list_subscribers` -> `/subscriptions list`
  - `/migrate_subscriptions_dryrun` -> `/subscriptions migrate_dryrun`
  - `/migrate_subscriptions_apply` -> `/subscriptions migrate_apply`
- CrystalTech admin/operator:
  - `/crystaltech_validate` -> `/crystaltech validate`
  - `/crystaltech_reload` -> `/crystaltech reload`
  - `/crystaltech_admin_reset` -> `/crystaltech admin_reset`
- Honor admin/operator:
  - `/honor_purge_last` -> `/honor purge_last`
- Location admin/leadership/operator:
  - `/import_locations` -> `/location import`
  - `/player_location` -> `/location player`
- Activity leadership/operator:
  - `/activity_top` -> `/activity top`

`/player_location` and `/player_stats` are included in Phase 5A because they are
admin/leadership lookup commands, not player self-service commands.

Expected Phase 5A outcome: reduce the top-level command count without changing public/player
self-service workflows.

Implementation correction: Phase 5A should not create a `/calendar` command group while the public
flat `/calendar` command remains in place. Calendar admin/operator commands should move under the
existing `/ops` group for Phase 5A. A future public calendar/KVK calendar redesign can decide
whether `/calendar overview` and related grouped public paths should replace the current flat
public command.

## 6. Deferred From Phase 5A

### Player Self-Service Workflow Redesign

The following commands are high-discoverability, player-specific, and should not be moved by a
simple grouped-path migration:

- Registry/account self-service:
  - `/register_governor`
  - `/modify_registration`
  - `/my_registrations`
  - `/mygovernorid`
- KVK/stats/crystal personal self-service:
  - `/mykvkstats`
  - `/my_stats`
  - `/my_stats_export`
  - `/mykvkhistory`
  - `/mykvktargets`
  - `/mykvkcrystaltech`
- Inventory personal self-service:
  - `/myinventory`
  - `/inventory_preferences`
  - `/export_inventory`
- Subscription self-service:
  - `/subscribe`
  - `/modify_subscription`
  - `/unsubscribe`
- Personal calendar preferences:
  - `/calendar_reminder_config`

Design note: these commands may represent development-time splits rather than ideal player
workflows. For example, governor/account commands may be better redesigned around one coherent
Governor ID or account command surface with lookup, register, review, and modify actions instead
of four separate entry points. That redesign should consider multi-step user journeys, SQL-backed
usage evidence, migration communication, command aliases/transition limits, and whether any
current command should remain flat for habit/discoverability.

### Public Calendar / KVK Calendar Redesign

The following commands are generic public/everybody-facing commands and are also deferred from
Phase 5A:

- `/calendar`
- `/calendar_next_event`
- `/next_kvk_fight`
- `/next_kvk_event`

Design note: these are inconsistent today:

- `/calendar` is an ephemeral calendar overview.
- `/calendar_next_event` is ephemeral and shows one next calendar event.
- `/next_kvk_fight` is public and shows one fight with controls for the next three fights.
- `/next_kvk_event` is public and shows one event with controls for the next five events.

A future calendar/KVK calendar design should review visibility, naming, and interaction behavior
together. Candidate end state to assess:

- `/calendar overview`
- `/calendar kvk_overview`
- `/calendar next_event`
- `/calendar next_kvk_fight`
- `/calendar next_kvk_event`

The future task should also evaluate the missing `/kvk_calendar` or equivalent KVK calendar
overview need and whether these public information commands should all display publicly.

## 7. Original Review Scope

### In Scope

Review and design grouping policy for:

- Registry:
  - `/register_governor`
  - `/modify_registration`
  - `/remove_registration`
  - `/remove_registration_by_id`
  - `/my_registrations`
  - `/admin_register_governor`
  - `/registration_audit`
  - `/bulk_export_registrations`
  - `/bulk_import_registrations_dryrun`
  - `/bulk_import_registrations`
- KVK / Stats / Player profile:
  - `/mykvktargets`
  - `/mygovernorid`
  - `/player_profile`
  - `/mykvkcrystaltech`
  - `/test_kvk_export`
  - `/mykvkstats`
  - `/refresh_stats_cache`
  - `/my_stats`
  - `/my_stats_export`
  - `/player_stats`
  - `/mykvkhistory`
  - `/kvk_rankings`
  - `/kvk_export_all`
  - `/kvk_recompute`
  - `/kvk_list_scans`
  - `/test_kvk_embed`
  - `/kvk_window_preview`
- Inventory:
  - `/import_inventory`
  - `/myinventory`
  - `/inventory_preferences`
  - `/export_inventory`
  - `/inventory_import_audit`
- Calendar / Events:
  - `/calendar`
  - `/calendar_next_event`
  - `/calendar_reminder_config`
  - `/calendar_refresh`
  - `/calendar_generate`
  - `/calendar_publish_cache`
  - `/calendar_status`
  - `/next_kvk_fight`
  - `/next_kvk_event`
  - `/refresh_events`
  - `/refresh_kvk_overview`
- Subscriptions:
  - `/subscribe`
  - `/modify_subscription`
  - `/unsubscribe`
  - `/list_subscribers`
  - `/migrate_subscriptions_dryrun`
  - `/migrate_subscriptions_apply`
- Other admin-heavy or low-use candidates:
  - `/activity_top`
  - `/honor_rankings`
  - `/honor_purge_last`
  - `/import_locations`
  - `/player_location`
  - `/crystaltech_validate`
  - `/crystaltech_reload`
  - `/crystaltech_admin_reset`

Also in scope:

- command-platform audit docs
- command-surface audit docs
- deferred optimisation backlog updates
- new candidate implementation phase recommendations
- operator communication notes for public/player command moves
- test and validation recommendations for later implementation phases

### Out Of Scope

- Moving any slash command path
- Changing command decorators, permissions, options, autocomplete, descriptions, versions, usage
  tracking, command-cache behavior, or command handlers
- SQL schema changes
- Runtime code changes except inspection-only findings documented for later approval
- Production promotion or deployment

## 8. Design Questions

Phase 5 answered:

1. Public/player self-service commands should stay flat for now and move into a separate workflow
   redesign task rather than a simple grouping implementation.
2. Admin/leadership/operator commands listed in the approved Phase 5A scope can move first.
3. Phase 5A should use domain groups where ownership is clear: `/registry`, `/kvk`, `/stats`,
   `/inventory`, `/calendar`, `/events`, `/subscriptions`, `/crystaltech`, `/honor`, `/location`,
   and `/activity`.
4. Public/player self-service command moves require separate operator approval, SQL-backed usage
   review, and clear briefing before implementation.
5. Public calendar/KVK calendar commands require a separate UX redesign before path grouping.
6. Aliases/transition messaging should be assessed in the deferred player and calendar redesign
   tasks; Phase 5A can use direct rename because it targets admin/leadership/operator surfaces.
7. The next safest implementation phase is Phase 5A only.

## 9. Expected Deliverables

1. Updated command-platform design section listing:
   - current path
   - owner module
   - permission model
   - public/admin classification
   - usage evidence available
   - recommended disposition
   - proposed target path where applicable
   - operator-communication requirement
2. Phase 5A admin/leadership/operator grouping policy.
3. Admin-heavy grouping candidate set for the next implementation PR.
4. Deferred player self-service redesign item requiring explicit operator approval.
5. Deferred public calendar/KVK calendar redesign item.
6. Documentation and smoke-test impact inventory.
7. Updated deferred optimisation items for any out-of-scope command architecture, docs, or test
   findings.
8. Proposed roadmap updates showing Phase 5A as the final command-count implementation slice in
   this programme.

## 10. Mandatory Workflow

1. Review/scope Phase 5 and stop for approval.
2. Map remaining flat command paths by domain, owner module, permission model, and user audience.
3. Review local usage evidence and clearly label any gaps where SQL-backed usage review is needed.
4. Identify documentation and smoke references that would need updates for each proposed path.
5. Present grouping policy and candidate path design.
6. Stop for approval before editing docs beyond the design deliverable or before any runtime work.
7. Update docs/deferred items only after approval.
8. Run documentation-focused validation.
9. Stop again before Phase 5A runtime implementation.

Proceed in one pass only if explicitly approved in the new chat.

## 11. Acceptance Criteria

- [ ] No command paths are moved in Phase 5.
- [ ] Remaining flat commands are classified by domain, audience, permission model, and grouping
      risk.
- [ ] Public/player self-service path moves are deferred into a separate workflow redesign task.
- [ ] Generic public calendar/KVK calendar moves are deferred into a separate UX redesign task.
- [ ] Admin-heavy low-risk candidate moves are separated from high-discoverability player and
      public information commands.
- [ ] Proposed target paths are consistent and discoverable.
- [ ] Operator communication needs are identified for future public/player candidates.
- [ ] Follow-up implementation phase or phases are clearly recommended.
- [ ] Command-platform docs and deferred backlog are updated with the approved design.
- [ ] Validation is run or intentionally skipped with reasons.

## 12. Suggested Validation

Documentation/design-only validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

If Phase 5 edits tests or runtime code despite the default design-only scope, add focused pytest
coverage for the affected command domains and rerun:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_registration_smoke.py tests\test_command_inventory.py tests\test_command_lifecycle.py
```

Codex Security may be skipped for pure documentation/design output. It becomes required before PR
handoff if Phase 5 changes runtime command registration, permissions, public interactions,
SQL/data access, file handling, or restart-sensitive behavior.

## 13. Required Delivery Output

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
