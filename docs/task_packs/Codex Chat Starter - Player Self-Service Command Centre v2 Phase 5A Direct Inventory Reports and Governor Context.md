# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5A Direct Inventory Reports and Governor Context

Status: ready to start after operator approval of the Phase 5A private visibility, command surface,
dashboard action layout, and report-control layout.

## Copy/Paste Starter

```text
Codex, start Player Self-Service Command Centre v2 Phase 5A: Direct Inventory Reports and Governor Context.

Context:
Phases 1-4 are complete. Phase 4 made the selected-governor dashboard a premium 1180x640
standalone PNG, retained the private same-payload embed fallback, standardized blue top-row
navigation, and added a paged author-gated Change Governor dropdown. Operator smoke passed every
governor option and accepted the wider/readable presentation on 2026-07-11.

Phase 5A adds private direct selected-governor Resources, Materials, and Speedups while reusing the
existing Inventory reporting services, 1400x980 report renderer, ranges, and exports. It must not
redesign Inventory data, SQL, renderer visuals, imports, exports, or /myinventory behavior.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5A Direct Inventory Reports and Governor Context.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 4 Premium Governor Dashboard Renderer.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 3 Governor Selector and Dashboard Shell.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 2 Governor Context and Dashboard Data Foundation.md
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Use these skills:
- k98-architecture-scope
- k98-discord-command-feature
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review
- codex-security:security-scan

Approval checkpoint:
Confirm before implementation:
- /me resources, /me materials, and /me speedups are always private/ephemeral
- /myinventory continues to honor the existing Only Me/Public preference unchanged
- top-level command count remains 42 and /me grouped count increases from 6 to 9
- selected-dashboard rows are Accounts/Reminders/Preferences blue, Exports secondary,
  RSS/Materials/Speedups actions next, Change Governor next, and governor paging last only when
  required; `/me inventory` remains registered but has no selected-dashboard button
- the multiple-governor entry screen is governor-dropdown-only, with paging controls only when
  more than 25 options require them
- direct reports use report tabs, 1M/3M/6M/12M ranges, private exports,
  Dashboard navigation, and Change Governor on the final row
- for more than 25 governors, keep Dashboard and use the compact navigation row for Previous/Next
  governor-page buttons so the view remains within Discord's five-row component limit
- the existing 1400x980 Inventory renderer/assets are reused without visual redesign
- the selected dashboard grows to 1180x760 and adds selected-governor-only latest RSS, combined
  Speedups days, and legendary-equivalent Materials totals as its third metric row

Objective:
Create a dedicated player-self-service Inventory report interaction adapter. Add the three grouped
commands and matching dashboard actions. Resolve no/one/multiple governors privately, recheck
access before every report fetch/action, render off-thread, deliver standalone PNGs, and retain a
same-payload private fallback.

Architecture requirements:
- Keep slash callbacks thin in commands/me_cmds.py.
- Put Discord selectors, controls, edits, attachments, fallback, paging, and timeout behavior in a
  dedicated player-self-service Inventory report view module.
- Reuse the Phase 2/3 governor context/access service, but do not couple reports to
  GovernorDashboardPayload or the governor renderer.
- Keep authorization and report payload assembly in inventory.reporting_service and existing
  registry/service paths; no SQL in commands or views.
- Reuse inventory.report_image_renderer through asyncio.to_thread.
- Reuse inventory.export_service and clean temporary export files in finally.
- Do not import renderer-private helpers or create a broad shared renderer/view framework.

Interaction contract:
- no governors: private setup guidance
- one governor: requested 1M report opens directly
- multiple governors: author-gated selector before payload fetch
- Change Governor retains current report type/range and rechecks access
- more than 25 governors use Phase 4-style paging that preserves the report attachment
- report type, range, governor, and export actions recheck current access
- foreign, forged, stale, timed-out, cancelled, and concurrent interactions fail privately
- new /me paths never use or modify the legacy Inventory visibility preference

Delivery contract:
- standalone PNG is primary; no embed-wrapped attachment image
- fallback is private and built from the same payload without another fetch
- clear/replace attachments on every selector/report/dashboard/page/fallback/denied/setup path
- close/reset renderer BytesIO, Discord file streams, and export files on every success, failure,
  cancellation, timeout, stale render, and send/edit failure

Do not do in Phase 5A:
- no SQL, DAL query, data-field, calculation, capacity, VIP, chart, asset, or renderer change
- no /me inventory summary-card migration; Phase 5B owns existing /me page presentation alignment
- no Accounts, Reminders, Preferences, or Exports summary-page migration
- no change to /myinventory, visibility preferences, imports, upload-first, correction, materials
  continuation, exports, filenames, schemas, or Google Sheets behavior
- no /me history, /me inspect, Export Stats, Olympia, Last Login data, CrystalTech, website/API,
  persistent image cache, redirect, removal, or public /kvk change

Command impact:
- top-level commands: unchanged at 42
- /me grouped subcommands: 6 -> 9
- add /me resources, /me materials, /me speedups with standard version/safety/usage decorators

Tests:
- command registration/decorators/versions/counts
- no/one/multiple/>25 governor journeys and access rechecks
- dashboard actions and same-page report type/range/governor switching
- author/forged/stale/timeout/cancellation/concurrent suppression
- private-only /me behavior and unchanged /myinventory Only Me/Public behavior
- standalone filename/dimensions, fallback without duplicate fetch, attachment replacement, and
  stream/export cleanup across every transition
- existing Inventory renderer, reporting service, report view, /me, dashboard, and legacy regressions
- representative Resources, Materials, and Speedups desktop/mobile smoke samples

Run focused tests selected from touched files plus:
.\.venv\Scripts\python.exe scripts/validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts/validate_deferred_items.py
.\.venv\Scripts\python.exe scripts/select_tests.py
.\.venv\Scripts\python.exe scripts/smoke_imports.py
.\.venv\Scripts\python.exe scripts/validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests

Run Codex Security review because private/public visibility, registry access, Discord attachments
and streams, user-controlled names, interaction transitions, exports, and fallback delivery are in
scope.
```
