# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5B Premium Inventory Report Backdrops and Visual Alignment

Status: complete and archived. Phase 5B operator smoke and final visual acceptance passed on
2026-07-13. This starter is retained as the original execution prompt; the accepted implementation
record is in the archived task pack and authoritative programme pack.

Use this prompt to start the next GovernorOS v2 slice after Phase 5A.

---

Codex, start Player Self-Service Command Centre v2 Phase 5B: Premium Inventory Report Backdrops
and Visual Alignment.

Context:
GovernorOS v2 Phase 5A is complete. Operator smoke passed populated and honest no-data Resources,
Speedups, and Materials reports, private exports, Dashboard navigation, and report-preserving Change
Governor on 2026-07-13. The direct reports use the established shared 1400x980 Inventory renderer,
which now looks materially older than the accepted premium 1180x760 governor dashboard.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5B Premium Inventory Report Backdrops and Visual Alignment.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5A Direct Inventory Reports and Governor Context.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 4 Premium Governor Dashboard Renderer.md
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

Approval checkpoint - confirm before implementation:
- the shared Inventory renderer refresh intentionally affects both private direct `/me` reports and
  legacy `/myinventory` report visuals, while `/myinventory` visibility and behavior stay unchanged
- runtime uses the 1400x980 production backdrops and retains 1400x980 output dimensions
- the 2800x1960 `_master_2x` files remain source masters and are not loaded at runtime
- the work is presentation-only: no report data, SQL, DAL, service, calculation, range, export,
  filename, import, Google Sheets, command, or interaction change
- no-data output uses the same honest native report shell with no dummy figures or invented trends
- direct report tabs, ranges, private exports, Dashboard navigation, author-gated Change Governor,
  report/range preservation, and >25 governor paging remain unchanged

Objective:
Refresh Resources, Speedups, Materials, and native no-data Inventory report visuals to the premium
GovernorOS v2.0 standard using the supplied report-specific backdrops. Preserve the established
renderer/service/view boundaries and every player behavior.

Assets already committed:
- assets/Inventory/cards/inventory_resources_governoros_backdrop.png
- assets/Inventory/cards/inventory_resources_governoros_backdrop_master_2x.png
- assets/Inventory/cards/inventory_speedups_governoros_backdrop.png
- assets/Inventory/cards/inventory_speedups_governoros_backdrop_master_2x.png
- assets/Inventory/cards/inventory_materials_governoros_backdrop.png
- assets/Inventory/cards/inventory_materials_governoros_backdrop_master_2x.png

Visual contract:
- preserve standalone 1400x980 PNGs and stable filenames
- use report-specific 1400x980 backdrops through the existing renderer's asset path
- align panel opacity, borders, chart surfaces, typography, spacing, hierarchy, and contrast to the
  premium backdrop while keeping desktop and mobile readability
- keep all genuine report values, units, captions, chart series, legends, deltas, timestamps, and
  upload guidance accurate
- keep the no-data card visually consistent but muted, explicit, and positive; never fabricate data
- preserve the existing same-payload fallback and attachment/file-stream cleanup contract
- do not import renderer-private helpers or create a broad renderer/view framework

Compatibility contract:
- `/me resources`, `/me materials`, and `/me speedups` remain always private/ephemeral
- `/myinventory` continues to honor the existing Only Me/Public preference unchanged
- direct report type, range, governor, and export actions continue to recheck current access
- Change Governor retains report type/range and remains author-gated, including >25 paging
- foreign, forged, stale, timed-out, cancelled, and concurrent interactions remain privately denied
- output filenames, report dimensions, export formats/schemas, and Google Sheets behavior stay stable

Do not do in Phase 5B:
- no SQL, DAL query, model field, payload field, calculation, capacity, VIP, range, export, filename,
  schema, import, upload, correction, command registration, visibility, or interaction redesign
- no `/me inventory` summary-card migration; Phase 5F owns that page
- no Accounts, Reminders, Preferences, or Exports summary-card migration; Phases 5C-5E and 5G own them
- no dashboard, history, inspect, Export Stats, Last Login, Olympia, CrystalTech, website/API,
  persistent cache, redirect, removal, or public `/kvk` change

Tests:
- Resources, Speedups, Materials, and native no-data renderer output at exactly 1400x980
- stable filenames and report-specific backdrop selection
- representative populated/partial/empty payloads and chart/value/legend accuracy
- asset missing/corrupt, renderer failure, fallback, attachment replacement, and stream cleanup
- direct `/me` tabs/ranges/exports/Dashboard/governor switching and >25 paging regressions
- unchanged `/myinventory` Only Me/Public behavior and current controls/exports
- original-size, Discord desktop, and Discord mobile visual samples for all report types and no-data
- existing Inventory renderer, reporting service, report view, player-self-service view, and command
  regressions

Run focused tests selected from touched files plus:
.\.venv\Scripts\python.exe scripts/validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts/validate_deferred_items.py
.\.venv\Scripts\python.exe scripts/select_tests.py
.\.venv\Scripts\python.exe scripts/smoke_imports.py
.\.venv\Scripts\python.exe scripts/validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests

Run Codex Security review because renderer assets, Discord attachments/streams, fallbacks, private
versus public legacy delivery, and user-visible report content are in scope.

Before coding, provide the architecture/scope review and confirm the approval checkpoint. Do not
assume approval from this starter.
