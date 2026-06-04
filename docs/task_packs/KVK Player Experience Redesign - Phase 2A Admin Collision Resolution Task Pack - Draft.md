# KVK Player Experience Redesign - Phase 2A Admin Collision Resolution Task Pack Draft

## 1. Task Header

- Task name: `KVK Player Experience Redesign - Phase 2A Admin Collision Resolution`
- Date: `2026-06-03`
- Task type: `command-surface refactor / admin migration`
- One-pass approved: `no`
- Status: `approved for /kvk_admin implementation`

## 2. Objective

Resolve the current `/kvk` command collision before the player `/kvk` scaffold is implemented.

Current `/kvk` is an admin/operator group in `commands/stats_cmds.py`. The programme target reserves `/kvk` for player journeys, so the existing admin/operator commands must move to an approved admin surface first.

## 3. Scope

In scope:

- Move or wrap current admin/operator `/kvk` commands under the approved admin surface.
- Preserve permissions, channel restrictions, usage tracking, versioning, safe command handling, logging, command-cache behaviour, and service/DAL ownership.
- Update command registration validation, canonical command reference, command inventory tests, smoke tests, and operator rollout notes.
- Keep old operator command paths live or provide approved compatibility/help behaviour if needed.

Out of scope:

- No player `/kvk stats`, `/kvk targets`, `/kvk history`, or `/kvk rankings` scaffold.
- No visual redesign.
- No SQL schema, procedure, view, function, import, recompute, export, or Google Sheets behaviour changes.
- No legacy player command removal.

## 4. Commands To Move

Current admin/operator commands:

```text
/kvk test_export
/kvk refresh_stats_cache
/kvk export_all
/kvk recompute
/kvk list_scans
/kvk test_embed
/kvk window_preview
```

Approved target:

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

## 5. Architecture Direction

- Commands remain thin and call `kvk.services.kvk_admin_service` or existing export/test helpers.
- DAL stays in `kvk/dal/` or current approved data-access modules.
- No direct SQL should be added to command/view layers.
- If compatibility wrappers are used, they should delegate to the new command/service path and avoid duplicated logic.

## 6. Testing And Validation

Run or justify:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_inventory.py tests\test_command_registration_smoke.py tests\test_stats_cmds.py tests\test_kvk_admin_service.py
```

Run Codex Security before PR handoff because command permissions, Discord interactions, and SQL/export-facing operator commands are touched.

## 7. Acceptance Criteria

- [ ] Approved admin target surface is documented.
- [ ] Current admin/operator `/kvk` commands no longer block the player `/kvk` scaffold.
- [ ] Permissions and channel restrictions are preserved.
- [ ] Command registration validation passes.
- [ ] Canonical command reference is updated.
- [ ] Legacy compatibility behaviour is documented.
- [ ] No SQL/import/recompute/export semantics changed.

## 8. Approval Decision

Phase 2A uses `/kvk_admin ...` because it is cleaner and clearer to admins. The existing
admin/operator `/kvk ...` command paths are removed from the active command surface so the player
`/kvk` scaffold can claim that group in Phase 2B.
