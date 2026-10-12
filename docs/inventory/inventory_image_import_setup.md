# Inventory Image Import Setup

This document covers Phase 0 of the inventory image import module. Phase 0 creates the
OpenAI Vision foundation only. It does not add Discord import commands, SQL inventory tables,
or inventory writes.

## OpenAI API Setup

1. Go to the OpenAI Platform.
2. Create or sign into the OpenAI account that will own billing for the bot.
3. Add billing details.
4. Add an initial billing credit or payment method.
5. Create a new API key.
6. Store the key securely.
7. Add the key to the bot `.env` file.
8. Never commit the API key to GitHub.

## Environment Variables

Add these entries to `.env`:

```text
OPENAI_API_KEY=
OPENAI_VISION_MODEL=gpt-4.1-mini
OPENAI_VISION_FALLBACK_MODEL=gpt-5.2
OPENAI_VISION_PROMPT_VERSION=inventory_vision_v1
```

`OPENAI_VISION_MODEL` is the normal extraction model. `OPENAI_VISION_FALLBACK_MODEL` is used
when the first pass returns low confidence or a retryable malformed result. The default fallback
is stronger and costlier, so the service only escalates once.

## Local Test Script

Use the local script with a sample resources or speedups screenshot:

```powershell
cd C:\discord_file_downloader
.\.venv\Scripts\Activate.ps1
python scripts\test_inventory_vision.py C:\path\to\resources_sample.png --type resources
python scripts\test_inventory_vision.py C:\path\to\speedups_sample.png --type speedups
```

The script prints structured JSON with:

- detected image type
- extracted values
- confidence score
- warnings
- model used
- fallback-used flag
- error details when extraction fails

The script writes no inventory SQL records.

## Sample Screenshot Guidance

Use full, unedited screenshots. Do not crop the image. Make sure all rows and values are visible.
Use English game language if possible. Avoid edited or compressed screenshots.

Resources screenshots must show Food, Wood, Stone, Gold, From Items, and Total Resources.

Speedups screenshots must show Building, Research, Training, Healing, and Universal Speedups.

Materials screenshots may be exercised in the Phase 0 local Vision/testing flow, but Phase 0 does
not provide downstream Discord import support, SQL inventory writes, or production materials import
handling. Full materials import support remains a Phase 2 feature.

## Phase 1 Debug Image Retention

For failed, rejected, corrected, or extreme-correction imports, Phase 1 should repost the image to
an admin debug channel with the governor, Discord user, import type, batch ID, confidence, warnings,
and detected/corrected values. Store that admin debug message/channel reference on the import batch.

Do not rely only on the user's original attachment URL, because the original message may be removed
or become hard to audit later. Admin DMs are not required.
