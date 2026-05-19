# Diagnostics Runbook

Purpose: triage errors, crashes, performance issues, offload problems, and telemetry questions.

## Primary Artifacts

- `logs/log.txt` - application log
- `logs/error_log.txt` - warnings and operational errors
- `logs/crash.log` - unhandled exceptions and tracebacks
- `logs/telemetry_log.jsonl` - structured telemetry
- `logs/last_shutdown_info.json` - last clean shutdown summary
- `QUEUE_CACHE_FILE` - live queue state
- `COMMAND_CACHE_FILE` - command signature cache

Exact paths are defined in `constants.py` and `logging_setup.py`.

## Pytest Log Review

Pytest runs are intentionally isolated from production operational logs. Expected negative-path
ERROR/WARNING records remain visible through pytest output and `caplog`, but routine test execution
must not write to `logs/log.txt`, `logs/error_log.txt`, `logs/crash.log`, or
`logs/telemetry_log.jsonl`.

For a saved pytest review artifact, tee the command to a non-production audit file:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests 2>&1 | Tee-Object -FilePath .codex_pytest_audit.log
```

To verify that pytest did not touch production operational logs, run:

```powershell
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Use production log files only for runtime diagnostics, deployment health, and bot-machine
operation review, not as the source of pytest negative-path evidence.

## Collect Diagnostics

```powershell
python scripts/collect_diagnostics.py -o diagnostics.tar.gz
```

Include full logs when needed:

```powershell
python scripts/collect_diagnostics.py --include-logs -o diagnostics.tar.gz
```

Upload options are available through:

- `--upload --s3-bucket <bucket> --s3-prefix <prefix>`
- `--upload --artifact-url <url> --artifact-token <token>`
- `DIAGNOSTICS_S3_BUCKET`
- `DIAGNOSTICS_S3_PREFIX`
- `ARTIFACT_UPLOAD_URL`
- `ARTIFACT_UPLOAD_TOKEN`

Keep upload tokens private. The diagnostics script redacts sensitive environment values in the
archive.

## Telemetry

Telemetry is written through the `telemetry` logger to `TELEMETRY_LOG_PATH`.

Useful searches:

```powershell
Select-String -Path logs\telemetry_log.jsonl -Pattern '"orphaned_offload_possible": true'
Select-String -Path logs\telemetry_log.jsonl -Pattern '"processing_pipeline_summary"'
Select-String -Path logs\telemetry_log.jsonl -Pattern '"maintenance_subproc"'
```

Common telemetry areas:

- processing pipeline summaries
- proc import and post-import stats offloads
- maintenance subprocess events
- orphaned offload markers
- SQL preflight/log-headroom results
- honor and activity import outcomes

## Offload Inspection

Use:

```powershell
python scripts/offload_admin.py list
python scripts/offload_admin.py cancel --id <offload_id> --actor "<operator>"
python scripts/offload_admin.py cancel --pid <pid> --actor "<operator>"
python scripts/offload_monitor.py --once
```

Only cancel work when you understand the import/process being interrupted.

## Live Queue Recovery

`QUEUE_CACHE_FILE` stores queued job state and message metadata. If the bot restarts, queue
helpers reload the persisted state and attempt to rehydrate the queue message.

If recovery fails:

1. Save a copy of the queue JSON.
2. Check `logs/error_log.txt` and `logs/crash.log`.
3. Confirm the queue message/channel still exists and is accessible.
4. Clear stale metadata only after preserving the file for review.

## Common Triage Flow

1. Check `crash.log` first for unhandled exceptions.
2. Check `error_log.txt` for operational failures.
3. Search telemetry for the relevant event, filename, `offload_id`, or `pid`.
4. Inspect persisted state under `DATA_DIR`.
5. Run focused smoke/test commands for the affected subsystem.
