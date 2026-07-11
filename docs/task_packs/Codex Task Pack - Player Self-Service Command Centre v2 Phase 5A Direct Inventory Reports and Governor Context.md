# Codex Task Pack - Player Self-Service Command Centre v2 Phase 5A Direct Inventory Reports and Governor Context

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 5A Direct Inventory Reports and Governor Context`
- Date: `2026-07-12`
- Owner/context: Follow-on from the completed and operator-smoke-approved Phase 4 premium governor dashboard renderer.
- Task type: `Discord grouped commands | governor-specific inventory reports | private attachment interaction flow`
- One-pass approved: `No`
- Implementation approved: `Yes - revised scope approved 2026-07-12`
- Status: `implemented and automated validation complete - operator smoke pending`

## Implementation Record — 2026-07-12

- Added private `/me resources`, `/me materials`, and `/me speedups` at `v1.00`; `/me dashboard`
  is `v1.03`.
- Added the dedicated non-persistent player-self-service Inventory report adapter with strict
  selected-governor rechecks, report/range switching, private exports, same-payload fallback,
  governor paging, Dashboard return, timeout handling, attachment replacement, and stream cleanup.
- Updated selected dashboards to the approved navigation and governor-only entry selector.
- Added selected-governor-only latest RSS, combined Speedups days, and legendary-equivalent
  Materials totals to the 1180x760 dashboard and fallback embed.
- Preserved `/me inventory`, `/myinventory`, Inventory visibility preferences, the standalone
  1400x980 Inventory renderer, ranges, filenames, exports, imports, calculations, SQL, and DAL
  result shapes.
- Automated validation passed: 209 focused tests; architecture, deferred-item, test-selection,
  smoke-import, and command-registration validators; full pre-commit; full pytest with 2475 passed
  and 2 skipped; and pytest production-log isolation with the same result.
- Original, Discord-desktop, and Discord-mobile dashboard samples plus Resources, Speedups, and
  Materials report samples were rendered and visually inspected. Live Discord operator smoke is
  still required.
- The requested Codex Security skill was not exposed and the local Codex CLI remained blocked by
  Windows access controls. The documented independent security-focused diff review found no
  reportable issue after checking self-only authorization, visibility, forged/stale state,
  attachments, streams, exports, filenames, fallback delivery, and concurrent transitions.

## 2. Objective

Add direct private `/me resources`, `/me materials`, and `/me speedups` journeys for a linked
governor, plus matching actions from the premium governor dashboard. Reuse the established
inventory reporting services, 1400x980 Pillow renderer, range controls, and export services while
carrying the Phase 3/4 governor access and interaction-safety contract into the report journey.

Phase 5A is an entry-point and interaction integration slice. It does not redesign inventory
metrics, renderer artwork, report calculations, SQL, imports, exports, or legacy visibility
semantics.

## 3. Approval Checkpoint

Confirm these recommendations before implementation:

1. New `/me` report output is always private/ephemeral, even when the player's legacy Inventory
   preference is Public. `/myinventory` continues to honor the existing preference unchanged.
2. Add exactly three grouped subcommands: `/me resources`, `/me materials`, and `/me speedups`.
   Top-level command count remains 42; `/me` grouped subcommands increase from 6 to 9.
3. Add Resources, Materials, and Speedups actions to the selected-governor dashboard. Keep the
   accepted Accounts/Reminders/Preferences blue top row, Inventory/Exports secondary row, direct
   report actions below them, and Change Governor dropdown last.
4. A direct report uses compact controls: blue report-type tabs, 1M/3M/6M/12M range controls,
   existing private export actions, Dashboard/Inventory/Exports handoffs, and an author-gated
   Change Governor dropdown on the final component row when multiple governors exist. For more
   than 25 governors, the pager shares the compact navigation row rather than exceeding Discord's
   five-row component limit.
5. The existing inventory renderer and assets are reused unchanged. Any material visual redesign
   belongs in a separately approved inventory-renderer phase.

If the operator wants `/me` reports to honor public Inventory visibility, wants command options
instead of three grouped paths, or wants a new renderer, stop and revise this task pack before
coding.

### Operator-approved scope revision — 2026-07-12

This revision supersedes conflicting Phase 5A statements below:

- Keep `/me resources`, `/me materials`, and `/me speedups`; the dashboard label for Resources is
  `RSS`.
- Keep `/me inventory` registered and behavior-compatible, but remove its button from the selected
  governor dashboard. Its future need will be reviewed separately.
- The selected dashboard rows are Accounts/Reminders/Preferences primary, Exports secondary,
  RSS/Materials/Speedups success, Change Governor next, and governor-page buttons last only when
  required.
- The multiple-governor entry state contains only the governor dropdown, plus Previous/Next paging
  controls when more than 25 options make paging unavoidable. It has no other navigation.
- Direct-report rows are report tabs, ranges, private exports, Dashboard (plus Previous/Next when
  required), and Change Governor on row five.
- Extend the selected-governor dashboard payload with latest approved totals for that governor
  only: total RSS, combined Speedups days, and legendary-equivalent Materials including choice
  chests.
- Increase the governor dashboard from 1180x640 to 1180x760 and add the three Inventory totals as
  a third metric row below Dead/Helps/Healed. This is an explicitly approved exception to the
  original no-dashboard-renderer/no-dashboard-data wording. It does not authorize an Inventory
  renderer, calculation, SQL, DAL, asset, import, export, or `/myinventory` redesign.
- Category-specific no-data states remain private, preserve report controls, and link the configured
  Inventory upload channel with `/inventory import` guidance.
- The existing standalone 1400x980 Inventory renderer remains accepted for Phase 5A. A future
  visual-quality review is deferred rather than folded into this implementation.

## 4. Required Reading

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 4 Premium Governor Dashboard Renderer.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 3 Governor Selector and Dashboard Shell.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 2 Governor Context and Dashboard Data Foundation.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Inspect before coding:

- `commands/me_cmds.py`
- `ui/views/player_self_service_governor_dashboard_views.py`
- `ui/views/player_self_service_views.py`
- `ui/views/inventory_report_views.py`
- `inventory/reporting_service.py`
- `inventory/report_image_renderer.py`
- `inventory/export_service.py`
- `inventory/models.py`
- `player_self_service/governor_dashboard_models.py`
- `player_self_service/governor_dashboard_service.py`
- `tests/test_governor_dashboard_discord_views.py`
- `tests/test_inventory_report_views.py`
- `tests/test_inventory_reporting_service.py`
- `tests/test_inventory_report_image_renderer.py`
- `tests/test_player_self_service_views.py`
- `tests/test_me_cmds.py`

No SQL change is expected. If implementation appears to require a new column, query, procedure,
view, or index, stop and scope it separately against `C:\K98-bot-SQL-Server`.

## 5. Delivered Baseline

Phases 2-4 provide:

- typed linked-governor options, context, access decisions, and no/one/multiple resolution
- default-deny self-view authorization and registry rechecks before governor payload loading
- author gating, forged/stale/concurrent suppression, timeout behavior, and private failures
- the 1180x640 standalone governor card and safe same-payload fallback embed
- paged Change Governor behavior for more than 25 linked governors
- attachment replacement and stream cleanup across current `/me` transitions

The existing Inventory subsystem provides:

- `InventoryReportView.RESOURCES`, `SPEEDUPS`, `MATERIALS`, and `ALL`
- 1M, 3M, 6M, and 12M report ranges
- linked-governor resolution and service/DAL-backed payload assembly
- the deterministic 1400x980 `inventory.report_image_renderer`
- stable category/range filenames and standalone Discord-file delivery
- Excel, CSV, and Google Sheets exports
- `/myinventory` selection and the user's Only Me/Public visibility preference

Phase 5A must integrate these boundaries rather than duplicate them.

## 6. User Journeys

### Direct grouped command

```text
/me resources | /me materials | /me speedups
-> private defer
-> resolve linked governors
-> none: private setup guidance
-> one: recheck access and open the requested report directly
-> multiple: author-gated governor selector before report payload fetch
-> render requested 1M report off-thread
-> send/edit standalone PNG with private controls
```

### Dashboard action

```text
selected governor dashboard
-> Resources | Materials | Speedups
-> recheck selected governor access
-> build one existing inventory payload
-> render and replace governor-card attachment in place
-> retain Dashboard/Inventory/Exports navigation
```

### Change Governor on a report

```text
current report type + current range
-> Change Governor dropdown
-> recheck new governor against invoking user
-> rebuild same report type/range once
-> replace attachment in place
-> preserve controls and selected governor
```

### Range, type, and export actions

- Report-type and range changes recheck current governor access before fetching data.
- Each successful change clears/replaces the prior attachment in the same private message.
- Export actions remain private, selected-governor scoped, and use the existing export service,
  filenames, schemas, cleanup, and error handling.

## 7. Architecture Direction

Recommended placement:

- Keep the three slash callbacks thin in `commands/me_cmds.py`; each passes a fixed
  `InventoryReportView` to one player-self-service inventory report sender.
- Add a dedicated Discord adapter/view such as
  `ui/views/player_self_service_inventory_report_views.py` for selector, report controls,
  message edits, attachments, fallback, paging, author gating, and timeout handling.
- Reuse the Phase 2/3 governor context/access service for linked-governor resolution. Do not couple
  inventory reports to `GovernorDashboardPayload` or the governor renderer.
- Keep governor/report authorization and payload assembly in `inventory.reporting_service` and
  existing registry/service paths. Views must not query SQL or trust a stored component ID without
  re-resolution.
- Call `inventory.report_image_renderer.render_inventory_reports` through `asyncio.to_thread`.
  Do not import renderer-private helpers from KVK, governor, page-card, or legacy view modules.
- Reuse `inventory.export_service` for exports and always clean temporary files in `finally`.
- If a tiny existing Inventory presentation helper must be shared by the legacy and `/me` views,
  promote it to a clearly named public helper with focused tests; do not create a broad renderer or
  Discord-view framework.

The new view is non-persistent. Its security comes from author gating and service-backed access
rechecks, not from trusting in-memory state after restart.

## 8. Command and Component Contract

Command surface after approval:

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me inventory
/me exports
/me resources
/me materials
/me speedups
```

- Top-level commands: unchanged at 42.
- `/me` grouped subcommands: 6 -> 9.
- New commands use standard version decorators, `safe_command`, and `track_usage`.
- Existing `/me`, `/myinventory`, inventory import, export, preference, and legacy registrations
  remain unchanged.

Recommended dashboard rows:

1. Accounts, Reminders, Preferences — primary blue.
2. Inventory, Exports — secondary.
3. Resources, Materials, Speedups — success actions.
4. Change Governor dropdown when multiple linked governors exist.
5. Previous/Next governor-page buttons only when more than 25 governors require them.

Recommended direct-report rows, adjusted only if Discord component limits require an equivalent:

1. Resources, Materials, Speedups — primary blue tabs with the current report disabled.
2. 1M, 3M, 6M, 12M — current range primary, others secondary.
3. Export Excel, Export CSV, Export Sheets — secondary/private actions.
4. Dashboard, Inventory, Exports — compact navigation. When governor paging is required, keep
   Dashboard and replace the optional Inventory/Exports handoffs with Previous/Next page buttons.
5. Change Governor dropdown when multiple linked governors exist.

When more than 25 governors require paging, use the established Phase 4 selector-page behavior.
Paging changes only the view and must preserve the current attachment, report type, and range.

## 9. Delivery, Fallback, and Resource Contract

- Successful reports are standalone PNG attachments, never embed-wrapped images.
- Build a concise private embed or text fallback from the same authorized inventory payload.
- Avatar read, render, file creation, or Discord image-delivery failure must not fetch the payload
  again and must not fall back to `/myinventory` visibility behavior.
- Clear or replace attachments on selector-to-report, report-to-selector, report-to-report,
  dashboard-to-report, report-to-dashboard, report-to-Inventory, report-to-Exports, fallback,
  denied, unavailable, setup, timeout, cancellation, and stale/concurrent transitions.
- Close/reset renderer `BytesIO`, Discord file streams, and export files on every success, failure,
  cancellation, timeout, send/edit exception, and stale-render suppression path.
- If image delivery fails after a message edit attempt, retry only with the same private fallback
  and current view when ownership is still valid.

## 10. Privacy and Access Contract

- All new `/me` command responses and report interactions are private/ephemeral.
- The legacy Inventory visibility preference is neither read nor changed by the new `/me` direct
  report path.
- `/myinventory` continues to honor Only Me/Public exactly as it does before Phase 5A.
- Every governor selection, report-type change, range change, and export action revalidates the
  governor against the invoking Discord user before data access.
- Foreign users, forged governor IDs, stale views, expired views, and concurrent actions fail
  privately without loading report data.
- Admin status does not silently grant inspect access through `/me resources`, `/me materials`, or
  `/me speedups`; these remain self-view paths. Phase 8 owns inspect mode.
- User-controlled governor names are fitted/sanitized through the existing renderer contract and
  must not create mentions or unsafe filenames.

## 11. In Scope

- Three grouped `/me` report commands and versions.
- Three selected-governor dashboard actions.
- Direct no/one/multiple governor journey and paged selector.
- Revalidation on every report fetch/action.
- Dedicated private report interaction view/adapter.
- Existing report types, default 1M range, range switching, and exports.
- Same-page report type/range/governor switching.
- Standalone image delivery, same-payload fallback, attachment cleanup, and stream cleanup.
- Dashboard/Inventory/Exports navigation and selected-governor return behavior.
- Focused command, view, service-boundary, renderer-compatibility, and legacy regression tests.
- Representative Resources, Materials, and Speedups Discord desktop/mobile smoke samples.

## 12. Explicitly Out of Scope

- No Inventory table, view, procedure, index, query, DAL result-shape, or data-field change.
- No inventory calculation, capacity, VIP, chart, icon, asset, colour, layout, or renderer redesign.
- No `/me inventory` summary-card migration; Phase 5B owns existing summary-page presentation.
- No Accounts, Reminders, Preferences, or Exports summary-page visual migration.
- No change to `/myinventory`, Inventory visibility preferences, imports, upload-first flows,
  corrections, materials continuation, admin debug, or audit behavior.
- No export schema, format, worksheet, header, Google Sheets, filename, or cleanup change.
- No `/me history`, `/me inspect`, Export Stats integration, Olympia, Last Login data wiring,
  CrystalTech integration, cache, persistence, website, or API work.
- No broad shared renderer/view framework and no persistent image cache.
- No legacy command redirect, removal, or public `/kvk` behavior change.

## 13. Likely Files

Likely create:

- `ui/views/player_self_service_inventory_report_views.py`
- `tests/test_me_inventory_report_views.py`

Likely modify:

- `commands/me_cmds.py`
- `ui/views/player_self_service_governor_dashboard_views.py`
- `player_self_service/governor_dashboard_service.py` only if the existing action list is the clean
  service-owned way to expose the new dashboard actions
- `inventory/reporting_service.py` only for a small public revalidation/orchestration helper if the
  current service API cannot safely support the new view without duplication
- `ui/views/inventory_report_views.py` only if a small stable public presentation helper is shared
- `tests/test_me_cmds.py`
- `tests/test_governor_dashboard_discord_views.py`
- `tests/test_inventory_reporting_service.py` when a service helper changes
- `docs/reference/canonical_command_reference.md`
- programme, briefing, task-pack, starter, and deferred documentation after delivery

`inventory/report_image_renderer.py`, Inventory DAL modules, and SQL should remain unchanged unless
an unexpected blocker is separately reviewed and approved.

## 14. Test Requirements

Command and registration:

- `/me resources`, `/me materials`, and `/me speedups` are registered once with the expected
  decorators, descriptions, versions, and fixed report types.
- Top-level count stays 42 and `/me` grouped count becomes 9.
- Existing `/me` and named legacy commands remain registered and behavior-compatible.

Governor resolution and security:

- no-governor setup, one-governor direct open, multiple-governor selector, unavailable, and denied
- selector paging above 25 governors
- author gating, forged ID denial, access removal between interactions, and self-view-only policy
- stale, timeout, cancellation, and concurrent-transition suppression
- no report payload fetch before multiple-governor selection or after denied access

Report behavior:

- each command/dashboard action maps to the correct `InventoryReportView`
- default 1M range and 1M/3M/6M/12M switching
- report-type and governor switching preserve current range where applicable
- Change Governor preserves report type/range and replaces the attachment in place
- empty data, complete data, long/Unicode names, avatar absence, and renderer failure
- fallback uses the same payload and does not duplicate data access
- export actions remain selected-governor scoped, private, and clean temporary files

Delivery/resource behavior:

- stable standalone inventory filenames and expected 1400x980 PNG dimensions remain compatible
- every dashboard/selector/report/page/fallback transition clears or preserves attachments exactly
  as specified
- every renderer/file/export stream closes on success, failure, cancellation, timeout, send/edit
  failure, and stale suppression
- paged governor dropdown edits only the view and preserves the report attachment

Compatibility/privacy:

- new `/me` paths are always private regardless of stored Inventory visibility
- `/myinventory` continues to honor Only Me/Public without changed output or picker behavior
- `/me inventory`, Inventory imports, preferences, VIP, range, export, and report renderer tests stay
  green
- Dashboard, Inventory, and Exports navigation preserves selected governor return context

## 15. Validation Plan

Use `k98-test-selection` after the exact touched-file set is known. Expected focused commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_me_inventory_report_views.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_governor_dashboard_discord_views.py tests/test_me_cmds.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_inventory_report_views.py tests/test_inventory_reporting_service.py tests/test_inventory_report_image_renderer.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_player_self_service_views.py tests/test_ui_imports.py
```

Required repository gates:

```powershell
.\.venv\Scripts\python.exe scripts/validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts/validate_deferred_items.py
.\.venv\Scripts\python.exe scripts/select_tests.py
.\.venv\Scripts\python.exe scripts/smoke_imports.py
.\.venv\Scripts\python.exe scripts/validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
```

Run Codex Security review because private/public visibility boundaries, registry authorization,
user-controlled governor names, Discord attachments/streams, interaction transitions, exports,
and fallback delivery are in scope. SQL security review is not required unless scope changes.

## 16. Manual Discord Smoke Test

1. Each direct command shows setup guidance with no linked governor.
2. Each direct command opens its requested 1M report with one linked governor.
3. Multiple governors show a private selector before report data is fetched.
4. Dashboard Resources, Materials, and Speedups open the selected governor directly.
5. Report tabs switch category while preserving governor and range.
6. Range buttons update the report in place without stale attachments.
7. Change Governor is absent for one governor and present/gated for multiple governors.
8. Change Governor retains report type/range and works across every governor option.
9. More-than-25 governor paging preserves the current report image.
10. Excel, CSV, and Sheets exports remain private and selected-governor scoped.
11. New `/me` reports remain private even when legacy Inventory visibility is Public.
12. `/myinventory` still follows Only Me/Public and its current picker/report journey.
13. Dashboard/Inventory/Exports handoffs and return to Dashboard preserve selected context.
14. Render/delivery failure shows the private fallback without a second payload fetch.
15. Timeout, stale, foreign, forged, and concurrent interactions fail safely.
16. Resources, Materials, and Speedups are readable at Discord desktop and mobile scale.

## 17. Acceptance Criteria

- [ ] Operator approves private-only `/me` direct reports, three grouped commands, and control layout.
- [ ] `/me resources`, `/me materials`, and `/me speedups` deliver the requested existing report.
- [ ] Dashboard actions carry and revalidate the selected governor.
- [ ] No/one/multiple and more-than-25 governor journeys are private and safe.
- [ ] Change Governor appears only when relevant and preserves report type/range.
- [ ] Existing 1400x980 renderer, report calculations, ranges, exports, and filenames are reused.
- [ ] Successful output is a standalone image with same-payload private fallback.
- [ ] Attachments and streams are correct across every success/failure/stale transition.
- [ ] New `/me` paths are private and `/myinventory` visibility behavior is unchanged.
- [ ] Top-level count is unchanged and `/me` grouped count is exactly 9.
- [ ] No SQL, DAL query, data field, import, export schema, or renderer redesign is introduced.
- [ ] Focused/full validation, visual smoke, and security review are recorded.
- [ ] Programme, briefing, canonical command, task-pack, starter, and deferred docs reflect delivery.

## 18. Delivery Output

Provide:

1. Approved privacy, command, component-row, and governor-selector decisions.
2. Command/view/service file manifest and architecture boundary confirmation.
3. No/one/multiple governor and Change Governor journey summary.
4. Attachment, fallback, and stream-cleanup behavior.
5. Command-count and no-SQL/no-data/no-renderer-redesign statement.
6. Focused/full automated validation and Codex Security result.
7. Representative desktop/mobile samples and operator smoke feedback.
8. Any structured deferred items discovered without expanding Phase 5A.
