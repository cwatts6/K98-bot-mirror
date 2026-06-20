# Codex Task Pack - KVK Player Experience Redesign Phase 6 Admin Command Hardening And Legacy Operator Cleanup

## 1. Task Header

- Task name: `KVK Player Experience Redesign - Phase 6 Admin Command Hardening And Legacy Operator Cleanup`
- Date: `2026-06-20`
- Owner/context: `K98 Bot KVK Player Experience Redesign after Phase 5 rankings closure`
- Task type: `audit / command hardening / refactor / documentation cleanup`
- One-pass approved: `no`
- Status: `complete; delivered in mirror PR #162 and production PR #470; archived 2026-06-20`

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
- `docs/reference/runbook_structure.md` if repo-navigation context is needed
- `docs/reference/REVIEW_HELPERS.md` if shared helper cleanup is proposed

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

`C:\K98-bot-SQL-Server`

Do not infer KVK admin SQL contracts from Python-only usage where SQL definitions exist.

## 3. Objective

Harden the delivered `/kvk_admin` operator command surface now that the player `/kvk` journey is
modernised through Phase 5. The phase should make the admin/operator commands easier to maintain
and safer to operate without changing KVK import, recompute, export, Google Sheets, ranking, stats,
targets, history, or player-facing behaviour.

Completed as the final active development hardening phase before rollout/deprecation work.
Implementation stayed within the approved PR-sized Phase 6 scope.

## 4. Background

Phase 2A moved the former admin/operator `/kvk ...` commands to `/kvk_admin ...` before the player
`/kvk` scaffold was introduced. Phase 2B through Phase 5 then delivered the player command group:

```text
/kvk stats
/kvk targets
/kvk history
/kvk rankings
```

The active admin/operator surface is:

```text
/kvk_admin test_export
/kvk_admin refresh_stats_cache
/kvk_admin recompute
/kvk_admin export_all
/kvk_admin list_scans
/kvk_admin window_preview
/kvk_admin test_embed
```

These commands live in `commands/stats_cmds.py` and mostly delegate to
`kvk.services.kvk_admin_service`, `kvk.dal.kvk_admin_dal`, `gsheet_module.py`, and existing stats
cache/export helpers. Earlier KVK_ALL modernisation work moved significant KVK admin data access
into service/DAL boundaries, but Phase 6 should audit the remaining command bodies, error handling,
logging, operator output, tests, and stale docs/smoke references as a coherent operator-hardening
pass.

Phase 5 is complete. The only active deferred item with ranking language is the future
legacy-ranking consolidation/deprecation item, which belongs to Phase 7 because legacy ranking
commands intentionally remain live during rollout.

## 5. Scope

### In Scope

- Audit all `/kvk_admin` command handlers in `commands/stats_cmds.py`.
- Preserve and verify permission decorators, channel restrictions, `@versioned()`, `@safe_command`,
  `@track_usage()`, deferral behaviour, and response visibility.
- Check that command handlers stay thin and delegate business logic/data access to services/DAL.
- Review `kvk.services.kvk_admin_service` and `kvk.dal.kvk_admin_dal` for remaining low-risk
  hardening opportunities connected to command safety, result shaping, logging, and testability.
- Review KVK admin operator output for clear user-visible errors, predictable success messages,
  Discord length limits, and stale legacy command names in logs/messages.
- Clean up stale documentation, task-pack, smoke-test, or operator references to removed admin
  paths such as `/kvk recompute`, `/kvk export_all`, `/kvk list_scans`, `/kvk window_preview`,
  `/kvk test_export`, and `/kvk test_embed` where those references are not intentionally historical.
- Update `docs/reference/canonical_command_reference.md` only if visible command docs or operator
  notes need correction.
- Add or update focused tests around changed command hardening and service/DAL boundaries.
- Capture out-of-scope findings structurally.

### Out of Scope

- Changing player `/kvk stats`, `/kvk targets`, `/kvk history`, or `/kvk rankings` behaviour.
- Removing, redirecting, or deprecating legacy player ranking commands. That belongs to Phase 7.
- Changing KVK import/recompute/export semantics, Google Sheets tab names, stored procedure
  contracts, SQL output contracts, stats cache semantics, or ranking semantics.
- Adding new top-level commands or new command groups.
- Moving `/kvk_admin` under `/ops` unless a separate command-surface task explicitly approves it.
- Changing Honor no-admin-override player-ranking gate behaviour.
- Replacing the image-based legacy `/prekvk report`.
- Production promotion or deployment steps beyond documenting validation and rollback.

## 6. Source Deferred Items

This phase is programme-driven rather than sourced from one active deferred item.

Related but out-of-scope active deferred item:

```md
### Deferred Optimisation
- Area: `build_KVKrankings_embed.py`, `ui/views/stats_views.py`, `honor_rankings_view.py`, `commands/stats_cmds.py`, legacy ranking commands
- Type: refactor
- Description: Phase 5B preserves the legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` paths during rollout. The legacy KVK and Honor ranking commands therefore still retain older builders/views and duplicated presentation semantics while the unified `/kvk rankings` path uses the shared current-ranking payload/browser foundation.
- Suggested Fix: After the unified browser has production usage evidence, scope a dedicated legacy-ranking consolidation or deprecation phase. Decide whether flat legacy commands should redirect to the unified service/renderer, remain as compatibility shims, or be retired with announcement support; preserve image-based `/prekvk report` unless a later approved visual phase replaces it.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5B production smoke results, command usage telemetry, user-facing rollout messaging, and focused regression tests for each retained legacy path.
```

Do not implement that item in Phase 6 unless the operator explicitly expands scope.

Phase 6 closeout note: the related legacy-ranking deferred item was not implemented in this phase.
It has been promoted into the Phase 7 task pack and removed from the active deferred optimisation
backlog. No active Phase 6 admin/operator deferred optimisations remain.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation; identify command/service/DAL/docs boundaries and approval checkpoints. |
| `k98-discord-command-feature` | use | `/kvk_admin` slash commands, permission decorators, response visibility, and command registration are in scope. |
| `k98-sql-validation` | use conditionally | Required if implementation touches SQL-facing service/DAL queries, procedures, output contracts, or cache/export contracts. |
| `k98-test-selection` | use | Required for focused tests, validators, and command-registration gates. |
| `k98-deferred-optimisation-capture` | use | Required for any out-of-scope command, service, DAL, docs, or legacy cleanup findings. |
| `k98-pr-review` | use before merge | Use for merge-readiness, architecture, tests, command-surface, and deferred-item review. |
| `k98-promotion-check` | use before production promotion | Required if Phase 6 changes are promoted to production. |
| `codex-security:security-scan` | use if risk triggers apply | Likely required for command/permission/operator-flow changes unless implementation is docs-only or purely mechanical. |

## 8. Mandatory Workflow

1. Start with audit/scope and stop for approval.
2. Confirm whether Phase 6 should be one PR or split into smaller slices.
3. Validate SQL-facing assumptions if service/DAL code or embedded SQL is touched.
4. Implement only the approved slice.
5. Add/update focused tests and docs.
6. Run focused tests, standard validators, command-registration gates, and pre-commit.
7. Run or explicitly justify skipping Codex Security.
8. Open a ready-for-review PR against `K98-bot-mirror`.

## 9. Audit Requirements

Audit the touched area for:

- direct SQL in command handlers or Discord views
- command handlers containing business logic that should live in services
- stale legacy command names in logs, tests, smoke references, or docs
- weak exception handling or user-visible failure messages
- missing or inconsistent operator audit logging
- Discord response length and embed field limits
- command registration drift or stale canonical command docs
- duplicate formatting/helpers that should be reused
- SQL/cache/export assumptions that require SQL repo validation
- tests that describe obsolete `/kvk ...` admin paths instead of `/kvk_admin ...`

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | `commands/stats_cmds.py` for existing `/kvk_admin` registration unless an approved extraction is scoped. |
| KVK admin orchestration | `kvk/services/kvk_admin_service.py` |
| KVK admin SQL/data access | `kvk/dal/kvk_admin_dal.py` |
| Existing export/cache helpers | Reuse established helpers; do not duplicate Google Sheets/export logic. |
| Documentation | `docs/reference/canonical_command_reference.md`, task packs, smoke references, and operator docs where applicable. |
| Tests | `tests/test_stats_cmds.py`, `tests/test_kvk_admin_service.py`, command-registration tests, and focused SQL contract tests if touched. |

## 11. Likely Files

### Review

- `commands/stats_cmds.py`
- `kvk/services/kvk_admin_service.py`
- `kvk/dal/kvk_admin_dal.py`
- `tests/test_stats_cmds.py`
- `tests/test_kvk_admin_service.py`
- `tests/test_validate_command_registration.py`
- `tests/test_command_inventory.py`
- `tests/test_command_registration_smoke.py`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- task-pack, runbook, smoke-test, and operator docs containing KVK admin command references

### Modify

- To be determined after audit.

### Create

- To be determined after audit. Prefer extending existing tests unless a distinct Phase 6 test file
  is clearer.

## 12. Implementation Requirements

- Preserve all existing `/kvk_admin` command names unless a later approved command-surface task says
  otherwise.
- Preserve admin notify-channel permission model and response visibility.
- Preserve KVK import/recompute/export and Google Sheets semantics.
- Keep command handlers thin: validate/defer/call service/render response.
- Keep data access in service/DAL layers; do not add new direct SQL to commands or views.
- Preserve command registration baseline and canonical command documentation.
- Prefer existing helpers for Discord content splitting, embed formatting, file/export handling,
  logging, and safe interactions.
- Capture out-of-scope legacy cleanup or architecture work using the Deferred Optimisation format.

### Command Surface Governance

- [ ] State whether the task changes top-level command count, grouped subcommand count, or neither.
- [ ] Preserve `/kvk_admin` as the existing operator command group.
- [ ] Do not add a new top-level command.
- [ ] Do not move `/kvk_admin` under `/ops` without separate approval.
- [ ] Preserve or explicitly update `@versioned()`, `@safe_command`, `@track_usage()`, permission
  decorators, response visibility, autocomplete/options, usage-log identity, and command-cache
  behaviour.
- [ ] Update `docs/reference/canonical_command_reference.md` if visible command docs or operator
  notes change.
- [ ] Run or justify skipping `scripts/validate_command_registration.py`,
  `tests/test_validate_command_registration.py`, `tests/test_command_inventory.py`, and
  `tests/test_command_registration_smoke.py`.

## 13. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| `/kvk_admin` command handler contains logic that belongs in service/DAL | `fix now | defer | not applicable` | Decide after audit. |
| Stale legacy `/kvk ...` admin references remain in active docs/tests/log messages | `fix now | defer | not applicable` | Fix active/current references; preserve historical references in archived execution records unless misleading. |
| KVK admin SQL assumptions are unclear | `fix now | defer | not applicable` | Validate against `C:\K98-bot-SQL-Server` before code changes. |
| Legacy player ranking command consolidation item | `defer` | Future Phase 7 rollout/deprecation work, not Phase 6 admin hardening. |

Deferred items must use the structured format from
`docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 14. Testing Requirements

Consider each category and either cover it or explain why it does not apply:

- happy path for each changed `/kvk_admin` command
- negative path or exception handling for changed command/service flows
- permission/channel boundary preservation
- command registration unchanged
- service/DAL delegation and no command-layer SQL
- Discord output shape/length where messages or embeds change
- SQL contract tests if service/DAL queries change
- docs-only validation when only references are cleaned

Suggested focused commands after audit, adapt to actual files changed:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_stats_cmds.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_admin_service.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_inventory.py tests\test_command_registration_smoke.py
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
```

Run full tests before merge/promotion if runtime is practical:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

## 15. Acceptance Criteria

- [ ] `/kvk_admin` command surface is audited and a PR-sized implementation slice is approved before coding.
- [ ] Existing permissions, channel restrictions, response visibility, versions, usage tracking, and command registration are preserved.
- [ ] Commands remain thin and delegate business/data logic to services/DAL.
- [ ] No new direct SQL exists in command or view modules.
- [ ] SQL-facing assumptions are validated against `C:\K98-bot-SQL-Server` if touched.
- [ ] Operator-facing success and failure messages remain clear and Discord-safe.
- [ ] Stale current docs/tests/smoke references to removed admin `/kvk ...` paths are cleaned or explicitly preserved as historical context.
- [ ] Player `/kvk` behaviour, Phase 5 rankings, My Rank, CSV export, legacy ranking commands, and image-based legacy `/prekvk report` are unchanged.
- [ ] Focused tests and standard validators pass.
- [ ] Codex Security is run or explicitly justified.
- [ ] Out-of-scope findings are captured structurally.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Command Surface Changes
7. User-Visible Behaviour Changes
8. Helpers Reused
9. Refactor Findings
10. Test Plan and Results
11. AI Review Gates
12. Deployment Steps
13. Rollback Plan
14. Deferred Optimisations

For documentation-only work, state that no runtime code, SQL, helper reuse, or restart behaviour
changed.

## 17. Completion Record

### Summary

Phase 6 hardened the `/kvk_admin` operator command boundary without changing the visible command
surface, SQL contracts, Google Sheets contracts, import/recompute/export semantics, player `/kvk`
flows, or legacy player ranking paths.

### Delivered

- Kept `/kvk_admin` at the existing seven subcommands.
- Moved admin export, cache-refresh, export-all, scan/window support, and test-embed context
  shaping into `kvk.services.kvk_admin_service`.
- Preserved command-layer ownership for Discord deferral, permissions, service calls, and response
  rendering.
- Added service result models and focused tests for export orchestration, cache-refresh outcomes,
  current-KVK resolution, zero-count cache-build counts, and test-embed routing.
- Preserved cache-builder traceback logging while returning readable operator outcomes.
- Resolved current KVK before export-all progress output.
- Passed computed `is_kvk` through the test-embed send path.
- Cleaned active operator docs for stale removed admin `/kvk ...` command references.

### Validation

- Focused pytest for `tests/test_stats_cmds.py` and `tests/test_kvk_admin_service.py`.
- Command registration validation.
- Architecture and deferred-item validators.
- `scripts/select_tests.py`.
- Pre-commit.
- Full pytest during Phase 6 PR preparation.
- Codex Security diff review during Phase 6 PR preparation.
- User-reported manual Discord smoke tests completed successfully before closeout.

### Deferred Optimisations

No active Phase 6 admin/operator deferred optimisations remain. The legacy player ranking
consolidation/deprecation item has been promoted into Phase 7 and is no longer listed as active
backlog.

## 18. PR Summary Template

```md
## Summary

- Hardened the `/kvk_admin` operator command surface according to the approved Phase 6 scope.
- Preserved player `/kvk` behaviour and all existing KVK import/recompute/export semantics.

## Changes

- <command/service/DAL/docs/test changes>

## SQL Changes

- None, or list validated SQL-facing changes and companion SQL PR/deployment order.

## Tests

- <focused pytest/validators/manual smoke checks>

## AI Review Gates

- Codex Security: <run | skipped, with reason>

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Risk: `/kvk_admin` commands are operator-critical during active KVK cycles.
- Mitigation: preserve command names, permissions, service/DAL contracts, and Google Sheets/export semantics; use focused command and service tests.
- Rollback: revert the Phase 6 implementation commit/PR; legacy player commands and Phase 5 player `/kvk` surfaces remain live.
```
