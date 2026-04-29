# PR Summary — Task 3: Event Instance Generator + SQL→JSON Publish

## Overview
This PR completes **Task 3** of the resilient Event Calendar architecture for K98 Bot:

**Google Sheets → SQL source tables → EventInstances → JSON cache → Bot runtime**

The implementation preserves the reliability goals established in Task 1/2:
- Bot runtime does not depend on live Google Sheets.
- SQL is the operational source of truth.
- JSON cache is the runtime source.
- Failure paths preserve last-known-good behavior and emit operational telemetry.

---

## Completed in this PR

## 1) Event instance generation engine (SQL-driven)
Implemented core generator module with deterministic behavior:

- `load_recurring_rules(conn)`
- `load_oneoff_events(conn)`
- `load_overrides(conn)`
- `generate_recurring_instances(...)`
- `merge_events(...)`
- `apply_overrides(...)`
- `compute_effective_hash(instance)`
- `write_event_instances(...)`
- `generate_calendar_instances(...)`

### Behavior delivered
- Loads active rules/events/overrides from SQL.
- Generates recurring occurrences within configurable horizon.
- Merges one-off events into unified instance set.
- Applies overrides deterministically:
  - `cancel` → marks instance cancelled
  - `modify` → patches non-null `New*` fields
- Sorts deterministically for stable output.
- Computes/stores `EffectiveHash` on final post-override payload.
- Writes `EventInstances` with transactional safety.

---

## 2) SQL → JSON cache publishing
Implemented cache publisher module:

- `load_runtime_instances(conn, horizon_days=365)`
- `build_cache_payload(instances, horizon_days)`
- `publish_event_calendar_cache(horizon_days=365, force_empty=False)`

### Behavior delivered
- Reads publishable rows from SQL only (not Sheets).
- Uses existing `build_event_calendar_cache_payload` contract adapter.
- Filters cancelled rows.
- Writes runtime JSON cache file.
- Includes preserve-on-empty guard unless `force_empty=True`.

---

## 3) Service orchestration expansion
`event_calendar/service.py` expanded with:

- `generate(...)`
- `publish_cache(...)`
- `refresh_full(...)` (sync → generate → publish orchestration)

### Reliability/operations improvements
- Blocking sync/generate/publish paths run in worker thread via `asyncio.to_thread(...)`.
- Telemetry emitted on both success and exception paths.
- Expanded status state:
  - sync status/result (existing)
  - generate status/result
  - publish status/result
- `get_status()` now returns:
  - `mode = "sheets_sql_generate_publish"`
  - full sync/generate/publish status blocks

---

## 4) Admin command wiring (slash commands)
Added/updated admin commands using repo-native style (`@bot.slash_command`):

- `/calendar_refresh`
- `/calendar_generate`
- `/calendar_publish_cache`
- `/calendar_status`

### Command guarantees
- Uses operation locks for serialization:
  - `calendar_refresh`
  - `calendar_generate`
  - `calendar_publish_cache`
- Operational embeds include status + metrics.

---

## 5) Task 1/2 hardening carry-forward completed
Applied hardening in `event_calendar/sheets_sync.py` and config:

- CSV header normalization (lower/trim/BOM-safe).
- Explicit `TargetKind` validation in `parse_overrides` (`rule|oneoff|instance`).
- Upsert identifier allowlist (tables/keys/columns) to reduce SQL injection footgun risk.
- Single-transaction strategy for 3-table source upsert path.
- `EVENT_CALENDAR_SHEET_ID` config parsing aligned to `_env_str(...)`.
- Dependency handling updated (requests maintained in project requirements).

---

## 6) SQL verification scripts added and executed
Created and ran:

- `sql/tests/verify_calendar_generation_smoke.sql`
- `sql/tests/verify_calendar_publish_source.sql`

Result: **both passed**.

---

## 7) Tests
Added/updated tests covering:
- service `to_thread` usage
- failure telemetry paths
- state/status updates
- command behavior (including lock patterns)

Result: **all tests passed**.

---

## Acceptance criteria status (Task 3)
- [x] Recurring generation works across horizon.
- [x] One-off merge works.
- [x] Override cancel/modify behavior implemented.
- [x] Deterministic sorting and stable instance output.
- [x] EffectiveHash generated from final payload.
- [x] SQL→JSON publish implemented from SQL source.
- [x] Preserve-on-empty cache guard implemented.
- [x] Admin controls for generate/publish/status added.
- [x] Failure telemetry and graceful behavior implemented.

---

## Proposed Task 4 (next)

## Task 4 — Runtime Consumption, Quality Gates, and Production Hardening

## Objective
Finalize the calendar pipeline for production bot usage by integrating runtime command consumption, strengthening idempotency/observability, and adding deployment-grade safeguards.

## Scope

### 1) Bot runtime integration
- Move calendar-facing bot commands/embeds to consume JSON runtime cache only.
- Ensure no command path queries Google Sheets directly.
- Add explicit stale-cache messaging if cache age exceeds threshold.

### 2) Scheduled pipeline automation
- Add scheduled jobs (or existing scheduler hooks) for:
  - refresh sync
  - generate instances
  - publish cache
- Add per-stage timeout, retry, and backoff policy.
- Ensure operation lock compatibility with scheduler-triggered runs.

### 3) Stronger idempotency + diff publish
- Optional optimization: only rewrite cache file if payload hash changed.
- Track last-published hash and change reason (sync/gen/publish run id).
- Reduce unnecessary downstream embed churn.

### 4) Observability upgrades
- Add run duration metrics (sync/generate/publish).
- Add structured “last successful run” and “last failed run” fields.
- Add `calendar_health` summary block for status command:
  - cache_age_minutes
  - next_upcoming_event
  - last_successful_pipeline_utc
  - current_degraded_mode flag

### 5) Data quality and anomaly checks
- Add guardrails for suspicious generation results:
  - sudden drop to zero events
  - extreme row volume spikes
  - unusually high cancelled ratio
- Emit warning telemetry without clobbering last-known-good cache.

### 6) Integration tests / contract tests
- End-to-end pipeline test:
  - source rows -> EventInstances -> JSON payload
- Cache contract snapshot test against expected schema.
- Determinism test across repeated identical runs.

### 7) Operational runbook + docs
- Update docs with:
  - normal operations
  - manual recovery steps
  - troubleshooting checklist
  - failure mode matrix and expected status values

## Task 4 Exit Criteria
- Runtime calendar commands are fully cache-driven.
- Scheduler-based unattended operation is stable.
- Health/status output is operator-friendly and actionable.
- End-to-end tests provide regression confidence.
- Runbook documentation is complete for on-call/admin usage.
