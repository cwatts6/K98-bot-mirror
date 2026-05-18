# DL_bot Upload Routing - Phase 2C PreKvK Report Starter

We are starting Phase 2C after:

- Phase 2A (`dlbot-prekvk-upload-route`) was smoke tested successfully and pushed to production.
- Phase 2B (`codex/prekvk-phase-sql-cleanup` in `K98-bot-SQL-Server`) was deployed to production
  and smoke tested successfully.

Phase 2C is the dedicated PreKvK report/embed design task. It should not alter upload routing or
PreKvK import behaviour unless a separate approval explicitly expands scope.

## Goal

Design a dedicated PreKvK report surface that uses the now-stable direct-stage PreKvK data path:

- overall total points
- Stage I points
- Stage II points
- Stage III points

The first step is an audit/design packet, not implementation. Stop before code changes until the
report surface, architecture direction, and implementation plan are each approved.

## Approved Phase 2C Direction

The audit/design packet was reviewed and implementation was approved with these decisions:

- Build a public read-only `/prekvk report` subcommand rather than an admin-only command. Use the
  shared `/prekvk` top-level group to avoid exceeding Discord's 100 top-level application-command
  limit.
- Keep the command unannounced initially; it remains low risk because it only reads existing
  PreKvK data.
- Default to the current `kvk_no` from metadata, with an optional `kvk_no` override.
- Default ordering is `Overall`; users can switch to `Stage 1`, `Stage 2`, or `Stage 3`.
- Default limit is Top 10; buttons support Top 10, Top 25, Top 50, and Top 100.
- Output should be a mobile-safe image report, improving on the older `/kvk_rankings` fixed-width
  embed table style and borrowing the image-rendering pattern used by the inventory reports.
- Report columns are `Rank`, `GovernorName`, `Power`, `Stage 1`, `Stage 2`, `Stage 3`, and
  `Overall`.
- `Power` should be enriched from the existing player/KVK stats SQL source when available and show
  `N/A` when unavailable.
- Use the approved architecture: PreKvK DAL, service, image renderer, and Discord view layers.
- Add Phase 2D as a required follow-on to refactor `stats_alerts/prekvk_stats.py` and
  `stats_alerts/embeds/prekvk.py` to reuse the new architecture before moving on from the PreKvK
  report phase.

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
- `docs/task_packs/Codex Task Pack - DL_bot Upload Routing Deferred Optimisation Audit.md`
- `docs/task_packs/prekvk_schema_standardisation_task_pack.md`

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

## Phase 2C Scope

In scope:

- Audit current PreKvK reporting helpers and embeds.
- Decide whether the report surface should be command-based, scheduled, admin-only, or channel
  triggered.
- Define permission model and target channel behaviour.
- Define report limits, tie handling, empty-data behaviour, and legacy total-only-row behaviour.
- Decide whether to reuse `stats_alerts.prekvk_stats.load_prekvk_top3` directly or introduce a
  small service layer.
- Design mobile-safe Discord output for overall and stage blocks.
- Recommend a PR-sized implementation plan after the audit packet is approved.

Out of scope until separately approved:

- Changing `import_prekvk_bytes`.
- Changing `upload_routes/prekvk_route.py` or `DL_bot.py` upload behaviour.
- Retiring `dbo.PreKvk_Phases` or any legacy SQL object.
- Reworking PreKvK storage, import history, or ranking procedures.
- Broad stats-alert panel redesign.
- Production deployment or bot-machine restart.

## Current Objects And Files To Review

Python/reporting:

- `stats_alerts/prekvk_stats.py`
- `stats_alerts/embeds/prekvk.py`
- `stats_alerts/interface.py`
- `kvk/dal/kvk_stats_dal.py`
- `commands/prekvk_admin_cmds.py`
- `upload_routes/prekvk_route.py`
- `DL_bot.py`

Tests:

- `tests/test_prekvk_stats.py`
- `tests/test_prekvk_diagnostics.py`
- `tests/test_prekvk_importer.py`
- `tests/test_prekvk_upload_route.py`
- any command/embed tests discovered during audit

SQL source of truth:

- `dbo.PreKvk_Scan`
- `dbo.PreKvk_Scores`
- `dbo.PreKvk_ImportHistory`
- `dbo.PreKvk_Scores_Ranked`
- `dbo.fn_PreKvkLatestOverall`
- `dbo.fn_PreKvkPhaseDelta`
- `dbo.sp_Build_Prekvk_And_Honor_Rankings`

## Design Questions

- Should the first report be an admin slash command, public slash command, scheduled embed, or
  channel-triggered action?
- Which roles/users can run or refresh the report?
- Should output default to the current KVK from config, or require a `kvk_no` argument?
- What Top N should be used by default, and should it be configurable?
- How should ties be displayed when more than N players share a boundary score?
- How should old total-only rows behave for stage blocks?
- Should the implementation call `load_prekvk_top3` directly, extend it, or introduce
  `prekvk/report_service.py`?
- Should report rendering reuse the existing stats-alert embed style or create a dedicated embed?
- What should the command/report say when no PreKvK import exists for the selected KVK?

## Step 1 Required Output

Phase 2C Step 1 must produce:

- Audit Summary
- Current PreKvK Reporting Map
- Proposed Report Surface Options
- Permission And Channel Model
- Data Access / SQL Review
- Discord Output Design
- Recommended Architecture Direction
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

For implementation after approval, choose validation based on the selected report surface:

- focused PreKvK report/service tests
- focused image rendering tests
- command registration validation if a slash command is added
- interaction/permission tests if a command or button/view is added
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`

## Acceptance Criteria

- Report design is separated from upload routing and SQL cleanup work.
- PreKvK report dependencies are mapped with file/object evidence.
- Proposed output is mobile-safe and handles empty/legacy data clearly.
- No upload route, importer, or production SQL behaviour changes are made without separate
  approval.
- Out-of-scope follow-ups are captured structurally.

## Explicit Stop Point

Stop after the Phase 2C audit/design packet.

Do not implement the report, alter SQL, change upload routing, or open a PR until the audit packet,
report surface, architecture direction, and implementation plan have each been approved.
