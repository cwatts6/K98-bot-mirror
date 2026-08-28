# Codex Task Pack - Player Self-Service Command Centre v2 Phase 5B Premium Inventory Report Backdrops and Visual Alignment

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 5B Premium Inventory Report Backdrops and Visual Alignment`
- Date: `2026-07-13`
- Owner/context: Follow-on from completed GovernorOS v2 Phase 5A and operator-supplied Inventory backdrop assets.
- Task type: `visual renderer refresh | Inventory reports | premium v2.0 presentation`
- One-pass approved: `No`
- Implementation approved: `Yes - operator confirmed the shared-renderer, 1400x980, source-master, presentation-only, honest no-data, and unchanged-interaction checkpoints on 2026-07-13`
- Status: `complete - operator smoke and final visual acceptance passed 2026-07-13; archived execution record`

## 2. Required Reading

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5A Direct Inventory Reports and Governor Context.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 4 Premium Governor Dashboard Renderer.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Inspect before implementation:

- `inventory/report_image_renderer.py`
- `inventory/models.py`
- `inventory/reporting_service.py`
- `ui/views/inventory_report_views.py`
- `ui/views/player_self_service_inventory_report_views.py`
- `tests/test_inventory_report_image_renderer.py`
- `tests/test_inventory_report_views.py`
- `tests/test_me_inventory_report_views.py`
- all six files under `assets/Inventory/cards/`

No SQL change is expected. If a visual refresh appears to require a new field, calculation, query,
view, table, procedure, or DAL result shape, stop and scope that work separately.

## 3. Objective

Bring Resources, Speedups, and Materials report images up to the accepted GovernorOS premium v2.0
visual standard by applying the operator-supplied 1400x980 report-specific backdrops and aligning
the existing cards, panels, typography, and chart treatment to them.

This is a presentation-only renderer slice. It must preserve the report data, calculations,
dimensions, filenames, ranges, controls, exports, privacy, governor context, and legacy
`/myinventory` behavior delivered before Phase 5B.

## 4. Background and Delivered Baseline

Phase 5A is complete and operator smoke passed on 2026-07-13. It delivered:

- private `/me resources`, `/me materials`, and `/me speedups`
- selected-governor dashboard actions and latest Inventory totals
- report tabs, 1M/3M/6M/12M ranges, private exports, Dashboard return, and Change Governor
- author gating, access rechecks, governor paging, attachment replacement, fallback, and cleanup
- honest renderer-native empty-state PNGs with no dummy values or fabricated graph lines
- unchanged `/myinventory` Only Me/Public behavior

Operator review confirmed that the established flat-blue Inventory reports now look materially
older than the premium GovernorOS dashboard. Six assets have therefore been committed in advance:

```text
assets/Inventory/cards/inventory_materials_governoros_backdrop.png
assets/Inventory/cards/inventory_materials_governoros_backdrop_master_2x.png
assets/Inventory/cards/inventory_resources_governoros_backdrop.png
assets/Inventory/cards/inventory_resources_governoros_backdrop_master_2x.png
assets/Inventory/cards/inventory_speedups_governoros_backdrop.png
assets/Inventory/cards/inventory_speedups_governoros_backdrop_master_2x.png
```

The production files are exactly 1400x980. The corresponding masters are exactly 2800x1960 and
are source-quality assets for future visual work; runtime rendering should use the 1400x980 files
unless an explicitly measured and approved reason requires otherwise. Preserve the supplied
`governoros` filenames exactly in this slice.

## 5. Approval Checkpoint

Confirm before implementation:

1. Phase 5B updates the shared Inventory report renderer, so the new visual treatment applies to
   both direct private `/me` reports and the preserved `/myinventory` report output. It does not
   change `/myinventory` visibility, picker, range, export, or command behavior.
2. Runtime uses the three 1400x980 production backdrops. The 2x masters remain committed source
   assets and are not loaded for each Discord render.
3. The renderer may adjust panel opacity, borders, chart colours, spacing, typography, and visual
   hierarchy where needed for contrast and polish, but it may not add, remove, reinterpret, or
   fabricate report data.
4. Existing successful filenames and 1400x980 dimensions remain stable.
5. The current no-data report shell remains honest: real governor/report/range context, muted
   unrecorded cards, no dummy values, no fake trends, and actionable upload guidance.
6. Direct `/me` reports retain the Phase 5A author-gated Change Governor dropdown, report/range
   preservation, private delivery, and more-than-25 governor paging. The renderer does not own
   Discord controls.
7. `/myinventory` retains its legacy interaction and Only Me/Public preference unchanged.
8. Operator approves representative Resources, Speedups, Materials, and empty-state prototypes at
   original, Discord desktop, and Discord mobile scale before final implementation acceptance.

If the operator wants new metrics, charts, calculations, dimensions, filenames, controls, export
formats, or visibility behavior, revise the task pack before coding.

## 6. Scope

### In Scope

- Load the report-specific production backdrop for Resources, Speedups, and Materials.
- Preserve a deterministic local fallback background when a supplied backdrop is missing or
  unreadable so the report/fallback journey remains safe.
- Restyle existing report panels, KPI cards, headings, legends, grid lines, charts, footer, and
  empty-state treatment only as required to work with the new backdrop.
- Preserve glyph-safe `core.visual_text` rendering and long/Unicode governor-name fitting.
- Preserve 1400x980 output and current category/range filenames.
- Preserve the Phase 5A empty-state content and no-fabricated-data rule.
- Add focused asset existence/dimension, renderer, populated/sparse/empty, filename, and visual
  structure tests.
- Generate and inspect representative original/desktop/mobile samples for every report type.
- Update programme, briefing, canonical, task-pack, starter, and deferred documentation after
  delivery.

### Out of Scope

- No command, grouped-subcommand, option, version, top-level count, or usage-tracking change.
- No Discord row, button, tab, range, export, Dashboard, selector, paging, Change Governor,
  author-gating, timeout, or interaction-state change.
- No SQL, DAL, service query, payload field, model meaning, calculation, capacity formula, VIP
  behavior, data freshness, import, correction, approval, or audit change.
- No report filename, 1400x980 dimension, Excel/CSV/Sheets schema, worksheet, or cleanup change.
- No `/myinventory` visibility/picker behavior change and no `/me inventory` summary-card redesign.
- No Accounts, Reminders, Preferences, Inventory summary, or Exports card change; Phases 5C-5G own
  those pages separately.
- No broad shared renderer framework, persistent image cache, website/API, Olympia, Last Login,
  CrystalTech, `/me history`, `/me inspect`, redirect, removal, or public `/kvk` work.

## 7. Architecture Direction

- Keep visual composition in `inventory/report_image_renderer.py`.
- Keep data assembly and authorization in the existing Inventory service/DAL paths unchanged.
- Keep Discord controls, attachment edits, fallback, author gating, and governor paging in their
  existing view modules; do not move them into the renderer.
- Reuse `core.visual_text`, existing icons, existing capacity calculations, and the current
  `InventoryReportPayload` contract.
- Add only narrowly named renderer-private helpers needed to load/composite the three backgrounds
  or apply consistent panel/contrast treatment. Do not create a cross-domain renderer framework.
- Continue rendering off the event loop through the existing adapters.
- Preserve complete `BytesIO` and Discord file-stream cleanup.

SQL/persistence/restart impact: none. The new images are packaged local assets. No persistent view,
cache, database, configuration, scheduler, or rehydration contract changes.

## 8. Premium v2.0 Inventory Visual Contract

- Full-canvas, report-specific fantasy backdrop at 1400x980.
- Clear Resources/Speedups/Materials identity and governor/range context.
- High-contrast readable KPI cards without hiding the supplied artwork unnecessarily.
- Existing values remain the visual priority; decorative detail must not compete with them.
- Charts retain their existing series, ordering, dates, units, and source values.
- Missing and one-scan states remain deliberate and balanced.
- Empty state uses the same premium shell and cards as a populated report, with muted unrecorded
  values and a clear no-approved-data message rather than sample or dummy data.
- Footer retains approved-source and generated-time meaning.
- Buttons/selectors remain real Discord components and are never painted into the PNG.

## 9. Governor and Navigation Contract

Phase 5B must not alter the interaction contract:

- Direct `/me` report pages are selected-governor pages and retain Change Governor when more than
  one linked governor exists.
- Changing governor retains report type and range, rechecks current access, and replaces the report
  attachment.
- More than 25 governors retain the compact Previous/Next paging row while preserving the report.
- Report tabs, ranges, exports, Dashboard, and Change Governor remain in their Phase 5A rows.
- `/myinventory` continues to use its established selector/report journey and visibility setting.
- Later Accounts, Reminders, Preferences, Inventory summary, and Exports cards are Discord-user or
  all-governor pages and must not gain Change Governor in Phases 5C-5G.

## 10. Asset Contract

- Validate all six asset paths, exact dimensions, decodability, and non-empty file content.
- Runtime assets: the three non-master 1400x980 PNGs.
- Source masters: the three `_master_2x` 2800x1960 PNGs.
- Do not resize and save over either source or production assets during tests.
- Do not generate derivative assets into the repository unless separately approved.
- Asset-load failure must degrade safely without a second payload fetch or data/visibility change.
- Record asset provenance as operator-supplied GovernorOS artwork in the implementation record.

## 11. Likely Files

### Review

- `inventory/report_image_renderer.py`
- `inventory/models.py`
- `ui/views/inventory_report_views.py`
- `ui/views/player_self_service_inventory_report_views.py`
- relevant existing renderer/view tests

### Modify

- `inventory/report_image_renderer.py`
- `tests/test_inventory_report_image_renderer.py`
- programme, briefing, canonical, task-pack, starter, and deferred docs after delivery

### Existing Inputs Added Before Implementation

- the six files under `assets/Inventory/cards/`

No command, service, DAL, SQL, export, import, or Discord view file is expected to change. Stop and
rescope if implementation requires one.

## 12. Refactor Decisions

| Issue | Decision | Reason |
|---|---|---|
| Older Inventory visual quality | fix now | This is the approved Phase 5B purpose. |
| Broad renderer framework | not applicable | Three report variants already share one renderer module; local helpers are sufficient. |
| Inventory import view orchestration | defer | Existing structured deferred item; unrelated to presentation. |
| New data/calculations/charts | not applicable | Presentation-only scope. |
| Summary-page premium migration | defer to Phases 5C-5G | Separate user-level pages, assets, semantics, and smoke evidence. |

## 13. Test Requirements

Renderer and assets:

- all production backdrops exist, decode, and are 1400x980
- all master assets exist, decode, and are 2800x1960
- each selected report uses the correct backdrop
- missing/corrupt backdrop follows the approved safe fallback
- populated, single-scan, partial, and empty data render successfully
- filenames and 1400x980 dimensions remain unchanged
- current series, values, units, and footer meaning remain unchanged
- long/Unicode governor names remain readable and safe
- renderer output streams remain seekable and closeable

Compatibility:

- `/me` direct reports remain private and selected-governor scoped
- report/range/governor switching still rechecks access and replaces attachments
- governor paging preserves the report
- `/myinventory` Only Me/Public behavior, picker, controls, and exports remain unchanged
- same-payload fallback remains available without duplicate fetch
- existing Inventory service, export, import, and view regressions stay green

Visual smoke samples:

- populated Resources, Speedups, and Materials
- one-scan/sparse examples where meaningful
- no-data Resources, Speedups, and Materials
- long/Unicode governor name
- original 1400x980, Discord desktop, and Discord mobile presentation

## 14. Validation Plan

Expected focused commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_inventory_report_image_renderer.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_inventory_report_views.py tests/test_me_inventory_report_views.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_inventory_reporting_service.py tests/test_inventory_export_service.py
```

Repository gates:

```powershell
.\.venv\Scripts\python.exe scripts/validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts/validate_deferred_items.py
.\.venv\Scripts\python.exe scripts/select_tests.py
.\.venv\Scripts\python.exe scripts/smoke_imports.py
.\.venv\Scripts\python.exe scripts/validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts/analyse_pytest_log_noise.py
```

Run Codex Security review because local asset/file handling, generated attachments, Discord report
delivery, user-controlled names, and private/public compatibility are in regression scope even
though authorization and data access should not change.

## 15. Manual Discord Smoke Test

1. `/me resources`, `/me speedups`, and `/me materials` show the correct premium backdrop.
2. Populated values and charts are legible at desktop and mobile scale.
3. No-data reports use the same premium shell without dummy values or fake trends.
4. 1M/3M/6M/12M switching preserves category, governor, controls, and attachment replacement.
5. Report tabs switch between the three correct backdrops.
6. Change Governor preserves report type/range and shows the correct governor data.
7. More-than-25 governor paging preserves the current report attachment.
8. Excel, CSV, and Sheets exports remain private and unchanged.
9. `/myinventory` renders the same premium reports while still honoring Only Me/Public.
10. Dashboard return, fallback, timeout, stale, foreign, and concurrent paths remain safe.
11. Long/Unicode governor names remain readable.

## 16. Acceptance Criteria

- [x] Operator approves the three backdrop directions and runtime/master asset policy.
- [x] Correct report-specific 1400x980 backdrop is applied to every report type.
- [x] The output is materially aligned with the accepted GovernorOS premium v2.0 standard; final operator visual acceptance passed.
- [x] Existing values, calculations, charts, dimensions, filenames, and footer meaning are preserved.
- [x] Empty reports remain honest, useful, and visually consistent without dummy data.
- [x] Direct `/me` governor dropdown, paging, privacy, tabs, ranges, exports, and Dashboard behavior are unchanged.
- [x] `/myinventory` visibility, selector, controls, exports, and compatibility remain unchanged.
- [x] Asset failure and renderer failure degrade safely without duplicate fetch or data exposure.
- [x] Focused/full validation, visual samples, operator smoke, and security review are recorded.
- [x] Programme, briefing, canonical, task-pack, starter, and deferred docs reflect completed delivery.

Implementation record (2026-07-13):

- Modified the shared Inventory renderer, the direct private report view's best-effort avatar
  handoff, their focused tests, the supplied Inventory item icons, and delivery docs. No service,
  DAL, SQL, calculation, export, command, registration, visibility, or interaction-state code changed.
- Runtime loads only the fixed 1400x980 report-specific assets; missing, corrupt, or wrong-sized
  assets fall back to the established safe canvas without changing filenames or stream behavior.
- Generated populated, sparse/Unicode, and honest no-data samples at original, Discord desktop, and
  Discord mobile sizes for each report type.
- Operator visual review accepted the premium theme/content direction and identified the missing
  item icons as a significant regression. The follow-up restores the supplied Resources, Speedups,
  and Materials icons to populated/no-data KPI shells, uses the invoking player's circular Discord
  avatar at top-left with the report logo as fallback, and increases fitted KPI/chart typography.
- The final chart-readability follow-up replaces the fixed first/middle/last date labels with up to
  six evenly spaced genuine upload dates and adds a density-aware diamond at every plotted upload.
  This exposes history depth without changing series values or fabricating observations.
- Passed 255 focused Inventory/dashboard tests and the full suite (`2503 passed, 2 skipped`) plus architecture,
  deferred-item, import, registration, formatting, type, and secret checks.
- The requested Codex Security skill was unavailable in this session; a manual security-focused
  diff review found no permission, privacy, user-input, path-selection, attachment, or cleanup
  regression; hosted production security scanning passed.
- Operator smoke and final visual acceptance completed successfully on 2026-07-13. Populated and
  honest no-data reports retained their data, controls, privacy, fallback, and compatibility
  contracts; the operator described the completed visual result as premium.

## 17. Remaining Phase 5 Handoff

After Phase 5B, prepare and execute the user-level summary pages independently:

- Phase 5C: Premium Accounts Summary Card
- Phase 5D: Premium Reminders Summary Card
- Phase 5E: Premium Preferences Summary Card
- Phase 5F: Premium Inventory Summary Card
- Phase 5G: Premium Exports Summary Card

Each slice requires its own operator-supplied/approved backdrop, representative prototype, current
page-action inventory, standalone attachment migration where still required, same-payload private
fallback, attachment/stream cleanup, and desktop/mobile smoke evidence. These pages are
Discord-user or all-governor surfaces and must not show Change Governor. They may retain selected
governor context only for returning to the governor dashboard or an explicitly governor-specific
action.

## 18. Required Delivery Output

Provide:

1. Approved visual direction and asset/runtime policy.
2. Renderer and test file manifest.
3. Before/after Resources, Speedups, Materials, and empty-state samples.
4. Confirmation that data/calculations/SQL/DAL/services/commands/views remain unchanged.
5. Dimensions, filenames, fallback, stream cleanup, and compatibility evidence.
6. Focused/full validation, Codex Security result, and operator smoke outcome.
7. Structured deferred items without expanding Phase 5B.
