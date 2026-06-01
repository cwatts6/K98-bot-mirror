# Codex Task Pack — Inventory Image Import Module — Phase 2 Materials

## Status / Context

Phase 0 and Phase 1A–1E are complete and deployed. Phase 1F should already be complete before this phase begins. Phase 2 is the Materials phase only.

Phase 2 must extend the existing Inventory Image Import Module to support Rise of Kingdoms equipment materials screenshots, while preserving the current Resources and Speedups behaviour.

Use the existing task pack and Standard Development Initiation Statement as mandatory working context.

## Implementation Wrap-Up

Phase 2 Materials was implemented and validated in PR #57 against the mirror repository.

Implemented capability:

- Materials import is enabled for upload-first inventory flow.
- Materials sessions support explicit multi-image upload via `Add Another Image`, up to 4 screenshots.
- Materials import recognises choice chests and individual material icons for Animal Bone, Leather, Ebony, and Iron Ore.
- Raw values are stored by material kind and rarity in `GovernorMaterialInventory`.
- Legendary-equivalent calculations are implemented and used for review, reporting, and export.
- Choice chests remain separate from fixed materials while contributing to the clearly labelled total.
- Typed correction flow is implemented through Materials section selection and five-rarity modals.
- Approval writes one logical import batch with material child rows.
- `/myinventory` supports Materials output with KPI cards, trend graph, range controls, and `assets/materials_logo.png`.
- `/export_inventory` includes Materials rows.
- `/inventory_import_audit` supports Materials imports and Materials-related debug metadata.
- Admin debug captures failed, rejected, cancelled, corrected, and low-confidence Materials paths.
- Existing Resources and Speedups behaviour was preserved.

Implementation files of note:

- `inventory/material_calculations.py`
- `inventory/material_service.py`
- `inventory/dal/inventory_material_dal.py`
- `inventory/inventory_service.py`
- `inventory/reporting_service.py`
- `inventory/report_image_renderer.py`
- `inventory/export_service.py`
- `services/vision_client.py`
- `ui/views/inventory_views.py`
- `ui/views/inventory_report_views.py`
- `commands/inventory_cmds.py`
- `sql/inventory_phase2_materials_schema.sql`
- `sql/inventory_phase2_materials_status_schema.sql`
- `assets/material_reference_sheet.png`
- `assets/materials_logo.png`

Issues found and resolved during smoke testing:

- Initial Materials vision recognition needed heavy correction. The fix was to use the stronger fallback model first for Materials-hinted scans and include a Materials-only visual reference sheet generated from labelled training images.
- Rarity detection was clarified to use icon tile background colour rather than detail-panel text or gold/yellow outer frame.
- Advanced ebony was occasionally misclassified as leather; prompt guidance now distinguishes dark wood grain/plank bundles from tan/yellow hide or rolled sheets.
- Duplicate values now report which duplicate was kept.
- Conflicting values now report exactly which value was kept and which was ignored.
- Older review messages are retired and disabled after `Add Another Image`, preventing stale approvals and duplicate/confusing import actions.
- `Add Another Image` now defers the interaction immediately and sends follow-up guidance, fixing `Unknown interaction` failures after correction flows.
- Materials significant-change checks were added. The gate now checks Choice Chests, Bone, Leather, Ebony, Iron, and Total Materials using the same 50% threshold as Resources and Speedups.
- `/myinventory Materials` initially failed because the renderer passed `color=` to `_draw_kpi`; this was corrected to `delta_color=`.
- `/myinventory Materials` now uses `assets/materials_logo.png` rather than the generic K98 logo.

Manual OpenAI vision smoke results:

- Prompt-only Materials training pass was insufficient.
- Stronger model plus prompt improvements improved results but still left rarity/kind misses.
- Materials reference sheet plus model/prompt changes produced 25 / 25 labelled training image matches for expected kind and rarity.
- Full Materials import smoke over the supplied import screenshots returned valid Materials detections with nonzero rows.

Validated commands during implementation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_vision_client.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_material_calculations.py tests\test_inventory_upload_flow.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_service.py tests\test_inventory_report_image_renderer.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_ui_imports.py <expanded tests\test_inventory_*.py list>
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe -m pre_commit run -a
```

Final local validation snapshot:

- Full suite passed: 1196 passed, 8 skipped.
- Targeted inventory/UI suite passed: 146 passed.
- Pre-commit passed.
- Architecture and deferred optimisation validators passed.
- User smoke testing confirmed correction, add-another-image, approval, significant-change, and `/myinventory Materials` output flows.

## Scope Control

### In scope

- Materials import from up to 4 uploaded screenshots per governor per day.
- Material choice chest screen recognition.
- Individual material recognition for Bone, Leather, Ebony, and Iron Ore.
- Raw quantity storage by material type and rarity.
- Legendary-equivalent calculations.
- Materials correction workflow.
- Materials approval workflow.
- Materials output image under `/myinventory`.
- Materials support in `/export_inventory`.
- Materials support in `/inventory_import_audit`.
- Admin debug retention for failed, corrected, cancelled, rejected, or low-confidence material imports.
- Test coverage for parsing, conversion, import sessions, reporting, export, and audit.

### Out of scope

- Action Points / AP import.
- `/my_stats` integration.
- Adding an export button under the report image.
- Adding an import-again button under the report image.
- Broad Resources or Speedups redesign.
- Stats export SQL refactor tracked separately.
- Any unrelated bot architecture refactor unless required to safely add Materials.

## Mandatory Working Method

Codex must follow the Standard Development Initiation Statement:

1. Audit first and stop.
2. Capture deferred optimisations in the required structured format.
3. Validate architecture and stop.
4. Provide implementation plan and stop.
5. Implement only after approval.
6. Test.
7. Perform mandatory read-only Codex review pass.

Do not proceed straight into coding.

## Required Reading

Before implementation, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/Promotion Guide.md`
- `docs/inventory_image_import_setup.md`
- `docs/inventory/Codex Task Pack - Inventory Image Import Module.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `commands/inventory_cmds.py`
- `inventory/models.py`
- `inventory/parsing.py`
- `inventory/inventory_service.py`
- `inventory/reporting_service.py`
- `inventory/report_image_renderer.py`
- `inventory/dal/inventory_dal.py`
- `inventory/dal/inventory_reporting_dal.py`
- `ui/views/inventory_views.py`
- `ui/views/inventory_report_views.py`
- `services/vision_client.py`
- `scripts/test_inventory_vision.py`

## User Experience

### Upload channel

Materials use the same inventory upload channel as existing inventory imports.

Channel name / intended location: `inventory`.

Upload-first remains the preferred flow: users add screenshots directly to the inventory channel and the bot starts the process.

### Materials upload count

Each governor may upload up to 4 materials images per day:

1. Choice chest screenshot.
2. Individual material screenshot 1.
3. Individual material screenshot 2.
4. Optional additional individual material screenshot if needed by screen layout or later samples.

The system must allow the user to build one materials import session from multiple screenshots before approval.

### Session lock

Keep the existing lock principle:

- One active import session per governor.
- Do not lock by Discord user.
- A Discord user may upload materials for several registered governors, but only one active import session per governor at a time.

### Daily limit

One approved Materials import per governor per day.

Admins may override using the existing admin override pattern if already supported.

### Multi-image review flow

A practical flow should be:

1. User uploads first materials screenshot in the inventory channel.
2. Bot detects Materials and starts a Materials import session.
3. Bot asks the user to add remaining materials screenshots or finish review.
4. User can upload additional screenshots for the same governor/session.
5. Bot analyses each image and merges recognised material rows into a pending combined result.
6. Bot shows a combined Materials Import Review embed.
7. User chooses:
   - Add Another Image
   - Review / Finish
   - Correct Data
   - Approve Import
   - Cancel Import
8. Approval writes one logical materials import batch with child records for all raw material quantities.

If the existing upload-first UX cannot support an explicit `Add Another Image` button cleanly, Codex must propose the safest architecture during Step 1/3 before implementing.

### Public upload visibility

Keep current privacy behaviour:

- Uploaded screenshots may be temporarily visible in the inventory channel.
- Keep screenshots visible during review so users can compare detected values.
- Delete original uploads after approval, cancellation, or timeout where permissions allow.
- Retain images in admin debug only when required for failed/corrected/cancelled/low-confidence imports.

## Accepted Materials Image Types

### Type A — Choice Chest screen

Recognise Equipment Material Choice Chests in these rarities:

- Normal choice chest — grey
- Advanced choice chest — green
- Elite choice chest — blue
- Epic choice chest — purple
- Legendary choice chest — orange

Store choice chests separately from fixed material types because they are flexible inventory, not committed to Bone, Leather, Ebony, or Iron.

### Type B/C — Individual materials

Recognise these material types:

- Animal Bone / Bone
- Leather
- Ebony
- Iron Ore / Iron

Each material can appear in these rarities:

- Normal — grey
- Advanced — green
- Elite — blue
- Epic — purple
- Legendary — orange

The individual material rows may be split over two or more screenshots.

## Recognition / Parsing Requirements

### Raw data to capture

For every recognised material item, capture:

- GovernorID
- ImportBatchID
- ScanUtc
- MaterialKind:
  - `choice_chest`
  - `animal_bone`
  - `leather`
  - `ebony`
  - `iron_ore`
- Rarity:
  - `normal`
  - `advanced`
  - `elite`
  - `epic`
  - `legendary`
- Raw quantity integer
- Source image index or image reference where practical
- Confidence / warning metadata where practical

### Duplicate handling

If the same material kind and rarity appears in multiple screenshots in the same pending session:

- Do not silently overwrite.
- Prefer deterministic duplicate handling:
  - if values are identical, keep one value and warn duplicate detected;
  - if values differ, block approval until user corrects or chooses the intended value.

### Missing values

Materials imports may be partially complete if the user only has some materials visible, but the review must clearly show missing/unseen categories as `0` or `not detected`.

Approval should be allowed when at least one valid material/chest value is captured and the user confirms the import.

### Value parsing

Material counts are positive integers shown under icons.

Support comma separators, e.g.:

- `1,409`
- `7,105`
- `4,165`

Reject negative values and non-integer corrections.

## Material Conversion Formula

Store raw values exactly. Calculate legendary equivalent for reporting.

Formula:

- Normal / 256 = Legendary equivalent
- Advanced / 64 = Legendary equivalent
- Elite / 16 = Legendary equivalent
- Epic / 4 = Legendary equivalent
- Legendary = Legendary equivalent

Equivalence chain:

- 4 Normal = 1 Advanced
- 4 Advanced = 1 Elite
- 4 Elite = 1 Epic
- 4 Epic = 1 Legendary

Recommended helper:

`inventory/material_calculations.py`

Expected functions:

- normalise material kind / rarity labels
- calculate legendary equivalent for a raw row
- aggregate fixed material legendary equivalents
- aggregate choice chest legendary equivalents
- calculate total legendary equivalent
- calculate net change over selected range

## SQL Requirements

Add SQL support in the SQL Server repository.

Recommended table:

`GovernorMaterialInventory`

Columns:

- `MaterialRecordID`
- `ImportBatchID`
- `GovernorID`
- `ScanUtc`
- `MaterialKind`
- `Rarity`
- `Quantity`
- `LegendaryEquivalent`
- `SourceImageIndex`
- `CreatedAtUtc`

Recommended constraints/indexes:

- Foreign key to `InventoryImportBatch`.
- Check constraint for allowed `MaterialKind`.
- Check constraint for allowed `Rarity`.
- Quantity must be >= 0.
- Index on `(GovernorID, ScanUtc)`.
- Index on `(GovernorID, MaterialKind, Rarity, ScanUtc)`.

If storing `LegendaryEquivalent` as calculated data is not preferred, Codex may store only raw values and calculate at query/report time, but the choice must be justified during architecture validation.

`InventoryImportBatch.ImportType` must support Materials if not already supported.

## Vision Structured Output Requirements

Update `services/vision_client.py` structured output for Materials without breaking Resources/Speedups.

The Materials schema should explicitly support:

- `material_screen_type`:
  - `choice_chests`
  - `individual_materials`
  - `mixed_materials`
  - `unknown_materials`
- `choice_chests` quantities by rarity.
- `individual_materials` quantities by material kind and rarity.
- `unreadable_items` list.
- `duplicate_candidates` list.
- warnings.

Strict schema rules must remain compatible with OpenAI structured outputs:

- every nested object must use `additionalProperties: false`;
- all required fields must be present;
- use `null`, empty arrays, or zero values where appropriate rather than missing keys.

## Import Review Requirements

The Materials review embed should show:

- Governor name / ID.
- Number of screenshots analysed.
- Detected screen types.
- Confidence summary.
- Warnings.
- Raw choice chest counts by rarity.
- Raw individual material counts by material and rarity.
- Calculated legendary equivalent per fixed material.
- Calculated choice chest legendary equivalent separately.
- Total legendary equivalent.

Keep review concise enough for Discord. If full raw data is too large, show summary in the embed and attach/admin-log full JSON as needed.

## Correction Workflow

Materials correction must be typed/user-safe. Do not ask normal users to edit raw JSON.

Recommended correction UX:

- User selects `Correct Data`.
- Bot shows a correction view with sections:
  - Choice Chests
  - Animal Bone
  - Leather
  - Ebony
  - Iron Ore
- User selects the section to correct.
- Bot opens a modal for the five rarities:
  - Normal
  - Advanced
  - Elite
  - Epic
  - Legendary
- Values must be integers >= 0.
- After correction, update the combined review summary and keep approval state clear.

Large changes versus detected values should follow the existing significant-change confirmation pattern.

Corrected materials imports must be retained in the admin debug channel with detected JSON and corrected/final JSON.

## Materials Output Image

Add Materials as an output option in `/myinventory` after Phase 2 is enabled.

Output selector should support:

- All
- RSS
- Speedups
- Materials

Do not add AP until Phase 3.

### Materials summary image content

Use the supplied example output as a visual direction, but adapt to K98 Bot style.

Show:

- Governor display name and governor name/ID where available.
- Bot/user avatar area consistent with existing inventory reports.
- First row KPI cards:
  - Bone legendary equivalent
  - Leather legendary equivalent
  - Ebony legendary equivalent
  - Iron legendary equivalent
  - Choice Chest legendary equivalent
- KPI cards should show delta over selected range where available.
- Secondary KPI cards:
  - Total Legendary Materials
  - Net Change over last 30 days or selected report range.
- Line graph by material type:
  - Animal Bone
  - Leather
  - Ebony
  - Iron Ore
  - Choice Chest
- Footer:
  - Built by K98 Bot / ProKingdoms style footer as appropriate.
  - Last scan timestamp in UTC.

### Graph rules

- Use approved scan timestamps only.
- Include all approved data points in selected range.
- Default range: 1M.
- Buttons: 1M / 3M / 6M / 12M.
- If only one approved Materials record exists, show summary only and no trend graph.
- Delta = latest approved value minus earliest approved value inside selected range.
- If no earlier approved point exists inside the range, show `N/A`.
- Net change over last 30 days should use the latest point minus earliest point inside the last 30 days where available; otherwise `N/A`.

### Design notes

- Mobile-first readable layout.
- Avoid overly dense raw tables in the image.
- Raw values belong in export, audit, and correction UX; report image should focus on legendary equivalents.
- Choice chests must remain separate from fixed material totals, but total legendary equivalent may include both if clearly labelled.

## Export Requirements

Extend `/export_inventory` to include Materials.

Export should include:

- GovernorID
- Governor name where available
- ScanUtc
- ImportBatchID
- MaterialKind
- Rarity
- Raw quantity
- Legendary equivalent
- Source image index/reference if available
- Approved/corrected metadata where consistent with existing export patterns

Do not expose private image URLs to normal users unless already allowed by the existing export design. Admin audit can show retained debug references.

## Admin Audit Requirements

Extend `/inventory_import_audit` filters and display to support `materials` import type.

Audit should allow review of:

- failed materials imports
- cancelled materials imports
- corrected materials imports
- low-confidence materials imports
- duplicate/conflict warnings
- debug image post references
- detected/corrected/final JSON

## Logging Requirements

Add clear logs for:

- materials session start
- screenshot added to session
- image type detected
- merge conflict / duplicate material key
- correction applied
- approval write
- cancellation/timeout cleanup
- original upload deletion success/failure
- admin debug post success/failure

Avoid logging secrets or full OpenAI API details.

## Restart / State Safety

Audit how active import sessions are currently persisted.

Materials multi-image sessions must not strand a governor lock after restart or timeout.

At minimum:

- active Materials batches must have `ExpiresAtUtc`;
- stale batches must be cleaned up consistently with existing inventory imports;
- a restart must not allow duplicate approved imports for the same governor/day/type;
- partially uploaded but unapproved Materials sessions must be recoverable or safely expired.

Codex must explicitly address this in Step 1 audit and Step 4 implementation plan.

## Test Images / Samples

Use these uploaded samples during local testing:

- `material_summary_exampleonly_output.png` — output design reference only.
- `Materials_import1.png` — materials import test image.
- `Materials_import2.png` — materials import test image.
- `Materials_import3.png` — materials import test image.
- `Materials_import4.png` — materials import test image.

Expected interpretation from supplied samples should be established during audit/test setup. More samples will be added during actual testing.

## Testing Requirements

Add focused tests.

### Unit tests

- Material rarity normalisation.
- Material kind normalisation.
- Quantity parsing with commas.
- Legendary equivalent formula for each rarity.
- Choice chest totals remain separate from fixed material totals.
- Total legendary equivalent calculation.
- Net change over range.
- Duplicate same-kind/same-rarity handling.
- Conflicting duplicate handling.

### Service tests

- Start Materials session.
- Add one choice chest image.
- Add individual material images.
- Merge multiple image results into one pending batch.
- Correct material values.
- Approve Materials import.
- Cancel Materials import.
- Timeout/stale session cleanup.
- One active session per governor.
- One approved Materials import per governor per day.
- Admin override if supported.

### Reporting tests

- `/myinventory` includes Materials output option.
- Materials summary renders with one approved record and no graph.
- Materials summary renders with multiple approved records and graph.
- Delta and net change calculations are correct.
- Choice chest line is separate from fixed material lines.
- Existing RSS and Speedups reports still render unchanged.

### Export/audit tests

- `/export_inventory` includes Materials rows.
- `/inventory_import_audit` supports Materials filter.
- Corrected Materials imports show detected/corrected/final metadata.
- Failed/cancelled Materials imports retain debug references where expected.

### Vision/schema tests

- Structured output schema remains strict.
- Resources and Speedups schema tests still pass.
- Materials choice chest sample parses.
- Materials individual sample parses.
- Mixed/partial material result handles missing values.
- Low-confidence handling follows existing fallback/warning rules.

### Manual smoke tests

Run using the uploaded Materials samples:

```powershell
cd C:\discord_file_downloader
.\.venv\Scripts\Activate.ps1
python scripts\test_inventory_vision.py C:\rok\Materials_import1.png --type materials
python scripts\test_inventory_vision.py C:\rok\Materials_import2.png --type materials
python scripts\test_inventory_vision.py C:\rok\Materials_import3.png --type materials
python scripts\test_inventory_vision.py C:\rok\Materials_import4.png --type materials
```

Also run targeted pytest:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests -k "inventory and material"
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe -m pytest -q tests --ignore=archive
```

Use the project-standard test path guidance: avoid false failures from archived tests.

## Acceptance Criteria

Phase 2 is complete when:

- Materials are no longer disabled in the inventory import flow.
- Users can import Materials using up to 4 screenshots per governor/day.
- Choice chests and individual materials are detected and stored separately.
- Raw values are stored by material kind and rarity.
- Legendary-equivalent calculations are correct and tested.
- Duplicate/conflicting screenshot data is not silently overwritten.
- Users can correct Materials values through typed modals, not raw JSON.
- Approved Materials imports write SQL records linked to `InventoryImportBatch`.
- `/myinventory` can render Materials output with KPI cards and trend graph.
- `/myinventory` output selector includes Materials but not AP.
- `/export_inventory` includes Materials rows.
- `/inventory_import_audit` supports Materials imports.
- Failed/cancelled/corrected Materials imports are retained in admin debug where required.
- Restart/timeout safety is explicitly handled.
- Existing Resources and Speedups behaviour is unchanged.
- Tests cover formulas, parsing, service workflow, reporting, export, audit, and schema compatibility.
- Codex performs mandatory read-only review pass after implementation and testing.

## Required Codex Output Format

Codex must return:

- Summary
- File manifest
- New files
- Modified files
- SQL changes
- Helpers reused
- Refactor findings
- Test plan
- Deployment steps
- Structured Deferred Optimisations section
- Codex Review Summary after implementation/testing

## Suggested Opening Prompt for Codex

```text
Start Phase 2 review/scope for the Inventory Image Import Module: Materials Import. Phase 0 and Phase 1A–1F are complete. Use the updated task pack at docs/inventory/Codex Task Pack - Inventory Image Import Module.md and the Phase 2 Materials task pack. Scope is Materials only: up to 4 screenshots per governor/day, choice chests, individual materials, raw SQL storage, legendary-equivalent calculations, typed correction flow, /myinventory Materials output, export, and audit. Keep AP, /my_stats integration, export button under images, import-again button, and broad Resources/Speedups redesign out of scope. Begin with audit/scope only and STOP for architecture validation before coding.
```
