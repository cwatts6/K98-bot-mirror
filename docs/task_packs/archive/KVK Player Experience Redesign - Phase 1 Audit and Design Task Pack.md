# KVK Player Experience Redesign — Phase 1 Audit and Design Task Pack

## 1. Task Header

- Task name: `KVK Player Experience Redesign — Phase 1 Audit and Design`
- Date: `2026-06-03`
- Owner/context: K98 Bot player-facing KVK command and visual-output modernisation
- Task type: `architecture / UX audit / command-surface design / deferred optimisation batch`
- One-pass approved: `no`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`.

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

```text
C:\K98-bot-SQL-Server
```

Also read:

- `docs/reference/canonical_command_reference.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/deferred_optimisations.md`
- current KVK-related task packs and completion notes, especially KVK_ALL schema modernisation phases that affect output semantics
- any command-surface audit or balancing documentation available in `docs/`
- any visual/image-generation standards or inventory-output implementation notes available in the repo

## 3. Objective

Audit and design the future KVK player command experience before implementation.

The intended end state is a clean player-facing `/kvk` command group with modern, consistent KVK outputs for stats, targets, history, and rankings, plus a later separation of admin/operator KVK commands away from the player surface.

This phase must produce the design and migration plan only. Do not modify runtime code, SQL, commands, embeds, images, or docs outside the audit/design deliverables unless explicitly approved.

## 4. Background

The current KVK player commands are useful but fragmented and visually dated compared with newer generated-image outputs such as the inventory module.

Current player-facing outputs likely include:

- `/mykvkstats`
- `/mykvktargets`
- `/mykvkhistory`
- `/mygovernorid`
- `/my_stats`
- `/my_stats_export`
- `/player_profile`
- `/player_stats`
- `/kvk_rankings`
- `/honor_rankings`
- PreKVK ranking/report commands

The desired future command model is:

```text
/kvk stats
/kvk targets
/kvk history
/kvk rankings
```

The desired later admin/operator command model is:

```text
/kvk_admin ...
```

The programme should be delivered through parallel migration: build the new `/kvk` group alongside existing commands, validate, soft-launch, then deprecate old paths only after approval.

## 5. Scope

### In Scope

- Audit current KVK player command paths, outputs, usage, permissions, service/DAL dependencies, SQL dependencies, and restart/persistence considerations.
- Audit current KVK admin/operator command paths and propose how they should move away from the player surface later.
- Design the target `/kvk` player command model.
- Design the target visual language for modern KVK outputs.
- Review feasibility of generated image cards for `/kvk stats`, `/kvk targets`, `/kvk history`, and rankings.
- Identify all affected command registration, command-cache, canonical command reference, smoke test, and docs updates.
- Validate metric terminology and source-of-truth concerns before visual redesign.
- Review how KVK_ALL Phase 10/11 source-of-truth and acclaim terminology decisions affect user-facing KVK outputs.
- Produce a phased implementation plan.
- Produce structured deferred optimisation items for any out-of-scope findings.

### Out of Scope

- No command implementation.
- No new `/kvk` command group creation.
- No old command removal or redirect behaviour.
- No generated image/card implementation.
- No SQL schema, procedure, view, function, or migration changes.
- No Google Sheets output contract changes.
- No import/recompute/export behaviour changes.
- No Discord reporting display change.
- No Basic Data or summary tab ingestion.
- No admin command migration implementation.
- No website implementation.

## 6. Source Deferred Items

### Deferred Optimisation
- Area: `commands/registry_cmds.py`, `commands/telemetry_cmds.py`, `commands/stats_cmds.py`, `commands/inventory_cmds.py`, `commands/subscriptions_cmds.py`, `commands/calendar_cmds.py`, player self-service command docs/tests
- Type: architecture
- Description: Player self-service commands are split across development-era entry points rather than designed as complete user workflows. KVK-related commands are high-discoverability and likely high-traffic during KVK.
- Suggested Fix: Scope a dedicated player self-service workflow redesign outside the command-count programme. Review each block as a user journey before choosing command paths. For KVK, evaluate a coherent `/kvk` command group and later admin separation.
- Impact: high
- Risk: medium
- Dependencies: Requires operator approval, SQL-backed usage review, user-facing briefing, and a fresh task pack.

### Programme Refinement

This Phase 1 task narrows the first implementation target to KVK player workflows only, rather than redesigning all player self-service commands at once.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required to map command, service, SQL, image generation, and migration boundaries before implementation. |
| `k98-discord-command-feature` | use | The task designs slash command changes, output UX, buttons/selects, and command-surface migration. |
| `k98-sql-validation` | use | KVK stats, targets, history, rankings, honor, and PreKVK outputs depend on SQL-backed views/procedures/DAL contracts. |
| `k98-test-selection` | use | Required to define Phase 2+ validation strategy and selected test suites. |
| `k98-deferred-optimisation-capture` | use | Audit will likely find out-of-scope command, visual, SQL, or output-shape debt. |
| `k98-pr-review` | use | Use before handoff of the audit/design PR or final design document. |
| `k98-promotion-check` | not applicable | No runtime deployment in this audit-only phase unless documentation is promoted through the normal bot process. |
| `codex-security:security-scan` | use if design PR touches security-sensitive docs or command permissions | No code changes expected, but command permissions and SQL-backed user outputs are security-sensitive in later phases. |

## 8. Mandatory Workflow

This is audit/design only.

1. Read required docs and current command references.
2. Audit command surface and current KVK user journeys.
3. Audit outputs and visual style.
4. Audit service/DAL/SQL dependencies.
5. Audit command registration and command-count implications.
6. Audit existing image-generation helpers and inventory output patterns.
7. Produce a design proposal.
8. Produce a phased delivery plan.
9. Capture deferred optimisations.
10. Stop for approval.

Do not implement runtime changes in this phase.

## 9. Audit Requirements

### 9.1 Current command map

Identify and document:

- current command path
- command file/module
- decorator stack
- permissions
- visibility/public/ephemeral behaviour
- channel restrictions
- autocomplete/options
- service calls
- DAL/SQL dependencies
- output type
- whether the command is player-facing, leadership, admin, operator, or diagnostic
- whether the command belongs in future `/kvk`, `/kvk_admin`, another existing group, or should remain unchanged

Minimum commands to search:

```text
/mykvkstats
/mykvktargets
/mykvkhistory
/mygovernorid
/my_stats
/my_stats_export
/player_profile
/player_stats
/kvk_rankings
/honor_rankings
/prekvk*
/kvk_recompute
/kvk_export_all
/kvk_list_scans
/kvk_window_preview
```

### 9.2 Player journey audit

Map the current and target journeys for:

- player checks personal KVK performance
- player checks targets
- player checks historical KVK performance
- player checks rankings
- player looks up governor ID
- player switches between linked governors
- player uses buttons from one KVK command to another
- leadership/admin checks KVK operational status

### 9.3 Output audit

For each relevant command, document:

- current output format
- current fields/metrics
- field names and terminology
- embed/image style
- whether output is clear to players
- whether output is too dense
- whether output should remain embed-first or become image-card-first
- whether buttons/dropdowns should be added
- whether the command output can be reused for website cards later

Include screenshots or text captures where available.

### 9.4 Visual architecture audit

Search for and review existing generated-image or card output code, especially inventory-related output.

Document:

- existing image-generation libraries/helpers
- reusable card primitives
- whether image generation is synchronous or async-safe
- file cleanup behaviour
- caching/reuse opportunities
- test strategy for generated images
- Discord attachment behaviour
- dark-mode/light-mode considerations
- fallback behaviour if image generation fails

### 9.5 Metric and terminology audit

Review current KVK metric terminology and source-of-truth rules, including:

- KP gain
- KP loss, if available
- power gain/loss
- deads
- DKP
- healed
- honor
- PreKVK points
- pass-window values
- acclaim/contribution terms
- tanking score or equivalent score if proposed
- playstyle labels, if proposed

Do not introduce new labels such as `tanking score`, `KP loss`, or `playstyle` into player outputs unless the underlying data source, formula, and player meaning are defined and approved.

### 9.6 SQL and DAL dependency audit

Validate against the SQL repo:

```text
C:\K98-bot-SQL-Server
```

At minimum identify dependencies for:

- personal KVK stats
- KVK targets
- KVK history
- KVK rankings
- honor rankings
- PreKVK rankings/reporting
- player profile/current stats
- governor ID lookup

Document:

- SQL objects used
- Python DAL/service paths
- whether direct SQL exists in command/view layers
- whether a DAL/service exists and can be reused
- missing DAL/service boundaries
- output-shape dependencies
- performance concerns
- cache usage

### 9.7 Command registration and migration audit

Document:

- whether adding `/kvk` changes top-level command count
- whether `/kvk` already exists
- whether `/kvk_admin` already exists or should be later grouped under another existing admin command
- updates needed for `scripts/validate_command_registration.py`
- updates needed for `canonical_command_reference.md`
- command-cache impacts
- smoke test impacts
- Discord alias limitations
- old-command deprecation plan

### 9.8 Risk audit

Assess:

- active KVK operational risk
- player confusion risk
- command discoverability risk
- data accuracy/metric semantics risk
- command-count risk
- permission regression risk
- performance risk for generated images
- restart/persistence risk for buttons/views
- rollout/deprecation risk

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | `commands/kvk_cmds.py` or approved existing command module |
| KVK admin commands | future `commands/kvk_admin_cmds.py` or approved admin/operator group |
| Views/buttons/selects | `ui/views/` |
| Services/business logic | `kvk/services/` or existing stats/target services |
| DAL/SQL access | `kvk/dal/`, stats DAL, target DAL, or approved existing repository layer |
| Generated image/card helpers | shared visual/card module, not embedded in command handlers |
| Documentation | `docs/` and canonical command reference |
| SQL validation | `C:\K98-bot-SQL-Server` |
| Tests | `tests/` focused command/service/image tests |

## 11. Likely Files

### Review

- `commands/stats_cmds.py`
- `commands/registry_cmds.py`
- `commands/telemetry_cmds.py`
- `commands/calendar_cmds.py`
- `commands/events_cmds.py`
- `kvk/`
- `stats_alerts/`
- `target_utils.py`
- `governor_registry.py`
- `player_stats_cache.py`
- `account_picker.py`
- `ui/views/`
- `embed_utils.py`
- `image_utils` or inventory image/card modules if present
- `scripts/validate_command_registration.py`
- `tests/test_command_inventory.py`
- `tests/test_command_registration_smoke.py`
- `docs/reference/canonical_command_reference.md`
- SQL repo KVK, honor, PreKVK, player-profile, and target objects

### Modify

- Documentation/design outputs only, if this phase is committed to the repo.

### Create

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/task_packs/KVK Player Experience Redesign - Phase 1 Audit and Design Task Pack.md`
- optional audit output under `reports/` or `docs/reports/` if repo conventions support it

## 12. Implementation Requirements

This phase has no runtime implementation.

The audit/design output must include:

1. Executive summary.
2. Current command inventory.
3. Current player journey map.
4. Proposed `/kvk` command model.
5. Proposed `/kvk_admin` or admin/operator separation model.
6. Output/visual audit.
7. Metric and terminology review.
8. SQL/DAL/service dependency map.
9. Image-generation feasibility review.
10. Migration/deprecation strategy.
11. Phase 2 implementation recommendation.
12. Risks and mitigations.
13. Test strategy for later phases.
14. Structured deferred optimisations.

### Command Surface Governance

- [ ] State whether the future task changes top-level command count, grouped subcommand count, or neither.
- [ ] Confirm whether `/kvk` already exists.
- [ ] Confirm whether `/kvk_admin` should be a new top-level group, part of an existing admin group, or deferred.
- [ ] Record command-count impact and approval requirements.
- [ ] Identify updates required to command registration validation and canonical command docs.
- [ ] Preserve or explicitly update `@versioned()`, `@safe_command`, `@track_usage()`, permission decorators, response visibility, autocomplete/options, usage-log identity, and command-cache behavior in future phases.

## 13. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| Existing KVK player commands fragmented across multiple paths | design now | Core objective of programme. |
| Current old-style KVK embeds | design now, implement later | Need agreed visual architecture first. |
| Admin KVK commands mixed with player-facing naming | design now, implement later | Should not be mixed into Phase 2 scaffold unless approved. |
| Direct SQL in commands/views, if found | fix later or defer with severity | Phase 1 is audit only. |
| Missing tests/output shape coverage | plan later | Implementation phases should add focused tests. |

Add further rows based on actual audit findings.

## 14. Testing Requirements

This phase is audit/design only. No runtime tests are required unless Codex changes repository docs and the repo enforces documentation checks.

However, the audit must define the test plan for Phase 2 and later, including:

- command registration validation
- command inventory tests
- focused `/kvk` command tests
- permission boundary tests
- old/new command parity tests
- output-shape tests
- visual image generation tests
- service/DAL regression tests
- SQL contract validation where applicable

Suggested commands to run if documentation-only changes still go through PR validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

## 15. Acceptance Criteria

- [ ] Current KVK player command surface is fully mapped.
- [ ] Current KVK admin/operator command surface is fully mapped.
- [ ] Target `/kvk` player command model is proposed.
- [ ] Target admin separation model is proposed.
- [ ] Current outputs and visual gaps are documented.
- [ ] Modern visual direction and image-card architecture are proposed.
- [ ] KVK metric and terminology risks are documented.
- [ ] SQL/DAL/service dependencies are mapped.
- [ ] Command registration and command-count implications are documented.
- [ ] Parallel migration and deprecation strategy is documented.
- [ ] Phase 2 implementation plan is ready.
- [ ] Out-of-scope findings are captured structurally.
- [ ] No runtime code or SQL was changed.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. Current Command Inventory
3. Player Journey Audit
4. Admin/Operator Command Audit
5. Output and Visual Audit
6. Metric and Terminology Review
7. SQL/DAL/Service Dependency Map
8. Image Generation Feasibility Review
9. Target Command Model
10. Migration and Deprecation Plan
11. Phase 2 Recommendation
12. Test Strategy
13. Risks and Mitigations
14. Deferred Optimisations
15. Approval Questions

## 17. PR Summary Template

```md
## Summary

- Completed audit/design for the KVK Player Experience Redesign programme.
- Proposed target `/kvk` command model and later admin separation.
- Documented output, visual, SQL, and command-registration dependencies.

## Changes

- Added/updated KVK Player Experience Redesign design documentation.

## Tests

- Documentation-only change; runtime tests not required.
- Command registration/deferred validation run if applicable: <commands/results>.

## AI Review Gates

- Codex Security: skipped for documentation-only audit, or run if repository policy requires.

## Deferred Optimisations

- <structured items or none>

## Risk / Rollback

- Documentation-only; rollback by reverting docs.
```
