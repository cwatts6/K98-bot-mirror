# DL_bot Upload Routing - Phase 2 PreKvK Initiation Statement

We are starting Phase 2 of the DL_bot upload-routing optimisation programme after PR 97
(`dlbot-player-location-upload-route`) was smoke tested successfully and promoted to production.

This phase is split into three approval-gated slices:

## Phase 2A - PreKvK Upload Route Extraction

Goal: extract the PreKvK upload route from `DL_bot.py` into the existing `upload_routes` pattern
introduced in Phase 1.

Status: implemented as the Phase 2A route-extraction slice. Phase 2B and Phase 2C remain separate
approval-gated follow-ons.

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

Minimum objects to review in `C:\K98-bot-SQL-Server`:

- `dbo.PreKvk_Phases`
- `dbo.fn_PreKvkPhaseDelta`
- KVK-specific PreKvK phase views, including `v_PreKvk*_Phase*`
- Any production reports, manual workflows, views, stored procedures, or functions that still
  depend on the scan-window delta model

This phase must stop for approval before any SQL object replacement, retirement, destructive
cleanup, or production SQL migration.

## Phase 2C - New PreKvK Report/Embed

Goal: design and implement a dedicated PreKvK report/embed after the route boundary is stable.

Design decisions required before implementation:

- Command, scheduled embed, admin-only, or channel-triggered surface.
- Permission model and target channel.
- Report limits and tie handling.
- Empty-data and legacy total-only-row behaviour.
- Whether to reuse `stats_alerts.prekvk_stats.load_prekvk_top3` directly or introduce a service
  boundary for report orchestration.
- Mobile-safe Discord output shape.

Phase 2C should not change upload routing behaviour unless separately approved.

## Required Stop Points

1. Phase 2A audit/scope, architecture direction, and implementation plan must each be approved
   before route extraction code changes.
2. Phase 2B must produce a SQL dependency audit/design packet and stop before SQL changes.
3. Phase 2C must produce a report/embed design packet and stop before implementation.
