# Codex Chat Starter - Command Platform Phase 5 Public Domain Grouping Design

Archived for implementation handoff: Phase 5 design was completed in PR 135
(`codex/command-platform-phase-5a-design-docs`), merged, and pushed to production in production PR
444. Phase 5A was later completed in PR 136
(`codex/command-platform-phase-5a-admin-grouping`), smoke tested successfully, merged, and pushed
to production on 2026-06-02. Use
`Codex Chat Starter - Command Platform Phase 6 Canonical Command Documentation.md` for the next
command-platform chat.

This starter is retained as the historical Phase 5 design prompt and source context.

Source programme documents:

- `docs/task_packs/Codex Task Pack - Command Platform Audit & Optimisation Programme.md`
- `docs/task_packs/Codex Task Pack - Command Platform Phase 5 Public Domain Grouping Design.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Phase 4 was completed in PR 134 (`codex/command-platform-phase-4-ark-grouping`), smoke tested
successfully, merged, and pushed to production. Production smoke confirmed:

- `/ops validate_command_cache` remained green after restart
- all 14 Ark commands are grouped under `/ark`
- old flat Ark command paths no longer appear in Discord command discovery
- public `/ark reminder_prefs` and `/ark report_players` work from the grouped path
- leadership/admin Ark commands preserve existing permission behavior
- current validator baseline:

```text
primary=62 grouped_subcommands_detected=43 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=62
```

## Copy/Paste Starter

Codex, begin Phase 5 of the Command Platform Audit & Optimisation Programme: Public Domain
Grouping Design.

This follows the completed Phase 4 Ark grouping PR:

- PR 134: `codex/command-platform-phase-4-ark-grouping`
- Result: smoke tested successfully, merged, pushed to production
- Current validator baseline:

```text
primary=62 grouped_subcommands_detected=43 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=62
```

The objective for this phase is to design the public/player command grouping policy before moving
any additional command paths. Do not move commands in this phase unless explicitly approved after
the design review.

## 1. Task Header

- Task name: Command Platform Phase 5 - Public Domain Grouping Design
- Date: 2026-06-01
- Owner/context: Command Platform Audit & Optimisation Programme
- Task type: deferred optimisation batch / command-surface design
- One-pass approved: no

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
- `docs/task_packs/Codex Task Pack - Command Platform Phase 5 Public Domain Grouping Design.md`
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

This phase should:

- review remaining flat public/player and admin-heavy domain command paths
- distinguish public discoverability-sensitive commands from low-risk admin/operator commands
- propose grouping domains, candidate subcommands, and target paths
- define which public command moves require operator approval and communication
- identify the safest next implementation slice or slices after design approval
- keep the current Phase 4 command baseline unchanged
- update command-platform docs with the approved Phase 5 design and roadmap

## 4. Scope

### In Scope

Review and design grouping policy for:

- Registry commands
- KVK, stats, and player profile commands
- Inventory commands
- Calendar and events commands
- Subscription commands
- CrystalTech, honor, location, activity, and other admin-heavy candidates
- command-platform audit docs
- command-surface audit docs
- deferred optimisation backlog updates
- operator communication notes for public/player command moves
- test and validation recommendations for later implementation phases

### Out Of Scope

- moving any slash command path
- changing command decorators, permissions, options, autocomplete, descriptions, versions, usage
  tracking, command-cache behavior, or command handlers
- SQL schema changes
- runtime code changes except inspection-only findings documented for later approval
- production promotion or deployment

## 5. Mandatory Workflow

1. Review/scope Phase 5 and stop for approval.
2. Map remaining flat command paths by domain, owner module, permission model, and user audience.
3. Review local usage evidence and clearly label any gaps where SQL-backed usage review is needed.
4. Identify documentation and smoke references that would need updates for each proposed path.
5. Present grouping policy and candidate path design.
6. Stop for approval before editing docs beyond the design deliverable or before any runtime work.
7. Update docs/deferred items only after approval.
8. Run documentation-focused validation.

Proceed in one pass only if explicitly approved in the new chat.

## 6. Acceptance Criteria

- [ ] No command paths are moved in Phase 5.
- [ ] Remaining flat commands are classified by domain, audience, permission model, and grouping
      risk.
- [ ] Public/player path moves are explicitly marked approval-gated.
- [ ] Admin-heavy low-risk candidate moves are separated from high-discoverability player commands.
- [ ] Proposed target paths are consistent and discoverable.
- [ ] Operator communication needs are identified for every public/player candidate.
- [ ] Follow-up implementation phase or phases are clearly recommended.
- [ ] Command-platform docs and deferred backlog are updated with the approved design.
- [ ] Validation is run or intentionally skipped with reasons.

## 7. Suggested Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

Codex Security may be skipped for pure documentation/design output. It becomes required before PR
handoff if Phase 5 changes runtime command registration, permissions, public interactions,
SQL/data access, file handling, or restart-sensitive behavior.

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
