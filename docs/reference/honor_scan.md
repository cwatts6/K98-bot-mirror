# Honor Ingestion And Reporting

Purpose: describe the KVK honor upload/import path and reporting surfaces.

## Main Files

- `upload_routes/honor_route.py` handles uploads in `HONOR_CHANNEL_ID`.
- `honor_importer.py` parses and ingests honor workbooks.
- `services/honor_import_audit_service.py` owns Honor-specific generic import audit wrappers.
- `services/import_audit_service.py` and `stats/dal/import_audit_dal.py` own the generic audit
  service/DAL boundary.
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

1. `upload_routes/honor_route.py` receives an attachment in `HONOR_CHANNEL_ID`.
2. The attachment filename is validated.
3. The route starts a best-effort generic `ImportAuditBatch` with `ImportKind = honor` and
   `SourceType = discord_upload_xlsx`.
4. The workbook is read and parsed by `parse_honor_xlsx`; the route records
   `honor_xlsx_parse`.
5. Blocking parse/ingest work is offloaded through the common offload helper.
6. `ingest_honor_snapshot` writes SQL-backed snapshot rows and emits telemetry; the route records
   `honor_sql_ingest`.
7. Successful domain imports correlate the generic audit batch to
   `ExternalBatchTable = dbo.KVK_Honor_Scan` and `ExternalBatchId = <KVK_NO>:<ScanID>`.
8. The route triggers the existing post-import stats refresh and records
   `honor_post_import_refresh`.
9. Ranking services/views read the latest scan through the KVK rankings service path; the legacy
   `/honor_rankings` command only redirects players to `/kvk rankings type:honor`.

## Generic Import Audit Contract

Task C Slice 4 adopted the generic durable import audit model for Honor in production PR #493.

Expected batch fields for successful Honor uploads:

- `ImportKind = honor`
- `SourceType = discord_upload_xlsx`
- `ExternalBatchTable = dbo.KVK_Honor_Scan`
- `ExternalBatchId = <KVK_NO>:<ScanID>`
- `RowsInSource = RowsStaged = RowsWritten`
- `RowsSkipped = 0`
- `Status = completed`

Expected phases:

- `honor_xlsx_parse`
- `honor_sql_ingest`
- `honor_post_import_refresh`

Production smoke on 2026-06-29 confirmed batch 7 completed for `1198_honor.xlsx` with
`ExternalBatchId = 15:92`, `RowsInSource = 562`, `RowsStaged = 562`, `RowsWritten = 562`,
`RowsSkipped = 0`, and all three phases completed with no errors.

## Validation And Tests

Relevant tests:

- `tests/test_honor_upload_route.py`
- `tests/test_honor_importer.py`
- `tests/test_honor_import_audit_service.py`
- `tests/test_honor_rankings_view.py`
- `tests/test_import_audit_service.py`
- `tests/test_import_audit_dal.py`

When changing this pipeline, cover:

- missing required workbook columns
- blank/NaN names
- rollback on ingest failure
- telemetry on success/failure
- generic audit batch/phase success, failure, and best-effort behavior
- terminal audit status after post-ingest notification or refresh failures
- empty latest-ranking output
- ranking view formatting

## Operational Notes

- SQL table/view names must be validated against `C:\K98-bot-SQL-Server`.
- Keep parsing and database work out of the Discord event loop.
- Preserve user-safe upload error messages in `upload_routes/honor_route.py`.
- Keep generic audit writes best-effort; Honor imports must not fail solely because audit writes
  fail.
- Do not infer schema from Python if SQL definitions exist.
