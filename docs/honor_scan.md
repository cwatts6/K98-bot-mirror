# 🏅 KVK Honour Ingestion & Reporting Pipeline

File: `docs/honor_scan.md`  
Audience: Developers & feature maintainers  
Last Updated: 2025-10-19

---

Purpose
- Describe the honour ingestion pipeline and the expected input formats, file naming patterns, processing steps, and embed output behavior.

Overview
- The KVK Honour pipeline ingests per-KVK honour snapshots and refreshes leaderboard embeds in Discord.
- It complements Pre-KVK and All-Kingdom flows and supports multiple input channels depending on the data type.

Accepted inputs & filename patterns
- Typical accepted filename (exact match semantics):
  - 1198_databook.xlsx
- Allowed prefixes:
  - TEST_1198_databook.xlsx
  - DEMO_1198_databook.xlsx
  - SAMPLE_1198_databook.xlsx
- Any file starting with "1198_databook" and ending with ".xlsx" is accepted.

Processing flow (high level)
1. DL_bot.py on_message fast-path or processing_pipeline.py file handling accepts the upload and enqueues processing.
2. processing_pipeline.py orchestrates:
   - Archive/copy of the original file (download folder),
   - Verification that the latest sheet exists and can be parsed (pandas/openpyxl),
   - Convert to canonical stats.xlsx in DOWNLOAD_FOLDER for downstream embed generation.
3. Stats sheet is parsed; additional transforms build leaderboard slices and compute deltas for embeds.

Common validation checks
- Required sheet presence: the code expects at least one sheet; the last sheet is used by default.
- Columns: required columns should match the stats schema. If key columns are absent, processing logs an error and the job is moved to FAILED_LOG.

Embed & reporting
- After successful processing, the bot builds an embed (or set of embeds) with:
  - Top N players, honour deltas, and relevant metadata (KVK number, source uploader, timestamp).
  - A downloadable XLSX attachment (stats.xlsx) may be attached when requested or when the embed consumer needs the source.
- The embed footer contains freshness metadata, and the bot uses CUSTOM_AVATAR_URL where provided.

Troubleshooting
- "Source file does not exist" error: file path mismatch or race in moving the uploaded file. Check download folder and input log entries.
- Missing "updated_on" column: code injects a timestamp column if absent.
- Excel write or read errors: confirm openpyxl is installed and not in a conflicting version. Reproduce locally with pandas/openpyxl.

Operational notes
- Keep DOWNLOAD_FOLDER and LOG_DIR backed up if running critical archival processes.
- When changing the parsing logic, add unit tests that cover:
  - Missing columns,
  - Sheet name variations,
  - Large file sizes and memory usage.
