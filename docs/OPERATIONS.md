```markdown
# Operations / Runbook

This document describes operational concerns for the processing pipeline, maintenance offloads,
telemetry fields, and live_queue recovery. It is intended to accompany PRs that add telemetry
and offload observability (PR A) and tests + runbook (PR B).

## Telemetry
Telemetry JSON lines are written to the telemetry logger (logging name `telemetry`) and written
to the file defined as TELEMETRY_LOG_PATH in `logging_setup.py`.

Key telemetry events emitted by the pipeline and maintenance helpers:

- `processing_pipeline_summary`
  - excel: bool
  - archive: bool
  - sql: bool
  - export: bool
  - proc_import: bool
  - duration_seconds: float
  - filename: str

- `run_stats_copy_archive`
  - status: "exception" | ...
  - filename: str

- `proc_import`, `post_import_stats`, `proc_import_worker`, `post_stats_worker`
  - status: "failed"|"success"|"timeout"|"exception"
  - filename / database fields
  - `orphaned_offload_possible`: bool (True when parent timed out while offload may still run)

- `maintenance_subproc*` series
  - Start / registered / success / failed / timeout events for subprocess-based maintenance workers
  - Includes `offload_id` (unique id assigned by parent), and `pid` when available
  - `output_snippet` may include a trimmed stdout/stderr sample

When offload tasks are started (PR A+), telemetry includes:
- `offload_id`: unique identifier assigned by the parent to the offload
- `pid`: process id (if offloaded to a process)
- `command`: exact command run (list)

### Inspecting telemetry
- Tail the telemetry file:
  - `tail -n 500 logs/telemetry_log.jsonl`
- Search for orphan markers:
  - `grep -R '"orphaned_offload_possible": true' logs/telemetry_log.jsonl`
- Look for maintenance subprocess events:
  - `grep -R '"event":"maintenance_subproc"' logs/telemetry_log.jsonl | jq .`

## Orphaned offloads — detection & recovery
- The parent process may time out waiting for a maintenance worker (post-import stats or proc_import).
- When that happens the parent emits telemetry containing:
  - `orphaned_offload_possible: true`
  - `offload_id` and `pid` (if available)
- To inspect the orphan:
  - On the host, use `ps aux | grep <pid>` (or `tasklist` on Windows) to examine the PID.
  - If the process is still running and appears stuck, you can:
    - TERM then KILL the PID. Prefer manual operator approval.
    - Use the admin cancellation tooling (planned PR) which safely signals the process and records telemetry.
  - Check logs:
    - `logs/log.txt`, `logs/error_log.txt`, `logs/crash.log`, and `logs/telemetry_log.jsonl`.

## Live queue persistence & recovery
- Persisted file: `QUEUE_CACHE_FILE` (typically `data/live_queue_cache.json`).
- Saved shape:
  ```
  {
    "jobs": [ ... ],
    "message_meta": {
      "channel_id": <int>,
      "message_id": <int>,
      "message_created": "<iso8601>" | null
    } | null
  }
  ```
- Recovery:
  - On bot startup `utils.load_live_queue()` will populate in-memory queue.
  - On first `update_live_queue_embed()` the bot attempts to rehydrate the message by fetching the channel and message.
  - If fetch returns NotFound or Forbidden the metadata will be cleared and a fresh embed will be created.

## Preflight / Log headroom
- `preflight_from_env_sync` probes SQL log usage and may raise `LogHeadroomError` when large writes are unsafe.
- Behaviors:
  - When preflight raises `LogHeadroomError`, proc_import will be skipped and the pipeline emits telemetry and a status embed.
  - When preflight times out in the parent, telemetry will mark `proc_import_preflight` with `status: timeout` and `orphaned_offload_possible=true`.

## Quick checks and commands
- Check telemetry file:
  - `jq 'select(.event=="processing_pipeline_summary")' -c logs/telemetry_log.jsonl | tail -n 50`
- Locate possible orphaned offloads:
  - `grep -R '"orphaned_offload_possible": true' logs/telemetry_log.jsonl`
- Inspect live queue file:
  - `cat data/live_queue_cache.json | jq .`

## Notes
- The offload registry introduced in PR A is in-memory. It is intended for immediate operational visibility
  (telemetry + ability to inspect via python REPL or possible admin command). It is not persisted to disk by design.
- PR E in the roadmap will add safe cancellation tooling and a persistent offload registry if desired.

```
