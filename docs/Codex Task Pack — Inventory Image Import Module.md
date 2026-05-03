# Codex Task Pack - Inventory Image Import Module

## Status Summary

Phase 0 is complete and deployed.

Phase 1A is complete, tested, and deployed.

Phase 1B is complete, tested, and deployed.

Phase 0 delivered:

- OpenAI Vision API setup documented in `docs/inventory_image_import_setup.md`.
- `.env` configured locally with OpenAI inventory vision settings.
- `openai` added to `requirements.txt`.
- Reusable async vision service added at `services/vision_client.py`.
- Local test utility added at `scripts/test_inventory_vision.py`.
- Strict structured-output schema fixed after deployment validation.
- Fallback escalation included and ready for Phase 1.
- No SQL inventory tables or Discord import workflow were added in Phase 0.

Phase 0 PRs:

- Mirror PR #44: Phase 0 foundation.
- Mirror PR #45: strict OpenAI structured-output schema fix.

Phase 1A delivered:

- Canonical `/import_inventory` command.
- Upload-first inventory image detection limited to `INVENTORY_UPLOAD_CHANNEL_ID`.
- `/import_inventory` restricted to `INVENTORY_UPLOAD_CHANNEL_ID`.
- Vision-derived image type instead of asking the user to choose Resources vs Speedups first.
- Resources and Speedups import foundation.
- Materials detection handled as disabled until Phase 2.
- SQL-isolated inventory DAL and service layer.
- Discord views for governor selection, confirmation, correction, rejection, and cancellation.
- Admin debug channel repost support for failed/rejected/corrected imports.
- Original public upload deletion after governor confirmation or timeout where permissions allow.
- SQL support script for Phase 1A tables, constraints, and indexes.

Phase 1A implementation files:

- `commands/inventory_cmds.py`
- `inventory/models.py`
- `inventory/parsing.py`
- `inventory/inventory_service.py`
- `inventory/dal/inventory_dal.py`
- `ui/views/inventory_views.py`
- `sql/inventory_phase1a_schema.sql`
- `tests/test_inventory_command_registration.py`
- `tests/test_inventory_parsing.py`
- `tests/test_inventory_schema_contract.py`
- `tests/test_inventory_service.py`
- `tests/test_inventory_upload_flow.py`

Phase 1A PR:

- Mirror PR #48: Inventory image import Phase 1A.

Phase 1A validation:

- Targeted Ruff checks passed.
- Focused inventory and command-registration pytest checks passed.
- Full test suite passed during promotion validation: `1056 passed, 8 skipped`.
- Production deployment completed.

Phase 1B delivered:

- Canonical `/myinventory` command.
- Latest Resources and Speedups inventory summary image.
- Generated mobile/desktop-suitable report images using SQL-backed inventory data.
- Range controls for 1M / 3M / 6M / 12M.
- Summary-only output when only one approved record exists.
- Summary plus trend graph when at least two approved records exist.
- Persistent reporting visibility preference.
- Materials kept disabled until Phase 2.

Phase 1B implementation files:

- `commands/inventory_cmds.py`
- `inventory/reporting_service.py`
- `inventory/report_image_renderer.py`
- `inventory/dal/inventory_reporting_dal.py`
- `ui/views/inventory_report_views.py`
- `tests/test_inventory_reporting_service.py`
- `tests/test_inventory_report_image_renderer.py`
- `tests/test_inventory_report_views.py`

Phase 1B validation:

- Phase 1B has been tested and deployed.
- Reporting service, image renderer, and report view test coverage added.

Phase 0 sample validation:

- `python scripts\test_inventory_vision.py C:\rok\rss_sample.png --type resources`
  - Result: `ok: true`
  - Model: `gpt-4.1-mini`
  - Confidence: `0.98`
  - Fallback used: `false`
- `python scripts\test_inventory_vision.py C:\rok\speedup_sample.png --type speedups`
  - Result: `ok: true`
  - Model: `gpt-4.1-mini`
  - Confidence: `0.98`
  - Fallback used: `false`

## Required Reading

Before progressing, read and review:

- `AGENTS.md`
- `README-DEV.md`
- `docs/Promotion Guide.md`
- `docs/inventory_image_import_setup.md`
- `docs/K98 Bot - Project Engineering Standards.md`
- `docs/K98 Bot - Coding Execution Guidelines.md`
- `docs/K98 Bot - Testing Standards.md`
- `docs/K98 Bot - Skills & Refactor Triggers.md`
- `docs/K98 Bot - Deferred Optimisation Framework.md`
- `commands/stats_cmds.py`
- `services/vision_client.py`
- `scripts/test_inventory_vision.py`

Reference `commands/stats_cmds.py` for current `/my_stats`, `/my_stats_export`, `/mykvkstats`, registry loading, account selection, and export patterns. Important: `/my_stats_export` currently contains direct SQL in the command body. Do not copy that pattern for `/export_inventory`; use service/DAL boundaries.

## Objective

Create an Inventory Import feature allowing players to upload Rise of Kingdoms inventory screenshots for:

- Resources
- Speedups
- Materials

Development is split into:

- Phase 0 - OpenAI Vision Integration Setup: complete and deployed.
- Phase 1A - Foundation + Resources/Speedups Import: complete, tested, and deployed.
- Phase 1B - Inventory reporting images and visibility preferences: complete, tested, and deployed.
- Phase 1C - Inventory export, admin audit, and interaction boundary hardening: next phase.
- Phase 1D - Final Resources/Speedups completion polish: planned follow-on.
- Phase 2 - Materials Import: later phase.

Work must proceed phase by phase. The next phase should begin with review/scope only per repository rules.

## Phase 0 - OpenAI Vision Integration Setup

### Current State

Phase 0 is complete.

Implemented files:

- `bot_config.py`
- `requirements.txt`
- `services/vision_client.py`
- `scripts/test_inventory_vision.py`
- `docs/inventory_image_import_setup.md`
- `tests/test_inventory_vision_client.py`
- `tests/test_inventory_vision_config.py`
- `tests/test_inventory_vision_script.py`

### Environment Variables

Current Phase 0 configuration:

```text
OPENAI_API_KEY=
OPENAI_VISION_MODEL=gpt-4.1-mini
OPENAI_VISION_FALLBACK_MODEL=gpt-5.2
OPENAI_VISION_PROMPT_VERSION=inventory_vision_v1
INVENTORY_UPLOAD_CHANNEL_ID=
INVENTORY_ADMIN_DEBUG_CHANNEL_ID=
```

`OPENAI_API_KEY` must only be loaded from `.env` or the runtime environment. Never commit the API key.

`INVENTORY_UPLOAD_CHANNEL_ID` is the only channel where inventory import commands and upload-first detection may run.

`INVENTORY_ADMIN_DEBUG_CHANNEL_ID` is the durable retained-image/debug channel for failed, rejected, corrected, or extreme-correction imports.

### Vision Service Behaviour

`services/vision_client.py`:

- Accepts image bytes plus optional filename/content type/import type hint.
- Uses OpenAI Responses API through the async client.
- Requests strict structured JSON.
- Returns a structured result with:
  - `ok`
  - `detected_image_type`
  - `values`
  - `confidence_score`
  - `warnings`
  - `prompt_version`
  - `model`
  - `fallback_used`
  - `error`
  - `raw_json`
- Handles missing API key gracefully.
- Handles OpenAI/API failures gracefully.
- Does not permanently store image files.
- Performs fallback escalation when the primary result fails or confidence is below threshold.

Fallback policy:

- Primary model: `gpt-4.1-mini`.
- Fallback model: `gpt-5.2`.
- Fallback threshold: confidence below `0.90` or retryable primary failure.
- Only one fallback attempt.
- If fallback fails, the service returns the primary structured failure.
- If fallback returns a worse result, preserve the stronger primary result where applicable.

### Strict Schema Decision

OpenAI strict structured outputs require every object schema to use `additionalProperties: false`. Phase 0 originally failed live testing because the nested `values` object allowed arbitrary keys.

The deployed schema fix now uses explicit sections:

- `values.resources`
- `values.speedups`
- `values.materials`

All nested objects declare `additionalProperties: false`.

The prompt tells the model to include all schema-required sections and use `null` for fields that do not apply to the detected image type.

### Local Test Utility

Use:

```powershell
cd C:\discord_file_downloader
.\.venv\Scripts\Activate.ps1
python scripts\test_inventory_vision.py C:\rok\rss_sample.png --type resources
python scripts\test_inventory_vision.py C:\rok\speedup_sample.png --type speedups
```

The script writes no inventory SQL records.

### Phase 0 Acceptance Criteria

All complete:

- OpenAI API key setup documented.
- API key loaded from `.env` only.
- Resources sample image returns structured JSON.
- Speedups sample image returns structured JSON.
- Fallback escalation exists and is tested.
- No SQL inventory tables are written.
- No full Discord import workflow is implemented yet.
- Failures are logged cleanly.

## Phase 1A - Foundation + Resources and Speedups

Phase 1A is complete, tested, and deployed.

Phase 1A established the import foundation and live intake path for Resources and Speedups. Phase 1A did not add reporting/export/audit commands beyond the schema and service foundations needed for later phases.

### Canonical Command Names

Use these command names:

- `/import_inventory`
- `/myinventory`
- `/export_inventory`
- `/inventory_import_audit`

Canonical import command name is `/import_inventory`.

Do not use `/inventory_import` for the user-facing command name.

### Commands

Add:

- `/import_inventory` - complete in Phase 1A.
- `/myinventory` - complete in Phase 1B.
- `/export_inventory` - Phase 1C.
- `/inventory_import_audit` - Phase 1C.

Commands must live in the target architecture, likely `commands/inventory_cmds.py`, with business logic in service modules and data access in DAL/repository modules.

Commands must use existing project command standards:

- `@versioned()`
- `@safe_command`
- `@track_usage()`
- `safe_defer(ctx)` where appropriate
- permission checks
- service handoff

Commands must not contain direct SQL or business logic.

`/import_inventory` must be restricted to `INVENTORY_UPLOAD_CHANNEL_ID` using the existing channel restriction pattern. Admin override may be allowed where consistent with existing command behaviour, but the command must not be available across arbitrary channels.

Upload-first detection must also be restricted to `INVENTORY_UPLOAD_CHANNEL_ID`. Do not scan arbitrary server image uploads.

### `/import_inventory` Flow

Status: complete in Phase 1A.

1. User runs `/import_inventory`.
2. Bot shows standard governor selector, reusing the `/mykvktargets` / registry account-selection pattern where practical.
3. User selects governor.
4. Bot opens or uses a private ephemeral upload workflow.
5. User uploads one screenshot.
6. Bot analyses image through `services/vision_client.py` without requiring an import type selection first.
7. Bot derives the image type from the vision result:
   - Resources
   - Speedups
   - Materials - disabled until Phase 2
   - Unknown - reject analysis and ask for retry where applicable
8. Bot returns confirmation summary:
   - detected image type
   - captured values
   - confidence score
   - model used
   - fallback-used flag
   - warnings/anomalies
9. User chooses:
   - Approve Import
   - Correct Data
   - Reject Import
   - Cancel Import
10. On approval, bot writes values to SQL with timestamp/history.
11. Bot generates output image if at least two approved records exist.

The normal flow must not ask the user to choose Resources vs Speedups before analysis. The user can correct or reject the detected result, and every avoidable click should be removed from the import path.

If the detected type is Materials during Phase 1, the bot must explain that Materials import is not available yet and no inventory values are written.

### Upload-First Flow

Status: complete in Phase 1A.

Users may start an import by uploading an image directly in the configured inventory channel instead of running `/import_inventory`.

1. User uploads an image attachment in `INVENTORY_UPLOAD_CHANNEL_ID`.
2. Bot confirms the message is in the configured inventory channel and contains a supported image attachment.
3. Bot reads the attachment bytes and records the source message/channel metadata.
4. Bot looks up governors registered to the uploading Discord user.
5. If no registered governors exist, bot replies with guidance to register a governor or use the command flow once registered.
6. If exactly one registered governor exists, bot proceeds with that governor.
7. If multiple registered governors exist, bot asks which governor the image is for using the standard account selector.
8. Once the governor is confirmed, bot deletes the original public upload message when it has permission to reduce the public visibility window.
9. If the user does not respond to the governor-selection follow-up before timeout, bot deletes the original public upload message when it has permission and exits cleanly.
10. After governor confirmation, the same vision analysis, confirmation, correction, reject, approval, daily limit, and debug retention rules as `/import_inventory` apply.

Upload-first detection must never run outside `INVENTORY_UPLOAD_CHANNEL_ID`.

Discord cannot convert a public user message into an ephemeral/private message after it has been posted. The intended privacy mitigation is to read the image, capture the needed bytes/source metadata, then delete the original upload message after governor confirmation or after timeout where permissions allow.

### Reject / Retry Flow

Status: partially complete in Phase 1A.

Phase 1A supports rejecting imports and admin debug retention. Phase 1C should review whether a richer same-session retry UX is still needed now that upload-first and command-led uploads share the inventory channel.

If user selects Reject Import:

1. Mark batch as rejected.
2. Post retained debug image and metadata to the admin debug channel.
3. Show screenshot guidelines and example image guidance for the selected import type.
4. Allow one retry in the same session.
5. If retry is rejected or fails, exit cleanly.
6. No SQL inventory values are written unless approved.

### Locking

One active import session per governor.

Do not lock by Discord user.

A user may upload for multiple registered governors in a day.

Status: complete in Phase 1A through SQL-backed active batch/session checks.

### Daily Limit

One approved import per governor, per import type, per day.

Admins may bypass if needed.

Status: complete in Phase 1A through service/DAL checks and SQL index support.

### Permissions

Normal users may only import for governors registered to them.

Admins may import for any governor.

Status: Phase 1A implemented registered-governor checks for normal users and admin override support.

### Upload Visibility

Command-led uploads should only ever be visible to:

- the uploading user
- admins

Upload-first images are initially visible in the configured inventory channel because they are user-posted public messages. The bot should minimise the visibility window:

- Delete the original public upload message after governor confirmation and byte capture where permissions allow.
- Delete the original public upload message after selection timeout where permissions allow.
- Continue the remaining workflow through ephemeral/private interaction responses where possible.
- Do not retain the original image after successful approved import unless debug/audit retention is required.

### Image Retention Decision

Default:

- Delete or do not retain the original user-uploaded image after successful approved import unless retention is required for debug/audit.

Retain/log for admin debug if:

- image analysis failed
- image was rejected
- values were corrected
- very large correction warning was triggered

Decision applied after Phase 0:

- Use an admin debug channel post as the durable debug/audit mechanism.
- Do not rely only on the user's original Discord attachment URL.
- Do not use admin DM as the retention mechanism.
- Store the admin debug channel ID and admin debug message ID/reference on the import batch.

Admin debug post should include:

- screenshot/image attachment or durable Discord-hosted copy
- GovernorID
- DiscordUserID
- import type
- batch ID
- status
- confidence score
- vision model
- prompt version
- fallback-used flag
- warnings
- detected JSON
- corrected JSON, if applicable
- final JSON, if applicable
- error JSON, if applicable

### Resource Parsing

Resource rows:

- Food
- Wood
- Stone
- Gold

Columns:

- From Items
- Total Resources

Value parsing examples:

- `7.0B` = `7,000,000,000`
- `122.2M` = `122,200,000`
- `30K` = `30,000`
- `30000` = `30,000`
- `0` = `0`

### Speedup Parsing

Speedup rows:

- Building Speedup
- Research Speedup
- Training Speedup
- Healing Speedup
- Speedup / Universal

Values:

- `122d 2h 42m`
- `935d 0h 7m`
- `239d`
- `2h 42m`
- `0`

Store internally as:

- `total_minutes`
- `total_hours`
- `total_days_decimal`

Report primarily as days.

### Correction Workflow

Users may correct values freely.

The bot must:

- validate corrected format
- reject negative values
- warn on very large corrections
- require second confirmation for extreme changes
- log original detected value and corrected value
- retain corrected image/debug reference for admin review through the admin debug channel post

### SQL Design

Recommended structure:

`InventoryImportBatch`

- ImportBatchID
- GovernorID
- DiscordUserID
- ImportType
- FlowType
- SourceMessageID
- SourceChannelID
- ImageAttachmentURL
- AdminDebugChannelID
- AdminDebugMessageID
- Status
- CreatedAtUtc
- ApprovedAtUtc
- RejectedAtUtc
- RetryCount
- VisionModel
- VisionPromptVersion
- FallbackUsed
- ConfidenceScore
- DetectedJson
- CorrectedJson
- FinalJson
- WarningJson
- ErrorJson
- IsAdminImport
- OriginalUploadDeletedAtUtc
- ExpiresAtUtc

`GovernorResourceInventory`

- ResourceRecordID
- ImportBatchID
- GovernorID
- ScanUtc
- ResourceType
- FromItemsValue
- TotalResourcesValue

`GovernorSpeedupInventory`

- SpeedupRecordID
- ImportBatchID
- GovernorID
- ScanUtc
- SpeedupType
- TotalMinutes
- TotalHours
- TotalDaysDecimal

SQL schema changes belong in the SQL Server repository, not only in Python.

### `/myinventory`

Status: complete in Phase 1B.

Purpose:

View latest generated inventory summary image.

Options:

- governor: optional
- view: Resources / Speedups / Materials / All
- range: 1M / 3M / 6M / 12M
- visibility: Only Me / Public Output Channel

Visibility preference must be persistent.

Once selected, it becomes the default until changed. Do not ask every time.

Output image buttons:

- 1M
- 3M
- 6M
- 12M

Do not add:

- Export Data button
- Import Again button

Output behaviour:

- If only one approved record exists, show latest summary only and no trend graph.
- If two or more approved records exist, show summary plus trend graph.

### `/export_inventory`

Status: Phase 1C.

Purpose:

Export raw inventory records for the user's registered governors.

Should follow the same user-facing style as `/my_stats_export`:

- Excel
- CSV
- Google Sheets-compatible
- ephemeral response
- temporary file cleanup
- clear usage instructions

Architecture note:

- Do not copy the direct SQL pattern from `/my_stats_export`.
- Implement inventory export through service and DAL/repository layers.

### Phase 1 Output Images

Status: Resources and Speedups output images complete in Phase 1B.

Shared output-image direction:

- Images should be suitable for both mobile and desktop viewing.
- Use a strong blue dashboard background.
- Use readable high-contrast text and clear boxed KPI areas.
- Top-left corner should show the output category logo:
  - Resources: `assets/rss_logo.png`
  - Speedups: `assets/speedup_logo.png`
- Top-right corner should show the user's Discord avatar where available.
- Range controls are Discord buttons below the image, not rendered as part of the static image.

Resources output should show:

- Use `TotalResourcesValue` for all displayed RSS totals, deltas, capacity calculations, velocity, forecast, and graph data.
- First row: five summary boxes:
  - Food
  - Wood
  - Stone
  - Gold
  - Total RSS
- Each first-row box should show:
  - RSS type title with the matching Rise of Kingdoms resource logo from `assets/RSS/`
  - latest total value using compact K/M/B formatting with up to 1 decimal place
  - delta over selected range using green `+` text for positive values and red `-` text for negative values
- Delta rule:
  - delta = latest approved value minus earliest approved value inside the selected range
  - if no earlier approved point exists inside the selected range, show `N/A`
- Second row: four insight boxes:
  - RSS Velocity
  - RSS Troop Training Capacity
  - RSS Troop Healing Capacity
  - RSS Forecast
- RSS Velocity:
  - total RSS increase per day based on the selected time range
  - example: if total RSS increased by 600m over 90 days, velocity is `6.7m/day`
  - value is always displayed as `m/day` with 1 decimal place
  - green `+` text for positive velocity and red `-` text for negative velocity
  - show `N/A` if range delta is unavailable
- RSS Troop Training Capacity:
  - display maximum mixed troops trainable from current available resources
  - include the training logo from `assets/Training/Training.png`
  - floor capacity to 1 decimal place
  - identify the limiting resource
  - show equivalent power/Zenith and MGE points
  - training costs per 1,000,000 troops:
    - Food: 533,000,000
    - Wood: 533,000,000
    - Stone: 400,000,000
    - Gold: 400,000,000
  - conversion: every 1m troops = 10m Power / Zenith Points and 100m MGE Points
- RSS Troop Healing Capacity:
  - display maximum mixed troops healable from current available resources
  - include the healing logo from `assets/healing/healing.png`
  - floor capacity to 1 decimal place
  - identify the limiting resource
  - show equivalent kills and kill points
  - healing costs per 1,000,000 troops:
    - Food: 213,300,000
    - Wood: 213,300,000
    - Stone: 160,000,000
    - Gold: 160,000,000
  - conversion: every 1m healed troops = 5m kills and 20m kill points
- RSS Forecast:
  - display expected total RSS value in 30 days based on current RSS velocity
  - formula: latest total RSS + (`velocity_per_day` * 30)
  - use compact K/M/B formatting with up to 1 decimal place
  - show `N/A` if velocity is unavailable
- Graph:
  - area graph below the summary/insight rows
  - use approved scan timestamps only
  - overlay Food, Wood, Stone, and Gold
  - include all approved data points within the selected range
  - no trend graph when only one approved record exists
  - show summary/insight boxes only when trend data is insufficient
- Default range: 1M
- Switchable ranges/buttons: 1M / 3M / 6M / 12M

Speedups output should show:

- Use approved speedup records only.
- Values display in whole days only, with comma separators and no decimals, e.g. `1,000d`.
- Delta rule:
  - delta = latest approved value minus earliest approved value inside the selected range
  - if no earlier approved point exists inside the selected range, show `N/A`
  - green `+` text for positive values and red `-` text for negative values
- First row: three summary boxes:
  - Universal
  - Training
  - Healing
- Each first-row box should show:
  - speedup type title with the matching Rise of Kingdoms logo
  - latest total value in days
  - delta over selected range
- Second row: two capacity boxes:
  - Total Speedup Training Capacity
  - Total Healing Speedup Capacity
- Total Speedup Training Capacity:
  - source value = Training + Universal speedups
  - include the training logo from `assets/Training/Training.png`
  - display total days as whole days
  - conversion baseline: `100 days = 136,000 troops / 1.36m Power (Zenith Points) / 13.6m MGE Points`
  - scale linearly from the current Training + Universal total
- Total Healing Speedup Capacity:
  - source value = Healing + Universal speedups
  - include the healing logo from `assets/healing/healing.png`
  - display total days as whole days
  - conversion baseline: `100 days = 6.1m T5 troops healed / 6.1m kills / 122m Kill Points`
  - scale linearly from the current Healing + Universal total
- Graph:
  - area graph below the summary/capacity rows
  - use approved scan timestamps only
  - overlay Universal, Training, and Healing
  - include all approved data points within the selected range
  - no trend graph when only one approved record exists
  - show summary/capacity boxes only when trend data is insufficient
- Default range: 1M
- Switchable ranges/buttons: 1M / 3M / 6M / 12M

## Phase 1C - Export, Audit, and Boundary Hardening

Phase 1C should be a linked follow-on PR after Phase 1B, not an untracked deferred optimisation.

Recommended scope:

- `/export_inventory`
- `/inventory_import_audit`
- raw inventory export using service/DAL boundaries
- admin audit filtering and debug-message reference access
- compare detected, corrected, and final JSON for retained admin review
- inventory interaction boundary hardening from Phase 1A review

Boundary hardening goals:

- Keep new commands thin and service-led.
- Avoid adding more orchestration to `ui/views/inventory_views.py`.
- Move reusable admin debug-post/audit preparation logic out of the view layer where practical.
- Prefer primitive service inputs such as `discord_user_id`, `governor_id`, and `is_admin` instead of passing Discord user objects deeper into service functions.
- Preserve Phase 1A behaviour while tightening layer ownership.
- Reassess whether same-session retry after reject needs richer UX or whether upload-first replacement is sufficient.

Phase 1C should remain Materials-free. Materials belong to Phase 2.

## Phase 1D - Final Resources/Speedups Completion Polish

Phase 1D should be a small follow-on phase after Phase 1C to finish the remaining
Resources and Speedups user-experience surface before declaring Phase 1 complete.

Recommended scope:

- Add export buttons under `/myinventory` report output where appropriate.
- Reuse the `/export_inventory` service/DAL path rather than adding export SQL or file generation to views.
- Perform targeted OCR/prompt tuning for Resources and Speedups only, based on production smoke-test failures or recurring admin-audit findings.
- Review the Phase 1A/1B/1C scenario matrix end to end for Resources and Speedups:
  - no registered governors
  - governor selector timeout/no approval
  - reject then repeat import
  - same-day duplicate approved import
  - random/unknown image
  - Materials-disabled image
  - export/audit access and empty-data handling
- Fix production smoke-test UX issues from Phase 1C deployment:
  - shared account picker dropdown placeholder says `Choose an account to view...`; change to a generic `Select Governor` so it fits inventory, stats, and targets flows.
  - after a governor is selected, the old picker remains active and stale select/lookup/refresh interactions can fail; disable or update the picker after successful selection.
  - user-facing Inventory Import Review embeds show model/fallback details that should remain admin-only.
  - detected Resources/Speedups values need user-friendly formatting; speedups should show days/hours/minutes or rounded days only, not raw minute totals.
  - raw JSON correction is too error-prone for normal users; replace it with typed correction fields for the detected import type.
  - corrected data is currently shown in a separate message, making it unclear that the original import must still be approved; update the original review message and make the approval state explicit.
  - Reject Import and Cancel Import are unclear as separate user actions; simplify or clearly distinguish them based on audit/debug retention needs.
  - buttons can remain clickable after terminal actions and produce failed interactions; ensure controls are disabled/updated after approve, correct, reject, cancel, and timeout.
- Fix OCR/prompt accuracy issues observed in Phase 1C smoke testing:
  - speedup screenshots can return high confidence (`0.95`-`0.98`) while one or more rows are materially wrong.
  - observed example: Healing Speedup should be read as `505d 3h 37m`, but was detected as about `50.52` days / `72,757` minutes.
  - the same screenshot may fail or produce different results across attempts/model versions, so confidence alone is not sufficient as a correctness signal.
  - add deterministic post-OCR validation and anomaly checks for speedup rows, especially missing hundreds/thousands digits and mismatches between days/hours/minutes and total minutes.
- Fix same-day duplicate import enforcement:
  - Phase 1 smoke testing allowed multiple approved imports for the same governor/import type/day.
  - preserve an admin override for repeated same-day imports because it is useful for testing and correction workflows.
  - normal users should be blocked from approving a second import of the same type for the same governor on the same UTC day.
- Investigate `/myinventory` runtime failure:
  - `/myinventory` should work after Phase 1B for Resources and Speedups reports.
  - observed response: `Inventory reporting preferences are not available yet. Please contact an admin.`
  - likely area to check first: `dbo.InventoryReportPreference` deployment/permissions and `inventory_reporting_dal.fetch_visibility_preference`.
  - preserve the persistent visibility preference behaviour; if the preference table is unavailable, return a clearer admin-facing diagnostic in logs and a useful user-facing fallback where safe.
- Confirm documentation and user-facing guidance are aligned with final Phase 1 behaviour.

Out of scope for Phase 1D:

- Materials processing or reporting.
- `/my_stats` integration.
- The stats export SQL refactor tracked by GitHub issue #46.
- Broad OCR redesign beyond targeted Resources/Speedups tuning.

Phase 1 for Resources and Speedups should be considered complete only after Phase 1D
validates import, report, export, audit, retry/repeat, and targeted OCR/prompt behaviour
against the documented scenario matrix.

## Phase 2 - Materials

Materials remain disabled in Phase 1.

### Materials Image Inputs

Up to 3 images.

Image type 1:

- Universal Equipment Material Choice Chest
- Normal
- Advanced
- Elite
- Epic
- Legendary

Image type 2/3:

- Leather
- Iron Ore
- Ebony
- Animal Bone

Each can appear as:

- Normal
- Advanced
- Elite
- Epic
- Legendary

### Material Conversion

Store raw quantities and calculate legendary equivalent:

- Normal / 256
- Advanced / 64
- Elite / 16
- Epic / 4
- Legendary / 1

Choice chests should be stored separately from fixed material types.

### Materials Output

Show:

- Legendary equivalent per material type
- Choice chest legendary equivalent separately
- Total legendary equivalent
- Net change over last 30 days
- Line graph by material type

## Validation and Warning Rules

Warnings, not hard blocks unless data is unreadable.

Flag:

- Unknown image type
- Missing required rows
- Missing required values
- Unreadable value
- Duplicate screenshot type
- Value changed by more than 50% from latest approved record
- Value decreased unexpectedly
- Total resources lower than from-items resources
- Exact duplicate of latest approved values
- Confidence score below threshold

Confidence thresholds:

- `>= 0.90`: normal confirmation
- `0.70-0.89`: confirmation with warning
- `< 0.70`: reject analysis and ask for retry

Phase 0 note:

- The vision service escalates to fallback when confidence is below `0.90` before Phase 1 applies the user-facing warning/retry decision.

## Screenshot Guidelines Message

Reusable message:

```text
Upload a full screenshot.
Do not crop the image.
Make sure all rows and values are visible.
Use English game language if possible.
Do not upload edited or compressed screenshots.
```

Resources:

- Must show Food, Wood, Stone, Gold, From Items, and Total Resources.

Speedups:

- Must show Building, Research, Training, Healing, and Universal Speedups.

Materials:

- Disabled until Phase 2.

## Admin Debug / Audit

Add:

- `/inventory_import_audit`

Admin only.

Status: Phase 1C.

Purpose:

- View failed imports
- View rejected imports
- View corrected imports
- Compare detected vs corrected values
- Filter by governor, user, date, import type
- Access retained debug image reference from the admin debug channel post

## Testing Expectations

### Phase 0

Complete:

- Test OpenAI Vision service with resource and speedup sample images.
- Confirm structured JSON.
- Confirm missing API key failure.
- Confirm no SQL writes.
- Confirm strict structured-output schema accepted by OpenAI.
- Confirm fallback escalation is tested.

### Phase 1

Test:

- registered governor permission - Phase 1A complete
- admin override - Phase 1A complete
- `/import_inventory` restricted to `INVENTORY_UPLOAD_CHANNEL_ID` - Phase 1A complete
- upload-first detection restricted to `INVENTORY_UPLOAD_CHANNEL_ID` - Phase 1A complete
- upload-first ignores images outside the configured inventory channel - Phase 1A complete
- upload-first no registered governors path - Phase 1A complete
- upload-first single registered governor shortcut - Phase 1A complete
- upload-first multi-governor selector - Phase 1A complete
- upload-first timeout deletes original public upload where permissions allow - Phase 1A complete
- image type derived without a required import type hint - Phase 1A complete
- unsupported Materials detection in Phase 1 - Phase 1A complete
- one active session per governor - Phase 1A complete
- one approved import per governor/type/day - Phase 1A complete
- reject + one retry - reject complete in Phase 1A; retry UX should be reassessed in Phase 1C
- correction workflow - Phase 1A complete
- large correction warning - review/extend in Phase 1C if additional comparison/audit UX is needed
- admin debug channel logging - Phase 1A complete
- image output generation - Phase 1B complete for Resources and Speedups
- visibility preference persistence - Phase 1B complete
- `/export_inventory` - Phase 1C
- `/inventory_import_audit` - Phase 1C
- restart/persistence behaviour for active/imported state - Phase 1A complete for import batches; Phase 1B complete for reporting preferences
- cache safety where applicable - continue in Phase 1C

### Phase 1B

Complete, tested, and deployed.

Delivered scope:

- `/myinventory`
- latest inventory summary view
- generated output image for Resources and Speedups
- range buttons: 1M / 3M / 6M / 12M
- no trend graph when only one approved record exists
- trend graph when at least two approved records exist
- persistent visibility preference

Completed Phase 1B audit points:

- Confirm live Phase 1A SQL schema is the source of truth before building read/report queries.
- Verify command name remains canonical: `/myinventory`.
- Review image generation/output helpers before creating new graph/export helpers.
- Define the SQL-backed persistent visibility preference contract.
- Keep Materials out of all output/reporting paths until Phase 2.

### Phase 1C

Next phase.

Recommended scope:

- `/export_inventory`
- `/inventory_import_audit`
- raw inventory export files using service/DAL boundaries
- admin audit filtering and debug-message reference access
- targeted cleanup of Phase 1A inventory view/service boundaries

Recommended Phase 1C audit points:

- Verify command names remain canonical: `/export_inventory`, `/inventory_import_audit`.
- Keep `/export_inventory` service/DAL-based and do not copy direct SQL from `/my_stats_export`.
- Confirm GitHub issue #46 remains the tracking item for the existing stats export direct-SQL refactor.
- Do not expand into `/my_stats` integration.
- Do not add Materials support before Phase 2.

### Phase 1D

Planned follow-on phase.

Recommended scope:

- `/myinventory` export buttons wired to the Phase 1C export service/DAL path.
- Targeted Resources/Speedups OCR and prompt tuning based on smoke-test/audit evidence.
- Final Phase 1 Resources/Speedups scenario validation and documentation alignment.

Do not include:

- Materials processing.
- `/my_stats` integration.
- Stats export SQL refactor work tracked by GitHub issue #46.

### Phase 2

Test:

- 1-image material chest upload
- 2/3-image material upload
- legendary equivalent calculations
- material correction workflow
- material output image

## Deferred / Downstream Work

Do not include in Phase 1:

- `/my_stats` integration
- Materials processing
- Import Again button
- Export button under image
- Full OCR tuning beyond initial prompt version

Do not include in Phase 1B:

- Materials processing
- `/my_stats` integration
- Import Again button
- Export button under image
- `/export_inventory`
- `/inventory_import_audit`
- Further OCR/prompt tuning unless a Phase 1A production issue specifically requires it

Do not include in Phase 1C:

- Materials processing
- `/my_stats` integration
- Import Again button
- Export button under image
- Further OCR/prompt tuning unless a Phase 1A production issue specifically requires it

Downstream task:

- Integrate inventory summaries into existing `/my_stats` or future refactored `/my_stats` experience.

## Existing Deferred Optimisation Tracking

### GitHub Issue Reference

- Area: `commands/stats_cmds.py`
- Type: architecture
- GitHub issue: https://github.com/cwatts6/K98-bot-mirror/issues/46
- Title: `Deferred: extract /my_stats_export SQL into service/DAL`
- Description: `/my_stats_export` contains direct SQL inside the command body. Inventory export work should not copy this pattern, and stats export remains harder to test and maintain while command code owns DB access.
- Suggested Fix: Extract stats export data access into a dedicated DAL/service in a later stats-export refactor. Keep the command responsible only for validation, permission/response handling, and service handoff.
- Impact: medium
- Risk: medium
- Scoring: Impact 3, Frequency 3, Risk Reduction 4, Effort 3, Priority Score 7
- Recommendation: Good batch candidate
- Dependencies: Separate stats export refactor task

Do not create a duplicate issue for this item. Reference issue #46 whenever Phase 1C discusses avoiding the `/my_stats_export` direct-SQL pattern.

## Suggested Next Chat Opening Prompt

```text
Start Phase 1C review/scope for the Inventory Image Import Module. Phase 0, Phase 1A, and Phase 1B are complete, tested, and deployed. Use the updated in-repo task pack at C:\discord_file_downloader\docs\Codex Task Pack — Inventory Image Import Module.md. Phase 1A delivered /import_inventory, upload-first import in INVENTORY_UPLOAD_CHANNEL_ID, Vision-derived image type, Resources/Speedups SQL-backed imports, correction/reject/cancel flow, and admin debug channel retention. Phase 1B delivered /myinventory, generated Resources/Speedups report images, 1M/3M/6M/12M range controls, summary-only output for one approved record, trend graphs for two or more approved records, and persistent visibility preference. For Phase 1C, assess and scope /export_inventory, /inventory_import_audit, raw inventory export files, admin audit filtering/debug-message reference access, and targeted cleanup of Phase 1A inventory view/service boundaries. Keep commands thin, use service/DAL boundaries, do not copy the direct SQL pattern from /my_stats_export, reference GitHub issue #46 for the existing stats export SQL refactor, keep Materials out of scope until Phase 2, and begin with audit/scope only per repo rules.
```
