# DL_bot Upload Routing - Phase 2 PreKvK Initiation Statement

We are starting Phase 2 of the DL_bot upload-routing optimisation programme after PR 97
(`dlbot-player-location-upload-route`) was smoke tested successfully and promoted to production.

This phase is split into three approval-gated slices:

## Phase 2A - PreKvK Upload Route Extraction

Goal: extract the PreKvK upload route from `DL_bot.py` into the existing `upload_routes` pattern
introduced in Phase 1.

Status: implemented in PR 98 (`dlbot-prekvk-upload-route`), smoke tested successfully, and pushed
to production. Phase 2B and Phase 2C remain separate approval-gated follow-ons.

In scope:

- `DL_bot.py` PreKvK route delegation.
- Dedicated `upload_routes/prekvk_route.py` or equivalent route module.
- Focused route-level tests for matching, non-matching, KVK lookup failure, duplicate skip,
  import success, import failure, and stats-refresh best-effort behaviour.
- Documentation updates that mark Phase 2A delivered or re-defer any remaining findings after
  implementation.

Preserve:

- Channel and attachment gating.
- Accepted filenames: `1198_prekvk.xlsx` and `PreKvK_Rankings_*.xlsx`.
- No-matching-file warning embed.
- SQL headroom preflight.
- Current KVK metadata lookup.
- `import_prekvk_bytes` offload contract.
- Uploader/channel/message metadata passed to the importer.
- Duplicate skip handling and embed title/colour.
- Success and failure embed fields.
- Background log-backup scheduling for successful imports.
- Stats embed refresh after successful imports.
- No fall-through after the PreKvK route handles a message.

Approved behaviour change:

- Duplicate skips should send the skipped embed but should not schedule a background log backup or
  refresh the stats embed.

Out of scope for Phase 2A:

- Legacy PreKvK SQL phase-object cleanup.
- New PreKvK report command or embed.
- KVK_ALL route extraction.
- Broad upload-router consolidation for MGE, honor, weekly, rally, inventory, or fallback queueing.
- `DL_bot.py` startup/lifecycle or `bot_instance.py` audit.

## Phase 2B - PreKvK SQL Cleanup Audit And Design

Goal: audit whether legacy PreKvK SQL phase objects can be replaced or retired safely.

Status: implemented in SQL PR 3 (`codex/prekvk-phase-sql-cleanup`), deployed to production,
smoke tested successfully, and left `dbo.PreKvk_Phases` in place for a later Option C retirement
audit.

Starter packet:

- `docs/task_packs/DL_bot Upload Routing - Phase 2B PreKvK SQL Cleanup Audit Statement.md`

Minimum objects to review in `C:\K98-bot-SQL-Server`:

- `dbo.PreKvk_Phases`
- `dbo.fn_PreKvkPhaseDelta`
- KVK-specific PreKvK phase views, including `v_PreKvk*_Phase*`
- Any production reports, manual workflows, views, stored procedures, or functions that still
  depend on the scan-window delta model

This phase must stop for approval before any SQL object replacement, retirement, destructive
cleanup, or production SQL migration.

Delivered outcome:

- `dbo.fn_PreKvkPhaseDelta` and `dbo.v_PreKvk13_Phase1/2/3` were preserved as compatibility
  object names but now source direct stage values from `dbo.PreKvk_Scores`.
- `dbo.sp_Build_Prekvk_And_Honor_Rankings` was aligned so PreKvK stage values and `ScanID` come
  from the same deterministic best-score row.
- Production deploy and rollback scripts were created in the SQL repo.
- Later destructive retirement of `dbo.PreKvk_Phases` remains deferred until a separate Option C
  audit and approval.

## Phase 2C - New PreKvK Report/Embed

Goal: design and implement a dedicated PreKvK report/embed after the route boundary is stable.

Approved implementation direction:

- Add a public read-only `/prekvk report` subcommand under a shared PreKvK command group so
  the report does not increase the Discord top-level command count.
- Default to the current KVK when `kvk_no` is omitted.
- Render a dedicated PNG leaderboard rather than a fixed-width embed table.
- Include `Rank`, `GovernorName`, `Power`, `Stage 1`, `Stage 2`, `Stage 3`, and `Overall`.
- Default sort is `Overall`; allow sorting by `Overall`, `Stage 1`, `Stage 2`, or `Stage 3`.
- Default limit is Top 10; allow Top 10, Top 25, Top 50, and Top 100 buttons.
- Use a new PreKvK report DAL/service/rendering architecture rather than extending upload routing
  or import behaviour.

Phase 2C should not change upload routing behaviour unless separately approved.

## Phase 2D - PreKvK Stats-Alert Architecture Refactor

Goal: after Phase 2C is validated, refactor the scheduled PreKvK stats-alert helper/embed to use
the new PreKvK report architecture where practical.

In scope:

- `stats_alerts/prekvk_stats.py`
- `stats_alerts/embeds/prekvk.py`
- preservation of scheduled-post, guard/state, previous-KVK target, honor, event, and upload-refresh
  behaviour
- focused tests proving the scheduled stats-alert behaviour still works

Phase 2D must be completed before moving on from the PreKvK report phase.

## Required Stop Points

1. Phase 2A audit/scope, architecture direction, and implementation plan must each be approved
   before route extraction code changes.
2. Phase 2B must produce a SQL dependency audit/design packet and stop before SQL changes.
3. Phase 2C must produce a report/embed design packet and stop before implementation.
4. Phase 2D must preserve scheduled stats-alert behaviour while adopting the new report
   architecture.
