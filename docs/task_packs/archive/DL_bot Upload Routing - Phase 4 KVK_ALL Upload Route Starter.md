# DL_bot Upload Routing - Phase 4 KVK_ALL Upload Route Starter

We are starting Phase 4 of the DL_bot upload-routing optimisation programme after:

- Phase 1 player-location upload routing was smoke tested successfully and pushed to production.
- Phase 2A PreKvK upload route extraction was smoke tested successfully and pushed to production.
- Phase 2B PreKvK SQL compatibility cleanup was deployed, smoke tested successfully, and pushed to
  production.
- Phase 2C delivered the public read-only `/prekvk report` image report, was smoke tested
  successfully, and pushed to production.
- Phase 2D refactored the scheduled PreKvK stats-alert path onto the Phase 2C report service
  architecture, was smoke tested successfully, and pushed to production.
- Phase 3 local validation blockers were audited and closed as a no-op after the focused blocker
  tests, full suite, and log-noise validation all passed under `.venv`.

## Completion Note

Status: complete in PR 110 (`codex/kvk-all-upload-route`), smoke tested successfully on
2026-05-26, and promoted to production.

Phase 4 extracted the KVK_ALL upload route from the root `DL_bot.py` listener into
`upload_routes/kvk_all_route.py` while preserving current production behaviour.

Delivered behaviour:

- `DL_bot.py` delegates KVK_ALL message handling to `handle_kvk_all_upload()` and keeps only
  listener/event plumbing for this route.
- KVK_ALL attachment filtering, SQL preflight, offload dispatch, result interpretation, embed
  rendering, sheet link button, per-attachment continuation, and auto-export scheduling are covered
  by focused route tests in `tests/test_kvk_all_upload_route.py`.
- Current Discord output, importer contract, structured failure handling, health line, and
  fall-through behaviour were preserved.
- The SQL preflight review fix relies on `ensure_sql_headroom_or_notify()` for the user-facing
  abort notification and avoids emitting a duplicate route-level abort embed.
- No SQL schema, stored procedure, view, export contract, or workbook-format changes were made.

Validation evidence included:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_kvk_all_upload_route.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_player_location_upload_route.py tests/test_prekvk_upload_route.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_kvk_all_importer.py tests/test_kvk_all_import_dal.py tests/test_kvk_all_import_service.py tests/test_kvk_all_schema.py tests/test_kvk_export_service.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_kvk_all_recompute_sql_contract.py
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
```

Observed full-suite result after review fix: `1473 passed, 2 skipped`.

Smoke evidence from production confirmed the route handled a KVK_ALL workbook, passed SQL
preflight, staged/imported Full Data, scheduled auto-export for KVK 15 Scan 31, and wrote the
expected Google Sheets export tabs.

Phase 5 remaining fast-path upload-route consolidation is the next upload-routing programme slice.

## Original Goal

Phase 4 was the next higher-blast-radius upload-routing slice: extract the KVK_ALL upload route
from the root `DL_bot.py` listener into the established `upload_routes` pattern while preserving
current production behaviour.

## Goal

Move KVK_ALL all-kingdom upload orchestration out of the inline `DL_bot.py` `on_message` branch and
behind a dedicated route/service boundary.

The desired end state is:

- `DL_bot.py` delegates KVK_ALL message handling to a route module and keeps only listener/event
  plumbing.
- KVK_ALL attachment filtering, SQL preflight, offload dispatch, result interpretation, embed
  rendering, sheet link button, per-attachment continuation, and auto-export scheduling are
  covered by focused route tests.
- Current Discord output, importer contract, structured failure handling, health line, and
  fall-through behaviour are preserved unless an explicit behaviour change is approved.
- No new SQL schema changes are introduced in this phase.

Step 1 is an audit/design packet, not implementation. Stop before code changes until the KVK_ALL
route classification and first PR scope are approved.

## Required Reading

Before audit work, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/Codex Task Pack - DL_bot Upload Routing Deferred Optimisation Audit.md`
- `docs/task_packs/DL_bot Upload Routing - Phase 3 Local Validation Blockers Starter.md`

Use `C:\K98-bot-SQL-Server` as the SQL source of truth for any KVK_ALL importer, DAL, export,
view, stored procedure, or output-contract assumptions reviewed during this phase.

## Skills To Use

- `k98-architecture-scope`
- `k98-discord-command-feature`
- `k98-sql-validation`
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review` before any PR handoff
- `k98-promotion-check` only before production promotion/deployment

## Source Deferred Item

### Deferred Optimisation
- Area: `DL_bot.py` KVK_ALL upload routing
- Type: architecture
- Description: KVK_ALL upload routing still lives in the legacy root bot listener with attachment filtering, offload dispatch, import result handling, Discord rendering, and export scheduling mixed together.
- Suggested Fix: Move KVK_ALL upload orchestration into a dedicated service or route module in a later phase, leaving `DL_bot.py` responsible for event delegation and Discord response plumbing.
- Impact: medium
- Risk: medium
- Dependencies: Preserve existing Discord output and auto-export behaviour; broader restart/performance hardening remains assigned to the KVK_ALL modernisation programme.

## Phase 4 Scope

In scope:

- Audit the current KVK_ALL branch in `DL_bot.py`.
- Map channel gating, accepted attachment extensions, no-file warning behaviour, per-attachment
  processing, SQL headroom preflight, offload contract, structured importer failure handling,
  success/warning embed fields, branding thumbnail, Google Sheet link button, and non-blocking
  auto-export scheduling.
- Extract KVK_ALL routing into `upload_routes/kvk_all_route.py` or an equivalent route module after
  audit approval.
- Preserve multi-attachment semantics: each matching attachment is processed independently, and a
  failure for one attachment must not stop later attachments.
- Preserve no fall-through into the monitored-channel queue after the KVK_ALL route handles a
  message.
- Add focused route tests around matching, non-matching, no matching attachment, preflight abort,
  structured importer failure, success without negatives, success with negative corrections,
  optional link button, auto-export scheduling, exception rendering, and multi-attachment
  continuation.
- Update docs/deferred backlog after implementation.

Out of scope until separately approved:

- Changing KVK_ALL importer behaviour or workbook format handling.
- Changing SQL schema, stored procedures, views, export result sets, or Google Sheets export
  contract.
- Redesigning `kvk_all_importer.py`, `kvk/dal/kvk_all_import_dal.py`, or KVK export services beyond
  route-boundary dependency injection needed for tests.
- Broad upload-router consolidation for MGE, honor, weekly activity, rally, inventory, or fallback
  queueing.
- Broad `DL_bot.py` startup/lifecycle or `bot_instance.py` refactor.
- KVK_ALL schema modernisation work, legacy SQL cleanup, or performance tuning outside the route
  extraction.

## Current Files To Review

Likely route/listener files:

- `DL_bot.py`
- `upload_routes/player_location_route.py`
- `upload_routes/prekvk_route.py`
- `upload_routes/__init__.py`

Likely KVK_ALL importer/service/DAL files:

- `kvk_all_importer.py`
- `kvk/dal/kvk_all_import_dal.py`
- `kvk/services/kvk_all_import_service.py`
- `kvk/services/kvk_export_service.py`
- `kvk/schemas/kvk_all_schema.py`
- `gsheet_module.py`
- `log_health.py`
- `file_utils.py`

Likely tests:

- `tests/test_kvk_all_importer.py`
- `tests/test_kvk_all_import_dal.py`
- `tests/test_kvk_all_import_service.py`
- `tests/test_kvk_all_schema.py`
- `tests/test_kvk_all_recompute_sql_contract.py`
- `tests/test_kvk_export_service.py`
- `tests/test_prekvk_upload_route.py`
- `tests/test_player_location_upload_route.py`
- new focused KVK_ALL route tests

## Design Questions

- What exact route dependency object should mirror the existing `PlayerLocationRouteDeps` and
  `PreKvkRouteDeps` patterns?
- Should the KVK_ALL route own embed construction directly, or should success/failure embed
  builders be split into small route-local helpers for testability?
- How should the route inject `discord.Embed`, `discord.ui.View`, and link-button creation so unit
  tests can avoid brittle Discord internals while preserving output?
- Should `_auto_export_kvk` remain imported from `kvk_all_importer.py` for this phase, or should
  the route receive an injected auto-export scheduler callable?
- Which KVK_ALL SQL contracts need validation against `C:\K98-bot-SQL-Server` before implementation,
  and which are already covered by existing SQL contract tests?
- What is the minimal route test surface that proves behaviour parity without duplicating importer
  and SQL contract tests?
- Are any KVK_ALL route observations large enough to defer to Phase 5 or the KVK_ALL schema
  modernisation programme instead of fixing in this PR?

## Step 1 Required Output

Phase 4 Step 1 must produce:

- Audit Summary
- Current KVK_ALL Route Map
- Importer / SQL Contract Map
- Discord Output Preservation Map
- Route Boundary Recommendation
- Refactor Trigger Findings
- Recommended First PR Scope
- Test And Validation Strategy
- Deferred Optimisation Findings
- Approval Questions
- Explicit Stop Point

Do not write bot code, SQL, tests, or deployment scripts during Step 1.

## Validation Requirements

For audit/design-only work:

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

For implementation after approval, choose validation based on the selected KVK_ALL route slice:

- focused new KVK_ALL route tests
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_kvk_all_importer.py tests/test_kvk_all_import_dal.py tests/test_kvk_all_import_service.py tests/test_kvk_all_schema.py tests/test_kvk_export_service.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_kvk_all_recompute_sql_contract.py`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests`

If live SQL integration is intentionally needed, document and validate the opt-in path:

```powershell
$env:RUN_DB_TESTS="1"
.\.venv\Scripts\python.exe -m pytest -q <selected live DB tests>
```

## Acceptance Criteria

- KVK_ALL route responsibilities are removed from the inline `DL_bot.py` listener branch within the
  approved scope.
- `DL_bot.py` delegates to the new route and preserves existing route order and fall-through
  behaviour.
- Accepted attachment extensions remain `.xlsx`, `.xls`, and `.csv`.
- No-matching-file warning embed remains unchanged.
- SQL headroom preflight aborts only the current attachment and keeps processing later matching
  attachments.
- Structured importer failures render the existing user-facing failure embed and continue to the
  next attachment.
- Success and warning embeds preserve KVK, ScanID, Rows, Staged, Negative Corrections, Duration,
  Health, File, Sheet, Channel, and Uploader fields.
- Sheet link button remains best-effort and never blocks the import result embed.
- `KVK_AUTO_EXPORT` still schedules non-blocking auto-export with the same KVK and notify channel.
- No new direct SQL is added to Discord listener/route layers.
- Out-of-scope KVK_ALL or upload-router findings are captured structurally.

## Explicit Stop Point

Stop after the Phase 4 audit/design packet.

Do not implement route extraction, alter SQL, change upload routing behaviour, or open a PR until
the audit packet, KVK_ALL route boundary, and first implementation scope have each been approved.
