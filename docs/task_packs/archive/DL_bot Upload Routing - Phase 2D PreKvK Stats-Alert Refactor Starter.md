# DL_bot Upload Routing - Phase 2D PreKvK Stats-Alert Refactor Starter

We are starting Phase 2D after:

- Phase 2A (`dlbot-prekvk-upload-route`) was smoke tested successfully and pushed to production.
- Phase 2B (`codex/prekvk-phase-sql-cleanup` in `K98-bot-SQL-Server`) was deployed to production
  and smoke tested successfully.
- Phase 2C delivered the public read-only `/prekvk report` image report, was smoke tested
  successfully, and was pushed to production.

Phase 2D is the required follow-on to bring the scheduled PreKvK stats-alert helper/embed onto the
new Phase 2C PreKvK report architecture where practical. It should not alter upload routing,
PreKvK import behaviour, or SQL behaviour unless a separate approval explicitly expands scope.

## Completion Status

Phase 2D is complete. The scheduled PreKvK stats-alert path was refactored to use a compact
PreKvK scheduled-summary service shape backed by the Phase 2C report DAL/service architecture.
The change was smoke tested successfully and pushed to production.

Delivered production behaviour:

- `stats_alerts/prekvk_stats.py` no longer owns duplicated PreKvK ranking SQL; it remains only as a
  compatibility wrapper over the PreKvK report service.
- `stats_alerts/embeds/prekvk.py` keeps scheduled stats-alert responsibilities: metadata,
  timeline, honor block, event block, guard/state handling, edit-vs-send behaviour, and upload
  refresh compatibility.
- Current Top 3 and previous-KVK target blocks are fed by the new PreKvK scheduled-summary service
  shape.
- Upload routing, PreKvK import behaviour, SQL behaviour, and `/prekvk report` UX were unchanged.

Next required follow-on:

- `docs/task_packs/DL_bot Upload Routing - Phase 3 Local Validation Blockers Starter.md`

## Goal

Refactor the scheduled PreKvK stats-alert path so it reuses the new PreKvK report architecture
instead of maintaining a separate legacy top-list query/rendering path.

The desired end state is:

- `stats_alerts/prekvk_stats.py` no longer owns duplicated PreKvK ranking SQL that should live in
  the new PreKvK DAL/service layer.
- `stats_alerts/embeds/prekvk.py` keeps the scheduled stats-alert responsibilities: metadata,
  timeline, honor block, event block, guard/state handling, edit-vs-send behaviour, and upload
  refresh compatibility.
- The scheduled embed can continue to show compact Top 3/current and previous-KVK target blocks,
  but those blocks should be fed by the Phase 2C data access/service model or a small adapter.
- Existing scheduled-post behaviour, daily guard behaviour, persisted `prekvk_msg_id` behaviour,
  and upload-refresh behaviour remain unchanged from the user's perspective.

Step 1 is an audit/design packet, not implementation. Stop before code changes until the report
architecture reuse direction and implementation plan are approved.

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
- `docs/task_packs/DL_bot Upload Routing - Phase 2 PreKvK Initiation Statement.md`
- `docs/task_packs/DL_bot Upload Routing - Phase 2C PreKvK Report Starter.md`
- `docs/task_packs/Codex Task Pack - DL_bot Upload Routing Deferred Optimisation Audit.md`

Use `C:\K98-bot-SQL-Server` as the SQL source of truth for PreKvK tables, views, functions, and
stored procedures.

## Skills To Use

- `k98-architecture-scope`
- `k98-discord-command-feature`
- `k98-sql-validation`
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review` before any PR handoff
- `k98-promotion-check` only before production promotion/deployment

## Phase 2C Architecture To Reuse

Review these Phase 2C files before proposing the Phase 2D design:

- `commands/prekvk_cmds.py`
- `prekvk/models.py`
- `prekvk/dal/report_dal.py`
- `prekvk/report_service.py`
- `prekvk/report_image_renderer.py`
- `ui/views/prekvk_report_views.py`

Review these Phase 2C tests:

- `tests/test_prekvk_report_command.py`
- `tests/test_prekvk_report_dal.py`
- `tests/test_prekvk_report_service.py`
- `tests/test_prekvk_report_image_renderer.py`
- `tests/test_prekvk_report_views.py`

## Phase 2D Scope

In scope:

- Audit `stats_alerts/prekvk_stats.py` and `stats_alerts/embeds/prekvk.py`.
- Decide whether `load_prekvk_top3` should become a compatibility adapter, move behind
  `prekvk/report_service.py`, or be retired after callers are migrated.
- Preserve the scheduled PreKvK embed's existing metadata, timeline, honor, events, links, guard,
  state, previous-KVK target, and edit-vs-send behaviour.
- Preserve upload-triggered stats refresh behaviour after successful PreKvK imports.
- Keep command `/prekvk report` behaviour unchanged.
- Add focused tests for the scheduled stats-alert path and any compatibility adapter.
- Update docs/deferred tracking after implementation.

Out of scope until separately approved:

- Changing `import_prekvk_bytes`.
- Changing `upload_routes/prekvk_route.py` or `DL_bot.py` upload behaviour.
- Changing `/prekvk report` command UX, buttons, image layout, or command registration.
- Retiring `dbo.PreKvk_Phases` or any legacy SQL object.
- Reworking PreKvK storage, import history, or ranking procedures.
- Broad stats-alert panel redesign.
- Production deployment or bot-machine restart.

## Current Objects And Files To Review

Python/reporting:

- `stats_alerts/prekvk_stats.py`
- `stats_alerts/embeds/prekvk.py`
- `stats_alerts/interface.py`
- `stats_alerts/guard.py`
- `stats_alerts/state.py`
- `stats_alerts/honors.py`
- `stats_alerts/kvk_meta.py`
- `prekvk/dal/report_dal.py`
- `prekvk/report_service.py`
- `prekvk/models.py`
- `upload_routes/prekvk_route.py`

Tests:

- `tests/test_prekvk_stats.py`
- `tests/test_prekvk_embed.py`
- `tests/test_prekvk_report_service.py`
- `tests/test_prekvk_report_dal.py`
- any stats-alert interface or scheduled embed tests discovered during audit

SQL source of truth:

- `dbo.PreKvk_Scan`
- `dbo.PreKvk_Scores`
- `dbo.PreKvk_ImportHistory`
- `dbo.PreKvk_Scores_Ranked`
- `dbo.fn_PreKvkLatestOverall`
- `dbo.fn_PreKvkPhaseDelta`
- `dbo.sp_Build_Prekvk_And_Honor_Rankings`

## Design Questions

- Should `stats_alerts.prekvk_stats.load_prekvk_top3` remain as a public compatibility helper,
  or should scheduled embed code call a new service adapter directly?
- Should the scheduled embed use `PreKvkReportPayload` and derive Top 3 blocks from it, or should
  `report_service` expose a compact scheduled-summary shape?
- How should previous-KVK target blocks be produced without duplicating the Phase 2C SQL?
- Should legacy total-only rows continue to render stage blocks as empty/`N/A`, matching Phase 2C
  report semantics?
- What should the scheduled embed show when no PreKvK import exists for the selected current or
  previous KVK?
- Which existing tests should be migrated from mocked cursor SQL expectations to service/DAL
  expectations?
- What logging is needed to make scheduled refresh failures traceable without noisy scheduled logs?

## Step 1 Required Output

Phase 2D Step 1 must produce:

- Audit Summary
- Current Scheduled PreKvK Reporting Map
- Phase 2C Architecture Reuse Options
- Recommended Compatibility Strategy For `load_prekvk_top3`
- SQL / Data Access Review
- Scheduled Embed Behaviour Preservation Plan
- Upload Refresh And State/Guard Review
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

For implementation after approval, choose validation based on the selected architecture:

- focused PreKvK stats-alert tests
- focused PreKvK report service/DAL tests
- focused scheduled embed rendering tests
- upload-route refresh regression tests if the refresh call path is touched
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`

## Acceptance Criteria

- Scheduled PreKvK stats-alert logic is separated from duplicated SQL/report helper debt.
- Phase 2C report command behaviour remains unchanged.
- Upload routing and importer behaviour remain unchanged.
- Scheduled embed guard/state/edit-vs-send behaviour is preserved and covered by focused tests.
- Current and previous-KVK PreKvK Top 3 blocks are fed by the new architecture or a documented
  compatibility adapter.
- Out-of-scope follow-ups are captured structurally.

## Explicit Stop Point

Stop after the Phase 2D audit/design packet.

Do not implement the refactor, alter SQL, change upload routing, change `/prekvk report`, or open a
PR until the audit packet, architecture reuse direction, and implementation plan have each been
approved.
