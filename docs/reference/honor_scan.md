# Honor Ingestion And Reporting

Purpose: describe the KVK honor upload/import path and reporting surfaces.

## Main Files

- `DL_bot.py` handles uploads in `HONOR_CHANNEL_ID`.
- `honor_importer.py` parses and ingests honor workbooks.
- `stats_alerts/honors.py` reads latest honor rankings for embeds/commands.
- `honor_rankings_view.py` builds interactive ranking views.
- `commands.kvk_cmds` exposes the canonical `/kvk rankings type:honor` player surface.
- `commands/stats_cmds.py` temporarily retains `/honor_rankings` as a deprecated redirect and
  exposes `/honor purge_last` for admin cleanup.

## Accepted Upload Names

The current upload handler accepts `.xlsx` files matching:

```text
1198_honor*.xlsx
TEST_1198_honor*.xlsx
DEMO_1198_honor*.xlsx
SAMPLE_1198_honor*.xlsx
```

Separators around `1198` and `honor` may be underscore, space, or hyphen.

## Processing Flow

1. `DL_bot.py` receives an attachment in `HONOR_CHANNEL_ID`.
2. The attachment filename is validated.
3. The workbook is read and parsed by `parse_honor_xlsx`.
4. Blocking parse/ingest work is offloaded through the common offload helper.
5. `ingest_honor_snapshot` writes SQL-backed snapshot rows and emits telemetry.
6. Ranking services/views read the latest scan through the KVK rankings service path; the legacy
   `/honor_rankings` command only redirects players to `/kvk rankings type:honor`.

## Validation And Tests

Relevant tests:

- `tests/test_honor_importer.py`
- `tests/test_honor_rankings_view.py`

When changing this pipeline, cover:

- missing required workbook columns
- blank/NaN names
- rollback on ingest failure
- telemetry on success/failure
- empty latest-ranking output
- ranking view formatting

## Operational Notes

- SQL table/view names must be validated against `C:\K98-bot-SQL-Server`.
- Keep parsing and database work out of the Discord event loop.
- Preserve user-safe upload error messages in `DL_bot.py`.
- Do not infer schema from Python if SQL definitions exist.
