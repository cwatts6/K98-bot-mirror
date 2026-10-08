# KVK Player Experience Redesign - Phase 2A Admin Collision Resolution Task Pack

## 1. Task Header

- Task name: `KVK Player Experience Redesign - Phase 2A Admin Collision Resolution`
- Date: `2026-06-03`
- Completed: `2026-06-04`
- Task type: `command-surface refactor / admin migration`
- One-pass approved: `no`
- Status: `complete - delivered and merged in PR #140`

## 2. Objective

Resolve the former `/kvk` command collision before the player `/kvk` scaffold is implemented.

Delivered result: the existing admin/operator commands were moved from `/kvk ...` to `/kvk_admin ...` in `commands/stats_cmds.py`. The `/kvk` top-level group is now available for the Phase 2B player scaffold.

## 3. Scope

In scope:

- Move current admin/operator `/kvk` commands under the approved admin surface.
- Preserve permissions, channel restrictions, usage tracking, versioning, safe command handling, logging, command-cache behaviour, and service/DAL ownership.
- Update command registration validation, canonical command reference, command inventory tests, smoke tests, and operator rollout notes.
- Document legacy operator path behaviour.

Out of scope:

- No player `/kvk stats`, `/kvk targets`, `/kvk history`, or `/kvk rankings` scaffold.
- No visual redesign.
- No SQL schema, procedure, view, function, import, recompute, export, or Google Sheets behaviour changes.
- No legacy player command removal.

## 4. Commands Moved

Former admin/operator commands:

```text
/kvk test_export
/kvk refresh_stats_cache
/kvk export_all
/kvk recompute
/kvk list_scans
/kvk test_embed
/kvk window_preview
```

Delivered admin target:

```text
/kvk_admin test_export
/kvk_admin refresh_stats_cache
/kvk_admin export_all
/kvk_admin recompute
/kvk_admin list_scans
/kvk_admin test_embed
/kvk_admin window_preview
```

Rejected alternative for this task:

```text
/ops kvk_test_export
/ops kvk_refresh_stats_cache
/ops kvk_export_all
/ops kvk_recompute
/ops kvk_list_scans
/ops kvk_test_embed
/ops kvk_window_preview
```

Legacy compatibility behaviour:

- Old `/kvk ...` admin/operator paths were removed from the active command surface.
- No compatibility wrappers were retained, by approval, so the player `/kvk` group can be scaffolded cleanly in Phase 2B.

## 5. Delivered Architecture

- Commands remain thin and call `kvk.services.kvk_admin_service` or existing export/test helpers.
- DAL remains in `kvk/dal/` or current approved data-access modules.
- No direct SQL was added to command/view layers.
- No SQL/import/recompute/export, Google Sheets, service, or DAL semantics changed.
- The command registration baseline, smoke tests, focused command tests, and canonical command reference now use `/kvk_admin`.

## 6. Testing And Validation

Completed validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_inventory.py tests\test_command_registration_smoke.py tests\test_stats_cmds.py tests\test_kvk_admin_service.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_governance_config.py tests\test_validate_command_registration.py tests\test_command_inventory.py tests\test_command_registration_smoke.py
```

Codex Security review was considered for PR handoff because command permissions, Discord interactions, and SQL/export-facing operator commands were touched. The delivered code change was a command-surface rename with existing permission decorators and service/DAL behaviour preserved.

## 7. Acceptance Criteria

- [x] Approved admin target surface is documented.
- [x] Current admin/operator `/kvk` commands no longer block the player `/kvk` scaffold.
- [x] Permissions and channel restrictions are preserved.
- [x] Command registration validation passes.
- [x] Canonical command reference is updated.
- [x] Legacy compatibility behaviour is documented.
- [x] No SQL/import/recompute/export semantics changed.

## 8. Approval Decision

Phase 2A uses `/kvk_admin ...` because it is cleaner and clearer to admins. The existing
admin/operator `/kvk ...` command paths are removed from the active command surface so the player
`/kvk` scaffold can claim that group in Phase 2B.
