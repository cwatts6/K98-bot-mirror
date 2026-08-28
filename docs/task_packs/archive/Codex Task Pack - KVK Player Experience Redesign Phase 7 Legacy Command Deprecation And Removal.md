# Codex Task Pack - KVK Player Experience Redesign Phase 7 Legacy Command Deprecation And Removal

## 1. Task Header

- Task name: `KVK Player Experience Redesign - Phase 7 Legacy Command Deprecation And Removal`
- Date: `2026-06-20`
- Owner/context: `K98 Bot KVK Player Experience Redesign after Phase 6 admin hardening closeout`
- Task type: `deferred optimisation batch / command rollout / deprecation planning`
- One-pass approved: `no`
- Status: `complete; tested; awaiting PR merge/promotion; archived 2026-06-22`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`

Also read:

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- `docs/reference/archive/deferred_optimisations_resolved.md`

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

`C:\K98-bot-SQL-Server`

Do not infer ranking, history, honor, PreKvK, telemetry, or usage-review SQL contracts from
Python-only usage where SQL definitions exist.

## 3. Objective

Prepare and execute the approved legacy player command transition after the modern `/kvk` command
surface has completed rollout validation. The approved Phase 7 slice changed retained legacy paths
into redirect/help responses, aligned the canonical `/kvk` command channel limits, and deferred
final command removal until after the agreed no-feedback window.

## 4. Background

Phase 5 delivered the unified `/kvk rankings` browser and visual ranking cards for current KVK,
Honor, PreKvK, and Hall of Fame records. Phase 6 then hardened `/kvk_admin` and closed the active
admin/operator development phase.

Legacy player paths intentionally remained live before Phase 7:

```text
/mykvkstats
/mykvktargets
/mykvkhistory
/kvk_rankings
/honor_rankings
/prekvk report
```

Phase 7 converted these paths into temporary deprecated redirect/help responses to the canonical
`/kvk` command group. The final removal of these paths is intentionally a later cleanup after
player communication, the no-feedback window, and operator approval.

## 5. Scope

### In Scope

- Audit current usage evidence for `/kvk_rankings`, `/honor_rankings`, and `/prekvk report`.
- Confirm the operator-approved transition strategy for each legacy path:
  redirect/help response, compatibility shim, retained legacy path, or removal after announcement.
- Preserve the unified `/kvk rankings` behaviour, ranking semantics, CSV export, My Rank, Top 10
  visual cards, Top 25/50 compact output, and Hall of Fame records semantics.
- Align canonical `/kvk` channel limits so `/kvk targets` uses the KVK targets channel and
  `/kvk stats`, `/kvk history`, and all `/kvk rankings` types use the KVK stats channel, all with
  admin override.
- Replace image-based `/prekvk report` execution with a redirect/help response unless an explicit
  approved Phase 7 decision changes it.
- Update canonical command reference docs, user/operator docs, smoke-test references, and rollout
  messaging for any command transition.
- Add or update focused command, service, view, and command-registration tests for changed paths.
- Capture any out-of-scope command-surface or ranking cleanups structurally.

### Out of Scope

- Changing ranking calculations, SQL output contracts, import/export/recompute behaviour, stats
  cache behaviour, or Google Sheets contracts.
- Changing `/kvk stats`, `/kvk targets`, `/kvk history`, or `/kvk_admin` output semantics.
- Adding new top-level commands or command groups.
- Reintroducing Top 100 as a primary player browser control.
- Replacing the legacy image-based `/prekvk report` without explicit operator approval.
- Removing any legacy command before redirect monitoring, the no-feedback window, and operator
  approval are recorded.
- Production promotion or bot deployment work beyond documenting validation and rollback.

## 6. Source Deferred Items

Promoted from `docs/reference/deferred_optimisations.md` during Phase 6 closeout:

```md
### Deferred Optimisation
- Area: `build_KVKrankings_embed.py`, `ui/views/stats_views.py`, `honor_rankings_view.py`, `commands/stats_cmds.py`, legacy player ranking command compatibility paths
- Type: refactor
- Description: Phase 5 intentionally preserved the legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` paths during rollout. With Phase 5 complete, the legacy KVK and Honor ranking commands still retain older builders/views and duplicated presentation semantics while the unified `/kvk rankings` path uses the shared current-ranking payload/browser foundation. This is tracked as future Phase 7 rollout/deprecation work, not remaining Phase 5 delivery debt.
- Suggested Fix: After the unified browser has production usage evidence, scope the approved Phase 7 legacy-ranking consolidation or deprecation phase. Decide whether flat legacy commands should redirect to the unified service/renderer, remain as compatibility shims, or be retired with announcement support; preserve image-based `/prekvk report` unless a later approved visual phase replaces it.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5 completion, command usage telemetry, user-facing rollout messaging, operator approval for Phase 7, and focused regression tests for each retained legacy path.
```

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation; identify command/service/view/docs boundaries, usage-review needs, SQL implications, and approval checkpoints. |
| `k98-discord-command-feature` | use | Legacy slash commands, grouped replacement paths, embeds, views, permissions, response visibility, and command registration are in scope. |
| `k98-sql-validation` | use conditionally | Required if usage telemetry, ranking SQL/DAL, history SQL, honor SQL, PreKvK SQL, or command usage queries are touched. |
| `k98-test-selection` | use | Required for focused tests, validators, and command-registration gates. |
| `k98-deferred-optimisation-capture` | use | Required for any out-of-scope ranking, command, docs, view, or service cleanup findings. |
| `k98-pr-review` | use before merge | Use for merge-readiness, architecture, command-surface, docs, tests, and deferred-item review. |
| `k98-promotion-check` | use before production promotion | Required before production PR/merge/deploy. |
| `codex-security:security-scan` | use if risk triggers apply | Likely required because command routing, permissions, Discord interactions, and user-controlled command inputs may change. |

## 8. Mandatory Workflow

1. Start with audit/scope only and stop for operator approval.
2. Present usage evidence and a per-command recommendation for `/kvk_rankings`, `/honor_rankings`,
   and `/prekvk report`.
3. Record the approved transition strategy before implementation.
4. Validate SQL-facing assumptions if telemetry or ranking data access is touched.
5. Implement only the approved PR-sized slice.
6. Update command docs, smoke references, and rollout messaging.
7. Run focused tests, standard validators, command-registration gates, and pre-commit.
8. Run Codex Security or document a clear skip reason.
9. Open a ready-for-review PR against `K98-bot-mirror` only after validation.

## 9. Audit Requirements

Audit the touched area for:

- current command usage and user-facing reliance on each legacy path
- permission and channel behaviour differences between legacy paths and `/kvk rankings`
- direct SQL in command handlers or Discord views
- duplicate ranking formatting, builders, views, or near-duplicate helpers
- stale legacy docs, smoke tests, operator notes, and command reference entries
- command registration impact and approved top-level command baseline changes
- Discord response length, ephemeral/public visibility, and interaction safety
- test coverage gaps for legacy redirects, compatibility shims, or removed paths
- rollout/announcement needs before user-visible command changes

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | Existing command modules only unless a scoped extraction is approved. |
| Unified ranking orchestration | Existing `kvk` ranking services and payload builders. |
| Legacy compatibility | Thin command-level redirects/help or service-backed compatibility shims, depending on approval. |
| Views / controls | Existing `ui/views/` ranking browser/view modules where applicable. |
| Documentation | `docs/reference/canonical_command_reference.md`, programme pack, smoke references, user/operator notes. |
| SQL schema | SQL repo `C:\K98-bot-SQL-Server` if usage telemetry or ranking SQL contracts are touched. |
| Tests | Focused command, ranking service/view, command inventory, and command registration tests. |

## 11. Likely Files

### Review

- `commands/stats_cmds.py`
- `build_KVKrankings_embed.py`
- `honor_rankings_view.py`
- `ui/views/stats_views.py`
- `ui/views/kvk_rankings_views.py`
- `kvk/services/kvk_rankings_service.py`
- `kvk/rendering/kvk_rankings_embed.py`
- `kvk/rendering/kvk_rankings_card_renderer.py`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- ranking and command-registration tests

### Modify

- To be determined after audit and operator approval.

### Create

- To be determined after audit. Prefer extending existing tests unless a distinct Phase 7 test file
  is clearer.

## 12. Implementation Requirements

- Preserve `/kvk rankings` as the canonical player ranking surface.
- Keep commands and views thin; put ranking semantics in existing services/renderers.
- Avoid new direct SQL in commands or views.
- Preserve the approved canonical `/kvk` channel limits.
- Preserve player-visible output semantics unless the approved transition strategy explicitly
  changes a legacy path.
- Preserve command registration governance and update baselines/docs only if an approved command
  removal changes them.
- Include user-facing redirect/help wording where commands are deprecated but not removed.
- Capture any new cleanup findings using the deferred optimisation format.

### Command Surface Governance

- [ ] State whether the task changes top-level command count, grouped subcommand count, or neither.
- [ ] Do not remove legacy command paths until operator approval, usage review, and announcement or
  redirect/help policy are recorded.
- [ ] If a top-level command is retired, update
  `scripts/validate_command_registration.py::APPROVED_TOP_LEVEL_COMMANDS`,
  `docs/reference/canonical_command_reference.md`, smoke references, user/operator docs, and
  command inventory tests.
- [ ] Preserve or explicitly update `@versioned()`, `@safe_command`, `@track_usage()`, permission
  decorators, response visibility, autocomplete/options, usage-log identity, and command-cache
  behaviour.
- [ ] Run or justify skipping `scripts/validate_command_registration.py`,
  `tests/test_validate_command_registration.py`, `tests/test_command_inventory.py`, and
  `tests/test_command_registration_smoke.py`.

## 13. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| `/kvk_rankings` legacy path duplicates unified ranking semantics | `fix now | retain | defer` | Decide after usage review and operator approval. |
| `/honor_rankings` legacy path duplicates unified ranking semantics | `fix now | retain | defer` | Preserve approved `/kvk rankings` channel gate regardless of strategy. |
| `/prekvk report` remains image-based legacy flow | `fix now | retain | defer` | Preserve unless an explicit approved visual/transition decision changes it. |
| Stale docs or smoke references describe legacy commands as preferred | `fix now | defer | not applicable` | Update when a transition strategy is approved. |

Deferred items must use the structured format from
`docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 14. Testing Requirements

Consider each category and either cover it or explain why it does not apply:

- happy path for each changed legacy command
- redirect/help or compatibility-shim output shape
- permission and channel boundary preservation for `/kvk targets`, `/kvk stats`, `/kvk history`, and all `/kvk rankings` types
- public/private response visibility
- command registration and command inventory
- service/renderer delegation and no command/view SQL
- regression coverage for `/kvk rankings` current modes, records, My Rank, CSV export, and Top
  10/25/50 output where touched
- docs-only validation if the approved slice is planning/docs only

Suggested baseline commands after audit, adapt to actual files changed:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_inventory.py tests\test_command_registration_smoke.py
.\.venv\Scripts\python.exe -m pre_commit run -a
```

Add focused ranking command/service/view tests based on the approved implementation path. Run full
tests before merge/promotion if runtime is practical:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

## 15. Acceptance Criteria

- [ ] Usage evidence and operator approval are recorded before implementation.
- [x] Each legacy path has an explicit approved strategy: redirect/help, compatibility shim,
  retained legacy path, or removal after announcement.
- [x] `/kvk rankings` remains the canonical player ranking surface.
- [x] Ranking semantics, SQL contracts, My Rank, CSV export, visual Top 10 cards, compact Top
  25/50 output, and Hall of Fame records semantics are preserved unless explicitly approved.
- [x] Canonical `/kvk` channel limits are aligned and tested.
- [x] No new direct SQL exists in command or view modules.
- [x] Command registration docs/tests/baselines are updated for any approved command-surface
  change.
- [x] User/operator docs and smoke references match the delivered command surface.
- [x] Focused tests and standard validators pass.
- [x] Codex Security was considered during PR preparation; no additional scan was required for this documentation-only closeout.
- [x] Out-of-scope findings are captured structurally.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Usage Review / Approval Record
7. Command Surface Changes
8. User-Visible Behaviour Changes
9. Helpers Reused
10. Refactor Findings
11. Test Plan and Results
12. AI Review Gates
13. Deployment Steps
14. Rollback Plan
15. Deferred Optimisations

For documentation-only work, state that no runtime code, SQL, helper reuse, or restart behaviour
changed.

## 17. Completion Record

### Summary

Phase 7 delivered the approved deprecation/redirect rollout for the legacy KVK player command
paths. The old commands remain registered only to guide players to the canonical `/kvk` commands.
Final removal is explicitly deferred until after the agreed no-feedback window.

### Delivered

- `/mykvkstats` redirects to `/kvk stats`.
- `/mykvktargets` redirects to `/kvk targets`.
- `/mykvkhistory` redirects to `/kvk history`.
- `/kvk_rankings` redirects to `/kvk rankings type:kvk`.
- `/honor_rankings` redirects to `/kvk rankings type:honor`.
- `/prekvk report` redirects to `/kvk rankings type:prekvk` and tells players to use the KVK
  stats channel.
- Inline legacy implementation blocks were removed from the redirect-only handlers.
- Deprecation wording was made neutral for both report and non-report commands.
- Canonical `/kvk` command channel limits were aligned:
  - `/kvk targets` uses `KVK_TARGET_CHANNEL_ID` with admin override.
  - `/kvk stats`, `/kvk history`, and all `/kvk rankings` types use
    `KVK_PLAYER_STATS_CHANNEL_ID` with admin override.
- Player briefing, canonical command reference, and relevant active docs were updated.

### Validation

- Full pytest passed: `1820 passed, 2 skipped`.
- Pre-commit passed.
- Architecture boundary validation passed.
- Deferred optimisation validation passed.
- `scripts/select_tests.py` was run.
- Smoke imports passed.
- Command registration validation passed.
- User-reported Discord smoke testing confirmed old command redirects and new-command channel
  consistency.

### Deferred Optimisations

Final removal of the temporary deprecated command paths is captured in
`docs/reference/deferred_optimisations.md` and should run only after the no-feedback window and
operator approval.

## 18. PR Summary Template

```md
## Summary

- Transitioned approved legacy KVK ranking command paths for Phase 7.
- Preserved `/kvk rankings` as the canonical player ranking surface.

## Changes

- <command/service/view/docs/test changes>

## Usage Review / Approval

- <usage evidence and operator approval summary>

## SQL Changes

- None, or list validated SQL-facing changes and companion SQL PR/deployment order.

## Tests

- <focused pytest/validators/manual smoke checks>

## AI Review Gates

- Codex Security: <run | skipped, with reason>

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Risk: legacy ranking command changes are player-visible and may affect command discoverability.
- Mitigation: preserve `/kvk rankings`, use redirect/help or compatibility shims where approved,
  update docs/smoke references, and smoke test in Discord before deployment.
- Rollback: revert the Phase 7 implementation commit/PR to restore the previous legacy command
  behaviour; `/kvk rankings` remains live.
```
