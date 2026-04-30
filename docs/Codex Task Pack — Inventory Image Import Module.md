# Codex Task Pack - Inventory Image Import Module

## Status Summary

Phase 0 is complete and deployed.

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
- Phase 1 - Foundation + Resources/Speedups Import: next phase.
- Phase 2 - Materials Import: later phase.

Work must proceed phase by phase. Phase 1 should begin with review/scope only per repository rules.

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

## Phase 1 - Foundation + Resources and Speedups

Phase 1 is the next implementation phase.

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

- `/import_inventory`
- `/myinventory`
- `/export_inventory`
- `/inventory_import_audit`

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

### Daily Limit

One approved import per governor, per import type, per day.

Admins may bypass if needed.

### Permissions

Normal users may only import for governors registered to them.

Admins may import for any governor.

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

Resources output should show:

- Food
- Wood
- Stone
- Gold
- Overall total RSS
- Net change over selected range
- Line graph by resource type
- Default range: 1M
- Switchable: 1M / 3M / 6M / 12M

Speedups output should show:

- Universal total
- Training total
- Healing total
- Building total
- Research total
- Net change over selected range
- Line graph by speedup type

Conversions:

Healing + Universal:

- 700 days = 1B Kill Points and 55m kills

Training + Universal:

- 731 days = 10m Power, 10m Zenith Points, 100m MGE Points

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

- registered governor permission
- admin override
- `/import_inventory` restricted to `INVENTORY_UPLOAD_CHANNEL_ID`
- upload-first detection restricted to `INVENTORY_UPLOAD_CHANNEL_ID`
- upload-first ignores images outside the configured inventory channel
- upload-first no registered governors path
- upload-first single registered governor shortcut
- upload-first multi-governor selector
- upload-first timeout deletes original public upload where permissions allow
- image type derived without a required import type hint
- unsupported Materials detection in Phase 1
- one active session per governor
- one approved import per governor/type/day
- reject + one retry
- correction workflow
- large correction warning
- admin debug channel logging
- image output generation
- visibility preference persistence
- `/export_inventory`
- restart/persistence behaviour for active/imported state
- cache safety where applicable

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

Downstream task:

- Integrate inventory summaries into existing `/my_stats` or future refactored `/my_stats` experience.

## Deferred Optimisation Captured During Phase 0

### Deferred Optimisation

- Area: `commands/stats_cmds.py`
- Type: architecture
- Description: `/my_stats_export` contains direct SQL inside the command body. Phase 1 inventory export work should avoid copying that pattern.
- Suggested Fix: Extract inventory export data access into a dedicated DAL/service. Consider a later stats export refactor separately.
- Impact: medium
- Risk: medium
- Dependencies: Phase 1 inventory export design

## Suggested Next Chat Opening Prompt

```text
Start Phase 1 review/scope for the Inventory Image Import Module. Phase 0 is complete and deployed. Use the updated task pack at C:\Users\cwatt\Downloads\Codex Task Pack - Inventory Image Import Module.md. Standardise command name to /import_inventory. Use admin debug channel posts for retained failed/rejected/corrected images. Begin with audit/scope only per repo rules.
```
